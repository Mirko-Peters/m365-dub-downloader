"""Creator-Videos auf dem YouTube-Kanal m365 Show: Seiten fuer von der Redaktion veroeffentlichte Videos, Verzeichnis und RSS."""
from datetime import datetime, timezone
from site_i18n import COMM_LANGS, pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS


def fetch_videos(api):
    return (_fetch_json(f"{api}/api/video/export") or {}).get("items", [])


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def rss(title, link, items, croot, lang):
    from xml.sax.saxutils import escape as x
    from email.utils import formatdate
    it = "".join(f"<item><title>{x(p['title'])}</title><link>{croot}video/{p['slug']}/</link><guid>{croot}video/{p['slug']}/</guid><pubDate>{formatdate(p['published'])}</pubDate>"
                 f"<author>{x(p['name'])}</author><description>{x(p.get('description') or '')}</description></item>" for p in items[:50])
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{x(title)}</title><link>{link}</link><description>{x(title)}</description><language>{lang}</language>{it}</channel></rss>'


def build(g, vids, people, api):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY, ctags = g["sitemap"], g["TODAY"], g.get("community_tags")
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:48em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}
    vids = [v for v in vids if v["handle"] in pb]
    for lang in COMM_LANGS:
        mine = [v for v in vids if v["lang"] == lang]
        if not mine:
            croot = f"{BASE}{pfx(lang)}/community/"; t0 = T(lang, "Creator videos", "Creator-Videos"); ru = f"{croot}video/"
            intro = T(lang, "Videos from community creators on the m365 Show YouTube channel. Nothing published in this language yet.", "Videos von Community-Creators auf dem YouTube-Kanal m365 Show. In dieser Sprache gibt es noch nichts.")
            b = shell(lang, f'<h1>{esc(t0)}</h1><p class="mut">{esc(intro)}</p><p><a class="btn main" href="{croot}#c-video">{esc(T(lang, "Submit a video", "Video einreichen"))}</a></p>')
            write(f"{pfx2(lang)}community/video/index.html", page(lang, f"{t0} – M365.FM", intro, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=True))
            continue
        croot = f"{BASE}{pfx(lang)}/community/"; ttl = T(lang, "Creator videos", "Creator-Videos")
        for v in mine:
            u = f"{croot}video/{v['slug']}/"; au = f"{BASE}/community/u/{v['handle']}/"
            topics = [t for t in v.get("topics", []) if t in ENTS]
            tl = "".join(f'<a class="mb-tag" href="{BASE}/entity/{t}/">{esc(ENTS[t]["name"])}</a> ' for t in topics)
            player = f'<div style="position:relative;padding-top:56.25%"><iframe title="{esc(v["title"])}" src="https://www.youtube-nocookie.com/embed/{v["video_id"]}" loading="lazy" allowfullscreen style="position:absolute;inset:0;width:100%;height:100%;border:0"></iframe></div>'
            gs = [g for g in (v.get("guests") or []) if g.get("handle") != v["handle"]]
            guests_html = (f'<p class="mut">{esc(T(lang, "Guests", "Gäste"))}: ' + ", ".join(f'<a href="{croot}u/{g["handle"]}/">{esc(g["name"])}</a>' for g in gs) + "</p>") if gs else ""
            b = shell(lang, f'<p class="mut"><a href="{croot}video/">{esc(ttl)}</a></p><article><h1>{esc(v["title"])}</h1>'
                            f'<p class="mut">{esc(T(lang, "By", "Von"))} <a href="{croot}u/{v["handle"]}/" rel="author">{esc(v["name"])}</a> · {iso(v["published"])}</p>{guests_html}{player}'
                            f'{"".join("<p>" + esc(par) + "</p>" for par in (v.get("description") or "").split(chr(10) * 2) if par.strip())}'
                            f'{"<p class=mut>" + esc(T(lang, "The author disclosed the use of AI.", "Die Autorin bzw. der Autor hat den KI-Einsatz offengelegt.")) + "</p>" if v.get("ai") else ""}</article><p>{tl}</p>'
                            f'<p><a class="btn" href="https://youtu.be/{v["video_id"]}" rel="noopener">{esc(T(lang, "Watch on YouTube", "Auf YouTube ansehen"))}</a> <a href="{croot}video/feed.xml">RSS</a></p><section id="c-comments"></section>'
                            + (ctags(lang, "video%d" % v["id"]) if ctags else ""))
            ld = [{"@context": "https://schema.org", "@type": "VideoObject", "@id": u + "#video", "url": u, "name": v["title"], "description": (v.get("description") or "")[:500], "inLanguage": lang,
                   "uploadDate": iso(v["published"]), "thumbnailUrl": f"https://i.ytimg.com/vi/{v['video_id']}/hqdefault.jpg", "embedUrl": f"https://www.youtube.com/embed/{v['video_id']}",
                   "contentUrl": f"https://youtu.be/{v['video_id']}", "author": {"@type": "Person", "@id": au + "#person", "name": v["name"], "url": au}, **({"actor": [{"@type": "Person", "@id": f"{BASE}/community/u/{g['handle']}/#person", "name": g["name"], "url": f"{BASE}/community/u/{g['handle']}/"} for g in gs]} if gs else {}),
                   "publisher": {"@id": f"{BASE}/#org"}, "about": [{"@id": f"{BASE}/entity/{t}/#thing"} for t in topics]}]
            write(f"{pfx2(lang)}community/video/{v['slug']}/index.html", page(lang, f'{v["title"]} – {ttl} | M365.FM', (v.get("description") or "")[:155], u, b, None, ld, og_type="video.other", extra_head=LCSS, noindex=v["title"].startswith("[Test]")))
            if not v["title"].startswith("[Test]"): sitemap.append((u, iso(v["published"]), None))
        it = sorted(mine, key=lambda x: -x["published"]); ru = f"{croot}video/"
        lst = '<ul class="bl-list" style="padding:0;list-style:none">' + "".join(f'<li style="padding:.7em 0;border-bottom:1px solid var(--bd)"><a href="{croot}video/{v["slug"]}/"><b>{esc(v["title"])}</b></a> <span class="mut">· {esc(v["name"])} · {iso(v["published"])}</span></li>' for v in it) + "</ul>"
        b = shell(lang, f'<h1>{esc(ttl)}</h1><p class="mut">{esc(T(lang, "Videos from members of the Microsoft community on the m365 Show YouTube channel, reviewed by the editors.", "Videos von Mitgliedern der Microsoft-Community auf dem YouTube-Kanal m365 Show, von der Redaktion geprüft."))}</p>{lst}')
        write(f"{pfx2(lang)}community/video/index.html", page(lang, f'{ttl} – M365.FM', ttl, ru, b, None, [{"@context": "https://schema.org", "@type": "CollectionPage", "name": ttl, "url": ru}], og_type="website", extra_head=LCSS))
        write(f"{pfx2(lang)}community/video/feed.xml", rss("M365.FM " + ttl, ru, it, croot, lang))
        sitemap.append((ru, TODAY, None))
