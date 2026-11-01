CREATE TABLE IF NOT EXISTS sponsor_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created INTEGER NOT NULL,
  company TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  message TEXT NOT NULL DEFAULT '',
  package TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'won', 'lost', 'spam')),
  ip_hash TEXT NOT NULL,
  lang TEXT NOT NULL DEFAULT 'de'
);
CREATE INDEX IF NOT EXISTS idx_sponsor_requests_created ON sponsor_requests(created DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_sponsor_requests_status ON sponsor_requests(status, created DESC, id DESC);
