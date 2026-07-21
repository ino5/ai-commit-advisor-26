from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "demo_start.ps1"


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_demo_start_script_uses_canonical_demo_runtime_values():
    text = _script_text()

    assert '$projectId = 2716' in text
    assert '$lmStudioPort = 12345' in text
    assert '$chatContextLength = 8192' in text
    assert 'qwen2.5-coder-7b-instruct' in text
    assert 'text-embedding-nomic-embed-text-v1.5' in text
    assert 'http://127.0.0.1:8501/_stcore/health' in text


def test_demo_start_script_separates_normal_start_build_and_tunnel_creation():
    text = _script_text()

    assert 'docker compose up -d app' in text
    assert 'docker compose up -d --build app' in text
    assert 'quick_tunnel.py status' in text
    assert 'quick_tunnel.py start' in text
    assert 'if ($StartTunnel)' in text
    assert 'if ($Build)' in text


def test_demo_start_script_never_uses_destructive_compose_commands():
    normalized = " ".join(_script_text().lower().split())

    assert "docker compose down" not in normalized
    assert "docker compose rm" not in normalized
    assert "docker volume" not in normalized


def test_demo_start_script_runs_preflight_unless_explicitly_skipped():
    text = _script_text()

    assert 'if (-not $SkipPreflight)' in text
    assert 'demo_preflight.ps1' in text
    assert '-ProjectId $projectId' in text


def test_demo_start_script_keeps_check_only_non_mutating():
    text = _script_text()

    assert 'if ($CheckOnly -and ($Build -or $StartTunnel))' in text
    assert '-CheckOnly는 -Build 또는 -StartTunnel과 함께 사용할 수 없습니다.' in text
