# Dry-Run Shownotes -> Spreaker

2026-11-01T08:30:47+00:00 · 60 Folgen offen, 0 ungueltig, 0 unbekannt, 10 im Diff (meistgehoerte zuerst). Schreiben erst mit Datei shownotes/APPROVED.

## Power Apps Component Framework - Simply Explained (76020421, 0 Abrufe, 3541 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,12 +1,24 @@
-The controls you drag onto a Power Apps screen are only half the story. Underneath them sits a second layer that lets developers build their own controls, the kind that turn plain forms into real maps, custom grids, and interfaces that feel made by hand.
-In this episode of Simply Explained you will learn:
-- The Hidden Half of Power Apps
-- The Wall Every Power App Hits Eventually
-- What the Component Framework Actually Is
-- How a Component Works Under the Hood
-- From Idea to Shipped Component
-- Where You'll Actually Meet These Components
-- The Honest Limits and the Mistakes to Avoid
-- Where This Fits in Your Microsoft World
-- What to Take Away and One Question for You
-Simply Explained by M365.FM breaks down Microsoft 365, Azure and modern IT topics in clear, jargon-free language. Hosted by Mirko Peters.
+Every Power Apps maker eventually hits a wall where the standard controls are not enough. This episode explains the Power Apps component framework in plain English for makers, business users and aspiring developers: what code components are, how they work and when they are worth the effort. You will learn to spot the limits early and plan custom controls without creating fragile apps.
+In this episode
+00:00 – The hidden half of Power Apps
+00:38 – The wall every Power App hits
+02:17 – What the component framework is
+04:00 – How a component works
+06:04 – From idea to shipped component
+08:05 – Where you meet code components
+09:33 – Limits and mistakes to avoid
+11:36 – Where PCF fits in the Microsoft world
+Key takeaways
+The Power Apps component framework lets developers build custom code components that behave like any other control in model-driven apps, canvas apps and Power Pages.
+Building a code component is real developer work with a manifest, lifecycle methods, TypeScript, the Power Platform CLI and packaging into a Dataverse solution.
+Use PCF only when standard controls or canvas components cannot do the job, and plan for ownership and maintenance before a custom control becomes a black box.
+Worth quoting
+“Makers build the app, developers build the components, and the two meet inside a single solution. Neither one has to pretend to be the other.” – Mirko Peters (03:52)
+“A code component is a self-contained piece of user interface. It has its own look, its own behavior, and it's packaged so it can be reused across different apps and different environments.” – Mirko Peters (02:47)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on code components
+Power Apps – the low-code platform whose standard controls hit a ceiling that code components fill
+Canvas app – the drag-and-drop app style where code components run alongside maker-built canvas components
+Model-driven app – the data-driven app style where PCF first became generally available, before canvas apps
+Related episode: Power Platform Environments - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Every Power Apps maker eventually hits a wall where the standard controls are not enough. This episode explains the Power Apps component framework in plain English for makers, business users and aspiring developers: what code components are, how they work and when they are worth the effort. You will learn to spot the limits early and plan custom controls without creating fragile apps.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – The hidden half of Power Apps</li><li>00:38 – The wall every Power App hits</li><li>02:17 – What the component framework is</li><li>04:00 – How a component works</li><li>06:04 – From idea to shipped component</li><li>08:05 – Where you meet code components</li><li>09:33 – Limits and mistakes to avoid</li><li>11:36 – Where PCF fits in the Microsoft world</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>The Power Apps component framework lets developers build custom code components that behave like any other control in model-driven apps, canvas apps and <a href="https://www.m365.fm/entity/power-pages/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Power Pages</a>.</li><li>Building a code component is real developer work with a manifest, lifecycle methods, TypeScript, the <a href="https://www.m365.fm/entity/power-platform/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Power Platform</a> CLI and packaging into a Dataverse solution.</li><li>Use PCF only when standard controls or canvas components cannot do the job, and plan for ownership and maintenance before a custom control becomes a black box.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Makers build the app, developers build the components, and the two meet inside a single solution. Neither one has to pretend to be the other.” – Mirko Peters (03:52)</p>
<p>“A code component is a self-contained piece of user interface. It has its own look, its own behavior, and it's packaged so it can be reused across different apps and different environments.” – Mirko Peters (02:47)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/power-apps-component-framework/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Episode page</a>: the full episode with chapters, quotes and FAQ on code components</li><li><a href="https://www.m365.fm/entity/power-apps/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Power Apps</a> – the low-code platform whose standard controls hit a ceiling that code components fill</li><li><a href="https://www.m365.fm/entity/canvas-app/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Canvas app</a> – the drag-and-drop app style where code components run alongside maker-built canvas components</li><li><a href="https://www.m365.fm/entity/model-driven-app/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Model-driven app</a> – the data-driven app style where PCF first became generally available, before canvas apps</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/power-platform-environments/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=power-apps-component-framework">Power Platform Environments - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Windows Update Management: Autopatch, Update Rings and Feature Updates Explained (75992271, 0 Abrufe, 3209 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,4 +1,24 @@
-Windows update management gets painful when rings, deadlines and feature updates are handled in separate corners of the organization. This episode of M365 FM explains how Windows Autopatch, update rings and feature updates fit together, and how to build a rollout model that your service desk and your users can live with.
-We look at how to design deployment rings, how to pace quality updates and feature updates, which signals tell you to pause a rollout, and how to handle exceptions without letting them quietly become the default.
-You will learn how to choose between Autopatch and self-managed update rings, how to set expectations for users and the helpdesk, and how to keep a clear picture of compliance across your Windows estate.
-Who it is for: Microsoft 365, Intune and endpoint administrators, endpoint architects and IT managers who are responsible for keeping Windows devices secure and current.
+Most teams still treat Windows patching as a monthly event, while updates now run continuously and exploits arrive within days. This episode walks IT admins through Windows Update for Business, Intune update rings, feature update policies, Windows Autopatch, expedited updates, drivers, reporting and troubleshooting. You will leave with an operating model that turns patching into governed, measurable change.
+In this episode
+00:00 – Patching is not an event
+01:12 – The old model and why it breaks
+06:04 – Desired state and Windows Update for Business
+15:56 – Update rings, deadlines and feature update policies
+32:33 – What Windows Autopatch actually is
+49:18 – Expedited updates and drivers
+59:50 – Failures, reporting and metrics
+83:47 – From patching devices to governing change
+Key takeaways
+Modern Windows updates run as a continuous, client-side system: Intune declares the policy and Windows Update for Business delivers, wherever the device is.
+Design staged rings with real deadlines, pin feature versions deliberately against the support calendar, and use Autopatch to automate execution, not accountability.
+Measure exposure windows and time to patch instead of a single compliance percentage, and give policy, pilots and exceptions named owners with a monthly review.
+Worth quoting
+“Patch Tuesday was never meant to be a deadline. It was a signal. Microsoft was telling you that new updates were available and that the clock had started.” – Mirko Peters (01:59)
+“The cost of delay is invisible. Nothing happens until it does. And when it does, it's not a ticket. It's an incident.” – Mirko Peters (05:35)
+Explore more on M365.FM
+Microsoft Intune – the policy plane where update rings, feature update policies, expedites and reports live
+Microsoft Entra ID – devices must be Entra ID joined or hybrid joined before Windows Autopatch accepts them
+Governance – the closing argument that continuous change needs continuous governance with named owners
+Mirko Peters – host of this episode, who asks listeners for their next topic in the outro
+Related episode: Group Policy - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Most teams still treat Windows patching as a monthly event, while updates now run continuously and exploits arrive within days. This episode walks IT admins through Windows Update for Business, Intune update rings, feature update policies, Windows Autopatch, expedited updates, drivers, reporting and troubleshooting. You will leave with an operating model that turns patching into governed, measurable change.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Patching is not an event</li><li>01:12 – The old model and why it breaks</li><li>06:04 – Desired state and Windows Update for Business</li><li>15:56 – Update rings, deadlines and feature update policies</li><li>32:33 – What Windows Autopatch actually is</li><li>49:18 – Expedited updates and drivers</li><li>59:50 – Failures, reporting and metrics</li><li>83:47 – From patching devices to governing change</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Modern Windows updates run as a continuous, client-side system: <a href="https://www.m365.fm/entity/intune/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Intune</a> declares the policy and Windows Update for Business delivers, wherever the device is.</li><li>Design staged rings with real deadlines, pin feature versions deliberately against the support calendar, and use Autopatch to automate execution, not accountability.</li><li>Measure exposure windows and time to patch instead of a single compliance percentage, and give policy, pilots and exceptions named owners with a monthly review.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Patch Tuesday was never meant to be a deadline. It was a signal. Microsoft was telling you that new updates were available and that the clock had started.” – Mirko Peters (01:59)</p>
<p>“The cost of delay is invisible. Nothing happens until it does. And when it does, it's not a ticket. It's an incident.” – Mirko Peters (05:35)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/entity/intune/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft Intune</a> – the policy plane where update rings, feature update policies, expedites and reports live</li><li><a href="https://www.m365.fm/entity/entra-id/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft Entra ID</a> – devices must be Entra ID joined or hybrid joined before Windows Autopatch accepts them</li><li><a href="https://www.m365.fm/entity/governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Governance</a> – the closing argument that continuous change needs continuous governance with named owners</li><li><a href="https://www.m365.fm/entity/mirko-peters/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Mirko Peters</a> – host of this episode, who asks listeners for their next topic in the outro</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/group-policy-simply-explained/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Group Policy - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Microsoft Fabric for Microsoft 365 Admins: What You Need to Know (75992221, 0 Abrufe, 3644 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,3 +1,23 @@
-Fabric is not just a data engineer topic. Admins meet it through capacities, workspaces, licensing and governance. In this episode of M365 FM, we introduce the parts of Microsoft Fabric that matter to Microsoft 365 administrators: capacities, tenant settings, workspaces, OneLake and security.
-You will learn what to expect, what to ask and where admin responsibility starts and ends.
-Who it is for: Microsoft 365 and Power BI admins, platform owners and IT leaders who support analytics teams.
+Microsoft Fabric often appears in a tenant before anyone has planned its governance. This episode gives Microsoft 365 admins the platform view: how capacities, OneLake, workspaces, tenant settings, identity, labels and licensing fit together. It ends with a practical 30-day plan to put owners and guardrails in place before data and costs drift.
+In this episode
+00:00 – Why Fabric lands on the M365 admin's desk
+06:36 – Capacities, throttling and monitoring
+18:57 – OneLake: one copy for the tenant
+22:09 – Workspaces, items and tenant settings
+38:11 – Identity and the layered security model
+57:09 – Connecting Microsoft 365 data, Copilot and auditing
+75:39 – A 30-day admin plan and common failures
+Key takeaways
+Fabric runs as one shared platform inside your tenant, so a single capacity is at once a billing object, a performance boundary and a blast radius.
+Workspaces are the real unit of control, so every workspace needs a name, an owner, group-based roles and a lifecycle before sprawl sets in.
+Security, labels and AI agents only protect what is configured at every layer, so review tenant settings, OneLake access paths and copied Microsoft 365 data early.
+Worth quoting
+“A capacity unit isn't a server or a machine. It's a measure of how much work the platform can do for you per second, and every action in fabric costs some amount of it.” – Mirko Peters (06:56)
+“You stop controlling data by controlling where it lives. You start controlling it by controlling who can reach it.” – Mirko Peters (20:56)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes, FAQ and the 30-day admin plan
+Microsoft Fabric – the SaaS data platform running inside your tenant on one compute pool and one bill
+Fabric workspace – the real unit of control, needing a name, an owner, group roles and a lifecycle
+Microsoft Purview – supplies the sensitivity labels, DLP policies for semantic models and the audit log for Fabric activity
+Related episode: Data Loss Prevention in Microsoft 365: Policies That Actually Work
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Microsoft Fabric often appears in a tenant before anyone has planned its governance. This episode gives Microsoft 365 admins the platform view: how capacities, OneLake, workspaces, tenant settings, identity, labels and licensing fit together. It ends with a practical 30-day plan to put owners and guardrails in place before data and costs drift.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Why <a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Fabric</a> lands on the M365 admin's desk</li><li>06:36 – Capacities, throttling and monitoring</li><li>18:57 – OneLake: one copy for the tenant</li><li>22:09 – Workspaces, items and tenant settings</li><li>38:11 – Identity and the layered security model</li><li>57:09 – Connecting <a href="https://www.m365.fm/entity/microsoft-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Microsoft 365</a> data, Copilot and auditing</li><li>75:39 – A 30-day admin plan and common failures</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Fabric runs as one shared platform inside your tenant, so a single capacity is at once a billing object, a performance boundary and a blast radius.</li><li>Workspaces are the real unit of control, so every <a href="https://www.m365.fm/entity/fabric-workspace/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">workspace</a> needs a name, an owner, group-based roles and a lifecycle before sprawl sets in.</li><li>Security, labels and AI agents only protect what is configured at every layer, so review tenant settings, OneLake access paths and copied Microsoft 365 data early.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“A capacity unit isn't a server or a machine. It's a measure of how much work the platform can do for you per second, and every action in fabric costs some amount of it.” – Mirko Peters (06:56)</p>
<p>“You stop controlling data by controlling where it lives. You start controlling it by controlling who can reach it.” – Mirko Peters (20:56)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/microsoft-fabric-for-m365-admins/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Episode page</a>: the full episode with chapters, quotes, FAQ and the 30-day admin plan</li><li><a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Microsoft Fabric</a> – the SaaS data platform running inside your tenant on one compute pool and one bill</li><li><a href="https://www.m365.fm/entity/fabric-workspace/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Fabric workspace</a> – the real unit of control, needing a name, an owner, group roles and a lifecycle</li><li><a href="https://www.m365.fm/entity/purview/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Microsoft Purview</a> – supplies the sensitivity labels, DLP policies for semantic models and the audit log for Fabric activity</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/data-loss-prevention-in-microsoft-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=microsoft-fabric-for-m365-admins">Data Loss Prevention in Microsoft 365: Policies That Actually Work</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Intune and Autopilot at Scale: What Breaks in Real Rollouts (75992188, 0 Abrufe, 3584 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,3 +1,24 @@
-Autopilot demos work. Real rollouts hit networks, hardware, apps and user behavior. In this episode of M365 FM, we discuss what breaks in large Intune and Autopilot rollouts: enrollment flows, app dependencies, hardware hashes, ESP failures and support processes.
-You will learn how to design for scale, test the awkward cases and prepare your helpdesk.
-Who it is for: Endpoint engineers, Intune admins and service desk leads.
+Autopilot pilots of fifty devices look perfect, then ten thousand devices start failing in ways nobody predicted. This episode is for endpoint engineers, Intune admins and service desk leads who run large Windows rollouts. You will learn where enrollment, ESP, apps, networks and update rings break, and how to design, test and operate for scale.
+In this episode
+00:00 – Why the pilot lies
+06:15 – Enrollment paths and hardware hash registration
+16:33 – Network reality and join types
+22:58 – The enrollment status page and app deployment order
+36:25 – Policy conflicts and pre-provisioning
+43:00 – Update rings, deadlines and user trust
+49:20 – Troubleshooting, logs and fleet reporting
+59:50 – Operations, governance and the new model
+Key takeaways
+Autopilot rollouts fail at scale because a device is a sequence of dependent steps with different owners, not a thing you configure once.
+Most stalls trace back to networks, group timing, app dependencies or conflicting policies, so name the failing layer before reading logs or chasing error codes.
+Treat every profile, app and update change as a small ring-based deployment, with named owners, rollback notes and metrics such as time to productive desktop.
+Worth quoting
+“Autopilot doesn't fail because of bugs. It fails because of the model behind it. The assumption that a device is a thing you configure instead of a sequence you orchestrate.” – Mirko Peters (00:12)
+“The enrollment status page isn't there to show progress. It's there to hold the door shut, a gate that stays closed until the things you marked as required are finished.” – Mirko Peters (23:05)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on Autopilot at scale
+Microsoft Intune – the endpoint service where enrollment, the enrollment status page, app order and reports play out
+Microsoft Entra – the cloud join target in the Autopilot chain, set against hybrid join's extra dependencies
+Active Directory – the on-premises half of hybrid join, needing domain controller line of sight and a connector
+Related episode: Group Policy - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Autopilot pilots of fifty devices look perfect, then ten thousand devices start failing in ways nobody predicted. This episode is for endpoint engineers, Intune admins and service desk leads who run large Windows rollouts. You will learn where enrollment, ESP, apps, networks and update rings break, and how to design, test and operate for scale.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Why the pilot lies</li><li>06:15 – Enrollment paths and hardware hash registration</li><li>16:33 – Network reality and join types</li><li>22:58 – The enrollment status page and app deployment order</li><li>36:25 – Policy conflicts and pre-provisioning</li><li>43:00 – Update rings, deadlines and user trust</li><li>49:20 – Troubleshooting, logs and fleet reporting</li><li>59:50 – Operations, <a href="https://www.m365.fm/entity/governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=intune-and-autopilot-at-scale-what-breaks-in-real-rollouts">governance</a> and the new model</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Autopilot rollouts fail at scale because a device is a sequence of dependent steps with different owners, not a thing you configure once.</li><li>Most stalls trace back to networks, group timing, app dependencies or conflicting policies, so name the failing layer before reading logs or chasing error codes.</li><li>Treat every profile, app and update change as a small ring-based deployment, with named owners, rollback notes and metrics such as time to productive desktop.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Autopilot doesn't fail because of bugs. It fails because of the model behind it. The assumption that a device is a thing you configure instead of a sequence you orchestrate.” – Mirko Peters (00:12)</p>
<p>“The enrollment status page isn't there to show progress. It's there to hold the door shut, a gate that stays closed until the things you marked as required are finished.” – Mirko Peters (23:05)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/intune-and-autopilot-at-scale/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=intune-and-autopilot-at-scale-what-breaks-in-real-rollouts">Episode page</a>: the full episode with chapters, quotes and FAQ on Autopilot at scale</li><li><a href="https://www.m365.fm/entity/intune/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=intune-and-autopilot-at-scale-what-breaks-in-real-rollouts">Microsoft Intune</a> – the endpoint service where enrollment, the enrollment status page, app order and reports play out</li><li><a href="https://www.m365.fm/entity/microsoft-entra/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=intune-and-autopilot-at-scale-what-breaks-in-real-rollouts">Microsoft Entra</a> – the cloud join target in the Autopilot chain, set against hybrid join's extra dependencies</li><li><a href="https://www.m365.fm/entity/active-directory/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=intune-and-autopilot-at-scale-what-breaks-in-real-rollouts">Active Directory</a> – the on-premises half of hybrid join, needing domain controller line of sight and a connector</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/group-policy-simply-explained/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=intune-and-autopilot-at-scale-what-breaks-in-real-rollouts">Group Policy - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Entra ID Governance: Access Reviews, Entitlement Management and Lifecycle Workflows (75992172, 0 Abrufe, 3861 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,3 +1,23 @@
-Access that is never reviewed tends to grow. Identity governance puts lifecycle and accountability around it. In this episode of M365 FM, we look at access reviews, entitlement management and lifecycle workflows in Microsoft Entra ID Governance and how they work together.
-You will learn how to introduce governance step by step, from joiner-mover-leaver basics to access packages.
-Who it is for: Identity architects, IAM and compliance teams.
+Access that is never reviewed keeps growing, and yearly recertifications end in rubber stamps. This episode shows identity architects, IAM and compliance teams how access packages, access reviews, lifecycle workflows and PIM in Microsoft Entra ID Governance work together as one event-driven system.
+In this episode
+00:00 – The thesis: governance is a behavior problem
+03:21 – The old model and the map of Entra ID Governance
+10:00 – Identity data and licensing
+17:01 – Entitlement management, access packages and guests
+33:40 – Access reviews that people actually complete
+47:10 – Lifecycle workflows: joiners, movers and leavers
+67:45 – Privileged access with PIM
+74:56 – One system: ownership, metrics, rollout and failure patterns
+Key takeaways
+Entra ID Governance works when it is designed around real behavior: named owners, safe defaults and review tasks small enough to finish.
+Access packages with expiry, scoped access reviews with recommendations and auto-apply, and lifecycle workflows driven by clean HR attributes replace the yearly cleanup.
+Privileged roles should be eligible and activated just in time through PIM, and the whole program should be rolled out in phases starting with data quality.
+Worth quoting
+“Attribute quality is the first architecture decision, not the last one. Most teams treat it as cleanup.” – Mirko Peters (12:35)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on Entra ID Governance
+Identity lifecycle management – the joiner, mover and leaver events that lifecycle workflows turn into automatic access changes
+Microsoft Entra ID – the directory whose attributes, P1 and P2 licenses and governance add-on drive every control here
+Governance – framed here as a behavior problem solved with owners, safe defaults and small review tasks
+Related episode: Microsoft Entra Agent ID - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Access that is never reviewed keeps growing, and yearly recertifications end in rubber stamps. This episode shows identity architects, IAM and compliance teams how access packages, access reviews, lifecycle workflows and PIM in Microsoft Entra ID Governance work together as one event-driven system.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – The thesis: <a href="https://www.m365.fm/entity/governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">governance</a> is a behavior problem</li><li>03:21 – The old model and the map of <a href="https://www.m365.fm/entity/entra-id/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">Entra ID</a> Governance</li><li>10:00 – Identity data and licensing</li><li>17:01 – Entitlement management, access packages and guests</li><li>33:40 – Access reviews that people actually complete</li><li>47:10 – Lifecycle workflows: joiners, movers and leavers</li><li>67:45 – Privileged access with PIM</li><li>74:56 – One system: ownership, metrics, rollout and failure patterns</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Entra ID Governance works when it is designed around real behavior: named owners, safe defaults and review tasks small enough to finish.</li><li>Access packages with expiry, scoped access reviews with recommendations and auto-apply, and <a href="https://www.m365.fm/entity/identity-lifecycle/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">lifecycle workflows</a> driven by clean HR attributes replace the yearly cleanup.</li><li>Privileged roles should be eligible and activated just in time through PIM, and the whole program should be rolled out in phases starting with data quality.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Attribute quality is the first architecture decision, not the last one. Most teams treat it as cleanup.” – Mirko Peters (12:35)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/entra-id-governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">Episode page</a>: the full episode with chapters, quotes and FAQ on Entra ID Governance</li><li><a href="https://www.m365.fm/entity/identity-lifecycle/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">Identity lifecycle management</a> – the joiner, mover and leaver events that lifecycle workflows turn into automatic access changes</li><li><a href="https://www.m365.fm/entity/entra-id/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">Microsoft Entra ID</a> – the directory whose attributes, P1 and P2 licenses and governance add-on drive every control here</li><li><a href="https://www.m365.fm/entity/governance/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">Governance</a> – framed here as a behavior problem solved with owners, safe defaults and small review tasks</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/microsoft-entra-agent-id/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=entra-id-governance-access-reviews-entitlement-management-and-lifecycle-workflows">Microsoft Entra Agent ID - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Defender for Office 365: Tuning Anti-Phishing and Safe Links Policies (75992168, 0 Abrufe, 3737 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,3 +1,24 @@
-Anti-phishing and Safe Links policies only help if they are tuned to your organization rather than left at defaults. In this episode of M365 FM, we cover how to tune Microsoft Defender for Office 365 policies: impersonation protection, preset policies, Safe Links, Safe Attachments and reporting.
-You will learn how to reduce both missed threats and false positives.
-Who it is for: Email security admins, security engineers and SOC teams.
+Most tenants run Microsoft Defender for Office 365 on defaults and assume they are protected while attackers test their filters every day. This episode is for email security admins, security engineers and SOC teams who want to tune anti-phishing, Safe Links, Safe Attachments and quarantine into a measurable loop that reduces both missed threats and false positives.
+In this episode
+00:00 – Why defaults fail: tuning as a measurement loop
+03:48 – Plan 1 versus Plan 2 and what you are licensed for
+07:04 – Preset security policies and policy precedence
+17:20 – Impersonation and anti-phishing policy anatomy
+27:35 – SPF, DKIM, DMARC and phishing thresholds
+34:20 – Safe Links, Safe Attachments and exception debt
+50:25 – Quarantine, false positives and investigation
+67:27 – Attack simulation, metrics and the operating rhythm
+Key takeaways
+Start with the standard and strict preset policies, check which policy actually applies to each user because the first match wins, and keep custom policies only for documented, owned exceptions.
+Impersonation protection, Safe Links and Safe Attachments only work as well as the protected lists, DMARC enforcement and do-not-rewrite exceptions behind them, so every exception needs an owner, a reason and an expiry date.
+Measure delivered phish, report rate, time to remediate and false positives on a monthly and quarterly rhythm, and use attack simulation and Threat Explorer to tune instead of setting policies once and forgetting them.
+Worth quoting
+“Tuning isn't a configuration event, it's a measurement loop. You set a policy, you measure what it catches and what it misses. You adjust and you do it again.” – Mirko Peters (00:31)
+“The system doesn't merge policies. It doesn't take the stricter setting from each one it finds the first match, applies that policy and ignores everything below it.” – Mirko Peters (10:47)
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and an FAQ on policy tuning
+Microsoft Defender – the product family behind this episode, from Defender for Office 365 to Defender XDR incidents
+Exchange Online – the mail platform whose built-in Exchange Online Protection forms the base layer under Defender
+Microsoft Teams – where Safe Links checks shared links and, once switched on, Safe Attachments scans files
+Related episode: Data Loss Prevention in Microsoft 365: Policies That Actually Work
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Most tenants run Microsoft Defender for Office 365 on defaults and assume they are protected while attackers test their filters every day. This episode is for email security admins, security engineers and SOC teams who want to tune anti-phishing, Safe Links, Safe Attachments and quarantine into a measurable loop that reduces both missed threats and false positives.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Why defaults fail: tuning as a measurement loop</li><li>03:48 – Plan 1 versus Plan 2 and what you are licensed for</li><li>07:04 – Preset security policies and policy precedence</li><li>17:20 – Impersonation and anti-phishing policy anatomy</li><li>27:35 – SPF, DKIM, DMARC and phishing thresholds</li><li>34:20 – Safe Links, Safe Attachments and exception debt</li><li>50:25 – Quarantine, false positives and investigation</li><li>67:27 – Attack simulation, metrics and the operating rhythm</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Start with the standard and strict preset policies, check which policy actually applies to each user because the first match wins, and keep custom policies only for documented, owned exceptions.</li><li>Impersonation protection, Safe Links and Safe Attachments only work as well as the protected lists, DMARC enforcement and do-not-rewrite exceptions behind them, so every exception needs an owner, a reason and an expiry date.</li><li>Measure delivered phish, report rate, time to remediate and false positives on a monthly and quarterly rhythm, and use attack simulation and Threat Explorer to tune instead of setting policies once and forgetting them.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Tuning isn't a configuration event, it's a measurement loop. You set a policy, you measure what it catches and what it misses. You adjust and you do it again.” – Mirko Peters (00:31)</p>
<p>“The system doesn't merge policies. It doesn't take the stricter setting from each one it finds the first match, applies that policy and ignores everything below it.” – Mirko Peters (10:47)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/defender-for-office-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=defender-for-office-365-tuning-anti-phishing-and-safe-links-policies">Episode page</a>: the full episode with chapters, quotes and an FAQ on policy tuning</li><li><a href="https://www.m365.fm/entity/defender/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=defender-for-office-365-tuning-anti-phishing-and-safe-links-policies">Microsoft Defender</a> – the product family behind this episode, from Defender for Office 365 to Defender XDR incidents</li><li><a href="https://www.m365.fm/entity/exchange-online/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=defender-for-office-365-tuning-anti-phishing-and-safe-links-policies">Exchange Online</a> – the mail platform whose built-in Exchange Online Protection forms the base layer under Defender</li><li><a href="https://www.m365.fm/entity/teams/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=defender-for-office-365-tuning-anti-phishing-and-safe-links-policies">Microsoft Teams</a> – where Safe Links checks shared links and, once switched on, Safe Attachments scans files</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/data-loss-prevention-in-microsoft-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=defender-for-office-365-tuning-anti-phishing-and-safe-links-policies">Data Loss Prevention in Microsoft 365: Policies That Actually Work</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Data Loss Prevention in Microsoft 365: Policies That Actually Work (75992165, 0 Abrufe, 3734 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,10 +1,25 @@
-Learn how to design Microsoft Purview DLP policies that actually work. Master scoping, sensitive information types, simulation mode, and tuning to reduce risk.
-DLP policies fail when they either block everything or catch nothing. The sweet spot takes iteration. In this episode of M365 FM, we explain how to design Microsoft Purview DLP policies that work: scoping, sensitive information types, policy tips, simulation mode and tuning.
-You will learn how to roll out DLP in stages and measure whether it actually reduces risk.
-Who it is for: Compliance and security admins, Purview owners and data protection officers.
+A new DLP policy blocks everything on Monday, and by Friday half the finance team is mailing files from personal accounts. This episode is for Microsoft 365 admins and compliance owners who want Purview DLP policies people actually accept. You'll learn how to detect the right data, guide users with tips and overrides, test safely, triage alerts and measure what really works.
+In this episode
+00:00 – Why block-first DLP fails
+06:46 – The new model: context, not content alone
+12:37 – Detection: SITs, EDM, classifiers and labels
+25:29 – Policy tips and user overrides
+31:27 – Simulation, tuning, scoping and exceptions
+47:26 – Endpoint DLP, Teams, Copilot and cloud apps
+57:10 – Alert triage and measuring effectiveness
+73:48 – Phased rollout and common failure patterns
+Key takeaways
+DLP policies built to block drive users to invisible workarounds, so design policies that use context and guide people with tips before enforcing.
+Run every policy in simulation for weeks, then with tips but no enforcement, and block only high-confidence, high-volume risks with a reporting path.
+Treat DLP as an ongoing practice with a named owner, weekly tuning from overrides and triage, owned and expiring exceptions, and metrics like true positive rate instead of block counts.
+Worth quoting
+“it's failing for one reason. Not the tools, the model behind it. Policies built to block lose to policies built to guide.” – Mirko Peters (00:22)
+“A credit card number in an email to a payment processor is business. The same number in an email to a personal address is a problem.” – Mirko Peters (02:17)
 Explore more on M365.FM
