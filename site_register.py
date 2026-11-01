"""Registerdateien fuer die Datenbank (Paket 16/17): der Worker uebernimmt sie alle 30 Minuten.
- episodes-register.json: eine Zeile je Folge der Hauptshow (Slug, Spreaker-ID, Titel, Teaser, Datum, Dauer, Bild, Audio, YouTube, Meta) plus Texte (Show Notes, Markup, Kernpunkte, FAQ, Transkript-Link) und Gaeste.
- translations-register.json: Uebersetzungen der Folgen (Titel, Teaser, Show Notes je Sprache) aus data/podpage_i18n.
- translations-blog.json: Uebersetzungen der frueheren Blogbeitraege (Titel, Teaser, FAQ, Verweis auf die fertige Seite im R2-Bucket) aus den gebauten Sprachfassungen.
Modell: ein Inhalt einmal im Original, je Sprache und Feld eine Uebersetzung ("ist Uebersetzung von"), keine Dopplung ganzer Datensaetze."""
import json, re
from pathlib import Path

ROOT = Path(__file__).parent
LANGS = ["de", "fr", "es", "it", "nl", "pt", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko"]


def build(write, BASE, TODAY, posts):
    import site_podpage as P
    import site_notes as SNT
    idx = P.episode_index(BASE)
    enx = json.loads((ROOT / "data" / "en_episodes.json").read_text("utf-8")) if (ROOT / "data" / "en_episodes.json").exists() else {}
    gents = {e["id"]: e for e in json.loads((ROOT / "data" / "guest_entities.json").read_text("utf-8"))} if (ROOT / "data" / "guest_entities.json").exists() else {}
    gid = {}
    for e in gents.values():
        gid[e["id"][:-6] if e["id"].endswith("-guest") else e["id"]] = e["id"]
    eps = []
    for e in idx["eps"]:
        it = idx["by_slug"].get(e["slug"]) or {}
        nrec = SNT.get("en", title=e["name"]); r = enx.get(P.norm(e["name"])) or {}
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", e.get("video_link") or "")
        eps.append({"slug": e["slug"], "spreaker_id": str((nrec or {}).get("id") or ""), "title": e["name"], "summary": it.get("sum") or "", "published": (e.get("create_time") or "")[:10],
                    "duration": int((nrec or {}).get("duration") or 0), "season": "" if str(e.get("season")) == "None" else str(e.get("season") or ""), "number": "" if str(e.get("number")) in ("None", "") else str(e.get("number")),
                    "image": P.thumb_of(e, nrec), "audio": r.get("audio") or "", "youtube_id": m.group(1) if m else "", "meta_title": e.get("meta_title") or "", "meta_description": e.get("meta_description") or "",
                    "texts": {"notes": ((nrec or {}).get("markup") or P.san(e.get("show_notes")) or "")[:20000], "keypoints": it.get("keypoints") or [], "faq": it.get("faq") or [], "transcript_url": (nrec or {}).get("transcript_url") or ""},
                    "guests": [gid[g] for g in (it.get("guests") or []) if g in gid]})
    PART = 300   # Teile von je 300 Folgen (Worker-Speicher): episodes-register.json (Index) + episodes-register-N.json
    for n in range(0, len(eps), PART):
        write(f"episodes-register-{n // PART + 1}.json", json.dumps({"generated": TODAY, "part": n // PART + 1, "episodes": eps[n:n + PART]}, ensure_ascii=False))
    write("episodes-register.json", json.dumps({"generated": TODAY, "count": len(eps), "parts": (len(eps) + PART - 1) // PART, "slugs": [e["slug"] for e in eps]}, ensure_ascii=False))
    # Uebersetzungen der Folgen (Titel, Teaser, Show Notes)
    tr = []
    I18 = ROOT / "data" / "podpage_i18n"
    for l in LANGS:
        f = I18 / f"{l}.json"
        if f.exists():
            for slug, v in json.loads(f.read_text("utf-8")).items():
                if not v or not v[0]: continue
                tr.append({"kind": "episode", "id": slug, "lang": l, "field": "title", "text": v[0], "src": "haiku"})
                if len(v) > 1 and v[1]: tr.append({"kind": "episode", "id": slug, "lang": l, "field": "summary", "text": v[1], "src": "haiku"})
        f = I18 / f"notes_{l}.json"
        if f.exists():
            for slug, v in json.loads(f.read_text("utf-8")).items():
                if v: tr.append({"kind": "episode", "id": slug, "lang": l, "field": "notes_html", "text": v if isinstance(v, str) else json.dumps(v, ensure_ascii=False), "src": "haiku"})
    for l in LANGS:   # je Sprache eine Datei (Worker-Speicher); der Worker nimmt je Lauf eine Sprache
        items = [x for x in tr if x["lang"] == l]
        write(f"translations-register-{l}.json", json.dumps({"generated": TODAY, "kind": "episode", "lang": l, "count": len(items), "items": items}, ensure_ascii=False))
    write("translations-register.json", json.dumps({"generated": TODAY, "kind": "episode", "count": len(tr), "langs": LANGS}, ensure_ascii=False))
    # Uebersetzungen der frueheren Blogbeitraege: aus den gebauten Sprachfassungen (Titel, Teaser, FAQ; fertige Seite liegt im R2-Bucket)
    bt = []
    for p in posts:
        if not p.get("tr_of"): continue
        bt.append({"kind": "lblog", "id": p["slug"], "lang": p["lang"], "field": "title", "text": p["title"], "src": "haiku"})
        if p.get("summary"): bt.append({"kind": "lblog", "id": p["slug"], "lang": p["lang"], "field": "summary", "text": p["summary"], "src": "haiku"})
        if p.get("faq"): bt.append({"kind": "lblog", "id": p["slug"], "lang": p["lang"], "field": "faq", "text": json.dumps(p["faq"], ensure_ascii=False), "src": "haiku"})
        bt.append({"kind": "lblog", "id": p["slug"], "lang": p["lang"], "field": "html_key", "text": f"pages/{p['lang']}/community/u/{p['handle']}/blog/{p['slug']}/index.html", "src": "site"})
    write("translations-blog.json", json.dumps({"generated": TODAY, "kind": "lblog", "count": len(bt), "items": bt}, ensure_ascii=False))
    print(f"Register: {len(eps)} Folgen, {len(tr)} Folgen-Uebersetzungen, {len(bt)} Blog-Uebersetzungen")
