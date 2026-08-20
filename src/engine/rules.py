from .models import Finding, Severity

def _unavailable(check):
    return check is not None and check.severity in (Severity.INFO, Severity.UNKNOWN)

def network_findings(checks):
    d={c.name:c for c in checks}; out=[]
    if d.get("IP Configuration") and d["IP Configuration"].severity==Severity.FAIL:
        out.append(Finding("No usable IPv4 configuration","HIGH",d["IP Configuration"].message,
            "Check adapter state and DHCP/manual addressing. Renew DHCP if appropriate.",Severity.FAIL))
        return out
    if d.get("Gateway Reachability") and d["Gateway Reachability"].severity==Severity.FAIL:
        out.append(Finding("Default gateway is unreachable","HIGH",d["Gateway Reachability"].message,
            "Check cable/Wi-Fi, adapter state, VLAN/local network access and gateway.",Severity.FAIL))
    if d.get("DNS Resolution") and d["DNS Resolution"].severity==Severity.FAIL:
        if d.get("Internet Reachability") and d["Internet Reachability"].severity==Severity.OK:
            out.append(Finding("DNS resolution is failing","HIGH",
                "IP reachability succeeded while DNS resolution failed.",
                "Verify DNS server configuration and DNS client state.",Severity.FAIL))
        else:
            out.append(Finding("DNS resolution failed","MEDIUM",d["DNS Resolution"].message,
                "Verify DNS configuration after basic connectivity is restored.",Severity.WARN))
    if any(_unavailable(c) for c in checks) and not out:
        out.append(Finding("Network result is inconclusive","LOW",
            "One or more required evidence sources were unavailable.",
            "Repeat the diagnostic or collect the affected adapter/gateway evidence manually.",Severity.UNKNOWN))
    elif not out and checks and all(c.severity==Severity.OK for c in checks):
        out.append(Finding("No fault detected by selected checks","HIGH",
            "All selected checks completed successfully.",
            "If the issue persists, test the affected application, destination or account.",Severity.OK))
    elif not out:
        out.append(Finding("Root cause not determined","UNKNOWN",
            "Available evidence does not isolate one cause.",
            "Collect additional evidence or run the ticket-specific workflow.",Severity.UNKNOWN))
    return out

def generic_findings(checks):
    bad=[c for c in checks if c.severity in (Severity.FAIL,Severity.CRITICAL)]
    warn=[c for c in checks if c.severity==Severity.WARN]
    unknown=[c for c in checks if c.severity in (Severity.INFO,Severity.UNKNOWN)]
    if bad:
        return [Finding("One or more checks require attention","HIGH",
            "; ".join(f"{c.name}: {c.message}" for c in bad[:4]),
            next((c.recommendation for c in bad if c.recommendation),"Investigate the failed checks and verify after any repair."),Severity.FAIL)]
    if warn:
        return [Finding("Potential issue detected","MEDIUM",
            "; ".join(f"{c.name}: {c.message}" for c in warn[:4]),
            next((c.recommendation for c in warn if c.recommendation),"Review the warnings before making changes."),Severity.WARN)]
    if unknown:
        return [Finding("Diagnostic result is inconclusive","LOW",
            "; ".join(f"{c.name}: {c.message}" for c in unknown[:4]),
            next((c.recommendation for c in unknown if c.recommendation),
                 "The tool could not collect enough evidence to declare the device healthy."),Severity.UNKNOWN)]
    if checks:
        return [Finding("No issue detected by selected checks","HIGH",
            "Selected diagnostics completed successfully with usable evidence.",
            "If the reported issue remains, run a more specific workflow.",Severity.OK)]
    return [Finding("No diagnostic evidence collected","UNKNOWN",
        "The selected workflow returned no checks.","Run the diagnostic again or collect evidence manually.",Severity.UNKNOWN)]
