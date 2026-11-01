"""Sitemaps je Sprache und Typ (Ticket T1).

Eingabe: die Liste (url, lastmod, alternates) des Seitenbaus. Jede URL wird einer Sprache (en oder /<lang>/) und einem Typ zugeordnet:
show-episodes (Hauptshow, auch Sprachfassungen), episodes (Dub-Folgen der Sprach-Shows), blog, entity, community (Profile, Bibliothek,
Podcast, Video, Feed, Shows), events (Events, Live), pages (Startseiten, Lernen, Glossar, Updates, Presse, Rechtliches, sonstige).
Ausgabe: sitemap-<lang>-<typ>.xml (bei mehr als 45.000 URLs in Teilen -2, -3 ...), sitemap.xml als Index. lastmod: Hub-Seiten, die der
Seitenbau mit dem Baudatum meldet, bekommen das juengste Datum ihrer Gruppe (sie aendern sich, wenn Inhalte dazukommen); der Index
fuehrt je Datei das juengste Datum. Alternates erhalten zusaetzlich x-default (= englische Fassung, sonst die erste)."""
import re
from urllib.parse import urlsplit

MAX_URLS = 45000
TYPES = ("show-episodes", "episodes", "blog", "entity", "community", "events", "pages")


def classify(path, langs):
    """-> (lang, typ) fuer einen URL-Pfad (ohne Host)."""
    seg = [x for x in path.split("/") if x]
    lang = "en"
    if seg and seg[0] in langs:
        lang = seg[0]; seg = seg[1:]
    if not seg:
        return lang, "pages"
    a = seg[0]
    if a == "show":
        return lang, ("show-episodes" if len(seg) >= 3 and seg[1] == "episodes" else "pages")
    if a == "entity":
        return lang, "entity"
    if a == "community":
        if len(seg) >= 2 and seg[1] in ("events", "event"): return lang, "events"
        if len(seg) >= 4 and seg[1] == "u" and seg[3] == "blog": return lang, "blog"
        return lang, "community"
    if a in ("live", "events"):
        return lang, "events"
    if a in ("learn", "glossary", "updates", "press", "legal", "privacy", "datenschutz", "imprint", "impressum", "accessibility", "top", "podcast", "shows", "mcp", "about", "sessions", "speakers", "m365con", "search"):
        return lang, "pages"
    # Dub-Folgen: /<lang>/<slug>/ (eine Ebene) in den Sprach-Shows; auf Englisch gibt es diese Ebene fuer Kernseiten
    if lang != "en" and len(seg) == 1:
        return lang, "episodes"
    return lang, "pages"


def _xml(entries, langs):
    x = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, lm, alts in entries:
        x.append(f"<url><loc>{u}</loc><lastmod>{lm}</lastmod>")
        if alts:
            for k, au in alts.items():
                x.append(f'<xhtml:link rel="alternate" hreflang="{langs[k][1] if k in langs else k}" href="{au}"/>')
            xd = alts.get("en") or next(iter(alts.values()))
            x.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{xd}"/>')
        x.append("</url>")
    x.append("</urlset>")
    return "\n".join(x)


def write_all(sitemap, write, base, langs, today):
    """Schreibt alle Dateien und den Index; -> Liste der Dateinamen."""
    groups = {}
    seen = set()
    for u, lm, alts in sitemap:
        if u in seen: continue
        seen.add(u)
        lang, typ = classify(urlsplit(u).path, langs)
        groups.setdefault((lang, typ), []).append((u, (lm or today)[:10], alts))
    files = []
    for (lang, typ) in sorted(groups, key=lambda k: (k[0] != "en", k[0], TYPES.index(k[1]))):
        ents = groups[(lang, typ)]
        real = [e[1] for e in ents if e[1] != today]
        newest = max(real) if real else today
        ents = [(u, newest if lm == today and real else lm, alts) for u, lm, alts in ents]   # Hubs: juengster Inhalt statt Baudatum
        ents.sort(key=lambda e: (e[1], e[0]), reverse=True)
        parts = [ents[i:i + MAX_URLS] for i in range(0, len(ents), MAX_URLS)] or [[]]
        for n, part in enumerate(parts):
            name = f"sitemap-{lang}-{typ}{'' if n == 0 else '-' + str(n + 1)}.xml"
            write(name, _xml(part, langs))
            files.append((name, max((e[1] for e in part), default=today), len(part)))
    idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for name, lm, _ in files:
        idx.append(f"<sitemap><loc>{base}/{name}</loc><lastmod>{lm}</lastmod></sitemap>")
    idx.append("</sitemapindex>")
    write("sitemap.xml", "\n".join(idx))
    return files
