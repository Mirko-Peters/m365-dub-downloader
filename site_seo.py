"""SEO-Check-Seite (noindex): On-Page-Pruefung aller Episoden und Community-Inhalte mit denselben Regeln wie der Editor und der MCP (worker/src/seo.js)."""
import json, os, subprocess
from site_learn import esc, LCSS

GRADE = {"green": ("#1a7f37", "sehr gut", "very good"), "good": ("#7a8a00", "gut", "good"), "weak": ("#b36b00", "ausbaufähig", "needs work"), "poor": ("#c62828", "schwach", "weak")}
MARK = {True: "✓", "warn": "⚠", False: "✗", None: "–"}
T = {"en": dict(title="SEO check", intro="On-page check of every episode and community post: title, meta description, header graphic, images, text length, structure, search intent, entities, sources, FAQ and author box. The same rules run in the editor and through the MCP (check_seo).",
                avg="Average score", n="Checked", sort="Lowest score first", fix="Fix", sug="Suggestions", add="Add topics", link="Link mentions", create="Missing entities (heuristic)", ask="Improve it yourself or let your AI do it through the MCP (check_seo, save_blog_post, save_feed_item_text).", none="No open items."),
     "de": dict(title="SEO-Check", intro="On-Page-Prüfung aller Episoden und Community-Beiträge: Titel, Meta-Description, Header-Grafik, Bilder, Textlänge, Struktur, Suchabsicht, Entitäten, Quellen, FAQ und Author-Box. Dieselben Regeln laufen im Editor und über den MCP (check_seo).",
                avg="Durchschnitt", n="Geprüft", sort="Schwächste zuerst", fix="So beheben", sug="Vorschläge", add="Themen ergänzen", link="Erwähnungen verlinken", create="Fehlende Entitäten (Heuristik)", ask="Selbst verbessern oder deine KI über den MCP machen lassen (check_seo, save_blog_post, save_feed_item_text).", none="Nichts offen.")}
CSS = ('<style>.seo-t{display:flex;gap:1.2em;flex-wrap:wrap;margin:1em 0}.seo-t div{border:1px solid var(--bd);border-radius:.5em;padding:.5em 1em}.seo-t b{display:block;font-size:1.6em}'
       '.seo-i{border:1px solid var(--bd);border-radius:.5em;margin:.5em 0;padding:.4em .8em}.seo-i summary{cursor:pointer;display:flex;gap:.8em;align-items:baseline}.seo-s{font-weight:700;min-width:3em}'
       '.seo-c{margin:.2em 0 .2em 1em}.seo-c small{display:block;color:var(--mut)}.seo-k{color:var(--mut);font-size:.85em}</style>')


def author_info(p):
    """Autorendaten fuer den E-E-A-T-Check aus einem oeffentlichen Profil (wie die Author-Box der Seite)."""
    if not p:
        return None
    return {"profile": bool(p.get("handle")), "photo": bool(p.get("img")), "bio": len((p.get("about") or p.get("headline") or "").strip()),
            "expertise": len(p.get("expertise", [])), "channels": len(p.get("channels", [])), "verified": any(x.get("verified") for x in p.get("programs", []))}


def run(extras):
    try:
        out = subprocess.run(["node", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "seo_report.mjs")], input=json.dumps(extras), capture_output=True, text=True, timeout=120, check=True).stdout
        return json.loads(out)
    except Exception as e:
        print("SEO report failed:", e)
        return None


def build(g, people, posts, pods, vids, feed, author, urls):
    BASE, write, page, header, footer, footer_en, LANGS, sitemap = g["BASE"], g["write"], g["page"], g["header"], g["footer"], g["footer_en"], g["LANGS"], g["sitemap"]
    by = {p.get("handle"): p for p in people}
    items = []
    for kind, lst in (("blog", posts), ("podcast", pods), ("video", vids), ("feed", feed)):
        for x in lst:
            if kind == "podcast" and x.get("status") not in (None, "published"):
                continue
            items.append({"kind": kind, "id": x.get("id"), "title": x.get("title", ""), "summary": x.get("summary", ""), "description": x.get("description", ""), "body": x.get("body", ""),
                          "lang": x.get("lang") or "en", "topics": x.get("topics", []), "handle": x.get("handle", ""), "keypoints": x.get("keypoints"), "faq": x.get("faq"),
                          "author": ({**author_info(by.get(x.get("handle"))), "coauthors": len(x.get("coauthors") or x.get("guests") or [])} if by.get(x.get("handle")) else None)})
    rep = run({"author": author, "items": items, "urls": urls})
    if not rep:
        return
    write("seo-report.json", json.dumps(rep, ensure_ascii=False))
    for lang in ("en", "de"):
        t = T[lang]; ru = f"{BASE}/{'de/' if lang == 'de' else ''}seo/"; ix = 1 if lang == "de" else 2
        rows = []
        for it in rep["items"]:
            col, gd, ge = GRADE[it["grade"]]
            cks = "".join(f'<li class="seo-c">{MARK[c["ok"]]} <b>{esc(c["label"][lang])}</b><small>{esc(c["detail"][lang])}</small>' + (f'<small>→ {esc(c["fix"][lang])}</small>' if c["ok"] in (False, "warn") and c["fix"][lang] else "") + "</li>" for c in it["checks"])
            s = it["suggest"]
            sg = "".join(f"<p><b>{esc(lbl)}:</b> {esc(', '.join(vals))}</p>" for lbl, vals in ((t["add"], s["topics"]), (t["link"], s["links"]), (t["create"], s["create"])) if vals)
            name = f'<a href="{esc(it["url"])}">{esc(it["title"])}</a>' if it.get("url") else esc(it["title"])
            rows.append(f'<details class="seo-i"><summary><span class="seo-s" style="color:{col}">{it["score"]}</span><span>{name} <span class="seo-k">· {esc(it["kind"])} · {esc(it["lang"])} · {esc(gd if lang == "de" else ge)}</span></span></summary><ul>{cks}</ul>'
                        + (f'<h4>{esc(t["sug"])}</h4>{sg}' if sg else "") + (f'<p class="seo-k">{esc(t["ask"])}</p>' if it["todo"] else f'<p class="seo-k">{esc(t["none"])}</p>') + "</details>")
        b = (f'{header(lang, "")}<main class="wrap" style="max-width:56em"><h1>{esc(t["title"])}</h1><p>{esc(t["intro"])}</p>'
             f'<div class="seo-t"><div><b>{rep["average"]}</b>{esc(t["avg"])}</div><div><b>{len(rep["items"])}</b>{esc(t["n"])}</div></div><p class="seo-k">{esc(t["sort"])}</p>{"".join(rows)}{CSS}</main>'
             f'{footer(lang) if lang in LANGS else footer_en()}')
        write(f"{'de/' if lang == 'de' else ''}seo/index.html", page(lang, f'{t["title"]} – M365.FM', t["intro"][:155], ru, b, None, None, og_type="website", noindex=True))
