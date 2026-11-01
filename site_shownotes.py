"""T26: Episodenseiten aus den Shownotes-Vollfassungen shownotes/site/<spreaker_episode_id>.md (Shownotes-Generator, Ticket T24/T26).

Datei = Frontmatter (--- ... ---: episode_id, slug, lang, title, hook, chapters, takeaways, entities, related_episode, best_of_category,
faq, generated_at) + Markdown-Text (Hook, "In this episode"/"In dieser Folge" mit Kapiteln "mm:ss – Titel", "Key takeaways",
"Explore more on M365.FM", Call-to-Action, FAQ-Block). Der Text wird tolerant gelesen: Frontmatter per PyYAML, wenn vorhanden,
sonst mit einem kleinen Leser fuer Schluessel, Listen und Listen von Objekten; Markdown mit einem kleinen Umsetzer (Ueberschriften,
Absaetze, Listen, fett, Links). Entitaets-Links (www.m365.fm/entity/<id>/ bzw. /<lang>/entity/<id>/) bekommen die Kurzbeschreibung
als Hover (a.gl, data-gt/data-gd; Tooltip-Skript in assets/page.js). FAQ wird als <details> plus FAQPage-Schema ausgegeben.
Oeffentliche Funktionen: load_all() -> {episode_id: rec}; render(rec, lang, ents, base) -> (html, jsonld_list, faq_list)."""
import html as _html
import json
import re
from pathlib import Path
import site_quotes as SQ

ROOT = Path(__file__).resolve().parent
SN_DIR = ROOT / "shownotes" / "site"
esc = lambda s: _html.escape(str(s if s is not None else ""), quote=True)
_ENT_URL = re.compile(r"^https?://(?:www\.)?m365\.fm/(?:[a-z]{2}/)?entity/([a-z0-9-]+)/?(?:[?#].*)?$")
_FAQ_H = re.compile(r"^(faq|frequently asked questions|h[aä]ufige fragen|fragen und antworten|preguntas frecuentes|questions fr[ée]quentes|domande frequenti|perguntas frequentes|veelgestelde vragen|najcz[eę]stsze pytania|pertanyaan umum|часто задаваемые вопросы|часті запитання|الأسئلة الشائعة|שאלות נפוצות|よくある質問|자주 묻는 질문)\b", re.I)
_TIME = re.compile(r"^\s*(?:\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?)\s*[–—-]\s*(.+)$")


# ---------------------------------------------------------------- Frontmatter
def _yaml_min(text):
    """Kleiner YAML-Leser: key: wert | key: [a, b] | key:\\n  - wert | key:\\n  - k: v\\n    k2: v2 (keine Verschachtelung darueber hinaus)."""
    out, key, cur = {}, None, None
    def val(v):
        v = v.strip()
        if v[:1] in "\"'" and v[-1:] == v[:1]: return v[1:-1]
        if v.startswith("[") and v.endswith("]"): return [val(x) for x in re.split(r",(?![^\[]*\])", v[1:-1]) if x.strip()]
        if v.lower() in ("true", "false"): return v.lower() == "true"
        if v.lower() in ("null", "~", ""): return "" if v == "" else None
        if re.fullmatch(r"-?\d+", v): return int(v)
        if re.fullmatch(r"-?\d+\.\d+", v): return float(v)
        return v
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"): continue
        ind = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if ind == 0 and re.match(r"^[A-Za-z_][\w-]*\s*:", line):
            key, v = line.split(":", 1); key = key.strip(); v = v.strip()
            out[key] = val(v) if v else []; cur = None
        elif key is not None and line.startswith("- "):
            item = line[2:].strip()
            if not isinstance(out[key], list): out[key] = []
            if re.match(r"^[A-Za-z_][\w-]*\s*:\s*", item) and not item.startswith("http"):   # Objekt in der Liste
                k2, v2 = item.split(":", 1); cur = {k2.strip(): val(v2)}; out[key].append(cur)
            else:
                cur = None; out[key].append(val(item))
        elif cur is not None and key is not None and ind >= 2 and re.match(r"^[A-Za-z_][\w-]*\s*:", line):
            k2, v2 = line.split(":", 1); cur[k2.strip()] = val(v2)
        elif key is not None and isinstance(out.get(key), str) and ind >= 2:   # Fortsetzungszeile eines Textes
            out[key] = (out[key] + " " + line).strip()
    return out


def parse_file(path):
    """-> {"meta": {...}, "body": markdown} ; Frontmatter optional."""
    text = path.read_text("utf-8").replace("\r\n", "\n")
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if m:
        fm, body = m.group(1), text[m.end():]
        try:
            import yaml   # in CI nur, wenn installiert; sonst der kleine Leser
            meta = yaml.safe_load(fm) or {}
            if not isinstance(meta, dict): meta = {}
        except Exception:
            meta = _yaml_min(fm)
    return {"meta": meta, "body": body.strip(), "path": str(path)}


