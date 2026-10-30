#!/usr/bin/env python3
"""Speaker aller M365Con-Programme zusammenfuehren: Schreibvarianten (Koellner/Köllner, Chris/Christopher ...) und Auftritte in mehreren Events werden zu EINER Person;
daraus entstehen Personen-Entitaeten mit Sessions (data/speaker_entities.json) und die Zuordnung Name -> Entitaet/Profil (data/speakers.json, vom Worker gelesen).
Eigene Eingriffe in data/speaker_manual.json:
  {"merge": [["Name A", "Name B"]], "never": [["Name A", "Name B"]], "links": {"mirko peters": {"entity": "mirko-peters", "handle": "mirko-peters"}}, "fix": {"name": {"company": "...", "title": "..."}}}
Aufruf: python tools/build_speakers.py   (deterministisch, ohne Netz)"""
import json, re, unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
# Programme (alt -> neu); Handle und Titel wie die Events in der Plattform
PROGRAMS = [("m365con_program_2026.json", "m365con-2026", "M365Con 2026"), ("m365con_program_dach.json", "m365con-dach-2026", "M365Con DACH 2026"), ("m365con_program.json", "m365con-2027", "M365Con 2027")]
TITLES = r"\b(dr|prof|mvp|mct|ing|dipl|mba|msc|bsc|phd|mag)\b\.?"
CORP = {"gmbh", "ag", "inc", "ltd", "llc", "co", "kg", "se", "sa", "bv", "ab", "oy", "spain", "europe", "germany", "deutschland", "uk", "us", "usa", "group", "the", "und", "and", "company", "corp", "corporation", "limited"}


def ascii_(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


def norm(s):
    s = re.sub(TITLES, " ", ascii_(s).lower())
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


def company_key(c):
    return " ".join(t for t in norm(c).split() if t not in CORP)


def related_company(a, b):
    a, b = company_key(a), company_key(b)
    return bool(a and b and (a == b or a in b or b in a))


def tok_ok(a, b):
    return a == b or a.startswith(b) or b.startswith(a) or SequenceMatcher(None, a, b).ratio() >= 0.85


def same_person(x, y, never):
    nx, ny = norm(x["name"]), norm(y["name"])
    if (nx, ny) in never or (ny, nx) in never:
        return False
    if nx == ny:
        return True
    ta, tb = nx.split(), ny.split()
    if len(ta) < 2 or len(tb) < 2 or not related_company(x.get("company"), y.get("company")):
        return False   # ohne gleiche Firma wird nicht geraten (siehe 'review')
    first_ok, last_ok = tok_ok(ta[0], tb[0]), tok_ok(ta[-1], tb[-1])
    subset = set(ta) <= set(tb) or set(tb) <= set(ta)
    return (first_ok and last_ok) or (subset and (first_ok or last_ok))


def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm(name))).strip("-")[:48] or "speaker"


