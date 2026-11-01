#!/usr/bin/env python3
"""T26: Entitaetsvorschlaege aus imports/entities/<slug>.json mit status "approved" nach data/entities.json uebernehmen.

Vorschlaege schreiben die Extraktions-Agenten (status "review"); die QA setzt "rejected", Mirko bzw. die Redaktion "approved".
Je Vorschlag: slug, name, type (person|concept|product|certification|event|organization|platform|category), lang,
short_description (Pflicht, >= 20 Zeichen), aliases[], sameAs[] (Microsoft Learn -> docs, Wikipedia -> wikipedia, Wikidata -> wikidata,
sonst same_as), evidence[]. Quotes (imports/entities/quotes/, type "quote") sind Objekte an Personen-Entitaeten: tools/import_quotes.py.
Idempotent: vorhandene IDs werden nicht ueberschrieben (nur fehlende Aliase, sameAs und Beschreibungen in weiteren Sprachen ergaenzt);
die Datei bekommt status "imported" und imported_at. Nichts wird geloescht. Aufruf: python tools/import_entities.py [--dry-run]"""
import json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMP, ENT = ROOT / "imports" / "entities", ROOT / "data" / "entities.json"
TYPES = {"person": "person", "concept": "concept", "product": "product", "certification": "cert", "cert": "cert", "event": "event", "organization": "org", "org": "org", "platform": "platform", "category": "category", "media": "media"}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
LANG = re.compile(r"^[a-z]{2}$")


def classify(url):
    u = (url or "").strip()
    if not u.startswith("http"): return None, u
    if re.search(r"://(?:[\w-]+\.)*learn\.microsoft\.com/", u): return "docs", u
    if re.search(r"://(?:[\w-]+\.)*wikipedia\.org/", u): return "wikipedia", u
    m = re.search(r"wikidata\.org/(?:wiki|entity)/(Q\d+)", u)
    if m: return "wikidata", m.group(1)
    return "same_as", u


def convert(p):
    """Vorschlagsdatei -> (Eintrag fuer entities.json, Fehler)."""
    d = json.loads(p.read_text("utf-8"))
    if (d.get("type") or "") == "quote": return None, "quote (eigene Art, nicht importiert)"
    sid = str(d.get("slug") or d.get("id") or p.stem).strip().lower()
    name = str(d.get("name") or "").strip()
    t = TYPES.get(str(d.get("type") or "").strip().lower())
    lang = str(d.get("lang") or "en").strip().lower()[:2]
    desc = str(d.get("short_description") or d.get("desc") or d.get("description") or "").strip()
    errs = []
    if not SLUG.match(sid): errs.append(f"slug ungueltig: {sid!r}")
    if not name: errs.append("name fehlt")
    if not t: errs.append(f"type unbekannt: {d.get('type')!r}")
    if not LANG.match(lang): errs.append(f"lang ungueltig: {lang!r}")
    if len(desc) < 20: errs.append("short_description fehlt oder kuerzer als 20 Zeichen")
    if re.search(r"https?://", desc): errs.append("short_description enthaelt einen Link")
    if errs: return None, "; ".join(errs)
    e = {"id": sid, "type": t, "name": name, "aliases": [], "desc": {"en": "", "de": ""}, "web": "", "wikidata": "", "wikipedia": "", "docs": "", "rel": []}
    e["desc"][lang] = desc
    for a in (d.get("aliases") or []):
        a = str(a).strip()
        if a and a != name and a not in e["aliases"]: e["aliases"].append(a)
    same = []
    srcs = d.get("sameAs") or d.get("same_as") or d.get("sameas") or []
    if isinstance(srcs, str): srcs = [srcs]
    for s in srcs:
        u = s.get("url") if isinstance(s, dict) else s
        k, v = classify(str(u or ""))
        if not k: continue
        if k == "same_as": same.append(v)
        elif not e[k]: e[k] = v
    if same: e["same_as"] = same[:6]
    if d.get("web") and str(d["web"]).startswith("http"): e["web"] = str(d["web"])
    if d.get("rel"): e["rel"] = [list(x) for x in d["rel"] if isinstance(x, (list, tuple)) and len(x) == 2]
    e["source"] = {"import": p.name, "lang": lang, "approved_by": d.get("approved_by") or "", "episodes": sorted({str(x.get("episode_id")) for x in (d.get("evidence") or []) if isinstance(x, dict) and x.get("episode_id")})[:20]}
    return e, ""


def merge(old, new):
    """Vorhandenen Eintrag nur ergaenzen (nichts ueberschreiben)."""
    ch = False
    for a in new.get("aliases") or []:
        if a not in (old.get("aliases") or []) and a != old.get("name"): old.setdefault("aliases", []).append(a); ch = True
    for k in ("wikidata", "wikipedia", "docs", "web"):
        if new.get(k) and not old.get(k): old[k] = new[k]; ch = True
    for l, t in (new.get("desc") or {}).items():
        if t and not (old.get("desc") or {}).get(l): old.setdefault("desc", {})[l] = t; ch = True
    for u in new.get("same_as") or []:
        if u not in (old.get("same_as") or []): old.setdefault("same_as", []).append(u); ch = True
    return ch


def main(dry=False):
    if not IMP.exists():
        print("Kein imports/entities/ - nichts zu tun"); return 0
    ents = json.loads(ENT.read_text("utf-8")); by = {e["id"]: e for e in ents}
    added, merged, skipped, bad = [], [], [], []
    for p in sorted(IMP.glob("*.json")):
        try:
            d = json.loads(p.read_text("utf-8"))
        except Exception as ex:
            bad.append((p.name, f"kein JSON: {ex}")); continue
        if str(d.get("status") or "").lower() != "approved":
            continue
        e, err = convert(p)
        if err: bad.append((p.name, err)); continue
        if e["id"] in by:
            if merge(by[e["id"]], e): merged.append(e["id"])
            else: skipped.append(e["id"])
        else:
            ents.append(e); by[e["id"]] = e; added.append(e["id"])
        if not dry:
            d["status"] = "imported"; d["imported_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); d["entity_id"] = e["id"]
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", "utf-8")
    if not dry and (added or merged):
        ENT.write_text(json.dumps(ents, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"neu: {len(added)} {added[:20]}\nergaenzt: {len(merged)} {merged[:20]}\nschon vorhanden: {len(skipped)}\nabgelehnt: {len(bad)}")
    for n, err in bad: print(f"  {n}: {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
