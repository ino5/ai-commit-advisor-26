from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import DocumentChunk, GitCommit, Program, ProgramCommitMapping, Project, VectorItem
from src.services import first_run_service
from src.services.first_run_service import get_first_run_actions
from src.services.neo4j_graph_service import Neo4jGraphFreshness


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def test_first_run_actions_handle_missing_project() -> None:
    init_db()

    with SessionLocal() as db:
        actions = get_first_run_actions(db, None)

    assert len(actions) == 1
    assert actions[0].area == "프로젝트"
    assert actions[0].status == "필수"
    assert actions[0].target_page == "프로젝트/Git 설정"


def test_first_run_actions_prioritize_empty_project_setup(monkeypatch) -> None:
    init_db()
    monkeypatch.setattr(
        first_run_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness("latest", "graph 최신"),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("first-run-empty"), git_repo_path=None)
        db.add(project)
        db.commit()

        try:
            actions = get_first_run_actions(db, project.id)
            areas = [action.area for action in actions]

            assert areas[:3] == ["Git 저장소", "프로그램", "Git 커밋"]
            assert actions[0].target_page == "프로젝트/Git 설정"
            assert actions[1].target_page == "프로그램 목록"
            assert actions[2].target_page == "Git 동기화"
        finally:
            db.delete(project)
            db.commit()


def test_first_run_actions_cover_mapping_source_vector_and_graph(monkeypatch) -> None:
    init_db()
    monkeypatch.setattr(
        first_run_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness("missing", "Neo4j graph를 아직 저장하지 않았습니다."),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("first-run-partial"), git_repo_path="C:/repo/demo")
        db.add(project)
        db.flush()
        program = Program(project_id=project.id, program_id=_unique("PRG"), program_name="Partial Program")
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="partial",
            author_name="tester",
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([program, commit])
        db.commit()

        try:
            actions = get_first_run_actions(db, project.id)
            areas = [action.area for action in actions]

            assert "Mapping" in areas
            assert "소스 근거" in areas
            assert "Knowledge Graph" in areas
            assert next(action for action in actions if action.area == "Mapping").target_page == "Mapping"
            assert next(action for action in actions if action.area == "소스 근거").target_page == "Project Chat"
        finally:
            db.delete(project)
            db.commit()


def test_first_run_actions_return_operational_check_when_ready(monkeypatch) -> None:
    init_db()
    monkeypatch.setattr(
        first_run_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness("latest", "graph 최신"),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("first-run-ready"), git_repo_path="C:/repo/demo")
        db.add(project)
        db.flush()
        program = Program(project_id=project.id, program_id=_unique("PRG"), program_name="Ready Program")
        commit = GitCommit(
            project_id=project.id,
            commit_hash=uuid.uuid4().hex,
            message="ready",
            author_name="tester",
            committed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
            mapping_analyzed_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        db.add_all([program, commit])
        db.flush()
        chunk = DocumentChunk(
            project_id=project.id,
            source_type="source_file",
            source_id="src/Ready.java",
            chunk_index=0,
            chunk_text="ready",
            raw_metadata={"file_path": "src/Ready.java"},
        )
        db.add_all(
            [
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=commit.id,
                    relevance_score=90,
                    is_related=True,
                    implementation_status="구현완료",
                    reason="ready mapping",
                ),
                chunk,
            ]
        )
        db.flush()
        db.add(VectorItem(chunk_id=chunk.id, embedding_model="mock", embedding=None))
        db.commit()

        try:
            actions = get_first_run_actions(db, project.id)

            assert len(actions) == 1
            assert actions[0].area == "운영 점검"
            assert actions[0].status == "확인됨"
            assert actions[0].target_page == "AI 운영 현황"
        finally:
            db.delete(project)
            db.commit()


def test_first_run_actions_use_analyzed_commits_instead_of_mapping_row_count(monkeypatch) -> None:
    init_db()
    monkeypatch.setattr(
        first_run_service,
        "get_project_graph_freshness",
        lambda db, project_id: Neo4jGraphFreshness("latest", "graph 최신"),
    )

    with SessionLocal() as db:
        project = Project(name=_unique("first-run-mapping-count"), git_repo_path="C:/repo/demo")
        db.add(project)
        db.flush()
        program = Program(project_id=project.id, program_id=_unique("PRG"), program_name="Analyzed Program")
        analyzed_at = datetime(2026, 6, 15, tzinfo=timezone.utc)
        commits = [
            GitCommit(
                project_id=project.id,
                commit_hash=uuid.uuid4().hex,
                message=f"analyzed-{index}",
                author_name="tester",
                committed_at=analyzed_at,
                mapping_analyzed_at=analyzed_at,
            )
            for index in range(2)
        ]
        db.add_all([program, *commits])
        db.flush()
        chunk = DocumentChunk(
            project_id=project.id,
            source_type="source_file",
            source_id="src/Analyzed.java",
            chunk_index=0,
            chunk_text="analyzed",
            raw_metadata={"file_path": "src/Analyzed.java"},
        )
        db.add_all(
            [
                ProgramCommitMapping(
                    program_id=program.id,
                    commit_id=commits[0].id,
                    relevance_score=90,
                    is_related=True,
                    implementation_status="구현완료",
                    reason="one related mapping for two analyzed commits",
                ),
                chunk,
            ]
        )
        db.flush()
        db.add(VectorItem(chunk_id=chunk.id, embedding_model="mock", embedding=None))
        db.commit()

        try:
            actions = get_first_run_actions(db, project.id)

            assert all(action.area != "Mapping" for action in actions)
            assert len(actions) == 1
            assert actions[0].area == "운영 점검"
        finally:
            db.delete(project)
            db.commit()
