#!/usr/bin/env python3
"""Zweiter Seed: Entitaeten aus dem M365Con-Programm (Dynamics, Logic Apps, Agenten, Fabric, Azure, SharePoint-Governance ...) und Session-Themen.
Idempotent: vorhandene nicht leere Felder bleiben, fehlende werden ergaenzt, Beziehungen werden vereinigt."""
import json
P = "data/entities.json"; PP = "data/m365con_program.json"
D = json.load(open(P)); M = {e["id"]: e for e in D}
MT = "microsoft-tool"


def T(id, type, name, aliases, en, de, rel, long_en="", long_de="", **kw):
    r = [["developed_by", kw.pop("dev", "microsoft")]] if kw.pop("ms", True) and type in ("product", "platform") else []
    for p, lst in rel.items():
        for x in (lst if isinstance(lst, list) else [lst]):
            r.append([p, x])
    e = {"id": id, "type": type, "name": name, "aliases": aliases, "desc": {"en": en, "de": de}, "web": kw.pop("web", ""), "wikidata": "", "wikipedia": kw.pop("wiki", ""), "docs": kw.pop("docs", ""), "rel": r}
    if long_en or long_de:
        e["long"] = {"en": long_en, "de": long_de}
    e.update({k: v for k, v in kw.items() if v not in ("", None)})
    return e


