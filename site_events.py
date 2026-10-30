"""Events und Sessions: oeffentliche Event-Seiten mit Schema.org (Event, subEvent, performer, organizer, about -> Entitaeten)."""
from datetime import datetime
from site_learn import ENTS, esc, _fetch_json, LCSS
from site_entities import eurl, eid_of

S = {"en": dict(events="Events", intro="Conferences, webinars and meetups of the Microsoft community – with their sessions and speakers.", upcoming="Upcoming", past="Past", none="No events yet.",
                organizer="Organizer", when="When", where="Where", online="Online", onsite="On site", hybrid="Hybrid", free="Free", paid="Paid", topics="Topics", sessions="Sessions", speakers="Speakers", website="Website", tickets="Tickets / register",
                lang="Language", level="Level", room="Room", track="Track", about="About", create="Add your event", my="Sessions at events", recording="Recording", more="Events", sponsors="Looking for sponsors", nosess="No sessions published yet.", tbc="speaker(s) to be confirmed", propose="Propose a session"),
     "de": dict(events="Events", intro="Konferenzen, Webinare und Meetups der Microsoft-Community – mit Sessions und Speakern.", upcoming="Kommende", past="Vergangene", none="Noch keine Events.",
                organizer="Veranstalter", when="Wann", where="Wo", online="Online", onsite="Vor Ort", hybrid="Hybrid", free="Kostenlos", paid="Kostenpflichtig", topics="Themen", sessions="Sessions", speakers="Speaker", website="Webseite", tickets="Tickets / Anmeldung",
                lang="Sprache", level="Level", room="Raum", track="Track", about="Über das Event", create="Event eintragen", my="Sessions bei Events", recording="Aufzeichnung", more="Events", sponsors="Sucht Sponsoren", nosess="Noch keine Sessions veröffentlicht.", tbc="Speaker noch zu bestätigen", propose="Session vorschlagen")}
MODE_URL = {"online": "OnlineEventAttendanceMode", "onsite": "OfflineEventAttendanceMode", "hybrid": "MixedEventAttendanceMode"}


def fetch_events(api):
    return (_fetch_json(f"{api}/api/events/export") or {}).get("events", [])


def eurl_(BASE, lang, h):
    return f"{BASE}{'/de' if lang == 'de' else ''}/community/events/{h}/"


def fdate(s, lang):
    try:
        d = datetime.fromisoformat(s)
    except Exception:
        return s or ""
    t = f" {d:%H:%M}" if "T" in s else ""
    return (f"{d:%d.%m.%Y}" if lang == "de" else f"{d:%d %b %Y}") + t


def span(ev, lang):
    a, b = fdate(ev["start"], lang), fdate(ev.get("end"), lang) if ev.get("end") else ""
    return a if not b or b == a else f"{a} – {b}"


