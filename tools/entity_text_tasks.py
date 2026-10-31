"""Aufgabenpakete fuer die Entitaeten-Texte: je Entitaet (ohne Personen) die belegten Fakten (Kurzbeschreibung, Verknuepfungen, Links)
und die Folgen der Show, in denen sie vorkommt. Schreibt data/entity_tasks/part-N.json (N = 1..PARTS).
Aufruf: python tools/entity_text_tasks.py [--parts 8]"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import site_podpage as P
import site_notes as SNT

D = ROOT / "data"
parts = int(sys.argv[sys.argv.index("--parts") + 1]) if "--parts" in sys.argv else 8
ents = json.loads((D / "entities.json").read_text("utf-8"))
by = {e["id"]: e for e in ents}
eps = [e for e in P.load("episodes") if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True")]
eps.sort(key=lambda e: e["create_time"], reverse=True)
hay = [(e, (e["name"] + " " + P.plain(e.get("summary")) + " " + P.plain(e.get("show_notes")))) for e in eps]


def names(e):
    out = {e["name"]} | set(e.get("aliases") or [])
    out |= {re.sub(r"^Microsoft\s+", "", n) for n in out}
    return {n for n in out if len(n) >= 4}


def episodes_for(e):
    rx = [re.compile(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", re.I) for n in names(e)]
    if not rx:
        return []
    hits = []
    for ep, text in hay:
        in_title = any(r.search(ep["name"]) for r in rx)
        n = sum(len(r.findall(text)) for r in rx)
        if n:
            hits.append((not in_title, -min(n, 5), ep))
    hits.sort(key=lambda h: (h[0], h[1]))
    out = []
    for _, _, ep in hits[:6]:
        out.append({"title": ep["name"], "date": (ep["create_time"] or "")[:10], "url": f"https://www.m365.fm/show/episodes/{ep['slug']}/", "summary": P.plain(ep.get("summary") or ep.get("show_notes"))[:420]})
    return out


tasks = []
for e in ents:
    if e["type"] in ("person",) or e.get("long", {}).get("en"):
        continue
    rel = []
    for p, to in e.get("rel", []):
        if to in by:
            rel.append({"relation": p, "name": by[to]["name"], "id": to})
    tasks.append({"id": e["id"], "type": e["type"], "name": e["name"], "aliases": e.get("aliases") or [], "short": {"en": e["desc"].get("en", ""), "de": e["desc"].get("de", "")},
                  "web": e.get("web", ""), "docs": e.get("docs", ""), "wikipedia": e.get("wikipedia", ""), "version": e.get("version", ""), "license": e.get("license", ""),
                  "exam": e.get("exam", ""), "relations": rel[:14], "episodes": episodes_for(e)})
out = D / "entity_tasks"; out.mkdir(exist_ok=True)
for f in out.glob("part-*.json"): f.unlink()
n = len(tasks); per = -(-n // parts)
for i in range(parts):
    chunk = tasks[i * per:(i + 1) * per]
    (out / f"part-{i + 1}.json").write_text(json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
print(n, "Entitaeten in", parts, "Paketen;", sum(1 for t in tasks if t["episodes"]), "mit Folgen,", sum(1 for t in tasks if not t["episodes"]), "ohne Folgen")
