#!/usr/bin/env python3
"""The ancient-history ruling (user, 2026-11-17) as one title rule shared by the thesis screens.

User: "ancient history is history unless it is archeology". The coordinator's reading, applied here (Claude's
reading, recorded in the dissertation README): Assyriology, Egyptology and classics count when the thesis is
historical, and stay held when it is philology or text edition, or archaeology. Church history, theology and the
history of religions were not ruled on and stay held.

``verdict(title)`` returns one of:
- 'archaeology'  excavation, material culture, art and architecture of antiquity, archaeometry, prehistory;
- 'religion'     theology, church history, history of religions (not ruled; held), unless the title is about
                 the state, law or war (religious policy of an emperor, persecution by the state);
- 'philology'    text edition, translation, commentary, text history, grammar and lexicon (always), or
                 literary study (unless the title also names a historical subject: politics, law, society,
                 slavery, war, economy, administration, history);
- 'history'      everything else.

Used by: dissertation_ingest.dnb_screen (Germany), register_france_resurvey.scope (France),
register_sweden_theses.scope (Sweden), and uk_ancient_ruling_overrides.py (Edinburgh classical titles).
The order of the tests is the order above. Titles are matched case-insensitively, accents kept and folded.
"""
import re
import unicodedata


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).casefold()


ARCHAEOLOGY = re.compile(
    r'archaeolog|archaolog|archeolog|arkeolog|archaeometr|archaometr|excavat|ausgrab|altgrabung|\bgrabung|fouille|utgravning|'
    r'prehistor|prahistor|protohistor|vorgeschicht|neolith|mesolith|pal(a)?eolith|palaolith|chalcolith|\blithic|lithik|'
    r'stone age|steinzeit|stenalder|bronze age|bronzezeit|bronsalder|age du bronze|iron age|eisenzeit|jarnalder|age du fer|'
    r'hallstatt|latene|jager-sammler|hunter-gatherer|chasseurs-cueilleurs|steel making|'
    r'pottery|ceramic|keramik|ceramique|ceramica|sigillata|terracott|terrakott|amphor|typolog|'
    r'graberfeld|grabfund|necropol|nekropol|necropole|burial|mortuary|bestattung|sepulture|pratiques funeraires|'
    r'monuments funeraires|funerary rites|tomb decoration|zooarchaeolog|archaozoolog|tierknochen|animal bones|osteolog|'
    r'skeletal|soft tissue|bioanthropolog|isotop|radiocarbon|\b14c\b|hillfort|midden|fundplatz|fundplatze|fundkomplex|'
    r'\bfunde\b|siedlungsfunde|villa rustica|mosaic|mosaik|mosaique|fresco|wandmalerei|malerei|wall painting|peinture|'
    r'sculpt|skulptur|plastik\b|rundplastik|reliefplastik|grabplastik|idealplastik|statue|statuar|\breliefs?\b|weihrelief|'
    r'\bvases?\b|vasen|vasenbild|vasenmalerei|iconograph|ikonograph|ikonolog|iconolog|architect|architekt|bauornament|'
    r'baugeschicht|building techniques|built landscape|domestic architecture|doors and windows|\btempel\b|mastaba|pyramid|'
    r'grabanlag|grabbau|grabdenkm|grabkunst|grabmal|sarcophag|sarkophag|\bparure|petit mobilier|metallurg|bronzes\b|'
    r'geoarch|the site of|geochronolog|sedimentolog|turmgrab|graber\b|besiedlung|siedlungsgeschicht|settlement behavio|felsbild|rock art|felseinsiedel|settlement archaeolog|siedlungsarch|survey\b|'
    r'\b(minoan|mycenaean|greek|roman|etruscan|egyptian|hellenistic|classical|griechisch\w*|romisch\w*|antik\w*) (art|kunst)\b',
    re.I)
RELIGION = re.compile(
    r'theolog|exeges|exegese|\bbibl(e|ical|isch\w*|ique)|christolog|liturg|hagiograph|\bchurch|kirche|\beglise|kyrk|'
    r'\bclergy|klerus|\bclerge|\bbishops?\b|bischof|bischofl|\beveques?\b|martyr|heresi|heresy|heretic|haresi|haretik|patriarchat|religio|'
    r'\bcults?\b|\bkult(e|s)?\b|kaiserkult|\bgods?\b|gott(er|es)?\b|\bdieux\b|\bdieu\b|deities|divine|gottlich|'
    r'hymn|sanctification|\bpagan|heiden|myth', re.I)
RELIGION_BUT_HISTORY = re.compile(r'politi|administrat|verwaltung|\bsocial|sozial|societe|gesellschaft|econom|wirtschaft|\bpolicy|\bstaat|\bstate\b|\betat\b|\blaw\b|\brecht|\bdroit|\bkrieg|\bwar\b|'
                                  r'\bguerre|\barmy|militar|military|verfolgung|persecution', re.I)
PHILOLOGY_HARD = re.compile(
    r'\bedition|\beditio\b|erstedition|lesetext|kritisch\w* edition|critical edition|textkrit|\btranslation|traduction|'
    r'ubersetzung|commentary|commentaire|kommentar|commento|histoire du texte|textgeschichte|text history|philolog|'
    r'linguist|grammat|\bsyntax|lexic|lexik|semantic|semant\w*|semasiolog|phraseolog|indogerman|\bmanuscripts?\b', re.I)
PHILOLOGY_SOFT = re.compile(
    r'metaphor|poetry|poetics|poesie|\bpoem|poeme|elegy|elegie|\bepic\b|epopee|\bepos\b|tragedy|tragedie|tragodie|'
    r'comedy|komodie|novel\b|romans? (grecs?|d.antiquite)|literatur|literary|litterat|literaire|\bhomer|ovid|'
    r'euripid|sophocl|apollonius|pindar|lyric|lyrik|\bmyth|narrative|erzahlten welt|reading (latin|greek)', re.I)
HISTORY_WORDS = re.compile(
    r'politi|\blaw\b|\brecht|\bdroit|econom|wirtschaft|administrat|verwaltung|society|gesellschaft|societe|\bsocial|sozial|'
    r'slave|sklav|esclav|citizen|burger|citoyen|diplomac|diplomat|\barmy|armee|militar|military|\bwar\b|\bkrieg|\bguerre|'
    r'empire\b|\breich\b|histor|geschicht|histoire|power\b|\bmacht|status|identity|identitat', re.I)


def verdict(title):
    t = fold(title)
    if ARCHAEOLOGY.search(t):
        return 'archaeology'
    if RELIGION.search(t) and not RELIGION_BUT_HISTORY.search(t):
        return 'religion'
    if PHILOLOGY_HARD.search(t):
        return 'philology'
    if PHILOLOGY_SOFT.search(t) and not HISTORY_WORDS.search(t):
        return 'philology'
    return 'history'


HELD_REASON = {
    'archaeology': 'archaeology (ancient-history ruling 2026-11-17: archaeology stays out)',
    'religion': 'history of religions / church history (not ruled): held',
    'philology': 'philology or text edition (ancient-history ruling 2026-11-17, coordinator reading): held',
}
