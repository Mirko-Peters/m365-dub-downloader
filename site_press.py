"""Presskit-Seite (Mirko Peters / M365.FM) – /press/ (en) und /de/press/ plus Downloads in /press/files/."""
import html, json, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).parent
E = lambda s: html.escape(s or "", quote=True)

COLORS = [("Accent", "#3B6391", "#82A7D4"), ("Background", "#F3F3F2", "#101214"), ("Text", "#17191C", "#E9ECEF"), ("Muted", "#5D6470", "#98A0AB"), ("Card", "#FFFFFF", "#16191C")]

TXT = {
 "en": dict(
  title="Press kit – Mirko Peters, Microsoft MVP & M365.FM", meta="Press kit for Mirko Peters, Microsoft MVP, host of the M365.FM podcast and organizer of M365Con: bio, facts, photo, logo, colors, downloads and contact.",
  h1="Press kit", tag="Mirko Peters · M365.FM · M365Con",
  nav=["About", "Media", "Files", "Colors", "Team", "Contact", "Press"],
  about="About", about_p="Mirko Peters is a Microsoft MVP, podcaster, author and conference organizer focused on Microsoft 365, Microsoft Copilot, Azure and AI agents. He hosts the podcast M365.FM and the m365 Show on YouTube, publishes the animated explainer series Sticky Man Explained, and organizes the free online conference M365Con. His content is aimed at IT admins, architects, developers and decision makers who want to understand the Microsoft cloud without marketing noise.",
  facts="Key facts", f=[("Name", "Mirko Peters"), ("Role", "Microsoft MVP, host of M365.FM, organizer of M365Con"), ("Focus", "Microsoft 365, Copilot, Azure, Power Platform, security, AI agents"),
                       ("Podcast", "M365.FM – in German plus AI-dubbed editions in {L} languages"), ("Episodes on dub.m365.fm", "{N}"), ("M365Con 2027", "Free, 100% online · Jan 11–22, 2027 · 120 sessions"), ("Based in", "Stuttgart, Germany")],
  topics="Topics for interviews and talks", topics_l=["Microsoft 365 Copilot adoption and governance", "AI agents and Copilot Studio", "Security, identity and compliance in Microsoft 365", "Power Platform and Dynamics 365", "Microsoft Fabric and data", "Building a multilingual podcast and SEO/GEO strategy with AI"],
  media="Media", media_p="Photo and logo for editorial use. Please credit “Mirko Peters / M365.FM”.", portrait="Portrait", logo="Logo / icon", og="Social preview image",
  files="Files", files_p="Everything in one place – free to use for coverage of Mirko Peters, M365.FM and M365Con.", zip="Download everything (ZIP)",
  fl=[("mirko-peters-bio-en.txt", "Short bio (English)"), ("mirko-peters-bio-de.txt", "Kurzbiografie (Deutsch)"), ("fact-sheet-en.txt", "Fact sheet (English)"), ("mirko-peters-800.jpg", "Portrait (JPG, 800×800)"), ("mirko-peters.jpg", "Portrait (JPG)"), ("logo.svg", "Logo (SVG)"), ("logo-192.png", "Logo (PNG)"), ("og-default.png", "Social preview image (PNG)"), ("colors.txt", "Brand colors")],
  colors="Colors", colors_p="Brand colors of the M365.FM dub site, light and dark mode. Click a value to copy it.", light="Light", dark="Dark", fonts="Fonts: Barlow Condensed (headings) and Barlow (text).", copied="Copied",
  team="Team", team_p="Mirko Peters is the host, author and organizer behind all projects. For M365Con, speakers and partners are listed on m365con.net.",
  contact="Contact", contact_p="For interviews, speaking requests, partnerships and press inquiries:", addr="Address",
  press="Press & links", press_l=[("M365Con 2027 – free online conference, Jan 11–22, 2027", "https://m365con.net"), ("M365.FM – the podcast and episode archive", "https://www.m365.fm"), ("About Mirko Peters", "{ABOUT}"), ("Microsoft MVP profile", "{MVP}"), ("LinkedIn", "{LIN}"), ("m365 Show on YouTube", "{YT}")],
  machine="Machine-readable summaries for journalists and AI assistants:", usage="Usage: editorial use with credit.", ),
 "de": dict(
  title="Pressekit – Mirko Peters, Microsoft MVP & M365.FM", meta="Pressekit für Mirko Peters, Microsoft MVP, Host des Podcasts M365.FM und Veranstalter der M365Con: Biografie, Fakten, Foto, Logo, Farben, Downloads und Kontakt.",
  h1="Pressekit", tag="Mirko Peters · M365.FM · M365Con",
  nav=["Über", "Medien", "Dateien", "Farben", "Team", "Kontakt", "Presse"],
  about="Über", about_p="Mirko Peters ist Microsoft MVP, Podcaster, Autor und Konferenzveranstalter mit Schwerpunkt auf Microsoft 365, Microsoft Copilot, Azure und KI-Agenten. Er hostet den Podcast M365.FM und die m365 Show auf YouTube, veröffentlicht die animierte Erklärreihe Sticky Man Explained und organisiert die kostenlose Online-Konferenz M365Con. Seine Inhalte richten sich an IT-Admins, Architekten, Entwickler und Entscheider, die die Microsoft-Cloud ohne Marketing-Rauschen verstehen wollen.",
  facts="Fakten", f=[("Name", "Mirko Peters"), ("Rolle", "Microsoft MVP, Host von M365.FM, Veranstalter der M365Con"), ("Schwerpunkt", "Microsoft 365, Copilot, Azure, Power Platform, Sicherheit, KI-Agenten"),
                    ("Podcast", "M365.FM – auf Deutsch plus KI-vertonte Ausgaben in {L} Sprachen"), ("Folgen auf dub.m365.fm", "{N}"), ("M365Con 2027", "Kostenlos, 100 % online · 11.–22. Januar 2027 · 120 Sessions"), ("Sitz", "Stuttgart, Deutschland")],
  topics="Themen für Interviews und Vorträge", topics_l=["Einführung und Governance von Microsoft 365 Copilot", "KI-Agenten und Copilot Studio", "Sicherheit, Identität und Compliance in Microsoft 365", "Power Platform und Dynamics 365", "Microsoft Fabric und Daten", "Mehrsprachiger Podcast und SEO/GEO-Strategie mit KI"],
  media="Medien", media_p="Foto und Logo zur redaktionellen Nutzung. Bitte nennen: „Mirko Peters / M365.FM“.", portrait="Porträt", logo="Logo / Icon", og="Social-Preview-Bild",
  files="Dateien", files_p="Alles an einem Ort – frei nutzbar für die Berichterstattung über Mirko Peters, M365.FM und M365Con.", zip="Alles herunterladen (ZIP)",
  fl=[("mirko-peters-bio-en.txt", "Short bio (English)"), ("mirko-peters-bio-de.txt", "Kurzbiografie (Deutsch)"), ("fact-sheet-en.txt", "Fact sheet (English)"), ("mirko-peters-800.jpg", "Porträt (JPG, 800×800)"), ("mirko-peters.jpg", "Porträt (JPG)"), ("logo.svg", "Logo (SVG)"), ("logo-192.png", "Logo (PNG)"), ("og-default.png", "Social-Preview-Bild (PNG)"), ("colors.txt", "Markenfarben")],
  colors="Farben", colors_p="Markenfarben der M365.FM-Dub-Seite, heller und dunkler Modus. Wert anklicken zum Kopieren.", light="Hell", dark="Dunkel", fonts="Schriften: Barlow Condensed (Überschriften) und Barlow (Text).", copied="Kopiert",
  team="Team", team_p="Mirko Peters ist Host, Autor und Veranstalter hinter allen Projekten. Für die M365Con sind Speaker und Partner auf m365con.net aufgeführt.",
  contact="Kontakt", contact_p="Für Interviews, Vortragsanfragen, Kooperationen und Presseanfragen:", addr="Adresse",
  press="Presse & Links", press_l=[("M365Con 2027 – kostenlose Online-Konferenz, 11.–22. Januar 2027", "https://m365con.net"), ("M365.FM – der Podcast und das Folgenarchiv", "https://www.m365.fm"), ("Über Mirko Peters", "{ABOUT}"), ("Microsoft-MVP-Profil", "{MVP}"), ("LinkedIn", "{LIN}"), ("m365 Show auf YouTube", "{YT}")],
  machine="Maschinenlesbare Zusammenfassungen für Journalisten und KI-Assistenten:", usage="Nutzung: redaktionell, mit Quellenangabe."),
}

