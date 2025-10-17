from __future__ import annotations
import re
import subprocess
from pathlib import Path


def get_version_from_changelog(repo_root: Path) -> str:
    """Parse CHANGELOG.md for latest version like '## [0.3.2] - ...'"""
    try:
        text = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
        m = re.search(r"^## \[(?P<ver>\d+\.\d+\.\d+)\]", text, re.M)
        if m:
            return m.group("ver")
    except Exception:
        pass
    return "0.0.0"


def get_git_short_hash(repo_root: Path) -> str:
    """Return short git hash or 'no-git' if not available."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return "no-git"


def get_version_banner(repo_root: Path) -> str:
    ver = get_version_from_changelog(repo_root)
    h = get_git_short_hash(repo_root)
    return f"v{ver} [{h}]"
