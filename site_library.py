"""Copilot-Bibliothek: Prompts, Anweisungen, KQL/DAX/PowerShell, Flows ... Einzelseiten + Verzeichnis. Eintraege kommen aus /api/library/export (Google-Index ab 10 Upvotes)."""
from datetime import datetime, timezone
from site_i18n import COMM_LANGS, pfx, pfx2, T
from site_learn import ENTS, esc, _fetch_json, LCSS

INDEX_VOTES = 10
KINDS = {  # key: (en, de, code-sprache oder None fuer Text)
    "prompt": ("Prompt", "Prompt", None), "instructions": ("Custom instructions", "Custom Instructions", None), "agent": ("Agent instructions", "Agenten-Anweisung", None),
    "skill": ("Skill", "Skill", None), "plugin": ("Plugin", "Plugin", "JSON"), "manifest": ("Agent manifest", "Agent-Manifest", "JSON"),
    "copilotstudio": ("Copilot Studio topic", "Copilot-Studio-Thema", "YAML"), "flow": ("Power Automate flow", "Power-Automate-Flow", "JSON"),
    "powerapp": ("Power Apps template", "Power-Apps-Vorlage", "Power Fx"), "kql": ("KQL", "KQL", "KQL"), "dax": ("DAX", "DAX", "DAX"),
    "excel": ("Excel formula", "Excel-Formel", "Excel"), "graph": ("Graph query", "Graph-Abfrage", "HTTP"), "powershell": ("PowerShell", "PowerShell", "PowerShell"),
    "adaptivecard": ("Adaptive Card", "Adaptive Card", "JSON"), "other": ("Other", "Sonstiges", None)}


def fetch_items(api):
    return (_fetch_json(f"{api}/api/library/export") or {}).get("items", [])


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def kl(lang, k):
    en, de, _ = KINDS.get(k, KINDS["other"]); return T(lang, en, de)


JS = ('(function(){var A="%API%",b=document.querySelector(".bl-vote");if(!b)return;var id=b.dataset.i;'
      'function f(p,o){o=o||{};o.credentials="include";o.headers=Object.assign({"x-requested-with":"m365"},o.headers||{});return fetch(A+p,o).then(function(r){return r.json()})}'
      'f("/api/library/votes").then(function(d){b.querySelector(".n").textContent=(d.votes||{})[id]||0;if((d.mine||[]).indexOf(+id)>-1)b.setAttribute("aria-pressed","true")}).catch(function(){});'
      'b.addEventListener("click",function(){f("/api/library/vote",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({id:+id})}).then(function(d){if(d.error==="login"){location.href=A.replace("api-","")+"/community/";return}'
      'if(d.ok){b.querySelector(".n").textContent=d.votes;b.setAttribute("aria-pressed",d.voted?"true":"false")}}).catch(function(){})});'
      'var c=document.getElementById("lib-copy");if(c)c.addEventListener("click",function(){var t=document.getElementById("lib-code").textContent;(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){c.textContent=c.dataset.ok}).catch(function(){})})})();')
CSS = ('<style>.bl-vote{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:2em;padding:.25em .8em;background:var(--card);color:inherit}.bl-vote[aria-pressed=true]{border-color:var(--ac)}'
       '.lib-code{white-space:pre-wrap;word-break:break-word;border:1px solid var(--bd);border-radius:.5em;padding:1em;background:var(--card);max-height:32em;overflow:auto}</style>')


