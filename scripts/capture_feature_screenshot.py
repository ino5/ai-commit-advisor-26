from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
import os
from pathlib import Path
import sys

from PIL import Image
from playwright.sync_api import Error, Page, sync_playwright


@dataclass(frozen=True)
class FeatureScenario:
    name: str
    sidebar_label: str | None
    wait_text: str
    required_texts: tuple[str, ...]
    forbidden_texts: tuple[str, ...] = field(default_factory=tuple)
    default_screenshot: str = ""
    description: str = ""
    verify_sidebar_stability: bool = False
    scroll_to_text: str | None = None
    full_page: bool = True
    tab_label: str | None = None
    fill_label: str | None = None
    fill_value: str | None = None
    click_label: str | None = None
    button_label: str | None = None
    button_before_tab: bool = False
    action_wait_text: str | None = None
    crop_box: tuple[int, int, int, int] | None = None


SCENARIOS: dict[str, FeatureScenario] = {
    "home": FeatureScenario(
        name="home",
        sidebar_label="Home",
        wait_text="분석 상태",
        required_texts=(
            "AI Commit Advisor",
            "계획, 커밋, 진척도, 리스크 현황",
            "Dashboard",
            "AI Progress",
            "프로젝트 설정",
            "분석 상태",
            "다음 작업",
            "추정 진척도",
        ),
        forbidden_texts=(
            "분석 파이프라인 상태",
            "업무 의미",
            "AI 분석 결과는 근거 데이터와 함께 검증하는 보조 지표로 활용하세요.",
        ),
        default_screenshot="docs/images/features/home.png",
        description="Home 분석 관제 화면",
        verify_sidebar_stability=True,
    ),
    "project": FeatureScenario(
        name="project",
        sidebar_label="프로젝트/Git 설정",
        wait_text="프로젝트 저장",
        required_texts=(
            "프로젝트/Git 설정",
            "프로젝트 저장",
            "앱 서버 Git 저장소 경로",
            "Git remote URL",
            "서버 저장소 clone/fetch",
            "분석 데이터 초기화",
        ),
        default_screenshot="docs/images/features/project.png",
        description="프로젝트/Git 설정 화면",
    ),
    "project-operations": FeatureScenario(
        name="project-operations",
        sidebar_label="프로젝트/Git 설정",
        wait_text="분석 데이터 초기화",
        required_texts=(
            "프로젝트/Git 설정",
            "앱 서버 저장소 상태",
            "서버 저장소 clone/fetch",
            "분석 데이터 초기화",
            "프로젝트 삭제",
        ),
        default_screenshot="docs/images/features/project-operations.png",
        description="프로젝트/Git 설정 운영 action 화면",
        scroll_to_text="서버 저장소 clone/fetch",
    ),
    "developer": FeatureScenario(
        name="developer",
        sidebar_label="개발자 현황",
        wait_text="개발자 목록",
        required_texts=("Developer", "개발자별 커밋 수", "개발자 목록"),
        default_screenshot="docs/images/features/developer.png",
        description="개발자 현황 화면",
    ),
    "developer-upload": FeatureScenario(
        name="developer-upload",
        sidebar_label="개발자 목록",
        wait_text="현재 프로젝트 개발자",
        required_texts=("개발자 관리", "현재 프로젝트 개발자", "직접 추가"),
        default_screenshot="docs/images/features/developer-upload.png",
        description="개발자 목록 관리 화면",
    ),
    "program-upload": FeatureScenario(
        name="program-upload",
        sidebar_label="프로그램 목록",
        wait_text="현재 프로그램 데이터",
        required_texts=("프로그램 관리", "현재 프로그램 데이터", "직접 추가"),
        default_screenshot="docs/images/features/program-upload.png",
        description="프로그램 목록 관리 화면",
    ),
    "development-plan-upload": FeatureScenario(
        name="development-plan-upload",
        sidebar_label="개발계획",
        wait_text="현재 개발계획",
        required_texts=("개발계획 관리", "현재 개발계획", "직접 수정"),
        default_screenshot="docs/images/features/development-plan-upload.png",
        description="개발계획 관리 화면",
    ),
    "git-sync": FeatureScenario(
        name="git-sync",
        sidebar_label="Git 동기화",
        wait_text="앱 서버 저장소 상태",
        required_texts=("Git 동기화", "증분 동기화", "앱 서버 저장소 상태"),
        default_screenshot="docs/images/features/git-sync.png",
        description="Git 동기화 화면",
    ),
    "project-chat": FeatureScenario(
        name="project-chat",
        sidebar_label="Project Chat",
        wait_text="현재 코드에서 확인된 소스 근거를 찾아 프로젝트 질문에 답합니다.",
        required_texts=(
            "Project Chat",
            "현재 코드에서 확인된 소스 근거를 찾아 프로젝트 질문에 답합니다.",
            "답변 근거 상태",
            "코드 반영 상태",
            "최신 변경분 반영",
            "전체 소스 다시 읽기",
            "대화 관리",
            "저장된 대화",
            "새 대화 시작",
        ),
        forbidden_texts=(
            "Project Chat의 재인덱싱은 PC 부하",
            "chunk만 갱신합니다",
            "현재 소스 파일에서 검증된 RAG 근거로 프로젝트 질문에 답합니다.",
        ),
        default_screenshot="docs/images/features/project-chat.png",
        description="Project Chat 질문/근거 화면",
        scroll_to_text="현재 코드에서 확인된 소스 근거를 찾아 프로젝트 질문에 답합니다.",
    ),
    "git-history": FeatureScenario(
        name="git-history",
        sidebar_label="Git History",
        wait_text="현재 프로젝트의 Git 커밋 이력",
        required_texts=(
            "Git History",
            "현재 프로젝트의 Git 커밋 이력",
            "커밋 목록",
            "조회 커밋",
            "변경 파일",
            "전체 diff",
        ),
        forbidden_texts=(),
        default_screenshot="docs/images/features/git-history.png",
        description="Git History 커밋 이력/diff 탐색 화면",
    ),
    "git-history-detail": FeatureScenario(
        name="git-history-detail",
        sidebar_label="Git History",
        wait_text="현재 프로젝트의 Git 커밋 이력",
        required_texts=(
            "Git History",
            "커밋 상세",
            "변경 파일",
            "저장된 diff preview",
            "전체 diff",
        ),
        forbidden_texts=(),
        default_screenshot="docs/images/features/git-history-detail.png",
        description="Git History 커밋 상세/diff preview 화면",
        scroll_to_text="저장된 diff preview",
    ),
    "sample-data": FeatureScenario(
        name="sample-data",
        sidebar_label="샘플 데이터 생성",
        wait_text="앱 서버 Git 저장소 경로",
        required_texts=("샘플 데이터 생성", "앱 서버 Git 저장소 경로", "샘플 데이터 생성"),
        default_screenshot="docs/images/features/sample-data.png",
        description="샘플 데이터 생성 화면",
    ),
    "standard-terms": FeatureScenario(
        name="standard-terms",
        sidebar_label="표준용어/표준단어",
        wait_text="현재 표준용어/표준단어",
        required_texts=("표준용어/표준단어", "현재 표준용어/표준단어", "Excel 업로드"),
        default_screenshot="docs/images/features/standard-terms.png",
        description="표준용어/표준단어 관리 화면",
    ),
    "mapping": FeatureScenario(
        name="mapping",
        sidebar_label="Mapping",
        wait_text="커밋 기준 분석",
        required_texts=(
            "프로그램-커밋 매핑 분석",
            "프로그램 수",
            "Git 커밋 수",
            "미완료 커밋",
            "완료 커밋",
            "실패 커밋",
        ),
        default_screenshot="docs/images/features/mapping.png",
        description="Mapping 커밋 기준 분석 완료 화면",
    ),
    "risk-analysis": FeatureScenario(
        name="risk-analysis",
        sidebar_label="Risk Analysis",
        wait_text="리스크 프로그램 목록",
        required_texts=(
            "Risk Analysis",
            "전체 리스크",
            "MEDIUM",
            "리스크 유형",
            "계획 대비 AI 진척 차이",
        ),
        default_screenshot="docs/images/features/risk-analysis.png",
        description="Risk Analysis 리스크 탐지 결과 화면",
    ),
    "risk-analysis-list": FeatureScenario(
        name="risk-analysis-list",
        sidebar_label="Risk Analysis",
        wait_text="리스크 프로그램 목록",
        required_texts=(
            "Risk Analysis",
            "리스크 프로그램 목록",
            "리스크 수준",
            "Resolved 처리",
        ),
        default_screenshot="docs/images/features/risk-analysis-list.png",
        description="Risk Analysis 리스크 목록/처리 화면",
        scroll_to_text="리스크 프로그램 목록",
    ),
    "program-detail": FeatureScenario(
        name="program-detail",
        sidebar_label="Program Detail",
        wait_text="프로그램 선택",
        required_texts=("Program Detail", "프로그램 선택", "기본 정보"),
        default_screenshot="docs/images/features/program-detail.png",
        description="Program Detail 화면",
    ),
    "program-detail-analysis": FeatureScenario(
        name="program-detail-analysis",
        sidebar_label="Program Detail",
        wait_text="구현상태 분석",
        required_texts=(
            "Program Detail",
            "구현상태 분석",
            "구현상태",
            "상태 요약",
        ),
        default_screenshot="docs/images/features/program-detail-analysis.png",
        description="Program Detail 구현상태 분석 상세 화면",
        scroll_to_text="구현상태 분석",
    ),
    "commit-impact": FeatureScenario(
        name="commit-impact",
        sidebar_label="Commit Impact",
        wait_text="커밋 선택",
        required_texts=("Commit Impact", "커밋 선택"),
        default_screenshot="docs/images/features/commit-impact.png",
        description="Commit Impact 커밋 선택 화면",
    ),
    "knowledge-graph": FeatureScenario(
        name="knowledge-graph",
        sidebar_label="Knowledge Graph",
        wait_text="Neo4j에 node",
        required_texts=(
            "Knowledge Graph",
            "Neo4j",
            "연결",
            "ON",
            "Neo4j에 node",
            "Neo4j 저장 확인",
            "동기화 대상 요약",
            "도메인 묶음",
            "클래스 관계도",
            "영향 경로",
            "노드/엣지",
        ),
        forbidden_texts=("NEO4J_ENABLED=false",),
        default_screenshot="docs/images/features/knowledge-graph.png",
        description="Neo4j Knowledge Graph 동기화 완료 화면",
        button_label="Neo4j 동기화",
        action_wait_text="Neo4j에 node",
    ),
    "knowledge-graph-class": FeatureScenario(
        name="knowledge-graph-class",
        sidebar_label="Knowledge Graph",
        wait_text="Neo4j 저장 그래프 기준",
        required_texts=(
            "Knowledge Graph",
            "Neo4j에 node",
            "클래스 관계도",
            "Neo4j 저장 그래프 기준",
            "PaymentService",
            "OrderMapper",
        ),
        forbidden_texts=("NEO4J_ENABLED=false",),
        default_screenshot="docs/images/features/knowledge-graph-class.png",
        description="Neo4j Knowledge Graph 클래스 관계도 화면",
        tab_label="클래스 관계도",
        button_label="Neo4j 동기화",
        button_before_tab=True,
        action_wait_text="Neo4j 저장 확인",
    ),
    "knowledge-graph-impact": FeatureScenario(
        name="knowledge-graph-impact",
        sidebar_label="Knowledge Graph",
        wait_text="Neo4j 저장 그래프 기준",
        required_texts=(
            "Knowledge Graph",
            "Neo4j에 node",
            "영향 경로",
            "Neo4j 저장 그래프 기준",
            "커밋",
            "프로그램",
            "파일",
            "클래스",
            "도메인",
        ),
        forbidden_texts=("NEO4J_ENABLED=false",),
        default_screenshot="docs/images/features/knowledge-graph-impact.png",
        description="Neo4j Knowledge Graph 영향 경로 화면",
        tab_label="영향 경로",
        button_label="Neo4j 동기화",
        button_before_tab=True,
        action_wait_text="Neo4j 저장 확인",
    ),
    "knowledge-graph-nodes-edges": FeatureScenario(
        name="knowledge-graph-nodes-edges",
        sidebar_label="Knowledge Graph",
        wait_text="Neo4j에서 조회한 저장 상태입니다.",
        required_texts=(
            "Knowledge Graph",
            "Neo4j 저장 확인",
            "노드/엣지",
            "Neo4j에서 조회한 저장 상태입니다.",
            "Node",
            "Edge",
            "class",
            "commit",
            "IMPORTS_CLASS",
            "MAPPED_TO_COMMIT",
        ),
        forbidden_texts=("NEO4J_ENABLED=false",),
        default_screenshot="docs/images/features/knowledge-graph-nodes-edges.png",
        description="Neo4j Knowledge Graph 노드/엣지 저장 상태 화면",
        tab_label="노드/엣지",
        button_label="Neo4j 동기화",
        button_before_tab=True,
        action_wait_text="Neo4j 저장 확인",
    ),
    "planning-dashboard": FeatureScenario(
        name="planning-dashboard",
        sidebar_label="개발계획 대시보드",
        wait_text="상태별 프로그램 수",
        required_texts=("개발계획 대시보드", "전체 프로그램", "상태별 프로그램 수"),
        default_screenshot="docs/images/features/planning-dashboard.png",
        description="개발계획 대시보드 화면",
    ),
    "ai-progress": FeatureScenario(
        name="ai-progress",
        sidebar_label="AI Progress",
        wait_text="프로그램별 비교",
        required_texts=(
            "AI Progress",
            "계획 진척도 평균",
            "AI 진척도 평균",
            "진척도 차이",
            "프로그램 단위 구현상태 분석",
        ),
        default_screenshot="docs/images/features/ai-progress.png",
        description="AI Progress 계획 대비 AI 진척도 비교 화면",
    ),
    "ai-progress-detail": FeatureScenario(
        name="ai-progress-detail",
        sidebar_label="AI Progress",
        wait_text="프로그램별 비교",
        required_texts=(
            "AI Progress",
            "프로그램별 비교",
            "관련 커밋 상세",
            "프로그램 선택",
        ),
        default_screenshot="docs/images/features/ai-progress-detail.png",
        description="AI Progress 프로그램별 상세 비교 화면",
        scroll_to_text="프로그램별 비교",
    ),
    "dashboard-overview": FeatureScenario(
        name="dashboard-overview",
        sidebar_label="Dashboard",
        wait_text="프로젝트 현황",
        required_texts=(
            "Dashboard",
            "프로젝트 현황",
            "AI Resource Radar",
            "최근 분석 결과",
            "개발자 Git 활동",
        ),
        default_screenshot="docs/images/features/dashboard-overview.png",
        description="Dashboard 프로젝트 현황 화면",
    ),
    "dashboard-radar": FeatureScenario(
        name="dashboard-radar",
        sidebar_label="Dashboard",
        wait_text="AI Resource Radar",
        required_texts=(
            "Dashboard",
            "AI Resource Radar",
            "PL Briefing 생성",
            "Radar 근거 상세",
        ),
        default_screenshot="docs/images/features/dashboard-radar.png",
        description="Dashboard AI Resource Radar 화면",
        scroll_to_text="AI Resource Radar",
    ),
    "dashboard-pl-briefing": FeatureScenario(
        name="dashboard-pl-briefing",
        sidebar_label="Dashboard",
        wait_text="AI Resource Radar",
        required_texts=(
            "Dashboard",
            "AI Resource Radar",
            "PL Briefing 생성",
            "provider=local_openai",
            "mode=LLM 생성",
            "최근 저장된 PL Briefing",
            "PL Briefing 이력",
            "PL 주간 점검 브리핑",
            "요약",
            "우선 확인 항목",
            "회의 질문",
            "다음 액션",
        ),
        default_screenshot="docs/images/features/dashboard-pl-briefing.png",
        description="Dashboard PL Briefing LLM 생성 결과 화면",
        scroll_to_text="AI Resource Radar",
        button_label="PL Briefing 생성",
        action_wait_text="mode=LLM 생성",
    ),
    "dashboard-pl-briefing-actions": FeatureScenario(
        name="dashboard-pl-briefing-actions",
        sidebar_label="Dashboard",
        wait_text="AI Resource Radar",
        required_texts=(
            "Dashboard",
            "AI Resource Radar",
            "provider=local_openai",
            "mode=LLM 생성",
            "최근 저장된 PL Briefing",
            "PL 주간 점검 브리핑",
            "회의 질문",
            "다음 액션",
        ),
        default_screenshot="docs/images/features/dashboard-pl-briefing-actions.png",
        description="Dashboard PL Briefing 회의 질문과 다음 액션 화면",
        scroll_to_text="회의 질문",
        button_label="PL Briefing 생성",
        action_wait_text="mode=LLM 생성",
        crop_box=(300, 2200, 1440, 3100),
    ),
    "dashboard": FeatureScenario(
        name="dashboard",
        sidebar_label="Dashboard",
        wait_text="자원관리 지표",
        required_texts=(
            "Dashboard",
            "프로젝트 현황",
            "AI Resource Radar",
            "자원관리 지표",
            "예상 지연 프로그램",
            "개발자별 부하",
            "예상 지연/난이도",
            "추가 투입 예방 가능성",
        ),
        default_screenshot="docs/images/features/dashboard.png",
        description="Dashboard 자원관리 지표 화면",
        scroll_to_text="자원관리 지표",
    ),
    "ai-evidence": FeatureScenario(
        name="ai-evidence",
        sidebar_label="AI 운영 현황",
        wait_text="AI 운영 현황",
        required_texts=(
            "AI 운영 현황",
            "연결된 AI",
            "운영 준비",
            "AI 실행 바로가기",
            "Mapping 실행",
            "운영 준비 요약",
            "주의/실패 우선 확인",
            "근거 추적",
            "품질 점검",
            "주간 보고서",
            "호출 기록",
        ),
        default_screenshot="docs/images/features/ai-evidence.png",
        description="AI 운영 현황과 근거 추적 화면",
    ),
    "rag-search": FeatureScenario(
        name="rag-search",
        sidebar_label="RAG 검색",
        wait_text="조회된 근거 목록",
        required_texts=(
            "RAG 검색",
            "근거 조각",
            "검색 데이터",
            "검색 품질 확인",
            "검색어:",
            "조회된 근거 목록",
        ),
        default_screenshot="docs/images/features/rag-search.png",
        description="RAG 검색 결과 화면",
        tab_label="검색 확인",
        fill_label="검색어",
        fill_value="payment amount validation PaymentService",
        click_label="검색",
        action_wait_text="조회된 근거 목록",
    ),
    "rag-search-results": FeatureScenario(
        name="rag-search-results",
        sidebar_label="RAG 검색",
        wait_text="조회된 근거 목록",
        required_texts=(
            "RAG 검색",
            "검색 품질 확인",
            "조회된 근거 목록",
            "PaymentService.java",
        ),
        default_screenshot="docs/images/features/rag-search-results.png",
        description="RAG 검색 결과 목록 화면",
        tab_label="검색 확인",
        fill_label="검색어",
        fill_value="payment amount validation PaymentService",
        click_label="검색",
        action_wait_text="조회된 근거 목록",
        scroll_to_text="조회된 근거 목록",
    ),
    "project-chat-answer": FeatureScenario(
        name="project-chat-answer",
        sidebar_label="Project Chat",
        wait_text="결제금액 검증은",
        required_texts=(
            "Project Chat",
            "결제금액 검증은",
            "PaymentService.java",
            "답변 근거 보기",
        ),
        default_screenshot="docs/images/features/project-chat-answer.png",
        description="Project Chat 답변/근거 화면",
        scroll_to_text="결제금액 검증은",
    ),
    "ai-code-review": FeatureScenario(
        name="ai-code-review",
        sidebar_label="AI Code Review",
        wait_text="리뷰 대상",
        required_texts=("AI Code Review", "리뷰 대상", "AI 코드리뷰 실행"),
        default_screenshot="docs/images/features/ai-code-review.png",
        description="AI Code Review 대상 선택 화면",
    ),
    "settings": FeatureScenario(
        name="settings",
        sidebar_label="설정",
        wait_text="시스템 상태",
        required_texts=("설정", "시스템 상태", "LLM 설정", "Embedding 설정"),
        default_screenshot="docs/images/features/settings.png",
        description="설정 화면",
    ),
}


