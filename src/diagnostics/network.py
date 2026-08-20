import ipaddress, re
from src.engine.models import Check, Severity
from src.utils.runner import run
from src.utils.platform import is_windows

def _ips(text):
    vals=[]
    for x in re.findall(r"IPv4 Address[^:]*:\s*([0-9.]+)",text,re.I):
        try:
            ip=ipaddress.ip_address(x)
            if not ip.is_loopback: vals.append(x)
        except ValueError: pass
    return vals

def run_network():
    if not is_windows(): return [Check("Network",Severity.UNKNOWN,"Windows network diagnostics are unavailable on this platform.")]
    out=[]
    r=run(["ipconfig","/all"],15); text=r.stdout
    ipv4=_ips(text)
    out.append(Check("IP Configuration",Severity.OK if ipv4 else Severity.FAIL,
        f"Usable IPv4 address: {ipv4[0]}." if ipv4 else "No usable IPv4 address detected.",ipv4[0] if ipv4 else None,text[-3500:],"Check DHCP or manual IP configuration." if not ipv4 else "",r.elapsed))
    gateways=[x.strip() for x in re.findall(r"Default Gateway[^:]*:\s*([0-9.]+)",text,re.I) if x.strip()]
    gw=gateways[0] if gateways else None
    out.append(Check("Default Gateway",Severity.OK if gw else Severity.FAIL,
        f"Default gateway: {gw}." if gw else "No default gateway detected.",gw,text[-2000:],"Check adapter, DHCP and local network configuration." if not gw else ""))
    if gw:
        p=run(["ping","-n","1","-w","1200",gw],5)
        out.append(Check("Gateway Reachability",Severity.OK if p.code==0 else Severity.FAIL,
            "Gateway responded." if p.code==0 else "Gateway did not respond.",gw,p.stdout[-1500:],"Check cable/Wi-Fi, adapter state, VLAN/local network access and gateway." if p.code!=0 else "",p.elapsed))
    d=run(["nslookup","example.com"],10)
    dns_ok=d.code==0 and bool(re.search(r"Address(?:es)?\s*:\s*[0-9a-fA-F:.]+",d.stdout,re.I))
    out.append(Check("DNS Resolution",Severity.OK if dns_ok else Severity.FAIL,
        "DNS resolution succeeded." if dns_ok else "DNS resolution failed.","example.com",d.stdout[-2500:]+d.stderr[-1000:],"Verify DNS server configuration." if not dns_ok else "",d.elapsed))
    p=run(["ping","-n","1","-w","1500","1.1.1.1"],5)
    out.append(Check("Internet Reachability",Severity.OK if p.code==0 else Severity.WARN,
        "Public IP reachability succeeded." if p.code==0 else "Public IP reachability failed.","1.1.1.1",p.stdout[-1500:],"Check upstream connectivity or firewall policy." if p.code!=0 else "",p.elapsed))
    return out
