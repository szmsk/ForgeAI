from pathlib import Path
from app.sandbox.docker_executor import DockerSandbox

def test_sandbox_configuration():
    s=DockerSandbox()
    assert s.image
