-- Betrieb: Protokoll der Cron-Aufgaben, Audit-Protokoll der Verwaltung, Vormerkliste fuer Uebersetzungen (Paket 11)
CREATE TABLE IF NOT EXISTS cron_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  started INTEGER NOT NULL,
  finished INTEGER NOT NULL DEFAULT 0,
  ok INTEGER NOT NULL DEFAULT 0,
  info TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_cron_runs ON cron_runs(name, started);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL DEFAULT 0,
  action TEXT NOT NULL,
  target TEXT NOT NULL DEFAULT '',
  detail TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit(created);
CREATE TABLE IF NOT EXISTS tr_queue (
  kind TEXT NOT NULL,
  item_id TEXT NOT NULL,
  lang TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  requested_by INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  info TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (kind, item_id, lang)
);
CREATE INDEX IF NOT EXISTS idx_tr_queue_status ON tr_queue(status, created);
