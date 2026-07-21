"""Start, inspect, and stop a one-day Cloudflare Quick Tunnel demo.

The tunnel runs in the official ``cloudflare/cloudflared`` Docker image and
joins the application's Compose network. The script never removes Compose
volumes and only owns the dedicated Quick Tunnel container.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PROJECT_NAME = "ai-commit-advisor"
APP_CONTAINER_NAME = "ai_commit_advisor_app"
TUNNEL_CONTAINER_NAME = "ai_commit_advisor_demo_tunnel"
TUNNEL_CONTAINER_LABEL = "com.ai-commit-advisor.purpose=quick-tunnel-demo"
LEGACY_TUNNEL_CONTAINER_NAMES = ("ai_commit_advisor_quick_tunnel",)
DEFAULT_CLOUDFLARED_IMAGE = os.environ.get("CLOUDFLARED_IMAGE", "cloudflare/cloudflared:latest")
LOCAL_HEALTH_URL = "http://127.0.0.1:8501/_stcore/health"
TUNNEL_ORIGIN_URL = "http://app:8501"
QUICK_TUNNEL_URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


class QuickTunnelError(RuntimeError):
    """Raised when a Quick Tunnel operation cannot complete safely."""


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise QuickTunnelError(f"명령을 찾을 수 없습니다: {command[0]}") from exc

    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit code {result.returncode}"
        raise QuickTunnelError(f"명령 실행 실패: {' '.join(command)}\n{detail}")
    return result


def _compose(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(
        ["docker", "compose", "--project-name", COMPOSE_PROJECT_NAME, *arguments],
        check=check,
    )


def _ensure_docker_available() -> str:
    result = _run(["docker", "version", "--format", "{{.Server.Version}}"])
    version = result.stdout.strip()
    if not version:
        raise QuickTunnelError("Docker daemon version을 확인하지 못했습니다. Docker Desktop 실행 상태를 확인하세요.")
    return version


def _container_state(container_name: str) -> dict[str, Any] | None:
    result = _run(
        ["docker", "inspect", "--format", "{{json .State}}", container_name],
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        state = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise QuickTunnelError(f"{container_name} container 상태를 해석하지 못했습니다.") from exc
    return state if isinstance(state, dict) else None


def _container_logs(container_name: str, *, since: str | None = None) -> str:
    command = ["docker", "logs"]
    if since:
        command.extend(["--since", since])
    command.append(container_name)
    result = _run(command, check=False)
    return "\n".join(part for part in (result.stdout, result.stderr) if part).strip()


def _current_run_logs(container_name: str) -> str:
    """Return logs produced since the container's current process started."""

    state = _container_state(container_name) or {}
    started_at = state.get("StartedAt")
    if started_at:
        return _container_logs(container_name, since=str(started_at))
    return _container_logs(container_name)


def _container_labels(container_name: str) -> dict[str, str]:
    result = _run(
        ["docker", "inspect", "--format", "{{json .Config.Labels}}", container_name]
    )
    try:
        labels = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise QuickTunnelError(f"{container_name} container label을 해석하지 못했습니다.") from exc
    if labels is None:
        return {}
    if not isinstance(labels, dict):
        raise QuickTunnelError(f"{container_name} container label 형식이 올바르지 않습니다.")
    return {str(key): str(value) for key, value in labels.items()}


def _assert_owned_tunnel_container() -> None:
    label_key, expected_value = TUNNEL_CONTAINER_LABEL.split("=", maxsplit=1)
    actual_value = _container_labels(TUNNEL_CONTAINER_NAME).get(label_key)
    if actual_value != expected_value:
        raise QuickTunnelError(
            f"{TUNNEL_CONTAINER_NAME} 이름을 다른 container가 사용 중입니다. "
            "안전을 위해 자동으로 재사용하거나 제거하지 않습니다."
        )


def _select_running_tunnel_container() -> str | None:
    """Return one active canonical or legacy Tunnel without mutating either."""

    running_names = [
        name
        for name in (TUNNEL_CONTAINER_NAME, *LEGACY_TUNNEL_CONTAINER_NAMES)
        if bool((_container_state(name) or {}).get("Running"))
    ]
    if len(running_names) > 1:
        names = ", ".join(running_names)
        raise QuickTunnelError(
            f"실행 중인 Quick Tunnel container가 여러 개입니다: {names}. "
            "주소를 임의로 선택하지 않고 운영자가 하나만 남길 때까지 중단합니다."
        )
    return running_names[0] if running_names else None


