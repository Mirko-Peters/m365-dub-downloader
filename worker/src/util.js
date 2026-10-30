// Hilfsfunktionen: Base64url, HMAC-Sessions, CORS/JSON, Text-Bereinigung, Ratelimit
const enc = new TextEncoder();

export const b64u = {
  enc(buf) {
    const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
    let s = ""; for (const x of b) s += String.fromCharCode(x);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  },
  dec(str) {
    str = str.replace(/-/g, "+").replace(/_/g, "/"); while (str.length % 4) str += "=";
    const s = atob(str); const b = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) b[i] = s.charCodeAt(i);
    return b;
  },
};

async function hmacKey(secret) {
  return crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}
export async function sign(secret, data) {
  return b64u.enc(await crypto.subtle.sign("HMAC", await hmacKey(secret), enc.encode(data)));
}
export async function verify(secret, data, sig) {
  try { return await crypto.subtle.verify("HMAC", await hmacKey(secret), b64u.dec(sig), enc.encode(data)); } catch { return false; }
}

export async function makeSession(env, uid, days = 60) {
  const exp = Math.floor(Date.now() / 1000) + days * 86400;
  const body = `${uid}.${exp}`;
  return `${body}.${await sign(env.SESSION_SECRET, body)}`;
}
export async function readSession(env, request) {
  const m = /(?:^|;\s*)m365s=([^;]+)/.exec(request.headers.get("cookie") || "");
  if (!m) return null;
  const [uid, exp, sig] = m[1].split(".");
  if (!uid || !exp || !sig || +exp < Date.now() / 1000) return null;
  if (!(await verify(env.SESSION_SECRET, `${uid}.${exp}`, sig))) return null;
  return +uid;
}
export function cookie(name, value, maxAge) {
  return `${name}=${value}; Max-Age=${maxAge}; Path=/; HttpOnly; Secure; SameSite=Lax`;
}

export function cors(env, request) {
  const origin = request.headers.get("origin");
  const h = { "vary": "Origin" };
  if (origin && (origin === env.SITE || /^http:\/\/localhost(:\d+)?$/.test(origin))) {
    h["access-control-allow-origin"] = origin;
    h["access-control-allow-credentials"] = "true";
    h["access-control-allow-headers"] = "content-type, x-requested-with";
    h["access-control-allow-methods"] = "GET, POST, DELETE, OPTIONS";
    h["access-control-max-age"] = "86400";
  }
  return h;
}
export function json(data, status, env, request, extra = {}) {
  return new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...cors(env, request), ...extra },
  });
}

export function cleanText(s, max) {
  s = String(s ?? "").normalize("NFC").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f​-‏‪-‮⁦-⁩]/g, "");
  s = s.replace(/\r\n?/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
  return s.length > max ? s.slice(0, max) : s;
}
export const cleanName = (s) => cleanText(s, 40).replace(/\s+/g, " ").replace(/[<>]/g, "");

export function randomToken(bytes = 24) { return b64u.enc(crypto.getRandomValues(new Uint8Array(bytes))); }

export async function sha256hex(s) {
  const d = await crypto.subtle.digest("SHA-256", enc.encode(s));
  return [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

// Ratelimit: max Aktionen pro Fenster (Sekunden). true = erlaubt
export async function rateLimit(db, key, max, windowSec) {
  const now = Math.floor(Date.now() / 1000);
  const row = await db.prepare("SELECT n, win FROM ratelimit WHERE k=?").bind(key).first();
  if (!row || now - row.win >= windowSec) {
    await db.prepare("INSERT OR REPLACE INTO ratelimit(k,n,win) VALUES(?,?,?)").bind(key, 1, now).run();
    return true;
  }
  if (row.n >= max) return false;
  await db.prepare("UPDATE ratelimit SET n=n+1 WHERE k=?").bind(key).run();
  return true;
}

export const LANGS = ["de", "es", "fr", "it", "pt", "nl", "pl", "id", "ru", "uk", "ar", "he", "ja", "ko"];
export const isLang = (l) => LANGS.includes(l);
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
