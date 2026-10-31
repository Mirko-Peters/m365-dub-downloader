"""Kategorien, Tags und interne Verlinkung für die Website (sprachbezogen)."""
import re
from urllib.parse import quote

CATS = [
    ("agents", r"copilot studio|ai agent|agentic|ki-agent|agent flow|teams toolkit|scout|agent mode"),
    ("copilot", r"microsoft 365 copilot|microsoft copilot|copilot roi|copilot adoption|copilot readiness|gpt-5|prompt|copilot cowork"),
    ("security", r"governance|purview|compliance|security|defender|dlp|eu ai act|prompt injection|entra|identity|identit|private link|permission|active directory|responsible ai"),
    ("platform", r"power platform|power automate|power pages|dynamics|dataverse|business central|power apps"),
    ("azure", r"azure|github|graph|api |api-|webhook|\.net|powershell|devops|developer|rag"),
    ("data", r"fabric|data activator|power bi|dataflow|real-time|echtzeit"),
    ("workplace", r"microsoft teams|viva|designer|outlook|word|excel|powerpoint|productivity|sharepoint"),
]
_N = {
    "agents": {"en": "AI Agents & Copilot Studio", "de": "KI-Agenten & Copilot Studio", "es": "Agentes de IA y Copilot Studio", "fr": "Agents IA et Copilot Studio",
               "it": "Agenti AI e Copilot Studio", "pt": "Agentes de IA e Copilot Studio", "nl": "AI-agents & Copilot Studio", "pl": "Agenci AI i Copilot Studio",
               "id": "Agen AI & Copilot Studio", "ru": "ИИ-агенты и Copilot Studio", "uk": "ШІ-агенти та Copilot Studio", "ar": "وكلاء الذكاء الاصطناعي وCopilot Studio",
               "he": "סוכני AI ו-Copilot Studio", "ja": "AIエージェントとCopilot Studio", "ko": "AI 에이전트와 Copilot Studio"
               },
    "copilot": {"en": "Microsoft 365 Copilot"},
    "security": {"en": "Security, Identity & Governance", "de": "Sicherheit, Identität & Governance", "es": "Seguridad, identidad y gobernanza", "fr": "Sécurité, identité et gouvernance",
                 "it": "Sicurezza, identità e governance", "pt": "Segurança, identidade e governança", "nl": "Beveiliging, identiteit & governance", "pl": "Bezpieczeństwo, tożsamość i governance",
                 "id": "Keamanan, identitas & tata kelola", "ru": "Безопасность, идентичность и governance", "uk": "Безпека, ідентичність і governance", "ar": "الأمان والهوية والحوكمة",
                 "he": "אבטחה, זהות וממשל", "ja": "セキュリティ・ID・ガバナンス", "ko": "보안, ID 및 거버넌스"
                 },
    "platform": {"en": "Power Platform & Dynamics 365"},
    "azure": {"en": "Azure & Developer", "de": "Azure & Entwicklung", "es": "Azure y desarrollo", "fr": "Azure et développement", "it": "Azure e sviluppo", "pt": "Azure e desenvolvimento",
              "nl": "Azure & ontwikkeling", "pl": "Azure i programowanie", "id": "Azure & pengembangan", "ru": "Azure и разработка", "uk": "Azure і розробка", "ar": "Azure والتطوير",
              "he": "Azure ופיתוח", "ja": "Azureと開発", "ko": "Azure 및 개발", },
    "data": {"en": "Data & Fabric", "de": "Daten & Fabric", "es": "Datos y Fabric", "fr": "Données et Fabric", "it": "Dati e Fabric", "pt": "Dados e Fabric", "nl": "Data & Fabric",
             "pl": "Dane i Fabric", "id": "Data & Fabric", "ru": "Данные и Fabric", "uk": "Дані та Fabric", "ar": "البيانات وFabric", "he": "נתונים ו-Fabric", "ja": "データとFabric", "ko": "데이터와 Fabric", },
    "workplace": {"en": "Teams & Productivity", "de": "Teams & Produktivität", "es": "Teams y productividad", "fr": "Teams et productivité", "it": "Teams e produttività",
                  "pt": "Teams e produtividade", "nl": "Teams & productiviteit", "pl": "Teams i produktywność", "id": "Teams & produktivitas", "ru": "Teams и продуктивность",
                  "uk": "Teams і продуктивність", "ar": "Teams والإنتاجية", "he": "Teams ופרודוקטיביות", "ja": "Teamsと生産性", "ko": "Teams 및 생산성"
                  }
}
TOPICS = {"de": "Themen", "es": "Temas", "fr": "Thèmes", "it": "Argomenti", "pt": "Tópicos", "nl": "Onderwerpen", "pl": "Tematy", "id": "Topik", "ru": "Темы", "uk": "Теми",
          "ar": "المواضيع", "he": "נושאים", "ja": "トピック", "ko": "주제", "en": "Topics"}
