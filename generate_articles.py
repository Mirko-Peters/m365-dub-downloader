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


def _post(prompt, max_tokens):
    body = json.dumps({"model": MODEL, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}).encode()
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
    return "".join(b.get("text", "") for b in r["content"])


def parse_info(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(0))
        return j if isinstance(j, dict) and j.get("punkte") or j.get("links") else None
    except Exception:
        return None


def info_for(lang, html):
    """Zweiter Versuch: nur die Infografik (JSON) aus dem fertigen Artikel ableiten."""
    txt = re.sub(r"<[^>]+>", " ", html)[:12000]
    p = (f"Erstelle aus dem folgenden Artikel eine Infografik als reines JSON (keine Erklärung, kein Markdown), Texte in {NAMES.get(lang, lang)}, "
         'nur Inhalte aus dem Artikel. Format: {"titel": "...", "typ": "schritte", "punkte": [{"kopf": "max. 4 Wörter", "text": "max. 18 Wörter"}, ...4 bis 6 Punkte]}. '
         'Alternativ "typ": "vergleich" mit "links"/"rechts": {"titel","punkte":[Strings]} oder "typ": "fakten" mit "punkte": [{"wert","text"}].\n\nArtikel:\n' + txt)
    try:
        return parse_info(_post(p, 1500))
    except Exception as ex:
        print("Infografik-Fehler", str(ex)[:100])
        return None


def faq_for(lang, html):
    """3-4 Fragen/Antworten (JSON-Liste) aus dem fertigen Artikel."""
    txt = re.sub(r"<[^>]+>", " ", html)[:14000]
    p = (f"Erstelle aus dem folgenden Artikel 4 häufige Fragen mit kurzen, präzisen Antworten (je 25 bis 60 Wörter) in {NAMES.get(lang, lang)}. "
         "Nur Inhalte aus dem Artikel, keine Verweise auf Transkript/Podcast/Folge, keine Links. Die Fragen so formulieren, wie Leser sie bei Google oder einem KI-Assistenten stellen würden. "
         'Ausgabe: reines JSON, keine Erklärung: [{"q": "...", "a": "..."}, ...]\n\nArtikel:\n' + txt)
    try:
        raw = _post(p, 2500)
        m = re.search(r"\[.*\]", raw, re.S)
        j = json.loads(m.group(0)) if m else None
        j = [{"q": str(x["q"]).strip(), "a": str(x["a"]).strip()} for x in j if x.get("q") and x.get("a")] if j else None
        return j[:5] if j and len(j) >= 3 else None
    except Exception as ex:
        print("FAQ-Fehler", str(ex)[:100])
        return None


def quiz_for(lang, html):
    """4 Multiple-Choice-Fragen (je 4 Optionen) aus dem fertigen Artikel."""
    txt = re.sub(r"<[^>]+>", " ", html)[:14000]
    p = (f"Erstelle aus dem folgenden Artikel ein Quiz mit genau 4 Multiple-Choice-Fragen in {NAMES.get(lang, lang)}. Jede Frage hat genau 4 Antwortoptionen (je max. 14 Wörter), genau eine ist richtig, "
         "die falschen sind plausibel, aber eindeutig falsch. Nur Wissen aus dem Artikel, keine Verweise auf Transkript/Podcast/Folge, keine Links, richtige Antwort nicht immer an derselben Position. "
         'Zu jeder Frage eine kurze Erklärung (max. 25 Wörter). Ausgabe: reines JSON, keine Erklärung: [{"q": "...", "opts": ["...","...","...","..."], "a": 0, "why": "..."}, ...] ("a" = Index 0-3 der richtigen Option)\n\nArtikel:\n' + txt)
    try:
        raw = _post(p, 3000)
        m = re.search(r"\[.*\]", raw, re.S)
        j = json.loads(m.group(0)) if m else None
        out = []
        for x in j or []:
            o = [str(t).strip() for t in x.get("opts", [])]
            a = int(x.get("a", -1))
            if x.get("q") and len(o) == 4 and all(o) and 0 <= a < 4:
                out.append({"q": str(x["q"]).strip(), "opts": o, "a": a, "why": str(x.get("why", "")).strip()})
        return out[:5] if len(out) >= 3 else None
    except Exception as ex:
        print("Quiz-Fehler", str(ex)[:100])
        return None


