#!/usr/bin/env python3
"""Quotes als Objekte an Personen-Entitaeten (Mirko, 1.11.): keine eigenen Quote-Entitaeten. Quelle sind die Felder quotes[] der
Extraktionsdateien shownotes/entities/<episode_id>.json (Korrektur 07:25: Quotes werden in der Extraktion gesammelt). Uebernommen wird
eine Folge, sobald die QA sie in shownotes/QA.txt mit ok oder fixed fuehrt; aeltere Einzeldateien imports/entities/quotes/*.json mit
status "approved" werden ebenfalls gelesen. Jedes Zitat braucht einen Sprecher, der eine Personen-Entitaet ist (speaker_slug oder
Name/Alias in data/entities.json, data/guest_entities.json, data/speaker_entities.json); sonst wird es nicht uebernommen und in der
Ausgabe gemeldet. Pflicht: text (15-80 Woerter), lang. Ergebnis: data/quotes.json (id = <episode_id>-<n>), idempotent, nichts wird
geloescht. Aufruf: python tools/import_quotes.py [--dry-run]"""
import json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QD, OUT = ROOT / "imports" / "entities" / "quotes", ROOT / "data" / "quotes.json"
SE, QA = ROOT / "shownotes" / "entities", ROOT / "shownotes" / "QA.txt"
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


def qa_ok():
    """episode_ids, die die QA mit ok oder fixed gefuehrt hat (letzter Eintrag je Folge zaehlt)."""
    st = {}
    if QA.exists():
        for line in QA.read_text("utf-8").splitlines():
            f = [x.strip() for x in line.split(";")]
            if len(f) >= 2 and f[0].isdigit(): st[f[0]] = f[1].lower()
    return {k for k, v in st.items() if v in ("ok", "fixed")}


def candidates():
    """(id, quote-dict, episode-dict, quelle) aus den Extraktionsdateien (QA ok/fixed) und alten Einzeldateien (approved)."""
    ok = qa_ok()
    if SE.exists():
        for f in sorted(SE.glob("*.json")):
            if not f.stem.isdigit() or f.stem not in ok: continue
            try:
                ep = json.loads(f.read_text("utf-8"))
            except Exception:
                continue
            for n, q in enumerate(ep.get("quotes") or [], 1):
                if isinstance(q, dict): yield f"{f.stem}-{n}", q, ep, f.name
    if QD.exists():
        for p in sorted(QD.glob("*.json")):
            try:
                d = json.loads(p.read_text("utf-8"))
            except Exception:
                continue
            if str(d.get("status") or "").lower() == "approved": yield p.stem, d, d, p.name


def main(dry=False):
    ids, names = persons()
    have = json.loads(OUT.read_text("utf-8")) if OUT.exists() else []
    by = {q["id"]: q for q in have}
    added, blocked, bad = [], [], []
    for qid, d, ep, src in candidates():
        text = re.sub(r"\s+", " ", str(d.get("text") or "")).strip()
        n = len(text.split()); err = []
        lang = str(d.get("lang") or ep.get("lang") or "")
        eid = str(d.get("episode_id") or ep.get("episode_id") or qid.split("-")[0])
        if not 15 <= n <= 80: err.append(f"{n} Woerter (15-80)")
        if not re.fullmatch(r"[a-z]{2}", lang): err.append("lang fehlt")
        if not eid.isdigit(): err.append("episode_id fehlt")
        if re.search(r"https?://", text): err.append("Link im Text")
        if err:
            bad.append((qid, "; ".join(err))); continue
        pid = resolve(d, ids, names)
        if not pid:
            blocked.append(f"{qid} ({d.get('speaker') or d.get('speaker_slug') or '?'})"); continue
        ts = d.get("time_s")
        q = {"id": qid, "person": pid, "text": text, "lang": lang, "episode_id": eid, "episode_slug": d.get("episode_slug") or ep.get("slug") or "",
             "time_s": int(float(ts)) if isinstance(ts, (int, float)) or str(ts or "").replace(".", "", 1).isdigit() else None,
             "about": [x for x in (d.get("entities") or []) if isinstance(x, str)][:8], "why": str(d.get("why") or "")[:200],
             "source_video_id": d.get("source_video_id") or ep.get("source_video_id") or ep.get("youtube_video_id") or "", "src": src}
        if qid not in by:
            added.append(qid); q["imported"] = time.strftime("%Y-%m-%d", time.gmtime())
        by[qid] = {**by.get(qid, {}), **q}
    if not dry and (added or len(by) != len(have)):
        OUT.write_text(json.dumps(sorted(by.values(), key=lambda q: (q["person"], q["episode_id"], q["id"])), ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"Quotes neu: {len(added)}, gesamt: {len(by)}, ohne Personen-Entitaet: {len(blocked)}, abgelehnt: {len(bad)}")
    for n, e in bad[:30]: print("   abgelehnt:", n, e)
    for n in blocked[:30]: print("   ohne Personen-Entitaet:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
