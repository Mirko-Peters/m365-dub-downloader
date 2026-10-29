#!/usr/bin/env python3
"""Erzeugt die mehrsprachige SEO-Website (docs/) aus episodes/*.json + data/published.json.

Nur Python-Standardbibliothek. Lauf:  python generate_site.py
Basis-URL (z. B. eigene Domain):  SITE_BASE=https://international.m365.fm python generate_site.py
"""
import html, json, os, re, shutil, sys, unicodedata
from datetime import date
from pathlib import Path
import hashlib
from site_content import FAQ

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
_dom = (ROOT / "domain.txt").read_text().strip() if (ROOT / "domain.txt").exists() else ""
BASE = os.environ.get("SITE_BASE") or (f"https://{_dom}" if _dom else "https://mirko-peters.github.io/m365-dub-downloader")
BASE = BASE.rstrip("/")
TODAY = date.today().isoformat()
INDEXNOW_KEY = "0348df8af6514d5bae4d9f9a5ba51f57"

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

CSS = """:root{--bg:#f6f1ea;--fg:#141210;--mut:#6b645c;--ac:#b4233c;--card:#fffdf9;--bd:#1412101f;--ink:#141210;--onink:#f6f1ea}
@media (prefers-color-scheme:dark){:root{--bg:#0e0d0c;--fg:#f1ebe2;--mut:#a39a8e;--ac:#ff5a72;--card:#171513;--bd:#f1ebe226;--ink:#f1ebe2;--onink:#0e0d0c}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.7 -apple-system,"Segoe UI",Inter,Roboto,"Noto Sans",system-ui,sans-serif}
a{color:inherit;text-decoration-color:var(--ac);text-underline-offset:3px}a:hover{color:var(--ac)}
.serif,h1,h2,.brand,.tile b,.num{font-family:"Didot","Bodoni 72","Playfair Display","Iowan Old Style",Georgia,"Noto Serif",serif}
.wrap{max-width:1040px;margin:0 auto;padding:0 22px}
.top{border-bottom:1px solid var(--fg)}.top .wrap{display:flex;flex-wrap:wrap;gap:10px 22px;align-items:center;justify-content:space-between;padding-top:14px;padding-bottom:14px}
.brand{font-size:1.35rem;font-weight:700;letter-spacing:.02em;text-decoration:none}.brand i{color:var(--ac);font-style:normal}
nav.langs{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase}
nav.langs a{text-decoration:none;color:var(--mut)}nav.langs a[aria-current]{color:var(--fg);border-bottom:2px solid var(--ac)}
.kicker{font-size:.76rem;letter-spacing:.2em;text-transform:uppercase;color:var(--ac);font-weight:600;margin:46px 0 10px}
h1{font-size:clamp(1.9rem,4.6vw,3.1rem);line-height:1.1;font-weight:700;letter-spacing:-.015em;margin:0 0 .45em}
h2{font-size:1.5rem;line-height:1.2;margin:2.1em 0 .6em;font-weight:700}
.lede{font-size:clamp(1.15rem,2.4vw,1.45rem);line-height:1.55;max-width:40em;margin:.2em 0 1.4em}
.panel{background:var(--ink);color:var(--onink);border-radius:4px;padding:22px;margin:26px 0}
.panel iframe{width:100%;border:0;border-radius:4px;background:#fff}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 4px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:11px 20px;border:1px solid currentColor;border-radius:999px;text-decoration:none;font-size:.88rem;letter-spacing:.06em;text-transform:uppercase;font-weight:600;color:inherit}
.btn.main{background:var(--ac);border-color:var(--ac);color:#fff}.btn:hover{background:var(--fg);border-color:var(--fg);color:var(--bg)}.panel .btn:hover{background:var(--onink);color:var(--ink)}
.btns{flex-direction:row}.apple-first .btns{display:flex}.apple-first .btn[data-p=apple]{order:-1}.apple-first .btn[data-p=spotify]{order:0}
.points{list-style:none;padding:0;margin:0;counter-reset:n;border-top:1px solid var(--fg)}
.points li{counter-increment:n;display:grid;grid-template-columns:3.2rem 1fr;gap:6px 14px;padding:16px 0;border-bottom:1px solid var(--bd)}
.points li:before{content:counter(n,decimal-leading-zero);font-family:Didot,"Bodoni 72",Georgia,serif;font-size:1.8rem;line-height:1;color:var(--ac)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0;border-top:1px solid var(--fg);border-left:1px solid var(--bd)}
.tile{display:block;padding:20px 16px 18px;border-right:1px solid var(--bd);border-bottom:1px solid var(--bd);text-decoration:none}
.tile b{display:block;font-size:1.5rem;line-height:1.15;font-weight:700}.tile span{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.tile:hover{background:var(--ink);color:var(--onink)}.tile:hover span{color:var(--onink)}
.list{border-top:1px solid var(--fg)}.row{display:block;padding:20px 0;border-bottom:1px solid var(--bd);text-decoration:none}
.row h3{margin:0 0 .25em;font:700 1.35rem/1.25 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.row p{margin:0;color:var(--mut);font-size:.98rem}.row:hover h3{color:var(--ac)}
.author{display:flex;gap:16px;align-items:center;border-top:1px solid var(--fg);border-bottom:1px solid var(--bd);padding:18px 0;margin:36px 0}
.author img.badge{object-fit:cover;border:2px solid var(--ac)}.portrait{float:right;width:190px;height:190px;object-fit:cover;border-radius:50%;border:3px solid var(--ac);margin:0 0 12px 22px}
.author .badge{flex:none;width:58px;height:58px;border-radius:50%;background:var(--ink);color:var(--onink);display:grid;place-items:center;font:700 1.15rem Didot,Georgia,serif}
.author p{margin:0;font-size:.95rem;color:var(--mut)}.author strong{color:var(--fg);display:block;font-size:1.02rem}
.mut{color:var(--mut);font-size:.9rem}.crumbs{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-top:26px}.crumbs a{text-decoration:none}
footer{border-top:1px solid var(--fg);margin-top:64px;padding:26px 0 48px;font-size:.85rem;color:var(--mut)}footer a{margin-right:14px}
.info{margin:1.6em 0;padding:20px 22px;border:1px solid var(--ln,#d9cfc2);background:#fff8;border-radius:6px}.info figcaption{font-family:Didot,"Bodoni 72",Georgia,serif;font-size:1.25rem;margin-bottom:14px}.info small{display:block;margin-top:12px;opacity:.6;font-size:.75rem}
.isteps{list-style:none;padding:0;margin:0;display:grid;gap:12px}.isteps li{display:grid;grid-template-columns:36px 1fr;gap:2px 12px;align-items:start}.isteps i{grid-row:span 2;width:32px;height:32px;border-radius:50%;background:var(--ac);color:#fff;font-style:normal;display:flex;align-items:center;justify-content:center;font-weight:700}.isteps b{font-size:1rem}.isteps span{font-size:.92rem;opacity:.85}
.icols{display:grid;grid-template-columns:1fr 1fr;gap:14px}.icol{border-top:3px solid var(--ac);padding-top:8px}.icol h4{margin:0 0 6px}.icol ul{margin:0;padding-left:18px}.ifacts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}.ifacts div{border-left:3px solid var(--ac);padding-left:10px}.ifacts b{display:block;font-size:1.5rem;font-family:Didot,"Bodoni 72",Georgia,serif}.ifacts span{font-size:.88rem}@media(max-width:560px){.icols{grid-template-columns:1fr}}
.article{margin-top:2em;max-width:42em}.article h2{margin-top:1.6em}.article p,.article li{line-height:1.75}.showrow{font-size:.85rem;margin:10px 0 0}.showrow a{margin-right:12px}.yt{position:relative;margin:22px 0;aspect-ratio:16/9;background:#000;border-radius:4px;overflow:hidden;cursor:pointer}.yt img{width:100%;height:100%;object-fit:cover;opacity:.85}.yt button{position:absolute;inset:0;margin:auto;width:76px;height:76px;border-radius:50%;border:0;background:var(--ac);color:#fff;font-size:30px;cursor:pointer}.yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.cover{margin:18px 0 6px;border-radius:4px;overflow:hidden;line-height:0}.cover svg{width:100%;height:auto;display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0;border-top:1px solid var(--fg);border-bottom:1px solid var(--fg);margin:30px 0}
.stats div{padding:18px 14px;border-inline-end:1px solid var(--bd)}.stats b{display:block;font:700 2.4rem/1 Didot,"Bodoni 72",Georgia,serif;color:var(--ac)}.stats span{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px;margin:14px 0}
.thumb{display:block;text-decoration:none}.thumb .cover{margin:0 0 10px}.thumb h3{margin:0 0 .2em;font:700 1.08rem/1.3 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.thumb p{margin:0;font-size:.82rem;color:var(--mut)}.thumb:hover h3{color:var(--ac)}
.band{background:var(--ink);color:var(--onink);margin:46px 0;padding:34px 0}.band .wrap{display:grid;gap:10px}.band h2{margin:0}.band .btn:hover{background:var(--onink);color:var(--ink)}
.faq details{border-bottom:1px solid var(--bd);padding:14px 0}.faq summary{cursor:pointer;font:700 1.15rem/1.35 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.faq p{margin:.6em 0 0;color:var(--mut)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:22px;margin:16px 0}.cols h3{margin:.1em 0 .3em;font:700 1.15rem Didot,"Bodoni 72",Georgia,serif}.cols p{margin:0;color:var(--mut);font-size:.96rem}
@media (max-width:560px){body{font-size:16px}.panel{padding:14px}.btn{padding:10px 16px}}"""


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
<meta property="og:image" content="{BASE}/assets/og-default.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}/assets/og-default.png">
{extra_head}<style>{CSS}</style>
{ld}</head>
<body>
{body}
</body></html>
"""


def person_ld():
    d = {"@context": "https://schema.org", "@type": "Person", "@id": f"{BASE}/about/mirko-peters/#person",
         "name": "Mirko Peters", "alternateName": ["Mirko Peters MVP", "Mirko Peters M365.FM"], "givenName": "Mirko", "familyName": "Peters",
         "jobTitle": "Microsoft MVP", "description": "Microsoft MVP, host of the M365.FM podcast and the m365 Show on YouTube, organizer of the free online conference M365Con.",
         "url": f"{BASE}/about/mirko-peters/", "mainEntityOfPage": f"{BASE}/about/mirko-peters/", "sameAs": SAME_AS,
         "award": "Microsoft Most Valuable Professional (MVP)",
         "hasOccupation": {"@type": "Occupation", "name": "Microsoft MVP, podcaster and conference organizer"},
         "knowsAbout": ["Microsoft 365", "Microsoft Copilot", "Copilot Studio", "Azure", "Azure AI Foundry", "Power Platform", "Microsoft Fabric",
                        "Microsoft Entra", "Microsoft Purview", "Microsoft Teams", "SharePoint", "AI agents", "Dynamics 365"],
         "worksFor": {"@id": f"{BASE}/#org"}, "founder": [{"@id": f"{BASE}/#org"}]}
    if (ROOT / "assets" / "mirko-peters.jpg").exists():
        d["image"] = f"{BASE}/assets/mirko-peters.jpg"
    return d


def art_svg(seed, big, small="M365.FM · AI"):
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    h1 = h % 360; h2 = (h1 + 35 + (h >> 9) % 70) % 360
    bars = ""
    x = 60; hh = h
    for i in range(44):
        hh = (hh * 1103515245 + 12345) & 0x7fffffff
        v = 40 + (hh >> 8) % 180
        bars += f'<rect x="{x}" y="{330 - v // 2}" width="14" height="{v}" rx="7" fill="hsl({h1 + 18},85%,72%)" opacity="{0.35 + (v / 400):.2f}"/>'
        x += 25
    return (f'<svg viewBox="0 0 1200 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" focusable="false">'
            f'<defs><linearGradient id="g{h % 99999}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl({h1},55%,24%)"/><stop offset="1" stop-color="hsl({h2},60%,11%)"/></linearGradient></defs>'
            f'<rect width="1200" height="420" fill="url(#g{h % 99999})"/>{bars}'
            f'<text x="60" y="92" font-family="Didot,Georgia,serif" font-size="64" font-weight="700" fill="#f6f1ea">{esc(big)}</text>'
            f'<text x="60" y="388" font-family="system-ui,sans-serif" font-size="22" letter-spacing="5" fill="#f6f1ea" opacity=".8">{esc(small.upper())}</text>'
            f'<circle cx="1120" cy="66" r="14" fill="#b4233c"/></svg>')


def org_ld():
    return {"@context": "https://schema.org", "@type": "Organization", "@id": f"{BASE}/#org", "name": "M365.FM", "url": "https://www.m365.fm",
            "logo": f"{BASE}/assets/og-default.png", "founder": {"@id": f"{BASE}/about/mirko-peters/#person"},
            "sameAs": ["https://www.m365.fm", "https://m365con.net", YT_CHANNEL, LINKEDIN]}


def event_ld():
    return {"@context": "https://schema.org", "@type": "Event", "@id": f"{BASE}/#m365con2027", "name": "M365Con 2027 – free online conference",
            "description": "Free, 100% online Microsoft community conference with 120 sessions on Microsoft 365, Copilot, Azure, Power Platform, security and AI.",
            "startDate": "2027-01-11", "endDate": "2027-01-22", "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled", "isAccessibleForFree": True, "inLanguage": "en",
            "location": {"@type": "VirtualLocation", "url": "https://m365con.net"}, "url": "https://m365con.net",
            "organizer": {"@id": f"{BASE}/about/mirko-peters/#person"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "url": "https://m365con.net", "availability": "https://schema.org/InStock"}}


def faq_ld(lang):
    return {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": LANGS[lang][1] if lang in LANGS else "en",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ[lang]]}


def faq_html(lang, title="FAQ"):
    rows = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in FAQ[lang])
    return f'<section class="faq"><h2>{esc(title)}</h2>{rows}</section>'


def m365con_band():
    return (f'<div class="band"><div class="wrap"><div class="kicker" style="margin:0;color:inherit;opacity:.8">M365Con 2027 · Jan 11–22 · 100% online · free</div>'
            f'<h2>120 sessions. 10 days. Microsoft community from all over the world.</h2>'
            f'<div class="btns"><a class="btn main" href="https://m365con.net">m365con.net</a></div></div></div>')


def header(lang, switch):
    home = f"{BASE}/{lang}/" if lang in LANGS else f"{BASE}/"
    return f'<div class="top"><div class="wrap"><a class="brand" href="{home}">M365<i>.</i>FM <span class="mut" style="font:400 .8rem sans-serif;letter-spacing:.14em">MIRKO PETERS</span></a>{switch}</div></div>'


def footer(lang):
    ui = UI.get(lang)
    about = ui[5] if ui else "About Mirko Peters"
    return (f'<footer><div class="wrap"><a href="{BASE}/about/mirko-peters/">{esc(about)}</a><a href="https://www.m365.fm">m365.fm</a>'
            f'<a href="https://m365con.net">M365Con</a><a href="{LINKEDIN}" rel="me">LinkedIn</a><a href="{YT_CHANNEL}">YouTube</a></div></footer>')


def author_box(lang):
    ui = UI.get(lang)
    name = ui[5] if ui else "About Mirko Peters"
    bio = ui[6] if ui else "Mirko Peters is a Microsoft MVP, host of the podcast M365.FM and initiator of the free online conference M365Con."
    photo = (ROOT / "assets" / "mirko-peters.jpg").exists()
    badge = (f'<img class="badge" src="{BASE}/assets/mirko-peters.jpg" alt="Mirko Peters, Microsoft MVP" width="58" height="58" loading="lazy">' if photo else '<div class="badge">MP</div>')
    return (f'<div class="author">{badge}<div><strong><a href="{BASE}/about/mirko-peters/">Mirko Peters</a> · Microsoft MVP</strong>'
            f'<p>{esc(bio)}</p></div></div>')


YT_JS = """<script>document.querySelectorAll('.yt').forEach(function(b){b.addEventListener('click',function(){var i=document.createElement('iframe');i.src='https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1&rel=0';i.allow='accelerometer;autoplay;encrypted-media;picture-in-picture';i.allowFullscreen=true;i.title='YouTube';b.innerHTML='';b.appendChild(i)},{once:true})});</script>"""
EXTRA = (("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart"), ("podcastaddict_show", "Podcast Addict"), ("podchaser_show", "Podchaser"))


def extra_btns(sh):
    return "".join(f'<a class="btn" href="{sh[k]}" rel="noopener">{n}</a>' for k, n in EXTRA if sh.get(k))


def same_as(l, sh):
    return [f"https://www.spreaker.com/show/{LANGS[l][3]}"] + [sh[k] for k in ("apple_show", "spotify_show", "amazon_show", "deezer_show", "iheart_show", "podcastaddict_show", "podchaser_show") if sh.get(k)]


def info_html(info):
    """Infografik (Schritte / Vergleich / Fakten) aus strukturierten Daten – serverseitig gerendert, kein fremdes HTML."""
    try:
        t = esc(info.get("titel", ""))
        typ = info.get("typ")
        if typ == "vergleich":
            def col(c):
                return f'<div class="icol"><h4>{esc(c.get("titel", ""))}</h4><ul>' + "".join(f"<li>{esc(x)}</li>" for x in c.get("punkte", [])[:6]) + "</ul></div>"
            body = f'<div class="icols">{col(info["links"])}{col(info["rechts"])}</div>'
        elif typ == "fakten":
            body = '<div class="ifacts">' + "".join(f'<div><b>{esc(p.get("wert", ""))}</b><span>{esc(p.get("text", ""))}</span></div>' for p in info.get("punkte", [])[:6]) + "</div>"
        else:
            body = '<ol class="isteps">' + "".join(f'<li><i>{n + 1}</i><b>{esc(p.get("kopf", ""))}</b><span>{esc(p.get("text", ""))}</span></li>' for n, p in enumerate(info.get("punkte", [])[:6])) + "</ol>"
        return f'<figure class="info"><figcaption>{t}</figcaption>{body}<small>M365.FM · Mirko Peters</small></figure>'
    except Exception:
        return ""


PLAT_JS = """<script>(function(){try{var ua=navigator.userAgent||"",pl=navigator.platform||"";var apple=/iPhone|iPad|iPod|Macintosh|Mac OS X/.test(ua)||/Mac|iPhone|iPad/.test(pl)||(navigator.maxTouchPoints>1&&/Mac/.test(pl));
var d=document.documentElement;if(apple)d.className+=" apple-first";var pick=document.querySelector(apple?'[data-p=apple]':'[data-p=spotify]')||document.querySelector('[data-p=spotify]')||document.querySelector('[data-p=apple]')||document.querySelector('[data-p=spreaker]');if(pick)pick.className+=" main"}catch(e){}})();</script>"""


def build():
    eps, pub, seo = load()
    plat = json.load(open(ROOT / "data" / "platforms.json", encoding="utf-8")) if (ROOT / "data" / "platforms.json").exists() else {}
    articles = {p.stem: json.load(open(p, encoding="utf-8")) for p in (ROOT / "data" / "articles").glob("*.json")} if (ROOT / "data" / "articles").exists() else {}
    elinks = json.load(open(ROOT / "data" / "episode_links.json", encoding="utf-8")) if (ROOT / "data" / "episode_links.json").exists() else {}
    videos = json.load(open(ROOT / "data" / "videos.json", encoding="utf-8")) if (ROOT / "data" / "videos.json").exists() else {}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / ".nojekyll").write_text("")
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", OUT / "assets")

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
             "image": f"{BASE}/assets/og-default.png", "isAccessibleForFree": True, "keywords": e.get("tags", ""),
             "about": [{"@type": "Thing", "name": t.strip()} for t in (e.get("tags") or "").split(",")[:5] if t.strip() and "m365.fm" not in t],
             **({"transcript": tr} if tr else {}),
             "partOfSeries": {"@type": "PodcastSeries", "name": seo.get(l, {}).get("title", "M365.FM"), "url": f"https://www.spreaker.com/show/{LANGS[l][3]}", "sameAs": same_as(l, plat.get(l, {}))},
             "author": {"@id": f"{BASE}/about/mirko-peters/#person"}},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "M365.FM", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 2, "name": LANGS[l][0], "item": f"{BASE}/{l}/"},
                {"@type": "ListItem", "position": 3, "name": e["title"], "item": canonical}]},
            {"@context": "https://schema.org", "@type": "VideoObject", "@id": canonical + "#video", "name": e["title"], "description": strip_tags(intro),
             "thumbnailUrl": [f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
             "uploadDate": videos.get(vid, {}).get("date", it["date"]), "contentUrl": f"https://www.youtube.com/watch?v={vid}",
             "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}", "isFamilyFriendly": True,
             "publisher": {"@id": f"{BASE}/#org"}, "author": {"@id": f"{BASE}/about/mirko-peters/#person"}},
            person_ld(), org_ld(),
        ]
        ld[0]["video"] = {"@id": canonical + "#video"}
        art = articles.get(vid, {}).get(l, {})
        art_html = art.get("html", "")
        if art_html and art.get("info"):
            ih = info_html(art["info"])
            art_html = re.sub(r"(</p>)", r"\1" + ih.replace("\\", "\\\\"), art_html, count=1) if ih else art_html
        if art_html:
            ld.append({"@context": "https://schema.org", "@type": "Article", "headline": e["title"][:110], "inLanguage": LANGS[l][1],
                       "datePublished": it["date"], "dateModified": it["date"], "mainEntityOfPage": canonical,
                       "author": {"@id": f"{BASE}/about/mirko-peters/#person"}, "publisher": {"@id": f"{BASE}/#org"},
                       "wordCount": len(strip_tags(art_html).split())})
        lis = "".join(f"<li>{x}</li>" for x in bullets)
        el = elinks.get(f"{vid}:{l}", {}); sh = plat.get(l, {})
        apple = el.get("apple") or sh.get("apple_show"); spot = el.get("spotify") or sh.get("spotify_show")
        btns = ""
        if apple: btns += f'<a class="btn" data-p="apple" href="{apple}" rel="noopener">Apple Podcasts</a>'
        if spot: btns += f'<a class="btn" data-p="spotify" href="{spot}" rel="noopener">Spotify</a>'
        if el.get("deezer") or sh.get("deezer_show"): btns += f'<a class="btn" href="{el.get("deezer") or sh["deezer_show"]}" rel="noopener">Deezer</a>'
        if sh.get("amazon_show"): btns += f'<a class="btn" href="{sh["amazon_show"]}" rel="noopener">Amazon Music</a>'
        showrow = "".join(f'<a href="{sh[k]}" rel="noopener">{n}</a>' for k, n in (("apple_show", "Apple Podcasts"), ("spotify_show", "Spotify"), ("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart"), ("podcastaddict_show", "Podcast Addict"), ("podchaser_show", "Podchaser")) if sh.get(k))
        btns += f'<a class="btn" data-p="spreaker" href="{spk}" rel="noopener">🎧 {esc(ui[0])}</a>' 
        btns += f'<a class="btn" href="{yt}" rel="noopener">▶ {esc(ui[1])}</a>'
        if tr: btns += f'<a class="btn" href="{tr}">📄 {esc(ui[2])}</a>'
        rel = "".join(f'<a class="row" href="{url_of(x)}"><h3>{esc(x["e"]["title"])}</h3></a>' for x in more)
        body = f"""{header(l, lang_switch(l, alts, [x for x in LANGS if x in alts]))}
