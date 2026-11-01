# Erkundung MVP-Verzeichnis (2026-11-01T13:20Z)

Seite: https://mvp.microsoft.com/en-US/search?target=Profile&program=MVP

robots.txt (Status 200):

```
# Robots.txt file for https://studentambassadors.microsoft.com/

User-agent: *
Allow: /
Allow: /*/search*
Allow: /*/events
Allow: /*/activities
Allow: /*/studentambassadors/*
Allow: /*/mvp/*
Allow: /*/rd/*
Allow: /*/studentambassadors/milestones
Allow: /*/studentambassadors/profile/*
Allow: /*/mvp/overview
Allow: /*/mvp/profile/*
Allow: /*/rd/profile/*
Allow: /*/mvp
Allow: /*/faq
Allow: /*/locale
Allow: /locale

Disallow: /*/apply
Disallow: /*/account
Disallow: /*/studentambassadors/nominate
Disallow: /onboard
Disallow: /*/onboard
Disallow: /*/studentambassadors/application/status
Disallow: /certificate
Disallow: /*/certificate
Disallow: /nominations
Disallow: /*/nominations
Disallow: /privacy
Disallow: /*/privacy
Disallow: /*/notfound
Disallow: /*/amplify/
Disallow: /*/amplify/career
Disallow: /*/amplify/action
Disallow: /*/amplify/comingsoon
Disallow: /*/Summit
Disallow: /Summit

Sitemap: https://mvp.microsoft.com/sitemap.xml
```

Profil-Links auf der ersten Seite: 0 · Muster: -

Nutzungsbedingungen / Datenschutz: https://aka.ms/YourCaliforniaPrivacyChoices, https://go.microsoft.com/fwlink/?LinkID=206977, https://go.microsoft.com/fwlink/?LinkId=521839

## Abrufe der Seite (XHR/fetch)

- `GET https://mvp.microsoft.com/Locales/translation.json` → 200 text/html
- `GET https://mvp.microsoft.com/Locales/Common.json` → 200 application/json
  - Antwort: `{"mvp-communities": {"FAQ_NEED_MORE_HELP": "str", "FAQ_CONTACT_THE_MSP_TEAM": "str", "_FAQ_CONTACT_THE_MSP_TEAM.comment": "str", "FAQ_CONTACT_THE_MVP_TEAM": "str", "_FAQ_CONTACT_THE_MVP_TEAM.comment": "str", "FAQ_CONTACT_THE_RD_TEAM": "str", "_FAQ_CONTACT_THE_RD_TEAM.comment": "str", "FAQ_CONTACT_THE_CL_TEAM": "str", "_FAQ_CONTACT_THE_CL_TEAM.comment": "str", "FAQ_BANNER_TITLE": "str", "ABOUT_DESCRIPTION_TEXT": "str", "FAQ_META_KEYWORDS": "str", "FAQ_META_DESCRIPTION": "str", "FAQ_META_TITLE": "str", "COMMUNITY_QUESTIONS": {"list": 2, "item": "str"}, "COMMUNITY_ANSWERS": {"list": 2, "item": {"list": {"list": 3, "item": "…"}}}}, "title": {"HOME": "str", "SEARCH": "str", "FAQ": "str", "NOMINATE": "str", "APPLY": "str", "APPLICATION_STATUS": "str", "ONBOARD": "str", "ACCOUNT": "str", "ABOUT": "str"}, "mlsa_title": {"HOME": "str", "SEARCH": "str", "FAQ": "str", "NOMINATE": "str", "APPLY": "s`
- `GET https://mvp.microsoft.com/Locales/Footer.json` → 200 application/json
  - Antwort: `{"ABOUT_OUR_ADS": "str", "AZURE_FOR_STUDENTS": "str", "CAREERS": "str", "CODE_OF_CONDUCT": "str", "CONTACT_US": "str", "DOCS": "str", "FACEBOOK": "str", "GITHUB": "str", "IMAGINE_CUP": "str", "INSTAGRAM": "str", "INTERNSHIP": "str", "LEARN": "str", "LINKEDIN": "str", "MANAGE_COOKIES": "str", "MVP_BLOG": "str", "PRIVACY_AND_COOKIES": "str", "REACTORS": "str", "RSS": "str", "FOUNDERS_HUB": "str", "STARTUPS": "str", "TERMS_OF_USE": "str", "TRADEMARKS": "str", "TWITTER": "str", "YOUTUBE": "str", "CALIFORNIA_PRIVACY_CHOICES_DESCRIPTION": "str"}`
