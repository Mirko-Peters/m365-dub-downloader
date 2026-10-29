// Abzeichen und Punkte. Anzeigenamen stehen im Frontend (data/community_i18n.json), hier nur IDs und Regeln.
export const BADGE_ORDER = ["editor", "wiki_author", "curator", "voice", "polyglot", "helpful", "early_bird", "streak", "commentator", "guardian", "li_follower", "founder", "team_member", "organizer", "speaker", "recommender", "recommended", "endorsed", "endorser", "connector", "profile_pro", "entity_owner", "sponsor_open", "notified", "first_comment", "newcomer"];

let epCache = { at: 0, map: null };
export async function episodeDates(env) {
  if (epCache.map && Date.now() - epCache.at < 3600e3) return epCache.map;
  try {
    const j = await (await fetch(`${env.SITE}/episodes.json`)).json();
    const m = new Map();
    for (const e of j.episodes || []) m.set(`${e.id}|${e.language}`, e.date);
    epCache = { at: Date.now(), map: m };
  } catch { epCache.map = epCache.map || new Map(); }
  return epCache.map;
}

export async function award(db, uid, badge) {
  const r = await db.prepare("INSERT OR IGNORE INTO user_badges(user_id,badge,earned) VALUES(?,?,?)").bind(uid, badge, Math.floor(Date.now() / 1000)).run();
  return (r.meta?.changes || 0) > 0;
}

// Prueft alle regelbasierten Abzeichen eines Nutzers; gibt neu verdiente zurueck
export async function evalBadges(env, uid) {
  const db = env.DB, now = Math.floor(Date.now() / 1000), got = [];
  const c = await db.prepare("SELECT COUNT(*) n, COUNT(DISTINCT lang) l FROM comments WHERE user_id=? AND status='ok'").bind(uid).first();
  const lk = await db.prepare("SELECT COUNT(*) n FROM likes l JOIN comments c ON c.id=l.comment_id WHERE c.user_id=? AND l.user_id<>?").bind(uid, uid).first();
  const ro = await db.prepare("SELECT role FROM users WHERE id=?").bind(uid).first();
  if (ro?.role === "editor") { if (await award(db, uid, "editor")) got.push("editor"); }
  else await db.prepare("DELETE FROM user_badges WHERE user_id=? AND badge='editor'").bind(uid).run();
  const wk = await db.prepare("SELECT COUNT(*) n FROM wiki_rev WHERE user_id=? AND status IN ('live','old')").bind(uid).first().catch(() => ({ n: 0 }));
  if (wk.n >= 1 && (await award(db, uid, "wiki_author"))) got.push("wiki_author");
  const rules = [["newcomer", true], ["first_comment", c.n >= 1], ["commentator", c.n >= 10], ["voice", c.n >= 50], ["helpful", lk.n >= 10], ["polyglot", c.l >= 3]];
  for (const [b, ok] of rules) if (ok && (await award(db, uid, b))) got.push(b);
  // Early bird: Kommentar innerhalb von 24 h nach Erscheinen der Folge
  if (c.n >= 1) {
    const dates = await episodeDates(env);
    const rows = await db.prepare("SELECT vid, lang, created FROM comments WHERE user_id=? AND status='ok' ORDER BY created DESC LIMIT 200").bind(uid).all();
    for (const r of rows.results || []) {
      const d = dates.get(`${r.vid}|${r.lang}`);
      if (d && r.created < Date.parse(d + "T00:00:00Z") / 1000 + 2 * 86400) { if (await award(db, uid, "early_bird")) got.push("early_bird"); break; }
    }
  }
  // Streak: 7 Tage in Folge aktiv (Kommentar oder Like)
  const act = await db.prepare(
    "SELECT DISTINCT date(created,'unixepoch') d FROM (SELECT created FROM comments WHERE user_id=?1 UNION ALL SELECT created FROM likes WHERE user_id=?1) WHERE created>?2"
  ).bind(uid, now - 8 * 86400).all();
  const days = new Set((act.results || []).map((r) => r.d));
  let run = 0;
  for (let i = 0; i < 7; i++) if (days.has(new Date((now - i * 86400) * 1000).toISOString().slice(0, 10))) run++;
  if (run >= 7 && (await award(db, uid, "streak"))) got.push("streak");
  // Guardian: 2 Meldungen, die zum Ausblenden gefuehrt haben
  const g = await db.prepare("SELECT COUNT(*) n FROM reports r JOIN comments c ON c.id=r.comment_id WHERE r.user_id=? AND c.status='hidden'").bind(uid).first();
  if (g.n >= 2 && (await award(db, uid, "guardian"))) got.push("guardian");
  // Neue Plattform-Abzeichen (Firmen, Events, Speaker, Empfehlungen, Bestaetigungen, Kontakte, Profil)
  const n = async (sql, ...b) => ((await db.prepare(sql).bind(...b).first().catch(() => ({ n: 0 })))?.n) || 0;
  const q = {
    founder: await n("SELECT COUNT(*) n FROM org_members WHERE user_id=? AND role='owner' AND status='active'", uid),
    team_member: await n("SELECT COUNT(*) n FROM org_members WHERE user_id=? AND role<>'owner' AND status='active'", uid),
    organizer: await n("SELECT COUNT(*) n FROM events WHERE owner_id=?", uid),
    speaker: await n("SELECT COUNT(*) n FROM event_sessions WHERE speakers LIKE '%\"s\":\"confirmed\"%' AND speakers LIKE '%\"h\":\"' || COALESCE((SELECT handle FROM profiles WHERE user_id=?),'-') || '\"%'", uid),
    recommender: await n("SELECT COUNT(*) n FROM recommendations WHERE author_id=? AND status='live'", uid),
    recommended: await n("SELECT COUNT(*) n FROM recommendations WHERE subject_id=? AND status='live'", uid),
    endorsed: await n("SELECT COUNT(*) n FROM endorsements n2 JOIN expertise e ON e.owner_id=n2.owner_id AND e.eid=n2.eid AND e.owner_type='u' WHERE n2.owner_id=?", uid),
    endorser: await n("SELECT COUNT(*) n FROM endorsements WHERE by_id=?", uid),
    connector: await n("SELECT COUNT(*) n FROM msg_threads WHERE a_id=?", uid),
    profile_pro: await n("SELECT COUNT(*) n FROM profiles p WHERE p.user_id=? AND p.public=1 AND p.headline<>'' AND p.about<>'' AND EXISTS (SELECT 1 FROM expertise WHERE owner_type='u' AND owner_id=p.user_id) AND EXISTS (SELECT 1 FROM images WHERE kind='u' AND owner_id=p.user_id)", uid),
    entity_owner: await n("SELECT COUNT(*) n FROM entity_claims WHERE user_id=? AND status='verified'", uid),
    sponsor_open: await n("SELECT COUNT(*) n FROM org_sponsor s JOIN org_members m ON m.org_id=s.org_id WHERE s.open=1 AND m.user_id=? AND m.status='active'", uid),
  };
  const need = { founder: 1, team_member: 1, organizer: 1, speaker: 1, recommender: 1, recommended: 1, endorsed: 3, endorser: 5, connector: 3, profile_pro: 1, entity_owner: 1, sponsor_open: 1 };
  for (const [b, k] of Object.entries(need)) if (q[b] >= k && (await award(db, uid, b))) got.push(b);
  return got;
}

