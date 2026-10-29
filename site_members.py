"""Mitglieder- und Firmenverzeichnis: oeffentliche Experten-Profile (nur Opt-in) mit Schema.org-Verknuepfung zu den Entitaeten."""
import json
from datetime import datetime, timezone
from site_learn import ENTS, esc, _fetch_json, LCSS
from site_entities import TL, eurl, eid_of

PROG = {"mvp": ("Microsoft MVP", "Microsoft MVP"), "mct": ("Microsoft Certified Trainer (MCT)", "Microsoft Certified Trainer (MCT)"), "rd": ("Microsoft Regional Director", "Microsoft Regional Director"),
        "msa": ("Microsoft Student Ambassador", "Microsoft Student Ambassador"), "ms_employee": ("Microsoft employee", "Microsoft-Mitarbeiter:in"), "partner": ("Microsoft Partner", "Microsoft Partner")}
KIND = {"linkedin": "LinkedIn", "github": "GitHub", "youtube": "YouTube", "x": "X", "mastodon": "Mastodon", "bluesky": "Bluesky", "twitch": "Twitch", "blog": "Blog", "podcast": "Podcast", "newsletter": "Newsletter", "website": "Website", "other": "Link"}
LV = {1: ("learning", "lernt"), 2: ("practitioner", "Praxis"), 3: ("expert", "Experte")}
S = {"en": dict(members="Members", companies="Companies", mintro="Experts of the Microsoft community – with programs such as MVP and MCT, certifications, topics and channels. Profiles are opt-in.", cintro="Companies in the Microsoft ecosystem and their teams.",
                about="About", expertise="Topics and expertise", certs="Certifications", channels="Channels and links", contrib="Contributions", latest="Latest from this creator", team="Team", verified="confirmed by the editorial team", selfdecl="self-declared", endorsed="confirmed by {n} members",
                none="No public profiles yet.", join="Create your profile", filter="Filter", all="All", feed="Latest from the creators", feedtop="Most upvoted (30 days)", company="Company", country="Country", wiki="wiki edit", entity="entity edit", prog="Programs", size="Employees", site="Website", since="since"),
     "de": dict(members="Mitglieder", companies="Firmen", mintro="Expert:innen der Microsoft-Community – mit Programmen wie MVP und MCT, Zertifizierungen, Themen und Kanälen. Profile sind freiwillig.", cintro="Firmen im Microsoft-Ökosystem und ihre Teams.",
                about="Über", expertise="Themen und Expertise", certs="Zertifizierungen", channels="Kanäle und Links", contrib="Beiträge", latest="Das Neueste von diesem Creator", team="Team", verified="vom Redaktionsteam bestätigt", selfdecl="Selbstangabe", endorsed="von {n} Mitgliedern bestätigt",
                none="Noch keine öffentlichen Profile.", join="Eigenes Profil anlegen", filter="Filter", all="Alle", feed="Das Neueste der Creator", feedtop="Meist gelobt (30 Tage)", company="Firma", country="Land", wiki="Wiki-Änderung", entity="Entitäts-Änderung", prog="Programme", size="Mitarbeitende", site="Webseite", since="seit")}
SIZE_N = {"1": (1, 1), "2-10": (2, 10), "11-50": (11, 50), "51-200": (51, 200), "201-1000": (201, 1000), "1000+": (1001, None)}


def fetch_members(api):
    j = _fetch_json(f"{api}/api/profiles/export") or {}
    return j.get("people", []), j.get("orgs", [])


def experts_index(people, orgs):
    ix = {}
    for kind, lst in (("u", people), ("o", orgs)):
        for x in lst:
            for ex in x.get("expertise", []):
                ix.setdefault(ex["e"], []).append({"kind": kind, "handle": x["handle"], "name": x["name"], "headline": x.get("headline") or x.get("tagline") or "", "verified": ex.get("verified"), "level": ex.get("level", 2), "endorsed": ex.get("endorsed", 0)})
    for k in ix:
        ix[k].sort(key=lambda a: (-int(bool(a["verified"])), -a["endorsed"], -a["level"], a["name"].lower()))
    return ix


