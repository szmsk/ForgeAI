from pathlib import Path

def review(root: Path, changed: list[str], test_output: str) -> tuple[bool,list[str]]:
    findings=[]
    for rel in changed:
        if rel.startswith(".env") or ".git" in Path(rel).parts: findings.append(f"Forbidden file changed: {rel}")
        try:
            text=(root/rel).read_text(encoding="utf-8")
            if "sk-" in text or "ghp_" in text: findings.append(f"Possible secret in {rel}")
        except OSError: findings.append(f"Changed file missing: {rel}")
    return not findings, findings
