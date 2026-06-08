from scripts.generate_sample_development_data import classify_file, infer_role_and_skills, module_from_path
import pandas as pd

from scripts.create_sample_target_repo import DEVELOPERS, PROGRAM_ROWS, _apply_developer_profiles, _commit_steps


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
