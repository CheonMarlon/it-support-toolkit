import argparse
import json
import os
import shutil
import textwrap
import time
from datetime import datetime

from src.utils.platform import app_root, summary, is_admin
from src.workflows import WORKFLOWS, BY_KEY
from src.engine.rules import network_findings, generic_findings
from src.repairs.catalog import REPAIRS
from src.reports.io import save_session, list_sessions, export_text, export_json, export_html


# --- Professional table output helpers ---
def _term_width(default=100):
    try:
        return max(72, min(140, shutil.get_terminal_size((default, 24)).columns))
    except Exception:
        return default

def _clip(value, width):
    text = "" if value is None else str(value).replace("\r", " ").replace("\n", " ")
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[:width-3] + "..."

def print_rule(char="=", width=None):
    print(char * (width or _term_width()))

def print_title(title, subtitle=None):
    width = _term_width()
    print_rule("=" , width)
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print_rule("=" , width)

def print_table(headers, rows, widths=None, align=None):
    """Render readable ASCII tables with wrapped cells instead of truncating important text."""
    import textwrap

    width = _term_width()
    headers = [str(h) for h in headers]
    rows = [[("" if c is None else str(c)).replace("\r", " ") for c in r] for r in rows]
    cols = len(headers)
    if cols == 0:
        return

    # Give important prose columns more room. The table will wrap long text
    # instead of replacing it with "...".
    if widths is None:
        natural = []
        for i in range(cols):
            vals = [headers[i]] + [r[i] if i < len(r) else "" for r in rows]
            natural.append(max(len(v) for v in vals))

        available = max(60, width - (3 * cols + 1))
        if sum(natural) <= available:
            widths = natural
        else:
            # Sensible minimums, with more space assigned to prose columns.
            mins = [10] * cols
            for i, h in enumerate(headers):
                if h.upper() in ("RESULT", "EVIDENCE", "RECOMMENDATION", "FINDING", "NEXT STEP"):
                    mins[i] = 18

            # If this is a very narrow terminal, keep every column usable.
            if sum(mins) > available:
                mins = [max(8, int(available / cols))] * cols

            extra_space = max(0, available - sum(mins))
            extra_need = [max(0, n - m) for n, m in zip(natural, mins)]
            total_need = sum(extra_need) or 1

            widths = [
                m + int(extra_space * need / total_need)
                for m, need in zip(mins, extra_need)
            ]

    widths = [max(8, int(w)) for w in widths]
    if align is None:
        align = ["left"] * cols

    def border(ch="-"):
        return "+" + "+".join(ch * (w + 2) for w in widths) + "+"

    def wrapped_lines(value, w):
        value = "" if value is None else str(value)
        # Preserve readable word boundaries; break very long paths/commands.
        return textwrap.wrap(
            value,
            width=w,
            break_long_words=True,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=True,
        ) or [""]

    print(border("="))
    print("| " + " | ".join(
        headers[i][:widths[i]].ljust(widths[i]) for i in range(cols)
    ) + " |")
    print(border("="))

    for row in rows:
        cells = [
            wrapped_lines(row[i] if i < len(row) else "", widths[i])
            for i in range(cols)
        ]
        height = max(len(c) for c in cells)

        for line_no in range(height):
            rendered = []
            for i in range(cols):
                value = cells[i][line_no] if line_no < len(cells[i]) else ""
                if align[i] == "right":
                    value = value.rjust(widths[i])
                else:
                    value = value.ljust(widths[i])
                rendered.append(value)
            print("| " + " | ".join(rendered) + " |")

    print(border("-"))

def print_kv_table(items, title=None):
    if title:
        print(f"\n  {title}")
    rows = [[k, v] for k, v in items]
    print_table(["FIELD", "VALUE"], rows)

def print_findings_table(findings):
    rows = []
    for f in findings:
        if isinstance(f, dict):
            rows.append([
                f.get("severity", "INFO").upper(),
                f.get("title", f.get("name", "")),
                f.get("confidence", ""),
                f.get("evidence", ""),
                f.get("recommendation", f.get("next_step", "")),
            ])
        else:
            rows.append(["INFO", str(f), "", "", ""])
    print_table(
        ["STATUS", "FINDING", "CONFIDENCE", "EVIDENCE", "RECOMMENDATION"],
        rows,
    )

def print_diagnostic_table(records):
    """Normalize common diagnostic record shapes into a technician-friendly table."""
    rows = []
    for r in records or []:
        if isinstance(r, dict):
            status = r.get("status", r.get("severity", "INFO")).upper()
            name = r.get("name", r.get("check", r.get("title", "")))
            value = r.get("value", r.get("result", r.get("details", "")))
            next_step = r.get("recommendation", r.get("next_step", ""))
            rows.append([status, name, value, next_step])
        else:
            rows.append(["INFO", "", str(r), ""])
    print_table(["STATUS", "CHECK", "RESULT", "NEXT STEP"], rows)



