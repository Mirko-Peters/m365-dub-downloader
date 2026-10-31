-- Expertise-Stufen aus Belegen statt Selbstangabe (Paket 22).
-- expertise bleibt die Zustandstabelle (owner_type, owner_id, eid, level, verified); level wird jetzt vom System gesetzt:
--   1 lernt | 2 Praxis | 3 Experte | 4 Evangelist (Experte + 100 Bestaetigungen anderer Mitglieder) | 5 Master (1000) | 6 Master Evangelist (1000 Bestaetigungen von Evangelisten im selben Thema)
-- expertise_evidence: ein Beleg je Beitrag und Thema (kind: blog | coauthor | session | podcast | video | guest | library | listing | wiki | entity | cert | answer | self), wird vom Cron syncExpertise neu aufgebaut; 'self' = fruehere Selbstangabe (einmalig uebernommen).
-- expertise_score: berechnete Kennzahlen je Person und Thema (Punkte, Bestaetigungen, Bestaetigungen durch Evangelisten).
CREATE TABLE IF NOT EXISTS expertise_evidence (
  owner_id INTEGER NOT NULL,
  eid TEXT NOT NULL,
  kind TEXT NOT NULL,
  item_id TEXT NOT NULL DEFAULT '',
  weight REAL NOT NULL DEFAULT 1,
  created INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (owner_id, eid, kind, item_id)
);
CREATE INDEX IF NOT EXISTS idx_exp_ev_owner ON expertise_evidence(owner_id, eid);
CREATE TABLE IF NOT EXISTS expertise_score (
  owner_id INTEGER NOT NULL,
  eid TEXT NOT NULL,
  score REAL NOT NULL DEFAULT 0,
  endorsed INTEGER NOT NULL DEFAULT 0,
  endorsed_ev INTEGER NOT NULL DEFAULT 0,
  updated INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (owner_id, eid)
);
