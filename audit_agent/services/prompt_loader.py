from pathlib import Path


def load_prompt(name: str) -> str:
    base = Path(__file__).resolve().parent.parent / "prompts"
    return (base / name).read_text(encoding="utf-8")
