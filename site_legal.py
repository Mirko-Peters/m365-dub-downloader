"""Impressum und Datenschutz (de/en). Kontakt-E-Mail in CONTACT_EMAIL eintragen (Pflichtangabe im Impressum)."""
CONTACT_EMAIL = ""   # z. B. "kontakt@m365.fm" – leer = Zeile wird weggelassen
NAME, STREET, CITY = "Mirko Peters (M365.FM)", "Julius-Hölder-Str 60", "70597 Stuttgart"
AUTH_DE = "Der Landesbeauftragte für den Datenschutz und die Informationsfreiheit Baden-Württemberg"


def _mail(de=True):
    return f"<p>{'E-Mail' if de else 'Email'}: <a href=\"mailto:{CONTACT_EMAIL}\">{CONTACT_EMAIL}</a></p>" if CONTACT_EMAIL else ""


def impressum_de():
    return f"""<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2><p>{NAME}<br>{STREET}<br>{CITY}<br>Deutschland</p>
<h2>Kontakt</h2>{_mail() or '<p>Kontakt über <a href="https://www.m365.fm">m365.fm</a>.</p>'}
<h2>Verantwortlich für den Inhalt (§ 18 Abs. 2 MStV)</h2><p>Mirko Peters, Anschrift wie oben.</p>
<h2>Hinweis zu KI-Inhalten</h2><p>Die Audio-Folgen in anderen Sprachen sind KI-synchronisierte Fassungen (Dubbing) der englischen Originalvideos. Texte und Zusammenfassungen werden teilweise mit KI aus den Transkripten erstellt und können Fehler enthalten.</p>
<h2>Haftung für Links</h2><p>Diese Seite enthält Links zu externen Webseiten Dritter, auf deren Inhalte ich keinen Einfluss habe. Für diese fremden Inhalte übernehme ich keine Gewähr; verantwortlich ist stets der jeweilige Anbieter.</p>
<h2>Urheberrecht</h2><p>Die Inhalte dieser Seite unterliegen dem deutschen Urheberrecht. Microsoft, Microsoft 365, Copilot, Azure und weitere genannte Produktnamen sind Marken ihrer jeweiligen Inhaber; diese Seite steht in keiner offiziellen Verbindung zu Microsoft.</p>"""


def impressum_en():
    return f"""<h1>Legal notice</h1>
<h2>Provider (§ 5 DDG)</h2><p>{NAME}<br>{STREET}<br>{CITY}<br>Germany</p>
<h2>Contact</h2>{_mail(False) or '<p>Contact via <a href="https://www.m365.fm">m365.fm</a>.</p>'}
<h2>Responsible for content (§ 18 (2) MStV)</h2><p>Mirko Peters, address as above.</p>
<h2>AI-generated content</h2><p>Audio episodes in other languages are AI-dubbed versions of the English original videos. Texts and summaries are partly generated with AI from the transcripts and may contain errors.</p>
<h2>Liability for links</h2><p>This site links to external third-party websites whose content I do not control. The respective provider is always responsible for it.</p>
<h2>Copyright and trademarks</h2><p>Content on this site is subject to German copyright law. Microsoft, Microsoft 365, Copilot, Azure and other product names are trademarks of their respective owners; this site is not officially affiliated with Microsoft.</p>"""