SIDEBAR_GROUP_BY_LABEL = {
    "Home": "개요",
    "Dashboard": "개요",
    "AI Progress": "개요",
    "프로젝트/Git 설정": "프로젝트 설정",
    "Git 동기화": "프로젝트 설정",
    "샘플 데이터 생성": "프로젝트 설정",
    "개발자 현황": "산출물 관리",
    "개발자 목록": "산출물 관리",
    "프로그램 목록": "산출물 관리",
    "개발계획": "산출물 관리",
    "표준용어/표준단어": "산출물 관리",
    "Mapping": "분석 실행",
    "Risk Analysis": "분석 실행",
    "RAG 검색": "분석 실행",
    "Project Chat": "분석 실행",
    "AI Code Review": "분석 실행",
    "Program Detail": "분석 결과",
    "Git History": "분석 결과",
    "Commit Impact": "분석 결과",
    "Knowledge Graph": "분석 결과",
    "개발계획 대시보드": "분석 결과",
    "설정": "관리",
}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture verified feature screenshots from a running Streamlit app."
    )
    parser.add_argument("--url", default="http://localhost:8501", help="Streamlit app URL.")
    parser.add_argument(
        "--feature",
        choices=tuple(SCENARIOS.keys()) + ("all",),
        default="home",
        help="Feature scenario to capture.",
    )
    parser.add_argument(
        "--screenshot",
        help="Screenshot output path. Only valid when capturing a single feature.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory used when --screenshot is not set. Defaults to each scenario path.",
    )
    parser.add_argument(
        "--expect-text",
        action="append",
        default=[],
        help="Additional text that must be visible before the screenshot is saved.",
    )
    parser.add_argument(
        "--forbid-text",
        action="append",
        default=[],
        help="Additional text that must not be visible before the screenshot is saved.",
    )
    parser.add_argument(
        "--surface",
        default="local",
        choices=("local", "docker", "other"),
        help="Runtime surface used for this capture. Printed in the result for traceability.",
    )
    parser.add_argument(
        "--project-name",
        help="Sidebar current project label text to select before navigating to the feature.",
    )
    parser.add_argument("--width", type=int, default=1440, help="Browser viewport width.")
    parser.add_argument("--height", type=int, default=1000, help="Browser viewport height.")
    return parser.parse_args(argv)


