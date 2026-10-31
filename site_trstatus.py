"""Uebersicht der Uebersetzungen fuer die Verwaltung (/admin/ -> Uebersetzungen): translation-status.json mit einer Zeile je Inhalt und den vorhandenen Sprachfassungen.
Arten: lblog (fruehere Blogbeitraege, data/blog_i18n), notes (Show Notes der Hauptshow, data/podpage_i18n/notes_<l>.json), entity (Kurz-/Langtext; Deutsch aus entities.json,
weitere Sprachen ergaenzt der Worker aus ent_tr). Community-Inhalte (Blog, Podcast, Video) liefert der Worker direkt aus der Datenbank."""
import gzip, json, os
from pathlib import Path

ROOT = Path(__file__).parent
LANGS = ["de", "fr", "es", "it", "nl", "pt", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko"]
CACHE = ROOT / "data" / "cache" / "blog_i18n_done.json"


def blog_done():
    """Je Sprache die Slugs mit vollstaendiger Uebersetzung; die gz-Dateien werden nur neu gelesen, wenn sie sich geaendert haben."""
    try:
        cache = json.loads(CACHE.read_text("utf-8")) if CACHE.exists() else {}
    except Exception:
        cache = {}
    out, changed = {}, False
    for l in LANGS:
        d = ROOT / "data" / "blog_i18n" / l
        files = sorted(d.glob("*.json.gz")) if d.exists() else []
        sig = ",".join(f"{f.name}:{int(f.stat().st_mtime)}:{f.stat().st_size}" for f in files)
        c = cache.get(l) or {}
        if c.get("sig") == sig:
            out[l] = c.get("slugs") or []; continue
        slugs = []
        for f in files:
            try:
                for slug, rec in json.loads(gzip.open(f, "rt", encoding="utf-8").read()).items():
                    if rec and rec.get("ok"): slugs.append(slug)
            except Exception:
                pass
        out[l] = sorted(set(slugs)); cache[l] = {"sig": sig, "slugs": out[l]}; changed = True
    if changed:
        try:
            CACHE.parent.mkdir(parents=True, exist_ok=True); CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return out


def build(write, TODAY, ents, legacy_posts, episodes):
    """legacy_posts: [{slug,title}], episodes: [{slug,title}] der Hauptshow."""
    rows = []
    done = blog_done()
    by_slug = {l: set(v) for l, v in done.items()}
    for p in legacy_posts:
        rows.append({"k": "lblog", "id": p["slug"], "t": p["title"][:120], "lang": "en", "langs": [l for l in LANGS if p["slug"] in by_slug.get(l, ())]})
    notes = {}
    for l in LANGS:
        f = ROOT / "data" / "podpage_i18n" / f"notes_{l}.json"
        try:
            notes[l] = set(json.loads(f.read_text("utf-8"))) if f.exists() else set()
        except Exception:
            notes[l] = set()
    for e in episodes:
        rows.append({"k": "notes", "id": e["slug"], "t": e["title"][:120], "lang": "en", "langs": [l for l in LANGS if e["slug"] in notes[l]]})
    for e in ents:
        if e.get("type") in ("person",): continue
        src = "en" if (e.get("desc") or {}).get("en") else "de"
        has_de = bool((e.get("desc") or {}).get("de")) and (e.get("desc") or {}).get("de") != (e.get("desc") or {}).get("en")
        rows.append({"k": "entity", "id": e["id"], "t": e["name"][:120], "lang": src, "langs": (["de"] if has_de and src == "en" else [])})
    write("translation-status.json", json.dumps({"generated": TODAY, "langs": LANGS, "rows": rows}, ensure_ascii=False))
    n = {k: sum(1 for r in rows if r["k"] == k) for k in ("lblog", "notes", "entity")}
    print(f"Uebersetzungsstatus: {n['lblog']} fruehere Beitraege, {n['notes']} Show Notes, {n['entity']} Entitaeten; de: {len(done.get('de', []))} Beitraege uebersetzt")
