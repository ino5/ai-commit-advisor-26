from __future__ import annotations

from pathlib import Path

from src.utils.config import settings


def _normalize(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def resolve_repo_path(repo_path: str | Path) -> Path:
    """Resolve a stored repository path for the current runtime.

    Projects may store Windows host paths such as ``C:\\dev\\repo`` while the
    Docker app sees the same files through a mounted Linux path such as
    ``/host-dev/repo``.
    """
    raw_path = str(repo_path)
    host_prefix = settings.repo_path_host_prefix
    container_prefix = settings.repo_path_container_prefix

    if host_prefix and container_prefix:
        normalized_path = _normalize(raw_path)
        normalized_host = _normalize(host_prefix)
        if normalized_path == normalized_host or normalized_path.startswith(f"{normalized_host}/"):
            suffix = normalized_path[len(normalized_host) :].lstrip("/")
            mapped = _normalize(container_prefix)
            if suffix:
                mapped = f"{mapped}/{suffix}"
            return Path(mapped).expanduser().resolve()

    return Path(repo_path).expanduser().resolve()
