#!/usr/bin/env python3
"""Schreibt pro Folge und Sprache einen Blogartikel aus dem Transkript (Claude API) → data/articles/<VIDEO>.json.
Braucht ANTHROPIC_API_KEY. ARTICLE_LIMIT (Standard 30) begrenzt die neuen Artikel pro Lauf (Kosten). Vorhandene Artikel bleiben."""
import glob, json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
MODEL = os.environ.get("ARTICLE_MODEL", "claude-sonnet-5-5")
LIMIT = int(os.environ.get("ARTICLE_LIMIT", "90"))
WORKERS = int(os.environ.get("ARTICLE_WORKERS", "10"))
NAMES = {"de": "Deutsch", "es": "Spanisch", "fr": "Französisch", "it": "Italienisch", "pt": "Portugiesisch", "nl": "Niederländisch",
         "pl": "Polnisch", "id": "Indonesisch", "ru": "Russisch", "uk": "Ukrainisch", "ar": "Arabisch", "he": "Hebräisch", "hi": "Hindi",
         "ja": "Japanisch", "ko": "Koreanisch", "ml": "Malayalam", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu"}
ALLOWED = {"h2", "h3", "p", "ul", "ol", "li", "strong", "em", "blockquote"}


def vtt_text(p):
    out = []
    for line in open(p, encoding="utf-8").read().splitlines():
        if not line.strip() or line.startswith("WEBVTT") or "-->" in line or line.strip().isdigit():
            continue
        out.append(line.strip())
    return re.sub(r"\s+", " ", " ".join(out))


def clean(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    html = re.sub(r"</?(\w+)[^>]*>", lambda m: re.sub(r"\s[^>]*", "", m.group(0)) if m.group(1).lower() in ALLOWED else "", html)
    return html.strip()


def ask(lang, title, text):  # -> (html, infografik|None)
    prompt = f"""Schreibe aus dem folgenden Podcast-Transkript einen eigenständigen, gut lesbaren Blogartikel für Suchmaschinen und Leser.

Regeln:
- Sprache des Artikels: {NAMES.get(lang, lang)} (Zielsprache der Leser), natürliche, idiomatische Sprache, keine Wort-für-Wort-Übersetzung.
- 1200-1800 Wörter, ausführlich und tiefgehend. Struktur: Einstieg (ein bis zwei <p>), 5-7 Abschnitte mit <h2>-Überschriften (suchmaschinenfreundlich, mit den Kernbegriffen), pro Abschnitt mehrere Absätze, wo sinnvoll <h3>-Unterpunkte oder Listen, ein Abschnitt "häufige Fehler / Stolpersteine" falls im Transkript vorhanden, zum Schluss ein Abschnitt mit praktischen Takeaways als <ul> und ein kurzes Fazit.
- Nur Inhalte aus dem Transkript. Nichts erfinden: keine Zahlen, Produktnamen, Zitate oder Versprechen, die nicht im Transkript stehen. Produktnamen (Microsoft 365, Copilot, Azure ...) unübersetzt lassen.
- Keine Titelwiederholung als H1, keine Links, keine Werbung, kein Hinweis auf KI.
- Erlaubtes HTML: h2, h3, p, ul, ol, li, strong, em.
- Ausgabeformat: zuerst das HTML des Artikels. Danach eine Zeile mit genau ---INFOGRAFIK--- und darunter ein JSON-Objekt für eine Infografik, die den Kern der Folge zusammenfasst (Texte in der Zielsprache, kurz, nur Inhalte aus dem Transkript):
  {"titel": "...", "typ": "schritte", "punkte": [{"kopf": "max. 4 Wörter", "text": "max. 18 Wörter"}, ...4 bis 6 Punkte]}
  Mögliche "typ": "schritte" (Ablauf/Vorgehen), "vergleich" (dann "links": {"titel","punkte":[Strings]}, "rechts": {"titel","punkte":[Strings]}), "fakten" (dann "punkte": [{"wert": "nur wenn im Transkript genannt", "text": "..."}]).
- Sonst nichts ausgeben.

Titel der Folge: {title}

Transkript:
{text[:60000]}"""
    body = json.dumps({"model": MODEL, "max_tokens": 9000, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    r = None
    for attempt in range(5):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=240))
            break
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 500, 502, 503, 529) and attempt < 4:
                time.sleep(15 * (attempt + 1))
                continue
            raise
    raw = "".join(b.get("text", "") for b in r["content"])
    html, _, info = raw.partition("---INFOGRAFIK---")
    inf = None
    m = re.search(r"\{.*\}", info, re.S)
    if m:
        try:
            inf = json.loads(m.group(0))
        except Exception:
            inf = None
    return clean(html), inf


def work(job):
    vid, l, title, vp = job
    text = vtt_text(vp)
    if len(text) < 800:
        return vid, l, None
    try:
        html, inf = ask(l, title, text)
    except Exception as ex:
        print("Fehler", vid, l, str(ex)[:150])
        return vid, l, None
    if len(re.sub(r"<[^>]+>", "", html)) < 3000:
        print("Zu kurz, verworfen:", vid, l)
        return vid, l, None
    print("Artikel", vid, l, len(html))
    res = {"html": html, "model": MODEL}
    if inf:
        res["info"] = inf
    return vid, l, res


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Kein ANTHROPIC_API_KEY – übersprungen")
        return
    (ROOT / "data" / "articles").mkdir(parents=True, exist_ok=True)
    jobs, store = [], {}
    for p in sorted(glob.glob(str(ROOT / "episodes" / "*.json"))):
        vid = Path(p).stem
        eps = json.load(open(p, encoding="utf-8"))
        ap = ROOT / "data" / "articles" / f"{vid}.json"
        store[vid] = json.load(open(ap, encoding="utf-8")) if ap.exists() else {}
        for l, e in eps.items():
            vp = ROOT / "transcripts" / l / f"{vid}.vtt"
            if l not in store[vid] and vp.exists():
                jobs.append((vid, l, e["title"], vp))
    jobs = jobs[:LIMIT]
    changed = set()
    with ThreadPoolExecutor(WORKERS) as ex:
        for vid, l, res in ex.map(work, jobs):
            if res:
                store[vid][l] = res
                changed.add(vid)
                json.dump(store[vid], open(ROOT / "data" / "articles" / f"{vid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(changed), "Videos aktualisiert,", len(jobs), "Artikel versucht")


if __name__ == "__main__":
    main()
