// M365 Show (Livestreams auf YouTube, data/live.json -> SITE/live.json): jeder Stream wird ein Event im Community-System (Veranstalter: Admin),
// gelaufene Streams als vergangene Events, geplante als kommende; dazu je Stream ein Beitrag im Feed des Admins (Seite /live/<slug>/).
// Idempotent ueber das Event-Handle live-<youtube-id> und die Feed-URL. Nur Englisch (die Live-Show gibt es nur auf Englisch).
const now = () => Math.floor(Date.now() / 1000);
const slugify = (t) => String(t || "").toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss").replace(/[^\x00-\x7f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 60);
const stamp = (s) => (s || "").replace("Z", "").slice(0, 16);   // YYYY-MM-DDTHH:MM

async function adminOwner(db, env) {
  const r = await db.prepare("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").first().catch(() => null);
  if (r) return r;
  for (const a of (env.ADMIN_SUBS || "").split(",").map((x) => x.trim()).filter(Boolean)) {
    const [pr, ...rest] = a.split(":"); const o = await db.prepare("SELECT id FROM users WHERE provider=? AND sub=?").bind(pr, rest.join(":")).first(); if (o) return o;
  }
  return null;
}

export async function syncLiveEvents(env, entityMap) {
  const db = env.DB, owner = await adminOwner(db, env);
  if (!owner) return { skipped: "kein Admin" };
  let j = null; try { j = await (await fetch(env.SITE + "/live.json", { cf: { cacheTtl: 600 } })).json(); } catch { return { skipped: "live.json nicht erreichbar" }; }
  const streams = (j?.streams || []).filter((s) => s.id && s.title);
  if (!streams.length) return { skipped: "keine Streams" };
  const map = entityMap ? await entityMap(env).catch(() => null) : null;
  const names = map ? [...map.values()].filter((e) => e.type !== "person" && e.type !== "category").flatMap((e) => [e.name, ...(e.aliases || [])].filter((n) => n && n.length >= 4).map((n) => [n.toLowerCase(), e.id])) : [];
  const topicsOf = (title) => { const t = String(title).toLowerCase(), out = []; for (const [n, id] of names) if (t.includes(n) && !out.includes(id)) { out.push(id); if (out.length >= 4) break; } return out; };
  const ch = await db.prepare("SELECT id FROM channels WHERE owner_type='u' AND owner_id=? AND kind='youtube' ORDER BY id LIMIT 1").bind(owner.id).first().catch(() => null);
  const t = now(); let created = 0, updated = 0, posts = 0;
  for (const s of streams.slice(0, 400)) {
    const handle = "live-" + String(s.id).toLowerCase(), start = stamp(s.start || s.published), url = "https://www.youtube.com/watch?v=" + s.id;
    const summary = String(s.description || "").replace(/\s+/g, " ").trim().slice(0, 300), topics = JSON.stringify(topicsOf(s.title));
    if (!start) continue;
    const ex = await db.prepare("SELECT id FROM events WHERE handle=?").bind(handle).first();
    if (ex) {
      const r = await db.prepare("UPDATE events SET title=?,summary=?,start=?,url=?,updated=? WHERE id=? AND (title<>? OR start<>? OR summary<>?)").bind(s.title, summary, start, url, t, ex.id, s.title, start, summary).run(); if (r.meta?.changes) updated++;
    } else {
      await db.prepare("INSERT INTO events(handle,owner_id,org_id,title,summary,about,start,end,mode,location,country,url,tickets_url,free,lang,topics,seeking_sponsor,public,created,updated) VALUES(?,?,NULL,?,?,?,?,'','online','YouTube (M365 Show)','',?,'',1,'en',?,0,1,?,?)")
        .bind(handle, owner.id, s.title, summary, "Live stream of the M365 Show on YouTube. " + summary, start, url, topics, t, t).run(); created++;
    }
    const pageUrl = `${env.SITE}/live/${(String(s.id).toLowerCase() + "-" + slugify(s.title)).replace(/-+$/, "").slice(0, 72)}/`;
    const pub = Math.floor(new Date((s.published || s.start || "").replace("Z", "") + "Z").getTime() / 1000) || t;
    if (ch) { const r = await db.prepare("INSERT OR IGNORE INTO feed_items(channel_id,owner_type,owner_id,url,title,published,summary,topics) VALUES(?,'u',?,?,?,?,?,?)").bind(ch.id, owner.id, pageUrl, s.title, pub, summary, topics).run(); if (r.meta?.changes) posts++; }
  }
  return { streams: streams.length, created, updated, posts };
}