CSS = """<style>
.pk{max-width:62em}.pk nav.kpn{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--bd);display:flex;gap:.2em 1.2em;flex-wrap:wrap;padding:.2em 0;margin:1em 0 0}
.pk nav.kpn a{color:var(--fg)!important;display:inline-block;padding:.55em .5em;min-height:24px;text-decoration:none;font:600 .85rem "Barlow Condensed",sans-serif;letter-spacing:.12em;text-transform:uppercase}.pk nav.kpn a:hover,.pk nav.kpn a:focus-visible{color:var(--ac)}
.pk section{padding:2.2em 0 .4em;border-bottom:1px solid var(--bd)}.pk h2{margin:0 0 .6em}
.pk .kfacts{display:grid;grid-template-columns:max-content 1fr;gap:.5em 1.4em;margin:1em 0}.pk .kfacts dt{color:var(--mut);font-weight:600}.pk .kfacts dd{margin:0}
.pk .kg{display:grid;grid-template-columns:repeat(auto-fit,minmax(14em,1fr));gap:1em;margin:1em 0}.pk .ktile{border:1px solid var(--bd);border-radius:.8em;background:var(--card);padding:1em;text-align:center}
.pk .ktile img{max-width:100%;height:auto;border-radius:.5em}.pk .ktile small{display:block;color:var(--mut);margin-top:.5em}
.pk .kfl{list-style:none;padding:0;margin:1em 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(16em,1fr));gap:.6em}.pk .kfl a{display:block;border:1px solid var(--bd);background:var(--card);border-radius:.6em;padding:.7em .9em;color:var(--fg);text-decoration:none;font-weight:600}
.pk .kfl a:hover,.pk .kfl a:focus-visible{border-color:var(--ac)}.pk .kfl small{display:block;color:var(--mut);font-weight:400}
.pk .ksw{display:grid;grid-template-columns:repeat(auto-fit,minmax(11em,1fr));gap:.8em}.pk .ksw button{font:inherit;cursor:pointer;border:1px solid var(--bd);border-radius:.6em;padding:0;overflow:hidden;background:var(--card);color:var(--fg);text-align:start}
.pk .ksw i{display:block;height:3.4em}.pk .ksw span{display:block;padding:.45em .7em}.pk .ksw b{display:block}.pk .ksw small{color:var(--mut)}
.pk .kcta{display:inline-block;background:var(--ac);color:var(--onac);padding:.6em 1.1em;border-radius:.5em;text-decoration:none;font-weight:700}
.pk ul.kpl{padding-left:1.2em}
</style>"""

