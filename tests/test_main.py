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


def test_dry_run_phase2_only_outputs():
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "src.main", "--dry-run", "--phase2-only"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)

    out = result.stdout
    assert "[dry-run] Phase2 context analysis" in out
    assert "Phase1 URL discovery" not in out
    assert "Phase3 outreach drafting" not in out
    assert "Phase4 form automation" not in out


def test_dry_run_phase3_only_outputs():
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "src.main", "--dry-run", "--phase3-only"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)

    out = result.stdout
    assert "[dry-run] Phase3 outreach drafting" in out
    assert "Phase1 URL discovery" not in out
    assert "Phase2 context analysis" not in out
    assert "Phase4 form automation" not in out


def test_dry_run_phase4_only_outputs():
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "src.main", "--dry-run", "--phase4-only"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)

    out = result.stdout
    assert "[dry-run] Phase4 form automation" in out
    assert "Phase1 URL discovery" not in out
    assert "Phase2 context analysis" not in out
    assert "Phase3 outreach drafting" not in out


def test_phase_only_run_logs():
    repo_root = Path(__file__).resolve().parents[1]
    for flag, expected in (
        ("--phase2-only", "[phase2-only] start"),
        ("--phase3-only", "[phase3-only] start"),
        ("--phase4-only", "[phase4-only] start"),
    ):
        cmd = [sys.executable, "-m", "src.main", flag, "--max-companies", "0"]
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)
        assert expected in result.stdout
