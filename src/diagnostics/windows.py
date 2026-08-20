from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import ps_json, run

def service(name,label):
    if not is_windows(): return [Check(label,Severity.UNKNOWN,"Unavailable on this platform.")]
    r,data=ps_json(f"Get-Service -Name '{name}' -ErrorAction SilentlyContinue | Select Status,Name,DisplayName,StartType | ConvertTo-Json -Compress",10)
    if data is None:
        return [Check(label,Severity.UNKNOWN,f"Windows did not return service state for {name}.",details=r.stdout+r.stderr,recommendation=f"Open Services and inspect {name}.",elapsed=r.elapsed)]
    item=data if isinstance(data,dict) else data[0]
    status=str(item.get("Status",""))
    sev=Severity.OK if status.lower()=="running" else Severity.WARN
    return [Check(label,sev,f"Service status: {status}.",value=status,details=r.stdout,
                  recommendation=f"Review {name} configuration and dependencies." if sev!=Severity.OK else "",elapsed=r.elapsed)]

def run_updates():
    checks=service("wuauserv","Windows Update Service")
    if is_windows():
        r,data=ps_json("Get-HotFix -ErrorAction SilentlyContinue | Sort-Object InstalledOn -Descending | Select -First 5 HotFixID,InstalledOn,Description | ConvertTo-Json -Compress -Depth 4",15)
        checks.append(Check("Recent Windows Updates",Severity.OK if data else Severity.UNKNOWN,
            "Recent installed updates were retrieved." if data else "Windows returned no recent update inventory.",details=r.stdout+r.stderr,elapsed=r.elapsed,
            recommendation="Use Windows Update settings to check for pending updates." if not data else ""))
    return checks

def run_audio_service(): return service("Audiosrv","Windows Audio Service")
def run_spooler(): return service("Spooler","Print Spooler")

def run_services():
    if not is_windows(): return [Check("Windows Services",Severity.UNKNOWN,"Unavailable on this platform.")]
    r,data=ps_json("Get-Service | Where-Object {$_.Status -eq 'Stopped'} | Select -First 50 Status,Name,DisplayName,StartType | ConvertTo-Json -Compress -Depth 4",15)
    if data is None: return [Check("Stopped Services",Severity.UNKNOWN,"Windows returned no service inventory.",details=r.stdout+r.stderr,elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    return [Check("Stopped Services",Severity.INFO,f"{len(items)} stopped service(s) were inventoried; stopped does not automatically mean faulty.",value=len(items),details=r.stdout,recommendation="Investigate only services relevant to the reported issue.",elapsed=r.elapsed)]

def run_event_errors():
    if not is_windows(): return [Check("Event Logs",Severity.UNKNOWN,"Unavailable on this platform.")]
    cmd="Get-WinEvent -FilterHashtable @{LogName='System';Level=1,2;StartTime=(Get-Date).AddDays(-3)} -MaxEvents 30 -ErrorAction SilentlyContinue | Select TimeCreated,ProviderName,Id,LevelDisplayName,Message | ConvertTo-Json -Compress -Depth 5"
    r,data=ps_json(cmd,20)
    if data is None:
        return [Check("Recent System Errors",Severity.UNKNOWN,"No usable System error-event inventory was returned.",details=r.stdout+r.stderr,recommendation="Check Event Viewer > Windows Logs > System.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    return [Check("Recent System Errors",Severity.WARN if items else Severity.OK,
        f"{len(items)} recent System critical/error event(s) found." if items else "No recent System critical/error events were found in the selected window.",value=len(items),details=r.stdout,
        recommendation="Review the event timestamps and providers against the reported failure." if items else "",elapsed=r.elapsed)]

def run_accounts():
    r=run(["whoami"],5)
    if r.code!=0 or not r.stdout.strip(): return [Check("Current Account",Severity.UNKNOWN,"Current account could not be determined.",details=r.stderr,elapsed=r.elapsed)]
    return [Check("Current Account",Severity.OK,"Current Windows account identified.",value=r.stdout.strip(),details=r.stderr,elapsed=r.elapsed)]

def run_security():
    if not is_windows(): return [Check("Windows Security",Severity.UNKNOWN,"Unavailable on this platform.")]
    out=[]
    r,data=ps_json("Get-NetFirewallProfile -ErrorAction SilentlyContinue | Select Name,Enabled,DefaultInboundAction,DefaultOutboundAction | ConvertTo-Json -Compress -Depth 4",12)
    if data is None:
        out.append(Check("Windows Firewall",Severity.UNKNOWN,"Firewall profile status could not be retrieved.",details=r.stdout+r.stderr,recommendation="Open Windows Security > Firewall & network protection.",elapsed=r.elapsed))
    else:
        items=data if isinstance(data,list) else [data]; disabled=[x for x in items if x.get("Enabled") is False]
        out.append(Check("Windows Firewall",Severity.WARN if disabled else Severity.OK,
            f"{len(disabled)} firewall profile(s) disabled." if disabled else "Firewall profiles are enabled.",value=len(items),details=r.stdout,
            recommendation="Review the disabled firewall profile(s)." if disabled else "",elapsed=r.elapsed))
    r,data=ps_json("Get-MpComputerStatus -ErrorAction SilentlyContinue | Select AntivirusEnabled,RealTimeProtectionEnabled,AMServiceEnabled,AntispywareEnabled | ConvertTo-Json -Compress",12)
    if data is None:
        out.append(Check("Microsoft Defender",Severity.UNKNOWN,"Defender status could not be retrieved; another antivirus may be installed.",details=r.stdout+r.stderr,recommendation="Check Windows Security or the installed endpoint security product.",elapsed=r.elapsed))
    else:
        bad=any(x is False for x in data.values())
        out.append(Check("Microsoft Defender",Severity.WARN if bad else Severity.OK,
            "One or more Defender protections are disabled." if bad else "Defender protection services are enabled.",details=r.stdout,
            recommendation="Review endpoint protection configuration." if bad else "",elapsed=r.elapsed))
    return out
