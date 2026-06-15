from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import GitCommit, Project
from src.rag.chat_service import answer_source_question
from src.rag.embedding_client import EmbeddingClient
from src.services.ai_evidence_service import (
    get_local_ai_verification_rows,
    list_local_ai_verification_invocations,
    run_pl_briefing_shortcut,
)
from src.services.ai_invocation_service import record_ai_invocation
from src.services.code_review_service import CodeReviewService
from src.services.mapping_service import MappingService
from src.utils.config import settings


DEFAULT_FEATURES = ["embedding-check", "pl-briefing", "project-chat", "code-review"]


def _resolve_project(db, *, project_id: int | None, project_name: str | None) -> Project:
    if project_id is not None:
        project = db.get(Project, int(project_id))
        if project is None:
            raise SystemExit(f"프로젝트를 찾을 수 없습니다: id={project_id}")
        return project
    if project_name:
        project = db.query(Project).filter(Project.name == project_name).one_or_none()
        if project is None:
            raise SystemExit(f"프로젝트를 찾을 수 없습니다: name={project_name}")
        return project
    project = db.query(Project).order_by(Project.id.desc()).first()
    if project is None:
        raise SystemExit("등록된 프로젝트가 없습니다.")
    return project


def _ensure_live_settings(features: list[str], *, allow_mock: bool) -> None:
    llm_features = {"pl-briefing", "project-chat", "code-review", "mapping"}
    needs_llm = bool(set(features) & llm_features)
    needs_embedding = "embedding-check" in features
    errors = []
    if needs_llm and settings.llm_provider == "mock":
        errors.append("LLM_PROVIDER=mock 상태입니다. live 검증에는 LLM_PROVIDER=local_openai가 필요합니다.")
    if needs_embedding and settings.embedding_provider == "mock":
        errors.append("EMBEDDING_PROVIDER=mock 상태입니다. live embedding 검증에는 EMBEDDING_PROVIDER=local_openai가 필요합니다.")
    if errors and not allow_mock:
        raise SystemExit("\n".join(errors) + "\nmock 검증을 의도한 경우에만 --allow-mock을 붙이세요.")


def _run_embedding_check(db, project_id: int) -> dict:
    started_at = datetime.now(timezone.utc)
    client = EmbeddingClient()
    ok, message = client.test_connection()
    finished_at = datetime.now(timezone.utc)
    row = record_ai_invocation(
        db,
        project_id=project_id,
        feature="embedding_connection",
        provider=client.provider,
        model=client.model,
        status="completed" if ok else "failed",
        mode="connection_check",
        fallback_used=False,
        validation_status="dimension_checked" if ok else "failed",
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=int((finished_at - started_at).total_seconds() * 1000),
        error_message=None if ok else message,
        raw_metadata={
            "base_url": client.base_url,
            "dimension": settings.pgvector_dimension,
            "message": message,
        },
    )
    db.commit()
    return {"feature": "embedding-check", "status": row.status, "summary": message}


def _run_pl_briefing(db, project_id: int) -> dict:
    result = run_pl_briefing_shortcut(db, project_id)
    db.commit()
    return {"feature": "pl-briefing", "status": result.status, "summary": result.summary}


def _run_project_chat(db, project: Project, question: str, top_k: int) -> dict:
    answer = answer_source_question(db, project, question, top_k=top_k)
    db.commit()
    status = "failed" if answer.errors else "completed"
    summary = (
        f"used_sources={answer.used_source_count}, excluded={answer.excluded_count}, "
        f"insufficient={answer.insufficient_evidence}, graph={answer.graph_evidence_metadata.get('status', '-')}"
    )
    if answer.errors:
        summary += f", errors={'; '.join(answer.errors[:3])}"
    return {"feature": "project-chat", "status": status, "summary": summary}


def _run_code_review(db, project: Project, target_type: str, target_ref: str | None) -> dict:
    result = CodeReviewService().review_project(db, project, target_type=target_type, target_ref=target_ref)
    if result.errors:
        return {"feature": "code-review", "status": "failed", "summary": "; ".join(result.errors)}
    review = result.review
    status = review.status if review is not None else "failed"
    summary = review.summary if review is not None else "review result 없음"
    return {"feature": "code-review", "status": status, "summary": summary}


