from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def project_page(name: str) -> str:
    return str(REPO / "project" / "pages" / name)


def midpoint_page(name: str) -> str:
    return str(REPO / "midpoint" / "pages" / name)
