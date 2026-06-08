from scripts.generate_sample_development_data import classify_file, infer_role_and_skills, module_from_path
import pandas as pd

from scripts.create_sample_target_repo import (
    DEVELOPERS,
    PROGRAM_ROWS,
    _apply_demo_plan_overrides,
    _apply_developer_profiles,
    _commit_steps,
)


def test_python_controller_and_service_paths_are_backend() -> None:
    assert classify_file("src/market_ops/controllers/order_controller.py") == "backend"
    assert classify_file("src/market_ops/services/order_service.py") == "backend"


def test_python_repository_path_is_database() -> None:
    assert classify_file("src/market_ops/repositories/order_repository.py") == "database"


def test_spring_mybatis_paths_are_classified_by_layer() -> None:
    assert classify_file("src/main/java/com/example/market/order/controller/OrderController.java") == "backend"
    assert classify_file("src/main/java/com/example/market/order/service/OrderService.java") == "backend"
    assert classify_file("src/main/java/com/example/market/order/mapper/OrderMapper.java") == "database"
    assert classify_file("src/main/resources/mappers/OrderMapper.xml") == "database"
    assert classify_file("src/main/webapp/WEB-INF/views/orders/new.jsp") == "other"


def test_python_module_name_strips_layer_suffix() -> None:
    assert module_from_path("src/market_ops/controllers/order_controller.py") == "order"
    assert module_from_path("src/market_ops/services/payment_service.py") == "payment"


def test_python_paths_infer_specific_skills() -> None:
    role, skills = infer_role_and_skills(
        [
            "src/market_ops/controllers/order_controller.py",
            "src/market_ops/services/order_service.py",
            "src/market_ops/repositories/order_repository.py",
        ]
    )

    assert role == "Backend Developer"
    assert "Python" in skills
    assert "Service Layer" in skills


def test_sample_target_repo_is_spring_mybatis_shaped() -> None:
    all_paths = {
        path
        for step in _commit_steps()
        for path in step.files
    }

    assert "pom.xml" in all_paths
    assert any(path.endswith("OrderController.java") for path in all_paths)
    assert any(path.endswith("OrderMapper.java") for path in all_paths)
    assert any(path.endswith("OrderMapper.xml") for path in all_paths)
    assert any(path.endswith("dashboard/index.jsp") for path in all_paths)
    assert all(".py" not in row["Controller"] for row in PROGRAM_ROWS)


def test_sample_target_repo_has_rich_demo_commit_history() -> None:
    steps = _commit_steps()
    messages = {step.message for step in steps}
    all_paths = {path for step in steps for path in step.files}

    assert len(steps) == 30
    assert "Relax partner payment validation for pilot channel" in messages
    assert "Reject zero and negative payment amounts" in messages
    assert "Change dashboard summary query across operations modules" in messages
    assert "Fix dashboard summary over-counting" in messages
    assert "Add coupon discount service skeleton" in messages
    assert "Add release verification checklist" in messages
    assert "docs/review-targets/payment-zero-amount-risk.md" in all_paths
    assert "docs/business-rules/payment-inventory-rules.md" in all_paths
    assert "docs/demo-guide.md" in all_paths


def test_sample_program_rows_include_risk_demo_programs() -> None:
    program_ids = {row["프로그램ID"] for row in PROGRAM_ROWS}

    assert len(PROGRAM_ROWS) == 8
    assert {"SMP-CPN-001", "SMP-SET-001"}.issubset(program_ids)


def test_sample_target_repo_uses_korean_developer_names() -> None:
    names = {developer.name for developer in DEVELOPERS.values()}

    assert names == {"최현우", "오세훈", "김민수", "이지은", "박지훈", "정서연"}


def test_sample_target_repo_uses_public_si_roles() -> None:
    developers = pd.DataFrame(
        [
            {"developer_name": "최현우", "email": "hyunwoo.choi@sample.local", "role": "", "skills": ""},
            {"developer_name": "오세훈", "email": "sehun.oh@sample.local", "role": "", "skills": ""},
            {"developer_name": "김민수", "email": "minsu.kim@sample.local", "role": "", "skills": ""},
            {"developer_name": "이지은", "email": "jieun.lee@sample.local", "role": "", "skills": ""},
            {"developer_name": "박지훈", "email": "jihoon.park@sample.local", "role": "", "skills": ""},
            {"developer_name": "정서연", "email": "seoyeon.jung@sample.local", "role": "", "skills": ""},
        ]
    )

    profiled = _apply_developer_profiles(developers)

    assert set(profiled["role"]) == {"PM", "PL", "개발자", "QA"}


def test_sample_plan_overrides_create_risk_demo_rows() -> None:
    plan = pd.DataFrame(
        [
            {
                "program_id": "SMP-CPN-001",
                "developer_id": "",
                "planned_start_date": "",
                "planned_end_date": "",
                "actual_start_date": "",
                "actual_end_date": "",
                "status": "",
                "progress_rate": 0,
            },
            {
                "program_id": "SMP-SET-001",
                "developer_id": "DEV_JIEUN_LEE",
                "planned_start_date": "",
                "planned_end_date": "",
                "actual_start_date": "",
                "actual_end_date": "",
                "status": "",
                "progress_rate": 0,
            },
        ]
    )

    overridden = _apply_demo_plan_overrides(plan)
    coupon = overridden[overridden["program_id"] == "SMP-CPN-001"].iloc[0]
    settlement = overridden[overridden["program_id"] == "SMP-SET-001"].iloc[0]

    assert coupon["developer_id"] == "DEV_JIEUN_LEE"
    assert coupon["status"] == "지연"
    assert coupon["progress_rate"] == 80
    assert settlement["developer_id"] == ""
    assert settlement["status"] == "지연"
    assert settlement["progress_rate"] == 45
