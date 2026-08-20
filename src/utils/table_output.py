"""Professional, width-aware CLI table formatting."""
import shutil
import textwrap

def terminal_width(default=100):
    try:
        return max(80, min(140, shutil.get_terminal_size((default, 24)).columns))
    except Exception:
        return default

def clip(value, width):
    # Kept for compatibility; table() now wraps rather than clipping.
    text = "" if value is None else str(value).replace("\r", " ").replace("\n", " ")
    return text if len(text) <= width else text[:max(0, width-3)] + ("..." if width >= 3 else "")

def wrap(value, width):
    return textwrap.wrap(
        "" if value is None else str(value),
        width=max(1, width),
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]

def table(headers, rows, widths=None):
    headers = [str(h) for h in headers]
    rows = [[str(c) if c is not None else "" for c in r] for r in rows]
    n = len(headers)
    if not n:
        return ""
    if widths is None:
        natural = [max([len(headers[i])] + [len(r[i]) if i < len(r) else 0 for r in rows])
                   for i in range(n)]
        available = max(40, terminal_width() - (3*n + 1))
        if sum(natural) > available:
            mins = [min(10, x) for x in natural]
            remain = max(0, available - sum(mins))
            extra = [max(0, x-m) for x,m in zip(natural, mins)]
            total = sum(extra) or 1
            widths = [m + int(remain*e/total) for m,e in zip(mins,extra)]
        else:
            widths = natural
    def line(ch):
        return "+" + "+".join(ch*(w+2) for w in widths) + "+"
    out=[line("="),
         "| "+" | ".join(clip(headers[i],widths[i]).ljust(widths[i]) for i in range(n))+" |",
         line("=")]
    for r in rows:
        out.append("| "+" | ".join(clip(r[i] if i<len(r) else "",widths[i]).ljust(widths[i]) for i in range(n))+" |")
    out.append(line("-"))
    return "\n".join(out)
