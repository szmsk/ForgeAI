from __future__ import annotations
import re, subprocess, time, sys
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TestExecution:
    passed: int
    total: int
    exit_code: int
    output: str
    duration_ms: int

def _parse_pytest(output: str) -> tuple[int,int]:
    m=re.search(r"(\d+) passed(?:,?\s*(\d+) failed)?(?:,?\s*(\d+) error)?", output)
    if m and any(x for x in m.groups()):
        p=int(m.group(1) or 0); f=int(m.group(2) or 0); e=int(m.group(3) or 0); return p, p+f+e
    u=re.search(r"Ran (\d+) tests?", output)
    if u:
        total=int(u.group(1)); failed=1 if "FAILED" in output else 0
        return total-failed,total
    return 0,0

def run_tests(root: Path, timeout: int=120) -> TestExecution:
    started=time.perf_counter()
    commands=[]
    if (root/"pyproject.toml").exists() or list(root.glob("test_*.py")) or (root/"tests").exists():
        try:
            import pytest  # noqa: F401
            commands.append([sys.executable,"-m","pytest","-q"])
        except ImportError:
            commands.append([sys.executable,"-m","unittest","discover","-v"])
    if (root/"package.json").exists(): commands.append(["npm","test","--","--runInBand"])
    if not commands: return TestExecution(0,0,0,"No supported test suite detected.",0)
    last=""; code=1
    for command in commands:
        try:
            proc=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=timeout,env={"PATH":"/usr/local/bin:/usr/bin:/bin"})
            code=proc.returncode; last=(proc.stdout+"\n"+proc.stderr)[-12000:]
            p,t=_parse_pytest(last)
            if code==0 and t: return TestExecution(p,t,code,last,int((time.perf_counter()-started)*1000))
        except subprocess.TimeoutExpired as exc:
            return TestExecution(0,0,124,(exc.stdout or "")[-12000:]+"\nTIMEOUT",124,int((time.perf_counter()-started)*1000))
    p,t=_parse_pytest(last)
    return TestExecution(p,t,code,last,int((time.perf_counter()-started)*1000))