def privacy_de():
    return f"""<h1>Datenschutzerklärung</h1>
<h2>Verantwortlicher</h2><p>{NAME}, {STREET}, {CITY}, Deutschland.</p>
<h2>Hosting (GitHub Pages) und DNS (Cloudflare)</h2><p>Diese Seite wird über GitHub Pages (GitHub Inc., USA) ausgeliefert, die Domain über Cloudflare aufgelöst. Beim Aufruf verarbeiten diese Dienste technisch notwendige Daten (u. a. IP-Adresse, Zeitpunkt, aufgerufene Seite) in Server-Logs. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (sicherer und effizienter Betrieb). Die Übermittlung in die USA erfolgt auf Basis des EU-US Data Privacy Framework bzw. von Standardvertragsklauseln.</p>
<h2>Schriften</h2><p>Schriften werden von diesem Server selbst ausgeliefert; es werden keine Daten an Google Fonts übertragen.</p>
<h2>Eingebettete YouTube-Videos</h2><p>Auf Folgenseiten sind Videos über den erweiterten Datenschutzmodus (youtube-nocookie.com) von YouTube (Google Ireland Limited / Google LLC) eingebunden. Beim Laden der Seite kann Ihre IP-Adresse an YouTube übertragen werden. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO. Näheres: <a href="https://policies.google.com/privacy">policies.google.com/privacy</a>.</p>
<h2>Microsoft Clarity (nur mit Einwilligung)</h2><p>Mit Ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 25 TDDDG) nutzen wir Microsoft Clarity zur Analyse der Nutzung (z. B. Klicks, Scrolltiefe, Seitenaufrufe). Dabei können Cookies gesetzt und Daten an Microsoft übertragen werden. Ohne Ihre Zustimmung wird Clarity nicht geladen. Sie können die Einwilligung jederzeit widerrufen, indem Sie die Website-Daten Ihres Browsers für diese Seite löschen; die Abfrage erscheint dann erneut. Mehr: <a href="https://privacy.microsoft.com/privacystatement">privacy.microsoft.com</a>.</p>
<h2>Externe Links und Teilen</h2><p>Links zu Spreaker, Spotify, Apple Podcasts, Amazon Music, Deezer, LinkedIn, X, Facebook, WhatsApp, Telegram, Reddit u. a. sind einfache Verweise. Erst beim Anklicken werden Daten an den jeweiligen Anbieter übertragen; es gelten dessen Datenschutzbestimmungen.</p>
<h2>Ihre Rechte</h2><p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch (Art. 15–21 DSGVO) sowie das Recht, eine erteilte Einwilligung jederzeit mit Wirkung für die Zukunft zu widerrufen. Außerdem können Sie sich bei einer Aufsichtsbehörde beschweren, z. B.: {AUTH_DE}.</p>
{_mail()}"""


def privacy_en():
    return f"""<h1>Privacy policy</h1>
<h2>Controller</h2><p>{NAME}, {STREET}, {CITY}, Germany.</p>
<h2>Hosting (GitHub Pages) and DNS (Cloudflare)</h2><p>This site is served via GitHub Pages (GitHub Inc., USA) and the domain is resolved through Cloudflare. When you visit, these services process technically necessary data (e.g. IP address, time, requested page) in server logs. Legal basis: Art. 6(1)(f) GDPR (secure and efficient operation). Transfers to the USA rely on the EU-US Data Privacy Framework or standard contractual clauses.</p>
<h2>Fonts</h2><p>Fonts are served from this server; no data is sent to Google Fonts.</p>
<h2>Embedded YouTube videos</h2><p>Episode pages embed videos using YouTube's privacy-enhanced mode (youtube-nocookie.com) from Google Ireland Limited / Google LLC. Your IP address may be transmitted to YouTube when the page loads. Legal basis: Art. 6(1)(f) GDPR. See <a href="https://policies.google.com/privacy">policies.google.com/privacy</a>.</p>
<h2>Microsoft Clarity (consent only)</h2><p>With your consent (Art. 6(1)(a) GDPR, § 25 TDDDG) we use Microsoft Clarity to analyse usage (e.g. clicks, scroll depth, page views). Cookies may be set and data transmitted to Microsoft. Without your consent Clarity is not loaded. You can withdraw consent at any time by clearing this site's data in your browser; the banner then reappears. More: <a href="https://privacy.microsoft.com/privacystatement">privacy.microsoft.com</a>.</p>
<h2>External links and sharing</h2><p>Links to Spreaker, Spotify, Apple Podcasts, Amazon Music, Deezer, LinkedIn, X, Facebook, WhatsApp, Telegram, Reddit and others are plain links. Data is only sent to the respective provider once you click; their privacy policies apply.</p>
<h2>Your rights</h2><p>You have the right of access, rectification, erasure, restriction, data portability and objection (Arts. 15–21 GDPR), and to withdraw consent at any time with effect for the future. You may also lodge a complaint with a supervisory authority, e.g. {AUTH_DE}.</p>
{_mail(False)}"""
