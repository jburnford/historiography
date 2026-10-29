"""History-scope screen for the UK doctorates collected from OpenAIRE and UK repositories
(data/field-research/openaire-uk-downloads-2026-10-26).

The collector verifies that each record is a UK doctorate; it does not verify the programme. Its
discovery routes were history searches, but they also reach archaeology, classics, art history and
other neighbouring disciplines (user, 2026-10-28: "a few might be archaeology or other related
disciplines"). Each record is judged on the strongest evidence it carries, in this order:

1. A recorded department (Oxford, Cambridge, Sussex, UCL): a History faculty or department is
   ``explicit_history_department``; History and Philosophy of Science counts too (user,
   2026-10-28); any
   other department (archaeology, classics, art history, English, oriental studies, law, ...) is
   ``adjacent_department``.
2. Library of Congress subject classes from the Glasgow and Birmingham browse pages: a history
   class (D, E, F) or another class (HC economic history, HN social history, LA, PN, C, CB, CT)
   counts with a historical title (LC classes describe content, and D/E/F also file contemporary
   policy theses by region); an archaeological title with CC, or CC/AZ alone, is adjacent.
3. Edinburgh's School of History, Classics and Archaeology community: archaeological titles are
   adjacent, classical-antiquity titles need review, the rest are taken as history.
4. OpenAIRE history-search records with neither: a historical title (dates, centuries, periods,
   "history") is taken, an archaeological title is adjacent, and the rest need review.

``history_scope`` values starting ``explicit_history`` count as History PhDs in the graph builder;
everything else stays out of the strict graph. Reviewed decisions go in eligibility-overrides.csv.
"""
import re

NOT_DEPARTMENT = re.compile(
    r'^(university|the univerisity|the university|univeristy|unviersity|oxford university|swansea university|'
    r'durham university|brown university|koc university|bogazici university|queen mary|queens\'|king\'s college|'
    r'pembroke college|kellogg college|jesus college|peterhouse|bodleian|ashmolean|pitt rivers|national museums|'
    r'institute of historical research|zentralbibliothek|dominican friars|same$|soge$|dars$)', re.I)
HISTORY_DEPT = re.compile(r'\bhistory\b', re.I)
NOT_HISTORY_DEPT = re.compile(r'history of art|art history|philosophy of science', re.I)
HPS_DEPT = re.compile(r'philosophy of science', re.I)

ARCHAEOLOGY_TITLE = re.compile(
    r'archaeolog|archaeometr|excavat|prehistor|neolithic|mesolithic|palaeolithic|paleolithic|bronze age|'
    r'iron age|chalcolithic|lithic|ceramic assemblage|pottery|burial practice|mortuary|zooarchaeolog|'
    r'osteolog|isotop|radiocarbon|hillfort|settlement pattern|burials\b|middens?\b', re.I)
CLASSICAL_TITLE = re.compile(
    r'\b(roman|romans|rome|greek|greece|hellen\w*|athen\w*|sparta\w*|latin|homer\w*|virgil|vergil|'
    r'cicero\w*|augustan|republican rome|late antiquity|antiquity|classical|ptolem\w*|pharaonic|'
    r'mycenae\w*|minoan|etrusc\w*|byzant\w*)\b', re.I)
HISTORICAL_TITLE = re.compile(
    r'\b(1[0-9]\d\d|20[0-2]\d)\s*(?:[-–]|to|and)\s*(1[0-9]\d\d|20[0-2]\d|\d\d)\b|\bc\.\s*\d{3,4}\b|'
    r'\b(1[0-9]\d\d)s?\b|\b(century|centuries|medieval|mediaeval|middle ages|early modern|ancien r[eé]gime|'
    r'victorian|edwardian|georgian|tudor|stuart|jacobite|jacobean|elizabethan|restoration|reformation|'
    r'renaissance|enlightenment|colonial|empire|imperial|revolution\w*|interwar|wartime|war|histor\w*|'
    r'anglo-saxon|carolingian|merovingian|norman|crusade\w*|monast\w*|abbey|parliament\w*|reign|dynasty|'
    r'nineteenth|eighteenth|seventeenth|sixteenth|fifteenth|fourteenth|thirteenth|twelfth|eleventh|tenth)\b|'
    # Added after the spot check of 2026-10-28 (149 excluded titles read): three-digit and AD dates,
    # period words in other languages, dynasties and polities, church and institutional history.
    # 'Soviet', 'peasant' and 'Viking' were tried and dropped: they pull in Glasgow's contemporary
    # Russia studies, anthropology and Viking Age archaeology. BC/BCE ranges are left to archaeology.
    r'\b\d{3,4}\s*[-–]\s*\d{3,4}\b(?!\s*B\.?C)|\ba\.?\s?d\.?\s*\d{3,4}\b|\b(secol\w*|si[eè]cles?|jahrhunderts?|siglos?|'
    r'byzant\w*|jacobit\w*|lancastrian|yorkist|plantagenet|angevin|hanoverian|habsburg|tsarist|bolshevik\w*|'
    r'weimar|nazi\w*|fascis\w*|ottoman|qajar|safavid|mughal|abbasid|umayyad|fatimid|mamluk|'
    r'ming|qing|tokugawa|meiji|longobard\w*|lombard\w*|frankish|visigoth\w*|british mandate|'
    r'chronicles?|martyrolog\w*|hagiograph\w*|pittism|puritan\w*|covenanter\w*|recusan\w*|jesuits?|friars?|'
    r'papacy|papal|bishops?|diocese\w*|clergy|kingship|lordship|aristocra\w*|gentry|nobility|guilds?)\b',
    re.I)
