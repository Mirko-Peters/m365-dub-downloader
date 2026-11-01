"""Folgen-Cover im "Industry"-Design (dunkle Tafel, Raster, Eck-Kreuze, Barlow Condensed, Linien-Motiv, Stichwort-Chips).
Wird fuer die Seiten (art_svg) und die Teilen-Bilder (generate_og.py) benutzt. Spec stammt aus generate_covers.py (Claude),
ohne Spec wird aus Titel/Kategorie/Tags ein passendes Cover abgeleitet."""
import html, re

INK, FG, MUT, AC, LINE = "#1d2126", "#eef0f3", "#98a0ab", "#82a7d4", "#e9ecef"

# Linien-Motive auf 100x100 (Strich = Akzentfarbe)
MOTIFS = {
    "shield": '<path d="M50 8 L84 20 V48 C84 70 68 86 50 94 C32 86 16 70 16 48 V20 Z"/><path d="M34 50 L46 62 L68 38"/>',
    "lock": '<rect x="22" y="44" width="56" height="44" rx="4"/><path d="M34 44 V30 a16 16 0 0 1 32 0 V44"/><circle cx="50" cy="66" r="5"/><path d="M50 71 V78"/>',
    "key": '<circle cx="32" cy="50" r="18"/><circle cx="32" cy="50" r="5"/><path d="M50 50 H90 M76 50 V64 M64 50 V60"/>',
    "cloud": '<path d="M28 74 H72 a16 16 0 0 0 2-31.8 A22 22 0 0 0 31 40 A17 17 0 0 0 28 74 Z"/><path d="M50 58 V84 M40 68 L50 58 L60 68"/>',
    "database": '<ellipse cx="50" cy="22" rx="30" ry="10"/><path d="M20 22 V76 C20 82 33 88 50 88 S80 82 80 76 V22"/><path d="M20 49 C20 55 33 61 50 61 S80 55 80 49"/>',
    "chart": '<path d="M12 12 V88 H90"/><rect x="24" y="52" width="12" height="28"/><rect x="46" y="34" width="12" height="46"/><rect x="68" y="18" width="12" height="62"/>',
    "chat": '<path d="M12 18 H88 V66 H44 L26 84 V66 H12 Z"/><path d="M28 34 H72 M28 48 H58"/>',
    "bot": '<rect x="18" y="32" width="64" height="48" rx="8"/><path d="M50 32 V16"/><circle cx="50" cy="12" r="4"/><circle cx="36" cy="54" r="6"/><circle cx="64" cy="54" r="6"/><path d="M38 70 H62 M8 50 V62 M92 50 V62"/>',
    "gear": '<circle cx="50" cy="50" r="14"/><path d="M50 8 V22 M50 78 V92 M8 50 H22 M78 50 H92 M20 20 L30 30 M70 70 L80 80 M80 20 L70 30 M30 70 L20 80"/><circle cx="50" cy="50" r="30"/>',
    "mail": '<rect x="10" y="20" width="80" height="60" rx="4"/><path d="M12 24 L50 56 L88 24"/>',
    "folder": '<path d="M10 24 H38 L46 34 H90 V80 H10 Z"/><path d="M10 44 H90"/>',
    "network": '<circle cx="50" cy="20" r="9"/><circle cx="20" cy="76" r="9"/><circle cx="80" cy="76" r="9"/><path d="M45 28 L25 68 M55 28 L75 68 M29 76 H71"/>',
    "document": '<path d="M22 8 H60 L80 28 V92 H22 Z"/><path d="M60 8 V28 H80 M34 46 H68 M34 60 H68 M34 74 H56"/>',
    "calendar": '<rect x="12" y="20" width="76" height="68" rx="4"/><path d="M12 40 H88 M32 10 V28 M68 10 V28"/><rect x="26" y="52" width="12" height="10"/><rect x="44" y="52" width="12" height="10"/><rect x="62" y="52" width="12" height="10"/><rect x="26" y="68" width="12" height="10"/>',
    "device": '<rect x="10" y="18" width="80" height="52" rx="4"/><path d="M34 86 H66 M50 70 V86"/><path d="M24 34 H56 M24 46 H44"/>',
    "users": '<circle cx="36" cy="32" r="14"/><path d="M8 84 C8 62 22 54 36 54 S64 62 64 84"/><circle cx="70" cy="38" r="11"/><path d="M68 56 C82 56 92 64 92 84"/>',
    "search": '<circle cx="42" cy="42" r="28"/><path d="M62 62 L90 90"/><path d="M30 42 H54 M42 30 V54"/>',
    "bolt": '<path d="M56 6 L22 56 H46 L40 94 L78 40 H54 Z"/>',
}
CAT_MOTIF = {"agents": "bot", "copilot": "chat", "security": "shield", "platform": "gear", "azure": "cloud", "data": "chart", "workplace": "users"}
KEYWORD_MOTIF = [(r"mail|outlook|exchange", "mail"), (r"sharepoint|onedrive|file|datei|document", "folder"), (r"calendar|kalender|planner|schedul", "calendar"),
                 (r"key|schl|entra|identity|identit|conditional|pim|mfa", "key"), (r"lock|encrypt|purview|dlp|label", "lock"), (r"api|graph|network|integration|connector", "network"),
                 (r"search|suche|ediscovery|audit", "search"), (r"device|intune|windows|endpoint|rooms", "device"), (r"power bi|fabric|dataverse|sql|lakehouse|data", "database")]
