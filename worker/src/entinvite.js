// Einladungsmails fuer Personen-Entitaeten: "Zu dir gibt es eine Seite auf M365.FM – uebernehmen, ergaenzen oder entfernen lassen."
// Token im Link belegt die Adresse; Annahme verknuepft die Entitaet mit dem Konto (entity_claims, via invite). Ablehnen sperrt weitere Einladungen.
import { sendMail } from "./digest.js";
import { esc, randomToken, rateLimit, cleanText } from "./util.js";
import { claimEntity } from "./events.js";

const now = () => Math.floor(Date.now() / 1000);
const EID = /^[a-z0-9][a-z0-9-]{1,78}$/;
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS entity_invites (token TEXT PRIMARY KEY, eid TEXT NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL, by_user INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'sent', created INTEGER NOT NULL, reminded INTEGER NOT NULL DEFAULT 0, UNIQUE(eid, email))"),
    db.prepare("CREATE TABLE IF NOT EXISTS entity_contacts (eid TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL, created INTEGER NOT NULL)"),
    db.prepare("CREATE TABLE IF NOT EXISTS invite_block (email TEXT PRIMARY KEY, created INTEGER NOT NULL)"),
  ]);
  ready = true;
}
const page = (t, b, code = 200) => new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M365.FM</title><body style="font-family:system-ui,Arial,sans-serif;max-width:520px;margin:12vh auto;padding:0 16px"><h2>${t}</h2>${b}</body>`, { status: code, headers: { "content-type": "text/html; charset=utf-8" } });
const link = (env, t) => `${env.SITE}/community/?invite=${encodeURIComponent(t)}#c-invite`;

function mailBody(env, inv, byName, reminder) {
  const accept = link(env, inv.token), decline = `${env.API}/api/entityinvite/decline?t=${encodeURIComponent(inv.token)}`, page_ = `${env.SITE}/entity/${inv.eid}/`;
  const intro = reminder ? "Kurze Erinnerung: " : "";
  return `<div style="font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:560px;margin:auto;color:#1b2430;line-height:1.55"><p style="font-weight:700;font-size:18px">M365.FM</p>
<p>${intro}Hallo ${esc(inv.name)},</p>
<p>auf M365.FM, einer Plattform rund um Microsoft 365, gibt es eine Seite zu dir: <a href="${page_}">${page_}</a>. ${byName ? `<b>${esc(byName)}</b> hat dich dort eingetragen und dir diese Einladung geschickt.` : ""}</p>
<p>Du kannst die Seite <b>übernehmen</b> (kostenloses Konto, dann pflegst du Angaben, Themen und Links selbst) oder <b>entfernen lassen</b>.</p>
<p><a href="${accept}" style="background:#3E8BC0;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;display:inline-block">Seite übernehmen</a></p>
<p><a href="${decline}">Das bin ich nicht / bitte entfernen und nicht mehr einladen</a></p>
<hr style="border:0;border-top:1px solid #dde3ea;margin:20px 0">
<p>Hello ${esc(inv.name)}, M365.FM has a page about you (<a href="${page_}">${page_}</a>)${byName ? `, added by ${esc(byName)}` : ""}. You can <a href="${accept}">claim it</a> (free account) or <a href="${decline}">ask us to remove it and not invite you again</a>.</p>
<p style="font-size:12px;color:#6b7785">Diese Nachricht informiert dich über gespeicherte Angaben zu deiner Person (Name, öffentliche Angaben). Es ist keine Werbung; wir schreiben dir nur einmal und erinnern höchstens einmal. Verantwortlich: M365.FM, Julius-Hölder-Str 60, 70597 Stuttgart, mirko.peters@m365.fm.</p></div>`;
}
async function send(env, inv, byName, reminder) {
  return sendMail(env, inv.email, reminder ? `Erinnerung: Deine Seite auf M365.FM, ${inv.name}` : `Deine Seite auf M365.FM – übernehmen oder entfernen lassen / claim or remove`, mailBody(env, inv, byName, reminder), `${env.API}/api/entityinvite/decline?t=${encodeURIComponent(inv.token)}`);
}
export async function remindInvites(env) {   // Cron: nach 7 Tagen einmal erinnern
  const db = env.DB; await ensure(db); if (!env.RESEND_API_KEY) return 0;
  const rows = (await db.prepare("SELECT i.*,COALESCE(u.name,'') byn FROM entity_invites i LEFT JOIN users u ON u.id=i.by_user WHERE i.status='sent' AND i.reminded=0 AND i.created<? LIMIT 20").bind(now() - 7 * 86400).all()).results || [];
  for (const r of rows) { const x = await send(env, r, r.byn, true); await db.prepare("UPDATE entity_invites SET reminded=? WHERE token=?").bind(x.ok ? 1 : 2, r.token).run(); }
  return rows.length;
}

