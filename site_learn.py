"""Lern-Bereich: Glossar, Lernpfade, Übungs-Trainer (alles aus vorhandenen Daten, ohne API-Kosten)."""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).parent


def _load(name, default):
    p = ROOT / "data" / name
    return json.loads(p.read_text("utf-8")) if p.exists() else default


LUI = _load("learn_ui.json", {})
GLOSS = _load("glossary.json", [])


def sortkey(x):
    n = x.get("sort") or re.sub(r"^Microsoft ", "", x["name"])
    return n.lower()


def letter_of(x):
    c = (x.get("sort") or re.sub(r"^Microsoft ", "", x["name"]))[:1].upper()
    return c if c.isalpha() else "#"


def az_html(terms, lang, link_fn, with_eps=None, t=None):
    """Alphabetisches Glossar mit Buchstaben-Ueberschriften und A-Z-Navigation."""
    groups = {}
    for x in sorted(terms, key=sortkey):
        groups.setdefault(letter_of(x), []).append(x)
    nav = "".join(f'<a href="#l-{k}">{k}</a>' for k in groups)
    out = f'<nav class="ln-az" aria-label="A–Z">{nav}</nav>'
    for k, lst in groups.items():
        out += f'<h2 class="ln-letter" id="l-{k}">{k}</h2><dl class="ln-def">'
        for x in lst:
            d, other = (x["de"], False) if lang == "de" else (x["en"], lang != "en")
            out += link_fn(x, d, other)
        out += "</dl>"
    return out


def T(lang):
    t = dict(LUI.get("en", {}))
    t.update(LUI.get(lang, {}))
    return t


def esc(s):
    return html.escape(s or "", quote=True)


LCSS = """<style>
.ln-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(15em,1fr));gap:1em;margin:1.2em 0}
.ln-card{display:block;padding:1.1em 1.2em;border:1px solid var(--bd);border-radius:.9em;background:var(--card);color:var(--fg);text-decoration:none}
.ln-card:hover,.ln-card:focus-visible{border-color:var(--ac)}.ln-card b{display:block;font-size:1.1em;margin-bottom:.3em}.ln-card span{color:var(--mut)}
.ln-list{list-style:none;padding:0;margin:1em 0}.ln-list li{display:flex;gap:.8em;align-items:flex-start;padding:.8em 0;border-bottom:1px solid var(--bd)}
.ln-list a{color:var(--fg);font-weight:600}.ln-list .n{flex:none;min-width:1.8em;color:var(--mut)}
.ln-btn{font:inherit;cursor:pointer;border:1px solid var(--bd);background:var(--card);color:var(--fg);border-radius:.6em;padding:.4em .8em}
.ln-btn[aria-pressed=true]{background:var(--ac);color:var(--onac);border-color:var(--ac)}
.ln-bar{height:.6em;background:var(--bd);border-radius:1em;overflow:hidden;margin:.6em 0}.ln-bar i{display:block;height:100%;background:var(--ac);width:0}
.ln-def{margin:.8em 0 1.4em}.ln-def dt{font-weight:700;font-size:1.05em}.ln-def dd{margin:.2em 0 .2em}
.ln-az{display:flex;flex-wrap:wrap;gap:.3em;margin:1em 0;position:sticky;top:0;background:var(--bg);padding:.4em 0;z-index:5}.ln-az a{display:inline-block;min-width:2em;text-align:center;padding:.35em .3em;border:1px solid var(--bd);border-radius:.4em;color:var(--fg);text-decoration:none;font-weight:700}.ln-az a:hover,.ln-az a:focus-visible{border-color:var(--ac);color:var(--ac)}.ln-letter{margin:1.2em 0 .2em;border-bottom:2px solid var(--ac);padding-bottom:.1em}
.ln-q{border:1px solid var(--bd);border-radius:.9em;padding:1em 1.2em;margin:1em 0;background:var(--card)}
.ln-q legend{font-weight:700;padding:0 .4em}.ln-q label{display:block;padding:.45em .3em;cursor:pointer}
.ln-ok{color:var(--fg);font-weight:700}.ln-cert{border:3px double var(--fg);padding:2em;text-align:center;margin:1.5em 0;background:var(--card)}
.ln-cert h2{margin-top:0}.ln-cert .nm{font-size:1.6em;font-weight:700;margin:.6em 0;border-bottom:1px solid var(--fg);display:inline-block;min-width:60%}
.ln-nm{font:inherit;padding:.45em .7em;border:1px solid var(--bd);border-radius:.5em;background:var(--card);color:var(--fg);min-width:16em}
@media print{body *{visibility:hidden}#cert,#cert *{visibility:visible}#cert{position:absolute;left:0;top:0;width:100%;background:#fff;color:#000;border-color:#000}}
</style>"""

