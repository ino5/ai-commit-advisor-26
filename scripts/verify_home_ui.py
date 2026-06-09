from __future__ import annotations

import argparse

from capture_feature_screenshot import main as capture_main


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the Home page renders with compact copy.")
    parser.add_argument("--url", default="http://localhost:8501", help="Streamlit app URL.")
    parser.add_argument(
        "--screenshot",
        default=".tmp/home-ui-check.png",
        help="Screenshot output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    capture_main(
        [
            "--feature",
            "home",
            "--url",
            args.url,
            "--screenshot",
            args.screenshot,
        ]
    )


if __name__ == "__main__":
    main()
