import { TOOLS, HOWTO } from "../worker/src/mcp.js";
console.log(JSON.stringify({ tools: TOOLS.map(t => ({ name: t.name, write: !!t.write, en: t.description, de: t.de || t.description })), howto: HOWTO }));
