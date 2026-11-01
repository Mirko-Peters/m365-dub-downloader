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
# Fallback-Schriften mit den Metriken von Barlow (upm 1000, Oberlaenge 1000, Unterlaenge 200, xAvg 513 / Condensed 417): waehrend die Webfont laedt,
# nimmt der Platzhaltertext dieselbe Breite und Zeilenhoehe ein - beim Austausch verschiebt sich nichts mehr (CLS). Je System eine Variante
# (Windows: Arial, Android: Roboto, Apple: Helvetica Neue); der Browser nimmt die erste, die vorhanden ist. Werte: size-adjust = xAvg(Barlow)/xAvg(Fallback),
# ascent/descent-override = Barlow-Werte / size-adjust (Arial 904/1854/434 @2048, Roboto 911/1900/500 @2048, Helvetica Neue 509/952/213 @1000).
FB = {"Arial": (904 / 2048, 1854 / 2048, 434 / 2048, 67 / 2048), "Roboto": (911 / 2048, 1900 / 2048, 500 / 2048, 0), "Helvetica Neue": (509 / 1000, 952 / 1000, 213 / 1000, 28 / 1000)}
def _fb(name, local, xavg):
    out = ""
    for i, (loc, (fx, fa, fd, fg)) in enumerate(FB.items()):
        sa = xavg / fx
        out += (f'@font-face{{font-family:"{name} FB{i}";src:local("{loc}");size-adjust:{sa * 100:.1f}%;ascent-override:{100 / sa:.1f}%;'
                f'descent-override:{20 / sa:.1f}%;line-gap-override:0%}}')
    return out
