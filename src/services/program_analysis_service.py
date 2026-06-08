from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping


STATUS_IMPLEMENTED = "구현됨"
STATUS_PARTIAL = "일부구현"
STATUS_UNKNOWN = "판단불가"
STATUS_NO_MAPPING = "매핑없음"


@dataclass
class ProgramOption:
    program_db_id: int
    program_id: str | None
    program_name: str
    developer: str
    status: str
    module: str | None
    screen_name: str | None


@dataclass
class RelatedCommitRow:
    mapping_id: int
    commit_db_id: int | None
    commit_hash: str
    commit_message: str
    author_name: str
    committed_at: datetime | None
    relevance_score: float
    implementation_status: str
    reason: str


@dataclass
class CommitFileDetail:
    file_path: str
    change_type: str | None
    diff_snippet: str


@dataclass
class DeveloperContribution:
    developer: str
    commit_count: int
    contribution_ratio: float


@dataclass
class ProgramActivitySummary:
    first_commit_at: datetime | None
    last_commit_at: datetime | None
    recent_30d_commit_count: int
    recent_90d_commit_count: int


@dataclass
class ProgramRiskSummary:
    risk_level: str
    risk_reasons: list[str] = field(default_factory=list)

    @property
    def is_risk(self) -> bool:
        return self.risk_level != "LOW" or bool(self.risk_reasons)


@dataclass
class ProgramDetailAnalysis:
    program: Program
    developer: str
    ai_progress_rate: float
    related_commit_count: int
    implemented_count: int
    partial_count: int
    unknown_count: int
    commit_rows: list[RelatedCommitRow]
    developer_contributions: list[DeveloperContribution]
    activity: ProgramActivitySummary
    risk: ProgramRiskSummary


def normalize_implementation_status(status: str | None) -> str:
    value = (status or "").strip().lower()
    if not value:
        return STATUS_UNKNOWN
    if value in {"구현됨", "구현완료", "implemented", "done", "complete", "completed"}:
        return STATUS_IMPLEMENTED
    if value in {"일부구현", "부분구현", "partial", "partially_implemented"}:
        return STATUS_PARTIAL
    if value in {"판단불가", "unknown", "unclear", "not_applicable"}:
        return STATUS_UNKNOWN
    return status.strip()


def _developer_name(program: Program) -> str:
    if program.assigned_developer and program.assigned_developer.developer_name:
        return program.assigned_developer.developer_name
    return program.developer or "미지정"


def _ai_progress(statuses: list[str]) -> float:
    if STATUS_IMPLEMENTED in statuses:
        return 100.0
    if STATUS_PARTIAL in statuses:
        return 50.0
    return 0.0


def _risk_summary(program: Program, ai_progress_rate: float, related_commit_count: int, statuses: list[str]) -> ProgramRiskSummary:
    reasons = []
    today = date.today()
    if program.planned_end_date and program.planned_end_date < today and ai_progress_rate < 100:
        reasons.append("계획 종료일 경과 + AI 진척도 미완료")
    if related_commit_count == 0:
        reasons.append("관련 커밋 없음")
    if statuses and all(status == STATUS_UNKNOWN for status in statuses):
        reasons.append("판단불가만 존재")

    if any(reason.startswith("계획 종료일") for reason in reasons):
        level = "HIGH"
    elif "관련 커밋 없음" in reasons:
        level = "MEDIUM"
    elif "판단불가만 존재" in reasons:
        level = "MEDIUM"
    else:
        level = "LOW"

    return ProgramRiskSummary(risk_level=level, risk_reasons=reasons)


def list_program_options(db: Session, project_id: int) -> list[ProgramOption]:
    programs = (
        db.query(Program)
        .options(joinedload(Program.assigned_developer))
        .filter(Program.project_id == project_id)
        .order_by(Program.program_name)
        .all()
    )
    return [
        ProgramOption(
            program_db_id=program.id,
            program_id=program.program_id,
            program_name=program.program_name,
            developer=_developer_name(program),
            status=program.status or "미지정",
            module=program.module,
            screen_name=program.screen_name,
        )
        for program in programs
    ]


