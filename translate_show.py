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


# Haiku 5.5, Message Batch (50 % Rabatt, Prompts bis 100K Tokens): $ je 1 Mio. Tokens
PRICE_IN, PRICE_OUT = float(os.environ.get("PRICE_IN", "0.05")), float(os.environ.get("PRICE_OUT", "0.25"))
BUDGET = float(os.environ.get("BUDGET_USD", "70"))


def cost(tin, tout):
    return tin * PRICE_IN / 1e6 + tout * PRICE_OUT / 1e6


def spent():
    uf = OUT / "usage.json"
    if not uf.exists(): return 0.0
    u = json.loads(uf.read_text()); return cost(u.get("input_tokens", 0), u.get("output_tokens", 0))


def guard(n, est_in, est_out, what):
    """Bricht ab, wenn der geschaetzte Worst-Case das Gesamtbudget sprengen wuerde."""
    est = n * cost(est_in, est_out); already = float(os.environ.get("RUN_SPENT", "0"))
    print(f"Budget {what}: bisher {spent():.2f} $ (Datei) + dieser Lauf {already:.2f} $ + Worst-Case {est:.2f} $ <= {BUDGET:.0f} $?")
    if spent() + already + est > BUDGET: raise SystemExit(f"Abbruch: Budget {BUDGET} $ wuerde ueberschritten")


def parse_json(txt):
    """Robust: Codezaeune entfernen, sonst Felder per Regex holen."""
    import re
    t = txt.strip()
    if t.startswith("```"): t = re.sub(r"^```[a-z]*\n?|```$", "", t).strip()
    try:
        j = json.loads(t[t.index("{"):t.rindex("}") + 1], strict=False)
        return j["title"], j["summary"]
    except Exception:
        m = re.search(r'"title"\s*:\s*"(.*?)"\s*,\s*"summary"\s*:\s*"(.*)"\s*}?\s*$', t, re.S)
        if m: return m.group(1), m.group(2)
        raise


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
            src = json.dumps({"title": e["name"], "summary": (P.plain(e.get("summary")) or P.plain(e.get("show_notes")))[:900]}, ensure_ascii=False)
            reqs.append({"custom_id": f"{l}__{e['slug']}"[:64] if len(f"{l}__{e['slug']}") <= 64 else f"{l}__{e['id']}", "params": {"model": MODEL, "max_tokens": 4096, "thinking": {"type": "disabled"},
                         "system": f"Translate the podcast episode title and summary into {NAMES[l]}. Keep product names (Microsoft 365, Copilot, Power BI, Azure ...) untranslated. Reply with JSON only: {{\"title\": ..., \"summary\": ...}}",
                         "messages": [{"role": "user", "content": src}]}})
    if not reqs:
        print("Nichts zu uebersetzen"); return
    idmap = {r["custom_id"]: r["custom_id"] for r in reqs}
    slug_by_id = {e["id"]: e["slug"] for e in eps}
    print(len(reqs), "Anfragen, Modell", MODEL)
    guard(len(reqs), 500, 1500, "Titel/Zusammenfassungen")
    b = call("POST", "/v1/messages/batches", {"requests": reqs})
    bid = b["id"]; print("Batch", bid)
    (OUT / "batch.json").write_text(json.dumps({"id": bid, "n": len(reqs), "model": MODEL}))
    while b["processing_status"] != "ended":
        time.sleep(120); b = call("GET", f"/v1/messages/batches/{bid}"); print(b["processing_status"], b["request_counts"], flush=True)
    tin = tout = ok = bad = 0; why = {}; samples = []
    req = urllib.request.Request(b["results_url"], headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    for line in urllib.request.urlopen(req, timeout=600).read().decode().splitlines():
        r = json.loads(line); cid = r["custom_id"]; l, key = cid.split("__", 1); key = slug_by_id.get(key, key)
        res = r["result"]
        if res["type"] != "succeeded":
            bad += 1; why[res["type"]] = why.get(res["type"], 0) + 1
            if len(samples) < 8: samples.append({"id": cid, "result": json.dumps(res)[:400]})
            continue
        u = res["message"]["usage"]; tin += u["input_tokens"]; tout += u["output_tokens"]
        if res["message"].get("stop_reason") == "max_tokens":
            bad += 1; why["max_tokens"] = why.get("max_tokens", 0) + 1; continue
        try:
            t, sm = parse_json(res["message"]["content"][0]["text"]); have[l][key] = [t.strip(), sm.strip()]; ok += 1
        except Exception:
            bad += 1; why["parse"] = why.get("parse", 0) + 1
            if len(samples) < 8: samples.append({"id": cid, "text": res["message"]["content"][0]["text"][:400]})
    for l in langs: (OUT / f"{l}.json").write_text(json.dumps(have[l], ensure_ascii=False), encoding="utf-8")
    uf = OUT / "usage.json"; old = json.loads(uf.read_text()) if uf.exists() else {"input_tokens": 0, "output_tokens": 0, "runs": []}
    old["input_tokens"] += tin; old["output_tokens"] += tout; old["runs"].append({"batch": bid, "model": MODEL, "ok": ok, "failed": bad, "why": why, "input_tokens": tin, "output_tokens": tout})
    uf.write_text(json.dumps(old, indent=1))
    if samples: (OUT / "fail_samples.json").write_text(json.dumps(samples, ensure_ascii=False, indent=1))
    rep = {"stage": "titles", "requests": len(reqs), "ok": ok, "failed": bad, "why": why, "input_tokens": tin, "output_tokens": tout, "cost_usd": round(cost(tin, tout), 3), "success_rate": round(ok / max(1, ok + bad), 4)}
    (OUT / "report_titles.json").write_text(json.dumps(rep, indent=1))
    print(f"fertig: {ok} ok, {bad} fehlgeschlagen {why}, Tokens ein/aus: {tin}/{tout}, Kosten {cost(tin, tout):.3f} $")
    return rep


def run_all():
    rep1 = main() or {}
    if "--notes" in sys.argv:
        os.environ["RUN_SPENT"] = str(rep1.get("cost_usd", 0))
        import translate_notes
        rep2 = translate_notes.main() or {}
        tot = {"titles": rep1, "notes": rep2, "total_cost_usd": round(rep1.get("cost_usd", 0) + rep2.get("cost_usd", 0), 3),
               "total_input_tokens": rep1.get("input_tokens", 0) + rep2.get("input_tokens", 0), "total_output_tokens": rep1.get("output_tokens", 0) + rep2.get("output_tokens", 0)}
        (OUT / "report.json").write_text(json.dumps(tot, indent=1)); print(json.dumps(tot, indent=1))


if __name__ == "__main__":
    try:
        run_all()
    except Exception as ex:
        import traceback
        OUT.mkdir(parents=True, exist_ok=True)
        if not (OUT / "last_error.txt").exists() or "API-Fehler" not in (OUT / "last_error.txt").read_text():
            (OUT / "last_error.txt").write_text(traceback.format_exc()[-1500:])
        raise
