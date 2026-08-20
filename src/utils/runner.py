import json
import subprocess
import time
from dataclasses import dataclass

@dataclass
class CommandResult:
    command: list[str]
    code: int | None
    stdout: str
    stderr: str
    elapsed: float
    timed_out: bool = False
    error: str = ""

def run(command, timeout=30):
    started = time.perf_counter()
    try:
        p = subprocess.run(command, capture_output=True, text=True, shell=False,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return CommandResult(command, p.returncode, p.stdout, p.stderr,
                             time.perf_counter()-started)
    except subprocess.TimeoutExpired as e:
        return CommandResult(command, None, e.stdout or "", e.stderr or "",
                             time.perf_counter()-started, True)
    except Exception as e:
        return CommandResult(command, None, "", "", time.perf_counter()-started,
                             error=str(e))

def run_powershell(script, timeout=20):
    return run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], timeout)

def json_value(stdout):
    text = (stdout or "").strip()
    if not text or text.lower() in {"null", "[]", "{}"}:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None

def ps_json(script, timeout=20):
    """Run PowerShell and decode ConvertTo-Json output safely."""
    r = run_powershell(script, timeout)
    return r, json_value(r.stdout)
