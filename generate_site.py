#!/usr/bin/env python3
"""Erzeugt die mehrsprachige SEO-Website (docs/) aus episodes/*.json + data/published.json.

Nur Python-Standardbibliothek. Lauf:  python generate_site.py
Basis-URL (z. B. eigene Domain):  SITE_BASE=https://international.m365.fm python generate_site.py
"""
import html, json, os, re, shutil, sys, unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
BASE = os.environ.get("SITE_BASE", "https://mirko-peters.github.io/m365-dub-downloader").rstrip("/")
TODAY = date.today().isoformat()
INDEXNOW_KEY = "c1d5e8a7b3f94a6e8d2b7f0a9c4e6b13"

YT_CHANNEL = "https://www.youtube.com/channel/UCIdo4tN3khKldHP3733E9JA"
LINKEDIN = "https://www.linkedin.com/in/m365showpodcast/"
SAME_AS = [LINKEDIN, "https://www.m365.fm", "https://m365con.net", YT_CHANNEL]

# lang: (Eigenname, hreflang, dir, Spreaker-Show-ID, OpenGraph-Locale)
LANGS = {
    "de": ("Deutsch", "de", "ltr", 7393187, "de_DE"), "es": ("Español", "es", "ltr", 7393248, "es_ES"),
    "fr": ("Français", "fr", "ltr", 7393223, "fr_FR"), "it": ("Italiano", "it", "ltr", 7393231, "it_IT"),
    "pt": ("Português", "pt", "ltr", 7393243, "pt_BR"), "nl": ("Nederlands", "nl", "ltr", 7393222, "nl_NL"),
    "pl": ("Polski", "pl", "ltr", 7393242, "pl_PL"), "id": ("Bahasa Indonesia", "id", "ltr", 7393230, "id_ID"),
    "ru": ("Русский", "ru", "ltr", 7393247, "ru_RU"), "uk": ("Українська", "uk", "ltr", 7393254, "uk_UA"),
    "ar": ("العربية", "ar", "rtl", 7393221, "ar_AR"), "he": ("עברית", "he", "rtl", 7393227, "he_IL"),
    "hi": ("हिन्दी", "hi", "ltr", 7393228, "hi_IN"), "ja": ("日本語", "ja", "ltr", 7393232, "ja_JP"),
    "ko": ("한국어", "ko", "ltr", 7393236, "ko_KR"), "ml": ("മലയാളം", "ml", "ltr", 7393238, "ml_IN"),
    "pa": ("ਪੰਜਾਬੀ", "pa", "ltr", 7393244, "pa_IN"), "ta": ("தமிழ்", "ta", "ltr", 7393250, "ta_IN"),
    "te": ("తెలుగు", "te", "ltr", 7393253, "te_IN"),
}

