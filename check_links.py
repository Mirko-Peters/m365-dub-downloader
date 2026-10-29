#!/usr/bin/env python3
"""Prüft die gebaute Seite (docs/): kaputte interne Links, Sprachtreue der Verlinkung in Artikeln, verwaiste Folgenseiten, Artikel ohne interne Links.
Aufruf: python check_links.py   (Exit-Code 1 bei kaputten Links)"""
import re, sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
dom = (ROOT / "domain.txt").read_text().strip() if (ROOT / "domain.txt").exists() else ""
HOSTS = {dom} if dom else set()


def target(href, cur):
    u = urlparse(href)
    if u.scheme in ("http", "https"):
        if u.netloc not in HOSTS:
            return None
        path = u.path
    elif u.scheme or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    else:
        path = u.path or cur
    path = unquote(path)
    p = DOCS / path.lstrip("/")
    return p / "index.html" if (path.endswith("/") or p.is_dir()) else p


pages = list(DOCS.rglob("index.html"))
broken, inbound, ep_links, wrong_lang = [], {}, {}, []
for p in pages:
    rel = "/" + str(p.relative_to(DOCS).parent).replace("\\", "/") + "/"
    html = p.read_text(encoding="utf-8")
    lang = rel.strip("/").split("/")[0]
    for m in re.finditer(r'<a [^>]*href="([^"]+)"', html):
        t = target(m.group(1), rel)
        if t is None:
            continue
        if not t.exists():
            broken.append((rel, m.group(1)))
        else:
            inbound[t] = inbound.get(t, 0) + 1
    for m in re.finditer(r'class="ilink" href="([^"]+)"', html):  # automatische Artikel-Links
        ep_links[rel] = ep_links.get(rel, 0) + 1
        if urlparse(m.group(1)).path.strip("/").split("/")[0] != lang:
            wrong_lang.append((rel, m.group(1)))

eps = [p for p in pages if len(p.relative_to(DOCS).parts) == 3 and p.relative_to(DOCS).parts[1] not in ("c", "tag")]
orph = [str(p.parent.relative_to(DOCS)) for p in eps if inbound.get(p, 0) < 2]
art = [str(p.parent.relative_to(DOCS)) for p in eps if "class=article" in p.read_text(encoding="utf-8")]
no_ilink = [a for a in art if ep_links.get("/" + a + "/", 0) == 0]
print(f"{len(pages)} Seiten geprüft | kaputte interne Links: {len(broken)} | Links in Artikeln in falscher Sprache: {len(wrong_lang)}")
print(f"Folgenseiten: {len(eps)} | mit <2 eingehenden Links: {len(orph)} | Artikel: {len(art)} | Artikel ohne automatische interne Links: {len(no_ilink)}")
for b in broken[:15]:
    print("  KAPUTT", b)
for w in wrong_lang[:10]:
    print("  FALSCHE SPRACHE", w)
sys.exit(1 if broken or wrong_lang else 0)
