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


PER = 100


def publish(write, BASE):
    """Dateien fuer den Worker (worker/src/legacyblog.js): SITE/blog-import/index.json und part-N.json. Nur solange data/blog_import.json "enabled": true ist."""
    import json
import site_r2 as R2
    from pathlib import Path
    cfg = Path(__file__).parent / "data" / "blog_import.json"
    if not cfg.exists() or not json.loads(cfg.read_text("utf-8")).get("enabled"):
        return 0
    its = items(BASE)
    rows = [{"slug": p["slug"], "title": p["title"], "summary": p["summary"], "html": p["html"], "topics": p["topics"], "faq": p["faq"], "published": p["published"], "updated": p["updated"]} for p in its]
    for i in range(0, len(rows), PER):
        write(f"blog-import/part-{i // PER + 1}.json", R2.rewrite(json.dumps(rows[i:i + PER], ensure_ascii=False, separators=(",", ":"))))
    write("blog-import/index.json", json.dumps({"total": len(rows), "per": PER}))
    return len(rows)
