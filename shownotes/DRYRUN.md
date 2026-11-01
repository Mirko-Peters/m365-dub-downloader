# Dry-Run Shownotes -> Spreaker

2026-11-01T10:26:08+00:00 · 120 Folgen offen, 0 ungueltig, 0 unbekannt, 10 im Diff (meistgehoerte zuerst). Schreiben erst mit Datei shownotes/APPROVED.

## Beyond Copilot: Building Enterprise AI Agents That Actually Work with Copilot Studio with Manpreet Singh [MVP-MCT] (74640221, 341 Abrufe, 3648 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,46 +1,24 @@
-Enterprise AI is moving beyond chatbots that simply answer questions. The next generation of AI agents can understand business context, connect to enterprise systems, orchestrate workflows, and take action on behalf of users.But building an impressive AI agent demo is easy. Building an agent that works reliably across a global enterprise—with sensitive data, complex business processes, governance requirements, thousands of users, and measurable outcomes—is a very different challenge.In https://www.m365.fm/manpreet-singh/ of the M365 FM Podcast, Mirko Peters talks with Manpreet Singh [MVP/MCT] about what it actually takes to build production-ready enterprise AI agents with Microsoft Copilot Studio and the wider Microsoft AI ecosystem.Manpreet explains how organizations are evolving from individual departmental agents toward multi-agent architectures where specialized agents collaborate behind a single interface. The discussion explores when to use https://www.m365.fm/categories/copilot-talk/, Copilot Studio, and https://www.m365.fm/azure-ai-foundry-simply-explained/—and how these technologies can work together rather than becoming isolated AI platforms.
-FROM ANSWERS TO ACTIONS
-The real transformation begins when an AI agent can do more than retrieve information.Using practical examples, Manpreet explains how agents can connect with systems such as Workday, Salesforce, SAP, ServiceNow, Jira, Confluence, and PeopleSoft. Instead of navigating several applications manually, employees can interact with an agent through Microsoft Teams or another conversational interface.An employee requesting leave, for example, could have an agent check available leave, consult HR policies, initiate the request in the underlying HR system, ask the manager for approval, and return the final result—all without the employee opening the individual applications.
-KNOWLEDGE, TOOLS AND TRIGGERS
-A useful enterprise agent requires more than a good prompt.Manpreet breaks the architecture down into essential elements: knowledge sources that provide organizational context, tools and connectors that allow the agent to interact with enterprise systems, and triggers that determine when processes should begin.SharePoint can become an important knowledge layer, while Power Platform connectors and APIs enable agents to perform actions across business applications.
-WHY DATA QUALITY MATTERS
-Connecting an agent to twenty years of SharePoint content is not necessarily a good strategy.Manpreet strongly recommends cleaning and curating organizational knowledge before exposing it to AI. Thousands of outdated PDFs, duplicate documents, missing metadata, and obsolete policies can undermine the quality of agent responses.A smaller, carefully maintained knowledge base with current documents, useful metadata, tags, descriptions, and version management can produce significantly better results than simply indexing everything an organization owns.
-HUMAN-IN-THE-LOOP AI
-Autonomous does not have to mean uncontrolled.For low-risk transactions, organizations may allow an agent to complete an action automatically. Higher-value or sensitive decisions can introduce human approval.Manpreet discusses examples including financial claims, invoice processing, access requests, and infrastructure changes where humans remain part of the decision-making process while AI handles much of the repetitive work surrounding the decision.
-GOVERNANCE BEFORE SCALE
-As agents gain access to multiple enterprise applications, governance becomes critical.The conversation explores https://www.m365.fm/microsoft-purview-simply-explained/, Data Loss Prevention policies, security controls, sensitivity labels, Microsoft Defender, identity, environment strategies, and the importance of establishing an https://www.m365.fm/microsoft-ai-center-of-excellence/ before allowing agent development to expand throughout an organization.Governance should protect enterprise information without creating policies so restrictive that agent performance and usability suffer.
-CONTROLLING AGENT SPRAWL
-Organizations can quickly move from a handful of experimental agents to hundreds or thousands.Manpreet discusses agent lifecycle management, parent-child agent relationships, centralized inventories, ownership, connected data sources, permissions, consumption, and emerging management capabilities around Agent 365.The goal is to give administrators visibility into which agents exist, who owns them, what they can access, and how they are being used.
-THE AI COMMAND CENTER
-One of the most interesting concepts discussed in the episode is a unified AI Command Center.Instead of agent creation happening without oversight, organizations can establish a central process for requesting agents, connectors, APIs, MCP integrations, environments, and permissions.The command center can combine approval workflows, auditing, monitoring, governance, usage information, and cost controls—creating a central operational layer for enterprise AI.
-OBSERVABILITY AND TROUBLESHOOTING
-Traditional applications have logs. Enterprise AI needs observability.When an employee reports that an agent produced an unexpected result, administrators need to understand which knowledge sources were accessed, which tools were called, what actions occurred, and where the process failed.Copilot Studio's tracing and evaluation capabilities can help teams investigate these execution paths and understand how an agent arrived at an outcome.
-TESTING NON-DETERMINISTIC AI
-Testing AI agents requires a different mindset from testing traditional applications.Manpreet discusses evaluation features, generated test cases, structured datasets, indexing, user feedback, and repeated validation. Organizations should continuously test their agents against realistic questions and expected outcomes rather than deploying an agent once and assuming it will behave correctly forever.
-MULTI-AGENT ARCHITECTURES
-Instead of forcing employees to find the correct agent for every task, organizations can create an orchestration layer.A primary agent can understand the user's intent and delegate work to specialized agents for HR, travel, marketing, sales, IT, or other functions.The user interacts with one interface while multiple specialized agents operate behind it.
-ADOPTION IS WHERE AI ROI HAPPENS
-The final challenge is not technical.Organizations can build thousands of sophisticated agents and still fail to generate meaningful business value if employees do not understand when, why, and how to use them.Manpreet argues that adoption, persona-based training, practical use cases, and helping employees integrate agents into their daily work are essential to realizing ROI from Microsoft 365 Copilot and enterprise AI investments.
-IN THIS EPISODE
-- Microsoft Copilot Studio and enterprise AI agents
-- Microsoft 365 Copilot vs. Copilot Studio vs. Azure AI Foundry
-- Autonomous agents and action-oriented AI
-- Enterprise knowledge grounding
-- SharePoint as an AI knowledge source
-- Data quality, metadata, and indexing
-- Power Platform connectors and enterprise integrations
-- Human-in-the-loop architectures
-- Multi-agent systems and orchestration
-- Microsoft Purview and DLP
-- AI security and governance
-- Agent lifecycle management
-- Agent inventories and Agent 365
-- AI Centers of Excellence
-- Unified AI Command Centers
-- AI observability and tracing
-- Agent testing and evaluation
-- Hallucination reduction
-- AI consumption and cost management
-- Enterprise AI adoption and ROI
-KEY TAKEAWAY
-The next phase of enterprise AI is not simply about adding better chatbots. It is about moving from answers to outcomes.AI agents can connect organizational knowledge, applications, workflows, and business processes—but the fundamentals of enterprise technology remain essential: identity, security, governance, data quality, architecture, testing, observability, cost control, and adoption.And ultimately, the technology only creates value when people actually use it.
+Building an impressive agent demo is easy, but making agents work reliably in a global enterprise with sensitive data, governance and real users is something else. Microsoft MVP Manpreet Singh explains for architects, IT leaders and makers how to design Copilot Studio agents with clean knowledge, human in the loop, governance, observability and the adoption work that finally delivers ROI.
+In this episode
+00:00 – Introduction: from Copilot to agents
+04:48 – Designing an enterprise AI agent
+11:38 – Knowledge, grounding and data quality
+14:20 – Actions, integrations and a first agent
+20:02 – Human in the loop and governance
+27:50 – Agent lifecycle, Agent 365 and the AI command center
+45:23 – Observability, testing and multi-agent systems
+56:22 – Rapid fire and adoption as the key to ROI
+Key takeaways
+An enterprise agent needs three pillars: a trigger, tools and actions, and clean, well-tagged knowledge sources rather than decades of unfiltered SharePoint content.
+Governance, DLP and a Center of Excellence should be in place before agents roll out, with policies scoped to what each agent actually needs and tools like Agent 365 providing inventory and observability.
+The return on AI agents depends mostly on adoption, so every user needs role-based training on what an agent does and what input it expects.
+Worth quoting
+“So with the AI's, we are not replacing people, we are just empowering them to do their job much better.” – Manpreet Singh (22:28)
+“And that also means the difficult part for enterprise technology doesn't disappear. Identity matters, security matters, data quality matters, governance matters, architecture matters, testing matters.” – Mirko Peters (62:45)
+Explore more on M365.FM
+Episode page: the full interview with chapters, quotes and FAQ on Copilot Studio agents
+Manpreet Singh – Microsoft MVP and MCT who shares how he designs enterprise agents for global clients
+AI agent – the core topic, from a leave request agent to multi-agent networks
+Copilot Studio – where Manpreet suggests building a first agent, and its evaluation feature for testing
+Related episode: The Death of the Chatbot: Why Your Dataverse Strategy Is Broken
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Building an impressive agent demo is easy, but making agents work reliably in a global enterprise with sensitive data, governance and real users is something else. Microsoft MVP Manpreet Singh explains for architects, IT leaders and makers how to design Copilot Studio agents with clean knowledge, human in the loop, governance, observability and the adoption work that finally delivers ROI.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Introduction: from <a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">Copilot</a> to agents</li><li>04:48 – Designing an enterprise AI agent</li><li>11:38 – Knowledge, grounding and data quality</li><li>14:20 – Actions, integrations and a first agent</li><li>20:02 – Human in the loop and governance</li><li>27:50 – Agent lifecycle, <a href="https://www.m365.fm/entity/agent-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">Agent 365</a> and the AI command center</li><li>45:23 – Observability, testing and multi-agent systems</li><li>56:22 – Rapid fire and adoption as the key to ROI</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>An enterprise agent needs three pillars: a trigger, tools and actions, and clean, well-tagged knowledge sources rather than decades of unfiltered <a href="https://www.m365.fm/entity/sharepoint/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">SharePoint</a> content.</li><li>Governance, DLP and a Center of Excellence should be in place before agents roll out, with policies scoped to what each agent actually needs and tools like Agent 365 providing inventory and observability.</li><li>The return on AI agents depends mostly on adoption, so every user needs role-based training on what an agent does and what input it expects.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“So with the AI's, we are not replacing people, we are just empowering them to do their job much better.” – Manpreet Singh (22:28)</p>
<p>“And that also means the difficult part for enterprise technology doesn't disappear. Identity matters, security matters, data quality matters, governance matters, architecture matters, testing matters.” – Mirko Peters (62:45)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/manpreet-singh/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">Episode page</a>: the full interview with chapters, quotes and FAQ on Copilot Studio agents</li><li><a href="https://www.m365.fm/entity/manpreet-singh/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">Manpreet Singh</a> – Microsoft MVP and MCT who shares how he designs enterprise agents for global clients</li><li><a href="https://www.m365.fm/entity/ai-agent/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">AI agent</a> – the core topic, from a leave request agent to multi-agent networks</li><li><a href="https://www.m365.fm/entity/copilot-studio/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">Copilot Studio</a> – where Manpreet suggests building a first agent, and its evaluation feature for testing</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/the-death-of-the-chatbot-why-your-dataverse-strategy-is-broken/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=manpreet-singh">The Death of the Chatbot: Why Your Dataverse Strategy Is Broken</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Microsoft 365 Copilot Without the Hype: Adoption, Governance &amp; Getting Your Tenant Ready with Paul Keijzers [MVP] (75328001, 252 Abrufe, 3607 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,7 +1,24 @@
-https://www.m365.fm/categories/copilot-talk/ can help people find information and get work done faster, but its answers depend on the content and permissions already in an organization’s Microsoft 365 tenant. In https://www.m365.fm/paul-keijzers/ of the M365 FM podcast, Mirko Peters speaks with Microsoft MVP Paul Keijzers, founder of KB Works, about preparing Microsoft 365 for Copilot in a practical, responsible way. They look beyond demos and licensing to the foundations that shape Copilot results: SharePoint, Microsoft Teams, OneDrive, data quality, access controls and governance. Copilot can make existing access issues more visible. Files that have been shared broadly, outdated documents, old versions and content with unclear ownership may all affect what employees can find. Paul explains why organizations should review their sharing settings and understand where sensitive or unnecessary access exists before rolling Copilot out widely. SharePoint oversharing reports can help identify potential issues across SharePoint, Teams and OneDrive, although organizations still need to check whether flagged sharing is appropriate for their business.
-GOVERNANCE, LEGACY DATA AND INFORMATION PROTECTION
-The conversation explores how to manage years of legacy SharePoint content. Old project files may need to be retained for legal or business reasons, but that does not always mean they should appear in everyday search or Copilot results. Organizations can consider archiving content or restricting access, depending on how often it needs to be used and how the tenant is structured. Paul also highlights the need to plan for Microsoft 365 backup and recovery, including how a company can retrieve its data if it changes backup providers. https://www.m365.fm/microsoft-purview-simply-explained/ is part of the wider governance picture. Paul recommends reviewing sensitivity labels, checking whether they are applied consistently, and considering automatic labeling where appropriate. Data Loss Prevention policies can help protect personal and sensitive information, while https://www.m365.fm/power-automate-simply-explained/ DLP policies need attention when Copilot uses connectors to work with services such as Jira. These controls should fit the organization’s actual needs, since a global company and a small business may require different policies.
-SHAREPOINT STRUCTURE AND COPILOT ADOPTION
-Good information architecture remains important even as AI becomes better at understanding natural language. Paul discusses using metadata and content types to make information easier to organize and retrieve, while keeping SharePoint libraries practical for employees. His guideline is to avoid overly deep folder structures and excessive metadata fields, since people are less likely to maintain a system that is too complicated. Copilot can help suggest or populate information, but organizations still need a clear structure and reliable content. Copilot adoption also requires ongoing support. Rather than delivering a single training session and expecting employees to figure out the rest, organizations can share regular tips, demonstrate useful prompts and agents, and help teams solve real daily frustrations. Paul recommends starting with the work people actually do, then identifying where Copilot could save time or improve an outcome. Adoption plans should be adapted to the size and working practices of each organization instead of copied wholesale from a framework designed for a different environment.
-AI VALUE, AGENTS AND A PRACTICAL PATH FORWARD
-Mirko and Paul also discuss how organizations can assess the value and cost of AI, how agents may increasingly work alongside employees, and why administrators need ways to discover and manage agents in their environments. Paul shares his Focus Week concept in Portugal, where teams spend dedicated time working on Microsoft 365, SharePoint, governance or Copilot challenges away from their usual workplace interruptions. The central message for IT leaders is that Copilot readiness starts with understanding the Microsoft 365 tenant: who can access what, how information is organized, which content should be retained or surfaced, and how employees will learn to use AI in their work. Review sharing settings, improve information governance and connect adoption to real business needs before treating Copilot as simply another license to deploy.
+Buying Copilot licenses is easy, but Copilot then surfaces years of SharePoint, Teams and OneDrive content that was never meant to be shared. In this episode, Microsoft MVP Paul Keijzers explains to IT leaders and Microsoft 365 admins what a Copilot-ready tenant really means. You get practical advice on oversharing, Purview labels and DLP, content lifecycle, adoption and agent governance.
+In this episode
+00:00 – Is your tenant ready for Copilot?
+02:37 – Paul's journey from car audio to SharePoint and Copilot
+11:33 – What companies underestimate
+15:11 – Old SharePoint content and content lifecycle
+21:28 – Oversharing, Purview, labels and DLP
+30:17 – Adoption, champions and Copilot costs
+40:46 – Agents and Agent 365
+45:08 – Focus weeks and rapid fire round
+Key takeaways
+Copilot readiness is a Microsoft 365 project: start with sharing settings, permissions, retention, sensitivity labels and DLP, including Power Automate DLP for connectors.
+Old, unarchived SharePoint content and duplicate versions make Copilot look like it hallucinates, so archive or restrict content and keep metadata and folder structures simple.
+Strong adoption comes from continuous, outcome-focused support in the business rather than one-time training days, while token-based tools like Copilot Cowork need cost awareness.
+Worth quoting
+“they forget about permissions they forget about retention they forget about a DLP they forget about the labeling aspect” – Paul Keijzers (11:46)
+“copilot readiness isn't really a copilot project it's Microsoft 365 project it's understand your share point environment it's understand who can access what” – Mirko Peters (53:21)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on Copilot readiness
+Paul Keijzers – Microsoft MVP who explains what a Copilot-ready tenant needs before the rollout
+Microsoft 365 Copilot – the AI assistant that surfaces whatever overshared or outdated content a tenant holds
+SharePoint – the storage layer behind Teams and OneDrive, where old migrated files confuse Copilot
+Related episode: Beyond Copilot: Building Enterprise AI Agents That Actually Work with Copilot Studio with Manpreet Singh [MVP-MCT]
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Buying Copilot licenses is easy, but Copilot then surfaces years of SharePoint, Teams and OneDrive content that was never meant to be shared. In this episode, Microsoft MVP Paul Keijzers explains to IT leaders and Microsoft 365 admins what a Copilot-ready tenant really means. You get practical advice on oversharing, Purview labels and DLP, content lifecycle, adoption and agent governance.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Is your tenant ready for Copilot?</li><li>02:37 – Paul's journey from car audio to SharePoint and Copilot</li><li>11:33 – What companies underestimate</li><li>15:11 – Old SharePoint content and content lifecycle</li><li>21:28 – Oversharing, Purview, labels and <a href="https://www.m365.fm/entity/dlp/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">DLP</a></li><li>30:17 – Adoption, champions and Copilot costs</li><li>40:46 – Agents and <a href="https://www.m365.fm/entity/ai-agent/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">Agent</a> 365</li><li>45:08 – Focus weeks and rapid fire round</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Copilot readiness is a <a href="https://www.m365.fm/entity/microsoft-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">Microsoft 365</a> project: start with sharing settings, permissions, retention, sensitivity labels and DLP, including Power Automate DLP for connectors.</li><li>Old, unarchived SharePoint content and duplicate versions make Copilot look like it hallucinates, so archive or restrict content and keep metadata and folder structures simple.</li><li>Strong adoption comes from continuous, outcome-focused support in the business rather than one-time training days, while token-based tools like Copilot Cowork need cost awareness.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“they forget about permissions they forget about retention they forget about a DLP they forget about the labeling aspect” – Paul Keijzers (11:46)</p>
<p>“copilot readiness isn't really a copilot project it's Microsoft 365 project it's understand your share point environment it's understand who can access what” – Mirko Peters (53:21)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/paul-keijzers/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">Episode page</a>: the full episode with chapters, quotes and FAQ on Copilot readiness</li><li><a href="https://www.m365.fm/entity/paul-keijzers/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">Paul Keijzers</a> – Microsoft MVP who explains what a Copilot-ready tenant needs before the rollout</li><li><a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">Microsoft 365 Copilot</a> – the AI assistant that surfaces whatever overshared or outdated content a tenant holds</li><li><a href="https://www.m365.fm/entity/sharepoint/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">SharePoint</a> – the storage layer behind Teams and OneDrive, where old migrated files confuse Copilot</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/manpreet-singh/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=paul-keijzers">Beyond Copilot: Building Enterprise AI Agents That Actually Work with Copilot Studio with Manpreet Singh [MVP-MCT]</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## How AI Changed Software Development Forever — Building the Agentic Future with Andre Baltieri [MVP] (74870393, 235 Abrufe, 3663 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,33 +1,25 @@
-Artificial intelligence is changing software development at a speed we have rarely seen before.Developers have already moved from writing every line of code themselves to working with AI assistants that can generate code, explain unfamiliar systems, create tests, debug applications, and automate repetitive work.But according to Microsoft MVP Andre Baltieri, that is only the beginning.In https://www.m365.fm/andre-baltieri/ of M365.FM, Mirko Peters sits down with Andre for a deep dive into the transition from traditional software development to AI-assisted development, coding agents, agentic architectures, https://www.m365.fm/microsoft-agent-framework-simply-explained/, .NET, RAG, context engineering, security, and the economics of generative AI.
-FROM .NET IN 2003 TO THE AI ERA
-Andre takes us back to the early days of .NET and C#, when learning a new Microsoft technology often meant purchasing official training and traveling to another city.Since then, software development has moved through desktop, web, mobile, cloud, containers, microservices, and https://www.m365.fm/serverless-computing-simply-explained/.Andre argues that the transition to AI feels fundamentally different. Instead of simply introducing another platform or framework, AI introduces a new way for humans to interact with software.
-AI ASSISTANTS VS. AI CODING AGENTS
-There is an important difference between having an AI assistant inside your IDE and delegating work to an agent.An assistant can explain code, suggest refactoring, answer questions, and help developers understand their applications.An agent can receive a goal, create a plan, divide the work into smaller tasks, use tools, coordinate additional agents, and implement significant parts of the solution.Andre explains how this is already changing his own development workflow, with AI now generating much of the code he previously would have written manually.
-SPEC-DRIVEN SOFTWARE DEVELOPMENT
-As agents become more capable, specifications become increasingly important.Instead of describing every implementation detail, developers can define requirements, architecture, constraints, and expected behavior and allow agents to determine how parts of the implementation should be completed.This shifts developer attention from simply producing code toward defining what should be built and why.
-MICROSOFT AGENT FRAMEWORK
-The conversation moves into Microsoft Agent Framework and its role in bringing AI capabilities into existing applications.Andre explains how the framework brings together capabilities associated with Semantic Kernel and AutoGen and provides developers with tools for connecting models, orchestrating workflows, using MCP, implementing RAG, handling data ingestion, and exposing application functionality to AI.For .NET developers in particular, this can significantly reduce the amount of integration code required.
-WHY .NET STILL MATTERS IN THE AI ERA
-Python remains one of the dominant languages in AI development, but Andre argues strongly that .NET and C# are extremely well positioned for enterprise AI applications..NET continues to evolve rapidly, while Microsoft's AI tooling increasingly gives C# developers native access to modern AI capabilities.Organizations with years of business logic already implemented in .NET may therefore have a major advantage: they do not necessarily need to rebuild everything before introducing AI.Existing functionality can instead be selectively exposed to agents and AI-powered applications.
-FROM DETERMINISTIC SOFTWARE TO AGENTIC SYSTEMS
-Traditional applications are largely deterministic:If X happens, execute Y.Agentic systems introduce another model:Here is the goal. Determine which actions are required to accomplish it.That represents a significant architectural shift.Instead of explicitly defining every possible path, developers increasingly define goals, tools, context, permissions, constraints, and boundaries within which AI can operate.
-DESIGN PATTERNS ARE NOT DEAD
-AI-generated code does not eliminate decades of software engineering knowledge.Clean code, maintainability, testing, architecture, and design patterns remain important because AI frequently learns how to implement new functionality by examining the existing codebase.Messy code can therefore lead to more messy code.Developers still need to understand architecture and engineering principles even when an AI agent performs much of the implementation.
-THE STOCHASTIC SOFTWARE PROBLEM
-Traditional developers expect identical inputs to produce identical outputs.Generative AI is probabilistic.The same request can produce different implementations, answers, or behavior across multiple executions.Andre discusses why this requires developers to rethink testing and validation and why strong guardrails become increasingly important when AI functionality is exposed to large numbers of users.
-CONTEXT ENGINEERING IS MORE IMPORTANT THAN PROMPTING
-Choosing the latest model is not necessarily the most important decision.Andre argues that context is everything.Developers need to understand both the business problem and the technical environment well enough to provide AI with the right information.Too little context produces weak results.Too much context can overwhelm the model.The challenge is finding the information that actually matters.
-RAG, DATA AND THE CONTEXT WINDOW
-Retrieval-Augmented Generation becomes especially important when organizations want AI systems to work with their own knowledge.But building a RAG system is not simply about putting documents into a vector database.Data needs to be cleaned, structured, chunked, retrieved, and inserted into the model's context intelligently.Andre shares an example from his own education platform, where video lessons were transcribed and indexed so users could search for concepts and jump directly to the relevant point in a video.
-MEMORY AND MANAGING AI CONTEXT
-Long-running AI conversations create another challenge: memory.As context windows fill, conversations need to be summarized or compacted.Andre explains why developers should actively manage this process instead of assuming that an AI system will always preserve the most important information.Sometimes the best solution is surprisingly simple: finish a task, close the conversation, and start again with a clean context.Specifications and Markdown files can also provide persistent project context for coding agents.
-SECURITY, PERMISSIONS AND LEAST PRIVILEGE
-Giving an AI agent access to tools and company data creates significant security implications.Andre recommends treating agents according to principles similar to human identities: close everything by default and expose only what the agent genuinely requires.Instead of giving an AI system unrestricted database access, developers should expose carefully controlled functions that return only the information required for a particular task.This becomes particularly important when agents can read or modify enterprise data.
-PROMPT INJECTION AND AI GUARDRAILS
-Prompt injection creates a new attack surface for AI-powered applications.Users can intentionally manipulate prompts, attempt to retrieve information outside the intended context, consume company resources, or persuade an AI system to perform actions its designers never anticipated.The discussion explores the importance of system instructions, application-level restrictions, controlled functions, identity, permissions, and platforms such as https://www.m365.fm/azure-ai-foundry-simply-explained/ for establishing additional security boundaries.
-AI FINOPS — DON'T USE GENERATIVE AI FOR EVERYTHING
-One of the most practical lessons from the conversation is that just because AI can perform a task does not mean AI should perform that task.Andre distinguishes between generative and deterministic workloads.If something must happen the same way every time, traditional programming may be faster, cheaper, and more reliable.He gives the example of his video workflow: Python scripts can extract audio and perform deterministic processing locally, while generative AI is reserved for tasks such as translation where generation actually adds value.The result is a hybrid architecture that can dramatically reduce unnecessary token consumption.
-BUILDING THE AGENTIC FUTURE
-Software development is moving beyond developers manually defining every individual step.Increasingly, developers will define goals, specifications, context, tools, permissions, architecture, and guardrails while AI systems determine how portions of the work should be accomplished.That does not eliminate the developer.It changes where the developer creates value.Understanding the business, designing maintainable systems, controlling context, securing tools and data, validating AI-generated work, and deciding when not to use AI may become some of the most important software engineering skills of the agentic era.RAPID FIRESingle agent or multi-agent?For complex workloads, Andre sees significant potential in multi-agent architectures and sub-agents.Prompt engineering or context engineering?Context engineering.And what comes next?More capable models, more powerful agents, better code generation, stronger architectures, and continued evolution of the tools developers use to build software.We are still at the beginning of the generative AI era.
-ABOUT THE GUEST
-Andre Baltieri is a Microsoft MVP and software development specialist with more than two decades of experience in the industry.His work focuses on .NET, C#, artificial intelligence, Microsoft Agent Framework, software architecture, and m
+AI has moved from autocomplete to agents that plan and write most of the code, and developers wonder what is left for them. Microsoft MVP Andre Baltieri shares how he builds with AI coding agents, Microsoft Agent Framework and .NET, and why context, RAG and security matter more than model choice. A practical episode for developers and architects moving existing applications into the agentic era.
+In this episode
+00:00 – AI is changing software development
+02:21 – Software development since 2003
+07:34 – AI coding assistants versus agents
+13:39 – Microsoft Agent Framework and .NET
+32:58 – Deterministic code, probabilistic AI
+38:27 – Context, RAG and memory
+51:21 – Security, least privilege and prompt injection
+62:15 – Cost, generative AI and rapid fire
+Key takeaways
+AI agents now write most of the code, but developers are still needed to understand business rules, provide good context and orchestrate the agents.
+Microsoft Agent Framework lets .NET teams expose existing functions to AI through MCP and connect multiple models with little code.
+Security comes first: give agents least privilege, expose only small purpose-built functions and add guardrails against prompt injection.
+Worth quoting
+“this doesn't mean that we don't need programmers anymore. I think there's a bit of misconception out there, because AI can generate code for us.” – Andre Baltieri (05:58)
+“another thing that I do is every time that I finish something that I say, I achieve that what I was looking for, I close the conversation and start another conversation because it starts with a clean context.” – Andre Baltieri (49:11)
+Explore more on M365.FM
+Episode page: the full conversation with chapters, quotes and an FAQ
+Andre Baltieri – the guest, a Microsoft MVP coding with .NET since 2003 and now mostly through agents
+AI agent – the shift from coding assistants to agents that plan, split tasks and write the code
+Retrieval-augmented generation (RAG) – why a good RAG with well-chunked data matters more than stuffing the context window
+Prompt injection – the main risk when exposing AI to users, compared here to SQL injection
+Related episode: Beyond Copilot: Building AI That Works in the Real World with Azure AI Foundry and Agentic AI for Frontline Workers with Fergus Kidd [MVP]
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>AI has moved from autocomplete to agents that plan and write most of the code, and developers wonder what is left for them. Microsoft MVP Andre Baltieri shares how he builds with AI coding agents, Microsoft Agent Framework and .NET, and why context, RAG and security matter more than model choice. A practical episode for developers and architects moving existing applications into the agentic era.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – AI is changing software development</li><li>02:21 – Software development since 2003</li><li>07:34 – AI coding assistants versus agents</li><li>13:39 – Microsoft Agent Framework and .NET</li><li>32:58 – Deterministic code, probabilistic AI</li><li>38:27 – Context, RAG and memory</li><li>51:21 – Security, least privilege and prompt injection</li><li>62:15 – Cost, generative AI and rapid fire</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>AI agents now write most of the code, but developers are still needed to understand business rules, provide good context and orchestrate the agents.</li><li>Microsoft Agent Framework lets .NET teams expose existing functions to AI through <a href="https://www.m365.fm/entity/mcp/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">MCP</a> and connect multiple models with little code.</li><li>Security comes first: give agents least privilege, expose only small purpose-built functions and add guardrails against prompt injection.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“this doesn't mean that we don't need programmers anymore. I think there's a bit of misconception out there, because AI can generate code for us.” – Andre Baltieri (05:58)</p>
<p>“another thing that I do is every time that I finish something that I say, I achieve that what I was looking for, I close the conversation and start another conversation because it starts with a clean context.” – Andre Baltieri (49:11)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/andre-baltieri/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">Episode page</a>: the full conversation with chapters, quotes and an FAQ</li><li><a href="https://www.m365.fm/entity/andre-baltieri/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">Andre Baltieri</a> – the guest, a Microsoft MVP coding with .NET since 2003 and now mostly through agents</li><li><a href="https://www.m365.fm/entity/ai-agent/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">AI agent</a> – the shift from coding assistants to agents that plan, split tasks and write the code</li><li><a href="https://www.m365.fm/entity/rag/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">Retrieval-augmented generation (RAG)</a> – why a good RAG with well-chunked data matters more than stuffing the context window</li><li><a href="https://www.m365.fm/entity/prompt-injection/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">Prompt injection</a> – the main risk when exposing AI to users, compared here to SQL injection</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/beyond-copilot-building-ai-that-works-in-the-real-world-with-azure-ai-foundry-and-agentic-ai-for-fr/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=andre-baltieri">Beyond Copilot: Building AI That Works in the Real World with Azure AI Foundry and Agentic AI for Frontline Workers with Fergus Kidd [MVP]</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Microsoft Fabric End-to-End: From Raw Data to Business Decisions with Amit Chandak [MVP] (74686736, 216 Abrufe, 3810 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,31 +1,23 @@
-https://www.m365.fm/microsoft-fabric-simply-explained/ brings data engineering, analytics, business intelligence, governance and increasingly https://www.m365.fm/categories/copilot-talk/ together in one platform. But what does an end-to-end Fabric architecture actually look like when you move beyond individual features and start connecting everything?In https://www.m365.fm/amit-chandak/ of the M365 FM Podcast, Mirko Peters is joined by Amit Chandak [Microsoft Data Platform MVP] for a practical journey through Microsoft Fabric — starting with raw organizational data and ending with trusted information that business users can use to make decisions.
-WHY MICROSOFT FABRIC?
-Before Fabric, organizations could already build sophisticated analytics architectures using Azure, Power BI and other platforms. The problem wasn't a lack of technology. In many cases, it was the opposite: organizations had too many choices, separate storage technologies, different compute models and multiple copies of essentially the same data.Amit explains how Microsoft Fabric attempts to simplify this architecture by bringing workloads together around shared foundations such as OneLake, common Fabric capacity and the Delta format. Lakehouses, warehouses, Power BI and other Fabric experiences can therefore operate as parts of a broader platform instead of completely isolated services.
-ONELAKE AS THE FOUNDATION
-OneLake is one of the central concepts behind Fabric. Amit compares it conceptually to OneDrive: instead of every analytics workload creating completely independent storage environments, OneLake provides a virtualized storage foundation across the Fabric tenant.Organizations can still separate data through workspaces, Lakehouses, Warehouses and domains, but those resources exist within a common Fabric storage architecture. This becomes particularly important when organizations want to reduce unnecessary duplication while maintaining security and organizational boundaries.
-CENTRALIZED DATA OR DATA MESH?
-Fabric doesn't automatically mean putting everything into one giant centralized analytics environment.For smaller organizations, a centralized architecture may still work well. As organizations become larger, Amit sees increasing value in domain-oriented architectures where areas such as sales, finance and purchasing can have their own workspaces and responsibilities.IT can remain responsible for availability, governance and the technical foundation while business domains increasingly take ownership of how their data is analyzed and consumed.
-SHORTCUTS INSTEAD OF COPYING DATA
-One of the recurring themes throughout the conversation is avoiding unnecessary copies of data.Fabric Shortcuts allow teams to reference data stored elsewhere rather than physically copying it into every environment that needs it. That can apply both inside Fabric and to supported external storage.Amit also explains an interesting architectural benefit of shortcuts: they can help separate workloads across capacities. This can become important when organizations want Power BI consumption workloads isolated from intensive data engineering workloads while still working with the same underlying information.
-LAKEHOUSE VS. WAREHOUSE
-One of the biggest Fabric architecture questions remains: Should you use a Lakehouse or a Warehouse?A Lakehouse can work with structured and unstructured data and is naturally aligned with Spark. A Fabric Warehouse focuses on structured data and provides the familiar T-SQL experience.Both ultimately use Delta for structured data inside Fabric, which means the decision increasingly comes down to the type of data, preferred technologies and workloads.Organizations with strong SQL teams don't necessarily need to abandon their existing skills. Teams working with very large datasets, advanced engineering scenarios, unstructured information or extensive data science workloads may find the Lakehouse and Spark approach more attractive.
-GETTING DATA INTO FABRIC
-Once the architecture is defined, organizations still need to bring data into Fabric.Amit walks through several approaches, including Shortcuts, Mirroring, Pipelines, Copy Activity, Copy Jobs, Dataflow Gen2 and notebooks.The right option depends heavily on the source and use case. Dataflow Gen2 remains particularly useful because of its broad connector support and familiar Power Query experience. For Power BI professionals entering Fabric, this can provide a natural starting point before moving toward more engineering-oriented approaches.
-WHEN PYSPARK BECOMES IMPORTANT
-Power Query and Dataflow Gen2 can work very well for small and medium-sized workloads, but scale changes the equation.For larger transformation workloads, Amit sees significant advantages in Spark-based processing. PySpark and Spark notebooks provide greater flexibility and are designed for distributed processing at scale.SQL and Power BI professionals don't necessarily have to make that transition immediately. Spark SQL can provide a familiar entry point for SQL developers, while many PySpark operations have conceptual similarities to transformations Power Query users already understand.
-DO YOU REALLY NEED BRONZE, SILVER AND GOLD?
-The Medallion Architecture has become almost synonymous with modern data engineering: Bronze for raw data, Silver for cleaned and transformed data, and Gold for business-ready information.But Amit argues that organizations shouldn't create layers simply because an architecture diagram says they should.If an organization already has excellent master data management and high-quality source data, every intermediate layer may not provide enough value to justify another copy and another transformation step. Where source data quality is inconsistent, however, the traditional Bronze-Silver-Gold structure remains highly valuable.
-WHERE SHOULD BUSINESS LOGIC LIVE?
-Another important architecture decision is determining where calculations and business rules belong.Amit prefers keeping measures and KPIs in the semantic model where possible because they remain dynamic and easier to change. Heavy row-level calculations across millions of records, however, are generally better handled earlier in the Gold layer.The result is not an either-or decision. A mature Fabric architecture distributes business logic deliberately between the transformation layer and semantic model depending on the type and cost of the calculation.
-SEMANTIC MODELS ARE BECOMING MORE IMPORTANT
-The semantic model was traditionally viewed primarily as the foundation for Power BI reports. AI is changing that role.Relationships, measures, KPIs and business definitions encoded within a semantic model represent organizational knowledge. That knowledge can increasingly be consumed by experiences beyond traditional dashboards.Amit discusses how Data Agents, ontology-driven solutions and Fabric Apps can build on semantic models. Instead of being merely a Power BI component, the semantic model can become a reusable business layer between organizational data and multiple human or AI-driven experiences.
-DOES DAX STILL MATTER IN THE AI ERA?
-AI can already generate DAX, SQL, PySpark and other code remarkably quickly. Does that mean professionals no longer need to learn these languages?Amit argues that expertise still matters, particularly when generated solutions don't work correctly or need optimization. AI can dramatically reduce the amount of syntax professionals need to write manually, but understanding the underlying logic remains valuable for debugging and improving what AI creates.Over time, the skill may shift from remembering syntax toward understanding architecture, algorithms, business logic and how to describe requirements precisely.
-SECURITY FROM WORKSPACE TO DATA
-Putting more organizational data into a unified platform makes security increasingly important.The discussion covers security across multiple layers, beginning with Fabric workspace roles and continuing through item-level access, OneLake security and semantic-model security.For larger organizations, Amit recommends using security groups rather than managing individual users wherever possible. Microsoft Entra provides the identity and group foundation, while Fabric applies those identities and groups to workspaces, items and data access.
-FROM DATA ENGINEERING TO BUSINESS DECISIONS
-Ultimately, most business users don't care whether their information came through PySpark, a Lakehouse, Delta tables or Dataflow Gen2. They care about getting reliable answers.This is where Amit sees Data Agents, ontology and AI-driven analytics becoming increasingly important.Instead of every user receiving the same predefined dashboard, future analytics experiences could become far more dynamic. Users may interact conversationally with organizational data and eventually have personalized reports or applications generated around their specific questions and responsibilities.
-RAPID FIRE
-The episode closes with a rapid-fire round.SQL or PySpark? PySpark.Dataflow Gen2 or Notebook? Notebook.DAX or SQL? DAX.Most underrated Fabric feature? Fabric Apps.Biggest Power BI modeling mistake? Many-to-many relationships.And perhaps the most provocative answer of the episode:Are Fabric Apps the new Power BI?Amit's answer: Yes.
-THE BIG PICTURE
-Microsoft Fabric isn't simply another analytics product to add to the Microsoft stack.Its larger opportunity is connecting ingestion, engineering, storage, Lakehouse and Warehouse architectures, semantic models, security, Power BI and emerging AI experiences into one coherent analytics platform.The technical architecture matters, but the endpoint isn't OneLake, PySpark or even Powe
+Many organizations run too many analytics tools and too many copies of the same data. In this interview, Mirko Peters and Microsoft Data Platform MVP Amit Chandak walk data engineers and BI teams through an end-to-end Microsoft Fabric architecture. You learn when to use lakehouse, warehouse, shortcuts, mirroring, Dataflow Gen2 and Spark, and how semantic models, security and data agents turn raw data into decisions.
+In this episode
+00:00 – Introduction and Amit Chandak's journey into data
+02:30 – Why Microsoft Fabric: one platform, OneLake and Delta
+07:25 – Domains, workspaces and OneLake shortcuts
+16:40 – Lakehouse vs. warehouse and SQL database
+24:00 – Ingestion: mirroring, pipelines, Dataflow Gen2 and Spark notebooks
+33:40 – Medallion architecture and semantic models
+44:50 – Security: workspaces, OneLake security and RLS
+52:00 – Data agents, self-service BI and rapid fire
+Key takeaways
+Microsoft Fabric reduces data copies by storing lakehouse and warehouse data in OneLake in Delta format and by using shortcuts and mirroring instead of physical copies.
+Choose lakehouse with Spark for unstructured data and large-scale data science, warehouse with T-SQL for structured data, and keep reusable measures in the semantic model.
+Secure Fabric in layers from workspace to item to OneLake security and RLS, assign access through Entra security groups, and expect ontology-driven data agents to change self-service BI.
+Worth quoting
+“Today we are going to end to end with Microsoft Fabric. Not looking at one isolated feature, but at how the different parts of the platform come together to create a modern analytics architecture.” – Mirko Peters (00:07)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on Fabric architecture
+Amit Chandak – Microsoft Data Platform MVP with over 22 years in data analytics, guiding the Fabric walkthrough
+Microsoft Fabric – the end-to-end platform discussed, from OneLake, shortcuts and mirroring to security and data agents
+Semantic model – where Amit prefers to keep measures and KPIs, now also feeding data agents and Fabric apps
+Related episode: Microsoft Fabric for Microsoft 365 Admins: What You Need to Know
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Many organizations run too many analytics tools and too many copies of the same data. In this interview, Mirko Peters and Microsoft Data Platform MVP Amit Chandak walk data engineers and BI teams through an end-to-end Microsoft Fabric architecture. You learn when to use lakehouse, warehouse, shortcuts, mirroring, Dataflow Gen2 and Spark, and how semantic models, security and data agents turn raw data into decisions.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Introduction and Amit Chandak's journey into data</li><li>02:30 – Why Microsoft Fabric: one platform, OneLake and Delta</li><li>07:25 – Domains, workspaces and OneLake shortcuts</li><li>16:40 – Lakehouse vs. warehouse and SQL database</li><li>24:00 – Ingestion: mirroring, pipelines, Dataflow Gen2 and Spark notebooks</li><li>33:40 – Medallion architecture and semantic models</li><li>44:50 – Security: workspaces, OneLake security and RLS</li><li>52:00 – Data agents, self-service BI and rapid fire</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Microsoft Fabric reduces data copies by storing lakehouse and warehouse data in OneLake in Delta format and by using shortcuts and mirroring instead of physical copies.</li><li>Choose lakehouse with Spark for unstructured data and large-scale data science, warehouse with T-SQL for structured data, and keep reusable measures in the semantic model.</li><li>Secure Fabric in layers from <a href="https://www.m365.fm/entity/fabric-workspace/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-end-to-end-from-raw-data-to-business-decisions-with-amit-chandak-mvp">workspace</a> to item to OneLake security and RLS, assign access through Entra security groups, and expect ontology-driven data agents to change self-service BI.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Today we are going to end to end with Microsoft Fabric. Not looking at one isolated feature, but at how the different parts of the platform come together to create a modern analytics architecture.” – Mirko Peters (00:07)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/amit-chandak/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-end-to-end-from-raw-data-to-business-decisions-with-amit-chandak-mvp">Episode page</a>: the full episode with chapters, quotes and FAQ on Fabric architecture</li><li><a href="https://www.m365.fm/entity/amit-chandak/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-end-to-end-from-raw-data-to-business-decisions-with-amit-chandak-mvp">Amit Chandak</a> – Microsoft Data Platform MVP with over 22 years in data analytics, guiding the Fabric walkthrough</li><li><a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-end-to-end-from-raw-data-to-business-decisions-with-amit-chandak-mvp">Microsoft Fabric</a> – the end-to-end platform discussed, from OneLake, shortcuts and mirroring to security and data agents</li><li><a href="https://www.m365.fm/entity/semantic-model/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-end-to-end-from-raw-data-to-business-decisions-with-amit-chandak-mvp">Semantic model</a> – where Amit prefers to keep measures and KPIs, now also feeding data agents and Fabric apps</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/microsoft-fabric-for-m365-admins/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-end-to-end-from-raw-data-to-business-decisions-with-amit-chandak-mvp">Microsoft Fabric for Microsoft 365 Admins: What You Need to Know</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## From Garage Band to Symphony Orchestra- How Microsoft 365 Governance Creates Harmony at Scale — with Heiko Brenn (74111862, 205 Abrufe, 3637 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,23 +1,24 @@
-https://www.m365.fm/categories/power-platform-talk/ can begin like a garage band. A few people collaborate, everybody knows what the others are doing, Teams are created when needed, SharePoint sites appear naturally, and external guests are invited without requiring complicated processes. But as the organization grows, more musicians join the band. Teams multiply, SharePoint sites accumulate, guests remain after projects end, naming conventions become inconsistent, ownership becomes unclear, and manual administration can no longer keep pace. In https://www.m365.fm/heiko-brenn/ of M365 FM, Mirko Peters talks with Heiko Brenn, Director of Product Marketing at BCC, about how Microsoft 365 governance can transform that growing collaboration environment from noise into something closer to a well-coordinated orchestra. With more than 30 years of IT experience spanning administration, consulting, Exchange, PowerShell, product management, and Microsoft 365 governance, Heiko combines technology and business perspectives with his passion for music to explain why governance should enable collaboration rather than restrict it.
-GOVERNANCE IS THE BALANCE BETWEEN FREEDOM AND STRUCTURE
-For Heiko, Microsoft 365 governance is fundamentally about finding the balance between creativity, freedom, and structure. Governance is often perceived as a collection of restrictions telling employees what they cannot do, but effective governance should operate differently. Employees should be able to perform their work and remain creative while the necessary rules and processes operate as unobtrusively as possible in the background. The objective is not bureaucracy for its own sake. Governance provides the framework within which people can work effectively without allowing the Microsoft 365 environment to become uncontrolled.
-GOVERNANCE, SECURITY, ADMINISTRATION AND COMPLIANCE ARE NOT THE SAME THING
-Governance is closely connected with security and compliance, but Heiko argues that they should not simply be treated as interchangeable concepts. Security provides foundational protections such as MFA and other technical security measures. Governance sits above that foundation and incorporates how people and business departments actually work. Finance, HR, Legal, Sales, Development, and Marketing may require different policies because their information, risks, business processes, and regulatory requirements are different. Effective governance therefore needs to translate organizational requirements into practical rules that allow employees to continue working while remaining within the company's required framework. ㅤ
-THERE IS NO ONE-SIZE-FITS-ALL GOVERNANCE MODEL
-Certain governance principles appear repeatedly across organizations. Ownership, lifecycle automation, policies, templates, and reporting are examples of common building blocks. The implementation, however, needs to reflect the organization itself. Guest access appropriate for Marketing may be completely inappropriate for Legal. A development team may need different collaboration rules from HR. The challenge is therefore not merely deciding that governance is required but understanding the business well enough to translate common governance principles into policies appropriate for different areas of the organization.
-GOVERNANCE IS A TEAM SPORT
-Another common question is who should own Microsoft 365 governance. Is it IT, Security, Compliance, Legal, leadership, or the business? Heiko's answer is that governance is a team sport. Executive sponsorship matters because governance often exists to satisfy company-wide responsibilities, including internal policies, external regulations, ISO requirements, and other legal or organizational obligations. IT and security teams provide technical expertise and operational capabilities, but line-of-business employees also need to participate because governance ultimately affects how they work. Implementing a governance product without involving these different groups does not mean governance has been solved. Technology supports governance, but people, responsibilities, business requirements, and executive sponsorship determine whether it actually works.
-FROM GARAGE BAND TO SYMPHONY ORCHESTRA
-Music provides the central analogy throughout the conversation. When Heiko creates music in GarageBand, the process begins creatively. There might be a drum beat, chord progression, melody, or simply an inspiring title. Creativity comes first, but eventually the song needs structure. There is an intro, verse, chorus, perhaps a pre-chorus, and an outro. Without structure, listeners can become lost. Microsoft 365 works similarly. Employees need the freedom to collaborate and create, but completely unrestricted collaboration eventually produces noise rather than harmony. The analogy becomes even stronger when more people join. A single musician can control everything personally. A band needs musicians to agree on tuning, rhythm, tempo, and the song they are playing. An orchestra containing dozens of musicians needs considerably more coordination. As Microsoft 365 grows from a few employees to thousands of users, governance increasingly performs the role of that coordination layer.
-GREAT MUSICIANS CAN STILL CREATE NOISE
-A particularly useful part of the analogy is that every individual musician could be excellent and the performance could still sound terrible. The drummer might be brilliant. The guitarist might be technically exceptional. The keyboard player might be world-class. But if everyone plays independently without listening to the others, the result is noise. Microsoft 365 can experience the same problem. Every department may be using Teams, SharePoint, OneDrive, and other services productively within its own area. But if everybody creates their own structures, naming approaches, guest processes, and lifecycle rules without coordination, the organization eventually develops a fragmented collaboration environment. Governance is what helps those individually productive activities work together.
-SMALL COMPANIES NEED GOVERNANCE TOO
-Governance is not exclusively an enterprise problem. A smaller company may need fewer policies and simpler controls, but Heiko recommends starting early rather than waiting until collaboration has already become difficult to control. His approach can essentially be summarized as think big, start small. The organization's industry also matters. A small company operating in a highly regulated environment may require stronger governance than a considerably larger organization operating under different requirements. Size influences governance complexity, but regulation, risk, information sensitivity, and business requirements can be equally important.
-WHAT JAM SESSIONS TEACH US ABOUT SELF-SERVICE
-A jam session appears spontaneous. Musicians join, contribute ideas, improvise, and create something together. But even improvisation normally contains structure. Someone might say, “Let's play a blues in D minor.” Immediately, the musicians have a shared framework. They understand the basic progression and can contribute creatively inside it. Microsoft 365 self-service can work in much the same way. Employees should be able to create and collaborate without submitting an IT ticket for every action, but they still benefit from common rules. Governance provides the equivalent of agreeing on the key and rhythm before everybody begins playing. Freedom works considerably better when everybody understands the basic framework.
-SELF-SERVICE DOES NOT HAVE TO MEAN CHAOS
-Organizations frequently react to Microsoft 365 sprawl by considering whether they should simply prevent employees from creating Teams and other workspaces. Heiko's approach is more nuanced. Organizations can introduce naming conventions, predefined templates, ownership requirements, guest policies, lifecycle controls, and other guardrails while still allowing employees to create what they need. The objective is not necessarily to centralize every Microsoft 365 action inside IT. It is to make self-service predictable and manageable. Once the guardrails are established, organizations can potentially delegate more work to line-of-business users because those users operate inside a controlled framework.
-NAMING CONVENTIONS ARE A SIMPLE BUT IMPORTANT STARTING POINT
-Teams environments can quickly become difficult to navigate when employees create workspaces without consistent naming. A useful naming convention can provide immediate context about the purpose, department, project, or other relevant characteristics of a workspace. The same concept can help with external guests, particularly when guest access is connected to temporary projects. These controls may appear basic compared with sophisticated security technology, but they help organizations answer fundamental operational questions: What is this workspace? Who owns it? Why does it exist? Who belongs there? And is it still needed?
-GUEST ACCESS NEEDS A LIFECYCLE
-External collaboration is one of Microsoft 365's major strengths, but guests frequently remain long after the reason for their access disappears. A consultant joins a six-month project. An agency collaborates with Marketing. A partner receives access to a Team. The project finishes, but nobody remembers to review the guest account. Governance needs to consider external access as something with a lifecycle rather than something granted indefinitely. Organizations need visibility into why a guest exists, what the guest can access, who is responsible for that relationship, and whether the access remains necessary.
+As Microsoft 365 grows, Teams, SharePoint sites and guest accounts multiply until collaboration turns into noise. In this interview, Heiko Brenn of BCC uses music metaphors to show IT leaders and governance owners how ownership, lifecycle management, monitoring and automation turn that sprawl into a well-coordinated orchestra.
+In this episode
+00:00 – From garage band to orchestra: the governance challenge
+02:28 – Heiko Brenn's journey from Exchange 5.5 to BCC
+05:18 – What Microsoft 365 governance means
+10:16 – Governance is a team sport
+14:26 – Music metaphors: bands, conductors and jam sessions
+28:58 – AI as conductor, workload rules and the sound check
+35:54 – Governance maturity and detecting drift
+45:43 – Sprawl, BCC's role and rapid-fire round
+Key takeaways
+Microsoft 365 governance is the balance between creativity, freedom and structure, and it works best in the background so people can collaborate without bureaucracy getting in the way.
+Governance is a team sport that needs a leadership sponsor, IT and security, and line-of-business owners, with different rules for areas such as HR and legal than for sales or marketing.
+Start early with basic policies such as naming conventions, ownership and lifecycle rules for Teams and guests, then monitor for drift and automate so sprawl stays under control as the organization grows.
+Worth quoting
+“So from my perspective, I would say governance in general is a team sport. So it's really about involving all the different, I would say even everything that you mentioned is part of the process.” – Heiko Brenn (10:33)
+“So I would definitely start at an early stage with some maybe more simplified rules, but have something in place already.” – Heiko Brenn (22:19)
+Explore more on M365.FM
+Episode page: the full interview with chapters, quotes and a governance FAQ
+Heiko Brenn – BCC's Director of Product Marketing, explaining Microsoft 365 governance through bands, conductors and jam sessions
+Governance – described as the balance between creativity, freedom and structure, run as a team sport
+Microsoft Teams – named alongside guests as the top source of sprawl without naming and lifecycle rules
+Related episode: Data Loss Prevention in Microsoft 365: Policies That Actually Work
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>As Microsoft 365 grows, Teams, SharePoint sites and guest accounts multiply until collaboration turns into noise. In this interview, Heiko Brenn of BCC uses music metaphors to show IT leaders and governance owners how ownership, lifecycle management, monitoring and automation turn that sprawl into a well-coordinated orchestra.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – From garage band to orchestra: the governance challenge</li><li>02:28 – Heiko Brenn's journey from Exchange 5.5 to BCC</li><li>05:18 – What Microsoft 365 governance means</li><li>10:16 – Governance is a team sport</li><li>14:26 – Music metaphors: bands, conductors and jam sessions</li><li>28:58 – AI as conductor, workload rules and the sound check</li><li>35:54 – Governance maturity and detecting drift</li><li>45:43 – Sprawl, BCC's role and rapid-fire round</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Microsoft 365 governance is the balance between creativity, freedom and structure, and it works best in the background so people can collaborate without bureaucracy getting in the way.</li><li>Governance is a team sport that needs a leadership sponsor, IT and security, and line-of-business owners, with different rules for areas such as HR and legal than for sales or marketing.</li><li>Start early with basic policies such as naming conventions, ownership and lifecycle rules for Teams and guests, then monitor for drift and automate so sprawl stays under control as the organization grows.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“So from my perspective, I would say governance in general is a team sport. So it's really about involving all the different, I would say even everything that you mentioned is part of the process.” – Heiko Brenn (10:33)</p>
<p>“So I would definitely start at an early stage with some maybe more simplified rules, but have something in place already.” – Heiko Brenn (22:19)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/heiko-brenn/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-garage-band-to-symphony-orchestra-microsoft-365-governance-with-heiko-brenn">Episode page</a>: the full interview with chapters, quotes and a governance FAQ</li><li><a href="https://www.m365.fm/entity/heiko-brenn/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-garage-band-to-symphony-orchestra-microsoft-365-governance-with-heiko-brenn">Heiko Brenn</a> – BCC's Director of Product Marketing, explaining Microsoft 365 governance through bands, conductors and jam sessions</li><li><a href="https://www.m365.fm/entity/governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-garage-band-to-symphony-orchestra-microsoft-365-governance-with-heiko-brenn">Governance</a> – described as the balance between creativity, freedom and structure, run as a team sport</li><li><a href="https://www.m365.fm/entity/teams/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-garage-band-to-symphony-orchestra-microsoft-365-governance-with-heiko-brenn">Microsoft Teams</a> – named alongside guests as the top source of sprawl without naming and lifecycle rules</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/data-loss-prevention-in-microsoft-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-garage-band-to-symphony-orchestra-microsoft-365-governance-with-heiko-brenn">Data Loss Prevention in Microsoft 365: Policies That Actually Work</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## How Microsoft 365 &amp; Copilot Are Redesigning the Way We Work with Tracy van der Schyff [MVP] (74744840, 198 Abrufe, 3944 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,17 +1,24 @@
-Microsoft 365 has given organizations more tools than ever to communicate, collaborate, automate, and manage information. Now https://www.m365.fm/categories/copilot-talk/ adds an entirely new layer of AI capability. But behind all the discussion about productivity, automation, agents, and AI, there is a much bigger question: are these technologies simply helping us work faster, or are they fundamentally changing the way we think, learn, communicate, collaborate, and work?In https://www.m365.fm/tracy-van-der-schyff/ of m365.fm, Mirko Peters sits down with Tracy van der Schyff to explore the human side of Microsoft 365 and Copilot. Tracy has spent years working at the intersection of technology, productivity, digital literacy, training, adoption, and organizational change. Her focus is not simply on teaching people which buttons to click. It is about helping people understand technology, use it with purpose, and become more capable because of it.The conversation goes far beyond Copilot features. Mirko and Tracy discuss digital fluency, Microsoft 365 adoption, information management, AI readiness, change management, https://www.m365.fm/responsible-ai-is-good-business-featuring-wiebke-apitzsch/, the broken digital workplace, and a powerful idea that runs throughout the episode: we design technology, but the technology we create and use also shapes us.
-FROM DIGITAL LITERACY TO DIGITAL FLUENCY
-For many years, organizations talked about PC literacy and later digital literacy. But Tracy believes those terms no longer fully describe the skills people need in a modern workplace.Knowing how to operate a computer is not enough. Knowing where a button is inside Microsoft Teams or how to upload a document to SharePoint does not necessarily mean somebody understands how to work effectively in a digital environment.Digital fluency goes further. It means understanding the purpose of a technology, knowing when it should be used, understanding how your actions affect other people, and using technology responsibly and intentionally.This becomes even more important as AI enters everyday work. Tracy explains how her original model of eight pillars of digital literacy has evolved into eleven pillars of digital fluency, now incorporating responsible AI use and the additional skills people need when working alongside AI systems.The important distinction is that these are not simply Microsoft 365 skills. They are becoming life skills.AI is also creating unexpected opportunities to develop human skills. Communicating effectively with Copilot requires people to explain what they actually want. Better questions can produce better answers, and those answers can help people formulate better questions the next time. In that sense, working with AI can improve communication, creativity, critical thinking, and the ability to express intent clearly.
-THE MICROSOFT 365 TOOL OVERLOAD PROBLEM
-Teams, Outlook, SharePoint, OneDrive, Loop, Planner, Lists, https://www.m365.fm/power-platform-simply-explained/, Copilot and countless other applications give employees enormous capabilities. But providing access to tools does not automatically teach people how those tools should fit together.Organizations often deploy technology and expect employees to figure out the rest.That can result in departmental information being shared from personal OneDrive accounts, Teams being created simply for individual meetings, documents being stored in inappropriate locations, and employees constantly switching between tools without understanding where work actually belongs.When that happens, Tracy argues that blaming users is the wrong response.If an employee was never taught the intent behind Teams, SharePoint, OneDrive, Outlook, or another application, they will naturally choose whatever tool helps them complete the immediate task. The underlying problem is often not the employee. It is the absence of a clear digital strategy.
-ME, WE, US: SIMPLIFYING THE DIGITAL WORKPLACE
-One framework Tracy uses to make the Microsoft 365 environment easier to understand is ME, WE, US.The ME space represents the individual. These are the tools and information primarily associated with your personal work.The WE space begins when people collaborate around a common goal. Microsoft Teams and collaborative SharePoint environments become particularly relevant here.The US space represents information intended for the broader organization, such as publishing environments and intranets.This sounds simple, and that is precisely the point.Employees should not need to understand every architectural detail behind Microsoft 365 before they can make a sensible decision about where their work belongs. Organizations need to translate complicated technology landscapes into models that ordinary employees can understand and apply.
-COPILOT DOES NOT FIX A BROKEN DIGITAL WORKPLACE
-One of the strongest messages from the conversation is that Microsoft 365 Copilot should not be treated as a solution for an already broken digital workplace.Copilot does not magically repair years of poor information architecture, excessive sharing, unmanaged Teams, confusing permissions, duplicated documents, abandoned SharePoint sites, or inconsistent working practices.Instead, Tracy describes AI as an amplifier.If an organization has a healthy digital environment, Copilot can amplify that healthy environment. If the underlying environment is unhealthy, AI can make those existing problems significantly more visible.In that sense, Copilot acts like a huge spotlight.Information that may previously have been difficult to discover can suddenly become much easier to surface. That can make organizations believe Copilot created a problem when, in reality, the underlying permissions, sharing practices, or information-management problems may have existed for years.The AI did not necessarily create the mess. It exposed it.
-ONTOLOGICAL DESIGN: THE THINGS WE CREATE CHANGE
-USA fascinating part of the conversation explores ontological design.The concept sounds complicated, but Tracy explains it in a very practical way: we create things, and the things we create eventually change us.That applies to software, applications, intranets, processes, social media, Microsoft Teams, Copilot, and almost every digital environment people interact with.When someone designs an application, they make decisions about how users will interact with it. Those decisions influence the behavior of the people using the application.The same principle applies at a much larger scale to the modern workplace.Employees can spend many hours every day inside Teams, Outlook, SharePoint, OneDrive, Microsoft 365, and increasingly Copilot. Those environments are therefore not neutral. They influence how people communicate, how quickly they expect responses, how they organize information, how they collaborate, and even how they think about work.The intention behind what we design matters because what people consume eventually influences them.
-WHEN ACTIVITY BECOMES CONFUSED WITH PRODUCTIVITY
-Microsoft Teams and other collaboration tools have dramatically reduced the friction required to communicate. But reducing friction can also create enormous amounts of noise.Tracy raises an interesting problem: people can begin to use visible activity as proof that they are productive.More messages. More notifications. More updates. More documents. More meetings. More channels.But every communication creates work for somebody else.A message that takes one person a few minutes to write might interrupt dozens or hundreds of other employees. Individually, that interruption may seem insignificant. Across an organization, the cumulative cost can become substantial.The question therefore should not simply be whether Microsoft 365 allows us to communicate faster. Organizations also need to ask whether all of that communication is necessary in the first place.
-AI CAN BE MORE THAN A PRODUCTIVITY TOOL
-Many discussions about Copilot focus on straightforward productivity scenarios.Summarize my emails. Summarize this meeting. Create a presentation. Rewrite this document. Analyze this information. Help me find something.Those capabilities are useful, but Tracy argues that AI can become something much more interesting.People can use AI to learn.Someone who struggles with delegation can ask Copilot how to become better at delegating. Someone intimidated by AI can ask AI how to begin learning about AI. Someone concerned about cybersecurity can ask how to protect themselves and their family. Someone who lacks confidence with a technology can use AI as a private environment for experimentation and learning.This moves the conversation from simply asking, “How much time can Copilot save?” toward asking, “How can Copilot increase human capability?”That distinction is important.The most valuable use of AI may not always be automating another task. Sometimes it may be helping someone become better at performing that task themselves.
-AI DOES NOT REMOVE HUMAN RESPONSIBILITY
-Copilot might summarize hundreds of emails, but responsibility does not disappear if an important message is missed.AI can generate a document quickly, but somebody still needs to understand why that document exists.AI can retrieve organizational information, but companies still need to understand permissions, ownership, governance, security, and information management.AI can produce an answer, but people still need the judgment required to evaluate that answer.For Tracy, this is another reason digital fluency becomes more important as AI becomes more capable.Organizations should not respond to increasingly powerful technology by investing less in human skills. They should invest more.
+Many organizations switch on Copilot and expect it to fix a chaotic Microsoft 365 environment. In this conversation, Mirko Peters and Tracy van der Schyff discuss digital fluency, the Me, We, Us model, ontological design and permanent change management for adoption leads, IT managers and business leaders. You will learn why investing in people matters more than adding another tool.
+In this episode
+00:00 – Introduction and Tracy's path into the Microsoft ecosystem
+02:09 – From PC literacy to digital fluency
+04:00 – Where work belongs: the Me, We, Us model
+11:30 – What changed when Copilot entered the workplace
+19:20 – Ontological design: what we create shapes us
+23:40 – Teams, noise and using AI to overcome fear of AI
+35:50 – Copilot in a broken digital workplace and change management
+59:30 – Rapid-fire round and closing
+Key takeaways
+Digital fluency goes beyond knowing which buttons to click: people need to use tools with purpose, efficiently and responsibly, and that now includes AI.
+Copilot does not fix a messy Microsoft 365 environment; it amplifies what is already there, so storage habits, sharing and permissions have to be addressed first.
+Change management works only as a permanent part of the company's strategy, explaining to people why practices matter rather than just telling them what to do.
+Worth quoting
+“I think in the era of AI, the responsible use of technology is going to become the most important thing, apart from all the skills that we should focus on.” – Tracy van der Schyff (03:44)
+“And whether it's co-pilot or whatever it might be, as I mentioned, it doesn't fix things, it amplifies. So, if you had a healthy environment, it's going to amplify that healthy environment.” – Tracy van der Schyff (37:46)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on digital fluency and Copilot
+Tracy van der Schyff – Microsoft MVP from South Africa who frames technology adoption around digital fluency and people
+Microsoft 365 Copilot – described as an amplifier and spotlight that exposes existing storage, sharing and permission problems
+Copilot adoption – treated as permanent change management that explains why, not a one-off project
+Related episode: Copilot Inherits Your Mess: Modernizing Microsoft 365 for AI with Richard Harbridge [MVP]
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Many organizations switch on Copilot and expect it to fix a chaotic Microsoft 365 environment. In this conversation, Mirko Peters and Tracy van der Schyff discuss digital fluency, the Me, We, Us model, ontological design and permanent change management for adoption leads, IT managers and business leaders. You will learn why investing in people matters more than adding another tool.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Introduction and Tracy's path into the Microsoft ecosystem</li><li>02:09 – From PC literacy to digital fluency</li><li>04:00 – Where work belongs: the Me, We, Us model</li><li>11:30 – What changed when Copilot entered the workplace</li><li>19:20 – Ontological design: what we create shapes us</li><li>23:40 – <a href="https://www.m365.fm/entity/teams/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=how-microsoft-365-copilot-are-redesigning-the-way-we-work-with-tracy-van-der-schyff-mvp">Teams</a>, noise and using AI to overcome fear of AI</li><li>35:50 – Copilot in a broken digital workplace and change management</li><li>59:30 – Rapid-fire round and closing</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Digital fluency goes beyond knowing which buttons to click: people need to use tools with purpose, efficiently and responsibly, and that now includes AI.</li><li>Copilot does not fix a messy Microsoft 365 environment; it amplifies what is already there, so storage habits, sharing and permissions have to be addressed first.</li><li>Change management works only as a permanent part of the company's strategy, explaining to people why practices matter rather than just telling them what to do.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“I think in the era of AI, the responsible use of technology is going to become the most important thing, apart from all the skills that we should focus on.” – Tracy van der Schyff (03:44)</p>
<p>“And whether it's co-pilot or whatever it might be, as I mentioned, it doesn't fix things, it amplifies. So, if you had a healthy environment, it's going to amplify that healthy environment.” – Tracy van der Schyff (37:46)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/tracy-van-der-schyff/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=how-microsoft-365-copilot-are-redesigning-the-way-we-work-with-tracy-van-der-schyff-mvp">Episode page</a>: the full episode with chapters, quotes and FAQ on digital fluency and Copilot</li><li><a href="https://www.m365.fm/entity/tracy-van-der-schyff/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=how-microsoft-365-copilot-are-redesigning-the-way-we-work-with-tracy-van-der-schyff-mvp">Tracy van der Schyff</a> – Microsoft MVP from South Africa who frames technology adoption around digital fluency and people</li><li><a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=how-microsoft-365-copilot-are-redesigning-the-way-we-work-with-tracy-van-der-schyff-mvp">Microsoft 365 Copilot</a> – described as an amplifier and spotlight that exposes existing storage, sharing and permission problems</li><li><a href="https://www.m365.fm/entity/copilot-adoption/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=how-microsoft-365-copilot-are-redesigning-the-way-we-work-with-tracy-van-der-schyff-mvp">Copilot adoption</a> – treated as permanent change management that explains why, not a one-off project</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/richard-harbridge/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=how-microsoft-365-copilot-are-redesigning-the-way-we-work-with-tracy-van-der-schyff-mvp">Copilot Inherits Your Mess: Modernizing Microsoft 365 for AI with Richard Harbridge [MVP]</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## From Copilot Rollout to AI Workplace: Adoption, Agents &amp; Real Business Value with Christoffer Besler Hansen [MVP] (74469132, 196 Abrufe, 3968 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,30 +1,23 @@
-https://www.m365.fm/categories/copilot-talk/ has moved beyond the question of “What can generative AI do?” The harder challenge is now turning AI into something thousands of employees actually use, trust, and derive measurable business value from. In https://www.m365.fm/christoffer-besler-hansen/ of M365 FM, Mirko Peters talks with Microsoft MVP Christoffer Besler Hansen, Head of AI Workplace at Atea Group, about what it takes to move from a Copilot rollout to a genuine AI-powered workplace. Drawing on experience supporting AI adoption across more than 8,000 employees, Christoffer shares lessons on Microsoft 365 Copilot adoption, training, agents, Copilot Studio, Microsoft Foundry, governance, security, extensibility, FinOps, and measuring business value.
-WHAT IS AN AI WORKPLACE?
-An AI workplace is much broader than simply giving employees Microsoft 365 Copilot licenses. At Atea, the AI Workplace team is responsible for how more than 8,000 users incorporate AI into their daily work. Microsoft Copilot is a major component, but the strategy also includes Copilot Studio, agentic AI, Foundry, experimentation with other technologies, and—critically—continuous user adoption. The objective is not to deploy one AI product. It is to change how people work with information, applications, and business processes.
-TECHNOLOGY MOVES FAST. PEOPLE NEED TIME.
-New AI models and capabilities can appear every week. Human working habits don't change at the same speed. Christoffer explains why organizations need to spend substantial effort helping employees feel comfortable changing established workflows. At Atea, this includes training throughout the year, sometimes every other week, with sessions designed for different audiences such as managers, consultants, salespeople, beginners, and advanced users. AI adoption therefore isn't a launch event. It is an ongoing organizational capability.
-BUYING 5,000 COPILOT LICENSES ISN'T A STRATEGY
-What should happen after an organization purchases thousands of Microsoft 365 Copilot licenses? According to Christoffer, the organization first needs to determine why it purchased them. What is the objective? What should employees accomplish differently? How will the organization support adoption? How will success be measured? Simply assigning licenses and expecting employees to teach themselves isn't enough. Employees already have jobs to perform and cannot realistically follow every weekly change across rapidly evolving AI products.
-WHY EARLY COPILOT ADOPTION OFTEN DROPS
-AI naturally generates curiosity. When users initially received Copilot without structured adoption support, Christoffer observed strong engagement for approximately the first four weeks. Employees experimented with the technology. But when they struggled to turn those experiments into new working habits, usage declined. After structured training was introduced, users were more likely to continue using Copilot over time—and began asking for additional training as the products evolved. Initial excitement gets people through the door. Continuous education helps keep them there.
-HOW DO YOU MEASURE COPILOT ROI?
-One of the hardest enterprise AI questions is determining whether Copilot is actually creating value. Usage alone isn't enough. An employee opening Copilot 50 times doesn't necessarily mean the organization has become more productive. Christoffer argues that organizations need to identify what matters to their particular business and then measure whether AI improves those outcomes. That could include completing work faster, handling more customer cases, improving quality, or increasing business capacity.
-MEASURE OUTPUT, NOT JUST AI USAGE
-One example discussed in the episode involves an employee who previously handled two cases simultaneously but could use AI to work across six while still receiving better customer feedback. That represents something more meaningful than a Copilot usage statistic. The employee is producing more output while maintaining or improving quality. The right KPI therefore depends on what the organization actually produces. AI metrics should ultimately connect with business metrics.
-COPILOT AS A THINKING PARTNER
-Meetings were one of the earliest areas where Microsoft 365 Copilot delivered obvious value. Transcription, summaries, and meeting intelligence can reduce administrative effort. But Christoffer highlights another important pattern: using AI as a thinking partner. Instead of asking AI to do all the thinking, start with your own ideas. Speak or dictate those thoughts. Let Copilot structure them. Review the result. Give feedback. Iterate until you have something useful. This approach can save time while simultaneously improving the quality of emails, presentations, documents, and other knowledge work.
-RESEARCH AGENT CHANGES KNOWLEDGE WORK
-Christoffer highlights Microsoft's Research Agent as one of the particularly valuable additions to Copilot. For large projects involving significant amounts of information, an agent capable of working through numerous sources can dramatically reduce research effort. It can also help users find information they may previously have struggled to discover manually. Importantly, users can review the underlying sources and verify whether the resulting information is correct.
-YOUR AI IS ONLY AS GOOD AS YOUR INFORMATION
-Enterprise AI quickly exposes existing information-management problems. Organizations need to think about how information is structured across SharePoint, OneDrive, CRM systems, and other repositories. https://www.m365.fm/microsoft-purview-simply-explained/ can play an important role in identifying and protecting confidential information. Retention policies also matter because outdated documents can lead AI toward outdated answers. Simply giving an agent access to more information doesn't automatically make it better. Sometimes the correct approach is to clean the data before connecting the agent.
-WHEN SHOULD YOU BUILD AN AGENT? ㅤ Christoffer recommends encouraging employees to start thinking about potential agent use cases early. Initially, organizations may create many simple agents that primarily retrieve information. Some will provide little long-term value. But experimentation changes how employees think about automation. The next maturity step is building agents that don't merely answer questions but perform actions—sending messages, updating CRM systems, triggering processes, or interacting with other applications. Eventually, organizations can move toward more autonomous agents working alongside employees.
-AGENT BUILDER VS COPILOT STUDIO
-Not every employee needs to begin with Copilot Studio. Christoffer sees many non-technical employees using Agent Builder directly inside Copilot to create simpler agents. More technical users move toward Copilot Studio when they require additional capabilities. This can create a useful progression: Idea → Simple Agent → Validation → Copilot Studio → Advanced Enterprise Agent An employee can prove the concept without becoming a professional developer, then involve technical specialists when the solution needs to become more sophisticated.
-FROM ANSWERS TO ACTIONS
-An HR agent answering “How many vacation days do I have?” is useful. An agent that can actually book next Friday as vacation represents a fundamentally different capability. This transition from information retrieval toward actions changes the architecture and security requirements surrounding AI. Christoffer expects users to interact less directly with traditional application interfaces as agents increasingly perform tasks on their behalf. Instead of navigating several administrative screens, users may simply describe the desired outcome to an agent.
-AGENT SECURITY BECOMES CRITICAL
-Once agents can take actions, organizations need strong guardrails. What can the agent do automatically? What requires explicit approval? What can it delete? Which systems can it access? What permissions does it receive? Christoffer emphasizes least privilege and approval controls, particularly when agents interact with administrative environments. Giving an autonomous agent Global Administrator privileges and allowing it to operate without restrictions would create obvious risks. The more capable agents become, the more important their permission architecture becomes.
-ENTERPRISE AGENTS NEED AN INTAKE PROCESS
-A personal agent used by one employee is different from an agent deployed to thousands of users. Enterprise-wide agents need quality control. Organizations should review instructions, permissions, connectors, integrations, and data access before allowing large numbers of employees to use them. Christoffer suggests establishing an intake process where employee ideas can be evaluated. Some agents may be returned to their creators for improvement. Strategically important ideas can instead be developed by a dedicated internal agent team.
-COPILOT EXTENSIBILITY AND AGENT 365
-The conversation also explores Copilot extensibility and the Agent 365 SDK. Christoffer describes experimenting with personal agents that have their own identities in Microsoft Entra. Such an agent could appear within an organizational structure, have its own email and Teams presence, and receive carefully controlled permissions. His example involves building an agent that can act as a personal assistant and potentially answer appropriate questions when he is away from work. The important architectural shift is that the agent begins looking less like a chatbot and more like another identity participating in the organization.
+Rolling out Microsoft 365 Copilot is easy; getting thousands of employees to use it and proving value is not. Microsoft MVP Christoffer Besler Hansen of Atea shares practical lessons for IT and business leaders on adoption, agents, Copilot Studio, governance and cost control on the way to a real AI workplace.
+In this episode
+00:00 – Introduction and guest
+01:40 – Christoffer's journey into Microsoft technology
+03:03 – What an AI workplace is and why training matters
+06:07 – Expectations, licenses and measuring value
+15:16 – Time savings, Researcher and preparing data
+22:24 – From Copilot to agents and Copilot Studio
+27:29 – Agents that take actions, guardrails and the Agent 365 SDK
+41:45 – Agent lifecycle, shadow AI, FinOps and the future of work
+Key takeaways
+Buying Copilot licenses is not enough; continuous, role-based training is what keeps people using AI after the first few weeks.
+Organizations should measure AI value against real business outcomes, prepare and label their data, and move step by step from informational agents to agents that take actions with guardrails.
+Agent sprawl, shadow AI and rising token costs call for lifecycle policies, good sanctioned tools and FinOps thinking about which model and tool to use for each task.
+Worth quoting
+“Of course but the technology is moving very quickly. It's new modules and new things every week but getting people to actually change your habits takes time.” – Christoffer Besler Hansen (04:42)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on Copilot adoption and agents
+Christoffer Besler Hansen – Microsoft MVP and head of AI workplaces at Atea, sharing lessons from its internal rollout
+Microsoft 365 Copilot – the main AI tool for Atea's more than 8,000 users and the focus of its training
+AI agent – the step from informational agents to agents that take actions, with guardrails and lifecycle policies
+Related episode: Power Platform Copilot Integration - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Rolling out Microsoft 365 Copilot is easy; getting thousands of employees to use it and proving value is not. Microsoft MVP Christoffer Besler Hansen of Atea shares practical lessons for IT and business leaders on adoption, agents, Copilot Studio, governance and cost control on the way to a real AI workplace.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Introduction and guest</li><li>01:40 – Christoffer's journey into Microsoft technology</li><li>03:03 – What an AI workplace is and why training matters</li><li>06:07 – Expectations, licenses and measuring value</li><li>15:16 – Time savings, Researcher and preparing data</li><li>22:24 – From Copilot to agents and Copilot Studio</li><li>27:29 – Agents that take actions, guardrails and the <a href="https://www.m365.fm/entity/agent-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">Agent 365</a> SDK</li><li>41:45 – Agent lifecycle, shadow AI, <a href="https://www.m365.fm/entity/finops/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">FinOps</a> and the future of work</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Buying Copilot licenses is not enough; continuous, role-based training is what keeps people using AI after the first few weeks.</li><li>Organizations should measure AI value against real business outcomes, prepare and label their data, and move step by step from informational agents to agents that take actions with guardrails.</li><li>Agent sprawl, shadow AI and rising token costs call for lifecycle policies, good sanctioned tools and FinOps thinking about which model and tool to use for each task.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Of course but the technology is moving very quickly. It's new modules and new things every week but getting people to actually change your habits takes time.” – Christoffer Besler Hansen (04:42)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/christoffer-besler-hansen/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">Episode page</a>: the full episode with chapters, quotes and FAQ on Copilot adoption and agents</li><li><a href="https://www.m365.fm/entity/christoffer-besler-h/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">Christoffer Besler Hansen</a> – Microsoft MVP and head of AI workplaces at Atea, sharing lessons from its internal rollout</li><li><a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">Microsoft 365 Copilot</a> – the main AI tool for Atea's more than 8,000 users and the focus of its training</li><li><a href="https://www.m365.fm/entity/ai-agent/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">AI agent</a> – the step from informational agents to agents that take actions, with guardrails and lifecycle policies</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/power-platform-copilot-integration/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=from-copilot-rollout-to-ai-workplace-adoption-agents-real-business-value-with-christoffer-besler-hansen-mvp">Power Platform Copilot Integration - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Architecting Power Platform for Complex Enterprise Solutions with Ian Tweedie [MVP] (74770060, 191 Abrufe, 3733 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,23 +1,24 @@
-Microsoft https://www.m365.fm/power-platform-simply-explained/ is often described as a low-code platform. But what happens when the applications you build become business-critical, highly integrated, and too complex for a simple maker-first approach?In https://www.m365.fm/ian-tweedie/ of M365 FM, Mirko Peters talks with Power Platform Solution Architect Ian Tweedie about what happens when Power Platform moves beyond simple low-code applications and becomes part of a serious enterprise architecture.
-LOW-CODE DOESN’T MEAN LOW ARCHITECTURE
-Power Platform can deliver a large percentage of business value quickly, but enterprise solutions almost always contain requirements that go beyond standard low-code capabilities.Ian explains why low-code should never be confused with no-code — and why traditional software architecture principles still matter when building with https://www.m365.fm/categories/power-platform-talk/, Power Automate, Dataverse, custom connectors, APIs, and Azure services.
-WHEN POWER PLATFORM BECOMES ENTERPRISE SOFTWARE
-There isn’t necessarily a clean line between “low-code” and “enterprise.”Complexity starts increasing when applications involve multiple user journeys, development teams, integrations, security requirements, business-critical processes, and interconnected services.At that point, architecture becomes essential.Ian explains why solutions should be divided into clearly defined features and modules with clean interfaces instead of becoming one large interconnected application.
-ESCAPING THE WHACK-A-MOLE DEVELOPMENT PROBLEM
-Fix one bug and another appears somewhere else.That familiar development problem is often a symptom of tightly coupled architecture.Ian discusses how modular design can isolate functionality and reduce unintended dependencies. Using email delivery as an example, he explains how separating business processes from delivery mechanisms can make applications easier to test, maintain, replace, and scale.
-LOW-CODE + PRO-CODE = HYBRID ARCHITECTURE
-Power Platform doesn’t have to compete with traditional software development.A Power Apps frontend might represent only a small part of a much larger application using Azure, AWS, GCP, APIs, or custom services.The important architectural question isn’t whether something is “low-code” or “pro-code.”It’s which technology is best suited to each feature.
-CITIZEN DEVELOPERS, MAKERS AND ARCHITECTURE
-Citizen developers bring something extremely valuable: deep knowledge of the business processes they work with every day.But business expertise doesn’t automatically translate into good application architecture.Ian discusses the balance between empowering makers and introducing enough architecture, governance, normalization, and technical review to prevent solutions from becoming difficult to maintain.
-GOVERNANCE WITHOUT KILLING INNOVATION
-Too little governance creates chaos.Too much governance creates friction — and can drive employees toward unsupported workarounds, spreadsheets, VBA, and shadow IT.The challenge is finding the right level of governance based on organizational risk, application criticality, users, and business impact.
-POWER PLATFORM, APIs AND AZURE
-Where should business logic live?Should secrets be stored inside Power Platform? When should Azure Key Vault, https://www.m365.fm/azure-functions-simply-explained/, or API Management become part of the architecture?Ian explains why architecture should always begin with the problem being solved rather than adding Azure services simply because they are available.
-GIT, SOURCE CONTROL AND CI/CD
-As Power Platform development becomes more collaborative, traditional development practices become increasingly relevant.The conversation explores Git, repositories, development environments, pipelines, source control, feature isolation, cross-dependencies, and CI/CD.There may not always be a perfect approach to source control in Power Platform — sometimes the goal is choosing the “least worst option” for the project.
-IAN’S POWER PLATFORM ARCHITECTURE PLAYBOOK
-Ian’s core principle is straightforward:Break solutions into features and modules.Each feature should have a clear reason to exist and ideally perform one specific responsibility.Then determine how those features communicate, where logic should execute, how they should be tested, and which technology is best suited to implementing them.
-THE RAPID-FIRE ROUND
-Mirko puts Ian through a series of quick questions:Should every enterprise application use Dataverse?Can Power Platform build mission-critical applications?Can Power Automate replace Logic Apps?Does low-code automatically reduce technical debt?Can Power Platform replace traditional application development?And perhaps most importantly: what should you order when visiting Newcastle?
-KEY TAKEAWAY
-Low-code does not mean low architecture.As https://www.m365.fm/power-platform-solutions/ become larger, more connected, and more important to the business, the fundamentals of software engineering remain relevant.Architecture matters.Data modeling matters.Governance matters.Security matters.API design matters.DevOps matters.And successful enterprise Power Platform development is increasingly about understanding how low-code, pro-code, Azure, APIs, automation, and traditional software engineering practices work together.
+Power Platform solutions often start as quick low-code apps and end up business-critical, integrated and hard to maintain. In this interview Ian Tweedie explains to Power Platform makers, developers and architects how modular features, server-side logic, Key Vault, Git-based ALM and intent-based governance keep enterprise solutions maintainable.
+In this episode
+00:00 – Intro: when low-code becomes enterprise
+02:28 – Ian's path to Power Platform
+08:14 – Breaking solutions into features and modules
+20:14 – Just enough architecture for citizen developers
+30:21 – AI, MCP and modular design
+40:57 – Secrets, Key Vault and environment variables
+46:03 – Git, ALM and source control
+51:24 – Governance, the architecture playbook and rapid-fire
+Key takeaways
+Low-code is not no-code: once Power Platform solutions become business-critical, classic clean-architecture principles such as single-purpose, decoupled features apply just as in pro-code.
+Business-critical logic should run server side, and secrets belong in a governed store such as Azure Key Vault rather than in reversible places like environment variables.
+Governance works best when it defines intent and lets makers show how they meet it, while source control in Power Platform always means choosing the least-worst option.
+Worth quoting
+“if it's something that has to be right and always must be accurate then we need to execute that server side” – Ian Tweedie (07:44)
+“If we're storing it in a place that's reversible then we potentially shouldn't be storing it there unless it's somewhere like key vault where it's got the right governance around it.” – Ian Tweedie (41:04)
+Explore more on M365.FM
+Episode page: the full interview with chapters, quotes and FAQ on Power Platform architecture
+Ian Tweedie – solution architect who explains his feature-first playbook for enterprise Power Platform solutions
+Power Platform – treated here as a low-code, not no-code, platform that needs clean architecture once solutions turn business-critical
+Governance – framed by Ian as defining intent and letting makers show how they will meet it
+Related episode: Power Platform Copilot Integration - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Power Platform solutions often start as quick low-code apps and end up business-critical, integrated and hard to maintain. In this interview Ian Tweedie explains to Power Platform makers, developers and architects how modular features, server-side logic, Key Vault, Git-based ALM and intent-based governance keep enterprise solutions maintainable.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Intro: when low-code becomes enterprise</li><li>02:28 – Ian's path to Power Platform</li><li>08:14 – Breaking solutions into features and modules</li><li>20:14 – Just enough architecture for citizen developers</li><li>30:21 – AI, <a href="https://www.m365.fm/entity/mcp/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=architecting-power-platform-for-complex-enterprise-solutions-with-ian-tweedie">MCP</a> and modular design</li><li>40:57 – Secrets, Key Vault and environment variables</li><li>46:03 – Git, ALM and source control</li><li>51:24 – Governance, the architecture playbook and rapid-fire</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Low-code is not no-code: once Power Platform solutions become business-critical, classic clean-architecture principles such as single-purpose, decoupled features apply just as in pro-code.</li><li>Business-critical logic should run server side, and secrets belong in a governed store such as Azure Key Vault rather than in reversible places like environment variables.</li><li>Governance works best when it defines intent and lets makers show how they meet it, while source control in Power Platform always means choosing the least-worst option.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“if it's something that has to be right and always must be accurate then we need to execute that server side” – Ian Tweedie (07:44)</p>
<p>“If we're storing it in a place that's reversible then we potentially shouldn't be storing it there unless it's somewhere like key vault where it's got the right governance around it.” – Ian Tweedie (41:04)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/ian-tweedie/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=architecting-power-platform-for-complex-enterprise-solutions-with-ian-tweedie">Episode page</a>: the full interview with chapters, quotes and FAQ on Power Platform architecture</li><li><a href="https://www.m365.fm/entity/ian-tweedie/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=architecting-power-platform-for-complex-enterprise-solutions-with-ian-tweedie">Ian Tweedie</a> – solution architect who explains his feature-first playbook for enterprise Power Platform solutions</li><li><a href="https://www.m365.fm/entity/power-platform/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=architecting-power-platform-for-complex-enterprise-solutions-with-ian-tweedie">Power Platform</a> – treated here as a low-code, not no-code, platform that needs clean architecture once solutions turn business-critical</li><li><a href="https://www.m365.fm/entity/governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=architecting-power-platform-for-complex-enterprise-solutions-with-ian-tweedie">Governance</a> – framed by Ian as defining intent and letting makers show how they will meet it</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/power-platform-copilot-integration/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=architecting-power-platform-for-complex-enterprise-solutions-with-ian-tweedie">Power Platform Copilot Integration - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## SharePoint Isn&#x27;t Boring Anymore: How Copilot Is Reinventing the Modern Workplace with Marcin Siewnicki [MVP] (74711575, 181 Abrufe, 3646 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,33 +1,24 @@
-For years, SharePoint has carried a reputation for complicated document libraries, outdated intranets, confusing navigation, too many sites, and information that employees simply cannot find. But Microsoft 365 is changing, and https://www.m365.fm/categories/copilot-talk/ is making SharePoint more important than it has been in a long time.In https://www.m365.fm/marcin-siewnicki/ of the M365 FM Podcast, Mirko Peters talks with Microsoft MVP Marcin Siewnicki about how SharePoint is evolving from a traditional document and intranet platform into a central information and knowledge layer for the modern workplace. Marcin has worked with SharePoint since the SharePoint 2003 era, giving him more than two decades of perspective on how the platform has changed.
-WHY SHAREPOINT GOT A BAD REPUTATION
-Much of SharePoint’s reputation was created by the way organizations implemented it. Intranets were often designed by IT, heavily customized, difficult to use, and disconnected from what employees actually needed.Instead of continuously gathering feedback and improving the experience, many companies delivered an intranet and expected employees to adapt to it. The result was complex navigation, outdated content, overloaded pages, and systems people avoided whenever possible.
-INFORMATION ARCHITECTURE BEFORE TECHNOLOGY
-One of the biggest problems is not SharePoint itself but how information is organized inside it. Without a clear information architecture, SharePoint can quickly become a huge shared folder filled with duplicated files, outdated information, unclear ownership, and multiple versions of the same document.Marcin explains why organizations should start with a simple structure, understand their data, remove unnecessary content, and introduce basic metadata. Information architecture does not have to be complicated to make SharePoint significantly easier to use.
-BUILDING A MODERN SHAREPOINT WORKPLACE
-A modern SharePoint homepage should not become an endless collection of web parts, corporate announcements, applications, and links. It should be simple, personalized, visually clear, and focused on what employees actually need.Communication sites can provide departments and organizations with modern, mobile-friendly publishing experiences without requiring the enormous custom intranet projects that were common in the past. The focus should be on useful information, important applications, relevant documents, straightforward navigation, and strong search capabilities.
-SOLVING THE SHAREPOINT NAVIGATION PROBLEM
-Navigation remains one of SharePoint’s biggest challenges. Organizations frequently attempt to expose every department, application, resource, and internal page through a single navigation structure.Marcin explains why simpler navigation usually works better. Global navigation should focus on the most important destinations, while detailed navigation can be provided closer to individual departments, sites, and business areas. Otherwise, navigation itself becomes another information problem.
-SHAREPOINT AND TEAMS SPRAWL
-Microsoft Teams and SharePoint are deeply connected. Every new Team and many Teams channels can introduce additional SharePoint resources, which means uncontrolled Teams creation can quickly become uncontrolled SharePoint growth.Organizations therefore need simple creation processes, templates, basic metadata, lifecycle management, and user education. Employees should understand when they need a Team, when a SharePoint site is sufficient, and what happens behind the scenes when these collaboration environments are created.One useful way of looking at the relationship is to think of Microsoft Teams as the collaboration interface while SharePoint provides much of the document and information layer underneath it.
-GOVERNANCE WITHOUT KILLING INNOVATION
-Governance does not need to mean preventing employees from using new technology. The goal is to provide enough freedom for people to work effectively while maintaining control over information, permissions, external sharing, security, and lifecycle management.Marcin discusses periodically reviewing inactive SharePoint sites and Teams, identifying environments that are no longer needed, checking ownership, reviewing permissions, and archiving or removing obsolete workspaces.Governance also cannot remain exclusively an IT exercise. Business stakeholders and users need to be involved because overly complicated policies often lead employees to find their own workarounds.
-PERMISSIONS, SHARING AND SECURITY
-Permissions become increasingly difficult to understand as SharePoint environments grow. Users add colleagues, external partners, vendors, and sharing links over time, but access is rarely reviewed with the same frequency.Regular permission reviews should therefore become part of the governance model. Site and Team owners need responsibility for checking who still requires access and whether external sharing remains necessary.https://www.m365.fm/microsoft-purview-simply-explained/ sensitivity labels can add another security layer by helping organizations classify and protect information based on its sensitivity.
-AUTOMATING SHAREPOINT GOVERNANCE
-Governance does not have to be completely manual. PowerShell, Microsoft Graph, https://www.m365.fm/power-automate-simply-explained/, https://www.m365.fm/azure-logic-apps-simply-explained/, and specialized third-party platforms can automate many administrative and governance processes.Marcin sees PowerShell and Microsoft Graph as fundamental tools for administrators, while Power Automate can provide practical automation for provisioning, approvals, notifications, lifecycle processes, and many other SharePoint scenarios.
-MODERN DOCUMENT MANAGEMENT
-SharePoint is still heavily associated with documents, and documents remain an important part of the platform. The challenge is managing them properly.Metadata, naming conventions, permissions, versioning, storage management, and sensitivity labels all contribute to a healthier information environment. Versioning deserves particular attention because large documents with many retained versions can consume significant amounts of SharePoint storage.
-METADATA VS. FOLDERS
-The old SharePoint debate between folders and metadata has not completely disappeared. Marcin argues that metadata remains extremely valuable, but organizations need to keep their metadata models simple.If users need to spend too much time deciding how to classify every document, adoption will suffer. Metadata should support the way employees work rather than creating another administrative task.
-COPILOT CAN AUTOMATE METADATA
-Copilot changes this equation because AI can reduce the manual work associated with metadata. SharePoint can analyze documents, extract relevant information, and populate columns based on the content.Organizations still need to decide which metadata is useful, but employees no longer necessarily have to enter everything manually. This can make structured information much more practical at scale.
-COPILOT CHANGES SHAREPOINT
-Copilot significantly lowers the amount of SharePoint knowledge employees need before they can start accomplishing useful work.Users can increasingly create content, work with documents, extract information, generate pages, and interact with organizational knowledge using natural language instead of understanding every technical SharePoint concept.Many of the repetitive tasks traditionally associated with maintaining SharePoint environments can therefore become easier.
-FROM FINDING DOCUMENTS TO GETTING ANSWERS
-This may be the biggest change of all.Traditional SharePoint experiences required employees to find the right site, navigate to the right library, locate the correct document, open it, and search for the information they needed.Copilot changes that interaction. Instead of only finding documents, employees can increasingly ask questions and receive answers based on information stored across their Microsoft 365 environment.SharePoint therefore starts moving from document storage toward becoming an enterprise knowledge layer.
-COPILOT CAN UNDERSTAND MORE THAN OFFICE DOCUMENTS
-Organizational knowledge is not limited to Word documents, Excel files, and PowerPoint presentations.Copilot can work with different types of information, including text, HTML, Markdown, SharePoint lists, and content extracted from video transcripts.That means training videos, recorded meetings, presentations, and other media stored within the Microsoft 365 environment can become part of the knowledge available through AI.
-WHAT HAPPENED TO SHAREPOINT AGENTS?
-SharePoint Agents provide dedicated AI experiences grounded in selected SharePoint sites, document libraries, or information sources.Marcin discusses where these agents fit into the current Copilot landscape and why the concept has become less prominent as Copilot itself gains broader capabilities for interacting directly with SharePoint information.
-IS SHAREPOINT REALLY COPILOT’S KNOWLEDGE LAYER?
-There is certainly marketing around the idea, but there is also a strong technical reality behind it.Organizations already store enormous amounts of business information in SharePoint and Microsoft Teams. Copilot can use this information, which means the quality of the underlying environment directly affects the quality of the AI experience.Poor permissions, outdated documents, duplicated information, weak metadata, and uncontrolled SharePoint sprawl do not disappear because Copilot has been introduced. They potentially become even more important
+SharePoint has long been seen as complicated and boring, but Copilot turns it into the knowledge layer of the modern workplace. In this conversation, MVP Marcin Siewnicki shares practical advice for IT pros, intranet owners and governance teams on information architecture, sprawl, metadata and permissions. You will learn what to fix before AI arrives and how Copilot, agents and Power Automate fit together.
+In this episode
+00:00 – Intro and Marcin's SharePoint journey
+05:45 – Why SharePoint got a bad reputation
+17:20 – Sprawl, Teams and SharePoint
+27:47 – Governance policies for SharePoint and Teams
+33:38 – Document management and metadata
+41:09 – What Copilot changes in SharePoint
+47:46 – SharePoint agents and Power Automate
+54:35 – Rapid fire round
+Key takeaways
+SharePoint's bad reputation stems mostly from missing information architecture and IT-driven intranets rather than from the platform itself.
+Simple governance such as site request forms with business justification, periodic usage and permission reviews, and controlled versioning keeps SharePoint and Teams manageable.
+Copilot makes SharePoint the main knowledge source of the organization, so basic metadata and well-governed content directly improve AI answers, while Power Automate remains the choice for deterministic processes.
+Worth quoting
+“So usually SharePoint is a shared folder for huge bucket for everything. So there's no information architecture. And then it's hard to find information, hard to find documents.” – Marcin Siewnicki (08:17)
+“I always encourage people to build or implement even basic metadata, policy metadata model, because it will help them later, and metadata are supported by copilot” – Marcin Siewnicki (38:26)
+Explore more on M365.FM
+Episode page: the full conversation with chapters, quotes and an FAQ on SharePoint and Copilot
+Marcin Siewnicki – Microsoft 365 solution architect who shares 20 years of SharePoint project experience in this episode
+SharePoint – the platform at the center of the talk, from its reputation problem to Copilot readiness
+Microsoft 365 Copilot – turns SharePoint content into answers, so metadata and governed content directly shape its results
+Related episode: Microsoft 365 Copilot Without the Hype: Adoption, Governance & Getting Your Tenant Ready with Paul Keijzers [MVP]
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>SharePoint has long been seen as complicated and boring, but Copilot turns it into the knowledge layer of the modern workplace. In this conversation, MVP Marcin Siewnicki shares practical advice for IT pros, intranet owners and governance teams on information architecture, sprawl, metadata and permissions. You will learn what to fix before AI arrives and how Copilot, agents and Power Automate fit together.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Intro and Marcin's SharePoint journey</li><li>05:45 – Why SharePoint got a bad reputation</li><li>17:20 – Sprawl, Teams and SharePoint</li><li>27:47 – Governance policies for SharePoint and Teams</li><li>33:38 – Document management and metadata</li><li>41:09 – What Copilot changes in SharePoint</li><li>47:46 – SharePoint agents and <a href="https://www.m365.fm/entity/power-automate/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">Power Automate</a></li><li>54:35 – Rapid fire round</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>SharePoint's bad reputation stems mostly from missing information architecture and IT-driven intranets rather than from the platform itself.</li><li>Simple governance such as site request <a href="https://www.m365.fm/entity/microsoft-forms/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">forms</a> with business justification, periodic usage and permission reviews, and controlled versioning keeps SharePoint and Teams manageable.</li><li>Copilot makes SharePoint the main knowledge source of the organization, so basic metadata and well-governed content directly improve AI answers, while Power Automate remains the choice for deterministic processes.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“So usually SharePoint is a shared folder for huge bucket for everything. So there's no information architecture. And then it's hard to find information, hard to find documents.” – Marcin Siewnicki (08:17)</p>
<p>“I always encourage people to build or implement even basic metadata, policy metadata model, because it will help them later, and metadata are supported by copilot” – Marcin Siewnicki (38:26)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/marcin-siewnicki/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">Episode page</a>: the full conversation with chapters, quotes and an FAQ on SharePoint and Copilot</li><li><a href="https://www.m365.fm/entity/marcin-siewnicki/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">Marcin Siewnicki</a> – Microsoft 365 solution architect who shares 20 years of SharePoint project experience in this episode</li><li><a href="https://www.m365.fm/entity/sharepoint/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">SharePoint</a> – the platform at the center of the talk, from its reputation problem to Copilot readiness</li><li><a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">Microsoft 365 Copilot</a> – turns SharePoint content into answers, so metadata and governed content directly shape its results</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/paul-keijzers/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=marcin-siewnicki">Microsoft 365 Copilot Without the Hype: Adoption, Governance &amp; Getting Your Tenant Ready with Paul Keijzers [MVP]</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## What Happens When Sales Promises an Urgent Order (75585104, 172 Abrufe, 3625 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,72 +1,22 @@
-An urgent customer request sounds simple: sales promises a fast delivery date, marks the order as priority, and asks production to fit it in. But the new order does not enter an empty factory. It enters a schedule already filled with machine reservations, material allocations, setup plans, qualified people, inspection capacity, maintenance windows, and promises made to other customers. The real question is therefore not simply whether the urgent order can be produced, but which existing commitment absorbs the disruption when it moves forward.
-A PROMISE IS NOT A PRODUCTION PLAN
-A commercial promise tells the customer what the business intends to deliver. A feasible production date proves that there is actually a path through material, machining, assembly, inspection, packing, and shipping within the available time.
-ERP can hold requested dates, promised dates, production orders, materials, and routing information, but a priority flag does not create capacity. A CNC machine still has limited hours, inspection still needs qualified people and equipment, and shipping still has carrier cutoffs. Urgency changes priority; it does not remove physical constraints.
-FINITE CAPACITY EXPOSES THE REAL TRADE-OFF
-Infinite-capacity planning can place several orders against the same resource and leave the collision for production to solve later. Finite-capacity scheduling forces that conflict into the open.
-If the urgent order receives Tuesday morning on a CNC machine, another operation loses Tuesday morning. That displaced order may then miss assembly, inspection, or packing windows and lose far more time than the urgent order actually consumed.
-The first scheduling move therefore creates a chain reaction through the remaining route.
-MATERIAL DOESN'T OBEY PRIORITY FLAGS
-Inventory showing as available does not always mean it is usable for the urgent order. Material may already be allocated to another customer order, still be waiting for quality release, require a specific batch or supplier, or have traceability and shelf-life restrictions.
-Reallocating material can save the urgent customer while quietly creating a shortage somewhere else. The factory has not removed the constraint; it has transferred it.
-The same applies to fixtures, gauges, special packaging, test equipment, and other physical resources that multiple orders may depend on.
-MACHINE CAPACITY IS NOT USABLE CAPACITY
-A machine can have an open calendar slot and still be unavailable for the work. The required setter may not be on shift, an operator may lack the necessary certification, the fixture may be installed somewhere else, or the CNC program may not be released for the current product revision.
-Real capacity exists only when the machine, people, tools, material, process approvals, and time window come together.
-That is why an alternate machine is not automatically an alternate production route. A proven alternate route needs approved tooling, programs, quality checks, realistic cycle times, and people who can actually run the work.
-THE BOTTLENECK MOVES
-An urgent order may initially look like a machining problem. Once machining finds a solution, the pressure can move immediately to assembly, inspection, testing, packing, or even one person responsible for an approval.
-A bottleneck is not permanently attached to one machine. It is whichever constraint currently limits the flow of work toward shipment.
-This is why high equipment utilization does not automatically mean good delivery performance. A plant can have efficient machines and still ship late because the wrong work is waiting at the wrong constraint at the wrong time.
-THE SECOND-ORDER EFFECTS ARE WHERE THE DAMAGE SPREADS
-The visible effect of an urgent order is easy to see: it moves forward.
-The less visible effect is everything that moves backward.
-One displaced machining operation can delay an assembly component. That missing component can create partial work, additional handling, another inspection window, and finally a missed shipment. Another order may lose a fixture, material allocation, test bench, or skilled person even though it never shares the original machine with the urgent order.
-Factories operate through dependencies, not isolated departments.
-An urgent order changes product, process, and resource relationships throughout that network.
-DELIVERY DATES HAVE TO BE RECALCULATED
-When work moves, the old customer dates should not simply remain untouched in ERP.
-A displaced order needs a new feasible path through every remaining operation. Machining must finish before assembly can start, assembly must finish before inspection, and inspection must finish early enough for packing and the carrier cutoff.
-An order can technically finish production on its due date and still arrive late because the truck already left.
-Customer service therefore needs a realistic ship date and the assumptions behind it, not reassurance based on a date that the current production situation no longer supports.
-WHY EXCEL BECOMES THE EMERGENCY CONTROL ROOM
-In many factories, the planner pulls information from ERP, MES, production supervisors, purchasing, quality, maintenance, and supplier updates into one spreadsheet because that is the fastest way to rebuild the complete situation.
-Excel itself is not the problem. It is flexible and practical.
-The problem appears when the spreadsheet becomes the only place where the real production decision exists. Sales sees one date in ERP, planning sees another date in a workbook, and the shop floor follows a sequence changed during the previous shift.
-The deeper issue is missing shared context between the systems.
-CONTEXT CONNECTS THE FACTS
-A machine record, work order, material quantity, operator roster, and customer due date are useful facts. They become useful for urgent-order decisions when the relationships between them are explicit.
-The system needs to understand that:
-• This operation belongs to this work order
-• This work order supports this customer commitment
-• This operation can run on these approved resources
-• This material is allocated to this production order
-• This tool or fixture is required for this process
-• This person is qualified for this operation
-• This inspection must happen before shipment
-A knowledge graph or similar relationship model can help make those dependencies visible and traceable instead of leaving them inside spreadsheets and people's heads.
-WHERE https://www.m365.fm/microsoft-fabric-simply-explained/ AND POWER BI FIT
-https://www.m365.fm/categories/security-talk/ Fabric can provide a shared data foundation across ERP, MES, maintenance, quality, machine data, and planning information. It can help prepare, govern, history, and connect data used for cross-system analysis.
-Power BI can expose current load, orders at risk, material status, queue development, and delivery exposure so sales, planning, production, and customer service work from a more consistent view.
-But neither Fabric nor Power BI is automatically a finite-capacity scheduling engine.
-A scheduling or optimization layer still needs to test resource calendars, routing dependencies, setups, material availability, skills, maintenance windows, and other constraints before a production option can be considered feasible.
-SIMULATION BEFORE YOU MOVE THE WORK
-Instead of immediately pushing an urgent order to the front, simulation allows planning to test the consequences first.
-Possible scenarios might include:
-• Move the urgent order ahead of existing work
-• Add controlled overtime
-• Use an approved alternate route
-• Split the shipment
-• Offer a later delivery date
-• Decline the requested date when no safe feasible option exists
-Each option moves risk somewhere. Simulation makes those consequences visible before production starts changing machines, people, materials, and schedules.
-PREDICTION, SIMULATION, OPTIMIZATION, AND AI
-These technologies solve different problems.
-Prediction estimates what may happen. Simulation tests what happens if the plant chooses a specific response. Optimization searches across available options for the best schedule according to defined objectives and constraints.
-Generative AI can help planners understand those results, ask questions in natural language, summarize the trade-offs, and prepare communication for sales or customer service.
-AI should not invent finite-capacity schedule mathematics from a prompt. A fluent answer is not proof that the production plan is feasible.
-WHO GETS TO CALL AN ORDER URGENT?
-Urgency needs governance.
-A customer line-down situation is different from a late internal request. A contractual recovery is different from a strategic opportunity. A safety-related requirement may justify disruption that a normal expedite request does not.
-Without clear categories and decision rights, everything eventually becomes urgent and normal work becomes whatever nobody defended loudly enough.
-Production should be able to return a feasibility answer that explains what is possible, what conditions apply, and which existing commitments change if the request is accepted.
+When sales promises an urgent delivery date, the order lands in a factory schedule that is already full, and other customers quietly absorb the delay. This episode is for manufacturing planners, operations leaders and data architects who connect ERP, MES and analytics. It shows how to turn urgent requests into visible, tested trade-offs with a shared promise process and a layered decision architecture.
+In this episode
+00:00 – The urgent order and the factory scenario
+05:45 – A promise is not a production plan
+10:10 – Machine time, displaced orders, material and labor
+34:00 – Shifting bottlenecks, OEE and cascading delivery dates
+52:50 – Excel, missing context and Microsoft Fabric as the data layer
+70:30 – Simulation, prediction and optimization
+79:05 – Who defines priority: governance and a shared promise process
+88:10 – Decision architecture, Copilot and human judgment
+Key takeaways
+A priority flag in ERP does not create capacity: an urgent order always takes machine time, material, people or inspection slots from existing commitments.
+Finite capacity scheduling and simulation make the trade-off visible before the plant moves, while OEE dashboards and Excel recovery files only describe parts of the situation.
+Microsoft Fabric, Power BI, Power Platform and Copilot can connect ERP and MES facts and route approvals, but the feasibility decision needs scheduling logic, defined urgency categories and an accountable human owner.
+Explore more on M365.FM
+Episode page: the full episode with chapters, key takeaways and an FAQ on urgent order promises
+Microsoft Fabric – the shared data layer tying ERP orders, MES events and supply data together, without solving scheduling
+Power BI – the shared view of order exposure and capacity pressure for sales, planning and production
+Microsoft Excel – the planner's emergency control room when ERP and MES do not talk to each other
+Microsoft 365 Copilot – a safer interface once data, scheduling logic and approvals exist, for questions and customer update drafts
+Related episode: Power Platform Copilot Integration - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>When sales promises an urgent delivery date, the order lands in a factory schedule that is already full, and other customers quietly absorb the delay. This episode is for manufacturing planners, operations leaders and data architects who connect ERP, MES and analytics. It shows how to turn urgent requests into visible, tested trade-offs with a shared promise process and a layered decision architecture.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – The urgent order and the factory scenario</li><li>05:45 – A promise is not a production plan</li><li>10:10 – Machine time, displaced orders, material and labor</li><li>34:00 – Shifting bottlenecks, OEE and cascading delivery dates</li><li>52:50 – Excel, missing context and Microsoft Fabric as the data layer</li><li>70:30 – Simulation, prediction and optimization</li><li>79:05 – Who defines priority: governance and a shared promise process</li><li>88:10 – Decision architecture, Copilot and human judgment</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>A priority flag in ERP does not create capacity: an urgent order always takes machine time, material, people or inspection slots from existing commitments.</li><li>Finite capacity scheduling and simulation make the trade-off visible before the plant moves, while OEE dashboards and Excel recovery files only describe parts of the situation.</li><li>Microsoft Fabric, Power BI, <a href="https://www.m365.fm/entity/power-platform/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Power Platform</a> and Copilot can connect ERP and MES facts and route approvals, but the feasibility decision needs scheduling logic, defined urgency categories and an accountable human owner.</li></ul>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/urgent-order-sales-promises/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Episode page</a>: the full episode with chapters, key takeaways and an FAQ on urgent order promises</li><li><a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Microsoft Fabric</a> – the shared data layer tying ERP orders, MES events and supply data together, without solving scheduling</li><li><a href="https://www.m365.fm/entity/power-bi/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Power BI</a> – the shared view of order exposure and capacity pressure for sales, planning and production</li><li><a href="https://www.m365.fm/entity/excel/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Microsoft Excel</a> – the planner's emergency control room when ERP and MES do not talk to each other</li><li><a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Microsoft 365 Copilot</a> – a safer interface once data, scheduling logic and approvals exist, for questions and customer update drafts</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/power-platform-copilot-integration/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=what-happens-when-sales-promises-an-urgent-order">Power Platform Copilot Integration - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>
