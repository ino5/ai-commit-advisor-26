from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session, joinedload

from src.db.models import GitCommit, PLBriefingHistory, Program, ProgramCommitMapping, RiskFinding
from src.services.ai_invocation_service import record_ai_invocation
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
    model: str | None
    mode: str
    used_llm: bool
    raw: dict
    title: str = "PL 주간 점검 브리핑"
    summary: str = ""
    priority_items: list[dict] = field(default_factory=list)
    meeting_questions: list[str] = field(default_factory=list)
    next_actions: list[dict] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    prompt_length: int | None = None
    response_length: int | None = None
    validation_status: str | None = None
    fallback_reason: str | None = None
    repair_attempted: bool = False


@dataclass(frozen=True)
class PLBriefingHistoryRow:
    id: int
    generated_at: datetime
    provider: str
    model: str | None
    mode: str
    title: str
    summary: str | None
    rendered_text: str
    priority_items: list | None = None
    meeting_questions: list | None = None
    next_actions: list | None = None
    evidence_payload: dict | None = None
    raw_response: dict | None = None


class BriefingLLM(Protocol):
    provider: str
    model: str | None

    def generate(self, prompt: str):
        ...


def _priority_level(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def _format_progress(value: float | None, fallback: str) -> str:
    return f"{value:.1f}%" if value is not None else fallback


def _format_gap(value: float | None, fallback: str) -> str:
    return f"{value:.1f}p" if value is not None else fallback


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
    if metric.ai_progress_rate is None:
        return "구현상태 분석을 먼저 실행하거나 갱신해 AI 진척도를 확정하세요."
    if high_risk_count > 0 or metric.forecast_level == "DELAY_EXPECTED":
        return "담당자와 범위/일정 조정 필요 여부를 먼저 확인하세요."
    if metric.progress_gap is not None and metric.progress_gap >= 30:
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
        RadarEvidence(
            "계획/AI 진척도",
            f"{metric.plan_progress_rate:.1f}% / {_format_progress(metric.ai_progress_rate, metric.ai_progress_state_label)}",
        ),
        RadarEvidence("진척도 차이", _format_gap(metric.progress_gap, metric.ai_progress_state_label)),
        RadarEvidence("난이도", f"{metric.difficulty_label} ({metric.difficulty_score:.1f})"),
        RadarEvidence("미해결 리스크", str(metric.unresolved_risk_count)),
    ]

    if metric.ai_progress_rate is None:
        score += 18
        reasons.append(metric.ai_progress_state_label)

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

    if metric.progress_gap is not None and metric.progress_gap > 0:
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

    if metric.related_commit_count == 0 and (metric.ai_progress_rate is None or metric.ai_progress_rate < 100):
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
다음 AI Resource Radar 근거를 바탕으로 PL 주간 점검 브리핑 데이터를 작성하세요.

규칙:
- 응답은 JSON object 하나만 반환하세요. Markdown, code fence, 표를 쓰지 마세요.
- 모든 문장은 한국어로 작성하되, 제목에는 "한국어 브리핑" 같은 언어 설명을 넣지 마세요.
- title은 "PL 주간 점검 브리핑"으로 작성하세요.
- 근거에 없는 사실을 추가하지 마세요.
- 위험 단정 대신 "확인 필요", "주의", "우선 검토"처럼 보조 판단으로 표현하세요.
- priority_items와 next_actions에는 program_id 또는 program_name과 근거 숫자를 포함하세요.
- 다음 schema를 지키세요:
{{
  "title": "PL 주간 점검 브리핑",
  "summary": "한 문단 요약",
  "priority_items": [
    {{"program_id": "SMP-ORD-001", "program_name": "주문 접수", "reason": "미해결 리스크 2건, 예상 지연 53일", "owner": "김민수"}}
  ],
  "meeting_questions": ["회의에서 확인할 질문"],
  "next_actions": [
    {{"program_id": "SMP-ORD-001", "action": "담당자와 범위/일정 조정 필요 여부 확인"}}
  ]
}}

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


def _parse_structured_briefing(text: str) -> dict | None:
    stripped = _strip_code_fence(text)
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _validate_structured_briefing(payload: dict | None) -> list[str]:
    if not isinstance(payload, dict):
        return ["JSON object가 아닙니다."]
    errors: list[str] = []
    if not isinstance(payload.get("summary"), str) or not payload.get("summary", "").strip():
        errors.append("summary 문자열이 필요합니다.")
    for key in ("priority_items", "meeting_questions", "next_actions"):
        if not isinstance(payload.get(key), list):
            errors.append(f"{key} list가 필요합니다.")
    return errors


