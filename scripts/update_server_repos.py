"""Update pre-cloned Git repositories under an app-server storage root.

This script intentionally does not clone repositories or manage credentials.
It is for the operating model where an internal server already has repositories
under REPO_STORAGE_ROOT and AI Commit Advisor reads those paths.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - dotenv is a project dependency.
    load_dotenv = None


@dataclass
class RepoUpdateResult:
    path: Path
    status: str
    branch_before: str | None = None
    head_before: str | None = None
    head_after: str | None = None
    messages: list[str] = field(default_factory=list)


def _run_git(repo_path: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={repo_path.as_posix()}", *args],
        cwd=repo_path,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_output(repo_path: Path, args: list[str], *, check: bool = True) -> str:
    result = _run_git(repo_path, args, check=check)
    return result.stdout.strip()


def _is_git_repo(path: Path) -> bool:
    if not path.exists():
        return False
    result = _run_git(path, ["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        return False
    try:
        top_level = Path(result.stdout.strip()).expanduser().resolve()
    except Exception:
        return False
    return top_level == path.resolve()


def _discover_repos(root: Path) -> list[Path]:
    if _is_git_repo(root):
        return [root]
    if not root.exists():
        return []
    repos = [child for child in root.iterdir() if child.is_dir() and _is_git_repo(child)]
    return sorted(repos, key=lambda path: path.as_posix().lower())


def _ensure_under_root(root: Path, repo: Path) -> None:
    try:
        repo.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Repository path is outside root: {repo}") from exc


def _checkout_branch(repo: Path, *, branch: str, remote: str, dry_run: bool, messages: list[str]) -> None:
    if dry_run:
        messages.append(f"would checkout/reset {branch} to {remote}/{branch}")
        return

    checkout = _run_git(repo, ["checkout", branch], check=False)
    if checkout.returncode != 0:
        _run_git(repo, ["checkout", "-B", branch, f"{remote}/{branch}"])
    _run_git(repo, ["reset", "--hard", f"{remote}/{branch}"])


def update_repo(
    repo: Path,
    *,
    remote: str,
    branch: str,
    reset: bool,
    force: bool,
    dry_run: bool,
) -> RepoUpdateResult:
    result = RepoUpdateResult(path=repo, status="ok")
    try:
        result.branch_before = _git_output(repo, ["branch", "--show-current"], check=False) or None
        result.head_before = _git_output(repo, ["rev-parse", "HEAD"], check=False) or None
        dirty_status = _git_output(repo, ["status", "--porcelain"], check=False)

        if dry_run:
            result.messages.append(f"would fetch --prune {remote}")
        else:
            _run_git(repo, ["fetch", "--prune", remote])
            result.messages.append(f"fetched {remote}")

        if reset:
            if dirty_status and not force:
                result.status = "skipped"
                result.messages.append("working tree has local changes; use --force to allow reset")
                return result
            _checkout_branch(repo, branch=branch, remote=remote, dry_run=dry_run, messages=result.messages)

        result.head_after = result.head_before if dry_run else _git_output(repo, ["rev-parse", "HEAD"], check=False) or None
    except subprocess.CalledProcessError as exc:
        result.status = "failed"
        stderr = (exc.stderr or "").strip()
        result.messages.append(stderr or str(exc))
    except Exception as exc:
        result.status = "failed"
        result.messages.append(str(exc))
    return result


def _print_result(result: RepoUpdateResult) -> None:
    short_before = result.head_before[:12] if result.head_before else "-"
    short_after = result.head_after[:12] if result.head_after else "-"
    print(f"[{result.status}] {result.path}")
    print(f"  branch: {result.branch_before or '-'}")
    print(f"  head:   {short_before} -> {short_after}")
    for message in result.messages:
        print(f"  - {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and optionally reset pre-cloned repositories under REPO_STORAGE_ROOT.",
    )
    parser.add_argument(
        "--root",
        default=os.environ.get("REPO_STORAGE_ROOT"),
        help="Repository storage root. Defaults to REPO_STORAGE_ROOT from the environment or .env.",
    )
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Specific repository path under the root. Can be provided multiple times.",
    )
    parser.add_argument("--remote", default="origin", help="Remote name to fetch from.")
    parser.add_argument("--branch", default="main", help="Branch used when --reset is enabled.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="After fetch, checkout/reset the branch to <remote>/<branch>.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --reset even when the working tree has local changes.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without changing repositories.")
    return parser.parse_args()


def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = parse_args()
    root_value = args.root or os.environ.get("REPO_STORAGE_ROOT")
    if not root_value:
        print("REPO_STORAGE_ROOT is not set. Pass --root or set it in the environment.")
        return 2

    root = Path(root_value).expanduser().resolve()
    if not root.exists():
        print(f"Repository root does not exist: {root}")
        return 2

    if args.repo:
        repos = [Path(repo).expanduser().resolve() for repo in args.repo]
        try:
            for repo in repos:
                _ensure_under_root(root, repo)
        except ValueError as exc:
            print(str(exc))
            return 2
    else:
        repos = _discover_repos(root)

    if not repos:
        print(f"No Git repositories found under: {root}")
        return 1

    results = [
        update_repo(
            repo,
            remote=args.remote,
            branch=args.branch,
            reset=args.reset,
            force=args.force,
            dry_run=args.dry_run,
        )
        for repo in repos
    ]

    for result in results:
        _print_result(result)

    failed = [result for result in results if result.status == "failed"]
    skipped = [result for result in results if result.status == "skipped"]
    print(f"Summary: ok={len(results) - len(failed) - len(skipped)}, skipped={len(skipped)}, failed={len(failed)}")
    return 1 if failed or skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
