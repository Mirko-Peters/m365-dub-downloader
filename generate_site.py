#!/usr/bin/env python3
"""Erzeugt die mehrsprachige SEO-Website (docs/) aus episodes/*.json + data/published.json.

Nur Python-Standardbibliothek. Lauf:  python generate_site.py
Basis-URL (z. B. eigene Domain):  SITE_BASE=https://international.m365.fm python generate_site.py
"""
import site_learn as LRN
import site_fetch as SF
import time
import site_press as PRS
import site_entities as ENT
from site_i18n import COMM_LANGS, pfx
import site_members as MEM
import site_events as EVT
import site_mcp as MCPS
import site_seo as SEOR
import site_live as LIVE
import site_notes as SNT
import site_shownotes as SNS   # T26
import site_extract as SX   # T27: Folgen und Videos <-> Entitaeten aus der QA-geprueften Extraktion
SNALL = SNS.load_all()   # Vollfassungen der Shownotes je Spreaker-Folge (shownotes/site/<episode_id>.md)
import site_text
import site_ads as ADS
import site_media as MED
import site_sidebar as SBR
import site_r2 as R2
import glob, hashlib, html, json, os, re, shutil, sys, unicodedata
from datetime import date
from pathlib import Path
import hashlib
import site_money as SM
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
    "ja": ("日本語", "ja", "ltr", 7393232, "ja_JP"),
    "ko": ("한국어", "ko", "ltr", 7393236, "ko_KR")
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
 "ja": ("今すぐ聴く", "YouTube で動画を見る", "文字起こしを読む", "すべてのエピソード", "他のエピソード", "Mirko Peters について",
        "Mirko Peters は Microsoft MVP であり、ポッドキャスト M365.FM のホスト、無料オンライン カンファレンス M365Con の主催者です。", "ホーム"),
 "ko": ("지금 듣기", "YouTube에서 영상 보기", "대본 읽기", "모든 에피소드", "다른 에피소드", "Mirko Peters 소개",
        "Mirko Peters는 Microsoft MVP이자 팟캐스트 M365.FM의 진행자이며 무료 온라인 컨퍼런스 M365Con의 주최자입니다.", "홈")
 }

CSS = """:root{--bg:#f6f1ea;--fg:#141210;--mut:#6b645c;--ac:#b4233c;--card:#fffdf9;--bd:#1412101f;--ink:#141210;--onink:#f6f1ea}
@media (prefers-color-scheme:dark){:root{--bg:#0e0d0c;--fg:#f1ebe2;--mut:#a39a8e;--ac:#ff5a72;--card:#171513;--bd:#f1ebe226;--ink:#f1ebe2;--onink:#0e0d0c}}
:root[data-theme=dark]{--bg:#0e0d0c;--fg:#f1ebe2;--mut:#a39a8e;--ac:#ff5a72;--card:#171513;--bd:#f1ebe226;--ink:#f1ebe2;--onink:#0e0d0c}
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
.auth-ch a{margin-right:.9em;font-size:.9em}.author{display:flex;gap:16px;align-items:center;border-top:1px solid var(--fg);border-bottom:1px solid var(--bd);padding:18px 0;margin:36px 0}
.author img.badge{object-fit:cover;border:2px solid var(--ac)}.portrait{float:right;width:190px;height:190px;object-fit:cover;border-radius:50%;border:3px solid var(--ac);margin:0 0 12px 22px}
.author .badge{flex:none;width:58px;height:58px;border-radius:50%;background:var(--ink);color:var(--onink);display:grid;place-items:center;font:700 1.15rem Didot,Georgia,serif}
.author p{margin:0;font-size:.95rem;color:var(--mut)}.author .auth-ex{margin:.5em 0 0}.author .auth-ul{list-style:none;display:flex;flex-wrap:wrap;gap:.35em .5em;padding:0;margin:.2em 0 0}.author .auth-ul li{border:1px solid var(--bd);border-radius:1em;padding:.05em .7em;font-size:.88rem}.author strong{color:var(--fg);display:block;font-size:1.02rem}
.mut{color:var(--mut);font-size:.9rem}.crumbs{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-top:26px}.crumbs a{text-decoration:none}
footer{border-top:1px solid var(--fg);margin-top:64px;padding:26px 0 48px;font-size:.85rem;color:var(--mut)}footer a{margin-right:14px}
.info{margin:1.6em 0;padding:20px 22px;border:1px solid var(--ln,#d9cfc2);background:#fff8;border-radius:6px}.info figcaption{font-family:Didot,"Bodoni 72",Georgia,serif;font-size:1.25rem;margin-bottom:14px}.info small{display:block;margin-top:12px;opacity:.6;font-size:.75rem}
.isteps{list-style:none;padding:0;margin:0;display:grid;gap:12px}.isteps li{display:grid;grid-template-columns:36px 1fr;gap:2px 12px;align-items:start}.isteps i{grid-row:span 2;width:32px;height:32px;border-radius:50%;background:var(--ac);color:#fff;font-style:normal;display:flex;align-items:center;justify-content:center;font-weight:700}.isteps b{font-size:1rem}.isteps span{font-size:.92rem;opacity:.85}
.icols{display:grid;grid-template-columns:1fr 1fr;gap:14px}.icol{border-top:3px solid var(--ac);padding-top:8px}.icol h4{margin:0 0 6px}.icol ul{margin:0;padding-left:18px}.ifacts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}.ifacts div{border-left:3px solid var(--ac);padding-left:10px}.ifacts b{display:block;font-size:1.5rem;font-family:Didot,"Bodoni 72",Georgia,serif}.ifacts span{font-size:.88rem}@media(max-width:560px){.icols{grid-template-columns:1fr}}
.article{margin-top:2em;max-width:42em}.article h2{margin-top:1.6em}.article p,.article li{line-height:1.75}.cc{position:fixed;left:12px;right:12px;bottom:12px;z-index:50;max-width:760px;margin:0 auto;background:var(--ink);color:var(--onink);padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;box-shadow:0 6px 28px #0006}.cc[hidden]{display:none}@media(max-width:1180px){body:has(.fshare) .cc{bottom:58px}}.cc span{flex:1 1 260px;font-size:.92rem}.cc .btn{padding:6px 14px;color:var(--onink);border-color:var(--onink)}.cc .btn.main{color:#fff;border-color:var(--ac)}.share{border-top:1px solid var(--ln,#d9cfc2);margin-top:2.5em;padding:16px 0}.share .wrap{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.share b{margin-right:6px}.share .btn{font-size:.85rem;padding:6px 12px}.showrow{font-size:.85rem;margin:10px 0 0}.showrow a{margin-right:12px}.yt{position:relative;margin:22px 0;aspect-ratio:16/9;background:#000;border-radius:4px;overflow:hidden;cursor:pointer}.yt img{width:100%;height:100%;object-fit:cover;opacity:.85}.yt button{position:absolute;inset:0;margin:auto;width:76px;height:76px;border-radius:50%;border:0;background:var(--ac);color:#fff;font-size:30px;cursor:pointer}.yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.cover{margin:18px 0 6px;border-radius:4px;overflow:hidden;line-height:0}.cover svg{width:100%;height:auto;display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0;border-top:1px solid var(--fg);border-bottom:1px solid var(--fg);margin:30px 0}
.stats div{padding:18px 14px;border-inline-end:1px solid var(--bd)}.stats b{display:block;font:700 2.4rem/1 Didot,"Bodoni 72",Georgia,serif;color:var(--ac)}.stats span{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px;margin:14px 0}
.thumb{display:block;text-decoration:none}.thumb .cover{margin:0 0 10px}.thumb h3{margin:0 0 .2em;font:700 1.08rem/1.3 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.thumb p{margin:0;font-size:.82rem;color:var(--mut)}.thumb:hover h3{color:var(--ac)}
.band{background:var(--ink);color:var(--onink);margin:46px 0;padding:34px 0}.band .wrap{display:grid;gap:10px}.band h2{margin:0}.band .btn:hover{background:var(--onink);color:var(--ink)}
.faq details{border-bottom:1px solid var(--bd);padding:14px 0}.faq summary{cursor:pointer;font:700 1.15rem/1.35 Didot,"Bodoni 72",Georgia,"Noto Serif",serif}.faq p{margin:.6em 0 0;color:var(--mut)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:22px;margin:16px 0}.cols h3{margin:.1em 0 .3em;font:700 1.15rem Didot,"Bodoni 72",Georgia,serif}.cols p{margin:0;color:var(--mut);font-size:.96rem}
@media (max-width:560px){body{font-size:16px}.panel{padding:14px}.btn{padding:10px 16px}}"""
from site_design import lang_dropdown, site_header, FONT_CSS, INDUSTRY, EN_NAMES, section, spec_box, lang_tile, spec_table, cta_box, hero_h1
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
    items = [(l, LANGS[l][0], alt_urls.get(l) or f"{BASE}/{l}/", LANGS[l][1]) for l in home_langs]
    if alt_urls.get("en"): items = [("en", "English", alt_urls["en"], "en")] + items   # Wechsel auf Seitenebene zum englischen Original (sonst /show/)
    return lang_dropdown(cur, items, "")


TOP_L = {"de": "Top-Folgen der Woche", "es": "Episodios más escuchados de la semana", "fr": "Épisodes les plus écoutés cette semaine", "it": "Episodi più ascoltati della settimana",
         "pt": "Episódios mais ouvidos da semana", "nl": "Meest beluisterde afleveringen van de week", "pl": "Najczęściej słuchane odcinki tygodnia", "id": "Episode terpopuler minggu ini",
         "ru": "Самые популярные выпуски недели", "uk": "Найпопулярніші випуски тижня", "ar": "أكثر الحلقات استماعًا هذا الأسبوع", "he": "הפרקים המובילים השבוע",
         "ja": "今週の人気エピソード", "ko": "이번 주 인기 에피소드", "en": "Top episodes this week"}
REC_L = {"de": "Empfohlene Folgen", "es": "Episodios recomendados", "fr": "Épisodes recommandés", "it": "Episodi consigliati", "pt": "Episódios recomendados",
         "nl": "Aanbevolen afleveringen", "pl": "Polecane odcinki", "id": "Episode pilihan", "ru": "Рекомендуемые выпуски", "uk": "Рекомендовані випуски",
         "ar": "حلقات مختارة", "he": "פרקים מומלצים", "ja": "おすすめエピソード", "ko": "추천 에피소드", "en": "Recommended episodes"}
OGLIST = []
TOP_REAL = set()   # Sprachen mit echten Statistikdaten (wird im Build gesetzt)
SHARE_L = {"de": "Teilen", "es": "Compartir", "fr": "Partager", "it": "Condividi", "pt": "Compartilhar", "nl": "Delen", "pl": "Udostępnij",
           "id": "Bagikan", "ru": "Поделиться", "uk": "Поділитися", "ar": "مشاركة", "he": "שיתוף", "ja": "シェア",
           "ko": "공유", "en": "Share"}
COPY_L = {"de": "Link kopieren", "es": "Copiar enlace", "fr": "Copier le lien", "it": "Copia link", "pt": "Copiar link", "nl": "Link kopiëren",
          "pl": "Kopiuj link", "id": "Salin tautan", "ru": "Копировать ссылку", "uk": "Копіювати посилання", "ar": "نسخ الرابط", "he": "העתקת קישור",
          "ja": "リンクをコピー", "ko": "링크 복사", "en": "Copy link"}


_BRAND_TAIL = re.compile(r"\s*[|–—-]\s*(?:M365[ .]?FM(?:\s+Podcast)?|M365 FM Podcast)\s*$", re.I)
BRAND = "M365.FM"


def bare_title(t):
    """Titel ohne angehaengte Marke (' – M365 FM Podcast', ' | M365.FM' usw.), fuer og:title, twitter:title und Teilen-Bild."""
    t = re.sub(r"\s+", " ", strip_tags(t)).strip()
    while True:
        u = _BRAND_TAIL.sub("", t).strip()
        if u == t or not u: return t
        t = u


def seo_title(t, limit=62, hard=78):
    """T7: eine Titel-Vorlage fuer alle Seiten. Marke genau einmal hinten (' | M365.FM'), wenn der Titel sie nicht schon enthaelt
    und alles in ~62 Zeichen passt; sonst der volle Titel ohne Marke (bis 78 Zeichen). Laengere Titel verlieren erst einen Anhang
    hinter dem letzten ' | ' oder ' – ' (wenn mindestens 40 Zeichen bleiben), sonst Schnitt an einer Wortgrenze mit Auslassungszeichen.
    Nie Schnitt am ersten Doppelpunkt: 'Microsoft Certified: …' wuerde sonst auf vielen Seiten gleich lauten."""
    b = bare_title(t)
    has = bool(re.search(r"M365[ .]?FM", b, re.I))
    tag = lambda x: x if has else f"{x} | {BRAND}"
    if len(tag(b)) <= limit or (has and len(b) <= hard): return tag(b)
    if len(b) <= hard: return b
    for sep in (" | ", " – ", " — "):
        if sep in b:
            head = b.rsplit(sep, 1)[0].strip()
            if 40 <= len(head) <= hard: return tag(head) if len(tag(head)) <= limit else head
    return b[: hard - 2].rsplit(" ", 1)[0].rstrip(",;:–—-") + "…"


def meta_desc(s, n=160):
    """Beschreibung fuer meta/og/twitter: hoechstens n Zeichen, bevorzugt am Satzende, sonst an einer Wortgrenze."""
    s = re.sub(r"\s+", " ", strip_tags(s or "")).strip()
    if len(s) <= n: return s
    cut = s[:n]
    m = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), cut.rfind("。"))
    if m >= 70: return cut[:m + 1].strip()
    return cut[: n - 1].rsplit(" ", 1)[0].rstrip(",;:–—-") + "…"


