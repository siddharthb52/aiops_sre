from __future__ import annotations
from typing import List
from pathlib import Path
from crewai.tools import tool

@tool("tail_log")
def tail_log(path: str, n: int = 20) -> str:
    """Return the last n lines of a text log file as a single string."""
    p = Path(path)
    if not p.exists():
        return f"[tail_log] File not found: {path}"

    try:
        lines: List[str] = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-n:])
    except Exception as e:
        return f"[tail_log] Error reading {path}: {e}"
