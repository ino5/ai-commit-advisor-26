from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping, RiskFinding
from src.services.resource_metrics_service import get_resource_metrics_summary


RISK_NO_RELATED_COMMITS = "NO_RELATED_COMMITS"
RISK_OVERDUE_AI_INCOMPLETE = "OVERDUE_AI_INCOMPLETE"
RISK_PROGRESS_GAP = "PROGRESS_GAP"
RISK_ALL_UNKNOWN = "ALL_UNKNOWN"
RISK_NO_RECENT_COMMITS = "NO_RECENT_COMMITS_14D"
RISK_ASSIGNEE_MISSING = "ASSIGNEE_MISSING"
RISK_FORECAST_DELAY = "FORECAST_DELAY"


@dataclass
class DetectedRisk:
    project_id: int
    program_db_id: int
    program_code: str | None
    program_name: str
    developer: str
    risk_type: str
    risk_level: str
    title: str
    description: str
    evidence: dict


@dataclass
class RiskRunResult:
    detected_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    auto_resolved_count: int = 0
    findings: list[RiskFinding] = field(default_factory=list)


def normalize_implementation_status(status: str | None) -> str:
    value = (status or "").strip().lower()
    if not value:
        return "판단불가"
    if value in {"구현됨", "구현완료", "implemented", "done", "completed", "complete"}:
        return "구현됨"
    if value in {"일부구현", "부분구현", "partial", "partially_implemented"}:
        return "일부구현"
    if value in {"판단불가", "unknown", "unclear", "not_applicable"}:
        return "판단불가"
    return status.strip()


def _developer_name(program: Program) -> str:
    if program.assigned_developer and program.assigned_developer.developer_name:
        return program.assigned_developer.developer_name
    return program.developer or "미지정"


def _assignee_missing(program: Program) -> bool:
    names = {
        (program.developer or "").strip().lower(),
        (program.developer_id or "").strip().lower(),
        (_developer_name(program) or "").strip().lower(),
    }
    unclear_values = {"", "미지정", "unknown", "none", "null", "-", "미상"}
    return all(value in unclear_values for value in names)


def _ai_progress(statuses: list[str]) -> float:
    if "구현됨" in statuses:
        return 100.0
    if "일부구현" in statuses:
        return 50.0
    return 0.0


def _mapping_commits(mappings: list[ProgramCommitMapping]) -> list[GitCommit]:
    return [mapping.commit for mapping in mappings if mapping.commit is not None and mapping.is_related is True]


def _base_evidence(program: Program, mappings: list[ProgramCommitMapping]) -> dict:
    statuses = [normalize_implementation_status(mapping.implementation_status) for mapping in mappings]
    commits = _mapping_commits(mappings)
    ai_progress = _ai_progress(statuses)
    plan_progress = float(program.progress_rate or 0)
    last_commit_at = max((commit.committed_at for commit in commits if commit.committed_at), default=None)
    return {
        "program_id": program.program_id,
        "program_name": program.program_name,
        "developer": _developer_name(program),
        "planned_end_date": program.planned_end_date.isoformat() if program.planned_end_date else None,
        "plan_progress_rate": plan_progress,
        "ai_progress_rate": ai_progress,
        "progress_gap": plan_progress - ai_progress,
        "mapping_count": len(mappings),
        "related_commit_count": len(commits),
        "implementation_statuses": statuses,
        "last_related_commit_at": last_commit_at.isoformat() if last_commit_at else None,
        "assignee_missing": _assignee_missing(program),
    }


def _risk(
    program: Program,
    risk_type: str,
    risk_level: str,
    title: str,
    description: str,
    evidence: dict,
) -> DetectedRisk:
    return DetectedRisk(
        project_id=program.project_id,
        program_db_id=program.id,
        program_code=program.program_id,
        program_name=program.program_name,
        developer=evidence.get("developer") or "미지정",
        risk_type=risk_type,
        risk_level=risk_level,
        title=title,
        description=description,
        evidence=evidence,
    )