<main class="wrap"><article>
<div class="crumbs"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])} / {it["date"]}</div>
<div class="kicker">M365.FM · {esc(LANGS[l][0])}</div>
<h1>{esc(e["title"])}</h1>
<p class="lede">{intro}</p>
<figure class="cover" style="margin-inline:0">{art_svg(vid, LANGS[l][0], "M365.FM · " + ui[0])}</figure>
<div class="panel"><iframe src="https://widget.spreaker.com/player?episode_id={it["eid"]}&amp;theme=light&amp;playlist=false" height="131" loading="lazy" title="{esc(e["title"])}"></iframe>
<div class="btns">{btns}</div>{"<p class=showrow>M365.FM ▸ " + showrow + "</p>" if showrow else ""}</div>
<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" title="{esc(e["title"])}" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
<h2>{esc(hdr)}</h2><ol class="points">{lis}</ol>
<p class="lede" style="margin-top:1.4em">{aud}</p>
{("<section class=article>" + art_html + "</section>") if art_html else ""}
{author_box(l)}
<p class="mut">{esc(ui[6])}</p>
</article>
{('<h2>' + esc(ui[4]) + '</h2><div class="list">' + rel + '</div>') if rel else ''}
<p style="margin-top:1.6em"><a class="btn" href="{BASE}/{l}/">{esc(ui[3])} →</a></p></main>
{footer(l)}{PLAT_JS}"""
        write(f'{l}/{it["slug"]}/index.html',
              page(l, e["title"], short(intro), canonical, body, alts, ld))
        sitemap.append((canonical, it["date"], alts))

    # Sprach-Startseiten
    for l in active:
        ui = UI[l]; s = seo.get(l, {})
        alts_home = {x: f"{BASE}/{x}/" for x in active}
        title = s.get("title") or f"M365.FM – {LANGS[l][0]}"
        d = short(s.get("description", ""), 300)
        newest = by_lang[l]
        thumbs = "".join(
            f'<a class="thumb" href="{url_of(i)}"><figure class="cover" style="margin-inline:0">{art_svg(i["vid"], LANGS[l][0])}</figure><h3>{esc(i["e"]["title"])}</h3><p>{esc(short(parse_desc(i["e"]["desc"])[0], 110))}</p></a>'
            for i in newest)
        ld = [{"@context": "https://schema.org", "@type": "PodcastSeries", "@id": f"{BASE}/{l}/#series", "name": title, "url": f"{BASE}/{l}/",
               "description": d, "inLanguage": LANGS[l][1], "webFeed": f"https://www.spreaker.com/show/{LANGS[l][3]}/episodes/feed", "image": f"{BASE}/assets/og-default.png",
               "numberOfEpisodes": len(newest),
               "sameAs": same_as(l, plat.get(l, {})),
               "author": {"@id": f"{BASE}/about/mirko-peters/#person"}, "publisher": {"@id": f"{BASE}/#org"}},
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": f"{BASE}/{l}/", "inLanguage": LANGS[l][1],
               "mainEntity": {"@type": "ItemList", "numberOfItems": len(newest),
                              "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": url_of(i)} for n, i in enumerate(newest[:50])]}},
              faq_ld(l), person_ld(), org_ld()]
        sh = plat.get(l, {})
        sbtn = ""
        if sh.get("apple_show"): sbtn += f'<a class="btn" data-p="apple" href="{sh["apple_show"]}">Apple Podcasts</a>'
        if sh.get("spotify_show"): sbtn += f'<a class="btn" data-p="spotify" href="{sh["spotify_show"]}">Spotify</a>'
        sbtn += f'<a class="btn" data-p="spreaker" href="https://www.spreaker.com/show/{LANGS[l][3]}">🎧 {esc(ui[0])}</a>' + extra_btns(sh) + '<a class="btn" href="https://www.m365.fm">m365.fm</a>'
        nvid = len({i["vid"] for i in newest})
        body = f"""{header(l, lang_switch(l, alts_home, active))}
