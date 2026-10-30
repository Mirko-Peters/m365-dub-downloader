"""Folgen einer Show mit den Folgen auf anderen Plattformen (Apple Podcasts, Spotify, Deezer, YouTube ...) zusammenfuehren.
Reine Funktionen (kein Netz): normalize, score, match. Jede Plattform liefert Kandidaten {title, url, date, duration}; match() ordnet sie den eigenen Folgen zu.
Zuordnung nur bei eindeutigem Treffer: gleicher Titel, oder sehr aehnlicher Titel (+ Datum innerhalb weniger Tage); sonst landet die Folge im Bericht 'offen'."""
import re
from datetime import date
from difflib import SequenceMatcher

_SUFFIX = re.compile(r"\s*[\(\[](?:ki|ai|dub|dubbed|synchron|synchronfassung|ki-synchronfassung|ai dub|ai-dub|audio|video)[^)\]]*[\)\]]\s*$", re.I)
_STOP = re.compile(r"\b(episode|folge|ep|podcast|the|der|die|das|a|an|und|and|und)\b", re.I)


def normalize(t):
    t = _SUFFIX.sub("", t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.casefold()
    t = re.sub(r"[\W_]+", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(t):
    return set(_STOP.sub(" ", normalize(t)).split())


def _day(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except Exception:
        return None


def score(a, b):
    """Aehnlichkeit zweier Titel 0..1: exakt normalisiert = 1, sonst Mischung aus Zeichen- und Wortuebereinstimmung."""
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = _tokens(a), _tokens(b)
    jac = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    pre = 1.0 if (len(na) >= 20 and (na.startswith(nb) or nb.startswith(na))) else 0.0   # gekuerzter Titel (Plattformen schneiden ab)
    return max(0.55 * seq + 0.45 * jac, 0.95 * pre)


def match(own, cands, min_score=0.9, date_window=3, date_min=0.82, margin=0.03):
    """own: {schluessel: {title, date}}, cands: [{title, url, date}] -> (treffer {schluessel: url}, offen [schluessel], mehrdeutig [schluessel]).
    Ein Kandidat wird nur einer Folge zugeordnet (beste Uebereinstimmung gewinnt); Kandidaten mit gleicher Punktzahl bei zwei Folgen werden nicht geraten."""
    pairs = []
    for k, o in own.items():
        od = _day(o.get("date"))
        for ci, c in enumerate(cands):
            s = score(o.get("title"), c.get("title"))
            cd = _day(c.get("date"))
            near = od and cd and abs((od - cd).days) <= date_window
            if od and cd and abs((od - cd).days) > 45:
                continue   # Datum passt nicht: kein Treffer
            ok = s >= min_score or (s >= date_min and near)
            if ok:
                pairs.append((s + (0.05 if near else 0.0), k, ci))
    pairs.sort(reverse=True)
    best, used_c, amb = {}, set(), set()
    by_k, by_c = {}, {}
    for s, k, ci in pairs:
        by_k.setdefault(k, []).append((s, ci))
        by_c.setdefault(ci, []).append((s, k))
    for s, k, ci in pairs:
        if k in best or ci in used_c or k in amb:
            continue
        rivals = [x for x in by_c[ci] if x[1] != k and x[1] not in best and x[0] >= s - margin]
        if rivals:   # derselbe Kandidat passt zu mehreren eigenen Folgen gleich gut (z. B. gleicher Titel): nicht raten
            amb.add(k); amb.update(x[1] for x in rivals); used_c.add(ci)
            continue
        others = [x for x in by_k[k] if x[1] != ci and x[1] not in used_c]
        if others and others[0][0] >= s - margin and cands[others[0][1]].get("url") != cands[ci].get("url"):
            amb.add(k); continue
        best[k] = cands[ci]["url"]; used_c.add(ci)
    open_ = [k for k in own if k not in best and k not in amb]
    return best, open_, sorted(amb)
