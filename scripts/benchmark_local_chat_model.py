from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.llm_client import LLMClient


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    prompt: str
    schema: dict
    validate: Callable[[dict], list[str]]


def _contains_hangul(value: object) -> bool:
    return isinstance(value, str) and any("가" <= character <= "힣" for character in value)


def _validate_mapping(payload: dict) -> list[str]:
    errors = []
    if payload.get("program_id") != "SMP-PAY-001":
        errors.append("program_id must be SMP-PAY-001")
    if not payload.get("evidence"):
        errors.append("evidence must not be empty")
    if not _contains_hangul(payload.get("reason_ko")):
        errors.append("reason_ko must contain Korean text")
    return errors


def _validate_payment_bug(payload: dict) -> list[str]:
    errors = []
    if payload.get("risk") != "high":
        errors.append("risk must be high")
    if payload.get("symbol") != "authorize":
        errors.append("symbol must be authorize")
    if not _contains_hangul(payload.get("summary_ko")):
        errors.append("summary_ko must contain Korean text")
    return errors


def _validate_sql_bug(payload: dict) -> list[str]:
    errors = []
    if payload.get("has_bug") is not True:
        errors.append("has_bug must be true")
    if payload.get("category") != "sql":
        errors.append("category must be sql")
    if payload.get("severity") not in {"high", "medium"}:
        errors.append("severity must be high or medium")
    if not _contains_hangul(payload.get("summary_ko")):
        errors.append("summary_ko must contain Korean text")
    return errors


CASES = [
    BenchmarkCase(
        name="commit_mapping",
        prompt="""
다음 commit을 가장 관련 있는 프로그램 하나에 매핑하세요.

commit title: Reject zero-amount payment before authorize
changed path: src/main/java/com/example/market/payment/service/PaymentService.java

후보:
- SMP-PAY-001: 결제 승인, payment, authorize
- SMP-INV-001: 재고 출고, inventory, release
- SMP-RPT-001: 매출 보고서, sales report

reason_ko는 선택 근거를 한국어 한 문장으로 작성하세요.
""".strip(),
        schema={
            "type": "object",
            "properties": {
                "program_id": {
                    "type": "string",
                    "enum": ["SMP-PAY-001", "SMP-INV-001", "SMP-RPT-001"],
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "reason_ko": {"type": "string"},
            },
            "required": ["program_id", "confidence", "evidence", "reason_ko"],
            "additionalProperties": False,
        },
        validate=_validate_mapping,
    ),
    BenchmarkCase(
        name="payment_code_review",
        prompt="""
다음 Java 결제 승인 코드를 검토하세요.

public String authorize(long amount) {
    if (amount <= 0) {
        return "APPROVED";
    }
    return paymentGateway.authorize(amount);
}

실제 운영 코드라면 가장 중요한 위험 하나를 판정하고 summary_ko를 한국어 한 문장으로 작성하세요.
""".strip(),
        schema={
            "type": "object",
            "properties": {
                "risk": {"type": "string", "enum": ["high", "medium", "low", "none"]},
                "symbol": {"type": "string"},
                "summary_ko": {"type": "string"},
            },
            "required": ["risk", "symbol", "summary_ko"],
            "additionalProperties": False,
        },
        validate=_validate_payment_bug,
    ),
    BenchmarkCase(
        name="sql_code_review",
        prompt="""
다음 SQL을 검토하세요.

SELECT customer_id, SUM(total_amount)
FROM orders
WHERE paid_at >= :from_date;

PostgreSQL에서 실행되는 운영 조회라고 가정하고 핵심 오류를 판정하세요. summary_ko는 한국어 한 문장으로 작성하세요.
""".strip(),
        schema={
            "type": "object",
            "properties": {
                "has_bug": {"type": "boolean"},
                "category": {"type": "string", "enum": ["sql", "security", "performance", "none"]},
                "severity": {"type": "string", "enum": ["high", "medium", "low", "none"]},
                "summary_ko": {"type": "string"},
            },
            "required": ["has_bug", "category", "severity", "summary_ko"],
            "additionalProperties": False,
        },
        validate=_validate_sql_bug,
    ),
]


def run_benchmark(model: str, base_url: str, max_tokens: int) -> dict:
    client = LLMClient(
        provider="local_openai",
        model=model,
        base_url=base_url,
        max_tokens=max_tokens,
    )
    case_results = []
    for case in CASES:
        started = time.perf_counter()
        try:
            response = client.generate(
                case.prompt,
                response_schema=case.schema,
                response_schema_name=f"benchmark_{case.name}",
            )
            elapsed_seconds = time.perf_counter() - started
            payload = json.loads(response.text)
            validation_errors = case.validate(payload)
            usage = response.raw.get("response", {}).get("usage", {})
            case_results.append(
                {
                    "name": case.name,
                    "elapsed_seconds": round(elapsed_seconds, 3),
                    "valid_json": True,
                    "expected_result": not validation_errors,
                    "validation_errors": validation_errors,
                    "usage": usage,
                    "response": payload,
                }
            )
        except Exception as exc:
            case_results.append(
                {
                    "name": case.name,
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "valid_json": False,
                    "expected_result": False,
                    "validation_errors": [str(exc)],
                }
            )

    return {
        "model": model,
        "base_url": base_url,
        "case_count": len(case_results),
        "valid_json_count": sum(bool(item["valid_json"]) for item in case_results),
        "expected_result_count": sum(bool(item["expected_result"]) for item in case_results),
        "total_seconds": round(sum(float(item["elapsed_seconds"]) for item in case_results), 3),
        "cases": case_results,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Benchmark a loaded OpenAI-compatible local chat model.")
    parser.add_argument("--model", required=True, help="LM Studio model identifier")
    parser.add_argument("--base-url", default="http://127.0.0.1:12345/v1")
    parser.add_argument("--max-tokens", type=int, default=220)
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.model, args.base_url, args.max_tokens), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
