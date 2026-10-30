"""Bewertungen einsammeln: Apple Podcasts (RSS je Land) + Podpage-Sicherung -> data/reviews_ext.json (fuer die statische Bewertungsseite)."""
import json, os, re, requests
ID = (json.load(open("data/platforms.json")).get("en", {}).get("apple_id") or "1810175174")
CC = "us gb de ca au ie in nz za sg fr es it nl se no dk fi at ch be pl pt br mx jp kr ae sa il tr ru ua id my ph th hk tw ng ke".split()
out = {}
def add(src, cc, author, rating, title, body, date, url=""):
    k = re.sub(r"\W+", "", (author + title + body)[:60]).lower()
    if k and k not in out and 1 <= int(rating) <= 5: out[k] = {"source": src, "country": cc, "author": author, "rating": int(rating), "title": title, "body": body, "date": date[:10], "url": url}
for p in json.load(open("data/podpage/reviews.json")):
    if str(p.get("hidden")) == "True": continue
    add("Apple Podcasts" if p.get("source") == "A" else "Website", p.get("country") or "", p.get("author_name") or "Listener", p.get("rating") or 0, p.get("title") or "", p.get("review") or "", p.get("published") or "", p.get("review_url") or "")
for cc in CC:
    for page in (1, 2):
        try:
            r = requests.get(f"https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={ID}/sortby=mostrecent/json", timeout=30)
            if r.status_code != 200: break
            ent = r.json().get("feed", {}).get("entry") or []
            if isinstance(ent, dict): ent = [ent]
            for e in ent:
                if "im:rating" not in e: continue
                add("Apple Podcasts", cc, e["author"]["name"]["label"], e["im:rating"]["label"], e["title"]["label"], e["content"]["label"], e["updated"]["label"], e["author"].get("uri", {}).get("label", ""))
            if len(ent) < 40: break
        except Exception: break
res = sorted(out.values(), key=lambda x: x["date"], reverse=True)
if res: json.dump(res, open("data/reviews_ext.json", "w"), ensure_ascii=False, indent=1)
print(len(res), "Bewertungen", sum(r["rating"] for r in res) / max(1, len(res)))
