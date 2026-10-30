"""Show Notes von Spreaker: HTML -> Wiki-Markup (editierbar im Editor), Aufteilung in Haupttext, Kernpunkte und FAQ, Kapitel und Personen aus dem RSS.
Reine Funktionen (kein Netz) - sync_show_notes.py holt die Feeds, site_*.py zeigt das Ergebnis."""
import html as _h
import re
from html.parser import HTMLParser

KEY_H = re.compile(r"^(key ?points?|key ?takeaways?|takeaways?|highlights?|in short|kernpunkte|wichtigste punkte|das wichtigste|stichpunkte|kurz gesagt)\b", re.I)
FAQ_H = re.compile(r"^(faq|f\.a\.q|frequently asked questions?|h(?:ä|ae)ufige fragen|fragen und antworten|q ?& ?a)\b", re.I)
_BAD_HOST = re.compile(r"(^|\.)(bit\.ly|t\.co|tinyurl\.com|goo\.gl|is\.gd|ow\.ly|buff\.ly|cutt\.ly|rebrand\.ly|shorturl\.at)$", re.I)


def _https(u):
    from urllib.parse import urlparse
    try:
        p = urlparse((u or "").strip())
    except Exception:
        return ""
    if p.scheme != "https" or not p.hostname or p.username or p.password or _BAD_HOST.search(p.hostname) or len(u) > 300:
        return ""
    return u.strip()


