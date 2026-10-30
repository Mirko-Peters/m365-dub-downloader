// Vergangene M365Con-Events (2026 und DACH 2026) aus den veroeffentlichten Programm-Dateien als Events mit Sessions und Speakern anlegen
import { baseIds } from "./entities.js";

const EVENTS = [
  { handle: "m365con-2026", file: "m365con_program_2026.json", title: "M365Con 2026", lang: "en", url: "https://2026.m365con.net", start: "2026-01-12T08:00", end: "2026-01-23",
    summary: "The first M365Con: a free online convention for the Microsoft 365 community with keynotes, expert sessions and workshops.",
    about: "M365Con 2026 (also known as M365 Show Week) was the free online convention for Microsoft 365 professionals, held from 12 to 23 January 2026. Sessions went beyond the basics into tools, code and configuration for the modern workplace. This page keeps the full program and speakers as an archive." },
  { handle: "m365con-dach-2026", file: "m365con_program_dach.json", title: "M365Con DACH 2026", lang: "de", url: "https://de.m365con.net", start: "2026-09-14T08:00", end: "2026-09-18",
    summary: "Die Microsoft-365-Community-Convention für den DACH-Raum: fünf Tage online, deutschsprachig.",
    about: "Die M365Con DACH fand vom 14. bis 18. September 2026 online statt. Gleichgesinnte aus Deutschland, Österreich und der Schweiz teilten Wissen, lernten voneinander und vernetzten sich. Diese Seite hält Programm und Speaker als Archiv fest." },
];
const addMin = (st, m) => { const d = new Date(st + ":00Z"); d.setUTCMinutes(d.getUTCMinutes() + (m || 45)); return d.toISOString().slice(0, 16); };
const rndToken = () => [...crypto.getRandomValues(new Uint8Array(18))].map((b) => b.toString(16).padStart(2, "0")).join("");