// Punkte = Aktivitaeten (berechnet) + Abzeichen x5; Guthaben = Punkte - eingeloeste Punkte
export async function stats(db, uid) {
  const n = async (sql, ...b) => ((await db.prepare(sql).bind(...b).first().catch(() => ({ n: 0 })))?.n) || 0;
  const c = await db.prepare("SELECT COUNT(*) n FROM comments WHERE user_id=? AND status='ok'").bind(uid).first();
  const l = await db.prepare("SELECT COUNT(*) n FROM likes l JOIN comments c ON c.id=l.comment_id WHERE c.user_id=? AND l.user_id<>?").bind(uid, uid).first();
  const b = await db.prepare("SELECT badge FROM user_badges WHERE user_id=?").bind(uid).all();
  const badges = (b.results || []).map((x) => x.badge).sort((a, z) => BADGE_ORDER.indexOf(a) - BADGE_ORDER.indexOf(z));
  const a = {
    wiki: await n("SELECT COUNT(*) n FROM wiki_rev WHERE user_id=? AND status IN ('live','old')", uid), ent: await n("SELECT COUNT(*) n FROM entity_rev WHERE user_id=? AND status IN ('live','old')", uid),
    orgs_owned: await n("SELECT COUNT(*) n FROM org_members WHERE user_id=? AND role='owner' AND status='active'", uid), orgs_joined: await n("SELECT COUNT(*) n FROM org_members WHERE user_id=? AND role<>'owner' AND status='active'", uid),
    events: await n("SELECT COUNT(*) n FROM events WHERE owner_id=?", uid), rec_w: await n("SELECT COUNT(*) n FROM recommendations WHERE author_id=? AND status='live'", uid), rec_r: await n("SELECT COUNT(*) n FROM recommendations WHERE subject_id=? AND status='live'", uid),
    endo_r: await n("SELECT COUNT(*) n FROM endorsements WHERE owner_id=?", uid), endo_g: await n("SELECT COUNT(*) n FROM endorsements WHERE by_id=?", uid),
    speaker: await n("SELECT COUNT(*) n FROM event_sessions WHERE speakers LIKE '%\"s\":\"confirmed\"%' AND speakers LIKE '%\"h\":\"' || COALESCE((SELECT handle FROM profiles WHERE user_id=?),'-') || '\"%'", uid),
    pub: await n("SELECT COUNT(*) n FROM profiles WHERE user_id=? AND public=1", uid),
  };
  // Punkteskala: Kommentar 1, erhaltener Like 1, Wiki-/Entitaets-Aenderung 3, Bestaetigung 2/1, Empfehlung 5/5, Firma gruenden 30, beitreten 5, Event 50, bestaetigter Speaker 100, oeffentliches Profil 10, Abzeichen je 5
  const earned = c.n * 1 + l.n * 1 + badges.length * 5 + a.wiki * 3 + a.ent * 3 + a.orgs_owned * 30 + a.orgs_joined * 5 + a.events * 50 + a.speaker * 100 + a.rec_w * 5 + a.rec_r * 5 + Math.min(a.endo_r, 20) * 2 + Math.min(a.endo_g, 20) + a.pub * 10;
  const spent = await n("SELECT COALESCE(SUM(cost),0) n FROM points_spent WHERE user_id=?", uid);
  return { comments: c.n, likes: l.n, badges, points: earned, earned, spent, balance: earned - spent };
}