-- https://www.m365.fm/data-loss-prevention-in-microsoft-365/
-- https://www.m365.fm/microsoft-purview-data-loss-prevention-dlp-simply-explained/
-- https://www.m365.fm/azure-policy-simply-explained/
-- https://www.m365.fm/categories/security-talk/
-- https://www.m365.fm/categories/best-of-microsoft-security/
+Episode page: the full episode with chapters, key quotes and an FAQ on Purview DLP
+Data loss prevention (DLP) – the core topic, rebuilt from block-first rules into context-aware policies that guide users
+Microsoft Purview – the portal where DLP policies, simulation, alerts, Activity Explorer and policy reports live
+Sensitivity labels – one policy condition that replaces many detectors and keeps labeled files out of Copilot
+Microsoft Defender – shares its sensor with endpoint DLP and correlates DLP alerts in the Defender XDR queue
+Related episode: Microsoft Fabric for Microsoft 365 Admins: What You Need to Know
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>A new DLP policy blocks everything on Monday, and by Friday half the finance team is mailing files from personal accounts. This episode is for Microsoft 365 admins and compliance owners who want Purview DLP policies people actually accept. You'll learn how to detect the right data, guide users with tips and overrides, test safely, triage alerts and measure what really works.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Why block-first DLP fails</li><li>06:46 – The new model: context, not content alone</li><li>12:37 – Detection: SITs, EDM, classifiers and labels</li><li>25:29 – Policy tips and user overrides</li><li>31:27 – Simulation, tuning, scoping and exceptions</li><li>47:26 – Endpoint DLP, Teams, <a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Copilot</a> and cloud apps</li><li>57:10 – Alert triage and measuring effectiveness</li><li>73:48 – Phased rollout and common failure patterns</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>DLP policies built to block drive users to invisible workarounds, so design policies that use context and guide people with tips before enforcing.</li><li>Run every policy in simulation for weeks, then with tips but no enforcement, and block only high-confidence, high-volume risks with a reporting path.</li><li>Treat DLP as an ongoing practice with a named owner, weekly tuning from overrides and triage, owned and expiring exceptions, and metrics like true positive rate instead of block counts.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“it's failing for one reason. Not the tools, the model behind it. Policies built to block lose to policies built to guide.” – Mirko Peters (00:22)</p>
<p>“A credit card number in an email to a payment processor is business. The same number in an email to a personal address is a problem.” – Mirko Peters (02:17)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/data-loss-prevention-in-microsoft-365/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Episode page</a>: the full episode with chapters, key quotes and an FAQ on Purview DLP</li><li><a href="https://www.m365.fm/entity/dlp/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Data loss prevention (DLP)</a> – the core topic, rebuilt from block-first rules into context-aware policies that guide users</li><li><a href="https://www.m365.fm/entity/purview/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Microsoft Purview</a> – the portal where DLP policies, simulation, alerts, Activity Explorer and policy reports live</li><li><a href="https://www.m365.fm/entity/sensitivity-labels/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Sensitivity labels</a> – one policy condition that replaces many detectors and keeps labeled files out of Copilot</li><li><a href="https://www.m365.fm/entity/defender/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Microsoft Defender</a> – shares its sensor with endpoint DLP and correlates DLP alerts in the Defender XDR queue</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/microsoft-fabric-for-m365-admins/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=data-loss-prevention-in-microsoft-365">Microsoft Fabric for Microsoft 365 Admins: What You Need to Know</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Traceability and Genealogy: Tracking Every Part From Supplier to Customer (75992006, 0 Abrufe, 3792 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,3 +1,22 @@
-Tracing every part from supplier to customer needs consistent identifiers and connected systems. In this episode of the iFAKT series, we explain the data foundations for traceability and genealogy: lot and serial concepts, system handoffs and typical gaps.
-You will learn how to design traceability that supports quality, recalls and audits.
-Who it is for: Quality managers, MES and ERP owners and manufacturing IT.
+When a supplier reports a suspect batch, many manufacturers cannot prove which products actually contain it. This episode is for quality managers, MES and ERP owners and manufacturing IT teams who need traceability that holds up in recalls and audits. You will learn how to design identities, genealogy records, integrations and investigations that support defensible decisions.
+In this episode
+00:00 – What the quality team needs to decide
+03:35 – A pump plant as the reference example
+07:14 – Traceability, genealogy and provenance
+10:53 – Tracking depth and identity rules
+18:50 – Receipt, containers and material consumption
+33:48 – Splits, rework and process evidence
+53:30 – Ownership, integration and the Azure architecture
+73:47 – Evidence, compliance, investigation and rollout
+Key takeaways
+Write traceability requirements backward from the recall and containment decisions your quality team must be able to defend.
+Record material contributions as explicit relationships captured at the moment of use, with identities, quantities and evidence sources, instead of copying planned bills of materials.
+Cloud services such as Azure and Microsoft Fabric can carry and analyze the records, but owners, tested event contracts, mock recalls and human approval decide whether the evidence holds.
+Explore more on M365.FM
+Episode page: the full episode with chapters and FAQ on genealogy, integration and recalls
+Microsoft Azure – the cloud platform whose services are placed around capture, replay and reconciliation duties
+Azure Event Hubs – suggested for streams of production events that several consumers process independently
+Microsoft Fabric – brings production, shipment and quality data together for investigations without owning holds
+Azure Service Bus – suggested for application messages that need queues, topics, locks and dead letter handling
+Related episode: Azure Event Grid - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>When a supplier reports a suspect batch, many manufacturers cannot prove which products actually contain it. This episode is for quality managers, MES and ERP owners and manufacturing IT teams who need traceability that holds up in recalls and audits. You will learn how to design identities, genealogy records, integrations and investigations that support defensible decisions.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – What the quality team needs to decide</li><li>03:35 – A pump plant as the reference example</li><li>07:14 – Traceability, genealogy and provenance</li><li>10:53 – Tracking depth and identity rules</li><li>18:50 – Receipt, containers and material consumption</li><li>33:48 – Splits, rework and process evidence</li><li>53:30 – Ownership, integration and the <a href="https://www.m365.fm/entity/azure/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Azure</a> architecture</li><li>73:47 – Evidence, compliance, investigation and rollout</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Write traceability requirements backward from the recall and containment decisions your quality team must be able to defend.</li><li>Record material contributions as explicit relationships captured at the moment of use, with identities, quantities and evidence sources, instead of copying planned bills of materials.</li><li>Cloud services such as Azure and <a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Microsoft Fabric</a> can carry and analyze the records, but owners, tested event contracts, mock recalls and human approval decide whether the evidence holds.</li></ul>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/traceability-and-genealogy/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Episode page</a>: the full episode with chapters and FAQ on genealogy, integration and recalls</li><li><a href="https://www.m365.fm/entity/azure/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Microsoft Azure</a> – the cloud platform whose services are placed around capture, replay and reconciliation duties</li><li><a href="https://www.m365.fm/entity/azure-event-hubs/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Azure Event Hubs</a> – suggested for streams of production events that several consumers process independently</li><li><a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Microsoft Fabric</a> – brings production, shipment and quality data together for investigations without owning holds</li><li><a href="https://www.m365.fm/entity/azure-service-bus/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Azure Service Bus</a> – suggested for application messages that need queues, topics, locks and dead letter handling</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/azure-event-grid-explained/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=traceability-and-genealogy-tracking-every-part-from-supplier-to-customer">Azure Event Grid - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## FinOps for Manufacturing IT: Controlling Cloud Cost for Industrial Workloads (75991847, 0 Abrufe, 3378 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,3 +1,22 @@
-Industrial workloads in the cloud need cost visibility that fits plants, lines and data volumes. In this episode of the iFAKT series, we cover applying FinOps principles in manufacturing IT: tagging, allocation, forecasting and ownership.
-You will learn how to control cloud cost for industrial workloads without slowing delivery.
-Who it is for: IT managers, cloud architects and controllers in manufacturing organizations.
+Factories running the same machines often pay more each month to collect, process and keep the data those machines produce. This episode is for manufacturing IT, platform engineers and finance teams who need to control Azure and Microsoft Fabric costs without losing the evidence behind downtime and quality investigations. It walks through baselines, telemetry, retention, capacity, commitments and fair allocation across plants.
+In this episode
+00:00 – Why factory cloud costs grow
+04:08 – FinOps ownership in manufacturing
+07:32 – Building a shared cost baseline
+14:05 – Telemetry, gateways and delivery
+32:06 – Retention and storage tiers
+44:03 – Fabric capacity and shared compute
+56:38 – Commitments and reservations
+70:33 – Allocation, showback and chargeback
+Key takeaways
+In manufacturing, cloud spend follows data handling decisions, so every cost change needs a named owner who understands the evidence and service level the plant depends on.
+A shared cost baseline, deliberate retention and storage-tier choices, and tested Fabric capacity sizing prevent savings that silently remove fault or quality evidence.
+Commitments, allocation rules and showback before chargeback only work when unused commitment, shared fixed costs and funding authority are made explicit.
+Explore more on M365.FM
+Episode page: the full episode with chapters, quotes and FAQ on factory cloud cost control
+FinOps – framed as shared engineering work between platform, plant, finance and procurement owners
+Microsoft Fabric – its shared capacity units, smoothing and throttling decide how plant workloads get sized
+Microsoft Azure – where machine readings land, with Cost Management, Blob Storage tiers and reservations discussed
+Fabric workspace – workspaces on one capacity share compute, so placement and ownership become cost decisions
+Related episode: FinOps - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Factories running the same machines often pay more each month to collect, process and keep the data those machines produce. This episode is for manufacturing IT, platform engineers and finance teams who need to control Azure and Microsoft Fabric costs without losing the evidence behind downtime and quality investigations. It walks through baselines, telemetry, retention, capacity, commitments and fair allocation across plants.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – Why factory cloud costs grow</li><li>04:08 – <a href="https://www.m365.fm/entity/finops/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">FinOps</a> ownership in manufacturing</li><li>07:32 – Building a shared cost baseline</li><li>14:05 – Telemetry, gateways and delivery</li><li>32:06 – Retention and storage tiers</li><li>44:03 – <a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">Fabric</a> capacity and shared compute</li><li>56:38 – Commitments and reservations</li><li>70:33 – Allocation, showback and chargeback</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>In manufacturing, cloud spend follows data handling decisions, so every cost change needs a named owner who understands the evidence and service level the plant depends on.</li><li>A shared cost baseline, deliberate retention and storage-tier choices, and tested Fabric capacity sizing prevent savings that silently remove fault or quality evidence.</li><li>Commitments, allocation rules and showback before chargeback only work when unused commitment, shared fixed costs and funding authority are made explicit.</li></ul>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/show/episodes/finops-for-manufacturing-it/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">Episode page</a>: the full episode with chapters, quotes and FAQ on factory cloud cost control</li><li><a href="https://www.m365.fm/entity/finops/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">FinOps</a> – framed as shared engineering work between platform, plant, finance and procurement owners</li><li><a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">Microsoft Fabric</a> – its shared capacity units, smoothing and throttling decide how plant workloads get sized</li><li><a href="https://www.m365.fm/entity/azure/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">Microsoft Azure</a> – where machine readings land, with Cost Management, Blob Storage tiers and reservations discussed</li><li><a href="https://www.m365.fm/entity/fabric-workspace/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">Fabric workspace</a> – workspaces on one capacity share compute, so placement and ownership become cost decisions</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/finops-simply-explained/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=finops-for-manufacturing-it">FinOps - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>