def _open_app(page: Page, url: str) -> None:
    page.goto(url, wait_until="networkidle", timeout=30_000)


def _navigate_to_sidebar_item(page: Page, label: str) -> None:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    _expand_sidebar_group(page, SIDEBAR_GROUP_BY_LABEL.get(label))
    item = sidebar.get_by_text(label, exact=True).last
    item.wait_for(timeout=15_000)
    item.click()


def _expand_sidebar_group(page: Page, group: str | None) -> None:
    if not group:
        return
    page.evaluate(
        """
        (group) => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (!sidebar) {
                throw new Error("Sidebar not found");
            }
            const details = Array.from(sidebar.querySelectorAll('details')).find((item) => {
                const summaryText = (item.querySelector('summary')?.innerText || '').trim();
                return summaryText === group;
            });
            if (details && !details.open) {
                details.querySelector('summary')?.click();
            }
        }
        """,
        group,
    )


def _select_sidebar_project(page: Page, project_name: str | None) -> None:
    if not project_name:
        return
    sidebar = page.locator('section[data-testid="stSidebar"]')
    selector = sidebar.get_by_role("combobox").first
    current_label = selector.get_attribute("aria-label", timeout=10_000) or ""
    if project_name in current_label:
        return
    selector.click()
    option = page.get_by_role("option").filter(has_text=project_name)
    if option.count() != 1:
        raise AssertionError(f"Project selector option is not unique for: {project_name}")
    option.click()
    page.wait_for_function(
        "(value) => document.querySelector('section[data-testid=\"stSidebar\"]')?.innerText.includes(value)",
        arg=project_name,
        timeout=15_000,
    )


