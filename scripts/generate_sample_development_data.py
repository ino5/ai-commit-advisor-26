"""Generate virtual development-plan sample data from a local Git repository.

The generated files are test fixtures for ai-commit-advisor. They are derived
from real Git commit metadata, but role, skills, planned dates, status, and
progress values are virtual estimates, not real business data.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd


SEED = 20260607
DONE_STATUS = "완료"
IN_PROGRESS_STATUS = "진행중"
PLANNED_STATUS = "예정"
DELAYED_STATUS = "지연"


@dataclass(frozen=True)
class CommitFile:
    status: str
    path: str


@dataclass
class Commit:
    commit_hash: str
    author_name: str
    author_email: str
    committed_at: datetime
    files: list[CommitFile] = field(default_factory=list)


def run_git(repo_path: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={repo_path.as_posix()}", *args],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def sanitize_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()
    if normalized:
        return normalized[:40]
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10].upper()


def stable_int(*parts: str, minimum: int = 0, maximum: int = 100) -> int:
    digest = hashlib.sha256(("|".join(parts) + f"|{SEED}").encode("utf-8")).hexdigest()
    span = maximum - minimum + 1
    return minimum + (int(digest[:12], 16) % span)


def parse_commits(repo_path: Path) -> list[Commit]:
    log = run_git(
        repo_path,
        [
            "log",
            "--reverse",
            "--name-status",
            "--date=iso-strict",
            "--pretty=format:--COMMIT--%x09%H%x09%an%x09%ae%x09%ad",
        ],
    )
    commits: list[Commit] = []
    current: Commit | None = None

    for raw_line in log.splitlines():
        line = raw_line.rstrip("\n")
        if not line:
            continue
        if line.startswith("--COMMIT--\t"):
            _, commit_hash, author_name, author_email, committed_at = line.split("\t", 4)
            current = Commit(
                commit_hash=commit_hash,
                author_name=author_name,
                author_email=author_email,
                committed_at=datetime.fromisoformat(committed_at),
            )
            commits.append(current)
            continue
        if current is None:
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[-1].replace("\\", "/")
        current.files.append(CommitFile(status=status, path=path))

    return commits


def classify_file(path: str) -> str:
    lower = path.lower()
    suffix = Path(path).suffix.lower()
    if any(token in lower for token in ["/mapper/", "mapper", "/repository/", "/repositories/", "repository"]) or suffix in {
        ".sql",
        ".xml",
    }:
        return "database"
    if any(token in lower for token in ["/controller/", "/controllers/", "/service/", "/services/", "/config/"]) or suffix in {
        ".java",
        ".py",
    }:
        return "backend"
    if "/templates/" in lower or suffix in {".html", ".js", ".css", ".scss"}:
        return "frontend"
    if suffix in {".md", ".txt"}:
        return "documentation"
    return "other"


def infer_role_and_skills(paths: list[str]) -> tuple[str, str]:
    categories = Counter(classify_file(path) for path in paths)
    role_by_category = {
        "backend": "Backend Developer",
        "frontend": "Frontend Developer",
        "database": "Database Developer",
        "documentation": "Technical Writer",
        "other": "Full-stack Developer",
    }
    main_category = categories.most_common(1)[0][0] if categories else "other"

    skill_flags: list[tuple[str, str]] = [
        ("controller", "Spring MVC Controller"),
        ("controllers", "Controller/API"),
        (".py", "Python"),
        ("service", "Service Layer"),
        ("services", "Service Layer"),
        ("repository", "Repository/JPA"),
        ("repositories", "Repository/JPA"),
        ("mapper", "Mapper/SQL"),
        ("templates", "Thymeleaf/HTML"),
        (".js", "JavaScript"),
        (".css", "CSS"),
        (".scss", "SCSS"),
        ("config", "Spring Configuration"),
        ("readme", "Documentation"),
    ]
    lower_paths = "\n".join(paths).lower()
    skills = []
    for marker, skill in skill_flags:
        if marker in lower_paths and skill not in skills:
            skills.append(skill)
    if not skills:
        skills = ["Application Maintenance"]
    return role_by_category[main_category], ", ".join(skills[:5])


def developer_id_for(name: str, email: str) -> str:
    local = email.split("@", 1)[0] if email else name
    return f"DEV_{sanitize_id(local or name)}"


def build_developers(commits: list[Commit]) -> tuple[pd.DataFrame, dict[str, str]]:
    author_paths: dict[str, list[str]] = defaultdict(list)
    author_names: dict[str, str] = {}
    author_emails: dict[str, str] = {}

    for commit in commits:
        key = commit.author_email or commit.author_name
        author_names[key] = commit.author_name
        author_emails[key] = commit.author_email
        author_paths[key].extend(file.path for file in commit.files)

    rows = []
    developer_ids = {}
    for key in sorted(author_names, key=lambda item: (author_names[item].lower(), item.lower())):
        developer_id = developer_id_for(author_names[key], author_emails[key])
        role, skills = infer_role_and_skills(author_paths[key])
        developer_ids[key] = developer_id
        rows.append(
            {
                "developer_id": developer_id,
                "developer_name": author_names[key],
                "email": author_emails[key],
                "role": role,
                "skills": skills,
            }
        )
    return pd.DataFrame(rows), developer_ids


def find_program_csv_candidates(repo_path: Path) -> list[Path]:
    return sorted(repo_path.glob("*프로그램목록*.csv"))


def read_program_csv(csv_path: Path) -> pd.DataFrame | None:
    for encoding in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
        if {"프로그램ID", "프로그램명"}.issubset(set(df.columns)):
            return df
    return None


def read_existing_program_csv(repo_path: Path, program_csv_path: Path | None = None) -> pd.DataFrame | None:
    candidates = [program_csv_path] if program_csv_path else find_program_csv_candidates(repo_path)
    if not candidates:
        return None

    for candidate in candidates:
        df = read_program_csv(candidate)
        if df is not None:
            return df
    return None


def module_from_path(path: str) -> str:
    lower = path.lower()
    if "/templates/" in lower:
        parts = lower.split("/templates/", 1)[1].split("/")
        return parts[0] if len(parts) > 1 else "common"
    if any(token in lower for token in ["/controller/", "/controllers/", "/service/", "/services/", "/repository/", "/repositories/"]):
        name = Path(path).stem
        name = re.sub(r"[_-]?(controller|service|repository|mapper|entity|dto)$", "", name, flags=re.IGNORECASE)
        return name.strip("_-") or "common"
    if "/static/" in lower:
        return "static"
    return "common"


def program_name_from_path(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"[_-]?(Controller|Service|Repository|Mapper|Entity|Dto)$", "", stem, flags=re.IGNORECASE)
    if stem and stem.lower() not in {"index", "main"}:
        return stem
    return module_from_path(path).title()


def build_programs_from_existing(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        program_id = str(row.get("프로그램ID", "")).strip()
        program_name = str(row.get("프로그램명", "")).strip()
        if not program_id or not program_name:
            continue
        rows.append(
            {
                "program_id": program_id,
                "program_name": program_name,
                "module": str(row.get("주요기능", "")).strip() or None,
                "screen_name": str(row.get("주요URL/화면", "")).strip() or None,
                "description": str(row.get("기능설명", "")).strip() or None,
                "_keywords": " ".join(
                    str(row.get(column, ""))
                    for column in ["Controller", "Service", "Mapper/Repository", "주요URL/화면", "프로그램명"]
                ),
            }
        )
    return pd.DataFrame(rows)


def build_programs_from_git(commits: list[Commit]) -> pd.DataFrame:
    programs: dict[str, dict] = {}
    module_counts: Counter[str] = Counter()

    for commit in commits:
        for file in commit.files:
            if Path(file.path).suffix.lower() not in {".java", ".html", ".js", ".css", ".scss", ".xml", ".sql"}:
                continue
            module = module_from_path(file.path)
            name = program_name_from_path(file.path)
            key = f"{module}:{name}".lower()
            module_counts[module] += 1
            programs.setdefault(
                key,
                {
                    "module": module,
                    "program_name": f"{name} 기능",
                    "screen_name": file.path if "/templates/" in file.path.lower() else None,
                    "description": f"{file.path} 변경 이력을 기준으로 생성한 가상 프로그램입니다.",
                    "_keywords": f"{module} {name} {file.path}",
                },
            )

    rows = []
    per_module = Counter()
    for item in sorted(programs.values(), key=lambda row: (row["module"], row["program_name"])):
        module_code = sanitize_id(item["module"])[:10] or "COMMON"
        per_module[module_code] += 1
        rows.append(
            {
                "program_id": f"GM-{module_code}-{per_module[module_code]:03d}",
                "program_name": item["program_name"],
                "module": item["module"],
                "screen_name": item["screen_name"],
                "description": item["description"],
                "_keywords": item["_keywords"],
            }
        )
    return pd.DataFrame(rows)


def build_programs(
    repo_path: Path,
    commits: list[Commit],
    use_existing_program_csv: bool = False,
    program_csv_path: Path | None = None,
) -> pd.DataFrame:
    if use_existing_program_csv:
        existing = read_existing_program_csv(repo_path, program_csv_path=program_csv_path)
        if existing is not None:
            programs = build_programs_from_existing(existing)
            if not programs.empty:
                return programs
    return build_programs_from_git(commits)


def match_program(path: str, programs: pd.DataFrame) -> str | None:
    lower_path = path.lower()
    best_score = 0
    best_program_id: str | None = None
    for _, program in programs.iterrows():
        keywords = str(program.get("_keywords", "")).replace(",", " ").split()
        module = str(program.get("module", ""))
        name = str(program.get("program_name", ""))
        tokens = [*keywords, module, name]
        score = sum(1 for token in tokens if token and token.lower() in lower_path)
        if score > best_score:
            best_score = score
            best_program_id = program["program_id"]
    if best_program_id:
        return best_program_id

    module = module_from_path(path).lower()
    matches = programs[programs["module"].fillna("").str.lower().str.contains(re.escape(module), na=False)]
    if not matches.empty:
        return str(matches.iloc[0]["program_id"])
    return None


def build_plan(commits: list[Commit], programs: pd.DataFrame, developer_ids: dict[str, str]) -> pd.DataFrame:
    program_commits: dict[str, list[Commit]] = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()

    for commit in commits:
        for file in commit.files:
            program_id = match_program(file.path, programs)
            if not program_id:
                continue
            pair = (program_id, commit.commit_hash)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            program_commits[program_id].append(commit)

    latest_commit_date = max((commit.committed_at.date() for commit in commits), default=date.today())
    recent_cutoff = latest_commit_date - timedelta(days=3)
    today = date.today()
    rows = []

    for _, program in programs.iterrows():
        program_id = str(program["program_id"])
        related = sorted(program_commits.get(program_id, []), key=lambda commit: commit.committed_at)
        if related:
            actual_start = related[0].committed_at.date()
            actual_end = related[-1].committed_at.date()
            lead_days = stable_int(program_id, "planned_start", minimum=1, maximum=5)
            lag_days = stable_int(program_id, "planned_end", minimum=1, maximum=5)
            planned_start = actual_start - timedelta(days=lead_days)
            planned_end = actual_end + timedelta(days=lag_days)

            author_counts = Counter(commit.author_email or commit.author_name for commit in related)
            assignee_key = author_counts.most_common(1)[0][0]
            developer_id = developer_ids[assignee_key]

            status = IN_PROGRESS_STATUS if actual_end >= recent_cutoff and len(related) >= 2 else DONE_STATUS
            progress_rate = 100 if status == DONE_STATUS else stable_int(program_id, "progress", minimum=30, maximum=90)
            if status != DONE_STATUS and planned_end < today:
                status = DELAYED_STATUS
        else:
            planned_start = today + timedelta(days=stable_int(program_id, "future_start", minimum=3, maximum=30))
            planned_end = planned_start + timedelta(days=stable_int(program_id, "future_end", minimum=5, maximum=20))
            actual_start = None
            actual_end = None
            developer_id = ""
            status = PLANNED_STATUS
            progress_rate = 0

        rows.append(
            {
                "program_id": program_id,
                "developer_id": developer_id,
                "planned_start_date": planned_start,
                "planned_end_date": planned_end,
                "actual_start_date": actual_start,
                "actual_end_date": actual_end,
                "status": status,
                "progress_rate": progress_rate,
            }
        )
    return pd.DataFrame(rows)


def write_excel(output_dir: Path, developers: pd.DataFrame, programs: pd.DataFrame, plan: pd.DataFrame) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    developers.to_excel(output_dir / "sample_developers.xlsx", index=False)
    programs.drop(columns=["_keywords"], errors="ignore").to_excel(output_dir / "sample_programs.xlsx", index=False)
    plan.to_excel(output_dir / "sample_development_plan.xlsx", index=False)


def generate_sample_data(
    repo_path: Path,
    use_existing_program_csv: bool = False,
    program_csv_path: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    commits = parse_commits(repo_path)
    if not commits:
        raise RuntimeError(f"No Git commits found in {repo_path}")

    developers, developer_ids = build_developers(commits)
    programs = build_programs(
        repo_path,
        commits,
        use_existing_program_csv=use_existing_program_csv,
        program_csv_path=program_csv_path,
    )
    plan = build_plan(commits, programs, developer_ids)
    return developers, programs, plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate virtual development-plan sample data from Git logs.")
    parser.add_argument("--repo-path", required=True, help="Local Git repository path to analyze.")
    parser.add_argument("--output-dir", default="sample_data", help="Directory to write generated Excel files.")
    parser.add_argument(
        "--use-existing-program-csv",
        action="store_true",
        help="Use an existing program-list CSV in the repository when available.",
    )
    parser.add_argument("--program-csv-path", help="Explicit program-list CSV path to use.")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    output_dir = Path(args.output_dir).resolve()

    program_csv_path = Path(args.program_csv_path).resolve() if args.program_csv_path else None
    developers, programs, plan = generate_sample_data(
        repo_path,
        use_existing_program_csv=args.use_existing_program_csv,
        program_csv_path=program_csv_path,
    )
    write_excel(output_dir, developers, programs, plan)

    print(f"Generated {len(developers)} developers, {len(programs)} programs, {len(plan)} plan rows.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
