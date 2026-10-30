"""Podcast-Gaeste mit Entitaeten abgleichen: Doubletten unter den Gaesten, Treffer bei Basis-Entitaeten
(Personen/Organisationen), bei Event-Speakern (data/speaker_entities.json, falls vorhanden) und Firmen aus dem
Titel ("CTO at Contoso"). Schreibt data/guest_match_report.json und gibt eine Kurzfassung aus.
Treffer-Stufen: sicher (gleicher Name oder gleiche Profil-URL) / moeglich (aehnlicher Name, bitte pruefen)."""
import difflib, json, re, sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"


def jl(n):
    f = D / n
    return json.loads(f.read_text("utf-8")) if f.exists() else []


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\b(dr|prof|mvp|rd|phd|msc|mba|jr|sr)\b\.?", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def urls(e):
    out = set()
    for u in (e.get("same_as") or []) + [e.get("web") or ""]:
        u = re.sub(r"^https?://(www\.)?", "", (u or "").lower()).rstrip("/").split("?")[0]
        if u and "/" in u:
            out.add(u)
    return out


def company(title):
    m = re.search(r"\b(?:at|@|bei)\s+([A-Z][\w&.\- ]{2,40}?)(?:[,;|(]|$)", title or "")
    return m.group(1).strip() if m else ""


def compare(a, pool, label):
    res = []
    na = norm(a["name"])
    for b in pool:
        if b is a or b.get("id") == a.get("id"):
            continue
        nb = norm(b.get("name"))
        names = {nb} | {norm(x) for x in b.get("aliases") or []}
        shared = urls(a) & urls(b)
        if na in names or shared:
            res.append({"with": b["id"], "name": b.get("name"), "level": "sicher", "why": "gleiche Profil-URL" if shared and na not in names else "gleicher Name", "source": label})
        else:
            r = max(difflib.SequenceMatcher(None, na, n).ratio() for n in names if n) if any(names) else 0
            ta, tb = set(na.split()), set(nb.split())
            if r >= .88 or (len(ta) > 1 and ta == tb):
                res.append({"with": b["id"], "name": b.get("name"), "level": "moeglich", "why": f"Name aehnlich ({r:.2f})", "source": label})
    return res


def main():
    guests = [g for g in jl("guest_entities.json")]
    base = [e for e in jl("entities.json") if e["type"] in ("person", "org", "media", "event")]
    speakers = jl("speaker_entities.json")
    orgs = {norm(e["name"]): e for e in base if e["type"] == "org"} | {norm(a): e for e in base if e["type"] == "org" for a in e.get("aliases") or []}
    rep = {"guests": len(guests), "speaker_entities": len(speakers), "dupes": [], "base": [], "speakers": [], "companies": []}
    seen = set()
    for g in guests:
        for m in compare(g, guests, "gast"):
            k = tuple(sorted((g["id"], m["with"])))
            if k not in seen:
                seen.add(k); rep["dupes"].append({"gast": g["id"], "name": g["name"], **m})
        for m in compare(g, base, "entitaet"):
            rep["base"].append({"gast": g["id"], "name": g["name"], **m})
        for m in compare(g, speakers, "speaker"):
            rep["speakers"].append({"gast": g["id"], "name": g["name"], **m})
        c = company(g.get("job"))
        if c:
            o = orgs.get(norm(c))
            rep["companies"].append({"gast": g["id"], "name": g["name"], "firma": c, "entitaet": o["id"] if o else None})
    (D / "guest_match_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in ("dupes", "base", "speakers"):
        print(f"{k}: {len(rep[k])} Treffer, davon sicher {sum(1 for x in rep[k] if x['level'] == 'sicher')}")
        for x in rep[k][:12]:
            print("  ", x["level"], x["gast"], "<->", x["with"], "|", x["why"])
    print("Firmen im Titel:", len(rep["companies"]), "davon als Organisation vorhanden:", sum(1 for x in rep["companies"] if x["entitaet"]))


main()
