import { cleanText, esc, rateLimit, sha256hex } from "./util.js";
import { notify } from "./mail.js";

const now = () => Math.floor(Date.now() / 1000);
const STATUSES = new Set(["new", "contacted", "won", "lost", "spam"]);
const EMAIL = /^[^\s@<>]{1,64}@[^\s@<>]{1,190}\.[a-z]{2,}$/i;

function cleanPackage(value) {
  if (typeof value === "string") {
    if (value.length > 5000) return null;
    try { value = JSON.parse(value); } catch { return null; }
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const clean = (v, depth = 0) => {
    if (typeof v === "string") return cleanText(v, 300);
    if (typeof v === "number") return Number.isFinite(v) ? v : null;
    if (typeof v === "boolean" || v === null) return v;
    if (Array.isArray(v)) return depth < 2 ? v.slice(0, 20).map((x) => clean(x, depth + 1)) : [];
    if (typeof v === "object" && depth < 2) {
      return Object.fromEntries(Object.entries(v).slice(0, 30).map(([k, x]) => [cleanText(k, 40), clean(x, depth + 1)]));
    }
    return null;
  };
  const result = clean(value);
  return JSON.stringify(result).length <= 5000 ? result : null;
}

function packageDetails(pkg) {
  const value = (...keys) => keys.map((k) => pkg[k]).find((x) => x !== undefined && x !== null && x !== "");
  const list = (v) => Array.isArray(v) ? v.join(", ") : v;
  const summary = [
    value("goal", "target", "ziel", "destination", "audience"),
    list(value("topics", "themen")),
    value("duration", "term", "laufzeit", "months"),
    list(value("components", "blocks", "bausteine", "elements")),
  ].filter(Boolean).join(" · ") || JSON.stringify(pkg).slice(0, 300);
  const monthly = value("monthlyUsd", "monthly_usd", "monthlyPrice", "priceMonthly", "monthly", "preisMonat");
  const total = value("totalUsd", "total_usd", "totalPrice", "priceTotal", "total", "gesamtpreis");
  const money = (x) => {
    if (typeof x === "number" && Number.isFinite(x)) return `USD ${x.toLocaleString("en-US")}`;
    if (typeof x === "string" && x) return `USD ${x.slice(0, 80)}`;
    return "";
  };
  return { summary, price: [monthly !== undefined ? `${money(monthly)}/Monat` : "", total !== undefined ? `${money(total)} gesamt` : ""].filter(Boolean).join(" · ") || "–" };
}

export async function handleSponsor(env, request, url, path, J) {
  if (!(path === "/api/sponsor/request" && request.method === "POST")) return null;
  const db = env.DB, body = (await request.json().catch(() => ({}))) || {};
  const company = cleanText(body.company, 160), name = cleanText(body.name, 120);
  const email = cleanText(body.email, 254).toLowerCase();
  const message = cleanText(body.message, 2000);
  const lang = /^[a-z]{2}(?:-[A-Z]{2})?$/.test(String(body.lang || "")) ? String(body.lang) : "de";
  const pkg = cleanPackage(body.package);
  if (company.length < 2 || name.length < 2 || !EMAIL.test(email) || !pkg) return J({ error: "bad_request" }, 400);

  const clientIp = request.headers.get("cf-connecting-ip") || "0";
  const ipHash = await sha256hex(`${env.SESSION_SECRET}:sponsor:${clientIp}`);
  if (!(await rateLimit(db, `sponsor:${ipHash}:h`, 5, 3600)) || !(await rateLimit(db, `sponsor:${ipHash}:d`, 20, 86400))) return J({ error: "rate_limit" }, 429);

  const spam = !!cleanText(body.website, 500);
  const created = now(), details = packageDetails(pkg);
  const result = await db.prepare("INSERT INTO sponsor_requests(created,company,name,email,message,package,status,ip_hash,lang) VALUES(?,?,?,?,?,?,?,?,?)")
    .bind(created, company, name, email, message, JSON.stringify(pkg), spam ? "spam" : "new", ipHash, lang).run();
  const id = result.meta.last_row_id;
  if (!spam) {
    const admins = (await db.prepare("SELECT id,role,provider,sub FROM users WHERE banned=0").all()).results || [];
    const allow = new Set((env.ADMIN_SUBS || "").split(",").map((s) => s.trim()).filter(Boolean));
    const recipients = admins.filter((u) => u.role === "admin" || allow.has(`${u.provider}:${u.sub}`)).sort((a, b) => a.id - b.id);
    const panel = `${env.SITE}/admin/`;
    const bodyHtml = `<p>Neue Sponsor-Anfrage von <b>${esc(company)}</b>.</p><p>Name: ${esc(name)}<br>E-Mail: ${esc(email)}<br>Paket: ${esc(details.summary)}<br>Preis: ${esc(details.price)}</p>${message ? `<p>${esc(message)}</p>` : ""}<p><a href="${esc(panel)}">Im Admin-Panel ansehen</a></p>`;
    let key = `sponsor:${id}`;
    for (const u of recipients) {
      if (await notify(env, u.id, "system", `Neue Sponsor-Anfrage: ${company}`, bodyHtml, key)) key = `${key}:${u.id}`;
    }
  }
  return J({ ok: true });
}

export { STATUSES as SPONSOR_STATUSES };
