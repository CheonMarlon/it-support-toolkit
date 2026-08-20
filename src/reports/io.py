import json, html, datetime
from pathlib import Path

def save_session(root,data):
    d=Path(root)/"sessions"; d.mkdir(exist_ok=True)
    stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ticket=(data.get("ticket") or "SESSION").replace(" ","_").replace("/","-")
    p=d/f"{ticket}_{stamp}.json"
    p.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8")
    return p

def list_sessions(root):
    d=Path(root)/"sessions"
    return sorted(d.glob("*.json"),reverse=True) if d.exists() else []

def export_text(root,data):
    d=Path(root)/"exports"; d.mkdir(exist_ok=True)
    p=d/f"{data.get('ticket','ticket')}_report.txt"
    lines=["IT SUPPORT TOOLKIT REPORT","="*72,""]
    lines += [f"{k}: {v}" for k,v in data.get("ticket_info",{}).items()]
    lines += ["","DIAGNOSTICS","-"*72]
    for c in data.get("checks",[]): lines.append(f"[{c['severity']}] {c['name']}: {c['message']}")
    lines += ["","FINDINGS","-"*72]
    for f in data.get("findings",[]): lines.append(f"[{f['severity']}] {f['title']} ({f['confidence']})\nEvidence: {f['evidence']}\nRecommendation: {f['recommendation']}\n")
    lines += ["ACTIONS","-"*72]
    for a in data.get("actions",[]): lines.append(f"{a['name']}: {'SUCCESS' if a['success'] else 'FAILED'} — {a['message']}")
    lines += ["","VERIFICATION","-"*72,data.get("verification","Not completed.")]
    p.write_text("\n".join(lines),encoding="utf-8"); return p

def export_json(root,data):
    d=Path(root)/"exports"; d.mkdir(exist_ok=True)
    p=d/f"{data.get('ticket','ticket')}_report.json"
    p.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8"); return p

def export_html(root,data):
    d=Path(root)/"exports"; d.mkdir(exist_ok=True)
    p=d/f"{data.get('ticket','ticket')}_report.html"
    rows="".join(f"<tr><td>{html.escape(c['severity'])}</td><td>{html.escape(c['name'])}</td><td>{html.escape(c['message'])}</td></tr>" for c in data.get("checks",[]))
    fs="".join(f"<li><b>{html.escape(f['title'])}</b> ({html.escape(f['confidence'])})<br>{html.escape(f['evidence'])}<br><small>{html.escape(f['recommendation'])}</small></li>" for f in data.get("findings",[]))
    acts="".join(f"<li>{html.escape(a['name'])}: {'SUCCESS' if a['success'] else 'FAILED'} — {html.escape(a['message'])}</li>" for a in data.get("actions",[]))
    ti="<br>".join(f"<b>{html.escape(str(k))}:</b> {html.escape(str(v))}" for k,v in data.get("ticket_info",{}).items())
    doc=f"""<!doctype html><html><head><meta charset=utf-8><title>IT Support Report</title>
<style>body{{font:14px Segoe UI,Arial;margin:36px;color:#182230}}h1{{font-size:26px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d9dee7;padding:8px;text-align:left}}th{{background:#f3f5f8}}.box{{background:#f7f9fc;padding:14px;border-radius:8px;margin:12px 0}}</style></head>
<body><h1>IT Support Ticket Report</h1><div class=box>{ti}</div><h2>Diagnostics</h2><table><tr><th>Severity</th><th>Check</th><th>Message</th></tr>{rows}</table>
<h2>Findings</h2><ul>{fs}</ul><h2>Actions</h2><ul>{acts}</ul><h2>Verification</h2><div class=box>{html.escape(data.get("verification","Not completed."))}</div></body></html>"""
    p.write_text(doc,encoding="utf-8"); return p
