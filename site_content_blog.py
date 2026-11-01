"""T15: Import-Pfad fuer Content-Pakete. Blogbeitraege liegen als imports/blog/<sprache>/<slug>.md (YAML-Kopf plus Markdown) im Repo.
Freigegebene Pakete (status: approved) veroeffentlicht der Seitenbau als SITE/blog-content/index.json; der Worker-Cron importContentBlog
legt sie in blog_posts an: ohne Flag als 'pending' (Freigabe in der Verwaltung, Bereich Blog-Pruefung), mit publish: true direkt 'live'.
Pakete mit status: review bleiben liegen. Geprueft wird: Titel, Kurzfassung, Laenge, Sprache, Autor-Handle, Themen (Entitaeten),
Bilder nur von img.m365.fm (CLAUDE.md), keine Skripte. Fehler stehen im Bericht blog-content/report.json und im Build-Log; nichts wird geloescht.

Kopf: title, summary, status (review|approved), publish (true|false), author (Profil-Handle, Standard mirko-p), date (JJJJ-MM-TT),
topics (Entitaets-IDs), faq ([{q, a}]). Text: Markdown mit ##-Ueberschriften, Absaetzen, Listen, **fett**, *kursiv*, `code`,
[Link](https://...) und Bildern ![Alt](https://img.m365.fm/...)."""
import hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path

import site_shownotes as SNS
from site_learn import esc

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "imports" / "blog"
LANGS = {"en", "de", "es", "fr", "it", "pt", "nl", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko"}
IMG = re.compile(r"!\[([^\]]*)\]\((https?://[^\s)]+)\)")
HANDLE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,100}$")


def _ts(d):
    try:
        return int(datetime.strptime(str(d)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    except ValueError:
        return 0


def render(md):
    """Markdown -> HTML (gleiche Grundlage wie die Shownotes); Bildzeilen werden zu <figure>."""
    out = []
    for b in SNS.md_blocks(IMG.sub(lambda m: f"\n\n@@IMG@@{m.group(2)}@@{m.group(1)}@@\n\n", md)):
        if b[0] == "h":
            lvl, t = b[1]; lvl = min(max(lvl, 2), 4); out.append(f"<h{lvl}>{SNS._inline(t)}</h{lvl}>")
        elif b[0] == "p":
            m = re.fullmatch(r"@@IMG@@(\S+)@@(.*)@@", b[1].strip())
            out.append(f'<figure><img src="{esc(m.group(1))}" alt="{esc(m.group(2))}" loading="lazy" decoding="async"></figure>' if m else f"<p>{SNS._inline(b[1])}</p>")
        else:
            out.append(f"<{b[0]}>" + "".join(f"<li>{SNS._inline(x)}</li>" for x in b[1]) + f"</{b[0]}>")
    return "\n".join(out)


def check(rec, lang, slug, ents):
    """-> (eintrag oder None, fehlerliste)"""
    m, body, err = rec["meta"], rec["body"], []
    title, summary = str(m.get("title") or "").strip(), str(m.get("summary") or "").strip()
    author = str(m.get("author") or "mirko-p").strip().lower()
    if not SLUG.match(slug): err.append("Slug ungueltig")
    if not 10 <= len(title) <= 140: err.append(f"Titel {len(title)} Zeichen (10-140)")
    if not 50 <= len(summary) <= 300: err.append(f"Kurzfassung {len(summary)} Zeichen (50-300)")
    if not HANDLE.match(author): err.append("Autor-Handle ungueltig")
    words = len(re.sub(r"[#*`>\[\]()!-]", " ", body).split())
    if words < 300: err.append(f"Text {words} Woerter (mindestens 300)")
    if re.search(r"<\s*(script|iframe|style|form)", body, re.I): err.append("HTML-Element nicht erlaubt (script/iframe/style/form)")
    bad = sorted({u for _, u in IMG.findall(body) if not u.startswith("https://img.m365.fm/")})
    if bad: err.append("Bilder nur von https://img.m365.fm/: " + ", ".join(bad[:3]))
    topics = [t for t in (m.get("topics") or []) if isinstance(t, str)]
    unknown = [t for t in topics if t not in ents]
    if unknown: err.append("unbekannte Themen: " + ", ".join(unknown[:5]))
    faq = [{"q": str(x.get("q") or "")[:200], "a": str(x.get("a") or "")[:600]} for x in (m.get("faq") or []) if isinstance(x, dict) and x.get("q") and x.get("a")]
    if err: return None, err
    html = render(body)
    item = {"slug": slug, "lang": lang, "title": title, "summary": summary, "author": author, "html": html, "topics": topics[:10], "faq": faq[:10],
            "publish": m.get("publish") in (True, "true", "yes", 1), "published": _ts(m.get("date")) or int(time.time())}
    item["hash"] = hashlib.sha1(json.dumps(item, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return item, []


def collect(ents):
    """-> (freigegebene Eintraege, Bericht). Gleicher Slug beim selben Autor in zwei Sprachen ist ein Fehler (Datenbank: UNIQUE user_id, slug)."""
    items, rep, seen = [], {"approved": 0, "review": 0, "errors": []}, {}
    if not DIR.exists(): return items, rep
    for f in sorted(DIR.glob("*/*.md")):
        lang, slug = f.parent.name, f.stem
        if lang not in LANGS or slug.startswith("_"): continue
        rec = SNS.parse_file(f)
        st = str(rec["meta"].get("status") or "review").lower()
        if st != "approved": rep["review"] += 1; continue
        it, err = check(rec, lang, slug, ents)
        key = (str(rec["meta"].get("author") or "mirko-p").lower(), slug)
        if it and key in seen: err, it = [f"Slug schon in {seen[key]} vergeben"], None
        if err: rep["errors"].append({"file": f"{lang}/{slug}.md", "errors": err}); continue
        seen[key] = lang; items.append(it); rep["approved"] += 1
    return items, rep


def publish(write, ents):
    """Schreibt blog-content/index.json (nur freigegebene, fehlerfreie Pakete) und blog-content/report.json."""
    items, rep = collect(ents)
    write("blog-content/index.json", json.dumps({"version": 1, "items": items}, ensure_ascii=False, separators=(",", ":")))
    write("blog-content/report.json", json.dumps(rep, ensure_ascii=False, indent=1))
    if items or rep["errors"] or rep["review"]:
        print(f"Content-Pakete Blog: {rep['approved']} freigegeben, {rep['review']} in Pruefung, {len(rep['errors'])} mit Fehlern")
        for e in rep["errors"][:20]: print("  FEHLER", e["file"], "; ".join(e["errors"]))
    return len(items)
