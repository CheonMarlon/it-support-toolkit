from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import ps_json

def run_applications():
    if not is_windows(): return [Check("Applications",Severity.UNKNOWN,"Unavailable on this platform.")]
    r,data=ps_json("Get-Process -ErrorAction SilentlyContinue | Sort-Object CPU -Descending | Select -First 40 ProcessName,Id,CPU,WorkingSet64,Responding | ConvertTo-Json -Compress -Depth 4",15)
    if data is None: return [Check("Running Applications",Severity.UNKNOWN,"Process inventory could not be collected.",details=r.stdout+r.stderr,recommendation="Open Task Manager to inspect CPU, memory and application state.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    return [Check("Running Applications",Severity.OK,f"{len(items)} running process entries collected.",value=len(items),details=r.stdout,recommendation="Review top CPU/memory consumers if the user reports slowness.",elapsed=r.elapsed)]
