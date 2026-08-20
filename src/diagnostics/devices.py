from src.engine.models import Check, Severity
from src.utils.platform import is_windows
from src.utils.runner import run_powershell, ps_json

def _inventory(name, classes, recommendation, limit=50):
    if not is_windows():
        return [Check(name, Severity.UNKNOWN, "This Windows hardware diagnostic is unavailable on this platform.", recommendation=recommendation)]
    cls = ",".join(repr(c) for c in classes)
    script = f"""
$items = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
  Where-Object {{ $_.PNPClass -in @({cls}) }} |
  Select-Object -First {limit} Status,PNPClass,Name,Manufacturer,DeviceID,ConfigManagerErrorCode)
$items | ConvertTo-Json -Compress -Depth 5
"""
    r,data=ps_json(script,15)
    if r.code is None:
        return [Check(name,Severity.UNKNOWN,"The device inventory command timed out or could not run.",details=r.stderr+r.error,recommendation=recommendation,elapsed=r.elapsed)]
    if data is None:
        return [Check(name,Severity.UNKNOWN,"Windows returned no usable device inventory.",details=r.stdout+r.stderr,recommendation=recommendation,elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    bad=[x for x in items if str(x.get("Status","")) not in ("OK", "Unknown") or x.get("ConfigManagerErrorCode") not in (None,0,"0")]
    if bad:
        return [Check(name,Severity.WARN,f"{len(items)} device(s) found; {len(bad)} report a non-OK status.",value=len(items),details=r.stdout,recommendation=recommendation,elapsed=r.elapsed)]
    return [Check(name,Severity.OK,f"{len(items)} device(s) found and no device-level error was reported.",value=len(items),details=r.stdout,recommendation=recommendation,elapsed=r.elapsed)]

def run_printer():
    if not is_windows(): return [Check("Printers",Severity.UNKNOWN,"Unavailable on this platform.")]
    script="Get-CimInstance Win32_Printer -ErrorAction SilentlyContinue | Select Name,Default,PrinterStatus,WorkOffline,Status | ConvertTo-Json -Compress -Depth 4"
    r,data=ps_json(script,15)
    if data is None: return [Check("Printers",Severity.UNKNOWN,"Windows returned no printer inventory.",details=r.stdout+r.stderr,recommendation="Check Print Management or Settings > Printers & scanners.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    offline=[x for x in items if x.get("WorkOffline") is True]
    return [Check("Printers",Severity.WARN if offline else Severity.OK,
        f"{len(items)} printer(s) found; {len(offline)} marked offline." if offline else f"{len(items)} printer(s) found.",value=len(items),details=r.stdout,
        recommendation="Check printer power, network/USB connection and queue." if offline else "",elapsed=r.elapsed)]

def run_audio(): return _inventory("Audio Devices",["MEDIA","AudioEndpoint"],"Check Device Manager and Windows Sound settings; verify the output device and driver.")
def run_bluetooth(): return _inventory("Bluetooth Devices",["Bluetooth"],"Check Bluetooth radio state, pairing and Device Manager.")
def run_camera(): return _inventory("Camera / Webcam",["Camera","Image"],"Check Camera privacy permissions, physical connection and Device Manager driver.")
def run_usb(): return _inventory("USB Devices",["USB"],"Check the USB port, cable/device power and Device Manager for errors.")
def run_display(): return _inventory("Display Devices",["Display","Monitor"],"Check display cable/input, monitor power and graphics/display drivers.")

def run_drivers():
    if not is_windows(): return [Check("Drivers",Severity.UNKNOWN,"Unavailable on this platform.")]
    script="Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object {$_.ConfigManagerErrorCode -notin @($null,0)} | Select -First 60 Status,PNPClass,Name,ConfigManagerErrorCode,DeviceID | ConvertTo-Json -Compress -Depth 5"
    r,data=ps_json(script,15)
    if data is None:
        return [Check("Device Driver Errors",Severity.UNKNOWN,"Windows returned no usable driver-error inventory.",details=r.stdout+r.stderr,recommendation="Open Device Manager and inspect devices with a warning icon.",elapsed=r.elapsed)]
    items=data if isinstance(data,list) else [data]
    return [Check("Device Driver Errors",Severity.WARN,
        f"{len(items)} device(s) report a configuration/driver error.",value=len(items),details=r.stdout,
        recommendation="Inspect Device Manager and identify the affected device before changing drivers.",elapsed=r.elapsed)]
