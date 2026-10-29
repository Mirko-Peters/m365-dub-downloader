-- D1-Schema fuer die Community-Funktionen (idempotent)
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  sub TEXT NOT NULL,
  name TEXT NOT NULL,
  bio TEXT NOT NULL DEFAULT '',
  lang TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL DEFAULT 'user',
  banned INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  UNIQUE(provider, sub)
);
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vid TEXT NOT NULL,
  lang TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  parent_id INTEGER,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ok',      -- ok | hidden
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comments_ep ON comments(vid, lang, status, created);
CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id, created);
CREATE TABLE IF NOT EXISTS likes (
  comment_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (comment_id, user_id)
);
CREATE TABLE IF NOT EXISTS reports (
  comment_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (comment_id, user_id)
);
CREATE TABLE IF NOT EXISTS user_badges (
  user_id INTEGER NOT NULL,
  badge TEXT NOT NULL,
  earned INTEGER NOT NULL,
  PRIMARY KEY (user_id, badge)
);
CREATE TABLE IF NOT EXISTS curators (          -- Kurator des Monats je Sprache
  lang TEXT NOT NULL,
  month TEXT NOT NULL,                         -- YYYY-MM
  user_id INTEGER NOT NULL,
  points INTEGER NOT NULL,
  PRIMARY KEY (lang, month)
);
CREATE TABLE IF NOT EXISTS push_subs (
  endpoint TEXT PRIMARY KEY,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  lang TEXT NOT NULL,
  user_id INTEGER,
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_push_lang ON push_subs(lang);
CREATE TABLE IF NOT EXISTS email_subs (
  email TEXT NOT NULL,
  lang TEXT NOT NULL,
  token TEXT NOT NULL,
  confirmed INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  PRIMARY KEY (email, lang)
);
CREATE INDEX IF NOT EXISTS idx_email_token ON email_subs(token);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ratelimit (k TEXT PRIMARY KEY, n INTEGER NOT NULL, win INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS wiki_rev (          -- Community-Wiki: Revisionen je Glossarbegriff und Sprache
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL,
  lang TEXT NOT NULL,
  body TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  user_id INTEGER NOT NULL,                    -- 0 = geloeschtes Konto
  status TEXT NOT NULL,                        -- live | pending | rejected | old
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wiki_term ON wiki_rev(term, lang, status, created);
CREATE TABLE IF NOT EXISTS wiki_reports (
  rev_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (rev_id, user_id)
);