BRAND_ICONS = {
    "LinkedIn": ("M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z", "0A66C2"),
    "X": ("M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z", "000000"),
    "Facebook": ("M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z", "0866FF"),
    "WhatsApp": ("M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z", "25D366"),
    "Telegram": ("M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z", "26A5E4"),
    "Reddit": ("M12 0C5.373 0 0 5.373 0 12c0 3.314 1.343 6.314 3.515 8.485l-2.286 2.286C.775 23.225 1.097 24 1.738 24H12c6.627 0 12-5.373 12-12S18.627 0 12 0Zm4.388 3.199c1.104 0 1.999.895 1.999 1.999 0 1.105-.895 2-1.999 2-.946 0-1.739-.657-1.947-1.539v.002c-1.147.162-2.032 1.15-2.032 2.341v.007c1.776.067 3.4.567 4.686 1.363.473-.363 1.064-.58 1.707-.58 1.547 0 2.802 1.254 2.802 2.802 0 1.117-.655 2.081-1.601 2.531-.088 3.256-3.637 5.876-7.997 5.876-4.361 0-7.905-2.617-7.998-5.87-.954-.447-1.614-1.415-1.614-2.538 0-1.548 1.255-2.802 2.803-2.802.645 0 1.239.218 1.712.585 1.275-.79 2.881-1.291 4.64-1.365v-.01c0-1.663 1.263-3.034 2.88-3.207.188-.911.993-1.595 1.959-1.595Zm-8.085 8.376c-.784 0-1.459.78-1.506 1.797-.047 1.016.64 1.429 1.426 1.429.786 0 1.371-.369 1.418-1.385.047-1.017-.553-1.841-1.338-1.841Zm7.406 0c-.786 0-1.385.824-1.338 1.841.047 1.017.634 1.385 1.418 1.385.785 0 1.473-.413 1.426-1.429-.046-1.017-.721-1.797-1.506-1.797Zm-3.703 4.013c-.974 0-1.907.048-2.77.135-.147.015-.241.168-.183.305.483 1.154 1.622 1.964 2.953 1.964 1.33 0 2.47-.81 2.953-1.964.057-.137-.037-.29-.184-.305-.863-.087-1.795-.135-2.769-.135Z", "FF4500"),
    "YouTube": ("M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z", "FF0000"),
    "E-Mail": ("M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm1.6 2L12 12.6 19.4 7H4.6zM4 9.2V17h16V9.2l-8 6-8-6z", "EA4335"),
    "Copy": ("M10.6 13.4a1 1 0 0 1 0-1.4l3-3a3 3 0 0 1 4.2 4.2l-2 2a1 1 0 1 1-1.4-1.4l2-2a1 1 0 0 0-1.4-1.4l-3 3a1 1 0 0 1-1.4 0zM13.4 10.6a1 1 0 0 1 0 1.4l-3 3a3 3 0 0 1-4.2-4.2l2-2a1 1 0 0 1 1.4 1.4l-2 2a1 1 0 0 0 1.4 1.4l3-3a1 1 0 0 1 1.4 0z", "6B7280")
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
    return fbar   # Klick-Logik in assets/page.js


CLARITY_ID = "v5hs0d3310"
CONSENT = {
    "de": ("Wir nutzen Microsoft Clarity zur Nutzungsanalyse.", "Akzeptieren", "Ablehnen"), "es": ("Usamos Microsoft Clarity para analizar el uso.", "Aceptar", "Rechazar"),
    "fr": ("Nous utilisons Microsoft Clarity pour analyser l'usage.", "Accepter", "Refuser"), "it": ("Usiamo Microsoft Clarity per analizzare l'utilizzo.", "Accetta", "Rifiuta"),
    "pt": ("Usamos o Microsoft Clarity para analisar o uso.", "Aceitar", "Recusar"), "nl": ("We gebruiken Microsoft Clarity voor gebruiksanalyse.", "Accepteren", "Weigeren"),
    "pl": ("Używamy Microsoft Clarity do analizy korzystania ze strony.", "Akceptuję", "Odrzucam"), "id": ("Kami memakai Microsoft Clarity untuk analisis penggunaan.", "Terima", "Tolak"),
    "ru": ("Мы используем Microsoft Clarity для анализа использования сайта.", "Принять", "Отклонить"), "uk": ("Ми використовуємо Microsoft Clarity для аналізу використання сайту.", "Прийняти", "Відхилити"),
    "ar": ("نستخدم Microsoft Clarity لتحليل الاستخدام.", "قبول", "رفض"), "he": ("אנו משתמשים ב-Microsoft Clarity לניתוח שימוש.", "אישור", "דחייה"),
    "ja": ("利用状況の分析に Microsoft Clarity を使用しています。", "同意する", "拒否する"),
    "ko": ("이용 분석을 위해 Microsoft Clarity를 사용합니다.", "동의", "거부"), "en": ("We use Microsoft Clarity for usage analytics.", "Accept", "Decline")}


def consent_html(lang):
    """Cookie-Hinweis; die Logik (Zustimmung merken, Clarity nur nach Zustimmung laden) liegt in assets/page.js."""
    m, a, d = CONSENT.get(lang, CONSENT["en"])
    return (f'<div id="cc" class="cc" hidden role="region" aria-label="Cookies" data-id="{CLARITY_ID}"><span>{esc(m)}</span>'
            f'<button type="button" class="btn main" id="cc1">{esc(a)}</button><button type="button" class="btn" id="cc0">{esc(d)}</button></div>')


def ext_links(html_):
    """Externe Links (andere Domain als die Seite) immer in neuem Tab oeffnen, mit rel=noopener."""
    host = BASE.split("//")[-1]
    def fix(m):
        tag = m.group(0)
        mh = re.search(r'href="(https?://[^"/]+)', tag)
        if not mh or mh.group(1).split("//")[-1] == host:
            return tag
        if "target=" not in tag:
            tag = tag[:-1] + ' target="_blank">'
        mr = re.search(r'rel="([^"]*)"', tag)
        if mr:
            if "noopener" not in mr.group(1):
                tag = tag.replace(mr.group(0), f'rel="{mr.group(1)} noopener"', 1)
        else:
            tag = tag[:-1] + ' rel="noopener">'
        return tag
    return re.sub(r"<a\s[^>]*>", fix, html_)


SKIP_T = {"en": "Skip to content", "de": "Zum Inhalt springen", "es": "Saltar al contenido", "fr": "Aller au contenu", "it": "Vai al contenuto", "pt": "Saltar para o conteúdo",
          "nl": "Naar de inhoud", "pl": "Przejdź do treści", "id": "Langsung ke konten", "ru": "Перейти к содержимому", "uk": "Перейти до вмісту", "ar": "انتقل إلى المحتوى",
          "he": "דלג לתוכן", "ja": "本文へスキップ", "ko": "본문으로 건너뛰기", }


_A11Y = {}
for _f in ("a11y_en.json", "a11y_i18n.json"):
    if (ROOT / "data" / _f).exists():
        for _k, _v in json.loads((ROOT / "data" / _f).read_text("utf-8")).items():
            _A11Y.setdefault(_k, {}).update(_v)

A11Y_EARLY = ("<script>try{var a=JSON.parse(localStorage.getItem('m365-a11y')||'{}'),c=document.documentElement.classList;"
              "if(a.s)c.add('a11y-s'+a.s);a.hc&&c.add('a11y-hc');a.font&&c.add('a11y-font');a.sp&&c.add('a11y-sp');a.ul&&c.add('a11y-ul');a.nomo&&c.add('a11y-nomo');"
              "a.dk&&document.documentElement.setAttribute('data-theme','dark')}catch(e){}</script>")


def a11y_tags(lang):
    t = dict(_A11Y.get("en", {}))
    t.update(_A11Y.get(lang, {}))
    return (f'<link rel="stylesheet" href="{BASE}/assets/a11y.css">'
            f'<script>window.M365A={{t:{json.dumps(t, ensure_ascii=False).replace("</", "<\\/")}}}</script><script defer src="{BASE}/assets/a11y.js"></script>')


_QUI = {}
for _f in ("quiz_ui_en.json", "quiz_ui_i18n.json"):
    if (ROOT / "data" / _f).exists():
        for _k, _v in json.loads((ROOT / "data" / _f).read_text("utf-8")).items():
            _QUI.setdefault(_k, {}).update(_v)


def quiz_html(qz, lang, title, url):
    """Quiz-Block (Fragen als echte Radiogruppen; Logik in assets/page.js)."""
    try:
        t = dict(_QUI.get("en", {}))
        t.update(_QUI.get(lang, {}))
        qs = ""
        for i, q in enumerate(qz[:5]):
            opts = "".join(f'<label class="qo"><input type="radio" name="q{i}" value="{j}"><span>{esc(o)}</span></label>' for j, o in enumerate(q["opts"][:4]))
            qs += (f'<fieldset class="qq" data-a="{int(q["a"])}" data-why="{esc(q.get("why", ""))}" hidden><legend><small>{esc(t["question_of"].replace("{i}", str(i + 1)).replace("{n}", str(len(qz[:5]))))}</small>'
                   f'<span>{esc(q["q"])}</span></legend>{opts}</fieldset>')
        cfg = json.dumps({"t": t, "title": strip_tags(title), "url": url}, ensure_ascii=False).replace("</", "<\\/")
        return (f'<section class="quiz" id="quiz" aria-labelledby="qz-h" data-n="{len(qz[:5])}"><h2 id="qz-h">{esc(t["quiz"])}</h2><p class="mut">{esc(t["quiz_intro"].replace("{n}", str(len(qz[:5]))))}</p>'
                f'{qs}<div class="qctl"></div><p class="qfb" role="status" aria-live="polite"></p><script type="application/json" class="qcfg">{cfg}</script></section>')
    except Exception:
        return ""




def single_main(html_):
    """Pro Seite genau ein <main>; weitere werden zu benannten <section>-Landmarken (Name = erste Ueberschrift)."""
    parts = re.split(r"(<main\b[^>]*>|</main>)", html_)
    n, used = 0, set()
    for i, p in enumerate(parts):
        if p.startswith("<main"):
            n += 1
            if n == 1:
                parts[i] = '<main id="main"' + p[5:]
            if n > 1:
                m = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", parts[i + 1] if i + 1 < len(parts) else "", re.S)
                lab = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "M365.FM"
                base_lab, k = lab, 1
                while lab in used:
                    k += 1
                    lab = f"{base_lab} {k}"
                used.add(lab)
                parts[i] = "<section" + p[5:-1] + f' aria-label="{html.escape(lab)}">'
        elif p == "</main>" and n > 1 and (sum(1 for q in parts[:i] if q.startswith("<main")) > 1):
            parts[i] = "</section>"
    return "".join(parts)


FXCSS = re.sub(r"/\*.*?\*/|\s*([{};:,])\s*", lambda m: m.group(1) or "", (ROOT / "assets" / "fx.css").read_text(encoding="utf-8"), flags=re.S).strip()   # kleines CSS inline statt eigener Anfrage (Ladezeit)


def page(lang, title, desc, canonical, body, alternates=None, jsonld=None, xdefault=None, og_type="article", extra_head="", noindex=False, side="", og_of=None):
    if lang in COMM_LANGS[2:] and any(k in canonical for k in ("/community/", "/entity/", "/glossary/")):
        extra_head += f'<script defer src="{BASE}/assets/ui-{lang}.js"></script>'
    hl = LANGS[lang][1] if lang in LANGS else "en"
    d = LANGS[lang][2] if lang in LANGS else "ltr"
    loc = LANGS[lang][4] if lang in LANGS else "en_US"
    alt = ""
    if alternates:
        for l, u in alternates.items():
            alt += f'<link rel="alternate" hreflang="{LANGS[l][1] if l in LANGS else l}" href="{u}">\n'
        alt += f'<link rel="alternate" hreflang="x-default" href="{xdefault or alternates.get("en") or BASE + "/"}">\n'   # x-default = englische Fassung des Clusters, sonst Startseite
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>\n' for j in complete_ld(jsonld))
    desc = meta_desc(desc)   # T7: Beschreibung einheitlich begrenzt
    if canonical.endswith("404.html") or noindex:
        ogimg = f"{BASE}/assets/og-default.png"
    elif og_of:   # lokalisierte Show-Seiten teilen das Teilen-Bild der englischen Seite (spart Zehntausende Bilder)
        ogimg = f"{BASE}/og/{og_of.replace(BASE, '').strip('/') or 'index'}.png"
        body = body.replace("<footer>", share_html(lang, canonical, title) + "<footer>", 1)
    else:
        rel = canonical.replace(BASE, "").strip("/") or "index"
        OGLIST.append({"path": f"og/{rel}.png", "title": bare_title(title), "lang": lang, "seed": canonical, "cover": OG_COVER.get(canonical)})
        ogimg = f"{BASE}/og/{rel}.png"
        body = body.replace("<footer>", share_html(lang, canonical, title) + "<footer>", 1)
    if side:   # Sidebar neben dem Hauptinhalt (wie auf den Show-Seiten): erstes <main> in zwei Spalten
        body = re.sub(r'<main class="wrap"([^>]*)>(.*?)</main>', lambda m: f'<main class="wrap shw"{m.group(1)}><div class="shmain">{m.group(2)}</div>{side}</main>', body, count=1, flags=re.S)
        extra_head += f'<link rel="stylesheet" href="{BASE}/assets/sbar.css">'
    body = single_main(body)
    body = ADS.inject(BASE, body, lang, canonical, noindex)
    if 'id="main"' in body:
        body = f'<a class="skip" href="#main">{esc(SKIP_T.get(lang, SKIP_T["en"]))}</a>' + body
    return f"""<!doctype html>
<html lang="{hl}" dir="{d}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(seo_title(title))}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Mirko Peters"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-image-preview:large,max-snippet:-1'}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{BASE}/assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="{BASE}/assets/favicon-32.png" sizes="32x32" type="image/png"><link rel="shortcut icon" href="{BASE}/assets/favicon.ico"><link rel="apple-touch-icon" href="{BASE}/assets/apple-touch-icon.png"><meta name="theme-color" content="#1d2126">
{alt}<meta property="og:type" content="{og_type}"><meta property="og:title" content="{esc(bare_title(title))}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:locale" content="{loc}"><meta property="og:site_name" content="M365.FM">
<meta property="og:image" content="{ogimg}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(bare_title(title))}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(bare_title(title))}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{ogimg}">
{"" if lang in ("ar", "he", "ja", "ko", "ru", "uk") else f'<link rel="preload" href="{BASE}/assets/fonts/barlow-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="{BASE}/assets/fonts/barlow-condensed-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>'}
{extra_head}{ADS.head(BASE, body, canonical, noindex)}{css_link()}<style>{FXCSS}</style>{A11Y_EARLY}
{ld}</head>
<body>
{ext_links(body)}
{consent_html(lang)}
{a11y_tags(lang)}
<script defer src="{BASE}/assets/page.js"></script>
<script defer src="{BASE}/assets/attend.js"></script>
<script>(function(){{if(!matchMedia("(pointer:fine)").matches||matchMedia("(prefers-reduced-motion: reduce)").matches)return;var d=0,ev=["wheel","keydown","pointerdown","touchstart"];function go(){{if(d)return;d=1;ev.forEach(function(e){{removeEventListener(e,go)}});var s=document.createElement("script");s.src="{BASE}/assets/smooth.js";document.body.appendChild(s)}}ev.forEach(function(e){{addEventListener(e,go,{{passive:true,once:true}})}})}})();</script>
<script defer src="{BASE}/assets/fx.js"></script>
{('<script defer src="' + BASE + '/assets/viz.js"></script>') if 'class="viz"' in body else ""}
</body></html>
"""


_CSSF = {}


def css_link():
    """Das gesamte Stylesheet liegt einmal als Datei mit Inhalts-Hash unter /assets/ (statt ~33 KB inline in jeder Seite): kleinere Seiten, Browser- und CDN-Cache."""
    if not _CSSF:
        import hashlib
        css = CSS + (ADS.CSS if ADS.active(BASE) else "")
        name = "site." + hashlib.sha1(css.encode("utf-8")).hexdigest()[:10] + ".css"
        (OUT / "assets").mkdir(parents=True, exist_ok=True); (OUT / "assets" / name).write_text(css, encoding="utf-8")
        _CSSF["u"] = f"{BASE}/assets/{name}"
    return f'<link rel="stylesheet" href="{_CSSF["u"]}">'


_IDENT = {"@id", "@type", "@context", "name", "url"}


def _defined(node, ids):
    """Merkt sich jede @id, die auf der Seite mit mehr als Identitaetsfeldern (name, url) definiert ist."""
    if isinstance(node, dict):
        if node.get("@id") and (set(node) - _IDENT): ids.add(node["@id"])
        for v in node.values(): _defined(v, ids)
    elif isinstance(node, list):
        for v in node: _defined(v, ids)


def complete_ld(jsonld):
    """T4: Verweise auf die Organisation (/#org) und die Person Mirko Peters (#entity) werden auf jeder Seite durch die vollen Knoten
    ergaenzt (eine Definition je @id, sonst nur Verweise), damit publisher/author nirgends ins Leere zeigen."""
    lst = list(jsonld or [])
    if not lst: return lst
    txt = json.dumps(lst); have = set(); _defined(lst, have)
    org, per = f"{BASE}/#org", f"{BASE}/entity/mirko-peters/#entity"
    if per in txt and per not in have: lst.append(person_ld())
    if org in txt and org not in have: lst.append(org_ld())
    return lst


def person_ld():
    d = {"@context": "https://schema.org", "@type": "Person", "@id": f"{BASE}/entity/mirko-peters/#entity",
         "name": "Mirko Peters", "alternateName": ["Mirko Peters MVP", "Mirko Peters M365.FM"], "givenName": "Mirko", "familyName": "Peters",
         "jobTitle": "Microsoft MVP", "description": "Microsoft MVP, host of the M365.FM podcast and the m365 Show on YouTube (animated explainers and Microsoft certification courses), author of e-books on Microsoft topics and organizer of the free online conference M365Con.",
         "url": f"{BASE}/entity/mirko-peters/", "mainEntityOfPage": f"{BASE}/entity/mirko-peters/", "sameAs": SAME_AS,
         "award": "Microsoft Most Valuable Professional (MVP)",
         "hasOccupation": {"@type": "Occupation", "name": "Microsoft MVP, podcaster and conference organizer"},
         "knowsAbout": ["Microsoft 365", "Microsoft Copilot", "Copilot Studio", "Azure", "Azure AI Foundry", "Power Platform", "Microsoft Fabric",
                        "Microsoft Entra", "Microsoft Purview", "Microsoft Teams", "SharePoint", "AI agents", "Dynamics 365"],
         "worksFor": {"@id": f"{BASE}/#org"}, "founder": [{"@id": f"{BASE}/#org"}]}
    if (ROOT / "assets" / "mirko-peters.jpg").exists():
        d["image"] = f"{BASE}/assets/mirko-peters.jpg"
    d["sameAs"] = list(dict.fromkeys(list(d.get("sameAs", [])) + [f"{BASE}/entity/mirko-peters/#entity"]))   # Entitaet in der Entitaetsdatenbank
    if AUTHOR.get("handle"):   # oeffentliches Profil ist die Quelle der Wahrheit
        a = AUTHOR
        if a.get("about") or a.get("headline"):
            d["description"] = (a.get("about") or a.get("headline"))[:500]
        if a.get("headline"):
            d["jobTitle"] = a["headline"][:100]
        names = _ent_names()
        ex = [e["e"] for e in a.get("expertise", []) if e.get("e") in names][:12]
        if ex:   # Expertise als Verweise auf die Entitaeten der Seite (Wissensgraph) neben den festen Themen
            have = {str(x).lower() for x in d.get("knowsAbout", []) if isinstance(x, str)}
            d["knowsAbout"] = list(d.get("knowsAbout", [])) + [{"@type": "Thing", "name": names[e], "@id": f"{BASE}/entity/{e}/#entity"} for e in ex if names[e].lower() not in have]
        cr = [{"@type": "EducationalOccupationalCredential", "name": names[c["e"]], "url": f"{BASE}/entity/{c['e']}/"} for c in a.get("certs", []) if c.get("e") in names and c.get("verified")][:6]
        if cr:
            d["hasCredential"] = cr
        ch = [c["url"] for c in a.get("channels", []) if c.get("url")]
        d["sameAs"] = list(dict.fromkeys(list(d.get("sameAs", [])) + ch))
        d["url"] = f"{BASE}/community/u/{a['handle']}/"
        if a.get("img"):
            d["image"] = f"{COMMUNITY_API}/api/img/u/{a['handle']}"
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
    return (f'<svg viewBox="0 0 1200 420" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">'
            f'<defs><linearGradient id="g{h % 99999}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl({h1},55%,24%)"/><stop offset="1" stop-color="hsl({h2},60%,11%)"/></linearGradient></defs>'
            f'<rect width="1200" height="420" fill="url(#g{h % 99999})"/>{bars}'
            f'<text x="60" y="92" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-size="68" font-weight="700" fill="#f6f1ea">{esc(big)}</text>'
            f'<text x="60" y="388" font-family="system-ui,sans-serif" font-size="22" letter-spacing="5" fill="#f6f1ea" opacity=".8">{esc(small.upper())}</text>'
            f'<circle cx="1120" cy="66" r="14" fill="#b4233c"/></svg>')


def org_ld():
    return {"@context": "https://schema.org", "@type": "Organization", "@id": f"{BASE}/#org", "name": "M365.FM", "url": "https://www.m365.fm",
            "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/apple-touch-icon.png", "width": 180, "height": 180}, "image": f"{BASE}/assets/og-default.png",
            "description": "M365.FM: Microsoft community podcast (M365.FM Show), blog, events and animated explainers on Microsoft 365, Copilot, Azure and Power Platform in 15 languages.",
            "founder": {"@id": f"{BASE}/entity/mirko-peters/#entity"},
            "sameAs": ["https://www.m365.fm", "https://m365con.net", YT_CHANNEL, LINKEDIN]}


