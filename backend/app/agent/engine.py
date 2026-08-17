from __future__ import annotations
import tempfile,time
from pathlib import Path
from uuid import uuid4
from app.core.config import settings
from app.github.client import GitHubClient
from app.llm.client import OpenAICompatibleClient, LLMError
from app.models.schemas import Event, RunRequest, RunResponse, RunStatus
from app.observability.tracing import span
from app.sandbox.demo_repo import create_demo_repo
from app.sandbox.executor import run_tests
from app.sandbox.executor_router import get_sandbox
from app.agent.repository import inventory,safe_write
from app.agent.reviewer import review

class ForgeAgent:
    def __init__(self,max_iterations=5):
        self.max_iterations=min(max_iterations,settings.max_iterations)
        self.github=GitHubClient(settings.github_token)
        self.llm=OpenAICompatibleClient(settings.llm_base_url,settings.llm_api_key,settings.llm_model)
        self.docker=get_sandbox()

    def planner(self,task):
        return ["analyze repository","create implementation plan","implement minimal change","run tests","review changes"]

    def demo_edit(self,root,task):
        if "subtract" in task.lower() or "odejm" in task.lower():
            calc=root/"calculator.py"; test=root/"test_calculator.py"
            text=calc.read_text()
            if "def subtract" not in text: calc.write_text(text+"\n\ndef subtract(a, b):\n    return a - b\n")
            test_text=test.read_text()
            if "test_subtract" not in test_text:
                marker="\nif __name__ == \"__main__\": unittest.main()\n"
                addition="\n    def test_subtract(self): self.assertEqual(__import__(\"calculator\").subtract(7, 2), 5)\n"
                test.write_text(test_text.replace(marker, addition+marker), encoding="utf-8")
            return ["calculator.py","test_calculator.py"]
        return []

    def _execute(self,root,timeout):
        if self.docker.available:
            result=self.docker.run_tests(root,timeout)
            if result is not None: return result
        return run_tests(root,timeout)

    def run(self,request):
        run_id=str(uuid4()); started=time.perf_counter(); events=[]; changed=[]; iterations=0; total_tokens=0; input_tokens=0; output_tokens=0; result=None; pr_url=None
        with tempfile.TemporaryDirectory(prefix="forgeai-") as temp:
            root=Path(temp)/"repo"
            with span("agent.run",run_id=run_id,task=request.task):
                if request.repository.startswith("demo://"):
                    root.mkdir(); create_demo_repo(root); repo_meta=None
                else:
                    events.append(Event(type="tool",message="Cloning GitHub repository")); repo_meta=self.github.clone(request.repository,root)
                files=inventory(root)
                events.append(Event(type="analysis",message="Repository analyzed",metadata={"files":len(files),"sandbox":self.docker.available}))
                plan=self.planner(request.task); failure=None
                for iteration in range(1,min(request.max_iterations,self.max_iterations)+1):
                    iterations=iteration; events.append(Event(type="iteration",message=f"Iteration {iteration}",iteration=iteration))
                    if self.llm.enabled:
                        try:
                            llm=self.llm.generate(request.task,inventory(root),failure)
                            input_tokens+=llm.input_tokens; output_tokens+=llm.output_tokens
                            if llm.plan: plan=llm.plan
                            for edit in llm.edits: changed.append(safe_write(root,edit.path,edit.content))
                            events.append(Event(type="agent",message=llm.summary or "LLM changes applied",iteration=iteration,metadata={"edits":len(llm.edits)}))
                        except LLMError as exc:
                            events.append(Event(type="warning",message=f"LLM error: {exc}",iteration=iteration))
                            if iteration==1: changed.extend(self.demo_edit(root,request.task))
                    else:
                        changed.extend(self.demo_edit(root,request.task))
                        events.append(Event(type="agent",message="Deterministic demo implementation applied",iteration=iteration))
                    events.append(Event(type="tool",message="Running tests in sandbox",iteration=iteration))
                    with span("sandbox.tests",iteration=iteration): result=self._execute(root,request.max_seconds)
                    events.append(Event(type="test",message=result.output[-5000:],iteration=iteration,metadata={"passed":result.passed,"total":result.total,"exit_code":result.exit_code,"duration_ms":result.duration_ms}))
                    if result.exit_code==0 and result.total>0 and result.passed==result.total:
                        ok,findings=review(root,sorted(set(changed)),result.output)
                        events.append(Event(type="review",message="Review passed" if ok else "Review failed",iteration=iteration,metadata={"findings":findings}))
                        if ok: break
                    failure=result.output
                success=bool(result and result.exit_code==0 and result.total>0 and result.passed==result.total)
                status=RunStatus.success if success else RunStatus.failed
                if success and request.create_pr and repo_meta:
                    branch=f"forgeai/{run_id[:8]}"; pr_url=self.github.create_branch_and_pr(request.repository,root,f"ForgeAI: {request.task[:70]}",f"ForgeAI autonomous change. Tests: {result.passed}/{result.total}. Iterations: {iterations}.",branch,base=request.base_branch)
                    events.append(Event(type="github",message="Draft pull request created",metadata={"url":pr_url}))
        duration=int((time.perf_counter()-started)*1000); cost=(input_tokens/1_000_000)*settings.model_cost_input_per_1m+(output_tokens/1_000_000)*settings.model_cost_output_per_1m
        return RunResponse(id=run_id,status=status,repository=request.repository,task=request.task,events=events,files_changed=sorted(set(changed)),tests_passed=result.passed if result else 0,tests_total=result.total if result else 0,iterations=iterations,duration_ms=duration,cost_usd=round(cost,6),input_tokens=input_tokens,output_tokens=output_tokens,pull_request_url=pr_url,summary="Task completed, tested and reviewed successfully." if success else "Agent stopped without a verified passing result.")