- `GET https://mavenapi-prod.microsoft.com/api/FeatureManager` → 200 application/json; charset=utf-8
  - Antwort: `{"featureFlags": {" Swag_Kit_Gold_Disabled": "bool", "A4Student": "bool", "Allow_Mvp_Rd_Nominate_SA": "bool", "Amplify": "bool", "AwardKit": "bool", "AwardKit_V2": "bool", "BenefitManagement": "bool", "Benefits_clipchamp-premium": "bool", "Benefits_dynamics-365-contact-center": "bool", "Benefits_github-certification-exam-voucher": "bool", "Benefits_linkedin": "bool", "Benefits_project-planner": "bool", "Benefits_w365": "bool", "CommunityLeader": "bool", "Credly_MSA_Disabled": "bool", "Credly_MVP_Banner": "bool", "Credly_MVP_Disabled": "bool", "Credly_V2": "bool", "Event_Search_Map": "bool", "First_Party_Microsoft_Event": "bool", "M365Copilot_Benefit_Disabled": "bool", "Maintenance": "bool", "MLSA": "bool", "MVP": "bool", "Mvp_Certificate_Download_Disabled": "bool", "My_Activity_View_Controls": "bool", "My_Event_View_Controls": "bool", "Nomination": "bool", "Nomination_MVP": "bool", "Nomi`
- `GET https://mvp.microsoft.com/Locales/Search.json` → 200 application/json
  - Antwort: `{"STUDENT_META_TITLE": "str", "STUDENT_META_DESCRIPTION": "str", "META_KEYWORDS": "str", "CL_META_TITLE": "str", "CL_META_DESCRIPTION": "str", "TITLE_TEXT_PROFILE": "str", "TITLE_TEXT_PROFILE_MLSA": "str", "TITLE_TEXT_EVENT": "str", "TITLE_TEXT_SITE": "str", "TITLE_TEXT_CONTRIBUTIONS": "str", "SEARCH_BOX_PLACEHOLDER_PROFILE": "str", "SEARCH_BOX_PLACEHOLDER_PROFILE_MLSA": "str", "SEARCH_BOX_PLACEHOLDER_EVENT": "str", "SEARCH_BOX_PLACEHOLDER_SITE": "str", "SEARCH_BOX_PLACEHOLDER_CONTRIBUTIONS": "str", "NO_RESULTS_FOUND_MESSAGE": "str", "RESULTS_LOADING_MESSAGE": "str", "SEARCH_LOAD_ERROR_MESSAGE": "str", "SEARCH_BANNER_TITLE_TEXT": "str", "SEARCH_BANNER_IMAGE_ALT_TEXT": "str", "SEARCH_BANNER_SUB_TITLE_TEXT": "str", "SEARCH_BANNER_SUB_TITLE_TEXT_MLSA": "str", "Profile": "str", "Event": "str", "Website": "str", "FILTER": "str", "SEARCH_RESULTS_FOUND": "str", "SEARCH_RESULT_FOUND": "str", "ON`
- `GET https://mvp.microsoft.com/Locales/Events.json` → 200 application/json
  - Antwort: `{"STUDENT_META_TITLE": "str", "STUDENT_META_DESCRIPTION": "str", "STUDENT_META_KEYWORDS": "str", "MVP_META_TITLE": "str", "MVP_META_DESCRIPTION": "str", "MVP_META_KEYWORDS": "str", "RD_META_TITLE": "str", "RD_META_DESCRIPTION": "str", "RD_META_KEYWORDS": "str", "CL_META_TITLE": "str", "CL_META_DESCRIPTION": "str", "CL_META_KEYWORDS": "str", "EVENT_BANNER_ALT_TEXT": "str", "EVENTS_HERO_TITLE": "str", "EVENTS_HERO_SUBTEXT": "str", "MORE_INFO": "str", "MORE_INFO_ARIA_LABEL": "str", "MORE_INFO_ARIA_DESCRIPTION": "str", "EVENT_FORMAT_IN_PERSON": "str", "EVENT_FORMAT_HYBRID": "str", "EVENT_FORMAT_ONLINE": "str", "ABOUT": "str", "DETAILS": "str", "PROGRAM": "str", "FORMAT": "str", "ORGANIZER": "str", "EVENT_TYPE": "str", "ADDRESS": "str", "COLLAPSE_TEXT": "str", "EXPAND_TEXT": "str", "TECHNOLOGY_AREA": "str", "ADDITIONAL_TECHNOLOGY_AREAS": "str", "TECHNICAL_EXPERTISE": "str", "TARGET_AUDIENCE":`
