"""Startseite als Inhalts-Hub: Blog, Community-Podcast, Events und Stick-Man-Videos gemischt, mit Filter (Stick-Man-Videos sind ein Filter-Punkt von vielen)."""
from datetime import date
from site_i18n import pfx, T
from site_learn import esc, _fetch_json

_C = {}


def _load(api):
    if not _C:
        import site_blog, site_podcast, site_events, site_video, site_library
        _C["cv"] = site_video.fetch_videos(api); _C["posts"] = site_blog.fetch_posts(api); _C["eps"] = site_podcast.fetch_eps(api); _C["events"] = site_events.fetch_events(api)
        _C["lib"] = site_library.fetch_items(api); _C["feed"] = (_fetch_json(f"{api}/api/feed/export") or {}).get("items", [])
    return _C


CSS = ('<style>.hub-f{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.4em 1em;margin:.2em .3em .2em 0;background:var(--card);color:inherit}'
       '.hub-f[aria-pressed=true]{border-color:var(--ac);font-weight:700}.hub-card .kicker{margin-bottom:.3em}.hub-card{border:1px solid var(--bd);border-radius:.6em;padding:.9em 1em;background:var(--card)}'
       '.hub-card a{text-decoration:none}.hub-card h3{margin:.1em 0 .3em}.hub-card[hidden],.thumb[hidden]{display:none}</style>')
JS = ('<script>(function(){var b=[].slice.call(document.querySelectorAll(".hub-f")),c=[].slice.call(document.querySelectorAll("#hub [data-k]")),N=%N%;'
      'function s(k){b.forEach(function(x){x.setAttribute("aria-pressed",x.dataset.k===k?"true":"false")});var n=0;c.forEach(function(e){var ok=k==="all"?n<N:e.dataset.k===k;if(ok&&k==="all")n++;e.hidden=!ok})}'
      'b.forEach(function(x){x.addEventListener("click",function(){s(x.dataset.k)})});s("all")})();</script>')