## Azure AI vs Copilot vs Fabric AI - Simply Explained (75940821, 0 Abrufe, 3524 Zeichen)

```diff
--- aktuell
+++ neu
@@ -1,12 +1,25 @@
-Azure AI, Copilot, and Fabric AI aren't rivals, though they sound like it. Copilot is an assistant that lives inside Word and Teams.
-In this episode of Simply Explained you will learn:
-- The three names that confuse everyone
-- Copilot is the assistant you already talk to
-- How Copilot knows about your work
-- The honest limits of Copilot
-- Fabric is where your data actually lives
-- Fabric AI is Copilot for your data
-- Azure AI is the workshop for builders
-- How the three fit together
-- What to remember, and one question for you
-Simply Explained by M365.FM breaks down Microsoft 365, Azure and modern IT topics in clear, jargon-free language. Hosted by Mirko Peters.
+Azure AI, Copilot and Fabric AI sound like rivals, and Microsoft's constant renaming makes it worse. This episode untangles the three for beginners and career changers, showing what each layer does, its honest limits and costs, and how they fit together. You'll know which one you'll actually touch first and where to start learning.
+In this episode
+00:00 – The three names that confuse everyone
+02:00 – Copilot, the assistant in your apps
+04:01 – How Copilot knows about your work
+05:40 – The honest limits of Copilot
+07:32 – Fabric, where your data lives
+09:22 – Fabric AI: Copilot for your data
+11:01 – Azure AI Foundry, the builders' workshop
+12:51 – How the three fit together
+Key takeaways
+Copilot, Fabric and Azure AI (now Microsoft Foundry) are three stacked layers of one Microsoft stack, not competing products.
+Copilot only surfaces what a user can already access, so cleaning up overshared permissions and training people matter more than buying licenses.
+Start with Copilot where your work already happens, add Fabric if you live in reports and data, and turn to Foundry only when you need to build custom AI tools or agents.
+Worth quoting
+“Copilot only sees what you can already see. It doesn't get a master key to the company” – Mirko Peters (05:08)
+“Copilot is a capable tool, and it isn't a magic wand. The first limit is that copilot doesn't fix bad permissions. It exposes them.” – Mirko Peters (05:47)
+Explore more on M365.FM
+Microsoft 365 Copilot – the assistant inside Word, Excel, Outlook and Teams that most listeners will touch first
+Microsoft Fabric – the data platform where company numbers land, get shaped and turn into Power BI reports
+Microsoft Foundry – the current name for Azure AI Studio and Azure AI Foundry, the builders' workshop
+Microsoft Azure – the cloud behind Azure AI and Azure OpenAI, though Fabric needs no Azure account
+AI agent – a model with instructions and tools that takes action, mostly built in Foundry or Copilot Studio
+Related episode: Power Platform Copilot Integration - Simply Explained
+Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.
```

