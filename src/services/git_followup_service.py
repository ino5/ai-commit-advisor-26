from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.db.models import CommitFile, GitCommit, Program, Project, RiskFinding
from src.rag.source_index_service import (
    SourceIndexStatus,
    get_changed_source_files_since_latest_index,
    get_source_index_status,
)
from src.services.git_repository_status_service import GitRepositoryStatus, get_repository_status
from src.services.git_service import GitSyncResult
from src.services.neo4j_graph_service import Neo4jGraphFreshness, get_project_graph_freshness
from src.utils.runtime_estimator import estimate_runtime


GROUP_RECOMMENDED = "권장 순서"
GROUP_LATER = "나중에 해도 됨"
STATUS_RECOMMENDED = "권장"
STATUS_WAITING = "대기"
STATUS_OPTIONAL = "선택"
STATUS_DONE = "완료"
STATUS_BLOCKED = "확인 필요"


@dataclass(frozen=True)
class GitFollowUpStep:
    step_id: str
    order: int
    title: str
    group: str
    status: str
    current_value: str
    reason: str
    next_action: str
    target_group: str
    target_page: str
    workload_count: int = 0
    estimated_runtime: str = "-"
    load_note: str = "-"
    restartable: bool = True


@dataclass(frozen=True)
class GitFollowUpSummary:
    project_id: int
    repo_head_hash: str | None
    db_sync_head_hash: str | None
    db_matches_head: bool | None
    total_commit_count: int
    total_file_count: int
    synced_commit_count: int = 0
    synced_file_count: int = 0
    latest_sync_commit_hash: str | None = None
    steps: list[GitFollowUpStep] = field(default_factory=list)

    @property
    def recommended_steps(self) -> list[GitFollowUpStep]:
        return [step for step in self.steps if step.group == GROUP_RECOMMENDED]

    @property
    def later_steps(self) -> list[GitFollowUpStep]:
        return [step for step in self.steps if step.group == GROUP_LATER]


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "-"


def _safe_source_status(db: Session, project) -> tuple[SourceIndexStatus | None, str | None]:
    try:
        return get_source_index_status(db, project), None
    except Exception as exc:
        return None, str(exc)


def _safe_changed_source_count(db: Session, project, source_status: SourceIndexStatus | None) -> int:
    if source_status is None or not source_status.latest_indexed_head_hash:
        return 0
    try:
        return len(get_changed_source_files_since_latest_index(db, project))
    except Exception:
        return 0


def _safe_graph_freshness(db: Session, project_id: int) -> Neo4jGraphFreshness:
    try:
        return get_project_graph_freshness(db, project_id)
    except Exception as exc:
        return Neo4jGraphFreshness("failed", f"Knowledge Graph 상태 확인 실패: {exc}", errors=[str(exc)])


