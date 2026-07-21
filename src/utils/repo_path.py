from __future__ import annotations

import ntpath
import posixpath
import re
from pathlib import Path

from src.utils.config import settings


def _is_windows_style(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", value) or "\\" in value or value.startswith("//"))


def _normalize(value: str) -> str:
    raw_value = value.strip()
    if _is_windows_style(raw_value):
        return ntpath.normpath(raw_value).replace("\\", "/").rstrip("/")
    return posixpath.normpath(raw_value).rstrip("/")


def _is_within(path: str | Path, root: str | Path) -> bool:
    normalized_path = _normalize(str(path))
    normalized_root = _normalize(str(root))
    if _is_windows_style(str(path)) or _is_windows_style(str(root)):
        normalized_path = normalized_path.casefold()
        normalized_root = normalized_root.casefold()
    return normalized_path == normalized_root or normalized_path.startswith(f"{normalized_root}/")


def _map_prefix(raw_path: str, host_prefix: str | None, container_prefix: str | None) -> Path | None:
    if not host_prefix or not container_prefix or not _is_within(raw_path, host_prefix):
        return None

    normalized_path = _normalize(raw_path)
    normalized_host = _normalize(host_prefix)
    suffix = normalized_path[len(normalized_host) :].lstrip("/")
    mapped = _normalize(container_prefix)
    if suffix:
        mapped = f"{mapped}/{suffix}"
    return Path(mapped).expanduser().resolve()


def is_repo_path_allowed(repo_path: str | Path) -> bool:
    """Return whether a project repository path stays inside the configured root.

    If REPO_STORAGE_ROOT is not set, repository path registration remains
    unrestricted for local 검증 and existing demo workflows.
    """
    storage_root = settings.repo_storage_root
    if not storage_root:
        return True

    allowed_roots = [storage_root, settings.managed_repo_storage_root]
    return any(root and _is_within(repo_path, root) for root in allowed_roots)


def repo_storage_root_label() -> str | None:
    return settings.repo_storage_root


def managed_repo_storage_root_label() -> str | None:
    return settings.managed_repo_storage_root


def is_managed_repo_path(repo_path: str | Path | None) -> bool:
    root = settings.managed_repo_storage_root
    return bool(repo_path and root and _is_within(repo_path, root))


def build_managed_repo_path(project_id: int) -> str:
    root = settings.managed_repo_storage_root
    if not root:
        raise ValueError("관리형 Git 저장소 루트가 설정되지 않았습니다.")
    separator = "\\" if "\\" in root else "/"
    normalized_root = root.rstrip("/\\")
    return f"{normalized_root}{separator}project-{int(project_id)}"


def resolve_repo_path(repo_path: str | Path) -> Path:
    """Resolve a stored repository path for the current runtime.

    Projects may store Windows host paths such as ``C:\\dev\\repo`` while the
    Docker app sees the same files through a mounted Linux path such as
    ``/host-dev/repo``.
    """
    raw_path = str(repo_path)

    managed_path = _map_prefix(
        raw_path,
        settings.managed_repo_storage_root,
        settings.managed_repo_container_prefix,
    )
    if managed_path is not None:
        return managed_path

    host_prefix = settings.repo_path_host_prefix
    container_prefix = settings.repo_path_container_prefix

    mapped_path = _map_prefix(raw_path, host_prefix, container_prefix)
    if mapped_path is not None:
        return mapped_path

    return Path(repo_path).expanduser().resolve()
