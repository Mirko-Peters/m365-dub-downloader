#!/usr/bin/env python3
"""Schreibt pro Folge und Sprache einen Blogartikel aus dem Transkript (Claude API) → data/articles/<VIDEO>.json.
Braucht ANTHROPIC_API_KEY. ARTICLE_LIMIT (Standard 30) begrenzt die neuen Artikel pro Lauf (Kosten). Vorhandene Artikel bleiben."""
import glob, json, os, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
MODEL = os.environ.get("ARTICLE_MODEL", "claude-sonnet-5-5")
LIMIT = int(os.environ.get("ARTICLE_LIMIT", "30"))
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


def ask(lang, title, text):
    prompt = f"""Schreibe aus dem folgenden Podcast-Transkript einen eigenständigen, gut lesbaren Blogartikel für Suchmaschinen und Leser.

Regeln:
- Sprache des Artikels: {NAMES.get(lang, lang)} (Zielsprache der Leser), natürliche, idiomatische Sprache, keine Wort-für-Wort-Übersetzung.
- 500-800 Wörter. Struktur: kurzer Einstieg (ein <p>), 3-5 Abschnitte mit <h2>-Überschriften (suchmaschinenfreundlich, mit den Kernbegriffen), pro Abschnitt Absätze, zum Schluss ein Abschnitt mit praktischen Takeaways als <ul>.
- Nur Inhalte aus dem Transkript. Nichts erfinden: keine Zahlen, Produktnamen, Zitate oder Versprechen, die nicht im Transkript stehen. Produktnamen (Microsoft 365, Copilot, Azure ...) unübersetzt lassen.
- Keine Titelwiederholung als H1, keine Links, keine Werbung, kein Hinweis auf KI.
- Erlaubtes HTML: h2, h3, p, ul, ol, li, strong, em.
- Antworte NUR mit dem HTML des Artikels.

Titel der Folge: {title}

Transkript:
{text[:60000]}"""
    body = json.dumps({"model": MODEL, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    return clean("".join(b.get("text", "") for b in r["content"]))


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Kein ANTHROPIC_API_KEY – übersprungen")
        return
    (ROOT / "data" / "articles").mkdir(parents=True, exist_ok=True)
    done = 0
    for p in sorted(glob.glob(str(ROOT / "episodes" / "*.json"))):
        vid = Path(p).stem
        eps = json.load(open(p, encoding="utf-8"))
        ap = ROOT / "data" / "articles" / f"{vid}.json"
        arts = json.load(open(ap, encoding="utf-8")) if ap.exists() else {}
        changed = False
        for l, e in eps.items():
            if l in arts:
                continue
            vp = ROOT / "transcripts" / l / f"{vid}.vtt"
            if not vp.exists() or done >= LIMIT:
                continue
            text = vtt_text(vp)
            if len(text) < 800:
                continue
            try:
                html = ask(l, e["title"], text)
            except Exception as ex:
                print("Fehler", vid, l, str(ex)[:150])
                continue
            if len(re.sub(r"<[^>]+>", "", html)) < 1500:
                print("Zu kurz, verworfen:", vid, l)
                continue
            arts[l] = {"html": html, "model": MODEL}
            changed = True
            done += 1
            print("Artikel", vid, l, len(html))
        if changed:
            json.dump(arts, open(ap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(done, "neue Artikel")


if __name__ == "__main__":
    main()
