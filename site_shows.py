"""Umgezogene Podcasts von Mitgliedern: /shows/ (Verzeichnis), /shows/<slug>/ (Show), /shows/<slug>/<folge>/ (Folge mit Player + Transkript).
Daten aus dem Worker (/api/show/export), importiert per RSS."""
import re
from datetime import datetime, timezone
from site_learn import esc
from site_podpage import san, plain


def d(ts):
    return datetime.fromtimestamp(ts or 0, timezone.utc).strftime("%Y-%m-%d")


def build(g, shows):
    BASE, write, page, header, footer_en, sitemap = g["BASE"], g["write"], g["page"], g["header"], g["footer_en"], g["sitemap"]
    shows = [s for s in shows if s.get("eps")]
    if not shows: return
    shell = lambda b: f'{header("en", "")}<main class="wrap" style="max-width:52em">{b}</main>{footer_en()}'
    root = f"{BASE}/shows/"

    def pub(rel, title, desc, body, ld=None, og="website", last=None):
        u = f"{root}{rel}"
        write(f"shows/{rel}index.html", page("en", f"{title} – M365.FM", desc[:300], u, shell(body), None, ld, og_type=og))
        sitemap.append((u, last or datetime.now(timezone.utc).strftime("%Y-%m-%d"), None))

    for s in shows:
        su = f"{root}{s['slug']}/"; who = f'<a href="{BASE}/community/u/{s["handle"]}/">{esc(s["name"])}</a>'
        eps = s["eps"]
        for k, e in enumerate(eps):
            eu = f"{su}{e['slug']}/"
            aud = f'<audio controls preload="none" style="width:100%" src="{esc(e["audio"])}"></audio>' if e.get("audio") else ""
            tr = e.get("transcript") or ""
            tx = f'<h2>Transcript</h2><details open><summary>Read the full transcript</summary><p style="white-space:pre-wrap;line-height:1.6">{esc(tr)}</p></details>' if len(tr) > 200 else ""
            nav = '<p style="display:flex;justify-content:space-between;gap:1em;margin-top:2em">' + (f'<a href="{su}{eps[k + 1]["slug"]}/">← {esc(eps[k + 1]["title"][:60])}</a>' if k + 1 < len(eps) else "<span></span>") + (f'<a href="{su}{eps[k - 1]["slug"]}/">{esc(eps[k - 1]["title"][:60])} →</a>' if k else "") + "</p>"
            body = (f'<article><p class="mut"><a href="{su}">{esc(s["title"])}</a> · {d(e["pub"])}{" · S" + str(e["season"]) if e.get("season") else ""}</p><h1>{esc(e["title"])}</h1>{aud}'
                    f'<div>{san(e.get("descr"))}</div><p class="mut">Host: {who}</p>{tx}</article>{nav}')
            ld = {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": e["title"], "url": eu, "datePublished": d(e["pub"]), "description": plain(e.get("descr"))[:500],
                  "partOfSeries": {"@type": "PodcastSeries", "name": s["title"], "url": su}, "inLanguage": s.get("lang") or "en", "author": {"@type": "Person", "name": s["name"], "url": f"{BASE}/community/u/{s['handle']}/"}}
            if e.get("audio"): ld["associatedMedia"] = {"@type": "AudioObject", "contentUrl": e["audio"]}
            if len(tr) > 200: ld["transcript"] = tr[:5000]
            pub(f"{s['slug']}/{e['slug']}/", e["title"], plain(e.get("descr")) or e["title"], body, ld, "article", d(e["pub"]))
        lst = "".join(f'<li style="margin:.8em 0"><a href="{su}{e["slug"]}/"><strong>{esc(e["title"])}</strong></a><br><span class="mut">{d(e["pub"])}</span></li>' for e in eps[:300])
        img = f'<img src="{esc(s["image"])}" alt="" width="160" height="160" style="float:right;margin:0 0 1em 1em;border-radius:8px" loading="lazy">' if s.get("image") else ""
        body = f'{img}<h1>{esc(s["title"])}</h1><p class="mut">Host: {who} · {len(eps)} episodes</p><p>{esc(plain(s.get("descr")))}</p><ul style="list-style:none;padding:0">{lst}</ul>'
        ld = {"@context": "https://schema.org", "@type": "PodcastSeries", "name": s["title"], "url": su, "description": plain(s.get("descr"))[:500], "inLanguage": s.get("lang") or "en", "author": {"@type": "Person", "name": s["name"], "url": f"{BASE}/community/u/{s['handle']}/"}}
        pub(f"{s['slug']}/", s["title"], plain(s.get("descr")) or s["title"], body, ld)
    LN = {"en": "English", "de": "Deutsch", "es": "Español", "fr": "Français", "it": "Italiano", "pt": "Português", "nl": "Nederlands", "pl": "Polski", "id": "Bahasa Indonesia", "ru": "Русский", "uk": "Українська", "ar": "العربية", "he": "עברית", "hi": "हिन्दी", "ja": "日本語", "ko": "한국어", "ml": "മലയാളം", "pa": "ਪੰਜਾਬੀ", "ta": "தமிழ்", "te": "తెలుగు"}
    item = lambda s: f'<li style="margin:.8em 0"><a href="{root}{s["slug"]}/"><strong>{esc(s["title"])}</strong></a> <span class="mut">· {esc(s["name"])} · {len(s["eps"])} episodes</span><br>{esc(plain(s.get("descr"))[:160])}</li>'
    li = "".join(f'<h2 lang="{k}">{LN.get(k, k)}</h2><ul style="list-style:none;padding:0">{"".join(item(s) for s in shows if (s.get("lang") or "en") == k)}</ul>' for k in LN if any((s.get("lang") or "en") == k for s in shows))
    pub("", "Podcasts from the M365.FM network", "Podcasts of the M365.FM network: shows that moved to M365.FM with all episodes and transcripts.", f'<h1>Podcasts in the network</h1>{li}')
