from app.core.config import settings
from app.sandbox.docker_executor import DockerSandbox

def get_sandbox():
    if getattr(settings,'sandbox_backend','docker')=='kubernetes':
        from app.sandbox.kubernetes_executor import KubernetesSandbox
        return KubernetesSandbox()
    return DockerSandbox()
