# AI Change Log

## 2026-06-08

### 매핑 피드백 기능 추가

- `program_commit_mappings`에 사용자 피드백 컬럼을 추가했습니다.
- 매핑 화면에 `매핑 피드백` 모드를 추가했습니다.
- 사용자가 AI 매핑 결과의 관련 여부, 관련도 점수, 구현상태, 판단 근거를 보정할 수 있게 했습니다.
- 보정된 매핑값이 `Commit Impact`, `Program Detail`, `AI Progress`, `Risk Analysis`에서 사용되도록 관련 서비스 로직을 조정했습니다.

### 테스트 추가

- `pytest`를 개발 의존성에 추가했습니다.
- 매핑 후보 점수, LLM JSON 파싱, Git diff path 파싱, 상태 정규화, 피드백 상태 정규화 테스트를 추가했습니다.

### 검증

- `python -m py_compile app.py src\db\models.py src\db\init_db.py src\services\mapping_feedback_service.py src\services\commit_impact_service.py src\services\progress_service.py src\services\risk_service.py src\services\program_analysis_service.py src\ui\mapping_page.py` 통과.
- `.venv\Scripts\python.exe -m pytest -q` 통과.
- 테스트 결과: `7 passed`.
