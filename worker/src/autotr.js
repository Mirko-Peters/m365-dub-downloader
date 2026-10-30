// Automatische Uebersetzung neuer Community-Inhalte (Blog, Podcast, Video) mit Claude Haiku: ohne Denkphase, Aufwand "low".
// Regel: 24 Stunden nach dem Erscheinen eines Inhalts wird nachgeschaut; fehlt eine Sprachfassung (hat sie niemand uebersetzt), uebersetzt Haiku sie.
// Sicherheitsnetz: nur mit Secret ANTHROPIC_API_KEY, Tageslimit, nur Inhalte der letzten 30 Tage, Notaus ueber meta atr_off=1.
// Ergebnis in item_tr; Blogfassungen erscheinen ueber /api/blog/export als Beitraege der Zielsprache (mit KI-Hinweis).
const MODEL = "claude-haiku-5-5", WAIT = 24 * 3600, WINDOW = 30 * 24 * 3600, DAILY_CAP = 150, PER_RUN = 4;
const LANGS = { en: "English", de: "German", fr: "French", es: "Spanish", it: "Italian", nl: "Dutch", pt: "Portuguese (European)", pl: "Polish", id: "Indonesian", ru: "Russian", uk: "Ukrainian", ar: "Arabic", he: "Hebrew", hi: "Hindi", ja: "Japanese", ko: "Korean" };
const KINDS = {
  blog: { table: "blog_posts", sel: "id,lang,title,summary,body", where: "status='live' AND html='' AND published>0", t: "published", f: ["title", "summary", "body"] },
  podcast: { table: "pod_episodes", sel: "id,lang,title,description AS summary", where: "published>0", t: "published", f: ["title", "summary"] },
  video: { table: "yt_videos", sel: "id,lang,title,description AS summary", where: "published>0", t: "published", f: ["title", "summary"] },
};
const now = () => Math.floor(Date.now() / 1000);
const SYS = "You translate community posts about Microsoft 365, Azure and IT. Translate the JSON values into the requested language and answer with the JSON object only, same keys. " +
  "Never translate names: product and feature names, event, person and company names, abbreviations and codes. Keep the markup exactly as it is: {{ref|...}} and [[...]] links, headings (== ... ==), lists, blank lines, URLs. " +
  "Keep tone and length. No commentary.";

async function meta(db, k) { return (await db.prepare("SELECT v FROM meta WHERE k=?").bind(k).first())?.v || ""; }
async function setMeta(db, k, v) { await db.prepare("INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(k, String(v)).run(); }
export async function ensureItemTr(db) {
  await db.prepare("CREATE TABLE IF NOT EXISTS item_tr (kind TEXT NOT NULL, item_id INTEGER NOT NULL, lang TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', summary TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', src TEXT NOT NULL DEFAULT 'auto', created INTEGER NOT NULL, PRIMARY KEY (kind, item_id, lang))").run();
}
const count = (s, re) => (String(s).match(re) || []).length;

async function call(env, from, to, obj) {
  const body = { model: MODEL, max_tokens: 8000, temperature: 0, system: SYS + ` Target language: ${LANGS[to]}.`, messages: [{ role: "user", content: JSON.stringify(obj) }] };
  const go = (b) => fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "content-type": "application/json", "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" }, body: JSON.stringify(b) });
  let r = await go({ ...body, output_config: { effort: "low" } });   // kein "thinking": keine Denkphase
  if (r.status === 400) r = await go(body);                          // falls der Parameter fuer das Modell nicht akzeptiert wird
  if (!r.ok) throw new Error("api " + r.status);
  let txt = ((await r.json()).content?.[0]?.text || "").trim();
  if (txt.startsWith("```")) txt = txt.replace(/^```[a-z]*\n?/, "").replace(/```$/, "");
  return JSON.parse(txt);
}

