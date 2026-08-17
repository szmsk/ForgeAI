from pathlib import Path

IGNORED={".git",".venv","venv","node_modules","__pycache__",".next","dist","build"}
MAX_FILE_BYTES=200_000

def inventory(root: Path, limit=80):
    result={}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED for part in path.parts): continue
        try:
            if path.stat().st_size>MAX_FILE_BYTES: continue
            result[str(path.relative_to(root))]=path.read_text(encoding="utf-8")
        except (OSError,UnicodeDecodeError): continue
        if len(result)>=limit: break
    return result

def safe_write(root: Path, relative: str, content: str):
    rel=Path(relative)
    if rel.is_absolute() or any(part in {".git",".env"} or part.startswith(".env") for part in rel.parts):
        raise ValueError(f"Forbidden edit path: {relative}")
    path=(root/rel).resolve()
    if root.resolve() not in path.parents: raise ValueError(f"Unsafe edit path: {relative}")
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding="utf-8")
    return str(path.relative_to(root))
