from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import run_powershell, ps_json

def run_performance():
    if not is_windows(): return [Check("Performance",Severity.UNKNOWN,"Windows performance counters are unavailable on this platform.")]
    out=[]
    r,data=ps_json("$cpu=(Get-Counter '\\Processor(_Total)\\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples.CookedValue; $os=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{CPU=[math]::Round($cpu,1); Memory=[math]::Round((1-($os.FreePhysicalMemory/$os.TotalVisibleMemorySize))*100,1); TotalRAMGB=[math]::Round($os.TotalVisibleMemorySize/1MB,1); FreeRAMGB=[math]::Round($os.FreePhysicalMemory/1MB,1)} | ConvertTo-Json -Compress",12)
    if not isinstance(data,dict): return [Check("Performance Counters",Severity.UNKNOWN,"CPU/memory counters could not be collected.",details=r.stdout+r.stderr,recommendation="Retry the diagnostic or inspect Task Manager.",elapsed=r.elapsed)]
    cpu=data.get("CPU"); mem=data.get("Memory")
    for label,val,rec in [("CPU Usage",cpu,"Review top CPU consumers before terminating processes."),("Memory Usage",mem,"Review memory-heavy processes and available RAM.")]:
        if val is None: out.append(Check(label,Severity.UNKNOWN,"Performance value unavailable.")); continue
        sev=Severity.WARN if float(val)>=90 else Severity.OK
        out.append(Check(label,sev,f"{float(val):.1f}% used.",float(val),details=r.stdout,recommendation=rec if sev==Severity.WARN else "",elapsed=r.elapsed))
    out.append(Check("Memory Capacity",Severity.OK,f"{data.get('TotalRAMGB','?')} GB total, {data.get('FreeRAMGB','?')} GB free.",details=r.stdout))
    return out