<details><summary>Neue Beschreibung (HTML)</summary>

```html
<p>Azure AI, Copilot and Fabric AI sound like rivals, and Microsoft's constant renaming makes it worse. This episode untangles the three for beginners and career changers, showing what each layer does, its honest limits and costs, and how they fit together. You'll know which one you'll actually touch first and where to start learning.</p>
<p><strong>In this episode</strong></p>
<ul><li>00:00 – The three names that confuse everyone</li><li>02:00 – <a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Copilot</a>, the assistant in your apps</li><li>04:01 – How Copilot knows about your work</li><li>05:40 – The honest limits of Copilot</li><li>07:32 – <a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Fabric</a>, where your data lives</li><li>09:22 – Fabric AI: Copilot for your data</li><li>11:01 – Azure AI Foundry, the builders' workshop</li><li>12:51 – How the three fit together</li></ul>
<p><strong>Key takeaways</strong></p>
<ul><li>Copilot, Fabric and Azure AI (now <a href="https://www.m365.fm/entity/microsoft-foundry/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft Foundry</a>) are three stacked layers of one Microsoft stack, not competing products.</li><li>Copilot only surfaces what a user can already access, so cleaning up overshared permissions and training people matter more than buying licenses.</li><li>Start with Copilot where your work already happens, add Fabric if you live in reports and data, and turn to Foundry only when you need to build custom AI tools or agents.</li></ul>
<p><strong>Worth quoting</strong></p>
<p>“Copilot only sees what you can already see. It doesn't get a master key to the company” – Mirko Peters (05:08)</p>
<p>“Copilot is a capable tool, and it isn't a magic wand. The first limit is that copilot doesn't fix bad permissions. It exposes them.” – Mirko Peters (05:47)</p>
<p><strong>Explore more on M365.FM</strong></p>
<ul><li><a href="https://www.m365.fm/entity/copilot/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft 365 Copilot</a> – the assistant inside Word, Excel, Outlook and Teams that most listeners will touch first</li><li><a href="https://www.m365.fm/entity/fabric/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft Fabric</a> – the data platform where company numbers land, get shaped and turn into Power BI reports</li><li><a href="https://www.m365.fm/entity/microsoft-foundry/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft Foundry</a> – the current name for Azure AI Studio and Azure AI Foundry, the builders' workshop</li><li><a href="https://www.m365.fm/entity/azure/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Microsoft Azure</a> – the cloud behind Azure AI and Azure OpenAI, though Fabric needs no Azure account</li><li><a href="https://www.m365.fm/entity/ai-agent/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">AI agent</a> – a model with instructions and tools that takes action, mostly built in Foundry or Copilot Studio</li><li>Related episode: <a href="https://www.m365.fm/show/episodes/power-platform-copilot-integration/?utm_source=podcast&amp;utm_medium=shownotes&amp;utm_campaign=None">Power Platform Copilot Integration - Simply Explained</a></li></ul>
<p>Follow and rate M365.FM in your podcast app, and join the free M365 community at m365con.net.</p>
```

</details>
