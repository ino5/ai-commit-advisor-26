from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Protocol

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, Program, ProgramCommitMapping, RiskFinding
from src.services.llm_client import LLMClient
from src.services.resource_metrics_service import ProgramResourceMetric, ResourceMetricsSummary


@dataclass(frozen=True)
class RadarEvidence:
    label: str
    value: str


@dataclass(frozen=True)
class RadarItem:
    rank: int
    program_db_id: int
    program_id: str | None
    program_name: str
    developer: str
    priority_score: float
    priority_level: str
    recommended_action: str
    reasons: list[str]
    evidence: list[RadarEvidence]
    related_commits: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResourceRadar:
    project_id: int
    generated_on: date
    items: list[RadarItem]
    interpretation_note: str


@dataclass(frozen=True)
class PLBriefing:
    text: str
    provider: str
    used_llm: bool
    raw: dict


class BriefingLLM(Protocol):
    provider: str

    def generate(self, prompt: str):
        ...


def _priority_level(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def _risk_findings_by_program(db: Session, project_id: int) -> dict[int, list[RiskFinding]]:
    findings = (
        db.query(RiskFinding)
        .filter(RiskFinding.project_id == project_id, RiskFinding.resolved_yn == "N")
        .order_by(RiskFinding.risk_level.desc(), RiskFinding.id.desc())
        .all()
    )
    grouped: dict[int, list[RiskFinding]] = {}
    for finding in findings:
        grouped.setdefault(int(finding.program_id), []).append(finding)
    return grouped


def _related_commit_messages(db: Session, program_ids: list[int], limit_per_program: int = 3) -> dict[int, list[str]]:
    if not program_ids:
        return {}
    programs = (
        db.query(Program)
        .options(joinedload(Program.mappings).joinedload(ProgramCommitMapping.commit))
        .filter(Program.id.in_(program_ids))
        .all()
    )
    result: dict[int, list[str]] = {}
    for program in programs:
        related = [
            mapping
            for mapping in (program.mappings or [])
            if mapping.is_related is True and isinstance(mapping.commit, GitCommit)
        ]
        related.sort(key=lambda mapping: mapping.relevance_score or 0, reverse=True)
        result[int(program.id)] = [
            f"{mapping.commit.commit_hash[:12]} {mapping.commit.message or ''}".strip()
            for mapping in related[:limit_per_program]
        ]
    return result


def _recommended_action(metric: ProgramResourceMetric, high_risk_count: int) -> str:
    if high_risk_count > 0 or metric.forecast_level == "DELAY_EXPECTED":
        return "담당자와 범위/일정 조정 필요 여부를 먼저 확인하세요."
    if metric.progress_gap >= 30:
        return "Program Detail에서 관련 commit과 구현상태 분석 근거를 검토하세요."
    if metric.difficulty_level == "HIGH" or metric.cross_program_commit_count > 0:
        return "AI Code Review와 Commit Impact로 변경 영향 범위를 확인하세요."
    if metric.related_commit_count == 0:
        return "Git 동기화 상태와 실제 구현 착수 여부를 확인하세요."
    return "다음 주 점검 항목으로 유지하고 추세 변화를 확인하세요."


def _score_metric(metric: ProgramResourceMetric, high_risk_count: int) -> tuple[float, list[str], list[RadarEvidence]]:
    score = 0.0
    reasons: list[str] = []
    evidence = [
        RadarEvidence("담당자", metric.developer),
        RadarEvidence("계획/AI 진척도", f"{metric.plan_progress_rate:.1f}% / {metric.ai_progress_rate:.1f}%"),
        RadarEvidence("진척도 차이", f"{metric.progress_gap:.1f}p"),
        RadarEvidence("난이도", f"{metric.difficulty_label} ({metric.difficulty_score:.1f})"),
        RadarEvidence("미해결 리스크", str(metric.unresolved_risk_count)),
    ]

    if high_risk_count:
        score += 30 + min(high_risk_count * 8, 16)
        reasons.append(f"HIGH 리스크 {high_risk_count}건")
    elif metric.unresolved_risk_count:
        score += min(metric.unresolved_risk_count * 10, 25)
        reasons.append(f"미해결 리스크 {metric.unresolved_risk_count}건")

    if metric.forecast_level == "DELAY_EXPECTED":
        score += 28
        reasons.append(f"예상 종료일 기준 {metric.forecast_delay_days or 0}일 지연 가능성")
    elif metric.forecast_level == "AT_RISK":
        score += 16
        reasons.append("예상 종료일 주의")

    if metric.progress_gap > 0:
        score += min(metric.progress_gap * 0.45, 22)
        if metric.progress_gap >= 20:
            reasons.append(f"계획 대비 AI 진척도 차이 {metric.progress_gap:.1f}p")

    if metric.difficulty_level == "HIGH":
        score += 18
        reasons.append("난이도 높음")
    elif metric.difficulty_level == "MEDIUM":
        score += 8

    if metric.cross_program_commit_count:
        score += min(metric.cross_program_commit_count * 8, 16)
        reasons.append(f"여러 프로그램에 걸친 commit {metric.cross_program_commit_count}건")

    if metric.related_commit_count == 0 and metric.ai_progress_rate < 100:
        score += 18
        reasons.append("관련 commit 근거 없음")

    score += min(metric.workload_points * 0.15, 12)
    evidence.extend(
        [
            RadarEvidence("예상 상태", metric.forecast_label),
            RadarEvidence("예상 지연일", "-" if metric.forecast_delay_days is None else str(metric.forecast_delay_days)),
            RadarEvidence("관련 commit", str(metric.related_commit_count)),
            RadarEvidence("변경 파일", str(metric.touched_file_count)),
            RadarEvidence("cross-program commit", str(metric.cross_program_commit_count)),
        ]
    )
    if not reasons:
        reasons.append("현재는 추세 관찰 대상")
    return round(min(score, 100.0), 1), reasons, evidence


def build_ai_resource_radar(
    db: Session,
    resource_summary: ResourceMetricsSummary,
    *,
    limit: int = 5,
) -> ResourceRadar:
    findings_by_program = _risk_findings_by_program(db, resource_summary.project_id)
    related_commits = _related_commit_messages(
        db,
        [metric.program_db_id for metric in resource_summary.program_metrics],
    )
    scored: list[tuple[float, ProgramResourceMetric, list[str], list[RadarEvidence], int]] = []
    for metric in resource_summary.program_metrics:
        high_risk_count = sum(1 for finding in findings_by_program.get(metric.program_db_id, []) if finding.risk_level == "HIGH")
        score, reasons, evidence = _score_metric(metric, high_risk_count)
        scored.append((score, metric, reasons, evidence, high_risk_count))

    scored.sort(
        key=lambda row: (
            row[0],
            row[4],
            row[1].unresolved_risk_count,
            row[1].forecast_delay_days or 0,
            row[1].difficulty_score,
        ),
        reverse=True,
    )
    items = [
        RadarItem(
            rank=index + 1,
            program_db_id=metric.program_db_id,
            program_id=metric.program_id,
            program_name=metric.program_name,
            developer=metric.developer,
            priority_score=score,
            priority_level=_priority_level(score),
            recommended_action=_recommended_action(metric, high_risk_count),
            reasons=reasons,
            evidence=evidence,
            related_commits=related_commits.get(metric.program_db_id, []),
        )
        for index, (score, metric, reasons, evidence, high_risk_count) in enumerate(scored[:limit])
    ]
    return ResourceRadar(
        project_id=resource_summary.project_id,
        generated_on=date.today(),
        items=items,
        interpretation_note=(
            "AI Resource Radar는 AI mapping/progress, 리스크, 예상 지연, diff 규모, 담당자 부하 신호를 "
            "설명 가능한 점수로 합산한 PL 우선 검토 목록입니다."
        ),
    )


def _briefing_payload(radar: ResourceRadar) -> dict:
    return {
        "generated_on": radar.generated_on.isoformat(),
        "items": [
            {
                "rank": item.rank,
                "program_id": item.program_id,
                "program_name": item.program_name,
                "developer": item.developer,
                "priority_score": item.priority_score,
                "priority_level": item.priority_level,
                "reasons": item.reasons,
                "recommended_action": item.recommended_action,
                "evidence": [asdict(evidence) for evidence in item.evidence],
                "related_commits": item.related_commits,
            }
            for item in radar.items
        ],
    }


def _build_briefing_prompt(radar: ResourceRadar) -> str:
    payload = json.dumps(_briefing_payload(radar), ensure_ascii=False, indent=2)
    return f"""
다음 AI Resource Radar 근거를 바탕으로 PL 주간 점검 브리핑을 작성하세요.

규칙:
- 응답은 한국어로 작성하되, 제목에는 "한국어 브리핑" 같은 언어 설명을 넣지 마세요.
- 제목이 필요하면 "PL 주간 점검 브리핑"을 사용하세요.
- 근거에 없는 사실을 추가하지 마세요.
- 위험 단정 대신 "확인 필요", "주의", "우선 검토"처럼 보조 판단으로 표현하세요.
- JSON, code fence, 표가 아니라 Markdown 본문으로만 작성하세요.
- 1) 요약, 2) 우선 확인 항목, 3) 회의 질문, 4) 다음 액션 순서로 작성하세요.
- 각 항목에는 program_name 또는 program_id와 근거 숫자를 포함하세요.

AI Resource Radar JSON:
{payload}
""".strip()


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _json_list_lines(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    lines: list[str] = []
    for value in values:
        if isinstance(value, str):
            lines.append(f"- {value}")
        elif isinstance(value, dict):
            name = value.get("program_name") or value.get("program_id") or value.get("action") or "항목"
            details: list[str] = []
            for key in ("reasons", "reason", "action", "program_id"):
                item_value = value.get(key)
                if not item_value or item_value == name:
                    continue
                if isinstance(item_value, list):
                    details.append(", ".join(str(item) for item in item_value))
                else:
                    details.append(str(item_value))
            suffix = f": {'; '.join(details)}" if details else ""
            lines.append(f"- {name}{suffix}")
    return lines


def _normalize_llm_briefing_text(text: str) -> str:
    stripped = _strip_code_fence(text)
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return _clean_korean_briefing_text(stripped)
    if not isinstance(payload, dict):
        return _clean_korean_briefing_text(stripped)

    lines: list[str] = []
    summary = payload.get("요약") or payload.get("summary")
    if summary:
        lines.extend(["### 요약", str(summary).strip()])

    sections = (
        ("### 우선 확인 항목", payload.get("우선 확인 항목") or payload.get("priority_items")),
        ("### 회의 질문", payload.get("회의 질문") or payload.get("meeting_questions")),
        ("### 다음 액션", payload.get("다음 액션 순서") or payload.get("next_actions")),
    )
    for title, values in sections:
        section_lines = _json_list_lines(values)
        if section_lines:
            if lines:
                lines.append("")
            lines.append(title)
            lines.extend(section_lines)
    return _clean_korean_briefing_text("\n".join(lines).strip() or stripped)


def _clean_korean_briefing_text(text: str) -> str:
    replacements = {
        "PL 주간 점검용 한국어 브리핑": "PL 주간 점검 브리핑",
        "한국어 브리핑": "브리핑",
        "本周": "이번 주",
        "고도의 우선순위": "높은 우선순위",
        "고우한": "높은",
        "기반으로이번": "기반으로 이번",
    }
    cleaned = text
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    return cleaned


def _fallback_briefing(radar: ResourceRadar, provider: str, raw: dict | None = None) -> PLBriefing:
    if not radar.items:
        return PLBriefing(
            text="현재 AI Resource Radar에 표시할 우선 검토 항목이 없습니다. Git 동기화, Mapping, Risk Analysis 실행 상태를 먼저 확인하세요.",
            provider=provider,
            used_llm=False,
            raw=raw or {"fallback": "empty_radar"},
        )
    top = radar.items[:3]
    lines = ["### 요약", f"- 우선 검토 항목 {len(radar.items)}개가 감지되었습니다."]
    lines.append("### 우선 확인 항목")
    for item in top:
        lines.append(
            f"- {item.rank}. {item.program_name}({item.priority_level}, {item.priority_score}점): "
            f"{', '.join(item.reasons)}. {item.recommended_action}"
        )
    lines.append("### 회의 질문")
    for item in top:
        lines.append(f"- {item.program_name}: {item.reasons[0]}에 대해 담당자 확인이 끝났나요?")
    lines.append("### 다음 액션")
    lines.append("- Dashboard의 Radar 항목에서 Program Detail, Risk Analysis, AI Code Review 근거를 순서대로 확인하세요.")
    return PLBriefing(
        text="\n".join(lines),
        provider=provider,
        used_llm=False,
        raw=raw or {"fallback": "deterministic"},
    )


def generate_pl_briefing(radar: ResourceRadar, llm_client: BriefingLLM | None = None) -> PLBriefing:
    llm = llm_client or LLMClient(max_tokens=900)
    provider = getattr(llm, "provider", "unknown")
    if provider == "mock":
        return _fallback_briefing(radar, provider, {"provider": provider, "mode": "mock_fallback"})
    try:
        response = llm.generate(_build_briefing_prompt(radar))
    except Exception as exc:
        return _fallback_briefing(radar, provider, {"provider": provider, "error": str(exc)})

    text = _normalize_llm_briefing_text((getattr(response, "text", "") or "").strip())
    if not text:
        return _fallback_briefing(radar, provider, {"provider": provider, "empty_response": True})
    return PLBriefing(
        text=text,
        provider=provider,
        used_llm=True,
        raw=getattr(response, "raw", {"provider": provider}),
    )
