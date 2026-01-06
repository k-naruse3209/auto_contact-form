import subprocess
import sys
from pathlib import Path


def test_dry_run_outputs():
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "src.main", "--dry-run"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)

    out = result.stdout
    assert "[dry-run] Phase1 URL discovery" in out
    assert "[dry-run] Phase2 context analysis" in out
    assert "[dry-run] Phase3 outreach drafting" in out
    assert "[dry-run] Phase4 form automation" in out
