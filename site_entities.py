import re
"""Entitaetsdatenbank fuer das Microsoft-Oekosystem: Seiten, JSON-Exporte, Schema.org-Graph."""
from site_i18n import T
import site_updates as SU
import site_quotes as SQ   # Quotes an Personen-Entitaeten
import site_media as MED
import json
from site_i18n import COMM_LANGS, pfx, pfx2, overlay
from pathlib import Path
from site_learn import (ENTS, esc, ent_names, fetch_wiki, wiki_block, WCSS, LCSS, WT, GLOSS, GLOSS_JS, write_wk_js)

TL = {"product": ("Product", "Produkt"), "platform": ("Platform", "Plattform"), "concept": ("Concept", "Konzept"), "org": ("Organization", "Organisation"), "person": ("Person", "Person"),
      "cert": ("Certification", "Zertifizierung"), "event": ("Event", "Veranstaltung"), "media": ("Media", "Medium"), "category": ("Category", "Kategorie")}
FWD = {"instance_of": ("Is a", "Ist ein"), "part_of": ("Part of", "Teil von"), "developed_by": ("Developed by", "Entwickelt von"), "related_to": ("Related to", "Verwandt mit"), "requires": ("Requires", "Benötigt"),
       "covers": ("Covers", "Behandelt"), "created_by": ("Created by", "Erstellt von"), "organized_by": ("Organized by", "Veranstaltet von"), "similar_to": ("Similar to", "Ähnlich wie")}
INV = {"instance_of": ("Examples", "Beispiele"), "part_of": ("Includes", "Enthält"), "developed_by": ("Products and works", "Produkte und Werke"), "related_to": ("Related to", "Verwandt mit"),
       "requires": ("Required by", "Benötigt von"), "covers": ("Covered by", "Behandelt in"), "created_by": ("Created", "Erstellt"), "organized_by": ("Organizes", "Veranstaltet"), "similar_to": ("Similar to", "Ähnlich wie")}
S = {"en": dict(entities="Microsoft ecosystem entity database", intro="Products, platforms, concepts, certifications and organisations around Microsoft – with relationships, described by the community and published as Schema.org data.", new="Add a new topic", all="All", facts="Facts", website="Website", docs="Documentation", wikipedia="Wikipedia", wikidata="Wikidata", type="Type", aka="Also known as", experts="Experts and companies for this topic", noexperts="Nobody has listed this topic yet. Add it to your profile.", eps="Episodes about {t}", export="Data export", edit_e="Edit properties", glossary="Glossary", count="{n} entries", up="Last edited"),
     "de": dict(entities="Entitätsdatenbank zum Microsoft-Ökosystem", intro="Produkte, Plattformen, Konzepte, Zertifizierungen und Organisationen rund um Microsoft – mit Beziehungen, von der Community beschrieben und als Schema.org-Daten veröffentlicht.", new="Neues Thema anlegen", all="Alle", facts="Fakten", website="Webseite", docs="Dokumentation", wikipedia="Wikipedia", wikidata="Wikidata", type="Typ", aka="Auch bekannt als", experts="Experten und Firmen zu diesem Thema", noexperts="Dieses Thema hat noch niemand im Profil angegeben. Trag es in deinem Profil ein.", eps="Folgen zu {t}", export="Datenexport", edit_e="Eigenschaften bearbeiten", glossary="Glossar", count="{n} Einträge", up="Zuletzt bearbeitet")}


SPEAKERS = {}   # Entitaets-ID -> zusammengefuehrter Speaker (data/speakers.json) mit Events und Sessions
GENTEXT = {}   # Entitaet -> {en, de}: Ueberblickstexte aus data/entity_texts/part-*.json (aus Folgen und Fakten geschrieben, tools/entity_text_tasks.py)
for _f in sorted((Path(__file__).parent / "data" / "entity_texts").glob("part-*.json")) if (Path(__file__).parent / "data" / "entity_texts").exists() else []:
    try: GENTEXT.update(json.loads(_f.read_text("utf-8")))
    except Exception: pass
AUTHOR_EID = "mirko-peters"   # Entitaet des Seitenautors (E-E-A-T: Autor und Pruefer der Entitaetsseiten)
PERSON_LD = None   # wird vom Seitenbau gesetzt (generate_site.person_ld): ein Person-Knoten fuer den Autor
EVENTS = {}   # Event-Handle -> Event (fuer Verlinkung Entitaet -> Eventseite)
CLAIMS = {}   # eid -> Profil-Handle (uebernommene Entitaeten)
ORGPAGES = {}   # eid -> Firmen-Handle


def eurl(BASE, lang, i):
    return f"{BASE}{pfx(lang)}/entity/{i}/"


def eid_of(BASE, i):
    return f"{BASE}/entity/{i}/#entity"


def inverse_index():
    inv = {}
    for e in ENTS.values():
        for p, to in e.get("rel", []):
            if to in ENTS:
                inv.setdefault(to, []).append((p, e["id"]))
    return inv


