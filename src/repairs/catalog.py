from .actions import flush_dns, renew_dhcp, reset_winsock, restart_spooler, sfc_scan

REPAIRS={
    "Flush DNS Cache":{
        "description":"Clears the Windows DNS resolver cache. Low-risk and useful when DNS data is stale.",
        "impact":"Temporary DNS resolution interruption is possible.",
        "requires_admin":True,"function":flush_dns
    },
    "Renew DHCP Lease":{
        "description":"Requests a new DHCP lease from the network.",
        "impact":"Network connectivity may briefly interrupt.",
        "requires_admin":True,"function":renew_dhcp
    },
    "Reset Winsock":{
        "description":"Resets the Windows Winsock catalog.",
        "impact":"A Windows restart may be required.",
        "requires_admin":True,"function":reset_winsock
    },
    "Restart Print Spooler":{
        "description":"Restarts the Windows Print Spooler service.",
        "impact":"Active printing may be interrupted.",
        "requires_admin":True,"function":restart_spooler
    },
    "Run System File Checker":{
        "description":"Runs Windows SFC to check protected system files.",
        "impact":"Can take time and consumes system resources.",
        "requires_admin":True,"function":sfc_scan
    }
}
