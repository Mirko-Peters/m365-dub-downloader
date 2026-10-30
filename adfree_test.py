"""Test: liefert der Besitzer-Download (mit Token) die werbefreie Originaldatei? Vergleicht Dauer mit der API-Dauer. Schreibt data/adfree_test.json."""
import json, os, subprocess, sys, requests
API = "https://api.spreaker.com/v2"; EP = sys.argv[1] if len(sys.argv) > 1 else "75899715"
tok = os.environ.get("SPREAKER_TOKEN", "").strip(); H = {}
if tok: H = {"Authorization": f"Bearer {tok}"}
if not tok or requests.get(API + "/me", headers=H, timeout=30).status_code == 401:
    import spreaker_auth
    d = spreaker_auth.load(); tok = d["access_token"] if d else ""
    H = {"Authorization": f"Bearer {tok}"}
    if requests.get(API + "/me", headers=H, timeout=30).status_code == 401: tok = spreaker_auth.refresh(); H = {"Authorization": f"Bearer {tok}"}
api_dur = requests.get(f"{API}/episodes/{EP}", headers=H, timeout=30).json()["response"]["episode"]["duration"] / 1000
def probe(name, url, hdr):
    r = requests.get(url, headers=hdr, timeout=300, allow_redirects=True); open(name, "wb").write(r.content)
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", name], capture_output=True, text=True).stdout.strip()
    return {"status": r.status_code, "bytes": len(r.content), "seconds": float(o) if o else None, "host": r.url.split("/")[2]}
res = {"episode": EP, "api_seconds": api_dur, "owner_download": probe("o.mp3", f"{API}/episodes/{EP}/download.mp3", H), "public_download": probe("p.mp3", f"{API}/episodes/{EP}/download.mp3", {})}
for k in ("owner_download", "public_download"):
    s = res[k]["seconds"]; res[k]["ads_seconds"] = round(s - api_dur, 1) if s else None
print(json.dumps(res, indent=1)); open("data/adfree_test.json", "w").write(json.dumps(res, indent=1))
