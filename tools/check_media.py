"""Bilder- und Textlaenge je Seitenart pruefen (nach generate_site.py): Titelbild, mindestens 3 Bilder, Textlaenge.
Aufruf: python tools/check_media.py [--list]   (--list gibt die Seiten ohne Titelbild aus)"""
import collections, re, statistics, sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "docs"


def kind(rel):
    p = rel.parts
    if p and len(p[0]) <= 3 and len(p) > 1:
        p = p[1:]
    if not p: return "start"
    if p[0] == "show": return "show/" + (p[1] if len(p) > 2 else "")
    if p[0] in ("community",): return "community/" + (p[1] if len(p) > 2 else "")
    return p[0] if len(p) > 1 else "seite"


def main():
    rows = collections.defaultdict(list)
    for f in D.rglob("index.html"):
        h = f.read_text(encoding="utf-8", errors="ignore")
        if "noindex" in h[:4000]:
            continue
        m = re.search(r"<main.*?</main>", h, re.S)
        body = m.group(0) if m else h
        txt = len(re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", body, flags=re.S)).strip())
        imgs = len(re.findall(r"<img\b", body)) + len(re.findall(r'<svg[^>]*role="img"', body)) + len(re.findall(r"<iframe[^>]*youtube", body))
        first = re.search(r"<(img|svg|iframe)\b", body)
        h1 = body.find("<h1")
        hero = bool(first and (h1 < 0 or first.start() < h1 + 1500))
        rows[kind(f.parent.relative_to(D))].append((txt, imgs, hero, str(f.parent.relative_to(D))))
    print(f"{'Art':28}{'Seiten':>7}{'Median Text':>12}{'<2500':>7}{'ohne Titelbild':>15}{'<3 Bilder':>10}")
    for k, v in sorted(rows.items(), key=lambda x: -len(x[1])):
        if len(v) < 3: continue
        print(f"{k:28}{len(v):7}{int(statistics.median(x[0] for x in v)):12}{sum(x[0] < 2500 for x in v):7}{sum(not x[2] for x in v):15}{sum(x[1] < 3 for x in v):10}")
        if "--list" in sys.argv:
            for x in v:
                if not x[2]: print("    ohne Titelbild:", x[3])


main()
