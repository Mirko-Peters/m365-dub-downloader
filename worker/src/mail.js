// Mail-System: bestaetigte Adresse je Konto, Einstellungen je Art, Warteschlange (Outbox) mit Versand per Resend, Abmeldelink in jeder Mail.
import { sendMail } from "./digest.js";
import { esc, sign, verify, randomToken, rateLimit } from "./util.js";

const now = () => Math.floor(Date.now() / 1000);
export const KINDS = { reply: 1, wish: 1, show: 1, event: 1, system: 1 };   // 1 = standardmaessig an; "system" = Test/Bestaetigung
const LABEL = { reply: ["Antworten auf meine Kommentare", "Replies to my comments"], wish: ["Status meiner Wünsche (Roadmap)", "Status of my wishes (roadmap)"], show: ["Freigabe meiner Podcast-Shows", "Approval of my podcast shows"], event: ["Einladungen zu Events und Sessions", "Invitations to events and sessions"] };
let ready = false;
async function ensure(db) {
  if (ready) return;
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS mail_addr (user_id INTEGER PRIMARY KEY, email TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0, token TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL)"),
    db.prepare("CREATE TABLE IF NOT EXISTS mail_prefs (user_id INTEGER NOT NULL, kind TEXT NOT NULL, on_ INTEGER NOT NULL, PRIMARY KEY (user_id, kind))"),
    db.prepare("CREATE TABLE IF NOT EXISTS mail_outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, kind TEXT NOT NULL, subject TEXT NOT NULL, html TEXT NOT NULL, key TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, sent INTEGER NOT NULL DEFAULT 0, tries INTEGER NOT NULL DEFAULT 0, err TEXT NOT NULL DEFAULT '')"),
    db.prepare("CREATE UNIQUE INDEX IF NOT EXISTS idx_outbox_key ON mail_outbox(key) WHERE key!=''"),
  ]);
  ready = true;
}
const wrap = (env, body, foot) => `<div style="font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:560px;margin:auto;color:#1b2430;line-height:1.55"><p style="font-weight:700;font-size:18px">M365.FM</p>${body}<hr style="border:0;border-top:1px solid #dde3ea;margin:24px 0"><p style="font-size:12px;color:#6b7785">${foot}</p></div>`;
const page = (t, b, code = 200) => new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M365.FM</title><body style="font-family:system-ui,Arial,sans-serif;max-width:520px;margin:12vh auto;padding:0 16px"><h2>${t}</h2>${b}</body>`, { status: code, headers: { "content-type": "text/html; charset=utf-8" } });
const unsubUrl = async (env, uid, kind) => `${env.API}/api/mail/unsub?t=${uid}.${kind}.${await sign(env.SESSION_SECRET, `unsub:${uid}:${kind}`)}`;

export async function wants(db, uid, kind) {
  await ensure(db);
  const a = await db.prepare("SELECT 1 x FROM mail_addr WHERE user_id=? AND verified=1").bind(uid).first(); if (!a) return false;
  const p = await db.prepare("SELECT on_ FROM mail_prefs WHERE user_id=? AND kind=?").bind(uid, kind).first();
  return p ? !!p.on_ : !!KINDS[kind];
}
// Benachrichtigung vormerken (und sofort versuchen). key = Duplikatschutz, z. B. "wish:12:planned".
export async function notify(env, uid, kind, subject, bodyHtml, key = "") {
  try {
    const db = env.DB; if (!uid || !(await wants(db, uid, kind))) return false;
    const r = await db.prepare("INSERT OR IGNORE INTO mail_outbox(user_id,kind,subject,html,key,created) VALUES(?,?,?,?,?,?)").bind(uid, kind, String(subject).slice(0, 160), bodyHtml, key, now()).run();
    if (!r.meta.changes) return false;
    await flushOutbox(env, 5); return true;
  } catch { return false; }
}
export async function flushOutbox(env, limit = 40) {
  const db = env.DB; await ensure(db); if (!env.RESEND_API_KEY) return { skipped: "no_key" };
  const rows = (await db.prepare("SELECT o.*,a.email FROM mail_outbox o JOIN mail_addr a ON a.user_id=o.user_id AND a.verified=1 WHERE o.sent=0 AND o.tries<3 ORDER BY o.id LIMIT ?").bind(limit).all()).results || [];
  let ok = 0;
  for (const m of rows) {
    const un = await unsubUrl(env, m.user_id, m.kind);
    const html = wrap(env, m.html, `Du erhältst diese E-Mail, weil du Benachrichtigungen aktiviert hast. / You get this e-mail because you enabled notifications. <a href="${un}">Abmelden / Unsubscribe</a> · <a href="${env.SITE}/community/">Einstellungen / Settings</a>`);
    const r = await sendMail(env, m.email, m.subject, html, un);
    await db.prepare("UPDATE mail_outbox SET tries=tries+1,sent=?,err=? WHERE id=?").bind(r.ok ? 1 : 0, r.ok ? "" : "http_" + r.status, m.id).run();
    if (r.ok) ok++;
  }
  await db.prepare("DELETE FROM mail_outbox WHERE sent=1 AND created<?").bind(now() - 30 * 86400).run();
  return { tried: rows.length, sent: ok };
}

export async function handleMail(env, request, url, path, user, J) {
  if (!path.startsWith("/api/mail/") && !path.startsWith("/api/admin/mail")) return null;
  const db = env.DB, method = request.method; await ensure(db);
  if (path === "/api/mail/confirm" && method === "GET") {
    const t = url.searchParams.get("t") || "";
    const r = t.length > 10 ? await db.prepare("UPDATE mail_addr SET verified=1,token='' WHERE token=?").bind(t).run() : { meta: { changes: 0 } };
    return r.meta.changes ? page("✓ E-Mail bestätigt / confirmed", `<p><a href="${env.SITE}/community/">${env.SITE.replace("https://", "")}/community</a></p>`) : page("Link ungültig / invalid", "<p>Bitte fordere in deinem Profil eine neue Bestätigung an.</p>", 404);
  }
  if (path === "/api/mail/unsub" && (method === "GET" || method === "POST")) {
    const [uid, kind, sig] = (url.searchParams.get("t") || "").split("."); 
    if (!uid || !kind || !sig || !(await verify(env.SESSION_SECRET, `unsub:${uid}:${kind}`, sig))) return page("Link ungültig / invalid", "", 400);
    await db.prepare("INSERT OR REPLACE INTO mail_prefs(user_id,kind,on_) VALUES(?,?,0)").bind(+uid, kind).run();
    return method === "POST" ? new Response("ok") : page("✓ Abgemeldet / Unsubscribed", `<p>${esc(LABEL[kind]?.[0] || kind)}: keine weiteren E-Mails. Du kannst das in deinem Profil wieder ändern.</p>`);
  }
  if (!user) return J({ error: "login" }, 401);
  if (path === "/api/mail/me" && method === "GET") {
    const a = await db.prepare("SELECT email,verified FROM mail_addr WHERE user_id=?").bind(user.id).first();
    const pr = Object.fromEntries(((await db.prepare("SELECT kind,on_ FROM mail_prefs WHERE user_id=?").bind(user.id).all()).results || []).map((r) => [r.kind, !!r.on_]));
    return J({ configured: !!env.RESEND_API_KEY, email: a?.email || "", verified: !!a?.verified, prefs: Object.fromEntries(Object.keys(LABEL).map((k) => [k, k in pr ? pr[k] : !!KINDS[k]])) }, 200, { "cache-control": "no-store" });
  }
  if (path === "/api/admin/mail" && method === "GET") {
    if (!user.admin) return J({ error: "forbidden" }, 403);
    const s = await db.prepare("SELECT COUNT(*) total,SUM(sent=1) sent,SUM(sent=0 AND tries<3) waiting,SUM(sent=0 AND tries>=3) failed FROM mail_outbox").first();
    return J({ configured: !!env.RESEND_API_KEY, ...s, addresses: (await db.prepare("SELECT COUNT(*) c FROM mail_addr WHERE verified=1").first()).c });
  }
  if (method !== "POST") return J({ error: "bad_request" }, 400);
  const b = await request.json().catch(() => ({}));
  if (path === "/api/mail/set") {   // Adresse eintragen -> Bestaetigungsmail
    const email = String(b.email || "").trim().toLowerCase();
    if (!/^[^\s@<>]{1,64}@[^\s@<>]{1,190}\.[a-z]{2,}$/.test(email)) return J({ error: "email" }, 400);
    if (!env.RESEND_API_KEY) return J({ error: "mail_off" }, 503);
    if (!(await rateLimit(db, `mset:${user.id}`, 4, 3600))) return J({ error: "rate_limit" }, 429);
    const token = randomToken(20);
    await db.prepare("INSERT OR REPLACE INTO mail_addr(user_id,email,verified,token,created) VALUES(?,?,0,?,?)").bind(user.id, email, token, now()).run();
    const link = `${env.API}/api/mail/confirm?t=${encodeURIComponent(token)}`;
    const r = await sendMail(env, email, "M365.FM – E-Mail bestätigen / confirm e-mail", wrap(env, `<p>Bitte bestätige deine E-Mail-Adresse für Benachrichtigungen:</p><p><a href="${link}">${link}</a></p><p>Please confirm your e-mail address for notifications. If this wasn’t you, ignore this message.</p>`, "M365.FM"));
    return J({ ok: r.ok });
  }
  if (path === "/api/mail/prefs") {
    if (!(b.kind in LABEL)) return J({ error: "bad_kind" }, 400);
    await db.prepare("INSERT OR REPLACE INTO mail_prefs(user_id,kind,on_) VALUES(?,?,?)").bind(user.id, b.kind, b.on ? 1 : 0).run(); return J({ ok: true });
  }
  if (path === "/api/mail/remove") { await db.batch([db.prepare("DELETE FROM mail_addr WHERE user_id=?").bind(user.id), db.prepare("DELETE FROM mail_outbox WHERE user_id=? AND sent=0").bind(user.id)]); return J({ ok: true }); }
  if (path === "/api/mail/test") {
    if (!(await rateLimit(db, `mtest:${user.id}`, 3, 3600))) return J({ error: "rate_limit" }, 429);
    const ok = await notify(env, user.id, "system", "M365.FM – Testnachricht / test message", "<p>Das ist eine Testnachricht. / This is a test message.</p>", `test:${user.id}:${now()}`);
    return J({ ok });
  }
  return J({ error: "not_found" }, 404);
}
export { LABEL as MAIL_LABEL };