PATH_JS = """<script>(function(){try{var R=document.getElementById("lnpath");if(!R)return;var K="m365-lp",S={};try{S=JSON.parse(localStorage.getItem(K)||"{}")}catch(e){}
var T=JSON.parse(R.getAttribute("data-t")),bs=[].slice.call(R.querySelectorAll("button[data-id]")),bar=R.querySelector(".ln-bar i"),lab=R.querySelector(".ln-p");
function upd(){var d=0;bs.forEach(function(b){var on=!!S[b.dataset.id];b.setAttribute("aria-pressed",on?"true":"false");b.textContent=on?T.done:T.mark;if(on)d++});
var n=bs.length;bar.style.width=(n?100*d/n:0)+"%";lab.textContent=T.progress.replace("{d}",d).replace("{n}",n)}
bs.forEach(function(b){b.addEventListener("click",function(){if(S[b.dataset.id])delete S[b.dataset.id];else S[b.dataset.id]=1;try{localStorage.setItem(K,JSON.stringify(S))}catch(e){}upd()})});
var r=R.querySelector(".ln-reset");r&&r.addEventListener("click",function(){bs.forEach(function(b){delete S[b.dataset.id]});try{localStorage.setItem(K,JSON.stringify(S))}catch(e){}upd()});upd()}catch(e){}})();</script>"""

TRAINER_JS = """<script>(function(){try{var R=document.getElementById("lntr");if(!R)return;var C=JSON.parse(R.querySelector(".cfg").textContent),T=C.t,P=C.pool,box=R.querySelector(".stage");
var c=(location.search.match(/[?&]c=([a-z]+)/)||[])[1];if(c){var f=P.filter(function(q){return q.c===c});if(f.length>=4)P=f}
function el(t,k,x){var e=document.createElement(t);if(k)e.className=k;if(x!=null)e.textContent=x;return e}
function shuf(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t}return a}
var N=Math.min(10,P.length);
if(P.length<4){box.appendChild(el("p","",T.soon));return}
function start(){box.textContent="";var qs=shuf(P).slice(0,N),i=0,sc=0,wrong={};var live=el("p","ln-ok");live.setAttribute("role","status");live.setAttribute("aria-live","polite");
function show(){box.textContent="";var q=qs[i],o=q.o.map(function(x,k){return[x,k]});o=shuf(o);var fs=el("fieldset","ln-q"),lg=el("legend","",(i+1)+" / "+N+" – "+q.q);fs.appendChild(lg);
o.forEach(function(p){var lb=el("label"),r=document.createElement("input");r.type="radio";r.name="a";r.value=p[1];lb.appendChild(r);lb.appendChild(document.createTextNode(" "+p[0]));fs.appendChild(lb)});box.appendChild(fs);
var fb=el("p");fb.setAttribute("role","status");fb.setAttribute("aria-live","polite");var b=el("button","ln-btn",T.check);b.type="button";var done=false;
b.addEventListener("click",function(){if(!done){var s=fs.querySelector("input:checked");if(!s)return;done=true;var ok=+s.value===q.a;if(ok)sc++;else wrong[q.k]=q;
fb.textContent=(ok?"✓ ":"✗ ")+(q.o[q.a]?q.o[q.a]+". ":"")+(q.w?T.explain+": "+q.w:"");fs.disabled=true;b.textContent=i+1<N?T.next:T.finish}
else{i++;if(i<N)show();else end()}});box.appendChild(fb);box.appendChild(b)}
function end(){box.textContent="";box.appendChild(el("h2","",T.score.replace("{s}",sc).replace("{n}",N)));var w=Object.keys(wrong);
if(w.length){box.appendChild(el("h3","",T.weak));var ul=el("ul"),seen={};w.forEach(function(k){var q=wrong[k];if(seen[q.u])return;seen[q.u]=1;var li=el("li"),a=el("a","",q.t);a.href=q.u;li.appendChild(a);ul.appendChild(li)});box.appendChild(ul)}
var lb=el("label","",T.name+" ");var nm=el("input","ln-nm");nm.type="text";nm.maxLength=60;lb.appendChild(nm);box.appendChild(lb);
var cert=el("section","ln-cert");cert.id="cert";cert.appendChild(el("h2","",T.cert));var n2=el("div","nm"," ");cert.appendChild(n2);cert.appendChild(el("p","",T.cert_text.replace("{s}",sc).replace("{n}",N)));
cert.appendChild(el("p","",new Date().toLocaleDateString(document.documentElement.lang||undefined)+" · M365.FM · dub.m365.fm"));var sm=el("small","",T.cert_note);cert.appendChild(sm);box.appendChild(cert);
nm.addEventListener("input",function(){n2.textContent=nm.value||" "});
var pb=el("button","ln-btn",T.print);pb.type="button";pb.addEventListener("click",function(){window.print()});var rb=el("button","ln-btn",T.again);rb.type="button";rb.addEventListener("click",start);
var wrap=el("p");wrap.appendChild(pb);wrap.appendChild(document.createTextNode(" "));wrap.appendChild(rb);box.appendChild(wrap)}
show()}
var sb=el("button","ln-btn",T.start.replace("{n}",N));sb.type="button";sb.addEventListener("click",start);box.appendChild(sb)}catch(e){}})();</script>"""

