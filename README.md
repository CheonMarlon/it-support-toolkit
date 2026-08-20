# IT Support Toolkit Professional

![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)

A portable Windows technician console for evidence-based troubleshooting. Built to run straight off a USB flash drive — no install, no Python required on the target machine.

## Why this exists

Most quick-fix diagnostic tools guess. This one doesn't. It separates **health** from **evidence availability**, so it never reports something is fine just because it couldn't check.

## Diagnostic truth model

- **OK** — evidence was collected and the check passed.
- **WARN** — evidence was collected and indicates a potential issue.
- **FAIL** — evidence was collected and the check failed.
- **UNKNOWN** — the tool could not obtain enough evidence to determine health.
- **INFO** — useful inventory/information that is not itself a health assertion.

**No evidence is never treated as a healthy result.**

## Included diagnostics

Network / Internet, Wi-Fi, VPN, mapped drives, printers, Print Spooler, audio, Windows Audio, camera/webcam, Bluetooth, display, USB, device-driver errors, battery, applications/processes, Windows Update, Windows Security/Defender, accounts, services, recent System errors, performance, storage, system information, and a full diagnostic pass.

## Professional output

Diagnostic checks and technician findings are rendered as width-aware ASCII tables. Long values wrap onto additional lines instead of truncating or breaking the table structure. Usable in a normal Command Prompt window, clearer when maximized.

## Windows environment behavior

Some corporate Windows environments restrict PowerShell/CIM/WMI, device inventory, endpoint-security APIs, or external network tests. The toolkit reports **UNKNOWN** when evidence cannot be collected rather than inventing an OK result.

---

## Getting the EXE

**Option 1 — Download the pre-built EXE**
Grab the latest `IT-Support-Toolkit.exe` from the [Releases](../../releases) page. Copy it, along with the `sessions` and `exports` folders, onto your USB drive. No Python required on the technician PC.

**Option 2 — Build it yourself**
A Windows machine with Python 3.11+ is required to build the EXE (PyInstaller must run in the Windows environment).

```bat
git clone https://github.com/YOUR-USERNAME/it-support-toolkit.git
cd it-support-toolkit
build_exe.bat
```

The script will:
1. Detect Python 3.11+
2. Check/install pip
3. Install PyInstaller if missing
4. Validate the source
5. Build a single-file console EXE
6. Verify and copy `IT-Support-Toolkit.exe` to the project root

## Running from source (no build)

```bash
python -m src.main
```

## Project structure

```
it_support_toolkit/
├── src/
│   ├── diagnostics/    # individual diagnostic checks
│   ├── engine/         # core run logic
│   ├── repairs/        # remediation helpers
│   ├── reports/        # output/export formatting
│   ├── utils/          # shared helpers
│   └── main.py         # entry point
├── tests/
├── build_exe.bat        # Windows EXE builder
├── run.bat               # quick launcher
└── VERSION.txt
```

## Contributing

Forks and pull requests are welcome. This project is licensed under the GPLv3 — if you distribute a modified version, your version must also be released as open source under GPLv3. See [LICENSE](LICENSE) for full terms.

Ways to contribute:
- Report issues or false OK/UNKNOWN classifications
- Add new diagnostic checks
- Improve output formatting or add export formats

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE) for the full text.
