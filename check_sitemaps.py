#!/usr/bin/env python3
"""Prueft die gebauten Sitemaps (docs/sitemap.xml und die darin genannten Dateien): wohlgeformtes XML, jede Datei <= 50.000 URLs und
<= 50 MB, loc absolut auf der eigenen Domain, lastmod als Datum, keine doppelten URLs ueber alle Dateien, hreflang-Alternates mit
x-default, Index verweist nur auf vorhandene Dateien. Exit 1 bei Fehlern (blockierend im Seitenbau)."""
import re, sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
BASE = "https://" + ((ROOT / "domain.txt").read_text().strip() if (ROOT / "domain.txt").exists() else "www.m365.fm")
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(T[0-9:+\-Z.]+)?$")


def main():
    errs, seen, total = [], {}, 0
    idx = DOCS / "sitemap.xml"
    if not idx.exists():
        print("docs/sitemap.xml fehlt"); return 1
    try:
        root = ET.parse(idx).getroot()
    except ET.ParseError as e:
        print("sitemap.xml nicht wohlgeformt:", e); return 1
    files = [el.text.strip() for el in root.findall("s:sitemap/s:loc", NS)]
    if not files: errs.append("Index ohne Einträge")
    for loc in files:
        if not loc.startswith(BASE + "/"): errs.append(f"Index: fremde URL {loc}")
        f = DOCS / loc[len(BASE) + 1:]
        if not f.exists(): errs.append(f"Index verweist auf fehlende Datei {f.name}"); continue
        if f.stat().st_size > 50 * 1024 * 1024: errs.append(f"{f.name}: größer als 50 MB")
        try:
            r = ET.parse(f).getroot()
        except ET.ParseError as e:
            errs.append(f"{f.name}: nicht wohlgeformt ({e})"); continue
        urls = r.findall("s:url", NS)
        if len(urls) > 50000: errs.append(f"{f.name}: {len(urls)} URLs (> 50.000)")
        total += len(urls)
        for u in urls:
            loc_el, lm = u.find("s:loc", NS), u.find("s:lastmod", NS)
            l = (loc_el.text or "").strip() if loc_el is not None else ""
            if not l.startswith(BASE + "/") and l != BASE + "/": errs.append(f"{f.name}: loc nicht absolut/eigene Domain: {l[:80]}")
            if lm is None or not DATE.match((lm.text or "").strip()): errs.append(f"{f.name}: lastmod fehlt/ungültig bei {l[:80]}")
            if l in seen: errs.append(f"doppelt: {l[:80]} in {seen[l]} und {f.name}")
            seen[l] = f.name
            alts = u.findall("x:link", NS)
            if alts and not any(a.get("hreflang") == "x-default" for a in alts): errs.append(f"{f.name}: Alternates ohne x-default bei {l[:80]}")
    for e in errs[:40]: print("FEHLER", e)
    print(f"{len(files)} Sitemap-Dateien, {total} URLs, {len(errs)} Fehler")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