def extract_quick_tunnel_url(log_text: str) -> str | None:
    """Return the most recently logged trycloudflare.com URL."""

    matches = QUICK_TUNNEL_URL_PATTERN.findall(log_text)
    return matches[-1] if matches else None


def select_compose_network(network_names: list[str]) -> str:
    """Select the app's Compose default network without guessing across matches."""

    if not network_names:
        raise QuickTunnelError(f"{APP_CONTAINER_NAME} container에 연결된 Docker network가 없습니다.")

    expected = f"{COMPOSE_PROJECT_NAME}_default"
    if expected in network_names:
        return expected
    if len(network_names) == 1:
        return network_names[0]

    default_networks = sorted(name for name in network_names if name.endswith("_default"))
    if len(default_networks) == 1:
        return default_networks[0]

    names = ", ".join(sorted(network_names))
    raise QuickTunnelError(f"앱의 Compose network를 하나로 결정할 수 없습니다: {names}")


def _app_network() -> str:
    result = _run(
        [
            "docker",
            "inspect",
            "--format",
            "{{json .NetworkSettings.Networks}}",
            APP_CONTAINER_NAME,
        ]
    )
    try:
        networks = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise QuickTunnelError("앱 container의 Docker network 정보를 해석하지 못했습니다.") from exc
    if not isinstance(networks, dict):
        raise QuickTunnelError("앱 container의 Docker network 정보 형식이 올바르지 않습니다.")
    return select_compose_network(list(networks))


def publicly_bound_host_ports(port_payload: dict[str, Any]) -> list[str]:
    """Return host bindings that listen on every IPv4 or IPv6 interface."""

    bindings = port_payload.get("8501/tcp") or []
    exposed: list[str] = []
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        host_ip = str(binding.get("HostIp") or "")
        host_port = str(binding.get("HostPort") or "8501")
        if host_ip in {"", "0.0.0.0", "::"}:
            exposed.append(f"{host_ip or '*'}:{host_port}")
    return exposed


def _warn_if_app_is_publicly_bound() -> None:
    result = _run(
        ["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", APP_CONTAINER_NAME]
    )
    try:
        ports = json.loads(result.stdout)
    except json.JSONDecodeError:
        return
    if not isinstance(ports, dict):
        return

    bindings = publicly_bound_host_ports(ports)
    if bindings:
        joined = ", ".join(bindings)
        print(f"[주의] 앱 port가 모든 host interface에 열려 있습니다: {joined}")
        print("       공용 네트워크에서는 Windows Firewall 또는 loopback port binding을 사용하세요.")


