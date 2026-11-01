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


R2OUT = ROOT / "r2out"   # uebersetzte Seiten liegen im R2-Bucket (Paket 20), der Site-Worker liefert sie unter derselben Adresse aus
_RD = DOCS / "show" / "redirects.json"
REDIR = __import__("json").loads(_RD.read_text("utf-8")) if _RD.exists() else {}   # alte Podpage-Adressen -> Ziel (301 im Site-Worker)
_LEP = re.compile(r"^/(de|es|fr|it|pt|nl|pl|id|ru|uk|ar|he|ja|ko)/show/episodes/([a-z0-9-]+)/?$")


def _exists(path):
    """Gibt es die Adresse so, wie der Site-Worker sie ausliefert? GitHub Pages, R2, Weiterleitungstabelle oder englisches Original."""
    for base in (DOCS, R2OUT):
        q = base / path.lstrip("/")
        if (q / "index.html").exists() if (path.endswith("/") or q.is_dir()) else q.exists(): return True
    p0 = path.rstrip("/") or "/"
    to = REDIR.get(p0) or REDIR.get(p0.lower())
    if to and to.rstrip("/") != p0: return _exists(to)
    m = _LEP.match(path)
    if m: return (DOCS / "show" / "episodes" / m.group(2) / "index.html").exists()
    return False


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
            u = urlparse(m.group(1)); pth = unquote(u.path or rel) if u.scheme in ("http", "https", "") else ""
            if pth and _exists(pth): continue   # per R2 oder 301 erreichbar
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
