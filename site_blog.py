"""Blog je Mitglied: oeffentliche Beitragsseiten (BlogPosting) und Verzeichnisse je Sprache. Beitraege kommen freigegeben aus /api/blog/export."""
import json, re
from datetime import datetime, timezone
from site_i18n import COMM_LANGS, pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS, WT, wiki_render, wiki_images, WCSS
import site_notes as SNT
import site_story as ST


def fetch_posts(api):
    items = (_fetch_json(f"{api}/api/blog/export", timeout=120) or {}).get("items", [])
    if any(p.get("has_html") for p in items):   # uebernommene Beitraege: HTML seitenweise nachladen
        html, off = {}, 0
        while True:
            part = (_fetch_json(f"{api}/api/blog/html?offset={off}&limit=40", timeout=120) or {}).get("items", [])
            for x in part: html[x["id"]] = x["html"]
            if len(part) < 40: break
            off += 40
        for p in items:
            if p.get("has_html"): p["html"] = html.get(p["id"], "")
    return items


def _aitr(p, lang):
    if not p.get("ai_tr"): return ""
    return f'<p class="mut"><em>{esc(T(lang, "Automatically translated with AI from the original post.", "Automatisch mit KI aus dem Originalbeitrag übersetzt."))}</em></p>'


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


VOTEJS = ('(function(){var A="%API%",H="%H%",bs=[].slice.call(document.querySelectorAll(".bl-vote"));if(!bs.length)return;'
          'function f(p,o){o=o||{};o.credentials="include";o.headers=Object.assign({"x-requested-with":"m365"},o.headers||{});return fetch(A+p,o).then(function(r){return r.json()})}'
          'f("/api/blog/votes?handle="+H).then(function(d){bs.forEach(function(b){var s=b.dataset.s;b.querySelector(".n").textContent=(d.votes||{})[s]||0;if((d.mine||[]).indexOf(s)>-1)b.setAttribute("aria-pressed","true")})}).catch(function(){});'
          'bs.forEach(function(b){b.addEventListener("click",function(){f("/api/blog/vote",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({handle:H,slug:b.dataset.s})}).then(function(d){if(d.error==="login"){location.href=A.replace("api-","")+"/community/";return}'
          'if(d.ok){b.querySelector(".n").textContent=d.votes;b.setAttribute("aria-pressed",d.voted?"true":"false")}}).catch(function(){})})})})();')

FOLLOWJS = ('(function(){var A="%API%",b=document.querySelector(".bl-follow");if(!b)return;var H=b.dataset.h,t=b.querySelector(".t");'
            'function f(p,o){o=o||{};o.credentials="include";o.headers=Object.assign({"x-requested-with":"m365"},o.headers||{});return fetch(A+p,o).then(function(r){return r.json()})}'
            'function set(on){b.setAttribute("aria-pressed",on?"true":"false");t.textContent=on?"%FOLLOWING%":"%FOLLOW%"}'
            'f("/api/blog/following").then(function(d){if(d.following)set(d.following.indexOf(H)>-1)}).catch(function(){});'
            'b.addEventListener("click",function(){var on=b.getAttribute("aria-pressed")!=="true";f("/api/blog/follow",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({handle:H,on:on})}).then(function(d){if(d.error==="login"){location.href=A.replace("api-","")+"/community/";return}if(d.ok)set(on)}).catch(function(){})})})();')

CSS = ('<style>.bl-list{padding:0}.bl-list li{list-style:none;padding:.8em 0;border-bottom:1px solid var(--bd)}.bl-vote{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.25em .8em;background:var(--card);color:inherit}'
       '.bl-vote[aria-pressed=true]{border-color:var(--ac)}</style>')


