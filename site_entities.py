"""Entitaetsdatenbank fuer das Microsoft-Oekosystem: Seiten, JSON-Exporte, Schema.org-Graph."""
from site_i18n import T
import site_updates as SU
import site_media as MED
import json
from site_i18n import COMM_LANGS, pfx, pfx2, overlay
from pathlib import Path
from site_learn import (ENTS, esc, ent_names, fetch_wiki, wiki_block, WCSS, LCSS, WT, GLOSS, GLOSS_JS)

TL = {"product": ("Product", "Produkt"), "platform": ("Platform", "Plattform"), "concept": ("Concept", "Konzept"), "org": ("Organization", "Organisation"), "person": ("Person", "Person"),
      "cert": ("Certification", "Zertifizierung"), "event": ("Event", "Veranstaltung"), "media": ("Media", "Medium"), "category": ("Category", "Kategorie")}
FWD = {"instance_of": ("Is a", "Ist ein"), "part_of": ("Part of", "Teil von"), "developed_by": ("Developed by", "Entwickelt von"), "related_to": ("Related to", "Verwandt mit"), "requires": ("Requires", "Benötigt"),
       "covers": ("Covers", "Behandelt"), "created_by": ("Created by", "Erstellt von"), "organized_by": ("Organized by", "Veranstaltet von"), "similar_to": ("Similar to", "Ähnlich wie")}
INV = {"instance_of": ("Examples", "Beispiele"), "part_of": ("Includes", "Enthält"), "developed_by": ("Products and works", "Produkte und Werke"), "related_to": ("Related to", "Verwandt mit"),
       "requires": ("Required by", "Benötigt von"), "covers": ("Covered by", "Behandelt in"), "created_by": ("Created", "Erstellt"), "organized_by": ("Organizes", "Veranstaltet"), "similar_to": ("Similar to", "Ähnlich wie")}
S = {"en": dict(entities="Microsoft ecosystem entity database", intro="Products, platforms, concepts, certifications and organisations around Microsoft – with relationships, described by the community and published as Schema.org data.", new="Add a new topic", all="All", facts="Facts", website="Website", docs="Documentation", wikipedia="Wikipedia", wikidata="Wikidata", type="Type", aka="Also known as", experts="Experts and companies for this topic", noexperts="Nobody has listed this topic yet. Add it to your profile.", eps="Episodes about {t}", export="Data export", edit_e="Edit properties", glossary="Glossary", count="{n} entries", up="Last edited"),
     "de": dict(entities="Entitätsdatenbank zum Microsoft-Ökosystem", intro="Produkte, Plattformen, Konzepte, Zertifizierungen und Organisationen rund um Microsoft – mit Beziehungen, von der Community beschrieben und als Schema.org-Daten veröffentlicht.", new="Neues Thema anlegen", all="Alle", facts="Fakten", website="Webseite", docs="Dokumentation", wikipedia="Wikipedia", wikidata="Wikidata", type="Typ", aka="Auch bekannt als", experts="Experten und Firmen zu diesem Thema", noexperts="Dieses Thema hat noch niemand im Profil angegeben. Trag es in deinem Profil ein.", eps="Folgen zu {t}", export="Datenexport", edit_e="Eigenschaften bearbeiten", glossary="Glossar", count="{n} Einträge", up="Zuletzt bearbeitet")}


SPEAKERS = {}   # Entitaets-ID -> zusammengefuehrter Speaker (data/speakers.json) mit Events und Sessions
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
        if e.get("job"):
            n["jobTitle"] = e["job"]
        if e.get("company"):
            n["worksFor"] = {"@type": "Organization", "name": e["company"]}
        if SPEAKERS.get(e["id"], {}).get("events"):   # Auftritte als Speaker (Events der Plattform)
            n["performerIn"] = [{"@type": "Event", "name": x["title"], "url": f"{BASE}/community/events/{x['handle']}/"} for x in SPEAKERS[e["id"]]["events"]]
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


