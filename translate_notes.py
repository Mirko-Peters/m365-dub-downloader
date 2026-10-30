"""Uebersetzt die Show Notes der meistgehoerten englischen Folgen (Haiku, Message Batch). Ranking: Spreaker-Statistik (Plays/Downloads seit 2025),
Ersatz: featured + neueste. Ergebnis: data/podpage_i18n/notes_<lang>.json {folgen-slug: html}. Kosten in usage.json (Schluessel notes_*)."""
import json, os, sys, time, urllib.request
from datetime import date
from pathlib import Path
import requests
import site_podpage as P
from translate_show import call, NAMES, OUT, MODEL

TOP = int(os.environ.get("NOTES_TOP", "150")); MAXC = 8000
S = requests.Session(); API = "https://api.spreaker.com/v2"


def spreaker_get(url):
    r = S.get(url if url.startswith("http") else API + url, timeout=60); r.raise_for_status(); return r.json().get("response", {})


def paged(path):
    items, url = [], path
    while url:
        resp = spreaker_get(url); items += resp.get("items", []); url = resp.get("next_url")
    return items


def ranking(eps):
    """-> Liste Podpage-Folgen, meistgehoert zuerst"""
    tok = os.environ.get("SPREAKER_TOKEN", "").strip()
    if not tok and os.environ.get("SPREAKER_CLIENT_SECRET"):
        try:
            import spreaker_auth; d = spreaker_auth.load(); tok = d["access_token"] if d else ""
        except Exception: tok = ""
    by = {P.norm(e["name"]): e for e in eps}
    if tok:
        S.headers["Authorization"] = f"Bearer {tok}"
        try:
            titles = {str(x["episode_id"]): x.get("title") for x in paged("/shows/6704921/episodes?limit=100")}
            tot = paged(f"/shows/6704921/episodes/statistics/plays/totals?from=2025-01-01&to={date.today()}&limit=100")
            rows = []
            for it in tot:
                eid = str(it.get("episode_id") or (it.get("episode") or {}).get("episode_id") or "")
                nums = [v for k, v in it.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ("episode_id", "show_id")]
                rows.append((max(nums, default=0), eid))
            rows.sort(reverse=True); out = []
            for sc, eid in rows:
                e = by.get(P.norm(titles.get(eid) or ""))
                if e and e not in out: out.append(e)
            if len(out) >= 20:
                print("Ranking aus Spreaker-Statistik:", len(out)); return out
        except Exception as ex:
            print("Statistik nicht verfuegbar:", str(ex)[:150])
    print("Ersatz-Ranking: featured + neueste")
    fe = [e for e in eps if e.get("featured") in (True, "True")]
    return fe + [e for e in sorted(eps, key=lambda e: e["create_time"], reverse=True) if e not in fe]


def main():
    langs = list(NAMES)
    eps = [e for e in P.load("episodes") if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True") and len(P.plain(e.get("show_notes"))) > 200]
    top = ranking(eps)[:TOP]
    OUT.mkdir(parents=True, exist_ok=True)
    have = {l: (json.loads((OUT / f"notes_{l}.json").read_text("utf-8")) if (OUT / f"notes_{l}.json").exists() else {}) for l in langs}
    reqs, key = [], {}
    for l in langs:
        for e in top:
            if e["slug"] in have[l]: continue
            cid = f"{l}__{e['id']}"; key[cid] = e["slug"]
            src = P.san(e["show_notes"])[:MAXC]
            reqs.append({"custom_id": cid, "params": {"model": MODEL, "max_tokens": 6000, "thinking": {"type": "disabled"},
                "system": f"Translate this podcast show-notes HTML into {NAMES[l]}. Keep the HTML tags and structure (p, ul, li, h2, h3, strong, em, a href). Keep product names (Microsoft 365, Copilot, Power BI, Azure ...) and URLs untranslated. Reply with the translated HTML only.",
                "messages": [{"role": "user", "content": src}]}})
    if not reqs: print("Nichts zu tun"); return
    print(len(reqs), "Anfragen fuer", len(top), "Folgen")
    b = call("POST", "/v1/messages/batches", {"requests": reqs}); bid = b["id"]; print("Batch", bid)
    while b["processing_status"] != "ended":
        time.sleep(120); b = call("GET", f"/v1/messages/batches/{bid}"); print(b["processing_status"], b["request_counts"], flush=True)
    tin = tout = ok = bad = 0
    rq = urllib.request.Request(b["results_url"], headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    for line in urllib.request.urlopen(rq, timeout=900).read().decode().splitlines():
        r = json.loads(line); res = r["result"]; l = r["custom_id"].split("__")[0]
        if res["type"] != "succeeded": bad += 1; continue
        u = res["message"]["usage"]; tin += u["input_tokens"]; tout += u["output_tokens"]
        if res["message"].get("stop_reason") == "max_tokens": bad += 1; continue
        have[l][key[r["custom_id"]]] = P.san(res["message"]["content"][0]["text"]); ok += 1
    for l in langs: (OUT / f"notes_{l}.json").write_text(json.dumps(have[l], ensure_ascii=False), encoding="utf-8")
    uf = OUT / "usage.json"; old = json.loads(uf.read_text()) if uf.exists() else {"input_tokens": 0, "output_tokens": 0, "runs": []}
    old["runs"].append({"kind": "notes", "batch": bid, "model": MODEL, "ok": ok, "failed": bad, "input_tokens": tin, "output_tokens": tout}); uf.write_text(json.dumps(old, indent=1))
    print(f"fertig: {ok} ok, {bad} fehlgeschlagen, Tokens ein/aus: {tin}/{tout}")


if __name__ == "__main__":
    main()
