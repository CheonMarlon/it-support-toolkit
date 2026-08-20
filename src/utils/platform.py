import ctypes, os, platform, sys
from pathlib import Path

def app_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]

def is_windows():
    return platform.system().lower() == "windows"

def is_admin():
    if not is_windows():
        return hasattr(os, "geteuid") and os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def summary():
    return {
        "computer": platform.node() or "Unknown",
        "os": f"{platform.system()} {platform.release()}",
        "version": platform.version(),
        "architecture": platform.machine() or "Unknown",
        "python": platform.python_version(),
        "administrator": is_admin(),
    }