<main class="wrap"><div class="kicker">{esc(LANGS[l][0])} · M365.FM</div><h1>{esc(title)}</h1><p class="lede">{esc(d)}</p>
<div class="btns">{sbtn}</div>
<div class="stats"><div><b>{len(newest)}</b><span>{esc(ui[3])}</span></div><div><b>{nvid}</b><span>Videos</span></div><div><b>{len(active)}</b><span>Languages</span></div></div>
<h2>{esc(ui[3])}</h2><div class="thumbs">{thumbs}</div></main>
{m365con_band()}
<main class="wrap">{faq_html(l, "FAQ")}{author_box(l)}</main>{footer(l)}{PLAT_JS}"""
        write(f"{l}/index.html", page(l, title, short(d), f"{BASE}/{l}/", body, alts_home, ld, og_type="website"))
        sitemap.append((f"{BASE}/{l}/", TODAY, alts_home))

    # Wurzel
    alts_home = {x: f"{BASE}/{x}/" for x in active}
    grid = "".join(f'<a class="tile" href="{BASE}/{l}/" hreflang="{LANGS[l][1]}" lang="{LANGS[l][1]}"><b>{esc(LANGS[l][0])}</b><span>{len(by_lang[l])} episodes</span></a>' for l in active)
    vids_new = sorted(by_vid, key=lambda v: max(x["date"] for x in by_vid[v].values()), reverse=True)[:9]
    latest = []
    for n, v in enumerate(vids_new):
        avail = [x for x in active if x in by_vid[v]]
        latest.append(by_vid[v][avail[n % len(avail)]])
    lt = "".join(f'<a class="thumb" href="{url_of(i)}" hreflang="{LANGS[i["lang"]][1]}"><figure class="cover" style="margin-inline:0">{art_svg(i["vid"], LANGS[i["lang"]][0])}</figure><h3>{esc(i["e"]["title"])}</h3><p>{esc(LANGS[i["lang"]][0])}</p></a>' for i in latest)
    nvid_all = len(by_vid)
    root_body = f"""{header('en', '')}
