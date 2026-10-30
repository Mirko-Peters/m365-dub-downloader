// Events (Veranstalter), Sessions mit Speakern, Sponsoren-Suche fuer Veranstalter
import { sendMail } from "./digest.js";
import { ownedEntity } from "./profiles.js";
import { cleanText, rateLimit } from "./util.js";
import { baseIds, entityMap } from "./entities.js";
import { cleanUrl } from "./profiles.js";
import { stats } from "./badges.js";

const FREE_ASKS = 2, ASK_COST = 1000;
const HANDLE = /^[a-z0-9][a-z0-9-]{2,39}$/, PH = /^[a-z0-9][a-z0-9-]{2,29}$/;
const DATE = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?$/, MODES = ["online", "onsite", "hybrid"], LEVELS = ["", "100", "200", "300", "400"];
const now = () => Math.floor(Date.now() / 1000);
const txt = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/\s+/g, " ").trim();
const long = (s, n) => cleanText(s, n).replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
const okDate = (s) => DATE.test(s) && !isNaN(Date.parse(s.length === 10 ? s + "T00:00:00Z" : s + ":00Z"));
const parse = (s, d) => { try { return JSON.parse(s); } catch { return d; } };

async function topics(env, list) {
  const known = await baseIds(env), out = [];
  for (const t of (Array.isArray(list) ? list : []).slice(0, 12)) { if (!known.has(t)) return null; if (!out.includes(t)) out.push(t); }
  return out;
}
// Event-Rollen: Rechte je Rolle (Veranstalter-Firma Inhaber/Admin/Event-Manager und Eigentuemer koennen alles ausser Rollen-Details)
// Events, deren Anmeldungen (mit Einwilligung) an ein externes System uebergeben werden
export const TRANSFER = { "m365con-2027": "heysummit:229506" };
export const EVENT_ROLES = {
  organisator: ["edit", "sessions", "sponsor", "roles", "delete"],
  "co-organisator": ["edit", "sessions", "sponsor", "roles"],
  "programm-manager": ["sessions"],
  "sponsor-manager": ["sponsor"],
  kommunikation: ["edit"],
  helfer: [],
};
// Darf der Nutzer am Event etwas tun? perm: edit | sessions | sponsor | roles | delete
export async function canManage(db, user, ev, perm = "edit") {
  if (!user || !ev) return false;
  if (ev.owner_id === user.id || user.admin) return true;
  if (ev.org_id) { const om = await db.prepare("SELECT role FROM org_members WHERE org_id=? AND user_id=? AND status='active' AND role IN ('owner','admin','events')").bind(ev.org_id, user.id).first(); if (om && (perm !== "delete" || om.role !== "events")) return true; }
  const r = await db.prepare("SELECT role FROM event_roles WHERE event_id=? AND user_id=?").bind(ev.id, user.id).first();
  return !!r && (EVENT_ROLES[r.role] || []).includes(perm);
}
// Freie Plaetze mit Wartelisten-Mitgliedern in Anmelde-Reihenfolge auffuellen
export async function promoteWaitlist(db, evId, cap) {
  if (cap <= 0) { await db.prepare("UPDATE event_attendees SET status='going' WHERE event_id=? AND status='waitlist'").bind(evId).run(); return; }
  const going = (await db.prepare("SELECT COUNT(*) n FROM event_attendees WHERE event_id=? AND status='going'").bind(evId).first()).n;
  if (going < cap) await db.prepare("UPDATE event_attendees SET status='going' WHERE rowid IN (SELECT rowid FROM event_attendees WHERE event_id=? AND status='waitlist' ORDER BY created LIMIT ?)").bind(evId, cap - going).run();
}
// Partner-Logik (REST und MCP): action = propose | accept | decline | remove
export async function partnerAction(db, user, ev, orgHandle, kind, level, action) {
  const org = await db.prepare("SELECT id,handle,name FROM orgs WHERE handle=?").bind(String(orgHandle || "")).first(); if (!org) return { error: "not_found" };
  const asTeam = await canManage(db, user, ev, "sponsor");
  const asOrg = !!(await db.prepare("SELECT 1 x FROM org_members WHERE org_id=? AND user_id=? AND status='active' AND role IN ('owner','admin','events')").bind(org.id, user.id).first());
  if (!asTeam && !asOrg) return { error: "forbidden" };
  const cur = await db.prepare("SELECT * FROM event_partners WHERE event_id=? AND org_id=?").bind(ev.id, org.id).first();
  if (action === "remove") { if (!cur) return { error: "not_found" }; await db.prepare("DELETE FROM event_partners WHERE event_id=? AND org_id=?").bind(ev.id, org.id).run(); return { ok: true }; }
  if (action === "accept" || action === "decline") {
    if (!cur || cur.status !== "pending") return { error: "not_found" };
    const mine = cur.by === "e" ? asOrg : asTeam;   // die Gegenseite entscheidet
    if (!mine) return { error: "forbidden" };
    if (action === "decline") { await db.prepare("DELETE FROM event_partners WHERE event_id=? AND org_id=?").bind(ev.id, org.id).run(); return { ok: true, declined: true }; }
    await db.prepare("UPDATE event_partners SET status='confirmed' WHERE event_id=? AND org_id=?").bind(ev.id, org.id).run(); return { ok: true, status: "confirmed" };
  }
  if (!["sponsor", "media"].includes(kind)) return { error: "bad_kind" };
  if (cur) { if (cur.status === "confirmed") return { error: "already" }; if ((cur.by === "e" && asOrg) || (cur.by === "o" && asTeam)) { await db.prepare("UPDATE event_partners SET status='confirmed',kind=?,level=? WHERE event_id=? AND org_id=?").bind(kind, txt(level || cur.level, 40), ev.id, org.id).run(); return { ok: true, status: "confirmed" }; } return { error: "already" }; }
  if ((await db.prepare("SELECT COUNT(*) n FROM event_partners WHERE event_id=?").bind(ev.id).first()).n >= 60) return { error: "limit" };
  await db.prepare("INSERT INTO event_partners(event_id,org_id,kind,level,status,by,created) VALUES(?,?,?,?,?,?,?)").bind(ev.id, org.id, kind, txt(level, 40), "pending", asTeam ? "e" : "o", now()).run();
  return { ok: true, status: "pending" };
}
const EID = /^[a-z0-9-]{2,48}$/;
const rndToken = () => [...crypto.getRandomValues(new Uint8Array(18))].map((b) => b.toString(16).padStart(2, "0")).join("");
// Speaker pruefen. Jede Person muss die Teilnahme selbst bestaetigen (s: invited|confirmed). Bestehende Stati/Tokens bleiben erhalten.
async function speakersCheck(db, list, prev, selfHandle) {
  const out = [], old = new Map((prev || []).map((x) => [x.h || x.n, x]));
  for (const s of (Array.isArray(list) ? list : []).slice(0, 8)) {
    const n = txt(s?.n, 80); let h = String(s?.h || "").toLowerCase().trim(), e = String(s?.e || "").toLowerCase().trim();
    if (e && !EID.test(e)) return null;
    if (!h && n.length >= 3) {   // Speaker existiert schon als oeffentliches Profil (eindeutiger Name)? Dann direkt verknuepfen, er bestaetigt in seinem Profil
      const m = (await db.prepare("SELECT p.handle FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.public=1 AND p.handle IS NOT NULL AND lower(u.name)=lower(?) LIMIT 2").bind(n).all()).results || [];
      if (m.length === 1) h = m[0].handle;
    }
    if (!e && n.length >= 3) {
      const pe = (await db.prepare("SELECT eid FROM entity_rev WHERE status='live' AND json_extract(data,'$.type')='person' AND lower(json_extract(data,'$.name'))=lower(?) LIMIT 2").bind(n).all()).results || [];
      if (pe.length === 1) e = pe[0].eid;
    }
    const keep = old.get(h || n);
    if (h) {
      if (!PH.test(h)) return null;
      const p = await db.prepare("SELECT u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.handle=? AND p.public=1").bind(h).first();
      if (!p) return null;
      out.push({ h, n: keep?.n || n || p.name, ...(e ? { e } : keep?.e ? { e: keep.e } : {}), s: keep?.s === "confirmed" || h === selfHandle ? "confirmed" : keep?.s === "declined" ? "declined" : "invited" });
    } else if (n.length >= 2) out.push({ n, ...(e ? { e } : keep?.e ? { e: keep.e } : {}), s: keep?.s === "confirmed" ? "confirmed" : "invited", ...(keep?.o ? { o: 1 } : {}), ...(keep?.t ? { t: keep.t } : { t: rndToken() }) });
  }
  return out;
}
async function saveInvites(db, evId, sid, sp) {
  const ops = [db.prepare("DELETE FROM speaker_invites WHERE session_id=? AND token NOT IN (SELECT value FROM json_each(?))").bind(sid, JSON.stringify(sp.filter((x) => x.t).map((x) => x.t)))];
  for (const x of sp) if (x.t && x.s !== "confirmed") ops.push(db.prepare("INSERT OR IGNORE INTO speaker_invites(token,event_id,session_id,name,eid,created) VALUES(?,?,?,?,?,?)").bind(x.t, evId, sid, x.n, x.e || "", now()));
  await db.batch(ops);
}
async function claimEntity(db, eid, uid, via) {
  const c = await db.prepare("SELECT user_id FROM entity_claims WHERE eid=?").bind(eid).first();
  if (c && c.user_id !== uid) return false;
  await db.prepare("INSERT INTO entity_claims(eid,user_id,status,via,created) VALUES(?,?,?,?,?) ON CONFLICT(eid) DO UPDATE SET status=CASE WHEN excluded.status='verified' THEN 'verified' ELSE entity_claims.status END").bind(eid, uid, via === "invite" ? "verified" : "pending", via, now()).run();
  return true;
}
const sessView = (r, mgr) => ({ id: r.id, title: r.title, abstract: r.abstract, start: r.start, end: r.end, room: r.room, track: r.track, level: r.level, lang: r.lang, topics: parse(r.topics, []), speakers: mgr ? parse(r.speakers, []) : parse(r.speakers, []).filter((x) => x.s === "confirmed").map((x) => ({ h: x.h, n: x.n, e: x.e })), speakers_open: parse(r.speakers, []).filter((x) => x.s !== "confirmed").length, recording_url: r.recording_url, status: r.status });
async function evView(db, ev, withPending) {
  const org = ev.org_id ? await db.prepare("SELECT handle,name,public FROM orgs WHERE id=?").bind(ev.org_id).first() : null;
  const ow = await db.prepare("SELECT u.name,p.handle FROM users u LEFT JOIN profiles p ON p.user_id=u.id AND p.public=1 WHERE u.id=?").bind(ev.owner_id).first();
  const rows = (await db.prepare("SELECT * FROM event_sessions WHERE event_id=? " + (withPending ? "" : "AND status='live' ") + "ORDER BY start,id").bind(ev.id).all()).results || [];
  return { handle: ev.handle, title: ev.title, summary: ev.summary, about: ev.about, start: ev.start, end: ev.end, mode: ev.mode, location: ev.location, country: ev.country, url: ev.url, tickets_url: ev.tickets_url,
    free: !!ev.free, lang: ev.lang, topics: parse(ev.topics, []), seeking_sponsor: !!ev.seeking_sponsor, public: !!ev.public,
    partners: ((await db.prepare("SELECT p.kind,p.level,o.handle,o.name,o.public FROM event_partners p JOIN orgs o ON o.id=p.org_id WHERE p.event_id=? AND p.status='confirmed' ORDER BY p.created").bind(ev.id).all()).results || []).map((x) => ({ kind: x.kind, level: x.level, name: x.name, handle: x.public ? x.handle : "" })),
    asked: withPending ? ((await db.prepare("SELECT o.handle FROM sponsor_asks a JOIN orgs o ON o.id=a.org_id WHERE a.event_id=?").bind(ev.id).all()).results || []).map((x) => x.handle) : undefined,
    organizer: org ? { kind: "o", handle: org.public ? org.handle : "", name: org.name } : { kind: "u", handle: ow?.handle || "", name: ow?.name || "" }, sessions: rows.map((r) => sessView(r, withPending)) };
}