def event_ld():
    return {"@context": "https://schema.org", "@type": "Event", "@id": f"{BASE}/#m365con2027", "name": "M365Con 2027 – free online conference",
            "description": "Free, 100% online Microsoft community conference with 120 sessions on Microsoft 365, Copilot, Azure, Power Platform, security and AI.",
            "startDate": "2027-01-11", "endDate": "2027-01-22", "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled", "isAccessibleForFree": True, "inLanguage": "en",
            "location": {"@type": "VirtualLocation", "url": "https://m365con.net"}, "url": "https://m365con.net",
            "organizer": {"@id": f"{BASE}/entity/mirko-peters/#entity"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "url": "https://m365con.net", "availability": "https://schema.org/InStock"}}


FAQ_T = {"de": "Häufige Fragen", "es": "Preguntas frecuentes", "fr": "Questions fréquentes", "it": "Domande frequenti", "pt": "Perguntas frequentes",
         "nl": "Veelgestelde vragen", "pl": "Najczęstsze pytania", "id": "Pertanyaan umum", "ru": "Частые вопросы", "uk": "Часті запитання",
         "ar": "الأسئلة الشائعة", "he": "שאלות נפוצות", "ja": "よくある質問", "ko": "자주 묻는 질문"
         }


def faq_ld(lang):
    return {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": LANGS[lang][1] if lang in LANGS else "en",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ[lang]]}


def faq_html(lang, title="FAQ"):
    rows = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in FAQ[lang])
    return f'<section class="faq"><h2>{esc(title)}</h2>{rows}</section>'


def m365con_band():
    return (f'<section class="band" aria-label="M365Con 2027"><div class="wrap"><div class="kicker" style="margin:0;color:inherit;opacity:.8">M365Con 2027 · Jan 11–22 · 100% online · free</div>'
            f'<h2>120 sessions. 10 days. Microsoft community from all over the world.</h2>'
            f'<div class="btns"><a class="btn main" href="https://m365con.net">m365con.net</a></div></div></section>')


BAR_T = {"en": "M365Con 2027 – free online conference", "de": "M365Con 2027 – die kostenlose Online-Konferenz", "es": "M365Con 2027 – conferencia online gratuita",
         "fr": "M365Con 2027 – conférence en ligne gratuite", "it": "M365Con 2027 – conferenza online gratuita", "pt": "M365Con 2027 – conferência online gratuita",
         "nl": "M365Con 2027 – gratis online conferentie", "pl": "M365Con 2027 – bezpłatna konferencja online", "id": "M365Con 2027 – konferensi online gratis",
         "ru": "M365Con 2027 – бесплатная онлайн-конференция", "uk": "M365Con 2027 – безкоштовна онлайн-конференція", "ar": "M365Con 2027 – مؤتمر مجاني عبر الإنترنت",
         "he": "M365Con 2027 – כנס אונליין חינמי", "ja": "M365Con 2027 – 無料オンラインカンファレンス",
         "ko": "M365Con 2027 – 무료 온라인 컨퍼런스", }
M365CON_END = date(2027, 1, 22)


def con_bar(lang):
    if date.today() > M365CON_END:
        return ""
    return (f'<div class="mbar"><a href="https://m365con.net" rel="noopener"><b>{esc(BAR_T.get(lang, BAR_T["en"]))}</b> · 11–22 Jan 2027 · 120 sessions<i>→ m365con.net</i></a></div>')


import site_home as HUB
import site_design as _SD
_SD.EN_URL = f"{BASE}/show/"
globals_ctx = None
COMMUNITY_API = os.environ.get("COMMUNITY_API", "https://api-dub.m365.fm")
_CI = json.loads((ROOT / "data" / "community_i18n.json").read_text("utf-8")) if (ROOT / "data" / "community_i18n.json").exists() else {}


def community_tags(lang, vid=None, mode=""):
    """Skripte/Stile fuer Community-Widgets (blenden sich aus, wenn die API nicht erreichbar ist)."""
    priv = f"{BASE}/{'datenschutz' if lang == 'de' else 'privacy'}/"
    cfg = {"api": COMMUNITY_API, "lang": lang, "vid": vid, "privacy": priv, "communityUrl": f"{BASE}/{lang}/community/"}
    # Die Oberflaechentexte (ca. 6 KB je Sprache, auf jeder Seite gleich) liegen in assets/cm-<sprache>.js (gecacht), nicht mehr in jeder Seite.
    return (f'<link rel="stylesheet" href="{BASE}/assets/community.css"><script defer src="{BASE}/assets/cm-{lang if lang in _CI else "en"}.js"></script>'
            f'<script>window.M365C={json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script><script defer src="{BASE}/assets/community.js"></script>')