def _source_index_step(
    source_status: SourceIndexStatus | None,
    source_error: str | None,
    changed_source_count: int,
) -> GitFollowUpStep:
    if source_status is None:
        return GitFollowUpStep(
            "source_index",
            1,
            "현재 소스 근거 갱신",
            GROUP_RECOMMENDED,
            STATUS_BLOCKED,
            source_error or "source index 상태 확인 실패",
            "RAG/Project Chat이 최신 파일을 읽으려면 source index 상태를 먼저 확인해야 합니다.",
            "RAG 검색에서 현재 소스 다시 읽기를 실행하세요.",
            "분석 실행",
            "RAG 검색",
            load_note="파일 스캔 작업입니다. LLM 호출은 하지 않습니다.",
        )

    if source_status.source_chunk_count == 0:
        return GitFollowUpStep(
            "source_index",
            1,
            "현재 소스 근거 갱신",
            GROUP_RECOMMENDED,
            STATUS_RECOMMENDED,
            "source_file chunks=0",
            "Project Chat과 RAG 검색이 사용할 현재 소스 근거가 아직 없습니다.",
            "RAG 검색에서 현재 소스 다시 읽기를 실행하세요.",
            "분석 실행",
            "RAG 검색",
            estimated_runtime="저장소 크기에 따름",
            load_note="파일 스캔 작업입니다. embedding은 별도 선택입니다.",
        )

    if source_status.needs_reindex:
        workload = changed_source_count or source_status.head_mismatch_chunk_count or source_status.stale_chunk_count
        estimate = estimate_runtime(workload, "source_index").label if workload else "변경 범위에 따름"
        return GitFollowUpStep(
            "source_index",
            1,
            "현재 소스 근거 갱신",
            GROUP_RECOMMENDED,
            STATUS_RECOMMENDED,
            (
                f"chunks={source_status.source_chunk_count}, "
                f"stale={source_status.stale_chunk_count}, invalid={source_status.invalid_chunk_count}, "
                f"changed_files={changed_source_count}"
            ),
            "Git Sync 이후 현재 소스 근거가 Repo HEAD와 어긋난 상태입니다.",
            "Project Chat 또는 RAG 검색에서 최신 변경분 반영을 실행하세요.",
            "분석 실행",
            "Project Chat",
            workload,
            estimate,
            "파일 스캔 작업입니다. embedding은 별도 선택입니다.",
        )

    return GitFollowUpStep(
        "source_index",
        1,
        "현재 소스 근거 갱신",
        GROUP_LATER,
        STATUS_DONE,
        f"chunks={source_status.source_chunk_count}, head={_short_hash(source_status.latest_indexed_head_hash)}",
        "현재 source_file 근거가 Repo HEAD 기준으로 사용할 수 있습니다.",
        "새 Git Sync 이후 stale 표시가 나오면 최신 변경분 반영을 실행하세요.",
        "분석 실행",
        "Project Chat",
        restartable=False,
    )


def _embedding_step(source_status: SourceIndexStatus | None) -> GitFollowUpStep:
    if source_status is None:
        return GitFollowUpStep(
            "embedding",
            2,
            "검색 준비 생성",
            GROUP_RECOMMENDED,
            STATUS_WAITING,
            "source index 확인 필요",
            "embedding 대상 chunk 수를 계산하려면 source index 상태가 먼저 필요합니다.",
            "현재 소스 근거 갱신을 먼저 확인하세요.",
            "분석 실행",
            "RAG 검색",
            load_note="embedding provider를 호출할 수 있습니다.",
        )

    if source_status.needs_reindex or source_status.source_chunk_count == 0:
        return GitFollowUpStep(
            "embedding",
            2,
            "검색 준비 생성",
            GROUP_RECOMMENDED,
            STATUS_WAITING,
            f"missing={source_status.missing_embedding_count}",
            "먼저 현재 소스 근거를 Repo HEAD 기준으로 맞춰야 합니다.",
            "소스 근거 갱신 후 RAG 검색에서 검색 준비를 실행하세요.",
            "분석 실행",
            "RAG 검색",
            source_status.missing_embedding_count,
            estimate_runtime(source_status.missing_embedding_count, "embedding").label,
            "embedding provider를 호출할 수 있습니다. local model 부하를 확인하세요.",
        )

    if source_status.missing_embedding_count > 0:
        return GitFollowUpStep(
            "embedding",
            2,
            "검색 준비 생성",
            GROUP_RECOMMENDED,
            STATUS_RECOMMENDED,
            f"missing={source_status.missing_embedding_count}, vectors={source_status.source_vector_count}",
            "검색 준비가 없는 source chunk가 있어 RAG/Project Chat 검색 품질이 떨어질 수 있습니다.",
            "RAG 검색에서 검색 준비 생성을 실행하세요.",
            "분석 실행",
            "RAG 검색",
            source_status.missing_embedding_count,
            estimate_runtime(source_status.missing_embedding_count, "embedding").label,
            "embedding provider를 호출할 수 있습니다. 비용과 local model 부하를 확인하세요.",
        )

    return GitFollowUpStep(
        "embedding",
        2,
        "검색 준비 생성",
        GROUP_LATER,
        STATUS_DONE,
        f"vectors={source_status.source_vector_count}, missing=0",
        "현재 source chunk에 대한 검색 준비가 완료되어 있습니다.",
        "새 chunk가 생기면 RAG 검색에서 검색 준비를 다시 실행하세요.",
        "분석 실행",
        "RAG 검색",
        restartable=False,
    )


