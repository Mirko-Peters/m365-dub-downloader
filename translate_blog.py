"""Uebersetzer-Team fuer Mirkos englische Blog-Originale: 19 Uebersetzer-Agenten arbeiten direkt hier in Claude (Cowork/Agent-Tool), kein API-Schluessel, kein Haiku.

Ablauf einer Runde (der Projektmanager agents/blog-team/projektmanager.md steuert):
  1. python translate_blog.py prepare [--langs de,fr] [--per-agent 2]
     -> work/blog-i18n/<lang>/BRIEF.md (Profil + Regeln) und <key>.in.txt je Artikel (nur noch offene Segmente)
  2. Je Sprache ein Agent: liest BRIEF.md, schreibt zu jeder <key>.in.txt eine <key>.out.txt mit denselben Markern
  3. python translate_blog.py apply  -> Pruefung (QA), Speichern, fertige Auftraege werden entfernt, Fehler kommen in die naechste Runde
Weitere Modi: plan (Status + Rundenschaetzung), sample (Stichprobe fuer Reviews: data/blog_i18n/review/<lang>.json)
Quelle: data/podpage/blog_posts.json.gz (bis die Uebernahme in D1 fertig ist). Zwischenablage der Uebersetzungen: data/blog_i18n/<lang>/<bucket>.json.gz;
Ziel ist D1 (blog_posts je Sprache), sobald die Uebernahme der englischen Beitraege abgeschlossen ist.
"""
import gzip, hashlib, json, os, random, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "blog_i18n"
TEAM = ROOT / "agents" / "blog-team"
SRC = ROOT / "data" / "podpage" / "blog_posts.json.gz"
LANGS = ("de", "fr", "es", "it", "nl", "pt", "pl", "id", "ru", "uk", "ar", "he", "hi", "ja", "ko", "ml", "pa", "ta", "te")
NAMES = {"de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Brazilian Portuguese", "nl": "Dutch", "pl": "Polish", "id": "Indonesian", "ru": "Russian",
         "uk": "Ukrainian", "ar": "Arabic", "he": "Hebrew", "hi": "Hindi", "ja": "Japanese", "ko": "Korean", "ml": "Malayalam", "pa": "Punjabi (Gurmukhi)", "ta": "Tamil", "te": "Telugu"}
WORK = ROOT / "work" / "blog-i18n"
MODEL = os.environ.get("AGENT_MODEL", "claude-agent")   # wird nur als Herkunft gespeichert
PER_AGENT = int(os.environ.get("PER_AGENT", "2"))         # Artikel je Agent und Runde
NEW_DAYS = int(os.environ.get("NEW_DAYS", "14"))
BUCKETS = 16
# Namen, die nie uebersetzt werden duerfen (Pruefung: im Quelltext vorhanden -> muss in der Uebersetzung stehen)
KEEP = ["Microsoft 365", "Microsoft Teams", "SharePoint", "OneDrive", "Copilot Studio", "Copilot", "Power BI", "Power Apps", "Power Automate", "Power Platform", "Dataverse",
        "Azure", "Entra", "Intune", "Purview", "Defender", "Sentinel", "Fabric", "Exchange Online", "Outlook", "Excel", "PowerPoint", "Word", "Viva", "Loop", "Planner",
        "Dynamics 365", "GitHub", "Windows", "Microsoft Graph", "PowerShell", "Mirko Peters", "M365.FM", "M365 Show", "M365Con", "MVP"]
SCRIPT = {"ru": "Ѐ-ӿ", "uk": "Ѐ-ӿ", "ar": "؀-ۿ", "he": "֐-׿", "hi": "ऀ-ॿ", "ja": "぀-ヿ一-鿿",
          "ko": "가-힯ᄀ-ᇿ", "ml": "ഀ-ൿ", "pa": "਀-੿", "ta": "஀-௿", "te": "ఀ-౿"}
BLOCK = {"p", "li", "h2", "h3", "h4", "blockquote", "td", "th", "ul", "ol", "table", "thead", "tbody", "tr", "hr", "pre"}


# ---------- Quelle und Segmente ----------
def posts():
    if not SRC.exists(): return []
    ps = [p for p in json.loads(gzip.open(SRC, "rt", encoding="utf-8").read()) if p.get("title") and p.get("html")]
    ps.sort(key=lambda p: p.get("iso") or "", reverse=True)
    return ps


