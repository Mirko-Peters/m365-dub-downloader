// Abzeichen und Punkte. Anzeigenamen stehen im Frontend (data/community_i18n.json), hier nur IDs und Regeln.
export const BADGE_ORDER = ["curator", "voice", "polyglot", "helpful", "early_bird", "streak", "commentator", "guardian", "notified", "first_comment", "newcomer"];

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
  return got;
}

export async function stats(db, uid) {
  const c = await db.prepare("SELECT COUNT(*) n FROM comments WHERE user_id=? AND status='ok'").bind(uid).first();
  const l = await db.prepare("SELECT COUNT(*) n FROM likes l JOIN comments c ON c.id=l.comment_id WHERE c.user_id=? AND l.user_id<>?").bind(uid, uid).first();
  const b = await db.prepare("SELECT badge FROM user_badges WHERE user_id=?").bind(uid).all();
  const badges = (b.results || []).map((x) => x.badge).sort((a, z) => BADGE_ORDER.indexOf(a) - BADGE_ORDER.indexOf(z));
  return { comments: c.n, likes: l.n, badges, points: c.n * 2 + l.n * 3 + badges.length * 5 };
}

// Punkte eines Zeitraums je Sprache (fuer den Kurator): Kommentare x2 + erhaltene Likes x3
export async function topUsers(db, lang, since, limit = 5) {
  const r = await db.prepare(
    `SELECT u.id, u.name, u.bio,
       (SELECT COUNT(*) FROM comments c WHERE c.user_id=u.id AND c.lang=?1 AND c.status='ok' AND c.created>=?2) AS cm,
       (SELECT COUNT(*) FROM likes l JOIN comments c ON c.id=l.comment_id WHERE c.user_id=u.id AND c.lang=?1 AND c.status='ok' AND l.created>=?2 AND l.user_id<>u.id) AS lk
     FROM users u WHERE u.banned=0 AND EXISTS (SELECT 1 FROM comments c WHERE c.user_id=u.id AND c.lang=?1 AND c.created>=?2)
     ORDER BY (cm*2 + lk*3) DESC, u.id ASC LIMIT ?3`
  ).bind(lang, since, limit).all();
  return (r.results || []).map((x) => ({ id: x.id, name: x.name, bio: x.bio, comments: x.cm, likes: x.lk, points: x.cm * 2 + x.lk * 3 })).filter((x) => x.points > 0);
}

export async function badgesFor(db, ids) {
  if (!ids.length) return new Map();
  const q = await db.prepare(`SELECT user_id, badge FROM user_badges WHERE user_id IN (${ids.map(() => "?").join(",")})`).bind(...ids).all();
  const m = new Map();
  for (const r of q.results || []) { if (!m.has(r.user_id)) m.set(r.user_id, []); m.get(r.user_id).push(r.badge); }
  for (const [k, v] of m) m.set(k, v.sort((a, z) => BADGE_ORDER.indexOf(a) - BADGE_ORDER.indexOf(z)));
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
