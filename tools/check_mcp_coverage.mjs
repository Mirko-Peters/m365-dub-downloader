// Taeglicher Abgleich: hat der MCP-Server alle Funktionen der Seite?
//  1) jede API-Route (worker/src/*.js) ist in worker/mcp_coverage.json einem vorhandenen Tool zugeordnet oder begruendet ausgenommen
//  2) jedes Tool steht in einer Anleitung (HOWTO) und hat eine deutsche Beschreibung
//  3) optional: der Live-Server (MCP_URL) bietet genau die Tools des Repos (Deploy aktuell)
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";
import { routes } from "./mcp_routes.mjs";
import { TOOLS, HOWTO } from "../worker/src/mcp.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const cov = JSON.parse(readFileSync(join(root, "worker", "mcp_coverage.json"), "utf8")).routes;
const names = new Set(TOOLS.map((t) => t.name)), problems = [], notes = [];
const live = routes();

for (const r of live) {
  const c = cov[r];
  if (!c) problems.push(`NEUE Seitenfunktion ohne MCP-Tool: \`${r}\` -> Tool in worker/src/mcp.js (BRIDGE) ergänzen und in worker/mcp_coverage.json eintragen (oder mit Begründung als skip).`);
  else if (c.tools) { for (const t of c.tools) if (!names.has(t)) problems.push(`Route \`${r}\` verweist auf fehlendes Tool \`${t}\`.`); }
  else if (!c.skip) problems.push(`Route \`${r}\`: Eintrag braucht tools oder skip.`);
}
for (const r of Object.keys(cov)) if (!live.includes(r)) notes.push(`Eintrag \`${r}\` in mcp_coverage.json hat keine Route mehr (aufräumen).`);

const inHowto = new Set(HOWTO.flatMap((h) => h.tools));
const adminOnly = new Set(["get_help", "list_event_transfers", "mark_event_transfers_done", "list_video_todo", "list_podcast_todo"]);
for (const t of TOOLS) {
  if (!inHowto.has(t.name) && !adminOnly.has(t.name)) problems.push(`Tool \`${t.name}\` steht in keiner Anleitung (HOWTO) - get_help und Skill kennen es sonst nicht.`);
  if (!t.de) problems.push(`Tool \`${t.name}\` hat keine deutsche Beschreibung (de).`);
}
for (const h of HOWTO) for (const t of h.tools) if (!names.has(t)) problems.push(`Anleitung \`${h.id}\` nennt unbekanntes Tool \`${t}\`.`);

if (process.env.MCP_URL) {
  try {
    const r = await fetch(process.env.MCP_URL, { method: "POST", headers: { "content-type": "application/json", accept: "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }) });
    const liveNames = new Set((await r.json()).result.tools.map((t) => t.name));
    const missing = [...names].filter((n) => !liveNames.has(n)), extra = [...liveNames].filter((n) => !names.has(n));
    if (missing.length) problems.push(`Live-Server (${process.env.MCP_URL}) kennt noch nicht: ${missing.join(", ")} - Worker-Deploy prüfen.`);
    if (extra.length) notes.push(`Live-Server hat zusätzliche Tools: ${extra.join(", ")}.`);
  } catch (e) { notes.push(`Live-Server nicht erreichbar: ${e.message}`); }
}

const report = `# MCP-Abgleich (${new Date().toISOString().slice(0, 10)})\n\n${live.length} API-Routen, ${TOOLS.length} Tools.\n\n` +
  (problems.length ? `## Zu tun\n${problems.map((p) => `- ${p}`).join("\n")}\n` : "Alles abgedeckt.\n") + (notes.length ? `\n## Hinweise\n${notes.map((p) => `- ${p}`).join("\n")}\n` : "");
console.log(report);
if (process.env.REPORT_FILE) writeFileSync(process.env.REPORT_FILE, report);
process.exit(problems.length ? 1 : 0);