def _wait_for_body_text(page: Page, text: str, timeout: int = 20_000) -> None:
    page.wait_for_function(
        "(value) => document.body && document.body.innerText.includes(value)",
        arg=text,
        timeout=timeout,
    )


def _page_text(page: Page, wait_text: str) -> str:
    _wait_for_body_text(page, wait_text)
    return page.locator("body").inner_text(timeout=10_000)


def _wait_for_texts(page: Page, texts: tuple[str, ...]) -> None:
    for text in texts:
        _wait_for_body_text(page, text)


def _assert_texts(
    text: str,
    required_texts: tuple[str, ...],
    forbidden_texts: tuple[str, ...],
) -> None:
    missing = [value for value in required_texts if value not in text]
    if missing:
        raise AssertionError(f"Missing expected text: {', '.join(missing)}")

    stale = [value for value in forbidden_texts if value in text]
    if stale:
        raise AssertionError(f"Forbidden text is visible: {', '.join(stale)}")


def _scroll_text_into_view(page: Page, text: str) -> None:
    page.evaluate(
        """
        (value) => {
            const elements = Array.from(document.querySelectorAll('h1,h2,h3,h4,p,li,div,span,strong'));
            const target = elements.find((element) => (element.innerText || element.textContent || '').includes(value));
            if (!target) {
                throw new Error(`Text not found for scroll: ${value}`);
            }
            target.scrollIntoView({ block: 'start', inline: 'nearest' });
            const scrollParents = [
                document.querySelector('[data-testid="stAppViewContainer"]'),
                document.querySelector('section.main'),
                document.scrollingElement,
            ].filter(Boolean);
            for (const parent of scrollParents) {
                const targetTop = target.getBoundingClientRect().top;
                if (targetTop > window.innerHeight * 0.6) {
                    parent.scrollTop += targetTop - 160;
                }
            }
        }
        """,
        text,
    )
    page.wait_for_timeout(300)


