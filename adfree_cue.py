"""Test: Cuepoints einer Folge auf ads_max_count=0 setzen -> Download-Laenge pruefen -> danach Original wiederherstellen (ausser KEEP=1)."""
import json, os, subprocess, sys, time, traceback, requests
API = "https://api.spreaker.com/v2"; EP = sys.argv[1]; KEEP = os.environ.get("KEEP") == "1"
def token():
    tok = os.environ.get("SPREAKER_TOKEN", "").strip()
    if tok and requests.get(API + "/me", headers={"Authorization": f"Bearer {tok}"}, timeout=30).status_code != 401: return tok
    import spreaker_auth
    d = spreaker_auth.load(); tok = d["access_token"] if d else ""
    if not tok or requests.get(API + "/me", headers={"Authorization": f"Bearer {tok}"}, timeout=30).status_code == 401: tok = spreaker_auth.refresh()
    return tok
def dur(H, name):
    r = requests.get(f"{API}/episodes/{EP}/download.mp3", headers=H, timeout=300); open(name, "wb").write(r.content)
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", name], capture_output=True, text=True).stdout.strip()
    return float(o) if o else None
res = {}
try:
    H = {"Authorization": "Bearer " + token()}
    res["api_seconds"] = requests.get(f"{API}/episodes/{EP}", headers=H, timeout=30).json()["response"]["episode"]["duration"] / 1000
    g = requests.get(f"{API}/episodes/{EP}/cuepoints", headers=H, timeout=30); res["get_status"] = g.status_code
    orig = (g.json().get("response") or {}).get("cuepoints", []) if g.ok else []; res["cuepoints_before"] = orig
    res["seconds_before"] = dur(H, "a.mp3")
    zero = [{"timecode": c["timecode"], "ads_max_count": 0} for c in orig]
    p = requests.post(f"{API}/episodes/{EP}/cuepoints", headers=H, data={"cuepoints": json.dumps(zero)}, timeout=30); res["set_zero"] = {"status": p.status_code, "body": p.text[:200]}
    time.sleep(20); res["seconds_after_zero"] = dur(H, "b.mp3")
    if not orig or res["seconds_after_zero"] - res["api_seconds"] > 2:   # Gegenprobe: alle Cuepoints loeschen
        d_ = requests.delete(f"{API}/episodes/{EP}/cuepoints", headers=H, timeout=30); res["delete"] = {"status": d_.status_code, "body": d_.text[:200]}
        time.sleep(20); res["seconds_after_delete"] = dur(H, "c.mp3")
    if not KEEP:
        r = requests.post(f"{API}/episodes/{EP}/cuepoints", headers=H, data={"cuepoints": json.dumps(orig)}, timeout=30); res["restored"] = {"status": r.status_code, "n": len(orig)}
except Exception:
    res["error"] = traceback.format_exc()[-1200:]
    try:
        if not KEEP and "cuepoints_before" in res: requests.post(f"{API}/episodes/{EP}/cuepoints", headers=H, data={"cuepoints": json.dumps(res["cuepoints_before"])}, timeout=30)
    except Exception: pass
print(json.dumps(res, indent=1)); open("data/adfree_cue.json", "w", encoding="utf-8").write(json.dumps(res, indent=1))
