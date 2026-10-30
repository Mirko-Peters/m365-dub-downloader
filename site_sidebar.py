"""Sidebar fuer die Show-Seiten (/show/…): M365Con-Karte mit Countdown, Google-Quelle, Entitaeten-Chips (Wissensgraph), neueste Folgen, Hoeren/Folgen, Community."""
import json, re
from html import escape as esc
from pathlib import Path
D = Path(__file__).parent / "data"
TYPE_L = {"product": "Product", "concept": "Concept", "cert": "Certification", "platform": "Platform", "org": "Organization", "event": "Event", "person": "Person", "media": "Media", "category": "Topic"}
STOP = {"access", "project", "compliance", "governance", "automation", "prompt", "actions", "polling", "agent", "agents", "lists", "forms", "flow", "loop", "word", "bing", "stream", "sites", "pages", "tasks", "security", "identity", "copilot", "microsoft", "azure", "m365", "teams"}
TYPE_PRIO = {"product": 0, "person": 1, "cert": 2, "platform": 3, "concept": 4, "event": 5, "org": 6, "media": 7, "category": 9}
GSRC = "https://www.google.com/preferences/source?q=m365.fm"
CON = "https://m365con.net/?utm_source=m365.fm&utm_medium=sidebar&utm_campaign=attending2027"


class Index:
    def __init__(self):
        ents = json.loads((D / "entities.json").read_text("utf-8"))
        gp = D / "guest_entities.json"
        if gp.exists(): ents += json.loads(gp.read_text("utf-8"))
        self.by = {}; names = {}
        for e in ents:
            if e["type"] in ("category",) or e["id"] == "mirko-peters": continue
            for n in [e["name"]] + list(e.get("aliases") or []):
                n = (n or "").strip()
                if " " not in n and n.lower() in STOP and n.lower() != e["name"].lower(): continue
                if len(n) < (6 if e.get("guest") else 4) and n not in ("Teams", "Excel", "Word", "Azure", "Loop", "Viva", "Bing"): continue
                names.setdefault(n.lower(), e["id"])
            self.by[e["id"]] = e
        keys = sorted(names, key=len, reverse=True)
        self.names = names
        self.rx = re.compile(r"(?<![\w-])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w-])", re.I) if keys else None

    def match(self, text, k=8):
        if not self.rx: return []
        cnt = {}
        for m in self.rx.finditer(text):
            i = self.names.get(m.group(1).lower()); cnt[i] = cnt.get(i, 0) + 1
        ids = sorted(cnt, key=lambda i: (self.by[i]["name"].lower() in STOP, -min(cnt[i], 3), TYPE_PRIO.get(self.by[i]["type"], 8), -cnt[i]))
        return [self.by[i] for i in ids[:k]]


