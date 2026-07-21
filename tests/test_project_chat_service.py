import subprocess
from pathlib import Path

from src.db.models import Project
from src.rag.chat_service import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    _build_prompt,
    _build_verified_method_fallback,
    _collect_verified_java_method_evidence,
    _query_code_identifiers,
    _relevant_method_calls,
    _sort_verified_sources_for_prompt,
    _validate_method_answer,
    answer_source_question,
)
from src.rag.source_verifier import hash_text
from src.services.git_service import get_head_commit_hash


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def retrieve(self, query, limit=5, project_id=None, source_types=None):
        self.calls.append(
            {
                "query": query,
                "limit": limit,
                "project_id": project_id,
                "source_types": source_types,
            }
        )
        return self.results


class MockLLM:
    provider = "mock"
    model = "mock-chat-model"


class FakeGraphResult:
    status = "completed"
    summary = "graph evidence found"
    seeds = ["paymentservice", "ordermapper"]
    errors = []

    evidence = [
        {
            "evidence_type": "class_import",
            "title": "class -> imports -> class",
            "matched_seeds": ["paymentservice", "ordermapper"],
            "source_class": "com.example.market.payment.service.PaymentService",
            "target_class": "com.example.market.order.mapper.OrderMapper",
            "source_file": "src/main/java/com/example/market/payment/service/PaymentService.java",
            "target_file": "src/main/java/com/example/market/order/mapper/OrderMapper.java",
            "path": [
                "com.example.market.payment.service.PaymentService",
                "com.example.market.order.mapper.OrderMapper",
            ],
        }
    ]


def _init_git_repo(repo: Path) -> str:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
    return get_head_commit_hash(repo) or ""


def test_answer_source_question_returns_insufficient_evidence_without_sources():
    project = Project(id=1, git_repo_path=None)
    answer = answer_source_question(
        None,
        project,
        "로그인 화면은 어디에 있나요?",
        retriever=FakeRetriever([]),
        llm_client=MockLLM(),
    )

    assert answer.insufficient_evidence is True
    assert answer.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert "현재 검증된 소스 근거만으로는 답변하기 어렵습니다." in answer.answer
    assert answer.used_source_count == 0
    assert answer.provider == "mock"
    assert answer.model == "mock-chat-model"
    assert answer.fallback_used is True


def test_answer_source_question_excludes_invalid_source_file_from_current_answer():
    project = Project(id=1, git_repo_path=None)
    answer = answer_source_question(
        None,
        project,
        "현재 구현을 설명해줘",
        retriever=FakeRetriever(
            [
                {
                    "id": 10,
                    "source_type": "source_file",
                    "source_id": "src/app.py",
                    "text": "print('hello')",
                    "metadata": {"file_path": "src/app.py"},
                    "similarity": 0.9,
                }
            ]
        ),
        llm_client=MockLLM(),
    )

    assert answer.insufficient_evidence is True
    assert answer.used_source_count == 0
    assert answer.excluded_count == 1
    assert answer.sources[0]["verification_status"] == "invalid"


