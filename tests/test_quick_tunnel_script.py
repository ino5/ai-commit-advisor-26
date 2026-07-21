from __future__ import annotations

import subprocess

import pytest

from scripts import quick_tunnel


def _completed(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def test_extract_quick_tunnel_url_returns_most_recent_url():
    logs = """
    INF https://first-demo.trycloudflare.com
    INF reconnecting
    INF https://second-demo-42.trycloudflare.com
    """

    assert quick_tunnel.extract_quick_tunnel_url(logs) == "https://second-demo-42.trycloudflare.com"


def test_select_compose_network_prefers_expected_project_network():
    networks = ["shared_default", "ai-commit-advisor_default"]

    assert quick_tunnel.select_compose_network(networks) == "ai-commit-advisor_default"


def test_select_compose_network_rejects_ambiguous_networks():
    with pytest.raises(quick_tunnel.QuickTunnelError, match="하나로 결정"):
        quick_tunnel.select_compose_network(["first_default", "second_default"])


def test_publicly_bound_host_ports_ignores_loopback_binding():
    ports = {
        "8501/tcp": [
            {"HostIp": "0.0.0.0", "HostPort": "8501"},
            {"HostIp": "::", "HostPort": "8501"},
            {"HostIp": "127.0.0.1", "HostPort": "8501"},
        ]
    }

    assert quick_tunnel.publicly_bound_host_ports(ports) == ["0.0.0.0:8501", ":::8501"]


def test_start_uses_app_service_and_dedicated_tunnel_without_down(monkeypatch):
    compose_calls: list[tuple[str, ...]] = []
    commands: list[list[str]] = []

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_compose",
        lambda *arguments, **_kwargs: compose_calls.append(arguments) or _completed(list(arguments)),
    )
    monkeypatch.setattr(quick_tunnel, "_wait_for_health", lambda *_args, **_kwargs: (True, "200 ok"))
    monkeypatch.setattr(quick_tunnel, "_warn_if_app_is_publicly_bound", lambda: None)
    monkeypatch.setattr(quick_tunnel, "_app_network", lambda: "ai-commit-advisor_default")
    monkeypatch.setattr(quick_tunnel, "_container_state", lambda _name: None)
    monkeypatch.setattr(
        quick_tunnel,
        "_run",
        lambda command, check=True: commands.append(command) or _completed(command),
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_wait_for_tunnel_url",
        lambda **_kwargs: "https://demo-address.trycloudflare.com",
    )
    monkeypatch.setattr(quick_tunnel, "_print_tunnel_result", lambda *_args: None)

    assert quick_tunnel.start_tunnel(build=False, timeout_seconds=10, image="cloudflared:test") == 0
    assert compose_calls == [("up", "-d", "app")]
    assert all("down" not in call and "-v" not in call for call in compose_calls)
    assert commands == [
        [
            "docker",
            "run",
            "--detach",
            "--name",
            quick_tunnel.TUNNEL_CONTAINER_NAME,
            "--network",
            "ai-commit-advisor_default",
            "--label",
            quick_tunnel.TUNNEL_CONTAINER_LABEL,
            "cloudflared:test",
            "tunnel",
            "--no-autoupdate",
            "--url",
            quick_tunnel.TUNNEL_ORIGIN_URL,
        ]
    ]


def test_start_reuses_running_legacy_tunnel_without_creating_second_container(monkeypatch):
    compose_calls: list[tuple[str, ...]] = []
    commands: list[list[str]] = []
    legacy_name = quick_tunnel.LEGACY_TUNNEL_CONTAINER_NAMES[0]

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_compose",
        lambda *arguments, **_kwargs: compose_calls.append(arguments) or _completed(list(arguments)),
    )
    monkeypatch.setattr(quick_tunnel, "_wait_for_health", lambda *_args, **_kwargs: (True, "200 ok"))
    monkeypatch.setattr(quick_tunnel, "_warn_if_app_is_publicly_bound", lambda: None)
    monkeypatch.setattr(
        quick_tunnel,
        "_container_state",
        lambda name: {"Running": True} if name == legacy_name else None,
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_run",
        lambda command, check=True: commands.append(command) or _completed(command),
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_wait_for_tunnel_url",
        lambda **kwargs: (
            "https://legacy-address.trycloudflare.com"
            if kwargs.get("container_name") == legacy_name
            else pytest.fail("legacy container name must be used")
        ),
    )
    monkeypatch.setattr(quick_tunnel, "_print_tunnel_result", lambda *_args: None)

    assert quick_tunnel.start_tunnel(build=False, timeout_seconds=10, image="cloudflared:test") == 0
    assert compose_calls == [("up", "-d", "app")]
    assert commands == []


