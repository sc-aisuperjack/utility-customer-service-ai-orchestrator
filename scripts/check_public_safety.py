from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()

FORBIDDEN_TERMS = [
    "british gas",
]

SKIP_DIRS = {
    ".git",
    ".venv",
    ".venv312",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
}

SKIP_FILES = {
    ".env",
    ".env.local",
    "check_public_safety.py",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".toml",
    ".ini",
}


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True

    if path.name in SKIP_FILES:
        return True

    return False


def is_git_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def main():
    hits = []

    # Check that .env is ignored rather than scanning its contents.
    env_path = ROOT / ".env"
    if env_path.exists() and not is_git_ignored(".env"):
        hits.append((Path(".env"), 0, ".env exists but is not ignored by Git"))

    for path in ROOT.rglob("*"):
        if should_skip(path) or not path.is_file():
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        low = text.lower()

        for term in FORBIDDEN_TERMS:
            if term in low:
                for i, line in enumerate(text.splitlines(), start=1):
                    if term in line.lower():
                        hits.append((path.relative_to(ROOT), i, term))

    if hits:
        print("Public safety scan failed. Review these:")
        for file, line, term in hits:
            print(f"{file}:{line} -> {term}")
        raise SystemExit(1)

    print("Public safety scan passed. No forbidden terms found.")


if __name__ == "__main__":
    main()