def render(ix, BASE, root, text, latest, shp, esc_=esc, nav=""):
    chips = "".join(f'<li><a class="sb-chip t-{esc(e["type"])}" href="{BASE}/entity/{esc(e["id"])}/" title="{esc(TYPE_L.get(e["type"], ""))}"><i></i>{esc(e["name"])}</a></li>' for e in ix.match(text))
    ents = f'<section class="sb-card"><h2>Topics &amp; people on this page</h2><ul class="sb-chips">{chips}</ul><a class="sb-more" href="{BASE}/glossary/">Explore the knowledge graph →</a></section>' if chips else ""
    late = "".join(f'<li><a href="{root}episodes/{esc(e["slug"])}/">{esc(e["name"])}</a></li>' for e in latest[:5])
    listen = " ".join(f'<a href="{esc(shp[k])}" rel="noopener">{n}</a>' for k, n in (("apple_show", "Apple Podcasts"), ("spotify_show", "Spotify"), ("amazon_show", "Amazon Music"), ("deezer_show", "Deezer"), ("iheart_show", "iHeart")) if shp.get(k))
    con = (f'<section class="sb-card sb-con"><a href="{CON}" rel="noopener" aria-label="M365Con International 2027 – I\'m attending"><img src="{BASE}/assets/attending-m365con.webp" alt="I\'m attending M365Con International 2027, January 11–22, 2027, free online event" width="675" height="563" loading="lazy"></a>'
           f'<a class="sb-btn" href="{CON}" rel="noopener">Save your free seat →</a></section>')
    goog = (f'<section class="sb-card sb-g"><a class="gb" href="{GSRC}" rel="noopener" target="_blank"><img src="{BASE}/assets/gsource.webp" alt="Add M365.fm as a preferred source on Google" width="647" height="192" loading="lazy"></a>'
            f'<p>See <b>M365.FM</b> first in Google&nbsp;Top&nbsp;Stories.</p></section>')
    new = f'<section class="sb-card"><h2>Latest episodes</h2><ol class="sb-list">{late}</ol><a class="sb-more" href="{root}episodes/">All episodes →</a></section>' if late else ""
    foll = (f'<section class="sb-card"><h2>Listen &amp; follow</h2><p class="sb-links">{listen}</p><p class="sb-links"><a href="{root}listen/">All platforms</a> <a href="https://www.spreaker.com/show/6704921/episodes/feed" rel="noopener">RSS</a></p></section>') if listen else ""
    comm = (f'<section class="sb-card sb-comm"><h2>Join the community</h2><p>Free profile, expert directory, events and your own page in the knowledge graph.</p><a class="sb-btn sb-ghost" href="{BASE}/community/">Create your profile →</a></section>')
    return f'<aside class="sbar" aria-label="Sidebar"><div class="sbar-in">{nav}{con}{goog}{ents}{new}{foll}{comm}</div></aside>'


