"""Ein Lader fuer alle Exporte des Community-Workers (api-dub.m365.fm).

- Jeder Endpunkt wird je Bau genau einmal geholt (Speicher-Cache), die Hauptexporte parallel vorab (prefetch).
- Bis zu drei Versuche je Endpunkt, Zeitueberschreitung 120 s.
- Jede erfolgreiche Antwort landet in data/cache/<name>.json (gitignored; in CI per actions/cache von Lauf zu Lauf).
  Faellt der Abruf aus, kommt die letzte gespeicherte Fassung mit Warnung - statt stillschweigend leerer Seiten.
- check(): fehlen Pflicht-Exporte (Blog, Profile, Entitaeten, Q&A) frisch UND im Cache, bricht der Bau mit Exit 1 ab.
  SITE_OFFLINE=1 (lokale Testbauten ohne Netz) macht daraus eine Warnung.
"""
import json, os, re, sys, time, threading, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

CACHE = Path(__file__).parent / "data" / "cache"
API = os.environ.get("COMMUNITY_API", "https://api-dub.m365.fm")
# Pflicht: ohne diese Exporte entstehen leere Bereiche (Blog, Mitglieder, Entitaeten, Fragen) - und kleinere Sitemaps, die Google als Loeschung liest
ESSENTIAL = ("/api/blog/export", "/api/profiles/export", "/api/entity/export", "/api/qa/export")
# Vorab parallel: alles, was der Seitenbau an Exporten kennt
PREFETCH = ESSENTIAL + ("/api/entity/claims", "/api/feed/export", "/api/show/export", "/api/events/export", "/api/guests/export", "/api/library/export",
                        "/api/podcast/export", "/api/video/export", "/api/notes/export", "/api/ui-i18n")

_MEM, _STATE, _LOCK = {}, {}, threading.Lock()   # url -> json | None ; url -> "frisch" | "cache" | "fehlt"


def _name(url):
    p = url.split("://", 1)[-1].split("/", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "_", p.lower()).strip("_")[:120] + ".json"


def _http(url, timeout, tries):
    last = None
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "m365-dub-build"}), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8")), None
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:120]}"
            if n + 1 < tries:
                time.sleep(3 * (n + 1))
    return None, last


def fetch(url, timeout=120, tries=3):
    """JSON eines Endpunkts: Speicher -> Netz (mit Wiederholung) -> data/cache. None nur, wenn beides fehlt."""
    with _LOCK:
        if url in _MEM:
            return _MEM[url]
    j, err = _http(url, timeout, tries)
    f = CACHE / _name(url)
    if j is not None:
        state = "frisch"
        try:
            CACHE.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    elif f.exists():
        try:
            j = json.loads(f.read_text("utf-8")); state = "cache"
            age = (time.time() - f.stat().st_mtime) / 3600
            print(f"WARNUNG: {url.split('://', 1)[-1]} nicht erreichbar ({err}) - gespeicherte Fassung von vor {age:.0f} h", file=sys.stderr)
        except Exception:
            j, state = None, "fehlt"
    else:
        state = "fehlt"
        print(f"WARNUNG: {url.split('://', 1)[-1]} nicht erreichbar ({err}) und keine gespeicherte Fassung", file=sys.stderr)
    with _LOCK:
        _MEM[url] = j; _STATE[url] = state
    return j


def prefetch(api=None, langs=()):
    """Hauptexporte parallel holen (8 gleichzeitig); spaetere Aufrufe kommen aus dem Speicher."""
    api = api or API
    urls = [api + p for p in PREFETCH] + [f"{api}/api/wiki/export?lang={l}" for l in langs]
    t = time.perf_counter()
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(fetch, urls))
    c = {k: sum(1 for v in _STATE.values() if v == k) for k in ("frisch", "cache", "fehlt")}
    print(f"Exporte: {c['frisch']} frisch, {c['cache']} aus Cache, {c['fehlt']} fehlen ({time.perf_counter() - t:.0f} s)")
    return c


def check(api=None):
    """Bricht ab, wenn ein Pflicht-Export weder frisch noch gespeichert vorliegt (sonst wuerde eine Seite ohne Blog/Profile/Entitaeten veroeffentlicht)."""
    api = api or API
    missing = [p for p in ESSENTIAL if _STATE.get(api + p, "fehlt") == "fehlt"]
    if "/api/profiles/export" in missing and (CACHE.parent / "members_export.json").exists():
        missing.remove("/api/profiles/export")   # Profile haben zusaetzlich die eingecheckte letzte Fassung (site_members.py)
    if not missing:
        return True
    msg = "Pflicht-Exporte fehlen (frisch und Cache): " + ", ".join(missing)
    if os.environ.get("SITE_OFFLINE") == "1":
        print("WARNUNG (SITE_OFFLINE=1): " + msg, file=sys.stderr); return False
    print("FEHLER: " + msg + " - Bau abgebrochen, damit keine leere Seite veroeffentlicht wird. Lokal: SITE_OFFLINE=1 setzen.", file=sys.stderr)
    sys.exit(1)


def states():
    return dict(_STATE)
