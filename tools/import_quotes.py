#!/usr/bin/env python3
"""Quotes als Objekte an Personen-Entitaeten (Mirko, 1.11.): imports/entities/quotes/<episode_id>-<n>.json mit status "approved"
werden nach data/quotes.json uebernommen - aber nur, wenn der Sprecher eine Personen-Entitaet ist (speaker_slug oder Name/Alias in
data/entities.json, data/guest_entities.json, data/speaker_entities.json, Typ person). Ein Quote ohne Personen-Entitaet bleibt
liegen und bekommt "blocked" mit dem Grund (erst die Person als Entitaet anlegen/freigeben, dann erneut).
Pflicht: text (15-80 Woerter), lang, episode_id; optional time_s, episode_slug, entities[] (Themen), why. Idempotent (id = Dateiname),
nichts wird geloescht; die Datei bekommt status "imported". Aufruf: python tools/import_quotes.py [--dry-run]"""
import json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QD, OUT = ROOT / "imports" / "entities" / "quotes", ROOT / "data" / "quotes.json"
REG = [ROOT / "data" / f for f in ("entities.json", "guest_entities.json", "speaker_entities.json")]
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\w\s-]", "", str(s or "").lower())).strip()


def persons():
    """id -> Entitaet (nur Personen); name/alias -> id."""
    ids, names = {}, {}
    for f in REG:
        if not f.exists(): continue
        for e in json.loads(f.read_text("utf-8")):
            if e.get("type") != "person" or e["id"] in ids: continue
            ids[e["id"]] = e
            for n in [e.get("name")] + list(e.get("aliases") or []):
                k = norm(n)
                if k: names[k] = e["id"] if k not in names else names[k]
    return ids, names


def resolve(d, ids, names):
    sid = str(d.get("speaker_slug") or "").strip().lower()
    if sid in ids: return sid
    if sid.endswith("-guest") and sid[:-6] in ids: return sid[:-6]
    k = norm(d.get("speaker"))
    if k in ("mirko", "mirko peters") and "mirko-peters" in ids: return "mirko-peters"
    return names.get(k)


def main(dry=False):
    if not QD.exists():
        print("Kein imports/entities/quotes/ - nichts zu tun"); return 0
    ids, names = persons()
    have = json.loads(OUT.read_text("utf-8")) if OUT.exists() else []
    by = {q["id"]: q for q in have}
    added, blocked, bad = [], [], []
    for p in sorted(QD.glob("*.json")):
        try:
            d = json.loads(p.read_text("utf-8"))
        except Exception as ex:
            bad.append((p.name, f"kein JSON: {ex}")); continue
        if str(d.get("status") or "").lower() != "approved": continue
        qid = p.stem
        text = re.sub(r"\s+", " ", str(d.get("text") or "")).strip()
        n = len(text.split())
        err = []
        if not 15 <= n <= 80: err.append(f"{n} Woerter (15-80)")
        if not re.fullmatch(r"[a-z]{2}", str(d.get("lang") or "")): err.append("lang fehlt")
        if not str(d.get("episode_id") or "").isdigit(): err.append("episode_id fehlt")
        if re.search(r"https?://", text): err.append("Link im Text")
        if err:
            bad.append((p.name, "; ".join(err))); continue
        pid = resolve(d, ids, names)
        if not pid:
            blocked.append(p.name)
            if not dry:
                d["blocked"] = "Sprecher ist keine Personen-Entitaet (" + str(d.get("speaker") or d.get("speaker_slug") or "?") + "): erst die Person als Entitaet anlegen und freigeben"
                p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", "utf-8")
            continue
        q = {"id": qid, "person": pid, "text": text, "lang": d["lang"], "episode_id": str(d["episode_id"]), "episode_slug": d.get("episode_slug") or "",
             "time_s": int(d["time_s"]) if str(d.get("time_s") or "").replace(".", "", 1).isdigit() else None,
             "about": [x for x in (d.get("entities") or []) if isinstance(x, str)][:8], "why": str(d.get("why") or "")[:200],
             "source_video_id": d.get("source_video_id") or "", "imported": time.strftime("%Y-%m-%d", time.gmtime())}
        if qid not in by: added.append(qid)
        by[qid] = {**by.get(qid, {}), **q}
        if not dry:
            d["status"] = "imported"; d["imported_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); d["person"] = pid; d.pop("blocked", None)
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", "utf-8")
    if not dry and (added or by.keys() != {q["id"] for q in have}):
        OUT.write_text(json.dumps(sorted(by.values(), key=lambda q: (q["person"], q["episode_id"], q["id"])), ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"Quotes neu: {len(added)}, gesamt: {len(by)}, ohne Personen-Entitaet: {len(blocked)}, abgelehnt: {len(bad)}")
    for n, e in bad: print("  ", n, e)
    for n in blocked[:20]: print("   ohne Person:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
