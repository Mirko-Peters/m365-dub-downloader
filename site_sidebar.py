"""Sidebar fuer die Show-Seiten (/show/…): M365Con-Karte mit Countdown, Google-Quelle, Entitaeten-Chips (Wissensgraph), neueste Folgen, Hoeren/Folgen, Community."""
import json, re
from html import escape as esc
from pathlib import Path
D = Path(__file__).parent / "data"
TYPE_L = {"product": "Product", "concept": "Concept", "cert": "Certification", "platform": "Platform", "org": "Organization", "event": "Event", "person": "Person", "media": "Media", "category": "Topic"}
STOP = {"access", "project", "compliance", "governance", "automation", "prompt", "actions", "polling", "agent", "agents", "lists", "forms", "flow", "loop", "word", "bing", "stream", "sites", "pages", "tasks", "security", "identity", "copilot", "microsoft", "azure", "m365", "teams"}
TYPE_PRIO = {"product": 0, "person": 1, "cert": 2, "platform": 3, "concept": 4, "event": 5, "org": 6, "media": 7, "category": 9}
GSRC = "https://www.google.com/preferences/source?q=m365.fm"
CON = "https://m365con.net/?utm_source=m365.fm&utm_medium=sidebar&utm_campaign=attending2027"


class Index:
    def __init__(self):
        ents = json.loads((D / "entities.json").read_text("utf-8"))
        gp = D / "guest_entities.json"
        if gp.exists(): ents += json.loads(gp.read_text("utf-8"))
        self.by = {}; names = {}
        for e in ents:
            if e["type"] in ("category",) or e["id"] == "mirko-peters": continue
            for n in [e["name"]] + list(e.get("aliases") or []):
                n = (n or "").strip()
                if " " not in n and n.lower() in STOP and n.lower() != e["name"].lower(): continue
                if len(n) < (6 if e.get("guest") else 4) and n not in ("Teams", "Excel", "Word", "Azure", "Loop", "Viva", "Bing"): continue
                names.setdefault(n.lower(), e["id"])
            self.by[e["id"]] = e
        keys = sorted(names, key=len, reverse=True)
        self.names = names
        self.rx = re.compile(r"(?<![\w-])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w-])", re.I) if keys else None

    def match(self, text, k=8):
        if not self.rx: return []
        cnt = {}
        for m in self.rx.finditer(text):
            i = self.names.get(m.group(1).lower()); cnt[i] = cnt.get(i, 0) + 1
        ids = sorted(cnt, key=lambda i: (self.by[i]["name"].lower() in STOP, -min(cnt[i], 3), TYPE_PRIO.get(self.by[i]["type"], 8), -cnt[i]))
        return [self.by[i] for i in ids[:k]]


def render(ix, BASE, root, text, latest, shp, esc_=esc):
    chips = "".join(f'<li><a class="sb-chip t-{esc(e["type"])}" href="{BASE}/entity/{esc(e["id"])}/" title="{esc(TYPE_L.get(e["type"], ""))}"><i></i>{esc(e["name"])}</a></li>' for e in ix.match(text))
    ents = f'<section class="sb-card"><h2>Topics &amp; people on this page</h2><ul class="sb-chips">{chips}</ul><a class="sb-more" href="{BASE}/glossary/">Explore the knowledge graph →</a></section>' if chips else ""
    late = "".join(f'<li><a href="{root}episodes/{esc(e["slug"])}/">{esc(e["name"])}</a></li>' for e in latest[:5])
    listen = " ".join(f'<a href="{esc(shp[k])}" rel="noopener">{n}</a>' for k, n in (("apple_show", "Apple Podcasts"), ("spotify_show", "Spotify"), ("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart")) if shp.get(k))
    con = (f'<section class="sb-card sb-con"><a href="{CON}" rel="noopener" aria-label="M365Con International 2027 – I\'m attending"><img src="{BASE}/assets/attending-m365con.webp" alt="I\'m attending M365Con International 2027, January 11–22, 2027, free online event" width="675" height="563" loading="lazy"></a>'
           f'<div class="sb-count" data-m365con-countdown><span class="sb-meta">Free online event · Jan 11–22, 2027</span></div>'
           f'<a class="sb-btn" href="{CON}" rel="noopener">Save your free seat →</a></section>')
    goog = (f'<section class="sb-card sb-g"><a href="{GSRC}" rel="noopener" target="_blank"><img src="{BASE}/assets/gsource.webp" alt="Add M365.fm as a preferred source on Google" width="647" height="192" loading="lazy"></a>'
            f'<p>See M365.FM first in Google&nbsp;Top&nbsp;Stories.</p></section>')
    new = f'<section class="sb-card"><h2>Latest episodes</h2><ol class="sb-list">{late}</ol><a class="sb-more" href="{root}episodes/">All episodes →</a></section>' if late else ""
    foll = (f'<section class="sb-card"><h2>Listen &amp; follow</h2><p class="sb-links">{listen}</p><p class="sb-links"><a href="{root}listen/">All platforms</a> <a href="https://www.spreaker.com/show/6704921/episodes/feed" rel="noopener">RSS</a></p></section>') if listen else ""
    comm = (f'<section class="sb-card sb-comm"><h2>Join the community</h2><p>Free profile, expert directory, events and your own page in the knowledge graph.</p><a class="sb-btn sb-ghost" href="{BASE}/community/">Create your profile →</a></section>')
    return f'<aside class="sbar" aria-label="Sidebar"><div class="sbar-in">{con}{goog}{ents}{new}{foll}{comm}</div></aside>'
