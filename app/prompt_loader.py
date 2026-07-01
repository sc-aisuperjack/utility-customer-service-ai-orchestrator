from pathlib import Path
from typing import Dict, Any
import yaml

PROMPT_DIR = Path(__file__).parent / "prompts"

def load_prompt(version: str) -> Dict[str, Any]:
    path = PROMPT_DIR / f"{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt version not found: {version}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def list_prompts():
    return sorted(p.stem for p in PROMPT_DIR.glob("*.yaml"))