def get_program_detail_analysis(db: Session, program_db_id: int) -> ProgramDetailAnalysis:
    program = (
        db.query(Program)
        .options(
            joinedload(Program.assigned_developer),
            joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit).joinedload(GitCommit.files),
        )
        .filter(Program.id == program_db_id)
        .one()
    )

    mappings = sorted(
        [mapping for mapping in (program.mappings or []) if mapping.is_related is True],
        key=lambda mapping: float(mapping.relevance_score or 0),
        reverse=True,
    )
    statuses = [normalize_implementation_status(mapping.implementation_status) for mapping in mappings]
    ai_progress_rate = _ai_progress(statuses)

    commit_rows = []
    commit_dates = []
    authors = []
    for mapping in mappings:
        commit = mapping.commit
        if commit and commit.committed_at:
            commit_dates.append(commit.committed_at)
        author_name = (commit.author_name or commit.author or "미상") if commit else "미상"
        if commit:
            authors.append(author_name)
        commit_rows.append(
            RelatedCommitRow(
                mapping_id=mapping.id,
                commit_db_id=commit.id if commit else None,
                commit_hash=commit.commit_hash[:12] if commit else "",
                commit_message=(commit.message or "").splitlines()[0] if commit else "",
                author_name=author_name,
                committed_at=commit.committed_at if commit else None,
                relevance_score=float(mapping.relevance_score or 0),
                implementation_status=normalize_implementation_status(mapping.implementation_status),
                reason=mapping.reason or "",
            )
        )

    total_commits = len(authors)
    author_counts = Counter(authors)
    developer_contributions = [
        DeveloperContribution(
            developer=developer,
            commit_count=count,
            contribution_ratio=round((count / total_commits) * 100, 1) if total_commits else 0.0,
        )
        for developer, count in author_counts.most_common()
    ]

    now = datetime.now(timezone.utc)
    recent_30d = now - timedelta(days=30)
    recent_90d = now - timedelta(days=90)
    activity = ProgramActivitySummary(
        first_commit_at=min(commit_dates) if commit_dates else None,
        last_commit_at=max(commit_dates) if commit_dates else None,
        recent_30d_commit_count=sum(1 for value in commit_dates if value >= recent_30d),
        recent_90d_commit_count=sum(1 for value in commit_dates if value >= recent_90d),
    )

    risk = _risk_summary(program, ai_progress_rate, len(commit_rows), statuses)

    return ProgramDetailAnalysis(
        program=program,
        developer=_developer_name(program),
        ai_progress_rate=ai_progress_rate,
        related_commit_count=len(commit_rows),
        implemented_count=statuses.count(STATUS_IMPLEMENTED),
        partial_count=statuses.count(STATUS_PARTIAL),
        unknown_count=statuses.count(STATUS_UNKNOWN),
        commit_rows=commit_rows,
        developer_contributions=developer_contributions,
        activity=activity,
        risk=risk,
    )


def get_commit_file_details(db: Session, program_db_id: int, commit_hash_prefix: str, max_diff_chars: int = 1200) -> tuple[str, list[CommitFileDetail], str]:
    mapping = (
        db.query(ProgramCommitMapping)
        .options(joinedload(ProgramCommitMapping.commit).joinedload(GitCommit.files))
        .join(GitCommit, ProgramCommitMapping.commit_id == GitCommit.id)
        .filter(
            ProgramCommitMapping.program_id == program_db_id,
            GitCommit.commit_hash.startswith(commit_hash_prefix),
        )
        .order_by(ProgramCommitMapping.relevance_score.desc().nullslast())
        .first()
    )
    if mapping is None or mapping.commit is None:
        return "", [], ""

    commit = mapping.commit
    details = [
        CommitFileDetail(
            file_path=file.file_path,
            change_type=file.change_type,
            diff_snippet=(file.diff_text or "")[:max_diff_chars],
        )
        for file in commit.files
    ]
    return commit.message or "", details, mapping.reason or ""
