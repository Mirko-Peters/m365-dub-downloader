"""Prueft die geschriebenen Entitaeten-Texte: python tools/check_entity_texts.py [N ...]   (ohne Argument: alle vorhandenen Pakete)
Je Entitaet des Pakets data/entity_tasks/part-N.json muss in data/entity_texts/part-N.json {id: {"en": ..., "de": ...}} stehen."""
import json, re, sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
DE_HINT = re.compile(r"\b(und|der|die|das|ist|mit|für|von|wird|zur|zum|ein|eine|nicht)\b", re.I)
EN_HINT = re.compile(r"\b(the|and|is|with|for|of|to|that|which|it)\b", re.I)
bad_total = 0


def check(n):
    global bad_total
    tf, rf = D / "entity_tasks" / f"part-{n}.json", D / "entity_texts" / f"part-{n}.json"
    if not tf.exists():
        print(f"Paket {n}: keine Aufgabe"); return
    if not rf.exists():
        print(f"Paket {n}: Ergebnis fehlt"); bad_total += 1; return
    tasks = json.loads(tf.read_text("utf-8")); res = json.loads(rf.read_text("utf-8"))
    probs = []
    ids = {t["id"] for t in tasks}
    for i in sorted(ids - set(res)): probs.append(f"{i}: fehlt")
    for i in sorted(set(res) - ids): probs.append(f"{i}: gehoert nicht zu diesem Paket")
    for t in tasks:
        r = res.get(t["id"])
        if not isinstance(r, dict): continue
        for lang, hint, other in (("en", EN_HINT, DE_HINT), ("de", DE_HINT, EN_HINT)):
            x = (r.get(lang) or "").strip()
            if not x: probs.append(f"{t['id']}.{lang}: leer"); continue
            if not 650 <= len(x) <= 2200: probs.append(f"{t['id']}.{lang}: Laenge {len(x)} (erlaubt 650-2200)")
            if re.search(r"https?://|www\.", x): probs.append(f"{t['id']}.{lang}: enthaelt einen Link")
            if re.search(r"^#|\*\*|^- ", x, re.M): probs.append(f"{t['id']}.{lang}: enthaelt Markdown")
            if not 2 <= len([p for p in x.split("\n\n") if p.strip()]) <= 4: probs.append(f"{t['id']}.{lang}: Absaetze nicht 2-4")
            if len(hint.findall(x)) < len(other.findall(x)): probs.append(f"{t['id']}.{lang}: Sprache wirkt falsch")
    print(f"Paket {n}: {len(tasks)} Aufgaben, {len(res)} Texte, {len(probs)} Probleme")
    for p in probs[:25]: print("   ", p)
    bad_total += len(probs)


nums = [int(a) for a in sys.argv[1:]] or sorted(int(re.search(r"part-(\d+)", f.name).group(1)) for f in (D / "entity_tasks").glob("part-*.json"))
for n in nums: check(n)
sys.exit(1 if bad_total else 0)