VERSION = "2.1.0-CLI-PROFESSIONAL"

# ---------------------------------------------------------------------------
# Console UI
# ---------------------------------------------------------------------------

WIDTH = 76
INNER = WIDTH - 4

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause(message="Press ENTER to continue..."):
    try:
        input(f"\n  {message}")
    except (EOFError, KeyboardInterrupt):
        pass

def line(char="=", width=WIDTH):
    return char * width

def box(title, subtitle=None):
    print(line("="))
    print(f"  {title[:INNER]}")
    if subtitle:
        print(f"  {subtitle[:INNER]}")
    print(line("="))

def section(title):
    print(f"\n  {title.upper()}")
    print(f"  {line('-', len(title)+2)}")

def wrap(text, width=INNER, prefix="  ", continuation="    "):
    text = "" if text is None else str(text)
    return textwrap.fill(text, width=width, initial_indent=prefix,
                         subsequent_indent=continuation)

def menu(items, columns=1):
    # Keep menus compact enough for a normal 80x25 CMD window.
    if columns == 1:
        for key, label in items:
            print(f"  [{key}] {label}")
    else:
        rows = (len(items) + columns - 1) // columns
        colw = max(1, INNER // columns)
        for r in range(rows):
            parts = []
            for c in range(columns):
                i = r + c * rows
                if i < len(items):
                    k, label = items[i]
                    parts.append(f"[{k}] {label}".ljust(colw))
            print("  " + "".join(parts).rstrip())

def ask_choice(valid):
    try:
        value = input("\n  Select an option: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "0"
    return value if value in valid else None

def status_tag(severity):
    s = getattr(severity, "value", str(severity)).upper()
    return {
        "OK": "[ OK ]", "INFO": "[INFO ]", "WARN": "[WARN ]",
        "FAIL": "[FAIL ]", "CRITICAL": "[CRIT ]"
    }.get(s, f"[{s[:6]:^6}]")

def render_check(check):
    status=getattr(check.severity,"value",str(check.severity)).upper()
    result=check.message
    if getattr(check,"value",None) not in (None, ""):
        result=f"{result} | Value: {check.value}"
    print_table(["STATUS","CHECK","RESULT","NEXT STEP"], [[status,check.name,result,check.recommendation or "-"]])

def render_findings(findings):
    section("Technician findings")
    if not findings:
        print("  No rule-based findings were generated.")
        return
    rows=[]
    for finding in findings:
        rows.append([getattr(finding.severity,"value",str(finding.severity)).upper(),finding.title,finding.confidence,finding.evidence,finding.recommendation])
    print_table(["STATUS","FINDING","CONFIDENCE","EVIDENCE","RECOMMENDATION"],rows)

def run_workflow(key, session):
    name, fn = BY_KEY[key]
    clear()
    box(f"DIAGNOSTIC - {name.upper()}",
        f"PC: {session['ticket_info'].get('computer') or summary()['computer']}  |  Admin: {'YES' if is_admin() else 'NO'}")
    print("\n  Collecting live evidence. Please wait...\n")
    started = time.time()
    try:
        checks = fn()
    except Exception as exc:
        print(f"  [FAIL ] Diagnostic could not complete: {exc}")
        pause()
        return
    findings = network_findings(checks) if key in ("network", "wifi") else generic_findings(checks)
    session["checks"] = [c.to_dict() for c in checks]
    session["findings"] = [f.to_dict() for f in findings]
    session["last_workflow"] = name
    session["last_run"] = datetime.now().isoformat(timespec="seconds")

    for check in checks:
        render_check(check)
        print()
    render_findings(findings)
    print(f"\n  Completed in {time.time()-started:.1f}s.")
    pause()

def ticket_menu(session):
    while True:
        clear()
        ti = session["ticket_info"]
        box("TICKET / SESSION",
            f"Ticket: {session.get('ticket') or 'Not created'}")
        menu([
            ("1", "Create / edit ticket"),
            ("2", "View current ticket"),
            ("3", "Save session"),
            ("4", "Export report"),
            ("5", "View saved sessions"),
            ("0", "Back"),
        ])
        choice = ask_choice(set("123450"))
        if choice == "0": return
        if choice == "1":
            fields = [
                ("ticket", "Ticket / incident number", session.get("ticket","")),
                ("user", "User / requester", ti.get("user","")),
                ("computer", "Computer name", ti.get("computer","")),
                ("department", "Department", ti.get("department","")),
                ("problem", "Problem description", ti.get("problem","")),
            ]
            for key, label, current in fields:
                try:
                    value=input(f"  {label}" + (f" [{current}]" if current else "") + ": ").strip()
                except (EOFError, KeyboardInterrupt):
                    value=""
                if value:
                    if key == "ticket": session["ticket"]=value
                    else: ti[key]=value
            print("\n  Ticket updated.")
            pause()
        elif choice == "2":
            section("Current ticket")
            print(f"  Ticket       : {session.get('ticket') or 'Not created'}")
            for k in ("user","computer","department","problem"):
                print(f"  {k.title():<13}: {ti.get(k) or 'Not entered'}")
            print(f"  Last workflow: {session.get('last_workflow') or 'None'}")
            pause()
        elif choice == "3":
            path=save_session(app_root(), session)
            print(f"\n  [OK] Session saved:\n       {path}")
            pause()
        elif choice == "4":
            export_menu(session)
        elif choice == "5":
            sessions=list_sessions(app_root())
            clear(); box("SAVED SESSIONS")
            if not sessions:
                print("  No saved sessions yet.")
            else:
                for i,p in enumerate(sessions[:15],1):
                    print(f"  [{i:02}] {p.name}")
                if len(sessions)>15:
                    print(f"\n  Showing newest 15 of {len(sessions)}.")
            pause()

def export_menu(session):
    clear(); box("EXPORT REPORT")
    if not session.get("ticket"):
        print("  A ticket number is recommended before exporting.")
    menu([("1","TXT report"),("2","JSON report"),("3","HTML report"),("0","Back")])
    choice=ask_choice(set("1230"))
    if choice=="1":
        p=export_text(app_root(),session)
    elif choice=="2":
        p=export_json(app_root(),session)
    elif choice=="3":
        p=export_html(app_root(),session)
    else:
        return
    print(f"\n  [OK] Report created:\n       {p}")
    pause()

def repairs_menu(session):
    while True:
        clear(); box("APPROVED REPAIRS",
                      f"Administrator: {'YES' if is_admin() else 'NO'}")
        items=[(str(i+1),name) for i,name in enumerate(REPAIRS)]
        items.append(("0","Back"))
        menu(items)
        choice=ask_choice({str(i) for i in range(len(REPAIRS)+1)})
        if choice=="0": return
        if not choice: continue
        name=list(REPAIRS)[int(choice)-1]
        item=REPAIRS[name]
        clear(); box(f"REPAIR - {name.upper()}")
        print(wrap(item["description"]))
        print(wrap(f"Impact: {item['impact']}"))
        if item["requires_admin"] and not is_admin():
            print("\n  [BLOCKED] Administrator privileges are required.")
            print("  This toolkit will not silently elevate itself.")
            pause(); continue
        print("\n  This action will change the computer.")
        try: confirm=input("  Type YES to continue: ").strip()
        except (EOFError, KeyboardInterrupt): confirm=""
        if confirm != "YES":
            print("  Cancelled.")
            pause(); continue
        try:
            result=item["function"]()
            session.setdefault("actions",[]).append(result.to_dict())
            print(f"\n  [{'OK' if result.success else 'FAIL'}] {result.message}")
            if result.details: print(wrap(result.details))
        except Exception as exc:
            print(f"\n  [FAIL] Repair error: {exc}")
        pause("Press ENTER after reviewing the result...")

def system_info():
    clear(); s=summary()
    box("SYSTEM INFORMATION")
    for k,label in [
        ("computer","Computer"),("os","OS"),("version","Windows Version"),
        ("architecture","Architecture"),("python","Python"),("administrator","Administrator")
    ]:
        print(f"  {label:<16}: {s.get(k)}")
    print(f"  {'Toolkit':<16}: {VERSION}")
    pause()

def diagnostics_menu(session, title, keys):
    while True:
        clear(); box(title.upper(), "Select a focused diagnostic")
        menu([(str(i+1), BY_KEY[k][0]) for i,k in enumerate(keys)])
        print("  [0] Back")
        valid={str(i) for i in range(len(keys)+1)}
        choice=ask_choice(valid)
        if choice=="0": return
        if choice and choice!="0":
            run_workflow(keys[int(choice)-1],session)

def full_diagnostic(session):
    clear(); box("FULL SYSTEM DIAGNOSTIC",
                  "Read-only collection across core workstation areas")
    print("\n  This runs multiple diagnostics and may take several minutes.")
    try: confirm=input("  Type RUN to continue: ").strip()
    except (EOFError,KeyboardInterrupt): confirm=""
    if confirm!="RUN":
        print("  Cancelled."); pause(); return
    all_checks=[]; all_findings=[]
    for key in [k for _,k,_ in WORKFLOWS if k!="full"]:
        name,fn=BY_KEY[key]
        print(f"\n  >> {name}")
        try:
            checks=fn()
            findings=network_findings(checks) if key in ("network","wifi") else generic_findings(checks)
            all_checks.extend(checks); all_findings.extend(findings)
            print(f"     {len(checks)} checks completed.")
        except Exception as exc:
            print(f"     [FAIL] {exc}")
    session["checks"]=[c.to_dict() for c in all_checks]
    session["findings"]=[f.to_dict() for f in all_findings]
    session["last_workflow"]="Full Diagnostic"
    clear(); box("FULL DIAGNOSTIC RESULTS")
    counts={}
    for c in all_checks:
        s=getattr(c.severity,"value",str(c.severity)); counts[s]=counts.get(s,0)+1
    print(f"  Checks completed : {len(all_checks)}")
    print(f"  OK               : {counts.get('OK',0)}")
    print(f"  Warnings         : {counts.get('WARN',0)}")
    print(f"  Failures         : {counts.get('FAIL',0)}")
    print(f"  Critical         : {counts.get('CRITICAL',0)}")
    print(f"  Inconclusive     : {counts.get('UNKNOWN',0)+counts.get('INFO',0)}")
    print_diagnostic_table(all_checks)
    render_findings(all_findings)
    pause()

def main_menu():
    session={
        "ticket": "",
        "ticket_info": {
            "user": "", "computer": summary()["computer"],
            "department": "", "problem": ""
        },
        "checks": [], "findings": [], "actions": [],
        "verification": "Not completed."
    }
    connectivity=["network","wifi","vpn","network_drive"]
    hardware=["printer","spooler","audio","audio_service","camera","bluetooth","display","usb","drivers","battery"]
    windows=["updates","security","accounts","services","event_errors"]
    performance=["performance","storage","applications","system"]

    while True:
        clear()
        s=summary()
        box("IT SUPPORT TOOLKIT",
            f"PC: {s['computer']}  |  OS: {s['os']}  |  Admin: {'YES' if s['administrator'] else 'NO'}")
        print("\n  QUICK ACCESS")
        menu([
            ("1","Connectivity & Network"),
            ("2","Hardware & Peripherals"),
            ("3","Windows & Security"),
            ("4","Performance & Software"),
            ("5","FULL SYSTEM DIAGNOSTIC"),
            ("6","Ticket / Session / Reports"),
            ("7","Approved Repairs"),
            ("8","System Information"),
            ("0","Exit"),
        ],columns=2)
        print(f"\n  Status: {session.get('last_workflow') or 'Ready'}")
        choice=ask_choice(set("012345678"))
        if choice=="0":
            clear(); box("IT SUPPORT TOOLKIT","Session ended.")
            return 0
        if choice=="1": diagnostics_menu(session,"CONNECTIVITY & NETWORK",connectivity)
        elif choice=="2": diagnostics_menu(session,"HARDWARE & PERIPHERALS",hardware)
        elif choice=="3": diagnostics_menu(session,"WINDOWS & SECURITY",windows)
        elif choice=="4": diagnostics_menu(session,"PERFORMANCE & SOFTWARE",performance)
        elif choice=="5": full_diagnostic(session)
        elif choice=="6": ticket_menu(session)
        elif choice=="7": repairs_menu(session)
        elif choice=="8": system_info()

def cli(args):
    if args.version:
        print(f"IT Support Toolkit {VERSION}")
        return 0
    if args.command=="diagnose":
        name,fn=BY_KEY[args.workflow]
        checks=fn()
        findings=network_findings(checks) if args.workflow in ("network","wifi") else generic_findings(checks)
        data={"workflow":name,"checks":[c.to_dict() for c in checks],"findings":[f.to_dict() for f in findings]}
        print(json.dumps(data,indent=2,default=str) if args.json else format_cli(name,checks,findings))
        return 0
    return main_menu()

def format_cli(name,checks,findings):
    clear()
    box(f"DIAGNOSTIC - {name.upper()}")
    for c in checks:
        render_check(c)
        print()
    render_findings(findings)
    return 0

def main():
    p=argparse.ArgumentParser(prog="IT-Support-Toolkit",
        description="Professional Windows IT support diagnostic toolkit")
    p.add_argument("--version",action="store_true")
    sub=p.add_subparsers(dest="command")
    d=sub.add_parser("diagnose",help="Run one diagnostic directly")
    d.add_argument("workflow",choices=list(BY_KEY.keys()))
    d.add_argument("--json",action="store_true")
    a=p.parse_args()
    return cli(a)

if __name__=="__main__":
    raise SystemExit(main())
