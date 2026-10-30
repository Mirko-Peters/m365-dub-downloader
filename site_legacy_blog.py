"""Die frueheren Podpage-Blogbeitraege (data/podpage/blog_posts.json.gz) als Community-Beitraege von mirko-peters.
Sie werden von site_blog.build wie echte Community-Beitraege ausgegeben (URL /community/u/mirko-peters/blog/<slug>/, Autorenzeile, Verzeichnisse, RSS),
bleiben aber statisch (HTML mit Tabellen und Bildern bleibt vollstaendig erhalten; kein Datenbank-Eintrag, kein Laengenlimit des Wiki-Markups)."""
import ast, re, zlib
from datetime import datetime, timezone

import site_podpage as P
import site_sidebar as SBR

HANDLE, NAME = "mirko-peters", "Mirko Peters"


def _ts(s):
    try:
        return int(datetime.fromisoformat((s or "").replace("Z", "+00:00")).astimezone(timezone.utc).timestamp())
    except Exception:
        return 0


def _faq(raw):
    if isinstance(raw, str):
        try: raw = ast.literal_eval(raw)
        except Exception: return []
    out = []
    for q in raw or []:
        a = ((q.get("acceptedAnswer") or {}).get("text") or "").strip(); n = (q.get("name") or "").strip()
        if n and a: out.append({"q": n, "a": a})
    return out


def url_of(BASE, slug):
    return f"{BASE}/community/u/{HANDLE}/blog/{slug}/"


def items(BASE):
    posts = [p for p in P.load("blog_posts") if p.get("title") and p.get("html")]
    eslug = {e["slug"] for e in P.load("episodes") if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True")}
    bslug = {p["slug"] for p in posts}
    ix = SBR.Index()

    def fix(h):
        def rep(m):
            path = re.sub(r"^https?://(www\.)?m365\.fm", "", m.group(1))
            if not path.startswith("/") or path.startswith("//"): return m.group(0)
            seg = path.strip("/").split("#")[0]
            if seg in eslug: return f'href="{BASE}/show/episodes/{seg}/"'
            if seg.startswith("blog/") and seg[5:] in bslug: return f'href="{url_of(BASE, seg[5:])}"'
            if seg == "blog": return f'href="{BASE}/community/u/{HANDLE}/blog/"'
            return m.group(0)
        return re.sub(r'href="([^"]+)"', rep, h)

    out = []
    for p in sorted(posts, key=lambda x: x.get("iso") or "", reverse=True):
        html = fix(P.san(p["html"]))
        text = P.plain(html)
        topics = [e["id"] for e in ix.match(p["title"] + " " + text[:3000], k=6)]
        pub = _ts(p.get("iso")); upd = _ts(p.get("modified")) or pub
        out.append({"id": 900_000_000 + zlib.crc32(p["slug"].encode()) % 90_000_000, "handle": HANDLE, "name": NAME, "slug": p["slug"], "title": p["title"], "summary": (p.get("desc") or "")[:400],
                    "body": "", "html": html, "lang": "en", "topics": topics, "keypoints": [], "faq": _faq(p.get("faq")), "published": pub, "created": pub, "updated": upd, "votes": 0,
                    "coauthors": [], "legacy": True, "images": re.findall(r'<img[^>]+src="(https://[^"]+)"', html)})
    return out
