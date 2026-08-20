from src.diagnostics.system import run_system
from src.diagnostics.network import run_network
from src.diagnostics.wifi import run_wifi
from src.diagnostics.storage import run_storage
from src.diagnostics.performance import run_performance
from src.diagnostics.devices import run_printer,run_audio,run_bluetooth,run_camera,run_usb,run_display,run_drivers
from src.diagnostics.windows import run_updates,run_audio_service,run_spooler,run_services,run_event_errors,run_accounts,run_security
from src.diagnostics.battery import run_battery
from src.diagnostics.applications import run_applications
from src.diagnostics.misc import run_vpn,run_network_drive,run_display_resolution,run_full

WORKFLOWS=[
("Network / Internet","network",run_network),
("Wi-Fi","wifi",run_wifi),
("VPN","vpn",run_vpn),
("Computer Running Slowly","performance",run_performance),
("Low Disk Space","storage",run_storage),
("Printer","printer",run_printer),
("Print Spooler","spooler",run_spooler),
("Audio / Speakers","audio",run_audio),
("Windows Audio Service","audio_service",run_audio_service),
("Camera / Webcam","camera",run_camera),
("Bluetooth","bluetooth",run_bluetooth),
("Display / Monitor","display",run_display),
("USB / External Devices","usb",run_usb),
("Drivers / Device Errors","drivers",run_drivers),
("Battery","battery",run_battery),
("Applications / Processes","applications",run_applications),
("Windows Update","updates",run_updates),
("Security / Antivirus","security",run_security),
("Accounts / Login","accounts",run_accounts),
("Network Drives","network_drive",run_network_drive),
("Windows Services","services",run_services),
("Recent System Errors","event_errors",run_event_errors),
("System Information","system",run_system),
("Full Diagnostic","full",run_full),
]
BY_KEY={k:(n,fn) for n,k,fn in WORKFLOWS}