def event_ld(BASE, ev, pb, ob):
    u = eurl_(BASE, "en", ev["handle"])
    n = {"@type": "Event", "@id": u + "#event", "name": ev["title"], "url": u, "startDate": ev["start"], "eventStatus": "https://schema.org/EventScheduled",
         "eventAttendanceMode": "https://schema.org/" + MODE_URL.get(ev["mode"], "OnlineEventAttendanceMode"), "isAccessibleForFree": bool(ev.get("free"))}
    if ev.get("end"):
        n["endDate"] = ev["end"]
    d = ev.get("summary") or ev.get("about") or ""
    if d:
        n["description"] = d[:500]
    if ev.get("lang"):
        n["inLanguage"] = ev["lang"]
    loc = []
    if ev["mode"] in ("online", "hybrid"):
        loc.append({"@type": "VirtualLocation", "url": ev.get("url") or u})
    if ev["mode"] in ("onsite", "hybrid"):
        loc.append({"@type": "Place", "name": ev.get("location") or ev.get("country") or "TBA", **({"address": {"@type": "PostalAddress", "addressCountry": ev["country"]}} if ev.get("country") else {})})
    n["location"] = loc[0] if len(loc) == 1 else loc
    org = ev.get("organizer") or {}
    if org.get("kind") == "o" and org.get("handle") in ob:
        n["organizer"] = {"@id": f"{BASE}/community/c/{org['handle']}/#org"}
    elif org.get("kind") == "u" and org.get("handle") in pb:
        n["organizer"] = {"@id": f"{BASE}/community/u/{org['handle']}/#person"}
    elif org.get("name"):
        n["organizer"] = {"@type": "Organization" if org.get("kind") == "o" else "Person", "name": org["name"]}
    if ev.get("tickets_url"):
        n["offers"] = {"@type": "Offer", "url": ev["tickets_url"], "availability": "https://schema.org/InStock", **({"price": 0, "priceCurrency": "EUR"} if ev.get("free") else {})}
    t = [{"@id": eid_of(BASE, e)} for e in ev.get("topics", []) if e in ENTS]
    if t:
        n["about"] = t
    subs = []
    for s in ev.get("sessions", []):
        sub = {"@type": "Event", "name": s["title"], "superEvent": {"@id": u + "#event"}}
        if s.get("start"):
            sub["startDate"] = s["start"]
        else:
            sub["startDate"] = ev["start"]
        if s.get("end"):
            sub["endDate"] = s["end"]
        if s.get("abstract"):
            sub["description"] = s["abstract"][:500]
        if s.get("lang"):
            sub["inLanguage"] = s["lang"]
        perf = [({"@id": f"{BASE}/community/u/{x['h']}/#person"} if x.get("h") in pb else {"@id": eid_of(BASE, x["e"])} if x.get("e") in ENTS else {"@type": "Person", "name": x["n"]}) for x in s.get("speakers", [])]
        perf = [x for i, x in enumerate(perf) if x not in perf[:i]]
        if perf:
            sub["performer"] = perf
        st = [{"@id": eid_of(BASE, e)} for e in s.get("topics", []) if e in ENTS]
        if st:
            sub["about"] = st
        if s.get("recording_url"):
            sub["recordedIn"] = {"@type": "CreativeWork", "url": s["recording_url"]}
        subs.append(sub)
    if subs:
        n["subEvent"] = subs
    return n


def blocks(BASE, events, lang):
    """HTML-Bloecke fuer Profil-/Firmenseiten: {'u': {handle: html}, 'c': {handle: html}}"""
    s = S[lang]; out = {"u": {}, "c": {}}; sp = {}
    for ev in events:
        for se in ev.get("sessions", []):
            for x in se.get("speakers", []):
                if x.get("h"):
                    sp.setdefault(x["h"], []).append((ev, se))
        o = ev.get("organizer") or {}
        if o.get("handle"):
            out["c" if o["kind"] == "o" else "u"].setdefault(o["handle"], []).append(ev)
    res = {"u": {}, "c": {}}
    for h, lst in sp.items():
        res["u"][h] = f'<h2>{esc(s["my"])}</h2><ul>' + "".join(f'<li><a href="{eurl_(BASE, lang, ev["handle"])}">{esc(se["title"])}</a> <span class="mut">· {esc(ev["title"])} · {esc(fdate(se.get("start") or ev["start"], lang))}</span></li>' for ev, se in lst) + "</ul>"
    for k in ("u", "c"):
        for h, lst in out[k].items():
            res[k][h] = res[k].get(h, "") + f'<h2>{esc(s["more"])}</h2><ul>' + "".join(f'<li><a href="{eurl_(BASE, lang, ev["handle"])}">{esc(ev["title"])}</a> <span class="mut">· {esc(span(ev, lang))}</span></li>' for ev in lst) + "</ul>"
    return res


