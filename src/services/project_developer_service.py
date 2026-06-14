from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import Developer, ProjectDeveloper


def link_project_developer(
    db: Session,
    project_id: int | None,
    developer_id: str,
    source: str,
    project_role: str | None = None,
) -> ProjectDeveloper | None:
    if project_id is None or not developer_id:
        return None

    membership = (
        db.query(ProjectDeveloper)
        .filter(ProjectDeveloper.project_id == project_id, ProjectDeveloper.developer_id == developer_id)
        .one_or_none()
    )
    if membership is None:
        membership = ProjectDeveloper(project_id=project_id, developer_id=developer_id)
        db.add(membership)

    membership.source = source
    membership.project_role = project_role or membership.project_role
    membership.active_yn = "Y"
    return membership


def list_project_developers(db: Session, project_id: int, keyword: str | None = None) -> list[Developer]:
    query = (
        db.query(Developer)
        .join(ProjectDeveloper, ProjectDeveloper.developer_id == Developer.developer_id)
        .filter(ProjectDeveloper.project_id == project_id, ProjectDeveloper.active_yn == "Y")
    )
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (Developer.developer_id.ilike(pattern))
            | (Developer.developer_name.ilike(pattern))
            | (Developer.email.ilike(pattern))
            | (Developer.role.ilike(pattern))
        )
    return query.order_by(Developer.developer_name, Developer.developer_id).limit(500).all()


def list_global_developers(db: Session, keyword: str | None = None) -> list[Developer]:
    query = db.query(Developer)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            (Developer.developer_id.ilike(pattern))
            | (Developer.developer_name.ilike(pattern))
            | (Developer.email.ilike(pattern))
            | (Developer.role.ilike(pattern))
        )
    return query.order_by(Developer.developer_name, Developer.developer_id).limit(500).all()
