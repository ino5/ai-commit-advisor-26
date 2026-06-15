from src.services.neo4j_graph_service import Neo4jGraphFreshness
from src.ui.project_chat_page import GRAPH_AWARE_QUESTION_TEMPLATES, _graph_template_status


def test_graph_question_templates_cover_project_commit_class_domain_relationships() -> None:
    questions = " ".join(template["question"] for template in GRAPH_AWARE_QUESTION_TEMPLATES)

    assert len(GRAPH_AWARE_QUESTION_TEMPLATES) >= 5
    assert "프로그램" in questions
    assert "commit" in questions
    assert "file" in questions
    assert "class" in questions
    assert "domain" in questions


def test_graph_template_status_enables_only_latest_graph() -> None:
    enabled, message = _graph_template_status(Neo4jGraphFreshness("latest", "최신"))

    assert enabled is True
    assert "graph 관계 근거" in message


def test_graph_template_status_blocks_missing_or_stale_graph() -> None:
    missing_enabled, missing_message = _graph_template_status(Neo4jGraphFreshness("missing", "저장 필요"))
    stale_enabled, stale_message = _graph_template_status(Neo4jGraphFreshness("stale", "갱신 필요"))

    assert missing_enabled is False
    assert "전체 재동기화" in missing_message
    assert stale_enabled is False
    assert "최신 변경분 반영" in stale_message
