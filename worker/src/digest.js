// Taeglicher Digest: neue Folgen je Sprache -> Web-Push + E-Mail
import { sendPush } from "./push.js";
import { esc } from "./util.js";
import { closeMonth } from "./badges.js";

const LANG_NAME = { de: "Deutsch", es: "Español", fr: "Français", it: "Italiano", pt: "Português", nl: "Nederlands", pl: "Polski", id: "Bahasa Indonesia", ru: "Русский", uk: "Українська", ar: "العربية", he: "עברית", hi: "हिन्दी", ja: "日本語", ko: "한국어", ml: "മലയാളം", pa: "ਪੰਜਾਬੀ", ta: "தமிழ்", te: "తెలుగు" };
const clean = (t) => String(t).replace(/\s*\((KI|AI)[^)]*\)\s*$/i, "").replace(/\s*[（(][^()（）]*[)）]\s*$/, "").trim();

async function pool(items, n, fn) {
  let i = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => { while (i < items.length) { const it = items[i++]; try { await fn(it); } catch (e) { console.log("fehler", String(e).slice(0, 120)); } } }));
}

export async function sendMail(env, to, subject, html, unsubUrl) {
  if (!env.RESEND_API_KEY) return { ok: false, status: 0 };
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, "content-type": "application/json" },
    body: JSON.stringify({ from: env.MAIL_FROM, to, subject, html, headers: unsubUrl ? { "List-Unsubscribe": `<${unsubUrl}>`, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click" } : {} }),
  });
  return { ok: r.ok, status: r.status };
}

export async function runDigest(env, { dry = false } = {}) {
  const db = env.DB;
  const j = await (await fetch(`${env.SITE}/episodes.json`, { cf: { cacheTtl: 0 } })).json();
  const eps = (j.episodes || []).filter((e) => e.id && e.language && e.url);
  const row = await db.prepare("SELECT v FROM meta WHERE k='sent'").first();
  const init = await db.prepare("SELECT v FROM meta WHERE k='digest_init'").first();
  const sent = new Set(row ? JSON.parse(row.v) : []);
  const key = (e) => `${e.id}|${e.language}`;
  if (!init) {   // erster Lauf: Bestand als bekannt markieren, nichts versenden
    for (const e of eps) sent.add(key(e));
    if (!dry) {
      await db.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES('sent',?)").bind(JSON.stringify([...sent])).run();
      await db.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES('digest_init','1')").run();
    }
    return { init: true, known: sent.size };
  }
  const fresh = eps.filter((e) => !sent.has(key(e)));
  const byLang = {};
  for (const e of fresh) (byLang[e.language] ||= []).push(e);
  const res = { new: fresh.length, push: 0, mail: 0, gone: 0, langs: Object.keys(byLang) };
  if (dry) return res;
  for (const [lang, list] of Object.entries(byLang)) {
    list.sort((a, b) => (a.date < b.date ? 1 : -1));
    const first = list[0];
    const payload = { title: `M365.FM · ${LANG_NAME[lang] || lang}`, body: clean(first.title) + (list.length > 1 ? ` (+${list.length - 1})` : ""),
      url: list.length > 1 ? `${env.SITE}/${lang}/` : first.url, tag: `digest-${lang}` };
    const subs = (await db.prepare("SELECT endpoint,p256dh,auth FROM push_subs WHERE lang=?").bind(lang).all()).results || [];
    await pool(subs, 8, async (s) => {
      const r = await sendPush(env, s, payload);
      if (r.ok) res.push++;
      else if (r.gone) { await db.prepare("DELETE FROM push_subs WHERE endpoint=?").bind(s.endpoint).run(); res.gone++; }
    });
    const mails = (await db.prepare("SELECT email,token FROM email_subs WHERE lang=? AND confirmed=1").bind(lang).all()).results || [];
    const items = list.slice(0, 10).map((e) => `<li style="margin:0 0 12px"><a href="${esc(e.url)}" style="color:#3b6391;font-weight:600;text-decoration:none">${esc(clean(e.title))}</a><br><span style="color:#5d6470;font-size:14px">${esc((e.summary || "").slice(0, 160))}</span></li>`).join("");
    await pool(mails, 4, async (m) => {
      const un = `${env.API}/api/email/unsub?token=${encodeURIComponent(m.token)}&lang=${lang}`;
      const html = `<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#17191c"><h2 style="margin:0 0 4px">M365.FM · ${esc(LANG_NAME[lang] || lang)}</h2><p style="color:#5d6470;margin:0 0 18px">${list.length} ${list.length === 1 ? "new episode" : "new episodes"}</p><ul style="padding-left:18px">${items}</ul><p><a href="${env.SITE}/${lang}/" style="color:#3b6391">${env.SITE.replace("https://", "")}/${lang}/</a></p><hr style="border:0;border-top:1px solid #ddd"><p style="font-size:12px;color:#777">Mirko Peters · M365.FM, Julius-Hölder-Str 60, 70597 Stuttgart · <a href="${un}" style="color:#777">Unsubscribe</a></p></div>`;
      const r = await sendMail(env, m.email, `${clean(first.title)}${list.length > 1 ? ` (+${list.length - 1})` : ""}`, html, un);
      if (r.ok) res.mail++;
    });
  }
  for (const e of fresh) sent.add(key(e));
  await db.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES('sent',?)").bind(JSON.stringify([...sent])).run();
  res.curators = await closeMonth(env);
  return res;
}