def write_cm_js(out):
    """assets/cm-<sprache>.js: Texte der Community-Skripte je Sprache (Englisch als Rueckfall), einmal gecacht statt in jeder Seite."""
    for lg in _CI:
        t = dict(_CI.get("en", {})); t.update(_CI.get(lg, {}))
        (out / "assets" / f"cm-{lg}.js").write_text("window.M365CT=" + json.dumps(t, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";", "utf-8")


_ABOUT_L = set(json.loads((ROOT / "data" / "about_i18n.json").read_text("utf-8"))) if (ROOT / "data" / "about_i18n.json").exists() else set()


def about_url(lang):
    return f"{BASE}/de/entity/mirko-peters/" if lang == "de" else f"{BASE}/entity/mirko-peters/"


def header(lang, switch):
    ui = UI.get(lang)
    if lang in LANGS:
        home = f"{BASE}/{lang}/"
        menu = []
        menu.insert(0, (LRN.T(lang)["learn"], f"{BASE}/{lang}/learn/"))
        menu.append(("Podcast", f"{BASE}/{lang}/podcast/"))   # der gedubbte Podcast der Sprache (Spreaker-Show); die Live-Show gibt es nur auf Englisch
        menu.insert(0, (_CI.get(lang, _CI.get("en", {})).get("profile", "Profile"), f"{BASE}/{lang}/community/"))
        _cl = {"de": ("Community", "Podcast", "Blog", "Videos", "Bibliothek", "Gäste")}.get(lang, ("Community", "Podcast", "Blog", "Videos", "Library", "Guests"))
        menu.insert(0, (_CI.get(lang, _CI.get("en", {})).get("community", _cl[0]), [(ui[3], home)] + [(_cl[i + 1], f"{BASE}/{lang}/community/{p}/") for i, p in enumerate(("podcast", "blog", "video", "library", "guests"))]))
    else:
        home = f"{BASE}/"
        menu = [("Languages", f"{BASE}/#languages"), ("Community", [("Podcast", f"{BASE}/community/podcast/"), ("Blog", f"{BASE}/community/blog/"), ("Videos", f"{BASE}/community/video/"), ("Library", f"{BASE}/community/library/"), ("Guests", f"{BASE}/community/guests/")]), ("Show", [("About the show", f"{BASE}/show/"), ("All episodes", f"{BASE}/show/episodes/")] + ([("M365 Show Live", f"{BASE}/live/")] if (ROOT / "data" / "live.json").exists() else []) + [("Guests", f"{BASE}/show/guests/"), ("Hosts", f"{BASE}/show/hosts/")]), ("Profile", f"{BASE}/community/")]
    if not switch:
        items = [(x, LANGS[x][0], f"{BASE}/{x}/", LANGS[x][1]) for x in LANGS if (ROOT / "episodes").exists()]
        switch = lang_dropdown(lang if lang in LANGS else "en", items, "")
    return site_header(home, home, menu, switch, con_bar(lang))


_AST = {}
for _f in ("a11y_statement_en.json", "a11y_statement_i18n.json"):
    if (ROOT / "data" / _f).exists():
        for _k, _v in json.loads((ROOT / "data" / _f).read_text("utf-8")).items():
            _AST.setdefault(_k, {}).update(_v)


def ast_url(lang):
    return f"{BASE}/accessibility/" if lang == "en" or lang not in LANGS else f"{BASE}/{lang}/accessibility/"


def ast_label(lang):
    return (_AST.get(lang) or _AST.get("en") or {}).get("title", "Accessibility")


def ast_body(lang):
    A = dict(_AST.get("en", {}))
    A.update(_AST.get(lang, {}))
    mail = '<a href="mailto:mirko.peters@m365.fm">mirko.peters@m365.fm</a>'
    li = lambda keys: "<ul class=\"points\">" + "".join(f"<li><span>{esc(A[k])}</span></li>" for k in keys) + "</ul>"
    return (f'<h1>{esc(A["title"])}</h1><p class="lede">{esc(A["intro"])}</p>'
            f'<h2>{esc(A["status_h"])}</h2><p>{esc(A["status_p"])}</p>'
            f'<h2>{esc(A["done_h"])}</h2>{li(["d1", "d2", "d3", "d4", "d5", "d6"])}'
            f'<h2>{esc(A["limits_h"])}</h2>{li(["l1", "l2", "l3", "l4"])}'
            f'<h2>{esc(A["contact_h"])}</h2><p>{esc(A["contact_p"]).replace("{MAIL}", mail)}</p><p class="mut">{esc(A["date_p"])}</p>')


def footer(lang):
    ui = UI.get(lang)
    about = ui[5] if ui else "About Mirko Peters"
    _tl = lang if lang in LANGS else "en"
    # Top-/Empfehlungsseiten gibt es nur je Dub-Sprache; englische Seiten verlinken die Folgenliste der Hauptshow (vorher /en/top/ = 404 auf jeder englischen Seite)
    _top = f'<a href="{BASE}/{_tl}/top/">{esc((TOP_L if _tl in TOP_REAL else REC_L).get(_tl, "Top"))}</a>' if _tl in LANGS else f'<a href="{BASE}/show/episodes/">Recommended episodes</a>'
    _nw = f'<a href="{BASE}/{"de/" if lang == "de" else ""}updates/">{"Updates & Roadmap" if lang == "de" else "Updates & roadmap"}</a>'
    return (f'<footer><div class="wrap">{_top}{_nw}<a href="https://www.m365.fm">m365.fm</a>'
            f'<a href="https://m365con.net">M365Con</a><a class="soc" href="{LINKEDIN}" rel="me" style="--bc:#0A66C2">{brand_icon("LinkedIn")}<span>LinkedIn</span></a><a class="soc" href="{YT_CHANNEL}" style="--bc:#FF0000">{brand_icon("YouTube")}<span>YouTube</span></a>'
            f'<a href="{ast_url(lang)}">{esc(ast_label(lang))}</a><a href="{BASE}/{"de/" if lang == "de" else ""}press/">{"Pressekit" if lang == "de" else "Press kit"}</a><a href="{BASE}/impressum/" rel="nofollow">Impressum</a><a href="{BASE}/legal/" rel="nofollow">Legal notice</a>'
            f'<a href="{BASE}/datenschutz/" rel="nofollow">Datenschutz</a><a href="{BASE}/privacy/" rel="nofollow">Privacy</a>'
            f'<div style="margin-top:10px">© {date.today().year} Mirko Peters · M365.FM</div></div></footer>')


AUTHOR_HANDLE = "mirko-p"   # Handle des oeffentlichen Profils (Community), nicht die Entitaets-ID mirko-peters
AUTHOR = {}   # oeffentliches Profil des Autors (Quelle der Wahrheit), faellt auf festen Text zurueck


def _ent_names():
    """id -> Name der Entitaeten (fuer Expertise-Links in der Author-Box); einmal geladen."""
    global _ENT_NAMES
    try:
        return _ENT_NAMES
    except NameError:
        try:
            _ENT_NAMES = {e["id"]: e["name"] for e in json.loads((ROOT / "data" / "entities.json").read_text(encoding="utf-8"))}
        except Exception:
            _ENT_NAMES = {}
        return _ENT_NAMES


def _sentences(text, limit):
    """Bio auf ganze Saetze kuerzen (nie mitten im Wort), damit Suchmaschinen und KI-Antworten ein vollstaendiges Zitat bekommen."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    k = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[:k + 1] if k > limit * 0.5 else cut.rsplit(" ", 1)[0] + "…"


def author_box(lang):
    """Author-Box mit schema.org-Auszeichnung (Person, gleiche @id wie das JSON-LD), Expertise als Entitaets-Links, Zertifikaten und sameAs-Kanaelen:
    macht den Autor fuer Suchmaschinen und KI-Antworten (GEO) als geprueften Experten erkennbar (E-E-A-T)."""
    de = lang == "de"; ent = f"{BASE}/entity/mirko-peters/#entity"; pref = f'{BASE}/{"de/" if de else ""}'
    L = dict(about="Über den Autor" if de else "About the author", exp="Expertise" if de else "Expertise", cert="Zertifizierungen" if de else "Certifications", prof="Profil ansehen" if de else "View profile")
    if AUTHOR.get("handle"):
        a = AUTHOR; progs = {"mvp": "Microsoft MVP", "mct": "Microsoft Certified Trainer", "rd": "Microsoft Regional Director", "msa": "Microsoft Student Ambassador"}
        icons = {"mvp": "🏆", "mct": "🎓", "rd": "🧭", "msa": "🌟"}
        vp = [x["p"] for x in a.get("programs", []) if x.get("verified") and x["p"] in progs]
        lab = " · ".join(icons[x] + " " + progs[x] for x in vp)
        KL = {"linkedin": "LinkedIn", "github": "GitHub", "youtube": "YouTube", "x": "X", "mastodon": "Mastodon", "bluesky": "Bluesky", "twitch": "Twitch", "blog": "Blog", "podcast": "Podcast", "newsletter": "Newsletter", "website": "Web", "other": "Link"}
        chs = "".join(f'<a href="{esc(c["url"])}" rel="me noopener" itemprop="sameAs">{esc(KL.get(c["kind"], "Link"))}</a> ' for c in a.get("channels", [])[:8] if c.get("url"))
        img = f'{COMMUNITY_API}/api/img/u/{a["handle"]}' if a.get("img") else (f"{BASE}/assets/mirko-peters.jpg" if (ROOT / "assets" / "mirko-peters.jpg").exists() else "")
        badge = f'<img class="badge" src="{img}" alt="{esc(a["name"])}" width="58" height="58" loading="lazy" itemprop="image">' if img else '<div class="badge">MP</div>'
        bio = _sentences(a.get("about") or a.get("headline") or "", 360)
        names = _ent_names(); ex = sorted([e for e in a.get("expertise", []) if e.get("e") in names], key=lambda e: (-int(bool(e.get("verified") or e.get("via"))), -(e.get("level") or 0)))[:6]
        exh = "".join(f'<li><a href="{pref}entity/{e["e"]}/" itemprop="knowsAbout">{esc(names[e["e"]])}</a></li>' for e in ex)
        cs = [c for c in a.get("certs", []) if c.get("e") in names and c.get("verified")][:4]
        csh = "".join(f'<li itemprop="hasCredential" itemscope itemtype="https://schema.org/EducationalOccupationalCredential"><a href="{pref}entity/{c["e"]}/" itemprop="name">{esc(names[c["e"]])}</a></li>' for c in cs)
        job = esc((a.get("headline") or progs.get(vp[0], "") if vp else a.get("headline") or "")[:100])
        return (f'<aside class="author" itemscope itemtype="https://schema.org/Person" itemid="{ent}" aria-label="{esc(L["about"])}"><link itemprop="sameAs" href="{ent}">{badge}<div>'
                f'<strong><a href="{pref}community/u/{a["handle"]}/" rel="author" itemprop="url"><span itemprop="name">{esc(a["name"])}</span></a>{(" · " + esc(lab)) if lab else ""}</strong>'
                + (f'<meta itemprop="jobTitle" content="{job}">' if job else "") + f'<p itemprop="description">{esc(bio)}</p>'
                + (f'<p class="auth-ex"><b>{esc(L["exp"])}:</b></p><ul class="auth-ul">{exh}</ul>' if exh else "")
                + (f'<p class="auth-ex"><b>{esc(L["cert"])}:</b></p><ul class="auth-ul">{csh}</ul>' if csh else "")
                + (f'<p class="auth-ch">{chs}</p>' if chs else "") + '</div></aside>')
    ui = UI.get(lang)
    bio = ui[6] if ui else "Mirko Peters is a Microsoft MVP, host of the podcast M365.FM and initiator of the free online conference M365Con."
    photo = (ROOT / "assets" / "mirko-peters.jpg").exists()
    badge = (f'<img class="badge" src="{BASE}/assets/mirko-peters.jpg" alt="Mirko Peters, Microsoft MVP" width="58" height="58" loading="lazy" itemprop="image">' if photo else '<div class="badge">MP</div>')
    return (f'<aside class="author" itemscope itemtype="https://schema.org/Person" itemid="{ent}" aria-label="{esc(L["about"])}"><link itemprop="sameAs" href="{ent}">{badge}<div>'
            f'<strong><a href="{about_url(lang)}" rel="author" itemprop="url"><span itemprop="name">Mirko Peters</span></a> · <span itemprop="jobTitle">Microsoft MVP</span></strong>'
            f'<p itemprop="description">{esc(bio)}</p></div></aside>')


EXTRA = (("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart"), ("castbox_show", "Castbox"), ("podcastaddict_show", "Podcast Addict"), ("podchaser_show", "Podchaser"))


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
        elif typ == "checkliste":
            body = '<ul class="ichecks">' + "".join(f'<li><button type="button" class="ck" aria-pressed="false">{esc(x if isinstance(x, str) else x.get("text", ""))}</button></li>' for x in info.get("punkte", [])[:7]) + "</ul>"
        elif typ == "prozess":
            pts = info.get("punkte", [])[:6]
            nodes = "".join(f'<li class="pn {esc(p.get("art", "schritt")) if p.get("art") in ("start", "ende", "entscheidung") else "schritt"}" tabindex="0"><span class="pi">{n + 1}</span><b>{esc(p.get("kopf", ""))}</b><span class="pt">{esc(p.get("text", ""))}</span></li>' for n, p in enumerate(pts))
            body = f'<ol class="iflow">{nodes}</ol><div class="iplay"><button type="button" class="btn">▶</button></div>'
        elif typ == "fakten":
            body = '<div class="ifacts">' + "".join(f'<div><b>{esc(p.get("wert", ""))}</b><span>{esc(p.get("text", ""))}</span></div>' for p in info.get("punkte", [])[:6]) + "</div>"
        else:
            body = '<ol class="isteps">' + "".join(f'<li tabindex="0"><i>{n + 1}</i><b>{esc(p.get("kopf", ""))}</b><span>{esc(p.get("text", ""))}</span></li>' for n, p in enumerate(info.get("punkte", [])[:6])) + "</ol>"
        return f'<figure class="info rv"><figcaption>{t}</figcaption>{body}<small>M365.FM · Mirko Peters</small></figure>'
    except Exception:
        return ""





_T0 = [time.perf_counter()]


def phase(name):
    """Zeit seit der letzten Phase ins Log (Grundlage fuer die Beschleunigung des Baus)."""
    t = time.perf_counter(); print(f"[{t - _T0[0]:6.0f} s] {name}", flush=True); _T0[0] = t


def sizes():
    """Groesse von docs/ je oberstem Verzeichnis (GitHub Pages: 1 GB Richtwert)."""
    tot, rows = 0, []
    for d in sorted(OUT.iterdir()):
        n = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) if d.is_dir() else d.stat().st_size
        tot += n; rows.append((n, d.name))
    print("docs/ gesamt: %.0f MB" % (tot / 1e6) + " - " + ", ".join(f"{n}: {b / 1e6:.0f} MB" for b, n in sorted(rows, reverse=True)[:12]))


def build():
    import shutil as _sh
    if (ROOT / "r2out").exists(): _sh.rmtree(ROOT / "r2out")
    SF.prefetch(COMMUNITY_API, langs=list(COMM_LANGS)); SF.check(COMMUNITY_API)   # alle Exporte einmal, parallel; ohne Pflicht-Exporte kein Bau
    phase("Exporte geholt")
    eps, pub, seo = load()
    try:
        _pp, _oo = MEM.fetch_members(COMMUNITY_API)
        AUTHOR.update(next((x for x in _pp if x.get("handle") == AUTHOR_HANDLE), {}))
    except Exception:
        pass
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
        write_cm_js(OUT)
        from site_i18n import write_ui_js
        write_ui_js(OUT)

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
    SBX = SBR.Index()
    def side_for(l, title, body_html):   # Sidebar der Sprachseiten: Themen der Seite, neueste Folgen der Sprache, Community
        return SBR.render_lang(SBX, BASE, l, strip_tags(title + " " + body_html.split("<main", 1)[-1])[:2500], by_lang.get(l, []), url_of, lambda x: anchor_title(x["e"]["title"]), pfx(l) if l in COMM_LANGS else "")

    R2OUT = ROOT / "r2out"; _r2n = [0, 0]   # Seiten, die nicht in GitHub Pages liegen, sondern im R2-Bucket (tools/r2_pages_upload.py laedt sie hoch, der Site-Worker liefert sie aus)
    def write_r2(rel, content):
        p = R2OUT / rel; p.parent.mkdir(parents=True, exist_ok=True)
        c = R2.rewrite(content) if rel.endswith(".html") else content
        p.write_text(c, encoding="utf-8"); _r2n[0] += 1; _r2n[1] += len(c.encode("utf-8"))
    def write(rel, content):
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(R2.rewrite(content) if rel.endswith(".html") else content, encoding="utf-8")

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
    MONEY = SM.update(ROOT / "data" / "money_keywords.json", by_lang, tagraw)

    def chips_html(l, it):
        out = "".join(f'<a class="chip cat" href="{cat_url(l, c)}">{esc(cat_name(c, l))}</a>' for c in ORDER if c in cat_of[it["vid"]] and c in catidx[l])
        for t in tagraw[l][it["vid"]]:
            s = tag_slug(t)
            if s and len(tagidx[l][s]["items"]) >= 2:
                out += f'<a class="chip" rel="tag" href="{tag_url(BASE, l, t)}">{esc(t)}</a>'
            elif s:
                out += f'<span class="chip">{esc(t)}</span>'
        return f'<div class="chips">{out}</div>' if out else ""

    def top_real(l, n=10):
        rows = (topdata.get("langs") or {}).get(l) or []
        by_eid = {i["eid"]: i for i in by_lang.get(l, [])}
        return [by_eid[r["episode_id"]] for r in rows if r.get("score", 0) > 0 and r["episode_id"] in by_eid][:n]

    def top_for(l, n=10):
        """Echte Top-Liste (Spreaker-Statistik); solange keine Daten da sind: vorlaeufige Auswahl = meistverlinkte (Money-Keyword-Ziele), dann neueste."""
        t = top_real(l, n)
        if t:
            return t
        tg = {}
        for v in SM.registry_for(MONEY, l).values():
            tg[v] = tg.get(v, 0) + 1
        pool = [i for i in by_lang.get(l, []) if i["vid"] in by_vid]
        pool.sort(key=lambda i: (tg.get(i["vid"], 0), i["date"]), reverse=True)
        return pool[:n]

    TOP_REAL.update(x for x in by_lang if top_real(x, 1))

    def is_prov(l):
        return not top_real(l, 1)

    def top_label(l):
        return (REC_L if is_prov(l) else TOP_L).get(l, (REC_L if is_prov(l) else TOP_L)["en"])

    def top_block(l):
        t = top_for(l, 5)
        if not t:
            return ""
        return (f'<h2>★ {esc(top_label(l))}</h2><div class="list">' + "".join(
            f'<a class="row" href="{url_of(x)}" title="{esc(x["e"]["title"])}"><h3>{n + 1}. {esc(anchor_title(x["e"]["title"]))}</h3></a>' for n, x in enumerate(t)) +
            f'</div><p><a class="btn" href="{BASE}/{l}/top/">{esc(top_label(l))} →</a></p>')

    def topics_nav(l):
        cs = "".join(f'<a class="chip cat" href="{cat_url(l, c)}">{esc(cat_name(c, l))} · {len(catidx[l][c])}</a>' for c in ORDER if c in catidx[l])
        return top_block(l) + f'<h2>{esc(TOPICS.get(l, "Topics"))}</h2><div class="chips">{cs}</div>'

    # Englisches Original je Video (Podpage-Show unter /show/), Zuordnung ueber den englischen YouTube-Titel
    ORIG = {}
    try:
        import site_podpage as _PPm
        _et = site_text.fix_tree(json.load(open(ROOT / "data" / "en_titles.json", encoding="utf-8"))) if (ROOT / "data" / "en_titles.json").exists() else {}   # T5
        _byt = {_PPm.norm(e["name"]): e for e in _PPm.load("episodes")}
        ORIG = {v: _byt[_PPm.norm(t)]["slug"] for v, t in _et.items() if _PPm.norm(t) in _byt}
    except Exception as _ex:
        print("Original-Zuordnung:", _ex)
    ORIG_ALTS = {}
    try:   # Speaker der M365Con-Programme: zusammengefuehrte Personen (tools/build_speakers.py) -> Entitaetsseiten und /speakers.json fuer den Worker
        _sp = json.loads((ROOT / "data" / "speakers.json").read_text("utf-8")).get("speakers", [])
        ENT.SPEAKERS.update({x["id"]: x for x in _sp})
        write("speakers.json", json.dumps({"version": 1, "speakers": [{k: x[k] for k in ("id", "name", "aliases", "handle") if k in x} for x in _sp]}, ensure_ascii=False))
    except Exception as _e:
        print("Speaker-Daten:", _e)
    SNT.load(COMMUNITY_API); SNT.publish(OUT)   # Show Notes aus Spreaker (data/show_notes) + Bearbeitungen aus dem Editor; Rohdaten fuer den Editor unter /show-notes/
    # Episoden-Seiten
    for (vid, l), it in items.items():
        e = it["e"]; ui = UI[l]
        intro, hdr, bullets, aud = parse_desc(e["desc"])
        alts = {x: url_of(by_vid[vid][x]) for x in by_vid[vid]}
        if vid in ORIG: alts["en"] = f"{BASE}/show/episodes/{ORIG[vid]}/"   # T3: englisches Original gehoert zum Cluster der Dub-Fassungen
        canonical = url_of(it)
        _xab = [{"@id": f"{BASE}/entity/{_s}/#entity"} for _s, _ in (SX.BY_EPISODE.get(str(it["eid"])) or {}).get("entities", []) if _s in LRN.ENTS][:8]   # T27: Entitaeten aus der QA-geprueften Extraktion
        spk = f'https://www.spreaker.com/episode/{it["eid"]}'
        yt = f"https://youtu.be/{vid}"
        tr = e.get("tr") or ""
        _nkp, _nnotes, _nfaq, _nld = SNT.blocks(SNT.get(l, ep_id=it["eid"]), l, edited_only=True)   # nur wenn im Editor bearbeitet: Kernpunkte, Show Notes, FAQ als eigene Bloecke
        _snx = SNALL.get(str(it["eid"]))   # T26: Vollfassung der Shownotes fuer die Dub-Folge (shownotes/site/<spreaker_episode_id>.md)
        if _snx:
            _snh, _snld, _snfaq = SNS.render(_snx, l, LRN.ENTS, BASE)
            _nnotes = _snh + f"<style>{SNS.CSS}</style>"; _nld = [x for x in _nld if x.get("@type") != "FAQPage"] + _snld
            if _snfaq: _nfaq = ""
        notes_block = _nkp + _nnotes + _nfaq + (SNT.CSS if (_nkp or _nnotes or _nfaq) else "")
        _el = {k: u for k, u in elinks.get(f"{vid}:{l}", {}).items() if u}   # zugeordnete Plattform-Folgenlinks -> sameAs
        more = related(it, by_lang[l], tagsets[l], catsets[l])
        ld = [
            {"@context": "https://schema.org", "@type": "PodcastEpisode", "@id": canonical + "#episode", "name": e["title"], "description": strip_tags(intro),
             "url": canonical, "inLanguage": LANGS[l][1], "datePublished": it["date"],
             "associatedMedia": {"@type": "AudioObject", "contentUrl": spk, "inLanguage": LANGS[l][1]},
             "image": f"{BASE}/og/{canonical.replace(BASE, '').strip('/')}.png", "isAccessibleForFree": True, "keywords": e.get("tags", ""),
             "about": _xab + [{"@type": "Thing", "name": t.strip()} for t in (e.get("tags") or "").split(",")[:5] if t.strip() and "m365.fm" not in t],
             **({"sameAs": list(_el.values())} if _el else {}),
             "partOfSeries": {"@id": f"{BASE}/{l}/#series", "@type": "PodcastSeries", "name": seo.get(l, {}).get("title", "M365.FM"), "url": f"{BASE}/{l}/"},   # T4: Serie = Knoten der Sprach-Startseite (vorher Spreaker-URL); das Transkript ist eine Datei (tr), kein Text -> kein transcript-Feld
             "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "M365.FM", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 2, "name": LANGS[l][0], "item": f"{BASE}/{l}/"},
                {"@type": "ListItem", "position": 3, "name": e["title"], "item": canonical}]},
            {"@context": "https://schema.org", "@type": "VideoObject", "@id": canonical + "#video", "name": e["title"], "description": strip_tags(intro),
             "thumbnailUrl": [f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
             "uploadDate": videos.get(vid, {}).get("date", it["date"]), "contentUrl": f"https://www.youtube.com/watch?v={vid}",
             "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}", "isFamilyFriendly": True, "inLanguage": LANGS[l][1],
             "publisher": {"@id": f"{BASE}/#org"}, "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}},
            person_ld(), org_ld(),
        ]
        ld[0]["video"] = {"@id": canonical + "#video"}
        for _n in ld:
            if _xab and _n.get("@type") == "VideoObject": _n["about"] = _xab   # T27: das Video behandelt dieselben Entitaeten wie die Folge
        pc = [c for c in ORDER if c in cat_of[vid]][0]
        ld[0]["genre"] = cat_name(pc, l)
        ld[0]["keywords"] = ", ".join(tagraw[l][vid]) or e.get("tags", "")
        art = articles.get(vid, {}).get(l, {})
        art_html = art.get("html", "")
        if art_html:
            art_html, _lk = autolink(art_html, it, [], tagraw[l], url_of, money=LRN.drop_glossed(SM.registry_for(MONEY, l)))
            autolink_log.append(((vid, l), _lk))
            art_html = LRN.gloss_link(art_html, l, BASE)
        if art_html and art.get("info"):
            ih = info_html(art["info"])
            art_html = re.sub(r"(</p>)", r"\1" + ih.replace("\\", "\\\\"), art_html, count=1) if ih else art_html
        if art_html and art.get("infos"):
            parts = re.split(r"(?=<h2>)", art_html)
            if len(parts) >= 4:
                slots = [max(2, len(parts) // 2), max(3, len(parts) - 1)]
                for k, inf2 in zip(sorted(set(slots)), art["infos"][:2]):
                    h2 = info_html(inf2)
                    if h2:
                        parts[k] = h2 + parts[k]
                art_html = "".join(parts)
        if art_html:
            ld.append({"@context": "https://schema.org", "@type": "Article", "headline": e["title"][:110], "inLanguage": LANGS[l][1],
                       "datePublished": it["date"], "dateModified": it["date"], "mainEntityOfPage": canonical,
                       "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}, "publisher": {"@id": f"{BASE}/#org"},
                       "image": [f"{BASE}/og/{canonical.replace(BASE, '').strip('/')}.png", f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"], "wordCount": len(strip_tags(art_html).split()), "articleSection": cat_name(pc, l), "keywords": ", ".join(tagraw[l][vid])})
        _t = re.sub(r"\s*[（(][^()（）]*[)）]\s*$", "", e["title"]).strip()
        h1_main, h1_rest = _t, ""
        if len(_t) > 70:
            _m = re.match(r"^(.{18,}?)(?:\s*[:：]\s+|\s+[–—-]\s+)(.+)$", _t)
            if _m and len(_m.group(1)) <= 70:
                h1_main, h1_rest = _m.group(1).strip(), _m.group(2).strip()
        faq_items = art.get("faq") or []
        quiz_block = quiz_html(art["quiz"], l, e["title"], canonical) if (art_html and art.get("quiz")) else ""
        faq_block = ""
        if art_html and faq_items:
            faq_block = ('<section class="faq" style="margin-top:2.2em"><h2>' + esc(FAQ_T.get(l, "FAQ")) + "</h2>"
                         + "".join(f"<details><summary>{esc(x['q'])}</summary><p>{esc(x['a'])}</p></details>" for x in faq_items) + "</section>")
            ld.append({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": LANGS[l][1], "mainEntity": [
                {"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in faq_items]})
        lis = "".join(f"<li>{x}</li>" for x in bullets)
        el = elinks.get(f"{vid}:{l}", {}); sh = plat.get(l, {})
        apple = el.get("apple") or sh.get("apple_show"); spot = el.get("spotify") or sh.get("spotify_show")
        btns = ""
        if apple: btns += f'<a class="btn" data-p="apple" href="{apple}" rel="noopener">Apple Podcasts</a>'
        if spot: btns += f'<a class="btn" data-p="spotify" href="{spot}" rel="noopener">Spotify</a>'
        if el.get("deezer") or sh.get("deezer_show"): btns += f'<a class="btn" href="{el.get("deezer") or sh["deezer_show"]}" rel="noopener">Deezer</a>'
        if sh.get("amazon_show"): btns += f'<a class="btn" href="{sh["amazon_show"]}" rel="noopener">Amazon Music</a>'
        showrow = "".join(f'<a href="{sh[k]}" rel="noopener">{n}</a>' for k, n in (("apple_show", "Apple Podcasts"), ("spotify_show", "Spotify"), ("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart"), ("youtube_show", "YouTube"), ("youtube_music_show", "YouTube Music"), ("castbox_show", "Castbox"), ("podcastaddict_show", "Podcast Addict"), ("podchaser_show", "Podchaser")) if sh.get(k))
        btns += f'<a class="btn" data-p="spreaker" href="{spk}" rel="noopener">🎧 {esc(ui[0])}</a>' 
        btns += f'<a class="btn" href="{yt}" rel="noopener">▶ {esc(ui[1])}</a>'
        if tr: btns += f'<a class="btn" href="{tr}">📄 {esc(ui[2])}</a>'
        rel = "".join(f'<a class="row" href="{url_of(x)}" title="{esc(x["e"]["title"])}"><h3>{esc(anchor_title(x["e"]["title"]))}</h3></a>' for x in more)
        body = f"""{header(l, lang_switch(l, alts, [x for x in LANGS if x in alts]))}
<main class="wrap"><article>
<nav class="crumbs" aria-label="breadcrumb"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])} / {it["date"]}</nav>
<div class="kicker">M365.FM · {esc(LANGS[l][0])}</div>{('<p class="mut"><a href="' + BASE + '/show/episodes/' + ORIG[vid] + '/" hreflang="en">' + ("Original (English)" if l != "de" else "Original (Englisch)") + '</a></p>') if vid in ORIG else ""}
<h1>{esc(h1_main)}</h1>{("<p class=sub>" + esc(h1_rest) + "</p>") if h1_rest else ""}
{chips_html(l, it)}<p class="lede">{intro}</p>
<figure class="cover" style="margin-inline:0">{art_svg(vid, LANGS[l][0], "M365.FM · " + ui[0], l)}</figure>
<div class="panel"><iframe src="https://widget.spreaker.com/player?episode_id={it["eid"]}&amp;theme=light&amp;playlist=false" height="131" loading="lazy" title="{esc(e["title"])}"></iframe>
<div class="btns">{btns}</div>{"<p class=showrow>M365.FM ▸ " + showrow + "</p>" if showrow else ""}</div>
<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" title="{esc(e["title"])}" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
<p class="mut">▶ {esc(e["title"])}</p>
<h2>{esc(hdr)}</h2><ol class="points">{lis}</ol>
<p class="lede" style="margin-top:1.4em">{aud}</p>
{("<section class=article>" + art_html + "</section>") if art_html else ""}{quiz_block}{faq_block}{notes_block}
{author_box(l)}
</article>
{('<h2>' + esc(ui[4]) + '</h2><div class="list">' + rel + '</div>') if rel else ''}
<p style="margin-top:1.6em"><a class="btn" href="{BASE}/{l}/">{esc(ui[3])} →</a></p>
<section id="c-comments"></section><section id="c-sub"></section></main>
{footer(l)}{community_tags(l, vid)}"""
        OG_COVER[canonical] = art_svg(vid, LANGS[l][0], lang=l)
        write(f'{l}/{it["slug"]}/index.html',
              page(l, e["title"], short(intro), canonical, body, alts, ld + _nld, xdefault=alts.get("en"), side=side_for(l, e["title"], body), extra_head=f'<meta property="article:section" content="{esc(cat_name(pc, l))}">' + "".join(f'<meta property="article:tag" content="{esc(t)}">' for t in tagraw[l][vid])))
        sitemap.append((canonical, it["date"], alts))
        if vid in ORIG: ORIG_ALTS.setdefault(ORIG[vid], {})[l] = (canonical, e["title"])

    # Sprach-Startseiten
    for l in active:
        ui = UI[l]; s = seo.get(l, {})
        alts_home = {"en": f"{BASE}/", **{x: f"{BASE}/{x}/" for x in active}}   # T3: englische Startseite gehoert zum Cluster
        title = s.get("title") or f"M365.FM – {LANGS[l][0]}"
        d = short(s.get("description", ""), 300)
        newest = by_lang[l]
        thumb_html = lambda i: f'<div class="thumb"><a href="{url_of(i)}" title="{esc(i["e"]["title"])}"><figure class="cover" style="margin-inline:0">{yt_thumb(i["vid"], "")}</figure><h3>{esc(anchor_title(i["e"]["title"]))}</h3></a><p>{esc(short(parse_desc(i["e"]["desc"])[0], 110))}</p></div>'
        thumbs = "".join(thumb_html(i) for i in newest)
        ld = [{"@context": "https://schema.org", "@type": "PodcastSeries", "@id": f"{BASE}/{l}/#series", "name": title, "url": f"{BASE}/{l}/",
               "description": d, "inLanguage": LANGS[l][1], "webFeed": f"https://www.spreaker.com/show/{LANGS[l][3]}/episodes/feed", "image": f"{BASE}/assets/og-default.png",
               "numberOfEpisodes": len(newest),
               "sameAs": same_as(l, plat.get(l, {})),
               "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}, "publisher": {"@id": f"{BASE}/#org"}},
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
<div class="sec"><div class="kicker">01 · {esc(ui[3])}</div>{HUB.hub(globals_ctx, l, BASE, COMMUNITY_API, newest, lambda i: thumb_html(i))}</div></main>
{m365con_band()}
<main class="wrap"><section id="c-curator"></section><section id="c-sub"></section>{faq_html(l, "FAQ")}{author_box(l)}</main>{footer(l)}{community_tags(l)}"""
        write(f"{l}/index.html", page(l, title, short(d), f"{BASE}/{l}/", body, alts_home, ld, og_type="website", side=side_for(l, title, body)))
        sitemap.append((f"{BASE}/{l}/", TODAY, alts_home))

    # Wurzel
    alts_home = {"en": f"{BASE}/", **{x: f"{BASE}/{x}/" for x in active}}   # T3: Startseite (Englisch) im Cluster
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
<h1>The Microsoft community: <em>blog, podcast, events and explainers</em></h1>
<p class="lede">Posts and podcasts from community members, events with their sessions and animated explainers about Microsoft 365, Copilot, Azure and the Power Platform by Microsoft MVP Mirko Peters – in {len(active)} languages. Free.</p>
<div class="btns"><a class="btn main" href="{BASE}/community/">Join the community</a><a class="btn" href="#languages">Choose your language ↓</a><a class="btn" href="{YT_CHANNEL}">Watch on YouTube</a><a class="btn" href="{BASE}/entity/mirko-peters/">About Mirko Peters</a></div></div>
{spec_box("Now dubbed", f"{len(active)} editions", rows[:6])}
<div class="stats"><div><b>{len(items)}</b><span>Episodes</span></div><div><b>{nvid_all}</b><span>Videos</span></div><div><b>{len(active)}</b><span>Languages</span></div><div><b>0 €</b><span>Free</span></div></div>
{section(1, "Languages", f'<div class="lgrid">{tiles}</div>', "languages")}
{section(2, "How it works", spec_table("From one video to many shows", ("No.", "Step", "Detail"), steps))}
{section(3, "Latest from the community", HUB.hub(None, "en", BASE, COMMUNITY_API, latest, lambda i: f'<div class="thumb"><a href="{url_of(i)}" hreflang="{LANGS[i["lang"]][1]}" title="{esc(i["e"]["title"])}"><figure class="cover" style="margin-inline:0">{yt_thumb(i["vid"], "")}</figure><h3>{esc(anchor_title(i["e"]["title"]))}</h3></a><p>{esc(LANGS[i["lang"]][0])}</p></div>', root=True))}
{section(4, "Topics", f'<h2 style="margin-top:0">The Microsoft cloud, one concept at a time</h2><div class="chips">{topics_root}</div>')}</main>
{m365con_band()}
<main class="wrap">{faq_html('en', 'FAQ')}{cta_box("Want the full interviews?", "The main M365.FM show brings 900+ conversations with Microsoft MVPs, product experts and architects – in English.", "Go to M365.FM", "https://www.m365.fm")}{author_box('en')}</main>{footer_en()}"""
    write("index.html", page("en", "M365.FM – Microsoft community: blog, podcast, events & explainers | Mirko Peters",
          "Blog posts, podcasts and events from the Microsoft community plus animated explainers on Microsoft 365, Copilot, Azure and Power Platform by Microsoft MVP Mirko Peters – in 14 languages.",
          f"{BASE}/", root_body, alts_home, [person_ld(), org_ld(), event_ld(), faq_ld("en"), {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{BASE}/#website", "name": "M365.FM international", "url": f"{BASE}/", "inLanguage": [LANGS[x][1] for x in active], "publisher": {"@id": f"{BASE}/#org"}, "author": {"@id": f"{BASE}/entity/mirko-peters/#entity"}}], og_type="website"))
    sitemap.append((f"{BASE}/", TODAY, None))
    for _hk, _hc in HUB.MORE.items():   # T6: Karten jenseits der ersten 24 je Hub als JSON (Mehr laden / Filter)
        write(("" if _hk == "root" else _hk + "/") + "hub-more.json", json.dumps({"cards": _hc}, ensure_ascii=False))
    import site_updates as _SU2; _SU2.load(COMMUNITY_API)
    from site_learn import ENTS as _E2
    for _nl in ("en", "de"):
        _nu = f"{BASE}/{'de/' if _nl == 'de' else ''}updates/"
        _nt = "Updates – neu seit gestern" if _nl == "de" else "Updates – new since yesterday"
        _nb = f'{header(_nl, "")}<main class="wrap"><h1>{esc(_nt)}</h1><p class="mut">{esc("Was seit dem letzten Tag neu dazugekommen ist. Die Seite wird höchstens einmal täglich erweitert (abgeschlossene Tage)." if _nl == "de" else "What was added since the last day. The page grows at most once a day (completed days only).")}</p><p><a class="btn main" href="{BASE}/{"de/" if _nl == "de" else ""}community/#c-wish">{"Roadmap &amp; Wunschliste" if _nl == "de" else "Roadmap &amp; wishlist"}</a></p>{_SU2.page_block(_nl, lambda i, _l=_nl: f"{BASE}{'/' + _l if _l != 'en' else ''}/entity/{i}/", {k: v["name"] for k, v in _E2.items()})}{HUB.news(_nl, BASE)}</main>{footer(_nl)}'
        write(f"{'de/' if _nl == 'de' else ''}updates/index.html", page(_nl, f"{_nt} – M365.FM", "Neue Beiträge, Folgen, Videos, Bibliothekseinträge und Updates pro Tag." if _nl == "de" else "New posts, episodes, videos, library items and updates per day.", _nu, _nb, None, [{"@context": "https://schema.org", "@type": "CollectionPage", "@id": _nu + "#page", "name": _nt, "url": _nu, "inLanguage": _nl, "dateModified": TODAY, "isPartOf": {"@id": f"{BASE}/#website"}, "publisher": {"@id": f"{BASE}/#org"}}]))
        sitemap.append((_nu, TODAY, None))

    # Rechtliche Seiten (noindex)
    import site_legal as SL
    for path, fn, lg, ttl in (("impressum", SL.impressum_de, "de", "Impressum"), ("legal", SL.impressum_en, "en", "Legal notice"),
                              ("datenschutz", SL.privacy_de, "de", "Datenschutz"), ("privacy", SL.privacy_en, "en", "Privacy policy")):
        write(f"{path}/index.html", page(lg, f"{ttl} – M365.FM", ttl, f"{BASE}/{path}/", f"{header(lg, '')}<main class=\"wrap\" style=\"max-width:46em\">{fn()}</main>{footer(lg)}", og_type="website", noindex=True))

    # Barrierefreiheitserklaerung je Sprache
    for lg in ["en"] + list(active):
        if lg not in _AST and lg != "en":
            continue
        u = ast_url(lg)
        alts_ast = {x: ast_url(x) for x in active if x in _AST}
        write(("accessibility" if lg == "en" else f"{lg}/accessibility") + "/index.html", page(lg, ast_label(lg) + " – M365.FM", (_AST.get(lg) or _AST["en"]).get("meta", ""), u,
              f'{header(lg, "")}<main class="wrap" style="max-width:46em">{ast_body(lg)}</main>{footer(lg)}', alts_ast or None, [], xdefault=ast_url("en"), og_type="website", extra_head=f'<link rel="alternate" hreflang="en" href="{ast_url("en")}">\n'))
        sitemap.append((u, TODAY, alts_ast or None))

    # Community-Seite je Sprache (noindex) + Service Worker fuer Web-Push
    for l in list(active) + ["en"]:
        ct = _CI.get(l, _CI.get("en", {})).get("profile", "Profile")
        write("community/index.html" if l == "en" else f"{l}/community/index.html", page(l, f"{ct} – M365.FM" + ("" if l == "en" else f" {LANGS[l][0]}"), ct, (f"{BASE}/community/" if l == "en" else f"{BASE}/{l}/community/"), f'{header(l, "")}<main class="wrap" style="max-width:48em"><h1 id="c-h1">{esc(ct)}</h1><div id="c-page"></div><div id="c-expert"></div><div id="c-events"></div><div id="c-blog"></div><div id="c-podcast"></div><div id="c-shows"></div><div id="c-video"></div><div id="c-library"></div><div id="c-guests"></div><div id="c-feed"></div><div id="c-notes"></div><div id="c-wish"></div><div id="c-mail"></div><div id="c-messages"></div></main>{footer(l)}{community_tags(l)}<script>window.M365X={{api:"{COMMUNITY_API}",base:"{BASE}",lang:"{l}"}}</script><script defer src="{BASE}/assets/profile.js"></script><script defer src="{BASE}/assets/events.js"></script><script defer src="{BASE}/assets/editor.js"></script><script defer src="{BASE}/assets/seo.js"></script><script defer src="{BASE}/assets/credits.js"></script><script defer src="{BASE}/assets/notes.js"></script><script defer src="{BASE}/assets/blog.js"></script><script defer src="{BASE}/assets/podcast.js"></script><script defer src="{BASE}/assets/shows.js"></script><script defer src="{BASE}/assets/video.js"></script><script defer src="{BASE}/assets/library.js"></script><script defer src="{BASE}/assets/guests.js"></script><script defer src="{BASE}/assets/feeditems.js"></script><script defer src="{BASE}/assets/wish.js"></script><script defer src="{BASE}/assets/mailprefs.js"></script><script defer src="{BASE}/assets/messages.js"></script>', og_type="website", extra_head=LRN.WCSS, noindex=True))
    shutil.copy(ROOT / "assets" / "sw.js", OUT / "sw.js")
    if (ROOT / "data" / "m365con_program.json").exists():
        shutil.copy(ROOT / "data" / "m365con_program.json", OUT / "m365con_program.json")
    for _pf in ("m365con_program_2026.json", "m365con_program_dach.json"):
        if (ROOT / "data" / _pf).exists():
            shutil.copy(ROOT / "data" / _pf, OUT / _pf)

    # Entity-Seite
    A_EN = json.loads((ROOT / "data" / "about_en.json").read_text("utf-8"))
    A_ALL = json.loads((ROOT / "data" / "about_i18n.json").read_text("utf-8")) if (ROOT / "data" / "about_i18n.json").exists() else {}
    about_alts = {l: f"{BASE}/{l}/about/mirko-peters/" for l in active if l in A_ALL}
    about_en_url = f"{BASE}/about/mirko-peters/"
    hl_en = f'<link rel="alternate" hreflang="en" href="{about_en_url}">\n'

    def about_body(lang):
        A = A_EN if lang == "en" else A_ALL[lang]
        sub = lambda t: (t.replace("{MVP}", MVP).replace("{LINKEDIN}", LINKEDIN).replace("{YT}", YT_CHANNEL).replace("{LLMS}", f"{BASE}/llms.txt").replace("{N}", str(len(active))))
        g = lambda k: sub(A[k])
        portrait = (f'<img class="portrait" src="{BASE}/assets/mirko-peters.jpg" alt="{esc(A["portrait_alt"])}" width="190" height="190">' if (ROOT / "assets" / "mirko-peters.jpg").exists() else "")
        eps = f'<h2>{esc(A["eps_h"])}</h2><div class="btns"><a class="btn main" href="{BASE}/{lang}/">{esc(A["eps_btn"])}</a></div>' if lang != "en" else f'<h2>Podcast episodes by language</h2><div class="grid">{grid}</div>'
        fq = faq_html(lang, "FAQ")
        return f"""{header(lang, '')}
