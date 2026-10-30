#!/usr/bin/env python3
"""Uebersetzt fehlende Texte (Kurzbeschreibung, Langbeschreibung) der Entitaeten zwischen Englisch und Deutsch mit der Claude-API (Haiku, wenige Cent).
Nur Luecken werden gefuellt, vorhandene Texte bleiben unberuehrt. Produktnamen, Aliase und Fachbegriffe werden nicht uebersetzt.

  export ANTHROPIC_API_KEY=...
  python3 tools/translate_missing.py --dry-run     # zeigt nur, was fehlt, und eine grobe Kostenschaetzung
  python3 tools/translate_missing.py               # uebersetzt und schreibt data/entities.json
Optional: --model claude-haiku-5-5 (Standard), --limit 20 (nur die ersten N)
"""
import argparse, json, os, sys, urllib.request

P = "data/entities.json"
SYS = ("You translate short encyclopedia texts about Microsoft products and IT concepts between English and German. "
       "Keep product names, feature names, abbreviations and code (e.g. Copilot Studio, Power Fx, D365FO, MS-900) unchanged. "
       "Keep the same length, tone and paragraph structure (blank lines between paragraphs). No links, no quotes, no commentary. "
       "Answer with a JSON object that maps each given key to its translation, and nothing else.")


def call(key, model, items):
    body = {"model": model, "max_tokens": 4000, "system": SYS,
            "messages": [{"role": "user", "content": json.dumps(items, ensure_ascii=False)}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(),
                                 {"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        txt = json.load(r)["content"][0]["text"].strip()
    if txt.startswith("```"):
        txt = txt.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(txt)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--model", default="claude-haiku-5-5"); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    D = json.load(open(P)); todo = []   # (entity, feld, quellsprache, zielsprache, text)
    for e in D:
        for field in ("desc", "long"):
            v = e.get(field) or {}
            for src, dst in (("en", "de"), ("de", "en")):
                if v.get(src, "").strip() and not v.get(dst, "").strip():
                    todo.append((e, field, src, dst, v[src]))
    if a.limit:
        todo = todo[:a.limit]
    chars = sum(len(t[4]) for t in todo)
    print(f"{len(todo)} fehlende Texte, {chars} Zeichen (ca. {chars // 3} Token Eingabe + gleich viel Ausgabe)")
    if a.dry_run or not todo:
        return
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY fehlt")
    for i in range(0, len(todo), 12):   # 12 Texte pro Anfrage
        chunk = todo[i:i + 12]
        res = call(key, a.model, {f"{e['id']}|{f}|{s}>{d}": f"[{s}->{d}] {txt}" for e, f, s, d, txt in chunk})
        for e, f, s, d, txt in chunk:
            out = str(res.get(f"{e['id']}|{f}|{s}>{d}", "")).replace(f"[{s}->{d}] ", "").strip()
            if out and (f != "desc" or 20 <= len(out) <= 300):
                e.setdefault(f, {})[d] = out
        json.dump(D, open(P, "w"), ensure_ascii=False, indent=1)   # nach jedem Block speichern
        print(f"  {min(i + 12, len(todo))}/{len(todo)}")


main()
