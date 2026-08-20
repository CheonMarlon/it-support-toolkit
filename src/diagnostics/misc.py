from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import run, ps_json

def run_vpn():
    if not is_windows(): return [Check("VPN",Severity.UNKNOWN,"Unavailable on this platform.")]
    r,data=ps_json("Get-VpnConnection -AllUserConnection -ErrorAction SilentlyContinue | Select Name,ConnectionStatus,ServerAddress | ConvertTo-Json -Compress -Depth 4",12)
    if data is None: return [Check("VPN Connections",Severity.UNKNOWN,"No VPN connection inventory was returned. This does not prove that no VPN software is installed.",details=r.stdout+r.stderr,recommendation="Check the organization's VPN client if one is installed.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    connected=[x for x in items if str(x.get("ConnectionStatus","")).lower()=="connected"]
    return [Check("VPN Connections",Severity.OK,f"{len(items)} Windows VPN profile(s) found; {len(connected)} connected.",value=len(items),details=r.stdout,recommendation="If a third-party VPN client is used, inspect that client separately.",elapsed=r.elapsed)]

def run_network_drive():
    if not is_windows(): return [Check("Network Drives",Severity.UNKNOWN,"Unavailable on this platform.")]
    r=run(["net","use"],10)
    text=r.stdout.strip()
    if r.code!=0: return [Check("Mapped Drives",Severity.UNKNOWN,"Mapped-drive inventory could not be collected.",details=r.stderr,elapsed=r.elapsed)]
    return [Check("Mapped Drives",Severity.OK,"Mapped-drive information collected.",details=text or "No mapped drives reported.",elapsed=r.elapsed)]

def run_display_resolution():
    if not is_windows(): return [Check("Display",Severity.UNKNOWN,"Unavailable on this platform.")]
    r,data=ps_json("Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Select Name,DriverVersion,CurrentHorizontalResolution,CurrentVerticalResolution,Status | ConvertTo-Json -Compress -Depth 4",15)
    if data is None: return [Check("Display Adapter",Severity.UNKNOWN,"Display adapter inventory unavailable.",details=r.stdout+r.stderr,recommendation="Check Device Manager > Display adapters.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    bad=[x for x in items if str(x.get("Status","OK")).lower() not in ("ok","")]
    return [Check("Display Adapter",Severity.WARN if bad else Severity.OK,
        f"{len(items)} display adapter(s) found" + (f"; {len(bad)} report non-OK status." if bad else "."),value=len(items),details=r.stdout,
        recommendation="Inspect display driver/device status." if bad else "",elapsed=r.elapsed)]

def run_full():
    from .system import run_system
    from .network import run_network
    from .wifi import run_wifi
    from .storage import run_storage
    from .performance import run_performance
    from .battery import run_battery
    from .devices import run_printer,run_audio,run_bluetooth,run_camera,run_usb,run_display,run_drivers
    from .windows import run_updates,run_audio_service,run_spooler,run_services,run_event_errors,run_accounts,run_security
    from .applications import run_applications
    funcs=[run_system,run_network,run_wifi,run_storage,run_performance,run_battery,run_printer,run_audio,run_bluetooth,run_camera,run_usb,run_display,run_drivers,run_updates,run_audio_service,run_spooler,run_services,run_event_errors,run_accounts,run_security,run_applications,run_vpn,run_network_drive]
    checks=[]
    for fn in funcs:
        try: checks.extend(fn())
        except Exception as e: checks.append(Check(fn.__name__,Severity.UNKNOWN,"Diagnostic component failed gracefully.",details=str(e),recommendation="Retry this workflow independently."))
    return checks