def ent_ld(BASE, e, lang, glossary_set=None):
    """Schema.org-Knoten einer Entitaet (sprachneutrale @id)."""
    t = e["type"]; i = e["id"]; d = e["desc"].get(lang) or e["desc"].get("en") or e["desc"].get("de") or ""
    ref = lambda x: {"@id": eid_of(BASE, x)}
    rel = {}
    _inv = inverse_index()
    for p, to in e.get("rel", []):
        if to in ENTS:
            rel.setdefault(p, []).append(to)
    same = [u for u in (e.get("web"), e.get("wikipedia"), e.get("docs"), f"https://www.wikidata.org/wiki/{e['wikidata']}" if e.get("wikidata") else "") if u]
    same += [u for u in e.get("same_as", []) if u]
    if CLAIMS.get(i):
        same.append(f"{BASE}/community/u/{CLAIMS[i]}/")
    n = {"@type": {"product": "SoftwareApplication", "platform": "SoftwareApplication", "concept": "DefinedTerm", "category": "DefinedTerm", "org": "Organization", "person": "Person", "cert": "EducationalOccupationalCredential",
                   "event": "Event", "media": "PodcastSeries"}[t], "@id": eid_of(BASE, i), "name": e["name"], "url": eurl(BASE, "en", i), "description": d}
    if e.get("aliases"):
        n["alternateName"] = e["aliases"]
    if e.get("logo"):
        n["logo" if t == "org" else "image"] = e["logo"]
    if e.get("web") and t in ("org", "product", "platform", "media", "event"):
        pass
    if same:
        n["sameAs"] = same
    inv_map = [x for x in rel.get("related_to", [])] + [x for x in rel.get("similar_to", [])]
    if t in ("product", "platform"):
        n["applicationCategory"] = ", ".join(ENTS[c]["name"] for c in rel.get("instance_of", []) if ENTS[c]["type"] == "category") or "BusinessApplication"
        n["operatingSystem"] = "Web"
        if e.get("version"):
            n["softwareVersion"] = e["version"]
        if e.get("released"):
            n["datePublished"] = e["released"]
        if e.get("license"):
            n["isAccessibleForFree"] = e["license"] == "free"
            if e["license"] in ("free", "included"):
                n["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "description": "Free" if e["license"] == "free" else "Included in a Microsoft 365 licence"}
        n["@type"] = ["SoftwareApplication", "Product"]   # Software und Produkt zugleich
        if rel.get("developed_by"):
            n["brand"] = ref(rel["developed_by"][0])
        if rel.get("part_of"):
            n["isPartOf"] = [ref(x) for x in rel["part_of"]]
        if rel.get("developed_by"):
            n["publisher"] = [ref(x) for x in rel["developed_by"]]; n["creator"] = [ref(x) for x in rel["developed_by"]]
        if rel.get("requires"):
            n["softwareRequirements"] = [eurl(BASE, "en", x) for x in rel["requires"]]
        if rel.get("instance_of"):
            n["additionalType"] = [eurl(BASE, "en", x) for x in rel["instance_of"]]
        if rel.get("developed_by"):
            n["manufacturer"] = [ref(x) for x in rel["developed_by"]]
        if e.get("docs"):
            n["softwareHelp"] = {"@type": "CreativeWork", "url": e["docs"]}
        if rel.get("similar_to"):
            n["isSimilarTo"] = [ref(x) for x in rel["similar_to"]]
        if rel.get("related_to"):
            n["isRelatedTo"] = [ref(x) for x in rel["related_to"]]
        _parts = [x for q, x in _inv.get(i, []) if q == "part_of"]
        if _parts:
            n["hasPart"] = [ref(x) for x in _parts]
        if rel.get("instance_of"):
            n["category"] = [ENTS[c]["name"] for c in rel["instance_of"] if ENTS[c]["type"] == "category"]
        if e.get("aliases"):
            n["keywords"] = ", ".join(e["aliases"])
        if inv_map:
            n["mentions"] = [ref(x) for x in inv_map]
    elif t in ("concept", "category"):
        n["inDefinedTermSet"] = {"@type": "DefinedTermSet", "@id": f"{BASE}/glossary/#set", "name": "M365.FM Glossary"} if i in (glossary_set or ()) else {"@type": "DefinedTermSet", "@id": f"{BASE}/entity/#set", "name": "M365.FM Entities"}
        n["termCode"] = i
    elif t == "org":
        if rel.get("part_of"):
            n["parentOrganization"] = ref(rel["part_of"][0])
        _sub = [x for q, x in _inv.get(i, []) if q == "part_of" and ENTS[x]["type"] == "org"]
        if _sub:
            n["subOrganization"] = [ref(x) for x in _sub]
        _brands = [x for q, x in _inv.get(i, []) if q == "developed_by" and ENTS[x]["type"] in ("product", "platform")]
        if _brands:
            n["brand"] = [ref(x) for x in _brands]
        _ev = [x for q, x in _inv.get(i, []) if q == "organized_by"]
        if _ev:
            n["event"] = [ref(x) for x in _ev]
    elif t == "cert":
        if rel.get("developed_by"):
            n["recognizedBy"] = ref(rel["developed_by"][0])
        n["credentialCategory"] = "certification"
        if e.get("level"):
            n["educationalLevel"] = {"fundamentals": "Fundamentals", "associate": "Associate", "expert": "Expert", "specialty": "Specialty"}[e["level"]]
        if e.get("valid_months"):
            n["validFor"] = f"P{e['valid_months']}M"
        if e.get("exam"):
            n["identifier"] = e["exam"]
        if rel.get("covers"):
            n["about"] = [ref(x) for x in rel["covers"]]
            n["competencyRequired"] = [ENTS[x]["name"] for x in rel["covers"]]
    elif t == "event":
        n["eventAttendanceMode"] = "https://schema.org/OnlineEventAttendanceMode"; n["eventStatus"] = "https://schema.org/EventScheduled"
        n["location"] = {"@type": "VirtualLocation", "url": e.get("web") or eurl(BASE, "en", i)}
        if e.get("start"):
            n["startDate"] = e["start"]
        if e.get("end"):
            n["endDate"] = e["end"]
        if rel.get("organized_by"):
            n["organizer"] = [ref(x) for x in rel["organized_by"]]
    elif t == "media":
        if rel.get("created_by"):
            n["creator"] = [ref(x) for x in rel["created_by"]]; n["author"] = [ref(x) for x in rel["created_by"]]
    elif t == "person":
        if i == AUTHOR_EID and PERSON_LD:   # T4: Seitenautor = derselbe Knoten wie auf allen anderen Seiten (keine vier Fassungen derselben @id)
            base = PERSON_LD(); n.update({k: v for k, v in base.items() if k != "@context"}); n["mainEntityOfPage"] = eurl(BASE, "en", i)
        if e.get("job"):
            n["jobTitle"] = e["job"]
        if e.get("image") and str(e["image"]).startswith("https://"):
            n["image"] = e["image"]
        if e.get("company"):
            _org = next((x for x in ENTS.values() if x["type"] == "org" and x["name"].lower() == e["company"].lower()), None)
            n["worksFor"] = {"@id": eid_of(BASE, _org["id"])} if _org else {"@type": "Organization", "name": e["company"]}
        if SPEAKERS.get(e["id"], {}).get("events"):   # Auftritte als Speaker (Events der Plattform): mit Beginn und Online-Ort, sonst unvollstaendiges Event-Schema
            _ses = SPEAKERS[e["id"]].get("sessions") or []
            n["performerIn"] = []
            for x in SPEAKERS[e["id"]]["events"]:
                _st = sorted(s_["start"] for s_ in _ses if s_.get("event") == x["handle"] and s_.get("start"))
                _ev = {"@type": "Event", "name": x["title"], "url": f"{BASE}/community/events/{x['handle']}/", "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
                       "location": {"@type": "VirtualLocation", "url": f"{BASE}/community/events/{x['handle']}/"}}
                if _st: _ev["startDate"] = _st[0]
                n["performerIn"].append(_ev)
    return n


def claim_html(eid, lang):
    oh = ORGPAGES.get(eid)
    if oh and not CLAIMS.get(eid):
        return f'<p><a href="{BASE_}{pfx(lang)}/community/c/{oh}/">{T(lang, "Company profile on M365.FM", "Firmenprofil auf M365.FM")}</a></p>'
    h = CLAIMS.get(eid)
    if not h:
        return ""
    return f'<p><a href="{BASE_}{pfx(lang)}/community/u/{h}/">{T(lang, "Profile on M365.FM (maintained by the person)", "Profil auf M365.FM (gepflegt von der Person)")}</a></p>'


OLD = {"en": ("outdated", "Also show outdated entries (e.g. past events, replaced products)", "No longer current.", "Replaced by:"),
       "de": ("veraltet", "Auch veraltete Einträge anzeigen (z. B. vergangene Events, ersetzte Produkte)", "Nicht mehr aktuell.", "Ersetzt durch:")}


def is_old(e, today):
    """Veraltet: markiert/ersetzt oder Event, dessen Ende vorbei ist."""
    if e.get("outdated") or e.get("replaced_by"):
        return True
    end = (e.get("end") or e.get("start") or "")[:10]
    return e.get("type") == "event" and bool(end) and end < today


FAQ = {}   # eid -> [{q, a, lang}] aus /api/qa/export


MOD_FILE = Path(__file__).parent / "data" / "entity_mod.json"


def mod_dates(recs, TODAY):
    """Echtes Aenderungsdatum je Entitaet: Inhalts-Hash der Entitaet wird in data/entity_mod.json gefuehrt (vom Seitenbau committet);
    aendert sich der Inhalt, wandert das Datum auf heute - sonst bleibt es stehen (statt bei jedem Bau TODAY)."""
    import hashlib
    try:
        old = json.loads(MOD_FILE.read_text("utf-8")) if MOD_FILE.exists() else {}
    except Exception:
        old = {}
    out = {}
    for e in recs:
        h = hashlib.sha1(json.dumps({k: v for k, v in e.items() if k != "edited"}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
        o = old.get(e["id"]) or {}
        out[e["id"]] = {"h": h, "d": o["d"] if o.get("h") == h and o.get("d") else TODAY}
    try:
        MOD_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    except Exception:
        pass
    return {k: v["d"] for k, v in out.items()}


def _iso(ts):
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return ""


def topic_posts(posts_by_topic, eid, lang):
    """Artikel einer Entitaet: bei sehr allgemeinen Entitaeten (> 60 Treffer) nur die Beitraege, deren Hauptthema sie ist; Seitensprache zuerst, dann Englisch."""
    ps = posts_by_topic.get(eid) or []
    if len(ps) > 60:   # sehr allgemeine Entitaet: nur Beitraege, bei denen sie Haupt- oder Zweitthema ist
        ps = [p for p in ps if eid in (p.get("topics") or [])[:2]] or ps[:60]
    ps = [p for p in ps if p.get("lang") in (lang, "en")]
    return sorted(ps, key=lambda p: (p.get("lang") != lang, -(p.get("published") or 0)))


def articles_block(BASE, e, lang, posts, T_):
    if not posts:
        return "", []
    def purl(p):
        return f"{BASE}{pfx(p['lang']) if p['lang'] in ('de',) else ''}/community/u/{p['handle']}/blog/{p['slug']}/"
    def item(p):
        sm = (p.get("summary") or "")[:180]
        return (f'<li class="en-art"><a href="{purl(p)}"><b>{esc(p["title"])}</b></a><br><span class="mut"><time datetime="{_iso(p.get("published"))}">{_iso(p.get("published"))}</time> · {esc(p.get("name") or p["handle"])}</span>'
                + (f'<br>{esc(sm)}' if sm else "") + "</li>")
    head, rest = posts[:20], posts[20:100]
    h = f'<section class="en-arts"><h2>{esc(T_("Articles about {t}", "Artikel zu {t}").format(t=e["name"]))} <span class="mut">({len(posts)})</span></h2><ul class="en-artl">' + "".join(item(p) for p in head) + "</ul>"
    if rest:
        h += f'<details><summary>{esc(T_("{n} more articles", "{n} weitere Artikel").format(n=len(posts) - 20))}</summary><ul class="en-artl">' + "".join(f'<li><a href="{purl(p)}">{esc(p["title"])}</a> <span class="mut">· {_iso(p.get("published"))}</span></li>' for p in rest) + "</ul></details>"
    h += "</section>"
    return h, [purl(p) for p in head + rest]


def build(g, wiki_links, experts_by_ent, ep_find):
    global BASE_
    BASE_ = g["BASE"]
    posts_by_topic = g.get("posts_by_topic") or {}
    author_box = g.get("author_box")
    """g: ctx wie bei build_learn. experts_by_ent: eid -> [{kind,handle,name,headline,verified,level,endorsed}]; ep_find(entity)->[episodes]."""
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY, url_of = g["sitemap"], g["TODAY"], g["url_of"]
    api = g.get("api", "https://api-dub.m365.fm")
    gl_ids = {x["id"] for x in GLOSS}
    inv = inverse_index()
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:56em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'

    # --- Exporte ---
    recs = sorted(ENTS.values(), key=lambda e: e["id"])
    MOD = mod_dates(recs, TODAY)
    write("entities.json", json.dumps({"version": 1, "generated": TODAY, "license": "CC BY 4.0, M365.FM community", "entities": recs}, ensure_ascii=False, indent=1))
    write("entities.jsonld", json.dumps({"@context": "https://schema.org", "@graph": [ent_ld(BASE, e, "en", gl_ids) for e in recs]}, ensure_ascii=False))

    cfg_t = lambda lang: S[lang]
    for lang in COMM_LANGS:
        s = S[lang]; li = 1 if lang == "de" else 0
        stat = fetch_wiki(api, lang)
        write_wk_js(write, lang, wiki_links(lang))
        root = f"{BASE}{pfx(lang)}/entity/"
        rel = f"{pfx2(lang)}entity"
        # Index mit Typ-Filter
        def card(e):
            d = (e["desc"].get(lang) or e["desc"].get("en") or "")[:140]
            old = is_old(e, TODAY)
            return (f'<li class="en-i" data-t="{e["type"]}"{" data-old=1 hidden" if old else ""}><a href="{root}{e["id"]}/"><b>{esc(e["name"])}</b></a> <span class="mut">· {esc(TL[e["type"]][li])}{(" · " + OLD[lang][0]) if old else ""}</span><br><span class="mut">{esc(d)}</span></li>')
        counts = {}
        for e in recs:
            counts[e["type"]] = counts.get(e["type"], 0) + 1
        filt = f'<button type="button" class="en-f" data-f="" aria-pressed="true">{esc(s["all"])} ({len(recs)})</button>' + "".join(f'<button type="button" class="en-f" data-f="{k}" aria-pressed="false">{esc(TL[k][li])} ({counts[k]})</button>' for k in TL if k in counts)
        js = ('<script>(function(){var b=[].slice.call(document.querySelectorAll(".en-f")),l=[].slice.call(document.querySelectorAll(".en-i")),o=document.getElementById("en-old"),cur=b[0];function ap(){l.forEach(function(i){i.hidden=(!!cur.dataset.f&&i.dataset.t!==cur.dataset.f)||(!!i.dataset.old&&!(o&&o.checked))})}b.forEach(function(x){x.addEventListener("click",function(){b.forEach(function(y){y.setAttribute("aria-pressed",y===x?"true":"false")});cur=x;ap()})});if(o)o.addEventListener("change",ap)})()</script>')
        css = '<style>' + MED.CSS + '.en-ep{margin:1em 0}.en-ep h3{margin:.2em 0}.en-ep p{margin:.2em 0}.en-faq details,.wk-q{border:1px solid var(--bd);border-radius:.4em;padding:.5em .8em;margin:.4em 0;background:var(--card)}.en-faq summary{cursor:pointer;font-weight:600}.wk-a{margin:.4em 0 .4em 1em}.en-old{border:1px solid var(--bd);border-left:4px solid #b45309;background:var(--card);padding:.6em .9em;border-radius:.4em}.en-f{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.35em .9em;margin:.2em .3em .2em 0;background:var(--card);color:var(--fg);min-height:2.5rem}.en-f[aria-pressed=true]{background:var(--ac);color:var(--onac);border-color:var(--ac)}.en-list{list-style:none;padding:0}.en-list li{padding:.55em 0;border-bottom:1px solid var(--bd)}.en-list li[hidden]{display:none}.en-facts{border-collapse:collapse;width:100%}.en-facts th{text-align:start;padding:.4em .8em .4em 0;vertical-align:top;white-space:nowrap}.en-facts td{padding:.4em 0}.en-rel h3{margin:.9em 0 .2em;font-size:1rem}.en-rel ul{margin:.2em 0;padding-inline-start:1.3em}.en-artl{list-style:none;padding:0}.en-artl li{padding:.5em 0;border-bottom:1px solid var(--bd)}.en-arts details{margin:.6em 0}.en-arts summary{cursor:pointer}.en-upd{font-size:.9em}.en-kp{border:1px solid var(--bd);border-inline-start:4px solid var(--ac,#0a5);border-radius:.4em;padding:.4em 1em;margin:1em 0}.en-kp h2{margin:.3em 0;font-size:1.1rem}.en-kp ul{margin:.3em 0;padding-inline-start:1.2em}.en-src ul{padding-inline-start:1.2em}.en-src li{margin:.2em 0;overflow-wrap:anywhere}</style>'
        newbtn = f'<div id="en-new" data-lang="{lang}"></div>'
        body = shell(lang, f'<h1>{esc(s["entities"])}</h1><p class="mut">{esc(s["intro"])}</p><p>{esc(s["count"].format(n=len(recs)))} · <a href="{BASE}/entities.json">{esc(s["export"])} (JSON)</a> · <a href="{BASE}/entities.jsonld">JSON-LD</a></p>{newbtn}<p><label><input type="checkbox" id="en-old"> {esc(OLD[lang][1])}</label></p><div role="group" aria-label="{esc(s["type"])}">{filt}</div><ul class="en-list">{"".join(card(e) for e in sorted(recs, key=lambda x: x["name"].lower()))}</ul>{js}'
                      f'<script>window.M365E={{api:"{api}",lang:"{lang}",base:"{BASE}",s:{json.dumps({k: s[k] for k in ("new",)}, ensure_ascii=False)}}}</script><script defer src="{BASE}/assets/entity.js"></script>')
        _terms = [e for e in recs if e["type"] in ("concept", "category")]
        ld = [{"@context": "https://schema.org", "@type": "DefinedTermSet", "@id": f"{BASE}/entity/#set", "name": "M365.FM Entities", "url": root, "inLanguage": lang, "description": s["intro"],
               "hasDefinedTerm": [{"@id": eid_of(BASE, e["id"])} for e in _terms]},
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": s["entities"], "url": root, "description": s["intro"], "mainEntity": {"@type": "ItemList", "numberOfItems": len(recs), "itemListElement":
               [{"@type": "ListItem", "position": i + 1, "item": {"@id": eid_of(BASE, e["id"])}} for i, e in enumerate(sorted(recs, key=lambda x: x["name"].lower()))]}}]
        (write if lang in ("en", "de") else (g.get("write_r2") or write))(f"{rel}/index.html", page(lang, f'{s["entities"]} – M365.FM', s["intro"], root, body, None, ld, og_type="website", extra_head=LCSS + WCSS + css, noindex=lang not in ("en", "de")))
        if lang in ("en", "de"): sitemap.append((root, TODAY, None))

        # Einzelseiten
        for e in recs:
            u = f"{root}{e['id']}/"; d = e["desc"].get(lang) or e["desc"].get("en") or e["desc"].get("de") or ""
            groups = {}
            for p, to in e.get("rel", []):
                if to in ENTS:
                    groups.setdefault(FWD[p][li], []).append(to)
            for p, frm in inv.get(e["id"], []):
                lab = INV[p][li]
                if frm not in groups.get(lab, []) and not (p in ("related_to", "similar_to") and frm in groups.get(FWD[p][li], [])):
                    groups.setdefault(lab, []).append(frm)
            rb = "".join(f'<h3>{esc(k)}</h3><ul>' + "".join(f'<li><a href="{root}{x}/">{esc(ENTS[x]["name"])}</a> <span class="mut">· {esc(TL[ENTS[x]["type"]][li])}</span></li>' for x in dict.fromkeys(v)) + "</ul>" for k, v in groups.items())
            facts = [(s["type"], esc(TL[e["type"]][li]))]
            if e.get("aliases"):
                facts.append((s["aka"], esc(", ".join(e["aliases"]))))
            for k, key in (("website", "web"), ("docs", "docs"), ("wikipedia", "wikipedia")):
                if e.get(key):
                    facts.append((s[k], f'<a href="{esc(e[key])}" rel="noopener">{esc(e[key].replace("https://", "").rstrip("/"))}</a>'))
            LIC = {"free": ("free", "kostenlos"), "included": ("included in Microsoft 365", "in Microsoft 365 enthalten"), "addon": ("add-on", "Add-on"), "paid": ("paid", "kostenpflichtig")}
            for lab_en, lab_de, val in (("Version", "Version", e.get("version")), ("Released", "Veröffentlicht", e.get("released")), ("Licence", "Lizenz", (T(lang, *LIC[e["license"]]) if True else "") if e.get("license") in LIC else ""),
                                        ("Level", "Stufe", (e.get("level") or "").capitalize()), ("Exam code", "Prüfungscode", e.get("exam")), ("Valid for", "Gültig für", (f"{e['valid_months']} " + (T(lang, "months", "Monate"))) if e.get("valid_months") else "")):
                if val:
                    facts.append((T(lang, lab_en, lab_de), esc(str(val))))
            if e.get("wikidata"):
                facts.append((s["wikidata"], f'<a href="https://www.wikidata.org/wiki/{e["wikidata"]}" rel="noopener">{e["wikidata"]}</a>'))
            if e.get("start"):
                facts.append((T(lang, "Date", "Datum"), esc(e["start"] + (" – " + e["end"] if e.get("end") else ""))))
            ft = '<table class="en-facts"><tbody>' + "".join(f'<tr><th scope="row">{esc(a)}</th><td>{b}</td></tr>' for a, b in facts) + "</tbody></table>"
            evl = ""
            if e["id"] in EVENTS:
                ev_ = EVENTS[e["id"]]; evl = f'<p><a class="btn" href="{BASE}{pfx(lang)}/community/events/{ev_["handle"]}/">{T(lang, "Go to the event", "Zum Event")}: {esc(ev_["title"])}</a></p>'
                _ses = ev_.get("sessions", []); _spk = {}
                for _se in _ses:
                    for _x in _se.get("speakers", []):
                        _spk.setdefault(_x["n"], _x)
                _pre = f'{BASE}{pfx(lang)}/community'
                def _sl(x):
                    return f'<a href="{_pre}/u/{x["h"]}/">{esc(x["n"])}</a>' if x.get("h") else esc(x["n"])
                if _ses:
                    evl += f'<h2>{T(lang, "Sessions", "Sessions")} ({len(_ses)})</h2><ul>' + "".join(f'<li>{esc(_se["title"])}' + (f' <span class="mut">· {", ".join(_sl(x) for x in _se.get("speakers", []))}</span>' if _se.get("speakers") else "") + "</li>" for _se in _ses[:150]) + "</ul>"
                if _spk:
                    evl += f'<h2>{T(lang, "Speakers", "Speaker")} ({len(_spk)})</h2><p>' + ", ".join(_sl(x) for x in sorted(_spk.values(), key=lambda a: a["n"].lower())[:200]) + "</p>"
            _spk = SPEAKERS.get(e["id"])
            if _spk and _spk.get("sessions"):   # Speaker-Profil: Auftritte und Sessions (aus den zusammengefuehrten Programmen)
                _p3 = f'{BASE}{pfx(lang)}/community'
                _evt = {x["handle"]: x["title"] for x in _spk.get("events", [])}
                evl += (f'<h2>{T(lang, "Speaker at", "Speaker bei")}</h2><p>' + ", ".join(f'<a href="{_p3}/events/{h}/">{esc(t)}</a>' for h, t in _evt.items()) + "</p>"
                        + f'<h2>{T(lang, "Sessions", "Sessions")} ({len(_spk["sessions"])})</h2><ul>' + "".join(
                            f'<li><a href="{_p3}/events/{s_["event"]}/">{esc(s_["title"])}</a> <span class="mut">· {esc(_evt.get(s_["event"], ""))} · {esc(s_["start"][:10])}</span></li>' for s_ in _spk["sessions"]) + "</ul>")
            _evu = {_ev["handle"]: _ev for _ev in EVENTS.values()}.values()   # EVENTS enthaelt ein Event unter mehreren Schluesseln (Handle und Themen): je Event nur einmal
            _hit, _seen = [], set()
            for _ev in _evu:
                for _se in _ev.get("sessions", []):
                    if e["id"] in (_se.get("topics") or []) and (_ev["handle"], _se.get("id", _se.get("title"))) not in _seen:
                        _seen.add((_ev["handle"], _se.get("id", _se.get("title")))); _hit.append((_ev, _se))
            if _hit and e["id"] not in EVENTS:   # Sessions zu diesem Thema (Gegenrichtung zu den Themen an der Session)
                _p2 = f'{BASE}{pfx(lang)}/community'
                _spl = lambda x: f'<a href="{_p2}/u/{x["h"]}/">{esc(x["n"])}</a>' if x.get("h") else esc(x["n"])
                evl += f'<h2>{T(lang, "Sessions on this topic", "Sessions zu diesem Thema")} ({len(_hit)})</h2><ul>' + "".join(
                    f'<li><a href="{_p2}/events/{_ev["handle"]}/">{esc(_se["title"])}</a> <span class="mut">· {", ".join(_spl(x) for x in _se.get("speakers", []))} · {esc(_ev["title"])}</span></li>' for _ev, _se in _hit[:30]) + "</ul>"
            if not e["desc"].get(lang if lang in ("en", "de") else "en"):
                evl += f'<p class="mut"><a href="#en-edit">{T(lang, "This short description is not yet available in your language – feel free to add it.", "Diese Kurzbeschreibung gibt es noch nicht in deiner Sprache – gern ergänzen.")}</a></p>'
            gloss = f'<p class="mut"><a href="{BASE}/{pfx2(lang)}glossary/">{esc(s["glossary"])}</a></p>' if e["id"] in gl_ids else ""
            eps = ep_find(e, lang)   # Folgen in der Sprache der Seite (englisch: Hauptshow), sonst keine
            _epu = lambda x: x.get("url") or url_of(x)
            ept = s.get("eps") or S["en"]["eps"]
            _yt = g.get("yt_of") or (lambda x: "")   # T27: YouTube-Video der Folge
            _ytl = lambda x: (f' · <a href="https://www.youtube.com/watch?v={esc(_yt(x))}" rel="noopener">{esc(T(lang, "Video on YouTube", "Video auf YouTube"))}</a>') if _yt(x) else ""
            eb = (f'<h2>{esc(ept.format(t=e["name"]))}</h2>' + "".join(
                f'<article class="en-ep"><h3><a href="{_epu(x)}">{esc(g["anchor_title"](x["e"]["title"]))}</a></h3><p class="mut">{esc(x.get("date", ""))}{_ytl(x)}</p><p>{esc(g["ep_sum"](x))}</p></article>' for x in eps)) if eps else ""
            tlab = TL[e["type"]][li]
            alt_h = T(lang, f"Title graphic: {e['name']} ({tlab})", f"Titelbild: {e['name']} ({tlab})")
            hero = MED.hero_svg(e, tlab, alt_h)
            rel_items = [(k, f"{root}{x}/", ENTS[x]["name"]) for k, v in groups.items() for x in dict.fromkeys(v)]
            relmap = MED.relation_svg(e, rel_items, T(lang, f"Relationship map of {e['name']}: linked topics", f"Beziehungskarte {e['name']}: verknüpfte Themen"))
            relx = ""
            if lang in ("en", "de") and rel_items:   # verknuepfte Themen mit ihrer Kurzbeschreibung: echter Inhalt aus den vorhandenen Entitaeten
                _seen, _li = set(), []
                for _k, _u, _n in rel_items:
                    _id = _u.rstrip("/").rsplit("/", 1)[-1]
                    if _id in _seen or _id not in ENTS: continue
                    _seen.add(_id); _dd = ENTS[_id]["desc"].get(lang) or ENTS[_id]["desc"].get("en") or ""
                    _li.append(f'<li><a href="{_u}"><b>{esc(_n)}</b></a> <span class="mut">· {esc(_k)} · {esc(TL[ENTS[_id]["type"]][li])}</span>' + (f'<br>{esc(_dd)}' if _dd else "") + "</li>")
                    if len(_li) >= 14: break
                relx = f'<h2>{T(lang, "Related topics in brief", "Verwandte Themen kurz erklärt")}</h2><ul class="en-relx">' + "".join(_li) + "</ul>" if _li else ""
            tline = MED.timeline_svg([(x.get("date", ""), g["anchor_title"](x["e"]["title"]), _epu(x)) for x in eps], T(lang, f"Timeline of episodes about {e['name']}", f"Zeitleiste der Folgen zu {e['name']}"))
            ex = experts_by_ent.get(e["id"], [])
            ehtml = ""
            if ex:
                ehtml = "<ul>" + "".join(f'<li><a href="{BASE}{pfx(lang)}/community/{"u" if x["kind"] == "u" else "c"}/{x["handle"]}/">{esc(x["name"])}</a>{" ✔" if x.get("verified") else ""}<span class="mut"> · {esc(x.get("headline", "")[:80])}</span></li>' for x in ex[:12]) + "</ul>"
            elif e["type"] in ("product", "platform", "concept", "category"):
                ehtml = f'<p class="mut">{esc(s["noexperts"])}</p>'
            if lang in ("en", "de") and rel_items:   # Experten zu verwandten Themen (ein Schritt im Entitaetsgraphen), mit Angabe, ueber welches Thema sie passen
                _seen, _rx = {x["handle"] for x in ex}, []
                for _k, _u, _n in rel_items:
                    for x in experts_by_ent.get(_u.rstrip("/").rsplit("/", 1)[-1], []):
                        if x["kind"] == "u" and x["handle"] not in _seen:
                            _seen.add(x["handle"]); _rx.append((x, _n))
                    if len(_rx) >= 8: break
                if _rx:
                    ehtml += f'<h3>{T(lang, "Experts on related topics", "Experten zu verwandten Themen")}</h3><ul>' + "".join(
                        f'<li><a href="{BASE}{pfx(lang)}/community/u/{x["handle"]}/">{esc(x["name"])}</a>{" ✔" if x.get("verified") else ""}<span class="mut"> · {T(lang, "via", "über")} {esc(n)}</span></li>' for x, n in _rx[:8]) + "</ul>"
            oldbanner = ""
            if is_old(e, TODAY):
                rp = ENTS.get(e.get("replaced_by") or "")
                oldbanner = f'<p class="en-old" role="note"><b>{esc(OLD[lang][2])}</b>' + (f' {esc(OLD[lang][3])} <a href="{root}{rp["id"]}/">{esc(rp["name"])}</a>.' if rp else "") + "</p>"
            _lt = (e.get("long") or {}).get(lang) or (e.get("long") or {}).get("en") or (e.get("long") or {}).get("de") or (EVENTS[e["id"]].get("about") if e["id"] in EVENTS else "") or ""
            _gen = ""
            if not _lt.strip() and e["id"] in GENTEXT:   # Ueberblick aus den Folgen der Show und den Fakten der Seite (data/entity_texts), solange es keinen redaktionellen Langtext gibt
                _lt = GENTEXT[e["id"]].get(lang) or GENTEXT[e["id"]].get("en") or ""
                _gen = f'<p class="mut" style="font-size:.85em">{esc(T(lang, "Overview compiled with AI from M365.FM episodes and the facts on this page. You can improve it with the edit button below.", "Überblick, mit KI aus M365.FM-Folgen und den Fakten dieser Seite zusammengestellt. Du kannst ihn unten über „Bearbeiten“ verbessern."))}</p>' if _lt.strip() else ""
            longbox = ("<h2>" + (T(lang, "Description", "Beschreibung")) + "</h2>" + "".join(f"<p>{esc(par).replace(chr(10), '<br>')}</p>" for par in _lt.split("\n\n") if par.strip()) + _gen) if _lt.strip() else ""
            w = WT.get(lang, WT["en"])
            data_attr = esc(json.dumps({k: e.get(k) for k in ("id", "name", "type", "aliases", "desc", "web", "docs", "wikipedia", "wikidata", "rel", "outdated", "replaced_by", "start", "end", "long", "logo", "version", "released", "license", "level", "exam", "valid_months")}, ensure_ascii=False))
            edit = f'<div id="en-edit" data-e="{data_attr}"></div>'
            _fq = [x for x in FAQ.get(e["id"], []) if x.get("lang", "en") == lang][:8]
            kpbox, _efq = "", []
            if lang == "en" and eps:   # Kernpunkte und FAQ der Folgen, die den Namen nennen (nur englisch: keine gemischtsprachigen Seiten)
                _nrx = [re.compile(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", re.I) for n in ent_names(e) if len(n) > 1]
                _hit = lambda t: any(r.search(t) for r in _nrx)
                _kps = [(k, x) for x in eps for k in (x.get("keypoints") or []) if _hit(k)][:5]
                if _kps:
                    kpbox = (f'<section class="en-kp"><h2>{esc("Key points about " + e["name"])}</h2><ul>'
                             + "".join(f'<li>{esc(k)} <span class="mut">· <a href="{_epu(x)}">{esc(g["anchor_title"](x["e"]["title"], 48))}</a></span></li>' for k, x in _kps) + "</ul></section>")
                _seenq = {x["q"].strip().lower() for x in _fq}
                for x in eps:
                    for q in (x.get("faq") or []):
                        if len(_efq) >= 5: break
                        if q["q"].strip().lower() not in _seenq and (_hit(q["q"]) or _hit(q["a"])):
                            _seenq.add(q["q"].strip().lower()); _efq.append({"q": q["q"], "a": q["a"], "src": x})
            _allq = _fq + _efq
            faqbox = (f'<section class="en-faq"><h2>{T(lang, "Frequently asked questions", "Häufige Fragen")}</h2>' + "".join(
                f'<details><summary>{esc(x["q"])}</summary><p>{esc(x["a"])}' + (f' <span class="mut">· <a href="{_epu(x["src"])}">{esc(T(lang, "From the episode", "Aus der Folge"))}: {esc(g["anchor_title"](x["src"]["e"]["title"], 48))}</a></span>' if x.get("src") else "") + "</p></details>" for x in _allq) + "</section>") if _allq else ""
            faqbox += f'<div id="en-qa" data-eid="{e["id"]}"></div>'
            _epq = g.get("ep_by_spreaker") or {}
            _qurl = lambda q: _epq.get(str(q.get("episode_id")), (None, None))
            qbox = SQ.block(e["id"], lang, _qurl) if e["type"] == "person" else ""   # Zitate der Person (Quotes sind an Personen-Entitaeten gebunden)
            wb = wiki_block(lang, e["id"], api, BASE, stat.get(e["id"]), wiki_links(lang))
            _arts = topic_posts(posts_by_topic, e["id"], lang)
            artbox, arturls = articles_block(BASE, e, lang, _arts, lambda a, b_: T(lang, a, b_))
            # echtes Aenderungsdatum: Entitaet selbst (Hash), Community-Bearbeitung, juengster Artikel, juengste Folge, juengste Frage
            _mod = max([MOD.get(e["id"], TODAY), str(e.get("edited") or "")[:10], *[_iso(p.get("published")) for p in _arts[:1]], *[max((str(x.get("date", ""))[:10] for x in eps), default="")],
                        *[_iso(x.get("created")) for x in _fq[:1]]] + [""])
            _mod = _mod if len(_mod) == 10 and _mod <= TODAY else TODAY
            _src = [(T(lang, "Official website", "Offizielle Website"), e.get("web")), (T(lang, "Documentation", "Dokumentation"), e.get("docs")), ("Wikipedia", e.get("wikipedia")),
                    ("Wikidata", f"https://www.wikidata.org/wiki/{e['wikidata']}" if e.get("wikidata") else "")] + [(T(lang, "Profile", "Profil"), u_) for u_ in (e.get("same_as") or [])[:4]]
            _src = [(n_, u_) for n_, u_ in _src if u_ and str(u_).startswith("http")]
            srcbox = (f'<section class="en-src"><h2>{esc(T(lang, "Sources", "Quellen"))}</h2><ul>' + "".join(f'<li>{esc(n_)}: <a href="{esc(u_)}" rel="noopener">{esc(u_.replace("https://", "").rstrip("/"))}</a></li>' for n_, u_ in _src)
                      + (f'<li>{esc(T(lang, "Feed for this topic (RSS)", "Feed zu diesem Thema (RSS)"))}: <a href="{BASE}/entity/{e["id"]}/feed.xml">entity/{e["id"]}/feed.xml</a></li>' if (eps or _arts) else "")
                      + (f'<li>{esc(T(lang, "M365.FM episodes on this topic", "M365.FM-Folgen zum Thema"))}: {len(eps)}</li>' if eps else "") + (f'<li>{esc(T(lang, "Articles on this topic", "Artikel zum Thema"))}: {len(_arts)}</li>' if _arts else "") + "</ul></section>") if (_src or eps or _arts) else ""
            _au = ENTS.get(AUTHOR_EID)
            updline = (f'<p class="mut en-upd">' + (f'{esc(T(lang, "Maintained by", "Gepflegt von"))} <a href="{root}{AUTHOR_EID}/">{esc(_au["name"])}</a> (Microsoft MVP) · ' if _au and e["id"] != AUTHOR_EID else "")
                       + f'{esc(T(lang, "Last updated", "Zuletzt aktualisiert"))}: <time datetime="{_mod}">{_mod}</time></p>')
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{root}">{esc(s["entities"])}</a></nav><h1>{esc(e["name"])}</h1><p class="mut">{esc(TL[e["type"]][li])}</p><p class="en-def" style="font-size:1.1em">{esc(d)}</p>{oldbanner}{claim_html(e["id"], lang)}{hero}{longbox}{ft}{evl}{kpbox}{eb}{tline}{artbox}'
                          f'{qbox}{faqbox}{relmap}{relx}<div class="en-rel">{rb}</div>{gloss}{SU.block(lang, e["id"])}{wb}{("<h2>" + esc(s["experts"]) + "</h2>" + ehtml) if ehtml else ""}{srcbox}{updline}{edit}'
                          f'<script>window.M365E={{api:"{api}",lang:"{lang}",base:"{BASE}",s:{json.dumps({k: s[k] for k in ("edit_e",)}, ensure_ascii=False)}}};'
                          f'(function(){{var d=0,u="{BASE}/assets/entity.js";function go(){{if(d)return;d=1;var s=document.createElement("script");s.src=u;document.body.appendChild(s)}}'
                          f'var t=document.getElementById("en-qa")||document.getElementById("en-edit");if(!t||!("IntersectionObserver" in window)||location.hash)return go();'
                          f'var o=new IntersectionObserver(function(x){{if(x.some(function(y){{return y.isIntersecting}})){{o.disconnect();go()}}}},{{rootMargin:"600px"}});o.observe(t)}})();</script>')
            node = ent_ld(BASE, e, lang, gl_ids)
            _qld = SQ.ld(BASE, e["id"], lang, _qurl) if e["type"] == "person" else []
            if arturls:
                node["subjectOf"] = [{"@id": x + "#post"} for x in arturls[:20]]   # Artikel ueber diese Entitaet (Gegenrichtung zu BlogPosting.about)
            ld = [{"@context": "https://schema.org", "@type": "WebPage", "@id": u + "#page", "url": u, "name": e["name"], "inLanguage": lang, "mainEntity": node, "dateModified": _mod,
                   **({"author": {"@id": eid_of(BASE, AUTHOR_EID)}} if _au else {}),
                   "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", ".en-def"]},
                   "isPartOf": {"@id": f"{BASE}/#website"}, "relatedLink": [f"{root}{x}/" for k, v in groups.items() for x in v][:25],
                   **({"hasPart": {"@id": u + "#articles"}} if arturls else {}),
                   "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": s["entities"], "item": root}, {"@type": "ListItem", "position": 2, "name": e["name"], "item": u}]}}]
            if arturls:
                ld.append({"@context": "https://schema.org", "@type": "ItemList", "@id": u + "#articles", "name": T(lang, "Articles about {t}", "Artikel zu {t}").format(t=e["name"]), "numberOfItems": len(arturls),
                           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": x} for i, x in enumerate(arturls[:50])]})
            if _allq:
                ld.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": u + "#faq", "mainEntity": [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in _allq]})
            if eps:
                ld.append({"@context": "https://schema.org", "@type": "ItemList", "@id": u + "#episodes", "name": ept.format(t=e["name"]), "numberOfItems": len(eps),
                           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": _epu(x), "name": x["e"]["title"]} for i, x in enumerate(eps)]})
                _epids = [{"@id": x["url"] + "#episode"} for x in eps if x.get("url")]   # Folgenseiten der Hauptshow definieren #episode
                _epids += [{"@id": _epu(x) + "#video"} for x in eps if not x.get("url") and x.get("vid")]   # T27: Dub-Folgenseiten definieren das YouTube-Video als #video
                if _epids:
                    node["subjectOf"] = (node.get("subjectOf") or []) + _epids
            # hreflang en/de nur bei echtem deutschem Text (Gast-Entitaeten haben de == en: dann ist /de/ ein Duplikat und bleibt ohne Index)
            _has_de = bool(e["desc"].get("de")) and e["desc"].get("de") != e["desc"].get("en") or bool((e.get("long") or {}).get("de")) or bool(GENTEXT.get(e["id"], {}).get("de"))
            _thin = False
            if e["type"] == "person" and e["id"] != AUTHOR_EID:   # Personen: nur mit echter Beschreibung (nicht der Speaker-Schablone) oder mehreren Auftritten in den Index
                _app = len(eps) + len((SPEAKERS.get(e["id"]) or {}).get("sessions") or [])
                _real = (len(e["desc"].get("en") or "") > 80 and not e.get("speaker")) or bool((e.get("long") or {}).get("en"))
                _thin = not _real and _app < 2 and not SQ.BY_PERSON.get(e["id"])   # eigene Zitate sind echter Inhalt
            _alts = {"en": eurl(BASE, "en", e["id"]), "de": eurl(BASE, "de", e["id"])} if _has_de and not _thin else None
            _noidx = lang not in ("en", "de") or (lang == "de" and not _has_de) or _thin
            _feedu = f"{BASE}/entity/{e['id']}/feed.xml"
            if lang == "en" and (_arts or eps):   # Themen-Feed: neueste Artikel und Folgen zu dieser Entitaet (fuer Leser und Agenten)
                from xml.sax.saxutils import escape as _x
                from email.utils import formatdate as _fd
                _items = [("article", p["title"], f"{BASE}/community/u/{p['handle']}/blog/{p['slug']}/", p.get("published") or 0, p.get("summary") or "") for p in _arts[:30] if p.get("lang") == "en"]
                for x in eps[:20]:
                    try: _ts = int(__import__("datetime").datetime.strptime(str(x.get("date", ""))[:10], "%Y-%m-%d").replace(tzinfo=__import__("datetime").timezone.utc).timestamp())
                    except Exception: _ts = 0
                    _items.append(("episode", x["e"]["title"], _epu(x), _ts, x.get("sum") or ""))
                _items.sort(key=lambda t: -t[3])
                write(f"entity/{e['id']}/feed.xml", '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>' + f"<title>{_x(e['name'])} – M365.FM</title><link>{u}</link><description>{_x(d[:300])}</description><language>en</language>"
                      + "".join(f"<item><title>{_x(t)}</title><link>{lnk}</link><guid>{lnk}</guid><pubDate>{_fd(ts)}</pubDate><category>{k}</category><description>{_x(sm[:400])}</description></item>" for k, t, lnk, ts, sm in _items[:40]) + "</channel></rss>")
            _fhead = f'<link rel="alternate" type="application/rss+xml" title="{esc(e["name"])} – M365.FM" href="{_feedu}">' if (_arts or eps) else ""
            _w = write if lang in ("en", "de") else (g.get("write_r2") or write)   # Entitaetsseiten der 13 weiteren Sprachen (noindex, bis ihre Uebersetzungen angezeigt werden) liegen im R2-Bucket, nicht in GitHub Pages (~620 MB)
            ld = ld + _qld   # Quotation-Knoten der Person
            _w(f"{rel}/{e['id']}/index.html", page(lang, f'{e["name"]} – {TL[e["type"]][li]} | M365.FM', d[:155], u, b, _alts if lang in ("en", "de") else None, ld, xdefault=eurl(BASE, "en", e["id"]), og_type="website", extra_head=LCSS + css + _fhead, noindex=_noidx))
            if not _noidx: sitemap.append((u, _mod, _alts))


overlay("entities.S", S)
for _l in COMM_LANGS:
    OLD.setdefault(_l, OLD["en"])