def build(g, items, people, api):
    BASE, write, page, header, footer, footer_en, LANGS = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"]
    ctags, sitemap, TODAY = g.get("community_tags"), g["sitemap"], g["TODAY"]
    shell = lambda lang, b: f'{header(lang, "")}<main class="wrap" style="max-width:48em">{b}</main>{footer(lang) if lang in LANGS else footer_en()}'
    pb = {p["handle"]: p for p in people}
    items = [i for i in items if i["handle"] in pb]
    for lang in COMM_LANGS:
        croot = f"{BASE}{pfx(lang)}/community/"; ru = f"{croot}library/"; t0 = T(lang, "Library", "Bibliothek")
        intro = T(lang, "Prompts, agent instructions, KQL, DAX, PowerShell, flows and more – shared by the Microsoft community.", "Prompts, Agenten-Anweisungen, KQL, DAX, PowerShell, Flows und mehr – geteilt von der Microsoft-Community.")
        mine = [i for i in items if i["lang"] == lang]
        if not mine:
            b = shell(lang, f'<h1>{esc(t0)}</h1><p class="mut">{esc(intro)} {esc(T(lang, "Nothing in this language yet – be the first.", "In dieser Sprache gibt es noch nichts – sei die oder der Erste."))}</p><p><a class="btn main" href="{croot}#c-library">{esc(T(lang, "Add an entry", "Eintrag anlegen"))}</a></p>')
            write(f"{pfx2(lang)}community/library/index.html", page(lang, f"{t0} – M365.FM", intro, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=True))
            continue
        links = {i: f"{BASE}{pfx(lang) if lang == 'de' else ''}/entity/{i}/" for i in ENTS}
        for p in mine:
            a = pb[p["handle"]]; au = f"{BASE}/community/u/{a['handle']}/"; u = f"{croot}library/{p['handle']}-{p['slug']}/"
            topics = [t for t in p.get("topics", []) if t in ENTS]
            tl = "".join(f'<a class="mb-tag" href="{links[t]}">{esc(ENTS[t]["name"])}</a> ' for t in topics)
            vote = f'<button type="button" class="bl-vote" data-i="{p["id"]}" aria-pressed="false" aria-label="Upvote">▲ <span class="n">{p.get("votes", 0)}</span></button>'
            b = shell(lang, f'{CSS}<p class="mut"><a href="{ru}">{esc(t0)}</a> · {esc(kl(lang, p["kind"]))}</p><article><h1>{esc(p["title"])}</h1>'
                            f'<p class="mut">{esc(T(lang, "By", "Von"))} <a href="{croot}u/{p["handle"]}/">{esc(a["name"])}</a> · {iso(p["published"])} · {esc(T(lang, "Version", "Version"))} {p.get("version", 1)}</p>'
                            f'{("<p>" + esc(p["summary"]) + "</p>") if p.get("summary") else ""}{("<p><a class=\"btn\" rel=\"nofollow ugc noopener\" target=\"_blank\" href=\"" + esc(p["link"]) + "\">" + esc(T(lang, "Open link", "Link öffnen")) + " ↗</a></p>") if str(p.get("link") or "").startswith("https://") else ""}<pre class="lib-code" id="lib-code">{esc(p["body"])}</pre></article>'
                            f'<p><button type="button" class="btn main" id="lib-copy" data-ok="{esc(T(lang, "Copied", "Kopiert"))}">{esc(T(lang, "Copy", "Kopieren"))}</button> {vote}</p><p>{tl}</p><section id="c-comments"></section>'
                            f'<script>{JS.replace("%API%", api)}</script>' + (ctags(lang, "lib%d" % p["id"]) if ctags else ""))
            lang_code = KINDS.get(p["kind"], KINDS["other"])[2]
            node = {"@type": "SoftwareSourceCode" if lang_code else "CreativeWork", "@id": u + "#item", "name": p["title"], "description": p.get("summary") or "", "inLanguage": lang,
                    "datePublished": iso(p["published"]), "dateModified": iso(p.get("updated") or p["published"]), "version": str(p.get("version", 1)), "text": p["body"][:5000],
                    "author": {"@type": "Person", "@id": au + "#person", "name": a["name"], "url": au}, "about": [{"@id": f"{BASE}/entity/{t}/#thing"} for t in topics]}
            if lang_code: node["programmingLanguage"] = lang_code
            ld = [{"@context": "https://schema.org", **node}]
            noidx = p.get("votes", 0) < INDEX_VOTES
            write(f"{pfx2(lang)}community/library/{p['handle']}-{p['slug']}/index.html", page(lang, f'{p["title"]} – {kl(lang, p["kind"])} | M365.FM', (p.get("summary") or "")[:155], u, b, None, ld, og_type="article", extra_head=LCSS, noindex=noidx))
            if not noidx:
                sitemap.append((u, iso(p.get("updated") or p["published"]), None))
        groups = ""
        for k in KINDS:
            it = sorted([p for p in mine if p["kind"] == k], key=lambda x: (-x.get("votes", 0), -x["published"]))
            if it:
                groups += f'<h2>{esc(kl(lang, k))}</h2><ul style="padding:0;list-style:none">' + "".join(
                    f'<li style="padding:.6em 0;border-bottom:1px solid var(--bd)"><a href="{croot}library/{p["handle"]}-{p["slug"]}/"><b>{esc(p["title"])}</b></a> <span class="mut">· {esc(pb[p["handle"]]["name"])} · ▲ {p.get("votes", 0)}</span>'
                    f'{("<br>" + esc(p["summary"])) if p.get("summary") else ""}</li>' for p in it) + "</ul>"
        noidx = not any(p.get("votes", 0) >= INDEX_VOTES for p in mine)
        b = shell(lang, f'<h1>{esc(t0)}</h1><p class="mut">{esc(intro)}</p><p><a class="btn main" href="{croot}#c-library">{esc(T(lang, "Add an entry", "Eintrag anlegen"))}</a></p>{groups}')
        write(f"{pfx2(lang)}community/library/index.html", page(lang, f"{t0} – M365.FM", intro, ru, b, None, None, og_type="website", extra_head=LCSS, noindex=noidx))
        if not noidx:
            sitemap.append((ru, TODAY, None))