def purl(BASE, lang, kind, h):
    return f"{BASE}{'/de' if lang == 'de' else ''}/community/{kind}/{h}/"


REL = {"colleague": ("Colleague", "Kollege/Kollegin"), "manager": ("Manager", "Führungskraft"), "report": ("Direct report", "Mitarbeiter:in"), "client": ("Client", "Kunde/Kundin"), "trainer": ("Trainer", "Trainer:in"),
       "student": ("Student / participant", "Teilnehmer:in / Schüler:in"), "cospeaker": ("Co-speaker / event", "Co-Speaker / Event"), "podcast": ("Podcast guest or host", "Podcast-Gast oder -Host"),
       "community": ("Community", "Community"), "mentor": ("Mentor / mentee", "Mentor:in / Mentee"), "other": ("Other", "Sonstiges")}
RS = {"en": dict(recs="Recommendations", relof="{n} · {rel}", write="Write a recommendation"), "de": dict(recs="Empfehlungen", relof="{n} · {rel}", write="Empfehlung schreiben")}
import os as _os
_API = _os.environ.get("COMMUNITY_API") or "https://api-dub.m365.fm"


def img_url(kind, x):
    return f"{_API}/api/img/{kind}/{x['handle']}.jpg?v={x['img']}" if x.get("img") else ""


def img_tag(kind, x, alt):
    u = img_url(kind, x)
    return f'<img src="{esc(u)}" alt="{esc(alt)}" width="112" height="112" loading="lazy" style="float:inline-end;border-radius:{"50%" if kind == "u" else "12px"};object-fit:cover;margin-inline-start:1em">' if u else ""


def person_ld(BASE, p, orgs_by_handle):
    pid = f"{purl(BASE, 'en', 'u', p['handle'])}#person"
    n = {"@type": "Person", "@id": pid, "name": p["name"], "url": purl(BASE, "en", "u", p["handle"]), "mainEntityOfPage": {"@id": purl(BASE, "en", "u", p["handle"]) + "#profile"}}
    if img_url("u", p):
        n["image"] = img_url("u", p)
    if p.get("recs"):
        n["review"] = [{"@type": "Review", "reviewBody": r["body"][:600], "author": {"@type": "Person", "name": r["by"]["name"], **({"url": purl(BASE, "en", "u", r["by"]["handle"])} if r["by"].get("handle") else {})}, "datePublished": datetime.fromtimestamp(r["created"], timezone.utc).strftime("%Y-%m-%d")} for r in p["recs"][:10]]
    if p.get("headline"):
        n["description"] = p["headline"]
    if p.get("about"):
        n["disambiguatingDescription"] = p["about"][:300]
    if p.get("job"):
        n["jobTitle"] = p["job"]
    if p.get("country"):
        n["address"] = {"@type": "PostalAddress", "addressCountry": p["country"]}
    org = p.get("org")
    if org and org["handle"] in orgs_by_handle:
        n["worksFor"] = {"@id": f"{purl(BASE, 'en', 'c', org['handle'])}#org"}
    elif p.get("company"):
        n["worksFor"] = {"@type": "Organization", "name": p["company"]}
    n["knowsAbout"] = [{"@id": eid_of(BASE, e["e"])} for e in p.get("expertise", []) if e["e"] in ENTS]
    creds = []
    for c in p.get("certs", []):
        if c["e"] in ENTS:
            cr = {"@type": "EducationalOccupationalCredential", "name": ENTS[c["e"]]["name"], "credentialCategory": "certification", "about": {"@id": eid_of(BASE, c["e"])}, "recognizedBy": {"@id": eid_of(BASE, "microsoft")}}
            if c.get("url"):
                cr["url"] = c["url"]
            creds.append(cr)
    if creds:
        n["hasCredential"] = creds
    aw = [PROG[x["p"]][0] for x in p.get("programs", []) if x.get("verified") and x["p"] in ("mvp", "mct", "rd", "msa")]
    if aw:
        n["award"] = aw
    mem = [{"@type": "OrganizationRole", "memberOf": {"@id": eid_of(BASE, "microsoft")}, "roleName": PROG[x["p"]][0]} for x in p.get("programs", []) if x.get("verified")]
    if mem:
        n["memberOf"] = mem
    same = [c["url"] for c in p.get("channels", [])] + [x["url"] for x in p.get("programs", []) if x.get("verified") and x.get("url")]
    if same:
        n["sameAs"] = same
    cnt = (p.get("counts") or {}); tot = cnt.get("wiki", 0) + cnt.get("entity", 0)
    if tot:
        n["agentInteractionStatistic"] = {"@type": "InteractionCounter", "interactionType": "https://schema.org/WriteAction", "userInteractionCount": tot}
    return n