<main class="wrap"><div class="kicker">{esc(A["kicker"])}</div>{portrait}<h1>Mirko Peters</h1>
<p class="lede">{g("lede")}</p>
<div class="btns"><a class="btn main" href="https://www.m365.fm">M365.FM</a><a class="btn" href="https://m365con.net">M365Con</a><a class="btn" href="{LINKEDIN}" rel="me">LinkedIn</a><a class="btn" href="{YT_CHANNEL}">YouTube</a><a class="btn" href="{MVP}" rel="me">{esc(A["btn_mvp"])}</a></div>
<h2>{esc(A["short_h"])}</h2>
<ul class="points">{"".join(f"<li><span>{g(k)}</span></li>" for k in ("li1","li2","li3","li4","li5"))}</ul>
<h2>{esc(A["work_h"])}</h2>
<div class="cols">{"".join(f"<div><h3>{esc(A[k+'h'])}</h3><p>{g(k+'p')}</p></div>" for k in ("c1","c2","c3","c4"))}</div>
<h2>{esc(A["bio_h"])}</h2><p>{g("bio_p")}</p>
<h2>{esc(A["press_h"])}</h2><p>{g("press_p")}</p>
<h2>{esc(A["topics_h"])}</h2><p>{esc(A["topics_p"])}</p>
<h2>{esc(A["online_h"])}</h2>
<ul class="points">{"".join(f"<li><span>{g(k)}</span></li>" for k in ("o1","o2","o3","o4","o5"))}</ul>
{eps}</main>
{m365con_band()}
<main class="wrap">{fq}</main>{footer(lang) if lang != "en" else footer_en()}"""

    # Ausgemusterte Seiten: Hinweisseite mit Verknüpfung zum Nachfolger (kein Auto-Redirect), noindex
    _RT = {"en": ("Page retired", "This page no longer exists.", "It has been replaced by:", "Home"),
           "de": ("Seite ausgemustert", "Diese Seite gibt es nicht mehr.", "Sie wurde ersetzt durch:", "Startseite")}
    _ret = json.loads((ROOT / "data" / "retired.json").read_text("utf-8")).get("pages", []) if (ROOT / "data" / "retired.json").exists() else []
    for r in _ret:
        for lang in (["en"] + list(active) if r.get("langs") else ["en"]):
            pre = "" if lang == "en" else f"{lang}/"
            path = pre + r["path"]
            tl = _RT.get(lang, _RT["en"])
            to = r.get("to")
            tgt = (f"{BASE}/{pre}{to}" if (lang in ("en", "de") or not r.get("to_all_langs")) and lang == "de" else f"{BASE}/{to}") if to else None
            body = f'<main class="wrap"><h1>{tl[0]}</h1><p>{tl[1]}</p>' + (f'<p>{tl[2]} <a class="btn main" href="{tgt}">{esc(r.get("name") or to)}</a></p>' if tgt else "") + f'<p><a class="btn" href="{BASE}/{pre if lang in LANGS else ""}">{tl[3]}</a></p></main>'
            write(path + "index.html", page("de" if lang == "de" else "en", tl[0], tl[1], f"{BASE}/{path}", body, None, [], noindex=True))

    LRN.build_learn(dict(write=write, page=page, header=header, footer=footer, footer_en=footer_en, BASE=BASE, LANGS=LANGS, active=active, by_lang=by_lang, catidx=catidx,
                        articles=articles, url_of=url_of, cat_name=cat_name, ORDER=ORDER, strip_tags=strip_tags, anchor_title=anchor_title, short=short, parse_desc=parse_desc,
                        sitemap=sitemap, TODAY=TODAY, api=COMMUNITY_API, SCORE={l: (_QUI.get(l, {}).get("score") or _QUI["en"]["score"]) for l in list(LANGS) + ["en"]}))

    _ctx = dict(community_tags=community_tags, write=write, write_r2=write_r2, page=page, header=header, footer=footer, footer_en=footer_en, BASE=BASE, LANGS=LANGS, active=active, url_of=url_of, anchor_title=anchor_title, sitemap=sitemap, TODAY=TODAY, api=COMMUNITY_API, orig_alts=ORIG_ALTS)
    phase("Folgenseiten (Dub-Sprachen), Startseiten")
    _people, _orgs = MEM.fetch_members(COMMUNITY_API)

    import site_podpage as PP
    _epc = {}
    def _ep_find(e, lang="de"):
        """Folgen zu einer Entitaet: englisch aus der Hauptshow (Titel 3 Punkte, Kernpunkte/FAQ 1 Punkt), Dub-Sprachen per Titel-/Tag-Treffer."""
        k = (e["id"], lang)
        if k not in _epc:
            if lang == "en":
                _epc[k] = PP.find_episodes(BASE, e, LRN.ent_names(e))
            else:
                rx = [re.compile(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", re.I) for n in LRN.ent_names(e)]
                _bye = {str(it["eid"]): it for it in by_lang.get(lang, [])}
                _ext = [_bye[sid] for sid in SX.episodes_for(e["id"]) if sid in _bye]   # T27: QA-gepruefte Extraktion der Dub-Folge nennt die Entitaet
                _hit = [it for it in by_lang.get(lang, []) if any(r.search(it["e"]["title"] + " " + (it["e"].get("tags") or "")) for r in rx)] if rx else []
                _epc[k] = list({it["slug"]: it for it in _ext + _hit}.values())[:12]
        return _epc[k]
    _yt_by_slug = {v: k for k, v in ORIG.items()}   # Hauptshow-Folge -> YouTube-Video (gleiches Video wie die Dub-Fassungen)
    def _yt_of(x):
        if x.get("lang") != "en": return x.get("vid") or ""   # Dub-Folge: ihr YouTube-Video
        return x.get("yt") or _yt_by_slug.get(x.get("slug") or "", "")   # Hauptshow: aus der Extraktion, sonst ueber die Dub-Zuordnung
    _ctx["yt_of"] = _yt_of
    _ctx["ep_sum"] = lambda x: x.get("sum") or short(parse_desc(x["e"]["desc"])[0], 260)
    _ep_about = {}   # Folge der Hauptshow -> Entitaeten, auf deren Seite sie steht (fuer PodcastEpisode.about)
    for _e in ENT.ENTS.values():
        for _x in _ep_find(_e, "en"):
            _ep_about.setdefault(_x["slug"], []).append(_e["id"])
    _ctx["ep_about"] = _ep_about
    _epq = {str(it["eid"]): (url_of(it), it["e"]["title"]) for it in items.values()}   # Quotes: Spreaker-Folgen-ID -> (Seite, Titel); Dub-Folgen
    for _it in PP.episode_index(BASE)["items"]:   # Hauptshow: Spreaker-ID aus den Show Notes
        _nr = SNT.get("en", title=_it["e"]["title"])
        if _nr and _nr.get("id"): _epq.setdefault(str(_nr["id"]), (_it["url"], _it["e"]["title"]))
    _ctx["ep_by_spreaker"] = _epq
    print(len(_ep_about), "Folgen der Hauptshow auf Entitaetsseiten")
    _cl = (LRN._fetch_json(f"{COMMUNITY_API}/api/entity/claims") or {}).get("claims", []) if hasattr(LRN, "_fetch_json") else []
    ENT.ORGPAGES.update({o["eid"]: o["handle"] for o in _orgs if o.get("eid")})
    _events = EVT.fetch_events(COMMUNITY_API)
    for _ev in _events:
        ENT.EVENTS[_ev["handle"]] = _ev
        for _t in _ev.get("topics", []):
            ENT.EVENTS.setdefault(_t, _ev)
    for _x in (LRN._fetch_json(f"{COMMUNITY_API}/api/qa/export") or {}).get("items", []):
        ENT.FAQ.setdefault(_x["eid"], []).append(_x)
    ENT.CLAIMS.update({c["eid"]: c["handle"] for c in _cl}); MEM.CLAIMED.update({c["handle"]: c["eid"] for c in _cl})
    import site_updates as _SU
    _SU.load(COMMUNITY_API)
    import site_blog as BLG
    import site_legacy_blog as LBL
    _posts = BLG.fetch_posts(COMMUNITY_API); _have = {(p["slug"], p.get("lang") or "en") for p in _posts if p["handle"] == "mirko-p"}
    _posts += [p for p in LBL.items(BASE) if (p["slug"], p.get("lang") or "en") not in _have]   # plus die frueheren Podpage-Blogbeitraege als Community-Beitraege von mirko-p; T6: je Slug UND Sprache (die deutschen Fassungen blieben sonst beim D1-Import auf der Strecke)
    LBL.publish(write, BASE); MEM.BLOGLANGS = {p["lang"] for p in _posts}   # stand seit T6 versehentlich im Kommentar: blog-import/ fuer den Worker und die Blog-Sprachen der Profile
    import site_content_blog as CBL; CBL.publish(write, LRN.ENTS)   # T15: freigegebene Content-Pakete imports/blog/<sprache>/*.md -> blog-content/index.json (Worker-Cron importContentBlog)
    for _p in _posts:
        MEM.BLOGS.setdefault(_p["handle"], set()).add(_p["lang"])
        if _p["handle"] == "mirko-p" and _p.get("html") and _p["slug"] in LBL.TOPICS: _p["topics"] = LBL.TOPICS[_p["slug"]]   # Datenbank-Fassung: Themen beim Import eingefroren, hier die aktuelle Zuordnung
    _pname = {x["handle"]: x["name"] for x in _people}
    _pbt = {}   # Entitaet -> Blogbeitraege (neueste zuerst): jede Entitaetsseite zeigt und verlinkt ihre Artikel
    for _p in sorted(_posts, key=lambda x: x.get("published") or 0, reverse=True):
        _p.setdefault("name", _pname.get(_p["handle"], _p["handle"]))
        for _t in _p.get("topics", []):
            _pbt.setdefault(_t, []).append(_p)
    _ctx["posts_by_topic"] = _pbt; _ctx["author_box"] = author_box
    phase("Blog geladen, Folgen der Hauptshow zugeordnet")
    ENT.PERSON_LD = person_ld   # T4: eine Definition der Person Mirko Peters (Entitaetsseite nutzt denselben Knoten)
    ENT.build(_ctx, lambda lang: LRN.gloss_links(lang, BASE), MEM.experts_index(_people, _orgs), _ep_find)
    phase("Entitaetsseiten")
    MEM.build(_ctx, _people, _orgs, extra={l: EVT.blocks(BASE, _events, l) for l in COMM_LANGS})
    EVT.build(_ctx, _events, _people, _orgs)
    BLG.build(_ctx, _posts, _people, COMMUNITY_API)
    import site_library as LIB
    LIB.build(_ctx, LIB.fetch_items(COMMUNITY_API), _people, COMMUNITY_API)
    import site_guests as GST
    GST.build(_ctx, GST.fetch_listings(COMMUNITY_API), _people)
    import site_podcast as PODS
    PODS.build(_ctx, PODS.fetch_eps(COMMUNITY_API), _people, COMMUNITY_API)
    import site_video as VIDS
    VIDS.build(_ctx, VIDS.fetch_videos(COMMUNITY_API), _people, COMMUNITY_API)
    import site_feed as FEED
    FEED.build(_ctx, (LRN._fetch_json(f"{COMMUNITY_API}/api/feed/export") or {}).get("items", []), COMMUNITY_API)
    import site_shows as SHW
    SHW.build(_ctx, (LRN._fetch_json(f"{COMMUNITY_API}/api/show/export") or {}).get("items", []))
    phase("Community (Profile, Events, Blog, Bibliothek, Podcast, Video, Feed, Shows)")
    PP.build(_ctx)
    phase("Englische Show (Podpage)")
    MCPS.build(_ctx)
    LIVE.build(_ctx)   # M365 Show: Livestream-Seite + Seite je Stream (data/live.json, sync_live.py)
    try:   # SEO-Check-Seite (noindex): Episoden + Community-Inhalte
        _urls = {f'{i["vid"]}:{l}': url_of(i) for l in active for i in by_lang[l] if i.get("vid")}
        SEOR.build(_ctx, _people, [p for p in _posts if not p.get("legacy") and not p.get("html")], PODS.fetch_eps(COMMUNITY_API), VIDS.fetch_videos(COMMUNITY_API), (LRN._fetch_json(f"{COMMUNITY_API}/api/feed/export") or {}).get("items", []), SEOR.author_info(AUTHOR), _urls)
    except Exception as _e:
        import traceback; traceback.print_exc(); print("SEO page failed:", _e)

    PRS.build_press(dict(write=write, page=page, header=header, footer=footer, footer_en=footer_en, BASE=BASE, LANGS=LANGS, sitemap=sitemap, TODAY=TODAY, n_eps=len(items), n_langs=len(active),
                         EMAIL=SL.CONTACT_EMAIL, MVP=MVP, LINKEDIN=LINKEDIN, YT=YT_CHANNEL, person_ld=person_ld, org_ld=org_ld))

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
        hero = MED.hero_svg({"id": "cat-" + re.sub(r"\W+", "-", label.lower()), "name": label, "type": "category"}, kind, label)
        body = f"""{header(l, lang_switch(l, alts or {}, active))}
