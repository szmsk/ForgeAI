from __future__ import annotations
import json
from dataclasses import dataclass
import httpx

class LLMError(RuntimeError):
    pass

@dataclass
class LLMEdit:
    path: str
    content: str

@dataclass
class LLMResult:
    plan: list[str]
    edits: list[LLMEdit]
    summary: str
    input_tokens: int = 0
    output_tokens: int = 0

class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key and self.model != "demo")

    def generate(self, task: str, files: dict[str, str], failure: str | None = None) -> LLMResult:
        if not self.enabled:
            raise LLMError("LLM adapter is not configured")
        inventory = "\n\n".join(f"FILE: {p}\n{c[:14000]}" for p, c in files.items())
        context = f"\nPrevious test failure:\n{failure[-8000:]}" if failure else ""
        prompt = f'''You are ForgeAI, an autonomous senior software engineer.\nTask:\n{task}\n{context}\nRepository snapshot:\n{inventory}\n\nReturn ONLY JSON: {{"plan":[string],"edits":[{{"path":string,"content":string}}],"summary":string}}.\nRules: make minimal complete changes; preserve existing behavior; add/update tests when appropriate; never edit .git, .env, secrets, absolute paths or paths outside the repository; return full file contents for edits.'''
        try:
            response = httpx.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type":"application/json"}, json={"model":self.model,"messages":[{"role":"system","content":"Return strict machine-readable JSON."},{"role":"user","content":prompt}],"temperature":0,"response_format":{"type":"json_object"}}, timeout=120)
        except httpx.HTTPError as exc:
            raise LLMError(str(exc)) from exc
        if not response.is_success:
            raise LLMError(f"LLM request failed: {response.status_code}: {response.text[-2000:]}")
        try:
            data=response.json(); content=data["choices"][0]["message"]["content"]; payload=json.loads(content)
        except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            raise LLMError("LLM returned invalid JSON") from exc
        usage=data.get("usage",{})
        edits=[LLMEdit(str(e["path"]), str(e["content"])) for e in payload.get("edits",[])]
        return LLMResult(payload.get("plan",[]), edits, payload.get("summary",""), int(usage.get("prompt_tokens",0)), int(usage.get("completion_tokens",0)))