RTL = {"ar", "he"}


def _e(s): return html.escape(s or "", quote=True)


def pick_motif(title, cats, tags, spec):
    m = (spec or {}).get("motif")
    if m in MOTIFS:
        return m
    blob = " ".join([title] + list(tags)).lower()
    for rx, mm in KEYWORD_MOTIF:
        if re.search(rx, blob):
            return mm
    for c in cats:
        if c in CAT_MOTIF:
            return CAT_MOTIF[c]
    return "bolt"


def headline_of(title, spec):
    h = ((spec or {}).get("headline") or "").strip()
    if h:
        return h
    t = re.sub(r"\s*\((KI|AI)[^)]*\)\s*$", "", title or "").strip()
    main = t.split(":")[0].strip() if ":" in t and len(t.split(":")[0].strip()) >= 12 else t
    return main


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def cover_svg(vid, lang, lang_label, title, cat_label, cats, tags, spec=None, uid=""):
    rtl = lang in RTL
    head = headline_of(title, spec).upper()
    n = len(head)
    size, width = (96, 17) if n <= 22 else (82, 20) if n <= 36 else (70, 24) if n <= 52 else (58, 29)
    lines = wrap(head, width)[:3]
    if len(wrap(head, width)) > 3:
        lines[-1] = lines[-1].rstrip(" ,.:;") + "…"
    motif = MOTIFS[pick_motif(title, cats, tags, spec)]
    kws = [k for k in ((spec or {}).get("keywords") or tags or [])][:3]
    kws = [k[:26] for k in kws]
    anchor, tx = ("end", 1136) if rtl else ("start", 64)
    ix = 64 if rtl else 868
    out = [f'<svg viewBox="0 0 1200 420" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">',
           f'<defs><pattern id="gr{uid}" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0 H0 V40" fill="none" stroke="{LINE}" stroke-opacity=".05"/></pattern>'
           f'<linearGradient id="gl{uid}" x1="0" x2="1"><stop offset="0" stop-color="{AC}" stop-opacity=".16"/><stop offset="1" stop-color="{AC}" stop-opacity="0"/></linearGradient></defs>',
           f'<rect width="1200" height="420" fill="{INK}"/><rect width="1200" height="420" fill="url(#gr{uid})"/>',
           f'<rect x="{0 if not rtl else 560}" y="0" width="640" height="420" fill="url(#gl{uid})" opacity="{0 if rtl else 1}"/>']
    # Eck-Kreuze
    for cx, cy in ((24, 24), (1176, 24), (24, 396), (1176, 396)):
        out.append(f'<path d="M{cx-7} {cy} H{cx+7} M{cx} {cy-7} V{cy+7}" stroke="{MUT}" stroke-width="1.5"/>')
    # Kicker + Linie
    kick = f"M365.FM · {lang_label}".upper()
    out.append(f'<text x="{tx}" y="74" text-anchor="{anchor}" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-size="22" font-weight="600" letter-spacing="4" fill="{AC}">{_e(kick)}</text>')
    kw = 24 + 13.5 * len(kick)
    lx1, lx2 = (tx - kw, 64) if rtl else (tx + kw, 800)
    out.append(f'<path d="M{lx1:.0f} 68 H{lx2}" stroke="{LINE}" stroke-opacity=".22"/>')
    # Headline
    y = 150 if len(lines) == 3 else 160 if len(lines) == 2 else 190
    for i, ln in enumerate(lines):
        out.append(f'<text x="{tx}" y="{y + i * (size + 4)}" text-anchor="{anchor}" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-size="{size}" font-weight="700" fill="{FG}">{_e(ln)}</text>')
    # Motiv
    out.append(f'<g transform="translate({ix} 96) scale(2.6)" fill="none" stroke="{AC}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{motif}</g>')
    # Fuss: Chips + Kategorie
    x = tx
    for k in kws:
        w = 26 + 10.4 * len(k)
        rx = x - w if rtl else x
        out.append(f'<rect x="{rx:.0f}" y="340" width="{w:.0f}" height="34" fill="none" stroke="{LINE}" stroke-opacity=".35"/>'
                   f'<text x="{rx + w / 2:.0f}" y="363" text-anchor="middle" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-size="19" font-weight="600" letter-spacing="1.5" fill="{FG}">{_e(k.upper())}</text>')
        x = x - w - 10 if rtl else x + w + 10
    if cat_label:
        out.append(f'<text x="{64 if rtl else 1136}" y="363" text-anchor="{"start" if rtl else "end"}" font-family="Barlow Condensed,Arial Narrow,sans-serif" font-size="19" font-weight="600" letter-spacing="3" fill="{MUT}">{_e(cat_label.upper())}</text>')
    out.append("</svg>")
    return "".join(out)
