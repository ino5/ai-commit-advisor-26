from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from src.db.models import CommitFile, GitCommit, Program, ProgramCommitMapping


@dataclass
class CommitOption:
    commit_db_id: int
    commit_hash: str
    message: str
    author_name: str
    committed_at: datetime | None


@dataclass
class ImpactProgram:
    program_id: str | None
    program_name: str
    module: str | None
    screen_name: str | None
    developer: str
    relevance_score: float
    implementation_status: str
    reason: str


@dataclass
class ImpactFile:
    file_path: str
    change_type: str | None
    diff_snippet: str


@dataclass
class ImpactDeveloper:
    developer: str
    role: str
    commit_count: int
    contribution_ratio: float


@dataclass
class ImpactAnalysis:
    commit: GitCommit
    programs: list[ImpactProgram]
    files: list[ImpactFile]
    developers: list[ImpactDeveloper]
    impact_score: str
    impact_reasons: list[str] = field(default_factory=list)


def _developer_name(program: Program) -> str:
    if program.assigned_developer and program.assigned_developer.developer_name:
        return program.assigned_developer.developer_name
    return program.developer or "미지정"


def _normalize_status(status: str | None) -> str:
    value = (status or "").strip().lower()
    if value in {"구현됨", "구현완료", "implemented", "done", "completed", "complete"}:
        return "구현됨"
    if value in {"일부구현", "부분구현", "partial", "partially_implemented"}:
        return "일부구현"
    if value in {"판단불가", "unknown", "unclear", "not_applicable"}:
        return "판단불가"
    return (status or "판단불가").strip()


def list_commit_options(
    db: Session,
    project_id: int,
    message_keyword: str | None = None,
    author_keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 300,
) -> list[CommitOption]:
    query = db.query(GitCommit).filter(GitCommit.project_id == project_id)

    if message_keyword:
        query = query.filter(GitCommit.message.ilike(f"%{message_keyword}%"))
    if author_keyword:
        keyword = f"%{author_keyword}%"
        query = query.filter((GitCommit.author_name.ilike(keyword)) | (GitCommit.author.ilike(keyword)))
    if start_date:
        query = query.filter(GitCommit.committed_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(GitCommit.committed_at <= datetime.combine(end_date, datetime.max.time()))

    commits = query.order_by(GitCommit.committed_at.desc().nullslast(), GitCommit.id.desc()).limit(limit).all()
    return [
        CommitOption(
            commit_db_id=commit.id,
            commit_hash=commit.commit_hash,
            message=(commit.message or "").splitlines()[0],
            author_name=commit.author_name or commit.author or "미상",
            committed_at=commit.committed_at,
        )
        for commit in commits
    ]


def _recent_area_developers(db: Session, commit: GitCommit, files: list[CommitFile]) -> Counter:
    file_paths = [file.file_path for file in files]
    if not file_paths:
        return Counter()

    recent_since = datetime.now(timezone.utc) - timedelta(days=180)
    recent_commits = (
        db.query(GitCommit)
        .options(joinedload(GitCommit.files))
        .filter(GitCommit.project_id == commit.project_id)
        .filter(GitCommit.committed_at >= recent_since)
        .all()
    )

    area_counter: Counter = Counter()
    for recent_commit in recent_commits:
        author = recent_commit.author_name or recent_commit.author or "미상"
        recent_paths = {file.file_path for file in recent_commit.files}
        if any(_same_area(path, recent_paths) for path in file_paths):
            area_counter[author] += 1
    return area_counter


def _same_area(path: str, candidate_paths: set[str]) -> bool:
    path_parts = path.replace("\\", "/").split("/")
    area = "/".join(path_parts[:2]) if len(path_parts) >= 2 else path
    return any(candidate.replace("\\", "/").startswith(area) for candidate in candidate_paths)


def _impact_score(program_count: int, developer_count: int, file_count: int, max_relevance: float) -> tuple[str, list[str]]:
    reasons = []
    if program_count >= 5:
        reasons.append("영향 프로그램 5개 이상")
    if developer_count >= 4:
        reasons.append("영향 개발자 4명 이상")
    if file_count >= 10:
        reasons.append("변경 파일 10개 이상")
    if max_relevance >= 80:
        reasons.append("높은 관련도 매핑 존재")

    if program_count >= 5 or developer_count >= 4 or file_count >= 10 or max_relevance >= 85:
        return "HIGH", reasons
    if program_count >= 2 or developer_count >= 2 or file_count >= 4 or max_relevance >= 60:
        return "MEDIUM", reasons or ["중간 규모 영향 범위"]
    return "LOW", reasons or ["영향 범위 제한적"]


def get_commit_impact_analysis(db: Session, commit_db_id: int) -> ImpactAnalysis:
    commit = (
        db.query(GitCommit)
        .options(joinedload(GitCommit.files))
        .filter(GitCommit.id == commit_db_id)
        .one()
    )

    mappings = (
        db.query(ProgramCommitMapping)
        .options(joinedload(ProgramCommitMapping.program).joinedload(Program.assigned_developer))
        .filter(ProgramCommitMapping.commit_id == commit_db_id)
        .order_by(ProgramCommitMapping.relevance_score.desc().nullslast())
        .all()
    )

    programs = [
        ImpactProgram(
            program_id=mapping.program.program_id if mapping.program else None,
            program_name=mapping.program.program_name if mapping.program else "",
            module=mapping.program.module if mapping.program else None,
            screen_name=mapping.program.screen_name if mapping.program else None,
            developer=_developer_name(mapping.program) if mapping.program else "미지정",
            relevance_score=float(mapping.relevance_score or 0),
            implementation_status=_normalize_status(mapping.implementation_status),
            reason=mapping.reason or "",
        )
        for mapping in mappings
    ]

    files = [
        ImpactFile(
            file_path=file.file_path,
            change_type=file.change_type,
            diff_snippet=(file.diff_text or "")[:1200],
        )
        for file in commit.files
    ]

    developer_counter: Counter = Counter()
    for program in programs:
        developer_counter[program.developer] += 1

    recent_counter = _recent_area_developers(db, commit, list(commit.files))
    for developer, count in recent_counter.items():
        developer_counter[developer] += count

    total = sum(developer_counter.values())
    developers = [
        ImpactDeveloper(
            developer=developer,
            role="프로그램 담당자 / 최근 영역 작업자",
            commit_count=count,
            contribution_ratio=round((count / total) * 100, 1) if total else 0.0,
        )
        for developer, count in developer_counter.most_common()
    ]

    max_relevance = max((program.relevance_score for program in programs), default=0.0)
    score, reasons = _impact_score(len(programs), len(developers), len(files), max_relevance)
    return ImpactAnalysis(
        commit=commit,
        programs=programs,
        files=files,
        developers=developers,
        impact_score=score,
        impact_reasons=reasons,
    )
