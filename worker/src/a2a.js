// A2A-Endpunkt (JSON-RPC 2.0, nur lesen, ohne Anmeldung): beantwortet Textanfragen mit passenden Folgen aus SITE/episodes.json.
// Beschrieben in /.well-known/agent-card.json (supportedInterfaces).
const H = { "access-control-allow-origin": "*", "access-control-allow-headers": "content-type, a2a-version", "access-control-allow-methods": "POST, OPTIONS", "content-type": "application/json" };
const STOP = new Set("the a an and or of for to in on with about what which who is are was how do does can i me my you your please find show give need want episode episodes podcast folge folgen zu ueber über und der die das ein eine mit für wie was welche gibt es".split(" "));
const LANG = { english: "en", englisch: "en", german: "de", deutsch: "de", french: "fr", spanish: "es", italian: "it", dutch: "nl", portuguese: "pt", polish: "pl", turkish: "tr", japanese: "ja", korean: "ko", chinese: "zh", arabic: "ar", hindi: "hi", swedish: "sv" };

const reply = (id, result, error) => new Response(JSON.stringify(error ? { jsonrpc: "2.0", id: id ?? null, error } : { jsonrpc: "2.0", id: id ?? null, result }), { status: 200, headers: H });

async function search(env, q) {
  const r = await fetch(`${env.SITE}/episodes.json`, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!r.ok) return null;
  const eps = (await r.json()).episodes || [];
  const words = q.toLowerCase().replace(/[^\p{L}\p{N}+#. -]/gu, " ").split(/\s+/).filter((w) => w.length > 1 && !STOP.has(w));
  const lang = words.map((w) => LANG[w]).find(Boolean) || "";
  const terms = words.filter((w) => !LANG[w]);
  const scored = eps.filter((e) => !lang || e.language === lang).map((e) => {
    const t = (e.title || "").toLowerCase(), s = ((e.summary || "") + " " + (e.categories || []).join(" ") + " " + (e.tags || []).join(" ")).toLowerCase();
    let n = 0; for (const w of terms) { if (t.includes(w)) n += 3; else if (s.includes(w)) n += 1; }
    return { e, n };
  }).filter((x) => x.n > 0 || !terms.length).sort((a, b) => b.n - a.n || String(b.e.date).localeCompare(String(a.e.date)));
  return scored.slice(0, 5).map((x) => x.e);
}

export async function handleA2a(env, request) {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: H });
  if (request.method !== "POST") return new Response(JSON.stringify({ error: "POST a JSON-RPC 2.0 request" }), { status: 405, headers: H });
  let b; try { b = await request.json(); } catch { return reply(null, null, { code: -32700, message: "Parse error" }); }
  if (!b || b.jsonrpc !== "2.0" || typeof b.method !== "string") return reply(b && b.id, null, { code: -32600, message: "Invalid Request" });
  if (b.method !== "message/send" && b.method !== "SendMessage") return reply(b.id, null, { code: -32601, message: "Method not found; supported: message/send" });
  const parts = (b.params && b.params.message && b.params.message.parts) || [];
  const q = parts.map((p) => (p && typeof p.text === "string" ? p.text : "")).join(" ").trim().slice(0, 300);
  if (!q) return reply(b.id, null, { code: -32602, message: "Invalid params: message.parts needs a text part" });
  const hits = await search(env, q);
  if (!hits) return reply(b.id, null, { code: -32603, message: "Episode index unavailable" });
  const text = hits.length
    ? "Matching M365.FM episodes:\n" + hits.map((e) => `- ${e.title} (${e.language}, ${e.date}): ${e.url}`).join("\n")
    : "No matching episodes found. Browse https://www.m365.fm/llms.txt or https://www.m365.fm/episodes.json.";
  return reply(b.id, { kind: "message", role: "agent", messageId: crypto.randomUUID(), parts: [{ kind: "text", text }], metadata: { episodes: hits.map((e) => e.url) } });
}
