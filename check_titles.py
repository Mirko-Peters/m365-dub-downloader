#!/usr/bin/env python3
"""Prueft <title> und meta description im erzeugten HTML (docs/ und r2out/, Ticket T7). Fehler (Exit 1): leerer Titel, Marke doppelt
(M365.FM/M365 FM mehr als einmal), Titel ueber 85 Zeichen, Beschreibung ueber 165 Zeichen. Hinweise: gleiche Titel auf mehreren
indexierbaren Seiten derselben Sprache, Titel mit Auslassungszeichen, fehlende Beschreibung."""
import html, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
DESC = re.compile(r'<meta name="description" content="([^"]*)"')
NOIDX = re.compile(r'<meta name="robots" content="[^"]*noindex')
LANG = re.compile(r'<html lang="([^"]+)"')
BRAND = re.compile(r"M365[ .]?FM", re.I)


def main():
    err, hint, n = Counter(), Counter(), 0
    ex = defaultdict(list); dup = defaultdict(list)
    for base in (ROOT / "docs", ROOT / "r2out"):
        if not base.exists(): continue
        for p in base.rglob("*.html"):
            try:
                h = p.read_text("utf-8")[:20000]
            except UnicodeDecodeError:
                continue
            if 'http-equiv="refresh"' in h or "http-equiv=refresh" in h: continue
            n += 1; rel = str(p.relative_to(base))
            m = TITLE.search(h); t = html.unescape(m.group(1)).strip() if m else ""
            d = DESC.search(h); dd = html.unescape(d.group(1)) if d else None
            def e(k):
                err[k] += 1; len(ex[k]) < 5 and ex[k].append(rel)
            def w(k):
                hint[k] += 1; len(ex[k]) < 5 and ex[k].append(rel)
            if not t: e("Titel fehlt")
            elif len(BRAND.findall(t)) > 1: e("Marke doppelt im Titel")
            elif len(t) > 85: e("Titel ueber 85 Zeichen")
            if t.endswith("…"): w("Titel mit Auslassungszeichen")
            if dd is None or not dd.strip(): w("Beschreibung fehlt")
            elif len(dd) > 165: e("Beschreibung ueber 165 Zeichen")
            if t and not NOIDX.search(h):
                lg = LANG.search(h); dup[((lg.group(1) if lg else ""), t)].append(rel)
    dd_ = {k: v for k, v in dup.items() if len(v) > 1}
    print(f"{n} Seiten geprueft: {sum(err.values())} Fehler, {sum(hint.values())} Hinweise, {len(dd_)} doppelte Titel (indexierbar, gleiche Sprache)")
    for k, c in err.most_common(): print("FEHLER", c, "x", k, "z.B.", ", ".join(ex[k]))
    for k, c in hint.most_common(): print("HINWEIS", c, "x", k, "z.B.", ", ".join(ex[k]))
    for (lg, t), v in sorted(dd_.items(), key=lambda kv: -len(kv[1]))[:15]: print(f"HINWEIS doppelter Titel ({lg}, {len(v)} Seiten): {t} z.B. {', '.join(v[:3])}")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
