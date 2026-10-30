#!/usr/bin/env python3
"""Prueft das JSON-LD aller gebauten Seiten (docs/): gueltiges JSON, Pflichtfelder je Typ (Google/schema.org), absolute URLs, ISO-Daten,
aufloesbare @id-Verweise, widerspruechliche @id-Definitionen."""
import glob, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

DOCS = Path(__file__).parent / "docs"
REQ = {
    "PodcastEpisode": ["name", "url", "datePublished", "partOfSeries"],
    "PodcastSeries": ["name", "url"],
    "VideoObject": ["name", "description", "thumbnailUrl", "uploadDate"],
    "Article": ["headline", "datePublished", "author", "image"],
    "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"],
    "Person": ["name"], "Organization": ["name", "url"], "CollectionPage": ["name", "url"],
    "ProfilePage": ["mainEntity"], "Event": ["name", "startDate", "location"], "WebSite": ["name", "url"],
}
iso = re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:.+\-Z]+)?$")
errs, warns = Counter(), Counter()
examples = {}
ids = defaultdict(set)
defs = defaultdict(set)


def note(kind, msg, f):
    (errs if kind == "E" else warns)[msg] += 1
    examples.setdefault(msg, f)


def walk(o, f, top):
    if isinstance(o, dict):
        t = o.get("@type")
        for tt in (t if isinstance(t, list) else [t]):
            if tt in REQ:
                for k in REQ[tt]:
                    v = o.get(k)
                    if v in (None, "", [], {}):
                        note("E" if tt != "Article" or k != "image" else "W", f"{tt}: Pflichtfeld '{k}' fehlt", f)
            if tt == "Question" and not (o.get("acceptedAnswer") or {}).get("text"):
                note("E", "Question ohne acceptedAnswer.text", f)
        for k in ("url", "item", "contentUrl", "embedUrl", "mainEntityOfPage"):
            v = o.get(k)
            if isinstance(v, str) and not v.startswith("http"):
                note("E", f"{k} nicht absolut", f)
        for k in ("datePublished", "dateModified", "uploadDate", "startDate", "endDate"):
            v = o.get(k)
            if isinstance(v, str) and not iso.match(v):
                note("E", f"{k} kein ISO-Datum: {v[:20]}", f)
        if "@id" in o:
            ids[o["@id"]].add(f)
            if len(o) > 1:
                defs[o["@id"]].add(json.dumps(o, sort_keys=True))
        for v in o.values():
            walk(v, f, False)
    elif isinstance(o, list):
        for v in o:
            walk(v, f, False)


n = 0
for p in sorted(glob.glob(str(DOCS / "**" / "*.html"), recursive=True)):
    h = open(p, encoding="utf-8", errors="ignore").read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    if not blocks:
        continue
    n += 1
    f = p.replace(str(DOCS), "")
    for b in blocks:
        try:
            walk(json.loads(b), f, True)
        except Exception as ex:
            note("E", "JSON-LD nicht parsebar: " + str(ex)[:60], f)
# @id-Verweise (nur {"@id": x}) muessen irgendwo definiert sein
refs = set()
for p in glob.glob(str(DOCS / "**" / "*.html"), recursive=True)[:2000]:
    h = open(p, encoding="utf-8", errors="ignore").read()
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        for m in re.findall(r'\{"@id": "([^"]+)"\}', b):
            if m.split("#")[0].startswith("http") and m not in defs and not m.endswith("#video"):
                refs.add(m)
for r in sorted(refs)[:10]:
    note("W", "@id referenziert, aber nirgends definiert: " + r.replace("https://www.m365.fm", ""), "")
for i, d in defs.items():
    if len(d) > 1 and any(k in i for k in ("#person", "#org")):
        note("W", f"{i.replace('https://www.m365.fm', '')} in {len(d)} Varianten definiert", "")
print(f"{n} Seiten mit JSON-LD geprueft")
for k, v in errs.most_common():
    print("FEHLER", v, "x", k, "z.B.", examples[k])
for k, v in warns.most_common():
    print("HINWEIS", v, "x", k, "z.B.", examples[k])
sys.exit(1 if errs else 0)
