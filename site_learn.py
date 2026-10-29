"""Lern-Bereich: Glossar, Lernpfade, Übungs-Trainer (alles aus vorhandenen Daten, ohne API-Kosten)."""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).parent


def _load(name, default):
    p = ROOT / "data" / name
    return json.loads(p.read_text("utf-8")) if p.exists() else default


LUI = _load("learn_ui.json", {})
GLOSS = _load("glossary.json", [])


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

    for lang in ["en", "de"]:
        t = T(lang)
        gb = f"{BASE}/glossary/" if lang == "en" else f"{BASE}/{lang}/glossary/"
        rel = "glossary" if lang == "en" else f"{lang}/glossary"
        terms = sorted(GLOSS, key=lambda x: x["name"].lower())
        dl = "".join(f'<dt><a href="{gb}{x["id"]}/">{esc(x["name"])}</a></dt><dd>{esc(definition(x, lang)[0])}</dd>' for x in terms)
        body = shell(lang, f'<h1>{esc(t["glossary"])}</h1><p class="mut">{esc(t["glossary_intro"])}</p><dl class="ln-def">{dl}</dl>')
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
                            f'<h2>{esc(t["glossary"])}</h2><ul>{rl}</ul>')
            write(f"{rel}/{x['id']}/index.html", page(lang, f'{x["name"]} – {t["glossary"]} | M365.FM', d0[:155], u, b, None, gloss_ld(lang, u, x), og_type="website", extra_head=LCSS))
            sitemap.append((u, TODAY, None))

    for lang in langs_all:
        t = T(lang)
        # Glossar in Sprache lang: Definitionen (Englisch außer Deutsch) mit Episoden – noindex, solange nicht übersetzt
        if lang != "de":
            gb = f"{BASE}/{lang}/glossary/"
            dl = ""
            for x in sorted(GLOSS, key=lambda y: y["name"].lower()):
                eps = eps_for(lang, x, 5)
                dl += (f'<dt id="{x["id"]}">{esc(x["name"])}</dt><dd lang="en" dir="ltr">{esc(x["en"])}</dd>'
                       + (f'<dd><small>{esc(t["term_eps"].replace("{t}", x["name"]))}:</small>{ep_list(eps)}</dd>' if eps else ""))
            body = shell(lang, f'<h1>{esc(t["glossary"])}</h1><p class="mut">{esc(t["glossary_intro"])} ({esc(t["en_note"])})</p><dl class="ln-def">{dl}</dl>')
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
        b = shell(lang, f'<h1>{esc(t["learn"])}</h1><p class="mut">{esc(t["learn_intro"])}</p><div class="ln-grid">{cards}</div><h2>{esc(t["paths"])}</h2><div class="ln-grid">{pl}</div>')
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


def gloss_link(html_, lang, base, max_links=4):
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
                        parts[i:i + 1] = [seg[:mm.start()], f'<a class="ilink gl" href="{tgt(x)}">', mm.group(0), "</a>", seg[mm.end():]]
                        used.add(x["id"])
                        cnt[0] += 1
                        break
        return "".join(parts)

    return re.sub(r"<(p|li)>.*?</\1>", blk, html_, flags=re.S)