def _build_briefing_repair_prompt(raw_text: str, errors: list[str]) -> str:
    return f"""
아래 응답은 PL 주간 점검 브리핑 JSON schema를 지키지 못했습니다.
오류를 고쳐 JSON object 하나만 다시 반환하세요. Markdown, code fence, 표를 쓰지 마세요.

필수 schema:
{{
  "title": "PL 주간 점검 브리핑",
  "summary": "한 문단 요약",
  "priority_items": [{{"program_id": "프로그램 ID", "program_name": "프로그램명", "reason": "근거", "owner": "담당자"}}],
  "meeting_questions": ["회의 질문"],
  "next_actions": [{{"program_id": "프로그램 ID", "action": "다음 액션"}}]
}}

오류:
{json.dumps(errors, ensure_ascii=False)}

원본 응답:
{raw_text}
""".strip()


def _duration_ms(started_at: datetime, finished_at: datetime) -> int:
    return int((finished_at - started_at).total_seconds() * 1000)


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


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_clean_korean_briefing_text(str(value).strip()) for value in values if str(value).strip()]


def _normalize_dict_list(values: object) -> list[dict]:
    if not isinstance(values, list):
        return []
    result: list[dict] = []
    for value in values:
        if isinstance(value, dict):
            normalized: dict[str, str] = {}
            for key, item in value.items():
                if item is None:
                    continue
                if isinstance(item, list):
                    item_text = ", ".join(str(part).strip() for part in item if str(part).strip())
                else:
                    item_text = str(item).strip()
                if item_text:
                    normalized[str(key)] = _clean_korean_briefing_text(item_text)
            if normalized:
                result.append(normalized)
        elif str(value).strip():
            result.append({"text": _clean_korean_briefing_text(str(value).strip())})
    return result


def _briefing_from_payload(
    payload: dict,
    *,
    provider: str,
    model: str | None,
    used_llm: bool,
    raw: dict,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    prompt_length: int | None = None,
    response_length: int | None = None,
    validation_status: str | None = None,
    fallback_reason: str | None = None,
    repair_attempted: bool = False,
) -> PLBriefing:
    title = _clean_korean_briefing_text(str(payload.get("title") or "PL 주간 점검 브리핑").strip())
    summary = _clean_korean_briefing_text(str(payload.get("summary") or payload.get("요약") or "").strip())
    priority_items = _normalize_dict_list(payload.get("priority_items") or payload.get("우선 확인 항목"))
    meeting_questions = _normalize_string_list(payload.get("meeting_questions") or payload.get("회의 질문"))
    next_actions = _normalize_dict_list(payload.get("next_actions") or payload.get("다음 액션 순서"))
    text = render_pl_briefing_markdown(title, summary, priority_items, meeting_questions, next_actions)
    return PLBriefing(
        text=text,
        provider=provider,
        model=model,
        mode="LLM 생성" if used_llm else "규칙 기반 fallback",
        used_llm=used_llm,
        raw=raw,
        title=title,
        summary=summary,
        priority_items=priority_items,
        meeting_questions=meeting_questions,
        next_actions=next_actions,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=_duration_ms(started_at, finished_at) if started_at and finished_at else None,
        prompt_length=prompt_length,
        response_length=response_length,
        validation_status=validation_status,
        fallback_reason=fallback_reason,
        repair_attempted=repair_attempted,
    )


def render_pl_briefing_markdown(
    title: str,
    summary: str,
    priority_items: list[dict],
    meeting_questions: list[str],
    next_actions: list[dict],
) -> str:
    lines = [f"## {title}", "### 요약", summary or "우선 검토 항목을 확인하세요."]
    if priority_items:
        lines.extend(["", "### 우선 확인 항목"])
        for index, item in enumerate(priority_items, start=1):
            name = item.get("program_name") or item.get("program_id") or item.get("text") or "항목"
            reason = item.get("reason") or item.get("reasons") or item.get("근거")
            owner = item.get("owner") or item.get("developer") or item.get("담당자")
            detail = f" - {reason}" if reason else ""
            owner_text = f" (담당자: {owner})" if owner else ""
            lines.append(f"{index}. **{name}**{owner_text}{detail}")
    if meeting_questions:
        lines.extend(["", "### 회의 질문"])
        lines.extend(f"- {question}" for question in meeting_questions)
    if next_actions:
        lines.extend(["", "### 다음 액션"])
        for index, action in enumerate(next_actions, start=1):
            program = action.get("program_name") or action.get("program_id")
            action_text = action.get("action") or action.get("text") or str(action)
            prefix = f"**{program}**: " if program else ""
            lines.append(f"{index}. {prefix}{action_text}")
    return "\n".join(lines)


