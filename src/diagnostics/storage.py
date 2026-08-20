import os, shutil
from src.engine.models import Check, Severity

def run_storage():
    drives=[]
    if os.name=="nt":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            p=f"{letter}:\\"
            if os.path.exists(p): drives.append(p)
    else: drives=["/"]
    out=[]
    for drive in drives:
        try:
            total,used,free=shutil.disk_usage(drive); pct=used/total*100
            sev=Severity.FAIL if free<5*1024**3 else Severity.WARN if pct>=90 else Severity.OK
            out.append(Check(f"Disk {drive}",sev,
                f"{free/1024**3:.1f} GB free of {total/1024**3:.1f} GB ({pct:.1f}% used).",
                pct,recommendation="Free space before troubleshooting applications." if sev!=Severity.OK else ""))
        except Exception as e:
            out.append(Check(f"Disk {drive}",Severity.UNKNOWN,"Disk information unavailable.",details=str(e)))
    return out or [Check("Disk Storage",Severity.UNKNOWN,"No accessible local volumes were detected.")]
