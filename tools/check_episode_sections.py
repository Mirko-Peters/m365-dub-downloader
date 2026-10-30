"""Prueft Kernpunkte und FAQ der Folgen: python tools/check_episode_sections.py [N ...]
Je Folge des Pakets data/episode_tasks/part-N.json muss in data/episode_sections/part-N.json {slug: {"keypoints": [...], "faq": [{"q":..,"a":..}]}} stehen."""
import json, re, sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
EN = re.compile(r"\b(the|and|is|with|for|of|to|that|which|it|how|what)\b", re.I)
DE = re.compile(r"\b(und|der|die|das|ist|mit|für|von|wird|nicht|ein|eine)\b", re.I)
bad_total = 0


def check(n):
    global bad_total
    tf, rf = D / "episode_tasks" / f"part-{n}.json", D / "episode_sections" / f"part-{n}.json"
    if not tf.exists(): print(f"Paket {n}: keine Aufgabe"); return
    if not rf.exists(): print(f"Paket {n}: Ergebnis fehlt"); bad_total += 1; return
    tasks = json.loads(tf.read_text("utf-8")); res = json.loads(rf.read_text("utf-8")); probs = []
    ids = {t["slug"] for t in tasks}
    for i in sorted(ids - set(res)): probs.append(f"{i}: fehlt")
    for i in sorted(set(res) - ids): probs.append(f"{i}: gehoert nicht zu diesem Paket")
    for t in tasks:
        r = res.get(t["slug"])
        if not isinstance(r, dict): continue
        kp, faq, s = r.get("keypoints") or [], r.get("faq") or [], t["slug"]
        if not 4 <= len(kp) <= 7: probs.append(f"{s}: {len(kp)} Kernpunkte (erlaubt 4-7)")
        if len(set(x.strip().lower() for x in kp)) != len(kp): probs.append(f"{s}: doppelte Kernpunkte")
        for x in kp:
            if not 25 <= len(x) <= 200: probs.append(f"{s}: Kernpunkt Laenge {len(x)} (25-200): {x[:40]}")
            if re.search(r"https?://|www\.|\*\*|^#", x): probs.append(f"{s}: Kernpunkt mit Link/Markdown")
        if not 4 <= len(faq) <= 6: probs.append(f"{s}: {len(faq)} FAQ-Eintraege (erlaubt 4-6)")
        qs = set()
        for f in faq:
            q, a = (f.get("q") or "").strip(), (f.get("a") or "").strip()
            if not 15 <= len(q) <= 200 or not q.endswith("?"): probs.append(f"{s}: Frage ungueltig: {q[:50]}")
            if not 100 <= len(a) <= 600: probs.append(f"{s}: Antwort Laenge {len(a)} (100-600): {q[:40]}")
            if re.search(r"https?://|www\.|\*\*", a): probs.append(f"{s}: Antwort mit Link/Markdown")
            if q.lower() in qs: probs.append(f"{s}: doppelte Frage")
            qs.add(q.lower())
        blob = " ".join(kp) + " " + " ".join((f.get("q") or "") + " " + (f.get("a") or "") for f in faq)
        if len(EN.findall(blob)) < len(DE.findall(blob)): probs.append(f"{s}: Sprache wirkt nicht englisch")
    print(f"Paket {n}: {len(tasks)} Folgen, {len(res)} Ergebnisse, {len(probs)} Probleme")
    for p in probs[:30]: print("   ", p)
    bad_total += len(probs)


nums = [int(a) for a in sys.argv[1:]] or sorted(int(re.search(r"part-(\d+)", f.name).group(1)) for f in (D / "episode_tasks").glob("part-*.json"))
for n in nums: check(n)
sys.exit(1 if bad_total else 0)