JS = """<script>document.querySelectorAll('.pk .ksw button').forEach(function(b){b.addEventListener('click',function(){var v=b.dataset.v,s=b.querySelector('small'),o=s.textContent;
if(navigator.clipboard)navigator.clipboard.writeText(v).then(function(){s.textContent=b.dataset.ok;setTimeout(function(){s.textContent=o},1500)})})});</script>"""


def build_press(g):
    BASE, write, page, sitemap, TODAY = g["BASE"], g["write"], g["page"], g["sitemap"], g["TODAY"]
    N, L = g["n_eps"], g["n_langs"]
    out = ROOT / "docs" / "press" / "files"
    out.mkdir(parents=True, exist_ok=True)
    A = ROOT / "assets"
    for src, dst in (("mirko-peters.jpg", "mirko-peters.jpg"), ("mirko-peters-800.jpg", "mirko-peters-800.jpg"), ("favicon.svg", "logo.svg"), ("favicon-192.png", "logo-192.png"), ("og-default.png", "og-default.png")):
        if (A / src).exists():
            shutil.copy(A / src, out / dst)
    en, de = TXT["en"], TXT["de"]
    facts_en = "\n".join(f"{k}: {v.replace('{L}', str(L)).replace('{N}', str(N))}" for k, v in en["f"])
    (out / "mirko-peters-bio-en.txt").write_text(f"Mirko Peters\n\n{en['about_p']}\n\nWebsite: {BASE}/about/mirko-peters/\nContact: {g['EMAIL']}\n", "utf-8")
    (out / "mirko-peters-bio-de.txt").write_text(f"Mirko Peters\n\n{de['about_p']}\n\nWebseite: {BASE}/de/about/mirko-peters/\nKontakt: {g['EMAIL']}\n", "utf-8")
    (out / "fact-sheet-en.txt").write_text(f"M365.FM / Mirko Peters – fact sheet\n\n{facts_en}\n\nContact: {g['EMAIL']}\nPress kit: {BASE}/press/\n", "utf-8")
    (out / "colors.txt").write_text("M365.FM brand colors (light / dark)\n" + "\n".join(f"{n}: {a} / {b}" for n, a, b in COLORS) + "\nFonts: Barlow Condensed, Barlow\n", "utf-8")
    names = ["mirko-peters-bio-en.txt", "mirko-peters-bio-de.txt", "fact-sheet-en.txt", "colors.txt", "mirko-peters.jpg", "mirko-peters-800.jpg", "logo.svg", "logo-192.png", "og-default.png"]
    with zipfile.ZipFile(out / "m365fm-presskit.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            if (out / n).exists():
                z.write(out / n, n)
    for lang in ("en", "de"):
        t = TXT[lang]
        url = f"{BASE}/press/" if lang == "en" else f"{BASE}/de/press/"
        about_url = f"{BASE}/about/mirko-peters/" if lang == "en" else f"{BASE}/de/about/mirko-peters/"
        ids = ["about", "media", "files", "colors", "team", "contact", "press"]
        nav = "".join(f'<a href="#{i}">{E(n)}</a>' for i, n in zip(ids, t["nav"]))
        facts = "".join(f'<dt>{E(k)}</dt><dd>{E(v.replace("{L}", str(L)).replace("{N}", str(N)))}</dd>' for k, v in t["f"])
        topics = "".join(f"<li>{E(x)}</li>" for x in t["topics_l"])
        base_files = f"{BASE}/press/files/"
        media = (f'<div class="kg"><figure class="ktile"><img src="{base_files}mirko-peters-800.jpg" width="200" height="200" alt="Mirko Peters, Microsoft MVP, host of M365.FM" loading="lazy"><small>{E(t["portrait"])}</small></figure>'
                 f'<figure class="ktile"><img src="{base_files}logo-192.png" width="96" height="96" alt="M365.FM logo" loading="lazy"><small>{E(t["logo"])}</small></figure>'
                 f'<figure class="ktile"><img src="{base_files}og-default.png" width="300" height="158" alt="M365.FM" loading="lazy"><small>{E(t["og"])}</small></figure></div>')
        files = "".join(f'<li><a href="{base_files}{f}" download>{E(lbl)}<small>{E(f)}</small></a></li>' for f, lbl in t["fl"])
        sw = "".join(f'<button type="button" data-v="{a}" data-ok="{E(t["copied"])}"><i style="background:{a}"></i><span><b>{E(n)} · {E(t["light"])}</b><small>{a}</small></span></button>'
                     f'<button type="button" data-v="{b}" data-ok="{E(t["copied"])}"><i style="background:{b}"></i><span><b>{E(n)} · {E(t["dark"])}</b><small>{b}</small></span></button>' for n, a, b in COLORS)
        sub = {"{ABOUT}": about_url, "{MVP}": g["MVP"], "{LIN}": g["LINKEDIN"], "{YT}": g["YT"]}
        pl = "".join(f'<li><a href="{sub.get(u, u)}"{" rel=\"me\"" if u in ("{MVP}", "{LIN}") else ""}>{E(n)}</a></li>' for n, u in t["press_l"])
        body = (f'{g["header"](lang, "")}<main class="wrap pk" id="main"><p class="kicker" style="color:var(--mut)">{E(t["tag"])}</p><h1>{E(t["h1"])}</h1><nav class="kpn" aria-label="{E(t["h1"])}">{nav}</nav>'
                f'<section id="about"><h2>{E(t["about"])}</h2><p style="font-size:1.1em;max-width:46em">{E(t["about_p"])}</p><h3>{E(t["facts"])}</h3><dl class="kfacts">{facts}</dl><h3>{E(t["topics"])}</h3><ul class="kpl">{topics}</ul></section>'
                f'<section id="media"><h2>{E(t["media"])}</h2><p>{E(t["media_p"])}</p>{media}</section>'
                f'<section id="files"><h2>{E(t["files"])}</h2><p>{E(t["files_p"])}</p><p><a class="kcta" href="{base_files}m365fm-presskit.zip" download>{E(t["zip"])}</a></p><ul class="kfl">{files}</ul></section>'
                f'<section id="colors"><h2>{E(t["colors"])}</h2><p>{E(t["colors_p"])}</p><div class="ksw">{sw}</div><p class="mut">{E(t["fonts"])}</p></section>'
                f'<section id="team"><h2>{E(t["team"])}</h2><div class="kg"><figure class="ktile"><img src="{base_files}mirko-peters.jpg" width="120" height="120" alt="Mirko Peters" loading="lazy"><small><b>Mirko Peters</b><br>Microsoft MVP · Host M365.FM</small></figure></div><p>{E(t["team_p"])}</p></section>'
                f'<section id="contact"><h2>{E(t["contact"])}</h2><p>{E(t["contact_p"])}</p><p><a class="kcta" href="mailto:{g["EMAIL"]}">{g["EMAIL"]}</a></p><p class="mut">{E(t["addr"])}: Julius-Hölder-Str 60, 70597 Stuttgart, Germany</p></section>'
                f'<section id="press"><h2>{E(t["press"])}</h2><ul class="kpl">{pl}</ul><p>{E(t["machine"])} <a href="{BASE}/llms.txt">llms.txt</a> · <a href="{BASE}/episodes.json">episodes.json</a></p><p class="mut">{E(t["usage"])}</p></section></main>'
                f'{g["footer"](lang) if lang in g["LANGS"] else g["footer_en"]()}{JS}')
        ld = [g["person_ld"](), g["org_ld"](), {"@context": "https://schema.org", "@type": "WebPage", "@id": f"{url}#page", "url": url, "name": t["title"], "inLanguage": lang, "about": {"@id": f"{BASE}/about/mirko-peters/#person"}, "dateModified": TODAY}]
        write("press/index.html" if lang == "en" else "de/press/index.html", page(lang, t["title"], t["meta"], url, body, None, ld, og_type="website", extra_head=CSS))
        sitemap.append((url, TODAY, None))