export async function ensureM365Con(env) {   // M365Con 2027 ist ein Event und gehoert dem Admin als Veranstalter
  const db = env.DB, subs = (env.ADMIN_SUBS || "").split(",").map((x) => x.trim()).filter(Boolean);
  let owner = null;
  for (const a of subs) { const [pr, ...rest] = a.split(":"); owner = await db.prepare("SELECT id FROM users WHERE provider=? AND sub=?").bind(pr, rest.join(":")).first(); if (owner) break; }
  if (!owner) return;
  const t = Math.floor(Date.now() / 1000), ex = await db.prepare("SELECT id,owner_id FROM events WHERE handle='m365con-2027'").first();
  // Admin-Profil einmalig vorbelegen (nur fehlende Teile, spaetere Aenderungen des Admins bleiben erhalten)
  if (!(await db.prepare("SELECT 1 x FROM profiles WHERE user_id=?").bind(owner.id).first()) && !(await db.prepare("SELECT 1 x FROM profiles WHERE handle='mirko-peters'").first())) {
    await db.prepare("INSERT INTO profiles(user_id,public,handle,headline,about,company,job,country,show_org,updated) VALUES(?,1,'mirko-peters',?,?,'M365.FM',?,'Germany',1,?)")
      .bind(owner.id, "Microsoft MVP · Host of M365.FM · Organizer of M365Con", "Mirko Peters is a Microsoft MVP who explains Microsoft 365, Microsoft Copilot, Azure, Power Platform, Microsoft Fabric and AI agents for IT admins, architects, developers and decision makers. He hosts the podcast M365.FM and the M365 Show on YouTube (animated explainers and Microsoft certification courses), organizes the free online conference M365Con and publishes e-books on Microsoft topics.", "Podcast host and conference organizer", t).run();
  }
  const prof = await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(owner.id).first();
  const seeded = await db.prepare("SELECT 1 x FROM meta WHERE k='seed_admin_profile'").first();   // Vorbelegung nur einmal, danach gehoert das Profil dem Admin
  if (prof?.handle && !seeded) {
    await db.prepare("UPDATE profiles SET about=? WHERE user_id=? AND length(about)<=420").bind(`Mirko Peters ist Microsoft MVP, Podcaster, Autor und Konferenzveranstalter mit Schwerpunkt auf Microsoft 365, Microsoft Copilot, Azure, Power Platform, Microsoft Fabric und KI-Agenten. Er hostet den Podcast M365.FM und die m365 Show auf YouTube mit animierten Erklärvideos (Sticky Man Explained) und Zertifizierungskursen, organisiert die kostenlose Online-Konferenz M365Con (11.–22. Januar 2027) und veröffentlicht E-Books zu Microsoft-Themen. Seine Inhalte richten sich an IT-Admins, Architekten, Entwickler und Entscheider, die die Microsoft-Cloud ohne Marketing-Rauschen verstehen wollen. Die Podcast-Episoden gibt es als KI-vertontes Audio in 19 Sprachen.

Mirko Peters is a Microsoft MVP, podcaster, author and conference organizer focused on Microsoft 365, Microsoft Copilot, Azure, Power Platform, Microsoft Fabric and AI agents. He hosts the podcast M365.FM and the m365 Show on YouTube with animated explainers (Sticky Man Explained) and certification courses, organizes the free online conference M365Con (11-22 January 2027) and publishes e-books on Microsoft topics. His content is aimed at IT admins, architects, developers and decision makers who want to understand the Microsoft cloud without marketing noise. The podcast episodes are available as AI-dubbed audio in 19 languages.`, owner.id).run();   // ausfuehrliche Bio einmalig, solange nur der Kurztext steht   // Besitzer ist der Admin (Mirko): Programm, Kanaele und 12 Expertise-Themen auch bei abweichender Profil-Adresse ergaenzen
    await db.prepare("INSERT OR IGNORE INTO programs(owner_type,owner_id,program,year,url,verified) VALUES('u',?,'mvp',0,'https://mvp.microsoft.com/de-DE/mvp/profile/9b0ca797-db5a-493a-a845-8b9158046cf5',1)").bind(owner.id).run();
    for (const [k, u] of [["linkedin", "https://www.linkedin.com/in/m365showpodcast/"], ["youtube", "https://www.youtube.com/channel/UCIdo4tN3khKldHP3733E9JA"], ["website", "https://www.m365.fm"], ["website", "https://m365con.net"], ["github", "https://github.com/Mirko-Peters"], ["podcast", "https://www.spreaker.com/show/7393187"], ["podcast", "https://www.spreaker.com/show/6704921"]])
      await db.prepare("INSERT OR IGNORE INTO channels(owner_type,owner_id,kind,url) VALUES('u',?,?,?)").bind(owner.id, k, u).run();
    for (const eid of ["microsoft-365", "copilot", "copilot-studio", "azure", "azure-ai-foundry", "power-platform", "fabric", "purview", "teams", "sharepoint", "ai-agent", "entra-id"])
      await db.prepare("INSERT OR IGNORE INTO expertise(owner_type,owner_id,eid,level,verified) VALUES('u',?,?,3,1)").bind(owner.id, eid).run();
    await db.prepare("INSERT OR IGNORE INTO meta(k,v) VALUES('seed_admin_profile','1')").run();
  }
  await db.prepare("UPDATE users SET name='Mirko Peters' WHERE id=? AND name LIKE 'Mirko P%' AND name<>'Mirko Peters'").bind(owner.id).run();   // voller Name fuer das oeffentliche Profil
  const adm = { id: owner.id, admin: true, name: "Mirko Peters" };
  await ownedEntity(env, adm, { eid: "m365show", type: "media", name: "M365 Show", en: "The M365 Show is a video and podcast show about Microsoft 365, Copilot, Azure and the Power Platform with animated explainers and certification courses.", de: "Die M365 Show ist eine Video- und Podcast-Show zu Microsoft 365, Copilot, Azure und Power Platform mit animierten Erklaerungen und Zertifizierungskursen.", web: "https://m365.show" });
  const ORGS = [
    ["m365show", "M365 Show", "Video and podcast show about Microsoft 365, Copilot and AI", "The M365 Show brings animated explainers, interviews and Microsoft certification courses on Microsoft 365, Copilot, Azure and the Power Platform. Hosted by Mirko Peters, Microsoft MVP.", "https://m365.show", "m365show", [["youtube", "https://www.youtube.com/channel/UCIdo4tN3khKldHP3733E9JA"], ["linkedin", "https://www.linkedin.com/in/m365showpodcast/"]]],
    ["m365fm", "M365.FM", "Podcast and community about Microsoft 365, Copilot and AI", "M365.FM is the podcast network about Microsoft 365 with 900+ conversations with Microsoft MVPs, product experts and architects, available in 19 languages.", "https://www.m365.fm", "m365fm", [["website", "https://www.m365.fm"]]],
    ["m365con", "M365Con", "Free online convention for the Microsoft 365 community", "M365Con is the free online convention for the Microsoft community: 10 days, 120+ sessions, 120+ speakers and a daily focus topic. Organized by Mirko Peters and team.", "https://m365con.net", "m365con", [["website", "https://m365con.net"]]],
  ];
  for (const [h, nm, tg, about, web, eid, chs] of ORGS) {
    let o = await db.prepare("SELECT id FROM orgs WHERE handle=?").bind(h).first();
    if (!o) { const r = await db.prepare("INSERT INTO orgs(handle,name,tagline,about,website,country,size,public,created) VALUES(?,?,?,?,?,'Germany','2-10',1,?)").bind(h, nm, tg, about, web, t).run(); o = { id: r.meta.last_row_id }; }
    else await db.prepare("UPDATE orgs SET about=CASE WHEN about='' THEN ? ELSE about END, tagline=CASE WHEN tagline='' THEN ? ELSE tagline END WHERE id=?").bind(about, tg, o.id).run();
    await db.prepare("INSERT OR IGNORE INTO org_members(org_id,user_id,role,status,created) VALUES(?,?,'owner','active',?)").bind(o.id, owner.id, t).run();
    await db.prepare("INSERT OR IGNORE INTO org_entity(org_id,eid) VALUES(?,?)").bind(o.id, eid).run();
    for (const [k, u] of chs) await db.prepare("INSERT OR IGNORE INTO channels(owner_type,owner_id,kind,url) VALUES('o',?,?,?)").bind(o.id, k, u).run();
  }
  for (const eid of ["m365con", "m365fm", "m365show", "mirko-peters"]) await db.prepare("INSERT INTO entity_claims(eid,user_id,status,via,created) VALUES(?,?,'verified','admin',?) ON CONFLICT(eid) DO NOTHING").bind(eid, owner.id, t).run();
  if (!ex) await db.prepare("INSERT INTO events(handle,owner_id,title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,created,updated) VALUES('m365con-2027',?,?,?,?,?,?,'online','Online','','https://m365con.net','https://m365con.net',1,'en','[\"m365con\"]',1,1,?,?)")
    .bind(owner.id, "M365Con 2027", "Free online convention: 10 days, 120+ sessions, 120+ speakers, a daily focus topic.", "M365Con 2027 is a free online convention about Microsoft 365, Copilot and AI with 10 days of sessions, a daily focus topic and 120+ speakers.", "2027-01-11T08:00", "2027-01-22", t, t).run();
  else if (ex.owner_id !== owner.id) await db.prepare("UPDATE events SET owner_id=? WHERE id=?").bind(owner.id, ex.id).run();
  // Programm einmalig aus der veroeffentlichten Datei uebernehmen (Sessions + Speaker, vom Veranstalter bestaetigt)
  const evr = await db.prepare("SELECT id FROM events WHERE handle='m365con-2027'").first();
  if (evr && !(await db.prepare("SELECT 1 x FROM event_sessions WHERE event_id=? LIMIT 1").bind(evr.id).first())) {
    try {
      const pr = await (await fetch(`${env.SITE}/m365con_program.json`, { cf: { cacheTtl: 0 } })).json(), sp = pr.speakers || {};
      const pm = new Map(((await db.prepare("SELECT p.handle,lower(u.name) n FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.public=1 AND p.handle IS NOT NULL").all()).results || []).map((r) => [r.n, r.handle]));
      const addMin = (st, m) => { const d = new Date(st + ":00Z"); d.setUTCMinutes(d.getUTCMinutes() + (m || 45)); return d.toISOString().slice(0, 16); };
      const ops = (pr.sessions || []).slice(0, 400).map((x) => db.prepare("INSERT INTO event_sessions(event_id,title,abstract,start,end,room,track,level,lang,topics,speakers,recording_url,status,proposer_id,created) VALUES(?,?,?,?,?,'',?,'','en','[]',?,'','live',?,?)")
        .bind(evr.id, String(x.title).slice(0, 140), String(x.abstract || "").slice(0, 1500), x.start, addMin(x.start, x.duration), x.category === "keynote" ? "Keynote" : x.category === "closing" ? "Closing" : "Expert Session",
          JSON.stringify((x.speaker_ids || []).map((i) => sp[i]).filter(Boolean).map((p) => (pm.has(String(p.name).toLowerCase()) ? { h: pm.get(String(p.name).toLowerCase()), n: String(p.name).slice(0, 80), s: "invited" } : { n: String(p.name).slice(0, 80), s: "confirmed", o: 1 }))), owner.id, t));
      for (let i = 0; i < ops.length; i += 40) await db.batch(ops.slice(i, i + 40));
    } catch (e) { /* naechster Cron-Lauf versucht es erneut */ }
  }
  if (evr) {   // Verknuepfungs-Links: vom Veranstalter importierte Speaker (ohne Profil) bekommen ein Token, mit dem sie ihr Profil per Link verbinden koennen
    try {
      const rows = (await db.prepare("SELECT id,speakers FROM event_sessions WHERE event_id=? AND speakers LIKE '%\"o\":1%'").bind(evr.id).all()).results || [];
      const ops = [];
      for (const r of rows) {
        const sp = parse(r.speakers, []); let ch = false;
        for (const x of sp) if (x.o && !x.h && !x.t) { x.t = rndToken(); ch = true; ops.push(db.prepare("INSERT OR IGNORE INTO speaker_invites(token,event_id,session_id,name,eid,created) VALUES(?,?,?,?,?,?)").bind(x.t, evr.id, r.id, x.n, x.e || "", now())); }
        if (ch) ops.push(db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), r.id));
      }
      for (let i = 0; i < ops.length; i += 40) await db.batch(ops.slice(i, i + 40));
    } catch (e) { /* naechster Lauf */ }
  }
  if (evr) {   // Themen (Entitaeten) der Programm-Sessions nachtragen, solange eine Session noch keine hat
    try {
      {   // Themen-Abgleich: bei neuer Programm-Version (topics_version) werden fehlende Themen zu den bestehenden hinzugefuegt (Eintraege der Organisatoren bleiben)
        const pr2 = await (await fetch(`${env.SITE}/m365con_program.json`, { cf: { cacheTtl: 0 } })).json(), ver = String(pr2.topics_version || 1);
        const mk = await db.prepare("SELECT v FROM meta WHERE k='m365con_topics_v'").first();
        if ((mk?.v || "1") !== ver && (pr2.sessions || []).length) {
          const known2 = await baseIds(env);
          if (known2.has("microsoft-fabric-apps")) {   // erst wenn die neuen Entitaeten veroeffentlicht sind
            const cur = (await db.prepare("SELECT id,title,topics FROM event_sessions WHERE event_id=?").bind(evr.id).all()).results || [], byT = new Map(cur.map((r) => [r.title, r]));
            const ops2 = [];
            for (const x of pr2.sessions) {
              const r = byT.get(String(x.title).slice(0, 140)); if (!r) continue;
              let have = []; try { have = JSON.parse(r.topics || "[]"); } catch { have = []; }
              const merged = [...new Set([...have, ...(x.topics || []).filter((i) => known2.has(i))])].slice(0, 8);
              if (merged.length !== have.length) ops2.push(db.prepare("UPDATE event_sessions SET topics=? WHERE id=?").bind(JSON.stringify(merged), r.id));
            }
            for (let i = 0; i < ops2.length; i += 40) await db.batch(ops2.slice(i, i + 40));
            await db.prepare("INSERT INTO meta(k,v) VALUES('m365con_topics_v',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(ver).run();
          }
        }
      }
      const todo = await db.prepare("SELECT COUNT(*) n FROM event_sessions WHERE event_id=? AND topics='[]'").bind(evr.id).first();
      if (todo?.n) {
        const pr = await (await fetch(`${env.SITE}/m365con_program.json`, { cf: { cacheTtl: 0 } })).json(), known = await baseIds(env);
        const ops = (pr.sessions || []).filter((x) => (x.topics || []).length).map((x) => db.prepare("UPDATE event_sessions SET topics=? WHERE event_id=? AND title=? AND topics='[]'").bind(JSON.stringify(x.topics.filter((i) => known.has(i)).slice(0, 8)), evr.id, String(x.title).slice(0, 140)));
        for (let i = 0; i < ops.length; i += 40) await db.batch(ops.slice(i, i + 40));
      }
    } catch (e) { /* naechster Lauf */ }
  }
}


