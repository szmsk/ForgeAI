from app.agent.engine import ForgeAgent
from app.models.schemas import RunRequest, RunStatus

def test_demo_agent_succeeds():
    result=ForgeAgent(max_iterations=3).run(RunRequest(repository="demo://calculator",task="Add a subtract function to the calculator",max_iterations=3,max_seconds=20))
    assert result.status==RunStatus.success
    assert result.tests_passed==result.tests_total
    assert "calculator.py" in result.files_changed