- `GET https://mvp.microsoft.com/Locales/TimeZone.json` → 200 application/json
  - Antwort: `{"DATELINE_STANDARD_TIME": "str", "UTC_M11": "str", "ALEUTIAN_STANDARD_TIME": "str", "HAWAIIAN_STANDARD_TIME": "str", "MARQUESAS_STANDARD_TIME": "str", "ALASKAN_STANDARD_TIME": "str", "UTC_M09": "str", "YUKON_STANDARD_TIME": "str", "PACIFIC_STANDARD_TIME_MEXICO": "str", "UTC_M08": "str", "PACIFIC_STANDARD_TIME": "str", "US_MOUNTAIN_STANDARD_TIME": "str", "MOUNTAIN_STANDARD_TIME_MEXICO": "str", "MOUNTAIN_STANDARD_TIME": "str", "CENTRAL_AMERICA_STANDARD_TIME": "str", "CENTRAL_STANDARD_TIME": "str", "EASTER_ISLAND_STANDARD_TIME": "str", "CENTRAL_STANDARD_TIME_MEXICO": "str", "CANADA_CENTRAL_STANDARD_TIME": "str", "SA_PACIFIC_STANDARD_TIME": "str", "EASTERN_STANDARD_TIME_MEXICO": "str", "EASTERN_STANDARD_TIME": "str", "HAITI_STANDARD_TIME": "str", "CUBA_STANDARD_TIME": "str", "US_EASTERN_STANDARD_TIME": "str", "TURKS_AND_CAICOS_STANDARD_TIME": "str", "PARAGUAY_STANDARD_TIME": "str", "ATLANTI`
- `GET https://mvp.microsoft.com/Locales/CountryOrRegion.json` → 200 application/json
  - Antwort: `{"AFGHANISTAN": "str", "ÅLAND_ISLANDS": "str", "ALBANIA": "str", "ALGERIA": "str", "AMERICAN_SAMOA": "str", "ANDORRA": "str", "ANGOLA": "str", "ANGUILLA": "str", "ANTARCTICA": "str", "ANTIGUA_AND_BARBUDA": "str", "ARGENTINA": "str", "ARMENIA": "str", "ARUBA": "str", "AUSTRALIA": "str", "AUSTRIA": "str", "AZERBAIJAN": "str", "BAHAMAS": "str", "BAHRAIN": "str", "BANGLADESH": "str", "BARBADOS": "str", "BELARUS": "str", "BELGIUM": "str", "BELIZE": "str", "BENIN": "str", "BERMUDA": "str", "BHUTAN": "str", "BOLIVIA": "str", "BONAIRE": "str", "BOSNIA_AND_HERZEGOVINA": "str", "BOTSWANA": "str", "BOUVET_ISLAND": "str", "BRAZIL": "str", "BRITISH_INDIAN_OCEAN_TERRITORY": "str", "BRITISH_VIRGIN_ISLANDS": "str", "BRUNEI": "str", "BULGARIA": "str", "BURKINA_FASO": "str", "BURUNDI": "str", "CABO_VERDE": "str", "CAMBODIA": "str"}`
- `GET https://mvp.microsoft.com/Locales/TargetAudiences.json` → 200 application/json
  - Antwort: `{"TARGETAUDIENCE_DEVELOPER": "str", "TARGETAUDIENCE_IT_PRO": "str", "TARGETAUDIENCE_BUSINESS_DECISION_MAKER": "str", "TARGETAUDIENCE_TECHNICAL_DECISION_MAKER": "str", "TARGETAUDIENCE_STUDENT": "str", "TARGETAUDIENCE_OTHER": "str"}`
