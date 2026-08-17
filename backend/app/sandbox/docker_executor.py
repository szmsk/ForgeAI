from __future__ import annotations
import tarfile, io, time
from pathlib import Path
from app.core.config import settings

class DockerSandbox:
    def __init__(self, image: str | None = None):
        self.image=image or settings.sandbox_image
        try:
            import docker
            self.client=docker.from_env()
            self.client.ping()
        except Exception:
            self.client=None

    @property
    def available(self): return self.client is not None

    def run_tests(self, root: Path, timeout: int = 120):
        from app.sandbox.executor import TestExecution
        if not self.client:
            return None
        container=None; started=time.perf_counter()
        try:
            container=self.client.containers.run(self.image, command=["python","-m","pytest","-q"], volumes={str(root):{"bind":"/workspace","mode":"rw"}}, working_dir="/workspace", network_mode="none", mem_limit=settings.sandbox_memory, nano_cpus=int(settings.sandbox_cpus*1e9), pids_limit=settings.sandbox_pids, cap_drop=["ALL"], security_opt=["no-new-privileges:true"], read_only=False, detach=True, remove=False)
            try:
                result=container.wait(timeout=timeout)
            except Exception:
                container.kill(); return TestExecution(0,0,124,"SANDBOX TIMEOUT",124,int((time.perf_counter()-started)*1000))
            output=container.logs(stdout=True,stderr=True).decode(errors="replace")[-12000:]
            from app.sandbox.executor import _parse_pytest
            p,t=_parse_pytest(output)
            return TestExecution(p,t,int(result.get("StatusCode",1)),output,int((time.perf_counter()-started)*1000))
        finally:
            if container:
                try: container.remove(force=True)
                except Exception: pass
