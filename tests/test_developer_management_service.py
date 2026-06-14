from io import BytesIO
import uuid

import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError

from src.db.database import SessionLocal
from src.db.init_db import init_db
from src.db.models import CommitFile, Developer, GitCommit, Project, ProjectDeveloper
from src.services.developer_service import extract_developers_from_git_commits
from src.services.developer_management_service import (
    build_developer_template_excel,
    delete_developer,
    existing_developer_ids,
    normalize_developer_payload,
    save_developers_with_result,
    save_manual_developer,
    validate_developer_import,
    validate_developer_payload,
)
from src.services.project_developer_service import list_global_developers, list_project_developers


def test_validate_developer_payload_requires_id_and_name():
    validation = validate_developer_payload({"developer_id": "", "developer_name": ""})

    assert validation.is_valid is False
    assert "developer_id" in validation.errors[0]
    assert "developer_name" in validation.errors[1]


def test_normalize_developer_payload_strips_text():
    normalized = normalize_developer_payload(
        {
            "developer_id": " dev001 ",
            "developer_name": " Hong ",
            "email": " hong@example.com ",
            "role": " Backend ",
            "skills": " Python ",
        }
    )

    assert normalized["developer_id"] == "dev001"
    assert normalized["developer_name"] == "Hong"
    assert normalized["email"] == "hong@example.com"
    assert normalized["role"] == "Backend"
    assert normalized["skills"] == "Python"


def test_validate_developer_import_counts_new_update_and_duplicate():
    df = pd.DataFrame(
        [
            {"developer_id": "dev001", "developer_name": "Existing"},
            {"developer_id": "dev002", "developer_name": "New"},
            {"developer_id": "dev002", "developer_name": "Duplicate"},
            {"developer_id": "", "developer_name": "Missing ID"},
        ]
    )

    result = validate_developer_import(df, existing_developer_ids={"dev001"})

    assert result.update_count == 1
    assert result.new_count == 1
    assert result.error_count == 2
    assert len(result.valid_rows) == 2
    assert "중복" in result.preview_rows[2]["errors"]


def test_build_developer_template_excel_contains_required_columns():
    excel_bytes = build_developer_template_excel()
    df = pd.read_excel(BytesIO(excel_bytes))

    assert {"developer_id", "developer_name"}.issubset(set(df.columns))


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def test_manual_and_excel_save_create_project_memberships():
    init_db()
    with SessionLocal() as db:
        project = Project(name=_unique("developer-membership-project"))
        db.add(project)
        db.commit()
        db.refresh(project)
        manual_id = _unique("manual-dev")
        excel_id = _unique("excel-dev")
        try:
            manual_validation = save_manual_developer(
                db,
                {
                    "developer_id": manual_id,
                    "developer_name": "Manual Dev",
                    "email": f"{manual_id}@example.local",
                    "role": "Backend Developer",
                    "skills": "Python",
                },
                project_id=project.id,
            )
            excel_result = save_developers_with_result(
                db,
                [
                    {
                        "developer_id": excel_id,
                        "developer_name": "Excel Dev",
                        "email": f"{excel_id}@example.local",
                        "role": "Frontend Developer",
                        "skills": "JavaScript",
                    }
                ],
                project_id=project.id,
                source="excel",
            )

            assert manual_validation.is_valid
            assert excel_result.created_count == 1
            assert existing_developer_ids(db).issuperset({manual_id, excel_id})
            memberships = (
                db.query(ProjectDeveloper)
                .filter(ProjectDeveloper.project_id == project.id)
                .order_by(ProjectDeveloper.developer_id)
                .all()
            )
            assert [membership.developer_id for membership in memberships] == sorted([excel_id, manual_id])
            assert {membership.source for membership in memberships} == {"excel", "manual"}
            assert {developer.developer_id for developer in list_project_developers(db, project.id)} == {
                manual_id,
                excel_id,
            }
            assert {developer.developer_id for developer in list_global_developers(db, manual_id)} == {manual_id}
        finally:
            db.delete(project)
            db.query(Developer).filter(Developer.developer_id.in_([manual_id, excel_id])).delete(
                synchronize_session=False
            )
            db.commit()