def load_all(d=None, qa=None):
    """episode_id (str) -> Datensatz; nur Dateien mit numerischem Namen und nur fuer Folgen, die die QA in shownotes/QA.txt
    mit ok oder fixed fuehrt (gleiches Gate wie Quotes und Entitaets-Verknuepfung). Ungepruefte Vollfassungen bleiben Arbeitsmaterial."""
    d = Path(d) if d else SN_DIR
    out = {}
    if not d.exists(): return out
    if qa is None:
        import site_extract as SX
        qa = SX.qa_ok()
    skipped = 0
    for f in sorted(d.glob("*.md")):
        if not f.stem.isdigit(): continue
        if f.stem not in qa: skipped += 1; continue
        try:
            rec = parse_file(f)
        except Exception:
            continue
        eid = str(rec["meta"].get("episode_id") or f.stem)
        rec["episode_id"] = eid
        out[eid] = rec
    if skipped: print(f"Shownotes-Vollfassungen: {len(out)} freigegeben, {skipped} warten auf die QA (shownotes/QA.txt)")
    return out


# ---------------------------------------------------------------- Markdown (kleiner Umsetzer fuer die Vorlage)
def _inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    return s


def md_blocks(md):
    """Markdown -> Liste von (art, inhalt): ('h', (level, text)) | ('p', text) | ('ul', [items]) | ('ol', [items])."""
    blocks, para, lst = [], [], None
    def flush():
        nonlocal para, lst
        if para: blocks.append(("p", " ".join(para).strip())); para = []
        if lst: blocks.append(lst); lst = None
    for line in md.split("\n"):
        s = line.rstrip()
        if not s.strip():
            flush(); continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush(); blocks.append(("h", (len(m.group(1)), m.group(2).strip()))); continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", s)
        if m:
            if para: blocks.append(("p", " ".join(para).strip())); para = []
            if not lst or lst[0] != "ul": 
                if lst: blocks.append(lst)
                lst = ("ul", [])
            lst[1].append(m.group(1).strip()); continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)$", s)
        if m:
            if para: blocks.append(("p", " ".join(para).strip())); para = []
            if not lst or lst[0] != "ol":
                if lst: blocks.append(lst)
                lst = ("ol", [])
            lst[1].append(m.group(1).strip()); continue
        if lst and s.startswith("  "):   # Fortsetzung eines Listenpunkts
            lst[1][-1] += " " + s.strip(); continue
        if lst: blocks.append(lst); lst = None
        para.append(s.strip())
    flush()
    return blocks


def _faq_from_blocks(blocks):
    """FAQ-Abschnitt (Ueberschrift FAQ ...) -> ([{"q","a"}], uebrige Bloecke). Frage = Ueberschrift, **fett** oder Listenpunkt mit '?' ; Antwort = folgender Text."""
    out, rest, i = [], [], 0
    while i < len(blocks):
        b = blocks[i]
        if b[0] == "h" and _FAQ_H.match(b[1][1].strip().rstrip(":")):
            lvl = b[1][0]; i += 1; q = None
            while i < len(blocks) and not (blocks[i][0] == "h" and blocks[i][1][0] <= lvl):
                c = blocks[i]
                if c[0] == "h": q = c[1][1].strip(); 
                elif c[0] == "p":
                    m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", c[1], flags=re.S)
                    if m and m.group(1).rstrip().endswith("?"):
                        q = m.group(1).strip()
                        if m.group(2).strip(): out.append({"q": q, "a": m.group(2).strip()}); q = None
                    elif q: out.append({"q": q, "a": c[1].strip()}); q = None
                    elif c[1].strip().endswith("?"): q = c[1].strip()
                elif c[0] in ("ul", "ol"):
                    for it in c[1]:
                        m = re.match(r"^\*\*(.+?)\*\*\s*[:–—-]?\s*(.*)$", it, flags=re.S)
                        if m and m.group(1).rstrip().endswith("?") and m.group(2).strip(): out.append({"q": m.group(1).strip(), "a": m.group(2).strip()})
                        elif q: out.append({"q": q, "a": it}); q = None
                i += 1
            continue
        rest.append(b); i += 1
    return [x for x in out if x["q"] and x["a"]], rest


def _chapters(meta):
    out = []
    for c in meta.get("chapters") or []:
        if isinstance(c, dict):
            t = c.get("title") or c.get("name") or ""
            s = c.get("start_s", c.get("time_s", c.get("start", c.get("t"))))
            out.append((s, t))
        elif isinstance(c, str):
            m = _TIME.match(c); out.append((m.group(1), m.group(2)) if m else (None, c))
    return [(_mmss(s), t) for s, t in out if t]