def org_ld(BASE, o, people_by_handle):
    n = {"@type": "Organization", "@id": f"{purl(BASE, 'en', 'c', o['handle'])}#org", "name": o["name"], "url": o.get("website") or purl(BASE, "en", "c", o["handle"]), "mainEntityOfPage": {"@id": purl(BASE, "en", "c", o["handle"]) + "#profile"}}
    if img_url("o", o):
        n["logo"] = n["image"] = img_url("o", o)
    if o.get("tagline"):
        n["slogan"] = o["tagline"]
    if o.get("about"):
        n["description"] = o["about"][:500]
    if o.get("country"):
        n["address"] = {"@type": "PostalAddress", "addressCountry": o["country"]}
    sz = SIZE_N.get(o.get("size") or "")
    if sz:
        n["numberOfEmployees"] = {"@type": "QuantitativeValue", "minValue": sz[0], **({"maxValue": sz[1]} if sz[1] else {})}
    n["knowsAbout"] = [{"@id": eid_of(BASE, e["e"])} for e in o.get("expertise", []) if e["e"] in ENTS]
    emp = [{"@id": f"{purl(BASE, 'en', 'u', m['handle'])}#person"} for m in o.get("members", []) if m["handle"] in people_by_handle]
    if emp:
        n["employee"] = emp
    if any(x["p"] == "partner" and x.get("verified") for x in o.get("programs", [])):
        n["memberOf"] = {"@type": "OrganizationRole", "memberOf": {"@id": eid_of(BASE, "microsoft")}, "roleName": "Microsoft Partner"}
    same = [c["url"] for c in o.get("channels", [])]
    if same:
        n["sameAs"] = same
    return n