WT = {
 "en": dict(h="Community wiki", intro="Short info above, community knowledge below: add practical tips, examples or corrections. New contributions are reviewed first; trusted members publish directly.", login="Sign in to add or edit.", by="Edited by {n} · {d}", anon="Community", report="Report", reported="Thanks, reported.",
            empty="No community notes yet – be the first to add a tip.", edit="Edit", add="Add a note", summary="What did you change? (optional)", save="Save", saved_live="Published. Thank you!", saved_pending="Thank you! Your note will appear after review.", too_short="Please write at least 20 characters.", unchanged="No changes found.", rate="Too many edits – please try again later.", error="Something went wrong. Please try again.",
            rules="Plain text only, no links or advertising. Keep it factual and helpful.", pending_own="You have a note waiting for review. Saving replaces it.", history="History", pending="Waiting for review", approve="Publish", reject="Reject"),
 "de": dict(h="Community-Wiki", intro="Oben die Kurzinfo, unten das Wissen der Community: ergänze praktische Tipps, Beispiele oder Korrekturen. Neue Beiträge werden zuerst geprüft, bewährte Mitglieder veröffentlichen direkt.", login="Melde dich an, um zu ergänzen oder zu bearbeiten.", by="Bearbeitet von {n} · {d}", anon="Community", report="Melden", reported="Danke, gemeldet.",
            empty="Noch keine Community-Hinweise – sei der Erste mit einem Tipp.", edit="Bearbeiten", add="Hinweis ergänzen", summary="Was hast du geändert? (optional)", save="Speichern", saved_live="Veröffentlicht. Danke!", saved_pending="Danke! Dein Hinweis erscheint nach der Prüfung.", too_short="Bitte schreibe mindestens 20 Zeichen.", unchanged="Keine Änderung gefunden.", rate="Zu viele Änderungen – bitte später noch einmal versuchen.", error="Etwas ist schiefgelaufen. Bitte versuche es erneut.",
            rules="Nur Text, keine Links oder Werbung. Bleib sachlich und hilfreich.", pending_own="Du hast einen Hinweis in der Prüfung. Speichern ersetzt ihn.", history="Verlauf", pending="Wartet auf Prüfung", approve="Veröffentlichen", reject="Ablehnen"),
}
WT['en'].update({'rules': 'Write plain text with simple markup (toolbar). Sources go in via “Source”; no other links or advertising. Keep it factual and cite where you can.', 'toc': 'Contents', 'refs': 'Sources', 'back': 'Back to text', 'cn': 'source needed', 'toolbar': 'Formatting', 'tb_h': 'Heading', 'tb_b': 'Bold', 'tb_i': 'Italic', 'tb_ul': 'Bulleted list', 'tb_ol': 'Numbered list', 'tb_q': 'Quote', 'tb_link': 'Link to a term', 'tb_ref': 'Add source', 'tb_cn': 'Mark as needing a source', 'link_ph': 'Search for a term…', 'insert': 'Insert', 'cancel': 'Cancel', 'ref_title': 'Title of the source', 'ref_pub': 'Publisher (optional)', 'ref_date': 'Date (optional)', 'preview': 'Preview', 'back_edit': 'Back to editing', 'bad_ref': 'A source needs a title and an https:// link (no link shorteners, max. 25).', 'current': 'current', 'changes': 'Show changes', 'added': 'Added', 'removed': 'Removed', 'restore': 'Restore this version'})
WT['de'].update({'rules': 'Schreibe Text mit einfacher Formatierung (Werkzeugleiste). Quellen fügst du über „Quelle“ ein; sonst keine Links oder Werbung. Bleib sachlich und belege, wo du kannst.', 'toc': 'Inhalt', 'refs': 'Quellen', 'back': 'Zurück zum Text', 'cn': 'Beleg fehlt', 'toolbar': 'Formatierung', 'tb_h': 'Überschrift', 'tb_b': 'Fett', 'tb_i': 'Kursiv', 'tb_ul': 'Aufzählung', 'tb_ol': 'Nummerierte Liste', 'tb_q': 'Zitat', 'tb_link': 'Auf einen Begriff verlinken', 'tb_ref': 'Quelle hinzufügen', 'tb_cn': 'Als belegbedürftig markieren', 'link_ph': 'Begriff suchen…', 'insert': 'Einfügen', 'cancel': 'Abbrechen', 'ref_title': 'Titel der Quelle', 'ref_pub': 'Herausgeber (optional)', 'ref_date': 'Datum (optional)', 'preview': 'Vorschau', 'back_edit': 'Zurück zum Bearbeiten', 'bad_ref': 'Eine Quelle braucht einen Titel und einen https://-Link (keine Kurzlinks, max. 25).', 'current': 'aktuell', 'changes': 'Änderungen anzeigen', 'added': 'Hinzugefügt', 'removed': 'Entfernt', 'restore': 'Diese Version wiederherstellen'})
WCSS = """<style>.wk{margin:.6em 0}.wk-body{line-height:1.7;max-width:46em}.wk-body h3{font-size:1.2em;margin:1.2em 0 .3em}.wk-body h4{font-size:1.05em;margin:1em 0 .3em}.wk-body blockquote{margin:.8em 0;padding:.1em 1em;border-inline-start:3px solid var(--ac);color:var(--mut)}.wk-fn a,.wk-back{text-decoration:none;font-weight:700}.wk-cn{color:var(--mut);font-size:.8em}.wk-toc{border:1px solid var(--bd);border-radius:.6em;padding:.5em 1em;display:inline-block;margin:.5em 0;background:var(--card)}.wk-toc ol{margin:.3em 0;padding-inline-start:1.3em}.wk-refs{font-size:.92rem;padding-inline-start:1.5em}.wk-refs li{margin:.25em 0}.wk-refh{font-size:1rem;margin:1.2em 0 .2em}.wk-bar{display:flex;flex-wrap:wrap;gap:.3em;margin:.4em 0}.wk-tb{font:inherit;min-width:2.5rem;min-height:2.5rem;cursor:pointer;border:1px solid var(--bd);border-radius:.5em;background:var(--card);color:var(--fg)}.wk-panel{border:1px dashed var(--bd);border-radius:.5em;padding:.4em .7em;margin:.4em 0}.wk-panel[hidden],.wk-prev[hidden]{display:none}.wk-prev{border:1px solid var(--bd);border-radius:.5em;padding:.5em 1em;margin:.4em 0;background:var(--bg)}.wk input[aria-invalid=true]{border-color:#b00020}.wk-hl{list-style:none;padding:0}.wk-hl>li{margin:.5em 0}.wk-dl{font:.85rem/1.5 ui-monospace,monospace;margin:.4em 0;max-height:16em;overflow:auto;border:1px solid var(--bd);border-radius:.4em;padding:.3em .6em;white-space:pre-wrap}.wk-add{border-inline-start:4px solid #1a7f37;padding-inline-start:.4em}.wk-del{border-inline-start:4px solid #b00020;padding-inline-start:.4em;text-decoration:line-through}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.wk-meta,.wk-empty{color:var(--mut)}.wk-link{font:inherit;background:none;border:0;color:var(--ac);text-decoration:underline;cursor:pointer;padding:0}
.wk-edit,.wk-hist{margin:1em 0;border:1px solid var(--bd);border-radius:.7em;padding:.6em 1em;background:var(--card)}.wk-edit summary,.wk-hist summary{cursor:pointer;font-weight:700}.wk textarea,.wk input[type=text]{width:100%;box-sizing:border-box;font:inherit;padding:.5em;border:1px solid var(--bd);border-radius:.5em;background:var(--bg);color:var(--fg);margin:.4em 0}
.wk .btn{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:.5em;padding:.45em 1em;background:var(--card);color:var(--fg);text-decoration:none;display:inline-block;margin:.2em .3em .2em 0}.wk .btn.main{background:var(--ac);color:var(--onac);border-color:var(--ac)}.wk-pend{border-top:1px solid var(--bd);padding:.5em 0}</style>"""