def test_status_reports_running_legacy_tunnel_without_requiring_owner_label(monkeypatch, capsys):
    legacy_name = quick_tunnel.LEGACY_TUNNEL_CONTAINER_NAMES[0]

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_container_state",
        lambda name: {"Running": True}
        if name in {quick_tunnel.APP_CONTAINER_NAME, legacy_name}
        else None,
    )
    monkeypatch.setattr(quick_tunnel, "_wait_for_health", lambda *_args, **_kwargs: (True, "200 ok"))
    monkeypatch.setattr(
        quick_tunnel,
        "_container_logs",
        lambda name: "INF https://legacy-address.trycloudflare.com" if name == legacy_name else "",
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_assert_owned_tunnel_container",
        lambda: pytest.fail("legacy status must not require the new ownership label"),
    )

    assert quick_tunnel.show_status(timeout_seconds=1) == 0
    output = capsys.readouterr().out
    assert legacy_name in output
    assert "legacy container를 read-only로 재사용" in output


def test_status_rejects_multiple_running_tunnel_containers(monkeypatch):
    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(quick_tunnel, "_container_state", lambda _name: {"Running": True})

    with pytest.raises(quick_tunnel.QuickTunnelError, match="여러 개"):
        quick_tunnel.show_status(timeout_seconds=1)


def test_stop_removes_only_dedicated_tunnel_container_by_default(monkeypatch):
    commands: list[list[str]] = []

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_container_state",
        lambda name: {"Running": True} if name == quick_tunnel.TUNNEL_CONTAINER_NAME else None,
    )
    monkeypatch.setattr(quick_tunnel, "_assert_owned_tunnel_container", lambda: None)
    monkeypatch.setattr(
        quick_tunnel,
        "_run",
        lambda command, check=True: commands.append(command) or _completed(command),
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_compose",
        lambda *_args, **_kwargs: pytest.fail("compose must not be changed without --stop-app"),
    )

    assert quick_tunnel.stop_tunnel(stop_app=False) == 0
    assert commands == [["docker", "rm", "--force", quick_tunnel.TUNNEL_CONTAINER_NAME]]


def test_stop_refuses_container_without_quick_tunnel_label(monkeypatch):
    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_container_state",
        lambda name: {"Running": True} if name == quick_tunnel.TUNNEL_CONTAINER_NAME else None,
    )
    monkeypatch.setattr(quick_tunnel, "_container_labels", lambda _name: {"owner": "someone-else"})
    monkeypatch.setattr(
        quick_tunnel,
        "_run",
        lambda *_args, **_kwargs: pytest.fail("foreign container must not be removed"),
    )

    with pytest.raises(quick_tunnel.QuickTunnelError, match="자동으로 재사용하거나 제거하지 않습니다"):
        quick_tunnel.stop_tunnel(stop_app=False)


def test_stop_does_not_remove_unlabelled_legacy_tunnel(monkeypatch, capsys):
    commands: list[list[str]] = []
    legacy_name = quick_tunnel.LEGACY_TUNNEL_CONTAINER_NAMES[0]

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_container_state",
        lambda name: {"Running": True} if name == legacy_name else None,
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_run",
        lambda command, check=True: commands.append(command) or _completed(command),
    )

    assert quick_tunnel.stop_tunnel(stop_app=False) == 1
    assert commands == []
    assert f"docker stop {legacy_name}" in capsys.readouterr().out


def test_stop_leaves_legacy_running_when_stopped_canonical_container_also_exists(monkeypatch, capsys):
    commands: list[list[str]] = []
    legacy_name = quick_tunnel.LEGACY_TUNNEL_CONTAINER_NAMES[0]

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(
        quick_tunnel,
        "_container_state",
        lambda name: {"Running": False}
        if name == quick_tunnel.TUNNEL_CONTAINER_NAME
        else ({"Running": True} if name == legacy_name else None),
    )
    monkeypatch.setattr(
        quick_tunnel,
        "_run",
        lambda command, check=True: commands.append(command) or _completed(command),
    )

    assert quick_tunnel.stop_tunnel(stop_app=False) == 1
    assert commands == []
    assert f"docker stop {legacy_name}" in capsys.readouterr().out


def test_stop_app_is_explicit_and_does_not_stop_databases(monkeypatch):
    compose_calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(quick_tunnel, "_ensure_docker_available", lambda: "test")
    monkeypatch.setattr(quick_tunnel, "_container_state", lambda _name: None)
    monkeypatch.setattr(
        quick_tunnel,
        "_compose",
        lambda *arguments, **_kwargs: compose_calls.append(arguments) or _completed(list(arguments)),
    )

    assert quick_tunnel.stop_tunnel(stop_app=True) == 0
    assert compose_calls == [("stop", "app")]