def detect_project_risks(db: Session, project_id: int) -> list[DetectedRisk]:
    programs = (
        db.query(Program)
        .options(
            joinedload(Program.assigned_developer),
            joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit),
        )
        .filter(Program.project_id == project_id)
        .order_by(Program.program_id, Program.program_name)
        .all()
    )
    today = date.today()
    recent_threshold = datetime.now(timezone.utc) - timedelta(days=14)
    risks: list[DetectedRisk] = []

    for program in programs:
        mappings = [mapping for mapping in (program.mappings or []) if mapping.is_related is True]
        statuses = [normalize_implementation_status(mapping.implementation_status) for mapping in mappings]
        related_commits = _mapping_commits(mappings)
        evidence = _base_evidence(program, mappings)
        ai_progress = float(evidence["ai_progress_rate"])
        progress_gap = float(evidence["progress_gap"])
        overdue = bool(program.planned_end_date and program.planned_end_date < today)
        no_related_commits = len(related_commits) == 0
        assignee_missing = bool(evidence["assignee_missing"])

        if no_related_commits:
            level = "HIGH" if overdue or assignee_missing else "MEDIUM"
            risks.append(
                _risk(
                    program,
                    RISK_NO_RELATED_COMMITS,
                    level,
                    "관련 커밋 없음",
                    "프로그램은 등록되어 있지만 관련 커밋 매핑 결과가 없습니다.",
                    evidence,
                )
            )

        if overdue and ai_progress < 100:
            level = "HIGH" if ai_progress < 50 else "MEDIUM"
            risks.append(
                _risk(
                    program,
                    RISK_OVERDUE_AI_INCOMPLETE,
                    level,
                    "계획 종료일 경과 후 AI 진척도 미완료",
                    "계획 종료일이 지났지만 AI 진척도가 100%에 도달하지 않았습니다.",
                    evidence,
                )
            )

        if progress_gap >= 30:
            risks.append(
                _risk(
                    program,
                    RISK_PROGRESS_GAP,
                    "MEDIUM",
                    "계획 대비 AI 진척도 차이 큼",
                    "계획 진척도와 AI 진척도 차이가 30 이상입니다.",
                    evidence,
                )
            )

        if mappings and all(status == "판단불가" for status in statuses):
            risks.append(
                _risk(
                    program,
                    RISK_ALL_UNKNOWN,
                    "MEDIUM",
                    "LLM 매핑 결과가 모두 판단불가",
                    "매핑 결과는 존재하지만 구현 상태가 모두 판단불가입니다.",
                    evidence,
                )
            )

        last_commit_at = max((commit.committed_at for commit in related_commits if commit.committed_at), default=None)
        if related_commits and (last_commit_at is None or last_commit_at < recent_threshold):
            risks.append(
                _risk(
                    program,
                    RISK_NO_RECENT_COMMITS,
                    "LOW",
                    "최근 14일 관련 커밋 없음",
                    "관련 커밋은 있으나 최근 14일 동안 추가 활동이 없습니다.",
                    evidence,
                )
            )

        if assignee_missing:
            level = "HIGH" if no_related_commits else "LOW"
            risks.append(
                _risk(
                    program,
                    RISK_ASSIGNEE_MISSING,
                    level,
                    "담당자 정보 불명확",
                    "담당자가 없거나 개발자 정보가 불명확합니다.",
                    evidence,
                )
            )

    resource_summary = get_resource_metrics_summary(db, project_id)
    for metric in resource_summary.program_metrics:
        if metric.forecast_level != "DELAY_EXPECTED" or metric.forecast_delay_days is None:
            continue
        program = next((item for item in programs if item.id == metric.program_db_id), None)
        if program is None:
            continue
        evidence = {
            "program_id": metric.program_id,
            "program_name": metric.program_name,
            "developer": metric.developer,
            "planned_end_date": program.planned_end_date.isoformat() if program.planned_end_date else None,
            "forecast_end_date": metric.forecast_end_date.isoformat() if metric.forecast_end_date else None,
            "forecast_delay_days": metric.forecast_delay_days,
            "forecast_confidence": metric.forecast_confidence,
            "forecast_confidence_label": metric.forecast_confidence_label,
            "ai_progress_rate": metric.ai_progress_rate,
            "plan_progress_rate": metric.plan_progress_rate,
            "related_commit_count": metric.related_commit_count,
        }
        risks.append(
            _risk(
                program,
                RISK_FORECAST_DELAY,
                "HIGH" if metric.forecast_delay_days >= 14 else "MEDIUM",
                "예상 종료일 기준 지연 가능성",
                "현재 AI 진척도와 관련 커밋 활동을 기준으로 계획 종료일 이후 완료될 가능성이 있습니다.",
                evidence,
            )
        )

    return risks


def run_risk_analysis(db: Session, project_id: int) -> RiskRunResult:
    detected = detect_project_risks(db, project_id)
    now = datetime.now(timezone.utc)
    result = RiskRunResult(detected_count=len(detected))

    current_keys = {(risk.program_db_id, risk.risk_type) for risk in detected}
    existing_unresolved = (
        db.query(RiskFinding)
        .filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N")
        .all()
    )
    existing_by_key = {(finding.program_id, finding.risk_type): finding for finding in existing_unresolved}

    for risk in detected:
        key = (risk.program_db_id, risk.risk_type)
        finding = existing_by_key.get(key)
        if finding is None:
            finding = RiskFinding(
                project_id=risk.project_id,
                program_id=risk.program_db_id,
                risk_type=risk.risk_type,
                risk_level=risk.risk_level,
                title=risk.title,
                description=risk.description,
                evidence=risk.evidence,
                detected_at=now,
                resolved_yn="N",
            )
            db.add(finding)
            result.created_count += 1
        else:
            finding.risk_level = risk.risk_level
            finding.title = risk.title
            finding.description = risk.description
            finding.evidence = risk.evidence
            finding.detected_at = now
            result.updated_count += 1
        result.findings.append(finding)

    for finding in existing_unresolved:
        if (finding.program_id, finding.risk_type) not in current_keys:
            finding.resolved_yn = "Y"
            result.auto_resolved_count += 1

    db.commit()
    return result


def get_unresolved_findings(db: Session, project_id: int, program_id: int | None = None) -> list[RiskFinding]:
    query = (
        db.query(RiskFinding)
        .filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N")
    )
    if program_id is not None:
        query = query.filter(RiskFinding.program_id == program_id)
    return query.order_by(RiskFinding.risk_level.desc(), RiskFinding.detected_at.desc()).all()


def resolve_findings(db: Session, finding_ids: list[int]) -> int:
    if not finding_ids:
        return 0
    updated = (
        db.query(RiskFinding)
        .filter(RiskFinding.id.in_(finding_ids), RiskFinding.resolved_yn == "N")
        .update({RiskFinding.resolved_yn: "Y"}, synchronize_session=False)
    )
    db.commit()
    return int(updated or 0)


def summarize_findings(findings: list[RiskFinding]) -> dict:
    level_counter = Counter(finding.risk_level for finding in findings)
    type_counter = Counter(finding.risk_type for finding in findings)
    developer_counter = Counter((finding.evidence or {}).get("developer") or "미지정" for finding in findings)
    return {
        "total": len(findings),
        "high": level_counter.get("HIGH", 0),
        "medium": level_counter.get("MEDIUM", 0),
        "low": level_counter.get("LOW", 0),
        "by_type": type_counter,
        "by_developer": developer_counter,
    }
