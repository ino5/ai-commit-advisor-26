from types import SimpleNamespace

from src.services.mapping_service import (
    _candidate_score,
    _normalize_implementation_status,
    _parse_commit_based_result,
)


def test_candidate_score_uses_program_text_and_file_paths():
    program = SimpleNamespace(
        program_id="P001",
        program_name="Login API",
        module="auth",
        screen_name="Login",
        description="사용자 로그인 인증 처리",
    )
    commit = SimpleNamespace(
        message="Implement login token validation",
        committed_at=None,
        files=[
            SimpleNamespace(
                file_path="src/auth/login_service.py",
                diff_text="+ validate login token\n+ authenticate user",
            )
        ],
    )

    assert _candidate_score(program, commit) >= 30


def test_parse_commit_based_result_accepts_only_known_candidates():
    program = SimpleNamespace(
        id=1,
        program_id="P001",
        program_name="Login API",
    )
    text = """
    {
      "related_programs": [
        {
          "program_id": "P001",
          "relevance_score": 120,
          "implementation_status": "구현완료",
          "reason": "관련 파일 변경"
        },
        {
          "program_id": "UNKNOWN",
          "relevance_score": 80,
          "implementation_status": "일부구현",
          "reason": "후보에 없음"
        }
      ]
    }
    """

    parsed = _parse_commit_based_result(text, [program])

    assert parsed is not None
    assert len(parsed) == 1
    assert parsed[0]["program"] is program
    assert parsed[0]["relevance_score"] == 100
    assert parsed[0]["implementation_status"] == "구현완료"


def test_normalize_implementation_status_falls_back_to_unknown():
    assert _normalize_implementation_status("일부구현") == "일부구현"
    assert _normalize_implementation_status("unexpected") == "판단불가"
