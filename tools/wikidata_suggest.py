"""Wikidata-IDs (und englische Wikipedia-Links) fuer Entitaeten vorschlagen.
Aufruf:  python tools/wikidata_suggest.py            -> schreibt data/wikidata_suggestions.json (nur Vorschlaege)
         python tools/wikidata_suggest.py --apply    -> traegt nur sichere Treffer in data/entities.json ein
Sicher ("hoch") ist ein Treffer nur, wenn Name oder Alias genau dem Wikidata-Titel entspricht UND die Beschreibung auf Microsoft
oder Software/Dienst/Zertifizierung hindeutet. Alles andere bleibt Vorschlag zur Pruefung: eine falsche ID waere schaedlicher als keine."""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
API = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "m365fm-entity-bot/1.0 (https://www.m365.fm; system@m365.fm)"}
TYPES = {"product", "platform", "org", "media", "event", "cert"}   # Konzepte sind zu mehrdeutig fuer automatische Treffer
SOFT = re.compile(r"software|service|cloud|application|app\b|platform|programming|certification|credential|exam|company|conference|podcast|operating system|suite|tool", re.I)


def get(params):
    q = urllib.parse.urlencode({**params, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers=UA), timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").casefold()).strip()


def names_of(e):
    base = [e["name"]] + list(e.get("aliases") or [])
    out = {norm(n) for n in base}
    out |= {norm(re.sub(r"^microsoft\s+", "", n, flags=re.I)) for n in base}   # "Microsoft Teams" == "Teams"
    out |= {norm("Microsoft " + n) for n in base}
    return {n for n in out if n}


def rate(e, hit):
    """Eine Stufe je Treffer: hoch | mittel | niedrig."""
    exact = norm(hit.get("label")) in names_of(e)
    desc = hit.get("description") or ""
    if exact and re.search(r"microsoft", desc, re.I):
        return "hoch"
    if exact and SOFT.search(desc):
        return "mittel"
    return "niedrig" if exact or SOFT.search(desc) else "keine"


def suggest(e, fetch=get):
    res = fetch({"action": "wbsearchentities", "search": e["name"], "language": "en", "type": "item", "limit": 6})
    cands = []
    for h in res.get("search", []):
        lv = rate(e, h)
        if lv != "keine":
            cands.append({"qid": h["id"], "label": h.get("label", ""), "description": h.get("description", ""), "level": lv})
    order = {"hoch": 0, "mittel": 1, "niedrig": 2}
    cands.sort(key=lambda c: order[c["level"]])
    return cands


def enwiki(qid, fetch=get):
    j = fetch({"action": "wbgetentities", "ids": qid, "props": "sitelinks", "sitefilter": "enwiki"})
    t = ((j.get("entities") or {}).get(qid, {}).get("sitelinks") or {}).get("enwiki", {}).get("title")
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")) if t else ""


def main(argv, fetch=get, sleep=time.sleep):
    apply = "--apply" in argv
    ents = json.loads((D / "entities.json").read_text("utf-8"))
    items, applied = [], 0
    for e in ents:
        if e["type"] not in TYPES or e.get("wikidata"):
            continue
        try:
            c = suggest(e, fetch)
        except Exception as x:
            print("Fehler", e["id"], str(x)[:80]); continue
        if c:
            items.append({"id": e["id"], "name": e["name"], "type": e["type"], "candidates": c[:3]})
            top = [x for x in c if x["level"] == "hoch"]
            if apply and len(top) == 1:   # genau ein sicherer Treffer
                e["wikidata"] = top[0]["qid"]; applied += 1
                if not e.get("wikipedia"):
                    wp = enwiki(top[0]["qid"], fetch)
                    if wp: e["wikipedia"] = wp
        sleep(0.2)
    (D / "wikidata_suggestions.json").write_text(json.dumps({"generated": time.strftime("%Y-%m-%d"), "count": len(items), "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    if apply and applied:
        (D / "entities.json").write_text(json.dumps(ents, ensure_ascii=False, indent=1), encoding="utf-8")
    sure = sum(1 for i in items if i["candidates"][0]["level"] == "hoch")
    print(f"{len(items)} Entitaeten mit Vorschlag, davon {sure} sicher; {applied} eingetragen")
    return items


if __name__ == "__main__":
    main(sys.argv[1:])
