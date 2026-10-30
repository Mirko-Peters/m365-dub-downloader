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


def _fonts():
    import base64
    out = ""
    for w in (500, 600, 700):
        for sub, rg in (("latin", "U+0000-00FF,U+2000-206F,U+20AC"), ("latin-ext", "U+0100-02FF,U+1E00-1EFF")):
            f = DOCS / "assets" / "fonts" / f"barlow-condensed-{sub}-{w}-normal.woff2"
            if f.exists():
                out += (f"@font-face{{font-family:'Barlow Condensed';font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format('woff2');unicode-range:{rg}}}")
    return out


FONTS = ""


def card(item):
    global FONTS
    if not FONTS:
        FONTS = _fonts()
    """1200x630: Folgen-Cover im Seitendesign oben, darunter Absenderzeile. Seiten ohne Cover: Titel-Tafel im gleichen Stil."""
    d = "rtl" if item["lang"] in RTL else "ltr"
    t = html.escape(item["title"].replace(" | M365.FM", ""))
    if item.get("cover"):
        mid = f'<div style="position:absolute;left:0;top:0;width:1200px;height:420px">{item["cover"]}</div>'
        foot_top = 420
        size_note = ""
    else:
        size = 78 if len(t) < 40 else 62 if len(t) < 70 else 50
        mid = (f'<div style="position:absolute;left:64px;right:64px;top:70px;color:#82a7d4;font:600 24px/1 \'Barlow Condensed\',sans-serif;letter-spacing:5px">M365.FM · {html.escape(NAMES.get(item["lang"], "").upper())}</div>'
               f'<h1 style="position:absolute;left:64px;right:64px;top:130px;margin:0;font:700 {size}px/1.04 \'Barlow Condensed\',\'Noto Sans\',sans-serif;text-transform:uppercase;color:#eef0f3">{t}</h1>')
        foot_top = 420
    return f"""<!doctype html><meta charset=utf-8><style>{FONTS}
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{position:relative;background:#1d2126;color:#eef0f3;font-family:'Barlow Condensed','Noto Sans','DejaVu Sans',sans-serif}}
body:before{{content:"";position:absolute;inset:0;background-image:linear-gradient(#e9ecef0d 1px,transparent 1px),linear-gradient(90deg,#e9ecef0d 1px,transparent 1px);background-size:40px 40px}}
.f{{position:absolute;left:0;right:0;top:{foot_top}px;bottom:0;border-top:1px solid #e9ecef33;background:#16191c;display:flex;align-items:center;justify-content:space-between;padding:0 64px}}
.b{{font:700 46px/1 'Barlow Condensed',sans-serif;letter-spacing:2px;text-transform:uppercase}}.b i{{color:#82a7d4;font-style:normal}}
.s{{font:600 26px/1.3 'Barlow Condensed',sans-serif;letter-spacing:3px;text-transform:uppercase;color:#98a0ab;text-align:right}}
</style><body dir="{d}">{mid}<div class=f><div class=b>M365<i>.</i>FM <span style="color:#82a7d4;font-size:30px;letter-spacing:4px">DUB</span></div><div class=s>Mirko Peters · Microsoft MVP<br>dub.m365.fm</div></div></body>"""


CARD_VERSION = 1   # bei Aenderungen am Kartenlayout erhoehen, dann werden alle Bilder neu gezeichnet


def main():
    mf = DOCS / "og-manifest.json"
    if not mf.exists():
        return
    items = json.load(open(mf, encoding="utf-8"))
    default = DOCS / "assets" / "og-default.png"
    ok = reused = 0
    cache = Path(__file__).parent / ".ogcache"   # Bilder aus frueheren Laeufen (Workflow-Cache), Schluessel = Hash der Karteninhalte
    cache.mkdir(exist_ok=True)
    key = lambda it: hashlib.sha1(json.dumps([it, CARD_VERSION], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    todo = []
    for it in items:
        out = DOCS / it["path"]; hit = cache / (key(it) + ".png")
        out.parent.mkdir(parents=True, exist_ok=True)
        if hit.exists():
            shutil.copy(hit, out); reused += 1
        else:
            todo.append(it)
    live = {key(it) + ".png" for it in items}
    for f in cache.glob("*.png"):   # Bilder zu nicht mehr vorhandenen Seiten verwerfen, damit der Cache klein bleibt
        if f.name not in live:
            f.unlink()
    print(reused, "Bilder aus dem Cache,", len(todo), "neu zu zeichnen")
    try:
        if not todo:
            raise StopIteration
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={"width": 1200, "height": 630})
            for it in todo:
                out = DOCS / it["path"]
                try:
                    pg.set_content(card(it))
                    pg.screenshot(path=str(out))
                    shutil.copy(out, cache / (key(it) + ".png"))
                    ok += 1
                except Exception as e:
                    print("OG Fehler", it["path"], str(e)[:80])
            br.close()
    except StopIteration:
        pass
    except Exception as e:
        print("Playwright nicht verfügbar:", str(e)[:120])
    for it in items:  # Fallback
        out = DOCS / it["path"]
        if not out.exists() and default.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(default, out)
    print(ok + reused, "von", len(items), "Teilen-Bildern bereit")


if __name__ == "__main__":
    main()