<main class="wrap"><div class="kicker">Microsoft 365 · Copilot · Azure · AI</div>
<h1>The M365.FM podcast in {len(active)} languages</h1>
<p class="lede">Animated explainers about Microsoft 365, Copilot, Azure and the Power Platform by Microsoft MVP Mirko Peters – as AI-dubbed audio episodes in your language. Free, with transcripts.</p>
<div class="btns"><a class="btn main" href="#languages">Choose your language</a><a class="btn" href="{BASE}/about/mirko-peters/">About Mirko Peters</a></div>
<div class="stats"><div><b>{len(items)}</b><span>Episodes</span></div><div><b>{nvid_all}</b><span>Videos</span></div><div><b>{len(active)}</b><span>Languages</span></div><div><b>0 €</b><span>Free</span></div></div>
<h2>Latest episodes</h2><div class="thumbs">{lt}</div>
<h2 id="languages">Languages</h2><div class="grid">{grid}</div></main>
{m365con_band()}
<main class="wrap">{faq_html('en', 'FAQ')}{author_box('en')}</main>{footer_en()}"""
    write("index.html", page("en", "M365.FM – Microsoft 365, Copilot & AI podcast in 19 languages | Mirko Peters",
          "AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure and Power Platform by Microsoft MVP Mirko Peters – in German, Spanish, French, Japanese and more.",
          f"{BASE}/", root_body, alts_home, [person_ld(), org_ld(), event_ld(), faq_ld("en"), {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{BASE}/#website", "name": "M365.FM international", "url": f"{BASE}/", "inLanguage": [LANGS[x][1] for x in active], "publisher": {"@id": f"{BASE}/#org"}, "author": {"@id": f"{BASE}/about/mirko-peters/#person"}}], og_type="website"))
    sitemap.append((f"{BASE}/", TODAY, None))

    # Entity-Seite
    PORTRAIT = (f'<img class="portrait" src="{BASE}/assets/mirko-peters.jpg" alt="Mirko Peters, Microsoft MVP, host of M365.FM" width="190" height="190">' if (ROOT / "assets" / "mirko-peters.jpg").exists() else "")
    about = f"""{header('en', '')}
