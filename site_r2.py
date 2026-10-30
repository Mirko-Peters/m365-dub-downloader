"""Bild-URLs auf den eigenen R2-Bucket (img.m365.fm) umschreiben, soweit data/r2_map.json sie kennt."""
import json
import re
from pathlib import Path

_F = Path(__file__).parent / "data" / "r2_map.json"
MAP = json.loads(_F.read_text(encoding="utf-8")) if _F.exists() else {}
_RX = re.compile("|".join(re.escape(u) for u in sorted(MAP, key=len, reverse=True))) if MAP else None


def rewrite(html):
    return _RX.sub(lambda m: MAP[m.group(0)], html) if _RX and "http" in html else html
