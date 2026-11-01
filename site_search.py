"""T37 Seitensuche (Mirko, 1.11.: "die Seite hat gar keine Suche, die soll in jeder Sprache suchen, Facetten bieten").

1) Suchindex: nach dem Schreiben der Sitemaps liest build_index() jede indexierbare Seite (alle Sprachen, Quelle: die
   Sitemap-Liste des Seitenbaus) aus docs/ bzw. r2out/ und schreibt search/manifest.json + search/part-<n>.json nach
   r2out/ (Site-Worker liefert sie aus dem R2-Bucket). Format = Vertrag mit dem Worker (Issue #128, /api/search):
   {"id","url","lang","type","title","summary","keywords","entities","date","image"}.
2) Suchseite /search/ und /<lang>/search/ (noindex): Formular, Treffer, Facetten (Typ, Sprache, Thema, Jahr);
   die Abfrage macht assets/search.js gegen die Community-API (tippfehlertolerant, alle Sprachen)."""
import html as _h, json, re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import site_sitemaps as SMAP

PART = 2000
TYPES = ("episode", "dub_episode", "entity", "person", "glossary", "blog", "event", "show", "page")
_RX = {k: re.compile(v, re.I | re.S) for k, v in {
    "lang": r'<html[^>]*\blang="([a-z]{2})', "title": r"<title>(.*?)</title>", "ogt": r'<meta property="og:title" content="([^"]*)"',
    "desc": r'<meta name="description" content="([^"]*)"', "ogi": r'<meta property="og:image" content="([^"]*)"',
    "robots": r'<meta name="robots" content="([^"]*)"', "ld": r'<script type="application/ld\+json">(.*?)</script>',
    "ent": r'href="(?:https://www\.m365\.fm)?(?:/[a-z]{2})?/entity/([a-z0-9-]+)/"'}.items()}


def _txt(s, n):
    s = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from _walk(v)
    elif isinstance(o, list):
        for v in o: yield from _walk(v)


def _type(path, typ, ld_types):
    seg = [x for x in path.split("/") if x]
    if seg and len(seg[0]) == 2: seg = seg[1:]
    if typ == "show-episodes": return "episode"
    if typ == "episodes": return "dub_episode"
    if typ == "blog": return "blog"
    if typ == "events": return "event"
    if typ == "entity":
        if len(seg) < 2: return "page"
        return "person" if "Person" in ld_types else "entity"
    if typ == "community":
        if len(seg) >= 3 and seg[1] == "u": return "person"
        if seg[:1] == ["shows"] or (len(seg) >= 2 and seg[1] == "shows"): return "show"
        return "page"
    if seg[:1] in (["glossary"], ["learn"]) and len(seg) >= 2: return "glossary"
    if seg[:1] == ["shows"] and len(seg) >= 2: return "show"
    return "page"


def extract(url, html, lang_default, typ):
    """Ein Suchdokument aus einer gebauten Seite (None, wenn die Seite nicht in die Suche gehoert)."""
    g = lambda k: (_RX[k].search(html) or [None, ""])[1]
    if "noindex" in g("robots").lower(): return None
    path = urlsplit(url).path
    if re.search(r"/page/\d+/?$", path): return None   # Listen-Seite 2, 3 ...
    lds, types, date, kw = [], set(), "", []
    for raw in _RX["ld"].findall(html):
        try: lds.append(json.loads(raw))
        except Exception: continue
    for n in (x for j in lds for x in _walk(j)):
        t = n.get("@type"); types |= set(t if isinstance(t, list) else [t] if t else [])
        for k in ("datePublished", "uploadDate", "startDate", "dateCreated"):
            if not date and isinstance(n.get(k), str) and re.match(r"\d{4}-\d{2}-\d{2}", n[k]): date = n[k][:10]
        for k in ("alternateName", "keywords"):
            v = n.get(k); kw += v if isinstance(v, list) else [v] if isinstance(v, str) else []
    title = _txt(g("ogt") or re.sub(r"\s+[|–—]\s+M365\.FM.*$", "", _h.unescape(g("title"))), 160)
    if not title: return None
    own = path.rstrip("/").split("/")[-1]
    ents = [e for e, _ in Counter(x for x in _RX["ent"].findall(html) if x != own).most_common(10)]
    kw = ", ".join(dict.fromkeys(_txt(str(k), 120) for k in kw if k))
    img = g("ogi")
    return {"id": f"{g('lang') or lang_default}:{path}", "url": url, "lang": g("lang") or lang_default, "type": _type(path, typ, types),
            "title": title, "summary": _txt(g("desc"), 300), "keywords": kw[:500], "entities": ents,
            "date": date, "image": img if img.startswith("https://img.m365.fm/") else ""}