def build(g, posts, people, api):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    ctags = g.get("community_tags")
    sitemap, TODAY = g["sitemap"], g["TODAY"]
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:48em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}
    if any(p.get("legacy") for p in posts) and "mirko-peters" not in pb:   # frueherer Blog: Autor ist auch ohne Profil-Export da
        pb["mirko-peters"] = {"handle": "mirko-peters", "name": "Mirko Peters"}
    posts = [p for p in posts if p["handle"] in pb]
    links = {i: [e["name"], f"{BASE}/entity/{i}/"] for i, e in ENTS.items()}
    for lang in COMM_LANGS:
        mine = [p for p in posts if p["lang"] == lang]
        if not mine:
            croot = f"{BASE}{pfx(lang)}/community/"; t0 = T(lang, "Blog", "Blog"); ru = f"{croot}blog/"
            intro = T(lang, "Blog posts from members of the Microsoft community. Nothing published in this language yet.", "Blogbeiträge von Mitgliedern der Microsoft-Community. In dieser Sprache gibt es noch nichts.")
            b = shell(lang, f'<h1>{esc(t0)}</h1><p class="mut">{esc(intro)}</p>')
            write(f"{pfx2(lang)}community/blog/index.html", page(lang, f"{t0} – M365.FM", intro, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=True))
            continue
        INDEX_VOTES = 10   # erst ab so vielen Upvotes bei Google (Index + Sitemap)
        w = WT.get(lang, WT["en"]); croot = f"{BASE}{pfx(lang)}/community/"
        links_l = {i: [e["name"], f"{BASE}{pfx(lang) if lang == 'de' else ''}/entity/{i}/"] for i, e in ENTS.items()}
        title_blog = T(lang, "Blog", "Blog")
        for p in mine:
            a = pb[p["handle"]]; au = f"{BASE}/community/u/{a['handle']}/"
            u = f"{croot}u/{p['handle']}/blog/{p['slug']}/"
            body_html, refs = (p["html"], []) if p.get("html") else wiki_render(p["body"], links_l, w)   # uebernommene fruehere Blogbeitraege: HTML bleibt vollstaendig erhalten
            if p.get("html") and not p.get("images"): p["images"] = re.findall(r'<img[^>]+src="(https://[^"]+)"', p["html"])
            topics = [t for t in p.get("topics", []) if t in ENTS]
            tl = "".join(f'<a class="mb-tag" href="{links_l[t][1]}">{esc(ENTS[t]["name"])}</a> ' for t in topics)
            vote = "" if p.get("legacy") else f'<p><button type="button" class="bl-vote" data-s="{esc(p["slug"])}" aria-pressed="false" aria-label="Upvote">▲ <span class="n">{p.get("votes", 0)}</span></button></p>'
            _kp, _fq, _fld = SNT.sections(p.get("keypoints"), p.get("faq"), lang)   # Kernpunkte und FAQ aus eigenen Feldern
            if p.get("html"): _fq = ""   # FAQ steht schon im Text des Beitrags; nur das Schema (FAQPage) bleibt
            cos = [c for c in (p.get("coauthors") or []) if c.get("handle") in pb and c["handle"] != p["handle"]]
            co_html = "".join(f' {esc(T(lang, "and", "und"))} <a href="{croot}u/{c["handle"]}/" rel="author">{esc(pb[c["handle"]]["name"])}</a>' for c in cos) if len(cos) == 1 else "".join(f', <a href="{croot}u/{c["handle"]}/" rel="author">{esc(pb[c["handle"]]["name"])}</a>' for c in cos)
            upd_html = f' · {esc(T(lang, "Updated", "Aktualisiert"))} <time datetime="{iso(p["updated"])}">{iso(p["updated"])}</time>' if p.get("updated") and iso(p["updated"]) != iso(p["published"]) else ""
            b = shell(lang, f'{WCSS}{CSS}<p class="mut"><a href="{croot}blog/">{esc(title_blog)}</a> · <a href="{croot}u/{p["handle"]}/blog/">{esc(a["name"])}</a></p><article class="wk-body" data-recipe="{ST.recipe_for(p["slug"], body_html)}"><h1>{esc(p["title"])}</h1>'
                            f'<p class="mut">{esc(T(lang, "By", "Von"))} <a href="{croot}u/{p["handle"]}/" rel="author">{esc(a["name"])}</a>{co_html}{esc(" · ")}<time datetime="{iso(p["published"])}">{iso(p["published"])}</time>{upd_html}</p>'
                            f'{("<p>" + esc(p["summary"]) + "</p>") if p.get("summary") else ""}{_aitr(p, lang)}{_kp}{body_html}{_fq}{SNT.CSS if (_kp or _fq) else ""}</article><p>{tl}</p>{vote}'
                            f'<p>{("" if p.get("legacy") else "<button type=" + chr(34) + "button" + chr(34) + " class=" + chr(34) + "bl-vote bl-follow" + chr(34) + " data-h=" + chr(34) + esc(p["handle"]) + chr(34) + " aria-pressed=" + chr(34) + "false" + chr(34) + "><span class=" + chr(34) + "t" + chr(34) + ">" + esc(T(lang, "Follow this blog", "Blog abonnieren")) + "</span></button> ")}<a href="{croot}u/{p["handle"]}/blog/feed.xml">RSS</a></p>'
                            + ("" if p.get("legacy") else (f'<section id="c-comments"></section>'
                            f'<script>{VOTEJS.replace("%API%", api).replace("%H%", p["handle"])}</script><script>{FOLLOWJS.replace("%API%", api).replace("%FOLLOW%", esc(T(lang, "Follow this blog", "Blog abonnieren"))).replace("%FOLLOWING%", esc(T(lang, "Following", "Abonniert")))}</script>'
                            + (ctags(lang, "blog%d" % p["id"]) if ctags else ""))))   # fruehere Blogbeitraege: keine Verbindung zur Community-Datenbank (kein Upvote, Abo, Kommentar)
            ld = [{"@context": "https://schema.org", "@type": "BlogPosting", "@id": u + "#post", "mainEntityOfPage": u, "headline": p["title"], "description": p.get("summary") or "",
                   "inLanguage": lang, **({"image": p["images"][:6]} if p.get("html") and p.get("images") else ({"image": [i["url"] for i in wiki_images(p["body"])]} if wiki_images(p["body"]) else {})), "datePublished": iso(p["published"]), "dateModified": iso(p.get("updated") or p["published"]),
                   "author": [{"@type": "Person", "@id": au + "#person", "name": a["name"], "url": au}] + [{"@type": "Person", "@id": f"{BASE}/community/u/{c['handle']}/#person", "name": pb[c["handle"]]["name"], "url": f"{BASE}/community/u/{c['handle']}/"} for c in cos],
                   "about": [{"@id": f"{BASE}/entity/{t}/#thing"} for t in topics], "citation": [{"@type": "CreativeWork", "name": r["title"], "url": r["url"]} for r in refs]}] + _fld
            noidx = False if p.get("html") else p.get("votes", 0) < INDEX_VOTES   # fruehere Blogbeitraege bleiben fuer Google sichtbar
            write(f"{pfx2(lang)}community/u/{p['handle']}/blog/{p['slug']}/index.html", page(lang, f'{p["title"]} – {a["name"]} | M365.FM', (p.get("summary") or "")[:155], u, b, None, ld, og_type="article", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((u, iso(p.get("updated") or p["published"]), None))
        # Verzeichnisse: je Autor und gesamt
        def lst(items):
            return '<ul class="bl-list">' + "".join(f'<li><a href="{croot}u/{p["handle"]}/blog/{p["slug"]}/"><b>{esc(p["title"])}</b></a> <span class="mut">· {esc(pb[p["handle"]]["name"])} · {iso(p["published"])}</span>'
                                                   f'{("<br>" + esc(p["summary"])) if p.get("summary") else ""}</li>' for p in items) + "</ul>"
        is_by = lambda p, h: p["handle"] == h or any(c.get("handle") == h for c in (p.get("coauthors") or []))   # Co-Autoren: der Beitrag steht auch in ihrer Blogliste
        for h in sorted({p["handle"] for p in mine} | {c["handle"] for p in mine for c in (p.get("coauthors") or []) if c.get("handle") in pb}):
            noidx = not any(is_by(p, h) and (p.get("html") or p.get("votes", 0) >= INDEX_VOTES) for p in mine)
            it = sorted([p for p in mine if is_by(p, h)], key=lambda x: -x["published"]); ru = f"{croot}u/{h}/blog/"
            nm = pb[h]["name"]
            b = shell(lang, f'{CSS}<h1>{esc(title_blog)} – {esc(nm)}</h1><p><a href="{croot}u/{h}/">{esc(nm)}</a></p>{lst(it)}')
            write(f"{pfx2(lang)}community/u/{h}/blog/index.html", page(lang, f'{title_blog} – {nm} | M365.FM', nm, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((ru, TODAY, None))
            write(f"{pfx2(lang)}community/u/{h}/blog/feed.xml", rss(f"{title_blog} – {nm}", ru, it, croot, pb, lang))
        noidx = not any(p.get("html") or p.get("votes", 0) >= INDEX_VOTES for p in mine)
        it = sorted(mine, key=lambda x: -x["published"]); ru = f"{croot}blog/"
        intro = T(lang, "Blog posts from members of the Microsoft community.", "Blogbeiträge von Mitgliedern der Microsoft-Community.")
        b = shell(lang, f'{CSS}<h1>{esc(title_blog)}</h1><p class="mut">{esc(intro)}</p>{lst(it)}')
        ld = [{"@context": "https://schema.org", "@type": "Blog", "name": "M365.FM " + title_blog, "url": ru, "inLanguage": lang,
               "blogPost": [{"@id": f"{croot}u/{p['handle']}/blog/{p['slug']}/#post"} for p in it[:50]]}]
        write(f"{pfx2(lang)}community/blog/feed.xml", rss("M365.FM " + title_blog, ru, it, croot, pb, lang))
        write(f"{pfx2(lang)}community/blog/index.html", page(lang, f'{title_blog} – M365.FM', intro, ru, b, None, ld, og_type="website", extra_head=LCSS, noindex=noidx))
        if not noidx:
            sitemap.append((ru, TODAY, None))


def rss(title, link, items, croot, pb, lang):
    from xml.sax.saxutils import escape as x
    from email.utils import formatdate
    it = "".join(f"<item><title>{x(p['title'])}</title><link>{croot}u/{p['handle']}/blog/{p['slug']}/</link><guid>{croot}u/{p['handle']}/blog/{p['slug']}/</guid>"
                 f"<pubDate>{formatdate(p['published'])}</pubDate><author>{x(pb[p['handle']]['name'])}</author><description>{x(p.get('summary') or '')}</description></item>" for p in items[:50])
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{x(title)}</title><link>{link}</link><description>{x(title)}</description><language>{lang}</language>{it}</channel></rss>'
