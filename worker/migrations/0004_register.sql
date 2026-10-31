-- Folgen-Register der Hauptshow und das Uebersetzungsmodell ohne Dopplung (Paket 16/17).
-- episode: eine Zeile je Folge (Schluessel Slug, Spreaker-ID wenn bekannt); episode_text: lange Felder getrennt (Show Notes, Markup, Kernpunkte, FAQ, Transkript-Link);
-- translation: "ist Uebersetzung von" - je Inhalt, Sprache und Feld genau eine Zeile; Seiten entstehen aus Original plus Ueberlagerung.
CREATE TABLE IF NOT EXISTS episode (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  spreaker_id TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  published TEXT NOT NULL DEFAULT '',
  duration INTEGER NOT NULL DEFAULT 0,
  season TEXT NOT NULL DEFAULT '',
  number TEXT NOT NULL DEFAULT '',
  image TEXT NOT NULL DEFAULT '',
  audio TEXT NOT NULL DEFAULT '',
  youtube_id TEXT NOT NULL DEFAULT '',
  meta_title TEXT NOT NULL DEFAULT '',
  meta_description TEXT NOT NULL DEFAULT '',
  lang TEXT NOT NULL DEFAULT 'en',
  h TEXT NOT NULL DEFAULT '',
  updated INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_episode_spreaker ON episode(spreaker_id);
CREATE INDEX IF NOT EXISTS idx_episode_published ON episode(published);
CREATE TABLE IF NOT EXISTS episode_text (
  episode_id INTEGER NOT NULL,
  field TEXT NOT NULL,
  text TEXT NOT NULL DEFAULT '',
  h TEXT NOT NULL DEFAULT '',
  updated INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (episode_id, field)
);
CREATE TABLE IF NOT EXISTS episode_guest (
  episode_id INTEGER NOT NULL,
  eid TEXT NOT NULL,
  PRIMARY KEY (episode_id, eid)
);
CREATE TABLE IF NOT EXISTS translation (
  kind TEXT NOT NULL,
  item_id TEXT NOT NULL,
  lang TEXT NOT NULL,
  field TEXT NOT NULL,
  text TEXT NOT NULL DEFAULT '',
  src TEXT NOT NULL DEFAULT 'auto',
  quality TEXT NOT NULL DEFAULT '',
  h TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL,
  PRIMARY KEY (kind, item_id, lang, field)
);
CREATE INDEX IF NOT EXISTS idx_translation_item ON translation(kind, item_id);
CREATE INDEX IF NOT EXISTS idx_translation_lang ON translation(kind, lang);