def infos_for(lang, html, have=()):
    """Zwei weitere Infografiken (andere Typen als die erste) als JSON-Liste."""
    txt = re.sub(r"<[^>]+>", " ", html)[:14000]
    p = (f"Erstelle aus dem folgenden Artikel genau 2 weitere Infografiken als reines JSON-Array (keine Erklärung, kein Markdown), Texte in {NAMES.get(lang, lang)}, "
         "nur Inhalte aus dem Artikel, keine Verweise auf Transkript/Podcast/Folge. Die beiden sollen unterschiedliche Typen haben und möglichst nicht den Typ " + ", ".join(have or ("schritte",)) + " wiederholen. "
         'Typen: {"titel":"...","typ":"vergleich","links":{"titel":"...","punkte":["..."]},"rechts":{"titel":"...","punkte":["..."]}} (je 3-5 Punkte, max. 14 Wörter) | '
         '{"titel":"...","typ":"fakten","punkte":[{"wert":"nur wenn im Artikel genannt, sonst ein Stichwort","text":"max. 14 Wörter"}]} (3-5 Punkte) | '
         '{"titel":"...","typ":"checkliste","punkte":["max. 14 Wörter", ...]} (4-7 Punkte) | '
         '{"titel":"...","typ":"schritte","punkte":[{"kopf":"max. 4 Wörter","text":"max. 18 Wörter"}]} (4-6 Punkte) | '
         '{"titel":"...","typ":"prozess","punkte":[{"kopf":"max. 3 Wörter","text":"max. 14 Wörter","art":"start|schritt|entscheidung|ende"}]} (4-6 Knoten eines Prozessablaufs, erster "start", letzter "ende"; "entscheidung" nur wenn der Artikel eine Ja/Nein-Weiche beschreibt). '
         "Ausgabe: [ {...}, {...} ]\n\nArtikel:\n" + txt)
    try:
        raw = _post(p, 3000)
        m = re.search(r"\[.*\]", raw, re.S)
        j = json.loads(m.group(0)) if m else []
        ok = [x for x in j if isinstance(x, dict) and x.get("typ") in ("vergleich", "fakten", "checkliste", "schritte", "prozess") and x.get("titel")]
        return ok[:2] or None
    except Exception as ex:
        print("Infografik2-Fehler", str(ex)[:100])
        return None


def ask(lang, title, text):  # -> (html, infografik|None)
    prompt = f"""Schreibe aus dem folgenden Podcast-Transkript einen eigenständigen, gut lesbaren Blogartikel für Suchmaschinen und Leser.

Regeln:
- Sprache des Artikels: {NAMES.get(lang, lang)} (Zielsprache der Leser), natürliche, idiomatische Sprache, keine Wort-für-Wort-Übersetzung.
- 1200-1800 Wörter (auf keinen Fall mehr als 1800), ausführlich, aber ohne Füllsätze. Struktur: Einstieg (ein bis zwei <p>), 5-7 Abschnitte mit <h2>-Überschriften (suchmaschinenfreundlich, mit den Kernbegriffen), pro Abschnitt mehrere Absätze, wo sinnvoll <h3>-Unterpunkte oder Listen, ein Abschnitt "häufige Fehler / Stolpersteine" falls im Transkript vorhanden, zum Schluss ein Abschnitt mit praktischen Takeaways als <ul> und ein kurzes Fazit.
- Nur Inhalte aus dem Transkript. Nichts erfinden: keine Zahlen, Produktnamen, Zitate oder Versprechen, die nicht im Transkript stehen. Produktnamen (Microsoft 365, Copilot, Azure ...) unübersetzt lassen.
- Keine Titelwiederholung als H1, keine Links, keine Werbung, kein Hinweis auf KI.
- Verweise nie auf "Transkript", "Podcast", "Folge", "Video" oder "Sprecher"; schreibe als eigenständiger Fachartikel. Wirkt eine Stelle im Transkript verstümmelt (Spracherkennungsfehler), formuliere neutral oder lass sie weg, statt zu raten. Beispiele nur, wenn sie im Transkript vorkommen. Beende den Artikel immer mit einem vollständigen Fazit-Absatz.
- Erlaubtes HTML: h2, h3, p, ul, ol, li, strong, em.
- Ausgabeformat: zuerst das HTML des Artikels. Danach eine Zeile mit genau ---INFOGRAFIK--- und darunter ein JSON-Objekt für eine Infografik, die den Kern der Folge zusammenfasst (Texte in der Zielsprache, kurz, nur Inhalte aus dem Transkript):
  {{"titel": "...", "typ": "schritte", "punkte": [{{"kopf": "max. 4 Wörter", "text": "max. 18 Wörter"}}, ...4 bis 6 Punkte]}}
  Mögliche "typ": "schritte" (Ablauf/Vorgehen), "vergleich" (dann "links": {{"titel","punkte":[Strings]}}, "rechts": {{"titel","punkte":[Strings]}}), "prozess" (Ablaufdiagramm, "punkte": [{{"kopf","text","art":"start|schritt|entscheidung|ende"}}], 4-6 Knoten), "fakten" (dann "punkte": [{{"wert": "nur wenn im Transkript genannt", "text": "..."}}]).
- Sonst nichts ausgeben.

Titel der Folge: {title}

Transkript:
{text[:60000]}"""
    raw = _post(prompt, 16000)
    html, _, info = raw.partition("---INFOGRAFIK---")
    inf = None
    m = re.search(r"\{.*\}", info, re.S)
    if m:
        try:
            inf = json.loads(m.group(0))
        except Exception:
            inf = None
    return clean(html), inf