FONT_CSS += _fb("Barlow", "", 0.513) + _fb("Barlow Condensed", "", 0.417) + "\n"
BF = '"Barlow","Barlow FB0","Barlow FB1","Barlow FB2"'   # Schriftstapel mit metrisch passenden Fallbacks
CF = '"Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2"'
INDUSTRY = """
:root{--onac:#fff;--bg:#f3f3f2;--fg:#17191c;--mut:#5d6470;--ac:#3b6391;--card:#fff;--bd:#17191c24;--ink:#1a1d21;--onink:#eef0f3}
@media (prefers-color-scheme:dark){:root{--onac:#101214;--bg:#101214;--fg:#e9ecef;--mut:#98a0ab;--ac:#82a7d4;--card:#16191c;--bd:#e9ecef26;--ink:#1d2126;--onink:#eef0f3}}
:root[data-theme=dark]{--onac:#101214;--bg:#101214;--fg:#e9ecef;--mut:#98a0ab;--ac:#82a7d4;--card:#16191c;--bd:#e9ecef26;--ink:#1d2126;--onink:#eef0f3;color-scheme:dark}
body{font-family:"Barlow","Barlow FB0","Barlow FB1","Barlow FB2",-apple-system,"Segoe UI",Inter,Roboto,"Noto Sans",system-ui,sans-serif}
.serif,h1,h2,h3,h4,.brand,.tile b,.num,.row h3,.thumb h3,.faq summary,.cols h3,.stats b,.ifacts b,.info figcaption,.points li:before,.author .badge{font-family:"Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2","Arial Narrow","Noto Sans",system-ui,sans-serif}
h1,h2{text-transform:uppercase;font-weight:600;letter-spacing:.01em}
h1{font-size:clamp(2.1rem,6vw,4.4rem);line-height:1;letter-spacing:0}
article h1{font-size:clamp(1.8rem,4.2vw,3rem);line-height:1.05}
h2{font-size:1.7rem;letter-spacing:.02em}
.brand{text-transform:uppercase;letter-spacing:.04em;font-weight:700}.brand i{color:var(--ac)}
.top{border-bottom:1px solid var(--bd)}
nav.langs{font-family:"Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;font-weight:500;letter-spacing:.12em}nav.langs a[aria-current]{border-bottom:2px solid var(--ac)}
.kicker{display:flex;align-items:center;gap:14px;font-family:"Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;font-weight:600;letter-spacing:.16em;color:var(--ac)}.kicker:after{content:"";flex:1;height:1px;background:var(--bd)}
.row h3,.thumb h3,.faq summary,.cols h3{font-weight:600;font-size:1.4rem;line-height:1.15}
.btn{border-radius:0;font-family:"Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;font-weight:600;letter-spacing:.1em;padding:9px 18px;border-color:var(--fg)}
.btn.main{background:var(--ac);border-color:var(--ac);color:var(--onac)}.btn:hover{background:var(--ac);border-color:var(--ac);color:var(--onac)}
.panel,.cover,.yt,.info,.portrait,.author .badge,.author img.badge{border-radius:0}.panel iframe{border-radius:0}
.panel{background:var(--ink)}.band{background:var(--ink)}
.tile,.thumb{position:relative}
.tile{padding:28px 18px 18px;border:1px solid var(--bd);margin:-1px 0 0 -1px}.grid{border:0}
.tile:before,.tile:after{content:"+";position:absolute;top:-10px;font:300 19px/1 "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;color:var(--mut)}.tile:before{left:-5px}.tile:after{right:-5px}
.tile b{font-weight:600;font-size:1.7rem}.tile:hover,.tile:focus-visible{background:var(--ink);color:var(--onink)}.tile:hover .mut,.tile:focus-visible .mut{color:var(--onink);opacity:.85}
.stats{border-color:var(--bd)}.stats b{color:var(--ac);font-weight:600}.points,.list{border-top:1px solid var(--bd)}.points li:before{color:var(--ac);font-weight:600}
.author,.share,footer{border-color:var(--bd)}.author .badge{background:var(--ac);color:var(--onac)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 16px}
.chip{display:inline-block;padding:2px 10px;border:1px solid var(--bd);font:600 .8rem/1.7 "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.09em;text-transform:uppercase;text-decoration:none;color:var(--mut)}
.chip.cat{border-color:var(--ac);color:var(--ac)}.chip:hover{background:var(--ac);border-color:var(--ac);color:var(--onac)}
.ilink{text-decoration:underline;text-decoration-color:var(--ac);text-decoration-thickness:2px;text-underline-offset:3px}
.info{background:var(--card)}.isteps i{border-radius:0;background:var(--ac)}.icol{border-top-color:var(--ac)}.ifacts div{border-left-color:var(--ac)}

/* ---- Design-Modul: Komponenten nach "SEO-Design fuer dub.m365.fm" ---- */
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.brand{font-size:1.25rem}.brand i{font-style:normal}.brand .dub{color:var(--ac);margin-left:6px}
.hero{padding:54px 0 12px}.hero h1{font-size:clamp(2.6rem,8vw,5.4rem);line-height:.98;margin:0 0 .35em}.hero h1 em{font-style:normal;color:var(--ac);display:block}
.hero .lede{color:var(--mut);font-size:1.12rem;max-width:34em}
.xbox{position:relative;border:1px solid var(--bd);margin:34px 0;padding:18px 20px}
.xbox:before,.xbox:after,.xbox>.x1,.xbox>.x2{content:"+";position:absolute;font:300 19px/1 "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;color:var(--mut);background:var(--bg)}
.xbox:before{left:-6px;top:-10px}.xbox:after{right:-6px;top:-10px}.xbox>.x1{left:-6px;bottom:-10px}.xbox>.x2{right:-6px;bottom:-10px}
.sbox .hd{display:flex;justify-content:space-between;font:500 .78rem "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);padding-bottom:10px;border-bottom:1px solid var(--bd)}
.sbox a{display:grid;grid-template-columns:3rem 1fr auto;gap:10px;align-items:baseline;padding:9px 0;border-bottom:1px solid var(--bd);text-decoration:none}.sbox a:last-of-type{border:0}
.sbox a i{font:600 .78rem "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;letter-spacing:.12em;color:var(--ac);font-style:normal;text-transform:uppercase}.sbox a b{font:600 1.15rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif}.sbox a span{font-size:.78rem;color:var(--mut)}
.sec{margin:78px 0 0}.sec .kicker{font-size:.8rem;margin-bottom:22px}
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px}
.lt{position:relative;display:flex;flex-direction:column;gap:18px;padding:20px 20px 16px;border:1px solid var(--bd);text-decoration:none;color:var(--fg)}
.lt:before,.lt:after{content:"+";position:absolute;top:-10px;font:300 19px/1 "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;color:var(--mut);background:var(--bg)}.lt:before{left:-6px}.lt:after{right:-6px}
.lt .m{display:flex;justify-content:space-between;font:500 .78rem "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;color:var(--mut)}.lt .m i{font-style:normal;font-weight:600;letter-spacing:.12em;color:var(--ac);text-transform:uppercase}
.lt b{font:600 1.9rem/1.1 "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif}.lt .go{font:600 .78rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--ac)}
.lt:hover{background:var(--ink);color:var(--onink)}.lt:hover .go,.lt:hover .m i{color:#9fc0ea}.lt.orig{border-style:dashed}
.stab{position:relative;border:1px solid var(--bd)}
.stab .th,.stab .tr{display:grid;grid-template-columns:3.4rem 1fr 1.4fr;gap:14px;padding:14px 20px;border-bottom:1px solid var(--bd);align-items:center}
.stab .th{font:500 .74rem "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}.stab .tr:last-child{border:0}
.stab .tr i{font:600 .8rem "Barlow","Barlow FB0","Barlow FB1","Barlow FB2",sans-serif;color:var(--ac);font-style:normal;letter-spacing:.1em}.stab .tr b{font:600 1.35rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif}.stab .tr span{color:var(--mut);font-size:.9rem}
.stab .cap{padding:14px 20px;border-bottom:1px solid var(--bd);font:600 .85rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.1em;text-transform:uppercase}
@media(max-width:560px){.stab .th,.stab .tr{grid-template-columns:2.4rem 1fr}.stab .th span:last-child,.stab .tr span{grid-column:1/-1}}
.cta{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:20px;padding:38px 40px}.cta h2{margin:0 0 .3em;font-size:1.9rem}.cta p{margin:0;color:var(--mut);max-width:32em}
.faq details{border-top:1px solid var(--bd);border-bottom:0;padding:18px 0}.faq details:last-child{border-bottom:1px solid var(--bd)}
.faq summary{list-style:none;display:flex;justify-content:space-between;gap:14px;text-transform:uppercase;font-size:1.15rem}.faq summary::-webkit-details-marker{display:none}.faq summary:after{content:"×";color:var(--ac);font-weight:400}.faq details[open] summary:after{content:"−"}
.faq p{max-width:40em}
footer{margin-top:80px}
.cc .btn{background:transparent;color:var(--onink);border-color:var(--onink)}.cc .btn.main{background:var(--ac);color:var(--onac);border-color:var(--ac)}

/* ---- Kopfbereich: M365Con-Leiste, Menue, Sprachwahl mit Flaggen ---- */
:focus-visible{outline:3px solid var(--ac);outline-offset:2px}summary:focus-visible{outline-offset:0}
.skip{position:absolute;inset-inline-start:8px;top:-60px;z-index:100;background:var(--ac);color:var(--onac);padding:10px 16px;font-weight:700;text-decoration:none}.skip:focus{top:8px}.sh{display:contents}h2.kicker{font-size:.95rem;line-height:1.4;margin-top:0}.mbar{position:sticky;top:0;z-index:60;background:var(--ink);color:var(--onink);text-align:center;font:600 .82rem/1.3 "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.1em;text-transform:uppercase}
.mbar a{display:block;padding:9px 14px;color:inherit;text-decoration:none}.mbar a:hover{background:var(--ac);color:var(--onac)}.mbar a:hover b{color:inherit}.mbar b{color:#9fc0ea;font-weight:600}.mbar i{font-style:normal;margin-inline-start:8px;opacity:.85}
.top .wrap{display:flex;align-items:center;gap:22px;flex-wrap:nowrap}
.top .brand{white-space:nowrap}
.menu{display:flex;gap:22px;margin-inline-start:auto;align-items:center}
.menu a{font:500 .88rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;color:var(--fg);padding:4px 0;border-bottom:2px solid transparent}
.menu a:hover{border-color:var(--ac);color:var(--ac)}
.mg{position:relative}.mg summary{list-style:none;cursor:pointer;font:500 .88rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.12em;text-transform:uppercase;padding:4px 0;border-bottom:2px solid transparent;user-select:none}
.mg summary::-webkit-details-marker{display:none}.mg summary:after{content:" ▾";color:var(--mut)}.mg[open] summary,.mg summary:hover{border-color:var(--ac);color:var(--ac)}
.mg .pn{position:absolute;inset-inline-start:0;top:calc(100% + 8px);z-index:70;background:var(--bg);border:1px solid var(--fg);padding:6px;display:grid;min-width:200px;box-shadow:0 12px 34px #0003}
.mg .pn a{display:block;padding:8px 10px;border:0;font:500 1rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.03em;text-transform:none}.mg .pn a:hover{background:var(--ac);color:var(--onac)}
.mgl{display:block;padding:8px 10px 2px;font:600 .75rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.lsw{position:relative}.lsw summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid var(--bd);font:600 .85rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.1em;text-transform:uppercase;user-select:none}
.lsw summary::-webkit-details-marker{display:none}.lsw summary:after{content:"▾";font-size:.8em;color:var(--mut)}.lsw[open] summary,.lsw summary:hover{border-color:var(--ac)}
.fl{width:22px;height:16px;object-fit:cover;border:1px solid var(--bd);flex:none;display:inline-block;vertical-align:middle}
.lsw .pn{position:absolute;inset-inline-end:0;top:calc(100% + 6px);z-index:70;background:var(--bg);border:1px solid var(--fg);padding:6px;display:grid;grid-template-columns:repeat(2,minmax(150px,1fr));gap:0;box-shadow:0 12px 34px #0003;max-height:70vh;overflow:auto}
.lsw .pn a{display:flex;align-items:center;gap:10px;padding:8px 10px;text-decoration:none;color:var(--fg);font:500 1rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.03em}
.lsw .pn a:hover{background:var(--ac);color:var(--onac)}.lsw .pn a[aria-current]{background:var(--ink);color:var(--onink)}
.mm{display:none;position:relative}.mm summary{list-style:none;cursor:pointer;padding:6px 12px;border:1px solid var(--bd);font:600 1.1rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif}.mm summary::-webkit-details-marker{display:none}
.mm .pn{position:absolute;inset-inline-end:0;top:calc(100% + 6px);z-index:70;background:var(--bg);border:1px solid var(--fg);min-width:220px;display:grid;box-shadow:0 12px 34px #0003}
.mm .pn a{padding:12px 16px;text-decoration:none;color:var(--fg);font:500 1rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.1em;text-transform:uppercase;border-bottom:1px solid var(--bd)}.mm .pn a:last-child{border:0}
@media(max-width:860px){.menu{display:none}.mm{display:block;margin-inline-start:auto}.top .wrap{gap:10px}.lsw .pn{grid-template-columns:1fr;position:fixed;inset-inline:12px;top:auto;width:auto}.lsw .pn{top:96px}.lsw .pn,.mm .pn{max-height:calc(100vh - 112px);max-height:calc(100dvh - 112px);overflow-y:auto;overscroll-behavior:contain}}
.share{display:none}
.fshare{border-radius:0}
.ichecks{list-style:none;margin:0;padding:0;display:grid;gap:8px}.ichecks li{padding-inline-start:30px;position:relative}.ichecks li:before{content:"✓";position:absolute;inset-inline-start:0;top:-1px;width:22px;height:22px;background:var(--ac);color:var(--onac);text-align:center;font-weight:700;line-height:22px}

.quiz{margin:2.2em 0;padding:22px;background:var(--card);border:1px solid var(--bd);border-top:4px solid var(--ac)}.quiz h2{margin-top:0}
.qq{border:0;padding:0;margin:14px 0}.qq legend{padding:0;font-weight:700;font-size:1.12rem;line-height:1.35;margin-bottom:12px}.qq legend small{display:block;color:var(--mut);font-weight:500;font-size:.8rem;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px}
.qo{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;margin:8px 0;border:2px solid var(--bd);cursor:pointer;transition:border-color .2s,background .2s}.qo:hover{border-color:var(--ac)}.qo input{margin-top:.25em;accent-color:var(--ac);width:18px;height:18px;flex:none}
.qo:has(input:checked){border-color:var(--ac);background:color-mix(in srgb,var(--ac) 9%,transparent)}.qo:has(input:focus-visible){outline:3px solid var(--ac);outline-offset:2px}
.qo.ok{border-color:#2e7d32!important;background:color-mix(in srgb,#2e7d32 14%,transparent)!important}.qo.no{border-color:#c62828!important;background:color-mix(in srgb,#c62828 12%,transparent)!important}.qq:disabled .qo{cursor:default}
.qctl{margin-top:10px}.qfb{min-height:1.4em;margin:12px 0 0;font-weight:600}.qfb.ok:before{content:"✓ "}.qfb.no:before{content:"✗ "}
.qres{text-align:center;padding:14px 0;animation:qpop .5s ease both}.qscore{font:700 2.2rem/1.1 "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;color:var(--ac);margin:0 0 6px}.qres .btns{justify-content:center;margin-top:14px}
@keyframes qpop{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:none}}@media (prefers-reduced-motion:reduce){.qres{animation:none}}

.iflow{list-style:none;margin:0;padding:0;display:flex;gap:0;align-items:stretch;counter-reset:n}
.pn{flex:1 1 0;position:relative;padding:14px 12px;border:2px solid color-mix(in srgb,var(--ac) 30%,transparent);background:var(--card);margin-inline-end:34px;cursor:pointer;display:flex;flex-direction:column;gap:6px;min-width:0;transition:border-color .3s,background .3s,transform .3s}
.pn:last-child{margin-inline-end:0}.pn .pi{width:24px;height:24px;line-height:24px;text-align:center;background:color-mix(in srgb,var(--ac) 25%,transparent);color:var(--ac);font-weight:700;font-size:.85rem;transition:background .3s,color .3s}.pn b{font-size:1.02rem;line-height:1.2}.pn .pt{font-size:.85rem;opacity:.8;line-height:1.35}
.pn:after{content:"";position:absolute;inset-inline-start:100%;top:50%;width:34px;height:2px;background:repeating-linear-gradient(90deg,var(--ac) 0 6px,transparent 6px 10px);background-size:20px 2px;opacity:.35;animation:flowdash 1s linear infinite}.pn:last-child:after{display:none}
.pn.on{border-color:var(--ac)}.pn.on:after{opacity:1}.pn.on .pi{background:var(--ac);color:var(--onac)}.pn.cur{transform:translateY(-4px);background:color-mix(in srgb,var(--ac) 8%,var(--card))}
.pn.entscheidung{clip-path:none;border-style:dashed}.pn.start .pi,.pn.ende .pi{border-radius:50%}.pn.ende.on{background:color-mix(in srgb,var(--ac) 12%,var(--card))}
.iplay{margin-top:12px}.iplay .btn{padding:4px 14px;font-size:.85rem}
@keyframes flowdash{to{background-position:20px 0}}
@media (max-width:720px){.iflow{flex-direction:column}.pn{margin-inline-end:0;margin-bottom:30px}.pn:last-child{margin-bottom:0}.pn:after{inset-inline-start:50%;top:100%;width:2px;height:30px;background:repeating-linear-gradient(180deg,var(--ac) 0 6px,transparent 6px 10px);background-size:2px 20px;animation-name:flowdashv}@keyframes flowdashv{to{background-position:0 20px}}}
@media (prefers-reduced-motion:reduce){.pn:after{animation:none}}

.js .info.rv{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}.js .info.rv.in{opacity:1;transform:none}
.js .info.rv .pn,.js .info.rv .isteps li,.js .info.rv .icol,.js .info.rv .ifacts div,.js .info.rv .ichecks li{opacity:0;transform:translateX(-14px);transition:opacity .5s ease,transform .5s ease}
.js .info.rv.in .pn,.js .info.rv.in .isteps li,.js .info.rv.in .icol,.js .info.rv.in .ifacts div,.js .info.rv.in .ichecks li{opacity:1;transform:none}
.info.in li:nth-child(2),.info.in .icol:nth-child(2),.info.in .ifacts div:nth-child(2){transition-delay:.12s}.info.in li:nth-child(3),.info.in .ifacts div:nth-child(3){transition-delay:.24s}.info.in li:nth-child(4),.info.in .ifacts div:nth-child(4){transition-delay:.36s}.info.in li:nth-child(5),.info.in .ifacts div:nth-child(5){transition-delay:.48s}.info.in li:nth-child(n+6),.info.in .ifacts div:nth-child(n+6){transition-delay:.6s}
.isteps li{cursor:pointer;transition:background .25s,box-shadow .25s}.isteps li:hover{background:color-mix(in srgb,var(--ac) 7%,transparent)}.isteps li.on i{background:var(--ac);transform:scale(1.12)}.isteps li.cur{box-shadow:inset 3px 0 0 var(--ac)}.isteps li:focus-visible,.ichecks li:focus-visible{outline:2px solid var(--ac);outline-offset:2px}.isteps i{transition:transform .25s}
.ichecks li{cursor:pointer;user-select:none}.ichecks li button.ck{all:unset;display:block;width:100%;cursor:pointer;box-sizing:border-box}.ichecks li button.ck:focus-visible{outline:2px solid var(--ac);outline-offset:3px}.ichecks li:before{transition:background .25s,transform .25s}.ichecks li:not(.done):before{background:transparent;color:transparent;box-shadow:inset 0 0 0 2px var(--ac)}.ichecks li.done{opacity:.6;text-decoration:line-through}.ichecks li.done:before{transform:scale(1.1)}
.iprog{height:6px;background:color-mix(in srgb,var(--ac) 15%,transparent);margin-top:14px;position:relative}.iprog i{display:block;height:100%;width:0;background:var(--ac);transition:width .4s ease}.iprog:after{content:attr(data-t);position:absolute;inset-inline-end:0;top:10px;font-size:.78rem;opacity:.7}
.icol{transition:transform .25s,box-shadow .25s}.icol:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.08)}.ifacts div{transition:transform .25s}.ifacts div:hover{transform:translateY(-3px)}
@media (prefers-reduced-motion:reduce){.info *{transition:none!important}}
.sub{font:500 1.35rem/1.35 "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;color:var(--mut);letter-spacing:.02em;margin:-.3em 0 1em;max-width:34em}
.chip{background:transparent;color:var(--fg)}
button.btn{background:transparent;color:var(--fg);font-size:.88rem;cursor:pointer}button.btn:hover{background:var(--ac);border-color:var(--ac);color:var(--onac)}
.fshare{position:fixed;z-index:40;display:flex;gap:0;background:var(--bg);border:1px solid var(--bd);left:0;top:50%;transform:translateY(-50%);flex-direction:column;border-left:0}
.fshare b{font:600 .65rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);padding:8px 0 6px;text-align:center;writing-mode:horizontal-tb}
.fshare a,.fshare button{display:block;width:44px;height:44px;line-height:44px;text-align:center;border:0;border-top:1px solid var(--bd);background:transparent;color:var(--fg);font:600 .9rem "Barlow Condensed","Barlow Condensed FB0","Barlow Condensed FB1","Barlow Condensed FB2",sans-serif;letter-spacing:.04em;text-decoration:none;cursor:pointer;padding:0}
.fshare a:hover,.fshare button:hover{background:transparent;color:var(--bc,var(--ac))}
.fshare .ic,footer .ic{display:block;margin:auto;transition:color .15s}.fshare a,.fshare button{display:flex;align-items:center;justify-content:center;color:var(--mut)}.fshare a:hover .ic,.fshare button:hover .ic{color:var(--bc)}
footer a.soc{display:inline-flex;align-items:center;gap:6px;color:var(--mut)}footer a.soc .ic{width:18px;height:18px;margin:0;color:currentColor}footer a.soc:hover{color:var(--bc)}footer a.soc:hover .ic{color:var(--bc)}
@media(max-width:1180px){.fshare{top:auto;bottom:0;left:0;right:0;transform:none;flex-direction:row;border:0;border-top:1px solid var(--bd)}.fshare b{display:none}.fshare a,.fshare button{flex:1;width:auto;border-top:0;border-left:1px solid var(--bd)}body{padding-bottom:46px}}

"""

