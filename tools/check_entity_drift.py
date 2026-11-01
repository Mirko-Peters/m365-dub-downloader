"""T30: Weichen die Entitaeten in D1 (live, /api/entity/export) von der JSON-Basis im Repo ab?
Der Seitenbau ersetzt jeden JSON-Eintrag ganz durch die live-Fassung aus D1. Was nach der ersten Uebernahme nur in
der JSON geaendert wurde (Doku-Links, Wikidata, Namen), kommt so nicht auf die Seite. Bericht je Feld:
reports/entity-drift.md/.json (nur Entitaets-IDs und Feldnamen)."""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api-dub.m365.fm/api/entity/export"
OUT = ROOT / "reports" / "entity-drift"
FIELDS = ("name", "type", "docs", "wikidata", "wikipedia", "web", "same_as", "aliases", "rel", "image", "job", "desc.en", "desc.de")


def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True) if v not in (None, "", [], {}) else ""


def get(e, f):
    if "." in f:
        a, b = f.split("."); return (e.get(a) or {}).get(b) if isinstance(e.get(a), dict) else None
    return e.get(f)


def main():
    base = {}
    for f in ("entities.json", "guest_entities.json", "speaker_entities.json"):   # gleiche Reihenfolge wie site_learn.load_entities
        p = ROOT / "data" / f
        for e in (json.loads(p.read_text("utf-8")) if p.exists() else []):
            base.setdefault(e["id"], e) if f != "entities.json" else base.__setitem__(e["id"], e)
    with urllib.request.urlopen(urllib.request.Request(API, headers={"User-Agent": "m365fm-drift/1.0"}), timeout=120) as r:
        items = json.loads(r.read().decode("utf-8")).get("items", [])
    live = {it["id"]: it for it in items if it.get("id")}
    rep = {"generated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "json": len(base), "d1_live": len(live), "both": 0, "only_d1": sorted(set(live) - set(base))[:50],
           "only_json": len(set(base) - set(live)), "by_source": {}, "fields": {f: {"json_newer_or_diff": 0, "missing_in_d1": 0, "ids": []} for f in FIELDS}, "entities_with_drift": 0}
    for i, e in base.items():
        it = live.get(i)
        if not it: continue
        rep["both"] += 1; d = it.get("data") or {}; src = "import/auto" if not it.get("uid") else "person"
        drift = False
        for f in FIELDS:
            a, b = canon(get(e, f)), canon(get(d, f))
            if a and a != b:
                k = rep["fields"][f]; k["json_newer_or_diff"] += 1; k["missing_in_d1"] += 0 if b else 1; drift = True
                if len(k["ids"]) < 15: k["ids"].append(i)
        if drift:
            rep["entities_with_drift"] += 1; rep["by_source"][src] = rep["by_source"].get(src, 0) + 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix(".json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", "utf-8")
    L = [f"# Entitäten: JSON gegen D1 ({rep['generated']})", "", f"JSON-Basis {rep['json']} · D1 live {rep['d1_live']} · in beiden {rep['both']} · nur JSON {rep['only_json']} · nur D1 {len(live) - rep['both']}", "",
         f"**{rep['entities_with_drift']} Entitäten** weichen ab (letzte live-Fassung: {', '.join(f'{k} {v}' for k, v in rep['by_source'].items()) or '-'}).", "",
         "| Feld | JSON anders als D1 | davon in D1 leer | Beispiele |", "|---|---|---|---|"]
    L += [f"| {f} | {v['json_newer_or_diff']} | {v['missing_in_d1']} | {', '.join(v['ids'][:6])} |" for f, v in rep["fields"].items()]
    OUT.with_suffix(".md").write_text("\n".join(L) + "\n", "utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
