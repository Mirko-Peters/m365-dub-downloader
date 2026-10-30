"""Aufgabenpakete fuer Kernpunkte und FAQ der Podcast-Folgen: je Folge Titel, Zusammenfassung, Show Notes und ein Auszug aus dem Transkript
(Anfang, Mitte, Ende; falls ein Transkript zugeordnet werden kann). Schreibt data/episode_tasks/part-N.json, neueste Folgen zuerst.
Aufruf: python tools/episode_section_tasks.py [--parts 8]"""
import json, re, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import site_podpage as P
import platform_match as PM

D = ROOT / "data"
parts = int(sys.argv[sys.argv.index("--parts") + 1]) if "--parts" in sys.argv else 8
SEP = r"(?:[-|:–—])"


def key(t):
    t = re.sub(r"\s*[\[(][^\])]*[\])]\s*$", "", t or "")
    t = re.sub(r"\s*" + SEP + r"\s*simply explained\s*$", "", t, flags=re.I)
    t = re.sub(r"\bexplained\b|\bsimply\b", "", t, flags=re.I)
    return PM.normalize(t)


en = json.loads((D / "en_episodes.json").read_text("utf-8"))
R = [(key(v["title"]), set(key(v["title"]).split()), v) for v in en.values() if v.get("transcript") and (D / "en_transcripts" / f"{v['transcript']}.txt").exists()]
idx = collections.defaultdict(list)
for i, (_, ts, _) in enumerate(R):
    for w in ts: idx[w].append(i)


def transcript_of(title):
    k = key(title); ts = set(k.split())
    ex = [v for a, _, v in R if a == k]
    if len(ex) == 1: return ex[0]
    if ex or not ts: return None
    c = collections.Counter(i for w in ts for i in idx.get(w, []))
    best = sorted(((len(ts & R[i][1]) / len(ts | R[i][1]), i) for i, _ in c.most_common(8)), reverse=True)[:2]
    if best and best[0][0] >= 0.75 and (len(best) < 2 or best[0][0] - best[1][0] >= 0.1): return R[best[0][1]][2]
    return None


def digest(text):
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= 4200: return t
    m = len(t) // 2
    return t[:2000] + " [...] " + t[m - 600:m + 600] + " [...] " + t[-900:]


eps = [e for e in P.load("episodes") if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True")]
eps.sort(key=lambda e: e["create_time"], reverse=True)
tasks, with_tr = [], 0
for e in eps:
    v = transcript_of(e["name"]); tr = ""
    if v:
        tr = digest((D / "en_transcripts" / f"{v['transcript']}.txt").read_text("utf-8")); with_tr += 1
    tasks.append({"slug": e["slug"], "title": e["name"], "date": (e.get("published") or e["create_time"] or "")[:10], "summary": P.plain(e.get("summary"))[:700],
                  "show_notes": P.plain(e.get("show_notes"))[:2600], "transcript_excerpt": tr})
out = D / "episode_tasks"; out.mkdir(exist_ok=True)
for f in out.glob("part-*.json"): f.unlink()
per = -(-len(tasks) // parts)
for i in range(parts):
    (out / f"part-{i + 1}.json").write_text(json.dumps(tasks[i * per:(i + 1) * per], ensure_ascii=False, indent=1), encoding="utf-8")
print(len(tasks), "Folgen in", parts, "Paketen;", with_tr, "mit Transkript;", sum(1 for t in tasks if len(t["show_notes"]) > 300), "mit Show Notes >300 Zeichen")