EN_NAMES = {"de": "German", "es": "Spanish", "fr": "French", "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
            "id": "Indonesian", "ru": "Russian", "uk": "Ukrainian", "ar": "Arabic", "he": "Hebrew", "ja": "Japanese",
            "ko": "Korean", "en": "English"}


def section(n, label, inner, sid=""):
    return f'<section class="sec"{' id="'+sid+'"' if sid else ""}><h2 class="kicker">{n:02d} · {_e(label)}</h2>{inner}</section>'


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


FLAG = {"de": "de", "es": "es", "fr": "fr", "it": "it", "pt": "br", "nl": "nl", "pl": "pl", "id": "id", "ru": "ru", "uk": "ua", "ar": "sa", "he": "il",
        "ja": "jp", "ko": "kr", "en": "gb"}


def flag(code, base, name=""):
    return f'<img class="fl" src="{base}/assets/flags/{FLAG.get(code, "gb")}.svg" width="22" height="16" alt="{_e(name)}" loading="lazy">'


EN_URL = ""


LANG_LBL = {"en": "Language", "de": "Sprache", "es": "Idioma", "fr": "Langue", "it": "Lingua", "pt": "Idioma", "nl": "Taal", "pl": "Język", "id": "Bahasa",
            "ru": "Язык", "uk": "Мова", "ar": "اللغة", "he": "שפה", "ja": "言語", "ko": "언어"}