def _mapping_step(commit_count: int, pending_count: int, failed_count: int) -> GitFollowUpStep:
    workload = pending_count
    if commit_count == 0:
        return GitFollowUpStep(
            "mapping",
            3,
            "Mapping 분석",
            GROUP_RECOMMENDED,
            STATUS_WAITING,
            "commits=0",
            "Mapping을 실행하려면 먼저 Git commit 수집이 필요합니다.",
            "Git 동기화에서 전체 수집 또는 증분 동기화를 실행하세요.",
            "프로젝트 설정",
            "Git 동기화",
            restartable=False,
        )

    if workload > 0:
        return GitFollowUpStep(
            "mapping",
            3,
            "Mapping 분석",
            GROUP_RECOMMENDED,
            STATUS_RECOMMENDED,
            f"pending={pending_count}, failed={failed_count}, total={commit_count}",
            "새 commit 또는 실패 commit은 프로그램 연결 분석이 필요합니다.",
            "Mapping에서 미완료 커밋 전체 분석을 실행하세요.",
            "분석 실행",
            "Mapping",
            workload,
            estimate_runtime(workload, "mapping").label,
            "LLM provider를 호출할 수 있습니다. batch 크기와 local model 부하를 확인하세요.",
        )

    return GitFollowUpStep(
        "mapping",
        3,
        "Mapping 분석",
        GROUP_LATER,
        STATUS_DONE,
        f"completed={commit_count}/{commit_count}",
        "현재 수집된 commit의 Mapping 분석이 완료되어 있습니다.",
        "새 commit을 동기화하거나 품질 점검에서 경고가 나오면 Mapping을 다시 확인하세요.",
        "분석 실행",
        "Mapping",
        restartable=False,
    )


def _risk_step(commit_count: int, pending_mapping_count: int, risk_count: int, synced_commit_count: int) -> GitFollowUpStep:
    if commit_count == 0:
        status = STATUS_WAITING
        reason = "Risk Analysis는 Git commit과 프로그램 데이터가 있어야 의미가 있습니다."
        action = "Git 동기화와 Mapping을 먼저 완료하세요."
        group = GROUP_RECOMMENDED
    elif pending_mapping_count > 0:
        status = STATUS_WAITING
        reason = "Risk Analysis는 Mapping 결과를 근거로 사용하므로 미완료 Mapping을 먼저 줄이는 편이 좋습니다."
        action = "Mapping 완료 후 Risk Analysis를 실행하세요."
        group = GROUP_RECOMMENDED
    elif risk_count == 0 or synced_commit_count > 0:
        status = STATUS_RECOMMENDED
        reason = "Mapping 기준이 준비되었으므로 리스크를 다시 계산할 차례입니다."
        action = "Risk Analysis 화면에서 분석을 실행하세요."
        group = GROUP_RECOMMENDED
    else:
        status = STATUS_OPTIONAL
        reason = "저장된 Risk Finding이 있어 즉시 필수 단계는 아닙니다."
        action = "새 commit이나 Mapping 변경 후 Risk Analysis를 다시 실행하세요."
        group = GROUP_LATER

    return GitFollowUpStep(
        "risk_analysis",
        4,
        "Risk Analysis 재계산",
        group,
        status,
        f"risk_findings={risk_count}, synced_commits={synced_commit_count}",
        reason,
        action,
        "분석 실행",
        "Risk Analysis",
        max(1, commit_count),
        estimate_runtime(max(1, commit_count), "risk_analysis").label,
        "규칙 기반 계산입니다. LLM 호출은 하지 않습니다.",
        restartable=status != STATUS_OPTIONAL,
    )


