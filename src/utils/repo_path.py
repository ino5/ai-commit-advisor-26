from __future__ import annotations

from pathlib import Path

from src.utils.config import settings


def _normalize(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def is_repo_path_allowed(repo_path: str | Path) -> bool:
    """Return whether a project repository path stays inside the configured root.

    If REPO_STORAGE_ROOT is not set, repository path registration remains
    unrestricted for local 검증 and existing demo workflows.
    """
    storage_root = settings.repo_storage_root
    if not storage_root:
        return True

    normalized_path = _normalize(str(repo_path))
    normalized_root = _normalize(storage_root)
    return normalized_path == normalized_root or normalized_path.startswith(f"{normalized_root}/")


def repo_storage_root_label() -> str | None:
    return settings.repo_storage_root


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
