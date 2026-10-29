"""Design-Modul fuer dub.m365.fm ("Industry"-Designsprache aus dem Claude-Design-Projekt).
Enthaelt CSS-Tokens und HTML-Bausteine; generate_site.py setzt damit die Seiten zusammen."""
import html

def _e(s): return html.escape(s or "", quote=True)

_LR = {"latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
       "latin-ext": "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"}
FONT_CSS = "".join(
    f'@font-face{{font-family:"{fam}";font-style:normal;font-weight:{w};font-display:swap;src:url(/assets/fonts/{fn}-{sub}-{w}-normal.woff2) format("woff2");unicode-range:{_LR[sub]}}}'
    for fam, fn, ws in (("Barlow Condensed", "barlow-condensed", (500, 600, 700)), ("Barlow", "barlow", (400, 500, 600)))
    for w in ws for sub in ("latin", "latin-ext")) + "\n"
INDUSTRY = """
:root{--bg:#f3f3f2;--fg:#17191c;--mut:#5d6470;--ac:#3b6391;--card:#fff;--bd:#17191c24;--ink:#1a1d21;--onink:#eef0f3}
@media (prefers-color-scheme:dark){:root{--bg:#101214;--fg:#e9ecef;--mut:#98a0ab;--ac:#82a7d4;--card:#16191c;--bd:#e9ecef26;--ink:#1d2126;--onink:#eef0f3}}
body{font-family:"Barlow",-apple-system,"Segoe UI",Inter,Roboto,"Noto Sans",system-ui,sans-serif}
.serif,h1,h2,h3,h4,.brand,.tile b,.num,.row h3,.thumb h3,.faq summary,.cols h3,.stats b,.ifacts b,.info figcaption,.points li:before,.author .badge{font-family:"Barlow Condensed","Arial Narrow","Noto Sans",system-ui,sans-serif}
h1,h2{text-transform:uppercase;font-weight:600;letter-spacing:.01em}
h1{font-size:clamp(2.1rem,6vw,4.4rem);line-height:1;letter-spacing:0}
article h1{font-size:clamp(1.8rem,4.2vw,3rem);line-height:1.05}
h2{font-size:1.7rem;letter-spacing:.02em}
.brand{text-transform:uppercase;letter-spacing:.04em;font-weight:700}.brand i{color:var(--ac)}
.top{border-bottom:1px solid var(--bd)}
nav.langs{font-family:"Barlow Condensed",sans-serif;font-weight:500;letter-spacing:.12em}nav.langs a[aria-current]{border-bottom:2px solid var(--ac)}
.kicker{display:flex;align-items:center;gap:14px;font-family:"Barlow Condensed",sans-serif;font-weight:600;letter-spacing:.16em;color:var(--ac)}.kicker:after{content:"";flex:1;height:1px;background:var(--bd)}
.row h3,.thumb h3,.faq summary,.cols h3{font-weight:600;font-size:1.4rem;line-height:1.15}
.btn{border-radius:0;font-family:"Barlow Condensed",sans-serif;font-weight:600;letter-spacing:.1em;padding:9px 18px;border-color:var(--fg)}
.btn.main{background:var(--ac);border-color:var(--ac);color:#fff}.btn:hover{background:var(--ac);border-color:var(--ac);color:#fff}
.panel,.cover,.yt,.info,.portrait,.author .badge,.author img.badge{border-radius:0}.panel iframe{border-radius:0}
.panel{background:var(--ink)}.band{background:var(--ink)}
.tile,.thumb{position:relative}
.tile{padding:28px 18px 18px;border:1px solid var(--bd);margin:-1px 0 0 -1px}.grid{border:0}
.tile:before,.tile:after{content:"+";position:absolute;top:-10px;font:300 19px/1 "Barlow",sans-serif;color:var(--mut)}.tile:before{left:-5px}.tile:after{right:-5px}
.tile b{font-weight:600;font-size:1.7rem}.tile:hover{background:var(--ink);color:var(--onink)}
.stats{border-color:var(--bd)}.stats b{color:var(--ac);font-weight:600}.points,.list{border-top:1px solid var(--bd)}.points li:before{color:var(--ac);font-weight:600}
.author,.share,footer{border-color:var(--bd)}.author .badge{background:var(--ac);color:#fff}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 16px}
.chip{display:inline-block;padding:2px 10px;border:1px solid var(--bd);font:600 .8rem/1.7 "Barlow Condensed",sans-serif;letter-spacing:.09em;text-transform:uppercase;text-decoration:none;color:var(--mut)}
.chip.cat{border-color:var(--ac);color:var(--ac)}.chip:hover{background:var(--ac);border-color:var(--ac);color:#fff}
.ilink{text-decoration:underline;text-decoration-color:var(--ac);text-decoration-thickness:2px;text-underline-offset:3px}
.info{background:var(--card)}.isteps i{border-radius:0;background:var(--ac)}.icol{border-top-color:var(--ac)}.ifacts div{border-left-color:var(--ac)}

/* ---- Design-Modul: Komponenten nach "SEO-Design fuer dub.m365.fm" ---- */
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.brand{font-size:1.25rem}.brand i{font-style:normal}.brand .dub{color:var(--ac);margin-left:6px}
.hero{padding:54px 0 12px}.hero h1{font-size:clamp(2.6rem,8vw,5.4rem);line-height:.98;margin:0 0 .35em}.hero h1 em{font-style:normal;color:var(--ac);display:block}
.hero .lede{color:var(--mut);font-size:1.12rem;max-width:34em}
.xbox{position:relative;border:1px solid var(--bd);margin:34px 0;padding:18px 20px}
.xbox:before,.xbox:after,.xbox>.x1,.xbox>.x2{content:"+";position:absolute;font:300 19px/1 "Barlow",sans-serif;color:var(--mut);background:var(--bg)}
.xbox:before{left:-6px;top:-10px}.xbox:after{right:-6px;top:-10px}.xbox>.x1{left:-6px;bottom:-10px}.xbox>.x2{right:-6px;bottom:-10px}
.sbox .hd{display:flex;justify-content:space-between;font:500 .78rem "Barlow",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);padding-bottom:10px;border-bottom:1px solid var(--bd)}
.sbox a{display:grid;grid-template-columns:3rem 1fr auto;gap:10px;align-items:baseline;padding:9px 0;border-bottom:1px solid var(--bd);text-decoration:none}.sbox a:last-of-type{border:0}
.sbox a i{font:600 .78rem "Barlow",sans-serif;letter-spacing:.12em;color:var(--ac);font-style:normal;text-transform:uppercase}.sbox a b{font:600 1.15rem "Barlow Condensed",sans-serif}.sbox a span{font-size:.78rem;color:var(--mut)}
.sec{margin:78px 0 0}.sec .kicker{font-size:.8rem;margin-bottom:22px}
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px}
.lt{position:relative;display:flex;flex-direction:column;gap:18px;padding:20px 20px 16px;border:1px solid var(--bd);text-decoration:none;color:var(--fg)}
.lt:before,.lt:after{content:"+";position:absolute;top:-10px;font:300 19px/1 "Barlow",sans-serif;color:var(--mut);background:var(--bg)}.lt:before{left:-6px}.lt:after{right:-6px}
.lt .m{display:flex;justify-content:space-between;font:500 .78rem "Barlow",sans-serif;color:var(--mut)}.lt .m i{font-style:normal;font-weight:600;letter-spacing:.12em;color:var(--ac);text-transform:uppercase}
.lt b{font:600 1.9rem/1.1 "Barlow Condensed",sans-serif}.lt .go{font:600 .78rem "Barlow Condensed",sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--ac)}
.lt:hover{background:var(--ink);color:var(--onink)}.lt:hover .go,.lt:hover .m i{color:#9fc0ea}.lt.orig{border-style:dashed}
.stab{position:relative;border:1px solid var(--bd)}
.stab .th,.stab .tr{display:grid;grid-template-columns:3.4rem 1fr 1.4fr;gap:14px;padding:14px 20px;border-bottom:1px solid var(--bd);align-items:center}
.stab .th{font:500 .74rem "Barlow",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.stab .tr:last-child{border:0}
.stab .tr i{font:600 .8rem "Barlow",sans-serif;color:var(--ac);font-style:normal;letter-spacing:.1em}.stab .tr b{font:600 1.35rem "Barlow Condensed",sans-serif}.stab .tr span{color:var(--mut);font-size:.9rem}
.stab .cap{padding:14px 20px;border-bottom:1px solid var(--bd);font:600 .85rem "Barlow Condensed",sans-serif;letter-spacing:.1em;text-transform:uppercase}
@media(max-width:560px){.stab .th,.stab .tr{grid-template-columns:2.4rem 1fr}.stab .th span:last-child,.stab .tr span{grid-column:1/-1}}
.cta{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:20px;padding:38px 40px}.cta h2{margin:0 0 .3em;font-size:1.9rem}.cta p{margin:0;color:var(--mut);max-width:32em}
.faq details{border-top:1px solid var(--bd);border-bottom:0;padding:18px 0}.faq details:last-child{border-bottom:1px solid var(--bd)}
.faq summary{list-style:none;display:flex;justify-content:space-between;gap:14px;text-transform:uppercase;font-size:1.15rem}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"\00d7";color:var(--ac);font-weight:400}.faq details[open] summary:after{content:"\2212"}
.faq p{max-width:40em}
footer{margin-top:80px}
.cc .btn{background:transparent;color:var(--onink);border-color:var(--onink)}.cc .btn.main{background:var(--ac);color:#fff;border-color:var(--ac)}
.chip{background:transparent;color:var(--fg)}
"""