META = re.compile(r"transkript|transcript|transcripci|transcrição|transcrizione|podcast|в подкасте|в транскрипте|في التسجيل|ポッドキャスト|トランスクリプト|팟캐스트|트랜스크립트", re.I)
NOSPACE = {"ja", "ko", "zh"}


def problems(html, lang):
    """Qualitätsprüfung: abgeschnitten, zu lang, Meta-Verweise auf Transkript/Podcast."""
    p = []
    if not re.search(r"</(p|ul|ol|blockquote)>\s*$", html.strip()):
        p.append("abgeschnitten")
    txt = re.sub(r"<[^>]+>", " ", html)
    if lang not in NOSPACE and len(txt.split()) > 2000:
        p.append("zu lang")
    if META.search(txt):
        p.append("meta")
    return p


def work(job):
    vid, l, title, vp = job
    text = vtt_text(vp)
    if len(text) < 800:
        return vid, l, None
    html = inf = None
    for attempt in range(2):
        try:
            html, inf = ask(l, title, text)
        except Exception as ex:
            print("Fehler", vid, l, str(ex)[:150])
            return vid, l, None
        pr = problems(html, l)
        if not pr:
            break
        print("Qualität", vid, l, pr, "Versuch", attempt + 1)
    if "abgeschnitten" in problems(html, l):
        return vid, l, None
    if len(re.sub(r"<[^>]+>", "", html)) < 3000:
        print("Zu kurz, verworfen:", vid, l)
        return vid, l, None
    print("Artikel", vid, l, len(html))
    res = {"html": html, "model": MODEL}
    if not inf:
        inf = info_for(l, html)
    if inf:
        res["info"] = inf
    fq = faq_for(l, html)
    if fq:
        res["faq"] = fq
    more = infos_for(l, html, [inf.get("typ", "schritte")] if inf else ())
    if more:
        res["infos"] = more
    qz = quiz_for(l, html)
    if qz:
        res["quiz"] = qz
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
        for _l in [x for x, a in store[vid].items() if {"abgeschnitten", "meta"} & set(problems(a["html"], x))]:
            print("Mangelhaften Artikel neu schreiben:", vid, _l)
            del store[vid][_l]
        for l, e in eps.items():
            vp = ROOT / "transcripts" / l / f"{vid}.vtt"
            if l not in store[vid] and vp.exists():
                jobs.append((vid, l, e["title"], vp))
    jobs = jobs[:LIMIT]
    changed = set()
    # vorhandene Artikel ohne Infografik nachrüsten
    fill = [(v, l) for v, d in store.items() for l, a in d.items() if not a.get("info") or not a.get("faq") or not a.get("infos") or not a.get("quiz")][:LIMIT]
    def fillwork(t):
        v, l = t
        a = store[v][l]
        inf = a.get("info") or info_for(l, a["html"])
        more = None if a.get("infos") else infos_for(l, a["html"], [(inf or {}).get("typ", "schritte")])
        return v, l, (None if a.get("info") else inf), (None if a.get("faq") else faq_for(l, a["html"])), more, (None if a.get("quiz") else quiz_for(l, a["html"]))
    with ThreadPoolExecutor(WORKERS) as ex:
        for v, l, inf, fq, more, qz in ex.map(fillwork, fill):
            if inf: store[v][l]["info"] = inf
            if fq: store[v][l]["faq"] = fq
            if more: store[v][l]["infos"] = more
            if qz: store[v][l]["quiz"] = qz
            if inf or fq or more or qz:
                changed.add(v)
                json.dump(store[v], open(ROOT / "data" / "articles" / f"{v}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(fill), "Infografiken/FAQ nachgerüstet versucht")
    with ThreadPoolExecutor(WORKERS) as ex:
        for vid, l, res in ex.map(work, jobs):
            if res:
                store[vid][l] = res
                changed.add(vid)
                json.dump(store[vid], open(ROOT / "data" / "articles" / f"{vid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(changed), "Videos aktualisiert,", len(jobs), "Artikel versucht")


if __name__ == "__main__":
    main()
