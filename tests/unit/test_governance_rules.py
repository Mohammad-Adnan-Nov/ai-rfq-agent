from pathlib import Path


def test_readme_contains_no_invention_rule():
    root = Path(__file__).resolve().parents[2]
    readme_text = (root / "README.md").read_text(encoding="utf-8").lower()

    assert "never invent part numbers" in readme_text
    assert "sql server is the source of truth" in readme_text


def test_gitignore_blocks_raw_pricebook_data():
    root = Path(__file__).resolve().parents[2]
    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8").lower()

    assert "data/raw/*" in gitignore_text
    assert ".env" in gitignore_text