NEW = [
    # ---------- Dynamics 365 / Integration ----------
    T("d365-finance-operations", "product", "Dynamics 365 Finance and Operations", ["D365FO", "D365 F&O", "Dynamics 365 Finance & Operations", "Dynamics 365 for Finance and Operations", "Dynamics AX", "Dynamics 365 Finance"],
      "Cloud ERP application of Dynamics 365 for finance, supply chain, manufacturing and operations; successor of Dynamics AX, usually abbreviated D365FO.",
      "Cloud-ERP-Anwendung von Dynamics 365 für Finanzen, Lieferkette, Fertigung und Betrieb; Nachfolger von Dynamics AX, meist als D365FO abgekürzt.",
      {"instance_of": [MT, "business-application"], "part_of": "dynamics-365", "related_to": ["azure-logic-apps", "dynamics-365-business-events", "d365-data-entities", "dual-write", "dataverse", "power-automate", "business-performance-analytics", "power-bi"], "similar_to": ["dynamics-365-business-central"]},
      docs="https://learn.microsoft.com/dynamics365/finance/", web="https://www.microsoft.com/dynamics-365/products/finance-and-operations", license="paid",
      long_en="Dynamics 365 Finance and Operations (D365FO) runs core ERP processes such as general ledger, accounts payable and receivable, procurement, inventory, production and project accounting for mid-sized and large organisations. It grew out of Dynamics AX and now consists of the Finance and Supply Chain Management applications.\n\nIntegration is a central topic. Typical building blocks are data entities exposed through OData, business events that notify other systems when something happens, dual-write to Dataverse, and orchestration with Azure Logic Apps or Power Automate.",
      long_de="Dynamics 365 Finance and Operations (D365FO) bildet zentrale ERP-Prozesse ab, etwa Hauptbuch, Kreditoren und Debitoren, Einkauf, Lager, Produktion und Projektbuchhaltung für mittlere und große Unternehmen. Es ging aus Dynamics AX hervor und besteht heute aus den Anwendungen Finance und Supply Chain Management.\n\nIntegration ist ein zentrales Thema. Typische Bausteine sind Datenentitäten über OData, Geschäftsereignisse, die andere Systeme über Vorgänge informieren, Dual-Write nach Dataverse und die Orchestrierung mit Azure Logic Apps oder Power Automate."),
    T("dynamics-365-business-central", "product", "Dynamics 365 Business Central", ["Business Central", "D365BC", "BC", "Dynamics NAV"],
      "Cloud ERP for small and mid-sized businesses covering finance, sales, purchasing, inventory and operations; successor of Dynamics NAV, extended with AL and agents.",
      "Cloud-ERP für kleine und mittlere Unternehmen mit Finanzen, Verkauf, Einkauf, Lager und Betrieb; Nachfolger von Dynamics NAV, erweiterbar mit AL und Agenten.",
      {"instance_of": [MT, "business-application"], "part_of": "dynamics-365", "related_to": ["power-platform", "copilot", "ai-agent", "mcp"], "similar_to": ["d365-finance-operations"]},
      docs="https://learn.microsoft.com/dynamics365/business-central/", web="https://www.microsoft.com/dynamics-365/products/business-central", license="paid"),
    T("azure-logic-apps", "product", "Azure Logic Apps", ["Logic Apps", "Azure Logic App", "Logic App Standard"],
      "Cloud integration service of Azure for building workflows and agentic automation with hundreds of connectors, triggers and actions; the Azure counterpart to Power Automate.",
      "Cloud-Integrationsdienst von Azure für Workflows und agentische Automatisierung mit hunderten Konnektoren, Triggern und Aktionen; das Azure-Gegenstück zu Power Automate.",
      {"instance_of": [MT, "developer-tool"], "part_of": "azure", "similar_to": ["power-automate"], "related_to": ["connector", "azure-functions", "azure-api-management", "d365-finance-operations", "dynamics-365-business-events", "microsoft-foundry", "agent-loop", "automation"]},
      docs="https://learn.microsoft.com/azure/logic-apps/", web="https://azure.microsoft.com/products/logic-apps", license="paid", released="2016-07",
      long_en="Azure Logic Apps lets developers and integrators build workflows visually or as code. A workflow starts with a trigger, for example a business event from Dynamics 365 or a message in a queue, and runs actions through managed or built-in connectors. Consumption logic apps are billed per execution; Standard logic apps run on a dedicated plan with VNet integration and local development in VS Code.\n\nPower Automate is built on the same engine, but Logic Apps targets IT teams who need source control, deployment pipelines and enterprise networking. Newer versions add agent loops so that workflows can use Foundry models and tools.",
      long_de="Mit Azure Logic Apps bauen Entwickler und Integratoren Workflows visuell oder als Code. Ein Workflow beginnt mit einem Trigger, etwa einem Geschäftsereignis aus Dynamics 365 oder einer Nachricht in einer Warteschlange, und führt Aktionen über verwaltete oder integrierte Konnektoren aus. Consumption-Logic-Apps werden pro Ausführung abgerechnet; Standard-Logic-Apps laufen in einem dedizierten Plan mit VNet-Integration und lokaler Entwicklung in VS Code.\n\nPower Automate basiert auf derselben Engine, Logic Apps richtet sich aber an IT-Teams, die Quellcodeverwaltung, Bereitstellungspipelines und Unternehmensnetzwerke brauchen. Neuere Versionen bringen Agent Loops mit, damit Workflows Foundry-Modelle und -Werkzeuge nutzen."),
    T("dynamics-365-business-events", "concept", "Business events (Dynamics 365)", ["D365 business events", "Geschäftsereignisse", "Business events in D365FO"],
      "Mechanism in Dynamics 365 Finance and Operations that sends a notification to external endpoints such as Logic Apps, Power Automate, Service Bus or Event Grid when a business process event occurs.",
      "Mechanismus in Dynamics 365 Finance and Operations, der bei einem Geschäftsvorfall eine Benachrichtigung an externe Endpunkte wie Logic Apps, Power Automate, Service Bus oder Event Grid sendet.",
      {"related_to": ["d365-finance-operations", "azure-logic-apps", "power-automate"]}, docs="https://learn.microsoft.com/dynamics365/fin-ops-core/dev-itpro/business-events/home-page"),
    T("d365-data-entities", "concept", "Data entities (Dynamics 365)", ["D365 data entities", "OData entities", "Datenentitäten"],
      "Abstractions in Dynamics 365 Finance and Operations that expose business data through OData, data management and Excel for reading, importing and integrating records.",
      "Abstraktionen in Dynamics 365 Finance and Operations, die Geschäftsdaten über OData, Datenverwaltung und Excel zum Lesen, Importieren und Integrieren von Datensätzen bereitstellen.",
      {"related_to": ["d365-finance-operations", "azure-logic-apps", "excel"]}, docs="https://learn.microsoft.com/dynamics365/fin-ops-core/dev-itpro/data-entities/data-entities"),
    T("dual-write", "concept", "Dual-write", ["Dual write", "Dual-Write"],
      "Near real-time, bi-directional data integration between Dynamics 365 finance and operations apps and Dataverse.",
      "Datenintegration in nahezu Echtzeit und in beide Richtungen zwischen den Finance-and-Operations-Apps von Dynamics 365 und Dataverse.",
      {"related_to": ["d365-finance-operations", "dataverse", "power-platform"]}, docs="https://learn.microsoft.com/power-platform/admin/dual-write/dual-write-overview"),
    T("business-performance-analytics", "product", "Business Performance Analytics", ["BPA", "BPA app", "Dynamics 365 Business Performance Analytics", "ERP Analytics MCP"],
      "Analytics offering for Dynamics 365 ERP data that builds prebuilt reports on Fabric and Power BI and exposes ERP analytics to agents through an MCP server.",
      "Analyseangebot für Dynamics-365-ERP-Daten mit vorgefertigten Berichten auf Fabric und Power BI, das ERP-Analysen über einen MCP-Server für Agenten bereitstellt.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "dynamics-365", "related_to": ["d365-finance-operations", "fabric", "power-bi", "mcp", "ai-agent"]}, docs="https://learn.microsoft.com/dynamics365/business-performance-analytics/", license="addon"),

    # ---------- Agenten / Foundry / Governance ----------
    T("agent-365", "product", "Microsoft Agent 365", ["Agent 365", "Agent365"],
      "Control plane for observing, governing and securing AI agents across an organisation, with agent registry, identity, access control and monitoring built on Entra, Purview and Defender.",
      "Kontrollebene zum Beobachten, Steuern und Absichern von KI-Agenten im Unternehmen, mit Agentenregister, Identität, Zugriffskontrolle und Überwachung auf Basis von Entra, Purview und Defender.",
      {"instance_of": [MT], "related_to": ["ai-agent", "agent-id", "microsoft-entra", "purview", "defender", "copilot-studio", "microsoft-foundry", "ai-governance", "agent-observability", "copilot-governance"]},
      docs="https://learn.microsoft.com/microsoft-agent-365/", license="paid",
      long_en="As organisations deploy dozens or hundreds of agents, they need to know which agents exist, who owns them, what data they reach and how they behave. Agent 365 provides a registry, gives agents their own identity, applies access and data-protection policies and surfaces telemetry for security and compliance teams.\n\nIt connects agents built in Copilot Studio, Microsoft Foundry and third-party platforms to the same governance stack that protects users.",
      long_de="Wenn Unternehmen Dutzende oder Hunderte Agenten einsetzen, müssen sie wissen, welche Agenten es gibt, wem sie gehören, auf welche Daten sie zugreifen und wie sie sich verhalten. Agent 365 liefert ein Register, gibt Agenten eine eigene Identität, setzt Zugriffs- und Datenschutzrichtlinien durch und stellt Telemetrie für Sicherheits- und Compliance-Teams bereit.\n\nEs bindet Agenten aus Copilot Studio, Microsoft Foundry und Drittplattformen an dieselbe Governance an, die auch Benutzer schützt."),
    T("agent-id", "product", "Microsoft Entra Agent ID", ["Agent ID", "Entra Agent ID", "Agent identity"],
      "Identity type in Microsoft Entra for AI agents, so agents get their own identity, permissions and lifecycle instead of borrowing a user's or app's credentials.",
      "Identitätstyp in Microsoft Entra für KI-Agenten, damit Agenten eine eigene Identität, Berechtigungen und einen Lebenszyklus haben, statt Zugangsdaten von Benutzern oder Apps zu leihen.",
      {"instance_of": [MT, "identity-security-tool"], "part_of": "microsoft-entra", "related_to": ["agent-365", "ai-agent", "entra-id", "conditional-access"]}, docs="https://learn.microsoft.com/entra/agent-id/", license="paid"),
    T("microsoft-foundry", "product", "Microsoft Foundry", ["Foundry", "Azure AI Foundry", "Azure AI Studio"],
      "Microsoft's platform for building, evaluating and operating AI applications and agents with model catalog, agent service, tools, evaluation and observability; formerly Azure AI Foundry.",
      "Microsofts Plattform zum Bauen, Bewerten und Betreiben von KI-Anwendungen und Agenten mit Modellkatalog, Agent Service, Werkzeugen, Evaluierung und Observability; früher Azure AI Foundry.",
      {"instance_of": [MT, "developer-tool"], "part_of": "azure", "related_to": ["azure-ai-foundry", "foundry-agent-service", "foundry-local", "ai-agent", "mcp", "azure-openai", "github-copilot", "azure-logic-apps", "agent-365"]},
      docs="https://learn.microsoft.com/azure/ai-foundry/", license="paid"),
    T("foundry-agent-service", "product", "Foundry Agent Service", ["Azure AI Agent Service", "Microsoft Foundry Agent Service"],
      "Managed service in Microsoft Foundry for hosting AI agents with threads, tool calling, knowledge, MCP servers and enterprise security.",
      "Verwalteter Dienst in Microsoft Foundry zum Betrieb von KI-Agenten mit Threads, Tool-Aufrufen, Wissen, MCP-Servern und Unternehmenssicherheit.",
      {"instance_of": [MT, "developer-tool"], "part_of": "microsoft-foundry", "related_to": ["ai-agent", "mcp", "azure-logic-apps"]}, docs="https://learn.microsoft.com/azure/ai-foundry/agents/", license="paid"),
    T("foundry-local", "product", "Foundry Local", ["Azure AI Foundry Local"],
      "Runtime and CLI for running AI models locally on a PC or device with an OpenAI-compatible API, without sending data to the cloud.",
      "Laufzeit und CLI, um KI-Modelle lokal auf PC oder Gerät mit OpenAI-kompatibler API auszuführen, ohne Daten in die Cloud zu senden.",
      {"instance_of": [MT, "developer-tool"], "part_of": "microsoft-foundry", "related_to": ["local-first-ai", "ai-agent"]}, docs="https://learn.microsoft.com/azure/ai-foundry/foundry-local/", license="free"),
    T("copilot-cowork", "product", "Copilot Cowork", ["Cowork", "Microsoft 365 Copilot Cowork"],
      "Capability of Microsoft 365 Copilot where the assistant carries out multi-step work on the user's behalf across Outlook, Teams, Word and Excel, instead of only answering single prompts.",
      "Funktion von Microsoft 365 Copilot, bei der der Assistent mehrstufige Aufgaben im Auftrag des Nutzers in Outlook, Teams, Word und Excel erledigt, statt nur einzelne Prompts zu beantworten.",
      {"instance_of": [MT, "ai-assistant"], "part_of": "copilot", "related_to": ["ai-agent", "agent-skill", "human-in-the-loop"]}, docs="https://learn.microsoft.com/copilot/microsoft-365/"),
    T("agent-skill", "concept", "Agent skill", ["Skills", "Agent Skills", "Copilot skills", "Skills für Agenten"],
      "Reusable package of instructions, scripts and resources that an AI agent loads on demand to perform a specific task consistently.",
      "Wiederverwendbares Paket aus Anweisungen, Skripten und Ressourcen, das ein KI-Agent bei Bedarf lädt, um eine bestimmte Aufgabe verlässlich auszuführen.",
      {"related_to": ["ai-agent", "copilot-cowork", "copilot-studio", "mcp", "governance"]}),
    T("agent-loop", "concept", "Agent loop", ["Agentic loop", "Agent-Schleife"],
      "Control cycle in which an AI agent plans, calls tools, observes the result and repeats until the goal is reached or it must hand over to a human.",
      "Kontrollzyklus, in dem ein KI-Agent plant, Werkzeuge aufruft, das Ergebnis beobachtet und wiederholt, bis das Ziel erreicht ist oder ein Mensch übernehmen muss.",
      {"related_to": ["ai-agent", "mcp", "human-in-the-loop", "azure-logic-apps", "agent-harness"]}),
    T("agent-harness", "concept", "Agent harness", ["Harness", "Agent-Harness"],
      "Software layer around a language model that provides tools, permissions, memory, evaluation and limits so an agent can act safely and reproducibly.",
      "Softwareschicht um ein Sprachmodell, die Werkzeuge, Berechtigungen, Gedächtnis, Bewertung und Grenzen bereitstellt, damit ein Agent sicher und reproduzierbar handeln kann.",
      {"related_to": ["agent-loop", "ai-agent", "mcp", "github-copilot", "copilot-studio"]}),
    T("agent-observability", "concept", "Agent observability", ["AI observability", "Agenten-Observability"],
      "Collecting traces, metrics, evaluations and audit data of AI agents to see what they did, why, and at what cost.",
      "Erfassen von Traces, Metriken, Bewertungen und Auditdaten von KI-Agenten, um zu sehen, was sie getan haben, warum und zu welchen Kosten.",
      {"related_to": ["agent-365", "ai-governance", "audit-logs", "finops", "microsoft-foundry"]}),
    T("knowledge-source", "concept", "Knowledge source", ["Wissensquelle", "Copilot Studio knowledge"],
      "Content an agent in Copilot Studio can ground its answers on, such as SharePoint sites, files, websites, Dataverse tables or connectors.",
      "Inhalte, auf die ein Agent in Copilot Studio seine Antworten stützen kann, etwa SharePoint-Websites, Dateien, Webseiten, Dataverse-Tabellen oder Konnektoren.",
      {"related_to": ["copilot-studio", "rag", "sharepoint", "dataverse", "connector", "mcp"]}),
    T("local-first-ai", "concept", "Local-first AI", ["On-device AI", "Lokale KI"],
      "Running AI models and agents on the user's device so data stays local, which can simplify compliance and reduce cloud costs.",
      "KI-Modelle und Agenten laufen auf dem Gerät des Nutzers, sodass Daten lokal bleiben; das kann Compliance vereinfachen und Cloud-Kosten senken.",
      {"related_to": ["foundry-local", "compliance", "ai-agent", "gdpr"]}),
    T("vibe-coding", "concept", "Vibe coding", ["Prompt-driven development", "AI-assisted app building"],
      "Building software by describing what you want in natural language and letting an AI generate and refine the code or app.",
      "Software entsteht, indem man in natürlicher Sprache beschreibt, was man möchte, und eine KI den Code oder die App erzeugt und verfeinert.",
      {"related_to": ["power-apps", "generative-pages", "code-apps", "github-copilot", "prompt"]}),
    T("agentic-sdlc", "concept", "Agentic SDLC", ["AI-driven software development lifecycle", "Agentic software development"],
      "Software development lifecycle in which AI agents take part in requirements, coding, testing, review and operations under human oversight.",
      "Softwareentwicklungszyklus, in dem KI-Agenten unter menschlicher Aufsicht an Anforderungen, Programmierung, Test, Review und Betrieb mitwirken.",
      {"related_to": ["github-copilot", "ai-agent", "agent-harness", "requirements-management", "github-actions"]}),
    T("requirements-management", "concept", "Requirements management", ["Anforderungsmanagement", "Requirements engineering"],
      "Discipline of capturing, structuring, validating and tracing the requirements of a system, increasingly supported by AI.",
      "Disziplin, Anforderungen an ein System zu erfassen, zu strukturieren, zu prüfen und nachzuverfolgen, zunehmend mit KI-Unterstützung.",
      {"related_to": ["copilot", "agentic-sdlc", "governance"]}),
    T("finops", "concept", "FinOps", ["Cloud financial management", "FinOps for AI"],
      "Practice of managing and optimising cloud and AI spending through cost visibility, allocation, budgets and accountability.",
      "Praxis, Cloud- und KI-Kosten durch Transparenz, Zuordnung, Budgets und Verantwortlichkeit zu steuern und zu optimieren.",
      {"related_to": ["copilot-credits", "agent-observability", "azure", "copilot-governance"]}),
    T("copilot-credits", "concept", "Copilot Credits", ["Copilot Studio credits", "Messages and credits"],
      "Consumption unit used to bill agent and Copilot Studio usage, which makes budgeting and monitoring of agent costs necessary.",
      "Verbrauchseinheit, mit der die Nutzung von Agenten und Copilot Studio abgerechnet wird; Budgetierung und Überwachung der Agentenkosten werden dadurch nötig.",
      {"related_to": ["copilot-studio", "finops", "copilot-governance"]}),

    T("microsoft-fabric-apps", "product", "Microsoft Fabric Apps", ["Fabric Apps", "Fabric apps"],
      "Custom, AI-assisted applications and dashboards built on top of Microsoft Fabric data, as an alternative or complement to classic Power BI reports.",
      "Individuelle, KI-gestützt entwickelte Anwendungen und Dashboards auf Basis von Microsoft-Fabric-Daten, als Alternative oder Ergänzung zu klassischen Power-BI-Berichten.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "fabric", "related_to": ["power-bi", "rayfin", "semantic-model", "vibe-coding", "copilot"]}, docs="https://learn.microsoft.com/fabric/"),
    T("rayfin", "product", "Rayfin", ["Rayfin for Fabric"],
      "Tool presented at M365Con 2027 for developing Microsoft Fabric Apps with AI-driven development; see the session for details.",
      "Werkzeug, das auf der M365Con 2027 zur Entwicklung von Microsoft Fabric Apps mit KI-gestützter Entwicklung vorgestellt wird; Details in der Session.",
      {"instance_of": ["developer-tool"], "related_to": ["microsoft-fabric-apps", "fabric", "power-bi"]}, ms=False),
    T("erp-analytics-mcp", "product", "ERP Analytics MCP", ["ERP Analytics MCP server", "BPA MCP server"],
      "MCP server that exposes Dynamics 365 ERP analytics from Business Performance Analytics to AI agents.",
      "MCP-Server, der Dynamics-365-ERP-Analysen aus Business Performance Analytics für KI-Agenten bereitstellt.",
      {"instance_of": [MT, "developer-tool"], "part_of": "business-performance-analytics", "related_to": ["mcp", "ai-agent", "d365-finance-operations", "fabric"]}),
    T("dataverse-mcp-server", "product", "Dataverse MCP server", ["Dataverse MCP", "MCP server for Dataverse"],
      "MCP server that lets agents query and update Dataverse and Dynamics 365 data through the Model Context Protocol, an alternative to connectors.",
      "MCP-Server, über den Agenten Dataverse- und Dynamics-365-Daten per Model Context Protocol abfragen und ändern können, eine Alternative zu Konnektoren.",
      {"instance_of": [MT, "developer-tool"], "part_of": "dataverse", "related_to": ["mcp", "copilot-studio", "connector", "knowledge-source", "dynamics-365"]}, docs="https://learn.microsoft.com/power-apps/maker/data-platform/data-platform-mcp"),
    T("copilot-ux-components", "product", "Copilot UX components", ["Copilot UX Components", "Copilot UI components"],
      "Reusable user-interface building blocks for extending Microsoft 365 Copilot experiences in custom apps and agents.",
      "Wiederverwendbare Oberflächenbausteine, um Microsoft-365-Copilot-Erlebnisse in eigenen Apps und Agenten zu erweitern.",
      {"instance_of": [MT, "developer-tool"], "part_of": "copilot", "related_to": ["copilot-studio", "microsoft-365"]}),
    T("sharepoint-html-pages", "concept", "HTML pages in SharePoint", ["SharePoint HTML pages", "HTML-Seiten in SharePoint"],
      "Way to publish custom HTML content as pages in SharePoint, for example generated with AI, within the tenant's security boundary.",
      "Möglichkeit, eigene HTML-Inhalte als Seiten in SharePoint zu veröffentlichen, etwa mit KI erzeugt, innerhalb der Sicherheitsgrenzen des Mandanten.",
      {"related_to": ["sharepoint", "copilot", "vibe-coding"]}),
    # ---------- Power Platform ----------
    T("generative-pages", "product", "Generative pages", ["Power Apps generative pages", "Generative Pages in Power Apps"],
      "Power Apps feature that generates app pages from a natural-language description on top of Dataverse data, using AI.",
      "Funktion in Power Apps, die aus einer Beschreibung in natürlicher Sprache per KI App-Seiten auf Basis von Dataverse-Daten erzeugt.",
      {"instance_of": [MT, "low-code-tool"], "part_of": "power-apps", "related_to": ["vibe-coding", "dataverse", "copilot"]}, docs="https://learn.microsoft.com/power-apps/maker/model-driven-apps/generative-pages-overview"),
    T("code-apps", "product", "Power Apps code apps", ["Code apps", "Power Apps Code Apps"],
      "Power Apps app type where developers write the front end in code such as React and still use Power Platform connectors, Dataverse and managed security.",
      "App-Typ in Power Apps, bei dem Entwickler das Frontend selbst programmieren, etwa mit React, und dennoch Konnektoren, Dataverse und verwaltete Sicherheit der Power Platform nutzen.",
      {"instance_of": [MT, "low-code-tool"], "part_of": "power-apps", "related_to": ["connector", "dataverse", "vibe-coding", "github-copilot"]}, docs="https://learn.microsoft.com/power-apps/developer/code-apps/overview"),
    T("figma", "product", "Figma", ["Figma Design"],
      "Collaborative interface design tool; a plugin turns Figma designs into Power Apps screens for designer-maker hand-off.",
      "Kollaboratives Werkzeug für Oberflächendesign; ein Plugin macht aus Figma-Entwürfen Power-Apps-Bildschirme für die Übergabe zwischen Designer und Ersteller.",
      {"instance_of": ["developer-tool"], "related_to": ["power-apps", "canvas-app"]}, ms=False, web="https://www.figma.com", wiki="https://en.wikipedia.org/wiki/Figma"),

    # ---------- Fabric / Power BI ----------
    T("semantic-model", "concept", "Semantic model", ["Power BI semantic model", "Dataset", "Semantisches Modell"],
      "Business-friendly data model of tables, relationships and measures that Power BI reports and Copilot query; formerly called a dataset.",
      "Fachlich verständliches Datenmodell aus Tabellen, Beziehungen und Kennzahlen, das Power-BI-Berichte und Copilot abfragen; früher Dataset genannt.",
      {"related_to": ["power-bi", "dax", "fabric", "star-schema"]}, docs="https://learn.microsoft.com/power-bi/connect-data/service-datasets-understand"),
    T("star-schema", "concept", "Star schema", ["Sternschema", "Dimensional modelling"],
      "Data model design with a central fact table surrounded by dimension tables; the recommended structure for fast, simple Power BI models.",
      "Datenmodell-Entwurf mit zentraler Faktentabelle und umgebenden Dimensionstabellen; die empfohlene Struktur für schnelle, einfache Power-BI-Modelle.",
      {"related_to": ["semantic-model", "power-bi", "fabric", "dax"]}, docs="https://learn.microsoft.com/power-bi/guidance/star-schema"),
    T("fabric-workspace", "concept", "Fabric workspace", ["Workspace", "Fabric-Arbeitsbereich"],
      "Container in Microsoft Fabric that groups items such as lakehouses, notebooks and reports and defines access, capacity and deployment boundaries.",
      "Container in Microsoft Fabric, der Elemente wie Lakehouses, Notebooks und Berichte bündelt und Zugriff, Kapazität und Bereitstellungsgrenzen festlegt.",
      {"related_to": ["fabric", "power-bi-service", "governance", "fabric-task-flow"]}, docs="https://learn.microsoft.com/fabric/get-started/workspaces"),
    T("fabric-task-flow", "concept", "Fabric task flow", ["Task flows", "Fabric Task Flow Studio"],
      "Visual design in a Fabric workspace that maps the tasks of a data solution to items, making architecture and ownership visible.",
      "Visueller Entwurf in einem Fabric-Arbeitsbereich, der die Aufgaben einer Datenlösung auf Elemente abbildet und Architektur und Zuständigkeiten sichtbar macht.",
      {"related_to": ["fabric-workspace", "fabric"]}, docs="https://learn.microsoft.com/fabric/get-started/task-flow-overview"),
    T("fabric-notebooks", "product", "Fabric notebooks", ["Python in Fabric", "Microsoft Fabric notebooks", "PySpark notebooks"],
      "Notebook experience in Microsoft Fabric for data engineering and data science with PySpark, Python and SQL on lakehouse data.",
      "Notebook-Umgebung in Microsoft Fabric für Data Engineering und Data Science mit PySpark, Python und SQL auf Lakehouse-Daten.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "fabric", "related_to": ["semantic-link-labs", "semantic-model"]}, docs="https://learn.microsoft.com/fabric/data-engineering/how-to-use-notebook", license="included"),
    T("semantic-link-labs", "product", "Semantic Link Labs", ["sempy-labs", "SLL"],
      "Open-source Python library from Microsoft that automates Power BI and Fabric semantic model management, best-practice checks and migrations from notebooks.",
      "Quelloffene Python-Bibliothek von Microsoft, die Verwaltung, Best-Practice-Prüfungen und Migrationen von Power-BI- und Fabric-Modellen aus Notebooks automatisiert.",
      {"instance_of": [MT, "developer-tool"], "part_of": "fabric", "related_to": ["fabric-notebooks", "semantic-model", "power-bi"]}, docs="https://github.com/microsoft/semantic-link-labs", license="free"),
    T("python-in-excel", "product", "Python in Excel", ["Excel Python"],
      "Excel feature that runs Python code directly in cells for analysis and visualisation, executed in the Microsoft cloud.",
      "Excel-Funktion, die Python-Code direkt in Zellen für Analyse und Visualisierung ausführt, berechnet in der Microsoft-Cloud.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "excel", "related_to": ["power-query", "copilot"]}, docs="https://support.microsoft.com/office/python-in-excel", license="included"),

    # ---------- SharePoint / M365 Admin / Security ----------
    T("sharepoint-advanced-management", "product", "SharePoint Advanced Management", ["SAM", "SharePoint Advanced Management (SAM)"],
      "Set of governance and lifecycle tools for SharePoint, such as site access reviews, inactive site policies, restricted access control and oversharing reports, included with Microsoft 365 Copilot.",
      "Sammlung von Governance- und Lifecycle-Werkzeugen für SharePoint, etwa Zugriffsüberprüfungen, Richtlinien für inaktive Websites, eingeschränkte Zugriffskontrolle und Oversharing-Berichte, mit Microsoft 365 Copilot enthalten.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "sharepoint-premium", "related_to": ["sharepoint", "copilot-governance", "pnp-powershell", "sharepoint-admin-agent", "purview", "copilot"]}, docs="https://learn.microsoft.com/sharepoint/advanced-management", license="included"),
    T("sharepoint-admin-agent", "product", "SharePoint admin agent", ["Admin Agent for SharePoint", "SharePoint Admin Agent"],
      "AI agent that helps SharePoint administrators find and fix tenant problems such as inactive sites, oversharing and permission sprawl in natural language.",
      "KI-Agent, der SharePoint-Administratoren hilft, Probleme im Mandanten wie inaktive Websites, Oversharing und Berechtigungswildwuchs in natürlicher Sprache zu finden und zu beheben.",
      {"instance_of": [MT, "ai-assistant"], "part_of": "sharepoint-advanced-management", "related_to": ["ai-agent", "copilot-governance", "pnp-powershell"]}, docs="https://learn.microsoft.com/sharepoint/sharepoint-admin-agent"),
    T("pnp-powershell", "product", "PnP PowerShell", ["PnP.PowerShell", "Patterns and Practices PowerShell"],
      "Open-source PowerShell module maintained by the community for managing SharePoint, Teams and Microsoft 365 through Microsoft Graph and CSOM.",
      "Quelloffenes PowerShell-Modul der Community zur Verwaltung von SharePoint, Teams und Microsoft 365 über Microsoft Graph und CSOM.",
      {"instance_of": ["developer-tool"], "related_to": ["sharepoint", "graph", "sharepoint-advanced-management", "teams"]}, ms=False, docs="https://pnp.github.io/powershell/", license="free"),
    T("tenant-to-tenant-migration", "concept", "Tenant-to-tenant migration", ["T2T migration", "Mandantenmigration", "Tenant migration"],
      "Moving users, mailboxes, files, Teams and settings from one Microsoft 365 tenant to another, for example after a merger or divestiture.",
      "Umzug von Benutzern, Postfächern, Dateien, Teams und Einstellungen von einem Microsoft-365-Mandanten in einen anderen, etwa nach Fusion oder Abspaltung.",
      {"related_to": ["microsoft-365", "exchange-online", "sharepoint", "teams", "governance"]}),
    T("custom-domain", "concept", "Custom domain in Microsoft 365", ["Custom domains", "Benutzerdefinierte Domäne", "Verified domain"],
      "Own DNS domain verified in Microsoft 365 and used for email addresses, sign-in names and branding, with SPF, DKIM and DMARC records for trust.",
      "Eigene DNS-Domäne, die in Microsoft 365 bestätigt und für E-Mail-Adressen, Anmeldenamen und Branding genutzt wird, mit SPF-, DKIM- und DMARC-Einträgen für Vertrauen.",
      {"related_to": ["microsoft-365", "exchange-online", "entra-id", "microsoft-365-admin-center"]}, docs="https://learn.microsoft.com/microsoft-365/admin/setup/domains-faq"),
    T("zero-trust-assessment", "product", "Zero Trust Assessment", ["Microsoft Zero Trust Assessment"],
      "Assessment tool that checks a Microsoft 365 and Entra tenant against Zero Trust practices and reports gaps with recommended fixes, going beyond Secure Score.",
      "Bewertungswerkzeug, das einen Microsoft-365- und Entra-Mandanten an Zero-Trust-Praktiken misst und Lücken mit empfohlenen Maßnahmen meldet, über den Secure Score hinaus.",
      {"instance_of": [MT, "identity-security-tool"], "related_to": ["zero-trust", "secure-score", "microsoft-entra", "defender"]}, docs="https://learn.microsoft.com/security/zero-trust/assessment/overview"),
    T("secure-score", "product", "Microsoft Secure Score", ["Secure Score"],
      "Measurement in the Microsoft Defender portal that scores a tenant's security posture and suggests improvement actions.",
      "Messgröße im Microsoft-Defender-Portal, die die Sicherheitslage eines Mandanten bewertet und Verbesserungsmaßnahmen vorschlägt.",
      {"instance_of": [MT, "identity-security-tool"], "part_of": "defender", "related_to": ["zero-trust-assessment", "zero-trust"]}, docs="https://learn.microsoft.com/defender-xdr/microsoft-secure-score"),
    T("entra-cloud-sync", "product", "Microsoft Entra Cloud Sync", ["Cloud Sync", "Azure AD Connect cloud sync"],
      "Lightweight agent-based synchronisation of on-premises Active Directory to Entra ID, successor to Entra Connect Sync for many scenarios.",
      "Schlanke, agentenbasierte Synchronisation von lokalem Active Directory nach Entra ID, für viele Szenarien der Nachfolger von Entra Connect Sync.",
      {"instance_of": [MT, "identity-security-tool"], "part_of": "microsoft-entra", "related_to": ["entra-connect", "active-directory", "entra-id", "identity-lifecycle"]}, docs="https://learn.microsoft.com/entra/identity/hybrid/cloud-sync/what-is-cloud-sync"),
    T("identity-lifecycle", "concept", "Identity lifecycle management", ["Joiner-mover-leaver", "Lifecycle Workflows", "Identitäts-Lebenszyklus"],
      "Automating how identities are created, changed and removed as people join, move within and leave an organisation, via provisioning and lifecycle workflows.",
      "Automatisierung, wie Identitäten angelegt, geändert und entfernt werden, wenn Personen eintreten, wechseln und austreten, per Provisionierung und Lifecycle-Workflows.",
      {"related_to": ["entra-id", "entra-cloud-sync", "active-directory", "governance", "agent-id"]}, docs="https://learn.microsoft.com/entra/id-governance/what-are-lifecycle-workflows"),
    T("data-governance", "concept", "Data governance", ["Datengovernance", "Data governance for Copilot"],
      "Rules, roles and tools that keep data classified, protected and used correctly, essential before and while deploying Copilot and agents.",
      "Regeln, Rollen und Werkzeuge, die Daten klassifiziert, geschützt und korrekt genutzt halten, unverzichtbar vor und während des Einsatzes von Copilot und Agenten.",
      {"related_to": ["purview", "sensitivity-labels", "dlp", "copilot-governance", "ai-governance", "compliance"]}),

    # ---------- Azure / Entwicklung ----------
    T("azure-functions", "product", "Azure Functions", ["Functions", "Azure Function"],
      "Serverless compute service of Azure that runs event-driven code; can be exposed as an MCP server, for example through API Management.",
      "Serverless-Rechendienst von Azure, der ereignisgesteuerten Code ausführt; lässt sich etwa über API Management als MCP-Server bereitstellen.",
      {"instance_of": [MT, "developer-tool"], "part_of": "azure", "related_to": ["azure-api-management", "mcp", "azure-logic-apps"]}, docs="https://learn.microsoft.com/azure/azure-functions/", license="paid"),
    T("azure-landing-zone", "concept", "Azure landing zone", ["Azure Landing Zones", "ALZ", "Landing Zone"],
      "Pre-configured Azure environment with management groups, networking, policy and identity that gives workloads a secure, scalable foundation.",
      "Vorkonfigurierte Azure-Umgebung mit Verwaltungsgruppen, Netzwerk, Richtlinien und Identität, die Workloads ein sicheres, skalierbares Fundament gibt.",
      {"related_to": ["azure", "infrastructure-as-code", "sovereign-landing-zone", "governance"]}, docs="https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/"),
    T("sovereign-landing-zone", "concept", "Sovereign landing zone", ["SLZ", "Sovereign Landing Zones"],
      "Azure landing zone variant with sovereignty controls for data residency, encryption and policy, built for regulated and public-sector customers.",
      "Variante der Azure Landing Zone mit Souveränitätskontrollen für Datenstandort, Verschlüsselung und Richtlinien, für regulierte Branchen und den öffentlichen Sektor.",
      {"related_to": ["azure-landing-zone", "azure", "compliance", "gdpr"]}, docs="https://learn.microsoft.com/industry/sovereignty/slz-overview"),
    T("infrastructure-as-code", "concept", "Infrastructure as code", ["IaC", "Infrastruktur als Code"],
      "Managing cloud infrastructure through versioned code and automated deployment instead of manual portal clicks.",
      "Verwaltung von Cloud-Infrastruktur durch versionierten Code und automatisierte Bereitstellung statt manueller Klicks im Portal.",
      {"related_to": ["bicep", "terraform", "azure-landing-zone", "github-actions"]}),
    T("bicep", "product", "Bicep", ["Azure Bicep"],
      "Domain-specific language from Microsoft for declaring Azure resources, compiled to ARM templates.",
      "Domänenspezifische Sprache von Microsoft zum Deklarieren von Azure-Ressourcen, die zu ARM-Vorlagen kompiliert wird.",
      {"instance_of": [MT, "developer-tool"], "part_of": "azure", "related_to": ["infrastructure-as-code", "terraform", "azure-landing-zone"], "similar_to": ["terraform"]}, docs="https://learn.microsoft.com/azure/azure-resource-manager/bicep/", license="free"),
    T("terraform", "product", "Terraform", ["HashiCorp Terraform"],
      "Multi-cloud infrastructure-as-code tool from HashiCorp with a provider for Azure.",
      "Multi-Cloud-Werkzeug für Infrastructure as Code von HashiCorp mit einem Provider für Azure.",
      {"instance_of": ["developer-tool"], "related_to": ["infrastructure-as-code", "azure"], "similar_to": ["bicep"]}, ms=False, web="https://www.terraform.io", wiki="https://en.wikipedia.org/wiki/Terraform_(software)"),
    T("azure-virtual-desktop", "product", "Azure Virtual Desktop", ["AVD", "Windows Virtual Desktop", "WVD"],
      "Cloud-hosted desktop and app virtualisation service on Azure, extendable to hybrid and other hypervisors.",
      "In Azure gehosteter Dienst für Desktop- und App-Virtualisierung, erweiterbar auf Hybrid-Umgebungen und andere Hypervisoren.",
      {"instance_of": [MT, "cloud-platform"], "part_of": "azure", "related_to": ["intune", "entra-id", "windows-365"]}, docs="https://learn.microsoft.com/azure/virtual-desktop/", license="paid"),
    T("windows-365", "product", "Windows 365", ["Cloud PC", "Windows 365 Cloud PC"],
      "Cloud PC service that streams a personal Windows desktop from the Microsoft cloud on a fixed monthly price.",
      "Cloud-PC-Dienst, der einen persönlichen Windows-Desktop aus der Microsoft-Cloud zu einem festen Monatspreis bereitstellt.",
      {"instance_of": [MT, "cloud-platform"], "related_to": ["azure-virtual-desktop", "intune"]}, docs="https://learn.microsoft.com/windows-365/", license="paid"),
    T("dotnet", "platform", ".NET", ["dotnet", "DotNet", ".NET Core"],
      "Microsoft's open-source, cross-platform developer platform for building web, cloud, desktop, mobile, CLI and AI applications with C#, F# and Visual Basic.",
      "Microsofts quelloffene, plattformübergreifende Entwicklungsplattform für Web-, Cloud-, Desktop-, Mobil-, CLI- und KI-Anwendungen mit C#, F# und Visual Basic.",
      {"instance_of": [MT, "developer-tool"], "related_to": ["azure", "github-copilot", "mcp", "ai-agent", "azure-functions"]}, docs="https://learn.microsoft.com/dotnet/", web="https://dotnet.microsoft.com", wiki="https://en.wikipedia.org/wiki/.NET", license="free", released="2002-02-13"),
]

for e in NEW:
    if e["id"] in M:
        old = M[e["id"]]
        for k, v in e.items():
            if k == "rel":
                have = {tuple(r) for r in old.get("rel", [])}
                old["rel"] = old.get("rel", []) + [r for r in v if tuple(r) not in have]
            elif not old.get(k):
                old[k] = v
    else:
        D.append(e); M[e["id"]] = e

# Bestehende Entitaeten verstaerken (Aliase + Gegenverweise)
ADD = {
    "dynamics-365": (["Dynamics", "D365", "MS Dynamics"], [["related_to", "d365-finance-operations"], ["related_to", "dynamics-365-business-central"], ["related_to", "business-performance-analytics"], ["related_to", "dual-write"]]),
    "azure": ([], [["related_to", "azure-logic-apps"], ["related_to", "azure-functions"], ["related_to", "azure-landing-zone"], ["related_to", "azure-virtual-desktop"], ["related_to", "bicep"]]),
    "azure-ai-foundry": (["Microsoft Foundry", "Foundry"], [["related_to", "microsoft-foundry"], ["related_to", "foundry-agent-service"], ["related_to", "foundry-local"]]),
    "power-automate": ([], [["similar_to", "azure-logic-apps"]]),
    "ai-agent": (["AI agents", "Agent", "KI-Agent"], [["related_to", "agent-365"], ["related_to", "agent-id"], ["related_to", "agent-loop"], ["related_to", "agent-harness"], ["related_to", "agent-skill"], ["related_to", "agent-observability"], ["related_to", "foundry-agent-service"]]),
    "mcp": (["Model Context Protocol"], [["related_to", "agent-harness"], ["related_to", "azure-functions"], ["related_to", "business-performance-analytics"], ["related_to", "foundry-agent-service"]]),
    "copilot-studio": ([], [["related_to", "knowledge-source"], ["related_to", "agent-365"], ["related_to", "copilot-credits"], ["related_to", "agent-skill"]]),
    "copilot": ([], [["related_to", "copilot-cowork"], ["related_to", "data-governance"], ["related_to", "requirements-management"]]),
    "sharepoint-premium": ([], [["related_to", "sharepoint-advanced-management"]]),
    "microsoft-entra": ([], [["related_to", "agent-id"], ["related_to", "entra-cloud-sync"], ["related_to", "identity-lifecycle"]]),
    "purview": ([], [["related_to", "data-governance"], ["related_to", "agent-365"]]),
    "defender": ([], [["related_to", "secure-score"], ["related_to", "agent-365"]]),
    "zero-trust": ([], [["related_to", "zero-trust-assessment"], ["related_to", "secure-score"]]),
    "fabric": ([], [["related_to", "semantic-model"], ["related_to", "fabric-workspace"], ["related_to", "fabric-notebooks"], ["related_to", "semantic-link-labs"], ["related_to", "star-schema"]]),
    "power-bi": ([], [["related_to", "semantic-model"], ["related_to", "star-schema"], ["related_to", "semantic-link-labs"]]),
    "github-copilot": ([], [["related_to", "agent-harness"], ["related_to", "agentic-sdlc"], ["related_to", "microsoft-foundry"]]),
    "excel": ([], [["related_to", "python-in-excel"]]),
    "active-directory": ([], [["related_to", "entra-cloud-sync"], ["related_to", "identity-lifecycle"]]),
    "entra-connect": ([], [["related_to", "entra-cloud-sync"]]),
    "power-apps": ([], [["related_to", "generative-pages"], ["related_to", "code-apps"], ["related_to", "figma"], ["related_to", "vibe-coding"]]),
    "azure-api-management": ([], [["related_to", "azure-functions"], ["related_to", "azure-logic-apps"]]),
    "human-in-the-loop": ([], [["related_to", "agent-loop"], ["related_to", "copilot-cowork"]]),
    "ai-governance": ([], [["related_to", "agent-365"], ["related_to", "data-governance"], ["related_to", "agent-observability"]]),
}
for k, (al, rl) in ADD.items():
    e = M.get(k)
    if not e:
        print("fehlt", k); continue
    e["aliases"] = list(dict.fromkeys(e.get("aliases", []) + al))[:10]
    have = {tuple(r) for r in e.get("rel", [])}
    e["rel"] = e.get("rel", []) + [r for r in rl if tuple(r) not in have and r[1] in M and r[1] != k]
# "SharePoint Advanced Management" ist jetzt eigene Entitaet
sp = M.get("sharepoint-premium")
if sp:
    sp["aliases"] = [a for a in sp["aliases"] if a != "SharePoint Advanced Management"]

# ---------- Session-Themen ----------
S = {917909: ["power-platform", "ai-governance", "governance", "agent-365", "power-platform-admin-center"], 1107710: ["copilot", "ai-governance", "copilot-governance"],
     1100399: ["code-apps", "power-apps", "vibe-coding"], 1094624: ["figma", "power-apps", "canvas-app"], 1107362: ["copilot", "github-copilot", "agentic-sdlc"],
     1113896: ["generative-pages", "power-apps", "vibe-coding", "dataverse"], 1117898: ["power-automate", "copilot", "ai-agent", "ai-builder"], 1096835: ["power-platform", "github-copilot", "power-fx", "power-platform-cli"],
     1088915: ["d365-finance-operations", "azure-logic-apps", "dynamics-365-business-events", "d365-data-entities", "azure", "dynamics-365", "connector"],
     1099079: ["copilot-studio", "dataverse", "dataverse-mcp-server", "mcp", "connector", "knowledge-source", "dynamics-365"], 1115183: ["dynamics-365", "ai-agent", "d365-finance-operations"],
     1101884: ["business-performance-analytics", "erp-analytics-mcp", "d365-finance-operations", "mcp", "dynamics-365"], 1101662: ["power-pages", "copilot"], 1109144: ["dynamics-365-business-central", "ai-agent", "dynamics-365"],
     1116866: ["power-pages", "power-platform", "dataverse", "power-automate"], 1117906: ["power-pages", "power-apps", "power-platform-cli"],
     1116932: ["power-bi", "copilot", "ai-agent", "semantic-model"], 1114160: ["power-bi", "semantic-model"], 1096256: ["microsoft-fabric-apps", "rayfin", "fabric", "power-bi"], 1115120: ["fabric", "fabric-notebooks"],
     1090436: ["power-bi", "dax"], 1115744: ["power-bi", "copilot"], 1116174: ["star-schema", "fabric", "power-bi", "semantic-model"], 1073275: ["fabric-workspace", "fabric", "governance"],
     1098354: ["semantic-link-labs", "power-bi", "fabric", "fabric-notebooks", "semantic-model", "finops"], 1114721: ["fabric-task-flow", "fabric-workspace", "fabric"],
     1108485: ["ai-agent", "human-in-the-loop", "ai-governance"], 1112015: ["copilot-studio", "github-copilot", "agent-harness", "copilot-credits", "finops"], 1106372: ["finops", "copilot-credits", "copilot", "ai-agent"],
     1094657: ["agent-skill", "sharepoint", "copilot-studio", "knowledge-source"], 1112981: ["copilot-studio", "agent-observability", "agent-365"], 1092974: ["ai-agent", "agent-365", "ai-governance", "agent-observability"],
     1099673: ["copilot-studio", "ai-agent"], 1098353: ["agent-id", "ai-agent", "agent-365", "ai-governance", "microsoft-foundry"], 1108022: ["copilot", "purview", "data-governance", "sensitivity-labels"],
     1105745: ["requirements-management", "copilot", "agentic-sdlc"], 1099617: ["agent-365", "defender", "purview", "ai-agent", "copilot-studio", "agent-id"],
     1074396: ["bicep", "terraform", "infrastructure-as-code", "azure"], 1094692: ["sovereign-landing-zone", "azure-landing-zone", "azure", "compliance"],
     1104362: ["microsoft-365-admin-center", "copilot", "microsoft-365", "copilot-governance"], 1106273: ["sharepoint-advanced-management", "pnp-powershell", "sharepoint-admin-agent", "sharepoint", "copilot-governance"],
     1096180: ["ai-governance", "copilot-adoption"], 1102225: ["microsoft-365", "governance"], 1106408: ["ai-governance", "purview", "sharepoint", "agent-365", "data-governance"],
     1110365: ["ai-agent", "windows-365", "dotnet"], 1106966: ["azure-virtual-desktop", "azure", "windows-365"], 1104821: ["sharepoint-html-pages", "sharepoint", "copilot"], 1098155: ["sharepoint-admin-agent", "sharepoint-advanced-management", "sharepoint", "ai-agent"],
     1108220: ["tenant-to-tenant-migration", "microsoft-365", "exchange-online", "teams"], 1109808: ["sharepoint-advanced-management", "sharepoint", "copilot", "data-governance"],
     1106391: ["teams", "copilot", "teams-phone", "teams-rooms", "teams-premium"], 1104260: ["onedrive", "sharepoint", "copilot"], 1104329: ["ai-agent", "copilot", "copilot-adoption"],
     1093766: ["copilot-cowork", "ai-agent", "human-in-the-loop"], 1105746: ["copilot", "microsoft-planner", "project", "copilot-studio"], 1098123: ["copilot-cowork", "copilot", "ai-agent"],
     1063175: ["copilot-adoption", "copilot", "ai-agent"], 1091654: ["sharepoint", "copilot", "knowledge-source"], 1099343: ["agent-skill", "copilot-cowork", "governance"],
     1105976: ["copilot", "microsoft-365"], 1114062: ["excel", "python-in-excel", "power-query", "copilot", "excel-online"], 1097066: ["copilot", "copilot-adoption"],
     1075187: ["zero-trust-assessment", "secure-score", "zero-trust", "microsoft-365"], 1116338: ["entra-cloud-sync", "entra-connect", "identity-lifecycle", "microsoft-entra", "entra-id"],
     1103930: ["local-first-ai", "foundry-local", "compliance", "ai-agent"], 1091556: ["active-directory", "entra-id", "entra-cloud-sync", "intune"], 1075749: ["purview", "data-governance", "dlp", "sensitivity-labels"],
     1102412: ["custom-domain", "exchange-online", "entra-id", "microsoft-365"], 1105613: ["copilot", "data-governance", "purview"], 1105811: ["copilot", "copilot-cowork", "ai-agent"],
     1107231: ["agent-loop", "agent-harness", "mcp", "ai-agent", "github-copilot"], 1108323: ["ai-agent", "prompt"], 1105910: ["copilot-ux-components", "copilot", "microsoft-365"], 1075715: ["dotnet", "mcp", "ai-agent"],
     1105325: ["agent-harness", "dotnet", "ai-agent", "mcp"], 1100636: ["graph", "dotnet", "microsoft-365"], 1101424: ["agentic-sdlc", "github-copilot", "ai-agent", "github-actions"],
     1101125: ["azure-landing-zone", "azure", "dotnet", "infrastructure-as-code"], 1117691: ["foundry-local", "local-first-ai", "microsoft-foundry"], 1096637: ["microsoft-foundry", "foundry-agent-service", "ai-agent"],
     1101323: ["ai-agent", "agent-loop", "agent-observability"], 1094925: ["mcp", "microsoft-foundry", "ai-agent", "foundry-agent-service"], 1100235: ["copilot", "ai-agent"],
     1108979: ["github-copilot", "microsoft-foundry", "copilot"], 1108154: ["azure-functions", "azure-api-management", "mcp", "azure"], 1117856: ["microsoft-foundry", "azure-logic-apps", "agent-loop", "ai-agent"],
     1084427: ["agent-365", "microsoft-foundry", "purview", "ai-agent", "agent-id"], 1105812: ["microsoft-365", "copilot"]}
pr = json.load(open(PP))
miss = set()
for s in pr["sessions"]:
    cur = s.get("topics") or []
    new = list(dict.fromkeys(cur + S.get(s["id"], [])))
    for t in new:
        if t not in M:
            miss.add(t)
    s["topics"] = [t for t in new if t in M][:8]
pr["topics_version"] = 2
assert not miss, miss
ids = set(M)
bad = [(e["id"], r) for e in D for r in e.get("rel", []) if r[1] not in ids]
longd = [e["id"] for e in D if len(e["desc"]["en"]) > 300 or len(e["desc"]["de"]) > 300]
assert not bad and not longd, (bad, longd)
json.dump(D, open(P, "w"), ensure_ascii=False, indent=1)
json.dump(pr, open(PP, "w"), ensure_ascii=False, indent=1)
print("gesamt", len(D), "Sessions", len(pr["sessions"]), "ohne Thema:", [s["title"][:40] for s in pr["sessions"] if not s["topics"]])