OTHER_DISCIPLINE_TITLE = re.compile(
    r'\b(a corpus study|corpus linguistics|syntactic|lexical|phonolog\w*|morpholog\w*|genre analysis|'
    r'novel(s|ist)?|poetry|poems?|poetics|fiction|literary|music(al)?|composer|opera|painting|sculpture|'
    r'iconograph\w*|architecture|theolog\w*|exegesis|biblical|christolog\w*|eucharist\w*|trinit\w*|'
    r'ecclesiolog\w*)\b', re.I)
HISTORY_LC = re.compile(r'^(D[A-Z]*|E|F)\d*$')


def departments(values):
    return [v.strip() for v in values if v.strip() and v.strip() != '|' and not NOT_DEPARTMENT.search(v.strip())]


def lc_classes(discovery):
    """LC class codes ('DA', 'D204', 'HC') from a Glasgow/Birmingham 'Discovery subjects' cell."""
    return [part.strip().split(' ')[0] for part in re.split(r';\s*', discovery or '') if part.strip()]


def classify(title, department_values=(), discovery='', origin=''):
    """(history_scope, eligibility_basis) for one UK doctorate."""
    title = title or ''
    depts = departments(department_values)
    if depts:
        history = [d for d in depts if HISTORY_DEPT.search(d) and not NOT_HISTORY_DEPT.search(d)]
        if history:
            return 'explicit_history_department', 'department: ' + '; '.join(history)
        if any(HPS_DEPT.search(d) for d in depts):
            # User, 2026-10-28: "history and philosophy of science should be included as well".
            return 'explicit_history_and_philosophy_of_science_department', 'department: ' + '; '.join(depts)
        return 'adjacent_department', 'department: ' + '; '.join(depts)
    classes = lc_classes(discovery) if origin in ('glasgow', 'birmingham') else []
    if classes:
        basis = 'LC subject classes: ' + ', '.join(classes)
        hist = [c for c in classes if HISTORY_LC.match(c)]
        if 'CC' in classes and ARCHAEOLOGY_TITLE.search(title):
            return 'adjacent_lc_class', basis + '; archaeological title'
        if not hist and set(classes) <= {'CC', 'AZ'}:
            return 'adjacent_lc_class', basis
        # LC classes describe content, not the awarding programme: D/E/F also file contemporary
        # policy and social-science theses by region, so a historical title is required as well.
        if HISTORICAL_TITLE.search(title) and not OTHER_DISCIPLINE_TITLE.search(title):
            return ('explicit_history_lc_class_and_title', basis + '; historical title') if hist else \
                   ('explicit_history_lc_class_and_title', basis + '; non-history class with historical title')
        return 'unverified_lc_class', basis
    if origin == 'edinburgh':
        basis = 'School of History, Classics and Archaeology community'
        if ARCHAEOLOGY_TITLE.search(title):
            return 'adjacent_school_title', basis + '; archaeological title'
        if CLASSICAL_TITLE.search(title) and not re.search(r'\b1[0-9]\d\d\b', title):  # 'Sack of Rome, 1527'
            return 'classical_school_title', basis + '; classical-antiquity title'
        if OTHER_DISCIPLINE_TITLE.search(title):
            return 'unverified_school_title', basis + '; other-discipline title'
        return 'explicit_history_school_title_screen', basis + '; title screen'
    basis = 'OpenAIRE history search; no department or subject recorded'
    if ARCHAEOLOGY_TITLE.search(title):
        return 'adjacent_title', basis + '; archaeological title'
    if HISTORICAL_TITLE.search(title) and not OTHER_DISCIPLINE_TITLE.search(title):
        return 'explicit_history_search_and_title', basis + '; historical title'
    return 'unverified_title', basis