def segment(html_clean):
    """Zerlegt bereinigtes HTML (site_podpage.san) in Vorlage + Textsegmente. Bloecke bleiben Struktur, Inline-Inhalt wird Segment; <pre> bleibt unuebersetzt."""
    toks = re.split(r"(<[^>]+>)", html_clean)
    tpl, segs, buf, pre = [], [], [], 0

    def flush():
        s = re.sub(r"\s+", " ", "".join(buf)).strip()
        if s and re.sub(r"<[^>]+>|&\w+;|[\s\W\d_]+", "", s):
            segs.append(s); tpl.append(f"\x00{len(segs)}\x00")
        elif s: tpl.append(s)
        buf.clear()
    for t in toks:
        if not t: continue
        m = re.match(r"<\s*(/?)\s*([a-zA-Z0-9]+)", t)
        name = m.group(2).lower() if m else None
        if name == "pre":
            flush(); tpl.append(t); pre += -1 if m.group(1) else 1; pre = max(0, pre); continue
        if pre: tpl.append(t); continue
        if name in BLOCK: flush(); tpl.append(t)
        else: buf.append(t)
    flush()
    return "".join(tpl), segs


def source_of(p):
    """Alle zu uebersetzenden Einheiten eines Beitrags: T (Titel), D (Beschreibung), Q/A (FAQ), 1..n (Absaetze)."""
    import site_podpage as P
    tpl, segs = segment(P.san(p["html"]))
    units = [("T", p["title"].strip())]
    if (p.get("desc") or "").strip(): units.append(("D", p["desc"].strip()))
    for i, q in enumerate([q for q in (p.get("faq") or []) if q.get("name") and (q.get("acceptedAnswer") or {}).get("text")], 1):
        units += [(f"Q{i}", q["name"].strip()), (f"A{i}", P.plain(q["acceptedAnswer"]["text"]))]
    units += [(str(i), s) for i, s in enumerate(segs, 1)]
    h = hashlib.sha1(json.dumps(units, ensure_ascii=False).encode()).hexdigest()[:16]
    return tpl, units, h


def key(slug): return hashlib.sha1(slug.encode()).hexdigest()[:12]
def bucket(slug): return int(hashlib.sha1(slug.encode()).hexdigest()[:2], 16) % BUCKETS


# ---------- Speicher ----------
def load_lang(lang):
    d = OUT / lang; res = {}
    if d.exists():
        for f in sorted(d.glob("*.json.gz")): res.update(json.loads(gzip.open(f, "rt", encoding="utf-8").read()))
    return res


def save_lang(lang, data, only_buckets=None):
    d = OUT / lang; d.mkdir(parents=True, exist_ok=True)
    by = {}
    for s, r in data.items(): by.setdefault(bucket(s), {})[s] = r
    for b in range(BUCKETS):
        if only_buckets is not None and b not in only_buckets: continue
        f = d / f"{b:02x}.json.gz"
        if by.get(b): f.write_bytes(gzip.compress(json.dumps(by[b], ensure_ascii=False, sort_keys=True).encode(), mtime=0))
        elif f.exists(): f.unlink()


def jload(name, default):
    f = OUT / name
    return json.loads(f.read_text("utf-8")) if f.exists() else default