def _mmss(s):
    if s is None or s == "": return ""
    if isinstance(s, str) and ":" in s: return s
    try:
        s = int(float(s))
    except (TypeError, ValueError):
        return str(s)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def _hover(html, ents, lang):
    """Entitaets-Links bekommen Kurzbeschreibung als Hover (a.gl); Beschreibung in der Seitensprache, sonst Englisch."""
    def rep(m):
        href = m.group(1); mm = _ENT_URL.match(_html.unescape(href))
        if not mm: return m.group(0)
        e = ents.get(mm.group(1))
        if not e: return m.group(0)
        d = (e.get("desc") or {}); dd = d.get(lang) or d.get("en") or ""
        if not dd: return m.group(0)
        return f'<a class="gl" href="{href}" data-gt="{esc(e["name"])}" data-gd="{esc(dd[:300])}"' + (f' data-gl="{"de" if lang == "de" and d.get("de") else "en"}"' if lang not in ("en", "de") or not d.get(lang) else "")
    return re.sub(r'<a href="([^"]+)"', rep, html)


def render(rec, lang, ents, base, labels=None):
    """-> (html, jsonld_list, faq_list). html: Hook, Kapitel, Takeaways, weitere Abschnitte, FAQ (details)."""
    meta, body = rec["meta"], rec["body"]
    L = {"chapters": {"en": "In this episode", "de": "In dieser Folge"}, "takeaways": {"en": "Key takeaways", "de": "Das Wichtigste"}, "faq": {"en": "FAQ", "de": "Häufige Fragen"}}
    T = lambda k: ((labels or {}).get(k)) or L[k].get(lang) or L[k]["en"]
    blocks = md_blocks(body)
    faq, blocks = _faq_from_blocks(blocks)
    if not faq:
        faq = [{"q": str(x.get("q") or x.get("question") or ""), "a": str(x.get("a") or x.get("answer") or "")} for x in (meta.get("faq") or []) if isinstance(x, dict)]
        faq = [x for x in faq if x["q"] and x["a"]]
    # Textkoerper
    out, used_hook = [], False
    hook = str(meta.get("hook") or "").strip()
    if hook and not (blocks and blocks[0][0] == "p" and blocks[0][1][:40] == hook[:40]):
        out.append(f'<p class="sn-hook"><strong>{_inline(hook)}</strong></p>'); used_hook = True
    for b in blocks:
        if b[0] == "h":
            lvl, t = b[1]; out.append(f"<h{min(max(lvl, 2), 4)}>{_inline(t)}</h{min(max(lvl, 2), 4)}>")
        elif b[0] == "p":
            first = not used_hook and not any(x.startswith("<p") for x in out) and not any(x.startswith("<h") for x in out)
            out.append(f'<p class="sn-hook"><strong>{_inline(b[1])}</strong></p>' if first else f"<p>{_inline(b[1])}</p>"); used_hook = used_hook or first
        else:
            items = []
            for it in b[1]:
                m = _TIME.match(it)
                items.append(f'<li><time class="sn-t">{esc(m.group(1))}</time> {_inline(m.group(2))}</li>' if m else f"<li>{_inline(it)}</li>")
            out.append(f"<{b[0]} class=\"sn-list\">{''.join(items)}</{b[0]}>")
    # Kapitel/Takeaways aus dem Frontmatter nur, wenn der Text sie nicht schon enthaelt
    if not any(b[0] in ("ul", "ol") and any(_TIME.match(x) for x in b[1]) for b in blocks):
        ch = _chapters(meta)
        if ch: out.append(f"<h2>{esc(T('chapters'))}</h2><ol class=\"sn-list sn-ch\">" + "".join(f'<li><time class="sn-t">{esc(s)}</time> {_inline(t)}</li>' for s, t in ch) + "</ol>")
    if not any(b[0] == "h" and re.search(r"takeaway|wichtigste|erkenntnis", b[1][1], re.I) for b in blocks):
        tk = [str(x) for x in (meta.get("takeaways") or []) if x]
        if tk: out.append(f"<h2>{esc(T('takeaways'))}</h2><ul class=\"sn-list\">" + "".join(f"<li>{_inline(x)}</li>" for x in tk) + "</ul>")
    html = _hover("".join(out), ents, lang)
    ld = []
    if faq:
        html += f'<section class="faq sn-faq"><h2>{esc(T("faq"))}</h2>' + "".join(f"<details><summary>{esc(x['q'])}</summary><p>{_inline(x['a'])}</p></details>" for x in faq) + "</section>"
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in faq]})
    _qh, _qld = SQ.episode_block(Path(rec.get("path") or "").stem, lang, base, ents)   # Quotes aus der Extraktion, an Personen-Entitaeten gebunden
    html += _qh; ld += _qld
    return f'<section class="shownotes sn">{html}</section>', ld, faq


CSS = ".sn .sn-t{font-variant-numeric:tabular-nums;color:var(--mut,#777);margin-inline-end:.4em}.sn .sn-hook{font-size:1.08em}.sn-list li{margin:.25em 0}a.gl{border-bottom:1px dotted var(--ac)}"
