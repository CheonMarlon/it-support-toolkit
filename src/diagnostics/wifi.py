import re
from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import run

def run_wifi():
    if not is_windows(): return [Check("Wi-Fi",Severity.UNKNOWN,"Unavailable on this platform.")]
    r=run(["netsh","wlan","show","interfaces"],10)
    if r.code!=0 or not r.stdout.strip():
        return [Check("Wi-Fi Adapter",Severity.UNKNOWN,"Windows did not return Wi-Fi interface information.",details=r.stderr,recommendation="Check whether a Wi-Fi adapter is installed and enabled.",elapsed=r.elapsed)]
    state=re.search(r"^\s*State\s*:\s*(.+)$",r.stdout,re.M|re.I)
    ssid=re.search(r"^\s*SSID\s*:\s*(.+)$",r.stdout,re.M|re.I)
    signal=re.search(r"^\s*Signal\s*:\s*(.+)$",r.stdout,re.M|re.I)
    radio=re.search(r"^\s*Radio type\s*:\s*(.+)$",r.stdout,re.M|re.I)
    state_val=state.group(1).strip() if state else "Unknown"
    connected=state_val.lower()=="connected"
    out=[Check("Wi-Fi Connection",Severity.OK if connected else Severity.WARN,
        f"Connected to {ssid.group(1).strip()}." if connected and ssid else "Wi-Fi is not connected.",
        details=r.stdout[-3500:],recommendation="Check adapter state and available networks." if not connected else "",elapsed=r.elapsed)]
    if signal:
        try: pct=int(re.sub(r"[^0-9]","",signal.group(1)))
        except: pct=None
        out.append(Check("Wi-Fi Signal",Severity.WARN if pct is not None and pct<30 else Severity.OK,
            signal.group(1).strip(),pct,r.stdout[-1500:],"Move closer to the access point or inspect RF conditions." if pct is not None and pct<30 else ""))
    else:
        out.append(Check("Wi-Fi Signal",Severity.UNKNOWN,"Signal strength was not returned by netsh.",details=r.stdout[-1500:]))
    return out