class _MD(HTMLParser):
    """HTML -> Wiki-Markup: ## ### Ueberschriften, - 1. Listen, > Zitat, **fett**, *kursiv*, {{link|https://..|Text}}, {{img|https://..|Alt}}."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.buf, self.stack, self.href = [], [], [], None
        self.list = []   # Stack aus ("ul"|"ol", Zaehler)

    def _flush(self, prefix=""):
        t = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if t:
            self.out.append(prefix + t)

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("h1", "h2"):
            self._flush(); self.stack.append("## ")
        elif tag in ("h3", "h4", "h5", "h6"):
            self._flush(); self.stack.append("### ")
        elif tag in ("p", "div", "section"):
            self._flush()
        elif tag in ("ul", "ol"):
            self._flush(); self.list.append([tag, 0])
        elif tag == "li":
            self._flush()
            if self.list:
                self.list[-1][1] += 1
        elif tag == "blockquote":
            self._flush(); self.stack.append("> ")
        elif tag == "br":
            self.buf.append(" ")
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("*")
        elif tag == "a":
            self.href = _https(a.get("href")); self.buf.append("\0A")
        elif tag == "img":
            src, alt = _https(a.get("src")), re.sub(r"[\[\]{}|]", "", (a.get("alt") or "")).strip()
            if src and len(alt) >= 5 and re.search(r"\.(jpe?g|png|webp|gif|avif)$", src.split("?")[0], re.I):
                self.buf.append("{{img|%s|%s}}" % (src, alt))

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "blockquote"):
            self._flush(self.stack.pop() if self.stack else "")
        elif tag in ("p", "div", "section"):
            self._flush()
        elif tag == "li":
            pre = "- "
            if self.list and self.list[-1][0] == "ol":
                pre = f"{self.list[-1][1]}. "
            self._flush(pre)
        elif tag in ("ul", "ol"):
            self._flush()
            if self.list:
                self.list.pop()
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("*")
        elif tag == "a":
            # Text zwischen \0A und jetzt als Linkbaustein, wenn die Adresse gueltig war
            i = len(self.buf) - 1
            while i >= 0 and self.buf[i] != "\0A":
                i -= 1
            if i >= 0:
                txt = re.sub(r"\s+", " ", "".join(self.buf[i + 1:])).strip().replace("|", " ")
                del self.buf[i:]
                self.buf.append("{{link|%s|%s}}" % (self.href, txt or self.href) if self.href else txt)
            self.href = None

    def handle_data(self, d):
        self.buf.append(re.sub(r"[<>{}]", "", d))

    def result(self):
        self._flush()
        return "\n\n".join(x for x in self.out if x.strip())


def html_to_markup(src):
    p = _MD()
    p.feed(src or "")
    t = p.result()
    t = re.sub(r"\n\n(- |\d+\. )", r"\n\1", t)           # Listenpunkte eng untereinander
    t = re.sub(r"(\n(?:- |\d+\. )[^\n]*)\n\n(?=(?:- |\d+\. ))", r"\1\n", t)
    return t.strip()


def _plain(s):
    return re.sub(r"\s+", " ", re.sub(r"\{\{(?:link|img)\|[^|{}]*\|([^{}]*)\}\}", r"\1", re.sub(r"[*#>]", "", s or ""))).strip()


def split_sections(markup):
    """Markup -> (Haupttext, Kernpunkte[], FAQ[{q,a}]). Abschnitte unter Ueberschriften wie 'Key points' / 'FAQ' werden herausgeloest."""
    lines = (markup or "").split("\n")
    body, key, faq, cur = [], [], [], None
    q, a = None, []

    def flush_q():
        nonlocal q, a
        if q and a:
            faq.append({"q": _plain(q), "a": _plain(" ".join(a))})
        q, a = None, []

    for ln in lines:
        m = re.match(r"^(#{2,3})\s+(.+)$", ln)
        if m:
            title = _plain(m.group(2))
            if KEY_H.match(title) or FAQ_H.match(title):   # neuer Abschnitt (h2 oder h3)
                flush_q(); cur = "key" if KEY_H.match(title) else "faq"; continue
            if cur == "faq" and len(m.group(1)) == 3:     # h3 im FAQ-Abschnitt = Frage
                flush_q(); q = title; continue
            flush_q(); cur = None; body.append(ln); continue
        if cur == "key":
            li = re.match(r"^(?:-|\d+\.)\s+(.+)$", ln)
            if li:
                key.append(_plain(li.group(1)))
            elif ln.strip() and not key:
                pass   # Einleitungssatz vor der Liste faellt weg
            elif ln.strip():
                body.append(ln); cur = None
            continue
        if cur == "faq":
            if not ln.strip():
                continue
            h3 = re.match(r"^###\s+(.+)$", ln)
            bold = re.match(r"^\*\*(.+?\?)\*\*\s*(.*)$", ln)
            item = re.match(r"^(?:-|\d+\.)\s+(?:\*\*)?(.+?\?)(?:\*\*)?\s*(.*)$", ln)
            qa = re.match(r"^(?:q|f|frage|question)\s*[:.)-]\s*(.+)$", ln, re.I)
            aa = re.match(r"^(?:a|antwort|answer)\s*[:.)-]\s*(.+)$", ln, re.I)
            if h3:
                flush_q(); q = h3.group(1)
            elif bold:
                flush_q(); q = bold.group(1); a = [bold.group(2)] if bold.group(2) else []
            elif item:
                flush_q(); q = item.group(1); a = [item.group(2)] if item.group(2) else []
            elif qa:
                flush_q(); q = qa.group(1)
            elif aa:
                a.append(aa.group(1))
            elif q:
                a.append(ln)
            else:
                body.append(ln); cur = None
            continue
        body.append(ln)
    flush_q()
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip()
    key = [k for k in key if len(k) >= 10][:8]
    faq = [f for f in faq if len(f["q"]) >= 10 and len(f["a"]) >= 20][:10]
    return text, key, faq


def hms(s):
    """itunes:duration -> Sekunden."""
    try:
        p = [int(float(x)) for x in str(s).split(":")]
    except Exception:
        return 0
    return sum(v * 60 ** i for i, v in enumerate(reversed(p)))


def render_html(markup, links=None):
    """Wiki-Markup (nur Show-Notes-Teilmenge) -> sicheres HTML fuer die statischen Seiten."""
    esc = _h.escape
    inl = re.compile(r"\{\{img\|([^{}|]*)\|([^{}]*)\}\}|\{\{link\|([^{}|]*)\|([^{}]*)\}\}|\*\*(.+?)\*\*|\*([^*\s][^*]*?)\*")

    def inline(t):
        out, pos = [], 0
        for m in inl.finditer(t):
            out.append(esc(t[pos:m.start()]))
            if m.group(1) is not None:
                out.append(f'<img src="{esc(m.group(1))}" alt="{esc(m.group(2))}" loading="lazy" decoding="async" referrerpolicy="no-referrer" style="max-width:100%;height:auto">')
            elif m.group(3) is not None:
                out.append(f'<a href="{esc(m.group(3))}" rel="nofollow ugc noopener" target="_blank">{esc(m.group(4))}</a>')
            elif m.group(5) is not None:
                out.append(f"<strong>{inline(m.group(5))}</strong>")
            else:
                out.append(f"<em>{inline(m.group(6))}</em>")
            pos = m.end()
        out.append(esc(t[pos:]))
        return "".join(out)

    res, lst, para = [], None, []

    def fp():
        nonlocal para
        if para:
            res.append(f"<p>{inline(' '.join(para))}</p>"); para = []

    def fl():
        nonlocal lst
        if lst:
            res.append(f"</{lst}>"); lst = None

    for ln in (markup or "").split("\n"):
        if not ln.strip():
            fp(); fl(); continue
        m = re.match(r"^(#{2,3})\s+(.+)$", ln)
        if m:
            fp(); fl(); lv = 3 if len(m.group(1)) == 2 else 4; res.append(f"<h{lv}>{inline(m.group(2))}</h{lv}>"); continue
        m = re.match(r"^(-|\d+\.)\s+(.+)$", ln)
        if m:
            fp(); tag = "ul" if m.group(1) == "-" else "ol"
            if lst != tag:
                fl(); res.append(f"<{tag}>"); lst = tag
            res.append(f"<li>{inline(m.group(2))}</li>"); continue
        m = re.match(r"^>\s?(.+)$", ln)
        if m:
            fp(); fl(); res.append(f"<blockquote><p>{inline(m.group(1))}</p></blockquote>"); continue
        fl(); para.append(ln.strip())
    fp(); fl()
    return "".join(res)
