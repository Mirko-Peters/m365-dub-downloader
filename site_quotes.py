"""Quotes als Objekte an Personen-Entitaeten (data/quotes.json, tools/import_quotes.py). Auf der Personenseite als Abschnitt
"Zitate"/"Quotes" mit Sprung zur Folge, im JSON-LD als Quotation mit creator = Personen-Entitaet und isPartOf = Folge."""
import json
from pathlib import Path
from site_learn import esc

_F = Path(__file__).resolve().parent / "data" / "quotes.json"
ALL = json.loads(_F.read_text("utf-8")) if _F.exists() else []
BY_PERSON = {}
for _q in ALL:
    BY_PERSON.setdefault(_q["person"], []).append(_q)
L = {"en": ("Quotes", "From the episode", "at"), "de": ("Zitate", "Aus der Folge", "bei")}


def _mmss(s):
    if s is None: return ""
    s = int(s); return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def for_person(pid, lang):
    """Zitate der Person; Seitensprache zuerst, dann Englisch, dann der Rest (hoechstens 12)."""
    qs = BY_PERSON.get(pid, [])
    order = {lang: 0, "en": 1}
    return sorted(qs, key=lambda q: (order.get(q["lang"], 2), q["episode_id"], q["id"]))[:12]


def block(pid, lang, ep_url):
    """HTML-Abschnitt; ep_url(q) -> (url, titel) oder (None, None)."""
    qs = for_person(pid, lang)
    if not qs: return ""
    t = L.get(lang, L["en"]); out = []
    for q in qs:
        u, title = ep_url(q)
        ts = _mmss(q.get("time_s"))
        src = (f' <a href="{esc(u)}{("#t=" + str(int(q["time_s"]))) if q.get("time_s") is not None else ""}">{esc(t[1])}{(": " + esc(title)) if title else ""}{(" (" + t[2] + " " + ts + ")") if ts else ""}</a>') if u else ""
        out.append(f'<figure class="en-quote" lang="{esc(q["lang"])}"><blockquote><p>{esc(q["text"])}</p></blockquote><figcaption class="mut">{src}</figcaption></figure>')
    css = "<style>.en-quote{margin:1em 0;border-inline-start:4px solid var(--ac);padding:.2em 1em}.en-quote blockquote{margin:0;font-size:1.05em}.en-quote figcaption{font-size:.9em}</style>"
    return f'{css}<section class="en-quotes"><h2>{esc(t[0])}</h2>{"".join(out)}</section>'


def ld(base, pid, lang, ep_url):
    """Quotation-Knoten (creator = Personen-Entitaet)."""
    out = []
    for q in for_person(pid, lang):
        u, title = ep_url(q)
        n = {"@context": "https://schema.org", "@type": "Quotation", "@id": f"{base}/entity/{pid}/#quote-{q['id']}", "text": q["text"], "inLanguage": q["lang"],
             "creator": {"@id": f"{base}/entity/{pid}/#entity"}}
        if u: n["isPartOf"] = {"@type": "PodcastEpisode", "url": u, **({"name": title} if title else {})}
        if q.get("about"): n["about"] = [{"@id": f"{base}/entity/{x}/#entity"} for x in q["about"]]
        out.append(n)
    return out
