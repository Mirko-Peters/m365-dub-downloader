-- Quotes als Objekte an Personen-Entitaeten (Mirko, 1.11.2026): ein Zitat gehoert immer zu genau einer Person (person_eid = Entitaet vom Typ person).
-- Quelle: quotes.json des Seitenbaus (tools/import_quotes.py aus imports/entities/quotes/, nur freigegebene, nur mit Personen-Entitaet); Cron importQuotesFromSite.
CREATE TABLE IF NOT EXISTS quote (
  id TEXT PRIMARY KEY,                         -- <episode_id>-<n>
  person_eid TEXT NOT NULL,
  text TEXT NOT NULL,
  lang TEXT NOT NULL,
  episode_id TEXT NOT NULL DEFAULT '',
  episode_slug TEXT NOT NULL DEFAULT '',
  time_s INTEGER,
  about TEXT NOT NULL DEFAULT '[]',            -- Entitaets-IDs der Themen
  src TEXT NOT NULL DEFAULT 'site',
  status TEXT NOT NULL DEFAULT 'live',         -- live | hidden
  created INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_quote_person ON quote(person_eid, lang);
CREATE INDEX IF NOT EXISTS idx_quote_episode ON quote(episode_id);