def _fallback_briefing(
    radar: ResourceRadar,
    provider: str,
    model: str | None,
    raw: dict | None = None,
    *,
    started_at: datetime | None = None,
    prompt_length: int | None = None,
    response_length: int | None = None,
    fallback_reason: str | None = None,
    repair_attempted: bool = False,
) -> PLBriefing:
    finished_at = datetime.now(timezone.utc)
    if not radar.items:
        return _briefing_from_payload(
            {
                "summary": "현재 AI Resource Radar에 표시할 우선 검토 항목이 없습니다. Git 동기화, Mapping, Risk Analysis 실행 상태를 먼저 확인하세요.",
                "priority_items": [],
                "meeting_questions": [],
                "next_actions": [],
            },
            provider=provider,
            model=model,
            used_llm=False,
            raw=raw or {"fallback": "empty_radar"},
            started_at=started_at,
            finished_at=finished_at,
            prompt_length=prompt_length,
            response_length=response_length,
            validation_status="fallback",
            fallback_reason=fallback_reason or "empty_radar",
            repair_attempted=repair_attempted,
        )
    top = radar.items[:3]
    payload = {
        "summary": f"우선 검토 항목 {len(radar.items)}개가 감지되었습니다.",
        "priority_items": [
            {
                "program_id": item.program_id,
                "program_name": item.program_name,
                "owner": item.developer,
                "reason": f"{', '.join(item.reasons)}. {item.recommended_action}",
            }
            for item in top
        ],
        "meeting_questions": [
            f"{item.program_name}: {item.reasons[0]}에 대해 담당자 확인이 끝났나요?" for item in top
        ],
        "next_actions": [
            {"action": "Dashboard의 Radar 항목에서 Program Detail, Risk Analysis, AI Code Review 근거를 순서대로 확인하세요."}
        ],
    }
    return _briefing_from_payload(
        payload,
        provider=provider,
        model=model,
        used_llm=False,
        raw=raw or {"fallback": "deterministic"},
        started_at=started_at,
        finished_at=finished_at,
        prompt_length=prompt_length,
        response_length=response_length,
        validation_status="fallback",
        fallback_reason=fallback_reason or str((raw or {}).get("fallback") or "deterministic"),
        repair_attempted=repair_attempted,
    )


def generate_pl_briefing(radar: ResourceRadar, llm_client: BriefingLLM | None = None) -> PLBriefing:
    llm = llm_client or LLMClient(max_tokens=900)
    provider = getattr(llm, "provider", "unknown")
    model = getattr(llm, "model", None)
    started_at = datetime.now(timezone.utc)
    if provider == "mock":
        return _fallback_briefing(
            radar,
            provider,
            model,
            {"provider": provider, "mode": "mock_fallback"},
            started_at=started_at,
            fallback_reason="mock_provider",
        )
    prompt = _build_briefing_prompt(radar)
    try:
        response = llm.generate(prompt)
    except Exception as exc:
        return _fallback_briefing(
            radar,
            provider,
            model,
            {"provider": provider, "error": str(exc)},
            started_at=started_at,
            prompt_length=len(prompt),
            fallback_reason=f"llm_error: {exc}",
        )

    raw_text = (getattr(response, "text", "") or "").strip()
    payload = _parse_structured_briefing(raw_text)
    errors = _validate_structured_briefing(payload)
    repair_attempted = False
    repair_raw = None
    repair_text = ""
    prompt_length = len(prompt)
    response_length = len(raw_text)
    validation_status = "valid"
    if errors:
        repair_attempted = True
        repair_prompt = _build_briefing_repair_prompt(raw_text, errors)
        prompt_length += len(repair_prompt)
        try:
            repair_response = llm.generate(repair_prompt)
            repair_text = (getattr(repair_response, "text", "") or "").strip()
            repair_raw = getattr(repair_response, "raw", None)
            response_length += len(repair_text)
            repaired_payload = _parse_structured_briefing(repair_text)
            repair_errors = _validate_structured_briefing(repaired_payload)
            if repair_errors:
                return _fallback_briefing(
                    radar,
                    provider,
                    model,
                    {
                        "provider": provider,
                        "validation_errors": errors,
                        "repair_errors": repair_errors,
                        "unstructured_response": raw_text,
                        "repair_response": repair_text,
                    },
                    started_at=started_at,
                    prompt_length=prompt_length,
                    response_length=response_length,
                    fallback_reason="structured_validation_failed",
                    repair_attempted=True,
                )
            payload = repaired_payload
            validation_status = "repaired"
        except Exception as exc:
            return _fallback_briefing(
                radar,
                provider,
                model,
                {
                    "provider": provider,
                    "validation_errors": errors,
                    "repair_error": str(exc),
                    "unstructured_response": raw_text,
                },
                started_at=started_at,
                prompt_length=prompt_length,
                response_length=response_length,
                fallback_reason=f"repair_error: {exc}",
                repair_attempted=True,
            )
    finished_at = datetime.now(timezone.utc)
    return _briefing_from_payload(
        payload or {},
        provider=provider,
        model=model,
        used_llm=True,
        raw={
            "llm": getattr(response, "raw", {"provider": provider}),
            "text": raw_text,
            "validation_status": validation_status,
            "repair_attempted": repair_attempted,
            "repair_raw": repair_raw,
            "repair_text": repair_text,
        },
        started_at=started_at,
        finished_at=finished_at,
        prompt_length=prompt_length,
        response_length=response_length,
        validation_status=validation_status,
        repair_attempted=repair_attempted,
    )