def _sidebar_item_box(page: Page, label: str) -> dict[str, float]:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    _expand_sidebar_group(page, SIDEBAR_GROUP_BY_LABEL.get(label))
    locator = sidebar.get_by_text(label, exact=True).last
    box = locator.bounding_box(timeout=10_000)
    if box is None:
        raise AssertionError(f"Sidebar item has no bounding box: {label}")
    return box


def _sidebar_item_metrics(page: Page, labels: tuple[str, ...]) -> dict[str, dict[str, float]]:
    for label in labels:
        _expand_sidebar_group(page, SIDEBAR_GROUP_BY_LABEL.get(label))
    metrics = page.evaluate(
        """
        (labels) => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (!sidebar) {
                throw new Error("Sidebar not found");
            }
            const activeMarkupCount = sidebar.querySelectorAll('.nav-active').length;
            if (activeMarkupCount > 0) {
                throw new Error(`Unexpected custom active sidebar markup: ${activeMarkupCount}`);
            }
            const buttons = Array.from(sidebar.querySelectorAll('.stButton > button'));
            const result = {};
            for (const label of labels) {
                const button = buttons.find((item) => (item.innerText || item.textContent || '').trim() === label);
                if (!button) {
                    throw new Error(`Sidebar button not found: ${label}`);
                }
                const box = button.getBoundingClientRect();
                const text = button.querySelector('p') || button;
                const textBox = text.getBoundingClientRect();
                result[label] = {
                    x: box.x,
                    y: box.y,
                    width: box.width,
                    height: box.height,
                    textRelX: textBox.x - box.x,
                    textRelY: textBox.y - box.y,
                    textHeight: textBox.height,
                };
            }
            return result;
        }
        """,
        list(labels),
    )
    return metrics


