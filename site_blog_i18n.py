"""Oberflaechentexte fuer die uebersetzten Blogseiten (/<lang>/show/blog/...): blog, alle Artikel, Folge anhoeren, KI-Hinweis, Original lesen, Artikel (Anzahl)."""
UI = {
    "de": ("Blog", "Alle Artikel", "Zur passenden Podcast-Folge:", "Dieser Artikel ist eine KI-gestützte Übersetzung des englischen Originals von Microsoft MVP Mirko Peters.", "Original lesen (Englisch)", "Artikel"),
    "fr": ("Blog", "Tous les articles", "Écouter l’épisode :", "Cet article est une traduction assistée par IA de l’original anglais de Mirko Peters, Microsoft MVP.", "Lire l’original (anglais)", "articles"),
    "es": ("Blog", "Todos los artículos", "Escucha el episodio:", "Este artículo es una traducción asistida por IA del original en inglés de Mirko Peters, Microsoft MVP.", "Leer el original (inglés)", "artículos"),
    "it": ("Blog", "Tutti gli articoli", "Ascolta l’episodio:", "Questo articolo è una traduzione assistita dall’IA dell’originale inglese di Mirko Peters, Microsoft MVP.", "Leggi l’originale (inglese)", "articoli"),
    "nl": ("Blog", "Alle artikelen", "Luister naar de aflevering:", "Dit artikel is een met AI vertaalde versie van het Engelse origineel van Microsoft MVP Mirko Peters.", "Lees het origineel (Engels)", "artikelen"),
    "pt": ("Blog", "Todos os artigos", "Ouça o episódio:", "Este artigo é uma tradução assistida por IA do original em inglês de Mirko Peters, Microsoft MVP.", "Ler o original (inglês)", "artigos"),
    "pl": ("Blog", "Wszystkie artykuły", "Posłuchaj odcinka:", "Ten artykuł to tłumaczenie wspomagane przez AI angielskiego oryginału autorstwa Mirko Petersa, Microsoft MVP.", "Przeczytaj oryginał (angielski)", "artykułów"),
    "id": ("Blog", "Semua artikel", "Dengarkan episodenya:", "Artikel ini adalah terjemahan berbantuan AI dari artikel asli berbahasa Inggris karya Mirko Peters, Microsoft MVP.", "Baca versi asli (Inggris)", "artikel"),
    "ru": ("Блог", "Все статьи", "Слушать выпуск:", "Эта статья — перевод с помощью ИИ английского оригинала Мирко Петерса, Microsoft MVP.", "Читать оригинал (английский)", "статей"),
    "uk": ("Блог", "Усі статті", "Слухати випуск:", "Ця стаття — переклад за допомогою ШІ англійського оригіналу Мірко Петерса, Microsoft MVP.", "Читати оригінал (англійською)", "статей"),
    "ar": ("المدونة", "جميع المقالات", "استمع إلى الحلقة:", "هذه المقالة ترجمة بمساعدة الذكاء الاصطناعي للنص الإنجليزي الأصلي بقلم ميركو بيترز، Microsoft MVP.", "اقرأ الأصل (بالإنجليزية)", "مقالة"),
    "he": ("בלוג", "כל המאמרים", "האזינו לפרק:", "מאמר זה הוא תרגום בסיוע בינה מלאכותית של המקור האנגלי מאת מירקו פטרס, Microsoft MVP.", "לקריאת המקור (אנגלית)", "מאמרים"),
    "ja": ("ブログ", "すべての記事", "エピソードを聴く：", "この記事は、Microsoft MVP の Mirko Peters による英語の原文を AI で翻訳したものです。", "原文を読む（英語）", "件の記事"),
    "ko": ("블로그", "모든 글", "에피소드 듣기:", "이 글은 Microsoft MVP Mirko Peters가 쓴 영어 원문을 AI로 번역한 것입니다.", "원문 읽기(영어)", "개의 글")
    }


def ui(lang):
    return UI.get(lang, ("Blog", "All articles", "Listen to the episode:", "", "Read the original (English)", "articles"))