<main class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])}</nav>
<div class="kicker">{esc(kind)} · {esc(LANGS[l][0])}</div><h1>{esc(label)}</h1>{hero}
<p class="mut">{len(lst)} × {esc(ui[3])}</p>
<h2>{esc(ui[3])}</h2><div class="list">{rows_html(lst)}</div>
<h2>{esc(TOPICS.get(l, "Topics"))}</h2><div class="chips">{others}</div>
<p style="margin-top:1.6em"><a class="btn" href="{BASE}/{l}/">{esc(ui[3])} →</a></p></main>{footer(l)}"""
        return page(l, label, desc, canonical, body, alts, ld, og_type="website", noindex=noindex, side=side_for(l, label, body))

    ncat = ntag = 0
    for l in active:
        _pl = {"de": "Podcast auf Deutsch (KI-gedubbt)", "en": "Podcast"}.get(l, f"Podcast · {LANGS[l][0]}")
        _pu = f"{BASE}/{l}/podcast/"; _palts = {x: f"{BASE}/{x}/podcast/" for x in active}
        write(f"{l}/podcast/index.html", list_page(l, "Podcast", f"M365.FM {_pl}", by_lang[l], _pu, _palts, False))   # alle Folgen der Sprache (Spreaker-Show), ersetzt die Live-Seite im Menue der Sprachseiten
        sitemap.append((_pu, TODAY, _palts))
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
        label = top_label(l)
        prov = is_prov(l)
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
<main class="wrap"><nav class="crumbs" aria-label="breadcrumb"><a href="{BASE}/{l}/">{esc(ui[7])}</a> / {esc(LANGS[l][0])}</nav>
<div class="kicker">★ {esc(LANGS[l][0])} · {esc(wk)}</div><h1>{esc(label)}</h1>
<h2>{esc(ui[3])}</h2><div class="list">{rows}</div>
<p style="margin-top:1.6em"><a class="btn" href="{BASE}/{l}/">{esc(ui[3])} →</a></p></main>{footer(l)}"""
        write(f"{l}/top/index.html", page(l, f"{label} – M365.FM {LANGS[l][0]}", short(" · ".join(strip_tags(x["e"]["title"]).split(":")[0] for x in t[:3]), 155), u, body, alts, ld, og_type="website", noindex=prov, side=side_for(l, label, body)))
        if not prov:
            sitemap.append((u, wk, alts))
        topfeed[l] = [{"rank": n + 1, "title": strip_tags(x["e"]["title"]), "url": url_of(x), "episode": x["eid"]} for n, x in enumerate(t)]
    topfeed = {l: v for l, v in topfeed.items() if not is_prov(l)}
    if topfeed:
        write("top.json", json.dumps({"period": "last 7 days", "from": topdata.get("from"), "to": topdata.get("week_end"), "languages": topfeed}, ensure_ascii=False, indent=1))
        print(len(topfeed), "Sprachen mit Top-Woche")

    phase("Lernseiten, Updates, Top-Listen")
    # Sitemap-Index je Sprache und Typ (T1): sitemap-<sprache>-<typ>.xml mit echtem lastmod und x-default; Hubs (lastmod = Baudatum)
    # bekommen das juengste Datum ihrer Gruppe, der Index das juengste Datum je Datei. Grenzen je Datei: 45.000 URLs.
    import site_sitemaps as SMAP
    files = SMAP.write_all(sitemap, write, BASE, LANGS, TODAY)
    print(f"Sitemaps: {len(files)} Dateien, {len(sitemap)} URLs")
    _showix = PP.episode_index(BASE)
    phase("Sitemaps")
    import site_quotes as _SQ
    write("quotes.json", json.dumps({"version": 1, "generated": TODAY, "quotes": _SQ.ALL}, ensure_ascii=False))   # Quotes an Personen-Entitaeten; der Worker uebernimmt sie in D1 (importQuotesFromSite)
    write("robots.txt", f"User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\nAllow: /\n\n# KI-Suchen und Assistenten ausdrücklich erlaubt\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot")) + f"Sitemap: {BASE}/sitemap.xml\n")
    # llms.txt (Überblick), llms-full.txt (alle Folgen), agent.json (Maschinen-Beschreibung), episodes.json (Datenfeed)
    summ = (f"AI-dubbed podcast episodes about Microsoft 365, Copilot, Azure, Power Platform and AI governance by Microsoft MVP Mirko Peters, "
            f"in {len(active)} languages. Each episode has its own page with player, YouTube video, key points, transcript link and links to Spotify, Amazon Music, Deezer and more.")
    L = [f"# M365.FM international – Mirko Peters", "", f"> {summ}", "",
         "Author: Mirko Peters (Microsoft MVP), host of the M365.FM podcast and the m365 Show on YouTube, organizer of M365Con (free online conference, 2027-01-11 to 2027-01-22).", "",
         "## Core", f"- [About Mirko Peters]({BASE}/entity/mirko-peters/): profile, expertise, links", f"- [Microsoft MVP profile]({MVP}): official Microsoft MVP recognition of Mirko Peters", f"- [Full episode list]({BASE}/llms-full.txt): every episode with title, language and summary",
         f"- [Machine-readable feed]({BASE}/episodes.json): all episodes as JSON", f"- [Agent card]({BASE}/agent.json): capabilities for AI agents", f"- [Sitemap]({BASE}/sitemap.xml)", "",
         "## Main show, knowledge graph and blog (English)",
         f"- [M365.FM podcast, all episodes]({BASE}/show/episodes/): {len(_showix['items'])} English episodes with key points, FAQ and transcript – list in [llms-show.txt]({BASE}/llms-show.txt)",
         f"- [Entities]({BASE}/entity/): {len(ENT.ENTS)} Microsoft products, concepts, certifications and people with definition, facts, sources, episodes and articles – list in [llms-entities.txt]({BASE}/llms-entities.txt), data in [entities.json]({BASE}/entities.json) and [entities.jsonld]({BASE}/entities.jsonld); each entity has a feed at /entity/<id>/feed.xml",
         f"- [Blog]({BASE}/community/u/mirko-p/blog/): {sum(1 for p in _posts if p.get('lang') == 'en')} articles by Mirko Peters – list in [llms-blog.txt]({BASE}/llms-blog.txt), data in [articles.json]({BASE}/articles.json)",
         f"- [Glossary]({BASE}/glossary/): short definitions of Microsoft terms (English and German)",
         f"- [M365 Show live stream]({BASE}/live/): the running live show on YouTube, past and upcoming streams",
         f"- Programmatic access: [OpenAPI]({BASE}/openapi.json), [MCP server card]({BASE}/.well-known/mcp/server-card.json), [A2A agent card]({BASE}/.well-known/agent-card.json), [auth.md]({BASE}/auth.md)", "",
         "## Languages"]
    for l in active:
        L.append(f"- [{LANGS[l][0]}]({BASE}/{l}/): {len(by_lang[l])} episodes – topics: " + ", ".join(cat_name(c, l) for c in ORDER if c in catidx[l]))
    L += ["", "## Topics (English labels; localized per language)"]
    for c in ORDER:
        L.append(f"- {cat_name(c, 'en')}: " + ", ".join(f"[{l}]({cat_url(l, c)})" for l in active if c in catidx[l]))
    write("llms.txt", "\n".join(L) + "\n")
    # Hauptshow, Entitaeten und Blog als eigene Listen fuer KI-Suchen und Agenten (bisher kannten llms*.txt und episodes.json nur die Dub-Folgen)
    _S = [f"# M365.FM podcast – all {len(_showix['items'])} English episodes", "", "> Conversations with Microsoft MVPs, product experts and architects about Microsoft 365, Copilot, Azure, Power Platform, security and AI; host Mirko Peters (Microsoft MVP). Each page has key points, FAQ, guests and a transcript.", ""]
    for x in _showix["items"]:
        _S.append(f"- [{x['e']['title']}]({x['url']}) – {x['date']}" + (f" – {x['sum'][:200]}" if x.get("sum") else "") + (f" – key points: {' | '.join(k[:120] for k in x['keypoints'][:3])}" if x.get("keypoints") else ""))
    write("llms-show.txt", "\n".join(_S) + "\n")
    _E = [f"# M365.FM entities – {len(ENT.ENTS)} Microsoft products, concepts, certifications and people", "", "> Each entity page has a definition, facts, sources, related episodes and articles, FAQ and a feed (/entity/<id>/feed.xml). JSON: /entities.json, JSON-LD: /entities.jsonld.", ""]
    for e in sorted(ENT.ENTS.values(), key=lambda e: (e["type"], e["name"].lower())):
        if e.get("type") == "person" and not (e.get("desc") or {}).get("en"): continue
        _E.append(f"- [{e['name']}]({BASE}/entity/{e['id']}/) ({e['type']}): {((e.get('desc') or {}).get('en') or (e.get('desc') or {}).get('de') or '')[:220]}")
    write("llms-entities.txt", "\n".join(_E) + "\n")
    _B = [f"# M365.FM blog – articles by Mirko Peters", "", "> Articles about Microsoft 365, Copilot, Azure, Power Platform, security, governance and AI. Each article links its topics (entities).", ""]
    _bp = sorted([p for p in _posts if p.get("lang") == "en"], key=lambda p: -(p.get("published") or 0))
    for p in _bp:
        _B.append(f"- [{p['title']}]({BASE}/community/u/{p['handle']}/blog/{p['slug']}/) – {BLG.iso(p['published'])}" + (f" – {(p.get('summary') or '')[:200]}" if p.get("summary") else "") + (f" – topics: {', '.join(ENT.ENTS[t]['name'] for t in (p.get('topics') or [])[:4] if t in ENT.ENTS)}" if p.get("topics") else ""))
    write("llms-blog.txt", "\n".join(_B) + "\n")
    write("articles.json", json.dumps({"name": "M365.FM blog", "author": "Mirko Peters", "generated": TODAY, "count": len(_bp), "articles": [
        {"slug": p["slug"], "title": p["title"], "url": f"{BASE}/community/u/{p['handle']}/blog/{p['slug']}/", "date": BLG.iso(p["published"]), "summary": (p.get("summary") or "")[:300], "topics": [t for t in (p.get("topics") or []) if t in ENT.ENTS],
         "translations": {q["lang"]: f"{BASE}/{q['lang']}/community/u/{q['handle']}/blog/{q['slug']}/" for q in _posts if q.get("tr_of") and q["slug"] == p["slug"] and q["handle"] == p["handle"]}} for p in _bp]}, ensure_ascii=False))
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
    for x in feed: x["kind"] = "dub"
    feed += [{"id": x["slug"], "kind": "show", "language": "en", "title": x["e"]["title"], "url": x["url"], "date": x["date"], "summary": (x.get("sum") or "")[:300], "keypoints": x.get("keypoints") or [],
              "entities": (_ep_about.get(x["slug"]) or [])[:12], "guests": x.get("guests") or [], "duration": x.get("duration") or "", "alternates": {}} for x in _showix["items"]]
    write("episodes.json", json.dumps({"name": "M365.FM international", "author": "Mirko Peters", "generated": TODAY, "count": len(feed), "episodes": feed}, ensure_ascii=False))
    write("agent.json", json.dumps({
        "schemaVersion": "1.0", "name": "M365.FM international", "description": summ, "url": f"{BASE}/", "version": TODAY,
        "provider": {"organization": "M365.FM", "url": "https://www.m365.fm", "person": "Mirko Peters", "personUrl": f"{BASE}/entity/mirko-peters/"},
        "documentationUrl": f"{BASE}/llms.txt", "license": "Content © Mirko Peters / M365.FM. Citation with link to the episode page welcome.",
        "capabilities": {"streaming": False, "readOnly": True, "authentication": "none"},
        "languages": [LANGS[l][1] for l in active],
        "interfaces": {"llms": f"{BASE}/llms.txt", "llmsFull": f"{BASE}/llms-full.txt", "llmsShow": f"{BASE}/llms-show.txt", "llmsEntities": f"{BASE}/llms-entities.txt", "llmsBlog": f"{BASE}/llms-blog.txt",
                       "episodesJson": f"{BASE}/episodes.json", "entitiesJson": f"{BASE}/entities.json", "entitiesJsonLd": f"{BASE}/entities.jsonld", "articlesJson": f"{BASE}/articles.json", "openapi": f"{BASE}/openapi.json", "mcp": f"{BASE}/.well-known/mcp/server-card.json", "a2a": f"{BASE}/.well-known/agent-card.json", "sitemap": f"{BASE}/sitemap.xml",
                       "rss": {l: f"https://www.spreaker.com/show/{LANGS[l][3]}/episodes/feed" for l in active}},
        "skills": [
            {"id": "find-episode", "name": "Find an episode", "description": "Find podcast episodes about Microsoft 365, Copilot, Azure, Power Platform, security and AI governance in a given language. Use episodes.json (filter by language, categories, tags) and link to the episode page.", "inputModes": ["text"], "outputModes": ["application/json", "text/html"]},
            {"id": "translate-link", "name": "Same episode in another language", "description": "Each episode page lists its alternate-language versions (hreflang / 'alternates' in episodes.json).", "inputModes": ["text"], "outputModes": ["application/json"]},
            {"id": "about-author", "name": "About Mirko Peters", "description": "Microsoft MVP, M365.FM host, M365Con organizer – see the about page.", "inputModes": ["text"], "outputModes": ["text/html"]},
            {"id": "find-entity", "name": "Look up a Microsoft product, concept or certification", "description": "entities.json / llms-entities.txt: definition, facts, sources, related episodes and articles for each entity; entity pages define schema.org nodes (#entity).", "inputModes": ["text"], "outputModes": ["application/json", "text/html"]},
            {"id": "find-article", "name": "Find a blog article", "description": "articles.json / llms-blog.txt: articles with date, summary and topics (entity ids); episodes.json entries with kind 'show' carry the same entity ids.", "inputModes": ["text"], "outputModes": ["application/json", "text/html"]}]
    }, ensure_ascii=False, indent=1))
    write(".well-known/agent.json", (OUT / "agent.json").read_text(encoding="utf-8"))
    _card = json.loads((OUT / "agent.json").read_text(encoding="utf-8"))   # A2A Agent Card: dieselben Faehigkeiten, Schnittstelle ist /a2a im Worker (nur lesen)
    write(".well-known/agent-card.json", json.dumps({
        "name": "M365.FM", "description": _card["description"], "version": TODAY,
        "supportedInterfaces": [{"url": "https://api-dub.m365.fm/a2a", "protocolBinding": "JSONRPC", "protocolVersion": "0.3.0"}],
        "url": "https://api-dub.m365.fm/a2a", "preferredTransport": "JSONRPC", "protocolVersion": "0.3.0",
        "provider": {"organization": "M365.FM", "url": f"{BASE}/"}, "documentationUrl": f"{BASE}/llms.txt",
        "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": False},
        "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain"],
        "skills": [{"id": "find-episode", "name": "Find an episode", "description": "Send a text question (optionally naming a language) with message/send; the agent answers with matching M365.FM episodes and their URLs.",
                    "tags": ["microsoft-365", "copilot", "azure", "podcast"], "examples": ["Find episodes about Copilot governance", "German episodes about Teams"],
                    "inputModes": ["text/plain"], "outputModes": ["text/plain"]}]}, ensure_ascii=False, indent=1))
    write(".well-known/mcp/server-card.json", json.dumps({   # MCP Server Card (SEP-1649)
        "serverInfo": {"name": "m365-dub", "title": "M365.FM Community (www.m365.fm)", "version": "1.1.0"},
        "description": "Read the M365.FM community (blog, shows, entities, experts, events) without sign-in; write and personal tools with a personal access token.",
        "transport": {"type": "streamable-http", "endpoint": "https://api-dub.m365.fm/mcp"}, "endpoint": "https://api-dub.m365.fm/mcp",
        "protocolVersion": "2025-06-18",
        "capabilities": {"tools": {"listChanged": False}},
        "authentication": {"required": False, "schemes": ["bearer"], "description": f"Reading needs no credentials. Write tools need a personal access token (Authorization: Bearer m365_...), see {BASE}/auth.md"},
        "documentationUrl": f"{BASE}/auth.md"}, ensure_ascii=False, indent=1))
    _sk = {   # Agent Skills Discovery 0.2.0: SKILL.md je Faehigkeit mit SHA-256
        "find-m365-episodes": ("Find M365.FM podcast episodes about Microsoft 365, Copilot, Azure, Power Platform, security and AI governance, in 14 languages.",
            f"# Find M365.FM episodes\n\nUse this skill to find podcast episodes of M365.FM.\n\n1. Fetch {BASE}/episodes.json (all episodes: title, language, date, url, summary, categories, tags, alternates).\n2. Filter by `language` (ISO code) and match the user's topic against title, summary, categories and tags.\n3. Answer with the episode title, date and `url`. Each episode lists the same episode in other languages under `alternates`.\n\nAlternatives: {BASE}/llms.txt (overview), or the A2A agent at https://api-dub.m365.fm/a2a (method `message/send`, text in, matching episodes out).\nCite the episode page when you use its content.\n"),
        "find-m365-experts": ("Find community experts for a Microsoft topic, including experts on related topics, with the public MCP tool find_experts.",
            f"# Find M365 experts\n\nUse the public MCP server `https://api-dub.m365.fm/mcp` (Streamable HTTP, JSON-RPC, no sign-in for reading).\n\n1. Call the tool `find_experts` with an entity id (for example `copilot`, `purview`, `intune`; entity pages live at {BASE}/entity/<id>/).\n2. The result ranks members by their expertise on the topic and on related topics (graph search, up to 2 hops).\n3. Link to the expert's profile when you name them.\n\nPlain REST alternative: `GET https://api-dub.m365.fm/api/experts?e=<entity-id>&hops=2&limit=12`.\n"),
        "use-m365-mcp": ("Connect to the M365.FM MCP server: read tools without sign-in, write tools with a personal access token.",
            f"# Use the M365.FM MCP server\n\nEndpoint: `https://api-dub.m365.fm/mcp` (Streamable HTTP, JSON-RPC 2.0).\n\n- Reading (blog, shows, entities, experts, events): no credentials.\n- Writing and personal data (for example `save_blog_post`, `get_my_profile`): send `Authorization: Bearer m365_...`. A signed-in member creates the token under their profile; agents cannot register themselves. Details: {BASE}/auth.md.\n- Call `tools/list` first; each tool describes its parameters. Never invent entity ids: look them up at {BASE}/entity/ or with the tool `suggest_entities`.\n")
    }
    _idx = []
    for _n, (_d, _md) in _sk.items():
        _b = _md.encode("utf-8")
        write(f".well-known/agent-skills/{_n}/SKILL.md", _md)
        _idx.append({"name": _n, "type": "skill-md", "description": _d, "url": f"{BASE}/.well-known/agent-skills/{_n}/SKILL.md", "digest": "sha256:" + hashlib.sha256(_b).hexdigest()})
    write(".well-known/agent-skills/index.json", json.dumps({"$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json", "skills": _idx}, ensure_ascii=False, indent=1))
    write("auth.md", f"""# M365.FM auth.md

How AI agents get access to M365.FM. This file is self-contained: the service publishes no OAuth metadata and has no self-service agent registration.

## Audience

AI agents and MCP clients that read M365.FM content or act on behalf of a signed-in member.

## Public access (no credentials)

- Website, `llms.txt`, `episodes.json`, sitemap and RSS: {BASE}/ - no authentication.
- MCP server `https://api-dub.m365.fm/mcp` (Streamable HTTP, JSON-RPC): all read tools work without credentials.
- Public REST endpoints are listed in {BASE}/openapi.json and {BASE}/.well-known/api-catalog.

## Authenticated access (writes and personal data)

Write tools and personal tools (for example `save_blog_post`, `get_my_profile`) need a personal AI access token.

- **Method:** `personal_access_token`. A human member signs in at {BASE}/community/ and creates the token under their profile (label, up to 5 tokens, shown once, revocable at any time).
- **Registration endpoint for agents:** none. Agents cannot register themselves or create accounts. A person must issue the token.
- **Anonymous and verified-email registration:** not supported.
- **Credential use:** send `Authorization: Bearer m365_...` to `https://api-dub.m365.fm/mcp`. The token acts with the rights of the member who created it, is rate limited, and never grants admin rights beyond that member's own role.
- **Revocation:** the member deletes the token in their profile; deleting the account removes all tokens.

## Contact

Mirko Peters, {BASE}/about/
""")
    _api = "https://api-dub.m365.fm"   # RFC 9727: API-Katalog + OpenAPI-Beschreibung der oeffentlichen Schnittstellen
    _j = {"application/json": {"schema": {"type": "object"}}}
    write("openapi.json", json.dumps({
        "openapi": "3.1.0",
        "info": {"title": "M365.FM Community API", "version": "1.0.0", "description": "Public, read-only endpoints of the M365.FM community platform (experts, entities, blog) and the MCP server at /mcp. Everything else requires sign-in.", "contact": {"name": "Mirko Peters", "url": f"{BASE}/about/"}},
        "servers": [{"url": _api}],
        "paths": {
            "/api/health": {"get": {"summary": "Health check", "responses": {"200": {"description": "Service is up", "content": _j}}}},
            "/api/experts": {"get": {"summary": "Experts for a topic, including related topics", "parameters": [
                {"name": "e", "in": "query", "required": True, "schema": {"type": "string"}, "description": "Entity id"},
                {"name": "hops", "in": "query", "schema": {"type": "integer", "default": 2}},
                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 12, "maximum": 30}}],
                "responses": {"200": {"description": "Experts", "content": _j}, "404": {"description": "Unknown entity"}}}},
            "/api/entity/export": {"get": {"summary": "Community revisions of entities", "responses": {"200": {"description": "Entities", "content": _j}}}},
            "/api/blog/export": {"get": {"summary": "Published community blog posts of public profiles", "responses": {"200": {"description": "Posts", "content": _j}}}},
            "/mcp": {"post": {"summary": "Model Context Protocol server (JSON-RPC over HTTP)", "requestBody": {"content": _j}, "responses": {"200": {"description": "JSON-RPC response", "content": _j}}}}}},
        ensure_ascii=False, indent=1))
    write(".well-known/api-catalog", json.dumps({"linkset": [{
        "anchor": f"{_api}/api",
        "service-desc": [{"href": f"{BASE}/openapi.json", "type": "application/vnd.oai.openapi+json"}],
        "service-doc": [{"href": f"{BASE}/llms.txt", "type": "text/plain"}],
        "status": [{"href": f"{_api}/api/health", "type": "application/json"}]}]}, indent=1))
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)
    if _dom:
        write("CNAME", _dom)
    if ADS.ads_txt(BASE):
        write("ads.txt", ADS.ads_txt(BASE))
    print("AdSense:", json.dumps(ADS.status(BASE)))
    # Verwaltung ohne Code (assets/admin.js): nur fuer Admins, nicht in Suchmaschinen
    _adm_css = ("<style>.adm-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:1em 0}.adm-tabs button{font:inherit;padding:.45em 1em;border:1px solid var(--bd);border-radius:2em;background:var(--card);color:inherit;cursor:pointer}"
                ".adm-tabs button[aria-selected=true]{border-color:var(--ac);background:var(--ac);color:#fff}.adm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(11em,1fr));gap:10px}"
                ".adm-tile{border:1px solid var(--bd);border-radius:.6em;padding:.8em;background:var(--card);display:flex;flex-direction:column;gap:.1em}.adm-tile b{font-size:1.7rem;line-height:1.1}.adm-tile.on b{color:var(--ac)}.adm-tile small{color:var(--mut)}"
                ".adm-row{display:flex;gap:8px;flex-wrap:wrap}.adm-row input{flex:1;min-width:12em}.adm-row input,.adm-row select{font:inherit;padding:.5em .7em;border:1px solid var(--bd);border-radius:.4em;background:var(--card);color:inherit}.adm-list{list-style:none;padding:0;margin:1em 0}.adm-item{font:inherit;color:inherit;background:none;border:0;border-bottom:1px solid var(--bd);width:100%;text-align:start;padding:.55em .2em;cursor:pointer}.adm-item:hover{background:var(--card)}"
                ".adm-tbl{width:100%;border-collapse:collapse;font-size:.92rem}.adm-tbl th,.adm-tbl td{text-align:start;padding:.35em .4em;border-bottom:1px solid var(--bd);vertical-align:top}.adm-tbl th{position:sticky;top:0;background:var(--bg)}"
                ".adm-chip{display:inline-block;min-width:2.2em;text-align:center;font:600 .78rem/1.6 inherit;border:1px solid var(--bd);border-radius:1em;margin:1px;background:none;color:inherit;cursor:pointer;padding:0 .3em}.adm-chip.ok{background:#1e7a4a;color:#fff;border-color:#1e7a4a;cursor:default}.adm-chip.q{background:var(--ac);color:#fff;border-color:var(--ac)}.adm-chip.fail{border-color:#b43;color:#b43}"
                ".adm-sum{display:grid;grid-template-columns:repeat(auto-fill,minmax(7.5em,1fr));gap:6px;margin:.6em 0}.adm-sum div{border:1px solid var(--bd);border-radius:.5em;padding:.4em .6em;background:var(--card)}.adm-sum b{display:block;font-size:1.1rem}.adm-sum small{color:var(--mut)}.adm-ops td{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85rem}"
                ".adm-badge{font-size:.75rem;border:1px solid var(--bd);border-radius:1em;padding:.05em .6em;color:var(--mut)}.adm-badge.on{border-color:var(--ac);color:var(--ac)}"
                ".adm-form{border:1px solid var(--bd);border-radius:.7em;padding:1em 1.2em;background:var(--card);margin:1em 0}.adm-field{display:flex;flex-direction:column;gap:.2em;margin:.7em 0}.adm-field input,.adm-field textarea,.adm-field select{font:inherit;padding:.45em .6em;border:1px solid var(--bd);border-radius:.4em;background:var(--bg);color:inherit}"
                ".adm-msg{min-height:1.4em}.adm-msg.bad{color:var(--ac);font-weight:600}</style>")
    write("admin/index.html", page("de", "Verwaltung – M365.FM", "Verwaltung der Website ohne Code", f"{BASE}/admin/",
          f'{header("de", "")}<main class="wrap" id="main"><h1>Verwaltung</h1><p class="mut">Inhalte, Datenbank und Schalter der Website, ohne Code. Nur für Admins.</p>'
          f'<div id="adm"><p class="mut">Lädt …</p></div>{_adm_css}'
          f'<script>window.M365ADM={{api:"{COMMUNITY_API}",base:"{BASE}"}}</script><script defer src="{BASE}/assets/admin.js"></script></main>{footer("de")}',
          noindex=True, og_type="website"))
    write("callback/index.html", """<!doctype html><meta charset=utf-8><meta name=robots content="noindex,nofollow"><meta name=viewport content="width=device-width,initial-scale=1"><title>Anmeldung</title>
<body style="font-family:system-ui,sans-serif;background:#101214;color:#e9ecef;padding:40px;max-width:640px;margin:auto"><h2>Anmeldung</h2><p id=m>Kein Code in der Adresse.</p>
<pre id=c style="white-space:pre-wrap;word-break:break-all;background:#1d2126;padding:14px;border:1px solid #444"></pre><button id=b style="display:none;padding:10px 18px">Code kopieren</button>
<script>var q=new URLSearchParams(location.search),c=q.get("code");if(c){document.getElementById("m").textContent="Code (in das Programm bzw. den GitHub-Workflow einfügen):";document.getElementById("c").textContent=c;var b=document.getElementById("b");b.style.display="inline-block";b.onclick=function(){navigator.clipboard.writeText(c);b.textContent="Kopiert ✓"}}else if(q.get("error")){document.getElementById("m").textContent="Fehler: "+q.get("error")}</script></body>""")
    write("og-manifest.json", json.dumps(OGLIST, ensure_ascii=False))
    write("404.html", page("en", "Not found", "Page not found", f"{BASE}/404.html", '<main class="wrap"><h1>404</h1><p><a class="btn" href="%s/">M365.FM</a></p></main>' % BASE, noindex=True))
    json.dump([u for u, _, _ in sitemap], open(ROOT / "data" / "urls.json", "w", encoding="utf-8"), indent=0)
    from site_i18n import write_src
    write_src(OUT, ROOT / "data" / "ui_js_en.json")
    import site_trstatus as TRS
    try:
        TRS.build(write, TODAY, list(ENT.ENTS.values()), [{"slug": p["slug"], "title": p["title"]} for p in _posts if p.get("legacy") and p.get("lang") == "en"], [{"slug": x["slug"], "title": x["e"]["title"]} for x in PP.episode_index(BASE)["items"]])
    except Exception as _e:
        print("Uebersetzungsstatus nicht geschrieben:", str(_e)[:160])
    # Inhalt <-> Entitaet mit Gewicht fuer die Datenbank (content_topic, Paket 13): fruehere Beitraege (Slug) und Folgen der Hauptshow (Slug); der Worker uebernimmt die Liste alle 30 Minuten
    _tj = []
    for _p in _posts:
        if _p.get("handle") == "mirko-p" and _p.get("html") and _p.get("lang") == "en":
            for _i, _t in enumerate((_p.get("topics") or [])[:8]): _tj.append({"kind": "lblog", "id": _p["slug"], "eid": _t, "w": round(max(0.2, 1 - _i * 0.15), 2)})
    for _slug, _eids in _ep_about.items():
        for _i, _t in enumerate(_eids[:8]): _tj.append({"kind": "show", "id": _slug, "eid": _t, "w": round(max(0.2, 1 - _i * 0.15), 2)})
    write("topics.json", json.dumps({"generated": TODAY, "count": len(_tj), "items": _tj}, ensure_ascii=False))
    import site_register as REG
    try:
        REG.build(write, BASE, TODAY, _posts)
    except Exception as _e:
        print("Register nicht geschrieben:", str(_e)[:160])
    phase("Agenten-Dateien, 404, UI-Quellen")
    sizes()
    print(f"r2out/: {_r2n[0]} Seiten, {_r2n[1] / 1e6:.0f} MB (werden in den R2-Bucket geladen, nicht in GitHub Pages)")
    print(f"{len(items)} Episodenseiten, {len(active)} Sprachen, {len(sitemap)} URLs → docs/")


def footer_en():
    return footer("en")


if __name__ == "__main__":
    (ROOT / "data").mkdir(exist_ok=True)
    build()
