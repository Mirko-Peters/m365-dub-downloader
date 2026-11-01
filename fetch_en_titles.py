"""Holt die englischen Original-Titel der YouTube-Videos (oEmbed, ohne API-Schluessel) -> data/en_titles.json {video-id: titel}."""
import json, glob, os, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent; f = ROOT / "data" / "en_titles.json"
import sys; sys.path.insert(0, str(ROOT)); from site_text import demojibake
have = json.loads(f.read_text("utf-8")) if f.exists() else {}
for p in glob.glob(str(ROOT / "episodes" / "*.json")):
    vid = os.path.basename(p)[:-5]
    if vid in have: continue
    try:
        u = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}")
        have[vid] = demojibake(json.loads(urllib.request.urlopen(u, timeout=30).read())["title"])   # T5: YouTube liefert gelegentlich CP850-Mojibake
    except Exception as e:
        print("kein Titel:", vid, str(e)[:80])
f.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8"); print(len(have), "Titel")