TAGW = {"de": "Schlagwort", "es": "Etiqueta", "fr": "Mot-clé", "it": "Tag", "pt": "Tag", "nl": "Tag", "pl": "Tag", "id": "Tag", "ru": "Тег", "uk": "Тег", "ar": "وسم", "he": "תג",
        "ja": "タグ", "ko": "태그", "en": "Tag"}
ORDER = [c for c, _ in CATS]


def cat_name(slug, lang):
    d = _N[slug]
    return d.get(lang) or d["en"]


def classify(texts):
    t = " ".join(texts).lower()
    hits = [c for c, rx in CATS if re.search(rx, t)]
    return hits or ["copilot"]


def tags_of(e):
    out, seen = [], set()
    for t in re.split(r"[,;、，]", e.get("tags") or ""):
        t = t.strip()
        k = t.lower()
        if t and k not in seen and "m365.fm" not in k and len(t) >= 2:
            seen.add(k)
            out.append(t)
    return out[:10]


def tag_slug(t):
    return re.sub(r"[^\w]+", "-", t.lower().strip(), flags=re.U).strip("-")


def tag_url(base, lang, t):
    return f"{base}/{lang}/tag/{quote(tag_slug(t))}/"


def related(it, pool, tagsets, catset, n=6):
    """Verwandte Folgen derselben Sprache: gemeinsame Tags (x2) + gemeinsame Kategorien, sonst neueste."""
    mine = tagsets[it["vid"]]
    scored = []
    for o in pool:
        if o["vid"] == it["vid"]:
            continue
        s = 2 * len(mine & tagsets[o["vid"]]) + len(catset[it["vid"]] & catset[o["vid"]])
        scored.append((s, o["date"], o))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [o for _, _, o in scored[:n]]


def autolink(html, it, pool, tagsets_raw, url_of, max_links=10, money=None):
    """Verlinkt im Artikel erstmalige Nennungen spezifischer Tags anderer Folgen (gleiche Sprache) auf diese Folgen.
    Nur Absätze/Listenpunkte, nie Überschriften oder bestehende Links. Rückgabe: (html, [(phrase, url)])."""
    df = {}
    for o in pool:
        for t in tagsets_raw[o["vid"]]:
            df.setdefault(t.lower(), set()).add(o["vid"])
    cands = []
    for o in pool:
        if o["vid"] == it["vid"]:
            continue
        for t in tagsets_raw[o["vid"]]:
            k = t.lower()
            if (len(t) >= 8 or " " in t) and len(df[k]) <= 2 and k not in tagsets_lower(tagsets_raw[it["vid"]]):
                cands.append((t, o))
    cands.sort(key=lambda c: -len(c[0]))
    byvid = {o["vid"]: o for o in pool}
    mcands = sorted(((p, byvid[v]) for p, v in (money or {}).items() if v in byvid and v != it["vid"]), key=lambda c: -len(c[0]))
    cands = mcands + [c for c in cands if c[0].lower() not in {p.lower() for p, _ in mcands}]
    used, links = set(), []

    def boundary(p):
        a = p[0].isascii() and p[0].isalnum()
        b = p[-1].isascii() and p[-1].isalnum()
        return a, b

    def do_block(m):
        nonlocal used, links
        block = m.group(0)
        if len(links) >= max_links:
            return block
        parts = re.split(r"(<[^>]+>)", block)
        for phrase, o in cands:
            if len(links) >= max_links:
                break
            if o["vid"] in used:
                continue
            a, b = boundary(phrase)
            rx = re.compile(("(?<![\\w])" if a else "") + re.escape(phrase) + ("(?![\\w])" if b else ""), re.I)
            depth = 0
            for i, seg in enumerate(parts):
                if i % 2 == 1:
                    if re.match(r"<a[\s>]", seg, re.I):
                        depth += 1
                    elif seg.lower().startswith("</a"):
                        depth = max(0, depth - 1)
                    continue
                if depth == 0 and seg.strip():
                    mm = rx.search(seg)
                    if mm:
                        # Link als eigenes Tag-Segment einfuegen, damit spaetere Treffer nie in href/Linktext landen
                        parts[i:i + 1] = [seg[:mm.start()], f'<a class="ilink" href="{url_of(o)}">', mm.group(0), "</a>", seg[mm.end():]]
                        used.add(o["vid"])
                        links.append((phrase, url_of(o)))
                        break
        return "".join(parts)

    out = re.sub(r"<(p|li)>.*?</\1>", do_block, html, flags=re.S)
    return out, links


def tagsets_lower(lst):
    return {x.lower() for x in lst}
