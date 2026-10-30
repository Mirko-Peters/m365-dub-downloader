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
CREATE TABLE IF NOT EXISTS entity_rev (        -- Entitaetsdatenbank: Community-Revisionen (Basisdaten liegen statisch in data/entities.json)
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  eid TEXT NOT NULL,
  data TEXT NOT NULL,                          -- JSON des ganzen Eintrags
  summary TEXT NOT NULL DEFAULT '',
  user_id INTEGER NOT NULL,                    -- 0 = geloeschtes Konto
  status TEXT NOT NULL,                        -- live | pending | rejected | old
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entity_rev ON entity_rev(eid, status, created);
CREATE TABLE IF NOT EXISTS profiles (          -- oeffentliche Experten-Profile (nur mit public=1 sichtbar)
  user_id INTEGER PRIMARY KEY,
  public INTEGER NOT NULL DEFAULT 0,
  handle TEXT UNIQUE,
  headline TEXT NOT NULL DEFAULT '',
  about TEXT NOT NULL DEFAULT '',              -- lange Bio (Klartext)
  company TEXT NOT NULL DEFAULT '',
  job TEXT NOT NULL DEFAULT '',
  country TEXT NOT NULL DEFAULT '',
  show_org INTEGER NOT NULL DEFAULT 1,         -- Firmenzugehoerigkeit oeffentlich zeigen
  updated INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS programs (          -- Microsoft-Programme: mvp | mct | rd | msa | ms_employee | partner
  owner_type TEXT NOT NULL,                    -- u (Person) | o (Firma)
  owner_id INTEGER NOT NULL,
  program TEXT NOT NULL,
  year INTEGER NOT NULL DEFAULT 0,
  url TEXT NOT NULL DEFAULT '',                -- Nachweis-Link
  verified INTEGER NOT NULL DEFAULT 0,         -- von Editor/Admin bestaetigt
  PRIMARY KEY (owner_type, owner_id, program)
);
CREATE TABLE IF NOT EXISTS expertise (
  owner_type TEXT NOT NULL,
  owner_id INTEGER NOT NULL,
  eid TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 2,            -- 1 lerne | 2 praktiziere | 3 Experte
  verified INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (owner_type, owner_id, eid)
);
CREATE INDEX IF NOT EXISTS idx_exp_eid ON expertise(eid);
CREATE TABLE IF NOT EXISTS certs (
  user_id INTEGER NOT NULL,
  eid TEXT NOT NULL,                           -- Entitaet vom Typ cert
  year INTEGER NOT NULL DEFAULT 0,
  url TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (user_id, eid)
);
CREATE TABLE IF NOT EXISTS channels (          -- Social-Media-Kanaele, optional mit Feed
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_type TEXT NOT NULL,
  owner_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  url TEXT NOT NULL,
  feed TEXT NOT NULL DEFAULT '',               -- RSS/Atom-URL (https)
  fetched INTEGER NOT NULL DEFAULT 0,
  fails INTEGER NOT NULL DEFAULT 0,
  UNIQUE(owner_type, owner_id, url)
);
CREATE TABLE IF NOT EXISTS feed_items (        -- nur Titel, Link und Datum (kein Volltext)
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel_id INTEGER NOT NULL,
  owner_type TEXT NOT NULL,
  owner_id INTEGER NOT NULL,
  url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  published INTEGER NOT NULL,
  hidden INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_feed_owner ON feed_items(owner_type, owner_id, published);
CREATE INDEX IF NOT EXISTS idx_feed_pub ON feed_items(published);
CREATE TABLE IF NOT EXISTS item_votes (
  item_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (item_id, user_id)
);
CREATE TABLE IF NOT EXISTS endorsements (
  owner_id INTEGER NOT NULL,                   -- Person
  eid TEXT NOT NULL,
  by_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (owner_id, eid, by_id)
);
CREATE TABLE IF NOT EXISTS orgs (              -- Firmen-Konten
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  handle TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  tagline TEXT NOT NULL DEFAULT '',
  about TEXT NOT NULL DEFAULT '',
  website TEXT NOT NULL DEFAULT '',
  country TEXT NOT NULL DEFAULT '',
  size TEXT NOT NULL DEFAULT '',               -- 1 | 2-10 | 11-50 | 51-200 | 201-1000 | 1000+
  public INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS org_members (
  org_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',         -- owner | admin | member
  status TEXT NOT NULL DEFAULT 'pending',      -- pending | active
  created INTEGER NOT NULL,
  PRIMARY KEY (org_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_om_user ON org_members(user_id);

-- Profilbilder / Firmenlogos (klein, vom Browser auf 256x256 JPEG verkleinert; Base64)
CREATE TABLE IF NOT EXISTS images (
  kind TEXT NOT NULL,                 -- u | o
  owner_id INTEGER NOT NULL,
  data TEXT NOT NULL,
  updated INTEGER NOT NULL,
  PRIMARY KEY (kind, owner_id)
);

-- Sponsoring-Gesuch von Firmen: NICHT oeffentlich (nur Inhaber/Admins; spaeter sichtbar fuer Veranstalter)
CREATE TABLE IF NOT EXISTS org_sponsor (
  org_id INTEGER PRIMARY KEY,
  open INTEGER NOT NULL DEFAULT 0,
  criteria TEXT NOT NULL DEFAULT '{}',   -- JSON: topics, format, min_audience, regions, budget, notes
  updated INTEGER NOT NULL
);

-- Anzeigename-Einstellung: echter Name (nur fuer den Nutzer selbst sichtbar) + gewaehlter Modus
CREATE TABLE IF NOT EXISTS user_prefs (
  user_id INTEGER PRIMARY KEY,
  real_name TEXT,
  name_mode TEXT NOT NULL DEFAULT 'short'   -- short | full | first | handle | custom
);

-- Events, Veranstalter und Sessions (Speaker)
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  handle TEXT NOT NULL UNIQUE,
  owner_id INTEGER NOT NULL,
  org_id INTEGER,                         -- optional: Veranstalter ist eine Firma
  title TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  about TEXT NOT NULL DEFAULT '',
  start TEXT NOT NULL,                    -- YYYY-MM-DD oder YYYY-MM-DDTHH:MM
  end TEXT NOT NULL DEFAULT '',
  mode TEXT NOT NULL DEFAULT 'online',    -- online | onsite | hybrid
  location TEXT NOT NULL DEFAULT '',
  country TEXT NOT NULL DEFAULT '',
  url TEXT NOT NULL DEFAULT '',
  tickets_url TEXT NOT NULL DEFAULT '',
  free INTEGER NOT NULL DEFAULT 1,
  lang TEXT NOT NULL DEFAULT '',
  topics TEXT NOT NULL DEFAULT '[]',      -- JSON: Entity-IDs
  seeking_sponsor INTEGER NOT NULL DEFAULT 0,
  public INTEGER NOT NULL DEFAULT 1,
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ev_owner ON events(owner_id);
CREATE TABLE IF NOT EXISTS event_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  abstract TEXT NOT NULL DEFAULT '',
  start TEXT NOT NULL DEFAULT '',
  end TEXT NOT NULL DEFAULT '',
  room TEXT NOT NULL DEFAULT '',
  track TEXT NOT NULL DEFAULT '',
  level TEXT NOT NULL DEFAULT '',
  lang TEXT NOT NULL DEFAULT '',
  topics TEXT NOT NULL DEFAULT '[]',
  speakers TEXT NOT NULL DEFAULT '[]',    -- JSON: [{h: profil-handle, n: name}]
  recording_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'live',    -- live | pending
  proposer_id INTEGER NOT NULL,
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_es_event ON event_sessions(event_id);

-- Empfehlungen (Recommendations) zwischen Mitgliedern; erst sichtbar, wenn die empfohlene Person freigibt
CREATE TABLE IF NOT EXISTS recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  subject_id INTEGER NOT NULL,
  relation TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',   -- pending | live
  created INTEGER NOT NULL,
  UNIQUE (author_id, subject_id)
);
CREATE INDEX IF NOT EXISTS idx_rec_subject ON recommendations(subject_id, status);

-- Speaker-Einladungen (Personen ohne Konto) und Entitaets-Uebernahme (Claim)
CREATE TABLE IF NOT EXISTS speaker_invites (
  token TEXT PRIMARY KEY,
  event_id INTEGER NOT NULL,
  session_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  eid TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS entity_claims (
  eid TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',   -- pending | verified
  via TEXT NOT NULL DEFAULT 'manual',       -- invite | manual
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_claim_user ON entity_claims(user_id);

-- Firma im Profil immer als Entitaet (nie Freitext)
CREATE TABLE IF NOT EXISTS profile_company (
  user_id INTEGER PRIMARY KEY,
  eid TEXT NOT NULL
);

-- Fluechtige Nachrichten: Threads + Nachrichten, Nachrichten werden nach 7 Tagen geloescht
CREATE TABLE IF NOT EXISTS msg_threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  a_id INTEGER NOT NULL,                 -- Initiator
  b_id INTEGER NOT NULL,
  ctx TEXT NOT NULL DEFAULT '',          -- optionaler Kontext, z. B. event:<handle>
  created INTEGER NOT NULL,
  last INTEGER NOT NULL,
  a_read INTEGER NOT NULL DEFAULT 0,
  b_read INTEGER NOT NULL DEFAULT 0,
  UNIQUE (a_id, b_id)
);
CREATE INDEX IF NOT EXISTS idx_mt_b ON msg_threads(b_id);
CREATE TABLE IF NOT EXISTS msg_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  from_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mm_thread ON msg_messages(thread_id, created);
CREATE TABLE IF NOT EXISTS msg_blocks (
  user_id INTEGER NOT NULL,
  blocked_id INTEGER NOT NULL,
  PRIMARY KEY (user_id, blocked_id)
);
CREATE TABLE IF NOT EXISTS msg_prefs (
  user_id INTEGER PRIMARY KEY,
  open INTEGER NOT NULL DEFAULT 1        -- 1 = Kontaktanfragen erlaubt
);

-- Firmenkonto <-> Firmen-Entitaet (wird beim Anlegen einer Firma automatisch erzeugt/verknuepft)
CREATE TABLE IF NOT EXISTS org_entity (
  org_id INTEGER PRIMARY KEY,
  eid TEXT NOT NULL
);

-- Punkte einloesen: Ausgaben (Guthaben = verdiente Punkte - Summe cost) und Tagesbonus fuer Kontakte
CREATE TABLE IF NOT EXISTS points_spent (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  item TEXT NOT NULL,
  cost INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'done',     -- done | pending (manuell zu erfuellen)
  note TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ps_user ON points_spent(user_id);
CREATE TABLE IF NOT EXISTS msg_bonus (
  user_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  extra INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);

-- Sponsoren-Anfragen von Veranstaltern an Firmen (2 Wunschfirmen je Event frei, weitere gegen Punkte)
CREATE TABLE IF NOT EXISTS sponsor_asks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL,
  org_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  UNIQUE (event_id, org_id)
);

CREATE TABLE IF NOT EXISTS edit_votes (
  kind TEXT NOT NULL,                     -- wiki | entity
  rev_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  v INTEGER NOT NULL,                     -- 1 | -1
  created INTEGER NOT NULL,
  PRIMARY KEY(kind, rev_id, user_id)
);

-- Persoenliche KI-Zugangstokens fuer den MCP-Server (nur Hash gespeichert)
CREATE TABLE IF NOT EXISTS api_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL,
  label TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL,
  last_used INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tok_user ON api_tokens(user_id);

CREATE TABLE IF NOT EXISTS cert_check (        -- Pruefung von Zertifikats-Nachweisen: verified (auto/admin) oder pending (wartet auf Redaktion)
  user_id INTEGER NOT NULL,
  eid TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  via TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, eid)
);
CREATE TABLE IF NOT EXISTS cert_endorse (      -- Bestaetigungen anderer Mitglieder fuer ein Zertifikat (Zaehler)
  owner_id INTEGER NOT NULL,
  eid TEXT NOT NULL,
  by_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (owner_id, eid, by_id)
);
CREATE TABLE IF NOT EXISTS entity_q (          -- Fragen zu Entitaeten
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  eid TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  q TEXT NOT NULL,
  lang TEXT NOT NULL DEFAULT 'en',
  hidden INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eq_eid ON entity_q(eid);
CREATE TABLE IF NOT EXISTS entity_a (          -- Antworten
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  q_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  a TEXT NOT NULL,
  accepted INTEGER NOT NULL DEFAULT 0,         -- vom Eigentuemer/der Redaktion angenommen
  hidden INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ea_q ON entity_a(q_id);
CREATE TABLE IF NOT EXISTS entity_a_votes (
  a_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created INTEGER NOT NULL,
  PRIMARY KEY (a_id, user_id)
);
CREATE TABLE IF NOT EXISTS profile_private (   -- Kontakt-/Adressdaten: standardmaessig privat, je Feld Sichtbarkeit all | contacts | none; spaeter fuer Umkreissuche
  user_id INTEGER PRIMARY KEY,
  city TEXT NOT NULL DEFAULT '', zip TEXT NOT NULL DEFAULT '', street TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '',
  vis_city TEXT NOT NULL DEFAULT 'none', vis_zip TEXT NOT NULL DEFAULT 'none', vis_street TEXT NOT NULL DEFAULT 'none', vis_email TEXT NOT NULL DEFAULT 'none', vis_phone TEXT NOT NULL DEFAULT 'none',
  updated INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS profile_i18n (       -- Profiltexte pro Sprache (Kurzzeile, Bio); Grundtext bleibt in profiles
  user_id INTEGER NOT NULL,
  lang TEXT NOT NULL,
  headline TEXT NOT NULL DEFAULT '',
  about TEXT NOT NULL DEFAULT '',
  updated INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, lang)
);

CREATE TABLE IF NOT EXISTS tr_gap (            -- fehlende Uebersetzungen: seit wann fehlt der Text (Community hat 24 h Vorrang vor der Auto-Uebersetzung)
  eid TEXT NOT NULL,
  field TEXT NOT NULL,
  first INTEGER NOT NULL,
  PRIMARY KEY (eid, field)
);

-- Event-Team: Rollen je Event (organisator, co-organisator, programm-manager, sponsor-manager, kommunikation, helfer)
CREATE TABLE IF NOT EXISTS event_roles (
  event_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  added_by INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  PRIMARY KEY (event_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_er_user ON event_roles(user_id);
