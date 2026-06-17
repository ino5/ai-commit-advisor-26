import subprocess
from pathlib import Path

from src.db.models import Project
from src.rag.chat_service import INSUFFICIENT_EVIDENCE_ANSWER, answer_source_question
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