export async function handleEntityInvite(env, request, url, path, user, J) {
  if (!path.startsWith("/api/entityinvite/")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (path === "/api/entityinvite/decline" && method === "GET") {
    const t = url.searchParams.get("t") || "", i = t ? await db.prepare("SELECT eid,email FROM entity_invites WHERE token=?").bind(t).first() : null;
    if (!i) return page("Link ungültig / invalid", "", 404);
    await db.batch([db.prepare("UPDATE entity_invites SET status='declined' WHERE token=?").bind(t), db.prepare("INSERT OR IGNORE INTO invite_block(email,created) VALUES(?,?)").bind(i.email, now())]);
    return page("✓ Erledigt / Done", `<p>Wir laden dich nicht erneut ein. Die Seite <b>${esc(i.eid)}</b> wird vom Team geprüft und auf Wunsch entfernt.</p><p>We will not invite you again; the team will review and, on request, remove the page.</p>`);
  }
  if (path === "/api/entityinvite/info" && method === "GET") {
    const i = await db.prepare("SELECT eid,name,status FROM entity_invites WHERE token=?").bind(url.searchParams.get("t") || "").first();
    return i ? J({ eid: i.eid, name: i.name, status: i.status }) : J({ error: "not_found" }, 404);
  }
  if (!user) return J({ error: "login" }, 401);
  const body = async () => request.json().catch(() => ({}));
  if (path === "/api/entityinvite/accept" && method === "POST") {
    const b = await body(), i = await db.prepare("SELECT * FROM entity_invites WHERE token=?").bind(String(b.t || "")).first();
    if (!i || i.status === "declined") return J({ error: "not_found" }, 404);
    const pr = await db.prepare("SELECT 1 x FROM profiles WHERE user_id=? AND public=1 AND handle IS NOT NULL").bind(user.id).first(); if (!pr) return J({ error: "need_profile" }, 409);
    if (!(await claimEntity(db, i.eid, user.id, "invite"))) return J({ error: "claimed" }, 409);
    await db.prepare("UPDATE entity_invites SET status='claimed' WHERE token=?").bind(i.token).run();
    return J({ ok: true, eid: i.eid });
  }
  if (path === "/api/entityinvite/mine" && method === "GET") {
    const rows = (await db.prepare(`SELECT eid,name,status,created,reminded,${user.admin || user.editor ? "email" : "'' email"} FROM entity_invites WHERE ${user.admin || user.editor ? "1=1" : "by_user=?"} ORDER BY created DESC LIMIT 300`).bind(...(user.admin || user.editor ? [] : [user.id])).all()).results || [];
    return J({ items: rows, mail: !!env.RESEND_API_KEY, staff: !!(user.admin || user.editor) }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/entityinvite/contacts" && (user.admin || user.editor)) {   // Kontaktadressen (nur DB, nie im Repo)
    if (method === "GET") { const c = await db.prepare("SELECT COUNT(*) n FROM entity_contacts").first(); const o = await db.prepare("SELECT COUNT(*) n FROM entity_contacts c WHERE NOT EXISTS (SELECT 1 FROM entity_invites i WHERE i.eid=c.eid)").first(); return J({ contacts: c.n, not_invited: o.n }); }
    if (method === "POST") {
      const b = await body(), items = (Array.isArray(b.items) ? b.items : []).slice(0, 400); let n = 0;
      for (const x of items) {
        const eid = String(x.eid || "").toLowerCase(), email = String(x.email || "").trim().toLowerCase(), name = cleanText(x.name, 80).replace(/[<>]/g, "");
        if (!EID.test(eid) || !name || !/^[^\s@<>]{1,64}@[^\s@<>]{1,190}\.[a-z]{2,}$/.test(email)) continue;
        await db.prepare("INSERT INTO entity_contacts(eid,email,name,created) VALUES(?,?,?,?) ON CONFLICT(eid) DO UPDATE SET email=excluded.email,name=excluded.name").bind(eid, email, name, now()).run(); n++;
      }
      return J({ ok: true, saved: n });
    }
  }
  if (path === "/api/entityinvite/send" && method === "POST") {
    const b = await body(), staff = !!(user.admin || user.editor);
    const list = (Array.isArray(b.items) ? b.items : [b]).slice(0, staff ? 50 : 3);
    if (!env.RESEND_API_KEY) return J({ error: "mail_off" }, 503);
    if (!(await rateLimit(db, `einv:${user.id}`, staff ? 200 : 5, 86400))) return J({ error: "rate_limit" }, 429);
    const out = [];
    for (const x of list) {
      const eid = String(x.eid || "").toLowerCase();
      let email = String(x.email || "").trim().toLowerCase(), name = cleanText(x.name, 80).replace(/[<>]/g, "");
      if (staff && eid && !email) { const c = await db.prepare("SELECT email,name FROM entity_contacts WHERE eid=?").bind(eid).first(); if (c) { email = c.email; name = name || c.name; } }
      if (!EID.test(eid) || !name || !/^[^\s@<>]{1,64}@[^\s@<>]{1,190}\.[a-z]{2,}$/.test(email)) { out.push({ eid, error: "bad_input" }); continue; }
      if (!staff) {   // Mitglieder: nur fuer Entitaeten, die sie selbst angelegt haben
        const own = await db.prepare("SELECT 1 x FROM entity_rev WHERE eid=? AND user_id=?").bind(eid, user.id).first(); if (!own) { out.push({ eid, error: "not_yours" }); continue; }
      }
      if (await db.prepare("SELECT 1 x FROM invite_block WHERE email=?").bind(email).first()) { out.push({ eid, error: "blocked" }); continue; }
      if (await db.prepare("SELECT 1 x FROM entity_claims WHERE eid=? AND status='verified'").bind(eid).first()) { out.push({ eid, error: "claimed" }); continue; }
      if (await db.prepare("SELECT 1 x FROM entity_invites WHERE eid=? AND email=?").bind(eid, email).first()) { out.push({ eid, error: "already" }); continue; }
      const inv = { token: randomToken(20), eid, name, email };
      await db.prepare("INSERT INTO entity_invites(token,eid,name,email,by_user,created) VALUES(?,?,?,?,?,?)").bind(inv.token, eid, name, email, user.id, now()).run();
      const r = await send(env, inv, user.name, false);
      if (!r.ok) await db.prepare("DELETE FROM entity_invites WHERE token=?").bind(inv.token).run();
      out.push({ eid, ok: r.ok });
    }
    return J({ results: out });
  }
  return J({ error: "not_found" }, 404);
}