export async function ensurePastEvents(env) {
  const db = env.DB, subs = (env.ADMIN_SUBS || "").split(",").map((x) => x.trim()).filter(Boolean);
  let owner = null;
  for (const a of subs) { const [pr, ...rest] = a.split(":"); owner = await db.prepare("SELECT id FROM users WHERE provider=? AND sub=?").bind(pr, rest.join(":")).first(); if (owner) break; }
  if (!owner) return;
  const t = Math.floor(Date.now() / 1000), org = await db.prepare("SELECT id FROM orgs WHERE handle='m365con'").first();
  for (const cfg of EVENTS) {
    try {
      let ev = await db.prepare("SELECT id FROM events WHERE handle=?").bind(cfg.handle).first();
      if (ev && (await db.prepare("SELECT 1 x FROM event_sessions WHERE event_id=? LIMIT 1").bind(ev.id).first())) continue;
      const r = await fetch(`${env.SITE}/${cfg.file}`, { cf: { cacheTtl: 0 } }); if (!r.ok) continue;
      const pr = await r.json(), sp = pr.speakers || {}; if (!(pr.sessions || []).length) continue;
      if (!ev) {
        await db.prepare("INSERT INTO events(handle,owner_id,org_id,title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,created,updated) VALUES(?,?,?,?,?,?,?,?,'online','Online','',?,'',1,?,'[\"m365con\"]',0,1,?,?)")
          .bind(cfg.handle, owner.id, org?.id || null, cfg.title, cfg.summary, cfg.about, cfg.start, cfg.end, cfg.url, cfg.lang, t, t).run();
        ev = await db.prepare("SELECT id FROM events WHERE handle=?").bind(cfg.handle).first();
      }
      const known = await baseIds(env);
      const pm = new Map(((await db.prepare("SELECT p.handle,lower(u.name) n FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.public=1 AND p.handle IS NOT NULL").all()).results || []).map((x) => [x.n, x.handle]));
      const ops = pr.sessions.slice(0, 400).map((x) => db.prepare("INSERT INTO event_sessions(event_id,title,abstract,start,end,room,track,level,lang,topics,speakers,recording_url,status,proposer_id,created) VALUES(?,?,?,?,?,'',?,'',?,?,?,?,'live',?,?)")
        .bind(ev.id, String(x.title).slice(0, 140), String(x.abstract || "").slice(0, 1500), x.start, addMin(x.start, x.duration),
          String(x.track || (x.category === "keynote" ? "Keynote" : x.category === "closing" ? "Closing" : x.category === "workshop" ? "Workshop" : "Expert Session")).slice(0, 60), cfg.lang,
          JSON.stringify((x.topics || []).filter((i) => known.has(i)).slice(0, 8)),
          JSON.stringify((x.speaker_ids || []).map((i) => sp[i]).filter(Boolean).map((p) => (pm.has(String(p.name).toLowerCase()) ? { h: pm.get(String(p.name).toLowerCase()), n: String(p.name).slice(0, 80), s: "invited" } : { n: String(p.name).slice(0, 80), s: "confirmed", o: 1 }))),
          /^https:\/\//.test(x.recording_url || "") ? String(x.recording_url).slice(0, 300) : "", owner.id, t));
      for (let i = 0; i < ops.length; i += 40) await db.batch(ops.slice(i, i + 40));
      // Speaker ohne Profil bekommen einen Verknuepfungs-Link (wie bei M365Con 2027)
      const rows = (await db.prepare("SELECT id,speakers FROM event_sessions WHERE event_id=? AND speakers LIKE '%\"o\":1%'").bind(ev.id).all()).results || [], ops2 = [];
      for (const rw of rows) {
        let s2 = []; try { s2 = JSON.parse(rw.speakers); } catch {}
        let ch = false;
        for (const x of s2) if (x.o && !x.h && !x.t) { x.t = rndToken(); ch = true; ops2.push(db.prepare("INSERT OR IGNORE INTO speaker_invites(token,event_id,session_id,name,eid,created) VALUES(?,?,?,?,?,?)").bind(x.t, ev.id, rw.id, x.n, x.e || "", t)); }
        if (ch) ops2.push(db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(s2), rw.id));
      }
      for (let i = 0; i < ops2.length; i += 40) await db.batch(ops2.slice(i, i + 40));
    } catch { /* naechster Lauf */ }
  }
}

// Redaktionell gepflegte Verknuepfungen: Con-Speaker (Name im Programm) <-> Community-Profil mit abweichendem Anzeigenamen
const SPEAKER_LINKS = [{ name: "Elliot Margot", like: "Elliot M%" }];
export async function linkSpeakers(env) {
  const db = env.DB; let n = 0;
  for (const L of SPEAKER_LINKS) {
    const c = (await db.prepare("SELECT DISTINCT p.handle FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.public=1 AND p.handle IS NOT NULL AND u.banned=0 AND (u.name LIKE ?1 OR p.handle LIKE lower(replace(?1,' ','-')))").bind(L.like).all()).results || [];
    if (c.length !== 1) continue;                       // nur eindeutige Treffer verknuepfen
    const h = c[0].handle;
    const rows = (await db.prepare("SELECT id,speakers FROM event_sessions WHERE speakers LIKE ?").bind(`%"n":"${L.name}"%`).all()).results || [], ops = [];
    for (const r of rows) {
      let sp = []; try { sp = JSON.parse(r.speakers); } catch { continue; }
      let ch = false;
      for (const x of sp) if (x.n === L.name && x.h !== h) { if (x.t) ops.push(db.prepare("DELETE FROM speaker_invites WHERE token=?").bind(x.t)); delete x.t; delete x.o; x.h = h; x.s = "confirmed"; ch = true; n++; }
      if (ch) ops.push(db.prepare("UPDATE event_sessions SET speakers=? WHERE id=?").bind(JSON.stringify(sp), r.id));
    }
    if (ops.length) await db.batch(ops);
  }
  return n;
}