def build(g, wiki_links, experts_by_ent, ep_find):
    global BASE_
    BASE_ = g["BASE"]
    """g: ctx wie bei build_learn. experts_by_ent: eid -> [{kind,handle,name,headline,verified,level,endorsed}]; ep_find(entity)->[episodes]."""
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY, url_of = g["sitemap"], g["TODAY"], g["url_of"]
    api = g.get("api", "https://api-dub.m365.fm")
    gl_ids = {x["id"] for x in GLOSS}
    inv = inverse_index()
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:56em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'

    # --- Exporte ---
    recs = sorted(ENTS.values(), key=lambda e: e["id"])
    write("entities.json", json.dumps({"version": 1, "generated": TODAY, "license": "CC BY 4.0, M365.FM community", "entities": recs}, ensure_ascii=False, indent=1))
    write("entities.jsonld", json.dumps({"@context": "https://schema.org", "@graph": [ent_ld(BASE, e, "en", gl_ids) for e in recs]}, ensure_ascii=False))
    sitemap.append((f"{BASE}/entities.jsonld", TODAY, None))

    cfg_t = lambda lang: S[lang]
    for lang in COMM_LANGS:
        s = S[lang]; li = 1 if lang == "de" else 0
        stat = fetch_wiki(api, lang)
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
        css = '<style>' + MED.CSS + '.en-ep{margin:1em 0}.en-ep h3{margin:.2em 0}.en-ep p{margin:.2em 0}.en-faq details,.wk-q{border:1px solid var(--bd);border-radius:.4em;padding:.5em .8em;margin:.4em 0;background:var(--card)}.en-faq summary{cursor:pointer;font-weight:600}.wk-a{margin:.4em 0 .4em 1em}.en-old{border:1px solid var(--bd);border-left:4px solid #b45309;background:var(--card);padding:.6em .9em;border-radius:.4em}.en-f{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.35em .9em;margin:.2em .3em .2em 0;background:var(--card);color:var(--fg);min-height:2.5rem}.en-f[aria-pressed=true]{background:var(--ac);color:var(--onac);border-color:var(--ac)}.en-list{list-style:none;padding:0}.en-list li{padding:.55em 0;border-bottom:1px solid var(--bd)}.en-list li[hidden]{display:none}.en-facts{border-collapse:collapse;width:100%}.en-facts th{text-align:start;padding:.4em .8em .4em 0;vertical-align:top;white-space:nowrap}.en-facts td{padding:.4em 0}.en-rel h3{margin:.9em 0 .2em;font-size:1rem}.en-rel ul{margin:.2em 0;padding-inline-start:1.3em}</style>'
        newbtn = f'<div id="en-new" data-lang="{lang}"></div>'
        body = shell(lang, f'<h1>{esc(s["entities"])}</h1><p class="mut">{esc(s["intro"])}</p><p>{esc(s["count"].format(n=len(recs)))} · <a href="{BASE}/entities.json">{esc(s["export"])} (JSON)</a> · <a href="{BASE}/entities.jsonld">JSON-LD</a></p>{newbtn}<p><label><input type="checkbox" id="en-old"> {esc(OLD[lang][1])}</label></p><div role="group" aria-label="{esc(s["type"])}">{filt}</div><ul class="en-list">{"".join(card(e) for e in sorted(recs, key=lambda x: x["name"].lower()))}</ul>{js}'
                      f'<script>window.M365E={{api:"{api}",lang:"{lang}",base:"{BASE}",s:{json.dumps({k: s[k] for k in ("new",)}, ensure_ascii=False)}}}</script><script defer src="{BASE}/assets/entity.js"></script>')
        _terms = [e for e in recs if e["type"] in ("concept", "category")]
        ld = [{"@context": "https://schema.org", "@type": "DefinedTermSet", "@id": f"{BASE}/entity/#set", "name": "M365.FM Entities", "url": root, "inLanguage": lang, "description": s["intro"],
               "hasDefinedTerm": [{"@id": eid_of(BASE, e["id"])} for e in _terms]},
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": s["entities"], "url": root, "description": s["intro"], "mainEntity": {"@type": "ItemList", "numberOfItems": len(recs), "itemListElement":
               [{"@type": "ListItem", "position": i + 1, "item": {"@id": eid_of(BASE, e["id"])}} for i, e in enumerate(sorted(recs, key=lambda x: x["name"].lower()))]}}]
        write(f"{rel}/index.html", page(lang, f'{s["entities"]} – M365.FM', s["intro"], root, body, None, ld, og_type="website", extra_head=LCSS + WCSS + css, noindex=lang not in ("en", "de")))
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
            eps = ep_find(e, lang)   # Folgen in der Sprache der Seite, sonst keine
            ept = s.get("eps") or S["en"]["eps"]
            eb = (f'<h2>{esc(ept.format(t=e["name"]))}</h2>' + "".join(
                f'<article class="en-ep"><h3><a href="{url_of(x)}">{esc(g["anchor_title"](x["e"]["title"]))}</a></h3><p class="mut">{esc(x.get("date", ""))}</p><p>{esc(g["ep_sum"](x))}</p></article>' for x in eps)) if eps else ""
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
            tline = MED.timeline_svg([(x.get("date", ""), g["anchor_title"](x["e"]["title"]), url_of(x)) for x in eps], T(lang, f"Timeline of episodes about {e['name']}", f"Zeitleiste der Folgen zu {e['name']}"))
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
            longbox = ("<h2>" + (T(lang, "Description", "Beschreibung")) + "</h2>" + "".join(f"<p>{esc(par).replace(chr(10), '<br>')}</p>" for par in _lt.split("\n\n") if par.strip())) if _lt.strip() else ""
            w = WT.get(lang, WT["en"])
            data_attr = esc(json.dumps({k: e.get(k) for k in ("id", "name", "type", "aliases", "desc", "web", "docs", "wikipedia", "wikidata", "rel", "outdated", "replaced_by", "start", "end", "long", "logo", "version", "released", "license", "level", "exam", "valid_months")}, ensure_ascii=False))
            edit = f'<div id="en-edit" data-e="{data_attr}"></div>'
            _fq = [x for x in FAQ.get(e["id"], []) if x.get("lang", "en") == lang][:8]
            faqbox = (f'<section class="en-faq"><h2>{T(lang, "Frequently asked questions", "Häufige Fragen")}</h2>' + "".join(f'<details><summary>{esc(x["q"])}</summary><p>{esc(x["a"])}</p></details>' for x in _fq) + "</section>") if _fq else ""
            faqbox += f'<div id="en-qa" data-eid="{e["id"]}"></div>'
            wb = wiki_block(lang, e["id"], api, BASE, stat.get(e["id"]), wiki_links(lang))
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{root}">{esc(s["entities"])}</a></nav><h1>{esc(e["name"])}</h1><p class="mut">{esc(TL[e["type"]][li])}</p><p style="font-size:1.1em">{esc(d)}</p>{oldbanner}{claim_html(e["id"], lang)}{hero}{longbox}{ft}{evl}{gloss}'
                          f'{faqbox}{relmap}{relx}<div class="en-rel">{rb}</div>{tline}{eb}{SU.block(lang, e["id"])}{wb}{("<h2>" + esc(s["experts"]) + "</h2>" + ehtml) if ehtml else ""}{edit}'
                          f'<script>window.M365E={{api:"{api}",lang:"{lang}",base:"{BASE}",s:{json.dumps({k: s[k] for k in ("edit_e",)}, ensure_ascii=False)}}}</script><script defer src="{BASE}/assets/entity.js"></script>')
            node = ent_ld(BASE, e, lang, gl_ids)
            ld = [{"@context": "https://schema.org", "@type": "WebPage", "@id": u + "#page", "url": u, "name": e["name"], "inLanguage": lang, "mainEntity": node, "dateModified": TODAY,
                   "isPartOf": {"@id": f"{BASE}/#website"}, "relatedLink": [f"{root}{x}/" for k, v in groups.items() for x in v][:25],
                   "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": s["entities"], "item": root}, {"@type": "ListItem", "position": 2, "name": e["name"], "item": u}]}}]
            if _fq:
                ld.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": u + "#faq", "mainEntity": [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in _fq]})
            write(f"{rel}/{e['id']}/index.html", page(lang, f'{e["name"]} – {TL[e["type"]][li]} | M365.FM', d[:155], u, b, None, ld, og_type="website", extra_head=LCSS + css, noindex=lang not in ("en", "de")))
            if lang in ("en", "de"): sitemap.append((u, TODAY, None))


overlay("entities.S", S)
for _l in COMM_LANGS:
    OLD.setdefault(_l, OLD["en"])