def _assert_metric_delta(
    before: dict[str, dict[str, float]],
    after: dict[str, dict[str, float]],
    labels: tuple[str, ...],
    fields: tuple[str, ...],
    max_delta: float,
) -> None:
    unstable: dict[str, dict[str, float]] = {}
    for label in labels:
        deltas = {
            field: abs(after[label][field] - before[label][field])
            for field in fields
            if abs(after[label][field] - before[label][field]) > max_delta
        }
        if deltas:
            unstable[label] = deltas

    if unstable:
        raise AssertionError(f"Sidebar item metrics changed after navigation: {unstable}")


def _sidebar_spacing(metrics: dict[str, dict[str, float]], first: str, second: str) -> float:
    first_box = metrics[first]
    second_box = metrics[second]
    return second_box["y"] - (first_box["y"] + first_box["height"])


def _verify_sidebar_layout_stability(page: Page) -> None:
    top_labels = ("Home", "Dashboard", "AI Progress")
    before_top = _sidebar_item_metrics(page, top_labels)
    before_dashboard_spacing = _sidebar_spacing(before_top, "Dashboard", "AI Progress")

    _navigate_to_sidebar_item(page, "Dashboard")
    page.get_by_text("프로젝트 계획, AI 분석, Git 활동을 한 화면에서 확인합니다.").wait_for(timeout=15_000)
    after_dashboard = _sidebar_item_metrics(page, top_labels)

    _assert_metric_delta(
        before_top,
        after_dashboard,
        top_labels,
        ("x", "y", "width", "height", "textRelX", "textRelY", "textHeight"),
        max_delta=1.0,
    )

    after_dashboard_spacing = _sidebar_spacing(after_dashboard, "Dashboard", "AI Progress")
    if abs(after_dashboard_spacing - before_dashboard_spacing) > 1.0:
        raise AssertionError(
            "Sidebar adjacent item spacing changed after active item navigation: "
            f"{before_dashboard_spacing} -> {after_dashboard_spacing}"
        )

    page.get_by_text("현재 위치").wait_for(timeout=10_000)


