// On-Page-SEO-Check fuer Blog, Video, Podcast und Episoden - reine Funktionen ohne Datenbank, damit derselbe Code
// im Worker (Editor, API, MCP) und im Seitenbau (tools/seo_report.mjs) laeuft.
// Jede Pruefung liefert: ok (true/false/null = nicht pruefbar), score (0..1), Text und Fix auf de/en und das MCP-Tool zum Beheben.

const DE = (de, en) => ({ de, en });
const strip = (h) => String(h || "").replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
const CJK = /^(ja|ko|zh|th)/;
const countWords = (t, lang) => { t = String(t || "").trim(); if (!t) return 0; return CJK.test(lang || "") ? Math.round(t.replace(/\s/g, "").length / 2.5) : t.split(/\s+/).length; };
const clamp = (x) => Math.max(0, Math.min(1, x));
const norm = (s) => String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");

// ---------- Eingabe aufbereiten ----------
// Wiki-Markup (Blog, Feed-Texte): ## Ueberschrift, - / 1. Listen, [[id|Text]] Entitaeten, {{ref|...}} Quellen, {{img|url|alt}} Bilder
export function fromWiki(body) {
  body = String(body || "");
  const lines = body.split("\n"), h2 = [], paras = []; let lists = 0, ordered = 0, cur = [], inList = false;
  const flush = () => { if (cur.length) paras.push(cur.join(" ")); cur = []; };
  for (const ln of lines) {
    let m;
    if (!ln.trim()) { flush(); inList = false; continue; }
    if ((m = /^(#{2,3})\s+(.+)$/.exec(ln))) { flush(); inList = false; if (m[1].length === 2) h2.push(m[2]); continue; }
    if ((m = /^(-|\d+\.)\s+/.exec(ln))) { flush(); if (!inList) { lists++; if (m[1] !== "-") ordered++; inList = true; } continue; }
    inList = false; cur.push(ln.trim());
  }
  flush();
  const imgs = [...body.matchAll(/\{\{img\|([^|{}]*)\|([^{}]*)\}\}/g)];
  const clean = (s) => s.replace(/\{\{img\|[^{}]*\}\}|\{\{ref\|[^{}]*\}\}|\{\{cn\}\}/g, " ").replace(/\[\[[a-z0-9-]+\|?([^\]]*)\]\]/g, "$1").replace(/[*#>]/g, "");
  const text = clean(body.replace(/^(-|\d+\.)\s+/gm, "").replace(/^#{2,3}\s+/gm, ""));
  return {
    text: text.replace(/\s+/g, " ").trim(), h2, firstPara: clean(paras[0] || "").replace(/\s+/g, " ").trim(), lists, ordered, tables: 0,
    entityLinks: [...body.matchAll(/\[\[([a-z0-9-]{2,48})(?:\|[^\]]*)?\]\]/g)].map((m) => m[1]),
    refs: [...body.matchAll(/\{\{ref\|[^{}]*\}\}/g)].length,
    plainLinks: [...body.replace(/\{\{[^{}]*\}\}/g, "").matchAll(/https?:\/\/\S+/g)].length,
    images: imgs.length, imagesNoAlt: imgs.filter((m) => !m[2].trim()).length,
  };
}
// HTML (Artikel der Episoden-Seiten)
export function fromHtml(html) {
  html = String(html || "");
  const paras = [...html.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/gi)].map((m) => strip(m[1])).filter(Boolean);
  const imgs = [...html.matchAll(/<img\b[^>]*>/gi)].map((m) => m[0]);
  const links = [...html.matchAll(/<a\b[^>]*href="([^"]+)"/gi)].map((m) => m[1]);
  return {
    text: strip(html), h2: [...html.matchAll(/<h2\b[^>]*>([\s\S]*?)<\/h2>/gi)].map((m) => strip(m[1])), firstPara: paras[0] || "",
    lists: (html.match(/<(ul|ol)\b/gi) || []).length, ordered: (html.match(/<ol\b/gi) || []).length, tables: (html.match(/<table\b/gi) || []).length,
    entityLinks: links.map((u) => /\/entity\/([a-z0-9-]+)\/?/.exec(u)?.[1]).filter(Boolean), refs: links.filter((u) => /^https?:\/\//.test(u)).length, plainLinks: 0,
    images: imgs.length, imagesNoAlt: imgs.filter((t) => !/\balt="[^"]+"/i.test(t)).length,
  };
}

// ---------- Suchabsicht (Heuristik) ----------
const Q = /^(was|wie|warum|wann|wo|wer|welche[rsmn]?|wozu|wieso|how|what|why|when|where|which|who|can|should|is|are|does)\b|\?/i;
const CMP = /\b(vs\.?|versus|unterschied|unterschiede|vergleich|difference|differences|compared?|comparison)\b/i;
const HOW = /(anleitung|schritt|einrichten|einrichtung|how to|guide|tutorial|setup|konfigur|step[- ]by[- ]step)/i;
export function intentOf(title) { return CMP.test(title) ? "compare" : HOW.test(title) ? "howto" : Q.test(title) ? "question" : "info"; }
const INTENT_DE = { compare: "Vergleich", howto: "Anleitung", question: "Frage", info: "Information" };

// ---------- Entitaeten-Vorschlaege anhand des Inhalts ----------
// entities: Map id -> { name, aliases[], type, desc{en,de}, outdated, replaced_by }. Liefert
//  topics   - passende Entitaeten, die noch nicht als Thema gesetzt sind (Hauptvorschlag: add_topic)
//  links    - Entitaeten, die im Text vorkommen, aber noch nicht mit [[id|Text]] verlinkt sind
//  create   - haeufige Fachbegriffe ohne Entitaet (Heuristik; erst search_entities, dann create_entity)
const STOP = new Set("the and for with this that from your you our are was were not but can will has have how what why when who which there their about into over more most also any all new use using used one two three des der die das und ein eine einer eines mit von für bei auf zum zur dem den ist sind wird wurde werden nicht auch noch wie was warum wenn dann diese dieser dieses wir ihr sie ich du es im am an in zu so als oder aber nur schon sehr mehr alle alles bitte teil neue neuer neues microsoft".split(" "));
const escRe = (x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
export function suggestEntities(inp, entities, opt = {}) {
  if (!entities || !entities.values) return { topics: [], links: [], create: [] };
  const P = inp.html != null ? fromHtml(inp.html) : fromWiki(inp.body != null ? inp.body : inp.text || "");
  const title = String(inp.title || ""), text = norm(title + " \n " + P.text), tn = norm(title), intro = norm(P.text.split(/\s+/).slice(0, 100).join(" "));
  const h2n = P.h2.map(norm), have = new Set((inp.topics || []).map(String)), linked = new Set(P.entityLinks), cands = [];
  for (const e of entities.values()) {
    if (!e || e.outdated || e.replaced_by || !e.id) continue;
    const names = [...new Set([e.name, ...(e.aliases || [])].map(norm).filter((n) => n && n.length >= 3 && !STOP.has(n)))];
    let count = 0, via = "";
    for (const n of names) {
      if (!text.includes(n)) continue;
      const c = (text.match(new RegExp("(?<![\\p{L}\\p{N}])" + escRe(n) + "(?![\\p{L}\\p{N}])", "gu")) || []).length;
      if (c > count) { count = c; via = n; }
    }
    if (!count) continue;
    const inTitle = names.some((n) => tn.includes(n)), inIntro = names.some((n) => intro.includes(n)), inH2 = names.some((n) => h2n.some((h) => h.includes(n)));
    const score = Math.round((Math.log2(1 + count) * 2 + (inTitle ? 3 : 0) + (inIntro ? 1.5 : 0) + (inH2 ? 1 : 0) + Math.min(1.5, via.length / 12) + (["product", "platform", "concept", "cert"].includes(e.type) ? 0.5 : 0)) * 10) / 10;
    const m = new RegExp("(?<![\\p{L}\\p{N}])" + escRe(via) + "(?![\\p{L}\\p{N}])", "iu").exec((P.text || "").normalize("NFKD").replace(/[̀-ͯ]/g, ""));
    cands.push({ id: e.id, name: e.name, type: e.type || "", score, count, in_title: inTitle, in_intro: inIntro, topic: have.has(e.id), linked: linked.has(e.id), match: m ? m[0] : via, description: (e.desc && (e.desc.de || e.desc.en)) || "" });
  }
  cands.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
  const topics = cands.filter((c) => !c.topic && (c.score >= 3.5 || c.in_title)).slice(0, opt.limit || 6).map((c) => ({ ...c, action: "add_topic" }));
  const links = cands.filter((c) => !c.linked).slice(0, opt.linkLimit || 10).map((c) => ({ ...c, action: "link", markup: `[[${c.id}|${c.match}]]` }));
  // Begriffe ohne Entitaet: Eigennamen aus 2-4 Grossbuchstaben-Woertern oder Abkuerzungen, mind. 2x im Text
  const known = new Set([...entities.values()].flatMap((e) => [e.name, ...(e.aliases || [])].map(norm))), seen = new Map();
  const raw = title + " " + P.text;
  for (const m of raw.matchAll(/\b(?:[A-Z][\p{L}0-9]+(?:\s+[A-Z][\p{L}0-9]+){1,3}|[A-Z]{3,8})\b/gu)) {
    const t = m[0].trim(), k = norm(t); if (known.has(k) || STOP.has(k) || k.length < 3) continue;
    if (!k.includes(" ") && /^(und|der|die|das|ein|eine|the|and)$/.test(k)) continue;
    if (t.split(/\s+/).every((w) => STOP.has(norm(w)))) continue;
    if (/^(ihr|ihre|ihrem|ihrer|ihren|ihres|sein|seine|seinem|seiner|mein|meine|dein|deine|unser|unsere|euer|eure|dies|diese|dieser|dieses|diesem|jede|jeder|jedes|manche|alle|kein|keine|das|der|die|den|dem|des|ein|eine|einen|einem|einer|eines|wenn|wie|was|wer|wir|man|hier|dort|dann|doch|auch|noch|schon|the|this|that|these|those|your|our|their|his|her|its|my|an|a|in|on|at|for|with|and|or|but|if|when|how|what|why|here|there|then)\s/i.test(t + " ")) continue;
    seen.set(k, { name: t, count: (seen.get(k)?.count || 0) + 1 });
  }
  const create = [...seen.values()].filter((x) => x.count >= 2 && !cands.some((c) => norm(c.name).includes(norm(x.name)) || norm(x.name).includes(norm(c.name)))).sort((a, b) => b.count - a.count).slice(0, 5).map((x) => ({ name: x.name, count: x.count, action: "create_entity" }));
  return { topics, links, create };
}

// ---------- Hauptfunktion ----------
// inp: { kind: blog|feed|podcast|video|episode, lang, title, description, body (Wiki-Markup) | html, text, topics[], keyword,
//        header: true|false|null, images: Zahl|null (null = Editor kann (noch) keine Bilder), faq: Zahl, transcript: true|false|null }
// ctx: { entities: Map|Set (ids der bekannten Entitaeten; Map mit {name,aliases} hilft fuer die Hauptentitaet) }
export function seoCheck(inp, ctx = {}) {
  const kind = inp.kind || "blog", lang = inp.lang || "en", title = String(inp.title || "").trim(), desc = String(inp.description || "").trim();
  const P = inp.html != null ? fromHtml(inp.html) : fromWiki(inp.body != null ? inp.body : inp.text || "");
  if (inp.html == null && inp.body == null && inp.text != null) { P.text = String(inp.text); P.firstPara = P.text.split(/\n\s*\n/)[0] || ""; }
  const topics = [...new Set((inp.topics || []).map(String))], ents = ctx.entities || null;
  const has = (id) => !ents || (ents.has ? ents.has(id) : false);
  const entName = (id) => (ents && ents.get && ents.get(id)?.name) || "";
  const words = countWords(P.text, lang), first100 = P.text.split(/\s+/).slice(0, 100).join(" ");
  const kw = norm(inp.keyword || entName(topics[0]) || title.split(/[:\-–—|]/)[0].trim().split(/\s+/).slice(0, 4).join(" "));
  const intent = intentOf(title), checks = [];
  const add = (id, group, weight, score, label, detail, fix, tool) => checks.push({ id, group, weight, score: score === null ? null : clamp(score), ok: score === null ? null : score >= 0.999 ? true : score >= 0.5 ? "warn" : false, label, detail, fix, tool });

  // 1 Titel
  const tl = title.length;
  add("title", "meta", 6, !tl ? 0 : tl >= 30 && tl <= 65 ? 1 : tl >= 20 && tl <= 75 ? 0.6 : 0.25, DE("Titel", "Title"),
    DE(`${tl} Zeichen (ideal 30–65)`, `${tl} characters (ideal 30–65)`), DE("Titel auf 30–65 Zeichen bringen, das Hauptthema vorn nennen.", "Bring the title to 30–65 characters and put the main topic first."));
  // 2 Meta-Description
  const dl = desc.length, dsame = norm(desc) === norm(title);
  add("meta", "meta", 12, !dl ? 0 : dsame ? 0.2 : dl >= 120 && dl <= 160 ? 1 : dl >= 90 && dl <= 175 ? 0.7 : dl >= 50 ? 0.4 : 0.2, DE("Meta-Description", "Meta description"),
    !dl ? DE("fehlt", "missing") : dsame ? DE("identisch mit dem Titel", "identical to the title") : DE(`${dl} Zeichen (ideal 120–160)`, `${dl} characters (ideal 120–160)`),
    DE("Kurzfassung in 120–160 Zeichen: Thema, Nutzen und das Hauptwort. Nicht den Titel wiederholen.", "Summary in 120–160 characters: topic, benefit and the main keyword. Do not repeat the title."), "summary");
  // 3 Header-Grafik
  add("header", "media", 8, inp.header === null || inp.header === undefined ? null : inp.header ? 1 : 0, DE("Header-Grafik / Titelbild", "Header graphic / cover"),
    inp.header ? DE("vorhanden", "present") : inp.header === false ? DE("fehlt", "missing") : DE("nicht prüfbar", "not checkable"), DE("Ein eigenes Titelbild (1200×630) hinterlegen.", "Add a cover image (1200×630)."));
  // 4 Bilder
  const imgN = inp.images === undefined ? P.images : inp.images;
  const imgScore = imgN === null ? null : clamp(imgN / 3) * (P.imagesNoAlt ? 0.8 : 1);
  add("images", "media", 10, imgScore, DE("Mindestens 3 Bilder mit Alt-Text", "At least 3 images with alt text"),
    imgN === null ? DE("Der Editor unterstützt für diesen Inhaltstyp noch keine Bilder im Text – wird nicht gewertet.", "The editor does not support images in the text for this content type yet – not scored.") : DE(`${imgN} Bild(er)${P.imagesNoAlt ? `, ${P.imagesNoAlt} ohne Alt-Text` : ""}`, `${imgN} image(s)${P.imagesNoAlt ? `, ${P.imagesNoAlt} without alt text` : ""}`),
    DE("Mindestens 3 aussagekräftige Bilder oder Grafiken einbauen, jedes mit Alt-Text: im Editor mit dem Bild-Button (🖼) oder als {{img|https://…/bild.jpg|Alt-Text}}.", "Add at least 3 meaningful images or graphics, each with alt text: with the image button (🖼) in the editor or as {{img|https://…/image.jpg|alt text}}."));
  // 5 Textlaenge
  const min = { blog: 600, feed: 300, podcast: 300, video: 300, episode: 800 }[kind] || 300;
  add("length", "content", 12, clamp(words / min), DE("Textlänge", "Text length"), DE(`${words} Wörter (Ziel ab ${min})`, `${words} words (goal ${min}+)`),
    DE(`Text auf mindestens ${min} Wörter ausbauen: Beispiele, Schritte, Hintergründe.`, `Expand the text to at least ${min} words: examples, steps, background.`), kind === "blog" ? "save_blog_post" : "save_feed_item_text");
  // 6 Struktur
  const intro = countWords(P.firstPara, lang);
  const struct = (P.h2.length >= 2 ? 0.5 : P.h2.length === 1 ? 0.25 : 0) + (intro >= 25 ? 0.3 : intro >= 10 ? 0.15 : 0) + (P.lists ? 0.2 : 0);
  add("structure", "content", 8, struct, DE("Struktur (Zwischenüberschriften, Einstieg, Liste)", "Structure (subheadings, intro, list)"),
    DE(`${P.h2.length} Zwischenüberschrift(en), Einstieg ${intro} Wörter, ${P.lists} Liste(n)`, `${P.h2.length} subheading(s), intro ${intro} words, ${P.lists} list(s)`),
    DE("Mindestens zwei ##-Zwischenüberschriften, einen klaren Einstiegsabsatz und eine Liste.", "At least two ## subheadings, a clear intro paragraph and a list."), kind === "blog" ? "save_blog_post" : "save_feed_item_text");
  // 7 Suchabsicht
  const inTitle = kw && norm(title).includes(kw), inFirst = kw && norm(first100).includes(kw), inH2 = kw && P.h2.some((h) => norm(h).includes(kw));
  let fit = 0, fitMsg;
  if (intent === "question") { fit = intro >= 25 && kw && norm(P.firstPara).includes(kw) ? 1 : (inp.faq ? 0.7 : 0); fitMsg = DE("Die Frage wird im ersten Absatz direkt beantwortet", "The question is answered directly in the first paragraph"); }
  else if (intent === "howto") { fit = P.ordered ? 1 : P.h2.length >= 3 ? 0.6 : 0; fitMsg = DE("Anleitung hat nummerierte Schritte", "How-to has numbered steps"); }
  else if (intent === "compare") { fit = P.tables || P.lists ? 1 : P.h2.length >= 3 ? 0.6 : 0; fitMsg = DE("Vergleich ist strukturiert (Liste/Tabelle/Abschnitte)", "Comparison is structured (list/table/sections)"); }
  else { fit = intro >= 25 && P.h2.length >= 2 ? 1 : intro >= 25 ? 0.6 : 0.2; fitMsg = DE("Einstieg erklärt das Thema, Abschnitte vertiefen es", "Intro explains the topic, sections go deeper"); }
  const kwScore = (inTitle ? 0.35 : 0) + (inFirst ? 0.35 : 0) + (inH2 ? 0.3 : 0);
  add("intent", "intent", 14, kwScore * 0.5 + fit * 0.5, DE(`Suchabsicht (erkannt: ${INTENT_DE[intent]})`, `Search intent (detected: ${intent})`),
    DE(`Hauptbegriff „${kw}“: im Titel ${inTitle ? "✓" : "✗"}, in den ersten 100 Wörtern ${inFirst ? "✓" : "✗"}, in einer Überschrift ${inH2 ? "✓" : "✗"}. ${fitMsg.de}: ${fit >= 1 ? "✓" : fit > 0 ? "teilweise" : "✗"}`,
       `Main term “${kw}”: in title ${inTitle ? "✓" : "✗"}, in first 100 words ${inFirst ? "✓" : "✗"}, in a heading ${inH2 ? "✓" : "✗"}. ${fitMsg.en}: ${fit >= 1 ? "✓" : fit > 0 ? "partly" : "✗"}`),
    DE("Hauptbegriff in Titel, Einstieg und eine Überschrift setzen und die Form zur Suchabsicht wählen (Frage → direkte Antwort, Anleitung → nummerierte Schritte, Vergleich → Liste/Tabelle).",
       "Use the main term in title, intro and one heading and choose the form that fits the intent (question → direct answer, how-to → numbered steps, comparison → list/table)."), kind === "blog" ? "save_blog_post" : "save_feed_item_text");
  // 8 Entitaeten
  const unknown = topics.filter((t) => !has(t)), linked = [...new Set(P.entityLinks)], badLinks = linked.filter((t) => !has(t));
  const mainEnt = topics[0], mainNames = mainEnt ? [norm(entName(mainEnt)), ...((ents && ents.get && ents.get(mainEnt)?.aliases) || []).map(norm)].filter(Boolean) : [];
  const mainIn = mainEnt && (mainNames.some((n) => norm(title).includes(n) || norm(first100).includes(n)) || P.entityLinks.slice(0, 3).includes(mainEnt));
  const sug = suggestEntities({ ...inp, html: inp.html, body: inp.body, text: inp.text }, ents && ents.values ? ents : null);
  const es = (topics.length >= 3 ? 0.4 : topics.length === 2 ? 0.3 : topics.length === 1 ? 0.15 : 0) + (linked.length >= 3 ? 0.35 : linked.length >= 1 ? 0.2 : 0) + (mainIn || (!ents && topics.length) ? 0.25 : 0);
  add("entities", "entities", 14, es - (unknown.length || badLinks.length ? 0.2 : 0) - (sug.topics.length >= 2 && topics.length < 3 ? 0.1 : 0), DE("Entitäten (Themen + Verlinkung)", "Entities (topics + links)"),
    DE(`${topics.length} Thema/Themen gesetzt, ${linked.length} Entität(en) im Text verlinkt${unknown.length ? `; unbekannt: ${unknown.join(", ")}` : ""}${badLinks.length ? `; kaputte Links: ${badLinks.join(", ")}` : ""}; Hauptentität im Titel/Einstieg: ${mainIn ? "✓" : "✗"}${sug.topics.length ? `; passende Themen noch nicht gesetzt: ${sug.topics.map((x) => x.id).join(", ")}` : ""}${sug.links.length ? `; ${sug.links.length} Erwähnung(en) ohne Link` : ""}`,
       `${topics.length} topic(s) set, ${linked.length} entity link(s) in the text${unknown.length ? `; unknown: ${unknown.join(", ")}` : ""}${badLinks.length ? `; broken links: ${badLinks.join(", ")}` : ""}; main entity in title/intro: ${mainIn ? "✓" : "✗"}${sug.topics.length ? `; matching topics not set yet: ${sug.topics.map((x) => x.id).join(", ")}` : ""}${sug.links.length ? `; ${sug.links.length} mention(s) without a link` : ""}`),
    DE("3–5 Themen (Entitäten statt Kategorien) setzen, die Hauptentität im Titel oder Einstieg nennen und mindestens drei Entitäten im Text mit [[id|Text]] verlinken. Fehlt eine Entität: erst mit search_entities suchen, sonst create_entity.",
       "Set 3–5 topics (entities instead of categories), name the main entity in the title or intro and link at least three entities in the text with [[id|text]]. If an entity is missing: search_entities first, then create_entity."), "search_entities");
  // 9 Quellen
  add("sources", "content", 6, kind === "episode" ? clamp((P.refs || 0) / 1) : clamp(P.refs / 1) - (P.plainLinks ? 0.3 : 0), DE("Quellen / externe Belege", "Sources / external references"),
    DE(`${P.refs} Quelle(n)${P.plainLinks ? `, ${P.plainLinks} einfache Links (werden entfernt)` : ""}`, `${P.refs} source(s)${P.plainLinks ? `, ${P.plainLinks} plain links (are removed)` : ""}`),
    DE("Mindestens eine Quelle als {{ref|Titel|https://url|Herausgeber|Datum}} angeben.", "Add at least one source as {{ref|Title|https://url|Publisher|Date}}."), kind === "blog" ? "save_blog_post" : "save_feed_item_text");
  // 9b Kernpunkte (eigenes Feld, 3-6 Punkte)
  const kpN = Array.isArray(inp.keypoints) ? inp.keypoints.length : inp.keypoints;
  add("keypoints", "content", 5, kpN === undefined || kpN === null ? null : kpN >= 3 && kpN <= 6 ? 1 : kpN >= 1 ? 0.5 : 0, DE("Kernpunkte (eigenes Feld)", "Key points (own field)"),
    kpN === undefined || kpN === null ? DE("nicht prüfbar", "not checkable") : DE(`${kpN} Kernpunkt(e) (ideal 3–6)`, `${kpN} key point(s) (ideal 3–6)`),
    DE("3–6 Kernpunkte als kurze, konkrete Aussagen (10–200 Zeichen) im Feld „Kernpunkte“ ergänzen – sie erscheinen als Zusammenfassung über dem Text.", "Add 3–6 key points as short, concrete statements (10–200 characters) in the “Key points” field – they appear as a summary above the text."), "save_blog_post");
  // 10 FAQ / Transkript
  const faqList = Array.isArray(inp.faq) ? inp.faq : null;
  const faq = faqList ? faqList.length : inp.faq != null ? inp.faq : P.h2.filter((h) => /\?\s*$/.test(h)).length, tr = inp.transcript;
  const audio = kind === "podcast" || kind === "video" || kind === "episode";
  add("faq", "intent", 5, clamp(faq ? 1 : 0) * (audio && tr === false ? 0.6 : 1) + (audio && tr ? 0 : 0), DE(audio ? "FAQ und Transkript" : "FAQ / Fragen & Antworten", audio ? "FAQ and transcript" : "FAQ / questions & answers"),
    DE(`${faq} FAQ-Eintrag/Einträge${audio ? `, Transkript: ${tr ? "✓" : tr === false ? "✗" : "?"}` : ""}`, `${faq} FAQ entr${faq === 1 ? "y" : "ies"}${audio ? `, transcript: ${tr ? "✓" : tr === false ? "✗" : "?"}` : ""}`),
    DE("Drei bis fünf echte Fragen mit kurzer Antwort im Feld „FAQ“ ergänzen – das bedient Suchfragen direkt und erzeugt FAQPage-Schema.", "Add three to five real questions with short answers in the “FAQ” field – it serves search questions directly and creates FAQPage schema."), "ask_question");

  // 11 Autor (Author-Box: Profil, Foto, Bio, Expertise, Kanaele, geprueftes Programm) - GEO/E-E-A-T
  const A = inp.author;
  if (A === undefined || A === null) add("author", "author", 8, null, DE("Autor / Author-Box", "Author / author box"), DE("nicht prüfbar", "not checkable"), DE("", ""));
  else {
    const as = (A.profile ? 0.25 : 0) + (A.photo ? 0.15 : 0) + (A.bio >= 120 ? 0.2 : A.bio >= 40 ? 0.1 : 0) + (A.expertise >= 3 ? 0.2 : A.expertise ? 0.1 : 0) + (A.channels >= 2 ? 0.1 : A.channels ? 0.05 : 0) + (A.verified ? 0.1 : 0) + (A.coauthors ? 0.1 : 0);
    add("author", "author", 8, as, DE("Autor / Author-Box (E-E-A-T)", "Author / author box (E-E-A-T)"),
      DE(`Profil ${A.profile ? "✓" : "✗"}, Foto ${A.photo ? "✓" : "✗"}, Bio ${A.bio} Zeichen (ideal ab 120), ${A.expertise} Expertise-Thema/Themen (ideal ab 3), ${A.channels} Kanal/Kanäle (ideal ab 2), geprüfter Status ${A.verified ? "✓" : "✗"}${inp.kind === "blog" ? `, Co-Autoren ${A.coauthors || 0}` : inp.kind === "podcast" || inp.kind === "video" ? `, Gäste ${A.coauthors || 0}` : ""}`,
         `Profile ${A.profile ? "✓" : "✗"}, photo ${A.photo ? "✓" : "✗"}, bio ${A.bio} characters (ideal 120+), ${A.expertise} expertise topic(s) (ideal 3+), ${A.channels} channel(s) (ideal 2+), verified status ${A.verified ? "✓" : "✗"}${inp.kind === "blog" ? `, co-authors ${A.coauthors || 0}` : inp.kind === "podcast" || inp.kind === "video" ? `, guests ${A.coauthors || 0}` : ""}`),
      DE("Öffentliches Profil mit Foto, Bio (ab 120 Zeichen, in ganzen Sätzen mit Fachbegriffen), mindestens drei Expertise-Themen und zwei Kanälen ausfüllen; Zertifikate/Programme nachweisen. Bei Blogbeiträgen helfen Co-Autoren mit eigenem Profil, bei Podcast und Video Gäste mit eigenem Profil (set_item_guests). Die Author-Box und das Person-Schema der Seite werden daraus erzeugt.",
         "Complete the public profile with photo, bio (120+ characters, full sentences with domain terms), at least three expertise topics and two channels; verify certifications/programmes. The author box and the page's Person schema are generated from it."), "update_my_profile");
  }

  const scored = checks.filter((c) => c.score !== null), total = scored.reduce((a, c) => a + c.weight, 0);
  const score = total ? Math.round((scored.reduce((a, c) => a + c.weight * c.score, 0) / total) * 100) : 0;
  const grade = score >= 85 ? "green" : score >= 65 ? "good" : score >= 40 ? "weak" : "poor";
  const todo = checks.filter((c) => c.ok === false || c.ok === "warn");
  const ai_questions = [
    DE(`Beantwortet der Text wirklich, was jemand sucht, der „${title}“ googelt (Erkannt: ${INTENT_DE[intent]})? Was fehlt dafür noch?`, `Does the text really answer what someone googling “${title}” wants (detected: ${intent})? What is still missing?`),
    DE("Ist der erste Absatz allein schon eine brauchbare Antwort (Featured Snippet)?", "Is the first paragraph on its own already a usable answer (featured snippet)?"),
    DE("Welche Begriffe im Text sind Produkte, Konzepte oder Personen, für die es eine Entität gibt, aber noch keinen Link?", "Which terms in the text are products, concepts or people that have an entity but no link yet?"),
  ];
  return { kind, lang, score, grade, words, intent, keyword: kw, summary: DE(`${score}/100 – ${todo.length ? todo.length + " Punkt(e) zu verbessern" : "alles passt"}`, `${score}/100 – ${todo.length ? todo.length + " item(s) to improve" : "all good"}`), checks, todo: todo.map((c) => c.id), suggestions: sug, ai_questions };
}

// Fertiger Auftrag fuer eine KI: was fehlt, was zu tun ist, welches Tool. (de|en)
export function aiPrompt(report, ref, lang = "de") {
  const L = (x) => x[lang] || x.en;
  const lines = report.checks.filter((c) => c.ok === false || c.ok === "warn").map((c) => `- ${L(c.label)}: ${L(c.detail)} → ${L(c.fix)}${c.tool ? ` (${c.tool})` : ""}`);
  const sg = report.suggestions || { topics: [], links: [], create: [] };
  if (sg.topics.length) lines.push(lang === "de" ? `- Themen ergänzen (topics): ${sg.topics.map((x) => `${x.id} (${x.name})`).join(", ")}` : `- Add topics: ${sg.topics.map((x) => `${x.id} (${x.name})`).join(", ")}`);
  if (sg.links.length) lines.push(lang === "de" ? `- Beim ersten Vorkommen verlinken: ${sg.links.slice(0, 8).map((x) => x.markup).join(" ")}` : `- Link at first mention: ${sg.links.slice(0, 8).map((x) => x.markup).join(" ")}`);
  if (sg.create.length) lines.push(lang === "de" ? `- Mögliche neue Entitäten (erst search_entities, dann create_entity): ${sg.create.map((x) => x.name).join(", ")}` : `- Possible new entities (search_entities first, then create_entity): ${sg.create.map((x) => x.name).join(", ")}`);
  if (!lines.length) return "";
  return (lang === "de"
    ? `Verbessere die On-Page-SEO von ${ref} (aktuell ${report.score}/100). Zeig mir zuerst jede geplante Textänderung und speichere erst nach meinem OK. Offene Punkte:\n${lines.join("\n")}\nPrüfe danach mit check_seo erneut.`
    : `Improve the on-page SEO of ${ref} (currently ${report.score}/100). Show me every planned text change first and save only after my OK. Open items:\n${lines.join("\n")}\nThen run check_seo again.`);
}