def fetch_wiki(api, lang):
    """Freigegebene Community-Texte zum Seitenbau holen (statisch, damit sie indexierbar sind). Fehler -> leer."""
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{api}/api/wiki/export?lang={lang}", headers={"user-agent": "m365-dub-build"}), timeout=10) as r:
            return {x["term"]: x for x in json.loads(r.read().decode("utf-8")).get("items", [])}
    except Exception:
        return {}


_INL = re.compile(r"\{\{ref\|([^{}]*)\}\}|\{\{cn\}\}|\[\[([a-z0-9-]{2,48})(?:\|([^\[\]]{1,80}))?\]\]|\*\*([^*]+?)\*\*|\*([^*\s][^*]*?)\*")


def wiki_render(body, links, w):
    """Spiegel von assets/wiki.js renderWiki: Wiki-Markup -> sicheres HTML. Rueckgabe (html, refs)."""
    refs, keys, seen = [], {}, set()

    def inline(text):
        out = []
        while text:
            m = _INL.search(text)
            if not m:
                out.append(esc(text)); break
            out.append(esc(text[:m.start()]))
            g = m.group(0)
            if g.startswith("{{ref|"):
                p = m.group(1).split("|")
                p += [""] * (4 - len(p))
                key = p[1] + "|" + p[0]
                n = keys.get(key)
                if not n:
                    refs.append({"title": p[0], "url": p[1], "pub": p[2], "date": p[3]}); n = keys[key] = len(refs)
                idattr = "" if n in seen else f' id="wkfn-{n}"'
                seen.add(n)
                out.append(f'<sup class="wk-fn"><a href="#wkref-{n}"{idattr}>[{n}]</a></sup>')
            elif g == "{{cn}}":
                out.append(f'<sup class="wk-cn"><span>[{esc(w["cn"])}]</span></sup>')
            elif m.group(2):
                t = links.get(m.group(2))
                out.append(f'<a href="{esc(t[1])}">{esc(m.group(3) or t[0])}</a>' if t else esc(m.group(3) or m.group(2)))
            elif m.group(4) is not None:
                out.append(f"<strong>{inline(m.group(4))}</strong>")
            else:
                out.append(f"<em>{inline(m.group(5))}</em>")
            text = text[m.end():]
        return "".join(out)

    out, para, lst, heads, hn = [], [], [None], [], [0]

    def flush_p():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>"); para.clear()

    def flush_l():
        if lst[0]:
            out.append(f"</{lst[0]}>"); lst[0] = None

    for ln in body.split("\n"):
        if not ln.strip():
            flush_p(); flush_l(); continue
        m = re.match(r"^(#{2,3})\s+(.+)$", ln)
        if m:
            flush_p(); flush_l()
            lv = 3 if len(m.group(1)) == 2 else 4
            hn[0] += 1
            hid = f"wk-h-{hn[0]}"
            out.append(f'<h{lv} id="{hid}">{inline(m.group(2))}</h{lv}>')
            if lv == 3:
                heads.append((hid, re.sub(r"\*|\[\[[^\]|]*\|?|\]\]|\{\{[^}]*\}\}", "", m.group(2))))
            continue
        m = re.match(r"^(-|\d+\.)\s+(.+)$", ln)
        if m:
            flush_p()
            tag = "ul" if m.group(1) == "-" else "ol"
            if lst[0] != tag:
                flush_l(); out.append(f"<{tag}>"); lst[0] = tag
            out.append(f"<li>{inline(m.group(2))}</li>"); continue
        m = re.match(r"^>\s?(.+)$", ln)
        if m:
            flush_p(); flush_l(); out.append(f"<blockquote><p>{inline(m.group(1))}</p></blockquote>"); continue
        flush_l(); para.append(ln.strip())
    flush_p(); flush_l()
    html_ = "".join(out)
    if len(heads) >= 3:
        toc = f'<nav class="wk-toc" aria-label="{esc(w["toc"])}"><b>{esc(w["toc"])}</b><ol>' + "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in heads) + "</ol></nav>"
        html_ = toc + html_
    if refs:
        from urllib.parse import urlparse
        def host(u):
            try:
                return (urlparse(u).hostname or u).removeprefix("www.")
            except Exception:
                return u
        html_ += f'<h3 class="wk-refh">{esc(w["refs"])}</h3><ol class="wk-refs">' + "".join(
            f'<li id="wkref-{i + 1}"><a href="#wkfn-{i + 1}" class="wk-back" aria-label="{esc(w["back"])}">↑</a> {esc(r["title"] + (" – " + r["pub"] if r["pub"] else "") + (" (" + r["date"] + ")" if r["date"] else ""))} · '
            f'<a href="{esc(r["url"])}" rel="nofollow ugc noopener" target="_blank">{esc(host(r["url"]))}</a></li>' for i, r in enumerate(refs)) + "</ol>"
    return html_, refs


