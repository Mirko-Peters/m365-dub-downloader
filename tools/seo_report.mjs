// SEO-Bericht fuer alle Episoden (episodes/*.json + data/articles) und - ueber stdin geliefert - Community-Inhalte.
// Aufruf: echo '{"author":{...},"items":[...]}' | node tools/seo_report.mjs   ->  JSON auf stdout
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";
import { seoCheck, aiPrompt } from "../worker/src/seo.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const J = (p) => JSON.parse(readFileSync(join(root, p), "utf8"));
const extras = (() => { try { return JSON.parse(readFileSync(0, "utf8") || "{}"); } catch { return {}; } })();
const ents = new Map(J("data/entities.json").map((e) => [e.id, e]));
const norm = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").trim();
const byName = new Map(); for (const e of ents.values()) for (const n of [e.id, e.name, ...(e.aliases || [])]) byName.set(norm(n), e.id);
const plain = (h) => String(h || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
const items = [], urls = extras.urls || {};

for (const f of readdirSync(join(root, "episodes")).filter((x) => x.endsWith(".json"))) {
  const id = f.replace(/\.json$/, ""), ep = J(`episodes/${f}`), apath = `data/articles/${id}.json`, art = existsSync(join(root, apath)) ? J(apath) : {};
  for (const [lang, e] of Object.entries(ep)) {
    const a = art[lang]; if (!a && lang !== "de") continue;
    const tags = String(e.tags || "").split(",").map(norm).filter(Boolean), topics = [...new Set(tags.map((t) => byName.get(t)).filter(Boolean))].slice(0, 6);
    const rep = seoCheck({
      kind: "episode", lang, title: plain(e.title), description: plain(e.desc).slice(0, 155), html: a ? a.html : "", topics, header: true,
      images: 2 + (a && a.info ? 1 : 0) + Math.min(2, ((a && a.infos) || []).length), faq: ((a && a.faq) || []).length, transcript: !!e.tr, author: extras.author || null,
    }, { entities: ents });
    items.push({ kind: "episode", id, lang, title: plain(e.title), url: urls[`${id}:${lang}`] || "", article: !!a, ...pick(rep) });
  }
}
for (const x of extras.items || []) {
  const rep = seoCheck({ kind: x.kind, lang: x.lang, title: x.title, description: x.summary || x.description || "", body: x.body || x.description || "", topics: x.topics || [], header: true, author: x.author || null }, { entities: ents });
  items.push({ kind: x.kind, id: x.id, lang: x.lang, title: x.title, url: x.url || "", handle: x.handle || "", article: true, ...pick(rep) });
}
function pick(r) {
  return { score: r.score, grade: r.grade, words: r.words, intent: r.intent, todo: r.todo,
    checks: r.checks.map((c) => ({ id: c.id, ok: c.ok, label: c.label, detail: c.detail, fix: c.fix, tool: c.tool || "" })),
    suggest: { topics: r.suggestions.topics.map((t) => t.id), links: r.suggestions.links.slice(0, 6).map((t) => t.markup), create: r.suggestions.create.map((t) => t.name) } };
}
items.sort((a, b) => a.score - b.score);
console.log(JSON.stringify({ generated: new Date().toISOString().slice(0, 10), average: items.length ? Math.round(items.reduce((a, x) => a + x.score, 0) / items.length) : 0, items }));