def build(g, people, orgs, extra=None):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    sitemap, TODAY = g["sitemap"], g["TODAY"]; api = g.get("api", "https://api-dub.m365.fm")
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:56em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}; ob = {o["handle"]: o for o in orgs}
    css = ('<style>.mb-card{list-style:none;padding:.7em 0;border-bottom:1px solid var(--bd)}.mb-list{padding:0}.mb-tag{display:inline-block;border:1px solid var(--bd);border-radius:2em;padding:.1em .7em;margin:.15em .3em .15em 0;font-size:.88rem;background:var(--card)}'
           '.mb-tag.ok{border-color:var(--ac)}.mb-f{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.35em .9em;margin:.2em .3em .2em 0;background:var(--card);color:var(--fg);min-height:2.5rem}.mb-f[aria-pressed=true]{background:var(--ac);color:var(--onac);border-color:var(--ac)}'
           '.mb-card[hidden]{display:none}.mb-facts{border-collapse:collapse}.mb-facts th{text-align:start;padding:.3em .8em .3em 0;vertical-align:top}.pf-item{display:flex;gap:.8em;align-items:flex-start;padding:.5em 0;border-bottom:1px solid var(--bd);list-style:none}.pf-item .vt{font:inherit;min-width:3.2rem;min-height:2.5rem;border:1px solid var(--bd);border-radius:.5em;background:var(--card);color:var(--fg);cursor:pointer}.pf-item .vt[aria-pressed=true]{background:var(--ac);color:var(--onac);border-color:var(--ac)}.pf-list{padding:0}</style>')
    live_js = f'<script>window.M365P={{api:"{api}",base:"{BASE}"}}</script><script defer src="{BASE}/assets/pfpub.js"></script>'

    def rec_html(p, lang, li, pb):
        if not p.get("recs"):
            return ""
        items = "".join('<li class="mb-card"><span class="mut">' + (f'<a href="{purl(BASE, lang, "u", r["by"]["handle"])}">{esc(r["by"]["name"])}</a>' if r["by"].get("handle") in pb else esc(r["by"]["name"])) + " · " + esc(REL.get(r["relation"], REL["other"])[li])
                        + "</span><br><span style=\"white-space:pre-line\">" + esc(r["body"]) + "</span></li>" for r in p["recs"])
        return f'<h2>{esc(RS[lang]["recs"])}</h2><ul class="mb-list">{items}</ul>'

    def tags_of_p(x, li, s):
        return "".join(f'<span class="mb-tag{" ok" if p.get("verified") else ""}">{esc(PROG[p["p"]][li])}{" ✔" if p.get("verified") else ""}</span>' for p in x.get("programs", []))

    def exp_ul(x, lang, li, s, mine=None):
        out = []
        for e in x.get("expertise", []):
            if e["e"] not in ENTS:
                continue
            en = ENTS[e["e"]]; note = []
            if e.get("verified"):
                note.append(s["verified"])
            elif e.get("endorsed"):
                note.append(s["endorsed"].format(n=e["endorsed"]))
            else:
                note.append(s["selfdecl"])
            out.append(f'<li><a href="{eurl(BASE, lang, e["e"])}">{esc(en["name"])}</a> <span class="mut">· {esc(LV[e.get("level", 2)][li])} · {esc(", ".join(note))}</span>'
                       f'<span class="pf-endorse" data-h="{esc(x["handle"])}" data-e="{e["e"]}"></span></li>')
        return "<ul>" + "".join(out) + "</ul>" if out else ""

    def items_ul(x):
        its = x.get("items", [])
        if not its:
            return ""
        return '<ul class="pf-list">' + "".join(f'<li class="pf-item" data-id="{i["id"]}"><button type="button" class="vt" aria-pressed="false" aria-label="Upvote"><span aria-hidden="true">▲</span> <span class="n">{i["votes"]}</span></button>'
                                                f'<div><a href="{esc(i["url"])}" rel="nofollow ugc noopener" target="_blank">{esc(i["title"])}</a><br><span class="mut">{esc(KIND.get(i["kind"], i["kind"]))} · {datetime.fromtimestamp(i["published"], timezone.utc).strftime("%Y-%m-%d")}</span></div></li>' for i in its) + "</ul>"

    def chan_ul(x):
        return '<ul>' + "".join(f'<li><a href="{esc(c["url"])}" rel="me nofollow ugc noopener" target="_blank">{esc(KIND.get(c["kind"], c["kind"]))}</a> <span class="mut">{esc(c["url"].replace("https://", "").rstrip("/")[:60])}</span></li>' for c in x.get("channels", [])) + "</ul>" if x.get("channels") else ""

    for lang in ("en", "de"):
        s = S[lang]; li = 0 if lang == "en" else 1; noidx = lang == "de"
        croot = f"{BASE}/community/" if lang == "en" else f"{BASE}/de/community/"
        # ---- Personen-Seiten ----
        for p in people:
            u = purl(BASE, lang, "u", p["handle"])
            org = p.get("org")
            facts = []
            if p.get("job") or p.get("company") or org:
                comp = f'<a href="{purl(BASE, lang, "c", org["handle"])}">{esc(org["name"])}</a>' if org and org["handle"] in ob else esc(p.get("company", ""))
                facts.append((s["company"], esc(p.get("job", "")) + (" · " if p.get("job") and comp else "") + comp))
            if p.get("country"):
                facts.append((s["country"], esc(p["country"])))
            ft = '<table class="mb-facts"><tbody>' + "".join(f'<tr><th scope="row">{esc(a)}</th><td>{b}</td></tr>' for a, b in facts) + "</tbody></table>" if facts else ""
            certs = "<ul>" + "".join(f'<li><a href="{eurl(BASE, lang, c["e"])}">{esc(ENTS[c["e"]]["name"])}</a>{" (" + str(c["year"]) + ")" if c.get("year") else ""}{" · " + "<a href=" + chr(34) + esc(c["url"]) + chr(34) + " rel=" + chr(34) + "nofollow ugc noopener" + chr(34) + ">✔</a>" if c.get("url") else ""}</li>' for c in p.get("certs", []) if c["e"] in ENTS) + "</ul>" if p.get("certs") else ""
            contrib = "<ul>" + "".join(f'<li><a href="{eurl(BASE, lang, c["t"])}">{esc(ENTS[c["t"]]["name"] if c["t"] in ENTS else c["t"])}</a> <span class="mut">· {esc(s["wiki"] if c["k"] == "wiki" else s["entity"])} · {datetime.fromtimestamp(c["c"], timezone.utc).strftime("%Y-%m-%d")}{" – " + esc(c["s"]) if c.get("s") else ""}</span></li>' for c in p.get("contrib", []) if c["t"] in ENTS) + "</ul>" if p.get("contrib") else ""
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{croot}members/">{esc(s["members"])}</a></nav>{img_tag("u", p, p["name"])}<h1>{esc(p["name"])}</h1><p style="font-size:1.1em">{esc(p.get("headline", ""))}</p><p>{tags_of_p(p, li, s)}</p>{ft}'
                          + (f'<h2>{esc(s["about"])}</h2><p style="white-space:pre-line">{esc(p["about"])}</p>' if p.get("about") else "")
                          + (f'<h2>{esc(s["expertise"])}</h2>{exp_ul(p, lang, li, s)}' if p.get("expertise") else "") + (f'<h2>{esc(s["certs"])}</h2>{certs}' if certs else "")
                          + (f'<h2>{esc(s["latest"])}</h2>{items_ul(p)}' if p.get("items") else "") + (f'<h2>{esc(s["channels"])}</h2>{chan_ul(p)}' if p.get("channels") else "")
                          + rec_html(p, lang, li, pb) + (f'<h2>{esc(s["contrib"])}</h2>{contrib}' if contrib else "") + ((extra or {}).get(lang, {}).get("u", {}).get(p["handle"], "")) + live_js + css)
            node = person_ld(BASE, p, ob)
            ld = [{"@context": "https://schema.org", "@type": "ProfilePage", "@id": purl(BASE, "en", "u", p["handle"]) + "#profile", "url": u, "name": p["name"], "inLanguage": lang, "dateModified": TODAY, "mainEntity": node}]
            write(f"{'de/' if lang == 'de' else ''}community/u/{p['handle']}/index.html", page(lang, f'{p["name"]} – {p.get("headline") or s["members"]} | M365.FM', (p.get("headline") or p.get("about") or "")[:155], u, b, None, ld, og_type="profile", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((u, TODAY, None))
        # ---- Firmen-Seiten ----
        for o in orgs:
            u = purl(BASE, lang, "c", o["handle"])
            mem = "<ul>" + "".join(f'<li><a href="{purl(BASE, lang, "u", m["handle"])}">{esc(m["name"])}</a><span class="mut"> · {esc(m.get("headline", "")[:80])}</span></li>' for m in o.get("members", []) if m["handle"] in pb) + "</ul>" if o.get("members") else ""
            facts = [(s["size"], esc(o["size"]))] if o.get("size") else []
            if o.get("country"):
                facts.append((s["country"], esc(o["country"])))
            if o.get("website"):
                facts.append((s["site"], f'<a href="{esc(o["website"])}" rel="nofollow ugc noopener" target="_blank">{esc(o["website"].replace("https://", "").rstrip("/"))}</a>'))
            ft = '<table class="mb-facts"><tbody>' + "".join(f'<tr><th scope="row">{esc(a)}</th><td>{b_}</td></tr>' for a, b_ in facts) + "</tbody></table>" if facts else ""
            b = shell(lang, f'<nav aria-label="breadcrumb"><a href="{croot}companies/">{esc(s["companies"])}</a></nav>{img_tag("o", o, o["name"])}<h1>{esc(o["name"])}</h1><p style="font-size:1.1em">{esc(o.get("tagline", ""))}</p><p>{tags_of_p(o, li, s)}</p>{ft}'
                          + (f'<h2>{esc(s["about"])}</h2><p style="white-space:pre-line">{esc(o["about"])}</p>' if o.get("about") else "")
                          + (f'<h2>{esc(s["expertise"])}</h2>{exp_ul(o, lang, li, s)}' if o.get("expertise") else "") + (f'<h2>{esc(s["team"])}</h2>{mem}' if mem else "")
                          + (f'<h2>{esc(s["latest"])}</h2>{items_ul(o)}' if o.get("items") else "") + (f'<h2>{esc(s["channels"])}</h2>{chan_ul(o)}' if o.get("channels") else "") + ((extra or {}).get(lang, {}).get("c", {}).get(o["handle"], "")) + live_js + css)
            ld = [{"@context": "https://schema.org", "@type": "ProfilePage", "@id": purl(BASE, "en", "c", o["handle"]) + "#profile", "url": u, "name": o["name"], "inLanguage": lang, "dateModified": TODAY, "mainEntity": org_ld(BASE, o, pb)}]
            write(f"{'de/' if lang == 'de' else ''}community/c/{o['handle']}/index.html", page(lang, f'{o["name"]} – {o.get("tagline") or s["companies"]} | M365.FM', (o.get("tagline") or o.get("about") or "")[:155], u, b, None, ld, og_type="profile", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((u, TODAY, None))
        # ---- Verzeichnisse ----
        for kind, lst, title, intro in (("members", people, s["members"], s["mintro"]), ("companies", orgs, s["companies"], s["cintro"])):
            pk = "u" if kind == "members" else "c"; ru = f"{croot}{kind}/"
            progs = sorted({x["p"] for it in lst for x in it.get("programs", [])})
            fb = f'<button type="button" class="mb-f" data-f="" aria-pressed="true">{esc(s["all"])}</button>' + "".join(f'<button type="button" class="mb-f" data-f="{p_}" aria-pressed="false">{esc(PROG[p_][li])}</button>' for p_ in progs)
            cards = "".join(f'<li class="mb-card" data-p="{" ".join(x["p"] for x in it.get("programs", []))}"><a href="{purl(BASE, lang, pk, it["handle"])}"><b>{esc(it["name"])}</b></a> <span class="mut">{esc(it.get("headline") or it.get("tagline") or "")}</span><br>{tags_of_p(it, li, s)}'
                            + "".join(f'<span class="mb-tag">{esc(ENTS[e["e"]]["name"])}</span>' for e in it.get("expertise", [])[:5] if e["e"] in ENTS) + "</li>" for it in lst) or f'<li class="mb-card mut">{esc(s["none"])}</li>'
            fjs = '<script>(function(){var b=[].slice.call(document.querySelectorAll(".mb-f")),l=[].slice.call(document.querySelectorAll(".mb-card[data-p]"));b.forEach(function(x){x.addEventListener("click",function(){b.forEach(function(y){y.setAttribute("aria-pressed",y===x?"true":"false")});l.forEach(function(i){i.hidden=!!x.dataset.f&&(" "+i.dataset.p+" ").indexOf(" "+x.dataset.f+" ")<0})})})})()</script>'
            feed = f'<h2>{esc(s["feed"])}</h2><div id="pf-feed" data-top="{esc(s["feedtop"])}" data-new="{esc(s["feed"])}"></div>' if kind == "members" else ""
            b = shell(lang, f'<h1>{esc(title)}</h1><p class="mut">{esc(intro)}</p><p><a class="btn main" href="{croot}">{esc(s["join"])}</a></p><div role="group" aria-label="{esc(s["filter"])}">{fb}</div><ul class="mb-list">{cards}</ul>{feed}{fjs}{live_js}{css}')
            ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": ru, "description": intro, "mainEntity": {"@type": "ItemList", "numberOfItems": len(lst), "itemListElement":
                   [{"@type": "ListItem", "position": i + 1, "item": {"@id": f"{purl(BASE, 'en', pk, it['handle'])}#{'person' if pk == 'u' else 'org'}"}} for i, it in enumerate(lst)]}}]
            write(f"{'de/' if lang == 'de' else ''}community/{kind}/index.html", page(lang, f'{title} – M365.FM', intro, ru, b, None, ld, og_type="website", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((ru, TODAY, None))
