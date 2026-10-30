"""Englische Show-Seite (Nachbau von www.m365.fm / Podpage) unter /show/: Folgen, Seiten, Hosts, Sponsoren, Reviews, Gaeste (als Personen-Entitaeten).
Daten: data/podpage/*.json(.gz); Audio/Transkript aus data/en_episodes.json (fetch_en_episodes.py). Videos sind bewusst ausgeschlossen."""
import gzip, json, re, html as _h
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime
from site_learn import esc

D = Path(__file__).parent / "data"
PD = D / "podpage"
PER = 100
OK_TAGS = {"p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li", "h2", "h3", "h4", "blockquote", "a", "code", "pre", "hr", "table", "thead", "tbody", "tr", "th", "td", "img"}
SKIP = {"script", "style", "iframe", "form", "object", "embed"}


class _San(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.o = []; self.skip = 0

    def handle_starttag(self, t, a):
        if t in SKIP: self.skip += 1; return
        if self.skip or t not in OK_TAGS: return
        at = ""
        d = dict(a)
        if t == "a" and d.get("href", "").startswith(("http://", "https://", "/", "#", "mailto:")):
            at = f' href="{esc(d["href"])}" rel="noopener"' + ("" if d["href"].startswith(("/", "#")) else ' target="_blank"')
        if t == "img" and d.get("src", "").startswith("https://"):
            at = f' src="{esc(d["src"])}" alt="{esc(d.get("alt", ""))}" loading="lazy"'
        elif t == "img": return
        self.o.append(f"<{t}{at}>")

    def handle_endtag(self, t):
        if t in SKIP: self.skip = max(0, self.skip - 1); return
        if self.skip or t not in OK_TAGS or t in ("br", "hr", "img"): return
        self.o.append(f"</{t}>")

    def handle_data(self, d):
        if not self.skip: self.o.append(esc(d))


def san(s):
    p = _San(); p.feed(s or ""); return "".join(p.o)


def plain(s):
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def load(name):
    for f in (PD / f"{name}.json", PD / f"{name}.json.gz"):
        if f.exists():
            return json.loads((gzip.open(f, "rt", encoding="utf-8") if f.suffix == ".gz" else open(f, encoding="utf-8")).read())
    return []


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def day(s):
    return (s or "")[:10]


def make_guest_entities():
    """Gaeste -> Personen-Entitaeten (data/guest_entities.json); id = Podpage-Slug, bei Kollision mit Basis-Entitaeten Suffix -guest."""
    gs = load("guests")
    base = {e["id"] for e in json.loads((D / "entities.json").read_text("utf-8"))}
    out = []
    for g in gs:
        if g.get("hidden") in (True, "True"): continue
        i = g["slug"] + ("-guest" if g["slug"] in base else "")
        bio = plain(g.get("bio"))
        same = [g[k] for k in ("linkedin_link", "twitter_link", "youtube_link", "instagram_link", "facebook_link", "threads_link") if g.get(k)]
        out.append({"id": i, "type": "person", "name": g["name"], "aliases": [], "desc": {"en": bio, "de": bio}, "web": g.get("website") or "", "same_as": same, "job": g.get("title") or "", "rel": [],
                    "image": g.get("image_path") or "", "guest": True})
    (D / "guest_entities.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def build(g):
    BASE, write, page, header, footer_en, sitemap, TODAY = g["BASE"], g["write"], g["page"], g["header"], g["footer_en"], g["sitemap"], g["TODAY"]
    eps = [e for e in load("episodes") if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True")]
    if not eps: return
    eps.sort(key=lambda e: e["create_time"], reverse=True)
    pod = json.loads((PD / "podcast.json").read_text("utf-8")) if (PD / "podcast.json").exists() else {}
    hosts, links, revs, spons, files, cats = (load(n) for n in ("hosts", "links", "reviews", "sponsors", "downloadable_files", "categories"))
    pages = load("pages"); guests = [x for x in load("guests") if x.get("hidden") not in (True, "True")]
    enx = json.loads((D / "en_episodes.json").read_text("utf-8")) if (D / "en_episodes.json").exists() else {}
    ents = {e["id"]: e for e in json.loads((D / "guest_entities.json").read_text("utf-8"))} if (D / "guest_entities.json").exists() else {}
    gent = {gg["name"]: (gg["slug"] + ("-guest" if gg["slug"] not in {e["id"] for e in []} and gg["slug"] + "-guest" in ents else "")) for gg in guests}
    root = f"{BASE}/show/"; NAME = pod.get("name") or "M365.FM Podcast"
    nav = ('<nav class="mut" style="margin:0 0 1em;display:flex;gap:1em;flex-wrap:wrap">'
           + "".join(f'<a href="{root}{p}">{t}</a>' for p, t in (("", "Home"), ("episodes/", "Episodes"), *((("guests/", "Guests"),) if guests else ()), ("hosts/", "Hosts"), ("sponsors/", "Sponsors"), ("reviews/", "Reviews"), ("work-with-me/", "Work with me"), ("about/", "About")))
           + "</nav>")
    shell = lambda b: f'{header("en", "")}<main class="wrap" style="max-width:52em">{nav}{b}</main>{footer_en()}'

    def pub(rel, title, desc, body, ld=None, og="website", noindex=False, last=TODAY):
        u = f"{root}{rel}"
        write(f"show/{rel}index.html", page("en", (title if title == NAME else f"{title} – {NAME}"), desc[:300], u, shell(body), None, ld, og_type=og, noindex=noindex))
        if not noindex: sitemap.append((u, last, None))

    # Gaeste je Folge: Namensnennung in Titel/Show Notes
    gnames = sorted(((gg["name"], gg) for gg in guests if len(gg["name"]) > 5), key=lambda x: -len(x[0]))
    eg = {}
    for e in eps:
        hay = (e["name"] + " " + plain(e.get("show_notes"))).lower()
        eg[e["slug"]] = [gg for n, gg in gnames if n.lower() in hay][:5]
    ge = {}
    for e in eps:
        for gg in eg[e["slug"]]: ge.setdefault(gg["slug"], []).append(e)

    def tr_for(e):
        r = enx.get(norm(e["name"]))
        t = ""
        if r and r.get("transcript"):
            f = D / "en_transcripts" / f"{r['transcript']}.txt"
            if f.exists(): t = f.read_text("utf-8")
        return r, t

    def ep_url(e): return f"{root}episodes/{e['slug']}/"

    def card(e):
        s = plain(e.get("summary"))[:200]
        return f'<li style="margin:.9em 0"><a href="{ep_url(e)}"><strong>{esc(e["name"])}</strong></a><br><span class="mut">{day(e["create_time"])}{" · S" + str(e["season"]) if e.get("season") else ""}</span><br>{esc(s)}</li>'

    # Folgenseiten
    for k, e in enumerate(eps):
        r, tr = tr_for(e)
        prev_, next_ = (eps[k + 1] if k + 1 < len(eps) else None), (eps[k - 1] if k else None)
        aud = f'<audio controls preload="none" style="width:100%" src="{esc(r["audio"])}"></audio>' if r and r.get("audio") else ""
        ext = " · ".join(f'<a href="{esc(e[x])}" rel="noopener">{n}</a>' for x, n in (("episode_apple_url_path", "Apple Podcasts"), ("episode_spotify_url_path", "Spotify"), ("episode_youtube_music_url_path", "YouTube Music")) if (e.get(x) or "").startswith("http"))
        gl = "".join(f'<li><a href="{root}guests/{gg["slug"]}/">{esc(gg["name"])}</a></li>' for gg in eg[e["slug"]])
        tx = f'<h2>Transcript</h2><details open><summary>Read the full transcript</summary><p style="white-space:pre-wrap;line-height:1.6">{esc(tr)}</p></details>' if len(tr) > 200 else ""
        body = (f'<article><p class="mut">{day(e["create_time"])}{" · Season " + str(e["season"]) if e.get("season") else ""}</p><h1>{esc(e["name"])}</h1>{aud}'
                f'<div style="margin:1em 0"><strong>{esc(plain(e.get("summary")))}</strong></div><div class="pp-notes">{san(e.get("show_notes"))}</div>'
                + (f"<p>{ext}</p>" if ext else "") + (f"<h2>Guests</h2><ul>{gl}</ul>" if gl else "") + tx + "</article>"
                + '<p style="display:flex;justify-content:space-between;gap:1em;margin-top:2em">' + (f'<a href="{ep_url(prev_)}">← {esc(prev_["name"][:60])}</a>' if prev_ else "<span></span>") + (f'<a href="{ep_url(next_)}">{esc(next_["name"][:60])} →</a>' if next_ else "") + "</p>")
        ld = {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": e["name"], "url": ep_url(e), "datePublished": day(e["create_time"]),
              "description": plain(e.get("summary"))[:500], "partOfSeries": {"@type": "PodcastSeries", "name": NAME, "url": root}, "inLanguage": "en"}
        if e.get("season"): ld["partOfSeason"] = {"@type": "PodcastSeason", "seasonNumber": e["season"]}
        if r and r.get("audio"): ld["associatedMedia"] = {"@type": "AudioObject", "contentUrl": r["audio"]}
        if len(tr) > 200: ld["transcript"] = tr[:5000]
        pub(f"episodes/{e['slug']}/", e.get("meta_title") or e["name"], e.get("meta_description") or plain(e.get("summary")), body, ld, "article", last=day(e.get("update_time")) or TODAY)

    # Listen (paginiert)
    pages_n = (len(eps) + PER - 1) // PER
    for p in range(pages_n):
        part = eps[p * PER:(p + 1) * PER]
        pg = "".join(f'<a href="{root}episodes/{"" if q == 0 else f"page/{q + 1}/"}"{" style=font-weight:700" if q == p else ""}>{q + 1}</a> ' for q in range(pages_n))
        pub("episodes/" if p == 0 else f"episodes/page/{p + 1}/", "All episodes" + (f" – page {p + 1}" if p else ""), f"All {len(eps)} episodes of the {NAME}.", f'<h1>All episodes</h1><ul style="list-style:none;padding:0">{"".join(card(e) for e in part)}</ul><p>{pg}</p>', noindex=bool(p))

    # Gaeste
    gl = ""
    for gg in sorted(guests, key=lambda x: x["name"]):
        mine = ge.get(gg["slug"], [])
        eid = next((i for i in (gg["slug"] + "-guest", gg["slug"]) if i in ents), gg["slug"])
        ent = f'<p><a href="{BASE}/entity/{eid}/">Entity page</a></p>' if eid in ents else ""
        soc = " · ".join(f'<a href="{esc(gg[k])}" rel="noopener">{n}</a>' for k, n in (("website", "Website"), ("linkedin_link", "LinkedIn"), ("twitter_link", "X"), ("youtube_link", "YouTube")) if gg.get(k))
        img = f'<img src="{esc(gg["image_path"])}" alt="{esc(gg["name"])}" width="120" height="120" style="border-radius:50%;object-fit:cover;float:right;margin:0 0 1em 1em" loading="lazy">' if (gg.get("image_path") or "").startswith("http") else ""
        body = (f'<article>{img}<h1>{esc(gg["name"])}</h1><p class="mut">{esc(gg.get("title") or "")}</p><div>{san(gg.get("bio"))}</div><p>{soc}</p>{ent}'
                + (f'<h2>Episodes</h2><ul style="list-style:none;padding:0">{"".join(card(e) for e in mine)}</ul>' if mine else "") + "</article>")
        ld = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {"@type": "Person", "@id": f"{BASE}/entity/{eid}/#entity" if eid in ents else f"{root}guests/{gg['slug']}/#p", "name": gg["name"], "jobTitle": gg.get("title") or "",
              "sameAs": [gg[k] for k in ("linkedin_link", "twitter_link", "youtube_link", "website") if gg.get(k)]}}
        pub(f"guests/{gg['slug']}/", f"{gg['name']} – guest", plain(gg.get("bio")) or f"{gg['name']} on the {NAME}", body, ld, "profile")
        gl += f'<li style="margin:.4em 0"><a href="{root}guests/{gg["slug"]}/">{esc(gg["name"])}</a> <span class="mut">{esc(gg.get("title") or "")[:90]}</span></li>'
    if guests: pub("guests/", "Guests", f"{len(guests)} guests of the {NAME}.", f'<h1>Guests</h1><ul style="list-style:none;padding:0">{gl}</ul>')

    # Hosts, Sponsoren, Reviews, Downloads, Links
    hb = "".join(f'<section><h2>{esc(h["name"])}</h2><p class="mut">{esc(h.get("title") or "")}</p>{san(h.get("bio"))}</section>' for h in hosts)
    pub("hosts/", "Hosts", f"Hosts of the {NAME}.", f"<h1>Hosts</h1>{hb}")
    sb = "".join(f'<section><h2><a href="{esc(s["website"])}" rel="noopener sponsored">{esc(s["name"])}</a></h2>{san(s.get("description"))}</section>' for s in spons if s.get("hidden") not in (True, "True"))
    pub("sponsors/", "Sponsors", f"Sponsors of the {NAME}.", f"<h1>Sponsors</h1>{sb}")
    rv = "".join(f'<blockquote><strong>{"★" * int(r.get("rating") or 0)} {esc(r.get("title") or "")}</strong><br>{esc(r.get("review") or "")}<br><span class="mut">– {esc(r.get("author_name") or "")}</span></blockquote>' for r in revs if r.get("hidden") not in (True, "True"))
    pub("reviews/", "Listener reviews", f"What listeners say about the {NAME}.", f"<h1>Listener reviews</h1>{rv}")
    lk = "".join(f'<li><a href="{esc(l["url"])}" rel="noopener">{esc(l["name"])}</a></li>' for l in links if l.get("hidden") not in (True, "True") and str(l.get("url") or "").startswith("http"))
    if lk: pub("listen/", "Listen on every platform", f"Where to listen to the {NAME}.", f"<h1>Listen</h1><ul>{lk}</ul>")

    # Seiten (about, work-with-me, Themenhubs ...)
    SKIPP = {"episodes", "blog", "reviews", "podroll", "courses", "store", "videos", "guests", "people", "sponsors", "contact", "join", "leave_review", "rate", "guest_intake", "newsletter", "follow", "voicemail", "community-events", "legal", "hosts"}
    plist = []
    for p in pages:
        c = p.get("page_content")
        if p["slug"] in SKIPP or not c or c == "None": continue
        if p["slug"] == "support": p = {**p, "slug": "support"}
        t = p.get("page_title") or p.get("nav_label") or p["slug"].replace("-", " ").title()
        body = f"<article><h1>{esc(t)}</h1>{san(c)}</article>"
        pub(f"{p['slug']}/", p.get("meta_title") or t, p.get("meta_description") or plain(c)[:200], body, noindex=str(p.get("hide_from_search_engines")) == "True")
        plist.append((p["slug"], t))

    # Hub
    ct = "".join(f'<li><a href="{root}{s}/">{esc(t)}</a></li>' for s, t in plist if s not in ("about", "work-with-me", "support", "imprint-legal-notice", "sponsor-the-m365-show-podcast", "become-a-podcast-host"))
    hub = (f'<h1>{esc(NAME)}</h1><p>{esc(plain(pod.get("description")))[:600]}</p><h2>Latest episodes</h2><ul style="list-style:none;padding:0">{"".join(card(e) for e in eps[:20])}</ul>'
           f'<p><a href="{root}episodes/">All {len(eps)} episodes →</a></p>' + (f"<h2>Topics</h2><ul>{ct}</ul>" if ct else ""))
    ld = {"@context": "https://schema.org", "@type": "PodcastSeries", "name": NAME, "url": root, "description": plain(pod.get("description"))[:500], "inLanguage": "en", "webFeed": "https://www.spreaker.com/show/6704921/episodes/feed"}
    pub("", NAME, plain(pod.get("description")) or NAME, hub, ld)
    # Weiterleitungsliste fuer den spaeteren Domain-Umzug
    write("show/redirects.json", json.dumps({f"/episodes/{e['slug']}": f"/show/episodes/{e['slug']}/" for e in eps} | {f"/{s}": f"/show/{s}/" for s, _ in plist} | {f"/guests/{x['slug']}": f"/show/guests/{x['slug']}/" for x in guests}))
    print(f"podpage: {len(eps)} Folgen, {len(guests)} Gaeste, {len(plist)} Seiten")
