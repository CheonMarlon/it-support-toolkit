from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import ps_json

def run_battery():
    if not is_windows(): return [Check("Battery",Severity.UNKNOWN,"Unavailable on this platform.")]
    script="Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select Name,BatteryStatus,EstimatedChargeRemaining,DesignVoltage,Status | ConvertTo-Json -Compress -Depth 4"
    r,data=ps_json(script,10)
    if data is None: return [Check("Battery",Severity.UNKNOWN,"No battery information was returned. This may be a desktop PC or the battery interface may be unavailable.",details=r.stdout+r.stderr,recommendation="If this is a laptop, check Device Manager > Batteries.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    charges=[x.get("EstimatedChargeRemaining") for x in items if isinstance(x.get("EstimatedChargeRemaining"),(int,float))]
    charge=charges[0] if charges else None
    sev=Severity.WARN if charge is not None and charge<=15 else Severity.OK
    return [Check("Battery",sev,f"{len(items)} battery device(s) detected"+(f"; charge {charge}%." if charge is not None else "."),charge,r.stdout,"Connect AC power and investigate battery health if charge is critically low." if sev==Severity.WARN else "",r.elapsed)]