def _default_output_path(scenario: FeatureScenario, output_dir: str | None) -> Path:
    if scenario.default_screenshot:
        return Path(scenario.default_screenshot)
    return Path(output_dir or "docs/images/features") / f"{scenario.name}.png"


def _capture_scenario(
    page: Page,
    url: str,
    scenario: FeatureScenario,
    screenshot_path: Path,
    extra_required_texts: tuple[str, ...],
    extra_forbidden_texts: tuple[str, ...],
    project_name: str | None,
) -> str:
    _open_app(page, url)
    _select_sidebar_project(page, project_name)
    if scenario.sidebar_label:
        _navigate_to_sidebar_item(page, scenario.sidebar_label)

    if scenario.button_label and scenario.button_before_tab:
        page.get_by_role("button", name=scenario.button_label).click()
        if scenario.action_wait_text:
            _wait_for_body_text(page, scenario.action_wait_text, timeout=180_000)
    if scenario.tab_label:
        page.get_by_role("tab", name=scenario.tab_label).click()
    if scenario.fill_label and scenario.fill_value is not None:
        page.get_by_label(scenario.fill_label).fill(scenario.fill_value)
        page.keyboard.press("Tab")
    if scenario.click_label:
        page.locator('[data-testid="stTabs"]').get_by_role("button", name=scenario.click_label).click()
    if scenario.button_label and not scenario.button_before_tab:
        page.get_by_role("button", name=scenario.button_label).click()
    if scenario.action_wait_text and not scenario.button_before_tab:
        _wait_for_body_text(page, scenario.action_wait_text, timeout=180_000)

    _wait_for_texts(page, scenario.required_texts + extra_required_texts)
    text = _page_text(page, scenario.wait_text)
    _assert_texts(
        text,
        scenario.required_texts + extra_required_texts,
        scenario.forbidden_texts + extra_forbidden_texts,
    )

    if scenario.verify_sidebar_stability:
        _verify_sidebar_layout_stability(page)
        _navigate_to_sidebar_item(page, scenario.sidebar_label or "Home")
        _wait_for_texts(page, scenario.required_texts + extra_required_texts)
        text = _page_text(page, scenario.wait_text)
        _assert_texts(
            text,
            scenario.required_texts + extra_required_texts,
            scenario.forbidden_texts + extra_forbidden_texts,
        )

    if scenario.scroll_to_text:
        _scroll_text_into_view(page, scenario.scroll_to_text)

    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=scenario.full_page)
    if scenario.crop_box:
        with Image.open(screenshot_path) as image:
            left, top, right, bottom = scenario.crop_box
            if image.height < bottom or image.width < right:
                raise AssertionError(
                    f"{scenario.name} crop requires at least {right}x{bottom}, "
                    f"captured {image.width}x{image.height}. Increase --height."
                )
            image.crop((left, top, right, bottom)).save(screenshot_path)
    return text