<main class="wrap"><div class="kicker">Microsoft MVP · Podcaster · Conference organizer</div>{PORTRAIT}<h1>Mirko Peters</h1>
<p class="lede">Mirko Peters is a Microsoft MVP who explains Microsoft 365, Microsoft Copilot, Azure, Power Platform, Microsoft Fabric and AI agents for IT admins, architects, developers and decision makers. He hosts the podcast <a href="https://www.m365.fm">M365.FM</a> and the <em>m365 Show</em> on YouTube, and organizes the free online conference <a href="https://m365con.net">M365Con</a>.</p>
<div class="btns"><a class="btn main" href="https://www.m365.fm">M365.FM</a><a class="btn" href="https://m365con.net">M365Con</a><a class="btn" href="{LINKEDIN}" rel="me">LinkedIn</a><a class="btn" href="{YT_CHANNEL}">YouTube</a></div>
<h2>What Mirko works on</h2>
<div class="cols"><div><h3>Podcast</h3><p>M365.FM covers Microsoft 365, Copilot, Azure, Power Platform and security – practical, from real projects, with new episodes every week.</p></div>
<div><h3>Video</h3><p>The m365 Show on YouTube turns complex Microsoft topics into short animated explainers, now also available as AI-dubbed audio in {len(active)} languages.</p></div>
<div><h3>Community</h3><p>M365Con is a free, 100% online conference (Jan 11–22, 2027) with 120 sessions by speakers from the global Microsoft community.</p></div></div>
<h2>Topics</h2>
<p>Microsoft 365 Copilot · Copilot Studio · AI agents · Azure AI Foundry · Power Platform · Microsoft Fabric · Microsoft Entra · Microsoft Purview · Microsoft Teams · SharePoint · Dynamics 365 · Governance &amp; security</p>
<h2>Find Mirko Peters online</h2>
<ul class="points"><li><span><a href="https://www.m365.fm">m365.fm</a> – the podcast and episode archive</span></li><li><span><a href="https://m365con.net">m365con.net</a> – free online conference</span></li><li><span><a href="{LINKEDIN}" rel="me">LinkedIn</a></span></li><li><span><a href="{YT_CHANNEL}">YouTube – m365 Show by Mirko Peters</a></span></li></ul>
<h2>Podcast episodes by language</h2><div class="grid">{grid}</div></main>
{m365con_band()}
<main class="wrap">{faq_html('en', 'FAQ')}</main>{footer_en()}"""
    write("about/mirko-peters/index.html", page("en", "Mirko Peters – Microsoft MVP, M365.FM podcast host & M365Con organizer",
          "Mirko Peters is a Microsoft MVP and host of the M365.FM podcast about Microsoft 365, Copilot, Azure and AI. Organizer of the free online conference M365Con.",
          f"{BASE}/about/mirko-peters/", about, None, [{"@context": "https://schema.org", "@type": "ProfilePage", "@id": f"{BASE}/about/mirko-peters/#profile", "url": f"{BASE}/about/mirko-peters/", "name": "Mirko Peters", "dateModified": TODAY, "mainEntity": {"@id": f"{BASE}/about/mirko-peters/#person"}}, person_ld(), org_ld(), event_ld(), faq_ld("en")], og_type="profile"))
    sitemap.append((f"{BASE}/about/mirko-peters/", TODAY, None))

    # Sitemap, robots, llms.txt, IndexNow
    def sm_file(entries):
        x = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
        for u, lm, alts in entries:
            x.append(f"<url><loc>{u}</loc><lastmod>{lm}</lastmod>")
            for k, au in (alts or {}).items():
                x.append(f'<xhtml:link rel="alternate" hreflang="{LANGS[k][1]}" href="{au}"/>')
            x.append("</url>")
        x.append("</urlset>")
        return "\n".join(x)

    # eine Sitemap pro Sprache (Startseite + alle Folgenseiten) + eine für Kernseiten, dazu der Index
    index = []
    core = [e for e in sitemap if not any(e[0].startswith(f"{BASE}/{l}/") for l in LANGS)]
    write("sitemap-core.xml", sm_file(core))
    index.append(("sitemap-core.xml", TODAY))
    for l in active:
        ents = [e for e in sitemap if e[0].startswith(f"{BASE}/{l}/")]
        lm = max(e[1] for e in ents)
        write(f"sitemap-{l}.xml", sm_file(ents))
        index.append((f"sitemap-{l}.xml", lm))
    idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for f, lm in index:
        idx.append(f"<sitemap><loc>{BASE}/{f}</loc><lastmod>{lm}</lastmod></sitemap>")
    idx.append("</sitemapindex>")
    write("sitemap.xml", "\n".join(idx))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    write("llms.txt", f"# M365.FM – Mirko Peters\n\n> AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure and Power Platform by Microsoft MVP Mirko Peters, in {len(active)} languages.\n\n"
          f"- [About Mirko Peters]({BASE}/about/mirko-peters/)\n" + "".join(f"- [{LANGS[l][0]}]({BASE}/{l}/)\n" for l in active))
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)
    if _dom:
        write("CNAME", _dom)
    write("404.html", page("en", "Not found", "Page not found", f"{BASE}/404.html", '<main class="wrap"><h1>404</h1><p><a class="btn" href="%s/">M365.FM</a></p></main>' % BASE))
    json.dump([u for u, _, _ in sitemap], open(ROOT / "data" / "urls.json", "w"), indent=0)
    print(f"{len(items)} Episodenseiten, {len(active)} Sprachen, {len(sitemap)} URLs → docs/")


def footer_en():
    return footer("en")


if __name__ == "__main__":
    (ROOT / "data").mkdir(exist_ok=True)
    build()
