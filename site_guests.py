"""Gaeste-Boerse: oeffentliche Liste der Speaker (als Gast verfuegbar) und der Hosts (Show/Kanal/Event sucht Gaeste)."""
from site_i18n import COMM_LANGS, pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS

FM = {"podcast": "Podcast", "youtube": "YouTube", "event": "Event", "webinar": "Webinar", "article": "Blog"}


def fetch_listings(api):
    return (_fetch_json(f"{api}/api/guests/export") or {}).get("items", [])


def build(g, items, people):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY = g["sitemap"], g["TODAY"]
    pb = {p["handle"] for p in people}
    items = [i for i in items if i["handle"] in pb]
    for lang in COMM_LANGS:
        croot = f"{BASE}{pfx(lang)}/community/"; ttl = T(lang, "Guest exchange", "Gäste-Börse")
        def card(i):
            tp = "".join(f'<a class="mb-tag" href="{BASE}/entity/{t}/">{esc(ENTS[t]["name"])}</a> ' for t in i["topics"] if t in ENTS)
            nm = i["title"] or i["name"]
            return (f'<li style="padding:.7em 0;border-bottom:1px solid var(--bd);list-style:none"><b>{esc(nm)}</b> <span class="mut">· <a href="{croot}u/{i["handle"]}/">{esc(i["name"])}</a> · '
                    f'{esc(", ".join(FM.get(f, f) for f in i["formats"]))} · {esc(", ".join(i["langs"]))}</span>{("<br>" + esc(i["note"])) if i.get("note") else ""}<br>{tp}'
                    f'<br><a class="btn" href="{croot}?msg={i["handle"]}#c-messages">{esc(T(lang, "Send message", "Nachricht senden"))}</a></li>')
        sp = [i for i in items if i["kind"] == "speaker"]; ho = [i for i in items if i["kind"] == "host"]
        sec = lambda h, l: f'<h2>{esc(h)}</h2>' + ('<ul style="padding:0">' + "".join(card(i) for i in l) + "</ul>" if l else f'<p class="mut">{esc(T(lang, "Nothing here yet.", "Noch nichts da."))}</p>')
        intro = T(lang, "Podcasters, YouTubers and organizers find guests and speakers – and speakers find hosts. Matching works through shared topics.", "Podcaster, YouTuber und Veranstalter finden Gäste und Speaker – und Speaker finden Hosts. Zugeordnet wird über gemeinsame Themen.")
        b = (f'{header(lang, "")}<main class="wrap" style="max-width:48em"><h1>{esc(ttl)}</h1><p class="mut">{esc(intro)}</p>'
             f'<p><a class="btn main" href="{croot}#c-guests">{esc(T(lang, "Add your listing", "Eintrag anlegen"))}</a></p>'
             f'{sec(T(lang, "Available as guest or speaker", "Als Gast oder Speaker verfügbar"), sp)}{sec(T(lang, "Shows, channels and events looking for guests", "Shows, Kanäle und Events suchen Gäste"), ho)}</main>{footer(lang) if lang in LANGS else footer_en()}')
        u = f"{croot}guests/"; noidx = lang not in ("en", "de")
        write(f"{pfx2(lang)}community/guests/index.html", page(lang, f"{ttl} – M365.FM", intro, u, b, None, [{"@context": "https://schema.org", "@type": "CollectionPage", "name": ttl, "url": u}], og_type="website", extra_head=LCSS, noindex=noidx))
        if not noidx:
            sitemap.append((u, TODAY, None))