- `GET https://mvp.microsoft.com/Locales/StateOrProvince.json` → 200 application/json
  - Antwort: `{"ASIR_SAUDI_ARABIA": "str", "AAKKÂR_LEBANON": "str", "AANA_SAMOA": "str", "AARGAU_SWITZERLAND": "str", "ABIA_NIGERIA": "str", "ABIDJAN_CÔTE_D_IVOIRE": "str", "ABIM_UGANDA": "str", "ABKHAZIA_GEORGIA": "str", "ABRA_PHILIPPINES": "str", "ABRUZZO_ITALY": "str", "ABSERON_AZERBAIJAN": "str", "ABU_DHABI_UNITED_ARAB_EMIRATES": "str", "ABYAN_YEMEN": "str", "ACEH_INDONESIA": "str", "ACKLINS_BAHAMAS": "str", "ACQUAVIVA_SAN_MARINO": "str", "ACRE_BRAZIL": "str", "AD_DAKHILIYAH_OMAN": "str", "AD_DALI_YEMEN": "str", "AD_DAQAHLIYAH_EGYPT": "str", "AD_DAWḨAH_QATAR": "str", "ADAMAOUA_CAMEROON": "str", "ADAMAWA_NIGERIA": "str", "ADANA_TURKEY": "str", "ADAŽU_NOVADS_LATVIA": "str", "ADDIS_ABABA_ETHIOPIA": "str", "ADEN_YEMEN": "str", "ADIYAMAN_TURKEY": "str", "ADJUMANI_UGANDA": "str", "ADJUNTAS_PUERTO_RICO": "str", "ADRAR_ALGERIA": "str", "ADRAR_MAURITANIA": "str", "ADYGEA_RUSSIA": "str", "AFAR_ETHIOPIA": "s`
- `GET https://mvp.microsoft.com/Locales/Formikdatepicker.json` → 200 application/json
  - Antwort: `{"MONTHS": {"list": 12, "item": "str"}, "SHORT_MONTHS": {"list": 12, "item": "str"}, "DAYS": {"list": 7, "item": "str"}, "SHORT_DAYS": {"list": 7, "item": "str"}, "GO_TO_TODAY": "str", "PREV_MONTH_ARIA_LABEL": "str", "NEXT_MONTH_ARIA_LABEL": "str", "PREV_YEAR_ARIA_LABEL": "str", "NEXT_YEAR_ARIA_LABEL": "str", "CLOSE_BUTTON_ARIA_LABEL": "str", "SELECTED_DATE_FORMAT_STRING": "str", "TODAY_DATE_FORMAT_STRING": "str", "MONTH_PICKER_HEADER_ARIA_LABEL": "str", "YEAR_PICKER_HEADER_ARIA_LABEL": "str", "DAY_MARKED_ARIA_LABEL": "str", "WEEK_NUMBER_FORMAT_STRING": "str"}`
- `POST https://browser.events.data.microsoft.com/OneCollector/1.0/` → 200 application/json · Parameter: apikey, client-id, client-version, content-type, cors, time-delta-to-apply-millis, upload-time, w
  - Anfrage: `{"name": "str", "time": "str", "ver": "str", "iKey": "str", "ext": {"web": {"isManual": "bool", "domain": "str", "userConsent": "bool"}, "sdk": {"ver": "str", "seq": "number", "epoch": "str", "installId": "str"}, "app": {"locale": "str", "sesId": "str"}, "user": {"locale": "str"}, "intweb": {}, "utc": {"popSample": "number"}, "loc": {"tz": "str"}, "metadata": {"f": {"behavior": {"t": "…"}}}}, "data": {"baseData": {"ver": "str", "id": "str", "name": "str", "uri": "str", "properties": {"pageTags": {"metaTags": "…"}, "version": "str"}, "isLoggedIn": "bool"}, "baseType": "str", "cookieEnabled": "b`
  - Antwort: `{"acc": 1, "webResult": {"msfpc": "str", "mc1": "str"}}`
- `GET https://mavenapi-prod.microsoft.com/api/SiteContent/SearchFilters/` → 200 application/json; charset=utf-8
  - Antwort: `{"data": {"eventTypes": {"list": 10, "item": {"tenantName": "str", "name": "str", "eventTypeLocKey": "str"}}, "eventFormats": {"list": 3, "item": {"tenantName": "str", "name": "str", "description": "NoneType", "eventFormatLocKey": "str"}}, "targetAudiences": {"list": 6, "item": {"tenantName": "str", "name": "str", "targetAudienceLocKey": "str"}}, "technologyFocusAreas": {"list": 94, "item": {"tenantName": "str", "technologyFocusAreaId": "number", "technologyFocusAreaGroupId": "number", "technologyName": "str", "technologyNameLocKey": "str", "technologyFocusAreaGroupName": "str", "technologyFocusAreaGroupNameLocKey": "str"}}, "timeZones": {"list": 144, "item": {"timeZoneIdentifier": "str", "timeZoneName": "str", "timeZoneNameLocKey": "str"}}, "countryRegions": {"list": 245, "item": {"countryRegionId": "number", "countryRegionName": "str", "countryRegionNameLocKey": "str", "clRegionID": "s`
