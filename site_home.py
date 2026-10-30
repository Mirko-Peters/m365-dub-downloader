"""Startseite als Inhalts-Hub: Blog, Community-Podcast, Events und Stick-Man-Videos gemischt, mit Filter (Stick-Man-Videos sind ein Filter-Punkt von vielen)."""
from datetime import date
from site_i18n import pfx, T
from site_learn import esc, _fetch_json, ENTS

_C = {}


def _load(api):
    if not _C:
        import site_blog, site_podcast, site_events, site_video, site_library, site_updates
        site_updates.load(api)
        _C["cv"] = site_video.fetch_videos(api); _C["posts"] = site_blog.fetch_posts(api); _C["eps"] = site_podcast.fetch_eps(api); _C["events"] = site_events.fetch_events(api)
        _C["lib"] = site_library.fetch_items(api); _C["feed"] = (_fetch_json(f"{api}/api/feed/export") or {}).get("items", [])
    return _C


CSS = ('<style>.hub-f{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.4em 1em;margin:.2em .3em .2em 0;background:var(--card);color:inherit}'
       '.hub-f[aria-pressed=true]{border-color:var(--ac);font-weight:700}.hub-card .kicker{margin-bottom:.3em}.hub-card{border:1px solid var(--bd);border-radius:.6em;padding:.9em 1em;background:var(--card)}'
       '.hub-card a{text-decoration:none}.hub-card h3{margin:.1em 0 .3em}.hub-ctl{display:flex;flex-wrap:wrap;gap:.5em;margin:.6em 0}.hub-ctl input,.hub-ctl select{font:inherit;padding:.4em .7em;border:1px solid var(--bd);border-radius:.4em;background:var(--card);color:inherit;max-width:100%}.hub-card[hidden],.thumb[hidden]{display:none}</style>')
JS = ('<script>(function(){var b=[].slice.call(document.querySelectorAll(".hub-f")),c=[].slice.call(document.querySelectorAll("#hub [data-k]")),N=%N%,NM=%NAMES%,'
      'q=document.getElementById("hub-q"),sa=document.getElementById("hub-a"),st=document.getElementById("hub-t"),sel=document.getElementById("hub-sel"),S={k:"all",ts:[]};'
      'function ap(){var n=0,ql=q?q.value.trim().toLowerCase():"",a=sa?sa.value:"",f=S.k!=="all"||ql||a||S.ts.length;'
      'b.forEach(function(x){x.setAttribute("aria-pressed",x.dataset.k===S.k?"true":"false")});'
      'c.forEach(function(e){var t=(e.dataset.t||"").split(" "),ok=(S.k==="all"||e.dataset.k===S.k)&&(!a||e.dataset.a===a)&&(!ql||(e.dataset.q||"").indexOf(ql)>-1||(e.dataset.a||"").toLowerCase().indexOf(ql)>-1)&&S.ts.every(function(x){return t.indexOf(x)>-1});'
      'if(ok&&!f){ok=n<N;n++}e.hidden=!ok});'
      'if(sel){sel.textContent="";S.ts.forEach(function(x){var s=document.createElement("button");s.type="button";s.className="hub-f";s.textContent=NM[x]+" ✕";s.title="%RM%";s.onclick=function(){S.ts=S.ts.filter(function(y){return y!==x});ap()};sel.appendChild(s)})}}'
      'b.forEach(function(x){x.addEventListener("click",function(){S.k=x.dataset.k;ap()})});'
      'if(q)q.addEventListener("input",ap);if(sa)sa.addEventListener("change",ap);'
      'if(st)st.addEventListener("change",function(){if(st.value&&S.ts.indexOf(st.value)<0)S.ts.push(st.value);st.value="";ap()});ap()})();</script>')