export async function autoTranslateItems(env) {
  const db = env.DB;
  if (!env.ANTHROPIC_API_KEY || (await meta(db, "atr_off")) === "1") return { skipped: true };
  await ensureItemTr(db);
  const day = new Date().toISOString().slice(0, 10), used = +(await meta(db, "atr_count:" + day)) || 0, room = Math.min(PER_RUN, DAILY_CAP - used);
  if (room <= 0) return { capped: true };
  const t = now(), todo = [];
  for (const [kind, K] of Object.entries(KINDS)) {
    let rows = [];
    try { rows = (await db.prepare(`SELECT ${K.sel},${K.t} ts FROM ${K.table} WHERE ${K.where} AND ${K.t}<=? AND ${K.t}>=? ORDER BY ${K.t} DESC LIMIT 60`).bind(t - WAIT, t - WINDOW).all()).results || []; } catch { continue; }
    if (!rows.length) continue;
    const have = new Set(((await db.prepare("SELECT item_id,lang FROM item_tr WHERE kind=?").bind(kind).all()).results || []).map((r) => r.item_id + "|" + r.lang));
    for (const r of rows) for (const to of Object.keys(LANGS)) if (to !== r.lang && !have.has(r.id + "|" + to)) todo.push({ kind, K, r, to });
    if (todo.length >= room) break;
  }
  let done = 0, failed = 0;
  await Promise.all(todo.slice(0, room).map(async ({ kind, K, r, to }) => {
    const inp = {}; for (const f of K.f) inp[f] = String(r[f] || "").slice(0, f === "body" ? 12000 : 600);
    try {
      const out = await call(env, r.lang, to, inp);
      const bad = K.f.some((f) => inp[f] && typeof out[f] !== "string") || /<script/i.test(JSON.stringify(out));
      const lr = (out.body || "").length / Math.max(1, (inp.body || "").length);
      if (bad || (inp.body && (lr < 0.2 || lr > 3)) || (inp.body && count(out.body, /\{\{ref\|/g) !== count(inp.body, /\{\{ref\|/g))) { failed++; return; }
      await db.prepare("INSERT OR IGNORE INTO item_tr(kind,item_id,lang,title,summary,body,src,created) VALUES(?,?,?,?,?,?,?,?)").bind(kind, r.id, to, out.title.slice(0, 140), String(out.summary || "").slice(0, 400), String(out.body || ""), "auto", t).run();
      done++;
    } catch { failed++; }
  }));
  await setMeta(db, "atr_count:" + day, used + done + failed);
  if (failed) await setMeta(db, "atr_err", `${failed} ${t}`);
  return { done, failed, open: Math.max(0, todo.length - room) };
}

// Blog: uebersetzte Fassungen als zusaetzliche Beitraege der Zielsprache (fuer /api/blog/export)
export async function translatedBlogItems(db) {
  try {
    const rows = (await db.prepare(
      `SELECT x.item_id,x.lang,x.title,x.summary,x.body,b.slug,b.lang src_lang,b.topics,b.created,b.published,b.updated,p.handle,u.name,(SELECT COUNT(*) FROM blog_votes v WHERE v.post_id=b.id) votes
       FROM item_tr x JOIN blog_posts b ON b.id=x.item_id AND b.status='live' JOIN profiles p ON p.user_id=b.user_id AND p.public=1 AND p.handle IS NOT NULL JOIN users u ON u.id=b.user_id AND u.banned=0
       WHERE x.kind='blog' ORDER BY b.published DESC LIMIT 2000`).all()).results || [];
    return rows.map((r) => ({ id: 1000000000 + r.item_id * 100 + Object.keys(LANGS).indexOf(r.lang), slug: r.slug, title: r.title, summary: r.summary, body: r.body, lang: r.lang, src_lang: r.src_lang, ai_tr: true,
      topics: JSON.parse(r.topics || "[]"), keypoints: [], faq: [], created: r.created, published: r.published, updated: r.updated, has_html: 0, handle: r.handle, name: r.name, votes: r.votes, coauthors: [] }));
  } catch { return []; }
}

// ---------- Entitaeten: Kurzbeschreibung (desc) und lange Beschreibung (long, enthaelt die Ueberschriften) in alle Sprachen ----------
// Quelle: Englisch (sonst Deutsch). Erst wenn ein Text seit 24 Stunden bekannt ist; Ergebnis in ent_tr (Seitenbau holt es ueber /api/entity/tr).
const SKIP_TYPES = ["person", "event", "org"], ENT_PER_RUN = 8, ENT_CAP = 300;
const ESYS = "You translate encyclopedia texts about Microsoft products and IT concepts. Translate the JSON values into the requested language and answer with the JSON object only, same keys. " +
  "Never translate names: product and feature names, event, person and company names, abbreviations and codes (e.g. Copilot Studio, Power Fx, MS-900, M365Con). Keep the structure exactly: paragraphs (blank lines), headings (== ... ==, ### ... or lines starting with #), lists, links and URLs. Keep tone and length. No commentary.";

export async function ensureEntTr(db) {
  await db.prepare("CREATE TABLE IF NOT EXISTS ent_tr (eid TEXT NOT NULL, field TEXT NOT NULL, lang TEXT NOT NULL, text TEXT NOT NULL, created INTEGER NOT NULL, PRIMARY KEY (eid, field, lang))").run();
  await db.prepare("CREATE TABLE IF NOT EXISTS ent_tr_seen (eid TEXT NOT NULL, field TEXT NOT NULL, first INTEGER NOT NULL, h TEXT NOT NULL DEFAULT '', PRIMARY KEY (eid, field))").run();
}

export async function autoTranslateEntities(env, entityMap) {
  const db = env.DB;
  if (!env.ANTHROPIC_API_KEY || (await meta(db, "atr_off")) === "1") return { skipped: true };
  await ensureEntTr(db);
  const day = new Date().toISOString().slice(0, 10), used = +(await meta(db, "atr_ent:" + day)) || 0, room = Math.min(ENT_PER_RUN, (+(await meta(db, "atr_ent_cap")) || ENT_CAP) - used);
  if (room <= 0) return { capped: true };
  const t = now(), map = await entityMap(env);
  const claimed = new Set(((await db.prepare("SELECT eid FROM entity_claims WHERE status='verified'").all()).results || []).map((r) => r.eid));
  const seen = new Map(((await db.prepare("SELECT eid,field,first,h FROM ent_tr_seen").all()).results || []).map((r) => [r.eid + "|" + r.field, r]));
  const have = new Set(((await db.prepare("SELECT eid,field,lang FROM ent_tr").all()).results || []).map((r) => r.eid + "|" + r.field + "|" + r.lang));
  const hash = (x) => { let h = 5381; for (let i = 0; i < x.length; i++) h = ((h << 5) + h + x.charCodeAt(i)) | 0; return String(h); };
  const jobs = [];
  for (const e of map.values()) {
    if (SKIP_TYPES.includes(e.type) || claimed.has(e.id) || e.outdated || e.replaced_by) continue;
    const src = {}; let from = "";
    for (const f of ["desc", "long"]) { const v = e[f] || {}; const txt = (v.en || "").trim() || (v.de || "").trim(); if (txt) { src[f] = txt.slice(0, 8000); from ||= (v.en || "").trim() ? "en" : "de"; } }
    if (!Object.keys(src).length) continue;
    for (const f of Object.keys(src)) {   // Text neu oder geaendert: Wartezeit beginnt von vorn
      const k = e.id + "|" + f, h = hash(src[f]), s = seen.get(k);
      if (!s || s.h !== h) { await db.prepare("INSERT INTO ent_tr_seen(eid,field,first,h) VALUES(?,?,?,?) ON CONFLICT(eid,field) DO UPDATE SET first=excluded.first,h=excluded.h").bind(e.id, f, t, h).run(); seen.set(k, { first: t, h }); if (s) await db.prepare("DELETE FROM ent_tr WHERE eid=? AND field=?").bind(e.id, f).run(); }
    }
    const due = Object.keys(src).filter((f) => t - seen.get(e.id + "|" + f).first >= WAIT);
    if (!due.length) continue;
    for (const to of Object.keys(LANGS)) { if (to === from) continue; const need = due.filter((f) => !have.has(e.id + "|" + f + "|" + to)); if (need.length) jobs.push({ id: e.id, to, from, inp: Object.fromEntries(need.map((f) => [f, src[f]])) }); }
    if (jobs.length >= room * 3) break;
  }
  let done = 0, failed = 0;
  await Promise.all(jobs.slice(0, room).map(async (j) => {
    try {
      const body = { model: MODEL, max_tokens: 8000, temperature: 0, system: ESYS + ` Target language: ${LANGS[j.to]}.`, messages: [{ role: "user", content: JSON.stringify(j.inp) }] };
      const go = (b) => fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "content-type": "application/json", "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" }, body: JSON.stringify(b) });
      let r = await go({ ...body, output_config: { effort: "low" } }); if (r.status === 400) r = await go(body);
      if (!r.ok) throw new Error("api " + r.status);
      let txt = ((await r.json()).content?.[0]?.text || "").trim(); if (txt.startsWith("```")) txt = txt.replace(/^```[a-z]*\n?/, "").replace(/```$/, "");
      const out = JSON.parse(txt);
      for (const f of Object.keys(j.inp)) {
        const o = String(out[f] || "").replace(/<script/gi, "").trim(), ratio = o.length / Math.max(1, j.inp[f].length);
        if (!o || ratio < 0.2 || ratio > 3 || (f === "desc" && o.length > 400)) { failed++; continue; }
        await db.prepare("INSERT OR IGNORE INTO ent_tr(eid,field,lang,text,created) VALUES(?,?,?,?,?)").bind(j.id, f, j.to, o, t).run(); done++;
      }
    } catch { failed++; }
  }));
  await setMeta(db, "atr_ent:" + day, used + Math.min(room, jobs.length));
  return { done, failed, open: Math.max(0, jobs.length - room) };
}

export async function entityTranslations(db) {   // fuer /api/entity/tr: {eid: {field: {lang: text}}}
  try {
    const out = {};
    for (const r of (await db.prepare("SELECT eid,field,lang,text FROM ent_tr").all()).results || []) ((out[r.eid] ||= {})[r.field] ||= {})[r.lang] = r.text;
    return out;
  } catch { return {}; }
}
