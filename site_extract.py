"""T27: Folgen und Videos mit Entitaetsprofilen verbinden. Quelle sind die Extraktionen shownotes/entities/<spreaker_episode_id>.json
(entities[] mit slug und score, youtube_video_id), aber nur fuer Folgen, die die QA in shownotes/QA.txt mit ok oder fixed fuehrt.
Ergebnis: je Entitaet die Folgen, in denen sie nachweislich vorkommt (staerker als ein Namenstreffer im Titel), je Folge die Entitaeten
und die YouTube-ID. Ungepruefte Extraktionen bleiben Arbeitsmaterial und wirken nicht auf die Seite."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SE, QA = ROOT / "shownotes" / "entities", ROOT / "shownotes" / "QA.txt"
MIN_SCORE = 40   # Entitaeten mit geringerem score (0-100) sind Randnennungen und verlinken nicht


def qa_ok(path=QA):
    """episode_ids (str), die die QA mit ok oder fixed fuehrt; der letzte Eintrag je Folge zaehlt. Format: episode_id;ok|fixed|redo;Datum"""
    st = {}
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            f = [x.strip() for x in line.split(";")]
            if len(f) >= 2 and f[0].isdigit(): st[f[0]] = f[1].lower()
    return {k for k, v in st.items() if v in ("ok", "fixed")}


def _num(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def load(se=SE, qa=QA):
    """-> {"by_episode": sid -> {"entities": [(slug, score)], "yt": id, "lang": l}, "by_entity": slug -> [(sid, score)]}"""
    ok, by_ep, by_ent = qa_ok(qa), {}, {}
    if se.exists():
        for f in sorted(se.glob("*.json")):
            if not f.stem.isdigit() or f.stem not in ok: continue
            try:
                d = json.loads(f.read_text("utf-8"))
            except (OSError, ValueError) as ex:
                print(f"WARNUNG: Extraktion {f.name} nicht lesbar ({ex.__class__.__name__})"); continue
            ents = {}
            for x in d.get("entities") or []:
                if not isinstance(x, dict) or not x.get("slug"): continue
                sc = _num(x.get("score"))
                if sc >= MIN_SCORE: ents[str(x["slug"])] = max(sc, ents.get(str(x["slug"]), 0))
            yt = str(d.get("youtube_video_id") or "").strip()
            by_ep[f.stem] = {"entities": sorted(ents.items(), key=lambda kv: -kv[1]), "yt": yt if 8 <= len(yt) <= 16 else "", "lang": str(d.get("lang") or "")}
            for slug, sc in ents.items(): by_ent.setdefault(slug, []).append((f.stem, sc))
    for v in by_ent.values(): v.sort(key=lambda t: -t[1])
    return {"by_episode": by_ep, "by_entity": by_ent}


X = load()
BY_EPISODE, BY_ENTITY = X["by_episode"], X["by_entity"]


def episodes_for(eid):
    """Spreaker-Folgen-IDs zur Entitaet, beste Treffer zuerst."""
    return [sid for sid, _ in BY_ENTITY.get(eid, [])]


def yt_of(sid):
    return (BY_EPISODE.get(str(sid or "")) or {}).get("yt") or ""