def main():
    manual = json.loads((D / "speaker_manual.json").read_text("utf-8")) if (D / "speaker_manual.json").exists() else {}
    never = {(norm(a), norm(b)) for a, b in manual.get("never", [])}
    base = {e["id"]: e for e in json.loads((D / "entities.json").read_text("utf-8"))}
    recs, sessions_of = [], {}   # recs: ein Eintrag je (Programm, Speaker-ID)
    for fn, handle, etitle in PROGRAMS:
        f = D / fn
        if not f.exists():
            continue
        prog = json.loads(f.read_text("utf-8"))
        for sid, sp in (prog.get("speakers") or {}).items():
            recs.append({"name": sp.get("name", "").strip(), "company": sp.get("company", ""), "title": sp.get("title", ""), "event": handle, "etitle": etitle, "sid": str(sid)})
        for se in prog.get("sessions", []):
            for sid in se.get("speaker_ids") or []:
                sessions_of.setdefault((handle, str(sid)), []).append({"event": handle, "id": se["id"], "title": se["title"], "start": se.get("start", ""), "category": se.get("category", ""), "topics": se.get("topics", [])})
    recs = [r for r in recs if r["name"]]
    # Union-Find ueber alle Eintraege
    parent = list(range(len(recs)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def union(i, j):
        parent[find(i)] = find(j)
    by_name = {}
    for i, r in enumerate(recs):
        by_name.setdefault(norm(r["name"]), []).append(i)
    for idx in by_name.values():
        for i in idx[1:]:
            union(idx[0], i)
    reps = [v[0] for v in by_name.values()]
    review = []
    for a in range(len(reps)):
        for b in range(a + 1, len(reps)):
            x, y = recs[reps[a]], recs[reps[b]]
            if same_person(x, y, never):
                union(reps[a], reps[b])
            elif SequenceMatcher(None, norm(x["name"]), norm(y["name"])).ratio() >= 0.88 and (norm(x["name"]), norm(y["name"])) not in never:
                review.append([x["name"], x["company"], y["name"], y["company"]])
    for a, b in manual.get("merge", []):
        ia, ib = by_name.get(norm(a)), by_name.get(norm(b))
        if ia and ib:
            union(ia[0], ib[0])
    groups = {}
    for i in range(len(recs)):
        groups.setdefault(find(i), []).append(i)
    links = {norm(k): v for k, v in (manual.get("links") or {}).items()}
    fixes = {norm(k): v for k, v in (manual.get("fix") or {}).items()}
    used_ids, speakers, merged = set(base), [], []
    order = {h: n for n, (_, h, _) in enumerate(PROGRAMS)}
    for idx in sorted(groups.values(), key=lambda g: norm(recs[g[0]]["name"])):
        members = sorted((recs[i] for i in idx), key=lambda r: order[r["event"]])
        names = {}
        for r in members:
            names[r["name"]] = names.get(r["name"], 0) + 1
        canon = max(names, key=lambda n: (bool(re.search(r"[^\x00-\x7f]", n)), len(n), names[n]))
        aliases = sorted({r["name"] for r in members} - {canon})
        latest = members[-1]
        company, title = latest["company"], latest["title"]
        fx = fixes.get(norm(canon)) or {}
        company, title = fx.get("company", company), fx.get("title", title)
        link = links.get(norm(canon)) or next((links[norm(n)] for n in aliases if norm(n) in links), {})
        eid = link.get("entity") or slug(canon)
        if not link.get("entity"):
            while eid in used_ids:
                eid += "-speaker"
        used_ids.add(eid)
        ses, seen = [], set()
        for r in members:
            for s in sessions_of.get((r["event"], r["sid"]), []):
                if (s["event"], s["id"]) not in seen:
                    seen.add((s["event"], s["id"])); ses.append(s)
        ses.sort(key=lambda s: s["start"])
        events = []
        for r in members:
            if r["event"] not in [e["handle"] for e in events]:
                events.append({"handle": r["event"], "title": r["etitle"]})
        topics = {}
        for s in ses:
            for t in s["topics"]:
                topics[t] = topics.get(t, 0) + 1
        top = [t for t, _ in sorted(topics.items(), key=lambda kv: (-kv[1], kv[0])) if t in base][:6]
        sp = {"id": eid, "name": canon, "aliases": aliases, "company": company, "title": title, "events": events, "sessions": ses, "topics": top,
              **({"handle": link["handle"]} if link.get("handle") else {}), "existing": eid in base}
        speakers.append(sp)
        if len(idx) > 1 and (aliases or len({r["event"] for r in members}) > 1):
            merged.append({"name": canon, "aliases": aliases, "events": [e["handle"] for e in events]})
    # Personen-Entitaeten (bestehende, z. B. mirko-peters, bleiben unveraendert)
    ents = []
    for sp in speakers:
        if sp["existing"]:
            continue
        ev_en = " and ".join(e["title"] for e in sp["events"])
        role_en = (sp["title"] + (" at " if sp["title"] and sp["company"] else "") + sp["company"]).strip() if (sp["title"] or sp["company"]) else ""
        role_de = (sp["title"] + (" bei " if sp["title"] and sp["company"] else "") + sp["company"]).strip() if (sp["title"] or sp["company"]) else ""
        n = len(sp["sessions"])
        ents.append({"id": sp["id"], "type": "person", "name": sp["name"], "aliases": sp["aliases"],
                     "desc": {"en": f"{sp['name']} is a speaker at {ev_en}" + (f" ({role_en})" if role_en else "") + f" with {n} session{'s' if n != 1 else ''}.",
                              "de": f"{sp['name']} ist Speaker bei {ev_en.replace(' and ', ' und ')}" + (f" ({role_de})" if role_de else "") + f" mit {n} Session{'s' if n != 1 else ''}."},
                     "web": "", "same_as": [], "job": sp["title"], "company": sp["company"], "rel": [["related_to", t] for t in sp["topics"]], "speaker": True})
    (D / "speaker_entities.json").write_text(json.dumps(ents, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"version": 1, "speakers": [{k: v for k, v in sp.items() if k != "existing"} for sp in speakers]}
    (D / "speakers.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (D / "speaker_report.json").write_text(json.dumps({"entries": len(recs), "persons": len(speakers), "merged": merged, "review": review}, ensure_ascii=False, indent=1), encoding="utf-8")
    multi = sum(1 for sp in speakers if len(sp["events"]) > 1)
    print(f"{len(recs)} Eintraege -> {len(speakers)} Personen ({multi} in mehreren Events), {len(ents)} neue Entitaeten, {len(merged)} zusammengefuehrt, {len(review)} zur Pruefung")


if __name__ == "__main__":
    main()
