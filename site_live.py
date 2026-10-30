"""M365 Show - die laufende Livestream-Show auf YouTube (data/live.json aus sync_live.py): Seite /live/ mit Live-Einbettung, geplanten Streams und Archiv,
dazu eine Seite je Stream (VideoObject + BroadcastEvent). Die Live-Einbettung (embed/live_stream?channel=) zeigt automatisch den laufenden Stream des Kanals."""
import html as _h
import json
import re
from pathlib import Path

from site_learn import esc, ENTS

D = Path(__file__).parent / "data"
T = {"en": dict(title="M365 Show – the live stream", h="M365 Show", kicker="Live on YouTube", lede="The M365 Show is a running live stream show: conversations and demos with Microsoft community experts about Microsoft 365, Copilot, Azure, the Power Platform and AI agents. Hosted by Mirko Peters, Microsoft MVP.",
                watch="Watch live", watchh="Live now or next stream", watchp="The player shows the current live stream of the channel; when nothing is live it shows the channel's latest stream or an offline message.", open="Open on YouTube", load="Load the live player (YouTube)",
                upc="Upcoming streams", noupc="No stream is scheduled right now – subscribe on YouTube to get notified.", past="Past streams", recent="Latest videos", livenow="Live now", on="Live on", dur="Duration", views="views", back="All streams",
                desc="Description", more="More from the M365 Show", sub="Subscribe", follow="Follow the show"),
     "de": dict(title="M365 Show – der Livestream", h="M365 Show", kicker="Live auf YouTube", lede="Die M365 Show ist eine laufende Livestream-Show: Gespräche und Demos mit Expertinnen und Experten der Microsoft-Community zu Microsoft 365, Copilot, Azure, der Power Platform und KI-Agenten. Moderiert von Mirko Peters, Microsoft MVP.",
                watch="Live ansehen", watchh="Jetzt live oder nächster Stream", watchp="Der Player zeigt den aktuellen Livestream des Kanals; läuft gerade nichts, erscheint der letzte Stream oder ein Offline-Hinweis.", open="Auf YouTube öffnen", load="Live-Player laden (YouTube)",
                upc="Kommende Streams", noupc="Aktuell ist kein Stream geplant – abonniere den Kanal auf YouTube, um benachrichtigt zu werden.", past="Vergangene Streams", recent="Neueste Videos", livenow="Jetzt live", on="Live am", dur="Dauer", views="Aufrufe", back="Alle Streams",
                desc="Beschreibung", more="Mehr von der M365 Show", sub="Abonnieren", follow="Der Show folgen")}
SOC = [("YouTube", "https://www.youtube.com/@m365show"), ("LinkedIn", "https://www.linkedin.com/company/m365-show/"), ("X", "https://x.com/m365show"), ("Instagram", "https://www.instagram.com/m365.show/"),
       ("Facebook", "https://www.facebook.com/m365show"), ("Bluesky", "https://bsky.app/profile/m365.show")]
LIVE_JS = ('<script>(function(){var b=document.getElementById("live-load");if(b)b.addEventListener("click",function(){var i=document.createElement("iframe");i.src=b.dataset.src;i.title=b.dataset.t;'
           'i.allow="accelerometer;autoplay;encrypted-media;picture-in-picture;fullscreen";i.allowFullscreen=true;i.style.cssText="width:100%;aspect-ratio:16/9;border:0;border-radius:.5rem";b.replaceWith(i)});'
           'var now=Date.now();document.querySelectorAll("li[data-start]").forEach(function(li){var s=Date.parse(li.dataset.start);if(!s)return;if(now>=s&&now<s+6*3600e3){li.classList.add("is-live");var t=li.querySelector(".live-badge");if(t)t.hidden=false}'
           'else if(now>=s+6*3600e3){li.hidden=true}})})();</script>')
