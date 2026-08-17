import pytest
from pathlib import Path
from app.agent.repository import safe_write

def test_blocks_path_traversal(tmp_path):
    with pytest.raises(ValueError): safe_write(tmp_path,"../escape.py","x")

def test_blocks_env(tmp_path):
    with pytest.raises(ValueError): safe_write(tmp_path,".env","SECRET=x")
