"""Startseite als Inhalts-Hub: Blog, Community-Podcast, Events und Stick-Man-Videos gemischt, mit Filter (Stick-Man-Videos sind ein Filter-Punkt von vielen)."""
from datetime import date
from site_i18n import pfx, T
from site_learn import esc

_C = {}


def _load(api):
    if not _C:
        import site_blog, site_podcast, site_events
        _C["posts"] = site_blog.fetch_posts(api); _C["eps"] = site_podcast.fetch_eps(api); _C["events"] = site_events.fetch_events(api)
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
    for v in videos[:24]:
        cards.append((str(v["date"])[:10], "video", vid_html(v).replace('<div class="thumb">', '<div class="thumb" data-k="video">', 1)))
    cards.sort(key=lambda x: x[0], reverse=True)
    counts = {}
    for _, k, _h in cards: counts[k] = counts.get(k, 0) + 1
    labels = [("all", T(lang, "All", "Alle")), ("blog", "Blog"), ("podcast", "Podcast"), ("event", T(lang, "Events", "Events")), ("video", T(lang, "Stick-man videos", "Stick-Man-Videos"))]
    chips = "".join(f'<button type="button" class="hub-f" data-k="{k}" aria-pressed="false">{esc(l)}{"" if k == "all" else " · " + str(counts.get(k, 0))}</button>' for k, l in labels if k == "all" or counts.get(k))
    cta = (f'<p><a class="btn main" href="{croot}">{esc(T(lang, "Join the community", "Zur Community"))}</a> '
           f'<a class="btn" href="{croot}blog/">Blog</a> <a class="btn" href="{croot}podcast/">Podcast</a> <a class="btn" href="{croot}events/">Events</a></p>')
    return (CSS + f'<div role="group" aria-label="{esc(T(lang, "Filter", "Filter"))}">{chips}</div><div id="hub" class="thumbs">' + "".join(h for _, _k, h in cards) + "</div>" + cta + JS.replace("%N%", "18"))
