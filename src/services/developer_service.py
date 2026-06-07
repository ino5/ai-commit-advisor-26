from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.models import Developer, GitCommit


ROLE_OPTIONS = [
    "Backend Developer",
    "Frontend Developer",
    "Database Developer",
    "Fullstack Developer",
]


@dataclass
class DeveloperExtractionResult:
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0


def make_developer_key(author_name: str | None, author_email: str | None) -> str:
    base = (author_email or author_name or "unknown").strip().lower()
    base = re.sub(r"[^a-z0-9가-힣._@-]+", "_", base).strip("_")
    return base or "unknown"


def _classify_path(file_path: str | None) -> str:
    path = (file_path or "").lower()
    if any(token in path for token in ["mapper", "repository", ".sql", ".xml"]):
        return "database"
    if any(token in path for token in ["controller", "service", "config", ".java"]):
        return "backend"
    if any(token in path for token in ["templates", ".html", ".js", ".css", ".scss"]):
        return "frontend"
    return "other"


def infer_role_and_skills(file_paths: list[str]) -> tuple[str, str]:
    categories = Counter(_classify_path(path) for path in file_paths)
    if not categories:
        return "Fullstack Developer", "Git commit"

    if categories["database"] >= categories["backend"] and categories["database"] >= categories["frontend"]:
        role = "Database Developer"
    elif categories["backend"] >= categories["frontend"]:
        role = "Backend Developer"
    elif categories["frontend"] > 0:
        role = "Frontend Developer"
    else:
        role = "Fullstack Developer"

    skill_markers = [
        ("controller", "Controller"),
        ("service", "Service"),
        ("repository", "Repository/JPA"),
        ("mapper", "Mapper/SQL"),
        (".sql", "SQL"),
        (".xml", "XML"),
        ("templates", "Template"),
        (".html", "HTML"),
        (".js", "JavaScript"),
        (".css", "CSS"),
        (".scss", "SCSS"),
    ]
    joined_paths = "\n".join(file_paths).lower()
    skills = [skill for marker, skill in skill_markers if marker in joined_paths]
    return role, ", ".join(skills[:6]) if skills else "Git commit"


def extract_developers_from_git_commits(db: Session, project_id: int) -> DeveloperExtractionResult:
    result = DeveloperExtractionResult()
    commits = db.query(GitCommit).filter(GitCommit.project_id == project_id).all()

    author_names: dict[str, str] = {}
    author_emails: dict[str, str | None] = {}
    file_paths_by_key: dict[str, list[str]] = defaultdict(list)

    for commit in commits:
        developer_key = make_developer_key(commit.author_name or commit.author, commit.author_email)
        author_names[developer_key] = commit.author_name or commit.author or developer_key
        author_emails[developer_key] = commit.author_email
        file_paths_by_key[developer_key].extend(file.file_path for file in commit.files)

    for developer_key, developer_name in author_names.items():
        developer = db.query(Developer).filter(Developer.developer_key == developer_key).one_or_none()
        if developer is None and author_emails[developer_key]:
            developer = db.query(Developer).filter(Developer.email == author_emails[developer_key]).one_or_none()

        role, skills = infer_role_and_skills(file_paths_by_key[developer_key])
        if developer is None:
            developer = Developer(
                developer_key=developer_key,
                developer_id=developer_key,
                developer_name=developer_name,
                email=author_emails[developer_key],
                role=role,
                skills=skills,
            )
            db.add(developer)
            result.created_count += 1
            continue

        changed = False
        if not developer.developer_key:
            developer.developer_key = developer_key
            changed = True
        if not developer.email and author_emails[developer_key]:
            developer.email = author_emails[developer_key]
            changed = True
        if not developer.developer_name or developer.developer_name == developer.developer_id:
            developer.developer_name = developer_name
            changed = True
        if not developer.role:
            developer.role = role
            changed = True
        if not developer.skills:
            developer.skills = skills
            changed = True

        if changed:
            result.updated_count += 1
        else:
            result.skipped_count += 1

    db.commit()
    return result


def get_developer_stats(db: Session, project_id: int) -> list[dict]:
    commits = db.query(GitCommit).filter(GitCommit.project_id == project_id).all()
    by_key: dict[str, dict] = {}

    for commit in commits:
        developer_key = make_developer_key(commit.author_name or commit.author, commit.author_email)
        item = by_key.setdefault(
            developer_key,
            {
                "author_name": commit.author_name or commit.author or developer_key,
                "author_email": commit.author_email,
                "commit_count": 0,
                "file_count": 0,
            },
        )
        item["commit_count"] += 1
        item["file_count"] += len(commit.files)
        if not item["author_email"] and commit.author_email:
            item["author_email"] = commit.author_email

    stats = []
    for developer_key, item in by_key.items():
        developer = db.query(Developer).filter(Developer.developer_key == developer_key).one_or_none()
        if developer is None and item["author_email"]:
            developer = db.query(Developer).filter(Developer.email == item["author_email"]).one_or_none()

        stats.append(
            {
                "developer_id": developer.id if developer else None,
                "developer_key": developer_key,
                "developer_name": developer.developer_name if developer else item["author_name"],
                "email": item["author_email"],
                "role": developer.role if developer else "",
                "skills": developer.skills if developer else "",
                "commit_count": item["commit_count"],
                "file_count": item["file_count"],
            }
        )
    return sorted(stats, key=lambda item: item["commit_count"], reverse=True)


def update_developer_profile(db: Session, developer_id: int, role: str | None, skills: str | None) -> None:
    developer = db.get(Developer, developer_id)
    if developer is None:
        return
    developer.role = role or None
    developer.skills = skills or None
    db.commit()
