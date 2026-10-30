import site_sidebar as SBR
"""Englische Show-Seite (Nachbau von www.m365.fm / Podpage) unter /show/: Folgen, Seiten, Hosts, Sponsoren, Reviews, Gaeste (als Personen-Entitaeten).
Daten: data/podpage/*.json(.gz); Audio/Transkript aus data/en_episodes.json (fetch_en_episodes.py). Videos sind bewusst ausgeschlossen."""
import site_notes as SNT
import site_media as MED
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
        same = [g[k] for k in ("linkedin_link", "twitter_link", "youtube_link", "instagram_link", "facebook_link", "threads_link", "bluesky_link", "mastodon_link", "tiktok_link", "twitch_link", "wikipedia_link", "imdb_link") if g.get(k)]
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
    navitems = (("", "Home"), ("episodes/", "Episodes"), *((("blog/", "Blog"),) if (PD / "blog_posts.json.gz").exists() else ()), *((("guests/", "Guests"),) if guests else ()), ("hosts/", "Hosts"), ("sponsors/", "Sponsors"), ("reviews/", "Reviews"), ("work-with-me/", "Work with me"), ("about/", "About"))
    nav = '<section class="sb-card sb-nav"><h2>M365.FM Show</h2><ul class="sb-navl">' + "".join(f'<li><a href="{root}{p}">{t}</a></li>' for p, t in navitems) + "</ul></section>"   # frueher zweite Menueleiste ueber dem Inhalt, jetzt Karte in der Sidebar
    shell = lambda b, side="": f'{header("en", "")}<link rel="stylesheet" href="{BASE}/assets/sbar.css"><main class="wrap shw"><div class="shmain">{b}</div>{side}</main>{footer_en()}'

    SBX = SBR.Index(); SHP = json.loads((D / "platforms.json").read_text("utf-8")).get("en", {}) if (D / "platforms.json").exists() else {}

    def pub(rel, title, desc, body, ld=None, og="website", noindex=False, last=TODAY, alts=None):
        u = f"{root}{rel}"
        side = SBR.render(SBX, BASE, root, title + " " + plain(body)[:8000], eps, SHP) if not noindex else SBR.render(SBX, BASE, root, "", [], {})   # die Karte "M365.FM Show" (Home, Episodes, Blog, Guests ...) ist entfernt; Navigation ueber den Header
        write(f"show/{rel}index.html", page("en", (title if title == NAME else f"{title} – {NAME}"), desc[:300], u, shell(body, side), alts, ld, xdefault=u, og_type=og, noindex=noindex))
        if not noindex: sitemap.append((u, last, None))

    # Gaeste je Folge: Namensnennung in Titel/Show Notes
    gnames = sorted(((gg["name"], gg) for gg in guests if len(gg["name"]) > 5), key=lambda x: -len(x[0]))
    eg = {}
    for e in eps:
        _n = SNT.get("en", title=e["name"])
        hay = (e["name"] + " " + plain(e.get("show_notes")) + " " + ((_n or {}).get("markup") or "") + " " + " ".join(p["name"] for p in (_n or {}).get("persons", []))).lower()
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

    def thumb_of(e, nrec=None):
        """Bild der Folge: Spreaker-Folgenbild (Podpage-Sicherung oder RSS), sonst YouTube-Vorschau aus dem Video-Link, sonst leer."""
        u = (e.get("image_path") or "")
        if u.startswith("https://") and "None" not in u:
            return u
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", e.get("video_link") or "")
        if m:
            return f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg"
        i = (nrec or {}).get("image") or ""
        return i if i.startswith("https://") else ""

    def short_desc(e, nrec=None, n=180):
        """Kurzbeschreibung: Zusammenfassung, sonst erster Absatz der Show Notes (Spreaker/Editor), sonst Meta-Beschreibung - an Wortgrenze gekuerzt."""
        t = plain(e.get("summary")) or plain(((nrec or {}).get("markup") or "").split("\n\n")[0].replace("*", "")) or plain(e.get("meta_description")) or plain(e.get("show_notes"))
        t = re.sub(r"\{\{(?:link|img)\|[^|{}]*\|([^{}]*)\}\}", r"\1", t)
        if len(t) <= n:
            return t
        return t[:n].rsplit(" ", 1)[0].rstrip(",;:- ") + "…"

    def img_tag(u, alt, size):
        return f'<img src="{esc(u)}" alt="{esc(alt)}" width="{size}" height="{size}" loading="lazy" decoding="async" style="width:{size}px;height:{size}px;object-fit:cover;border-radius:.5rem;flex:none">' if u else ""

    def card(e):
        nr = SNT.get("en", title=e["name"])
        s = short_desc(e, nr, 200); th = img_tag(thumb_of(e, nr), e["name"], 96)
        return (f'<li style="margin:.9em 0;display:flex;gap:1rem;align-items:flex-start">{th}<div><a href="{ep_url(e)}"><strong>{esc(e["name"])}</strong></a><br><span class="mut">{day(e["create_time"])}{" · S" + str(e["season"]) if e.get("season") else ""}</span><br>{esc(s)}</div></li>')

    # Blogposts (von www.m365.fm geholt, fetch_podpage_blog.py)
    import gzip as _gz, re as _re
    bposts = []
    _bf = PD / "blog_posts.json.gz"
    if _bf.exists():
        bposts = [p for p in json.loads(_gz.open(_bf, "rt", encoding="utf-8").read()) if p.get("title") and p.get("html")]
        bposts.sort(key=lambda p: p.get("iso") or "", reverse=True)
    eslug = {e["slug"] for e in eps}; bslug = {p["slug"] for p in bposts}
    def bp_url(p): return f"{root}blog/{p['slug']}/"
    def fixlinks(h):
        def rep(m):
            u = m.group(1); path = _re.sub(r"^https?://(www\.)?m365\.fm", "", u)
            if not path.startswith("/") or path.startswith("//"): return m.group(0)
            seg = path.strip("/").split("#")[0]
            if seg in eslug: return f'href="{root}episodes/{seg}/"'
            if seg.startswith("blog/") and seg[5:] in bslug: return f'href="{root}blog/{seg[5:]}/"'
            if seg == "blog": return f'href="{root}blog/"'
            return m.group(0)
        return _re.sub(r'href="([^"]+)"', rep, h)
    def bp_ep(p):
        for m in _re.finditer(r'href="([^"]+)"', p.get("html") or ""):
            seg = _re.sub(r"^https?://(www\.)?m365\.fm", "", m.group(1)).strip("/")
            if seg in eslug: return seg
        return None
    bp_by_ep = {}
    for p in bposts:
        k = bp_ep(p)
        if k: bp_by_ep.setdefault(k, []).append(p)
    def bday(p): return (p.get("iso") or "")[:10]

    # Folgenseiten
    # Lokalisierte Show-Seiten: Titel/Zusammenfassung (translate_show.py) und Show Notes der meistgehoerten Folgen (translate_notes.py)
    I18 = D / "podpage_i18n"; LG = g["LANGS"]
    TRL = {l: json.loads((I18 / f"{l}.json").read_text("utf-8")) for l in LG if (I18 / f"{l}.json").exists()}
    NTL = {l: json.loads((I18 / f"notes_{l}.json").read_text("utf-8")) for l in LG if (I18 / f"notes_{l}.json").exists()}
    loc_url = lambda l, rel: f"{BASE}/{l}/show/{rel}"
    elinks = json.loads((D / "episode_links.json").read_text("utf-8")) if (D / "episode_links.json").exists() else {}   # Plattform-Abgleich (sync_platforms.py)
    for k, e in enumerate(eps):
        r, tr = tr_for(e)
        nrec = SNT.get("en", title=e["name"])   # Spreaker-Show-Notes (oder im Editor bearbeitete Fassung) statt Podpage-Sicherung
        nkp, nnotes, nfaq, nld = SNT.blocks(nrec, "en")
        prev_, next_ = (eps[k + 1] if k + 1 < len(eps) else None), (eps[k - 1] if k else None)
        aud = f'<audio controls preload="none" style="width:100%" src="{esc(r["audio"])}"></audio>' if r and r.get("audio") else ""
        elk = elinks.get(f"{nrec['id']}:en", {}) if nrec else {}
        plat_links = [(n, (elk.get(pk) or e.get(fld) or "")) for n, pk, fld in (("Apple Podcasts", "apple", "episode_apple_url_path"), ("Spotify", "spotify", "episode_spotify_url_path"), ("YouTube", "youtube", "video_link"), ("YouTube Music", "youtube_music", "episode_youtube_music_url_path"), ("Deezer", "deezer", None))]
        plat_links = [(n, u) for n, u in plat_links if u.startswith("http")]   # frisch zugeordnete Links gehen vor der Podpage-Sicherung
        ext = " · ".join(f'<a href="{esc(u)}" rel="noopener">{n}</a>' for n, u in plat_links)
        hl = "".join(f'<a href="{BASE}/community/u/{h["slug"]}/">{esc(h["name"])}</a> ' for h in hosts if h.get("slug") == "mirko-peters")
        oa = (g.get("orig_alts") or {}).get(e["slug"]) or {}
        also = ('<h2>Also available in other languages</h2><ul>' + "".join(f'<li><a href="{u}" hreflang="{lg}">{esc(t)}</a> <span class="mut">({lg})</span></li>' for lg, (u, t) in sorted(oa.items())) + "</ul>") if oa else ""
        gl = "".join(f'<li><a href="{root}guests/{gg["slug"]}/">{esc(gg["name"])}</a></li>' for gg in eg[e["slug"]])
        tx = f'<h2>Transcript</h2><details open><summary>Read the full transcript</summary><p style="white-space:pre-wrap;line-height:1.6">{esc(tr)}</p></details>' if len(tr) > 200 else ""
        body = (f'<article><p class="mut">{day(e["create_time"])}{" · Season " + str(e["season"]) if e.get("season") else ""}</p><h1>{esc(e["name"])}</h1>{aud}'
                f'<div style="display:flex;gap:1rem;align-items:flex-start;margin:1em 0">{img_tag(thumb_of(e, nrec), e["name"], 160)}<div><strong>{esc(short_desc(e, nrec, 300))}</strong></div></div>{nkp}<div class="pp-notes">{(nnotes if nrec and nrec.get("markup") else san(e.get("show_notes")))}</div>{nfaq}{SNT.CSS if (nkp or nnotes or nfaq) else ""}'
                + (f"<p>{ext}</p>" if ext else "") + (f'<p class="mut">Host: {hl}</p>' if hl else "") + (f"<h2>Guests</h2><ul>{gl}</ul>" if gl else "") + also
                + (("<h2>Related articles</h2><ul>" + "".join(f'<li><a href="{bp_url(p)}">{esc(p["title"])}</a></li>' for p in bp_by_ep.get(e["slug"], [])[:6]) + "</ul>") if bp_by_ep.get(e["slug"]) else "") + tx + "</article>"
                + '<p style="display:flex;justify-content:space-between;gap:1em;margin-top:2em">' + (f'<a href="{ep_url(prev_)}">← {esc(prev_["name"][:60])}</a>' if prev_ else "<span></span>") + (f'<a href="{ep_url(next_)}">{esc(next_["name"][:60])} →</a>' if next_ else "") + "</p>")
        ld = {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": e["name"], "url": ep_url(e), "datePublished": day(e["create_time"]),
              "description": short_desc(e, nrec, 500), "partOfSeries": {"@type": "PodcastSeries", "name": NAME, "url": root}, "inLanguage": "en", **({"image": thumb_of(e, nrec)} if thumb_of(e, nrec) else {}), "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}}
        if e.get("season"): ld["partOfSeason"] = {"@type": "PodcastSeason", "seasonNumber": e["season"]}
        if r and r.get("audio"): ld["associatedMedia"] = {"@type": "AudioObject", "contentUrl": r["audio"]}
        if plat_links: ld["sameAs"] = [u for _, u in plat_links]
        if len(tr) > 200: ld["transcript"] = tr[:5000]
        alts = {"en": ep_url(e), **{l: loc_url(l, f"episodes/{e['slug']}/") for l in TRL if e["slug"] in TRL[l] and TRL[l][e["slug"]][0]}}
        pub(f"episodes/{e['slug']}/", e.get("meta_title") or e["name"], e.get("meta_description") or short_desc(e, nrec, 155), body, ([ld] + nld) if nld else ld, "article", last=day(e.get("update_time")) or TODAY, alts=alts if len(alts) > 1 else None)
        # lokalisierte Fassungen dieser Folge
        for l in TRL:
            tt = TRL[l].get(e["slug"])
            if not tt or not tt[0]: continue
            lt, ls = tt[0], tt[1] or short_desc(e, nrec, 300)
            ln = NTL.get(l, {}).get(e["slug"])
            lu = loc_url(l, f"episodes/{e['slug']}/")
            lbody = (f'<article><p class="mut">{day(e["create_time"])}</p><h1>{esc(lt)}</h1>{aud}'
                     f'<div style="display:flex;gap:1rem;align-items:flex-start;margin:1em 0">{img_tag(thumb_of(e, nrec), lt, 160)}<div><strong>{esc(ls)}</strong></div></div>'
                     + (f'<div class="pp-notes">{san(ln)}</div>' if ln else "") + (f"<p>{ext}</p>" if ext else "")
                     + f'<p class="mut"><a href="{ep_url(e)}" hreflang="en" lang="en">{esc(e["name"])}</a> (English)</p></article>')
            lald = {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": lt, "url": lu, "datePublished": day(e["create_time"]), "description": ls[:500],
                    "inLanguage": LG[l][1], "partOfSeries": {"@type": "PodcastSeries", "name": NAME, "url": root}, "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}}
            if r and r.get("audio"): lald["associatedMedia"] = {"@type": "AudioObject", "contentUrl": r["audio"]}
            write(f"{l}/show/episodes/{e['slug']}/index.html", g["page"](l, f"{lt} – {NAME}", ls[:300], lu, f'{g["header"](l, "")}<main class="wrap">{lbody}</main>{g["footer"](l)}', alts, [lald], xdefault=ep_url(e), og_type="article", og_of=ep_url(e)))
            sitemap.append((lu, day(e.get("update_time")) or TODAY, None))

    # Listen (paginiert)
    pages_n = (len(eps) + PER - 1) // PER
    for p in range(pages_n):
        part = eps[p * PER:(p + 1) * PER]
        pg = "".join(f'<a href="{root}episodes/{"" if q == 0 else f"page/{q + 1}/"}"{" style=font-weight:700" if q == p else ""}>{q + 1}</a> ' for q in range(pages_n))
        pub("episodes/" if p == 0 else f"episodes/page/{p + 1}/", "All episodes" + (f" – page {p + 1}" if p else ""), f"All {len(eps)} episodes of the {NAME}.", f'<h1>All episodes</h1><ul style="list-style:none;padding:0">{"".join(card(e) for e in part)}</ul><p>{pg}</p>', noindex=bool(p))

    # Lokalisierte Folgenlisten (paginiert) je Sprache mit uebersetzten Titeln/Zusammenfassungen
    for l in TRL:
        les = [e for e in eps if TRL[l].get(e["slug"]) and TRL[l][e["slug"]][0]]
        if not les: continue
        npg = (len(les) + PER - 1) // PER
        for p in range(npg):
            part = les[p * PER:(p + 1) * PER]
            lis = "".join(f'<li style="margin:.9em 0"><a href="{loc_url(l, "episodes/" + e["slug"] + "/")}"><strong>{esc(TRL[l][e["slug"]][0])}</strong></a><br><span class="mut">{day(e["create_time"])}</span><br>{esc((TRL[l][e["slug"]][1] or "")[:200])}</li>' for e in part)
            pg = "".join(f'<a href="{loc_url(l, "episodes/" + ("" if q == 0 else f"page/{q + 1}/"))}"{" style=font-weight:700" if q == p else ""}>{q + 1}</a> ' for q in range(npg))
            lrel = "episodes/" if p == 0 else f"episodes/page/{p + 1}/"
            lu = loc_url(l, lrel)
            ttl = f"{NAME} – {LG[l][0]}" + (f" ({p + 1})" if p else "")
            lal = {"en": f"{root}episodes/" if p == 0 else f"{root}episodes/page/{p + 1}/"}
            write(f"{l}/show/{lrel}index.html", g["page"](l, ttl, f"{NAME}: {len(les)} · {LG[l][0]}", lu, f'{g["header"](l, "")}<main class="wrap"><h1>{esc(ttl)}</h1><ul style="list-style:none;padding:0">{lis}</ul><p>{pg}</p></main>{g["footer"](l)}',
                                                         None, None, xdefault=lu if p else f"{root}episodes/", og_type="website", noindex=bool(p)))
            if not p: sitemap.append((lu, TODAY, None))

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

    # Blog
    ebyslug = {e["slug"]: e for e in eps}
    for p in bposts:
        ep = ebyslug.get(bp_ep(p) or "")
        _bi = thumb_of(ep, SNT.get("en", title=ep["name"])) if ep else ""   # Titelbild: Thumbnail der verlinkten Folge, sonst erzeugtes Bild
        _hero = (f'<figure style="margin:1em 0"><img src="{esc(_bi)}" alt="{esc("Cover: " + ep["name"])}" width="640" height="360" fetchpriority="high" decoding="async" style="width:100%;max-width:640px;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:.6em"></figure>' if _bi
                 else MED.hero_svg({"id": "blog-" + p["slug"], "name": p["title"], "type": "media"}, "Blog", "Titelbild: " + p["title"]))
        body = (f'<article><p class="mut">{bday(p)}</p><h1>{esc(p["title"])}</h1>{_hero}<div class="pp-notes">{fixlinks(san(p["html"]))}</div>'
                + (f'<p><strong>Listen to the episode:</strong> <a href="{ep_url(ep)}">{esc(ep["name"])}</a></p>' if ep else "") + "</article>"
                + f'<p><a href="{root}blog/">← All articles</a></p>')
        ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "url": bp_url(p), "mainEntityOfPage": bp_url(p), "datePublished": p.get("iso") or "", "dateModified": p.get("modified") or p.get("iso") or "",
              "description": p.get("desc") or "", "inLanguage": "en", "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}, "publisher": {"@type": "Organization", "name": NAME, "url": root}, "isPartOf": {"@type": "Blog", "name": f"{NAME} blog", "url": f"{root}blog/"}}
        if ep: ld["about"] = {"@type": "PodcastEpisode", "name": ep["name"], "url": ep_url(ep)}
        if _bi: ld["image"] = _bi
        faq = [q for q in (p.get("faq") or []) if q.get("name") and (q.get("acceptedAnswer") or {}).get("text")]
        lds = [ld] + ([{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq}] if faq else [])
        pub(f"blog/{p['slug']}/", p["title"], p.get("desc") or plain(p["html"])[:200], body, lds, "article", last=bday(p) or TODAY)
    BPER = 50; bn = (len(bposts) + BPER - 1) // BPER
    for q in range(bn):
        part = bposts[q * BPER:(q + 1) * BPER]
        pg = "".join(f'<a href="{root}blog/{"" if i == 0 else f"page/{i + 1}/"}"{" style=font-weight:700" if i == q else ""}>{i + 1}</a> ' for i in range(bn))
        li = "".join(f'<li style="margin:.8em 0"><a href="{bp_url(p)}"><strong>{esc(p["title"])}</strong></a><br><span class="mut">{bday(p)}</span><br>{esc((p.get("desc") or "")[:200])}</li>' for p in part)
        pub("blog/" if q == 0 else f"blog/page/{q + 1}/", "Blog" + (f" – page {q + 1}" if q else ""), f"{len(bposts)} articles on Microsoft 365, Azure, Power Platform and AI from the {NAME}.", f'<h1>Blog</h1><ul style="list-style:none;padding:0">{li}</ul><p>{pg}</p>', noindex=bool(q))

    # Hosts, Sponsoren, Reviews, Downloads, Links
    hb = "".join(f'<section><h2>{esc(h["name"])}</h2><p class="mut">{esc(h.get("title") or "")}</p>{san(h.get("bio"))}</section>' for h in hosts)
    pub("hosts/", "Hosts", f"Hosts of the {NAME}.", f"<h1>Hosts</h1>{hb}")
    sb = "".join(f'<section><h2><a href="{esc(s["website"])}" rel="noopener sponsored">{esc(s["name"])}</a></h2>{san(s.get("description"))}</section>' for s in spons if s.get("hidden") not in (True, "True"))
    pub("sponsors/", "Sponsors", f"Sponsors of the {NAME}.", f"<h1>Sponsors</h1>{sb}")
    xr = json.loads((D / "reviews_ext.json").read_text("utf-8")) if (D / "reviews_ext.json").exists() else [
        {"source": "Apple Podcasts" if r.get("source") == "A" else "Website", "country": r.get("country") or "", "author": r.get("author_name") or "Listener", "rating": int(r.get("rating") or 0), "title": r.get("title") or "", "body": r.get("review") or "", "date": (r.get("published") or "")[:10]}
        for r in revs if r.get("hidden") not in (True, "True")]
    xr = [r for r in xr if r["rating"]]
    dist = [sum(1 for r in xr if r["rating"] == k) for k in (1, 2, 3, 4, 5)]
    rv = "".join(f'<blockquote class="rv-ext"><strong>{"★" * r["rating"]}{"☆" * (5 - r["rating"])} {esc(r["title"])}</strong><br>{esc(r["body"])}<br><span class="mut">– {esc(r["author"])} · {esc(r["source"])}{" · " + esc(r["country"].upper()) if r.get("country") else ""} · {r["date"]}</span></blockquote>' for r in xr[:60])
    mount = (f'<div id="sh-reviews" data-show="en" data-ext-n="{len(xr)}" data-ext-sum="{sum(r["rating"] for r in xr)}" data-ext-dist="{",".join(map(str, dist))}" data-login="{BASE}/community/"><noscript><p>Enable JavaScript to rate and review.</p></noscript></div>'
             f'<link rel="stylesheet" href="{BASE}/assets/reviews.css"><script defer src="{BASE}/assets/reviews.js"></script>')
    pub("reviews/", "Listener reviews", f"What listeners say about the {NAME}: ratings and reviews from Apple Podcasts and the M365.FM community.", f'<h1>Listener reviews</h1>{mount}<h2>From Apple Podcasts and the web</h2>{rv}')
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
    shp = json.loads((D / "platforms.json").read_text("utf-8")).get("en", {}) if (D / "platforms.json").exists() else {}
    listen = " · ".join(f'<a href="{esc(shp[k])}" rel="noopener">{n}</a>' for k, n in (("apple_show", "Apple Podcasts"), ("spotify_show", "Spotify"), ("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart"), ("youtube_show", "YouTube"), ("youtube_music_show", "YouTube Music"), ("castbox_show", "Castbox"), ("podcastaddict_show", "Podcast Addict"), ("podchaser_show", "Podchaser")) if shp.get(k))
    hub = (f'<h1>{esc(NAME)}</h1><p>{esc(plain(pod.get("description")))[:600]}</p>' + (f'<p><strong>Listen on:</strong> {listen}</p>' if listen else "") + f'<h2>Latest episodes</h2><ul style="list-style:none;padding:0">{"".join(card(e) for e in eps[:20])}</ul>'
           f'<p><a href="{root}episodes/">All {len(eps)} episodes →</a></p>' + (f'<h2>Latest articles</h2><ul>{"".join(f"<li><a href=\"{bp_url(p)}\">{esc(p[chr(116)+chr(105)+chr(116)+chr(108)+chr(101)])}</a></li>" for p in bposts[:8])}</ul><p><a href="{root}blog/">All {len(bposts)} articles →</a></p>' if bposts else "") + (f"<h2>Topics</h2><ul>{ct}</ul>" if ct else ""))
    ld = {"@context": "https://schema.org", "@type": "PodcastSeries", "name": NAME, "url": root, "description": plain(pod.get("description"))[:500], "inLanguage": "en", "webFeed": "https://www.spreaker.com/show/6704921/episodes/feed", **({"sameAs": [shp[k] for k in ("apple_show", "spotify_show", "amazon_show", "deezer_show", "iheart_show", "youtube_show", "youtube_music_show", "castbox_show", "podcastaddict_show", "podchaser_show") if shp.get(k)]} if shp else {})}
    pub("", NAME, plain(pod.get("description")) or NAME, hub, ld)
    # Weiterleitungsliste fuer den Umzug (Podpage-Struktur: Folgen und Seiten direkt unter /<slug>/, Gaeste unter /guests/<slug>/, Blog /blog/<slug>/)
    from pathlib import Path as _P
    taken = {x.name for x in (_P(__file__).parent / "docs").iterdir()} if (_P(__file__).parent / "docs").exists() else set()
    taken |= {"show", "shows", "community", "entity", "glossary", "learn", "assets", "updates", "de", "en", "es", "fr", "it", "pt", "nl", "pl", "id", "ru", "uk", "ar", "he", "hi", "ja", "ko", "ml", "pa", "ta", "te"}
    rd, clash = {}, []
    def add(old, new):
        top = old.strip("/").split("/")[0]
        if "/" not in old.strip("/") and top in taken: clash.append(old); return
        rd[old] = new
    for e in eps: add(f"/{e['slug']}", f"/show/episodes/{e['slug']}/")
    for sl, _ in plist: add(f"/{sl}", f"/show/{sl}/")
    for x in guests: add(f"/guests/{x['slug']}", f"/show/guests/{x['slug']}/")
    for old, new in (("/episodes", "/show/episodes/"), ("/guests", "/show/guests/"), ("/hosts", "/show/hosts/"), ("/people", "/show/hosts/"), ("/sponsors", "/show/sponsors/"), ("/reviews", "/show/reviews/"), ("/podroll", "/show/listen/"), ("/videos", "/show/"), ("/blog", "/show/blog/" if bposts else "/show/")): rd.setdefault(old, new)
    for p in bposts: rd[f"/blog/{p['slug']}"] = f"/show/blog/{p['slug']}/"
    write("show/redirects.json", json.dumps(rd))
    write("show/redirect-conflicts.json", json.dumps(sorted(set(clash))))
    print(f"podpage: {len(eps)} Folgen, {len(guests)} Gaeste, {len(bposts)} Blogposts, {len(plist)} Seiten, {len(rd)} Weiterleitungen, Konflikte mit Plattform-Seiten: {sorted(set(clash))}")
