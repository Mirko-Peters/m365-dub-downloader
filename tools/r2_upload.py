#!/usr/bin/env python3
"""Fremde Bilder (Blog, Gaeste) in den R2-Bucket kopieren und eine Zuordnung schreiben.

Standard ist ein Testlauf (zaehlt nur). Mit --apply wird geladen/hochgeladen und
data/r2_map.json geschrieben (Original-URL -> https://img.m365.fm/<key>).
Zugang ueber R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY.
"""
import gzip, hashlib, io, json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "data" / "r2_map.json"
PUBLIC = "https://img.m365.fm"
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp", "image/svg+xml": ".svg", "image/avif": ".avif",
       "application/pdf": ".pdf"}   # PDFs: Podpage-Downloads (Archiv vor der Kuendigung)
HOSTS = ("statics.mylandingpages.co", "roundups-inarticle-public.s3", "m.media-amazon.com", "img.podpage.com",
         "blogifyai.s3", "rank-ai-generated-images.s3", "images.pexels.com", "s3.us-west-1.amazonaws.com/redwood-labs",
         "neuroncdn", "media.podpage.com", "redwood-labs.s3.amazonaws.com")   # Podpage-Speicher: Gastfotos, Cover, Downloads (T32)
URL_RX = re.compile(r'https?://[^\s"\'<>)\\]+')
# T32 Podpage-Abloesung: alles, was auf Podpage-Speicher liegt, vor der Kuendigung kopieren (auch nur archivierte Dateien)
PODPAGE_SOURCES = ["data/podpage/episodes.json.gz", "data/podpage/hosts.json", "data/podpage/sponsors.json", "data/podpage/podcast.json",
                   "data/podpage/downloadable_files.json", "data/podpage/pages.json"]


def urls():
    found = set()
    for b in json.load(gzip.open(ROOT / "data/podpage/blog_posts.json.gz")):
        found |= set(re.findall(r'https?://[^\s"\'<>)]+', b.get("html") or ""))
    for g in json.load(open(ROOT / "data/podpage/guests.json", encoding="utf-8")):
        found.add(g.get("image_path") or "")
    for rel in PODPAGE_SOURCES + sorted(str(x.relative_to(ROOT)) for x in (ROOT / "data/podpage_i18n").glob("notes_*.json")):
        f = ROOT / rel
        if f.exists():
            found |= set(URL_RX.findall(gzip.open(f, "rt", encoding="utf-8").read() if f.suffix == ".gz" else f.read_text("utf-8")))
    found = {u.rstrip(".,;") for u in found}
    return sorted(u for u in found if u.startswith("http") and any(h in u for h in HOSTS)
                  and (re.search(r"\.(jpe?g|jfif|png|gif|webp|svg|avif|pdf)(\?|$)", u, re.I) or "redwood-labs" in u or "neuroncdn" in u))


def main():
    apply = "--apply" in sys.argv
    todo = urls()
    done = json.load(open(MAP, encoding="utf-8")) if MAP.exists() else {}
    todo = [u for u in todo if u not in done]
    print(f"{len(todo)} Bilder offen, {len(done)} schon in R2")
    if not apply:
        for u in todo[:10]:
            print("  ", u[:110])
        print("Testlauf, nichts hochgeladen. Mit --apply ausfuehren.")
        return
    import boto3
    s3 = boto3.client("s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"], aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
    bucket = os.environ["R2_BUCKET"]
    failed = []

    def one(u):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (m365.fm image copy)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data, ct = r.read(), r.headers.get_content_type()
            if ct not in EXT or len(data) < 100 or len(data) > 15_000_000:
                raise ValueError(f"kein Bild ({ct}, {len(data)} Byte)")
            if ct in ("image/jpeg", "image/png"):   # als WebP speichern, wenn es kleiner wird
                try:
                    im = Image.open(io.BytesIO(data))
                    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                    buf = io.BytesIO()
                    im.save(buf, "WEBP", quality=82, method=6)
                    if len(buf.getvalue()) < len(data):
                        data, ct = buf.getvalue(), "image/webp"
                except Exception:
                    pass
            key = "i/" + hashlib.sha1(u.encode()).hexdigest()[:20] + EXT[ct]
            s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=ct, CacheControl="public, max-age=31536000, immutable")
            done[u] = f"{PUBLIC}/{key}"
        except Exception as e:
            failed.append((u, str(e)[:80]))

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, todo))
    MAP.write_text(json.dumps(dict(sorted(done.items())), indent=0, ensure_ascii=False), encoding="utf-8")
    print(f"{len(todo) - len(failed)} hochgeladen, {len(failed)} fehlgeschlagen (bleiben beim Original)")
    for u, e in failed[:20]:
        print("  FEHLER", u[:90], e)


if __name__ == "__main__":
    main()