EN_NAMES = {"de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
            "id": "Indonesian", "ru": "Russian", "uk": "Ukrainian", "ar": "Arabic", "he": "Hebrew", "hi": "Hindi", "ja": "Japanese",
            "ko": "Korean", "ml": "Malayalam", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "en": "English"}


def section(n, label, inner, sid=""):
    return f'<section class="sec"{' id="'+sid+'"' if sid else ""}><div class="kicker">{n:02d} · {_e(label)}</div>{inner}</section>'


def hero_h1(text, accent=""):
    return f'<h1>{_e(text)}{f"<em>{_e(accent)}</em>" if accent else ""}</h1>'


def spec_box(title, count_label, rows):
    """rows: (code, native name, English name, href)"""
    r = "".join(f'<a href="{_e(h)}"><i>{_e(c)}</i><b>{_e(n)}</b><span>{_e(en)}</span></a>' for c, n, en, h in rows)
    return f'<div class="xbox sbox"><div class="hd"><span>{_e(title)}</span><span>{_e(count_label)}</span></div>{r}<span class="x1"></span><span class="x2"></span></div>'


def lang_tile(code, native, english, href, hreflang, action, orig=False):
    return (f'<a class="lt{" orig" if orig else ""}" href="{_e(href)}" hreflang="{_e(hreflang)}" lang="{_e(hreflang)}">'
            f'<span class="m"><i>{_e(code)}</i><span>{_e(english)}</span></span><b>{_e(native)}</b><span class="go">{_e(action)} →</span></a>')


def spec_table(caption, cols, rows):
    """rows: (no, step, detail)"""
    r = "".join(f'<div class="tr"><i>{_e(a)}</i><b>{_e(b)}</b><span>{_e(c)}</span></div>' for a, b, c in rows)
    return (f'<div class="xbox stab" style="padding:0"><div class="cap">{_e(caption)}</div>'
            f'<div class="th"><span>{_e(cols[0])}</span><span>{_e(cols[1])}</span><span>{_e(cols[2])}</span></div>{r}<span class="x1"></span><span class="x2"></span></div>')


def cta_box(title, text, btn_label, href):
    return (f'<div class="xbox cta"><div><h2>{_e(title)}</h2><p>{_e(text)}</p></div>'
            f'<a class="btn main" href="{_e(href)}">{_e(btn_label)}</a><span class="x1"></span><span class="x2"></span></div>')