def test_save_without_project_keeps_global_developer_without_membership():
    init_db()
    developer_id = _unique("global-only-dev")
    with SessionLocal() as db:
        try:
            result = save_developers_with_result(
                db,
                [{"developer_id": developer_id, "developer_name": "Global Only"}],
                project_id=None,
            )

            assert result.created_count == 1
            assert db.query(Developer).filter(Developer.developer_id == developer_id).count() == 1
            assert db.query(ProjectDeveloper).filter(ProjectDeveloper.developer_id == developer_id).count() == 0
        finally:
            db.query(Developer).filter(Developer.developer_id == developer_id).delete(synchronize_session=False)
            db.commit()


def test_git_author_extraction_reuses_global_developer_and_links_each_project():
    init_db()
    email = f"{uuid.uuid4()}@example.local"
    with SessionLocal() as db:
        project_a = Project(name=_unique("git-author-a"))
        project_b = Project(name=_unique("git-author-b"))
        db.add_all([project_a, project_b])
        db.flush()
        for project in [project_a, project_b]:
            commit = GitCommit(
                project_id=project.id,
                commit_hash=uuid.uuid4().hex,
                message="Author commit",
                author_name="Shared Author",
                author_email=email,
            )
            db.add(commit)
            db.flush()
            db.add(
                CommitFile(
                    commit_id=commit.id,
                    git_commit_id=commit.id,
                    file_path="src/service.py",
                    change_type="Modified",
                    diff_text="+service",
                )
            )
        db.commit()

        try:
            result_a = extract_developers_from_git_commits(db, project_a.id)
            result_a_repeat = extract_developers_from_git_commits(db, project_a.id)
            result_b = extract_developers_from_git_commits(db, project_b.id)

            developer = db.query(Developer).filter(Developer.email == email).one()
            assert result_a.created_count == 1
            assert result_a_repeat.created_count == 0
            assert result_b.created_count == 0
            assert db.query(ProjectDeveloper).filter(ProjectDeveloper.developer_id == developer.developer_id).count() == 2
            assert {
                membership.project_id
                for membership in db.query(ProjectDeveloper).filter(
                    ProjectDeveloper.developer_id == developer.developer_id
                )
            } == {project_a.id, project_b.id}
        finally:
            db.delete(project_a)
            db.delete(project_b)
            db.query(Developer).filter(Developer.email == email).delete(synchronize_session=False)
            db.commit()


def test_project_and_developer_delete_cascade_memberships():
    init_db()
    developer_id = _unique("cascade-dev")
    with SessionLocal() as db:
        project = Project(name=_unique("cascade-project"))
        developer = Developer(
            developer_key=_unique("cascade-key"),
            developer_id=developer_id,
            developer_name="Cascade Dev",
        )
        db.add_all([project, developer])
        db.flush()
        membership = ProjectDeveloper(project_id=project.id, developer_id=developer.developer_id, source="manual")
        db.add(membership)
        db.commit()
        project_id = project.id
        developer_pk = developer.id

        db.delete(project)
        db.commit()
        assert db.query(ProjectDeveloper).filter(ProjectDeveloper.project_id == project_id).count() == 0
        assert db.get(Developer, developer_pk) is not None

        project = Project(name=_unique("developer-delete-cascade-project"))
        db.add(project)
        db.flush()
        db.add(ProjectDeveloper(project_id=project.id, developer_id=developer_id, source="manual"))
        db.commit()

        delete_developer(db, developer_pk)

        assert db.query(ProjectDeveloper).filter(ProjectDeveloper.developer_id == developer_id).count() == 0
        assert db.get(Developer, developer_pk) is None
        db.delete(project)
        db.commit()


def test_project_developer_unique_constraint_blocks_duplicates():
    init_db()
    developer_id = _unique("unique-membership-dev")
    with SessionLocal() as db:
        project = Project(name=_unique("unique-membership-project"))
        developer = Developer(
            developer_key=_unique("unique-membership-key"),
            developer_id=developer_id,
            developer_name="Unique Membership Dev",
        )
        db.add_all([project, developer])
        db.flush()
        db.add_all(
            [
                ProjectDeveloper(project_id=project.id, developer_id=developer_id, source="manual"),
                ProjectDeveloper(project_id=project.id, developer_id=developer_id, source="excel"),
            ]
        )

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()
