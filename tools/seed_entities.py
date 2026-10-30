#!/usr/bin/env python3
"""Einmaliges, idempotentes Befuellen von data/entities.json: Zertifikatsstufen/-codes, Lizenzen, neue Tools (Power Platform, Office, Teams, SharePoint ...).
Bestehende, nicht leere Felder werden nie ueberschrieben; fehlende werden ergaenzt."""
import json, re, sys
P = "data/entities.json"
D = json.load(open(P)); M = {e["id"]: e for e in D}

# ---------- 1. Zertifikate: Stufe, Pruefungscode, Gueltigkeit ----------
for e in D:
    if e["type"] != "cert":
        continue
    n = e["name"].lower()
    lvl = "fundamentals" if "fundamentals" in n else "expert" if " expert" in n else "associate" if "associate" in n else "specialty" if "specialty" in n else ""
    if lvl and not e.get("level"):
        e["level"] = lvl
    if not e.get("exam"):
        e["exam"] = e["id"].upper()
    if e.get("valid_months") is None:
        e["valid_months"] = 0 if (e.get("level") == "fundamentals") else 12 if e.get("level") else 0

# ---------- 2. Lizenzen und Veroeffentlichung bestehender Produkte ----------
LIC = {"copilot": "paid", "copilot-studio": "paid", "teams": "included", "sharepoint": "included", "onedrive": "included", "exchange-online": "included",
       "power-bi": "paid", "power-apps": "paid", "power-automate": "paid", "power-pages": "paid", "dataverse": "paid", "entra-id": "included", "github-copilot": "paid",
       "vs-code": "free", "github-actions": "free", "power-platform-cli": "free", "teams-toolkit": "free", "chatgpt": "paid", "purview": "paid", "defender": "paid", "intune": "paid"}
REL = {"teams": "2017-03-14", "power-bi": "2015-07-24", "sharepoint": "2001-03", "vs-code": "2015-04-29", "github-actions": "2019-11-13", "copilot": "2023-11-01",
       "chatgpt": "2022-11-30", "gpt-5": "2025-08-07", "github-copilot": "2022-06-21", "cosmos-db": "2017-05-10", "exchange-online": "2011-06", "viva": "2021-02-04"}
for k, v in LIC.items():
    if k in M and not M[k].get("license"):
        M[k]["license"] = v
for k, v in REL.items():
    if k in M and not M[k].get("released"):
        M[k]["released"] = v


# ---------- 3. Neue Entitaeten ----------
def T(id, type, name, aliases, en, de, rel, long_en="", long_de="", **kw):
    r = [["developed_by", "microsoft"]] if kw.pop("ms", True) and type in ("product", "platform", "cert") else []
    for p, lst in rel.items():
        for x in (lst if isinstance(lst, list) else [lst]):
            r.append([p, x])
    e = {"id": id, "type": type, "name": name, "aliases": aliases, "desc": {"en": en, "de": de}, "web": kw.pop("web", ""), "wikidata": "", "wikipedia": kw.pop("wiki", ""), "docs": kw.pop("docs", ""), "rel": r}
    if long_en or long_de:
        e["long"] = {"en": long_en, "de": long_de}
    e.update({k: v for k, v in kw.items() if v not in ("", None)})
    return e