def build_index(sitemap, roots, write_r2, base, langs):
    """sitemap: [(url, lastmod, alts)], roots: [docs/, r2out/] -> Anzahl Dokumente; schreibt search/*.json nach r2out/."""
    docs, seen = [], set()
    for u, _lm, _alts in sitemap:
        if u in seen or not u.startswith(base): continue
        seen.add(u)
        lang, typ = SMAP.classify(urlsplit(u).path, langs)
        rel = urlsplit(u).path.lstrip("/")
        f = next((r / rel / "index.html" for r in roots if (r / rel / "index.html").is_file()), None) if not rel.endswith(".html") else None
        if not f: continue
        try: d = extract(u, f.read_text("utf-8", errors="replace"), lang, typ)
        except Exception: d = None
        if d: docs.append(d)
    docs.sort(key=lambda d: (d["lang"] != "en", d["lang"], d["type"], d["url"]))
    parts = [docs[i:i + PART] for i in range(0, len(docs), PART)]
    for n, p in enumerate(parts, 1):
        write_r2(f"search/part-{n}.json", json.dumps({"part": n, "docs": p}, ensure_ascii=False, separators=(",", ":")))
    import datetime as _dt
    write_r2("search/manifest.json", json.dumps({"generated": _dt.date.today().isoformat(), "parts": len(parts), "count": len(docs),
                                                 "types": dict(Counter(d["type"] for d in docs)), "langs": dict(Counter(d["lang"] for d in docs))}, ensure_ascii=False))
    return docs


