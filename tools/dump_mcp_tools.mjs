import { TOOLS, HOWTO, needsToken } from "../worker/src/mcp.js";
console.log(JSON.stringify({ tools: TOOLS.map(t => ({ name: t.name, write: needsToken(t), en: t.description, de: t.de || t.description })), howto: HOWTO }));