def hub(g, lang, base, api, videos, vid_html, root=False):
    """videos: Liste von Episoden-Items (mit "date"), vid_html(item) -> HTML-Karte. Rückgabe: HTML-Block."""
    C = _load(api); today = date.today().isoformat(); cards = []
    ok = lambda l: root or l == lang
    def tag(author, topics, title):
        dd, kk, hh = cards[-1]
        hh = hh.replace(f'data-k="{kk}"', f'data-k="{kk}" data-a="{esc(author or "")}" data-t="{esc(" ".join(t for t in (topics or []) if t in ENTS))}" data-q="{esc((title or "").lower())}"', 1)
        cards[-1] = (dd, kk, hh)
    croot = f"{base}{pfx(lang)}/community/"
    for p in C["posts"]:
        if ok(p["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(p["published"]).strftime("%Y-%m-%d")
            cards.append((d, "blog", f'<div class="hub-card" data-k="blog"><a href="{base}{pfx(p["lang"])}/community/u/{p["handle"]}/blog/{p["slug"]}/"><div class="kicker">{esc(T(lang, "Blog", "Blog"))}</div><h3>{esc(p["title"])}</h3></a><p class="mut">{esc(p.get("summary") or "")} {esc(p["name"])} · {d}</p></div>'))
            tag(p["name"], p.get("topics"), p["title"])
    for e in C["eps"]:
        if ok(e["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(e["published"]).strftime("%Y-%m-%d")
            cards.append((d, "podcast", f'<div class="hub-card" data-k="podcast"><a href="{base}{pfx(e["lang"])}/community/podcast/{e["slug"]}/"><div class="kicker">{esc(T(lang, "Podcast", "Podcast"))}</div><h3>{esc(e["title"])}</h3></a><p class="mut">{esc(e["name"])} · {d}</p></div>'))
            tag(e["name"], e.get("topics"), e["title"])
    for ev in C["events"]:
        d = (ev.get("start") or "")[:10]
        if d and d >= today:
            cards.append((d, "event", f'<div class="hub-card" data-k="event"><a href="{croot}events/{ev["handle"]}/"><div class="kicker">{esc(T(lang, "Event", "Event"))}</div><h3>{esc(ev["title"])}</h3></a><p class="mut">{esc(d)}{(" · " + esc(ev["summary"][:110])) if ev.get("summary") else ""}</p></div>'))
            tag("", ev.get("topics"), ev["title"])
    import site_library as SL
    for it in C["lib"]:
        if ok(it["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(it["published"]).strftime("%Y-%m-%d")
            cards.append((d, "library", f'<div class="hub-card" data-k="library"><a href="{base}{pfx(it["lang"])}/community/library/{it["handle"]}-{it["slug"]}/"><div class="kicker">{esc(T(lang, "Library", "Bibliothek"))} · {esc(SL.kl(lang, it["kind"]))}</div><h3>{esc(it["title"])}</h3></a><p class="mut">{esc(it.get("summary") or "")} {esc(it["name"])} · {d}</p></div>'))
            tag(it["name"], it.get("topics"), it["title"])
    KL = {"youtube": "YouTube", "github": "GitHub", "blog": "Blog", "podcast": "Podcast", "newsletter": "Newsletter", "mastodon": "Mastodon", "bluesky": "Bluesky", "website": "Web"}
    for f in C["feed"]:
        d = __import__("datetime").datetime.fromtimestamp(f["published"]).strftime("%Y-%m-%d")
        who = f'{base}/community/{"c" if f["type"] == "o" else "u"}/{f["handle"]}/'
        cards.append((d, "feed", f'<div class="hub-card" data-k="feed"><div class="kicker">{esc(T(lang, "From the creators", "Von den Creatorn"))} · {esc(KL.get(f["kind"], f["kind"].title()))}</div><h3><a href="{esc(f["url"])}" rel="nofollow ugc noopener" target="_blank">{esc(f["title"])}</a></h3><p class="mut"><a href="{who}">{esc(f["name"])}</a> · {d}</p></div>'))
        tag(f["name"], [], f["title"])
    import site_updates as SU
    seen_u = set()
    for u in SU.ALL:
        if len(seen_u) >= 40: break
        if u["url"] in seen_u: continue
        seen_u.add(u["url"])
        cards.append((SU.day(u["published"]), "update", f'<div class="hub-card" data-k="update"><div class="kicker">{esc(T(lang, "Update", "Update"))} · {esc(u["source"])}</div><h3><a href="{esc(u["url"])}" rel="nofollow noopener" target="_blank">{esc(u["title"])}</a></h3><p class="mut">{SU.day(u["published"])}</p></div>'))
        tag("Microsoft", [x["eid"] for x in SU.ALL if x["url"] == u["url"]], u["title"])
    for e in C["cv"]:
        if ok(e["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(e["published"]).strftime("%Y-%m-%d")
            cards.append((d, "creatorvideo", f'<div class="thumb" data-k="creatorvideo"><a href="{base}{pfx(e["lang"])}/community/video/{e["slug"]}/"><figure class="cover" style="margin-inline:0"><img src="https://i.ytimg.com/vi/{e["video_id"]}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"></figure><h3>{esc(e["title"])}</h3></a><p>{esc(e["name"])} · {d}</p></div>'))
            tag(e["name"], e.get("topics"), e["title"])
    for v in videos[:24]:
        cards.append((str(v["date"])[:10], "video", vid_html(v).replace('<div class="thumb">', '<div class="thumb" data-k="video">', 1)))
        tag("Mirko Peters", [], str(v["e"]["title"]))
    cards.sort(key=lambda x: x[0], reverse=True)
    counts = {}
    for _, k, _h in cards: counts[k] = counts.get(k, 0) + 1
    labels = [("all", T(lang, "All", "Alle")), ("blog", "Blog"), ("podcast", "Podcast"), ("event", T(lang, "Events", "Events")), ("library", T(lang, "Library", "Bibliothek")), ("feed", T(lang, "From the creators", "Von den Creatorn")), ("update", T(lang, "Microsoft updates", "Microsoft-Updates")), ("creatorvideo", T(lang, "Creator videos", "Creator-Videos")), ("video", T(lang, "Stick-man videos", "Stick-Man-Videos"))]
    chips = "".join(f'<button type="button" class="hub-f" data-k="{k}" aria-pressed="false">{esc(l)}{"" if k == "all" else " · " + str(counts.get(k, 0))}</button>' for k, l in labels if k == "all" or counts.get(k))
    cta = (f'<p><a class="btn main" href="{croot}">{esc(T(lang, "Join the community", "Zur Community"))}</a> '
           f'<a class="btn" href="{croot}blog/">Blog</a> <a class="btn" href="{croot}podcast/">Podcast</a> <a class="btn" href="{croot}events/">Events</a> <a class="btn" href="{croot}library/">{esc(T(lang, "Library", "Bibliothek"))}</a> <a class="btn" href="{croot}guests/">{esc(T(lang, "Guest exchange", "Gäste-Börse"))}</a></p>')
    import re as _re
    auth, tcount = {}, {}
    for _, _k, h in cards:
        a = _re.search(r'data-a="([^"]*)"', h); t = _re.search(r'data-t="([^"]*)"', h)
        if a and a.group(1): auth[a.group(1)] = auth.get(a.group(1), 0) + 1
        for x in (t.group(1).split() if t else []): tcount[x] = tcount.get(x, 0) + 1
    aopts = "".join(f'<option value="{a}">{a} ({n})</option>' for a, n in sorted(auth.items(), key=lambda x: x[0].lower()))
    topts = "".join(f'<option value="{i}">{esc(ENTS[i]["name"])} ({n})</option>' for i, n in sorted(tcount.items(), key=lambda x: ENTS[x[0]]["name"].lower()))
    ctl = (f'<div class="hub-ctl"><input type="search" id="hub-q" placeholder="{esc(T(lang, "Search title or creator", "Titel oder Creator suchen"))}" aria-label="{esc(T(lang, "Search", "Suche"))}">'
           f'<select id="hub-a" aria-label="{esc(T(lang, "Creator", "Creator"))}"><option value="">{esc(T(lang, "All creators", "Alle Creator"))}</option>{aopts}</select>'
           f'<select id="hub-t" aria-label="{esc(T(lang, "Topic", "Thema"))}"><option value="">{esc(T(lang, "Add topic filter", "Thema hinzufügen"))}</option>{topts}</select></div><div id="hub-sel" aria-live="polite"></div>') if (auth or tcount) else ""
    return (CSS + f'<div role="group" aria-label="{esc(T(lang, "Filter", "Filter"))}">{chips}</div>{ctl}<div id="hub" class="thumbs">' + "".join(h for _, _k, h in cards) + "</div>" + cta + JS.replace("%N%", "18").replace("%NAMES%", __import__("json").dumps({i: ENTS[i]["name"] for i in tcount}, ensure_ascii=False)).replace("%RM%", esc(T(lang, "remove", "entfernen"))))