def gloss_links(lang, base):
    """id -> [Name, URL] aller verlinkbaren Begriffe (Glossar; Entitaeten kommen dazu, sobald es Seiten gibt)."""
    gb = f"{base}/glossary/" if lang == "en" else f"{base}/{lang}/glossary/"
    return {x["id"]: [x["name"], f"{gb}{x['id']}/"] for x in GLOSS}


def wiki_block(lang, term_id, api, base, static, links=None):
    w = WT.get(lang, WT["en"])
    links = links or {}
    cfg = json.dumps({"api": api, "term": term_id, "lang": lang, "t": w, "links": {k: v for k, v in links.items() if k != term_id}}, ensure_ascii=False).replace("</", "<\\/")
    st = f'<div class="wk-static wk-body">{wiki_render(static["body"], links, w)[0]}</div>' if static else ""
    return (f'{WCSS}<section aria-labelledby="wk-h"><h2 id="wk-h">{esc(w["h"])}</h2><p class="mut">{esc(w["intro"])}</p><div id="c-wiki">{st}</div></section>'
            f'<script>window.M365W={cfg}</script><script defer src="{base}/assets/wiki.js"></script>')


def build_learn(ctx):
    """ctx: dict mit write, page, header, footer, footer_en, BASE, LANGS, active, by_lang, catidx, articles, url_of,
    cat_name, ORDER, strip_tags, anchor_title, parse_desc, sitemap, TODAY."""
    g = ctx
    BASE, LANGS, write, page = g["BASE"], g["LANGS"], g["write"], g["page"]
    header, footer, footer_en = g["header"], g["footer"], g["footer_en"]
    ORDER, cat_name = g["ORDER"], g["cat_name"]
    sitemap, TODAY = g["sitemap"], g["TODAY"]
    articles, url_of = g["articles"], g["url_of"]

    def shell(lang, body):
        h = header(lang, "")
        f = footer(lang) if lang in LANGS else footer_en()
        return f'{h}<main class="wrap" style="max-width:56em">{body}</main>{f}'

    def eps_for(l, term, lim=8):
        rx = re.compile(term["kw"], re.I)
        out = []
        for it in g["by_lang"].get(l, []):
            e = it["e"]
            if rx.search(e["title"] + " " + (e.get("tags") or "")):
                out.append(it)
        return out[:lim]

    def ep_list(lst):
        return "<ul>" + "".join(f'<li><a href="{url_of(x)}">{esc(g["anchor_title"](x["e"]["title"]))}</a></li>' for x in lst) + "</ul>"

    def definition(term, lang):
        if lang == "de":
            return term["de"], False
        return term["en"], lang != "en"

    langs_all = list(g["active"])
    # ---- Glossar ----
    def gloss_ld(lang, url, term=None):
        setname = {"@type": "DefinedTermSet", "@id": f"{BASE}/glossary/#set", "name": "M365.FM Glossary"}
        if term is None:
            return [{"@context": "https://schema.org", "@type": "DefinedTermSet", "name": T(lang)["glossary"], "url": url,
                     "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t["name"], "description": definition(t, lang)[0]} for t in GLOSS]}]
        return [{"@context": "https://schema.org", "@type": "DefinedTerm", "name": term["name"], "description": definition(term, lang)[0], "url": url,
                 "inDefinedTermSet": setname}]

    WIKI_API = g.get("api", "https://api-dub.m365.fm")
    for lang in ["en", "de"]:
        t = T(lang)
        stat = fetch_wiki(WIKI_API, lang)
        gb = f"{BASE}/glossary/" if lang == "en" else f"{BASE}/{lang}/glossary/"
        rel = "glossary" if lang == "en" else f"{lang}/glossary"
        terms = sorted(GLOSS, key=lambda x: x["name"].lower())
        az = az_html(terms, lang, lambda x, d, o: f'<dt><a href="{gb}{x["id"]}/">{esc(x["name"])}</a></dt><dd>{esc(d)}</dd>')
        body = shell(lang, f'<h1>{esc(t["glossary"])}</h1><p class="mut">{esc(t["glossary_intro"])}</p>{az}')
        write(f"{rel}/index.html", page(lang, f'{t["glossary"]} – M365.FM', t["glossary_intro"], gb, body, None, gloss_ld(lang, gb), og_type="website", extra_head=LCSS))
        sitemap.append((gb, TODAY, None))
        for x in terms:
            u = f"{gb}{x['id']}/"
            d0 = definition(x, lang)[0]
            same = [y for y in terms if y["cat"] == x["cat"] and y["id"] != x["id"]][:6]
            eps = eps_for("de" if lang == "de" else "de", x) if lang == "de" else []
            rl = "".join(f'<li><a href="{gb}{y["id"]}/">{esc(y["name"])}</a></li>' for y in same)
            catlink = ""
            if lang == "de" and x["cat"] in g["catidx"].get("de", {}):
                catlink = f'<p><a href="{BASE}/de/path/{x["cat"]}/">{esc(t["paths"])}: {esc(cat_name(x["cat"], "de"))}</a></p>'
            eb = (f'<h2>{esc(t["term_eps"].replace("{t}", x["name"]))}</h2>{ep_list(eps)}') if eps else ""
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{gb}">{esc(t["glossary"])}</a></nav><h1>{esc(x["name"])}</h1><p style="font-size:1.1em">{esc(d0)}</p>{eb}{catlink}'
                            f'{wiki_block(lang, x["id"], WIKI_API, BASE, stat.get(x["id"]), gloss_links(lang, BASE))}<h2>{esc(t["glossary"])}</h2><ul>{rl}</ul>')
            write(f"{rel}/{x['id']}/index.html", page(lang, f'{x["name"]} – {t["glossary"]} | M365.FM', d0[:155], u, b, None, gloss_ld(lang, u, x), og_type="website", extra_head=LCSS))
            sitemap.append((u, TODAY, None))

    for lang in langs_all:
        t = T(lang)
        # Glossar in Sprache lang: Definitionen (Englisch außer Deutsch) mit Episoden – noindex, solange nicht übersetzt
        if lang != "de":
            gb = f"{BASE}/{lang}/glossary/"
            def row(x, d, o, lang=lang, t=t):
                eps = eps_for(lang, x, 5)
                return (f'<dt id="{x["id"]}">{esc(x["name"])}</dt><dd lang="en" dir="ltr">{esc(d)}</dd>'
                        + (f'<dd><small>{esc(t["term_eps"].replace("{t}", x["name"]))}:</small>{ep_list(eps)}</dd>' if eps else ""))
            body = shell(lang, f'<h1>{esc(t["glossary"])}</h1><p class="mut">{esc(t["glossary_intro"])} ({esc(t["en_note"])})</p>{az_html(GLOSS, lang, row)}')
            write(f"{lang}/glossary/index.html", page(lang, f'{t["glossary"]} – M365.FM {LANGS[lang][0]}', t["glossary_intro"], gb, body, None, None, og_type="website", extra_head=LCSS, noindex=True))
        # Lernpfade
        paths = {c: sorted(g["catidx"][lang][c], key=lambda i: (i["date"], i["vid"])) for c in ORDER if c in g["catidx"].get(lang, {}) and len(g["catidx"][lang][c]) >= 2}
        for c, lst in paths.items():
            pu = f"{BASE}/{lang}/path/{c}/"
            rows = "".join(f'<li><span class="n">{i + 1}.</span><div style="flex:1"><a href="{url_of(x)}">{esc(g["anchor_title"](x["e"]["title"]))}</a>'
                           f'<p class="mut" style="margin:.2em 0">{esc(g["short"](g["parse_desc"](x["e"]["desc"])[0], 140))}</p></div>'
                           f'<button type="button" class="ln-btn" data-id="{x["vid"]}" aria-pressed="false">{esc(t["mark"])}</button></li>' for i, x in enumerate(lst))
            cfg = json.dumps({"mark": t["mark"], "done": t["done"], "progress": t["progress"]}, ensure_ascii=False).replace("</", "<\\/")
            tr = f'<p><a class="ln-btn" style="text-decoration:none;display:inline-block" href="{BASE}/{lang}/trainer/?c={c}">{esc(t["trainer"])}</a></p>'
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{BASE}/{lang}/learn/">{esc(t["learn"])}</a></nav><h1>{esc(t["paths"])}: {esc(cat_name(c, lang))}</h1><p class="mut">{esc(t["paths_intro"])}</p>'
                            f'<div id="lnpath" data-t="{esc(cfg)}"><div class="ln-bar"><i></i></div><p class="ln-p" role="status" aria-live="polite"></p><ol class="ln-list" style="list-style:none">{rows}</ol>'
                            f'<button type="button" class="ln-btn ln-reset">{esc(t["reset"])}</button></div>{tr}{PATH_JS}')
            ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": f'{t["paths"]}: {cat_name(c, lang)}', "itemListElement":
                   [{"@type": "ListItem", "position": i + 1, "url": url_of(x), "name": x["e"]["title"]} for i, x in enumerate(lst)]}]
            write(f"{lang}/path/{c}/index.html", page(lang, f'{t["paths"]}: {cat_name(c, lang)} – M365.FM', t["paths_intro"], pu, b, None, ld, og_type="website", extra_head=LCSS))
            sitemap.append((pu, TODAY, None))
        # Trainer
        pool = []
        cat_first = {}
        for c in reversed(ORDER):
            for x in g["catidx"].get(lang, {}).get(c, []):
                cat_first[x["vid"]] = c
        for x in g["by_lang"].get(lang, []):
            for qi, q in enumerate((articles.get(x["vid"], {}).get(lang, {}) or {}).get("quiz", []) or []):
                try:
                    pool.append({"q": q["q"], "o": q["opts"][:4], "a": int(q["a"]), "w": q.get("why", ""), "k": f'{x["vid"]}{qi}', "c": cat_first.get(x["vid"], ""),
                                 "t": g["anchor_title"](x["e"]["title"]), "u": url_of(x)})
                except Exception:
                    pass
        pool = pool[:300]
        tu = f"{BASE}/{lang}/trainer/"
        cfg = json.dumps({"t": {k: t[k] for k in ("check", "next", "finish", "again", "start", "soon", "weak", "name", "cert", "cert_text", "cert_note", "print", "explain")} | {"score": g["SCORE"].get(lang, "{s}/{n}")}, "pool": pool}, ensure_ascii=False).replace("</", "<\\/")
        b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{BASE}/{lang}/learn/">{esc(t["learn"])}</a></nav><h1>{esc(t["trainer"])}</h1><p class="mut">{esc(t["trainer_intro"])}</p>'
                        f'<div id="lntr"><div class="stage"></div><script type="application/json" class="cfg">{cfg}</script></div><p><small>{esc(t["cert_note"])}</small></p>{TRAINER_JS}')
        write(f"{lang}/trainer/index.html", page(lang, f'{t["trainer"]} – M365.FM {LANGS[lang][0]}', t["trainer_intro"], tu, b, None, None, og_type="website", extra_head=LCSS, noindex=True))
        # Hub
        hu = f"{BASE}/{lang}/learn/"
        cards = (f'<a class="ln-card" href="{BASE}/{lang}/glossary/"><b>{esc(t["glossary"])}</b><span>{esc(t["glossary_intro"])}</span></a>'
                 f'<a class="ln-card" href="{BASE}/{lang}/trainer/"><b>{esc(t["trainer"])}</b><span>{esc(t["trainer_intro"])}</span></a>')
        pl = "".join(f'<a class="ln-card" href="{BASE}/{lang}/path/{c}/"><b>{esc(cat_name(c, lang))}</b><span>{len(paths[c])}</span></a>' for c in ORDER if c in paths)
        b = shell(lang, f'<h1>{esc(t["learn"])}</h1><p class="mut">{esc(t["learn_intro"])}</p><h2>{esc(t["paths"])}</h2><div class="ln-grid">{pl}</div><div class="ln-grid">{cards}</div>')
        write(f"{lang}/learn/index.html", page(lang, f'{t["learn"]} – M365.FM {LANGS[lang][0]}', t["learn_intro"], hu, b, None, None, og_type="website", extra_head=LCSS))
        sitemap.append((hu, TODAY, None))