// Punkte eines Zeitraums je Sprache (fuer den Kurator): Kommentare x2 + erhaltene Likes x3
export async function topUsers(db, lang, since, limit = 5) {
  const r = await db.prepare(
    `SELECT u.id, u.name, u.bio,
       (SELECT COUNT(*) FROM comments c WHERE c.user_id=u.id AND c.lang=?1 AND c.status='ok' AND c.created>=?2) AS cm,
       (SELECT COUNT(*) FROM likes l JOIN comments c ON c.id=l.comment_id WHERE c.user_id=u.id AND c.lang=?1 AND c.status='ok' AND l.created>=?2 AND l.user_id<>u.id) AS lk
     FROM users u WHERE u.banned=0 AND EXISTS (SELECT 1 FROM comments c WHERE c.user_id=u.id AND c.lang=?1 AND c.created>=?2)
     ORDER BY (cm + lk) DESC, u.id ASC LIMIT ?3`
  ).bind(lang, since, limit).all();
  return (r.results || []).map((x) => ({ id: x.id, name: x.name, bio: x.bio, comments: x.cm, likes: x.lk, points: x.cm + x.lk })).filter((x) => x.points > 0);
}

export async function badgesFor(db, ids) {
  if (!ids.length) return new Map();
  const q = await db.prepare(`SELECT user_id, badge FROM user_badges WHERE user_id IN (${ids.map(() => "?").join(",")})`).bind(...ids).all();
  const m = new Map();
  for (const r of q.results || []) { if (!m.has(r.user_id)) m.set(r.user_id, []); m.get(r.user_id).push(r.badge); }
  for (const [k, v] of m) m.set(k, v.sort((a, z) => BADGE_ORDER.indexOf(a) - BADGE_ORDER.indexOf(z)));
  const pq = await db.prepare(`SELECT owner_id id, program p FROM programs WHERE owner_type='u' AND verified=1 AND owner_id IN (${ids.map(() => "?").join(",")})`).bind(...ids).all();
  const PO = ["mvp", "rd", "mct", "msa", "ms_employee", "partner"];
  for (const r of (pq.results || []).sort((a, z) => PO.indexOf(z.p) - PO.indexOf(a.p))) m.set(r.id, ["prog_" + r.p, ...(m.get(r.id) || [])]);
  return m;
}

// Monatswechsel: Kurator des Vormonats je Sprache festschreiben + Abzeichen
export async function closeMonth(env) {
  const db = env.DB, d = new Date();
  const first = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000;
  const prevStart = Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - 1, 1) / 1000;
  const key = new Date(prevStart * 1000).toISOString().slice(0, 7);
  const done = await db.prepare("SELECT v FROM meta WHERE k='curator_closed'").first();
  if (done?.v === key) return 0;
  let n = 0;
  for (const lang of ["de", "es", "fr", "it", "pt", "nl", "pl", "id", "ru", "uk", "ar", "he", "hi", "ja", "ko", "ml", "pa", "ta", "te"]) {
    const rows = await db.prepare(
      `SELECT u.id, (SELECT COUNT(*) FROM comments c WHERE c.user_id=u.id AND c.lang=?1 AND c.status='ok' AND c.created>=?2 AND c.created<?3) cm,
        (SELECT COUNT(*) FROM likes l JOIN comments c ON c.id=l.comment_id WHERE c.user_id=u.id AND c.lang=?1 AND c.status='ok' AND l.created>=?2 AND l.created<?3 AND l.user_id<>u.id) lk
       FROM users u WHERE u.banned=0 ORDER BY (cm*2+lk*3) DESC LIMIT 1`).bind(lang, prevStart, first).all();
    const top = rows.results?.[0];
    if (top && top.cm * 2 + top.lk * 3 > 0) {
      await db.prepare("INSERT OR REPLACE INTO curators(lang,month,user_id,points) VALUES(?,?,?,?)").bind(lang, key, top.id, top.cm * 2 + top.lk * 3).run();
      await award(db, top.id, "curator"); n++;
    }
  }
  await db.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES('curator_closed',?)").bind(key).run();
  return n;
}
