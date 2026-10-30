// Feeds der Creator-Kanaele einsammeln: nur Titel, Link und Datum (kein Volltext), https, begrenzte Groesse
import { cleanText } from "./util.js";
import { goodHost } from "./profiles.js";

const dec = (s) => s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Math.min(+n, 0x10ffff))).replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(Math.min(parseInt(n, 16), 0x10ffff)))
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, "&");
const tag = (blk, name) => { const m = new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, "i").exec(blk); return m ? dec(m[1]).trim() : ""; };

export function parseFeed(xml) {
  const blocks = xml.match(/<(item|entry)[\s>][\s\S]*?<\/\1>/gi) || [], out = [];
  for (const b of blocks.slice(0, 12)) {
    let link = "";
    const alt = /<link[^>]*rel=["']alternate["'][^>]*href=["']([^"']+)["']/i.exec(b) || /<link[^>]*href=["']([^"']+)["'][^>]*rel=["']alternate["']/i.exec(b) || /<link[^>]*href=["']([^"']+)["'][^>]*\/?>/i.exec(b);
    link = alt ? dec(alt[1]) : tag(b, "link");
    const title = cleanText(dec(tag(b, "title")).replace(/<[^>]+>/g, ""), 200).replace(/\s+/g, " ").trim();
    const ds = tag(b, "pubDate") || tag(b, "published") || tag(b, "updated") || tag(b, "dc:date");
    let t = Date.parse(ds); t = Number.isFinite(t) ? Math.floor(t / 1000) : Math.floor(Date.now() / 1000);
    try { const u = new URL(link.trim()); if (u.protocol !== "https:" || !goodHost(u.hostname) || u.username) continue; link = u.href; } catch { continue; }
    if (title.length >= 3 && link.length <= 400) out.push({ title, url: link, t: Math.min(t, Math.floor(Date.now() / 1000)) });
  }
  return out;
}

// Feed automatisch finden: YouTube-Handle -> channel_id, GitHub/Bluesky/Mastodon -> Standard-Feed, sonst <link rel="alternate"> im HTML
async function get(u, ms = 6000) {
  const ctl = new AbortController(), to = setTimeout(() => ctl.abort(), ms);
  try { const r = await fetch(u, { signal: ctl.signal, redirect: "follow", headers: { "user-agent": "M365FM-community-feed/1.0 (+https://dub.m365.fm)", accept: "text/html,application/xml,*/*" } }); return r.ok ? (await r.text()).slice(0, 400000) : ""; } catch { return ""; } finally { clearTimeout(to); }
}
export async function discoverFeed(kind, url) {
  let u; try { u = new URL(url); } catch { return ""; }
  if (u.protocol !== "https:" || !goodHost(u.hostname)) return "";
  const h = u.hostname.replace(/^www\./, ""), seg = u.pathname.split("/").filter(Boolean);
  if (kind === "linkedin" || kind === "x" || kind === "twitch") return "";
  if (kind === "github" && seg[0]) return `https://github.com/${seg[0]}.atom`;
  if (kind === "bluesky" && seg[0] === "profile" && seg[1]) return `https://bsky.app/profile/${seg[1]}/rss`;
  if (kind === "mastodon" && /^@[\w.-]+$/.test(seg[0] || "")) return `https://${u.hostname}/${seg[0]}.rss`;
  const html = await get(u.href); if (!html) return "";
  if (kind === "youtube") { const m = /"(?:channelId|externalId)":"(UC[\w-]{22})"/.exec(html) || /channel_id=(UC[\w-]{22})/.exec(html) || /youtube\.com\/channel\/(UC[\w-]{22})/.exec(html); return m ? `https://www.youtube.com/feeds/videos.xml?channel_id=${m[1]}` : ""; }
  for (const m of html.matchAll(/<link\b[^>]*>/gi)) {
    const t = m[0]; if (!/rel=["']alternate["']/i.test(t) || !/type=["']application\/(rss|atom)\+xml["']/i.test(t)) continue;
    const href = /href=["']([^"']+)["']/i.exec(t); if (!href) continue;
    try { const f = new URL(dec(href[1]), u.href); if (f.protocol === "https:" && goodHost(f.hostname) && !f.username) return f.href; } catch {}
  }
  return "";
}

export async function refreshFeeds(env, max = 8) {
  const db = env.DB, now = Math.floor(Date.now() / 1000);
  const rows = (await db.prepare("SELECT id,owner_type,owner_id,feed FROM channels WHERE feed<>'' AND fails<5 AND fetched<? ORDER BY fetched ASC LIMIT ?").bind(now - 1800, max).all()).results || [];
  let n = 0;
  const nofeed = (await db.prepare("SELECT id,kind,url FROM channels WHERE feed='' AND fails<3 AND fetched<? AND kind NOT IN ('linkedin','x','twitch') ORDER BY fetched ASC LIMIT 3").bind(now - 86400).all()).results || [];
  for (const c of nofeed) { const f = await discoverFeed(c.kind, c.url).catch(() => ""); await db.prepare("UPDATE channels SET feed=?, fetched=?, fails=fails+? WHERE id=?").bind(f, f ? 0 : now, f ? 0 : 1, c.id).run(); }
  for (const c of rows) {
    try {
      const ctl = new AbortController(), to = setTimeout(() => ctl.abort(), 6000);
      const r = await fetch(c.feed, { signal: ctl.signal, headers: { "user-agent": "M365FM-community-feed/1.0 (+https://dub.m365.fm)", accept: "application/rss+xml, application/atom+xml, text/xml, */*" } });
      clearTimeout(to);
      if (!r.ok) throw new Error("http " + r.status);
      const xml = (await r.text()).slice(0, 600000);
      const items = parseFeed(xml); if (!items.length) throw new Error("empty");
      await db.batch([...items.map((i) => db.prepare("INSERT OR IGNORE INTO feed_items(channel_id,owner_type,owner_id,url,title,published) VALUES(?,?,?,?,?,?)").bind(c.id, c.owner_type, c.owner_id, i.url, i.title, i.t)),
        db.prepare("UPDATE channels SET fetched=?, fails=0 WHERE id=?").bind(now, c.id)]);
      n += items.length;
    } catch { await db.prepare("UPDATE channels SET fetched=?, fails=fails+1 WHERE id=?").bind(now, c.id).run(); }
  }
  await db.prepare("DELETE FROM feed_items WHERE published<?").bind(now - 400 * 86400).run();
  return n;
}