EVLIVE = r'''(function(){fetch("%API%/api/events/export").then(function(r){return r.json()}).then(function(j){var have={};[].forEach.call(document.querySelectorAll(".ev-list a[href]"),function(a){have[a.getAttribute("href")]=1});var T=new Date().toISOString().slice(0,10),ups=document.querySelector(".ev-list");(j.events||[]).forEach(function(e){var u="%BASE%"+e.handle+"/";if(have[u])return;if((e.end||e.start).slice(0,10)<T)return;var ul=document.querySelector(".ev-list");if(!ul){ul=document.createElement("ul");ul.className="ev-list";document.querySelector("h1").parentNode.appendChild(ul)}var li=document.createElement("li");li.className="ev-card";var a=document.createElement("a");a.href=u;var b=document.createElement("b");b.textContent=e.title;a.appendChild(b);li.appendChild(a);var sp=document.createElement("span");sp.className="mut";sp.textContent=" · "+e.start.slice(0,10);li.appendChild(sp);ul.insertBefore(li,ul.firstChild)})}).catch(function(){})})()'''


def build(g, events, people, orgs):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY = g["sitemap"], g["TODAY"]; api = g.get("api", "https://api-dub.m365.fm")
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:56em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}; ob = {o["handle"]: o for o in orgs}
    css = '<style>.ev-card{list-style:none;padding:.8em 0;border-bottom:1px solid var(--bd)}.ev-list{padding:0}.ev-s{padding:.7em 0;border-bottom:1px solid var(--bd)}.ev-s h3{margin:.1em 0}.ev-tag{display:inline-block;border:1px solid var(--bd);border-radius:2em;padding:.1em .7em;margin:.15em .3em .15em 0;font-size:.85em}</style>'
    for lang in ("en", "de"):
        s = S[lang]; noidx = lang == "de"; croot = f"{BASE}/community/" if lang == "en" else f"{BASE}/de/community/"
        for ev in events:
            u = eurl_(BASE, lang, ev["handle"]); org = ev.get("organizer") or {}
            if org.get("kind") == "o" and org.get("handle") in ob:
                oh = f'<a href="{BASE}{"/de" if lang == "de" else ""}/community/c/{org["handle"]}/">{esc(org["name"])}</a>'
            elif org.get("kind") == "u" and org.get("handle") in pb:
                oh = f'<a href="{BASE}{"/de" if lang == "de" else ""}/community/u/{org["handle"]}/">{esc(org["name"])}</a>'
            else:
                oh = esc(org.get("name", ""))
            facts = [(s["when"], esc(span(ev, lang))), (s["where"], esc({"online": s["online"], "onsite": s["onsite"], "hybrid": s["hybrid"]}[ev["mode"]] + (" · " + ev["location"] if ev.get("location") else "") + (" · " + ev["country"] if ev.get("country") else ""))),
                     (s["organizer"], oh), ("", esc(s["free"] if ev.get("free") else s["paid"]))]
            if ev.get("lang"):
                facts.append((s["lang"], esc(ev["lang"])))
            ft = '<table class="mb-facts"><tbody>' + "".join(f'<tr><th scope="row">{esc(a)}</th><td>{b_}</td></tr>' for a, b_ in facts if b_) + "</tbody></table>"
            btn = (f'<a class="btn main" href="{esc(ev["tickets_url"])}" rel="nofollow noopener" target="_blank">{esc(s["tickets"])}</a> ' if ev.get("tickets_url") else "") + (f'<a class="btn" href="{esc(ev["url"])}" rel="nofollow noopener" target="_blank">{esc(s["website"])}</a>' if ev.get("url") else "")
            tp = "".join(f'<a class="ev-tag" href="{eurl(BASE, lang, e)}">{esc(ENTS[e]["name"])}</a>' for e in ev.get("topics", []) if e in ENTS)
            ss = []
            for se in ev.get("sessions", []):
                spk = ", ".join((f'<a href="{BASE}{"/de" if lang == "de" else ""}/community/u/{x["h"]}/">{esc(x["n"])}</a>' if x.get("h") in pb else f'<a href="{eurl(BASE, lang, x["e"])}">{esc(x["n"])}</a>' if x.get("e") in ENTS else esc(x["n"])) for x in se.get("speakers", []))
                meta = " · ".join(esc(v) for v in [fdate(se["start"], lang) if se.get("start") else "", f'{s["room"]} {se["room"]}' if se.get("room") else "", f'{s["track"]} {se["track"]}' if se.get("track") else "", f'{s["level"]} {se["level"]}' if se.get("level") else "", se.get("lang", "")] if v)
                st = "".join(f'<a class="ev-tag" href="{eurl(BASE, lang, e)}">{esc(ENTS[e]["name"])}</a>' for e in se.get("topics", []) if e in ENTS)
                ss.append(f'<div class="ev-s"><h3>{esc(se["title"])}</h3><p class="mut">{meta}{" · " if meta and spk else ""}{spk}{(" · " + str(se["speakers_open"]) + " " + s["tbc"]) if se.get("speakers_open") else ""}</p>' + (f'<p style="white-space:pre-line">{esc(se["abstract"])}</p>' if se.get("abstract") else "") + st
                          + (f'<p><a href="{esc(se["recording_url"])}" rel="nofollow noopener" target="_blank">{esc(s["recording"])}</a></p>' if se.get("recording_url") else "") + "</div>")
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{croot}events/">{esc(s["events"])}</a></nav><h1>{esc(ev["title"])}</h1><p style="font-size:1.1em">{esc(ev.get("summary", ""))}</p>{ft}<p>{btn}</p>'
                      + (f'<h2>{esc(s["about"])}</h2><p style="white-space:pre-line">{esc(ev["about"])}</p>' if ev.get("about") else "") + (f'<h2>{esc(s["topics"])}</h2><p>{tp}</p>' if tp else "")
                      + f'<h2>{esc(s["sessions"])}</h2>' + ("".join(ss) or f'<p class="mut">{esc(s["nosess"])}</p>')
                      + f'<p><a class="btn" href="{croot}?propose={esc(ev["handle"])}#c-events">{esc(s["propose"])}</a></p>' + css)
            ld = [{"@context": "https://schema.org", **event_ld(BASE, ev, pb, ob)}]
            write(f"{'de/' if lang == 'de' else ''}community/events/{ev['handle']}/index.html", page(lang, f'{ev["title"]} – {s["events"]} | M365.FM', (ev.get("summary") or ev.get("about") or "")[:155], u, b, None, ld, og_type="website", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((u, TODAY, None))
        # Verzeichnis
        up = sorted([e for e in events if (e.get("end") or e["start"])[:10] >= TODAY], key=lambda e: e["start"]); pa = sorted([e for e in events if (e.get("end") or e["start"])[:10] < TODAY], key=lambda e: e["start"], reverse=True)
        li = lambda lst: "".join(f'<li class="ev-card"><a href="{eurl_(BASE, lang, e["handle"])}"><b>{esc(e["title"])}</b></a> <span class="mut">· {esc(span(e, lang))} · {esc({"online": s["online"], "onsite": s["onsite"], "hybrid": s["hybrid"]}[e["mode"]])}</span><br>{esc(e.get("summary", ""))}</li>' for e in lst)
        ru = f"{croot}events/"
        b = shell(lang, f'<h1>{esc(s["events"])}</h1><p class="mut">{esc(s["intro"])}</p><p><a class="btn main" href="{croot}#c-events">{esc(s["create"])}</a></p>'
                  + (f'<h2>{esc(s["upcoming"])}</h2><ul class="ev-list">{li(up)}</ul>' if up else "") + (f'<details class="ev-past"><summary><h2 style="display:inline">{esc(s["past"])} ({len(pa)})</h2></summary><ul class="ev-list">{li(pa)}</ul></details>' if pa else "") + ("" if events else f'<p class="mut">{esc(s["none"])}</p>') + "<script>" + EVLIVE.replace("%API%", api).replace("%BASE%", eurl_(BASE, lang, "")) + "</script>" + css)
        ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": s["events"], "url": ru, "description": s["intro"], "mainEntity": {"@type": "ItemList", "numberOfItems": len(events),
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@id": eurl_(BASE, "en", e["handle"]) + "#event"}} for i, e in enumerate(up + pa)]}}]
        write(f"{'de/' if lang == 'de' else ''}community/events/index.html", page(lang, f'{s["events"]} – M365.FM', s["intro"], ru, b, None, ld, og_type="website", extra_head=LCSS, noindex=noidx))
        if not noidx:
            sitemap.append((ru, TODAY, None))
