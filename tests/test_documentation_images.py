from __future__ import annotations

from pathlib import Path


def test_readme_representative_screenshot_uses_application_preview_home_image() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    preview = Path("docs/application-preview.md").read_text(encoding="utf-8")

    assert "docs/images/features/home.png" in readme
    assert "docs/images/ai-commit-advisor-home.png" not in readme
    assert "docs/images/ai-commit-advisor-home-48.png" not in readme
    assert "images/features/ai-evidence.png" in preview
    assert "images/features/dashboard-pl-briefing.png" in preview
    assert "images/features/dashboard-pl-briefing-actions.png" in preview
