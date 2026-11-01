"""Holt alle Blogposts von www.m365.fm (Podpage) -> data/podpage/blog_posts.json.gz
(Titel, Datum, Beschreibung, Inhalts-HTML, interne Links, JSON-LD BlogPosting/FAQ). Nur oeffentliche Seiten."""
import gzip, json, re, sys, time, concurrent.futures as cf, requests
from bs4 import BeautifulSoup
B = "https://www.m365.fm"; S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0 (m365.fm migration)"
OUT = "data/podpage/blog_posts.json.gz"
def get(u, n=3):
    for i in range(n):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 200: return r.text
            if r.status_code == 404: return None
        except Exception: pass
        time.sleep(2 * (i + 1))
    return None
def one(url):
    h = get(url)
    if not h: return {"url": url, "error": True}
    d = BeautifulSoup(h, "html.parser"); h1 = d.find("h1")
    if not h1: return {"url": url, "error": True}
    sec = h1.find_parent("section"); bp = faq = None
    for s in d.find_all("script", type="application/ld+json"):
        try: g = json.loads(s.string or "{}").get("@graph", [])
        except Exception: continue
        for x in g:
            if x.get("@type") == "BlogPosting": bp = x
            if x.get("@type") == "FAQPage": faq = x
    date = h1.find_previous(string=re.compile(r"\w+\.? \d{1,2}, \d{4}"))
    body = None
    for sib in h1.find_next_siblings():
        if sib.name == "div" and sib.find("p"): body = sib; break
    links = sorted({a["href"] for a in (sec or d).find_all("a", href=True) if a["href"].startswith(("/", B)) and "#" not in a["href"]})
    cat = [a.get_text(" ", strip=True) for a in (sec or d).find_all("a", href=re.compile(r"blog/\?|categor"))][:5]
    for t in (body.find_all(["script", "style", "form", "button"]) if body else []): t.decompose()
    return {"url": url, "slug": url.rstrip("/").split("/")[-1], "title": h1.get_text(" ", strip=True), "date": (date or "").strip(),
            "iso": (bp or {}).get("datePublished"), "modified": (bp or {}).get("dateModified"), "desc": (d.find("meta", attrs={"name": "description"}) or {}).get("content", ""),
            "words": (bp or {}).get("wordCount"), "html": str(body) if body else "", "links": links, "cats": cat, "faq": (faq or {}).get("mainEntity", [])}
def main():
    sm = get(B + "/sitemap.xml") or ""
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if "/blog/" in u and u.rstrip("/") != B + "/blog"]
    lim = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].strip() else 0
    if lim: urls = urls[:lim]
    old = {}
    try: old = {p["url"]: p for p in json.load(gzip.open(OUT, "rt", encoding="utf-8")) if not p.get("error")}
    except Exception: pass
    todo = [u for u in urls if u not in old]; print(len(urls), "URLs,", len(todo), "neu", flush=True)
    res = dict(old)
    with cf.ThreadPoolExecutor(6) as ex:
        for i, r in enumerate(ex.map(one, todo)):
            if not r.get("error"): res[r["url"]] = r
            if i % 200 == 0: print(i, flush=True)
    out = [res[u] for u in urls if u in res]; print("gespeichert:", len(out), "fehlend:", len(urls) - len(out))
    out += [p for u, p in old.items() if u not in set(urls)]   # T32: Beitraege der Sicherung, die die Sitemap nicht (mehr) nennt, bleiben erhalten
    if len(out) < len(old):   # nie verkleinern (www.m365.fm ist nicht mehr Podpage, die Sitemap ist ein Index)
        print(f"ABBRUCH: {len(out)} < {len(old)} Beitraege in der Sicherung - nichts geschrieben"); sys.exit(1)
    with gzip.open(OUT, "wt", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False)
main()