def hub(g, lang, base, api, videos, vid_html, root=False):
    """videos: Liste von Episoden-Items (mit "date"), vid_html(item) -> HTML-Karte. Rückgabe: HTML-Block."""
    C = _load(api); today = date.today().isoformat(); cards = []
    ok = lambda l: root or l == lang
    croot = f"{base}{pfx(lang)}/community/"
    for p in C["posts"]:
        if ok(p["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(p["published"]).strftime("%Y-%m-%d")
            cards.append((d, "blog", f'<div class="hub-card" data-k="blog"><a href="{base}{pfx(p["lang"])}/community/u/{p["handle"]}/blog/{p["slug"]}/"><div class="kicker">{esc(T(lang, "Blog", "Blog"))}</div><h3>{esc(p["title"])}</h3></a><p class="mut">{esc(p.get("summary") or "")} {esc(p["name"])} · {d}</p></div>'))
    for e in C["eps"]:
        if ok(e["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(e["published"]).strftime("%Y-%m-%d")
            cards.append((d, "podcast", f'<div class="hub-card" data-k="podcast"><a href="{base}{pfx(e["lang"])}/community/podcast/{e["slug"]}/"><div class="kicker">{esc(T(lang, "Podcast", "Podcast"))}</div><h3>{esc(e["title"])}</h3></a><p class="mut">{esc(e["name"])} · {d}</p></div>'))
    for ev in C["events"]:
        d = (ev.get("start") or "")[:10]
        if d and d >= today:
            cards.append((d, "event", f'<div class="hub-card" data-k="event"><a href="{croot}events/{ev["handle"]}/"><div class="kicker">{esc(T(lang, "Event", "Event"))}</div><h3>{esc(ev["title"])}</h3></a><p class="mut">{esc(d)}{(" · " + esc(ev["summary"][:110])) if ev.get("summary") else ""}</p></div>'))
    import site_library as SL
    for it in C["lib"]:
        if ok(it["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(it["published"]).strftime("%Y-%m-%d")
            cards.append((d, "library", f'<div class="hub-card" data-k="library"><a href="{base}{pfx(it["lang"])}/community/library/{it["handle"]}-{it["slug"]}/"><div class="kicker">{esc(T(lang, "Library", "Bibliothek"))} · {esc(SL.kl(lang, it["kind"]))}</div><h3>{esc(it["title"])}</h3></a><p class="mut">{esc(it.get("summary") or "")} {esc(it["name"])} · {d}</p></div>'))
    KL = {"youtube": "YouTube", "github": "GitHub", "blog": "Blog", "podcast": "Podcast", "newsletter": "Newsletter", "mastodon": "Mastodon", "bluesky": "Bluesky", "website": "Web"}
    for f in C["feed"]:
        d = __import__("datetime").datetime.fromtimestamp(f["published"]).strftime("%Y-%m-%d")
        who = f'{base}/community/{"c" if f["type"] == "o" else "u"}/{f["handle"]}/'
        cards.append((d, "feed", f'<div class="hub-card" data-k="feed"><div class="kicker">{esc(T(lang, "From the creators", "Von den Creatorn"))} · {esc(KL.get(f["kind"], f["kind"].title()))}</div><h3><a href="{esc(f["url"])}" rel="nofollow ugc noopener" target="_blank">{esc(f["title"])}</a></h3><p class="mut"><a href="{who}">{esc(f["name"])}</a> · {d}</p></div>'))
    for e in C["cv"]:
        if ok(e["lang"]):
            d = __import__("datetime").datetime.fromtimestamp(e["published"]).strftime("%Y-%m-%d")
            cards.append((d, "creatorvideo", f'<div class="thumb" data-k="creatorvideo"><a href="{base}{pfx(e["lang"])}/community/video/{e["slug"]}/"><figure class="cover" style="margin-inline:0"><img src="https://i.ytimg.com/vi/{e["video_id"]}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"></figure><h3>{esc(e["title"])}</h3></a><p>{esc(e["name"])} · {d}</p></div>'))
    for v in videos[:24]:
        cards.append((str(v["date"])[:10], "video", vid_html(v).replace('<div class="thumb">', '<div class="thumb" data-k="video">', 1)))
    cards.sort(key=lambda x: x[0], reverse=True)
    counts = {}
    for _, k, _h in cards: counts[k] = counts.get(k, 0) + 1
    labels = [("all", T(lang, "All", "Alle")), ("blog", "Blog"), ("podcast", "Podcast"), ("event", T(lang, "Events", "Events")), ("library", T(lang, "Library", "Bibliothek")), ("feed", T(lang, "From the creators", "Von den Creatorn")), ("creatorvideo", T(lang, "Creator videos", "Creator-Videos")), ("video", T(lang, "Stick-man videos", "Stick-Man-Videos"))]
    chips = "".join(f'<button type="button" class="hub-f" data-k="{k}" aria-pressed="false">{esc(l)}{"" if k == "all" else " · " + str(counts.get(k, 0))}</button>' for k, l in labels if k == "all" or counts.get(k))
    cta = (f'<p><a class="btn main" href="{croot}">{esc(T(lang, "Join the community", "Zur Community"))}</a> '
           f'<a class="btn" href="{croot}blog/">Blog</a> <a class="btn" href="{croot}podcast/">Podcast</a> <a class="btn" href="{croot}events/">Events</a> <a class="btn" href="{croot}library/">{esc(T(lang, "Library", "Bibliothek"))}</a> <a class="btn" href="{croot}guests/">{esc(T(lang, "Guest exchange", "Gäste-Börse"))}</a></p>')
    return (CSS + f'<div role="group" aria-label="{esc(T(lang, "Filter", "Filter"))}">{chips}</div><div id="hub" class="thumbs">' + "".join(h for _, _k, h in cards) + "</div>" + cta + JS.replace("%N%", "18"))