- `POST https://dc.services.visualstudio.com/v2/track` → 200 application/json; charset=utf-8
  - Anfrage: `{"list": 16, "item": {"time": "str", "iKey": "str", "name": "str", "tags": {"ai.user.id": "str", "ai.session.id": "str", "ai.device.id": "str", "ai.device.type": "str", "ai.operation.name": "str", "ai.operation.id": "str", "ai.internal.sdkVersion": "str", "ai.internal.snippet": "str"}, "data": {"baseType": "str", "baseData": {"ver": "number", "message": "str", "severityLevel": "number", "properties": {}}}}}`
  - Antwort: `{"itemsReceived": 16, "itemsAccepted": 16, "appId": "str", "errors": {"list": 0, "item": null}}`
- `POST https://dc.services.visualstudio.com/v2/track` → 200 application/json; charset=utf-8
  - Anfrage: `{"list": 1, "item": {"time": "str", "iKey": "str", "name": "str", "tags": {"ai.user.id": "str", "ai.session.id": "str", "ai.device.id": "str", "ai.device.type": "str", "ai.operation.name": "str", "ai.operation.id": "str", "ai.internal.sdkVersion": "str", "ai.internal.snippet": "str"}, "data": {"baseType": "str", "baseData": {"ver": "number", "name": "str", "url": "str", "duration": "str", "properties": {"refUri": "…"}, "measurements": {"duration": "…"}, "id": "str"}}}}`
  - Antwort: `{"itemsReceived": 1, "itemsAccepted": 1, "appId": "str", "errors": {"list": 0, "item": null}}`
- `POST https://dc.services.visualstudio.com/v2/track` → 200 application/json; charset=utf-8
  - Anfrage: `{"list": 2, "item": {"time": "str", "iKey": "str", "name": "str", "tags": {"ai.user.id": "str", "ai.session.id": "str", "ai.device.id": "str", "ai.device.type": "str", "ai.operation.name": "str", "ai.operation.id": "str", "ai.internal.sdkVersion": "str"}, "data": {"baseType": "str", "baseData": {"id": "str", "ver": "number", "name": "str", "resultCode": "str", "duration": "str", "success": "bool", "data": "str", "target": "str", "type": "str", "properties": {"HttpMethod": "…"}, "measurements": {}}}}}`
  - Antwort: `{"itemsReceived": 2, "itemsAccepted": 2, "appId": "str", "errors": {"list": 0, "item": null}}`
- `POST https://dc.services.visualstudio.com/v2/track` → 200 application/json; charset=utf-8
  - Anfrage: `{"list": 1, "item": {"time": "str", "iKey": "str", "name": "str", "tags": {"ai.user.id": "str", "ai.session.id": "str", "ai.device.id": "str", "ai.device.type": "str", "ai.operation.name": "str", "ai.operation.id": "str", "ai.internal.sdkVersion": "str", "ai.internal.snippet": "str"}, "data": {"baseType": "str", "baseData": {"ver": "number", "name": "str", "url": "str", "duration": "str", "properties": {"refUri": "…"}, "measurements": {"duration": "…"}, "id": "str"}}}}`
  - Antwort: `{"itemsReceived": 1, "itemsAccepted": 1, "appId": "str", "errors": {"list": 0, "item": null}}`
- `POST https://mavenapi-prod.microsoft.com/api/CommunityLeaders/search/` → 200 application/json; charset=utf-8
  - Anfrage: `{"searchKey": "str", "academicInstitution": "str", "program": {"list": 1, "item": "str"}, "countryRegionList": {"list": 0, "item": null}, "stateProvinceList": {"list": 0, "item": null}, "languagesList": {"list": 0, "item": null}, "milestonesList": {"list": 0, "item": null}, "academicCountryRegionList": {"list": 0, "item": null}, "technologyFocusAreaList": {"list": 0, "item": null}, "industryFocusList": {"list": 0, "item": null}, "technicalExpertiseList": {"list": 0, "item": null}, "technologyFocusAreaGroupList": {"list": 0, "item": null}, "pageIndex": 1, "pageSize": 18}`
  - Antwort: `{"communityLeaderProfiles": {"list": 18, "item": {"firstName": "str", "lastName": "str", "localizedFirstName": "str", "localizedLastName": "str", "profilePictureUrl": "str", "headline": "str", "screenNameLocalized": "bool", "addressCountryOrRegionName": "str", "addressCountryOrRegionNameLocKey": "str", "pictureLink": "NoneType", "userProfileIdentifier": "str", "tenants": {"list": 1, "item": "str"}, "levelStatus": "NoneType"}}, "filteredCount": 3864}`
