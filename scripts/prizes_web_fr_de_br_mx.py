"""History prize winners from awarding bodies in France, Germany, Brazil and Mexico (harvest of 2026-11-12).

One row per (prize, year, winner, work), read only from the awarding body's own public pages, fetched through the
project's polite fetcher (scripts/prizes_fetch.py: robots.txt obeyed, 1.2 s per host, raw pages cached under
build/prizes-2026-11-12/raw/, every fetch and refusal logged to build/prizes-2026-11-12/fetch-log.jsonl).

Sources
  FR  Académie française, laureate lists per prize (https://www.academie-francaise.fr/<prize-slug>):
        Grand Prix Gobert, Prix Guizot, Prix Thiers, Prix Augustin Thierry, Prix Eugène Colas, Prix Georges Goyau,
        Prix François Millepierres, Prix Monseigneur Marcel, Prix Diane Potier-Boès, Prix Eugène Carrière
      Les Rendez-vous de l'histoire (Blois), https://rdv-histoire.com/le-festival/les-prix/<prize-slug>:
        Grand prix des Rendez-vous de l'histoire, Prix Augustin Thierry, Prix lycéen du livre d'histoire,
        Prix Anthony Rowley
  DE  VHD (https://www.historikerverband.de/aktivitaeten/preise/...): Hedwig Hintze Preis, Carl Erdmann Preis,
        Peter-Haber-Preis
      Gerda Henkel Stiftung, https://www.gerda-henkel-stiftung.de/preistraegerinnen-und-preistraeger?page_id=93602
      Historisches Kolleg, https://www.historischeskolleg.de/historikerpreis/ and one page per laureate
      Stadt Münster, two news pages (2017, 2023) - the city site has no full laureate list
  BR  ANPUH-Brasil, Prêmio de Teses Manoel Salgado Guimarães, editions 1-9
        (https://anpuh.org.br/index.php/2015-01-20-00-01-55/programas-de-pos-graduacao-em-historia/<n>)
      Prêmio Jabuti (Câmara Brasileira do Livro), https://www.premiojabuti.com.br/jabuti/premiados-por-edicao/premiacao/?ano=YYYY
        category 'Ciências Humanas' (and any category named for history); Jabuti Acadêmico
        (/academico/premiados-por-edicao-academico/premiacao/?ano=YY), category 'História e Arqueologia'
  MX  Diario Oficial de la Federación (https://dof.gob.mx/nota_detalle.php?codigo=...): the presidential
        'Acuerdo por el que se otorga el Premio Nacional de Ciencias y Artes / de Artes y Literatura', Campo III
        (Historia, Ciencias Sociales y Filosofía), 2000-2025 (2005 and 2016 acuerdos not found by the DOF search)
      INAH, Premio Francisco Javier Clavijero (Historia y Etnohistoria): 2024 results PDF and 2023 Boletín 757
        (premios.inah.gob.mx does not resolve from here, so other years are missing)

Field notes: Jabuti 'Ciências Humanas' rows are not all history; their field says so. ANPUH editions 1-8 print no
award year: year is '' and the note gives the edition and the defence window. Jury members, shortlists and
nominees are never rows; honourable mentions are rows with note 'mention'.

Run:  python3 scripts/prizes_web_fr_de_br_mx.py
      -> build/prizes-2026-11-12/rows-web-fr-de-br-mx.jsonl, counts per body printed
"""
import html as H
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prizes_fetch import fetch, text_of, path_for, BUILD  # noqa: E402
from prizes_harvest import prize_id, COLS  # noqa: E402

OUT = BUILD / 'rows-web-fr-de-br-mx.jsonl'


