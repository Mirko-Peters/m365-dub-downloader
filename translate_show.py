"""Uebersetzt Titel + Zusammenfassungen der englischen Show (data/podpage) mit Claude Haiku per Message Batch (halber Preis).
Aufruf: python translate_show.py [--langs de,es,...] [--limit N]. Ergebnis: data/podpage_i18n/<lang>.json {folgen-slug: [titel, zusammenfassung]}
und data/podpage_i18n/usage.json (Tokens gesamt, fuer die Kostenrechnung). Bereits uebersetzte Folgen werden uebersprungen."""
import json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
import site_podpage as P

MODEL = os.environ.get("TRANSLATE_MODEL", "claude-haiku-5-5")
OUT = Path(__file__).parent / "data" / "podpage_i18n"
NAMES = {"de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish", "id": "Indonesian", "ru": "Russian", "uk": "Ukrainian",
         "ar": "Arabic", "he": "Hebrew", "hi": "Hindi", "ja": "Japanese", "ko": "Korean", "ml": "Malayalam", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu"}


def call(method, path, body=None):
    req = urllib.request.Request("https://api.anthropic.com" + path, json.dumps(body).encode() if body is not None else None, {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"}, method=method)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        msg = f"API-Fehler {e.code} {method} {path}: {e.read()[:600]!r}"
        print(msg); OUT.mkdir(parents=True, exist_ok=True); (OUT / "last_error.txt").write_text(msg); raise


def main():
    a = sys.argv[1:]
    langs = (a[a.index("--langs") + 1].split(",") if "--langs" in a else list(NAMES))
    limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 0
    eps = [e for e in P.load("episodes") if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True")]
    eps.sort(key=lambda e: e["create_time"], reverse=True)
    if limit: eps = eps[:limit]
    OUT.mkdir(parents=True, exist_ok=True)
    have = {l: (json.loads((OUT / f"{l}.json").read_text("utf-8")) if (OUT / f"{l}.json").exists() else {}) for l in langs}
    reqs = []
    for l in langs:
        for e in eps:
            if e["slug"] in have[l]: continue
            src = json.dumps({"title": e["name"], "summary": P.plain(e.get("summary"))[:1200]}, ensure_ascii=False)
            reqs.append({"custom_id": f"{l}__{e['slug']}"[:64] if len(f"{l}__{e['slug']}") <= 64 else f"{l}__{e['id']}", "params": {"model": MODEL, "max_tokens": 700,
                         "system": f"Translate the podcast episode title and summary into {NAMES[l]}. Keep product names (Microsoft 365, Copilot, Power BI, Azure ...) untranslated. Reply with JSON only: {{\"title\": ..., \"summary\": ...}}",
                         "messages": [{"role": "user", "content": src}]}})
    if not reqs:
        print("Nichts zu uebersetzen"); return
    idmap = {r["custom_id"]: r["custom_id"] for r in reqs}
    slug_by_id = {e["id"]: e["slug"] for e in eps}
    print(len(reqs), "Anfragen, Modell", MODEL)
    b = call("POST", "/v1/messages/batches", {"requests": reqs})
    bid = b["id"]; print("Batch", bid)
    (OUT / "batch.json").write_text(json.dumps({"id": bid, "n": len(reqs), "model": MODEL}))
    while b["processing_status"] != "ended":
        time.sleep(120); b = call("GET", f"/v1/messages/batches/{bid}"); print(b["processing_status"], b["request_counts"], flush=True)
    tin = tout = ok = bad = 0
    req = urllib.request.Request(b["results_url"], headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    for line in urllib.request.urlopen(req, timeout=600).read().decode().splitlines():
        r = json.loads(line); cid = r["custom_id"]; l, key = cid.split("__", 1); key = slug_by_id.get(key, key)
        res = r["result"]
        if res["type"] != "succeeded": bad += 1; continue
        u = res["message"]["usage"]; tin += u["input_tokens"]; tout += u["output_tokens"]
        try:
            txt = res["message"]["content"][0]["text"]; j = json.loads(txt[txt.index("{"):txt.rindex("}") + 1]); have[l][key] = [j["title"].strip(), j["summary"].strip()]; ok += 1
        except Exception:
            bad += 1
    for l in langs: (OUT / f"{l}.json").write_text(json.dumps(have[l], ensure_ascii=False), encoding="utf-8")
    uf = OUT / "usage.json"; old = json.loads(uf.read_text()) if uf.exists() else {"input_tokens": 0, "output_tokens": 0, "runs": []}
    old["input_tokens"] += tin; old["output_tokens"] += tout; old["runs"].append({"batch": bid, "model": MODEL, "ok": ok, "failed": bad, "input_tokens": tin, "output_tokens": tout})
    uf.write_text(json.dumps(old, indent=1))
    print(f"fertig: {ok} ok, {bad} fehlgeschlagen, Tokens ein/aus: {tin}/{tout}")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        import traceback
        OUT.mkdir(parents=True, exist_ok=True)
        if not (OUT / "last_error.txt").exists() or "API-Fehler" not in (OUT / "last_error.txt").read_text():
            (OUT / "last_error.txt").write_text(traceback.format_exc()[-1500:])
        raise