def _run_mapping(db, project_id: int, commit_limit: int, candidates_per_commit: int) -> dict:
    commit_ids = [
        row.id
        for row in (
            db.query(GitCommit)
            .filter(GitCommit.project_id == project_id)
            .order_by(GitCommit.committed_at.desc().nullslast(), GitCommit.id.desc())
            .limit(max(1, int(commit_limit)))
            .all()
        )
    ]
    if not commit_ids:
        return {"feature": "mapping", "status": "skipped", "summary": "검증할 commit이 없습니다."}
    result = MappingService().analyze_commits(
        db,
        project_id=project_id,
        commit_ids=commit_ids,
        candidates_per_commit=candidates_per_commit,
        skip_completed=False,
    )
    status = "completed_with_warnings" if result.errors or result.failed_count else "completed"
    return {
        "feature": "mapping",
        "status": status,
        "summary": (
            f"analyzed={result.analyzed_count}, created={result.created_count}, "
            f"updated={result.updated_count}, failed={result.failed_count}"
        ),
    }


def _render_report(project: Project, features: list[str], results: list[dict], rows: list, invocations: list[dict]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Local LLM Verification Result",
        "",
        f"- 생성 시각(UTC): {generated_at}",
        f"- 프로젝트: {project.name} ({project.id})",
        f"- Git 저장소: {project.git_repo_path or '-'}",
        f"- LLM: provider={settings.llm_provider}, model={settings.llm_model or '-'}, base={settings.llm_base_url or '-'}",
        (
            f"- Embedding: provider={settings.embedding_provider}, model={settings.embedding_model or '-'}, "
            f"base={settings.embedding_base_url or settings.llm_base_url or '-'}, dimension={settings.pgvector_dimension}"
        ),
        f"- 실행 기능: {', '.join(features)}",
        "",
        "## 실행 결과",
        "| 기능 | 상태 | 요약 |",
        "|---|---|---|",
    ]
    lines.extend(f"| {row['feature']} | {row['status']} | {row['summary']} |" for row in results)
    lines.extend(["", "## AI 운영 현황 live 검증 요약", "| 영역 | 상태 | 현재 값 | 다음 조치 |", "|---|---|---|---|"])
    lines.extend(f"| {row.area} | {row.status} | {row.value} | {row.action} |" for row in rows)
    lines.extend(["", "## 최근 invocation telemetry", "| 기능 | Provider | Model | 상태 | Fallback | Validation | Started | Error |", "|---|---|---|---|---|---|---|---|"])
    if invocations:
        lines.extend(
            (
                f"| {row['feature_label']} | {row['provider']} | {row['model']} | {row['status']} | "
                f"{row['fallback_used']} | {row['validation_status']} | {row['started_at']} | {row['error']} |"
            )
            for row in invocations
        )
    else:
        lines.append("| - | - | - | - | - | - | - | invocation 없음 |")
    lines.extend(
        [
            "",
            "## 해석 기준",
            "- 이 결과는 mock/fallback 실행과 live local provider 실행을 분리하기 위한 운영 증거입니다.",
            "- `LLM_PROVIDER=mock` 또는 `EMBEDDING_PROVIDER=mock`으로 실행한 결과는 live 검증으로 보지 않습니다.",
            "- 외부 유료 API나 CI에서 이 스크립트를 자동 실행하지 마세요.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local OpenAI-compatible AI verification and record telemetry.")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project-id", type=int)
    target.add_argument("--project-name")
    parser.add_argument(
        "--features",
        nargs="+",
        default=DEFAULT_FEATURES,
        choices=["embedding-check", "pl-briefing", "project-chat", "code-review", "mapping"],
        help="Verification features to run.",
    )
    parser.add_argument("--question", default="결제금액 검증은 어디에서 수행되나요?")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--code-review-target", default="latest_commit", choices=["latest_commit", "working_tree", "staged", "commit"])
    parser.add_argument("--code-review-ref")
    parser.add_argument("--mapping-commit-limit", type=int, default=1)
    parser.add_argument("--mapping-candidates", type=int, default=10)
    parser.add_argument("--output", help="Optional Markdown report path.")
    parser.add_argument("--allow-mock", action="store_true", help="Allow mock providers for workflow smoke checks.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    features = list(dict.fromkeys(args.features))
    _ensure_live_settings(features, allow_mock=args.allow_mock)
    init_db()
    with SessionLocal() as db:
        project = _resolve_project(db, project_id=args.project_id, project_name=args.project_name)
        results: list[dict] = []
        if "embedding-check" in features:
            results.append(_run_embedding_check(db, int(project.id)))
        if "pl-briefing" in features:
            results.append(_run_pl_briefing(db, int(project.id)))
        if "project-chat" in features:
            results.append(_run_project_chat(db, project, args.question, int(args.top_k)))
        if "code-review" in features:
            results.append(_run_code_review(db, project, args.code_review_target, args.code_review_ref))
        if "mapping" in features:
            results.append(_run_mapping(db, int(project.id), args.mapping_commit_limit, args.mapping_candidates))

        rows = get_local_ai_verification_rows(db, int(project.id))
        invocations = list_local_ai_verification_invocations(db, int(project.id), limit=20)
        report = _render_report(project, features, results, rows, invocations)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
