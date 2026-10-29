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

export async function refreshFeeds(env, max = 8) {
  const db = env.DB, now = Math.floor(Date.now() / 1000);
  const rows = (await db.prepare("SELECT id,owner_type,owner_id,feed FROM channels WHERE feed<>'' AND fails<5 AND fetched<? ORDER BY fetched ASC LIMIT ?").bind(now - 1800, max).all()).results || [];
  let n = 0;
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