- `POST https://dc.services.visualstudio.com/v2/track` → 200 application/json; charset=utf-8
  - Anfrage: `{"list": 1, "item": {"time": "str", "iKey": "str", "name": "str", "tags": {"ai.user.id": "str", "ai.session.id": "str", "ai.device.id": "str", "ai.device.type": "str", "ai.operation.name": "str", "ai.operation.id": "str", "ai.internal.sdkVersion": "str", "ai.internal.snippet": "str"}, "data": {"baseType": "str", "baseData": {"ver": "number", "name": "str", "url": "str", "duration": "str", "properties": {"refUri": "…"}, "measurements": {"duration": "…"}, "id": "str"}}}}`
  - Antwort: `{"itemsReceived": 1, "itemsAccepted": 1, "appId": "str", "errors": {"list": 0, "item": null}}`
- `POST https://browser.events.data.microsoft.com/OneCollector/1.0/` → 200 application/json · Parameter: apikey, client-id, client-version, content-type, cors, ext.intweb.msfpc, time-delta-to-apply-millis, upload-time, w
  - Anfrage: `{"name": "str", "time": "str", "ver": "str", "iKey": "str", "ext": {"web": {"isManual": "bool", "domain": "str", "userConsent": "bool"}, "sdk": {"ver": "str", "seq": "number", "epoch": "str", "installId": "str"}, "app": {"locale": "str", "sesId": "str"}, "user": {"locale": "str"}, "intweb": {"msfpc": "str"}, "utc": {"popSample": "number"}, "loc": {"tz": "str"}, "metadata": {"f": {"baseData": {"f": "…"}}}}, "data": {"baseData": {"name": "str", "uri": "str", "isLoggedIn": "bool", "id": "str", "properties": {"pageTags": {"metaTags": "…"}, "version": "str"}, "ver": "str", "behavior": "number", "pa`
  - Antwort: `{"acc": 1, "webResult": {}}`
- `POST https://browser.events.data.microsoft.com/OneCollector/1.0/` → 200 application/json · Parameter: apikey, client-id, client-version, content-type, cors, ext.intweb.msfpc, time-delta-to-apply-millis, upload-time, w
  - Anfrage: `{"name": "str", "time": "str", "ver": "str", "iKey": "str", "ext": {"web": {"isManual": "bool", "domain": "str", "userConsent": "bool"}, "sdk": {"ver": "str", "seq": "number", "epoch": "str", "installId": "str"}, "app": {"locale": "str", "sesId": "str"}, "user": {"locale": "str"}, "intweb": {"msfpc": "str"}, "utc": {"popSample": "number"}, "loc": {"tz": "str"}, "metadata": {"f": {"behavior": {"t": "…"}}}}, "data": {"baseData": {"ver": "str", "id": "str", "name": "str", "uri": "str", "properties": {"pageTags": {"metaTags": "…"}, "version": "str"}, "duration": "str", "perfTotal": "str", "network`
  - Antwort: `{"acc": 1, "webResult": {}}`
- `POST https://browser.events.data.microsoft.com/OneCollector/1.0/` → 200 application/json · Parameter: apikey, client-id, client-version, content-type, cors, ext.intweb.msfpc, time-delta-to-apply-millis, upload-time, w
  - Anfrage: `{"name": "str", "time": "str", "ver": "str", "iKey": "str", "ext": {"web": {"isManual": "bool", "domain": "str", "userConsent": "bool"}, "sdk": {"ver": "str", "seq": "number", "epoch": "str", "installId": "str"}, "app": {"locale": "str", "sesId": "str"}, "user": {"locale": "str"}, "intweb": {"msfpc": "str"}, "utc": {"popSample": "number"}, "loc": {"tz": "str"}, "metadata": {"f": {"baseData": {"f": "…"}}}}, "data": {"baseData": {"name": "str", "uri": "str", "isLoggedIn": "bool", "id": "str", "properties": {"pageTags": {"metaTags": "…"}, "version": "str"}, "ver": "str", "actionType": "str", "beh`
  - Antwort: `{"acc": 1, "webResult": {}}`
