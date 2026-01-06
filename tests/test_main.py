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


def test_dry_run_phase1_only_outputs():
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "src.main", "--dry-run", "--phase1-only"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)

    out = result.stdout
    assert "[dry-run] Phase1 URL discovery" in out
    assert "Phase2 context analysis" not in out
    assert "Phase3 outreach drafting" not in out
    assert "Phase4 form automation" not in out
