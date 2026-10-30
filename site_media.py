"""Kostenlose Bilder und eine Checkliste fuer Entitaetsseiten, zur Bauzeit erzeugt (kein KI-Dienst, keine Bilddateien):
- hero_svg: Titelbild (Name, Typ, Farbe nach Typ)
- relation_svg: Beziehungskarte mit echten Verknuepfungen (anklickbar)
- timeline_svg: Folgen-Zeitleiste, wenn mindestens zwei Folgen mit Datum vorhanden sind
Alle Inhalte stammen aus vorhandenen Daten, es wird nichts dazuerfunden."""
import hashlib
from html import escape as esc

HUE = {"product": 210, "platform": 265, "concept": 150, "org": 30, "person": 330, "cert": 45, "event": 0, "media": 185, "category": 100}
ICON = {"product": "◆", "platform": "▣", "concept": "✦", "org": "▲", "person": "●", "cert": "★", "event": "◉", "media": "▶", "category": "■"}


def _clip(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _lines(s, n=26, k=2):
    words, out, cur = (s or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    out.append(cur)
    out = [x for x in out if x][:k]
    if len(" ".join(words)) > sum(len(x) for x in out) + len(out):
        out[-1] = _clip(out[-1], n - 1) + "…"
    return out


def hero_svg(e, type_label, alt):
    h = HUE.get(e["type"], 210); h2 = (h + 40 + int(hashlib.md5(e["id"].encode()).hexdigest()[:2], 16) % 40) % 360
    ls = _lines(e["name"], 24, 2)
    txt = "".join(f'<text x="64" y="{150 + i * 64}" font-size="54" font-weight="700" fill="#fff">{esc(l)}</text>' for i, l in enumerate(ls))
    return (f'<figure class="en-fig"><svg role="img" aria-label="{esc(alt)}" viewBox="0 0 1200 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">'
            f'<defs><linearGradient id="g{e["id"][:8]}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl({h},55%,32%)"/><stop offset="1" stop-color="hsl({h2},60%,18%)"/></linearGradient></defs>'
            f'<rect width="1200" height="320" fill="url(#g{e["id"][:8]})"/><circle cx="1040" cy="150" r="120" fill="#fff" fill-opacity=".08"/><circle cx="1110" cy="250" r="70" fill="#fff" fill-opacity=".06"/>'
            f'<text x="64" y="76" font-size="26" fill="#fff" fill-opacity=".85" letter-spacing="3">{ICON.get(e["type"], "◆")} {esc(type_label.upper())}</text>{txt}'
            f'<text x="64" y="296" font-size="22" fill="#fff" fill-opacity=".7">M365.FM</text></svg><figcaption class="mut">{esc(alt)}</figcaption></figure>')


def relation_svg(e, items, alt):
    """items: [(label, url, name)] bis 8 Stueck rund um die Entitaet."""
    items = items[:8]
    if len(items) < 2:
        return ""
    import math
    h = HUE.get(e["type"], 210); cx, cy, R = 600, 200, 150
    parts = [f'<svg role="img" aria-label="{esc(alt)}" viewBox="0 0 1200 400" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">']
    pos = []
    for i, it in enumerate(items):
        a = -math.pi / 2 + 2 * math.pi * i / len(items)
        pos.append((cx + 380 * math.cos(a), cy + R * 1.05 * math.sin(a)))
    for x, y in pos:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="currentColor" stroke-opacity=".3" stroke-width="2"/>')
    parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="120" ry="46" fill="hsl({h},55%,32%)"/>')
    for i, l in enumerate(_lines(e["name"], 18, 2)):
        parts.append(f'<text x="{cx}" y="{cy + 5 + (i - (len(_lines(e["name"], 18, 2)) - 1) / 2) * 20:.0f}" text-anchor="middle" font-size="18" font-weight="700" fill="#fff">{esc(l)}</text>')
    for (x, y), (lab, url, name) in zip(pos, items):
        parts.append(f'<a href="{esc(url)}"><ellipse cx="{x:.0f}" cy="{y:.0f}" rx="105" ry="36" fill="Canvas" stroke="hsl({h},55%,45%)" stroke-width="2"/>'
                     f'<text x="{x:.0f}" y="{y - 4:.0f}" text-anchor="middle" font-size="15" fill="CanvasText">{esc(_clip(name, 20))}</text>'
                     f'<text x="{x:.0f}" y="{y + 15:.0f}" text-anchor="middle" font-size="11" fill="CanvasText" fill-opacity=".65">{esc(_clip(lab, 22))}</text></a>')
    parts.append("</svg>")
    return f'<figure class="en-fig">{"".join(parts)}<figcaption class="mut">{esc(alt)}</figcaption></figure>'


def timeline_svg(eps, alt):
    """eps: [(datum 'YYYY-MM-DD', titel, url)] -> Zeitleiste."""
    pts = sorted((d, t, u) for d, t, u in eps if d and len(d) >= 7)
    if len(pts) < 2:
        return ""
    y0, y1 = int(pts[0][0][:4]) + (int(pts[0][0][5:7]) - 1) / 12, int(pts[-1][0][:4]) + (int(pts[-1][0][5:7]) - 1) / 12
    span = max(y1 - y0, 0.08)
    out = [f'<svg role="img" aria-label="{esc(alt)}" viewBox="0 0 1200 150" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif"><line x1="40" y1="75" x2="1160" y2="75" stroke="currentColor" stroke-opacity=".35" stroke-width="3"/>']
    for d, t, u in pts:
        v = int(d[:4]) + (int(d[5:7]) - 1) / 12
        x = 40 + 1120 * (v - y0) / span
        out.append(f'<a href="{esc(u)}"><title>{esc(d)} – {esc(t)}</title><circle cx="{x:.0f}" cy="75" r="11" fill="hsl(210,60%,45%)"/></a>')
    out.append(f'<text x="40" y="125" font-size="16" fill="CanvasText">{esc(pts[0][0][:7])}</text><text x="1160" y="125" font-size="16" text-anchor="end" fill="CanvasText">{esc(pts[-1][0][:7])}</text></svg>')
    return f'<figure class="en-fig">{"".join(out)}<figcaption class="mut">{esc(alt)}</figcaption></figure>'


CSS = ".en-fig{margin:1.2em 0}.en-fig svg{width:100%;height:auto;display:block;border-radius:.5em}.en-fig figcaption{font-size:.85em;margin-top:.3em}"