CSS = ('<style>.lv-hero{display:grid;gap:1rem}.lv-play{width:100%;aspect-ratio:16/9;background:#000 center/cover no-repeat;border:0;border-radius:.5rem;color:#fff;font:600 1.1rem inherit;cursor:pointer;display:grid;place-items:center}'
       '.lv-list{list-style:none;padding:0}.lv-list li{display:flex;gap:1rem;align-items:flex-start;margin:1rem 0}.lv-list img{width:176px;aspect-ratio:16/9;object-fit:cover;border-radius:.5rem;flex:none}'
       '.live-badge{background:#c62828;color:#fff;border-radius:.3rem;padding:0 .5em;font-size:.8rem;margin-inline-start:.5em}.lv-list li.is-live{outline:2px solid #c62828;outline-offset:6px;border-radius:.5rem}'
       '@media(max-width:560px){.lv-list li{flex-direction:column}.lv-list img{width:100%}}</style>')


def plain(s):
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def short(s, n=180):
    s = plain(re.sub(r"https?://\S+", "", s or ""))
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(",;:- ") + "…"


def thumb(vid):
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


def slugify(t):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", re.sub(r"[^\x00-\x7f]", "", t.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")))).strip("-")[:60]


def build(g):
    f = D / "live.json"
    if not f.exists():
        return
    data = json.loads(f.read_text("utf-8"))
    streams = [s for s in data.get("streams", []) if s.get("id") and s.get("title")]
    if not streams:
        return
    BASE, write, page, header, footer, footer_en, LANGS, sitemap, TODAY = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"], g["sitemap"], g["TODAY"]
    cid = data.get("channel", "")
    for s in streams:
        s["slug"] = f'{s["id"].lower()}-{slugify(s["title"])}'.strip("-")[:72]
    upcoming = sorted([s for s in streams if s.get("live_status") in ("is_upcoming", "is_live")], key=lambda s: s.get("start") or "")
    pastl = [s for s in streams if s.get("live_status") in ("was_live", "post_live")]
    arch = pastl or [s for s in streams if s not in upcoming]
    ent = ENTS.get("m365show") or {}
    for lang in ("en", "de"):
        t = T[lang]; root = f"{BASE}{'/de' if lang == 'de' else ''}/live/"; shell = lambda b: f'{header(lang, "")}<main class="wrap" style="max-width:56em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
        desc = (ent.get("desc") or {}).get(lang) or t["lede"]
        embed = f"https://www.youtube-nocookie.com/embed/live_stream?channel={cid}&autoplay=1&rel=0"
        lead = upcoming[0] if upcoming else (arch[0] if arch else None)
        player = (f'<h2>{esc(t["watchh"])}</h2><div class="lv-hero"><button type="button" id="live-load" class="lv-play" data-src="{esc(embed)}" data-t="{esc(t["h"])}" style="background-image:linear-gradient(#0008,#0008),url({thumb(lead["id"])})" aria-label="{esc(t["load"])}">▶ {esc(t["load"])}</button>'
                  f'<p><a class="btn main" href="https://www.youtube.com/@m365show/live" rel="noopener">{esc(t["open"])} ↗</a> <a class="btn" href="https://www.youtube.com/@m365show?sub_confirmation=1" rel="noopener">{esc(t["sub"])}</a></p><p class="mut">{esc(t["watchp"])}</p></div>') if lead else ""

        def when(s):
            st = s.get("start") or s.get("published") or ""
            return st[:10] if not s.get("start") else f'<time datetime="{esc(s["start"])}">{esc(s["start"][:10])} {esc(s["start"][11:16])} UTC</time>'

        def row(s, up=False):
            lnk = f'{root}{s["slug"]}/'
            return (f'<li data-start="{esc(s.get("start", ""))}"><a href="{lnk}"><img src="{thumb(s["id"])}" alt="{esc(s["title"])}" width="176" height="99" loading="lazy" decoding="async"></a>'
                    f'<div><a href="{lnk}"><strong>{esc(s["title"])}</strong></a>{f"<span class=live-badge hidden>{esc(t["livenow"])}</span>" if up else ""}<br><span class="mut">{when(s)}</span><br>{esc(short(s.get("description")))}</div></li>')
        up_html = (f'<h2>{esc(t["upc"])}</h2><ul class="lv-list">' + "".join(row(s, True) for s in upcoming) + "</ul>") if upcoming else f'<h2>{esc(t["upc"])}</h2><p class="mut">{esc(t["noupc"])}</p>'
        ar_html = (f'<h2>{esc(t["past"] if pastl else t["recent"])}</h2><ul class="lv-list">' + "".join(row(s) for s in arch[:40]) + "</ul>") if arch else ""
        soc = " · ".join(f'<a href="{u}" rel="me noopener">{n}</a>' for n, u in SOC)
        body = (f'<p class="kicker">{esc(t["kicker"])}</p><h1>{esc(t["h"])}</h1><p class="lede">{esc(desc)}</p>{player}{up_html}{ar_html}<h2>{esc(t["follow"])}</h2><p>{soc}</p>{CSS}{LIVE_JS}')
        ld = [{"@context": "https://schema.org", "@type": "CreativeWorkSeries", "@id": f"{BASE}/live/#show", "name": "M365 Show", "url": root, "description": desc, "inLanguage": lang,
               "sameAs": [u for _, u in SOC] + ["https://m365.show/", f"{BASE}/entity/m365show/"], "creator": {"@id": f"{BASE}/entity/mirko-peters/#entity"}}]
        for s in upcoming:
            if s.get("start"):
                ld.append({"@context": "https://schema.org", "@type": "BroadcastEvent", "name": s["title"], "startDate": s["start"], "isLiveBroadcast": True, "url": f'{root}{s["slug"]}/',
                           "videoFormat": "HD", "publishedOn": {"@type": "BroadcastService", "name": "YouTube", "url": "https://www.youtube.com/@m365show"}})
        write(f"{'de/' if lang == 'de' else ''}live/index.html", page(lang, f'{t["title"]} | M365.FM', short(desc, 155), root, shell(body), None, ld, og_type="website"))
        sitemap.append((root, TODAY, None))
        for s in streams:
            u = f'{root}{s["slug"]}/'; d = (s.get("description") or "").strip(); dn = s.get("start") or s.get("published") or ""
            paras = "".join(f"<p>{esc(p)}</p>" for p in re.split(r"\n\s*\n", d)[:12] if p.strip())
            vid = {"@context": "https://schema.org", "@type": "VideoObject", "@id": u + "#video", "name": s["title"], "description": short(d, 500) or s["title"], "thumbnailUrl": [thumb(s["id"])],
                   "uploadDate": (s.get("published") or dn)[:10] or TODAY, "embedUrl": f"https://www.youtube-nocookie.com/embed/{s['id']}", "contentUrl": f"https://www.youtube.com/watch?v={s['id']}",
                   "inLanguage": lang, "isFamilyFriendly": True, "isPartOf": {"@id": f"{BASE}/live/#show"}, "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}}
            if s.get("live_status") in ("was_live", "post_live", "is_live", "is_upcoming") and (s.get("start") or s.get("published")):
                vid["publication"] = {"@type": "BroadcastEvent", "isLiveBroadcast": True, "startDate": s.get("start") or s["published"]}
            if s.get("duration"):
                m, sec = divmod(int(s["duration"]), 60); hh, m = divmod(m, 60); vid["duration"] = f"PT{hh}H{m}M{sec}S"
            sb = (f'<p class="mut"><a href="{root}">{esc(t["back"])}</a></p><article><h1>{esc(s["title"])}</h1><p class="mut">{when(s)}{" · " + str(s["views"]) + " " + t["views"] if s.get("views") else ""}</p>'
                  f'<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{s["id"]}?rel=0" title="{esc(s["title"])}" loading="lazy" allow="accelerometer;encrypted-media;picture-in-picture;fullscreen" allowfullscreen style="width:100%;aspect-ratio:16/9;border:0;border-radius:.5rem"></iframe></div>'
                  f'{("<h2>" + esc(t["desc"]) + "</h2>" + paras) if paras else ""}<p><a class="btn" href="https://www.youtube.com/watch?v={s["id"]}" rel="noopener">{esc(t["open"])} ↗</a></p></article>')
            write(f"{'de/' if lang == 'de' else ''}live/{s['slug']}/index.html", page(lang, f'{s["title"]} – M365 Show | M365.FM', short(d, 155) or s["title"], u, shell(sb), None, [vid], og_type="video.other"))
            sitemap.append((u, (s.get("published") or TODAY)[:10], None))
