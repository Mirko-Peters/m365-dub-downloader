#!/usr/bin/env python3
"""Holt die Spotify-Folgenlinks aller Sprach-Shows von den öffentlichen Show-Seiten (ohne API/Premium)
und ergänzt data/spotify_links.json ({"<VIDEO>:<lang>": url}). Läuft im GitHub-Workflow; bei Fehlern bleibt der bisherige Stand."""
import glob, json, re
from pathlib import Path

ROOT = Path(__file__).parent


def norm(t): return re.sub(r"[\W_]+", "", (t or "").casefold())


def main():
    from playwright.sync_api import sync_playwright
    plat = json.load(open(ROOT / "data" / "platforms.json", encoding="utf-8"))
    fp = ROOT / "data" / "spotify_links.json"
    links = json.load(open(fp, encoding="utf-8")) if fp.exists() else {}
    titles = {}
    for p in glob.glob(str(ROOT / "episodes" / "*.json")):
        vid = Path(p).stem
        for l, e in json.load(open(p, encoding="utf-8")).items():
            titles.setdefault(l, {})[norm(e["title"])] = vid
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(locale="en-US")
        for l, ids in plat.items():
            sid = ids.get("spotify_id")
            if not sid:
                continue
            try:
                pg = ctx.new_page()
                pg.goto(f"https://open.spotify.com/show/{sid}", wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_selector('a[href*="/episode/"]', timeout=30000)
                found = {}
                for _ in range(40):
                    for a in pg.query_selector_all('a[href*="/episode/"]'):
                        href = (a.get_attribute("href") or "").split("?")[0]
                        txt = (a.inner_text() or "").strip()
                        if "/episode/" in href and txt:
                            found[href.rsplit("/", 1)[1]] = txt
                    btn = pg.query_selector('button:has-text("Load more episodes")')
                    if not btn:
                        break
                    btn.click()
                    pg.wait_for_timeout(1500)
                n = 0
                for eid, txt in found.items():
                    vid = titles.get(l, {}).get(norm(txt))
                    if vid:
                        links[f"{vid}:{l}"] = f"https://open.spotify.com/episode/{eid}"
                        n += 1
                print(l, len(found), "Spotify-Folgen,", n, "zugeordnet")
                pg.close()
            except Exception as e:
                print("Spotify", l, "Fehler:", str(e)[:120])
        br.close()
    json.dump(links, open(fp, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(len(links), "Links gesamt")


if __name__ == "__main__":
    main()
