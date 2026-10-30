// Automatische Uebersetzung fehlender EN/DE-Texte von Entitaeten mit Claude Haiku.
// Sicherheitsnetz: nur mit gesetztem Secret ANTHROPIC_API_KEY, Tageslimit, 24 h Wartezeit fuer die Community, Notaus ueber meta tr_off=1.
import { entityMap } from "./entities.js";

const MODEL = "claude-haiku-5-5", DAILY_CAP = 100, PER_RUN = 10, WAIT = 24 * 3600, SKIP_TYPES = ["person", "event", "org"];
const now = () => Math.floor(Date.now() / 1000);
const SYS = "You translate short encyclopedia texts about Microsoft products and IT concepts between English and German. " +
  "Never translate names: product and feature names, session and event titles, person and company names, abbreviations and codes (e.g. Copilot Studio, Power Fx, D365FO, MS-900, M365Con) stay exactly as written. " +
  "Keep the same length, tone and paragraph structure (blank lines between paragraphs). No links, no quotes, no commentary. " +
  "Answer with a JSON object that maps each given key to its translation, and nothing else.";

async function meta(db, k) { return (await db.prepare("SELECT v FROM meta WHERE k=?").bind(k).first())?.v || ""; }
async function setMeta(db, k, v) { await db.prepare("INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(k, String(v)).run(); }

export async function translateStatus(env) {
  const db = env.DB, day = new Date().toISOString().slice(0, 10);
  const pend = (await db.prepare("SELECT COUNT(*) n FROM tr_gap").first())?.n || 0;
  return { key: !!env.ANTHROPIC_API_KEY, enabled: (await meta(db, "tr_off")) !== "1", today: +(await meta(db, "tr_count:" + day)) || 0, cap: DAILY_CAP, open_gaps: pend, last_error: await meta(db, "tr_err") };
}

export async function autoTranslate(env) {
  const db = env.DB;
  if (!env.ANTHROPIC_API_KEY || (await meta(db, "tr_off")) === "1") return { skipped: true };
  const map = await entityMap(env), t = now(), day = new Date().toISOString().slice(0, 10);
  const claimed = new Set(((await db.prepare("SELECT eid FROM entity_claims WHERE status='verified'").all()).results || []).map((r) => r.eid));
  // Luecken ermitteln: Text nur in einer der beiden Sprachen vorhanden
  const gaps = [];
  for (const e of map.values()) {
    if (SKIP_TYPES.includes(e.type) || claimed.has(e.id) || e.outdated || e.replaced_by) continue;
    for (const f of ["desc", "long"]) {
      const v = e[f] || {};
      if ((v.en || "").trim() && !(v.de || "").trim()) gaps.push({ id: e.id, f, from: "en", to: "de", text: v.en });
      if ((v.de || "").trim() && !(v.en || "").trim()) gaps.push({ id: e.id, f, from: "de", to: "en", text: v.de });
    }
  }
  const key = (g) => g.id + "|" + g.f;
  const have = new Map(((await db.prepare("SELECT eid,field,first FROM tr_gap").all()).results || []).map((r) => [r.eid + "|" + r.field, r.first]));
  for (const g of gaps) if (!have.has(key(g))) { await db.prepare("INSERT OR IGNORE INTO tr_gap(eid,field,first) VALUES(?,?,?)").bind(g.id, g.f, t).run(); have.set(key(g), t); }
  const open = new Set(gaps.map(key));
  for (const k of [...have.keys()]) if (!open.has(k)) { const [eid, field] = k.split("|"); await db.prepare("DELETE FROM tr_gap WHERE eid=? AND field=?").bind(eid, field).run(); }
  // Tageslimit und Wartezeit (Community hat zuerst die Chance)
  const used = +(await meta(db, "tr_count:" + day)) || 0, room = Math.min(PER_RUN, DAILY_CAP - used);
  if (room <= 0) return { capped: true };
  const due = gaps.filter((g) => t - have.get(key(g)) >= WAIT).slice(0, room);
  if (!due.length) return { due: 0 };
  const items = Object.fromEntries(due.map((g) => [key(g) + ">" + g.to, `[${g.from}->${g.to}] ${g.text}`]));
  let res;
  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", headers: { "content-type": "application/json", "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" },
      body: JSON.stringify({ model: MODEL, max_tokens: 4000, system: SYS, messages: [{ role: "user", content: JSON.stringify(items) }] }) });
    if (!r.ok) { await setMeta(db, "tr_err", `${r.status} ${t}`); return { error: r.status }; }
    let txt = ((await r.json()).content?.[0]?.text || "").trim();
    if (txt.startsWith("```")) txt = txt.replace(/^```[a-z]*\n?/, "").replace(/```$/, "");
    res = JSON.parse(txt);
  } catch (e) { await setMeta(db, "tr_err", `parse ${t}`); return { error: "parse" }; }
  const byE = new Map();
  for (const g of due) {
    const out = String(res[key(g) + ">" + g.to] || "").replace(`[${g.from}->${g.to}] `, "").replace(/[<>]/g, "").replace(/https?:\/\/\S+/gi, "").trim();
    if (!out || (g.f === "desc" && (out.length < 20 || out.length > 300)) || (g.f === "long" && out.length > 3000)) continue;
    if (!byE.has(g.id)) byE.set(g.id, []);
    byE.get(g.id).push({ ...g, out });
  }
  let done = 0;
  for (const [id, list] of byE) {
    const e = map.get(id); if (!e) continue;
    const { id: _i, ...data } = e;
    for (const g of list) { data[g.f] = { ...(data[g.f] || {}), [g.to]: g.out }; done++; }
    await db.batch([db.prepare("UPDATE entity_rev SET status='old' WHERE eid=? AND status='live'").bind(id),
      db.prepare("INSERT INTO entity_rev(eid,data,summary,user_id,status,created) VALUES(?,?,?,0,'live',?)").bind(id, JSON.stringify(data), "Auto-Übersetzung (Claude Haiku)", t)]);
  }
  await setMeta(db, "tr_count:" + day, used + due.length);
  return { translated: done };
}
