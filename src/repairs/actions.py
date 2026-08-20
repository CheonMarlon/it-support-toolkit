from src.engine.models import ActionResult
from src.utils.platform import is_windows, is_admin
from src.utils.runner import run

def _guard():
    if not is_windows(): return "Windows-only repair."
    if not is_admin(): return "Administrator privileges are required."
    return None

def flush_dns():
    err=_guard()
    if err: return ActionResult("Flush DNS Cache",False,err,requires_admin=True)
    r=run(["ipconfig","/flushdns"],15)
    return ActionResult("Flush DNS Cache",r.code==0,
                        "DNS cache was flushed." if r.code==0 else "DNS cache flush failed.",
                        r.stdout+r.stderr,True)

def renew_dhcp():
    err=_guard()
    if err: return ActionResult("Renew DHCP Lease",False,err,requires_admin=True)
    r=run(["ipconfig","/renew"],30)
    return ActionResult("Renew DHCP Lease",r.code==0,
                        "DHCP lease renewal completed." if r.code==0 else "DHCP renewal failed.",
                        r.stdout+r.stderr,True)

def reset_winsock():
    err=_guard()
    if err: return ActionResult("Reset Winsock",False,err,requires_admin=True)
    r=run(["netsh","winsock","reset"],15)
    return ActionResult("Reset Winsock",r.code==0,
                        "Winsock reset completed; a restart may be required." if r.code==0 else "Winsock reset failed.",
                        r.stdout+r.stderr,True)

def restart_spooler():
    err=_guard()
    if err: return ActionResult("Restart Print Spooler",False,err,requires_admin=True)
    r=run(["net","stop","spooler"],20)
    r2=run(["net","start","spooler"],20)
    ok=r2.code==0
    return ActionResult("Restart Print Spooler",ok,
                        "Print Spooler restarted." if ok else "Print Spooler restart failed.",
                        (r.stdout+r.stderr+"\n"+r2.stdout+r2.stderr),True)

def sfc_scan():
    err=_guard()
    if err: return ActionResult("Run System File Checker",False,err,requires_admin=True)
    r=run(["sfc","/scannow"],120)
    return ActionResult("Run System File Checker",r.code==0,
                        "SFC completed; review output for repair status." if r.code==0 else "SFC did not complete successfully.",
                        r.stdout+r.stderr,True)