# ---- Sidebar fuer die Sprachseiten (alle Sprachen ausser den englischen Show-Seiten) ----
L10N = {
    "en": dict(topics="Topics & people on this page", kg="Explore the knowledge graph →", latest="Latest episodes", all="All episodes →", join="Join the community", joint="Free profile, expert directory, events and your own page in the knowledge graph.", create="Create your profile →", seat="Save your free seat →", google="See <b>M365.FM</b> first in Google&nbsp;Top&nbsp;Stories."),
    "de": dict(topics="Themen & Personen auf dieser Seite", kg="Wissensgraph entdecken →", latest="Neueste Folgen", all="Alle Folgen →", join="Werde Teil der Community", joint="Kostenloses Profil, Expertenverzeichnis, Events und deine eigene Seite im Wissensgraphen.", create="Profil anlegen →", seat="Sichere dir deinen kostenlosen Platz →", google="Sieh <b>M365.FM</b> zuerst in Google&nbsp;Top&nbsp;Stories."),
    "es": dict(topics="Temas y personas de esta página", kg="Explora el grafo de conocimiento →", latest="Últimos episodios", all="Todos los episodios →", join="Únete a la comunidad", joint="Perfil gratuito, directorio de expertos, eventos y tu propia página en el grafo de conocimiento.", create="Crea tu perfil →", seat="Reserva tu plaza gratis →", google="Ve <b>M365.FM</b> primero en Google&nbsp;Top&nbsp;Stories."),
    "fr": dict(topics="Sujets et personnes de cette page", kg="Explorer le graphe de connaissances →", latest="Derniers épisodes", all="Tous les épisodes →", join="Rejoignez la communauté", joint="Profil gratuit, annuaire d'experts, événements et votre propre page dans le graphe de connaissances.", create="Créer votre profil →", seat="Réservez votre place gratuite →", google="Voyez <b>M365.FM</b> en premier dans Google&nbsp;Top&nbsp;Stories."),
    "it": dict(topics="Argomenti e persone di questa pagina", kg="Esplora il grafo della conoscenza →", latest="Ultimi episodi", all="Tutti gli episodi →", join="Unisciti alla community", joint="Profilo gratuito, elenco di esperti, eventi e la tua pagina nel grafo della conoscenza.", create="Crea il tuo profilo →", seat="Riserva il tuo posto gratuito →", google="Vedi <b>M365.FM</b> per primo in Google&nbsp;Top&nbsp;Stories."),
    "pt": dict(topics="Tópicos e pessoas desta página", kg="Explore o grafo de conhecimento →", latest="Últimos episódios", all="Todos os episódios →", join="Junte-se à comunidade", joint="Perfil gratuito, diretório de especialistas, eventos e a sua própria página no grafo de conhecimento.", create="Crie o seu perfil →", seat="Reserve a sua vaga gratuita →", google="Veja a <b>M365.FM</b> primeiro no Google&nbsp;Top&nbsp;Stories."),
    "nl": dict(topics="Onderwerpen en personen op deze pagina", kg="Verken de kennisgraaf →", latest="Nieuwste afleveringen", all="Alle afleveringen →", join="Word lid van de community", joint="Gratis profiel, expertgids, evenementen en je eigen pagina in de kennisgraaf.", create="Maak je profiel →", seat="Reserveer je gratis plek →", google="Zie <b>M365.FM</b> als eerste in Google&nbsp;Top&nbsp;Stories."),
    "pl": dict(topics="Tematy i osoby na tej stronie", kg="Poznaj graf wiedzy →", latest="Najnowsze odcinki", all="Wszystkie odcinki →", join="Dołącz do społeczności", joint="Bezpłatny profil, katalog ekspertów, wydarzenia i własna strona w grafie wiedzy.", create="Utwórz profil →", seat="Zarezerwuj bezpłatne miejsce →", google="Zobacz <b>M365.FM</b> jako pierwsze w Google&nbsp;Top&nbsp;Stories."),
    "id": dict(topics="Topik dan tokoh di halaman ini", kg="Jelajahi grafik pengetahuan →", latest="Episode terbaru", all="Semua episode →", join="Bergabung dengan komunitas", joint="Profil gratis, direktori pakar, acara, dan halaman Anda sendiri di grafik pengetahuan.", create="Buat profil Anda →", seat="Amankan kursi gratis Anda →", google="Lihat <b>M365.FM</b> lebih dulu di Google&nbsp;Top&nbsp;Stories."),
    "ru": dict(topics="Темы и люди на этой странице", kg="Изучите граф знаний →", latest="Последние выпуски", all="Все выпуски →", join="Присоединяйтесь к сообществу", joint="Бесплатный профиль, каталог экспертов, события и собственная страница в графе знаний.", create="Создать профиль →", seat="Займите бесплатное место →", google="Видьте <b>M365.FM</b> первым в Google&nbsp;Top&nbsp;Stories."),
    "uk": dict(topics="Теми та люди на цій сторінці", kg="Досліджуйте граф знань →", latest="Останні випуски", all="Усі випуски →", join="Приєднуйтесь до спільноти", joint="Безкоштовний профіль, каталог експертів, події та власна сторінка в графі знань.", create="Створити профіль →", seat="Забронюйте безкоштовне місце →", google="Бачте <b>M365.FM</b> першим у Google&nbsp;Top&nbsp;Stories."),
    "ar": dict(topics="المواضيع والأشخاص في هذه الصفحة", kg="استكشف الرسم البياني للمعرفة ←", latest="أحدث الحلقات", all="كل الحلقات ←", join="انضم إلى المجتمع", joint="ملف شخصي مجاني ودليل خبراء وفعاليات وصفحتك الخاصة في الرسم البياني للمعرفة.", create="أنشئ ملفك الشخصي ←", seat="احجز مقعدك المجاني ←", google="شاهد <b>M365.FM</b> أولًا في Google&nbsp;Top&nbsp;Stories."),
    "he": dict(topics="נושאים ואנשים בעמוד זה", kg="גלו את גרף הידע ←", latest="הפרקים האחרונים", all="כל הפרקים ←", join="הצטרפו לקהילה", joint="פרופיל חינמי, מדריך מומחים, אירועים ועמוד משלכם בגרף הידע.", create="צרו את הפרופיל שלכם ←", seat="שמרו את מקומכם בחינם ←", google="ראו את <b>M365.FM</b> ראשון ב-Google&nbsp;Top&nbsp;Stories."),
    "hi": dict(topics="इस पेज के विषय और लोग", kg="ज्ञान ग्राफ़ देखें →", latest="नवीनतम एपिसोड", all="सभी एपिसोड →", join="समुदाय से जुड़ें", joint="मुफ़्त प्रोफ़ाइल, विशेषज्ञ निर्देशिका, इवेंट और ज्ञान ग्राफ़ में आपका अपना पेज।", create="अपनी प्रोफ़ाइल बनाएँ →", seat="अपनी मुफ़्त सीट सुरक्षित करें →", google="Google&nbsp;Top&nbsp;Stories में <b>M365.FM</b> को सबसे पहले देखें।"),
    "ja": dict(topics="このページのトピックと人物", kg="ナレッジグラフを探索 →", latest="最新エピソード", all="すべてのエピソード →", join="コミュニティに参加", joint="無料プロフィール、専門家ディレクトリ、イベント、ナレッジグラフ内のあなた自身のページ。", create="プロフィールを作成 →", seat="無料の席を確保 →", google="Google&nbsp;Top&nbsp;Stories で <b>M365.FM</b> を最初に表示。"),
    "ko": dict(topics="이 페이지의 주제와 인물", kg="지식 그래프 둘러보기 →", latest="최신 에피소드", all="모든 에피소드 →", join="커뮤니티 참여", joint="무료 프로필, 전문가 디렉터리, 이벤트, 지식 그래프 속 나만의 페이지.", create="프로필 만들기 →", seat="무료 좌석 예약 →", google="Google&nbsp;Top&nbsp;Stories에서 <b>M365.FM</b>을 가장 먼저 보세요."),
    "ml": dict(topics="ഈ പേജിലെ വിഷയങ്ങളും വ്യക്തികളും", kg="നോളജ് ഗ്രാഫ് കാണുക →", latest="ഏറ്റവും പുതിയ എപ്പിസോഡുകൾ", all="എല്ലാ എപ്പിസോഡുകളും →", join="കമ്മ്യൂണിറ്റിയിൽ ചേരൂ", joint="സൗജന്യ പ്രൊഫൈൽ, വിദഗ്ധ ഡയറക്ടറി, ഇവന്റുകൾ, നോളജ് ഗ്രാഫിൽ നിങ്ങളുടെ സ്വന്തം പേജ്.", create="പ്രൊഫൈൽ സൃഷ്ടിക്കൂ →", seat="സൗജന്യ സീറ്റ് ഉറപ്പാക്കൂ →", google="Google&nbsp;Top&nbsp;Stories-ൽ <b>M365.FM</b> ആദ്യം കാണൂ."),
    "pa": dict(topics="ਇਸ ਪੰਨੇ ਦੇ ਵਿਸ਼ੇ ਅਤੇ ਲੋਕ", kg="ਗਿਆਨ ਗ੍ਰਾਫ਼ ਵੇਖੋ →", latest="ਨਵੇਂ ਐਪੀਸੋਡ", all="ਸਾਰੇ ਐਪੀਸੋਡ →", join="ਕਮਿਊਨਿਟੀ ਨਾਲ ਜੁੜੋ", joint="ਮੁਫ਼ਤ ਪ੍ਰੋਫ਼ਾਈਲ, ਮਾਹਰ ਡਾਇਰੈਕਟਰੀ, ਇਵੈਂਟ ਅਤੇ ਗਿਆਨ ਗ੍ਰਾਫ਼ ਵਿੱਚ ਤੁਹਾਡਾ ਆਪਣਾ ਪੰਨਾ।", create="ਆਪਣੀ ਪ੍ਰੋਫ਼ਾਈਲ ਬਣਾਓ →", seat="ਆਪਣੀ ਮੁਫ਼ਤ ਸੀਟ ਰਾਖਵੀਂ ਕਰੋ →", google="Google&nbsp;Top&nbsp;Stories ਵਿੱਚ <b>M365.FM</b> ਨੂੰ ਸਭ ਤੋਂ ਪਹਿਲਾਂ ਵੇਖੋ।"),
    "ta": dict(topics="இந்தப் பக்கத்தின் தலைப்புகளும் நபர்களும்", kg="அறிவு வரைபடத்தை ஆராயுங்கள் →", latest="சமீபத்திய எபிசோடுகள்", all="அனைத்து எபிசோடுகள் →", join="சமூகத்தில் சேருங்கள்", joint="இலவச சுயவிவரம், நிபுணர் கோப்பகம், நிகழ்வுகள் மற்றும் அறிவு வரைபடத்தில் உங்கள் சொந்தப் பக்கம்.", create="சுயவிவரத்தை உருவாக்குங்கள் →", seat="இலவச இருக்கையை பதிவு செய்யுங்கள் →", google="Google&nbsp;Top&nbsp;Stories-இல் <b>M365.FM</b>-ஐ முதலில் காணுங்கள்."),
    "te": dict(topics="ఈ పేజీలోని అంశాలు మరియు వ్యక్తులు", kg="నాలెడ్జ్ గ్రాఫ్‌ను చూడండి →", latest="తాజా ఎపిసోడ్‌లు", all="అన్ని ఎపిసోడ్‌లు →", join="కమ్యూనిటీలో చేరండి", joint="ఉచిత ప్రొఫైల్, నిపుణుల డైరెక్టరీ, ఈవెంట్‌లు మరియు నాలెడ్జ్ గ్రాఫ్‌లో మీ సొంత పేజీ.", create="మీ ప్రొఫైల్‌ను సృష్టించండి →", seat="మీ ఉచిత సీటును రిజర్వ్ చేసుకోండి →", google="Google&nbsp;Top&nbsp;Stories‌లో <b>M365.FM</b>ని ముందుగా చూడండి."),
}


