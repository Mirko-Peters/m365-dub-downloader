"""Themen-Zuordnung, Verlinkung und Verwandtschaft fuer Beitraege (Paket 8).
- score_topics: Entitaeten eines Textes mit Gewicht (Titel 4, Anfang 2, Rest 1; allgemeine Begriffe wie "Microsoft 365" nur, wenn sie im Titel stehen oder nichts Spezifischeres da ist).
- autolink_html: erste Nennung einer Entitaet im HTML eines Beitrags auf ihre Seite verlinken (nur Absaetze/Listen, nie Ueberschriften oder bestehende Links).
- related: verwandte Beitraege ueber gemeinsame Themen (Hauptthema zaehlt doppelt), dann nach Datum.
Ergebnisse der Zuordnung werden je Beitrag in data/cache/blog_topics.json gehalten (Hash von Titel und Textanfang)."""
import hashlib, html as _h, json, re
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "cache" / "blog_topics.json"
GENERIC = {"microsoft-365", "microsoft", "compliance", "automation", "governance", "security", "ai", "artificial-intelligence", "cloud", "data", "microsoft-tool", "copilot"}
_C = {}


def _load():
    global _C
    if not _C and CACHE.exists():
        try: _C = json.loads(CACHE.read_text("utf-8"))
        except Exception: _C = {}
    return _C


def save():
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True); CACHE.write_text(json.dumps(_C, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def score_topics(ix, title, text, k=8, key=None):
    """-> [eid, ...] nach Gewicht; key: Cache-Schluessel (z. B. Slug)."""
    h = hashlib.sha1((title + "\n" + text[:3000]).encode("utf-8")).hexdigest()[:12]
    if key:
        c = _load().get(key)
        if c and c.get("h") == h: return list(c["t"])
    if not ix.rx:
        return []
    sc = {}
    def add(s, w):
        for m in ix.rx.finditer(s):
            i = ix.names.get(m.group(1).lower())
            if i: sc[i] = sc.get(i, 0) + w
    add(title, 4); add(text[:600], 2); add(text[600:3000], 1)
    in_title = {ix.names.get(m.group(1).lower()) for m in ix.rx.finditer(title)}
    for i in list(sc):
        if i in GENERIC and i not in in_title: sc[i] *= 0.35   # allgemeine Begriffe nur mit Titeltreffer voll werten
    order = sorted(sc, key=lambda i: (-sc[i], i in GENERIC, i))
    top = [i for i in order if sc[i] >= 1.5][:k] or order[:min(k, 2)]
    spec = [i for i in top if i not in GENERIC and ix.by[i]["type"] not in ("category",)]
    if spec and top and top[0] in GENERIC: top = [spec[0]] + [i for i in top if i != spec[0]]   # Hauptthema moeglichst spezifisch
    if key:
        _load()[key] = {"h": h, "t": top}
    return top


_SKIP = re.compile(r"<(a|h1|h2|h3|h4|h5|h6|code|pre|script|style|figure|figcaption)\b[^>]*>.*?</\1>", re.S | re.I)


def autolink_html(html, ents, url_of, max_links=8, exclude=()):
    """Erste Nennung je Entitaet (Name/Alias, >= 4 Zeichen oder mehrteilig) ausserhalb von Ueberschriften/Links verlinken. -> (html, [(name, url)])"""
    names = []
    for e in ents.values():
        if e["id"] in exclude or e["id"] in GENERIC or e.get("type") in ("category", "person") or e.get("outdated"): continue
        for n in [e["name"]] + list(e.get("aliases") or []):
            n = (n or "").strip()
            if len(n) >= 4 and (len(n) >= 6 or " " in n or n in ("Teams", "Excel", "Azure", "Loop", "Viva")): names.append((n, e["id"]))
    if not names: return html, []
    names.sort(key=lambda x: -len(x[0]))
    rx = re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n, _ in names) + r")(?![\w-])")
    byname = {n.lower(): i for n, i in names}
    # geschuetzte Bereiche herausnehmen
    parts, pos, used, links = [], 0, set(), []
    for m in _SKIP.finditer(html):
        parts.append((html[pos:m.start()], True)); parts.append((m.group(0), False)); pos = m.end()
    parts.append((html[pos:], True))
    out = []
    for seg, editable in parts:
        if not editable or len(links) >= max_links:
            out.append(seg); continue
        # nur Text ausserhalb von Tags ersetzen
        toks = re.split(r"(<[^>]+>)", seg); res = []
        for t in toks:
            if t.startswith("<") or len(links) >= max_links: res.append(t); continue
            def rep(m):
                i = byname.get(m.group(1).lower())
                if not i or i in used or len(links) >= max_links: return m.group(0)
                used.add(i); u = url_of(i); links.append((m.group(1), u))
                return f'<a href="{u}" class="en-al">{m.group(1)}</a>'
            res.append(rx.sub(rep, t))
        out.append("".join(res))
    return "".join(out), links


def related(posts, p, k=6):
    """Verwandte Beitraege nach Themen-Ueberschneidung (Hauptthema doppelt), dann nach Datum; gleiche Sprache."""
    t = p.get("topics") or []
    if not t: return []
    w = {x: (2 if n == 0 else 1) for n, x in enumerate(t)}
    out = []
    for q in posts:
        if q is p or q.get("slug") == p.get("slug") and q.get("handle") == p.get("handle"): continue
        if q.get("lang") != p.get("lang"): continue
        s = sum(w.get(x, 0) * (2 if n == 0 else 1) for n, x in enumerate(q.get("topics") or []))
        if s: out.append((s, q.get("published") or 0, q))
    out.sort(key=lambda x: (-x[0], -x[1]))
    return [q for _, _, q in out[:k]]
