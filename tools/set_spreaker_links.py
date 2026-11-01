"""T36 (Mirko, 1.11.): Bei jeder veroeffentlichten Spreaker-Folge (Hauptshow und 14 Sprach-Shows) zeigt das Feld "Website"
(API: episode_link, im RSS <link>) auf die eigene Episodenseite auf m365.fm - kanonisch, ohne UTM.

Ablauf je Folge: Ziel aus https://www.m365.fm/spreaker-pages.json (vom Seitenbau), Ziel muss mit 200 antworten (ohne
Weiterleitung), aktuellen Wert lesen, nur veroeffentlichte Folgen (keine Entwuerfe, nichts Geplantes), alten Wert im Protokoll
sichern, setzen, nachlesen. Protokoll: data/spreaker_links.tsv (Zeit, Folge, Status, alt, neu, Hinweis), letzter Eintrag zaehlt.
Aufruf: python tools/set_spreaker_links.py [--limit N] [--ids 1,2] [--dry-run]"""
import argparse, json, re, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_shownotes as A

ROOT = A.ROOT
LOG = ROOT / "data" / "spreaker_links.tsv"
MAP_URL = "https://www.m365.fm/spreaker-pages.json"
UA = {"User-Agent": "m365-site-bot (spreaker links)"}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


OPEN = urllib.request.build_opener(_NoRedirect)


def status_of(url):
    try:
        with OPEN.open(urllib.request.Request(url, headers=UA, method="GET"), timeout=30) as r: return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def read_log():
    out = {}
    if LOG.exists():
        for line in LOG.read_text("utf-8").splitlines():
            f = line.split("\t")
            if len(f) >= 5 and f[1].isdigit(): out[f[1]] = {"status": f[2], "old": f[3], "new": f[4]}
    return out


def log(eid, status, old, new, note=""):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write("\t".join([datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), str(eid), status, old or "", new or "", note.replace("\t", " ")[:200]]) + "\n")
    print(f"{eid}\t{status}\t{old or '-'} -> {new or '-'}\t{note}", flush=True)


def published(ep):
    """Nur veroeffentlichte Folgen: Veroeffentlichungsdatum in der Vergangenheit, nicht versteckt/privat, kein Entwurf."""
    p = ep.get("published_at") or ""
    try: when = datetime.strptime(p[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError: return False
    if when > datetime.now(timezone.utc): return False
    if str(ep.get("visibility", "PUBLIC")).upper() not in ("PUBLIC", "") or ep.get("hidden") in (True, "true", 1): return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300); ap.add_argument("--ids", default=""); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ids = {x for x in re.findall(r"\d+", a.ids)}
    with urllib.request.urlopen(urllib.request.Request(MAP_URL, headers=UA), timeout=60) as r:
        pages = json.loads(r.read().decode("utf-8")).get("pages") or {}
    if len(pages) < 100 and not ids:
        print(f"::error::Zuordnung zu klein ({len(pages)}) - Abbruch"); return 1
    done = read_log()
    sp = A.Spreaker()
    if not sp.login(): return 1
    own = sp.episodes()
    todo = [e for e in sorted(own, reverse=True) if str(e) in pages and (not ids or str(e) in ids)
            and not (done.get(str(e), {}).get("status") in ("ok", "unchanged") and done[str(e)]["new"] == pages[str(e)])]
    print(f"{len(own)} eigene Folgen, {len(pages)} mit Episodenseite, {len(todo)} offen" + (" (Probelauf)" if a.dry_run else ""))
    n = 0
    for eid in todo:
        if n >= a.limit: break
        url = pages[str(eid)]
        if not url.startswith("https://www.m365.fm/") or "utm_" in url:
            log(eid, "invalid", "", url, "Ziel nicht kanonisch"); continue
        try:
            ep = sp.req("GET", f"/episodes/{eid}")["episode"]
        except Exception as e:
            log(eid, "error", "", url, f"GET {str(e)[:120]}"); continue
        old = ep.get("episode_link") or ""
        if not published(ep):
            log(eid, "skipped", old, url, "nicht veroeffentlicht (Entwurf/geplant/privat)"); continue
        if old.rstrip("/") == url.rstrip("/"):
            log(eid, "unchanged", old, url); n += 1; continue
        st = status_of(url)
        if st != 200:
            log(eid, "target_not_200", old, url, f"Ziel antwortet {st}"); continue
        if a.dry_run:
            print(f"PROBE {eid}: {old or '(leer)'} -> {url}"); n += 1; continue
        try:
            sp.req("POST", f"/episodes/{eid}", data={"episode_link": url})
            after = (sp.req("GET", f"/episodes/{eid}")["episode"].get("episode_link") or "")
        except PermissionError as e:
            print(f"::error::{e}"); log(eid, "error", old, url, str(e)); return 1
        except Exception as e:
            log(eid, "error", old, url, str(e)[:160]); continue
        log(eid, "ok" if after.rstrip("/") == url.rstrip("/") else "mismatch", old, url, "" if after.rstrip("/") == url.rstrip("/") else f"Spreaker hat {after or '(leer)'}")
        n += 1; time.sleep(0.4)
    print(f"{n} Folgen bearbeitet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
