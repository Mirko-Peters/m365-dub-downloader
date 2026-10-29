#!/usr/bin/env python3
"""Claude entwirft pro Folge und Sprache die Cover-Texte: kurze Schlagzeile, 3 Stichworte, passendes Motiv -> data/covers/<VIDEO>.json.
Braucht ANTHROPIC_API_KEY. Vorhandene Eintraege bleiben. COVER_LIMIT begrenzt neue Eintraege pro Lauf."""
import glob, json, os, re, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from site_cover import MOTIFS

ROOT = Path(__file__).parent
MODEL = os.environ.get("COVER_MODEL", "claude-haiku-5-5")
LIMIT = int(os.environ.get("COVER_LIMIT", "700"))
NAMES = {"de": "Deutsch", "es": "Spanisch", "fr": "Französisch", "it": "Italienisch", "pt": "Portugiesisch", "nl": "Niederländisch", "pl": "Polnisch",
         "id": "Indonesisch", "ru": "Russisch", "uk": "Ukrainisch", "ar": "Arabisch", "he": "Hebräisch", "hi": "Hindi", "ja": "Japanisch", "ko": "Koreanisch",
         "ml": "Malayalam", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "en": "Englisch"}


def strip(h): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


def ask(lang, title, desc):
    prompt = f"""Entwirf das Cover-Bild (Text) für eine Podcast-Folge zu Microsoft 365 / Azure / Copilot.
Sprache aller Texte: {NAMES.get(lang, lang)}.
Gib NUR ein JSON-Objekt aus:
{{"headline": "packende Schlagzeile, 2 bis 7 Wörter, benennt das konkrete Thema/den Nutzen, kein Doppelpunkt, keine Anführungszeichen",
 "keywords": ["3 Stichworte, je 1-2 Wörter, konkrete Produkt- oder Fachbegriffe aus der Folge"],
 "motif": "genau eines von: {', '.join(MOTIFS)}"}}
Nichts erfinden, nur was Titel und Beschreibung hergeben.

Titel: {title}
Beschreibung: {desc[:1500]}"""
    body = json.dumps({"model": MODEL, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    for attempt in range(5):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=90))
            break
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 500, 502, 503, 529) and attempt < 4:
                time.sleep(10 * (attempt + 1)); continue
            raise
    raw = "".join(b.get("text", "") for b in r["content"])
    d = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    h = str(d.get("headline", "")).strip().strip('"“”')
    kws = [str(k).strip() for k in (d.get("keywords") or []) if str(k).strip()][:3]
    m = d.get("motif") if d.get("motif") in MOTIFS else None
    if not h or len(h) > 70:
        return None
    return {"headline": h, "keywords": kws, "motif": m}


def work(job):
    vid, l, title, desc = job
    try:
        return vid, l, ask(l, title, desc)
    except Exception as ex:
        print("Fehler", vid, l, str(ex)[:120])
        return vid, l, None


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Kein ANTHROPIC_API_KEY – übersprungen")
        return
    (ROOT / "data" / "covers").mkdir(parents=True, exist_ok=True)
    jobs, store = [], {}
    for p in sorted(glob.glob(str(ROOT / "episodes" / "*.json"))):
        vid = Path(p).stem
        eps = json.load(open(p, encoding="utf-8"))
        cp = ROOT / "data" / "covers" / f"{vid}.json"
        store[vid] = json.load(open(cp, encoding="utf-8")) if cp.exists() else {}
        for l, e in eps.items():
            if l not in store[vid]:
                jobs.append((vid, l, e["title"], strip(e.get("desc", ""))))
    jobs = jobs[:LIMIT]
    changed = set()
    with ThreadPoolExecutor(10) as ex:
        for vid, l, res in ex.map(work, jobs):
            if res:
                store[vid][l] = res
                changed.add(vid)
    for vid in changed:
        json.dump(store[vid], open(ROOT / "data" / "covers" / f"{vid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(changed), "Videos mit Covern aktualisiert,", len(jobs), "versucht")


if __name__ == "__main__":
    main()
