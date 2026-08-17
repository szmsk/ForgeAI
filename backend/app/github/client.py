from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class GitRepository:
    owner: str
    name: str
    default_branch: str
    clone_url: str


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str | None = None, api_url: str = "https://api.github.com"):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.api_url = api_url.rstrip("/")

    @staticmethod
    def parse_url(repository: str) -> tuple[str, str]:
        value = repository.strip().removesuffix("/")
        patterns = [
            r"^https?://github\.com/([^/]+)/([^/#]+?)(?:\.git)?$",
            r"^git@github\.com:([^/]+)/([^/#]+?)(?:\.git)?$",
            r"^github:([^/]+)/([^/#]+?)(?:\.git)?$",
        ]
        for pattern in patterns:
            match = re.match(pattern, value)
            if match:
                return match.group(1), match.group(2)
        raise GitHubError("Repository must be a GitHub URL such as https://github.com/owner/repo")

    def clone(self, repository: str, destination: Path) -> GitRepository:
        owner, name = self.parse_url(repository)
        url = f"https://github.com/{owner}/{name}.git"
        command = ["git", "clone", "--depth", "1", url, str(destination)]
        if self.token:
            authenticated = f"https://x-access-token:{self.token}@github.com/{owner}/{name}.git"
            command[4] = authenticated
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if completed.returncode != 0:
            raise GitHubError((completed.stderr or completed.stdout).strip()[-4000:])
        default_branch = self._default_branch(owner, name)
        return GitRepository(owner, name, default_branch, url)

    def _default_branch(self, owner: str, name: str) -> str:
        if not self.token:
            return "main"
        response = httpx.get(
            f"{self.api_url}/repos/{owner}/{name}",
            headers=self._headers(),
            timeout=20,
        )
        if response.is_success:
            return response.json().get("default_branch", "main")
        return "main"

    def create_branch_and_pr(
        self,
        repository: str,
        local_repo: Path,
        title: str,
        body: str,
        branch: str,
        base: str | None = None,
    ) -> str:
        if not self.token:
            raise GitHubError("GITHUB_TOKEN is required to create a pull request")
        owner, name = self.parse_url(repository)
        self._git(local_repo, ["checkout", "-b", branch])
        self._git(local_repo, ["add", "-A"])
        status = subprocess.run(
            ["git", "-C", str(local_repo), "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if status.returncode == 0:
            raise GitHubError("No changes detected; refusing to create an empty pull request")
        self._git(local_repo, ["config", "user.name", "ForgeAI Bot"])
        self._git(local_repo, ["config", "user.email", "forgeai-bot@users.noreply.github.com"])
        self._git(local_repo, ["commit", "-m", title])
        remote = f"https://x-access-token:{self.token}@github.com/{owner}/{name}.git"
        self._git(local_repo, ["push", remote, branch])

        response = httpx.post(
            f"{self.api_url}/repos/{owner}/{name}/pulls",
            headers=self._headers(),
            json={"title": title, "body": body, "head": branch, "base": base or self._default_branch(owner, name), "draft": True},
            timeout=30,
        )
        if response.status_code != 201:
            raise GitHubError(f"GitHub PR creation failed: {response.status_code}: {response.text[-2000:]}")
        return response.json()["html_url"]

    @staticmethod
    def _git(cwd: Path, args: list[str]) -> None:
        completed = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=120)
        if completed.returncode != 0:
            raise GitHubError((completed.stderr or completed.stdout).strip()[-4000:])

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }
