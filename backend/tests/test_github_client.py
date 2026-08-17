import pytest
from app.github.client import GitHubClient,GitHubError

def test_parse_github_url():
    assert GitHubClient.parse_url("https://github.com/acme/demo.git")==("acme","demo")

def test_reject_non_github_url():
    with pytest.raises(GitHubError): GitHubClient.parse_url("https://gitlab.com/acme/demo")