MT = "microsoft-tool"
NEW = [
    # ---- Power Platform ----
    T("power-fx", "concept", "Power Fx", ["Microsoft Power Fx"],
      "Microsoft's open-source low-code formula language, modelled on Excel formulas, used in Power Apps, Power Automate, Dataverse and Copilot Studio.",
      "Die quelloffene Low-Code-Formelsprache von Microsoft, an Excel-Formeln angelehnt, genutzt in Power Apps, Power Automate, Dataverse und Copilot Studio.",
      {"related_to": ["power-apps", "excel", "power-platform"]}, docs="https://learn.microsoft.com/power-platform/power-fx/overview",
      long_en="Power Fx lets makers express logic with formulas like =Filter(Orders, Status = \"Open\") instead of code. It is declarative and strongly typed, so formulas recalculate automatically when the data they depend on changes. Because it follows Excel conventions, people who know Excel formulas can build app logic quickly.\n\nThe language is open source and also runs outside Power Apps, for example in Dataverse formula columns and in Copilot Studio.",
      long_de="Mit Power Fx beschreiben Ersteller Logik mit Formeln wie =Filter(Bestellungen, Status = \"Offen\") statt mit Code. Die Sprache ist deklarativ und streng typisiert, Formeln berechnen sich deshalb automatisch neu, sobald sich die Daten ändern. Da sie Excel-Konventionen folgt, können Excel-Anwender App-Logik schnell aufbauen.\n\nDie Sprache ist quelloffen und läuft auch außerhalb von Power Apps, etwa in Dataverse-Formelspalten und in Copilot Studio."),
    T("power-query", "product", "Power Query", ["Microsoft Power Query", "M language"],
      "Data connection and transformation engine with a visual editor and the M language, built into Excel, Power BI, Power Apps dataflows and Fabric.",
      "Engine zum Verbinden und Aufbereiten von Daten mit visuellem Editor und der Sprache M, eingebaut in Excel, Power BI, Power-Apps-Dataflows und Fabric.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "power-platform", "related_to": ["power-bi", "excel", "fabric", "dax"]}, docs="https://learn.microsoft.com/power-query/", license="included",
      long_en="Power Query imports data from files, databases, web pages and online services, then cleans and reshapes it step by step. Every step is recorded, so the same transformation can be refreshed with one click when the source changes.\n\nThe same engine appears in several products: Get & Transform in Excel, the Power BI Desktop query editor, dataflows in Power Platform and Dataflows Gen2 in Microsoft Fabric.",
      long_de="Power Query importiert Daten aus Dateien, Datenbanken, Webseiten und Online-Diensten und bereinigt und formt sie Schritt für Schritt. Jeder Schritt wird aufgezeichnet, sodass sich dieselbe Transformation bei geänderter Quelle mit einem Klick aktualisieren lässt.\n\nDieselbe Engine steckt in mehreren Produkten: Abrufen und Transformieren in Excel, der Abfrage-Editor in Power BI Desktop, Dataflows der Power Platform und Dataflows Gen2 in Microsoft Fabric."),
    T("dax", "concept", "DAX", ["Data Analysis Expressions"],
      "Formula and query language for calculations in Power BI, Excel Power Pivot and Analysis Services semantic models.",
      "Formel- und Abfragesprache für Berechnungen in Power BI, Excel Power Pivot und semantischen Modellen von Analysis Services.",
      {"related_to": ["power-bi", "excel", "fabric"]}, docs="https://learn.microsoft.com/dax/",
      long_en="DAX defines measures, calculated columns and tables in a semantic model, for example year-to-date sales or a ratio that reacts to the filters in a report. Its filter context and row context are the key concepts to understand.\n\nSkills in DAX are tested in the Power BI Data Analyst certification PL-300.",
      long_de="DAX definiert Kennzahlen, berechnete Spalten und Tabellen in einem semantischen Modell, etwa den Umsatz seit Jahresbeginn oder eine Kennzahl, die auf Filter im Bericht reagiert. Filterkontext und Zeilenkontext sind die zentralen Konzepte.\n\nDAX-Kenntnisse werden in der Zertifizierung Power BI Data Analyst (PL-300) geprüft."),
    T("power-bi-desktop", "product", "Power BI Desktop", ["PBI Desktop"],
      "Free Windows application for connecting to data, modelling it and authoring Power BI reports before publishing them to the Power BI service.",
      "Kostenlose Windows-Anwendung zum Anbinden und Modellieren von Daten und zum Erstellen von Power-BI-Berichten vor der Veröffentlichung im Power-BI-Dienst.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "power-bi", "related_to": ["power-query", "dax"]}, docs="https://learn.microsoft.com/power-bi/fundamentals/desktop-what-is-desktop", license="free"),
    T("power-bi-service", "product", "Power BI Service", ["Power BI online", "app.powerbi.com"],
      "Cloud service of Power BI for publishing, sharing and refreshing reports, dashboards and semantic models, with workspaces, apps and row-level security.",
      "Cloud-Dienst von Power BI zum Veröffentlichen, Teilen und Aktualisieren von Berichten, Dashboards und semantischen Modellen, mit Arbeitsbereichen, Apps und Zeilensicherheit.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "power-bi", "related_to": ["fabric", "teams"]}, docs="https://learn.microsoft.com/power-bi/fundamentals/power-bi-service-overview", license="paid"),
    T("power-automate-desktop", "product", "Power Automate Desktop", ["Power Automate for desktop", "PAD"],
      "Robotic process automation (RPA) tool for Windows that records and runs desktop flows to automate repetitive tasks in desktop and web applications.",
      "Werkzeug für Robotic Process Automation (RPA) unter Windows, das Desktop-Flows aufzeichnet und ausführt, um wiederkehrende Aufgaben in Desktop- und Web-Anwendungen zu automatisieren.",
      {"instance_of": [MT, "low-code-tool"], "part_of": "power-automate", "related_to": ["automation"]}, docs="https://learn.microsoft.com/power-automate/desktop-flows/introduction", license="included"),
    T("ai-builder", "product", "AI Builder", ["Microsoft AI Builder"],
      "Power Platform capability that adds prebuilt and custom AI models, such as document processing, text classification and prompts, to apps and flows.",
      "Funktion der Power Platform, die vorgefertigte und eigene KI-Modelle, etwa Dokumentenverarbeitung, Textklassifizierung und Prompts, in Apps und Flows einbindet.",
      {"instance_of": [MT, "low-code-tool"], "part_of": "power-platform", "related_to": ["power-apps", "power-automate", "dataverse"]}, docs="https://learn.microsoft.com/ai-builder/", license="paid"),
    T("power-platform-admin-center", "product", "Power Platform admin center", ["PPAC", "admin.powerplatform.microsoft.com"],
      "Central portal for administering Power Platform environments, data policies, capacity, tenant settings and analytics.",
      "Zentrales Portal zur Verwaltung von Power-Platform-Umgebungen, Datenrichtlinien, Kapazität, Mandanteneinstellungen und Analysen.",
      {"instance_of": [MT], "part_of": "power-platform", "related_to": ["governance", "dlp", "microsoft-365-admin-center"]}, docs="https://learn.microsoft.com/power-platform/admin/admin-documentation", license="included"),
    T("power-virtual-agents", "product", "Power Virtual Agents", ["PVA"],
      "Former no-code chatbot builder of the Power Platform; it was merged into Microsoft Copilot Studio.",
      "Früherer No-Code-Chatbot-Baukasten der Power Platform; er ging in Microsoft Copilot Studio auf.",
      {"instance_of": [MT, "low-code-tool"], "part_of": "power-platform"}, outdated=True, replaced_by="copilot-studio", released="2019-11"),
    T("canvas-app", "concept", "Canvas app", ["Canvas apps", "Canvas-App"],
      "Power Apps app type where the maker designs the screen layout freely, like a slide, and connects it to data with Power Fx formulas.",
      "App-Typ in Power Apps, bei dem der Ersteller das Layout frei gestaltet, ähnlich einer Folie, und per Power-Fx-Formeln mit Daten verbindet.",
      {"related_to": ["power-apps", "power-fx"]}, docs="https://learn.microsoft.com/power-apps/maker/canvas-apps/getting-started"),
    T("model-driven-app", "concept", "Model-driven app", ["Model-driven apps", "Modellgesteuerte App"],
      "Power Apps app type generated from the Dataverse data model, with forms, views and business process flows laid out automatically.",
      "App-Typ in Power Apps, der aus dem Dataverse-Datenmodell erzeugt wird; Formulare, Ansichten und Geschäftsprozessflüsse entstehen automatisch.",
      {"related_to": ["power-apps", "dataverse"]}, docs="https://learn.microsoft.com/power-apps/maker/model-driven-apps/model-driven-app-overview"),
    T("connector", "concept", "Connector", ["Power Platform connectors", "Konnektor"],
      "Prebuilt wrapper around an API that lets Power Apps, Power Automate and Copilot Studio read and write data in hundreds of services.",
      "Vorgefertigte Hülle um eine API, mit der Power Apps, Power Automate und Copilot Studio Daten in hunderten Diensten lesen und schreiben.",
      {"related_to": ["power-platform", "power-automate", "power-apps", "dlp"]}, docs="https://learn.microsoft.com/connectors/connector-reference/"),

    # ---- Office-Apps ----
    T("microsoft-365-apps", "product", "Microsoft 365 Apps", ["Office apps", "Microsoft 365 Apps for enterprise", "Office 365 ProPlus"],
      "The installable Office applications of Microsoft 365, such as Word, Excel, PowerPoint, Outlook and OneNote, delivered and updated through subscription.",
      "Die installierbaren Office-Anwendungen von Microsoft 365, etwa Word, Excel, PowerPoint, Outlook und OneNote, per Abonnement bereitgestellt und laufend aktualisiert.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["copilot"]}, docs="https://learn.microsoft.com/microsoft-365-apps/", web="https://www.microsoft.com/microsoft-365/microsoft-365-apps", license="included"),
    T("word", "product", "Microsoft Word", ["Word"],
      "Word processor of Microsoft 365 for writing, formatting and reviewing documents, with co-authoring, comments, tracked changes and Copilot support.",
      "Textverarbeitung von Microsoft 365 zum Schreiben, Formatieren und Überarbeiten von Dokumenten, mit gemeinsamem Bearbeiten, Kommentaren, Änderungsnachverfolgung und Copilot.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365-apps", "related_to": ["copilot", "onedrive", "sharepoint", "word-online"]}, docs="https://support.microsoft.com/word", wiki="https://en.wikipedia.org/wiki/Microsoft_Word", web="https://www.microsoft.com/microsoft-365/word", released="1983-10-25", license="included",
      long_en="Word is the standard tool for letters, reports, contracts and manuscripts. Documents are stored as .docx files, ideally in OneDrive or SharePoint so several people can edit at once and keep version history.\n\nCopilot in Word can draft text, rewrite passages, summarise long documents and answer questions about their content.",
      long_de="Word ist das Standardwerkzeug für Briefe, Berichte, Verträge und Manuskripte. Dokumente liegen als .docx-Dateien vor, idealerweise in OneDrive oder SharePoint, damit mehrere Personen gleichzeitig arbeiten und Versionen nachvollziehbar bleiben.\n\nCopilot in Word kann Texte entwerfen, Passagen umformulieren, lange Dokumente zusammenfassen und Fragen zum Inhalt beantworten."),
    T("excel", "product", "Microsoft Excel", ["Excel"],
      "Spreadsheet application of Microsoft 365 for calculations, tables, charts and data analysis, with Power Query, PivotTables, dynamic arrays and Copilot.",
      "Tabellenkalkulation von Microsoft 365 für Berechnungen, Tabellen, Diagramme und Datenanalyse, mit Power Query, PivotTables, dynamischen Arrays und Copilot.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "microsoft-365-apps", "related_to": ["power-query", "dax", "power-bi", "copilot", "excel-online", "power-fx"]}, docs="https://support.microsoft.com/excel", wiki="https://en.wikipedia.org/wiki/Microsoft_Excel", web="https://www.microsoft.com/microsoft-365/excel", released="1985-09-30", license="included",
      long_en="Excel combines a grid of cells with formulas, charts and a data model. PivotTables summarise large lists, Power Query imports and cleans data, and dynamic array functions such as FILTER, SORT and XLOOKUP replace many older formula patterns.\n\nThe desktop app is the most complete version; Excel for the web covers common tasks in the browser, and Copilot in Excel can suggest formulas and analyse tables.",
      long_de="Excel verbindet ein Zellraster mit Formeln, Diagrammen und einem Datenmodell. PivotTables fassen große Listen zusammen, Power Query importiert und bereinigt Daten, und Funktionen für dynamische Arrays wie FILTER, SORTIEREN und XVERWEIS ersetzen viele ältere Formelmuster.\n\nDie Desktop-App ist die vollständigste Version; Excel im Web deckt gängige Aufgaben im Browser ab, und Copilot in Excel schlägt Formeln vor und analysiert Tabellen."),
    T("powerpoint", "product", "Microsoft PowerPoint", ["PowerPoint"],
      "Presentation software of Microsoft 365 for slides, templates, animations and live presenting, with co-authoring and Copilot-generated decks.",
      "Präsentationssoftware von Microsoft 365 für Folien, Vorlagen, Animationen und Live-Vorträge, mit gemeinsamem Bearbeiten und von Copilot erzeugten Präsentationen.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365-apps", "related_to": ["copilot", "powerpoint-online", "teams"]}, docs="https://support.microsoft.com/powerpoint", wiki="https://en.wikipedia.org/wiki/Microsoft_PowerPoint", web="https://www.microsoft.com/microsoft-365/powerpoint", released="1990-05-22", license="included"),
    T("outlook", "product", "Microsoft Outlook", ["Outlook", "new Outlook", "Outlook für Windows"],
      "Email, calendar, contacts and tasks client of Microsoft 365 that connects to Exchange Online and other mail accounts.",
      "E-Mail-, Kalender-, Kontakte- und Aufgaben-Client von Microsoft 365, der sich mit Exchange Online und weiteren Postfächern verbindet.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365-apps", "related_to": ["exchange-online", "teams", "copilot", "outlook-web"]}, docs="https://support.microsoft.com/outlook", wiki="https://en.wikipedia.org/wiki/Microsoft_Outlook", web="https://www.microsoft.com/microsoft-365/outlook/email-and-calendar-software-microsoft-outlook", released="1997-01-16", license="included"),
    T("outlook-web", "product", "Outlook on the web", ["OWA", "Outlook Web App", "outlook.office.com"],
      "Browser version of Outlook for mail, calendar and contacts, hosted by Exchange Online.",
      "Browser-Version von Outlook für E-Mail, Kalender und Kontakte, betrieben von Exchange Online.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "office-on-the-web", "related_to": ["outlook", "exchange-online"]}, docs="https://support.microsoft.com/outlook", license="included"),
    T("onenote", "product", "Microsoft OneNote", ["OneNote"],
      "Digital notebook for typed notes, ink, images and web clippings, organised in notebooks, sections and pages and synced through OneDrive.",
      "Digitales Notizbuch für getippte Notizen, Handschrift, Bilder und Webausschnitte, gegliedert in Notizbücher, Abschnitte und Seiten und über OneDrive synchronisiert.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365-apps", "related_to": ["onedrive", "teams"]}, docs="https://support.microsoft.com/onenote", wiki="https://en.wikipedia.org/wiki/Microsoft_OneNote", web="https://www.microsoft.com/microsoft-365/onenote/digital-note-taking-app", released="2003-11-19", license="included"),
    T("access", "product", "Microsoft Access", ["Access"],
      "Desktop database application for building small relational databases with tables, queries, forms and reports.",
      "Desktop-Datenbankanwendung zum Aufbau kleiner relationaler Datenbanken mit Tabellen, Abfragen, Formularen und Berichten.",
      {"instance_of": [MT, "business-application"], "part_of": "microsoft-365-apps", "related_to": ["dataverse", "power-apps"]}, docs="https://support.microsoft.com/access", wiki="https://en.wikipedia.org/wiki/Microsoft_Access", web="https://www.microsoft.com/microsoft-365/access", released="1992-11-13", license="included"),
    T("publisher", "product", "Microsoft Publisher", ["Publisher"],
      "Desktop publishing application for flyers, newsletters and brochures; Microsoft ended support in October 2026.",
      "Desktop-Publishing-Anwendung für Flyer, Newsletter und Broschüren; Microsoft hat den Support im Oktober 2026 beendet.",
      {"instance_of": [MT], "part_of": "microsoft-365-apps", "related_to": ["word", "powerpoint"]}, docs="https://support.microsoft.com/publisher", wiki="https://en.wikipedia.org/wiki/Microsoft_Publisher", outdated=True, released="1991-05"),
    T("visio", "product", "Microsoft Visio", ["Visio"],
      "Diagramming application for flowcharts, org charts, network and process diagrams, available as desktop app and Visio for the web.",
      "Diagramm-Anwendung für Flussdiagramme, Organigramme, Netzwerk- und Prozessdiagramme, als Desktop-App und Visio im Web verfügbar.",
      {"instance_of": [MT], "related_to": ["teams", "sharepoint", "microsoft-365"]}, docs="https://support.microsoft.com/visio", wiki="https://en.wikipedia.org/wiki/Microsoft_Visio", web="https://www.microsoft.com/microsoft-365/visio/flowchart-software", license="paid"),
    T("project", "product", "Microsoft Project", ["MS Project", "Project"],
      "Project management software for schedules, resources and Gantt charts; cloud scheduling continues in Planner premium.",
      "Projektmanagement-Software für Terminpläne, Ressourcen und Gantt-Diagramme; die Cloud-Planung läuft im Planner Premium weiter.",
      {"instance_of": [MT], "related_to": ["microsoft-planner", "teams"]}, docs="https://support.microsoft.com/project", wiki="https://en.wikipedia.org/wiki/Microsoft_Project", web="https://www.microsoft.com/microsoft-365/project/project-management-software", license="paid", released="1984"),
    T("office-on-the-web", "product", "Office on the web", ["Office Online", "Microsoft 365 for the web", "office.com"],
      "Browser versions of Word, Excel, PowerPoint, OneNote and Outlook that run without installation and support real-time co-authoring.",
      "Browser-Versionen von Word, Excel, PowerPoint, OneNote und Outlook, die ohne Installation laufen und gleichzeitiges Bearbeiten in Echtzeit unterstützen.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["onedrive", "sharepoint"]}, docs="https://support.microsoft.com/office", web="https://www.office.com", license="included"),
    T("word-online", "product", "Word for the web", ["Word Online", "Word im Web"],
      "Browser version of Word for writing and co-authoring documents without installing the desktop app.",
      "Browser-Version von Word zum Schreiben und gemeinsamen Bearbeiten von Dokumenten ohne Installation der Desktop-App.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "office-on-the-web", "related_to": ["word"]}, docs="https://support.microsoft.com/word", license="included"),
    T("excel-online", "product", "Excel for the web", ["Excel Online", "Excel im Web"],
      "Browser version of Excel for viewing, editing and co-authoring workbooks; it supports common formulas, tables and charts but fewer advanced features than the desktop app.",
      "Browser-Version von Excel zum Ansehen, Bearbeiten und gemeinsamen Bearbeiten von Arbeitsmappen; sie unterstützt gängige Formeln, Tabellen und Diagramme, aber weniger Spezialfunktionen als die Desktop-App.",
      {"instance_of": [MT, "analytics-tool"], "part_of": "office-on-the-web", "related_to": ["excel", "onedrive", "sharepoint", "teams"]}, docs="https://support.microsoft.com/excel", license="included",
      long_en="Excel for the web opens workbooks stored in OneDrive or SharePoint directly in the browser. Several people can edit the same sheet at once, and changes appear live. It is the version embedded in Teams channels and in SharePoint document libraries.\n\nSome features, for example advanced Power Query steps, VBA macros and certain data-model functions, still require the desktop app.",
      long_de="Excel im Web öffnet Arbeitsmappen aus OneDrive oder SharePoint direkt im Browser. Mehrere Personen bearbeiten dasselbe Blatt gleichzeitig, Änderungen erscheinen live. Diese Version steckt auch in Teams-Kanälen und SharePoint-Dokumentbibliotheken.\n\nEinige Funktionen, etwa erweiterte Power-Query-Schritte, VBA-Makros und bestimmte Datenmodell-Funktionen, brauchen weiterhin die Desktop-App."),
    T("powerpoint-online", "product", "PowerPoint for the web", ["PowerPoint Online", "PowerPoint im Web"],
      "Browser version of PowerPoint for creating, presenting and co-authoring slide decks.",
      "Browser-Version von PowerPoint zum Erstellen, Präsentieren und gemeinsamen Bearbeiten von Folien.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "office-on-the-web", "related_to": ["powerpoint"]}, docs="https://support.microsoft.com/powerpoint", license="included"),

    # ---- Teams-Umfeld ----
    T("teams-phone", "product", "Teams Phone", ["Microsoft Teams Phone", "Teams Calling"],
      "Cloud telephony in Microsoft Teams with calling plans, direct routing and operator connect for business phone numbers.",
      "Cloud-Telefonie in Microsoft Teams mit Calling Plans, Direct Routing und Operator Connect für geschäftliche Rufnummern.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "teams"}, docs="https://learn.microsoft.com/microsoftteams/what-is-phone-system-in-office-365", license="addon"),
    T("teams-premium", "product", "Teams Premium", ["Microsoft Teams Premium"],
      "Add-on licence for Teams with advanced meeting protection, branded meetings, AI-generated recaps and webinar features.",
      "Zusatzlizenz für Teams mit erweitertem Besprechungsschutz, Besprechungen im eigenen Design, KI-gestützten Zusammenfassungen und Webinar-Funktionen.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "teams", "related_to": ["copilot"]}, docs="https://learn.microsoft.com/microsoftteams/teams-add-on-licensing/licensing-enhance-teams", license="addon", released="2023-02"),
    T("teams-rooms", "product", "Microsoft Teams Rooms", ["MTR", "Teams Rooms"],
      "Meeting-room systems with cameras, microphones and displays that join Teams meetings with a single touch.",
      "Besprechungsraum-Systeme mit Kameras, Mikrofonen und Displays, die mit einem Fingertipp an Teams-Besprechungen teilnehmen.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "teams"}, docs="https://learn.microsoft.com/microsoftteams/rooms/rooms-intro", license="paid"),
    T("microsoft-planner", "product", "Microsoft Planner", ["Planner", "Tasks by Planner and To Do"],
      "Task and project planning tool with boards, buckets, schedules and goals, integrated in Teams as the Planner app.",
      "Werkzeug für Aufgaben- und Projektplanung mit Boards, Buckets, Zeitplänen und Zielen, in Teams als Planner-App eingebunden.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["teams", "microsoft-to-do", "project"]}, docs="https://support.microsoft.com/planner", wiki="https://en.wikipedia.org/wiki/Microsoft_Planner", web="https://www.microsoft.com/microsoft-365/planner/microsoft-planner", license="included"),
    T("microsoft-to-do", "product", "Microsoft To Do", ["To Do", "Wunderlist successor"],
      "Personal task list app with My Day, lists and reminders, synced with Outlook tasks and Planner.",
      "App für persönliche Aufgabenlisten mit „Mein Tag“, Listen und Erinnerungen, synchronisiert mit Outlook-Aufgaben und Planner.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["outlook", "microsoft-planner"]}, docs="https://support.microsoft.com/microsoft-to-do", wiki="https://en.wikipedia.org/wiki/Microsoft_To_Do", license="included"),
    T("microsoft-forms", "product", "Microsoft Forms", ["Forms"],
      "Tool for creating surveys, quizzes and polls whose responses flow into Excel, Power Automate and Teams.",
      "Werkzeug für Umfragen, Quizze und Abstimmungen, deren Antworten in Excel, Power Automate und Teams fließen.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["excel", "power-automate", "teams"]}, docs="https://support.microsoft.com/forms", wiki="https://en.wikipedia.org/wiki/Microsoft_Forms", license="included"),
    T("microsoft-lists", "product", "Microsoft Lists", ["Lists", "SharePoint Lists"],
      "Tool for tracking information and work in customisable lists with views, rules and formatting, stored in SharePoint.",
      "Werkzeug zum Nachverfolgen von Informationen und Arbeit in anpassbaren Listen mit Ansichten, Regeln und Formatierung, gespeichert in SharePoint.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "sharepoint", "related_to": ["power-apps", "power-automate", "teams"]}, docs="https://support.microsoft.com/lists", license="included", released="2020-07"),
    T("microsoft-loop", "product", "Microsoft Loop", ["Loop", "Loop components"],
      "Collaborative workspace with portable Loop components, pages and workspaces that stay in sync across Teams, Outlook and Word.",
      "Kollaborativer Arbeitsbereich mit portablen Loop-Komponenten, Seiten und Workspaces, die in Teams, Outlook und Word synchron bleiben.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["teams", "outlook", "copilot"]}, docs="https://support.microsoft.com/loop", license="included", released="2023-11"),
    T("microsoft-whiteboard", "product", "Microsoft Whiteboard", ["Whiteboard"],
      "Digital canvas for sketching, sticky notes and brainstorming, used in Teams meetings and on devices.",
      "Digitale Zeichenfläche für Skizzen, Haftnotizen und Brainstorming, genutzt in Teams-Besprechungen und auf Geräten.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["teams"]}, docs="https://support.microsoft.com/whiteboard", wiki="https://en.wikipedia.org/wiki/Microsoft_Whiteboard", license="included"),
    T("microsoft-bookings", "product", "Microsoft Bookings", ["Bookings"],
      "Appointment scheduling tool with a public booking page that checks Outlook calendars and sends confirmations.",
      "Terminbuchungs-Werkzeug mit öffentlicher Buchungsseite, das Outlook-Kalender prüft und Bestätigungen verschickt.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["outlook", "teams"]}, docs="https://support.microsoft.com/bookings", license="included"),
    T("microsoft-stream", "product", "Microsoft Stream", ["Stream on SharePoint", "Stream"],
      "Video service of Microsoft 365 where recordings and clips are stored in OneDrive and SharePoint and played back in Teams.",
      "Video-Dienst von Microsoft 365, bei dem Aufzeichnungen und Clips in OneDrive und SharePoint liegen und in Teams abgespielt werden.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "microsoft-365", "related_to": ["teams", "sharepoint", "onedrive"]}, docs="https://learn.microsoft.com/stream/", license="included"),
    T("microsoft-clipchamp", "product", "Microsoft Clipchamp", ["Clipchamp"],
      "Browser-based video editor with templates, text-to-speech and stock media, included in Microsoft 365.",
      "Browserbasierter Video-Editor mit Vorlagen, Text-to-Speech und Stock-Medien, in Microsoft 365 enthalten.",
      {"instance_of": [MT], "part_of": "microsoft-365", "related_to": ["microsoft-stream", "powerpoint"]}, docs="https://support.microsoft.com/clipchamp", license="included"),

    # ---- SharePoint / OneDrive / Exchange / Copilot-Umfeld ----
    T("sharepoint-premium", "product", "SharePoint Premium", ["Microsoft Syntex", "SharePoint Advanced Management"],
      "Add-on capabilities for SharePoint such as document processing, content AI, eSignature and advanced management, formerly marketed as Microsoft Syntex.",
      "Zusatzfunktionen für SharePoint wie Dokumentenverarbeitung, Inhalts-KI, E-Signatur und erweitertes Management, früher als Microsoft Syntex vermarktet.",
      {"instance_of": [MT, "collaboration-tool"], "part_of": "sharepoint", "related_to": ["ai-builder", "purview"]}, docs="https://learn.microsoft.com/sharepoint/sharepoint-premium", license="addon"),
    T("sharepoint-embedded", "product", "SharePoint Embedded", ["SPE"],
      "API-first content platform that lets developers store and manage documents for their own apps in Microsoft 365 with its security and compliance.",
      "API-basierte Inhaltsplattform, mit der Entwickler Dokumente für eigene Apps in Microsoft 365 speichern und verwalten, inklusive Sicherheit und Compliance.",
      {"instance_of": [MT, "developer-tool"], "part_of": "sharepoint", "related_to": ["graph", "purview"]}, docs="https://learn.microsoft.com/sharepoint/dev/embedded/overview", license="paid"),
    T("copilot-chat", "product", "Microsoft 365 Copilot Chat", ["Copilot Chat", "Microsoft Copilot Chat"],
      "Secure, web-grounded AI chat for Entra ID users that is included at no extra cost and can run agents; the paid Microsoft 365 Copilot adds work-data grounding.",
      "Sicherer, web-basierter KI-Chat für Entra-ID-Nutzer, ohne Zusatzkosten enthalten und mit Agenten nutzbar; das kostenpflichtige Microsoft 365 Copilot ergänzt den Zugriff auf Arbeitsdaten.",
      {"instance_of": [MT, "ai-assistant"], "part_of": "copilot", "related_to": ["copilot-studio", "ai-agent", "entra-id"]}, docs="https://learn.microsoft.com/copilot/overview", license="included", released="2025-01"),
]

added = []
for e in NEW:
    if e["id"] in M:
        old = M[e["id"]]
        for k, v in e.items():
            if k in ("rel",):
                have = {tuple(r) for r in old.get("rel", [])}
                old["rel"] = old.get("rel", []) + [r for r in v if tuple(r) not in have]
            elif not old.get(k):
                old[k] = v
    else:
        D.append(e); M[e["id"]] = e; added.append(e["id"])

# ---------- 4. Bestehende Tools anreichern ----------
ENR = {
    "power-bi": dict(web="https://powerbi.microsoft.com", docs="https://learn.microsoft.com/power-bi/", wikipedia="https://en.wikipedia.org/wiki/Power_BI", aliases_add=["PBI"],
                     rel_add=[["related_to", "power-bi-desktop"], ["related_to", "power-bi-service"], ["related_to", "power-query"], ["related_to", "dax"], ["related_to", "excel"], ["related_to", "copilot"]],
                     long=("Power BI turns data from many sources into interactive reports and dashboards. Authors build models and reports in Power BI Desktop, publish them to the Power BI service and share them through workspaces, apps and Teams. DAX defines calculations, Power Query prepares the data, and since 2023 Power BI is part of Microsoft Fabric.",
                           "Power BI macht aus Daten vieler Quellen interaktive Berichte und Dashboards. Ersteller bauen Modelle und Berichte in Power BI Desktop, veröffentlichen sie im Power-BI-Dienst und teilen sie über Arbeitsbereiche, Apps und Teams. DAX definiert Berechnungen, Power Query bereitet die Daten auf, und seit 2023 ist Power BI Teil von Microsoft Fabric.")),
    "power-automate": dict(web="https://www.microsoft.com/power-platform/products/power-automate", docs="https://learn.microsoft.com/power-automate/", wikipedia="https://en.wikipedia.org/wiki/Power_Automate", released="2016-11", aliases_add=["Microsoft Flow", "Flow"],
                           rel_add=[["related_to", "power-automate-desktop"], ["related_to", "connector"], ["related_to", "ai-builder"], ["related_to", "teams"], ["related_to", "sharepoint"], ["related_to", "microsoft-forms"], ["related_to", "outlook"]],
                           long=("Power Automate builds workflows that connect apps and services. Cloud flows react to triggers such as a new email or SharePoint item, desktop flows automate Windows applications through RPA, and process mining shows where workflows can be improved. It was called Microsoft Flow until 2019.",
                                 "Power Automate baut Workflows, die Apps und Dienste verbinden. Cloud-Flows reagieren auf Auslöser wie eine neue E-Mail oder ein neues SharePoint-Element, Desktop-Flows automatisieren Windows-Anwendungen per RPA, und Process Mining zeigt Verbesserungspotenzial. Bis 2019 hieß der Dienst Microsoft Flow.")),
    "power-apps": dict(web="https://www.microsoft.com/power-platform/products/power-apps", docs="https://learn.microsoft.com/power-apps/", wikipedia="https://en.wikipedia.org/wiki/Power_Apps", released="2016-11",
                       rel_add=[["related_to", "canvas-app"], ["related_to", "model-driven-app"], ["related_to", "power-fx"], ["related_to", "connector"], ["related_to", "ai-builder"], ["related_to", "teams"], ["related_to", "sharepoint"], ["related_to", "microsoft-lists"]],
                       long=("Power Apps lets people build business apps with little or no code. Canvas apps give full control over layout, model-driven apps are generated from the Dataverse data model, and Power Fx is the formula language that ties them together. Apps can be embedded in Teams and SharePoint.",
                             "Mit Power Apps entstehen Geschäfts-Apps mit wenig oder ganz ohne Code. Canvas-Apps geben volle Kontrolle über das Layout, modellgesteuerte Apps werden aus dem Dataverse-Datenmodell erzeugt, und Power Fx ist die verbindende Formelsprache. Apps lassen sich in Teams und SharePoint einbetten.")),
    "power-pages": dict(web="https://www.microsoft.com/power-platform/products/power-pages", docs="https://learn.microsoft.com/power-pages/", released="2022-02", rel_add=[["related_to", "power-fx"]]),
    "power-platform": dict(web="https://www.microsoft.com/power-platform", docs="https://learn.microsoft.com/power-platform/", wikipedia="https://en.wikipedia.org/wiki/Microsoft_Power_Platform", license="paid",
                           rel_add=[["related_to", "power-fx"], ["related_to", "connector"], ["related_to", "ai-builder"], ["related_to", "power-platform-admin-center"], ["related_to", "power-platform-cli"], ["related_to", "dlp"], ["related_to", "governance"]],
                           long=("The Power Platform is Microsoft's low-code family: Power Apps for apps, Power Automate for workflows, Power BI for analytics, Power Pages for websites and Copilot Studio for agents, all on Dataverse and a shared connector layer. The Power Platform admin center manages environments and data policies.",
                                 "Die Power Platform ist Microsofts Low-Code-Familie: Power Apps für Apps, Power Automate für Workflows, Power BI für Analysen, Power Pages für Webseiten und Copilot Studio für Agenten, alles auf Dataverse und einer gemeinsamen Konnektor-Ebene. Das Power Platform Admin Center verwaltet Umgebungen und Datenrichtlinien.")),
    "dataverse": dict(docs="https://learn.microsoft.com/power-apps/maker/data-platform/", released="2016", rel_add=[["related_to", "model-driven-app"], ["related_to", "power-fx"], ["related_to", "ai-builder"]]),
    "copilot-studio": dict(web="https://www.microsoft.com/microsoft-copilot/microsoft-copilot-studio", docs="https://learn.microsoft.com/microsoft-copilot-studio/", aliases_add=["Power Virtual Agents"], rel_add=[["related_to", "power-fx"], ["related_to", "connector"], ["related_to", "copilot-chat"], ["related_to", "power-virtual-agents"]]),
    "copilot": dict(web="https://www.microsoft.com/microsoft-365/copilot", rel_add=[["related_to", "word"], ["related_to", "excel"], ["related_to", "powerpoint"], ["related_to", "outlook"], ["related_to", "onenote"], ["related_to", "copilot-chat"], ["related_to", "microsoft-loop"]]),
    "teams": dict(web="https://www.microsoft.com/microsoft-teams/group-chat-software", docs="https://learn.microsoft.com/microsoftteams/", wikipedia="https://en.wikipedia.org/wiki/Microsoft_Teams", aliases_add=["Microsoft Teams"],
                  rel_add=[["related_to", "teams-phone"], ["related_to", "teams-premium"], ["related_to", "teams-rooms"], ["related_to", "microsoft-planner"], ["related_to", "microsoft-whiteboard"], ["related_to", "microsoft-loop"], ["related_to", "microsoft-stream"], ["related_to", "sharepoint"], ["related_to", "onedrive"], ["related_to", "power-apps"], ["related_to", "outlook"]],
                  long=("Teams combines chat, channels, meetings, calling and file collaboration in one app. Files shared in channels live in SharePoint, private chats store files in OneDrive, and apps from the Power Platform, Planner, Forms and Loop can be added to channels and meetings.",
                        "Teams vereint Chat, Kanäle, Besprechungen, Telefonie und Zusammenarbeit an Dateien in einer App. Dateien in Kanälen liegen in SharePoint, Dateien aus privaten Chats in OneDrive, und Apps aus Power Platform, Planner, Forms und Loop lassen sich in Kanäle und Besprechungen einbinden.")),
    "sharepoint": dict(web="https://www.microsoft.com/microsoft-365/sharepoint/collaboration", docs="https://learn.microsoft.com/sharepoint/", wikipedia="https://en.wikipedia.org/wiki/SharePoint",
                       rel_add=[["related_to", "microsoft-lists"], ["related_to", "sharepoint-premium"], ["related_to", "sharepoint-embedded"], ["related_to", "teams"], ["related_to", "power-apps"], ["related_to", "power-automate"], ["related_to", "excel-online"], ["related_to", "microsoft-stream"], ["related_to", "purview"]],
                       long=("SharePoint is the content and intranet platform of Microsoft 365. Team sites, communication sites and document libraries hold the files behind Teams, with permissions, versioning, metadata and retention labels. Lists, Power Apps and Power Automate extend libraries into small business solutions.",
                             "SharePoint ist die Inhalts- und Intranet-Plattform von Microsoft 365. Teamwebsites, Kommunikationswebsites und Dokumentbibliotheken halten die Dateien hinter Teams, mit Berechtigungen, Versionierung, Metadaten und Aufbewahrungsbezeichnungen. Listen, Power Apps und Power Automate erweitern Bibliotheken zu kleinen Geschäftslösungen.")),
    "onedrive": dict(web="https://www.microsoft.com/microsoft-365/onedrive/online-cloud-storage", docs="https://learn.microsoft.com/onedrive/", wikipedia="https://en.wikipedia.org/wiki/OneDrive", released="2007-08", rel_add=[["related_to", "word"], ["related_to", "excel"], ["related_to", "powerpoint"], ["related_to", "onenote"], ["related_to", "teams"], ["related_to", "sharepoint"]]),
    "exchange-online": dict(docs="https://learn.microsoft.com/exchange/", web="https://www.microsoft.com/microsoft-365/exchange/email", wikipedia="https://en.wikipedia.org/wiki/Microsoft_Exchange_Server", rel_add=[["related_to", "outlook"], ["related_to", "outlook-web"], ["related_to", "microsoft-bookings"]]),
    "microsoft-365": dict(docs="https://learn.microsoft.com/microsoft-365/", wikipedia="https://en.wikipedia.org/wiki/Microsoft_365", released="2011-06",
                          rel_add=[["related_to", "microsoft-365-apps"], ["related_to", "office-on-the-web"], ["related_to", "word"], ["related_to", "excel"], ["related_to", "powerpoint"], ["related_to", "outlook"], ["related_to", "onenote"]]),
}
for k, v in ENR.items():
    e = M.get(k)
    if not e:
        print("fehlt", k); continue
    for f in ("web", "docs", "wikipedia", "released", "license"):
        if v.get(f) and not e.get(f):
            e[f] = v[f]
    if v.get("aliases_add"):
        e["aliases"] = list(dict.fromkeys(e.get("aliases", []) + v["aliases_add"]))[:10]
    have = {tuple(r) for r in e.get("rel", [])}
    e["rel"] = e.get("rel", []) + [r for r in v.get("rel_add", []) if tuple(r) not in have and r[1] in M and r[1] != k]
    if v.get("long") and not e.get("long"):
        e["long"] = {"en": v["long"][0], "de": v["long"][1]}

# Zertifikate mit den Werkzeugen verknuepfen
CERT = {"pl-300": ["power-query", "dax", "power-bi-desktop", "power-bi-service"], "pl-200": ["power-apps", "power-automate", "dataverse", "ai-builder"], "pl-400": ["power-apps", "power-automate", "dataverse", "power-fx", "connector"],
        "pl-500": ["power-automate", "power-automate-desktop"], "pl-600": ["power-apps", "power-automate", "power-bi", "dataverse"], "pl-900": ["power-apps", "power-automate", "power-bi", "power-pages", "copilot-studio"],
        "ms-700": ["teams", "teams-phone", "teams-rooms"], "ms-102": ["exchange-online", "sharepoint", "onedrive", "microsoft-365-admin-center"], "ms-900": ["teams", "sharepoint", "exchange-online", "word", "excel", "outlook"],
        "dp-600": ["power-bi", "dax", "power-query"], "ab-620": ["copilot-studio"], "ab-900": ["copilot", "copilot-studio", "copilot-chat"]}
for c, lst in CERT.items():
    e = M.get(c)
    if e:
        have = {tuple(r) for r in e["rel"]}
        e["rel"] += [["covers", x] for x in lst if x in M and ("covers", x) not in have]

# Pruefung: Relationen zeigen auf existierende IDs, Kurzbeschreibung <= 300
ids = set(M)
bad = [(e["id"], r) for e in D for r in e.get("rel", []) if r[1] not in ids]
longd = [e["id"] for e in D if len(e["desc"]["en"]) > 300 or len(e["desc"]["de"]) > 300]
assert not bad and not longd, (bad, longd)
json.dump(D, open(P, "w"), ensure_ascii=False, indent=1)
print("neu:", len(added), "gesamt:", len(D))