_GEN = {"prompt", "governance", "graph", "teams", "viva", "fabric"}


def _names(term):
    n = term["name"]
    out = [re.sub(r"\s*\(.*?\)", "", n).strip()]
    m = re.search(r"\(([A-Za-z]{3,6})\)", n)
    if m:
        out.append(m.group(1))
    if n.startswith("Microsoft "):
        out.append(n[10:])
    seen, res = set(), []
    for x in out:
        if len(x) >= 3 and x.lower() not in _GEN and x not in seen:
            seen.add(x)
            res.append(x)
    return res


def drop_glossed(money):
    """Money-Keywords, zu denen es einen Glossar-Eintrag gibt, nicht mehr auf Folgen verlinken (das uebernimmt gloss_link -> Glossar)."""
    if not GLOSS or not money:
        return money
    names = {nm.lower() for x in GLOSS for nm in _names(x)} | {x["name"].lower() for x in GLOSS}
    return {k: v for k, v in money.items() if k.lower() not in names}


def gloss_link(html_, lang, base, max_links=8):
    """Erste Nennung bekannter Begriffe im Artikel auf die Glossar-Seite verlinken (nur Absätze/Listen, nie in Links)."""
    if not GLOSS or not html_:
        return html_
    tgt = (lambda x: f"{base}/de/glossary/{x['id']}/") if lang == "de" else (lambda x: f"{base}/{lang}/glossary/#{x['id']}")
    cands = sorted(((nm, x) for x in GLOSS for nm in _names(x)), key=lambda c: -len(c[0]))
    used, cnt = set(), [0]

    def blk(m):
        if cnt[0] >= max_links:
            return m.group(0)
        parts = re.split(r"(<[^>]+>)", m.group(0))
        for nm, x in cands:
            if cnt[0] >= max_links:
                break
            if x["id"] in used:
                continue
            rx = re.compile(r"(?<![\w-])" + re.escape(nm) + r"(?![\w-])")
            depth = 0
            for i, seg in enumerate(parts):
                if i % 2 == 1:
                    if re.match(r"<a[\s>]", seg, re.I):
                        depth += 1
                    elif seg.lower().startswith("</a"):
                        depth = max(0, depth - 1)
                    continue
                if depth == 0 and seg.strip():
                    mm = rx.search(seg)
                    if mm:
                        dd = x["de"] if lang == "de" else x["en"]
                        parts[i:i + 1] = [seg[:mm.start()], f'<a class="ilink gl" href="{tgt(x)}" data-gt="{esc(x["name"])}" data-gd="{esc(dd)}"' + ('' if lang == "de" else ' data-gl="en"') + '>', mm.group(0), "</a>", seg[mm.end():]]
                        used.add(x["id"])
                        cnt[0] += 1
                        break
        return "".join(parts)

    return re.sub(r"<(p|li)>.*?</\1>", blk, html_, flags=re.S)