def render_lang(ix, BASE, lang, text, items, url_of, title_of, ent_prefix=""):
    """Sidebar fuer eine Sprachseite: M365Con-Karte, Google-Quelle, Themen/Personen der Seite, neueste Folgen der Sprache, Community. Texte in der Sprache der Seite."""
    t = L10N.get(lang) or L10N["en"]
    chips = "".join(f'<li><a class="sb-chip t-{esc(e["type"])}" href="{BASE}{ent_prefix}/entity/{esc(e["id"])}/" title="{esc(TYPE_L.get(e["type"], ""))}"><i></i>{esc(e["name"])}</a></li>' for e in ix.match(text))
    ents = f'<section class="sb-card"><h2>{esc(t["topics"])}</h2><ul class="sb-chips">{chips}</ul><a class="sb-more" href="{BASE}{ent_prefix}/entity/">{esc(t["kg"])}</a></section>' if chips else ""
    late = "".join(f'<li><a href="{esc(url_of(x))}">{esc(title_of(x))}</a></li>' for x in items[:5])
    new = f'<section class="sb-card"><h2>{esc(t["latest"])}</h2><ol class="sb-list">{late}</ol><a class="sb-more" href="{BASE}/{lang}/">{esc(t["all"])}</a></section>' if late else ""
    con = (f'<section class="sb-card sb-con"><a href="{CON}" rel="noopener" aria-label="M365Con International 2027"><img src="{BASE}/assets/attending-m365con.webp" alt="I\'m attending M365Con International 2027, January 11–22, 2027, free online event" width="675" height="563" loading="lazy"></a>'
           f'<a class="sb-btn" href="{CON}" rel="noopener">{esc(t["seat"])}</a></section>')
    goog = (f'<section class="sb-card sb-g"><a class="gb" href="{GSRC}" rel="noopener" target="_blank"><img src="{BASE}/assets/gsource.webp" alt="Add M365.fm as a preferred source on Google" width="647" height="192" loading="lazy"></a><p>{t["google"]}</p></section>')
    comm = f'<section class="sb-card sb-comm"><h2>{esc(t["join"])}</h2><p>{esc(t["joint"])}</p><a class="sb-btn sb-ghost" href="{BASE}/{lang}/community/">{esc(t["create"])}</a></section>'
    return f'<aside class="sbar" aria-label="Sidebar"><div class="sbar-in">{con}{goog}{ents}{new}{comm}</div></aside>'