def _probe_health(url: str, *, timeout_seconds: float = 5.0) -> tuple[bool, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ai-commit-advisor-quick-tunnel-check/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(256).decode("utf-8", errors="replace").strip()
            if response.status == 200 and body == "ok":
                return True, "200 ok"
            return False, f"HTTP {response.status}, body={body!r}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, str(exc)


def _wait_for_health(url: str, *, timeout_seconds: int) -> tuple[bool, str]:
    deadline = time.monotonic() + timeout_seconds
    last_detail = "아직 응답이 없습니다."
    while time.monotonic() < deadline:
        healthy, detail = _probe_health(url)
        if healthy:
            return True, detail
        last_detail = detail
        time.sleep(1)
    return False, last_detail


def _wait_for_tunnel_url(*, timeout_seconds: int, container_name: str = TUNNEL_CONTAINER_NAME) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        tunnel_url = extract_quick_tunnel_url(_current_run_logs(container_name))
        if tunnel_url:
            return tunnel_url
        state = _container_state(container_name)
        if state is not None and not bool(state.get("Running")):
            logs = _current_run_logs(container_name)
            raise QuickTunnelError(f"Quick Tunnel container가 URL 발급 전에 종료됐습니다.\n{logs}")
        time.sleep(1)

    logs = _current_run_logs(container_name)
    raise QuickTunnelError(f"Quick Tunnel URL을 {timeout_seconds}초 안에 찾지 못했습니다.\n{logs}")


def _print_tunnel_result(tunnel_url: str, public_health: str, container_name: str) -> None:
    print()
    print("Quick Tunnel 준비가 완료됐습니다.")
    print(f"Tunnel container: {container_name}")
    print(f"외부 URL: {tunnel_url}")
    print(f"외부 health: {public_health}")
    print(f"상태 확인: {sys.executable} scripts/quick_tunnel.py status")
    print(f"Tunnel 종료: {sys.executable} scripts/quick_tunnel.py stop")


def start_tunnel(*, build: bool, timeout_seconds: int, image: str) -> int:
    docker_version = _ensure_docker_available()
    print(f"[1/4] Docker 확인: {docker_version}")

    if build:
        print("[2/4] 현재 소스로 app image를 빌드합니다.")
        _compose("build", "--quiet", "app")
    else:
        print("[2/4] 기존 app image를 사용합니다. 소스가 바뀌었다면 다음 실행에 --build를 추가하세요.")

    _compose("up", "-d", "app")
    healthy, detail = _wait_for_health(LOCAL_HEALTH_URL, timeout_seconds=timeout_seconds)
    if not healthy:
        raise QuickTunnelError(
            f"로컬 Streamlit health 확인 실패: {detail}\n"
            "docker compose logs app에서 migration과 시작 오류를 확인하세요."
        )
    print(f"[3/4] 로컬 앱 확인: {detail}")
    _warn_if_app_is_publicly_bound()

    active_tunnel_name = _select_running_tunnel_container()
    if active_tunnel_name is not None:
        if active_tunnel_name == TUNNEL_CONTAINER_NAME:
            _assert_owned_tunnel_container()
        else:
            print(f"[4/4] 기존 legacy Quick Tunnel을 재사용합니다: {active_tunnel_name}")
        tunnel_url = _wait_for_tunnel_url(
            timeout_seconds=timeout_seconds,
            container_name=active_tunnel_name,
        )
        public_url = f"{tunnel_url}/_stcore/health"
        public_ok, public_detail = _wait_for_health(public_url, timeout_seconds=timeout_seconds)
        if not public_ok:
            raise QuickTunnelError(f"기존 Quick Tunnel 외부 health 확인 실패: {public_detail}")
        if active_tunnel_name == TUNNEL_CONTAINER_NAME:
            print("[4/4] 기존 Quick Tunnel을 재사용합니다.")
        _print_tunnel_result(tunnel_url, public_detail, active_tunnel_name)
        return 0

    network_name = _app_network()
    tunnel_state = _container_state(TUNNEL_CONTAINER_NAME)
    if tunnel_state is not None:
        _assert_owned_tunnel_container()
        _run(["docker", "rm", TUNNEL_CONTAINER_NAME])

    print(f"[4/4] Quick Tunnel을 시작합니다: network={network_name}, image={image}")
    _run(
        [
            "docker",
            "run",
            "--detach",
            "--restart",
            "unless-stopped",
            "--name",
            TUNNEL_CONTAINER_NAME,
            "--network",
            network_name,
            "--label",
            TUNNEL_CONTAINER_LABEL,
            image,
            "tunnel",
            "--no-autoupdate",
            "--url",
            TUNNEL_ORIGIN_URL,
        ]
    )

    tunnel_url = _wait_for_tunnel_url(timeout_seconds=timeout_seconds)
    public_url = f"{tunnel_url}/_stcore/health"
    public_ok, public_detail = _wait_for_health(public_url, timeout_seconds=timeout_seconds)
    if not public_ok:
        raise QuickTunnelError(
            f"외부 URL은 발급됐지만 health 확인에 실패했습니다: {public_detail}\n"
            f"Tunnel 로그: docker logs {TUNNEL_CONTAINER_NAME}"
        )

    _print_tunnel_result(tunnel_url, public_detail, TUNNEL_CONTAINER_NAME)
    return 0


def show_status(*, timeout_seconds: int) -> int:
    _ensure_docker_available()
    app_state = _container_state(APP_CONTAINER_NAME)
    tunnel_name = _select_running_tunnel_container()

    app_running = bool(app_state and app_state.get("Running"))
    print(f"앱 container: {'running' if app_running else 'stopped'}")
    local_ok = False
    if app_running:
        local_ok, local_detail = _wait_for_health(LOCAL_HEALTH_URL, timeout_seconds=timeout_seconds)
        print(f"로컬 health: {'정상' if local_ok else '실패'} ({local_detail})")

    if tunnel_name is None:
        checked_names = ", ".join((TUNNEL_CONTAINER_NAME, *LEGACY_TUNNEL_CONTAINER_NAMES))
        print(f"Tunnel container: stopped (확인한 이름: {checked_names})")
        return 1

    print(f"Tunnel container: running ({tunnel_name})")
    if tunnel_name == TUNNEL_CONTAINER_NAME:
        _assert_owned_tunnel_container()
    else:
        print("Tunnel 유형: legacy container를 read-only로 재사용 중")
    try:
        tunnel_url = _wait_for_tunnel_url(
            timeout_seconds=timeout_seconds,
            container_name=tunnel_name,
        )
    except QuickTunnelError as exc:
        print(f"외부 URL: 현재 실행 로그에서 찾지 못했습니다. ({exc})")
        return 1

    print(f"외부 URL: {tunnel_url}")
    public_ok, public_detail = _wait_for_health(
        f"{tunnel_url}/_stcore/health",
        timeout_seconds=timeout_seconds,
    )
    print(f"외부 health: {'정상' if public_ok else '실패'} ({public_detail})")
    return 0 if app_running and local_ok and public_ok else 1


def stop_tunnel(*, stop_app: bool) -> int:
    _ensure_docker_available()
    active_tunnel_name = _select_running_tunnel_container()
    tunnel_state = _container_state(TUNNEL_CONTAINER_NAME)
    result_code = 0
    if active_tunnel_name in LEGACY_TUNNEL_CONTAINER_NAMES:
        print(
            f"Legacy Quick Tunnel {active_tunnel_name}은 ownership label이 없어 자동으로 제거하지 않습니다."
        )
        print(f"운영자가 주소 종료를 확인한 뒤 직접 중지하세요: docker stop {active_tunnel_name}")
        result_code = 1
    elif tunnel_state is None:
        print("Quick Tunnel container는 이미 없습니다.")
    else:
        _assert_owned_tunnel_container()
        _run(["docker", "rm", "--force", TUNNEL_CONTAINER_NAME])
        print("Quick Tunnel container를 종료하고 제거했습니다.")

    if stop_app:
        _compose("stop", "app")
        print("app container도 중지했습니다. PostgreSQL, Neo4j, volume은 유지됩니다.")
    else:
        print("app, PostgreSQL, Neo4j container는 변경하지 않았습니다.")
    return result_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Docker 기반 AI Commit Advisor의 Cloudflare Quick Tunnel을 관리합니다.",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    start_parser = subparsers.add_parser("start", help="Docker app과 Quick Tunnel을 시작합니다.")
    start_parser.add_argument(
        "--build",
        action="store_true",
        help="Tunnel 시작 전에 현재 소스로 app image를 다시 빌드합니다.",
    )
    start_parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="로컬/외부 health와 URL 발급을 기다릴 최대 초입니다. 기본값: 90",
    )
    start_parser.add_argument(
        "--image",
        default=DEFAULT_CLOUDFLARED_IMAGE,
        help=f"사용할 cloudflared Docker image. 기본값: {DEFAULT_CLOUDFLARED_IMAGE}",
    )

    status_parser = subparsers.add_parser("status", help="앱과 Quick Tunnel 상태를 확인합니다.")
    status_parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="health 응답을 기다릴 최대 초입니다. 기본값: 10",
    )

    stop_parser = subparsers.add_parser("stop", help="Quick Tunnel을 종료합니다.")
    stop_parser.add_argument(
        "--stop-app",
        action="store_true",
        help="Tunnel과 함께 app container도 중지합니다. DB/Neo4j와 volume은 유지합니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.action == "start":
            return start_tunnel(build=args.build, timeout_seconds=args.timeout, image=args.image)
        if args.action == "status":
            return show_status(timeout_seconds=args.timeout)
        if args.action == "stop":
            return stop_tunnel(stop_app=args.stop_app)
        raise QuickTunnelError(f"지원하지 않는 action입니다: {args.action}")
    except QuickTunnelError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("사용자가 작업을 중단했습니다.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