def clean(s):
    s = H.unescape(re.sub(r'<[^>]+>', ' ', s or '')).replace('\xa0', ' ').replace('\u2028', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def row(body, country, prize, **kw):
    r = {c: '' for c in COLS}
    r.update(prize_id=prize_id(body, prize), prize=prize, body=body, body_country=country, field='history',
             source_kind='awarding-body')
    for k, v in kw.items():
        r[k] = (v or '').strip() if isinstance(v, str) else str(v)
    return r


def per_author(rows_spec):
    """[(names list, kwargs)] -> one row kwargs per author with co_winners."""
    out = []
    for names, kw in rows_spec:
        names = [n for n in names if n]
        for n in names:
            d = dict(kw)
            d['winner'] = n
            d['co_winners'] = '; '.join(x for x in names if x != n)
            out.append(d)
    return out


def split_names(s):
    s = re.sub(r'^(?:de|De|par)\s+', '', s.strip())
    parts = re.split(r',\s*|\s+et\s+|\s+e\s+|\s+und\s+|\s+y\s+(?:a\s+)?', s)
    return [p.strip(' .') for p in parts if p.strip(' .')]


# ---------------------------------------------------------------- FR: Académie française

AF = 'Académie française'
AF_PRIZES = [  # slug, prize name, field
    ('grand-prix-gobert', 'Grand Prix Gobert', 'history of France'),
    ('prix-guizot', 'Prix Guizot', 'history'),
    ('prix-thiers', 'Prix Thiers', 'history'),
    ('prix-augustin-thierry', 'Prix Augustin Thierry', 'medieval history'),
    ('prix-eugene-colas', 'Prix Eugène Colas', 'history'),
    ('prix-georges-goyau', 'Prix Georges Goyau', 'local history'),
    ('prix-francois-millepierres', 'Prix François Millepierres', 'ancient history, erudition or philosophy'),
    ('prix-monseigneur-marcel', 'Prix Monseigneur Marcel', 'Renaissance history (philosophical, literary, artistic)'),
    ('prix-diane-potier-boes', 'Prix Diane Potier-Boès', 'history of Egypt and Franco-Egyptian relations'),
    ('prix-eugene-carriere', 'Prix Eugène Carrière', 'history of art'),
]
CIVILITY = re.compile(r"^((?:M\.|Mme|Mlle|MM\.|R\.P\.|R\.\s?P\.|Pr\.|Dr|Mgr|abbé|chanoine|dom|cardinal|amiral|vice-amiral|"
                      r"général|capitaine|lieutenant|colonel|commandant|duc|duchesse|comte|comtesse|vicomte|marquis|"
                      r"marquise|baron|baronne|prince|princesse|père|frère|sœur|pasteur|R\.\s?M\.)\s+)+")


def af_rows():
    rows = []
    for slug, prize, field in AF_PRIZES:
        url = f'https://www.academie-francaise.fr/{slug}'
        h = fetch(url)
        if not h:
            continue
        for m in re.finditer(r'(?s)<div class="academie-laureate">\s*<span class="date">(\d{4})</span>'
                             r'\s*<span class="infos">(.*?)</span>\s*<span class="clearfix">', h):
            year, inf = m.group(1), m.group(2)
            a = re.search(r'(?s)<a class="title" href="([^"]*)">(.*?)</a>', inf)
            if not a:
                continue
            printed = clean(a.group(2))
            civ = CIVILITY.match(printed)
            name = printed[civ.end():] if civ else printed
            if not civ and (name.isupper() or re.match(r"(?i)(revue|soci[ée]t[ée]|acad[ée]mie|association|institut|"
                                                           r"mus[ée]e|comit[ée]|biblioth[èe]que|archives|ville|commune)\b", name)):
                continue   # institutions (e.g. ACADÉMIE DE MÂCON, Revue historique de l'armée) are not persons
            em = re.search(r'(?s)<em>(.*?)</em>', inf)
            title = clean(em.group(1)) if em else ''
            award = clean(re.sub(r'(?s)<a .*?</a>|<em>.*?</em>', ' ', inf))
            notes = []
            honours = 'book'
            if re.fullmatch(r"(?i)(et )?(pour )?(l')?ensemble de (son|ses) .*", title):
                notes.append('for: ' + title)
                title, honours = '', 'career'
            elif re.search(r"(?i),?\s*(et )?(pour )?(l')?ensemble de son (œ|oe)uvre\s*$", title):
                title = re.sub(r"(?i)[,\s]*(et )?(pour )?(l')?ensemble de son (œ|oe)uvre\s*$", '', title).strip(' ,')
                notes.append("and for the whole of the author's work")
                if not title:
                    honours = 'career'
            if not title and honours == 'book':
                honours = 'other'
                notes.append('no work printed')
            if award:
                notes.append('award: ' + award)
                if re.search(r'(?i)mention', award):
                    notes.insert(0, 'mention')
            if civ:
                notes.append('printed as: ' + printed)
            notes.append('af page: ' + a.group(1))
            rows.append(row(AF, 'FR', prize, field=field, honours=honours, year=year, winner=name,
                            work_title=title, source_url=url, note='; '.join(notes)))
    return rows


# ---------------------------------------------------------------- FR: Rendez-vous de l'histoire (Blois)

RVH = "Les Rendez-vous de l'histoire (Blois)"
RVH_PRIZES = [
    ('le-grand-prix-des-rendez-vous-de-lhistoire', "Grand prix des Rendez-vous de l'histoire", 'history', ''),
    ('le-prix-augustin-thierry', 'Prix Augustin Thierry', 'contemporary history', ''),
    ('le-prix-lyceen-du-livre-dhistoire', "Prix lycéen du livre d'histoire", 'history', 'jury of lycée students'),
    ('le-prix-anthony-rowley', 'Prix Anthony Rowley', 'food history', ''),
]


def rvh_rows():
    rows = []
    for slug, prize, field, extra in RVH_PRIZES:
        url = f'https://rdv-histoire.com/le-festival/les-prix/{slug}'
        h = fetch(url)
        if not h:
            continue
        secs = re.split(r'<h2[^>]*>\s*<span>\s*(Lauréat[^<]*?(\d{4}))\s*</span>\s*</h2>', h)
        # secs = [pre, head, year, body, head, year, body, ...]
        for i in range(1, len(secs) - 2, 3):
            year, body = secs[i + 1], secs[i + 2]
            body = re.split(r'<h2', body)[0]
            for b in re.finditer(r'(?s)<div class="text-lg leading-tight font-bold">(.*?)</div>\s*<div>(.*?)</div>'
                                 r'(?:\s*<div class="font-alt[^"]*">(.*?)</div>)?', body):
                title, auth, pub = clean(b.group(1)), clean(b.group(2)), clean(b.group(3) or '')
                names = split_names(auth)
                note = extra
                for d in per_author([(names, dict(work_title=title.rstrip('.') if title.endswith('.') and not
                                                  title.endswith('..') else title, publisher=pub))]):
                    rows.append(row(RVH, 'FR', prize, field=field, honours='book', year=year, source_url=url,
                                    note=note, **d))
    return rows


# ---------------------------------------------------------------- DE: VHD

VHD = 'Verband der Historiker und Historikerinnen Deutschlands (VHD)'


def vhd_rows():
    rows = []
    for slug, prize, honours in [('hedwig-hintze-preis', 'Hedwig Hintze Preis', 'dissertation'),
                                 ('carl-erdmann-preis', 'Carl Erdmann Preis', 'other')]:
        url = f'https://www.historikerverband.de/aktivitaeten/preise/{slug}/'
        h = fetch(url)
        if not h:
            continue
        t = text_of(h)
        hab = 'habilitation thesis' if honours == 'other' else ''
        # current year: prose paragraph
        m = re.search(r'(?s)%s (\d{4})\n.*?(?:Auf der Shortlist|Bisherige)' % re.escape(prize), t)
        if m:
            y, para = m.group(1), m.group(0)
            w = re.search(r'\n([A-ZÄÖÜ][\w\-]+(?: [A-ZÄÖÜ][\w\-]+)+) \(im Bild[^)]*\) erhielt den [^\n]*?Arbeit zu „([^“]+)“'
                          r'(?:, mit der sie an der ([^\n]+?) promoviert)?', para)
            w2 = re.search(r'Ausgezeichnet wurde in diesem Jahr ([^(]+?) \(im Bild[^)]*\), die sich[^\n]*? an der ([^\n]+?) '
                           r'habilitierte[^\n]*?\n[^\n]*?Arbeit „([^“]+)“', para)
            if w:
                rows.append(row(VHD, 'DE', prize, honours=honours, year=y, winner=w.group(1), work_title=w.group(2),
                                source_url=url, note=('affiliation: ' + w.group(3)) if w.group(3) else ''))
            elif w2:
                rows.append(row(VHD, 'DE', prize, honours=honours, year=y, winner=w2.group(1).strip(),
                                work_title=w2.group(3), source_url=url,
                                note='; '.join(x for x in [hab, 'affiliation: ' + w2.group(2)] if x)))
        past = t.split('Bisherige Preis', 1)[-1] if 'Bisherige Preis' in t else ''
        year = ''
        for line in past.split('\n')[1:]:
            if re.fullmatch(r'(19|20)\d\d', line):
                year = line
                continue
            mm = re.match(r'^([^:„]{3,80}): „(.+)“\s*$', line)
            if mm and year:
                note = hab
                if prize == 'Carl Erdmann Preis' and int(year) <= 2011:
                    note = '; '.join(x for x in [hab, 'awarded as Preis für hervorragende Leistungen des '
                                                       'wissenschaftlichen Nachwuchses'] if x)
                rows.append(row(VHD, 'DE', prize, honours=honours, year=year, winner=mm.group(1).strip(),
                                work_title=mm.group(2).strip(), source_url=url, note=note))
            elif year and not mm:
                break
    # Peter-Haber-Preis (digital history projects; places 1-3)
    url = 'https://www.historikerverband.de/aktivitaeten/preise/peter-haber-preis/'
    h = fetch(url)
    if h:
        t = text_of(h)
        year = ''
        for line in t.split('\n'):
            y = re.search(r'Peter-Haber-Preise?s? (\d{4})', line) or re.fullmatch(r'((?:19|20)\d\d)', line)
            if y:
                year = y.group(1)
            mm = re.match(r'^Platz (\d): (.+?): [„"]?(.+?)[“"]?$', line)
            if mm and year:
                names = [n.strip() for n in re.split(r',\s*|\s+und\s+', mm.group(2)) if n.strip()]
                for d in per_author([(names, dict(work_title=mm.group(3).strip(' “"')))]):
                    rows.append(row(VHD, 'DE', 'Peter-Haber-Preis', field='digital history', honours='other',
                                    year=year, source_url=url, note=f'place {mm.group(1)}; digital history project', **d))
    return rows


# ---------------------------------------------------------------- DE: Gerda Henkel Stiftung

def henkel_rows():
    body, prize = 'Gerda Henkel Stiftung', 'Gerda Henkel Preis'
    url = 'https://www.gerda-henkel-stiftung.de/preistraegerinnen-und-preistraeger?page_id=93602'
    h = fetch(url)
    rows = []
    if not h:
        return rows
    t = text_of(h).split('\n')
    for i, line in enumerate(t):
        m = re.fullmatch(r'Preisträger(?:in)? (\d{4})', line)
        if m and i + 2 < len(t):
            nm = re.fullmatch(r'((?:Prof\.|Dr\.|D\.|h\.c\.|mult\.|\s)*)(.+?) \(([^)]+)\)', t[i + 1])
            if not nm:
                continue
            rows.append(row(body, 'DE', prize, field=t[i + 2], honours='career', year=m.group(1),
                            winner=nm.group(2).strip(), source_url=url,
                            note=f'affiliation (place as printed): {nm.group(3)}; printed as: {t[i + 1]}'))
    return rows


# ---------------------------------------------------------------- DE: Historisches Kolleg

def kolleg_rows():
    body, prize = 'Historisches Kolleg', 'Preis des Historischen Kollegs'
    idx = 'https://www.historischeskolleg.de/historikerpreis/'
    h = fetch(idx)
    rows = []
    if not h:
        return rows
    for link in dict.fromkeys(re.findall(r'href="(https://www\.historischeskolleg\.de/historikerpreis/[a-z0-9-]+/)"', h)):
        p = fetch(link)
        if not p:
            continue
        t = text_of(p)
        lines = t.split('\n')
        name = re.sub(r'^Professor(?:in)? (?:Dr\. )*', '', lines[0]).strip()
        y = re.search(r'(?:Preis(?:es)? des Historischen Kollegs|Träger(?:in)? des Preises des Historischen Kollegs) (\d{4})', t)
        if not y:
            continue
        work, isbn = '', ''
        w = re.search(r'Ausgezeichnetes Werk\n(.+)', t)
        if w:
            wl = w.group(1)
            pre = re.match(r'^([^:]{3,60}):\s*', wl)
            if pre and name.split()[-1] in pre.group(1):   # 'Gudrun Krämer: Title' (also misspelt first names)
                wl = wl[pre.end():]
            wl = re.sub(r'\s*\(=[^)]*\)', '', wl)
            i = re.search(r'ISBN[:\s]*([\d\-X]+)', wl)
            if i:
                isbn = 'isbn:' + i.group(1).replace('-', '')
            work = re.split(r'\.\s+[A-ZÄÖÜ][a-zäöü]+(?:/[A-Za-z]+)? \d{4}|,\s*\d+ S\.|,\s*ISBN', wl)[0].strip(' .')
        bio = ''
        for ln in lines[1:12]:
            if re.search(r' (war|ist|lehrt|lehrte)\b.*\b(Professor|Universität|Institut|Direktor|Leiter)', ln):
                bio = ln
                break
        rows.append(row(body, 'DE', prize, honours='career', year=y.group(1), winner=name, work_title=work,
                        work_ids=isbn, source_url=link,
                        note='; '.join(x for x in ['for the whole scholarly work' + (', distinguished work printed' if work else ''),
                                                   ('affiliation: ' + bio[:240]) if bio else ''] if x)))
    return rows


# ---------------------------------------------------------------- DE: Stadt Münster

def muenster_rows():
    body = 'Stadt Münster'
    rows = []
    u1 = 'https://www.stadt-muenster.de/archiv/startseite/historikerpreis-2017.html'
    t = text_of(fetch(u1) or '')
    if 'David Nirenberg' in t and 'Anti-Judaismus. Eine Geschichte des westlichen Denkens' in t:
        rows.append(row(body, 'DE', 'Historikerpreis der Stadt Münster', honours='book', year='2017',
                        winner='David Nirenberg', work_title='Anti-Judaismus. Eine Geschichte des westlichen Denkens',
                        source_url=u1, note='affiliation: teaches in Chicago (der in Chicago lehrende)'))
    if 'Philipp Erdmann' in t:
        rows.append(row(body, 'DE', 'Förderpreis der Stadt Münster für junge Historikerinnen und Historiker',
                        honours='other', year='2017', winner='Philipp Erdmann', source_url=u1,
                        note='for his work on denazification in Münster (Arbeit zur Entnazifizierung in Münster)'))
    u2 = 'https://www.stadt-muenster.de/aktuelles/newsdetail/historikerinnenpreis-der-stadt-muenster-geht-an-ute-daniel'
    t = text_of(fetch(u2) or '')
    if 'Ute Daniel' in t and 'Technischen Universität Braunschweig' in t:
        rows.append(row(body, 'DE', 'Historiker*innenpreis der Stadt Münster', honours='career', year='2023',
                        winner='Ute Daniel', source_url=u2,
                        note='affiliation: Technische Universität Braunschweig; council decision 15.02.2023, '
                             'presented 27 September 2023; for her broad body of work'))
    return rows


# ---------------------------------------------------------------- BR: ANPUH thesis prize

ANPUH = 'ANPUH-Brasil (Associação Nacional de História)'
ANPUH_PAGES = ['1', '2', '3', '4', '5', '6', '7-teses-de-julho-de-2018-a-junho-de-2020',
               '8-teses-setembro-de-2020-a-agosto-de-2022', '9-teses-setembro-de-2022-a-outubro-de-2024']
KEYS = {'Título': 'title', 'Autor': 'author', 'Autora': 'author', 'Autoria': 'author', 'Orientador': 'adv',
        'Orientadora': 'adv', 'Orientadores': 'adv', 'Orientadoras': 'adv', 'Orientação': 'adv',
        'Co-orientador': 'coadv', 'Co-orientadora': 'coadv', 'Programa': 'prog', 'Programa e Universidade': 'prog'}


def anpuh_rows():
    rows, prize = [], 'Prêmio de Teses Manoel Luiz Salgado Guimarães'
    base = 'https://anpuh.org.br/index.php/2015-01-20-00-01-55/programas-de-pos-graduacao-em-historia/'
    for ed, slug in enumerate(ANPUH_PAGES, 1):
        url = base + slug
        h = fetch(url)
        if not h:
            continue
        t = text_of(h)
        start = max(t.find('Teses concorrentes'), t.find('Lista de teses concorrentes'), t.find('TESE VENCEDORA'))
        if start < 0:
            continue
        window = ''
        wm = re.search(r'(?i)teses concorrentes, defendidas ([^:\n]+):', t)
        if wm:
            window = wm.group(1)
        t = t[start:t.find('Comissão Avaliadora') if 'Comissão Avaliadora' in t else len(t)]
        t = t.split('Tweet')[0]
        recs, cur, pending_prog, whole_winner = [], {}, '', 'TESE VENCEDORA' in t
        lines = t.split('\n')[1:]
        for ln in lines:
            k = re.match(r'^(Título|Autora?|Autoria|Orientador(?:a|es|as)?|Orientação|Co-orientador(?:a)?|'
                         r'Programa e Universidade|Programa)\s*:\s*(.*)$', ln)
            if k:
                key = KEYS[k.group(1)]
                if key in cur:
                    recs.append(cur)
                    cur = {}
                if not cur and pending_prog:
                    cur['prog'] = pending_prog
                    pending_prog = ''
                cur[key] = k.group(2).strip()
                cur['_last'] = key
            elif re.match(r'^(Resumo|Palavras-chave|Parabéns|TESE VENCEDORA)', ln):
                cur['_last'] = ''
            elif cur.get('_last') == 'title' and ln.startswith('('):
                cur['title'] += ' ' + ln            # wrapped title line, e.g. '(Rio de Janeiro, 1888-1898).'
            elif len(ln) < 120 and not ln.startswith(('Título', 'Lido')):
                if cur and 'author' in cur and 'title' in cur:
                    recs.append(cur)
                    cur = {}
                pending_prog = ln
        if cur:
            recs.append(cur)
        for r in recs:
            title = r.get('title', '')
            mark = ''
            mm = re.search(r'\s*[-–(]*\s*\(?\s*(VENC\s?EDORA|TESE PREMIADA[^)]*|MENÇÃO HONROSA[^)]*)\)?\s*$', title)
            if mm:
                mark = mm.group(1)
                title = title[:mm.start()].strip()
            if ed == 9 and whole_winner and not mark:
                mark = 'VENCEDORA'
            prog = re.sub(r'\s*[-–]\s*Menção Honrosa\s*$', '', r.get('prog', ''), flags=re.I)
            if re.search(r'(?i)menção honrosa', r.get('prog', '')) and not mark:
                mark = 'MENÇÃO HONROSA'
            if not mark:
                continue          # entrants (concorrentes) are not winners
            notes = []
            if 'MENÇÃO' in mark:
                notes.append('mention')
            pl = re.search(r'(\d)\s*[ºo°]?\s*LUGAR', mark)
            if pl:
                notes.append(f'place {pl.group(1)}')
            notes.append(f'edition {ed}')
            if ed < 9:
                notes.append('award year not printed')
            if window:
                notes.append('theses defended ' + window)
            if prog:
                notes.append('affiliation: ' + prog.rstrip('.'))
            if r.get('adv'):
                notes.append('advisor: ' + r['adv'].rstrip('.'))
            if r.get('coadv'):
                notes.append('co-advisor: ' + r['coadv'].rstrip('.'))
            rows.append(row(ANPUH, 'BR', prize, honours='dissertation', year='2025' if ed == 9 else '',
                            winner=r.get('author', '').rstrip('.'), work_title=title.strip(' "“”').rstrip('.'),
                            source_url=url, note='; '.join(notes)))
    return rows


# ---------------------------------------------------------------- BR: Prêmio Jabuti

JAB = 'Câmara Brasileira do Livro (Prêmio Jabuti)'
JAB_CATS = re.compile(r'(?i)^(ciências humanas.*|humanidades|história|história e arqueologia|historia)$')
ROLE_NOTE = {'Organizador(a)': 'editor', 'Tradutor(a)': 'translator', 'Ilustrador(a)': 'illustrator'}


def jabuti_page(url, prize, year):
    h = fetch(url)
    rows = []
    if not h:
        return rows
    for sec in re.split(r'<h4>', h)[1:]:
        cat = clean(sec.split('</h4>')[0])
        if not JAB_CATS.match(cat):
            continue
        field = ('history and archaeology' if cat.lower() == 'história e arqueologia' else 'history'
                 if cat.lower() in ('história', 'historia') else
                 f'humanities (category {cat}; not necessarily history)')
        for p in re.finditer(r'(?s)<p>\s*([^<]{0,40}?)\s*-\s*(<span>\s*Título.*?)</p>', sec):
            place, b = clean(p.group(1)), p.group(2)
            title = re.search(r'(?s)Título:\s*</span>.*?<strong>(.*?)</strong>', b)
            who = re.search(r'(?s)<span>\s*([A-Za-zçãéí]+\(a\)):\s*</span>\s*<strong>(.*?)</strong>', b)
            pub = re.search(r'(?s)Editora\(s\):\s*</span>\s*<strong>(.*?)</strong>', b)
            if not (title and who):
                continue
            role = who.group(1)
            names = []
            for n in [clean(x) for x in clean(who.group(2)).split(',')]:
                n2 = re.sub(r'\s*\((?:org|orgs|coord)\.?\)\s*$', '', n, flags=re.I)
                n2 = re.sub(r'^(?:Org|Orgs|Coord)\.\s*', '', n2)
                if n2:
                    names.append(n2)
            orgflag = bool(re.search(r'(?i)\((orgs?|coord)\.?\)|\b(orgs?|coord)\.\s', who.group(2))) or role == 'Organizador(a)'
            pl = re.match(r'(\d)º Lugar', place)
            notes = (['mention'] if re.search(r'(?i)menç', place) else []) + [f'place {pl.group(1)}' if pl else ('unranked winner' if 'Sem coloca' in place else 'placing: ' + place),
                     f'category: {cat}']
            if role != 'Autor(a)':
                notes.append('role: ' + ROLE_NOTE.get(role, role))
            elif orgflag:
                notes.append('role: editor (org)')
            for d in per_author([(names, dict(work_title=clean(title.group(1)), publisher=clean(pub.group(1)) if pub else ''))]):
                rows.append(row(JAB, 'BR', prize, field=field, honours='book', year=year, source_url=url,
                                note='; '.join(notes), **d))
    return rows


def jabuti_rows():
    rows = []
    idx = fetch('https://www.premiojabuti.com.br/jabuti/premiados-por-edicao/')
    years = sorted(set(re.findall(r'premiacao/\?ano=(\d{4})', idx or ''))) or [str(y) for y in range(1987, 2027)]
    if idx and not re.findall(r'premiacao/\?ano=(\d{4})', idx):
        years = sorted(set(re.findall(r'\n((?:19|20)\d\d)\n', text_of(idx)))) or years
    for y in years:
        rows += jabuti_page(f'https://www.premiojabuti.com.br/jabuti/premiados-por-edicao/premiacao/?ano={y}',
                            'Prêmio Jabuti', y)
    for yy in ('24', '25', '26'):
        rows += jabuti_page(f'https://www.premiojabuti.com.br/academico/premiados-por-edicao-academico/premiacao/?ano={yy}',
                            'Prêmio Jabuti Acadêmico', '20' + yy)
    return rows


# ---------------------------------------------------------------- MX: Premio Nacional (DOF acuerdos)

DOF_SEARCHES = [
    'https://dof.gob.mx/busqueda_detalle.php?vienede=avanzada&busqueda_cuerpo=C&BUSCAR_EN=T&textobusqueda=Premio+Nacional+de+Artes+y+Literatura&TIPO_TEXTO=Y&dfecha=01%2F01%2F2015&hfecha=12%2F11%2F2026&choosePeriodDate=D',
    'https://dof.gob.mx/busqueda_detalle.php?vienede=avanzada&busqueda_cuerpo=C&BUSCAR_EN=T&textobusqueda=Premio+Nacional+de+Ciencias+y+Artes&TIPO_TEXTO=Y&dfecha=01%2F01%2F1990&hfecha=31%2F12%2F2016&choosePeriodDate=D',
    'https://dof.gob.mx/busqueda_detalle.php?vienede=avanzada&busqueda_cuerpo=C&BUSCAR_EN=T&textobusqueda=Premio+Nacional+de+Ciencias+y+Artes&TIPO_TEXTO=Y&dfecha=01%2F01%2F1990&hfecha=31%2F12%2F2005&choosePeriodDate=D',
]
SUBFIELD = {'historia': 'history', 'ciencias sociales': 'social sciences', 'filosofía': 'philosophy'}


def dof_rows():
    rows, body = [], 'Gobierno de México (Diario Oficial de la Federación)'
    notas = {}
    for s in DOF_SEARCHES:
        if not fetch(s):
            continue
        raw = path_for(s).read_bytes().decode('latin-1')   # the search page is Latin-1
        for m in re.finditer(r'href="(/nota_detalle\.php\?codigo=(\d+)&fecha=[^"]*)"[^>]*><b><U>\s*Acuerdo por el que se '
                             r'otorga el (Premio Nacional de (?:Ciencias y Artes|Artes y Literatura)) (\d{4})', raw):
            notas[m.group(4)] = ('https://dof.gob.mx' + H.unescape(m.group(1)), m.group(3))
    for year, (url, prize) in sorted(notas.items()):
        h = fetch(url)
        if not h:
            continue
        t = text_of(h, main=False)
        i = t.find('PRIMERO')
        t = t[i if i > 0 else 0:]
        m = re.search(r'(?im)^(?:CAMPO\s+)?(?:III)?[.:\-\s]*Historia, Ciencias Sociales y Filosof[ií]a\.?\s*(?:,?\s*a:)?(.*)$', t)
        if not m:
            continue
        pnote = 'Campo III: Historia, Ciencias Sociales y Filosofía'
        lines = [m.group(1)] if m.group(1).strip() else []
        for ln in t[m.end():].split('\n'):
            if re.match(r'(?i)^(?:campo\s+)?(?:IV\b|Ciencias F[ií]sico|SEGUNDO|ART[IÍ]CULO SEGUNDO|TRANSITORIO)', ln.strip()):
                break
            lines.append(ln)
        sub = ''
        for ln in lines:
            ln = ln.strip()
            c = re.match(r'^Campo (Historia|Ciencias Sociales|Filosof[ií]a)\.?$', ln)
            if c:
                sub = c.group(1)
                continue
            ln = re.sub(r'^[-·•]\s*', '', ln)
            if not ln:
                continue
            why = ''
            w = re.match(r'^(.+?)\s*,\s*(por .*)$', ln)
            if w:
                ln, why = w.group(1), w.group(2)
            # new style may list several names on one line: 'X y a Y.'
            for n in re.split(r'\s*,?\s+y a\s+', ln):
                n = re.sub(r'(,\s*(y|e)|\.)\s*$', '', n.strip()).strip()
                notes = [pnote + (f' / Campo {sub}' if sub else '')]
                if re.search(r'(?i)\(p[óo]stumo\)', n):
                    n = re.sub(r'(?i)\s*\(p[óo]stumo\)', '', n)
                    notes.append('posthumous')
                if n.isupper() and len(n.split()) > 5:
                    notes.append('several names may be run together on this printed line')
                if why:
                    notes.append(why[:300])
                fld = SUBFIELD.get(sub.lower().replace('filosofia', 'filosofía'), 'history, social sciences and philosophy')
                rows.append(row(body, 'MX', prize, field=fld, honours='career', year=year, winner=n,
                                source_url=url, note='; '.join(notes)))
    return rows


# ---------------------------------------------------------------- MX: INAH Premio Francisco Javier Clavijero

INAH = 'Instituto Nacional de Antropología e Historia (INAH)'
CLAV = 'Premio Francisco Javier Clavijero'


def pdf_text(url, layout=False):
    if fetch(url, binary=True) is None:
        return ''
    args = ['pdftotext'] + (['-layout'] if layout else []) + [str(path_for(url)), '-']
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return ''


def inah_rows():
    rows = []
    url = 'https://inah.gob.mx/images/cartel/2024/20240805_ResultadosPremiosINAH.pdf'
    t = pdf_text(url)
    m = re.search(r'(?s)PREMIO FRANCISCO JAVIER CLAVIJERO\nHISTORIA Y ETNOHISTORIA\n(.*?)\nPREMIO [A-Z]', t)
    if m:
        txt = m.group(1)
        parts = re.split(r'\n((?:Premio|Mención)[^\n]*(?:\n(?:de |tesis|trabajo)[^\n]*)?)\n', '\n' + txt)
        # parts: ['', head, body, head, body...]
        for i in range(1, len(parts) - 1, 2):
            head = re.sub(r'\s+', ' ', parts[i]).strip()
            body = re.sub(r'\s+', ' ', parts[i + 1]).strip()
            honours = 'dissertation' if re.search(r'tesis de doctorado', head) else (
                'other')   # 'trabajo de investigación' = research work, not necessarily a book
            level = re.search(r'tesis de (doctorado|maestría|licenciatura)', head)
            for ent in re.split(r',? y para ', body):
                e = re.match(r'(.+?), por el trabajo (.+)$', ent.strip())
                if not e:
                    continue
                notes = []
                if head.startswith('Mención'):
                    notes.append('mention')
                notes.append('category: ' + head)
                if level and level.group(1) != 'doctorado':
                    notes.append(f'{level.group(1)} thesis')
                rows.append(row(INAH, 'MX', CLAV, field='history and ethnohistory',
                                honours=honours if not (level and level.group(1) != 'doctorado') else 'other',
                                year='2024', winner=e.group(1).strip(), work_title=e.group(2).strip().rstrip('.'),
                                source_url=url, note='; '.join(notes)))
    # 2023: press bulletin prose (names only)
    url = 'https://www.inah.gob.mx/images/boletines/2023/757/Boletin%20757.pdf'
    t = re.sub(r'\s+', ' ', pdf_text(url))
    m = re.search(r'El Premio Francisco Javier Clavijero, concedido a las mejores tesis en Historia y Etnohistoria,(.*?)'
                  r'En la rama de Lingüística', t)
    if m:
        s = m.group(1)
        spec = [  # (category, mention?, regex capturing names joined by ' y ')
            ('Premio al mejor trabajo de investigación', False, r'lo obtuvo como mejor investigación, ([^;]+);'),
            ('Mención honorífica, trabajo de investigación', True, r'la mención honorífica fue para ([^.]+)\. La mejor tesis'),
            ('Premio a la mejor tesis de doctorado', False, r'La mejor tesis de doctorado fue para (.+?) por su trabajo'),
            ('Mención honorífica, tesis de doctorado', True, r'las menciones honoríficas fueron para ([^.]+)\. El premio'),
            ('Premio compartido, tesis de maestría', False, r'tesis de maestría fue para ([^,]+), mientras'),
            ('Mención honorífica, tesis de maestría', True, r'la mención honorífica la obtuvo (.+?), por su trabajo'),
            ('Mención honorífica, tesis de maestría', True, r'carmelitas descalzos en la Nueva España, y (.+?), quien'),
            ('Premio a la mejor tesis de licenciatura', False, r'licenciatura se dio a ([^,]+), y la mención'),
            ('Mención honorífica, tesis de licenciatura', True, r'y la mención honorífica fue para ([^.]+)\.\s*$'),
        ]
        for cat, mention, rx in spec:
            mm = re.search(rx, s.strip())
            if not mm:
                continue
            names = [n.strip() for n in re.split(r'\s+y\s+', mm.group(1)) if n.strip()]
            level = re.search(r'tesis de (doctorado|maestría|licenciatura)', cat)
            for n in names:
                rows.append(row(INAH, 'MX', CLAV, field='history and ethnohistory',
                                honours='dissertation' if level and level.group(1) == 'doctorado' else (
                                    'book' if 'investigación' in cat else 'other'),
                                year='2023', winner=n, source_url=url,
                                note='; '.join(x for x in ['mention' if mention else '', 'category: ' + cat,
                                                           f'{level.group(1)} thesis' if level and level.group(1) != 'doctorado' else '',
                                                           'press bulletin; work titles not printed'] if x)))
    return rows


# ----------------------------------------------------------------

HARVESTERS = [af_rows, rvh_rows, vhd_rows, henkel_rows, kolleg_rows, muenster_rows, anpuh_rows, jabuti_rows, dof_rows,
              inah_rows]


def harvest():
    rows = []
    for f in HARVESTERS:
        try:
            got = f()
        except Exception as e:  # keep going; one body failing should not lose the others
            print(f.__name__, 'FAILED', type(e).__name__, e, file=sys.stderr)
            got = []
        rows += got
    seen, out = set(), []
    for r in rows:
        k = (r['prize_id'], r['year'], r['winner'], r['work_title'], r['note'])
        if k not in seen and r['winner']:
            seen.add(k)
            out.append(r)
    return out


if __name__ == '__main__':
    rows = harvest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps({c: r.get(c, '') for c in COLS}, ensure_ascii=False) + '\n')
    c = Counter((r['body'], r['prize']) for r in rows)
    for (b, p), n in sorted(c.items()):
        yrs = sorted(r['year'] for r in rows if r['body'] == b and r['prize'] == p and r['year'])
        print(f'{n:5d}  {b} | {p}  {yrs[0] + "-" + yrs[-1] if yrs else ""}')
    print(len(rows), 'rows ->', OUT)