def test_answer_source_question_excludes_stale_source_file_from_current_answer(tmp_path):
    repo = tmp_path
    source_path = repo / "src" / "app.py"
    source_path.parent.mkdir()
    source_path.write_text("print('old')\n", encoding="utf-8")
    old_head = _init_git_repo(repo)
    old_hash = hash_text("print('old')")

    source_path.write_text("print('new')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "change"], cwd=repo, check=True, capture_output=True)

    project = Project(id=1, git_repo_path=str(repo))
    answer = answer_source_question(
        None,
        project,
        "현재 app.py 내용을 알려줘",
        retriever=FakeRetriever(
            [
                {
                    "id": 11,
                    "source_type": "source_file",
                    "source_id": "src/app.py",
                    "text": "print('old')",
                    "metadata": {
                        "file_path": "src/app.py",
                        "line_start": 1,
                        "line_end": 1,
                        "chunk_content_hash": old_hash,
                        "indexed_head_hash": old_head,
                    },
                    "similarity": 0.9,
                }
            ]
        ),
        llm_client=MockLLM(),
    )

    assert answer.insufficient_evidence is True
    assert answer.excluded_count == 1
    assert answer.sources[0]["verification_status"] == "stale"


def test_answer_source_question_keeps_verified_source_citation_metadata(tmp_path):
    repo = tmp_path
    source_path = repo / "src" / "app.py"
    source_path.parent.mkdir()
    source_path.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    head_hash = _init_git_repo(repo)
    chunk_hash = hash_text("def hello():\n    return 'world'")

    project = Project(id=1, git_repo_path=str(repo))
    answer = answer_source_question(
        None,
        project,
        "hello 함수는 무엇을 반환하나요?",
        retriever=FakeRetriever(
            [
                {
                    "id": 12,
                    "source_type": "source_file",
                    "source_id": "src/app.py",
                    "text": "def hello():\n    return 'world'",
                    "metadata": {
                        "file_path": "src/app.py",
                        "line_start": 1,
                        "line_end": 2,
                        "chunk_content_hash": chunk_hash,
                        "indexed_head_hash": head_hash,
                    },
                    "similarity": 0.95,
                }
            ]
        ),
        llm_client=MockLLM(),
    )

    assert answer.insufficient_evidence is False
    assert answer.used_source_count == 1
    assert answer.sources[0]["verification_status"] == "verified"
    assert answer.sources[0]["source_type"] == "source_file"
    assert answer.sources[0]["metadata"]["file_path"] == "src/app.py"
    assert answer.sources[0]["metadata"]["line_start"] == 1
    assert "src/app.py:1-2" in answer.answer


def test_sort_verified_sources_prioritizes_question_identifiers():
    sources = [
        {
            "source_type": "source_file",
            "source_id": "src/main/java/com/example/market/payment/mapper/PaymentMapper.java",
            "text": "public interface PaymentMapper {}",
            "metadata": {"file_path": "src/main/java/com/example/market/payment/mapper/PaymentMapper.java", "line_start": 1},
            "similarity": 0.99,
        },
        {
            "source_type": "source_file",
            "source_id": "src/main/java/com/example/market/order/mapper/OrderMapper.java",
            "text": "public interface OrderMapper { void updateOrderStatus(long orderId, String status); }",
            "metadata": {"file_path": "src/main/java/com/example/market/order/mapper/OrderMapper.java", "line_start": 1},
            "similarity": 0.8,
        },
        {
            "source_type": "source_file",
            "source_id": "src/main/java/com/example/market/payment/service/PaymentService.java",
            "text": "import com.example.market.order.mapper.OrderMapper; public class PaymentService {}",
            "metadata": {"file_path": "src/main/java/com/example/market/payment/service/PaymentService.java", "line_start": 1},
            "similarity": 0.7,
        },
    ]

    sorted_sources = _sort_verified_sources_for_prompt(
        sources,
        "PaymentService와 OrderMapper는 어떤 클래스 import 관계야?",
    )

    top_files = {source["metadata"]["file_path"].rsplit("/", 1)[-1] for source in sorted_sources[:2]}
    assert top_files == {"PaymentService.java", "OrderMapper.java"}


def test_query_code_identifiers_keeps_java_class_name_without_generic_extension():
    identifiers = _query_code_identifiers("PaymentController.java와 PaymentService.authorize 흐름")

    assert "paymentcontroller.java" in identifiers
    assert "paymentcontroller" in identifiers
    assert "paymentservice" in identifiers
    assert "authorize" in identifiers
    assert "java" not in identifiers


def test_prompt_with_verified_sources_does_not_prime_exact_insufficient_answer():
    prompt = _build_prompt(
        "PaymentService와 OrderMapper 관계를 설명해줘",
        [
            {
                "source_type": "source_file",
                "source_id": "src/main/java/com/example/market/payment/service/PaymentService.java",
                "text": "import com.example.market.order.mapper.OrderMapper;\norderMapper.updateOrderStatus(orderId, \"PAID\");",
                "metadata": {
                    "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                    "line_start": 1,
                    "line_end": 3,
                },
                "verification_status": "verified",
            }
        ],
        [],
        [],
    )

    assert INSUFFICIENT_EVIDENCE_ANSWER not in prompt
    assert "still answer the parts that are covered" in prompt
    assert "Named identifier focus" in prompt
    assert "import com.example.market.order.mapper.OrderMapper" in prompt
    assert "orderMapper.updateOrderStatus(orderId, \"PAID\")" in prompt


def test_method_evidence_preserves_sample_payment_direct_call_chain(tmp_path):
    files = {
        "src/main/java/com/example/market/payment/controller/PaymentController.java": """\
public class PaymentController {
    private final PaymentService paymentService;
    public String authorize(long orderId, int amount) {
        return paymentService.authorize(orderId, amount);
    }
}
""",
        "src/main/java/com/example/market/payment/service/PaymentService.java": """\
public class PaymentService {
    private final OrderStatusService orderStatusService;
    public String authorize(long orderId, int amount) {
        if (amount <= 0) {
            return "REJECTED";
        }
        orderStatusService.markPaid(orderId);
        return "AUTHORIZED";
    }
}
""",
        "src/main/java/com/example/market/order/service/OrderStatusService.java": """\
public class OrderStatusService {
    private final OrderStatusMapper orderStatusMapper;
    public void changeStatus(long orderId, String currentStatus, String nextStatus) {
        orderStatusMapper.updateStatus(orderId, nextStatus);
        orderStatusMapper.insertStatusHistory(orderId, nextStatus);
    }
    public void markPaid(long orderId) {
        changeStatus(orderId, PAYMENT_WAITING, PAID);
    }
}
""",
        "src/main/java/com/example/market/order/mapper/OrderStatusMapper.java": """\
public interface OrderStatusMapper {
    void updateStatus(long orderId, String status);
    void insertStatusHistory(long orderId, String status);
}
""",
    }
    sources = []
    for file_path, text in files.items():
        target = tmp_path / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        line_count = len(text.splitlines())
        sources.append(
            {
                "source_type": "source_file",
                "source_id": file_path,
                "text": text,
                "metadata": {"file_path": file_path, "line_start": 1, "line_end": line_count},
                "verification_status": "verified",
            }
        )

    question = (
        "PaymentController.java, PaymentService.java, OrderStatusService.java, "
        "OrderStatusMapper.java의 결제 금액 조건과 PAID 연결 흐름을 설명해줘"
    )
    evidence = _collect_verified_java_method_evidence(str(tmp_path), question, sources)
    call_pairs = [(call.caller, call.callee) for call in _relevant_method_calls(question, evidence)]

    assert call_pairs == [
        ("PaymentController.authorize", "PaymentService.authorize"),
        ("PaymentService.authorize", "OrderStatusService.markPaid"),
        ("OrderStatusService.markPaid", "OrderStatusService.changeStatus"),
        ("OrderStatusService.changeStatus", "OrderStatusMapper.updateStatus"),
        ("OrderStatusService.changeStatus", "OrderStatusMapper.insertStatusHistory"),
    ]
    payment_authorize = next(item for item in evidence if item.owner == "PaymentService.authorize")
    assert payment_authorize.condition_outcomes[0].condition == "amount <= 0"
    assert payment_authorize.condition_outcomes[0].outcome == 'return "REJECTED"'

    invalid_answer = (
        "`PaymentController.authorize → PaymentService.authorize` 뒤 "
        "`PaymentService.authorize → OrderStatusMapper.updateStatus`를 직접 호출하며 "
        "amount < 0이면 AUTHORIZED입니다."
    )
    errors = _validate_method_answer(question, invalid_answer, evidence, sources)
    assert any("검증되지 않은 직접 호출 단계" in error for error in errors)
    assert any("조건 결과 누락 또는 불일치" in error for error in errors)

    fallback = _build_verified_method_fallback(question, evidence)
    assert "PaymentService.authorize → OrderStatusService.markPaid" in fallback
    assert "OrderStatusService.markPaid → OrderStatusService.changeStatus" in fallback
    assert "PaymentService.authorize → OrderStatusMapper.updateStatus" not in fallback
    assert "amount <= 0" in fallback
    assert 'return "REJECTED"' in fallback


def test_answer_source_question_adds_graph_evidence_without_replacing_source_verification(tmp_path):
    repo = tmp_path
    source_path = repo / "src" / "main" / "java" / "com" / "example" / "market" / "payment" / "service" / "PaymentService.java"
    source_path.parent.mkdir(parents=True)
    source_text = "\n".join(
        [
            "package com.example.market.payment.service;",
            "import com.example.market.order.mapper.OrderMapper;",
            "public class PaymentService {}",
        ]
    )
    source_path.write_text(source_text + "\n", encoding="utf-8")
    head_hash = _init_git_repo(repo)
    chunk_hash = hash_text(source_text.strip())
    provider_calls = []

    def graph_provider(project_id, question, sources, *, expanded_queries=None, limit=8):
        provider_calls.append(
            {
                "project_id": project_id,
                "question": question,
                "sources": sources,
                "expanded_queries": expanded_queries,
                "limit": limit,
            }
        )
        return FakeGraphResult()

    project = Project(id=1, git_repo_path=str(repo))
    answer = answer_source_question(
        None,
        project,
        "결제 변경이 주문 쪽에 영향을 줄 수 있는 근거가 뭐야?",
        retriever=FakeRetriever(
            [
                {
                    "id": 13,
                    "source_type": "source_file",
                    "source_id": "src/main/java/com/example/market/payment/service/PaymentService.java",
                    "text": source_text,
                    "metadata": {
                        "file_path": "src/main/java/com/example/market/payment/service/PaymentService.java",
                        "line_start": 1,
                        "line_end": 3,
                        "chunk_content_hash": chunk_hash,
                        "indexed_head_hash": head_hash,
                    },
                    "similarity": 0.95,
                }
            ]
        ),
        llm_client=MockLLM(),
        graph_evidence_provider=graph_provider,
    )

    assert provider_calls
    assert provider_calls[0]["sources"][0]["verification_status"] == "verified"
    assert answer.used_source_count == 1
    assert answer.graph_evidence == FakeGraphResult.evidence
    assert answer.graph_evidence_metadata["status"] == "completed"
    assert "그래프 관계 근거" in answer.answer
    assert "PaymentService" in answer.answer
    assert answer.provider == "mock"
    assert answer.model == "mock-chat-model"
    assert answer.fallback_used is True


def test_answer_source_question_does_not_use_graph_evidence_without_verified_sources():
    provider_calls = []

    def graph_provider(*args, **kwargs):
        provider_calls.append((args, kwargs))
        return FakeGraphResult()

    project = Project(id=1, git_repo_path=None)
    answer = answer_source_question(
        None,
        project,
        "결제와 주문 관계를 알려줘",
        retriever=FakeRetriever([]),
        llm_client=MockLLM(),
        graph_evidence_provider=graph_provider,
    )

    assert answer.insufficient_evidence is True
    assert answer.graph_evidence == []
    assert provider_calls == []
