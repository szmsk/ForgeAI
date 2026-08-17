from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", ".next", ".pytest_cache", ".ruff_cache"}
PATTERNS = {
    "OpenAI API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
}

failures = []
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
        continue
    if path.name.startswith(".env") and path.name != ".env.example":
        failures.append(f"environment file: {path}")
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            failures.append(f"{name}: {path}")

if failures:
    print("Potential secrets found:")
    print("\n".join(f"- {item}" for item in failures))
    sys.exit(1)

print("Secret scan passed: no known credential patterns found.")