def _graph_step(graph: Neo4jGraphFreshness, pending_mapping_count: int, synced_commit_count: int) -> GitFollowUpStep:
    graph_value = (
        f"status={graph.status}, repo={_short_hash(graph.repo_head_hash)}, "
        f"graph={_short_hash(graph.graph_sync_head_hash)}, nodes={graph.node_count}, edges={graph.edge_count}"
    )
    if graph.status == "latest":
        return GitFollowUpStep(
            "knowledge_graph",
            5,
            "Knowledge Graph 갱신",
            GROUP_LATER,
            STATUS_DONE,
            graph_value,
            "Neo4j graph가 현재 Git/DB 기준과 일치합니다.",
            "새 Git Sync나 Mapping 변경 후 갱신 필요가 표시되면 다시 실행하세요.",
            "분석 결과",
            "Knowledge Graph",
            restartable=False,
        )

    if graph.status == "skipped":
        return GitFollowUpStep(
            "knowledge_graph",
            5,
            "Knowledge Graph 갱신",
            GROUP_LATER,
            STATUS_OPTIONAL,
            graph.summary,
            "Neo4j가 꺼져 있으면 graph read model은 갱신하지 않습니다.",
            "GraphRAG/관계 탐색을 사용할 때 Neo4j를 켠 뒤 Knowledge Graph를 동기화하세요.",
            "분석 결과",
            "Knowledge Graph",
            load_note="Neo4j service가 필요합니다.",
        )

    if pending_mapping_count > 0:
        status = STATUS_WAITING
        reason = "프로그램-커밋 Mapping이 graph edge에 반영되므로 Mapping 완료 후 갱신하는 편이 좋습니다."
        action = "Mapping 완료 후 Knowledge Graph에서 최신 변경분만 Neo4j 반영을 실행하세요."
    else:
        status = STATUS_RECOMMENDED
        reason = graph.summary or "Git Sync 이후 Knowledge Graph 갱신이 필요합니다."
        action = "Knowledge Graph에서 최신 변경분만 Neo4j 반영을 실행하세요."

    workload = max(1, synced_commit_count)
    return GitFollowUpStep(
        "knowledge_graph",
        5,
        "Knowledge Graph 갱신",
        GROUP_RECOMMENDED,
        status,
        graph_value,
        reason,
        action,
        "분석 결과",
        "Knowledge Graph",
        workload,
        estimate_runtime(workload, "graph_sync").label,
        "Neo4j write 작업입니다. 대형 저장소에서는 전체 재동기화보다 증분 동기화를 먼저 사용하세요.",
    )


def build_git_sync_follow_up(
    db: Session,
    project_id: int,
    sync_result: GitSyncResult | None = None,
) -> GitFollowUpSummary:
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError("프로젝트를 찾을 수 없습니다.")

    repo_status: GitRepositoryStatus = get_repository_status(project)
    commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()
    file_count = (
        db.query(CommitFile)
        .join(GitCommit, CommitFile.commit_id == GitCommit.id)
        .filter(GitCommit.project_id == project_id)
        .count()
    )
    mapping_completed_count = (
        db.query(GitCommit)
        .filter(GitCommit.project_id == project_id, GitCommit.mapping_analysis_status == "completed")
        .count()
    )
    mapping_failed_count = (
        db.query(GitCommit)
        .filter(GitCommit.project_id == project_id, GitCommit.mapping_analysis_status == "failed")
        .count()
    )
    mapping_pending_count = max(0, commit_count - mapping_completed_count)
    program_count = db.query(Program).filter(Program.project_id == project_id).count()
    risk_count = db.query(RiskFinding).filter(RiskFinding.project_id == project_id).count()
    source_status, source_error = _safe_source_status(db, project)
    changed_source_count = _safe_changed_source_count(db, project, source_status)
    graph = _safe_graph_freshness(db, project_id)
    synced_commit_count = int(sync_result.saved_commit_count if sync_result else 0)
    synced_file_count = int(sync_result.saved_file_count if sync_result else 0)

    steps = [
        _source_index_step(source_status, source_error, changed_source_count),
        _embedding_step(source_status),
        _mapping_step(commit_count, mapping_pending_count, mapping_failed_count),
        _risk_step(commit_count if program_count else 0, mapping_pending_count, risk_count, synced_commit_count),
        _graph_step(graph, mapping_pending_count, synced_commit_count),
    ]

    return GitFollowUpSummary(
        project_id=project_id,
        repo_head_hash=repo_status.head_hash,
        db_sync_head_hash=repo_status.db_last_synced_commit_hash,
        db_matches_head=repo_status.db_matches_head,
        total_commit_count=commit_count,
        total_file_count=file_count,
        synced_commit_count=synced_commit_count,
        synced_file_count=synced_file_count,
        latest_sync_commit_hash=sync_result.latest_commit_hash if sync_result else project.last_synced_commit_hash,
        steps=sorted(steps, key=lambda step: step.order),
    )