# UI-Texte je Sprache: listen, watch, transcript, all, more, about, bio, home
UI = {
 "de": ("Jetzt anhören", "Video auf YouTube ansehen", "Transkript lesen", "Alle Folgen", "Weitere Folgen", "Über Mirko Peters",
        "Mirko Peters ist Microsoft MVP, Host des Podcasts M365.FM und Initiator der kostenlosen Online-Konferenz M365Con.", "Startseite"),
 "es": ("Escuchar ahora", "Ver el vídeo en YouTube", "Leer la transcripción", "Todos los episodios", "Más episodios", "Sobre Mirko Peters",
        "Mirko Peters es Microsoft MVP, presentador del podcast M365.FM e impulsor de la conferencia online gratuita M365Con.", "Inicio"),
 "fr": ("Écouter maintenant", "Voir la vidéo sur YouTube", "Lire la transcription", "Tous les épisodes", "Autres épisodes", "À propos de Mirko Peters",
        "Mirko Peters est Microsoft MVP, animateur du podcast M365.FM et initiateur de la conférence en ligne gratuite M365Con.", "Accueil"),
 "it": ("Ascolta ora", "Guarda il video su YouTube", "Leggi la trascrizione", "Tutti gli episodi", "Altri episodi", "Su Mirko Peters",
        "Mirko Peters è Microsoft MVP, conduttore del podcast M365.FM e promotore della conferenza online gratuita M365Con.", "Home"),
 "pt": ("Ouvir agora", "Assistir ao vídeo no YouTube", "Ler a transcrição", "Todos os episódios", "Mais episódios", "Sobre Mirko Peters",
        "Mirko Peters é Microsoft MVP, apresentador do podcast M365.FM e idealizador da conferência online gratuita M365Con.", "Início"),
 "nl": ("Nu luisteren", "Video bekijken op YouTube", "Transcript lezen", "Alle afleveringen", "Meer afleveringen", "Over Mirko Peters",
        "Mirko Peters is Microsoft MVP, host van de podcast M365.FM en initiatiefnemer van de gratis online conferentie M365Con.", "Home"),
 "pl": ("Posłuchaj teraz", "Obejrzyj wideo na YouTube", "Czytaj transkrypcję", "Wszystkie odcinki", "Więcej odcinków", "O Mirko Petersie",
        "Mirko Peters jest Microsoft MVP, gospodarzem podcastu M365.FM i inicjatorem bezpłatnej konferencji online M365Con.", "Strona główna"),
 "id": ("Dengarkan sekarang", "Tonton video di YouTube", "Baca transkrip", "Semua episode", "Episode lainnya", "Tentang Mirko Peters",
        "Mirko Peters adalah Microsoft MVP, pembawa podcast M365.FM, dan penggagas konferensi online gratis M365Con.", "Beranda"),
 "ru": ("Слушать", "Смотреть видео на YouTube", "Читать расшифровку", "Все выпуски", "Другие выпуски", "О Mirko Peters",
        "Mirko Peters — Microsoft MVP, ведущий подкаста M365.FM и инициатор бесплатной онлайн-конференции M365Con.", "Главная"),
 "uk": ("Слухати", "Дивитися відео на YouTube", "Читати розшифровку", "Усі випуски", "Інші випуски", "Про Mirko Peters",
        "Mirko Peters — Microsoft MVP, ведучий подкасту M365.FM та ініціатор безкоштовної онлайн-конференції M365Con.", "Головна"),
 "ar": ("استمع الآن", "شاهد الفيديو على YouTube", "اقرأ النص المفرّغ", "كل الحلقات", "حلقات أخرى", "عن Mirko Peters",
        "Mirko Peters خبير Microsoft MVP ومقدّم بودكاست M365.FM ومُطلق مؤتمر M365Con المجاني عبر الإنترنت.", "الرئيسية"),
 "he": ("האזינו עכשיו", "צפו בסרטון ב-YouTube", "קראו את התמלול", "כל הפרקים", "פרקים נוספים", "על Mirko Peters",
        "Mirko Peters הוא Microsoft MVP, מנחה הפודקאסט M365.FM ויוזם הכנס המקוון והחינמי M365Con.", "דף הבית"),
 "hi": ("अभी सुनें", "YouTube पर वीडियो देखें", "ट्रांसक्रिप्ट पढ़ें", "सभी एपिसोड", "और एपिसोड", "Mirko Peters के बारे में",
        "Mirko Peters Microsoft MVP, पॉडकास्ट M365.FM के होस्ट और निःशुल्क ऑनलाइन कॉन्फ़्रेंस M365Con के आयोजक हैं।", "होम"),
 "ja": ("今すぐ聴く", "YouTube で動画を見る", "文字起こしを読む", "すべてのエピソード", "他のエピソード", "Mirko Peters について",
        "Mirko Peters は Microsoft MVP であり、ポッドキャスト M365.FM のホスト、無料オンライン カンファレンス M365Con の主催者です。", "ホーム"),
 "ko": ("지금 듣기", "YouTube에서 영상 보기", "대본 읽기", "모든 에피소드", "다른 에피소드", "Mirko Peters 소개",
        "Mirko Peters는 Microsoft MVP이자 팟캐스트 M365.FM의 진행자이며 무료 온라인 컨퍼런스 M365Con의 주최자입니다.", "홈"),
 "ml": ("ഇപ്പോൾ കേൾക്കൂ", "YouTube-ൽ വീഡിയോ കാണൂ", "ട്രാൻസ്ക്രിപ്റ്റ് വായിക്കൂ", "എല്ലാ എപ്പിസോഡുകളും", "കൂടുതൽ എപ്പിസോഡുകൾ", "Mirko Peters നെക്കുറിച്ച്",
        "Mirko Peters ഒരു Microsoft MVP ആണ്; M365.FM പോഡ്കാസ്റ്റിന്റെ ഹോസ്റ്റും സൗജന്യ ഓൺലൈൻ കോൺഫറൻസ് M365Con-ന്റെ സംഘാടകനും.", "ഹോം"),
 "pa": ("ਹੁਣੇ ਸੁਣੋ", "YouTube 'ਤੇ ਵੀਡੀਓ ਦੇਖੋ", "ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ ਪੜ੍ਹੋ", "ਸਾਰੇ ਐਪੀਸੋਡ", "ਹੋਰ ਐਪੀਸੋਡ", "Mirko Peters ਬਾਰੇ",
        "Mirko Peters Microsoft MVP, ਪੌਡਕਾਸਟ M365.FM ਦੇ ਹੋਸਟ ਅਤੇ ਮੁਫ਼ਤ ਆਨਲਾਈਨ ਕਾਨਫ਼ਰੰਸ M365Con ਦੇ ਪ੍ਰਬੰਧਕ ਹਨ।", "ਮੁੱਖ ਪੰਨਾ"),
 "ta": ("இப்போது கேளுங்கள்", "YouTube-இல் வீடியோவைப் பாருங்கள்", "எழுத்துப்படியைப் படியுங்கள்", "அனைத்து எபிசோட்களும்", "மேலும் எபிசோட்கள்", "Mirko Peters பற்றி",
        "Mirko Peters ஒரு Microsoft MVP; M365.FM பாட்காஸ்ட்டின் தொகுப்பாளர் மற்றும் இலவச ஆன்லைன் மாநாடு M365Con-ஐ நடத்துபவர்.", "முகப்பு"),
 "te": ("ఇప్పుడే వినండి", "YouTube లో వీడియో చూడండి", "ట్రాన్స్క్రిప్ట్ చదవండి", "అన్ని ఎపిసోడ్‌లు", "మరిన్ని ఎపిసోడ్‌లు", "Mirko Peters గురించి",
        "Mirko Peters ఒక Microsoft MVP; M365.FM పాడ్‌కాస్ట్ హోస్ట్, ఉచిత ఆన్‌లైన్ కాన్ఫరెన్స్ M365Con నిర్వాహకుడు.", "హోమ్"),
}