GLOSS_JS = """<script>(function(){try{var L=[].slice.call(document.querySelectorAll("a.gl[data-gd]"));if(!L.length)return;
var st=document.createElement("style");st.textContent=".glpop{position:absolute;z-index:60;max-width:22em;background:var(--card);color:var(--fg);border:1px solid var(--ac);border-radius:.6em;padding:.7em .9em;box-shadow:0 8px 24px rgba(0,0,0,.2);font-size:.92rem;line-height:1.45}.glpop b{display:block;margin-bottom:.2em}.glpop a{font-weight:700}a.gl{border-bottom:1px dotted var(--ac);text-decoration:none}";document.head.appendChild(st);
var pop=document.createElement("div");pop.className="glpop";pop.id="glpop";pop.setAttribute("role","tooltip");pop.hidden=true;document.body.appendChild(pop);var cur=null,touch=matchMedia("(hover:none)").matches;
function show(a){cur=a;pop.textContent="";var b=document.createElement("b");b.textContent=a.dataset.gt;pop.appendChild(b);var p=document.createElement("span");p.textContent=a.dataset.gd;if(a.dataset.gl)p.lang=a.dataset.gl;pop.appendChild(p);
if(touch){var m=document.createElement("a");m.href=a.href;m.textContent=" →";m.setAttribute("aria-label",a.dataset.gt);pop.appendChild(m)}
pop.hidden=false;a.setAttribute("aria-describedby","glpop");var r=a.getBoundingClientRect(),x=Math.max(8,Math.min(r.left+scrollX,scrollX+document.documentElement.clientWidth-pop.offsetWidth-8));pop.style.left=x+"px";pop.style.top=(r.bottom+scrollY+6)+"px"}
function hide(){pop.hidden=true;if(cur)cur.removeAttribute("aria-describedby");cur=null}
L.forEach(function(a){a.addEventListener("mouseenter",function(){if(!touch)show(a)});a.addEventListener("mouseleave",function(){setTimeout(function(){if(!pop.matches(":hover"))hide()},120)});a.addEventListener("focus",function(){show(a)});a.addEventListener("blur",function(){setTimeout(function(){if(!pop.contains(document.activeElement))hide()},120)});
a.addEventListener("click",function(e){if(touch&&cur!==a){e.preventDefault();show(a)}})});
pop.addEventListener("mouseleave",hide);document.addEventListener("keydown",function(e){if(e.key==="Escape")hide()});document.addEventListener("click",function(e){if(cur&&!pop.contains(e.target)&&e.target!==cur)hide()})}catch(e){}})();</script>"""
