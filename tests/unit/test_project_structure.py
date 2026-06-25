from pathlib import Path


def test_required_project_folders_exist():
    root = Path(__file__).resolve().parents[2]

    required_paths = [
        root / "src" / "rfq_agent",
        root / "src" / "rfq_agent" / "ingestion",
        root / "src" / "rfq_agent" / "db",
        root / "src" / "rfq_agent" / "retrieval",
        root / "src" / "rfq_agent" / "llm",
        root / "src" / "rfq_agent" / "workflow",
        root / "src" / "rfq_agent" / "api",
        root / "src" / "rfq_agent" / "ui",
        root / "docs",
        root / "scripts",
        root / "tests",
    ]

    missing_paths = [str(path) for path in required_paths if not path.exists()]

    assert not missing_paths, f"Missing required project paths: {missing_paths}"


def test_rfq_agent_package_can_be_imported():
    import rfq_agent

    assert rfq_agent is not None
