from src.engine.models import Check, Severity
from src.utils.platform import summary, is_windows
from src.utils.runner import ps_json

def run_system():
    s=summary()
    out=[
        Check("Computer",Severity.OK,s["computer"],s["computer"]),
        Check("Operating System",Severity.OK,s["os"],s["os"]),
        Check("Architecture",Severity.OK,s["architecture"],s["architecture"]),
        Check("Administrator",Severity.INFO,"Administrator session" if s["administrator"] else "Standard user session",s["administrator"],recommendation="Elevate only when an approved repair requires it."),
    ]
    if is_windows():
        r,data=ps_json("Get-CimInstance Win32_OperatingSystem | Select Caption,Version,BuildNumber,LastBootUpTime,FreePhysicalMemory,TotalVisibleMemorySize | ConvertTo-Json -Compress -Depth 4",10)
        if isinstance(data,dict):
            out.append(Check("Windows Runtime",Severity.OK,"Windows runtime information collected.",details=r.stdout,elapsed=r.elapsed))
        else:
            out.append(Check("Windows Runtime",Severity.UNKNOWN,"Windows runtime information was not returned.",details=r.stdout+r.stderr,elapsed=r.elapsed))
    return out
