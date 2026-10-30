"""Blog je Mitglied: oeffentliche Beitragsseiten (BlogPosting) und Verzeichnisse je Sprache. Beitraege kommen freigegeben aus /api/blog/export."""
import json
from datetime import datetime, timezone
from site_i18n import COMM_LANGS, pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS, WT, wiki_render, WCSS


def fetch_posts(api):
    return (_fetch_json(f"{api}/api/blog/export") or {}).get("items", [])


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


VOTEJS = ('(function(){var A="%API%",H="%H%",bs=[].slice.call(document.querySelectorAll(".bl-vote"));if(!bs.length)return;'
          'function f(p,o){o=o||{};o.credentials="include";o.headers=Object.assign({"x-requested-with":"m365"},o.headers||{});return fetch(A+p,o).then(function(r){return r.json()})}'
          'f("/api/blog/votes?handle="+H).then(function(d){bs.forEach(function(b){var s=b.dataset.s;b.querySelector(".n").textContent=(d.votes||{})[s]||0;if((d.mine||[]).indexOf(s)>-1)b.setAttribute("aria-pressed","true")})}).catch(function(){});'
          'bs.forEach(function(b){b.addEventListener("click",function(){f("/api/blog/vote",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({handle:H,slug:b.dataset.s})}).then(function(d){if(d.error==="login"){location.href=A.replace("api-","")+"/community/";return}'
          'if(d.ok){b.querySelector(".n").textContent=d.votes;b.setAttribute("aria-pressed",d.voted?"true":"false")}}).catch(function(){})})})})();')

CSS = ('<style>.bl-list{padding:0}.bl-list li{list-style:none;padding:.8em 0;border-bottom:1px solid var(--bd)}.bl-vote{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.25em .8em;background:var(--card);color:inherit}'
       '.bl-vote[aria-pressed=true]{border-color:var(--ac)}</style>')


def build(g, posts, people, api):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY = g["sitemap"], g["TODAY"]
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:48em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}
    posts = [p for p in posts if p["handle"] in pb]
    if not posts:
        return
    links = {i: [e["name"], f"{BASE}/entity/{i}/"] for i, e in ENTS.items()}
    for lang in COMM_LANGS:
        mine = [p for p in posts if p["lang"] == lang]
        if not mine:
            continue
        noidx = lang != "en" and lang != "de"
        w = WT.get(lang, WT["en"]); croot = f"{BASE}{pfx(lang)}/community/"
        links_l = {i: [e["name"], f"{BASE}{pfx(lang) if lang == 'de' else ''}/entity/{i}/"] for i, e in ENTS.items()}
        title_blog = T(lang, "Blog", "Blog")
        for p in mine:
            a = pb[p["handle"]]; au = f"{BASE}/community/u/{a['handle']}/"
            u = f"{croot}u/{p['handle']}/blog/{p['slug']}/"
            body_html, refs = wiki_render(p["body"], links_l, w)
            topics = [t for t in p.get("topics", []) if t in ENTS]
            tl = "".join(f'<a class="mb-tag" href="{links_l[t][1]}">{esc(ENTS[t]["name"])}</a> ' for t in topics)
            vote = f'<p><button type="button" class="bl-vote" data-s="{esc(p["slug"])}" aria-pressed="false" aria-label="Upvote">▲ <span class="n">{p.get("votes", 0)}</span></button></p>'
            b = shell(lang, f'{WCSS}{CSS}<p class="mut"><a href="{croot}blog/">{esc(title_blog)}</a> · <a href="{croot}u/{p["handle"]}/blog/">{esc(a["name"])}</a></p><article class="wk-body"><h1>{esc(p["title"])}</h1>'
                            f'<p class="mut">{esc(T(lang, "By", "Von"))} <a href="{croot}u/{p["handle"]}/">{esc(a["name"])}</a> · {iso(p["published"])}</p>'
                            f'{("<p>" + esc(p["summary"]) + "</p>") if p.get("summary") else ""}{body_html}</article><p>{tl}</p>{vote}'
                            f'<script>{VOTEJS.replace("%API%", api).replace("%H%", p["handle"])}</script>')
            ld = [{"@context": "https://schema.org", "@type": "BlogPosting", "@id": u + "#post", "mainEntityOfPage": u, "headline": p["title"], "description": p.get("summary") or "",
                   "inLanguage": lang, "datePublished": iso(p["published"]), "dateModified": iso(p.get("updated") or p["published"]),
                   "author": {"@type": "Person", "@id": au + "#person", "name": a["name"], "url": au},
                   "about": [{"@id": f"{BASE}/entity/{t}/#thing"} for t in topics], "citation": [{"@type": "CreativeWork", "name": r["title"], "url": r["url"]} for r in refs]}]
            write(f"{pfx2(lang)}community/u/{p['handle']}/blog/{p['slug']}/index.html", page(lang, f'{p["title"]} – {a["name"]} | M365.FM', (p.get("summary") or "")[:155], u, b, None, ld, og_type="article", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((u, iso(p.get("updated") or p["published"]), None))
        # Verzeichnisse: je Autor und gesamt
        def lst(items):
            return '<ul class="bl-list">' + "".join(f'<li><a href="{croot}u/{p["handle"]}/blog/{p["slug"]}/"><b>{esc(p["title"])}</b></a> <span class="mut">· {esc(pb[p["handle"]]["name"])} · {iso(p["published"])}</span>'
                                                   f'{("<br>" + esc(p["summary"])) if p.get("summary") else ""}</li>' for p in items) + "</ul>"
        for h in sorted({p["handle"] for p in mine}):
            it = sorted([p for p in mine if p["handle"] == h], key=lambda x: -x["published"]); ru = f"{croot}u/{h}/blog/"
            nm = pb[h]["name"]
            b = shell(lang, f'{CSS}<h1>{esc(title_blog)} – {esc(nm)}</h1><p><a href="{croot}u/{h}/">{esc(nm)}</a></p>{lst(it)}')
            write(f"{pfx2(lang)}community/u/{h}/blog/index.html", page(lang, f'{title_blog} – {nm} | M365.FM', nm, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((ru, TODAY, None))
        it = sorted(mine, key=lambda x: -x["published"]); ru = f"{croot}blog/"
        intro = T(lang, "Blog posts from members of the Microsoft community.", "Blogbeiträge von Mitgliedern der Microsoft-Community.")
        b = shell(lang, f'{CSS}<h1>{esc(title_blog)}</h1><p class="mut">{esc(intro)}</p>{lst(it)}')
        ld = [{"@context": "https://schema.org", "@type": "Blog", "name": "M365.FM " + title_blog, "url": ru, "inLanguage": lang,
               "blogPost": [{"@id": f"{croot}u/{p['handle']}/blog/{p['slug']}/#post"} for p in it[:50]]}]
        write(f"{pfx2(lang)}community/blog/index.html", page(lang, f'{title_blog} – M365.FM', intro, ru, b, None, ld, og_type="website", extra_head=LCSS, noindex=noidx))
        if not noidx:
            sitemap.append((ru, TODAY, None))