def _selected_scenarios(feature: str) -> list[FeatureScenario]:
    if feature == "all":
        return list(SCENARIOS.values())
    return [SCENARIOS[feature]]


def _screenshot_path(
    args: argparse.Namespace,
    scenario: FeatureScenario,
    scenario_count: int,
) -> Path:
    if args.screenshot:
        if scenario_count > 1:
            raise SystemExit("--screenshot can only be used with a single --feature value.")
        return Path(args.screenshot)
    if args.output_dir:
        return Path(args.output_dir) / f"{scenario.name}.png"
    return _default_output_path(scenario, args.output_dir)


def _candidate_browser_paths() -> list[str]:
    env_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    candidates = [env_path] if env_path else []
    candidates.extend(
        [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            str(Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
    )
    return [path for path in candidates if path and Path(path).exists()]


def _launch_chromium(playwright):
    try:
        return playwright.chromium.launch(headless=True)
    except Error:
        for executable_path in _candidate_browser_paths():
            try:
                return playwright.chromium.launch(headless=True, executable_path=executable_path)
            except Error:
                continue
        raise


def main(argv: Sequence[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = _parse_args(argv)
    scenarios = _selected_scenarios(args.feature)
    extra_required_texts = tuple(args.expect_text)
    extra_forbidden_texts = tuple(args.forbid_text)

    try:
        with sync_playwright() as playwright:
            browser = _launch_chromium(playwright)
            page = browser.new_page(viewport={"width": args.width, "height": args.height})
            for scenario in scenarios:
                path = _screenshot_path(args, scenario, len(scenarios))
                text = _capture_scenario(
                    page,
                    args.url,
                    scenario,
                    path,
                    extra_required_texts,
                    extra_forbidden_texts,
                    args.project_name,
                )
                preview = "\n".join(line for line in text.splitlines() if line.strip())[:1000]
                print(
                    f"{scenario.name} screenshot captured on {args.surface}: {path}\n"
                    f"{preview}\n"
                )
            browser.close()
    except Error as exc:
        raise SystemExit(
            "Playwright browser 실행에 실패했습니다. "
            "필요하면 `.venv\\Scripts\\python.exe -m playwright install chromium`을 실행하세요.\n"
            f"{exc}"
        ) from exc


if __name__ == "__main__":
    main()