def save_pl_briefing(db: Session, radar: ResourceRadar, briefing: PLBriefing) -> PLBriefingHistoryRow:
    record = PLBriefingHistory(
        project_id=radar.project_id,
        provider=briefing.provider,
        model=briefing.model,
        mode=briefing.mode,
        title=briefing.title,
        summary=briefing.summary,
        priority_items=briefing.priority_items,
        meeting_questions=briefing.meeting_questions,
        next_actions=briefing.next_actions,
        rendered_text=briefing.text,
        evidence_payload=_briefing_payload(radar),
        raw_response=briefing.raw,
    )
    db.add(record)
    record_ai_invocation(
        db,
        project_id=radar.project_id,
        feature="pl_briefing",
        provider=briefing.provider,
        model=briefing.model,
        status="completed",
        mode=briefing.mode,
        fallback_used=not briefing.used_llm,
        validation_status=briefing.validation_status,
        started_at=briefing.started_at,
        finished_at=briefing.finished_at,
        duration_ms=briefing.duration_ms,
        prompt_length=briefing.prompt_length,
        response_length=briefing.response_length,
        error_message=briefing.fallback_reason if not briefing.used_llm else None,
        raw_metadata={
            "repair_attempted": briefing.repair_attempted,
            "fallback_reason": briefing.fallback_reason,
            "history_title": briefing.title,
        },
    )
    db.commit()
    db.refresh(record)
    return _briefing_history_row(record)


def get_latest_pl_briefing(db: Session, project_id: int) -> PLBriefingHistoryRow | None:
    record = (
        db.query(PLBriefingHistory)
        .filter(PLBriefingHistory.project_id == project_id)
        .order_by(PLBriefingHistory.generated_at.desc(), PLBriefingHistory.id.desc())
        .first()
    )
    return _briefing_history_row(record) if record else None


def get_pl_briefing_history(db: Session, project_id: int, limit: int = 5) -> list[PLBriefingHistoryRow]:
    records = (
        db.query(PLBriefingHistory)
        .filter(PLBriefingHistory.project_id == project_id)
        .order_by(PLBriefingHistory.generated_at.desc(), PLBriefingHistory.id.desc())
        .limit(limit)
        .all()
    )
    return [_briefing_history_row(record) for record in records]


def _briefing_history_row(record: PLBriefingHistory) -> PLBriefingHistoryRow:
    return PLBriefingHistoryRow(
        id=int(record.id),
        generated_at=record.generated_at,
        provider=record.provider,
        model=record.model,
        mode=record.mode,
        title=record.title,
        summary=record.summary,
        rendered_text=record.rendered_text,
        priority_items=record.priority_items,
        meeting_questions=record.meeting_questions,
        next_actions=record.next_actions,
        evidence_payload=record.evidence_payload,
        raw_response=record.raw_response,
    )