// Aehnlichkeit Vorname + Nachname (auch Initiale, kleine Tippfehler)
const norm = (t) => String(t || "").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9 ]+/g, " ").trim().split(/\s+/).filter(Boolean);
function lev(a, b) { const d = Array.from({ length: a.length + 1 }, (_, i) => [i]); for (let j = 1; j <= b.length; j++) d[0][j] = j; for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); return d[a.length][b.length]; }
export function similarName(a, b) {
  const x = norm(a), y = norm(b); if (x.length < 2 || y.length < 2) return false;
  const fx = x[0], fy = y[0], lx = x[x.length - 1], ly = y[y.length - 1];
  if (lev(fx, fy) > (Math.min(fx.length, fy.length) >= 5 ? 1 : 0)) return false;
  return lx === ly || (lx.length === 1 && ly[0] === lx) || (ly.length === 1 && lx[0] === ly) || (Math.min(lx.length, ly.length) >= 5 && lev(lx, ly) <= 1);
}
async function speakerMatches(db, me) {
  const rows = (await db.prepare("SELECT s.speakers,e.title ev FROM event_sessions s JOIN events e ON e.id=s.event_id WHERE s.speakers LIKE '%\"n\":%' AND e.public=1 LIMIT 3000").all()).results || [], by = new Map();
  for (const r of rows) { let sp = []; try { sp = JSON.parse(r.speakers); } catch { continue; } for (const x of sp) if (x.n && !x.h && similarName(me.name, x.n)) { const o = by.get(x.n) || { name: x.n, sessions: 0, events: new Set() }; o.sessions++; o.events.add(r.ev); by.set(x.n, o); } }
  return [...by.values()].map((o) => ({ name: o.name, sessions: o.sessions, events: [...o.events].slice(0, 4) }));
}
export async function handleEvents(env, request, url, path, user, J) {
  const db = env.DB, method = request.method; let m;
  const need = () => (user ? null : J({ error: "login" }, 401));
  const body = async () => await request.json().catch(() => ({}));

  if (path === "/api/events/seed-m365con" && method === "POST") {   // Admin: M365Con 2027 als Event anlegen (zunaechst nicht oeffentlich, Daten spaeter im Organizer-Bereich pflegen)
    if (!user?.admin) return J({ error: "forbidden" }, 403);
    const ex = await db.prepare("SELECT id FROM events WHERE handle='m365con-2027'").first();
    if (ex) { await db.prepare("UPDATE events SET owner_id=?, public=1 WHERE id=?").bind(user.id, ex.id).run(); return J({ ok: true, existed: true, handle: "m365con-2027" }); }
    const b = await body(), t = Math.floor(Date.now() / 1000);
    await db.prepare("INSERT INTO events(handle,owner_id,title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,created,updated) VALUES('m365con-2027',?,?,?,?,?,?,'online','Online','',?,?,1,'en','[\"m365con\"]',1,1,?,?)")
      .bind(user.id, "M365Con 2027", "Free online convention: 10 days, 120+ sessions, 120+ speakers, a daily focus topic.", "M365Con 2027 is a free online convention about Microsoft 365, Copilot and AI with 10 days of sessions, a daily focus topic and 120+ speakers.", String(b.start || "2027-01-11T08:00").slice(0, 16), String(b.end || "2027-01-22").slice(0, 16), "https://m365con.net", "https://m365con.net", t, t).run();
    return J({ ok: true, handle: "m365con-2027", public: false });
  }
  if (path === "/api/events/export" && method === "GET") {
    const evs = (await db.prepare("SELECT * FROM events WHERE public=1 ORDER BY start DESC LIMIT 300").all()).results || [];
    const out = []; for (const e of evs) out.push(await evView(db, e, false));
    return J({ events: out }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/events/mine" && method === "GET") {
    if (need()) return need();
    const evs = (await db.prepare("SELECT e.* FROM events e WHERE e.owner_id=?1 OR e.id IN (SELECT event_id FROM event_roles WHERE user_id=?1) OR e.org_id IN (SELECT org_id FROM org_members WHERE user_id=?1 AND status='active' AND role IN ('owner','admin','events')) ORDER BY e.start DESC").bind(user.id).all()).results || [];
    const out = []; for (const e of evs) out.push(await evView(db, e, true));
    const orgs = (await db.prepare("SELECT o.handle,o.name FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=? AND m.status='active' AND m.role IN ('owner','admin','events')").bind(user.id).all()).results || [];
    return J({ events: out, orgs });
  }
  if (path === "/api/event" && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `event:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body(), handle = String(b.handle || "").toLowerCase().trim();
    if (!HANDLE.test(handle)) return J({ error: "bad_handle" }, 400);
    const title = txt(b.title, 120); if (title.length < 3) return J({ error: "bad_title" }, 400);
    if (!okDate(String(b.start || ""))) return J({ error: "bad_date" }, 400);
    const end = String(b.end || ""); if (end && (!okDate(end) || end < b.start)) return J({ error: "bad_date" }, 400);
    const mode = MODES.includes(b.mode) ? b.mode : "online";
    const eu = cleanUrl(b.url, null), tu = cleanUrl(b.tickets_url, null); if (eu === null || tu === null) return J({ error: "bad_url" }, 400);
    const tp = await topics(env, b.topics); if (!tp) return J({ error: "bad_topic" }, 400);
    let orgId = null;
    if (b.org) {
      const o = await db.prepare("SELECT o.id FROM orgs o JOIN org_members m ON m.org_id=o.id WHERE o.handle=? AND m.user_id=? AND m.status='active' AND m.role IN ('owner','admin','events')").bind(String(b.org), user.id).first();
      if (!o) return J({ error: "forbidden" }, 403); orgId = o.id;
    }
    const ex = await db.prepare("SELECT * FROM events WHERE handle=?").bind(handle).first();
    if (ex && !(await canManage(db, user, ex))) return J({ error: "handle_taken" }, 409);
    const vals = [title, txt(b.summary, 200), long(b.about, 3000), b.start, end, mode, txt(b.location, 120), txt(b.country, 60), eu, tu, b.free === false ? 0 : 1, txt(b.lang, 10), JSON.stringify(tp), b.seeking_sponsor ? 1 : 0, b.public === false ? 0 : 1, now()];
    if (ex) await db.prepare("UPDATE events SET title=?,summary=?,about=?,start=?,end=?,mode=?,location=?,country=?,url=?,tickets_url=?,free=?,lang=?,topics=?,seeking_sponsor=?,public=?,updated=?,org_id=? WHERE id=?").bind(...vals, b.org === undefined ? ex.org_id : orgId, ex.id).run();
    else await db.prepare("INSERT INTO events(title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,updated,handle,owner_id,org_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(...vals, handle, user.id, orgId, now()).run();
    if (b.public !== false) await ownedEntity(env, user, { eid: handle, type: "event", name: title, en: `${title} is an event in the Microsoft community, starting ${b.start}.`, de: `${title} ist eine Veranstaltung der Microsoft-Community, Beginn ${b.start}.`, web: String(b.url || "").startsWith("https://") ? b.url : "" });
    return J({ ok: true });
  }
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})$/)) && method === "DELETE") {
    if (need()) return need();
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first();
    if (!(await canManage(db, user, ev, "delete"))) return J({ error: "forbidden" }, 403);
    await db.batch([db.prepare("DELETE FROM event_roles WHERE event_id=?").bind(ev.id), db.prepare("DELETE FROM event_partners WHERE event_id=?").bind(ev.id), db.prepare("DELETE FROM event_attendees WHERE event_id=?").bind(ev.id), db.prepare("DELETE FROM event_settings WHERE event_id=?").bind(ev.id), db.prepare("DELETE FROM event_sessions WHERE event_id=?").bind(ev.id), db.prepare("DELETE FROM events WHERE id=?").bind(ev.id)]);
    return J({ ok: true });
  }
  // Session anlegen/aendern: Veranstalter -> sofort live; andere Mitglieder -> Vorschlag (pending)
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/session$/)) && method === "POST") {
    if (need()) return need();
    if (!(await rateLimit(db, `sess:${user.id}`, 40, 3600))) return J({ error: "rate_limit" }, 429);
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev) return J({ error: "not_found" }, 404);
    const mgr = await canManage(db, user, ev, "sessions"), b = await body();
    const title = txt(b.title, 140); if (title.length < 3) return J({ error: "bad_title" }, 400);
    const st = String(b.start || ""), en = String(b.end || "");
    if ((st && !okDate(st)) || (en && !okDate(en))) return J({ error: "bad_date" }, 400);
    const tp = await topics(env, b.topics); if (!tp) return J({ error: "bad_topic" }, 400);
    const myH = (await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(user.id).first())?.handle || "";
    let prevSp = []; if (b.id) { const ps = await db.prepare("SELECT speakers FROM event_sessions WHERE id=? AND event_id=?").bind(+b.id, ev.id).first(); prevSp = parse(ps?.speakers, []); }
    const sp = await speakersCheck(db, b.speakers, prevSp, myH); if (!sp) return J({ error: "bad_speaker" }, 400);
    const ru = cleanUrl(b.recording_url, null); if (ru === null) return J({ error: "bad_url" }, 400);
    const level = LEVELS.includes(String(b.level || "")) ? String(b.level || "") : "";
    const f = [title, long(b.abstract, 1500), st, en, txt(b.room, 60), txt(b.track, 60), level, txt(b.lang, 10), JSON.stringify(tp), JSON.stringify(sp), ru];
    if (b.id) {
      const s = await db.prepare("SELECT * FROM event_sessions WHERE id=? AND event_id=?").bind(+b.id, ev.id).first(); if (!s) return J({ error: "not_found" }, 404);
      if (!mgr && !(s.proposer_id === user.id && s.status === "pending")) {
        if (!(myH && parse(s.speakers, []).some((x) => x.h === myH && x.s === "confirmed"))) return J({ error: "forbidden" }, 403);
        await db.prepare("UPDATE event_sessions SET abstract=?,recording_url=? WHERE id=?").bind(f[1], ru, s.id).run();   // bestaetigte Speaker pflegen nur Beschreibung und Aufzeichnung
        return J({ ok: true, limited: true });
      }
      await db.prepare("UPDATE event_sessions SET title=?,abstract=?,start=?,end=?,room=?,track=?,level=?,lang=?,topics=?,speakers=?,recording_url=? WHERE id=?").bind(...f, s.id).run();
      await saveInvites(db, ev.id, s.id, sp);
      return J({ ok: true });
    }
    if ((await db.prepare("SELECT COUNT(*) n FROM event_sessions WHERE event_id=?").bind(ev.id).first()).n >= 300) return J({ error: "limit" }, 400);
    await db.prepare("INSERT INTO event_sessions(title,abstract,start,end,room,track,level,lang,topics,speakers,recording_url,event_id,status,proposer_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(...f, ev.id, mgr ? "live" : "pending", user.id, now()).run();
    const nid = (await db.prepare("SELECT last_insert_rowid() id").first()).id; await saveInvites(db, ev.id, nid, sp);
    return J({ ok: true, status: mgr ? "live" : "pending" });
  }
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/session\/(\d+)(\/approve)?$/))) {
    if (need()) return need();
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev) return J({ error: "not_found" }, 404);
    const s = await db.prepare("SELECT * FROM event_sessions WHERE id=? AND event_id=?").bind(+m[2], ev.id).first(); if (!s) return J({ error: "not_found" }, 404);
    const mgr = await canManage(db, user, ev, "sessions");
    if (m[3] && method === "POST") {
      if (!mgr) return J({ error: "forbidden" }, 403);
      const b = await body();
      if (b.ok === false) await db.prepare("DELETE FROM event_sessions WHERE id=?").bind(s.id).run(); else await db.prepare("UPDATE event_sessions SET status='live' WHERE id=?").bind(s.id).run();
      return J({ ok: true });
    }
    if (!m[3] && method === "DELETE") {
      if (!mgr && s.proposer_id !== user.id) return J({ error: "forbidden" }, 403);
      await db.prepare("DELETE FROM event_sessions WHERE id=?").bind(s.id).run(); return J({ ok: true });
    }
  }
  // ---- Teilnehmer: anmelden (Warteliste bei vollem Event), Sichtbarkeit selbst bestimmen, abmelden ----
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/(attendees|register|capacity|invite-mail)$/))) {
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev || (!ev.public && !(await canManage(db, user, ev, "edit")))) return J({ error: "not_found" }, 404);
    const cap = (await db.prepare("SELECT capacity FROM event_settings WHERE event_id=?").bind(ev.id).first())?.capacity || 0;
    if (m[2] === "attendees" && method === "GET") {
      const going = (await db.prepare("SELECT COUNT(*) n FROM event_attendees WHERE event_id=? AND status='going'").bind(ev.id).first()).n;
      const wl = (await db.prepare("SELECT COUNT(*) n FROM event_attendees WHERE event_id=? AND status='waitlist'").bind(ev.id).first()).n;
      const vis = (await db.prepare("SELECT u.name,p.handle FROM event_attendees a JOIN users u ON u.id=a.user_id JOIN profiles p ON p.user_id=u.id AND p.public=1 WHERE a.event_id=? AND a.status='going' AND a.visible=1 ORDER BY a.created LIMIT 200").bind(ev.id).all()).results || [];
      const me = user ? await db.prepare("SELECT status,visible FROM event_attendees WHERE event_id=? AND user_id=?").bind(ev.id, user.id).first() : null;
      return J({ transfer: !!TRANSFER[ev.handle], going, waitlist: wl, capacity: cap, full: cap > 0 && going >= cap, visible: vis.map((r) => ({ name: r.name, handle: r.handle })), me: me ? { status: me.status, visible: !!me.visible } : null, can_edit: user ? await canManage(db, user, ev, "edit") : false }, 200, { "cache-control": "no-store" });
    }
    if (need()) return need();
    if (m[2] === "register" && method === "POST") {
      if (!(await rateLimit(db, `reg:${user.id}`, 40, 3600))) return J({ error: "rate_limit" }, 429);
      const b = await body(), vis = b.visible ? 1 : 0;
      if (vis && !(await db.prepare("SELECT 1 x FROM profiles WHERE user_id=? AND public=1").bind(user.id).first())) return J({ error: "need_profile" }, 400);
      if (b.transfer && TRANSFER[ev.handle]) {   // Einwilligung: Name und E-Mail werden einmalig an das Event-System (m365con.net) weitergegeben
        const em = String(b.email || "").trim().toLowerCase();
        if (!/^[^\s@<>]{1,64}@[^\s@<>]{1,120}\.[a-z]{2,}$/i.test(em)) return J({ error: "bad_email" }, 400);
        await db.prepare("INSERT INTO event_transfers(event_id,user_id,target,name,email,status,created) VALUES(?,?,?,?,?,'pending',?) ON CONFLICT(event_id,user_id) DO UPDATE SET email=excluded.email,name=excluded.name,status=CASE WHEN event_transfers.status='done' THEN 'done' ELSE 'pending' END").bind(ev.id, user.id, TRANSFER[ev.handle], txt(user.name, 80), em, now()).run();
      }
      const cur = await db.prepare("SELECT status FROM event_attendees WHERE event_id=? AND user_id=?").bind(ev.id, user.id).first();
      if (cur) { await db.prepare("UPDATE event_attendees SET visible=? WHERE event_id=? AND user_id=?").bind(vis, ev.id, user.id).run(); return J({ ok: true, status: cur.status }); }
      const going = (await db.prepare("SELECT COUNT(*) n FROM event_attendees WHERE event_id=? AND status='going'").bind(ev.id).first()).n;
      const st = cap > 0 && going >= cap ? "waitlist" : "going";
      await db.prepare("INSERT INTO event_attendees(event_id,user_id,status,visible,created) VALUES(?,?,?,?,?)").bind(ev.id, user.id, st, vis, now()).run();
      return J({ ok: true, status: st });
    }
    if (m[2] === "register" && method === "DELETE") {
      await db.batch([db.prepare("DELETE FROM event_attendees WHERE event_id=? AND user_id=?").bind(ev.id, user.id), db.prepare("DELETE FROM event_transfers WHERE event_id=? AND user_id=? AND status='pending'").bind(ev.id, user.id)]); await promoteWaitlist(db, ev.id, cap);
      return J({ ok: true });
    }
    if (m[2] === "capacity" && method === "POST") {
      if (!(await canManage(db, user, ev, "edit"))) return J({ error: "forbidden" }, 403);
      const n = Math.max(0, Math.min(100000, parseInt((await body()).capacity, 10) || 0));
      await db.prepare("INSERT INTO event_settings(event_id,capacity) VALUES(?,?) ON CONFLICT(event_id) DO UPDATE SET capacity=excluded.capacity").bind(ev.id, n).run(); await promoteWaitlist(db, ev.id, n);
      return J({ ok: true, capacity: n });
    }
    if (m[2] === "invite-mail" && method === "POST") {   // Einladung an Personen ohne Konto; Adresse wird nicht gespeichert
      if (!(await canManage(db, user, ev, "edit"))) return J({ error: "forbidden" }, 403);
      if (!(await rateLimit(db, `evmail:${user.id}`, 30, 3600))) return J({ error: "rate_limit" }, 429);
      const email = String((await body()).email || "").trim().toLowerCase();
      if (!/^[^\s@<>]{1,64}@[^\s@<>]{1,120}\.[a-z]{2,}$/i.test(email)) return J({ error: "bad_email" }, 400);
      if (!env.RESEND_API_KEY) return J({ error: "mail_off" }, 503);
      const esc = (x) => String(x).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])), u = `${env.SITE}/community/events/${ev.handle}/`;
      const r = await sendMail(env, email, `Invitation: ${ev.title}`, `<p>Hello,</p><p>${esc(user.name)} invites you to <b>${esc(ev.title)}</b> (${esc(ev.start)}).</p><p><a href="${u}">View the event and register</a> (sign-in required, free).</p><p>M365.FM</p>`);
      return r.ok ? J({ ok: true }) : J({ error: "send_failed" }, 502);
    }
  }
  // ---- Partner: Sponsoren und Medienpartner, Bestaetigung durch die Gegenseite (Firma oder Event-Team) ----
  if (path === "/api/events/my-registrations" && method === "GET") {   // Meine Anmeldungen: Status, Sichtbarkeit, Weitergabe
    if (need()) return need();
    const rows = (await db.prepare("SELECT e.handle,e.title,e.start,e.end,a.status,a.visible,(SELECT t.status FROM event_transfers t WHERE t.event_id=e.id AND t.user_id=a.user_id) tr FROM event_attendees a JOIN events e ON e.id=a.event_id WHERE a.user_id=? AND e.public=1 ORDER BY e.start DESC LIMIT 100").bind(user.id).all()).results || [];
    return J({ items: rows.map((r) => ({ handle: r.handle, title: r.title, start: r.start, end: r.end, status: r.status, visible: !!r.visible, transfer: r.tr || "" })) }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/events/partners-mine" && method === "GET") {
    if (need()) return need();
    const toOrg = (await db.prepare("SELECT e.handle eh,e.title,o.handle oh,o.name,p.kind,p.level FROM event_partners p JOIN events e ON e.id=p.event_id JOIN orgs o ON o.id=p.org_id JOIN org_members m ON m.org_id=o.id WHERE p.status='pending' AND p.by='e' AND m.user_id=? AND m.status='active' AND m.role IN ('owner','admin','events')").bind(user.id).all()).results || [];
    const toTeam = (await db.prepare("SELECT e.handle eh,e.title,o.handle oh,o.name,p.kind,p.level FROM event_partners p JOIN events e ON e.id=p.event_id JOIN orgs o ON o.id=p.org_id WHERE p.status='pending' AND p.by='o' AND (e.owner_id=?1 OR e.id IN (SELECT event_id FROM event_roles WHERE user_id=?1 AND role IN ('organisator','co-organisator','sponsor-manager')) OR e.org_id IN (SELECT org_id FROM org_members WHERE user_id=?1 AND status='active' AND role IN ('owner','admin','events')))").bind(user.id).all()).results || [];
    return J({ to_confirm_as_company: toOrg, to_confirm_as_team: toTeam });
  }
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/partners$/))) {
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev || !ev.public) return J({ error: "not_found" }, 404);
    if (method === "GET") {
      const rows = (await db.prepare("SELECT p.kind,p.level,p.status,p.by,o.handle,o.name,o.public FROM event_partners p JOIN orgs o ON o.id=p.org_id WHERE p.event_id=? ORDER BY p.created").bind(ev.id).all()).results || [];
      const team = user ? await canManage(db, user, ev, "sponsor") : false;
      return J({ partners: rows.filter((r) => r.status === "confirmed" || team).map((r) => ({ kind: r.kind, level: r.level, status: r.status, by: team ? r.by : undefined, name: r.name, handle: r.public ? r.handle : "", org: team ? r.handle : undefined })) });
    }
    if (need()) return need();
    if (!(await rateLimit(db, `partner:${user.id}`, 40, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body(), act = method === "DELETE" ? "remove" : b.action === "accept" || b.action === "decline" ? b.action : "propose";
    const r = await partnerAction(db, user, ev, b.org, b.kind, b.level, act);
    return J(r, r.error ? (r.error === "forbidden" ? 403 : r.error === "not_found" ? 404 : 400) : 200);
  }
  // ---- Event-Team: Rollen vergeben (Organisator, Co-Organisator, Programm-, Sponsoren-Manager, Kommunikation, Helfer) ----
  if ((m = path.match(/^\/api\/event\/([a-z0-9-]{3,40})\/team$/))) {
    const ev = await db.prepare("SELECT * FROM events WHERE handle=?").bind(m[1]).first(); if (!ev) return J({ error: "not_found" }, 404);
    if (method === "GET") {
      const rows = (await db.prepare("SELECT r.role,r.user_id,u.name,p.handle FROM event_roles r JOIN users u ON u.id=r.user_id LEFT JOIN profiles p ON p.user_id=u.id AND p.public=1 WHERE r.event_id=? ORDER BY r.created").bind(ev.id).all()).results || [];
      const mine = need() ? false : await canManage(db, user, ev, "roles");
      return J({ roles: Object.keys(EVENT_ROLES), team: rows.filter((r) => mine || r.handle).map((r) => ({ role: r.role, name: r.name, handle: r.handle || "", ...(mine ? { uid: r.user_id } : {}) })), can_edit: mine });
    }
    if (need()) return need();
    if (!(await canManage(db, user, ev, "roles"))) return J({ error: "forbidden" }, 403);
    const b = await body();
    const role = String(b.role || ""); if (!(role in EVENT_ROLES)) return J({ error: "bad_role" }, 400);
    const isOrganiser = ev.owner_id === user.id || user.admin || (await canManage(db, user, ev, "delete"));
    if (method === "POST") {
      if (role === "organisator" && !isOrganiser) return J({ error: "forbidden" }, 403);
      const pr = await db.prepare("SELECT user_id FROM profiles WHERE handle=? AND public=1").bind(String(b.handle || "").toLowerCase()).first(); if (!pr) return J({ error: "not_found" }, 404);
      if ((await db.prepare("SELECT COUNT(*) n FROM event_roles WHERE event_id=?").bind(ev.id).first()).n >= 40) return J({ error: "limit" }, 400);
      await db.prepare("INSERT INTO event_roles(event_id,user_id,role,added_by,created) VALUES(?,?,?,?,?) ON CONFLICT(event_id,user_id) DO UPDATE SET role=excluded.role").bind(ev.id, pr.user_id, role, user.id, now()).run();
      return J({ ok: true });
    }
    if (method === "DELETE") {
      const pr = await db.prepare("SELECT user_id FROM profiles WHERE handle=?").bind(String(b.handle || "").toLowerCase()).first(); if (!pr) return J({ error: "not_found" }, 404);
      const cur = await db.prepare("SELECT role FROM event_roles WHERE event_id=? AND user_id=?").bind(ev.id, pr.user_id).first();
      if (cur?.role === "organisator" && !isOrganiser) return J({ error: "forbidden" }, 403);
      await db.prepare("DELETE FROM event_roles WHERE event_id=? AND user_id=?").bind(ev.id, pr.user_id).run(); return J({ ok: true });
    }
  }
  // ---- Speaker: Einladung ansehen/bestaetigen, Anfragen an bestehende Mitglieder ----
  if (path === "/api/speaker/invite-send" && method === "POST") {   // Veranstalter laden einen Speaker per E-Mail ein (Adresse wird nicht gespeichert)
    if (need()) return need();
    if (!(await rateLimit(db, `invmail:${user.id}`, 20, 3600))) return J({ error: "rate_limit" }, 429);
    const b = await body(), email = String(b.email || "").trim().toLowerCase();
    if (!/^[^\s@<>]{1,64}@[^\s@<>]{1,120}\.[a-z]{2,}$/i.test(email)) return J({ error: "bad_email" }, 400);
    const i = await db.prepare("SELECT i.token,i.name,s.title st,e.* FROM speaker_invites i JOIN event_sessions s ON s.id=i.session_id JOIN events e ON e.id=i.event_id WHERE i.token=?").bind(String(b.token || "")).first();
    if (!i || !(await canManage(db, user, i, "sessions"))) return J({ error: "forbidden" }, 403);
    if (!env.RESEND_API_KEY) return J({ error: "mail_off" }, 503);
    const esc = (x) => String(x).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])), url = `${env.SITE}/community/?invite=${i.token}#c-events`;
    const r = await sendMail(env, email, `Speaker invitation: ${i.title}`, `<p>Hello ${esc(i.name)},</p><p>${esc(user.name)} invites you to speak at <b>${esc(i.title)}</b> (${esc(i.start)}) with the session <b>${esc(i.st)}</b>.</p><p><a href="${url}">Confirm your participation</a> (sign-in required, free).</p><p>M365.FM</p>`);
    return r.ok ? J({ ok: true }) : J({ error: "send_failed" }, 502);
  }
  if (path === "/api/speaker/suggest" && method === "GET") {   // "Bist du das?": ungebundene Speaker mit aehnlichem Namen wie das eigene Profil
    if (need()) return need();
    const me = await db.prepare("SELECT p.handle,u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=? AND p.public=1 AND p.handle IS NOT NULL").bind(user.id).first();
    if (!me) return J({ suggestions: [] });
    return J({ suggestions: await speakerMatches(db, me) });
  }
  if (path === "/api/speaker/claim" && method === "POST") {   // Nutzer bestaetigt: "das bin ich" -> Eintrag wird mit dem Profil verknuepft (Speaker-Anfrage, bestaetigt der Nutzer selbst)
    if (need()) return need();
    const b = await body(), me = await db.prepare("SELECT p.handle,u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=? AND p.public=1 AND p.handle IS NOT NULL").bind(user.id).first();
    if (!me) return J({ error: "need_profile" }, 400);
    const ok = (await speakerMatches(db, me)).find((x) => x.name === String(b.name || "")); if (!ok) return J({ error: "not_found" }, 404);
    let n = 0, ops = [];
    for (const r of (await db.prepare("SELECT id,speakers FROM event_sessions WHERE speakers LIKE ?").bind(`%"n":${JSON.stringify(ok.name).slice(0, -1)}"%`).all()).results || []) {
      let sp = []; try { sp = JSON.parse(r.speakers); } catch { continue; } let ch = false;
      for (const x of sp) if (x.n === ok.name && !x.h) { if (x.t) ops.push(db.prepare("DELETE FROM speaker_invites WHERE token=?").bind(x.t)); delete x.t; delete x.o; x.h = me.handle; x.s = "invited"; ch = true; n++; }
      if (ch) ops.push(db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), r.id));
    }
    if (ops.length) await db.batch(ops);
    return J({ ok: true, linked: n });
  }
  if ((m = path.match(/^\/api\/speaker\/invite\/([a-f0-9]{36})$/)) && method === "GET") {
    const i = await db.prepare("SELECT i.name,i.eid,s.title,e.title ev,e.handle FROM speaker_invites i JOIN event_sessions s ON s.id=i.session_id JOIN events e ON e.id=i.event_id WHERE i.token=?").bind(m[1]).first();
    return i ? J({ invite: i }) : J({ error: "not_found" }, 404);
  }
  if (path === "/api/speaker/confirm" && method === "POST") {
    if (need()) return need();
    const b = await body(), tok = String(b.token || "");
    const i = await db.prepare("SELECT * FROM speaker_invites WHERE token=?").bind(tok).first(); if (!i) return J({ error: "not_found" }, 404);
    const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(user.id).first();
    const se = await db.prepare("SELECT id,speakers FROM event_sessions WHERE id=?").bind(i.session_id).first();
    let sp = parse(se?.speakers, []);
    if (b.decline) { sp = sp.map((x) => (x.t === tok ? { ...x, s: "declined" } : x)); await db.batch([db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), se.id), db.prepare("DELETE FROM speaker_invites WHERE token=?").bind(tok)]); return J({ ok: true, declined: true }); }
    if (!pr) return J({ error: "need_profile" }, 409);
    sp = sp.map((x) => (x.t === tok ? { h: pr.handle, n: x.n, e: x.e || pr.handle, s: "confirmed" } : x));   // e = eigene Personen-Entitaet (Profil-Adresse), falls keine andere hinterlegt ist
    await db.batch([db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), se.id), db.prepare("DELETE FROM speaker_invites WHERE token=?").bind(tok)]);
    let claimed = false; if (i.eid) claimed = await claimEntity(db, i.eid, user.id, "invite");
    return J({ ok: true, handle: pr.handle, claimed });
  }
  if (path === "/api/speaker/requests" && method === "GET") {
    if (need()) return need();
    const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(user.id).first(); if (!pr?.handle) return J({ items: [] });
    const rows = (await db.prepare("SELECT s.id,s.title,e.title ev,e.handle eh,s.speakers FROM event_sessions s JOIN events e ON e.id=s.event_id WHERE s.speakers LIKE ?").bind(`%"h":"${pr.handle}"%`).all()).results || [];
    return J({ items: rows.filter((r) => parse(r.speakers, []).some((x) => x.h === pr.handle && x.s === "invited")).map((r) => ({ id: r.id, title: r.title, event: r.ev, eh: r.eh })) });
  }
  if (path === "/api/speaker/respond" && method === "POST") {
    if (need()) return need();
    const b = await body(), pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=?").bind(user.id).first(); if (!pr?.handle) return J({ error: "need_profile" }, 409);
    const se = await db.prepare("SELECT id,speakers FROM event_sessions WHERE id=?").bind(+b.id).first(); if (!se) return J({ error: "not_found" }, 404);
    const sp = parse(se.speakers, []).map((x) => (x.h === pr.handle ? { ...x, s: b.ok ? "confirmed" : "declined" } : x));
    await db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), se.id).run();
    return J({ ok: true });
  }
  // ---- Entitaet uebernehmen ----
  if (path === "/api/entity/suggest" && method === "GET") {   // "Gehoert diese Seite zu dir?": Personen- und Firmen-Entitaeten mit aehnlichem Namen, noch ohne Besitzer
    if (need()) return need();
    const me = await db.prepare("SELECT p.handle,u.name FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=? AND p.public=1").bind(user.id).first();
    const orgs = (await db.prepare("SELECT o.handle,o.name,(SELECT eid FROM org_entity WHERE org_id=o.id) eid FROM org_members m JOIN orgs o ON o.id=m.org_id WHERE m.user_id=? AND m.status='active' AND m.role IN ('owner','admin')").bind(user.id).all()).results || [];
    if (!me && !orgs.length) return J({ suggestions: [] });
    const claimed = new Set(((await db.prepare("SELECT eid FROM entity_claims").all()).results || []).map((r) => r.eid));
    const out = [], seen = new Set(), map = await entityMap(env);
    const sameOrg = (a, b) => { const x = norm(a).join(""), y = norm(b).join(""); return x.length >= 4 && y.length >= 4 && (x === y || lev(x, y) <= (x.length >= 8 ? 2 : 1) || x.startsWith(y) || y.startsWith(x)); };
    for (const [eid, e] of map) {
      if (claimed.has(eid) || seen.has(eid)) continue;
      const names = [e.name, ...(e.aliases || [])];
      if (me && e.type === "person" && names.some((n) => similarName(me.name, n))) { seen.add(eid); out.push({ eid, name: e.name, type: "person" }); continue; }
      if (e.type === "org") for (const o of orgs) if (o.eid !== eid && names.some((n) => sameOrg(o.name, n))) { seen.add(eid); out.push({ eid, name: e.name, type: "org", org: o.name }); break; }
    }
    return J({ suggestions: out.slice(0, 8) });
  }
  if (path === "/api/entity/claim" && method === "POST") {
    if (need()) return need();
    const b = await body(), eid = String(b.eid || "").toLowerCase();
    if (!EID.test(eid)) return J({ error: "bad_id" }, 400);
    const pr = await db.prepare("SELECT handle FROM profiles WHERE user_id=? AND public=1").bind(user.id).first(); if (!pr) return J({ error: "need_profile" }, 409);
    if (!(await rateLimit(db, `claim:${user.id}`, 5, 86400))) return J({ error: "rate_limit" }, 429);
    const ok = await claimEntity(db, eid, user.id, "manual"); return ok ? J({ ok: true }) : J({ error: "claimed" }, 409);
  }
  if (path === "/api/entity/claims" && method === "GET") {
    const rows = (await db.prepare("SELECT c.eid,p.handle FROM entity_claims c JOIN profiles p ON p.user_id=c.user_id AND p.public=1 WHERE c.status='verified'").all()).results || [];
    return J({ claims: rows }, 200, { "cache-control": "public, max-age=300" });
  }
  if (path === "/api/entity/claim/mine" && method === "GET") {
    if (need()) return need();
    return J({ claims: (await db.prepare("SELECT eid,status FROM entity_claims WHERE user_id=?").bind(user.id).all()).results || [] });
  }
  if (path === "/api/admin/entity/claims" && method === "GET") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    return J({ claims: (await db.prepare("SELECT c.eid,c.user_id,u.name,p.handle FROM entity_claims c JOIN users u ON u.id=c.user_id LEFT JOIN profiles p ON p.user_id=c.user_id WHERE c.status='pending'").all()).results || [] });
  }
  if (path === "/api/admin/entity/claim" && method === "POST") {
    if (!(user?.admin || user?.editor)) return J({ error: "forbidden" }, 403);
    const b = await body(); if (b.ok) await db.prepare("UPDATE entity_claims SET status='verified' WHERE eid=?").bind(String(b.eid)).run(); else await db.prepare("DELETE FROM entity_claims WHERE eid=?").bind(String(b.eid)).run();
    return J({ ok: true });
  }

  // Sponsoren (Firmen mit aktivem Gesuch) sehen Events, die Sponsoren suchen
  if (path === "/api/events/for-sponsors" && method === "GET") {
    if (need()) return need();
    const o = (await db.prepare("SELECT s.criteria FROM org_sponsor s JOIN org_members m ON m.org_id=s.org_id WHERE s.open=1 AND m.user_id=? AND m.status='active' AND m.role IN ('owner','admin','events')").bind(user.id).all()).results || [];
    if (!o.length) return J({ error: "forbidden" }, 403);
    const crits = o.map((r) => parse(r.criteria, {}));
    const today = new Date().toISOString().slice(0, 10);
    const evs = (await db.prepare("SELECT * FROM events WHERE seeking_sponsor=1 AND public=1 AND (CASE WHEN end<>'' THEN end ELSE start END)>=? ORDER BY start LIMIT 100").bind(today).all()).results || [];
    const out = []; for (const e of evs) { const v = await evView(db, e, false); delete v.sessions; v.match = crits.some((c) => !c.format || c.format === e.mode); out.push(v); }
    return J({ events: out });
  }
  // Veranstalter fragen Firmen an (2 Wunschfirmen je Event frei, weitere kosten Punkte); Nachricht landet im Postfach der Firma
  if (path === "/api/events/ask-sponsor" && method === "POST") {
    if (need()) return need();
    const b = await body(), ev = await db.prepare("SELECT * FROM events WHERE handle=? AND seeking_sponsor=1").bind(String(b.event || "")).first();
    if (!ev || !(await canManage(db, user, ev, "sponsor"))) return J({ error: "forbidden" }, 403);
    const org = await db.prepare("SELECT o.id FROM org_sponsor s JOIN orgs o ON o.id=s.org_id WHERE s.open=1 AND o.handle=?").bind(String(b.org || "")).first(); if (!org) return J({ error: "not_found" }, 404);
    const tx = txt(b.body, 1000); if (tx.length < 10) return J({ error: "too_short" }, 400);
    if (await db.prepare("SELECT 1 x FROM sponsor_asks WHERE event_id=? AND org_id=?").bind(ev.id, org.id).first()) return J({ error: "already" }, 409);
    const used = (await db.prepare("SELECT COUNT(*) n FROM sponsor_asks WHERE event_id=?").bind(ev.id).first()).n;
    let paid = false;
    if (used >= FREE_ASKS) { const st = await stats(db, user.id); if (st.balance < ASK_COST) return J({ error: "need_points", cost: ASK_COST, balance: st.balance }, 402); paid = true; }
    const to = (await db.prepare("SELECT user_id FROM org_members WHERE org_id=? AND role='owner' AND status='active' LIMIT 1").bind(org.id).first())?.user_id; if (!to || to === user.id) return J({ error: "no_recipient" }, 400);
    const t0 = now(); let t = await db.prepare("SELECT * FROM msg_threads WHERE (a_id=?1 AND b_id=?2) OR (a_id=?2 AND b_id=?1)").bind(user.id, to).first();
    const ops = [];
    if (!t) { const r = await db.prepare("INSERT INTO msg_threads(a_id,b_id,ctx,created,last,a_read) VALUES(?,?,?,?,?,?)").bind(user.id, to, "sponsor:" + ev.handle, t0, t0, t0).run(); t = { id: r.meta.last_row_id, a_id: user.id }; }
    ops.push(db.prepare("INSERT INTO msg_messages(thread_id,from_id,body,created) VALUES(?,?,?,?)").bind(t.id, user.id, tx, t0), db.prepare(`UPDATE msg_threads SET last=?,${t.a_id === user.id ? "a_read" : "b_read"}=? WHERE id=?`).bind(t0, t0, t.id),
      db.prepare("INSERT INTO sponsor_asks(event_id,org_id,created) VALUES(?,?,?)").bind(ev.id, org.id, t0));
    if (paid) ops.push(db.prepare("INSERT INTO points_spent(user_id,item,cost,status,note,created) VALUES(?,?,?,?,?,?)").bind(user.id, "sponsor_ask", ASK_COST, "done", ev.handle, t0));
    await db.batch(ops);
    return J({ ok: true, free_left: Math.max(0, FREE_ASKS - used - 1), paid });
  }
  // Veranstalter sehen Firmen, die Sponsoring angeboten haben (nur wer ein Event mit "sucht Sponsoren" hat)
  if (path === "/api/events/sponsors" && method === "GET") {
    if (need()) return need();
    const mine = await db.prepare("SELECT 1 x FROM events WHERE seeking_sponsor=1 AND (owner_id=?1 OR org_id IN (SELECT org_id FROM org_members WHERE user_id=?1 AND status='active' AND role IN ('owner','admin','events'))) LIMIT 1").bind(user.id).first();
    if (!mine && !user.admin) return J({ error: "forbidden" }, 403);
    const rows = (await db.prepare("SELECT o.handle,o.name,o.public,o.website,s.criteria FROM org_sponsor s JOIN orgs o ON o.id=s.org_id WHERE s.open=1 ORDER BY s.updated DESC LIMIT 100").all()).results || [];
    return J({ free_asks: FREE_ASKS, ask_cost: ASK_COST, sponsors: rows.map((r) => ({ handle: r.handle, name: r.name, website: r.website, criteria: parse(r.criteria, {}) })) });
  }
  return null;
}

export async function deleteUserEvents(db, uid) {
  const evs = (await db.prepare("SELECT id FROM events WHERE owner_id=? AND org_id IS NULL").bind(uid).all()).results || [];
  const ops = [];
  for (const e of evs) ops.push(db.prepare("DELETE FROM event_roles WHERE event_id=?").bind(e.id), db.prepare("DELETE FROM event_partners WHERE event_id=?").bind(e.id), db.prepare("DELETE FROM event_attendees WHERE event_id=?").bind(e.id), db.prepare("DELETE FROM event_settings WHERE event_id=?").bind(e.id), db.prepare("DELETE FROM event_sessions WHERE event_id=?").bind(e.id), db.prepare("DELETE FROM events WHERE id=?").bind(e.id));
  ops.push(db.prepare("DELETE FROM event_sessions WHERE proposer_id=? AND status='pending'").bind(uid), db.prepare("DELETE FROM event_roles WHERE user_id=?").bind(uid), db.prepare("DELETE FROM event_attendees WHERE user_id=?").bind(uid), db.prepare("DELETE FROM event_transfers WHERE user_id=?").bind(uid));
  if (ops.length) await db.batch(ops);
}
