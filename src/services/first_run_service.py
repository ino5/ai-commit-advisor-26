from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.models import DocumentChunk, GitCommit, Program, ProgramCommitMapping, Project, VectorItem
from src.rag.chunker import SOURCE_FILE_TYPE
from src.services.neo4j_graph_service import get_project_graph_freshness


@dataclass(frozen=True)
class FirstRunAction:
    area: str
    status: str
    current_value: str
    action: str
    target_group: str | None = None
    target_page: str | None = None
    help_text: str | None = None


def _action(
    area: str,
    status: str,
    current_value: str,
    action: str,
    target_group: str,
    target_page: str,
    help_text: str,
) -> FirstRunAction:
    return FirstRunAction(area, status, current_value, action, target_group, target_page, help_text)


def get_first_run_actions(db: Session, project_id: int | None) -> list[FirstRunAction]:
    if project_id is None:
        return [
            _action(
                "프로젝트",
                "필수",
                "선택된 프로젝트 없음",
                "프로젝트/Git 설정에서 프로젝트를 먼저 등록하세요.",
                "프로젝트 설정",
                "프로젝트/Git 설정",
                "프로젝트가 있어야 Git, 프로그램, AI 분석 결과를 같은 기준으로 묶을 수 있습니다.",
            )
        ]

    project = db.get(Project, project_id)
    if project is None:
        return [
            _action(
                "프로젝트",
                "필수",
                f"project_id={project_id}",
                "현재 프로젝트를 찾을 수 없습니다. 프로젝트/Git 설정에서 다시 선택하거나 등록하세요.",
                "프로젝트 설정",
                "프로젝트/Git 설정",
                "삭제되었거나 잘못된 URL project_id를 가리키는 상태입니다.",
            )
        ]

    program_count = db.query(Program).filter(Program.project_id == project_id).count()
    commit_count = db.query(GitCommit).filter(GitCommit.project_id == project_id).count()
    mapping_count = (
        db.query(ProgramCommitMapping)
        .join(Program, ProgramCommitMapping.program_id == Program.id)
        .filter(Program.project_id == project_id)
        .count()
    )
    source_chunk_count = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .count()
    )
    source_vector_count = (
        db.query(VectorItem)
        .join(DocumentChunk, VectorItem.chunk_id == DocumentChunk.id)
        .filter(DocumentChunk.project_id == project_id, DocumentChunk.source_type == SOURCE_FILE_TYPE)
        .count()
    )
    graph_freshness = get_project_graph_freshness(db, project_id)

    actions: list[FirstRunAction] = []
    if not project.git_repo_path:
        actions.append(
            _action(
                "Git 저장소",
                "필수",
                "경로 없음",
                "프로젝트/Git 설정에서 앱 서버가 접근할 Git 저장소 경로를 등록하세요.",
                "프로젝트 설정",
                "프로젝트/Git 설정",
                "로컬 Python 실행이면 내 PC 경로, 서버 실행이면 서버에 clone된 경로를 입력해야 합니다.",
            )
        )
    if program_count == 0:
        actions.append(
            _action(
                "프로그램",
                "필수",
                "0건",
                "프로그램 목록에서 현재 프로젝트의 프로그램을 직접 등록하거나 Excel로 업로드하세요.",
                "산출물 관리",
                "프로그램 목록",
                "프로그램이 있어야 Mapping, AI Progress, Risk Analysis가 업무 단위로 계산됩니다.",
            )
        )
    if commit_count == 0:
        actions.append(
            _action(
                "Git 커밋",
                "필수" if project.git_repo_path else "대기",
                "0건",
                "Git 동기화에서 commit과 변경 파일을 수집하세요.",
                "프로젝트 설정",
                "Git 동기화",
                "Git 저장소 경로가 먼저 등록되어야 commit 수집을 실행할 수 있습니다.",
            )
        )
    if commit_count > 0 and mapping_count == 0:
        actions.append(
            _action(
                "Mapping",
                "필수",
                f"0/{commit_count}건",
                "Mapping에서 대표 commit부터 분석해 프로그램-커밋 연결 근거를 만드세요.",
                "분석 실행",
                "Mapping",
                "Mapping이 있어야 AI Progress, Risk Analysis, Commit Impact가 더 의미 있는 근거를 갖습니다.",
            )
        )
    elif commit_count > 0 and mapping_count < commit_count:
        actions.append(
            _action(
                "Mapping",
                "권장",
                f"{mapping_count}/{commit_count}건",
                "Mapping에서 남은 미분석 commit을 순차적으로 처리하세요.",
                "분석 실행",
                "Mapping",
                "처음에는 selected commit 1개로 결과를 확인한 뒤 batch 범위를 늘리는 편이 안전합니다.",
            )
        )
    if project.git_repo_path and source_chunk_count == 0:
        actions.append(
            _action(
                "소스 근거",
                "권장",
                "source chunks=0",
                "Project Chat 또는 RAG 검색에서 현재 소스를 먼저 읽어 답변 근거를 준비하세요.",
                "분석 실행",
                "Project Chat",
                "현재 소스 근거가 있어야 Project Chat이 checkout 기준 코드 사실을 답할 수 있습니다.",
            )
        )
    elif source_chunk_count > 0 and source_vector_count < source_chunk_count:
        actions.append(
            _action(
                "검색 준비",
                "권장",
                f"vectors={source_vector_count}/{source_chunk_count}",
                "RAG 검색에서 검색 준비를 제한 수량으로 실행하세요.",
                "분석 실행",
                "RAG 검색",
                "Embedding provider/model/dimension이 맞아야 질문과 소스 근거가 연결됩니다.",
            )
        )
    if graph_freshness.status != "latest":
        actions.append(
            _action(
                "Knowledge Graph",
                "권장" if graph_freshness.status in {"skipped", "missing", "stale"} else "확인 필요",
                graph_freshness.summary,
                "Knowledge Graph에서 graph 상태를 확인하고 필요한 경우 전체 재동기화나 최신 변경분 반영을 실행하세요.",
                "분석 결과",
                "Knowledge Graph",
                "Neo4j를 사용하지 않는 환경이면 `NEO4J_ENABLED=false` 상태가 정상일 수 있습니다. GraphRAG를 보여야 하면 Neo4j를 켜세요.",
            )
        )

    if not actions:
        actions.append(
            _action(
                "운영 점검",
                "확인됨",
                "필수 준비 완료",
                "Dashboard와 AI 운영 현황에서 주간 점검 보고서와 품질 점검을 확인하세요.",
                "개요",
                "AI 운영 현황",
                "준비가 끝난 뒤에는 경고 항목과 근거 품질을 주기적으로 확인하면 됩니다.",
            )
        )
    return actions
