"""Hosts the atlas must not read from or cite (user, 2026-10-19 and 2026-10-29).

Blocked: shadow libraries, document-sharing and user-upload platforms (including user uploads on
scribd.com), and reposts of books or articles on unrelated personal or third-party sites. Allowed:
licensed publisher previews (including Everand), publisher and repository copies, the author's own
posting, Internet Archive lending and public-domain scans, and teaching shares of a single chapter
or article. A text reachable only through a blocked host is recorded as unread; sources link by DOI
or publisher page. Add a host here when a new one turns up.
"""
import re
from urllib.parse import urlparse

BLOCKED_HOSTS = (
    # shadow libraries, mirrors and document-sharing / user-upload platforms
    'dokumen.pub', 'scribd.com', 'epdf.mx', 'epdf.pub', 'pdfcoffee.com', 'vdoc.pub', 'ebin.pub', 'studocu.com',
    'studyres.com', 'paperzz.com', 'studylib.net', 'sweetstudy.com', 'docdrop.org', 'slideshare.net',
    'coursehero.com', 'cliffsnotes.com', 'isidore.co', 'icdst.org', 'communicationcache.com', 'ethernet.edu.et',
    'library.uc.edu.kh', 'libgen.lc', 'libgen.rs', 'libgen.is', 'z-lib.org', 'annas-archive.org',
    'theanarchistlibrary.org', 'libcom.org', 'transreads.org', 'memoof.me', 'thetedkarchive.com',
    'generation-online.org',
    # reposts of books or articles on unrelated personal or third-party sites
    'biknotes.com', 'sethabrutyn.com', 'knowledge4empowerment.com', 'blansh.wordpress.com', 'subpixel.space',
    'literarytheoryandresearchmethods.wordpress.com', 'bosnett.com', 'psychaanalyse.com', 'f-static.com',
    'vicasa.org', 'taradajko.org', 'basearts.com', 'democraziapura.it', 'rrojasdatabank.info', 'caspianet.eu',
    'globalisethis.wordpress.com', 'horomicos.wordpress.com', 'slpress.gr', 'fswg.wordpress.com',
    'hugoribeiro.com.br', 'notesoncraft.org', 'indybay.org', 'analepsis.org', 'zyrosite.com',
    'reclus.files.wordpress.com', 'avblivinglandscape.wordpress.com', 'sgqueeroralhistoryarchive.wordpress.com',
    'cico3.com', 'metodos.work', 'racismandnationalconsciousnessresources.wordpress.com',
    'whataboutthekennedys.com', 'tengkudhaniiqbal.wordpress.com', 'cssplatformbytha.com',
    'mukaddimenotlari.wordpress.com', 'blackbooksdotpub.wordpress.com', 'cesarsalgado.wordpress.com',
    'ddooss.org', 'balkansbg.eu',
)
# Names that identify a blocked route in prose even without a URL.
BLOCKED_NAMES = re.compile(r'\b(dokumen|scribd|epdf|pdfcoffee|studocu|studyres|paperzz|studylib|sweetstudy|'
                           r'docdrop|slideshare|course ?hero|libgen|z-library|anna\W?s archive|ddooss|balkan identities)\b', re.I)
URL = re.compile(r'https?://[^\s"\'<>)\]]+')


def blocked_url(url):
    host = urlparse(url.rstrip('.,;')).netloc.lower().split(':')[0]
    return any(host == h or host.endswith('.' + h) for h in BLOCKED_HOSTS)


def findings(text):
    """Blocked URLs and route names in one string."""
    hits = [u for u in URL.findall(text or '') if blocked_url(u)]
    hits += [m.group(0) for m in BLOCKED_NAMES.finditer(URL.sub(' ', text or ''))]
    return hits
