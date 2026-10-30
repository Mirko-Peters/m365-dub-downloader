"""Eigene Seiten für gezogene Inhalte (YouTube-Videos, Beiträge aus Creator-Feeds): Titel, gezogene Beschreibung, Thumbnail, Quellenangabe,
optional eigener Creator-Text (per MCP). Google-Index erst mit eigenem Text (≥300 Zeichen), sonst noindex."""
import re
from datetime import datetime, timezone
from site_i18n import pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS, WT, wiki_render, WCSS
import site_notes as SNT

LANGS2 = ("en", "de")
PLAT = {"youtube": "YouTube", "github": "GitHub", "blog": "Blog", "podcast": "Podcast", "newsletter": "Newsletter", "mastodon": "Mastodon", "bluesky": "Bluesky",
        "spotify": "Spotify", "website": "Website", "other": "Web"}


def slug(t):
    s = re.sub(r"[^a-z0-9]+", "-", re.sub(r"[äöüß]", lambda m: {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}[m.group()], t.lower())).strip("-")
    return s[:60].strip("-") or "inhalt"


def path_of(it):
    return f"community/feed/{it['id']}-{slug(it['title'])}/"


def link(base, lang, it):
    return f"{base}{'/de' if lang == 'de' else ''}/{path_of(it)}"


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def build(g, items, api):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap = g["sitemap"]
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:48em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    for lang in LANGS2:
        croot = f"{BASE}{pfx(lang)}/community/"
        links_l = {i: [e["name"], f"{BASE}{pfx(lang) if lang == 'de' else ''}/entity/{i}/"] for i, e in ENTS.items()}
        for it in items:
            if not it.get("id"):
                continue
            u = link(BASE, lang, it); own = it.get("body") or ""; has_text = len(own) >= 300
            who = f'{croot}{"c" if it["type"] == "o" else "u"}/{it["handle"]}/'; plat = PLAT.get(it["kind"], "Web")
            topics = [t for t in it.get("topics", []) if t in ENTS]
            tl = "".join(f'<a class="mb-tag" href="{links_l[t][1]}">{esc(ENTS[t]["name"])}</a> ' for t in topics)
            body_html = wiki_render(own, links_l, WT.get(lang, WT["en"]))[0] if has_text else ""
            _kp, _fq, _fld = SNT.sections(it.get("keypoints"), it.get("faq"), lang) if has_text else ("", "", [])   # Kernpunkte und FAQ aus eigenen Feldern
            thumb = f'<p><a href="{esc(it["url"])}" rel="nofollow ugc noopener" target="_blank"><img src="{esc(it["thumb"])}" alt="{esc(it["title"])}" loading="lazy" style="max-width:100%;border-radius:.5em"></a></p>' if it.get("thumb") else ""
            b = shell(lang, f'{WCSS}<p class="mut"><a href="{who}">{esc(it["name"])}</a> · {esc(plat)} · {iso(it["published"])}</p><article class="wk-body"><h1>{esc(it["title"])}</h1>{thumb}'
                            f'{("<p>" + esc(it["summary"]) + "</p>") if it.get("summary") else ""}{_kp}{body_html}{_fq}{SNT.CSS if (_kp or _fq) else ""}</article>'
                            f'<p><a class="btn main" href="{esc(it["url"])}" rel="nofollow ugc noopener" target="_blank">{esc(T(lang, "View the original on", "Original ansehen auf"))} {esc(plat)} ↗</a></p><p>{tl}</p>'
                            f'<p class="mut">{esc(T(lang, "Title, description and thumbnail come from the creator’s public feed; the original stays with its author.", "Titel, Beschreibung und Vorschaubild stammen aus dem öffentlichen Feed des Creators; das Original bleibt beim Urheber."))}</p>')
            node = {"@type": "VideoObject" if it["kind"] == "youtube" else "Article", "@id": u + "#item", "name": it["title"], "headline": it["title"], "description": (it.get("summary") or it["title"])[:300],
                    "datePublished": iso(it["published"]), "inLanguage": lang, "isBasedOn": it["url"], "author": {"@type": "Person" if it["type"] == "u" else "Organization", "name": it["name"], "url": who},
                    "about": [{"@id": f"{BASE}/entity/{t}/#thing"} for t in topics]}
            if it["kind"] == "youtube":
                node["uploadDate"] = iso(it["published"]); node["thumbnailUrl"] = it.get("thumb") or ""; node["contentUrl"] = it["url"]
            if has_text:
                node["text"] = own[:5000]
            write(f"{pfx2(lang)}{path_of(it)}", page(lang, f'{it["title"]} – {it["name"]} | M365.FM', (it.get("summary") or it["title"])[:155], u, b, None, [{"@context": "https://schema.org", **node}] + _fld, og_type="article", extra_head=LCSS, noindex=not has_text))
            if has_text and lang == "en":
                sitemap.append((u, iso(it["published"]), None))
