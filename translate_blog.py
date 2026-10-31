"""Uebersetzer-Team fuer Mirkos englische Blog-Originale in 14 Sprachen. Zwei Wege, gleiche Profile, gleiche Pruefung:

A) Haiku im Message Batch (guenstig, fuer die Masse) - laeuft als GitHub-Workflow translate-blog.yml:
   plan     Status + Kostenschaetzung (ohne Schluessel)
   submit   offene Uebersetzungen als Batch(es) absenden (Budget-Deckel BLOG_BUDGET_USD)
   collect  fertige Batches abholen, pruefen (QA), speichern
   run      collect -> submit -> warten (WAIT_MIN) -> collect;  auto = run nur fuer Artikel der letzten NEW_DAYS Tage
B) Claude-Agenten hier in Claude (Cowork, ohne API) - fuer Nacharbeit, Reviews, wichtige Artikel:
   prepare  -> work/blog-i18n/<lang>/BRIEF.md + <key>.in.txt;  Agent schreibt <key>.out.txt;  apply -> pruefen, speichern
sample: Stichprobe fuer die Review-Agenten (data/blog_i18n/review/<lang>.json)
Optionen: --langs de,fr  --limit N (Artikel je Sprache, Batch)  --per-agent N  --order newest|oldest  --slugs a,b  --redo
Profile: agents/blog-team/uebersetzer/<lang>.md (Systemprompt je Sprache). Quelle: data/podpage/blog_posts.json.gz (dieselben Beitraege liegen inzwischen in D1).
Zwischenablage: data/blog_i18n/<lang>/<bucket>.json.gz {slug: {h, n, seg{id: text}, ok, m, ts}}; Ziel D1 (blog_posts je Sprache) folgt.
"""
import gzip, hashlib, json, os, random, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "blog_i18n"
TEAM = ROOT / "agents" / "blog-team"
SRC = ROOT / "data" / "podpage" / "blog_posts.json.gz"
LANGS = ("de", "fr", "es", "it", "nl", "pt", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko")
NAMES = {"de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Brazilian Portuguese", "nl": "Dutch", "pl": "Polish", "id": "Indonesian", "ru": "Russian",
         "uk": "Ukrainian", "ar": "Arabic", "he": "Hebrew", "ja": "Japanese", "ko": "Korean"}
WORK = ROOT / "work" / "blog-i18n"
MODEL = os.environ.get("TRANSLATE_MODEL", "claude-haiku-5-5")
AGENT_MODEL = os.environ.get("AGENT_MODEL", "claude-agent")   # Herkunft bei Weg B
# Haiku 5.5 im Message Batch (50 % Rabatt, Prompts bis 100K Tokens), $ je 1 Mio. Tokens
PRICE_IN, PRICE_OUT = float(os.environ.get("PRICE_IN", "0.05")), float(os.environ.get("PRICE_OUT", "0.25"))
BUDGET = float(os.environ.get("BLOG_BUDGET_USD") or "10")
CHUNK = int(os.environ.get("CHUNK_CHARS", "4500"))        # Quelltext je Batch-Anfrage
MAX_TOK = int(os.environ.get("MAX_TOKENS", "16000"))
PER_BATCH = int(os.environ.get("PER_BATCH", "5000"))
WAIT_MIN = int(os.environ.get("WAIT_MIN", "300"))
# Ausgabe-Tokens je Quell-Token (Schaetzung bis Messwerte in usage.json da sind)
FACTOR = {**{l: 1.5 for l in LANGS}, "ru": 2.2, "uk": 2.2, "ar": 2.2, "he": 2.2, "ja": 1.8, "ko": 2.0}
PER_AGENT = int(os.environ.get("PER_AGENT", "2"))         # Artikel je Agent und Runde
NEW_DAYS = int(os.environ.get("NEW_DAYS", "14"))
BUCKETS = 16
# Namen, die nie uebersetzt werden duerfen (Pruefung: im Quelltext vorhanden -> muss in der Uebersetzung stehen)
KEEP = ["Microsoft 365", "Microsoft Teams", "SharePoint", "OneDrive", "Copilot Studio", "Copilot", "Power BI", "Power Apps", "Power Automate", "Power Platform", "Dataverse",
        "Azure", "Entra", "Intune", "Purview", "Defender", "Sentinel", "Fabric", "Exchange Online", "Outlook", "Excel", "PowerPoint", "Word", "Viva", "Loop", "Planner",
        "Dynamics 365", "GitHub", "Windows", "Microsoft Graph", "PowerShell", "Mirko Peters", "M365.FM", "M365 Show", "M365Con", "MVP"]
SCRIPT = {"ru": "Ѐ-ӿ", "uk": "Ѐ-ӿ", "ar": "؀-ۿ", "he": "֐-׿", "ja": "぀-ヿ一-鿿",
          "ko": "가-힯ᄀ-ᇿ"}
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


def user_prompt(lang, units):
    body = "\n".join(f"[[{i}]] {t}" for i, t in units)
    return f"Translate every segment into {NAMES[lang]}. Keep the markers.\n\n{body}"


def chunks(units, have):
    """Offene Einheiten in Anfragen zu ~CHUNK Zeichen; T/D/FAQ zuerst."""
    todo = [(i, t) for i, t in units if i not in have]
    out, cur, n = [], [], 0
    for u in todo:
        if cur and n + len(u[1]) > CHUNK: out.append(cur); cur, n = [], 0
        cur.append(u); n += len(u[1])
    if cur: out.append(cur)
    return out


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
            rec["ok"] = all(i in rec["seg"] for i in src); rec["m"] = AGENT_MODEL; rec["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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


# ---------- API ----------
def api(method, path, body=None, raw=False):
    req = urllib.request.Request(path if path.startswith("http") else "https://api.anthropic.com" + path,
                                 json.dumps(body).encode() if body is not None else None,
                                 {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"}, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=900).read()
        return r if raw else json.loads(r)
    except urllib.error.HTTPError as e:
        msg = f"API-Fehler {e.code} {method} {path}: {e.read()[:600]!r}"; print(msg)
        OUT.mkdir(parents=True, exist_ok=True); (OUT / "last_error.txt").write_text(msg); raise


def cost(tin, tout): return tin * PRICE_IN / 1e6 + tout * PRICE_OUT / 1e6


def measured_factor(lang):
    u = jload("usage.json", {}).get("by_lang", {}).get(lang)
    return (u["output_tokens"] / max(1, u["input_tokens"] - u.get("system_tokens", 0))) if u and u.get("input_tokens", 0) > 20000 else FACTOR[lang]


def est(lang, units):
    src_tok = sum(len(t) for _, t in units) / 4
    sys_tok = len(system_prompt(lang)) / 3.5
    n_req = max(1, -(-sum(len(t) for _, t in units) // CHUNK))
    return n_req * sys_tok + src_tok * 1.1, src_tok * measured_factor(lang)


def pending_cost(): return sum(b.get("est_usd", 0) for b in jload("batches.json", []))


def spent(): u = jload("usage.json", {}); return cost(u.get("input_tokens", 0), u.get("output_tokens", 0))


def submit(a):
    langs, ps = select(a, posts())
    busy = {(b2["lang"], b2["slug"]) for b in jload("batches.json", []) for b2 in b.get("items", [])}
    reqs, items, money = [], [], 0.0
    room = BUDGET - spent() - pending_cost()
    for lang in langs:
        have = load_lang(lang); sysp = system_prompt(lang); n_posts = 0
        for p in ps:
            if a["limit"] and n_posts >= a["limit"]: break
            if (lang, p["slug"]) in busy: continue
            tpl, units, h = source_of(p)
            rec = have.get(p["slug"])
            if a["redo"] or not rec or rec.get("h") != h: rec = {"h": h, "n": len(units), "seg": {}, "ok": False}
            if rec.get("ok"): continue
            n_posts += 1
            cs = chunks(units, rec["seg"])
            ti, to = est(lang, [u for c in cs for u in c]); c_usd = cost(ti, to)
            if money + c_usd > room:
                print(f"Budget erreicht ({BUDGET:.2f} $; bisher {spent():.2f} $, offen {pending_cost():.2f} $) - Rest bleibt fuer spaeter"); break
            money += c_usd
            for ci, c in enumerate(cs):
                reqs.append({"custom_id": f"{lang}_{key(p['slug'])}_{ci}", "params": {"model": MODEL, "max_tokens": MAX_TOK,
                             "system": [{"type": "text", "text": sysp, "cache_control": {"type": "ephemeral"}}],
                             "messages": [{"role": "user", "content": user_prompt(lang, c)}]}})
            items.append({"lang": lang, "slug": p["slug"], "h": h, "n": len(units)})
            if a["redo"]: have[p["slug"]] = rec
        if a["redo"]: save_lang(lang, have)
    if not reqs:
        print("Nichts abzusenden."); return 0
    bl = jload("batches.json", [])
    for i in range(0, len(reqs), PER_BATCH):
        part = reqs[i:i + PER_BATCH]
        ids = {r["custom_id"].rsplit("_", 1)[0] for r in part}
        its = [it for it in items if f"{it['lang']}_{key(it['slug'])}" in ids]
        share = money * len(part) / len(reqs)
        b = api("POST", "/v1/messages/batches", {"requests": part})
        bl.append({"id": b["id"], "n": len(part), "model": MODEL, "created": datetime.now(timezone.utc).isoformat()[:19], "est_usd": round(share, 3), "items": its})
        jsave("batches.json", bl); print("Batch", b["id"], len(part), "Anfragen, geschaetzt", round(share, 2), "$")
    return len(reqs)


def collect():
    bl = jload("batches.json", []); left = []; usage = jload("usage.json", {"input_tokens": 0, "output_tokens": 0, "runs": [], "by_lang": {}})
    for b in bl:
        st = api("GET", f"/v1/messages/batches/{b['id']}")
        if st["processing_status"] != "ended": print(b["id"], st["processing_status"], st["request_counts"]); left.append(b); continue
        info = {(it["lang"], key(it["slug"])): it for it in b["items"]}
        data, touched, qa_log = {}, {}, {}
        tin = tout = ok = bad = 0; why = {}
        for line in api("GET", st["results_url"], raw=True).decode().splitlines():
            r = json.loads(line); lang, k, _ = r["custom_id"].split("_")
            it = info.get((lang, k))
            if not it: continue
            if lang not in data: data[lang] = load_lang(lang); touched[lang] = set()
            res = r["result"]
            if res["type"] != "succeeded": bad += 1; why[res["type"]] = why.get(res["type"], 0) + 1; continue
            msg = res["message"]; u = msg["usage"]
            ti = u["input_tokens"] + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0); tin += ti; tout += u["output_tokens"]
            bl_ = usage["by_lang"].setdefault(lang, {"input_tokens": 0, "output_tokens": 0, "system_tokens": 0})
            bl_["input_tokens"] += ti; bl_["output_tokens"] += u["output_tokens"]; bl_["system_tokens"] += int(len(system_prompt(lang)) / 3.5)
            text = "".join(c.get("text", "") for c in msg["content"] if c.get("type") == "text")
            got = parse(text)
            if msg.get("stop_reason") == "max_tokens" and got: got.pop(list(got)[-1]); why["max_tokens"] = why.get("max_tokens", 0) + 1
            p = BY_KEY.get(k)
            if not p: continue
            tpl, units, h = source_of(p)
            if h != it["h"]: continue   # Original inzwischen geaendert
            src = dict(units)
            rec = data[lang].get(p["slug"])
            if not rec or rec.get("h") != h: rec = {"h": h, "n": len(units), "seg": {}, "ok": False}
            for i, t in got.items():
                if i not in src: continue
                good, reason, warn = qa(lang, src[i], t)
                if good:
                    rec["seg"][i] = __import__("site_podpage").san(t) if "<" in t or "&" in t else t; ok += 1
                    if warn: qa_log.setdefault(lang, []).append({"slug": p["slug"], "seg": i, "warn": warn})
                else:
                    bad += 1; why[reason] = why.get(reason, 0) + 1
                    qa_log.setdefault(lang, []).append({"slug": p["slug"], "seg": i, "fehler": reason, "src": src[i][:160], "out": t[:160]})
            rec["ok"] = all(i in rec["seg"] for i in src); rec["m"] = MODEL; rec["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            data[lang][p["slug"]] = rec; touched[lang].add(bucket(p["slug"]))
        for lang, d in data.items(): save_lang(lang, d, touched[lang])
        for lang, lg in qa_log.items():
            (OUT / "qa").mkdir(parents=True, exist_ok=True)
            f = OUT / "qa" / f"{lang}.json"; old = json.loads(f.read_text("utf-8")) if f.exists() else []
            f.write_text(json.dumps((old + lg)[-500:], ensure_ascii=False, indent=1), encoding="utf-8")
        usage["input_tokens"] += tin; usage["output_tokens"] += tout
        usage["runs"].append({"batch": b["id"], "model": b["model"], "segments_ok": ok, "segments_failed": bad, "why": why, "input_tokens": tin, "output_tokens": tout, "cost_usd": round(cost(tin, tout), 3)})
        jsave("usage.json", usage); print(f"{b['id']}: {ok} Segmente ok, {bad} fehlgeschlagen {why}, Kosten {cost(tin, tout):.3f} $")
    jsave("batches.json", left)
    return len(left)


def status():
    ps = posts(); per_round = len(LANGS) * PER_AGENT
    st = {"updated": datetime.now(timezone.utc).isoformat()[:19], "posts": len(ps), "engine": f"{MODEL} (Batch) + Claude-Agenten", "per_agent": PER_AGENT,
          "budget_usd": BUDGET, "spent_usd": round(spent(), 3), "pending_batches": len(jload("batches.json", [])), "pending_est_usd": round(pending_cost(), 3), "langs": {}}
    srcs0 = {p["slug"]: source_of(p) for p in ps}; srcs = {k: v[2] for k, v in srcs0.items()}; left = 0; all_ti = all_to = 0
    for lang in LANGS:
        have = load_lang(lang)
        done = sum(1 for p in ps if (have.get(p["slug"]) or {}).get("ok") and have[p["slug"]].get("h") == srcs[p["slug"]])
        ti = to = 0
        for p in ps:
            rec = have.get(p["slug"]) or {}
            if rec.get("ok") and rec.get("h") == srcs[p["slug"]]: continue
            seg = rec.get("seg", {}) if rec.get("h") == srcs[p["slug"]] else {}
            x, y = est(lang, [u for u in srcs0[p["slug"]][1] if u[0] not in seg]); ti += x; to += y
        all_ti += ti; all_to += to
        qf = OUT / "qa" / f"{lang}.json"; ql = json.loads(qf.read_text("utf-8")) if qf.exists() else []
        st["langs"][lang] = {"name": NAMES[lang], "done": done, "open": len(ps) - done, "pct": round(100 * done / max(1, len(ps)), 1), "rest_est_usd": round(cost(ti, to), 2), "out_factor": round(measured_factor(lang), 2),
                             "qa_errors_logged": sum(1 for x in ql if x.get("fehler")), "jobs_waiting": len(list((WORK / lang).glob("*.in.txt"))) if (WORK / lang).exists() else 0}
        left += len(ps) - done
    st["open_translations"] = left; st["rounds_left"] = -(-left // per_round); st["rest_est_usd_all"] = round(cost(all_ti, all_to), 2)
    jsave("status.json", st)
    print(f"{st['posts']} Artikel x 19 Sprachen | offen {left} Uebersetzungen | Haiku-Batch ~{st['rest_est_usd_all']} $ (ausgegeben {st['spent_usd']} von {BUDGET} $) | Agenten ~{st['rounds_left']} Runden")
    for l, v in st["langs"].items(): print(f"  {l:3} {v['done']:5}/{st['posts']} fertig ({v['pct']} %), Rest ~{v['rest_est_usd']} $")
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
BY_KEY = {}


def main():
    a = args(); ps = posts(); BY_SLUG.update({p["slug"]: p for p in ps}); BY_KEY.update({key(p["slug"]): p for p in ps})
    m = a["mode"]
    if m == "prepare": prepare(a); return
    if m == "apply": apply(a); status(); return
    if m == "sample": sample(a); return
    if m in ("collect", "run", "auto"): collect()
    if m in ("submit", "run", "auto"): submit(a)
    if m in ("run", "auto"):
        t0 = time.time()
        while jload("batches.json", []) and time.time() - t0 < WAIT_MIN * 60:
            time.sleep(120)
            if collect() == 0: break
    status()


if __name__ == "__main__":
    main()
