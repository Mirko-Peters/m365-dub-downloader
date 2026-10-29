#!/usr/bin/env python3
"""Erzeugt pro Seite ein Teilen-Bild (Open Graph, 1200x630 PNG) aus docs/og-manifest.json mit Chromium (Playwright).
Schlägt etwas fehl, wird das Standardbild kopiert, damit og:image nie ins Leere zeigt."""
import hashlib, html, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
NAMES = {"de": "Deutsch", "es": "Español", "fr": "Français", "it": "Italiano", "pt": "Português", "nl": "Nederlands", "pl": "Polski", "id": "Bahasa Indonesia",
         "ru": "Русский", "uk": "Українська", "ar": "العربية", "he": "עברית", "hi": "हिन्दी", "ja": "日本語", "ko": "한국어", "ml": "മലയാളം", "pa": "ਪੰਜਾਬੀ",
         "ta": "தமிழ்", "te": "తెలుగు", "en": "International"}
RTL = {"ar", "he"}


def card(item):
    h = int(hashlib.md5(item["seed"].encode()).hexdigest(), 16)
    h1 = h % 360
    h2 = (h1 + 35 + (h >> 9) % 70) % 360
    bars, x, hh = "", 60, h
    for _ in range(44):
        hh = (hh * 1103515245 + 12345) & 0x7fffffff
        v = 40 + (hh >> 8) % 150
        bars += f'<i style="left:{x}px;height:{v}px;bottom:150px;background:hsl({h1 + 18},85%,72%);opacity:{0.25 + v / 700:.2f}"></i>'
        x += 25
    t = item["title"].replace(" | M365.FM", "")
    size = 64 if len(t) < 60 else 54 if len(t) < 90 else 46
    d = "rtl" if item["lang"] in RTL else "ltr"
    return f"""<!doctype html><meta charset=utf-8><style>
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{position:relative;background:linear-gradient(135deg,hsl({h1},55%,24%),hsl({h2},60%,10%));color:#f6f1ea;font-family:'Noto Serif','Noto Sans','DejaVu Serif',serif}}
i{{position:absolute;width:14px;border-radius:7px}}
.k{{position:absolute;top:52px;left:60px;right:60px;font:600 24px/1 'Noto Sans','DejaVu Sans',sans-serif;letter-spacing:5px;opacity:.85}}
.dot{{position:absolute;top:44px;right:60px;width:30px;height:30px;border-radius:50%;background:#b4233c}}
h1{{position:absolute;left:60px;right:60px;top:120px;margin:0;font-size:{size}px;line-height:1.18;font-weight:700;text-shadow:0 2px 18px #0008}}
.f{{position:absolute;left:60px;right:60px;bottom:44px;font:500 24px/1 'Noto Sans','DejaVu Sans',sans-serif;display:flex;justify-content:space-between;opacity:.9}}
</style><body dir="{d}">{bars}<div class=dot></div><div class=k>M365.FM · {html.escape(NAMES.get(item['lang'], '').upper())}</div>
<h1>{html.escape(t)}</h1><div class=f><span>Mirko Peters · Microsoft MVP</span><span>dub.m365.fm</span></div></body>"""


def main():
    mf = DOCS / "og-manifest.json"
    if not mf.exists():
        return
    items = json.load(open(mf, encoding="utf-8"))
    default = DOCS / "assets" / "og-default.png"
    ok = 0
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={"width": 1200, "height": 630})
            for it in items:
                out = DOCS / it["path"]
                out.parent.mkdir(parents=True, exist_ok=True)
                try:
                    pg.set_content(card(it))
                    pg.screenshot(path=str(out))
                    ok += 1
                except Exception as e:
                    print("OG Fehler", it["path"], str(e)[:80])
            br.close()
    except Exception as e:
        print("Playwright nicht verfügbar:", str(e)[:120])
    for it in items:  # Fallback
        out = DOCS / it["path"]
        if not out.exists() and default.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(default, out)
    print(ok, "von", len(items), "Teilen-Bildern erzeugt")


if __name__ == "__main__":
    main()
