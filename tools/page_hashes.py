"""Hash je ausgelieferter Datei (docs/): Grundlage, um nach dem Deploy nur geaenderte Adressen im Cloudflare-Cache zu leeren und bei IndexNow zu melden.
Aufruf: python tools/page_hashes.py docs page-hashes.json"""
import hashlib, json, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
h = {}
for f in src.rglob("*"):
    if f.is_file() and f.suffix in (".html", ".xml", ".json", ".txt", ".jsonld", ".md", ".css", ".js"):
        rel = f.relative_to(src).as_posix()
        url = "/" + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)
        h[url] = hashlib.sha1(f.read_bytes()).hexdigest()[:16]
out.write_text(json.dumps(h, sort_keys=True), encoding="utf-8")
print(len(h), "Dateien gehasht")