CSS = """:root{--bg:#fff;--fg:#14202b;--mut:#5a6b7b;--ac:#0b6bcb;--card:#f4f7fa;--bd:#dbe3ea}
@media (prefers-color-scheme:dark){:root{--bg:#0f1720;--fg:#e8eef4;--mut:#9fb0c0;--ac:#6cb2ff;--card:#17222d;--bd:#26364a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.65 system-ui,-apple-system,Segoe UI,Roboto,Noto Sans,sans-serif}
a{color:var(--ac)}header,main,footer{max-width:820px;margin:0 auto;padding:16px}
header{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;border-bottom:1px solid var(--bd)}
header .brand{font-weight:700;text-decoration:none;color:var(--fg)}nav.langs{display:flex;flex-wrap:wrap;gap:6px 10px;font-size:14px}
h1{font-size:1.75rem;line-height:1.25;margin:.6em 0 .4em}h2{font-size:1.2rem;margin-top:1.6em}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 16px;margin:12px 0}
.card h2,.card h3{margin:.1em 0 .3em;font-size:1.05rem}.card p{margin:.2em 0;color:var(--mut);font-size:.95rem}
.btn{display:inline-block;margin:6px 8px 6px 0;padding:9px 16px;border-radius:999px;background:var(--ac);color:#fff;text-decoration:none;font-weight:600;font-size:.95rem}
.btn.alt{background:transparent;color:var(--ac);border:1px solid var(--ac)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}
.grid a{display:block;padding:12px;border:1px solid var(--bd);border-radius:10px;text-decoration:none;background:var(--card)}
iframe{width:100%;border:0;border-radius:12px}.mut{color:var(--mut);font-size:.9rem}footer{border-top:1px solid var(--bd);margin-top:32px;font-size:.9rem;color:var(--mut)}
ul{padding-inline-start:1.2em}li{margin:.35em 0}"""


