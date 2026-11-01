"""Nach dem Deploy: Vergleich der Seiten-Hashes mit dem letzten Lauf -> nur geaenderte Adressen im Cloudflare-Cache leeren (30 je Aufruf) und bei IndexNow melden.
Bei mehr als MAX_URLS Aenderungen (z. B. neues Stylesheet in jeder Seite) wird einmal alles geleert. Aufruf: python tools/purge_changed.py alt.json neu.json
Umgebung: CLOUDFLARE_API_TOKEN, CF_ZONE_ID (optional, sonst Zonensuche), BASE (https://www.m365.fm), INDEXNOW_KEY"""
import json, os, sys, time, urllib.request

MAX_URLS = 3000
old_f, new_f = sys.argv[1], sys.argv[2]
base = os.environ.get("BASE", "https://www.m365.fm").rstrip("/")
old = json.load(open(old_f)) if os.path.exists(old_f) else {}
new = json.load(open(new_f))
changed = sorted(u for u, h in new.items() if old.get(u) != h)
gone = sorted(u for u in old if u not in new)
# T41: optional 3. Argument - Liste der neu/geaendert nach R2 geladenen Seiten (tools/r2_pages_upload.py); der Site-Worker cacht sie unter /__r2c/<pfad>/
r2 = []
if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
    try: r2 = [u for u in json.load(open(sys.argv[3])) if isinstance(u, str) and u.startswith("/")]
    except Exception as e: print("R2-Liste nicht lesbar:", type(e).__name__)
if r2: print(f"{len(r2)} R2-Seiten neu oder geaendert")
print(f"{len(new)} Dateien, {len(changed)} neu oder geaendert, {len(gone)} weggefallen" + ("" if old else " (kein Vorlauf: erster Vergleich)"))


def cf(path, body):
    req = urllib.request.Request("https://api.cloudflare.com/client/v4" + path, json.dumps(body).encode(), {"Authorization": "Bearer " + os.environ["CLOUDFLARE_API_TOKEN"], "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)


tok = os.environ.get("CLOUDFLARE_API_TOKEN"); zone = os.environ.get("CF_ZONE_ID", "")
if tok:
    if not zone:
        with urllib.request.urlopen(urllib.request.Request("https://api.cloudflare.com/client/v4/zones?name=m365.fm", headers={"Authorization": "Bearer " + tok}), timeout=60) as r:
            res = json.load(r).get("result") or []; zone = res[0]["id"] if res else ""
    if not zone:
        print("::warning::Zone-ID nicht gefunden - kein Purge")
    elif not old or len(changed) + len(gone) + len(r2) > MAX_URLS:
        d = cf(f"/zones/{zone}/purge_cache", {"purge_everything": True}); print("Cache komplett geleert:", d.get("success"))
    else:
        urls = [base + u for u in changed + gone] + [base + "/__r2c" + u for u in r2]; ok = 0
        for i in range(0, len(urls), 30):
            d = cf(f"/zones/{zone}/purge_cache", {"files": urls[i:i + 30]}); ok += len(urls[i:i + 30]) if d.get("success") else 0
            if not d.get("success"): print("Purge-Fehler:", [e.get("message") for e in d.get("errors", [])][:2]); time.sleep(1)
        print(f"Cache geleert fuer {ok} Adressen")
else:
    print("Kein Cloudflare-Token - kein Purge")

key = os.environ.get("INDEXNOW_KEY", "")
pages = [base + u for u in changed if u.endswith("/") and not u.startswith("/assets/")]
if key and pages and old:
    host = base.split("//")[1]
    for i in range(0, len(pages), 9000):
        body = json.dumps({"host": host, "key": key, "keyLocation": f"{base}/{key}.txt", "urlList": pages[i:i + 9000]}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request("https://api.indexnow.org/indexnow", body, {"Content-Type": "application/json; charset=utf-8", "User-Agent": "m365fm-site-build/1.0 (+https://www.m365.fm/)"}), timeout=60) as r: print("IndexNow:", r.status, len(pages[i:i + 9000]), "geaenderte Seiten gemeldet")
        except Exception as e: print("IndexNow-Fehler:", str(e)[:120])
elif key and not old:
    print("IndexNow: erster Vergleich, keine Meldung (sonst alle Seiten)")
else:
    print("IndexNow: nichts zu melden")