def jsave(name, obj):
    OUT.mkdir(parents=True, exist_ok=True); (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def assemble(p, rec):
    """Fertige Sprachfassung: (titel, beschreibung, html, faq) oder None, solange nicht vollstaendig."""
    if not rec or not rec.get("ok"): return None
    import site_podpage as P
    tpl, units, h = source_of(p)
    if rec.get("h") != h: return None   # Original wurde geaendert -> alte Uebersetzung nicht mehr anzeigen
    sg = rec["seg"]
    html = re.sub("\x00(\\d+)\x00", lambda m: sg.get(m.group(1), ""), tpl)
    faq, i = [], 1
    while f"Q{i}" in sg:
        faq.append({"@type": "Question", "name": sg[f"Q{i}"], "acceptedAnswer": {"@type": "Answer", "text": sg.get(f"A{i}", "")}}); i += 1
    return sg.get("T", p["title"]), sg.get("D", ""), html, faq


# ---------- Agenten-Profile ----------
from functools import lru_cache


@lru_cache(None)
def profile(lang):
    f = TEAM / "uebersetzer" / f"{lang}.md"
    t = f.read_text("utf-8") if f.exists() else ""
    return re.sub(r"^---.*?---\s*", "", t, flags=re.S).strip()


@lru_cache(None)
def system_prompt(lang):
    return (f"You are the {NAMES[lang]} translator agent of the M365.FM translation team. You translate English blog articles written by Microsoft MVP Mirko Peters "
            f"(Microsoft 365, Azure, Power Platform, Copilot, security) into natural, fluent, professional {NAMES[lang]} for IT professionals and decision makers.\n\n"
            "TEAM RULES (always):\n"
            "1. Translate meaning, not word for word. It must read as if written natively. Do not add, drop, summarise or comment on content.\n"
            "2. NEVER translate names: product and feature brand names (Microsoft 365, Copilot, Teams, SharePoint, Power BI, Entra ID, Purview, Fabric ...), "
            "people, companies, events (M365.FM, M365 Show, M365Con), session and episode titles in quotes, code, cmdlets, file names, URLs, licence SKUs (E3, E5).\n"
            "3. Keep every inline HTML tag and its attributes exactly as in the source (<strong>, <em>, <a href=\"...\">, <code>, <br>, <img ...>); translate only the text between tags. "
            "Keep HTML entities valid. Never translate text inside <code>.\n"
            "4. Output format: the same markers as the input ([[T]], [[D]], [[Q1]], [[A1]], [[1]], [[2]] ...), each marker at the start of a new line followed by its translation, "
            "same order, every marker exactly once, nothing else (no intro, no notes, no code fences).\n"
            "5. Follow your language profile below (style, address form, typography, Microsoft terminology, glossary). The glossary wins over your own preference.\n\n"
            f"YOUR LANGUAGE PROFILE ({lang}):\n{profile(lang)}")


# ---------- Pruefung (QA) ----------
TAG = re.compile(r"<\s*(/?[a-zA-Z0-9]+)")
HREF = re.compile(r'href="([^"]*)"')


def qa(lang, src, out):
    """Gibt (ok, grund, warnung) zurueck. Harte Fehler -> Segment wird nicht gespeichert und spaeter neu uebersetzt."""
    if not out.strip(): return False, "leer", None
    if sorted(TAG.findall(src)) != sorted(TAG.findall(out)): return False, "html-tags", None
    if sorted(HREF.findall(src)) != sorted(HREF.findall(out)): return False, "links", None
    alpha = re.sub(r"<[^>]+>|&\w+;|[\W\d_]", "", out)
    if lang in SCRIPT and len(re.sub(r"<[^>]+>|&\w+;|[\W\d_]", "", src)) >= 20:
        own = len(re.findall(f"[{SCRIPT[lang]}]", alpha))
        if own < 0.25 * max(1, len(alpha)): return False, "falsche-schrift", None
    words = re.findall(r"[a-zA-Z]+", re.sub(r"<[^>]+>", " ", src))
    if lang not in SCRIPT and out.strip() == src.strip() and len(words) >= 8: return False, "unuebersetzt", None
    if len(src) >= 80 and not (0.3 <= len(out) / len(src) <= 5): return False, "laenge", None
    miss = [k for k in KEEP if re.search(rf"(?<!\w){re.escape(k)}(?!\w)", src) and k not in out]
    return True, None, (("name-fehlt:" + ",".join(miss[:4])) if miss else None)


MARK = re.compile(r"^\s*\[\[([TD]|[QA]\d+|\d+)\]\]\s?", re.M)


def parse(text):
    parts = MARK.split(text.strip())
    res = {}
    for i in range(1, len(parts) - 1, 2):
        res[parts[i]] = parts[i + 1].strip()
    return res


# ---------- Runden fuer die Agenten ----------
def pick(a, lang, have, ps, busy):
    n = a["per_agent"] or PER_AGENT
    out = []
    for p in ps:
        if len(out) >= n: break
        if p["slug"] in busy: continue
        tpl, units, h = source_of(p); rec = have.get(p["slug"])
        if a["redo"] or not rec or rec.get("h") != h: rec = {"h": h, "n": len(units), "seg": {}, "ok": False}
        if rec.get("ok"): continue
        out.append((p, units, h, rec))
    return out


def prepare(a):
    """Legt fuer jede Sprache die Auftraege der naechsten Runde an (bestehende, noch nicht angewendete Auftraege bleiben)."""
    langs, ps = select(a, posts()); total = 0
    for lang in langs:
        d = WORK / lang; d.mkdir(parents=True, exist_ok=True)
        busy = {json.loads(f.read_text("utf-8").split("\n", 1)[0][2:]).get("slug") for f in d.glob("*.in.txt")}
        have = load_lang(lang); new = pick(a, lang, have, ps, busy)
        for p, units, h, rec in new:
            todo = [(i, t) for i, t in units if i not in rec["seg"]]
            head = json.dumps({"slug": p["slug"], "h": h, "lang": lang}, ensure_ascii=False)
            (d / f"{key(p['slug'])}.in.txt").write_text(f"# {head}\n" + "\n".join(f"[[{i}]] {t}" for i, t in todo) + "\n", encoding="utf-8")
        (d / "BRIEF.md").write_text(system_prompt(lang) + f"""

## YOUR JOB IN THIS ROUND
In the folder {d} you find one or more files `<id>.in.txt`. The first line (starting with `# {{`) is metadata - do not translate it.
For EACH `<id>.in.txt` write a file `<id>.out.txt` in the same folder that contains ONLY the translated segments:
every marker line from the input ([[T]], [[D]], [[Q1]], [[A1]], [[1]] ...) exactly once, same order, marker at the start of the line, followed by the {NAMES[lang]} translation.
No metadata line, no comments, no code fences. Translate the whole file, never stop early, never summarise. Long files: write the output in one go with the Write tool.
When done, answer with one line per file: `<id>: <number of segments> segments`.
""", encoding="utf-8")
        jobs = sorted(f.name for f in d.glob("*.in.txt")); total += len(jobs)
        print(f"{lang}: {len(jobs)} Auftraege ({len(new)} neu) in {d}")
    return total


def apply(a=None):
    """Prueft alle <id>.out.txt, speichert gute Segmente, entfernt erledigte Auftraege, schreibt offene Segmente zurueck in die .in.txt."""
    stats = {}
    for d in sorted(WORK.glob("*")) if WORK.exists() else []:
        lang = d.name
        if lang not in LANGS: continue
        have = load_lang(lang); touched = set(); qa_log = []; ok = bad = done = 0; why = {}
        for fin in sorted(d.glob("*.in.txt")):
            fout = fin.with_name(fin.name.replace(".in.txt", ".out.txt"))
            if not fout.exists(): continue
            meta = json.loads(fin.read_text("utf-8").split("\n", 1)[0][2:]); p = BY_SLUG.get(meta["slug"])
            if not p: fin.unlink(); fout.unlink(); continue
            tpl, units, h = source_of(p)
            if h != meta["h"]: fin.unlink(); fout.unlink(); continue   # Original geaendert -> neu vorbereiten
            src = dict(units); rec = have.get(p["slug"])
            if not rec or rec.get("h") != h: rec = {"h": h, "n": len(units), "seg": {}, "ok": False}
            for i, t in parse(fout.read_text("utf-8")).items():
                if i not in src: continue
                good, reason, warn = qa(lang, src[i], t)
                if good:
                    rec["seg"][i] = __import__("site_podpage").san(t) if ("<" in t or "&" in t) else t; ok += 1
                    if warn: qa_log.append({"slug": p["slug"], "seg": i, "warn": warn})
                else:
                    bad += 1; why[reason] = why.get(reason, 0) + 1
                    qa_log.append({"slug": p["slug"], "seg": i, "fehler": reason, "src": src[i][:160], "out": t[:160]})
            rec["ok"] = all(i in rec["seg"] for i in src); rec["m"] = MODEL; rec["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            have[p["slug"]] = rec; touched.add(bucket(p["slug"])); fout.unlink()
            if rec["ok"]: fin.unlink(); done += 1
            else:
                todo = [(i, t) for i, t in units if i not in rec["seg"]]
                fin.write_text(fin.read_text("utf-8").split("\n", 1)[0] + "\n" + "\n".join(f"[[{i}]] {t}" for i, t in todo) + "\n", encoding="utf-8")
        if touched: save_lang(lang, have, touched)
        if qa_log:
            (OUT / "qa").mkdir(parents=True, exist_ok=True); f = OUT / "qa" / f"{lang}.json"
            old = json.loads(f.read_text("utf-8")) if f.exists() else []
            f.write_text(json.dumps((old + qa_log)[-500:], ensure_ascii=False, indent=1), encoding="utf-8")
        stats[lang] = {"artikel_fertig": done, "segmente_ok": ok, "segmente_fehler": bad, "gruende": why, "offen": len(list(d.glob("*.in.txt")))}
        print(lang, stats[lang])
    log = jload("rounds.json", []); log.append({"ts": datetime.now(timezone.utc).isoformat()[:19], "stats": stats}); jsave("rounds.json", log[-300:])
    return stats


def select(a, ps):
    langs = a["langs"]; sl = set(a["slugs"])
    if sl: ps = [p for p in ps if p["slug"] in sl]
    if a["mode"] == "auto":
        lim = (datetime.now(timezone.utc) - timedelta(days=NEW_DAYS)).isoformat()
        ps = [p for p in ps if (p.get("iso") or "") >= lim]
    if a["order"] == "oldest": ps = list(reversed(ps))
    return langs, ps


def status():
    ps = posts(); per_round = len(LANGS) * PER_AGENT
    st = {"updated": datetime.now(timezone.utc).isoformat()[:19], "posts": len(ps), "engine": "Claude-Agenten (Cowork)", "per_agent": PER_AGENT, "langs": {}}
    srcs = {p["slug"]: source_of(p)[2] for p in ps}; left = 0
    for lang in LANGS:
        have = load_lang(lang)
        done = sum(1 for p in ps if (have.get(p["slug"]) or {}).get("ok") and have[p["slug"]].get("h") == srcs[p["slug"]])
        qf = OUT / "qa" / f"{lang}.json"; ql = json.loads(qf.read_text("utf-8")) if qf.exists() else []
        st["langs"][lang] = {"name": NAMES[lang], "done": done, "open": len(ps) - done, "pct": round(100 * done / max(1, len(ps)), 1),
                             "qa_errors_logged": sum(1 for x in ql if x.get("fehler")), "jobs_waiting": len(list((WORK / lang).glob("*.in.txt"))) if (WORK / lang).exists() else 0}
        left += len(ps) - done
    st["open_translations"] = left; st["rounds_left"] = -(-left // per_round)
    jsave("status.json", st)
    print(f"{st['posts']} Artikel x 19 Sprachen | offen {left} Uebersetzungen | ~{st['rounds_left']} Runden a {per_round} (19 Agenten x {PER_AGENT})")
    for l, v in st["langs"].items(): print(f"  {l:3} {v['done']:5}/{st['posts']} fertig ({v['pct']} %)")
    return st


def sample(a):
    import site_podpage as P
    ps = posts(); random.seed(a.get("seed") or None)
    for lang in a["langs"]:
        have = load_lang(lang); okp = [p for p in ps if assemble(p, have.get(p["slug"]))]
        pick = random.sample(okp, min(a["limit"] or 3, len(okp)))
        res = []
        for p in pick:
            t, d, h, _ = assemble(p, have[p["slug"]]); tpl, units, _h = source_of(p)
            res.append({"slug": p["slug"], "url": f"https://www.m365.fm/{lang}/show/blog/{p['slug']}/", "pairs": [{"id": i, "en": s, lang: have[p["slug"]]["seg"].get(i, "")} for i, s in units][:60]})
        (OUT / "review").mkdir(parents=True, exist_ok=True)
        (OUT / "review" / f"{lang}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(lang, len(res), "Beitraege ->", OUT / "review" / f"{lang}.json")


def args():
    a = sys.argv[1:]
    def opt(n, d=""):
        return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else d
    mode = a[0] if a and not a[0].startswith("-") else "plan"
    langs = [l for l in (opt("--langs") or ",".join(LANGS)).split(",") if l in LANGS]
    return {"mode": mode, "langs": langs, "limit": int(opt("--limit", "0") or 0), "per_agent": int(opt("--per-agent", "0") or 0), "order": opt("--order", "newest"),
            "slugs": [s for s in opt("--slugs").split(",") if s], "redo": "--redo" in a, "seed": opt("--seed")}


BY_SLUG = {}


def main():
    a = args(); BY_SLUG.update({p["slug"]: p for p in posts()})
    m = a["mode"]
    if m == "prepare": prepare(a)
    elif m == "apply": apply(a); status()
    elif m == "sample": sample(a)
    else: status()


if __name__ == "__main__":
    main()
