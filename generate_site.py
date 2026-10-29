#!/usr/bin/env python3
"""Erzeugt die mehrsprachige SEO-Website (docs/) aus episodes/*.json + data/published.json.

Nur Python-Standardbibliothek. Lauf:  python generate_site.py
Basis-URL (z. B. eigene Domain):  SITE_BASE=https://international.m365.fm python generate_site.py
"""
import glob, html, json, os, re, shutil, sys, unicodedata
from datetime import date
from pathlib import Path
import hashlib
import site_cover
from site_content import FAQ
from site_taxonomy import (CATS, ORDER, TOPICS, TAGW, cat_name, classify, tags_of, tag_slug, tag_url, related, autolink)

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
_dom = (ROOT / "domain.txt").read_text().strip() if (ROOT / "domain.txt").exists() else ""
BASE = os.environ.get("SITE_BASE") or (f"https://{_dom}" if _dom else "https://mirko-peters.github.io/m365-dub-downloader")
BASE = BASE.rstrip("/")
TODAY = date.today().isoformat()
INDEXNOW_KEY = "0348df8af6514d5bae4d9f9a5ba51f57"

YT_CHANNEL = "https://www.youtube.com/channel/UCIdo4tN3khKldHP3733E9JA"
LINKEDIN = "https://www.linkedin.com/in/m365showpodcast/"
MVP = "https://mvp.microsoft.com/de-DE/mvp/profile/9b0ca797-db5a-493a-a845-8b9158046cf5"
SAME_AS = [MVP, LINKEDIN, "https://www.m365.fm", "https://m365con.net", YT_CHANNEL]

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
.row h3{margin:0 0 .25em;font:700 1.35rem/1.25 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.row p{margin:0;color:var(--mut);font-size:.98rem}.row:hover h3{color:var(--ac)}.row>a,.thumb>a{display:block;color:inherit;text-decoration:none}
.author{display:flex;gap:16px;align-items:center;border-top:1px solid var(--fg);border-bottom:1px solid var(--bd);padding:18px 0;margin:36px 0}
.author img.badge{object-fit:cover;border:2px solid var(--ac)}.portrait{float:right;width:190px;height:190px;object-fit:cover;border-radius:50%;border:3px solid var(--ac);margin:0 0 12px 22px}
.author .badge{flex:none;width:58px;height:58px;border-radius:50%;background:var(--ink);color:var(--onink);display:grid;place-items:center;font:700 1.15rem Didot,Georgia,serif}
.author p{margin:0;font-size:.95rem;color:var(--mut)}.author strong{color:var(--fg);display:block;font-size:1.02rem}
.mut{color:var(--mut);font-size:.9rem}.crumbs{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-top:26px}.crumbs a{text-decoration:none}
footer{border-top:1px solid var(--fg);margin-top:64px;padding:26px 0 48px;font-size:.85rem;color:var(--mut)}footer a{margin-right:14px}
.info{margin:1.6em 0;padding:20px 22px;border:1px solid var(--ln,#d9cfc2);background:#fff8;border-radius:6px}.info figcaption{font-family:Didot,"Bodoni 72",Georgia,serif;font-size:1.25rem;margin-bottom:14px}.info small{display:block;margin-top:12px;opacity:.6;font-size:.75rem}
.isteps{list-style:none;padding:0;margin:0;display:grid;gap:12px}.isteps li{display:grid;grid-template-columns:36px 1fr;gap:2px 12px;align-items:start}.isteps i{grid-row:span 2;width:32px;height:32px;border-radius:50%;background:var(--ac);color:#fff;font-style:normal;display:flex;align-items:center;justify-content:center;font-weight:700}.isteps b{font-size:1rem}.isteps span{font-size:.92rem;opacity:.85}
.icols{display:grid;grid-template-columns:1fr 1fr;gap:14px}.icol{border-top:3px solid var(--ac);padding-top:8px}.icol h4{margin:0 0 6px}.icol ul{margin:0;padding-left:18px}.ifacts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}.ifacts div{border-left:3px solid var(--ac);padding-left:10px}.ifacts b{display:block;font-size:1.5rem;font-family:Didot,"Bodoni 72",Georgia,serif}.ifacts span{font-size:.88rem}@media(max-width:560px){.icols{grid-template-columns:1fr}}
.article{margin-top:2em;max-width:42em}.article h2{margin-top:1.6em}.article p,.article li{line-height:1.75}.cc{position:fixed;left:12px;right:12px;bottom:12px;z-index:50;max-width:760px;margin:0 auto;background:var(--ink);color:var(--onink);padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;box-shadow:0 6px 28px #0006}.cc[hidden]{display:none}.cc span{flex:1 1 260px;font-size:.92rem}.cc .btn{padding:6px 14px;color:var(--onink);border-color:var(--onink)}.cc .btn.main{color:#fff;border-color:var(--ac)}.share{border-top:1px solid var(--ln,#d9cfc2);margin-top:2.5em;padding:16px 0}.share .wrap{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.share b{margin-right:6px}.share .btn{font-size:.85rem;padding:6px 12px}.showrow{font-size:.85rem;margin:10px 0 0}.showrow a{margin-right:12px}.yt{position:relative;margin:22px 0;aspect-ratio:16/9;background:#000;border-radius:4px;overflow:hidden;cursor:pointer}.yt img{width:100%;height:100%;object-fit:cover;opacity:.85}.yt button{position:absolute;inset:0;margin:auto;width:76px;height:76px;border-radius:50%;border:0;background:var(--ac);color:#fff;font-size:30px;cursor:pointer}.yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.cover{margin:18px 0 6px;border-radius:4px;overflow:hidden;line-height:0}.cover svg{width:100%;height:auto;display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0;border-top:1px solid var(--fg);border-bottom:1px solid var(--fg);margin:30px 0}
.stats div{padding:18px 14px;border-inline-end:1px solid var(--bd)}.stats b{display:block;font:700 2.4rem/1 Didot,"Bodoni 72",Georgia,serif;color:var(--ac)}.stats span{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px;margin:14px 0}
.thumb{display:block;text-decoration:none}.thumb .cover{margin:0 0 10px}.thumb h3{margin:0 0 .2em;font:700 1.08rem/1.3 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.thumb p{margin:0;font-size:.82rem;color:var(--mut)}.thumb:hover h3{color:var(--ac)}
.band{background:var(--ink);color:var(--onink);margin:46px 0;padding:34px 0}.band .wrap{display:grid;gap:10px}.band h2{margin:0}.band .btn:hover{background:var(--onink);color:var(--ink)}
.faq details{border-bottom:1px solid var(--bd);padding:14px 0}.faq summary{cursor:pointer;font:700 1.15rem/1.35 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.faq p{margin:.6em 0 0;color:var(--mut)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:22px;margin:16px 0}.cols h3{margin:.1em 0 .3em;font:700 1.15rem Didot,"Bodoni 72",Georgia,serif}.cols p{margin:0;color:var(--mut);font-size:.96rem}
@media (max-width:560px){body{font-size:16px}.panel{padding:14px}.btn{padding:10px 16px}}"""
from site_design import FONT_CSS, INDUSTRY, EN_NAMES, section, spec_box, lang_tile, spec_table, cta_box, hero_h1
CSS = FONT_CSS + CSS + INDUSTRY


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


def anchor_title(t, n=58):
    """Kurzer Ankertext fuer interne Links (Kernthema vor dem Doppelpunkt)."""
    t = re.sub(r"\s*\((KI|AI)[^)]*\)\s*$", "", strip_tags(t)).strip()
    main = t.split(":")[0].strip() if ":" in t and len(t.split(":")[0].strip()) >= 14 else t
    return main if len(main) <= n else main[: n - 1].rsplit(" ", 1)[0].rstrip(",;–-") + "…"


def short(s, n=155):
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


TOP_L = {"de": "Top-Folgen der Woche", "es": "Episodios más escuchados de la semana", "fr": "Épisodes les plus écoutés cette semaine", "it": "Episodi più ascoltati della settimana",
         "pt": "Episódios mais ouvidos da semana", "nl": "Meest beluisterde afleveringen van de week", "pl": "Najczęściej słuchane odcinki tygodnia", "id": "Episode terpopuler minggu ini",
         "ru": "Самые популярные выпуски недели", "uk": "Найпопулярніші випуски тижня", "ar": "أكثر الحلقات استماعًا هذا الأسبوع", "he": "הפרקים המובילים השבוע",
         "hi": "इस सप्ताह के टॉप एपिसोड", "ja": "今週の人気エピソード", "ko": "이번 주 인기 에피소드", "ml": "ഈ ആഴ്ചയിലെ ടോപ്പ് എപ്പിസോഡുകൾ", "pa": "ਇਸ ਹਫ਼ਤੇ ਦੇ ਟੌਪ ਐਪੀਸੋਡ",
         "ta": "இந்த வாரத்தின் சிறந்த எபிசோடுகள்", "te": "ఈ వారం టాప్ ఎపిసోడ్లు", "en": "Top episodes this week"}
OGLIST = []
SHARE_L = {"de": "Teilen", "es": "Compartir", "fr": "Partager", "it": "Condividi", "pt": "Compartilhar", "nl": "Delen", "pl": "Udostępnij",
           "id": "Bagikan", "ru": "Поделиться", "uk": "Поділитися", "ar": "مشاركة", "he": "שיתוף", "hi": "शेयर करें", "ja": "シェア",
           "ko": "공유", "ml": "പങ്കിടുക", "pa": "ਸਾਂਝਾ ਕਰੋ", "ta": "பகிர்", "te": "షేర్ చేయండి", "en": "Share"}
COPY_L = {"de": "Link kopieren", "es": "Copiar enlace", "fr": "Copier le lien", "it": "Copia link", "pt": "Copiar link", "nl": "Link kopiëren",
          "pl": "Kopiuj link", "id": "Salin tautan", "ru": "Копировать ссылку", "uk": "Копіювати посилання", "ar": "نسخ الرابط", "he": "העתקת קישור",
          "hi": "लिंक कॉपी करें", "ja": "リンクをコピー", "ko": "링크 복사", "ml": "ലിങ്ക് പകർത്തുക", "pa": "ਲਿੰਕ ਕਾਪੀ ਕਰੋ", "ta": "இணைப்பை நகலெடு",
          "te": "లింక్ కాపీ", "en": "Copy link"}


def seo_title(t):
    """<title> für Suchergebnisse: Kernthema vor dem Doppelpunkt, max. ~60 Zeichen, Marke hinten."""
    t = strip_tags(t).strip()
    main = t.split(":")[0].strip() if ":" in t and len(t.split(":")[0].strip()) >= 18 else t
    if len(main) > 52:
        main = main[:51].rsplit(" ", 1)[0].rstrip(",;–-") + "…"
    return f"{main} | M365.FM"


BRAND_ICONS = {
    "LinkedIn": ("M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z", "0A66C2"),
    "X": ("M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z", "000000"),
    "Facebook": ("M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z", "0866FF"),
    "WhatsApp": ("M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z", "25D366"),
    "Telegram": ("M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z", "26A5E4"),
    "Reddit": ("M12 0C5.373 0 0 5.373 0 12c0 3.314 1.343 6.314 3.515 8.485l-2.286 2.286C.775 23.225 1.097 24 1.738 24H12c6.627 0 12-5.373 12-12S18.627 0 12 0Zm4.388 3.199c1.104 0 1.999.895 1.999 1.999 0 1.105-.895 2-1.999 2-.946 0-1.739-.657-1.947-1.539v.002c-1.147.162-2.032 1.15-2.032 2.341v.007c1.776.067 3.4.567 4.686 1.363.473-.363 1.064-.58 1.707-.58 1.547 0 2.802 1.254 2.802 2.802 0 1.117-.655 2.081-1.601 2.531-.088 3.256-3.637 5.876-7.997 5.876-4.361 0-7.905-2.617-7.998-5.87-.954-.447-1.614-1.415-1.614-2.538 0-1.548 1.255-2.802 2.803-2.802.645 0 1.239.218 1.712.585 1.275-.79 2.881-1.291 4.64-1.365v-.01c0-1.663 1.263-3.034 2.88-3.207.188-.911.993-1.595 1.959-1.595Zm-8.085 8.376c-.784 0-1.459.78-1.506 1.797-.047 1.016.64 1.429 1.426 1.429.786 0 1.371-.369 1.418-1.385.047-1.017-.553-1.841-1.338-1.841Zm7.406 0c-.786 0-1.385.824-1.338 1.841.047 1.017.634 1.385 1.418 1.385.785 0 1.473-.413 1.426-1.429-.046-1.017-.721-1.797-1.506-1.797Zm-3.703 4.013c-.974 0-1.907.048-2.77.135-.147.015-.241.168-.183.305.483 1.154 1.622 1.964 2.953 1.964 1.33 0 2.47-.81 2.953-1.964.057-.137-.037-.29-.184-.305-.863-.087-1.795-.135-2.769-.135Z", "FF4500"),
    "YouTube": ("M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z", "FF0000"),
    "E-Mail": ("M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm1.6 2L12 12.6 19.4 7H4.6zM4 9.2V17h16V9.2l-8 6-8-6z", "EA4335"),
    "Copy": ("M10.6 13.4a1 1 0 0 1 0-1.4l3-3a3 3 0 0 1 4.2 4.2l-2 2a1 1 0 1 1-1.4-1.4l2-2a1 1 0 0 0-1.4-1.4l-3 3a1 1 0 0 1-1.4 0zM13.4 10.6a1 1 0 0 1 0 1.4l-3 3a3 3 0 0 1-4.2-4.2l2-2a1 1 0 0 1 1.4 1.4l-2 2a1 1 0 0 0 1.4 1.4l3-3a1 1 0 0 1 1.4 0z", "6B7280"),
}


def brand_icon(name):
    p, hx = BRAND_ICONS[name]
    return f'<svg class="ic" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" fill="currentColor" style="--bc:#{hx}"><path d="{p}"/></svg>'


def share_html(lang, url, title):
    from urllib.parse import quote
    u, t = quote(url, safe=""), quote(strip_tags(title), safe="")
    nets = [("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={u}"), ("X", f"https://twitter.com/intent/tweet?url={u}&text={t}"),
            ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}"), ("WhatsApp", f"https://wa.me/?text={t}%20{u}"),
            ("Telegram", f"https://t.me/share/url?url={u}&text={t}"), ("Reddit", f"https://www.reddit.com/submit?url={u}&title={t}"),
            ("E-Mail", f"mailto:?subject={t}&body={u}")]
    links = "".join(f'<a class="btn" href="{h}" target="_blank" rel="noopener nofollow">{n}</a>' for n, h in nets)
    fl = "".join(f'<a href="{h}" target="_blank" rel="noopener nofollow" aria-label="{n}" title="{n}" style="--bc:#{BRAND_ICONS[n][1]}">{brand_icon(n)}</a>' for n, h in nets)
    fbar = (f'<aside class="fshare" aria-label="{esc(SHARE_L.get(lang, "Share"))}">{fl}'
            f'<button type="button" data-share data-url="{url}" data-title="{esc(strip_tags(title))}" aria-label="{esc(COPY_L.get(lang, "Copy link"))}" title="{esc(COPY_L.get(lang, "Copy link"))}" style="--bc:#6B7280">{brand_icon("Copy")}</button></aside>')
    return (fbar + f'<div class="share"><div class="wrap"><b>{esc(SHARE_L.get(lang, "Share"))}</b>{links}'
            f'<button type="button" class="btn" data-share data-url="{url}" data-title="{esc(strip_tags(title))}">{esc(COPY_L.get(lang, "Copy link"))}</button></div></div>'
            "<script>document.querySelectorAll('[data-share]').forEach(function(b){b.addEventListener('click',function(){var u=b.dataset.url,t=b.dataset.title;"
            "if(navigator.share){navigator.share({title:t,url:u}).catch(function(){})}else if(navigator.clipboard){navigator.clipboard.writeText(u).then(function(){var o=b.textContent;b.textContent='✓';setTimeout(function(){b.textContent=o},1500)})}})});</script>")


CLARITY_ID = "z5dkd64e41"
CONSENT = {
    "de": ("Wir nutzen Microsoft Clarity zur Nutzungsanalyse.", "Akzeptieren", "Ablehnen"), "es": ("Usamos Microsoft Clarity para analizar el uso.", "Aceptar", "Rechazar"),
    "fr": ("Nous utilisons Microsoft Clarity pour analyser l'usage.", "Accepter", "Refuser"), "it": ("Usiamo Microsoft Clarity per analizzare l'utilizzo.", "Accetta", "Rifiuta"),
    "pt": ("Usamos o Microsoft Clarity para analisar o uso.", "Aceitar", "Recusar"), "nl": ("We gebruiken Microsoft Clarity voor gebruiksanalyse.", "Accepteren", "Weigeren"),
    "pl": ("Używamy Microsoft Clarity do analizy korzystania ze strony.", "Akceptuję", "Odrzucam"), "id": ("Kami memakai Microsoft Clarity untuk analisis penggunaan.", "Terima", "Tolak"),
    "ru": ("Мы используем Microsoft Clarity для анализа использования сайта.", "Принять", "Отклонить"), "uk": ("Ми використовуємо Microsoft Clarity для аналізу використання сайту.", "Прийняти", "Відхилити"),
    "ar": ("نستخدم Microsoft Clarity لتحليل الاستخدام.", "قبول", "رفض"), "he": ("אנו משתמשים ב-Microsoft Clarity לניתוח שימוש.", "אישור", "דחייה"),
    "hi": ("हम उपयोग विश्लेषण के लिए Microsoft Clarity का उपयोग करते हैं।", "स्वीकार करें", "अस्वीकार करें"), "ja": ("利用状況の分析に Microsoft Clarity を使用しています。", "同意する", "拒否する"),
    "ko": ("이용 분석을 위해 Microsoft Clarity를 사용합니다.", "동의", "거부"), "ml": ("ഉപയോഗ വിശകലനത്തിനായി ഞങ്ങൾ Microsoft Clarity ഉപയോഗിക്കുന്നു.", "അംഗീകരിക്കുക", "നിരസിക്കുക"),
    "pa": ("ਅਸੀਂ ਵਰਤੋਂ ਦੇ ਵਿਸ਼ਲੇਸ਼ਣ ਲਈ Microsoft Clarity ਵਰਤਦੇ ਹਾਂ।", "ਮਨਜ਼ੂਰ", "ਇਨਕਾਰ"), "ta": ("பயன்பாட்டு பகுப்பாய்விற்கு Microsoft Clarity பயன்படுத்துகிறோம்.", "ஏற்கிறேன்", "மறுக்கிறேன்"),
    "te": ("వినియోగ విశ్లేషణ కోసం మేము Microsoft Clarity ఉపయోగిస్తాము.", "అంగీకరించు", "తిరస్కరించు"), "en": ("We use Microsoft Clarity for usage analytics.", "Accept", "Decline")}


def consent_html(lang):
    m, a, d = CONSENT.get(lang, CONSENT["en"])
    return (f'<div id="cc" class="cc" hidden><span>{esc(m)}</span><button type="button" class="btn main" id="cc1">{esc(a)}</button><button type="button" class="btn" id="cc0">{esc(d)}</button></div>'
            "<script>(function(){var K='m365-consent',v=null;try{v=localStorage.getItem(K)}catch(e){}"
            "function load(){(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src='https://www.clarity.ms/tag/'+i;"
            f"y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y)}})(window,document,'clarity','script','{CLARITY_ID}')}}"
            "var b=document.getElementById('cc');if(v==='1'){load()}else if(v===null){b.hidden=false}"
            "function set(x){try{localStorage.setItem(K,x)}catch(e){}b.hidden=true;if(x==='1')load()}"
            "document.getElementById('cc1').onclick=function(){set('1')};document.getElementById('cc0').onclick=function(){set('0')}})();</script>")


def page(lang, title, desc, canonical, body, alternates=None, jsonld=None, xdefault=None, og_type="article", extra_head="", noindex=False):
    hl = LANGS[lang][1] if lang in LANGS else "en"
    d = LANGS[lang][2] if lang in LANGS else "ltr"
    loc = LANGS[lang][4] if lang in LANGS else "en_US"
    alt = ""
    if alternates:
        for l, u in alternates.items():
            alt += f'<link rel="alternate" hreflang="{LANGS[l][1]}" href="{u}">\n'
        alt += f'<link rel="alternate" hreflang="x-default" href="{xdefault or BASE + "/"}">\n'
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>\n' for j in (jsonld or []))
    if canonical.endswith("404.html") or noindex:
        ogimg = f"{BASE}/assets/og-default.png"
    else:
        rel = canonical.replace(BASE, "").strip("/") or "index"
        OGLIST.append({"path": f"og/{rel}.png", "title": strip_tags(title), "lang": lang, "seed": canonical, "cover": OG_COVER.get(canonical)})
        ogimg = f"{BASE}/og/{rel}.png"
        body = body.replace("<footer>", share_html(lang, canonical, title) + "<footer>", 1)
    return f"""<!doctype html>
<html lang="{hl}" dir="{d}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(seo_title(title) if og_type == "article" else title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Mirko Peters"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-image-preview:large,max-snippet:-1'}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{BASE}/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="{BASE}/assets/favicon-32.png" sizes="32x32" type="image/png"><link rel="shortcut icon" href="{BASE}/assets/favicon.ico"><link rel="apple-touch-icon" href="{BASE}/assets/apple-touch-icon.png"><meta name="theme-color" content="#1d2126">
{alt}<meta property="og:type" content="{og_type}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:locale" content="{loc}"><meta property="og:site_name" content="M365.FM">
<meta property="og:image" content="{ogimg}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(title)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{ogimg}">
{extra_head}<style>{CSS}</style>
{ld}</head>
<body>
{body}
{consent_html(lang)}
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


def yt_thumb(vid, alt=""):
    """YouTube-Vorschaubild (16:9) fuer Uebersichten/Listen."""
    return (f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" srcset="https://i.ytimg.com/vi/{vid}/mqdefault.jpg 320w, https://i.ytimg.com/vi/{vid}/hqdefault.jpg 480w, '
            f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg 1280w" sizes="(max-width:700px) 92vw, 380px" alt="{esc(alt)}" width="480" height="360" loading="lazy" '
            f'style="width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;display:block">')


COVER_CTX = {}   # (vid, lang) -> dict(title, cat_label, cats, tags, spec)
OG_COVER = {}    # canonical -> svg (fuer Teilen-Bilder)


def art_svg(seed, big, small="M365.FM · AI", lang=None):
    c = COVER_CTX.get((seed, lang)) if lang else None
    if c:
        return site_cover.cover_svg(seed, lang, big, c["title"], c["cat_label"], c["cats"], c["tags"], c["spec"], uid=f"{seed}{lang}".replace("-", "").replace("_", ""))
    return _art_svg_old(seed, big, small)


def _art_svg_old(seed, big, small="M365.FM · AI"):
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
            f'<text x="60" y="92" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-size="68" font-weight="700" fill="#f6f1ea">{esc(big)}</text>'
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
    return f'<div class="top"><div class="wrap"><a class="brand" href="{home}">M365<i>.</i>FM <span class="dub">DUB</span></a>{switch}</div></div>'


def footer(lang):
    ui = UI.get(lang)
    about = ui[5] if ui else "About Mirko Peters"
    return (f'<footer><div class="wrap"><a href="{BASE}/about/mirko-peters/">{esc(about)}</a><a href="https://www.m365.fm">m365.fm</a>'
            f'<a href="https://m365con.net">M365Con</a><a class="soc" href="{LINKEDIN}" rel="me" style="--bc:#0A66C2">{brand_icon("LinkedIn")}<span>LinkedIn</span></a><a class="soc" href="{YT_CHANNEL}" style="--bc:#FF0000">{brand_icon("YouTube")}<span>YouTube</span></a><a href="{MVP}" rel="me">Microsoft MVP</a>'
            f'<a href="{BASE}/impressum/" rel="nofollow">Impressum</a><a href="{BASE}/legal/" rel="nofollow">Legal notice</a>'
            f'<a href="{BASE}/datenschutz/" rel="nofollow">Datenschutz</a><a href="{BASE}/privacy/" rel="nofollow">Privacy</a>'
            f'<div style="margin-top:10px">© {date.today().year} Mirko Peters · M365.FM</div></div></footer>')


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
    topdata = json.load(open(ROOT / "data" / "top.json", encoding="utf-8")) if (ROOT / "data" / "top.json").exists() else {}
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

    # Taxonomie: Kategorien (video-weit) + sprachbezogene Tags
    cat_of = {}
    for vid, langs in eps.items():
        texts = [langs.get("de", next(iter(langs.values())))["title"]] + [e.get("tags", "") for e in langs.values()]
        cat_of[vid] = classify(texts)
    tagraw = {l: {} for l in by_lang}      # lang -> vid -> [Tags in dieser Sprache]
    for (vid, l), it in items.items():
        tagraw[l][vid] = tags_of(it["e"])
    tagsets = {l: {v: {t.lower() for t in ts} for v, ts in d.items()} for l, d in tagraw.items()}
    catsets = {l: {v: set(cat_of[v]) for v in d} for l, d in tagraw.items()}
    tagidx = {l: {} for l in by_lang}      # lang -> slug -> {"label", "items"}
    for (vid, l), it in items.items():
        for t in tagraw[l][vid]:
            s = tag_slug(t)
            if s:
                tagidx[l].setdefault(s, {"label": t, "items": []})["items"].append(it)
    catidx = {l: {} for l in by_lang}      # lang -> cat -> items
    for (vid, l), it in items.items():
        for c in cat_of[vid]:
            catidx[l].setdefault(c, []).append(it)
    covers = {}
    for p in glob.glob(str(ROOT / "data" / "covers" / "*.json")):
        try:
            covers[Path(p).stem] = json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    for (vid, l), it in items.items():
        cs = [c for c in ORDER if c in cat_of[vid]]
        COVER_CTX[(vid, l)] = {"title": it["e"]["title"], "cats": cs, "cat_label": cat_name(cs[0], l) if cs else "", "tags": tagraw[l][vid],
                               "spec": (covers.get(vid) or {}).get(l)}
    cat_url = lambda l, c: f"{BASE}/{l}/c/{c}/"
    autolink_log = []

    def chips_html(l, it):
        out = "".join(f'<a class="chip cat" href="{cat_url(l, c)}">{esc(cat_name(c, l))}</a>' for c in ORDER if c in cat_of[it["vid"]] and c in catidx[l])
        for t in tagraw[l][it["vid"]]:
            s = tag_slug(t)
            if s and len(tagidx[l][s]["items"]) >= 2:
                out += f'<a class="chip" rel="tag" href="{tag_url(BASE, l, t)}">{esc(t)}</a>'
            elif s:
                out += f'<span class="chip">{esc(t)}</span>'
        return f'<div class="chips">{out}</div>' if out else ""

    def top_for(l, n=10):
        rows = (topdata.get("langs") or {}).get(l) or []
        by_eid = {i["eid"]: i for i in by_lang.get(l, [])}
        out = [by_eid[r["episode_id"]] for r in rows if r.get("score", 0) > 0 and r["episode_id"] in by_eid]
        return out[:n]

    def top_block(l):
        t = top_for(l, 5)
        if not t:
            return ""
        return (f'<h2>★ {esc(TOP_L.get(l, TOP_L["en"]))}</h2><div class="list">' + "".join(
            f'<a class="row" href="{url_of(x)}" title="{esc(x["e"]["title"])}"><h3>{n + 1}. {esc(anchor_title(x["e"]["title"]))}</h3></a>' for n, x in enumerate(t)) +
            f'</div><p><a class="btn" href="{BASE}/{l}/top/">{esc(TOP_L.get(l, TOP_L["en"]))} →</a></p>')

    def topics_nav(l):
        cs = "".join(f'<a class="chip cat" href="{cat_url(l, c)}">{esc(cat_name(c, l))} · {len(catidx[l][c])}</a>' for c in ORDER if c in catidx[l])
        return top_block(l) + f'<h2>{esc(TOPICS.get(l, "Topics"))}</h2><div class="chips">{cs}</div>'

    # Episoden-Seiten
    for (vid, l), it in items.items():
        e = it["e"]; ui = UI[l]
        intro, hdr, bullets, aud = parse_desc(e["desc"])
        alts = {x: url_of(by_vid[vid][x]) for x in by_vid[vid]}
        canonical = url_of(it)
        spk = f'https://www.spreaker.com/episode/{it["eid"]}'
        yt = f"https://youtu.be/{vid}"
        tr = e.get("tr") or ""
        more = related(it, by_lang[l], tagsets[l], catsets[l])
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
        pc = [c for c in ORDER if c in cat_of[vid]][0]
        ld[0]["genre"] = cat_name(pc, l)
        ld[0]["keywords"] = ", ".join(tagraw[l][vid]) or e.get("tags", "")
        art = articles.get(vid, {}).get(l, {})
        art_html = art.get("html", "")
        if art_html:
            art_html, _lk = autolink(art_html, it, by_lang[l], tagraw[l], url_of)
            autolink_log.append(((vid, l), _lk))
        if art_html and art.get("info"):
            ih = info_html(art["info"])
            art_html = re.sub(r"(</p>)", r"\1" + ih.replace("\\", "\\\\"), art_html, count=1) if ih else art_html
        if art_html:
            ld.append({"@context": "https://schema.org", "@type": "Article", "headline": e["title"][:110], "inLanguage": LANGS[l][1],
                       "datePublished": it["date"], "dateModified": it["date"], "mainEntityOfPage": canonical,
                       "author": {"@id": f"{BASE}/about/mirko-peters/#person"}, "publisher": {"@id": f"{BASE}/#org"},
                       "wordCount": len(strip_tags(art_html).split()), "articleSection": cat_name(pc, l), "keywords": ", ".join(tagraw[l][vid])})
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
        rel = "".join(f'<a class="row" href="{url_of(x)}" title="{esc(x["e"]["title"])}"><h3>{esc(anchor_title(x["e"]["title"]))}</h3></a>' for x in more)
        body = f"""{header(l, lang_switch(l, alts, [x for x in LANGS if x in alts]))}
<main class="wrap"><article>
<div class="crumbs"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])} / {it["date"]}</div>
<div class="kicker">M365.FM · {esc(LANGS[l][0])}</div>
<h1>{esc(e["title"])}</h1>
{chips_html(l, it)}<p class="lede">{intro}</p>
<figure class="cover" style="margin-inline:0">{art_svg(vid, LANGS[l][0], "M365.FM · " + ui[0], l)}</figure>
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
        OG_COVER[canonical] = art_svg(vid, LANGS[l][0], lang=l)
        write(f'{l}/{it["slug"]}/index.html',
              page(l, e["title"], short(intro), canonical, body, alts, ld, extra_head=f'<meta property="article:section" content="{esc(cat_name(pc, l))}">' + "".join(f'<meta property="article:tag" content="{esc(t)}">' for t in tagraw[l][vid])))
        sitemap.append((canonical, it["date"], alts))

    # Sprach-Startseiten
    for l in active:
        ui = UI[l]; s = seo.get(l, {})
        alts_home = {x: f"{BASE}/{x}/" for x in active}
        title = s.get("title") or f"M365.FM – {LANGS[l][0]}"
        d = short(s.get("description", ""), 300)
        newest = by_lang[l]
        thumbs = "".join(
            f'<div class="thumb"><a href="{url_of(i)}" title="{esc(i["e"]["title"])}"><figure class="cover" style="margin-inline:0">{yt_thumb(i["vid"], "")}</figure><h3>{esc(anchor_title(i["e"]["title"]))}</h3></a><p>{esc(short(parse_desc(i["e"]["desc"])[0], 110))}</p></div>'
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
        topics_html = topics_nav(l)
        body = f"""{header(l, lang_switch(l, alts_home, active))}
<main class="wrap"><div class="hero"><div class="kicker">{esc(LANGS[l][0])} · {esc(EN_NAMES.get(l, ""))} · M365.FM</div><h1>{esc(title)}</h1><p class="lede">{esc(d)}</p>
<div class="btns">{sbtn}</div></div>{topics_html}
<div class="stats"><div><b>{len(newest)}</b><span>{esc(ui[3])}</span></div><div><b>{nvid}</b><span>Videos</span></div><div><b>{len(active)}</b><span>Languages</span></div></div>
<div class="sec"><div class="kicker">01 · {esc(ui[3])}</div><div class="thumbs">{thumbs}</div></div></main>
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
    lt = "".join(f'<div class="thumb"><a href="{url_of(i)}" hreflang="{LANGS[i["lang"]][1]}" title="{esc(i["e"]["title"])}"><figure class="cover" style="margin-inline:0">{yt_thumb(i["vid"], "")}</figure><h3>{esc(anchor_title(i["e"]["title"]))}</h3></a><p>{esc(LANGS[i["lang"]][0])}</p></div>' for i in latest)
    nvid_all = len(by_vid)
    rows = [(l, LANGS[l][0], EN_NAMES.get(l, ""), f"{BASE}/{l}/") for l in active]
    tiles = "".join(lang_tile(l, LANGS[l][0], EN_NAMES.get(l, ""), f"{BASE}/{l}/", LANGS[l][1], f"{len(by_lang[l])} episodes") for l in active)
    tiles += lang_tile("EN", "English", "Original", "https://www.m365.fm", "en", "Main show", True)
    steps = [("01", "Animated original", "Each Sticky Man Explained episode is produced in English on the m365 Show YouTube channel."),
             ("02", "Dub tracks", "Every available language track is picked up – German, Spanish, Japanese and more."),
             ("03", "One show per language", f"Each dub becomes an episode in its own language edition of M365.FM ({len(active)} languages)."),
             ("04", "Any podcast app", "Listen on Spreaker, Apple Podcasts, Spotify, Amazon Music, Deezer or wherever you listen.")]
    topics_root = " ".join(f'<span class="chip">{esc(t)}</span>' for t in ("Microsoft 365 Copilot", "AI agents", "Teams", "SharePoint", "Exchange", "Power Platform", "Microsoft Fabric", "Entra ID", "Purview", "Azure", "Security", "Governance"))
    root_body = f"""{header('en', '')}
<main class="wrap"><div class="hero"><div class="kicker" style="max-width:34em">Microsoft 365 · Copilot · Azure · AI</div>
<h1>The M365.FM podcast <em>in {len(active)} languages</em></h1>
<p class="lede">Animated explainers about Microsoft 365, Copilot, Azure and the Power Platform by Microsoft MVP Mirko Peters – as AI-dubbed audio episodes in your language. Free, with transcripts.</p>
<div class="btns"><a class="btn main" href="#languages">Choose your language ↓</a><a class="btn" href="{YT_CHANNEL}">Watch on YouTube</a><a class="btn" href="{BASE}/about/mirko-peters/">About Mirko Peters</a></div></div>
{spec_box("Now dubbed", f"{len(active)} editions", rows[:6])}
<div class="stats"><div><b>{len(items)}</b><span>Episodes</span></div><div><b>{nvid_all}</b><span>Videos</span></div><div><b>{len(active)}</b><span>Languages</span></div><div><b>0 €</b><span>Free</span></div></div>
{section(1, "Languages", f'<div class="lgrid">{tiles}</div>', "languages")}
{section(2, "How it works", spec_table("From one video to many shows", ("No.", "Step", "Detail"), steps))}
{section(3, "Latest episodes", f'<div class="thumbs">{lt}</div>')}
{section(4, "Topics", f'<h2 style="margin-top:0">The Microsoft cloud, one concept at a time</h2><div class="chips">{topics_root}</div>')}</main>
{m365con_band()}
<main class="wrap">{faq_html('en', 'FAQ')}{cta_box("Want the full interviews?", "The main M365.FM show brings 900+ conversations with Microsoft MVPs, product experts and architects – in English.", "Go to M365.FM", "https://www.m365.fm")}{author_box('en')}</main>{footer_en()}"""
    write("index.html", page("en", "M365.FM – Microsoft 365, Copilot & AI podcast in 19 languages | Mirko Peters",
          "AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure and Power Platform by Microsoft MVP Mirko Peters – in German, Spanish, French, Japanese and more.",
          f"{BASE}/", root_body, alts_home, [person_ld(), org_ld(), event_ld(), faq_ld("en"), {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{BASE}/#website", "name": "M365.FM international", "url": f"{BASE}/", "inLanguage": [LANGS[x][1] for x in active], "publisher": {"@id": f"{BASE}/#org"}, "author": {"@id": f"{BASE}/about/mirko-peters/#person"}}], og_type="website"))
    sitemap.append((f"{BASE}/", TODAY, None))

    # Rechtliche Seiten (noindex)
    import site_legal as SL
    for path, fn, lg, ttl in (("impressum", SL.impressum_de, "de", "Impressum"), ("legal", SL.impressum_en, "en", "Legal notice"),
                              ("datenschutz", SL.privacy_de, "de", "Datenschutz"), ("privacy", SL.privacy_en, "en", "Privacy policy")):
        write(f"{path}/index.html", page(lg, f"{ttl} – M365.FM", ttl, f"{BASE}/{path}/", f"{header(lg, '')}<main class=\"wrap\" style=\"max-width:46em\">{fn()}</main>{footer(lg)}", og_type="website", noindex=True))

    # Entity-Seite
    PORTRAIT = (f'<img class="portrait" src="{BASE}/assets/mirko-peters.jpg" alt="Mirko Peters, Microsoft MVP, host of M365.FM" width="190" height="190">' if (ROOT / "assets" / "mirko-peters.jpg").exists() else "")
    about = f"""{header('en', '')}
<main class="wrap"><div class="kicker">Microsoft MVP · Podcaster · Conference organizer</div>{PORTRAIT}<h1>Mirko Peters</h1>
<p class="lede">Mirko Peters is a Microsoft MVP who explains Microsoft 365, Microsoft Copilot, Azure, Power Platform, Microsoft Fabric and AI agents for IT admins, architects, developers and decision makers. He hosts the podcast <a href="https://www.m365.fm">M365.FM</a> and the <em>m365 Show</em> on YouTube, and organizes the free online conference <a href="https://m365con.net">M365Con</a>.</p>
<div class="btns"><a class="btn main" href="https://www.m365.fm">M365.FM</a><a class="btn" href="https://m365con.net">M365Con</a><a class="btn" href="{LINKEDIN}" rel="me">LinkedIn</a><a class="btn" href="{YT_CHANNEL}">YouTube</a><a class="btn" href="{MVP}" rel="me">Microsoft MVP profile</a></div>
<h2>What Mirko works on</h2>
<div class="cols"><div><h3>Podcast</h3><p>M365.FM covers Microsoft 365, Copilot, Azure, Power Platform and security – practical, from real projects, with new episodes every week.</p></div>
<div><h3>Video</h3><p>The m365 Show on YouTube turns complex Microsoft topics into short animated explainers, now also available as AI-dubbed audio in {len(active)} languages.</p></div>
<div><h3>Community</h3><p>M365Con is a free, 100% online conference (Jan 11–22, 2027) with 120 sessions by speakers from the global Microsoft community.</p></div></div>
<h2>Topics</h2>
<p>Microsoft 365 Copilot · Copilot Studio · AI agents · Azure AI Foundry · Power Platform · Microsoft Fabric · Microsoft Entra · Microsoft Purview · Microsoft Teams · SharePoint · Dynamics 365 · Governance &amp; security</p>
<h2>Find Mirko Peters online</h2>
<ul class="points"><li><span><a href="https://www.m365.fm">m365.fm</a> – the podcast and episode archive</span></li><li><span><a href="https://m365con.net">m365con.net</a> – free online conference</span></li><li><span><a href="{LINKEDIN}" rel="me">LinkedIn</a></span></li><li><span><a href="{YT_CHANNEL}">YouTube – m365 Show by Mirko Peters</a></span></li><li><span><a href="{MVP}" rel="me">Microsoft MVP profile</a> – official Microsoft recognition</span></li></ul>
<h2>Podcast episodes by language</h2><div class="grid">{grid}</div></main>
{m365con_band()}
<main class="wrap">{faq_html('en', 'FAQ')}</main>{footer_en()}"""
    write("about/mirko-peters/index.html", page("en", "Mirko Peters – Microsoft MVP, M365.FM podcast host & M365Con organizer",
          "Mirko Peters is a Microsoft MVP and host of the M365.FM podcast about Microsoft 365, Copilot, Azure and AI. Organizer of the free online conference M365Con.",
          f"{BASE}/about/mirko-peters/", about, None, [{"@context": "https://schema.org", "@type": "ProfilePage", "@id": f"{BASE}/about/mirko-peters/#profile", "url": f"{BASE}/about/mirko-peters/", "name": "Mirko Peters", "dateModified": TODAY, "mainEntity": {"@id": f"{BASE}/about/mirko-peters/#person"}}, person_ld(), org_ld(), event_ld(), faq_ld("en")], og_type="profile"))
    sitemap.append((f"{BASE}/about/mirko-peters/", TODAY, None))

    # Kategorie-Seiten (indexierbar, in Sitemap) und Tag-Seiten (noindex,follow – nur für die interne Verlinkung)
    def rows_html(lst):
        return "".join(f'<div class="row"><a href="{url_of(x)}" title="{esc(x["e"]["title"])}"><h3>{esc(anchor_title(x["e"]["title"]))}</h3></a><p>{esc(short(parse_desc(x["e"]["desc"])[0], 150))}</p></div>' for x in lst)

    def list_page(l, kind, label, lst, canonical, alts, noindex):
        ui = UI[l]
        lst = sorted(lst, key=lambda i: (i["date"], i["vid"]), reverse=True)
        others = "".join(f'<a class="chip cat" href="{cat_url(l, c)}">{esc(cat_name(c, l))}</a>' for c in ORDER if c in catidx[l])
        desc = short(f"{label} – {len(lst)} · " + " · ".join(strip_tags(x["e"]["title"]).split(":")[0] for x in lst[:3]), 155)
        ld = [] if noindex else [
            {"@context": "https://schema.org", "@type": "CollectionPage", "name": label, "url": canonical, "inLanguage": LANGS[l][1],
             "isPartOf": {"@id": f"{BASE}/#website"}, "about": {"@type": "Thing", "name": label},
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(lst), "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": url_of(i)} for n, i in enumerate(lst[:50])]}},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "M365.FM", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": LANGS[l][0], "item": f"{BASE}/{l}/"},
                {"@type": "ListItem", "position": 3, "name": label, "item": canonical}]}]
        body = f"""{header(l, lang_switch(l, alts or {}, active))}
<main class="wrap"><div class="crumbs"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])}</div>
<div class="kicker">{esc(kind)} · {esc(LANGS[l][0])}</div><h1>{esc(label)}</h1>
<p class="mut">{len(lst)} × {esc(ui[3])}</p>
<h2>{esc(ui[3])}</h2><div class="list">{rows_html(lst)}</div>
<h2>{esc(TOPICS.get(l, "Topics"))}</h2><div class="chips">{others}</div>
<p style="margin-top:1.6em"><a class="btn" href="{BASE}/{l}/">{esc(ui[3])} →</a></p></main>{footer(l)}"""
        return page(l, label, desc, canonical, body, alts, ld, og_type="website", noindex=noindex)

    ncat = ntag = 0
    for l in active:
        for c in ORDER:
            if c not in catidx[l]:
                continue
            alts = {x: cat_url(x, c) for x in active if c in catidx[x]}
            u = cat_url(l, c)
            write(f"{l}/c/{c}/index.html", list_page(l, TOPICS.get(l, "Topics"), cat_name(c, l), catidx[l][c], u, alts, False))
            sitemap.append((u, TODAY, alts))
            ncat += 1
        for s, d in tagidx[l].items():
            if len(d["items"]) >= 2:
                write(f"{l}/tag/{s}/index.html", list_page(l, TAGW.get(l, "Tag"), d["label"], d["items"], tag_url(BASE, l, d["label"]), None, True))
                ntag += 1
    print(ncat, "Kategorie-Seiten,", ntag, "Tag-Seiten (noindex),", sum(len(v) for _, v in autolink_log), "automatische interne Links in", sum(1 for _, v in autolink_log if v), "Artikeln")

    # "Top diese Woche" je Sprache (nur wenn Statistik-Daten vorliegen)
    topfeed = {}
    for l in active:
        t = top_for(l, 10)
        if not t:
            continue
        label = TOP_L.get(l, TOP_L["en"])
        u = f"{BASE}/{l}/top/"
        ui = UI[l]
        wk = topdata.get("week_end", TODAY)
        rows = "".join(f'<div class="row"><a href="{url_of(x)}" title="{esc(x["e"]["title"])}"><h3>{n + 1}. {esc(anchor_title(x["e"]["title"]))}</h3></a><p>{esc(short(parse_desc(x["e"]["desc"])[0], 150))}</p></div>' for n, x in enumerate(t))
        ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": label, "url": u, "inLanguage": LANGS[l][1], "dateModified": wk,
               "mainEntity": {"@type": "ItemList", "itemListOrder": "https://schema.org/ItemListOrderDescending", "numberOfItems": len(t),
                              "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": url_of(x)} for n, x in enumerate(t)]}},
              {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "M365.FM", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": LANGS[l][0], "item": f"{BASE}/{l}/"},
                  {"@type": "ListItem", "position": 3, "name": label, "item": u}]}]
        alts = {x: f"{BASE}/{x}/top/" for x in active if top_for(x, 1)}
        body = f"""{header(l, lang_switch(l, alts, active))}
<main class="wrap"><div class="crumbs"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])}</div>
<div class="kicker">★ {esc(LANGS[l][0])} · {esc(wk)}</div><h1>{esc(label)}</h1>
<h2>{esc(ui[3])}</h2><div class="list">{rows}</div>
<p style="margin-top:1.6em"><a class="btn" href="{BASE}/{l}/">{esc(ui[3])} →</a></p></main>{footer(l)}"""
        write(f"{l}/top/index.html", page(l, f"{label} – M365.FM {LANGS[l][0]}", short(" · ".join(strip_tags(x["e"]["title"]).split(":")[0] for x in t[:3]), 155), u, body, alts, ld, og_type="website"))
        sitemap.append((u, wk, alts))
        topfeed[l] = [{"rank": n + 1, "title": strip_tags(x["e"]["title"]), "url": url_of(x), "episode": x["eid"]} for n, x in enumerate(t)]
    if topfeed:
        write("top.json", json.dumps({"period": "last 7 days", "from": topdata.get("from"), "to": topdata.get("week_end"), "languages": topfeed}, ensure_ascii=False, indent=1))
        print(len(topfeed), "Sprachen mit Top-Woche")

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
    write("robots.txt", f"User-agent: *\nAllow: /\n\n# KI-Suchen und Assistenten ausdrücklich erlaubt\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot")) + f"Sitemap: {BASE}/sitemap.xml\n")
    # llms.txt (Überblick), llms-full.txt (alle Folgen), agent.json (Maschinen-Beschreibung), episodes.json (Datenfeed)
    summ = (f"AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure, Power Platform and AI governance by Microsoft MVP Mirko Peters, "
            f"in {len(active)} languages. Each episode has its own page with player, YouTube video, key points, transcript link and links to Spotify, Amazon Music, Deezer and more.")
    L = [f"# M365.FM international – Mirko Peters", "", f"> {summ}", "",
         "Author: Mirko Peters (Microsoft MVP), host of the M365.FM podcast and the m365 Show on YouTube, organizer of M365Con (free online conference, 2027-01-11 to 2027-01-22).", "",
         "## Core", f"- [About Mirko Peters]({BASE}/about/mirko-peters/): profile, expertise, links", f"- [Microsoft MVP profile]({MVP}): official Microsoft MVP recognition of Mirko Peters", f"- [Full episode list]({BASE}/llms-full.txt): every episode with title, language and summary",
         f"- [Machine-readable feed]({BASE}/episodes.json): all episodes as JSON", f"- [Agent card]({BASE}/agent.json): capabilities for AI agents", f"- [Sitemap]({BASE}/sitemap.xml)", "",
         "## Languages"]
    for l in active:
        L.append(f"- [{LANGS[l][0]}]({BASE}/{l}/): {len(by_lang[l])} episodes – topics: " + ", ".join(cat_name(c, l) for c in ORDER if c in catidx[l]))
    L += ["", "## Topics (English labels; localized per language)"]
    for c in ORDER:
        L.append(f"- {cat_name(c, 'en')}: " + ", ".join(f"[{l}]({cat_url(l, c)})" for l in active if c in catidx[l]))
    write("llms.txt", "\n".join(L) + "\n")
    F = [f"# M365.FM international – all episodes", "", f"> {summ}", ""]
    for l in active:
        F += [f"## {LANGS[l][0]} ({l})", ""]
        for x in by_lang[l]:
            F.append(f"- [{strip_tags(x['e']['title'])}]({url_of(x)}) – {x['date']} – " + short(parse_desc(x["e"]["desc"])[0], 200))
        F.append("")
    write("llms-full.txt", "\n".join(F))
    feed = [{"id": x["vid"], "language": l, "title": strip_tags(x["e"]["title"]), "url": url_of(x), "date": x["date"], "summary": short(parse_desc(x["e"]["desc"])[0], 300),
             "categories": [cat_name(c, "en") for c in ORDER if c in cat_of[x["vid"]]], "tags": tagraw[l][x["vid"]], "youtube": f"https://youtu.be/{x['vid']}",
             "spreaker": f"https://www.spreaker.com/episode/{x['eid']}", "alternates": {k: url_of(v) for k, v in by_vid[x["vid"]].items()}}
            for l in active for x in by_lang[l]]
    write("episodes.json", json.dumps({"name": "M365.FM international", "author": "Mirko Peters", "generated": TODAY, "count": len(feed), "episodes": feed}, ensure_ascii=False))
    write("agent.json", json.dumps({
        "schemaVersion": "1.0", "name": "M365.FM international", "description": summ, "url": f"{BASE}/", "version": TODAY,
        "provider": {"organization": "M365.FM", "url": "https://www.m365.fm", "person": "Mirko Peters", "personUrl": f"{BASE}/about/mirko-peters/"},
        "documentationUrl": f"{BASE}/llms.txt", "license": "Content © Mirko Peters / M365.FM. Citation with link to the episode page welcome.",
        "capabilities": {"streaming": False, "readOnly": True, "authentication": "none"},
        "languages": [LANGS[l][1] for l in active],
        "interfaces": {"llms": f"{BASE}/llms.txt", "llmsFull": f"{BASE}/llms-full.txt", "episodesJson": f"{BASE}/episodes.json", "sitemap": f"{BASE}/sitemap.xml",
                       "rss": {l: f"https://www.spreaker.com/show/{LANGS[l][3]}/episodes/feed" for l in active}},
        "skills": [
            {"id": "find-episode", "name": "Find an episode", "description": "Find podcast episodes about Microsoft 365, Copilot, Azure, Power Platform, security and AI governance in a given language. Use episodes.json (filter by language, categories, tags) and link to the episode page.", "inputModes": ["text"], "outputModes": ["application/json", "text/html"]},
            {"id": "translate-link", "name": "Same episode in another language", "description": "Each episode page lists its alternate-language versions (hreflang / 'alternates' in episodes.json).", "inputModes": ["text"], "outputModes": ["application/json"]},
            {"id": "about-author", "name": "About Mirko Peters", "description": "Microsoft MVP, M365.FM host, M365Con organizer – see the about page.", "inputModes": ["text"], "outputModes": ["text/html"]}],
    }, ensure_ascii=False, indent=1))
    write(".well-known/agent.json", (OUT / "agent.json").read_text(encoding="utf-8"))
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)
    if _dom:
        write("CNAME", _dom)
    write("callback/index.html", """<!doctype html><meta charset=utf-8><meta name=robots content="noindex,nofollow"><meta name=viewport content="width=device-width,initial-scale=1"><title>Spreaker-Anmeldung</title>
<body style="font-family:system-ui,sans-serif;background:#101214;color:#e9ecef;padding:40px;max-width:640px;margin:auto"><h2>Spreaker-Anmeldung</h2><p id=m>Kein Code in der Adresse.</p>
<pre id=c style="white-space:pre-wrap;word-break:break-all;background:#1d2126;padding:14px;border:1px solid #444"></pre><button id=b style="display:none;padding:10px 18px">Code kopieren</button>
<script>var q=new URLSearchParams(location.search),c=q.get("code");if(c){document.getElementById("m").textContent="Code (in das Programm auf dem PC einfügen):";document.getElementById("c").textContent=c;var b=document.getElementById("b");b.style.display="inline-block";b.onclick=function(){navigator.clipboard.writeText(c);b.textContent="Kopiert ✓"}}else if(q.get("error")){document.getElementById("m").textContent="Fehler: "+q.get("error")}</script></body>""")
    write("og-manifest.json", json.dumps(OGLIST, ensure_ascii=False))
    write("404.html", page("en", "Not found", "Page not found", f"{BASE}/404.html", '<main class="wrap"><h1>404</h1><p><a class="btn" href="%s/">M365.FM</a></p></main>' % BASE))
    json.dump([u for u, _, _ in sitemap], open(ROOT / "data" / "urls.json", "w"), indent=0)
    print(f"{len(items)} Episodenseiten, {len(active)} Sprachen, {len(sitemap)} URLs → docs/")


def footer_en():
    return footer("en")


if __name__ == "__main__":
    (ROOT / "data").mkdir(exist_ok=True)
    build()
