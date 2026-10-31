"""Community-Podcast: Seiten fuer veroeffentlichte (von der Redaktion in Spreaker freigegebene) Folgen, Verzeichnis und RSS."""
from datetime import datetime, timezone
from site_i18n import COMM_LANGS, pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS


def fetch_eps(api):
    return (_fetch_json(f"{api}/api/podcast/export") or {}).get("items", [])


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def rss(title, link, items, croot, lang):
    from xml.sax.saxutils import escape as x
    from email.utils import formatdate
    it = "".join(f"<item><title>{x(p['title'])}</title><link>{croot}podcast/{p['slug']}/</link><guid>{croot}podcast/{p['slug']}/</guid><pubDate>{formatdate(p['published'])}</pubDate>"
                 f"<author>{x(p['name'])}</author><description>{x(p.get('description') or '')}</description></item>" for p in items[:50])
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{x(title)}</title><link>{link}</link><description>{x(title)}</description><language>{lang}</language>{it}</channel></rss>'


def build(g, eps, people, api):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY, ctags = g["sitemap"], g["TODAY"], g.get("community_tags")
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:48em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}
    eps = [e for e in eps if e["handle"] in pb]
    for lang in COMM_LANGS:
        mine = [e for e in eps if e["lang"] == lang]
        if not mine:
            croot = f"{BASE}{pfx(lang)}/community/"; t0 = T(lang, "Community podcast", "Community-Podcast"); ru = f"{croot}podcast/"
            intro = T(lang, "Podcast episodes from members of the Microsoft community, reviewed by the editors. Nothing published in this language yet.", "Podcastfolgen von Mitgliedern der Microsoft-Community, von der Redaktion geprüft. In dieser Sprache gibt es noch nichts.")
            b = shell(lang, f'<h1>{esc(t0)}</h1><p class="mut">{esc(intro)}</p>')
            write(f"{pfx2(lang)}community/podcast/index.html", page(lang, f"{t0} – M365.FM", intro, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=True))
            continue
        croot = f"{BASE}{pfx(lang)}/community/"; ttl = T(lang, "Community podcast", "Community-Podcast")
        for e in mine:
            u = f"{croot}podcast/{e['slug']}/"; au = f"{BASE}/community/u/{e['handle']}/"
            topics = [t for t in e.get("topics", []) if t in ENTS]
            tl = "".join(f'<a class="mb-tag" href="{BASE}/entity/{t}/">{esc(ENTS[t]["name"])}</a> ' for t in topics)
            player = "" if not e["spreaker_id"] else f'<iframe title="{esc(e["title"])}" src="https://widget.spreaker.com/player?episode_id={e["spreaker_id"]}&theme=light" width="100%" height="200" loading="lazy" style="border:0"></iframe>'
            gs = [g for g in (e.get("guests") or []) if g.get("handle") != e["handle"]]
            guests_html = (f'<p class="mut">{esc(T(lang, "Guests", "Gäste"))}: ' + ", ".join(f'<a href="{croot}u/{g["handle"]}/">{esc(g["name"])}</a>' for g in gs) + "</p>") if gs else ""
            b = shell(lang, f'<p class="mut"><a href="{croot}podcast/">{esc(ttl)}</a></p><article><h1>{esc(e["title"])}</h1>'
                            f'<p class="mut">{esc(T(lang, "By", "Von"))} <a href="{croot}u/{e["handle"]}/" rel="author">{esc(e["name"])}</a> · {iso(e["published"])}</p>{guests_html}{player}'
                            f'{"".join("<p>" + esc(par) + "</p>" for par in (e.get("description") or "").split(chr(10) * 2) if par.strip())}'
                            f'{"<p class=mut>" + esc(T(lang, "The author disclosed the use of AI.", "Die Autorin bzw. der Autor hat den KI-Einsatz offengelegt.")) + "</p>" if e.get("ai") else ""}</article><p>{tl}</p>'
                            f'<p><a class="btn" href="{esc(e["ep_url"])}" rel="noopener">{esc(T(lang, "Listen on Spreaker", "Bei Spreaker anhören"))}</a> <a href="{croot}podcast/feed.xml">RSS</a></p><section id="c-comments"></section>'
                            + (ctags(lang, "podcast%d" % e["id"]) if ctags else ""))
            ld = [{"@context": "https://schema.org", "@type": "PodcastEpisode", "@id": u + "#episode", "url": u, "name": e["title"], "description": (e.get("description") or "")[:500], "inLanguage": lang,
                   "datePublished": iso(e["published"]), "author": {"@type": "Person", "@id": au + "#person", "name": e["name"], "url": au}, **({"actor": [{"@type": "Person", "@id": f"{BASE}/community/u/{g['handle']}/#person", "name": g["name"], "url": f"{BASE}/community/u/{g['handle']}/"} for g in gs]} if gs else {}),
                   "partOfSeries": {"@type": "PodcastSeries", "name": "M365.FM", "url": f"{BASE}/"}, "about": [{"@id": f"{BASE}/entity/{t}/#entity"} for t in topics],
                   "associatedMedia": {"@type": "AudioObject", "contentUrl": e["ep_url"]}}]
            write(f"{pfx2(lang)}community/podcast/{e['slug']}/index.html", page(lang, f'{e["title"]} – {ttl} | M365.FM', (e.get("description") or "")[:155], u, b, None, ld, og_type="article", extra_head=LCSS, noindex=e["title"].startswith("[Test]")))
            if not e["title"].startswith("[Test]"): sitemap.append((u, iso(e["published"]), None))
        it = sorted(mine, key=lambda x: -x["published"]); ru = f"{croot}podcast/"
        lst = '<ul class="bl-list" style="padding:0;list-style:none">' + "".join(f'<li style="padding:.7em 0;border-bottom:1px solid var(--bd)"><a href="{croot}podcast/{e["slug"]}/"><b>{esc(e["title"])}</b></a> <span class="mut">· {esc(e["name"])} · {iso(e["published"])}</span></li>' for e in it) + "</ul>"
        b = shell(lang, f'<h1>{esc(ttl)}</h1><p class="mut">{esc(T(lang, "Podcast episodes from members of the Microsoft community, reviewed by the editors.", "Podcastfolgen von Mitgliedern der Microsoft-Community, von der Redaktion geprüft."))}</p>{lst}')
        write(f"{pfx2(lang)}community/podcast/index.html", page(lang, f'{ttl} – M365.FM', ttl, ru, b, None, [{"@context": "https://schema.org", "@type": "CollectionPage", "name": ttl, "url": ru}], og_type="website", extra_head=LCSS))
        write(f"{pfx2(lang)}community/podcast/feed.xml", rss("M365.FM " + ttl, ru, it, croot, lang))
        sitemap.append((ru, TODAY, None))