def lang_dropdown(cur, items, base):
    """items: (code, native name, url, hreflang). Dropdown mit Flaggen."""
    if EN_URL and not any(x[0] == "en" for x in items):
        items = [("en", "English", EN_URL, "en")] + list(items)
    cur_i = next((x for x in items if x[0] == cur), None)
    label = (cur_i[0] if cur_i else cur).upper()
    links = "".join(f'<a href="{_e(u)}" hreflang="{_e(h)}" lang="{_e(h)}"{" aria-current=page" if c == cur else ""}>{flag(c, base, n)}{_e(n)}</a>' for c, n, u, h in items)
    nm = f'{LANG_LBL.get(cur, "Language")}: {cur_i[1] if cur_i else cur}'   # T10: zugaenglicher Name der Sprachwahl
    return f'<details class="lsw"><summary aria-label="{_e(nm)}">{flag(cur, base, cur_i[1] if cur_i else cur)}{_e(label)}</summary><div class="pn">{links}</div></details>'


def site_header(home, brand_href, menu, lang_html, bar_html=""):
    """menu: (label, href)"""
    def one(t, h, grp):
        if isinstance(h, (list, tuple)):
            sub = "".join(f'<a href="{_e(u)}">{_e(x)}</a>' for x, u in h)
            return f'<span class="mgl">{_e(t)}</span>{sub}' if grp else f'<details class="mg"><summary>{_e(t)}</summary><div class="pn">{sub}</div></details>'
        return f'<a href="{_e(h)}">{_e(t)}</a>'
    m = "".join(one(t, h, False) for t, h in menu); mm = "".join(one(t, h, True) for t, h in menu)
    return (f'<header class="sh">{bar_html}<div class="top"><div class="wrap"><a class="brand" href="{_e(brand_href)}">M365<i>.</i>FM <span class="dub">DUB</span></a>'
            f'<nav class="menu" aria-label="Menu">{m}</nav>{lang_html}<details class="mm"><summary aria-label="Menu">☰</summary><div class="pn">{mm}</div></details></div></div></header>')