# ---- Suchseite -------------------------------------------------------------------------------------------------------------------
UI = {   # Oberflaeche der Suchseite (15 Sprachen); Typ-Namen in derselben Reihenfolge wie TYPES
    "en": ("Search", "Search episodes, topics, people, glossary …", "Search", "{n} results", "No results. Try another spelling or fewer words.", "Type", "Language", "Topic", "Year", "All languages", "Load more", "Search is not available right now.", "Clear filters",
           ("Episode", "Dub episode", "Entity", "Person", "Glossary", "Blog", "Event", "Show", "Page")),
    "de": ("Suche", "Folgen, Themen, Personen, Glossar durchsuchen …", "Suchen", "{n} Treffer", "Keine Treffer. Andere Schreibweise oder weniger Wörter versuchen.", "Typ", "Sprache", "Thema", "Jahr", "Alle Sprachen", "Mehr laden", "Die Suche ist gerade nicht erreichbar.", "Filter zurücksetzen",
           ("Folge", "Dub-Folge", "Entität", "Person", "Glossar", "Blog", "Event", "Show", "Seite")),
    "fr": ("Recherche", "Rechercher épisodes, sujets, personnes, glossaire …", "Rechercher", "{n} résultats", "Aucun résultat. Essayez une autre orthographe ou moins de mots.", "Type", "Langue", "Sujet", "Année", "Toutes les langues", "Plus de résultats", "La recherche n'est pas disponible pour le moment.", "Effacer les filtres",
           ("Épisode", "Épisode doublé", "Entité", "Personne", "Glossaire", "Blog", "Événement", "Émission", "Page")),
    "es": ("Buscar", "Buscar episodios, temas, personas, glosario …", "Buscar", "{n} resultados", "Sin resultados. Prueba otra ortografía o menos palabras.", "Tipo", "Idioma", "Tema", "Año", "Todos los idiomas", "Cargar más", "La búsqueda no está disponible ahora.", "Quitar filtros",
           ("Episodio", "Episodio doblado", "Entidad", "Persona", "Glosario", "Blog", "Evento", "Programa", "Página")),
    "it": ("Cerca", "Cerca episodi, temi, persone, glossario …", "Cerca", "{n} risultati", "Nessun risultato. Prova un'altra grafia o meno parole.", "Tipo", "Lingua", "Tema", "Anno", "Tutte le lingue", "Carica altri", "La ricerca non è disponibile al momento.", "Rimuovi filtri",
           ("Episodio", "Episodio doppiato", "Entità", "Persona", "Glossario", "Blog", "Evento", "Show", "Pagina")),
    "nl": ("Zoeken", "Zoek afleveringen, onderwerpen, personen, woordenlijst …", "Zoeken", "{n} resultaten", "Geen resultaten. Probeer een andere spelling of minder woorden.", "Type", "Taal", "Onderwerp", "Jaar", "Alle talen", "Meer laden", "Zoeken is nu niet beschikbaar.", "Filters wissen",
           ("Aflevering", "Nagesynchroniseerde aflevering", "Entiteit", "Persoon", "Woordenlijst", "Blog", "Evenement", "Show", "Pagina")),
    "pt": ("Pesquisar", "Pesquisar episódios, temas, pessoas, glossário …", "Pesquisar", "{n} resultados", "Nenhum resultado. Tente outra grafia ou menos palavras.", "Tipo", "Idioma", "Tema", "Ano", "Todos os idiomas", "Carregar mais", "A pesquisa não está disponível agora.", "Limpar filtros",
           ("Episódio", "Episódio dublado", "Entidade", "Pessoa", "Glossário", "Blog", "Evento", "Programa", "Página")),
    "pl": ("Szukaj", "Szukaj odcinków, tematów, osób, słownika …", "Szukaj", "Wyniki: {n}", "Brak wyników. Spróbuj innej pisowni lub mniej słów.", "Typ", "Język", "Temat", "Rok", "Wszystkie języki", "Pokaż więcej", "Wyszukiwanie jest teraz niedostępne.", "Wyczyść filtry",
           ("Odcinek", "Odcinek z dubbingiem", "Encja", "Osoba", "Słownik", "Blog", "Wydarzenie", "Program", "Strona")),
    "id": ("Cari", "Cari episode, topik, orang, glosarium …", "Cari", "{n} hasil", "Tidak ada hasil. Coba ejaan lain atau kata yang lebih sedikit.", "Jenis", "Bahasa", "Topik", "Tahun", "Semua bahasa", "Muat lagi", "Pencarian sedang tidak tersedia.", "Hapus filter",
           ("Episode", "Episode sulih suara", "Entitas", "Orang", "Glosarium", "Blog", "Acara", "Acara podcast", "Halaman")),
    "ru": ("Поиск", "Искать выпуски, темы, людей, глоссарий …", "Найти", "Результатов: {n}", "Ничего не найдено. Попробуйте другое написание или меньше слов.", "Тип", "Язык", "Тема", "Год", "Все языки", "Показать ещё", "Поиск сейчас недоступен.", "Сбросить фильтры",
           ("Выпуск", "Дублированный выпуск", "Сущность", "Человек", "Глоссарий", "Блог", "Событие", "Шоу", "Страница")),
    "uk": ("Пошук", "Шукати випуски, теми, людей, глосарій …", "Шукати", "Результатів: {n}", "Нічого не знайдено. Спробуйте інше написання або менше слів.", "Тип", "Мова", "Тема", "Рік", "Усі мови", "Показати ще", "Пошук зараз недоступний.", "Скинути фільтри",
           ("Випуск", "Дубльований випуск", "Сутність", "Особа", "Глосарій", "Блог", "Подія", "Шоу", "Сторінка")),
    "ar": ("بحث", "ابحث في الحلقات والموضوعات والأشخاص والمسرد …", "بحث", "{n} نتيجة", "لا توجد نتائج. جرّب تهجئة أخرى أو كلمات أقل.", "النوع", "اللغة", "الموضوع", "السنة", "كل اللغات", "تحميل المزيد", "البحث غير متاح الآن.", "مسح عوامل التصفية",
           ("حلقة", "حلقة مدبلجة", "كيان", "شخص", "مسرد", "مدونة", "فعالية", "برنامج", "صفحة")),
    "he": ("חיפוש", "חיפוש פרקים, נושאים, אנשים, מילון מונחים …", "חיפוש", "{n} תוצאות", "אין תוצאות. נסו כתיב אחר או פחות מילים.", "סוג", "שפה", "נושא", "שנה", "כל השפות", "טעינת עוד", "החיפוש אינו זמין כרגע.", "ניקוי מסננים",
           ("פרק", "פרק מדובב", "ישות", "אדם", "מילון מונחים", "בלוג", "אירוע", "תוכנית", "דף")),
    "ja": ("検索", "エピソード、トピック、人物、用語集を検索 …", "検索", "{n} 件", "結果がありません。別の綴りや少ない語で試してください。", "種類", "言語", "トピック", "年", "すべての言語", "さらに表示", "現在検索を利用できません。", "フィルターをクリア",
           ("エピソード", "吹き替えエピソード", "エンティティ", "人物", "用語集", "ブログ", "イベント", "番組", "ページ")),
    "ko": ("검색", "에피소드, 주제, 인물, 용어집 검색 …", "검색", "결과 {n}개", "결과가 없습니다. 다른 철자나 더 적은 단어로 시도해 보세요.", "유형", "언어", "주제", "연도", "모든 언어", "더 보기", "지금은 검색을 사용할 수 없습니다.", "필터 지우기",
           ("에피소드", "더빙 에피소드", "엔티티", "인물", "용어집", "블로그", "이벤트", "쇼", "페이지")),
}
CSS = (".srch-f{display:flex;gap:8px;margin:12px 0 18px}.srch-f input{flex:1;min-width:0;font:inherit;padding:10px 12px;border:1px solid var(--line,#ccd);border-radius:6px;background:var(--bg,#fff);color:inherit}"
       ".srch{display:grid;grid-template-columns:220px minmax(0,1fr);gap:24px}@media(max-width:760px){.srch{grid-template-columns:1fr}}"
       ".srch-fa h2{font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;margin:14px 0 6px;color:var(--mut,#667)}"
       ".srch-fa button{display:flex;justify-content:space-between;width:100%;gap:8px;border:0;background:none;color:inherit;font:inherit;text-align:start;padding:3px 0;cursor:pointer}"
       ".srch-fa button[aria-pressed=true]{font-weight:700;color:var(--ac,#2b4bee)}.srch-fa button span{color:var(--mut,#667);font-variant-numeric:tabular-nums}"
       ".srch-r ol{list-style:none;padding:0;margin:0}.srch-r li{padding:12px 0;border-bottom:1px solid var(--line,#e4e6ee)}.srch-r a{font-weight:600}"
       ".srch-r .m{font-size:.82rem;color:var(--mut,#667);margin:2px 0}.srch-r p{margin:4px 0 0}.srch-c{font-size:.9rem;color:var(--mut,#667)}")


def ui(lang):
    return UI.get(lang, UI["en"])


def page_body(lang, api, base, lang_names):
    t = ui(lang)
    data = {"api": api, "lang": lang, "count": t[3], "none": t[4], "err": t[11], "more": t[10], "clear": t[12], "all": t[9],
            "h": {"type": t[5], "lang": t[6], "entity": t[7], "year": t[8]}, "types": dict(zip(TYPES, t[13])), "langs": lang_names}
    return (f'<style>{CSS}</style><h1>{_h.escape(t[0])}</h1>'
            f'<form class="srch-f" role="search" method="get"><label class="sr-only" for="srch-q">{_h.escape(t[0])}</label>'
            f'<input id="srch-q" type="search" name="q" placeholder="{_h.escape(t[1])}" autocomplete="off" maxlength="100" autofocus>'
            f'<button class="btn main" type="submit">{_h.escape(t[2])}</button></form>'
            f'<div class="srch" id="srch" data-cfg="{_h.escape(json.dumps(data, ensure_ascii=False))}"><aside class="srch-fa" aria-label="Filter"></aside>'
            f'<div class="srch-r" aria-live="polite"></div></div>'
            f'<script defer src="{base}/assets/search.js"></script>')
