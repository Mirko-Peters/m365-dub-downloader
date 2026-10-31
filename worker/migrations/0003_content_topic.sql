-- Verknuepfung Inhalt <-> Entitaet mit Gewicht (Paket 13): eine Tabelle statt JSON-Spalten je Inhaltsart.
-- kind: blog | lblog (fruehere Beitraege, item_id = Slug) | show (Folgen der Hauptshow, item_id = Slug) | podcast | video | library | session
-- src: site (Seitenbau, gewichtete Zuordnung) | db (aus topics-Spalten uebernommen) | admin (von Hand in der Verwaltung)
CREATE TABLE IF NOT EXISTS content_topic (
  kind TEXT NOT NULL,
  item_id TEXT NOT NULL,
  eid TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1,
  src TEXT NOT NULL DEFAULT 'site',
  created INTEGER NOT NULL,
  PRIMARY KEY (kind, item_id, eid)
);
CREATE INDEX IF NOT EXISTS idx_content_topic_eid ON content_topic(eid, weight);
CREATE INDEX IF NOT EXISTS idx_content_topic_item ON content_topic(kind, item_id);