def esc(s): return html.escape(s or "", quote=True)


def ascii_slug(t, vid):
    s = unicodedata.normalize("NFKD", t)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\(.*?\)|（.*?）", "", s)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    if len(s) > 70:
        s = s[:70].rsplit("-", 1)[0]
    return s.rstrip("-") if len(s) >= 15 else ""


def parse_desc(desc):
    ps = re.findall(r"<p>(.*?)</p>", desc, re.S)
    ul = re.search(r"<ul>(.*?)</ul>", desc, re.S)
    bullets = re.findall(r"<li>(.*?)</li>", ul.group(1), re.S) if ul else []
    hdr = re.search(r"<strong>(.*?)</strong>", desc)
    intro = ps[0] if ps else ""
    aud = ps[3] if len(ps) > 3 else ""
    return intro, (hdr.group(1) if hdr else ""), bullets, aud


def strip_tags(s): return re.sub(r"<[^>]+>", "", s)


def short(s, n=158):
    s = strip_tags(s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def load():
    eps = {}
    for p in sorted((ROOT / "episodes").glob("*.json")):
        eps[p.stem] = json.load(open(p, encoding="utf-8"))
    pub = {}
    pp = ROOT / "data" / "published.json"
    if pp.exists():
        pub = json.load(open(pp, encoding="utf-8"))
    seo = json.load(open(ROOT / "shows_seo.json", encoding="utf-8"))
    return eps, pub, seo


def lang_switch(cur, alt_urls, home_langs):
    items = []
    for l in home_langs:
        name = LANGS[l][0]
        url = alt_urls.get(l) or f"{BASE}/{l}/"
        cls = ' aria-current="page"' if l == cur else ""
        items.append(f'<a href="{url}" hreflang="{LANGS[l][1]}" lang="{LANGS[l][1]}"{cls}>{esc(name)}</a>')
    return '<nav class="langs" aria-label="Languages">' + " · ".join(items) + "</nav>"


def page(lang, title, desc, canonical, body, alternates=None, jsonld=None, xdefault=None, og_type="article", extra_head=""):
    hl = LANGS[lang][1] if lang in LANGS else "en"
    d = LANGS[lang][2] if lang in LANGS else "ltr"
    loc = LANGS[lang][4] if lang in LANGS else "en_US"
    alt = ""
    if alternates:
        for l, u in alternates.items():
            alt += f'<link rel="alternate" hreflang="{LANGS[l][1]}" href="{u}">\n'
        alt += f'<link rel="alternate" hreflang="x-default" href="{xdefault or BASE + "/"}">\n'
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>\n' for j in (jsonld or []))
    return f"""<!doctype html>
<html lang="{hl}" dir="{d}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Mirko Peters">
<link rel="canonical" href="{canonical}">
{alt}<meta property="og:type" content="{og_type}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:locale" content="{loc}"><meta property="og:site_name" content="M365.FM">
<meta name="twitter:card" content="summary">
{extra_head}<style>{CSS}</style>
{ld}</head>
<body>
{body}
</body></html>
"""


def person_ld():
    return {"@context": "https://schema.org", "@type": "Person", "@id": f"{BASE}/about/mirko-peters/#person",
            "name": "Mirko Peters", "jobTitle": "Microsoft MVP", "url": f"{BASE}/about/mirko-peters/",
            "sameAs": SAME_AS, "knowsAbout": ["Microsoft 365", "Microsoft Copilot", "Azure", "Power Platform", "Microsoft Fabric", "AI agents"],
            "worksFor": {"@type": "Organization", "name": "M365.FM", "url": "https://www.m365.fm"}}


def header(lang, switch):
    ui = UI.get(lang)
    home = f"{BASE}/{lang}/" if lang in LANGS else f"{BASE}/"
    return f'<header><a class="brand" href="{home}">M365.FM · Mirko Peters</a>{switch}</header>'


def footer(lang):
    ui = UI[lang] if lang in UI else None
    about = ui[5] if ui else "About Mirko Peters"
    return (f'<footer><a href="{BASE}/about/mirko-peters/">{esc(about)}</a> · <a href="https://www.m365.fm">m365.fm</a> · '
            f'<a href="https://m365con.net">M365Con</a> · <a href="{LINKEDIN}" rel="me">LinkedIn</a> · '
            f'<a href="{YT_CHANNEL}">YouTube</a></footer>')


def build():
    eps, pub, seo = load()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / ".nojekyll").write_text("")

    # veröffentlichte Folgen je Sprache sammeln
    items = {}  # (vid, lang) -> dict
    for vid, langs in eps.items():
        for l, e in langs.items():
            if l not in LANGS:
                continue
            p = pub.get(f"{vid}:{l}") or pub.get(f"{vid}:{l}-pub")
            if not p:
                continue
            slug = ascii_slug(e["title"], vid) or vid.lower().replace("_", "-")
            items[(vid, l)] = dict(vid=vid, lang=l, e=e, eid=p["episode_id"], slug=slug, date=(p.get("at") or TODAY)[:10])
    # Slug-Kollisionen je Sprache auflösen
    seen = {}
    for k, it in items.items():
        key = (it["lang"], it["slug"])
        if key in seen:
            it["slug"] = f'{it["slug"]}-{it["vid"].lower()[:6]}'
        seen[(it["lang"], it["slug"])] = 1

    by_vid = {}
    for (vid, l), it in items.items():
        by_vid.setdefault(vid, {})[l] = it
    by_lang = {}
    for (vid, l), it in items.items():
        by_lang.setdefault(l, []).append(it)
    for l in by_lang:
        by_lang[l].sort(key=lambda i: (i["date"], i["vid"]), reverse=True)
    active = [l for l in LANGS if l in by_lang]

    sitemap = []  # (url, lastmod, alternates)

    def url_of(it): return f'{BASE}/{it["lang"]}/{it["slug"]}/'

    def write(rel, content):
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # Episoden-Seiten
    for (vid, l), it in items.items():
        e = it["e"]; ui = UI[l]
        intro, hdr, bullets, aud = parse_desc(e["desc"])
        alts = {x: url_of(by_vid[vid][x]) for x in by_vid[vid]}
        canonical = url_of(it)
        spk = f'https://www.spreaker.com/episode/{it["eid"]}'
        yt = f"https://youtu.be/{vid}"
        tr = e.get("tr") or ""
        more = [x for x in by_lang[l] if x["vid"] != vid][:6]
        ld = [
            {"@context": "https://schema.org", "@type": "PodcastEpisode", "name": e["title"], "description": strip_tags(intro),
             "url": canonical, "inLanguage": LANGS[l][1], "datePublished": it["date"],
             "associatedMedia": {"@type": "AudioObject", "contentUrl": spk, "inLanguage": LANGS[l][1]},
             "partOfSeries": {"@type": "PodcastSeries", "name": seo.get(l, {}).get("title", "M365.FM"), "url": f"https://www.spreaker.com/show/{LANGS[l][3]}"},
             "author": {"@id": f"{BASE}/about/mirko-peters/#person"}},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "M365.FM", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 2, "name": LANGS[l][0], "item": f"{BASE}/{l}/"},
                {"@type": "ListItem", "position": 3, "name": e["title"], "item": canonical}]},
            person_ld(),
        ]
        lis = "".join(f"<li>{b}</li>" for b in bullets)
        btns = (f'<a class="btn" href="{spk}">🎧 {esc(ui[0])}</a><a class="btn alt" href="{yt}">▶ {esc(ui[1])}</a>' +
                (f'<a class="btn alt" href="{tr}">📄 {esc(ui[2])}</a>' if tr else ""))
        rel = "".join(f'<li><a href="{url_of(x)}">{esc(x["e"]["title"])}</a></li>' for x in more)
        body = f"""{header(l, lang_switch(l, alts, [x for x in LANGS if x in alts]))}
<main><article>
<p class="mut"><a href="{BASE}/{l}/">{esc(ui[7])}</a> › {esc(LANGS[l][0])}</p>
<h1>{esc(e["title"])}</h1>
<p>{intro}</p>
<iframe src="https://widget.spreaker.com/player?episode_id={it["eid"]}&amp;theme=light&amp;playlist=false" height="131" loading="lazy" title="{esc(e["title"])}"></iframe>
<h2>{esc(hdr)}</h2><ul>{lis}</ul>
<p>{aud}</p>
<p>{btns}</p>
<p class="mut">{esc(ui[6])}</p>
</article>
{('<h2>' + esc(ui[4]) + '</h2><ul>' + rel + '</ul>') if rel else ''}
<p><a href="{BASE}/{l}/">{esc(ui[3])} →</a></p></main>
{footer(l)}"""
        write(f'{l}/{it["slug"]}/index.html',
              page(l, e["title"], short(intro), canonical, body, alts, ld))
        sitemap.append((canonical, it["date"], alts))

    # Sprach-Startseiten
    for l in active:
        ui = UI[l]; s = seo.get(l, {})
        alts_home = {x: f"{BASE}/{x}/" for x in active}
        title = s.get("title") or f"M365.FM – {LANGS[l][0]}"
        d = short(s.get("description", ""), 300)
        cards = "".join(
            f'<div class="card"><h2><a href="{url_of(i)}">{esc(i["e"]["title"])}</a></h2><p>{esc(short(parse_desc(i["e"]["desc"])[0], 200))}</p></div>'
            for i in by_lang[l])
        ld = [{"@context": "https://schema.org", "@type": "PodcastSeries", "name": title, "url": f"{BASE}/{l}/",
               "description": d, "inLanguage": LANGS[l][1], "webFeed": f"https://www.spreaker.com/show/{LANGS[l][3]}/episodes/feed",
               "sameAs": [f"https://www.spreaker.com/show/{LANGS[l][3]}"], "author": {"@id": f"{BASE}/about/mirko-peters/#person"}},
              person_ld()]
        body = f"""{header(l, lang_switch(l, alts_home, active))}
<main><h1>{esc(title)}</h1><p>{esc(d)}</p>
<p><a class="btn" href="https://www.spreaker.com/show/{LANGS[l][3]}">🎧 {esc(ui[0])}</a><a class="btn alt" href="https://www.m365.fm">m365.fm</a></p>
<h2>{esc(ui[3])}</h2>{cards}
<p class="mut">{esc(ui[6])}</p></main>{footer(l)}"""
        write(f"{l}/index.html", page(l, title, short(d), f"{BASE}/{l}/", body, alts_home, ld, og_type="website"))
        sitemap.append((f"{BASE}/{l}/", TODAY, alts_home))

    # Wurzel
    alts_home = {x: f"{BASE}/{x}/" for x in active}
    grid = "".join(f'<a href="{BASE}/{l}/" hreflang="{LANGS[l][1]}" lang="{LANGS[l][1]}"><strong>{esc(LANGS[l][0])}</strong><br><span class="mut">{len(by_lang[l])}</span></a>' for l in active)
    root_body = f"""<header><a class="brand" href="{BASE}/">M365.FM · Mirko Peters</a></header>
<main><h1>Microsoft 365, Copilot &amp; AI – podcast episodes in {len(active)} languages</h1>
<p>Animated explainers about Microsoft 365, Copilot, Azure and the Power Platform by Microsoft MVP Mirko Peters – as AI-dubbed audio episodes in your language. Free, with transcripts.</p>
<div class="grid">{grid}</div>
<p><a href="{BASE}/about/mirko-peters/">About Mirko Peters</a></p></main>{footer_en()}"""
    write("index.html", page("en", "M365.FM – Microsoft 365, Copilot & AI podcast in 19 languages | Mirko Peters",
          "AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure and Power Platform by Microsoft MVP Mirko Peters – in German, Spanish, French, Japanese and more.",
          f"{BASE}/", root_body, alts_home, [person_ld(), {"@context": "https://schema.org", "@type": "WebSite", "name": "M365.FM international", "url": f"{BASE}/", "publisher": {"@id": f"{BASE}/about/mirko-peters/#person"}}], og_type="website"))
    sitemap.append((f"{BASE}/", TODAY, None))

    # Entity-Seite
    about = f"""<header><a class="brand" href="{BASE}/">M365.FM · Mirko Peters</a></header>
<main><h1>Mirko Peters – Microsoft MVP, podcaster, M365Con organizer</h1>
<p>Mirko Peters is a Microsoft MVP who explains Microsoft 365, Microsoft Copilot, Azure, Power Platform, Microsoft Fabric and AI agents for IT admins, architects, developers and decision makers. He hosts the podcast <a href="https://www.m365.fm">M365.FM</a> and the <em>m365 Show</em> on YouTube, and organizes the free online conference <a href="https://m365con.net">M365Con</a>.</p>
<ul><li><a href="https://www.m365.fm">M365.FM – the podcast</a></li><li><a href="https://m365con.net">M365Con – free online conference</a></li>
<li><a href="{LINKEDIN}" rel="me">LinkedIn</a></li><li><a href="{YT_CHANNEL}">YouTube: m365 Show by Mirko Peters</a></li></ul>
<h2>Podcast episodes by language</h2><div class="grid">{grid}</div></main>{footer_en()}"""
    write("about/mirko-peters/index.html", page("en", "Mirko Peters – Microsoft MVP, M365.FM podcast host & M365Con organizer",
          "Mirko Peters is a Microsoft MVP and host of the M365.FM podcast about Microsoft 365, Copilot, Azure and AI. Organizer of the free online conference M365Con.",
          f"{BASE}/about/mirko-peters/", about, None, [person_ld()], og_type="profile"))
    sitemap.append((f"{BASE}/about/mirko-peters/", TODAY, None))

    # Sitemap, robots, llms.txt, IndexNow
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, lm, alts in sitemap:
        sm.append(f"<url><loc>{u}</loc><lastmod>{lm}</lastmod>")
        for x, au in (alts or {}).items():
            sm.append(f'<xhtml:link rel="alternate" hreflang="{LANGS[x][1]}" href="{au}"/>')
        sm.append("</url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    write("llms.txt", f"# M365.FM – Mirko Peters\n\n> AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure and Power Platform by Microsoft MVP Mirko Peters, in {len(active)} languages.\n\n"
          f"- [About Mirko Peters]({BASE}/about/mirko-peters/)\n" + "".join(f"- [{LANGS[l][0]}]({BASE}/{l}/)\n" for l in active))
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)
    write("404.html", page("en", "Not found", "Page not found", f"{BASE}/404.html", '<main><h1>404</h1><p><a href="%s/">M365.FM</a></p></main>' % BASE))
    json.dump([u for u, _, _ in sitemap], open(ROOT / "data" / "urls.json", "w"), indent=0)
    print(f"{len(items)} Episodenseiten, {len(active)} Sprachen, {len(sitemap)} URLs → docs/")


def footer_en():
    return (f'<footer><a href="{BASE}/about/mirko-peters/">About Mirko Peters</a> · <a href="https://www.m365.fm">m365.fm</a> · '
            f'<a href="https://m365con.net">M365Con</a> · <a href="{LINKEDIN}" rel="me">LinkedIn</a> · <a href="{YT_CHANNEL}">YouTube</a></footer>')


if __name__ == "__main__":
    (ROOT / "data").mkdir(exist_ok=True)
    build()
