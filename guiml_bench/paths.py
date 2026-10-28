from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARBON_OUT = ROOT / "carbon" / "out"
CARBON_COMPOSITION = ROOT / "carbon" / "composition.json"
DATA = ROOT / "data"
TASKS_DIR = DATA / "tasks"
GOLD_DIR = DATA / "gold"
RUNS_DIR = ROOT / "runs"
GUIML_DIR = ROOT / "guiml"
FIXTURE_DIR = ROOT / "fixture"
GRADER_NODE = ROOT / "grader-node"
DOCS = ROOT / "docs"
SPACE = ROOT / "space"
PAPER = ROOT / "paper"


def pack_path(scale: str) -> Path:
    return CARBON_OUT / f"pack-{scale.upper()}.json"
