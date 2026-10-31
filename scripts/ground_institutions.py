#!/usr/bin/env python3
"""Ground institution names to ROR (PID-PLAN.md section 3 and rollout step 5).

Institutions appear as free text across the project. This script gathers every distinct name from:
- the dissertation graph's awarding institutions (committed `dissertations.csv` and `doctorates.json`;
  `base:` repository hosts are not institutions and are skipped);
- the historian positions table (`data/field-research/historian-positions-2026-10-29/positions.csv`:
  ORCID employment, IHR Teachers of History, AHA advisors and directory, Wikidata P108).

Each name is matched with ROR's affiliation matcher (api.ror.org/v2, `affiliation=`), with a country hint
where the source gives one (IHR lists are UK universities; dissertations carry a country). The record is
then read from the local ROR data dump for its status, country and Wikidata QID.

Candidates are first limited to the countries the source allows (IHR: GB; AHA advisor and directory: US
and CA; a dissertation: its country). IHR lists name a university by its town ('Edinburgh', 'East
Anglia', 'Oxford Brookes'), so for IHR names without an institution word the script also asks for
'University of X' and 'X University' and keeps the best allowed candidate. A match is `accepted` when ROR
marks it `chosen`, or when its score is at least 0.9 and beats the next allowed candidate by 0.05.
Everything else is `review`. An accepted match must also contain the name: every distinctive word of the
source name (after dropping department words such as 'Dept.', 'History', 'School') must appear in one of
the ROR record's names or its city, otherwise it goes to review ('Manchester Metropolitan' is not the
University of Manchester; 'Dept. of History University of Lancaster' is not Lancaster City Council).
Oxford and Cambridge colleges ('Peterhouse University of Cambridge') are accepted as the university: identity
evidence is kept at university level, and the college stays in the source string. Hand decisions in
OUT/reviewed.csv (string, ror, basis; ror empty = no institution) override both, and a later run keeps them.

    python3 scripts/ground_institutions.py --ror /mnt/e/ror/v2.15-2026-10-20/v2.15-2026-10-20-ror-data.csv \\
        --cache /mnt/e/ror/api-cache --out data/field-research/institutions-2026-10-31
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISS = 'data/field-research/dissertation-citations-2026-10-11'
POSITIONS = ROOT / 'data/field-research/historian-positions-2026-10-29/positions.csv'
API = 'https://api.ror.org/v2/organizations?affiliation='
UA = 'HistoriographyResearch/1.0 (jic823@usask.ca; institution grounding)'

# The dissertation graph's own slugs for Canadian and US harvests, as the repositories name the university.
BARE = {
    'alabama': 'University of Alabama', 'alberta': 'University of Alberta', 'arkansas': 'University of Arkansas',
    'calgary': 'University of Calgary', 'carleton': 'Carleton University', 'concordia': 'Concordia University',
    'dalhousie': 'Dalhousie University', 'duke': 'Duke University', 'florida': 'University of Florida',
    'guelph': 'University of Guelph', 'harvard': 'Harvard University', 'johnshopkins': 'Johns Hopkins University',
    'kentucky': 'University of Kentucky', 'laurier': 'Wilfrid Laurier University', 'laval': 'Université Laval',
    'lsu': 'Louisiana State University', 'manitoba': 'University of Manitoba', 'maryland': 'University of Maryland, College Park',
    'mcgill': 'McGill University', 'mcmaster': 'McMaster University', 'memorial': 'Memorial University of Newfoundland',
    'michigan': 'University of Michigan', 'minnesota': 'University of Minnesota', 'montreal': 'Université de Montréal',
    'nebraska': 'University of Nebraska–Lincoln', 'newmexico': 'University of New Mexico', 'oklahoma': 'University of Oklahoma',
    'ottawa': 'University of Ottawa', 'penn': 'University of Pennsylvania', 'queens': "Queen's University",
    'rice': 'Rice University', 'sfu': 'Simon Fraser University', 'sherbrooke': 'Université de Sherbrooke',
    'smu': 'Southern Methodist University', 'southcarolina': 'University of South Carolina', 'stanford': 'Stanford University',
    'tennessee': 'University of Tennessee, Knoxville', 'toronto': 'University of Toronto', 'ubc': 'University of British Columbia',
    'ucberkeley': 'University of California, Berkeley', 'ucdavis': 'University of California, Davis',
    'ucirvine': 'University of California, Irvine', 'ucla': 'University of California, Los Angeles',
    'ucriverside': 'University of California, Riverside', 'ucsantacruz': 'University of California, Santa Cruz',
    'ucsb': 'University of California, Santa Barbara', 'ucsd': 'University of California, San Diego',
    'unb': 'University of New Brunswick', 'unc': 'University of North Carolina at Chapel Hill',
    'uqam': 'Université du Québec à Montréal', 'usask': 'University of Saskatchewan', 'uvic': 'University of Victoria',
    'vanderbilt': 'Vanderbilt University', 'virginia': 'University of Virginia', 'washington': 'University of Washington',
    'waterloo': 'University of Waterloo', 'western': 'Western University', 'wisconsinmadison': 'University of Wisconsin–Madison',
    'yale': 'Yale University', 'york': 'York University',
}
COUNTRY = {'CA': 'CA', 'US': 'US', 'GB': 'GB', 'FR': 'FR'}
ALLOWED = {'ihr': {'GB'}, 'aha_advisor': {'US', 'CA'}, 'aha_directory': {'US', 'CA'}}
INSTITUTION_WORD = re.compile(r'\b(univ|university|college|school|institute|academy|polytechnic|centre|center)', re.I)


def git_text(path, rev='HEAD'):
    return subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def query_form(name, source):
    """The string sent to ROR: IHR's 'London: University College' reads 'University College London'."""
    s = name.strip()
    if source == 'ihr' and ': ' in s:
        city, _, rest = s.partition(': ')
        s = f'{rest} {city}' if city not in rest else rest
    return s


def gather():
    """{(name, source_family): dict(rows, country, slugs)} for every institution name in the inputs."""
    names = defaultdict(lambda: dict(rows=0, countries=Counter(), slugs=set(), sources=Counter()))
    rows = list(csv.DictReader(git_text(f'{DISS}/dissertations.csv').splitlines()))
    awarding = {}
    for r in json.loads(git_text(f'{DISS}/doctorates.json')):
        if r.get('awarding_institution'):
            awarding.setdefault(r['institution'], r['awarding_institution'])
    for r in rows:
        slug = r['institution']
        if slug.startswith('base:'):
            continue
        name = BARE.get(slug) or awarding.get(slug)
        if not name:
            continue
        n = names[name]
        n['rows'] += 1
        n['countries'][COUNTRY.get(r['country'], '')] += 1
        if slug.startswith('fr:'):
            n['open'] = True            # theses.fr co-tutelles name foreign universities ('Università degli studi (Bologne, Italie)')
        else:
            n.setdefault('allowed', set()).update({COUNTRY[r['country']]} if r['country'] in COUNTRY else set())
        n['awarding'] = True
        n['slugs'].add(slug)
        n.setdefault('diss_slugs', set()).add(slug)
        n['sources']['dissertation'] += 1
    with POSITIONS.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if not r['institution'].strip():
                continue
            n = names[query_form(r['institution'], r['source'])]
            n['rows'] += 1
            n['countries']['GB' if r['source'] == 'ihr' else ''] += 1
            n.setdefault('allowed', set()).update(ALLOWED.get(r['source'], set()))
            if r['source'] not in ALLOWED:
                n['open'] = True        # ORCID and Wikidata posts can be anywhere
            n['sources'][r['source']] += 1
            n['slugs'].add(f"{r['source']}:{r['institution']}")
    return names


GENERIC = {'dept', 'department', 'depts', 'of', 'the', 'and', 'history', 'historical', 'studies', 'school', 'schools',
           'faculty', 'program', 'programme', 'phd', 'division', 'graduate', 'in', 'at', 'for', 'de', 'des', 'du', 'la',
           'le', 'et', 'd', 'l', 'archaeology', 'classics', 'arts', 'humanities', 'social', 'sciences', 'science',
           'politics', 'economic', 'international', 'relations', 'american', 'culture', 'cultures', 'religion', 'area',
           'interdisciplinary', 'committee', 'on', 'civilization', 'civilizations', 'heritage', 'research'}
ABBREV = {'univ': 'university', 'coll': 'college', 'inst': 'institute', 'st': 'saint', 'ste': 'sainte', 'u': 'university',
          'mt': 'mount', 'tech': 'technology', 'natl': 'national', 'intl': 'international', 'cuny': 'cuny'}


SOFT = {'nj', 'ny', 'can', 'canada', 'usa', 'uk', 'england', 'ohio', 'texas', 'california', 'florida', 'virginia',
        'carolina', 'north', 'south', 'west', 'east', 'new', 'york', 'jersey', 'pennsylvania', 'pa', 'mass', 'calif',
        'ont', 'ontario', 'quebec', 'que', 'bc', 'london', 'ga', 'tenn', 'ky', 'md', 'wash', 'mich', 'ill', 'ind',
        'wis', 'minn', 'mo', 'la', 'conn', 'va', 'nc', 'sc', 'fla', 'okla', 'ariz', 'colo', 'ore', 'kans', 'neb'}
DEPT = re.compile(r'\b(dept|department|school of|faculty of|program|programme|committee|centre for|center for|'
                  r'division of|graduate (dept|program|group|school)|history (dept|department)|subject areas?)\b', re.I)


def segments(name):
    """The institution part of a name: comma segments naming a department are dropped ('Univ. of Virginia,
    Corcoran Dept. of History' -> 'Univ. of Virginia'); in 'Royal Holloway Dept. of History University of
    London' the part before the department ('Royal Holloway') is kept as its own form."""
    parts = [x for x in re.split(r',\s*', name) if x and not DEPT.search(x)]
    forms = [', '.join(parts)] if parts else []
    m = DEPT.search(name)
    if m and ',' not in name[:m.start()]:
        head = name[:m.start()].strip(' ,&')
        tail = re.search(r'\b(university|college)\b.*$', name[m.end():], re.I)
        forms += ([head] if head else []) + ([tail.group(0)] if tail else [])
    return [f for f in dict.fromkeys(forms) if f]


def expand(t):
    """AHA's abbreviations written out: 'Univ.', 'Coll.', 'Inst.', 'St.' (as 'State' only after a name)."""
    t = re.sub(r'\bUniv\.?(?=\W|$)', 'University', t)
    t = re.sub(r'\bColl\.?(?=\W|$)', 'College', t)
    t = re.sub(r'\bInst\.?(?=\W|$)', 'Institute', t)
    return re.sub(r'(?<=[a-z]) St\. Univ', ' State Univ', t)


def tokens(t):
    t = re.sub(r'[\u2010-\u2015\u2212/-]', ' ', t or '')
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    out = set()
    for w in re.findall(r'[a-z0-9]+', t):
        w = ABBREV.get(w, w)
        out.add('saint' if w == 'st' else w)
    return out


def contains(name, rec):
    """Every distinctive word of the source name appears in a ROR name of the record or its city. Department
    segments are left out, and place tags ('NJ', 'Ohio', 'Can.') may be missing."""
    forms = segments(name) or [name]
    bare = re.sub(r'\((?:ComUE|\d{4}\s*-\s*(?:\d{4}|\.\.\.)?)\)', '', forms[0])     # '(ComUE)', '(2018-2021)'
    need = tokens(bare) - GENERIC - SOFT
    have = set().union(*(tokens(x) for x in rec.get('names', []) + [rec.get('city', '')]))
    return need <= have


def load_ror(path):
    out = {}
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[r['id']] = dict(name=r['names.types.ror_display'], country=r['locations.geonames_details.country_code'],
                                status=r['status'], wikidata=(r['external_ids.type.wikidata.preferred'] or
                                                              r['external_ids.type.wikidata.all'].split(';')[0]).strip(),
                                types=r['types'], city=r['locations.geonames_details.name'],
                                names=[re.sub(r'^[a-z]{2,3}: ', '', x.strip()) for col in
                                       ('names.types.ror_display', 'names.types.label', 'names.types.alias',
                                        'names.types.acronym') for x in r[col].split(';') if x.strip()])
    return out


def fetch(cache, url, state):
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + '.json')
    if path.exists():
        return json.loads(path.read_text())
    time.sleep(max(0.0, 0.3 - (time.monotonic() - state['last'])))
    for attempt in range(5):
        state['last'] = time.monotonic()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                body = json.loads(r.read())
            path.write_text(json.dumps(body))
            return body
        except Exception:                       # 429 or network: stand back and retry
            time.sleep(15 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ror', type=Path, required=True, help='ROR data dump CSV (v2)')
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    ror = load_ror(args.ror)
    by_display = {(r['name'], r['country']): k for k, r in ror.items() if r['status'] == 'active'}
    reviewed = {}
    if (args.out / 'reviewed.csv').exists():
        with (args.out / 'reviewed.csv').open(newline='', encoding='utf-8') as f:
            reviewed = {r['string']: r for r in csv.DictReader(f)}
    names = gather()
    state, out, stats = {'last': 0.0}, [], Counter()
    for i, (name, n) in enumerate(sorted(names.items(), key=lambda x: -x[1]['rows']), 1):
        hint = next((c for c, _ in n['countries'].most_common() if c), '')
        allowed = set() if n.get('open') else n.get('allowed', set())
        forms = [name] + [f for f in segments(name) if f != name]
        forms += [x for x in (expand(f) for f in list(forms)) if x not in forms]   # 'Yale Univ.' -> 'Yale University'
        if n['sources'].get('ihr') and not INSTITUTION_WORD.search(name):
            forms += [f'University of {name}', f'{name} University']
        items = []
        for form in forms:
            body = fetch(args.cache, API + urllib.parse.quote(form), state)
            items += (body or {}).get('items', [])
        best = {}
        for it in items:                    # best score per organisation across the forms tried
            org = it['organization']['id']
            if org not in best or (it['chosen'], it['score']) > (best[org]['chosen'], best[org]['score']):
                best[org] = it
        cands = sorted(best.values(), key=lambda it: (-it['chosen'], -it['score']))
        if allowed:
            cands = [it for it in cands if ror.get(it['organization']['id'], {}).get('country') in allowed]
        if n.get('awarding'):           # a degree-granting institution, not a CNRS regional office ('Délégation Paris 11')
            cands = [it for it in cands if 'education' in ror.get(it['organization']['id'], {}).get('types', '')]
        named = [it for it in cands if contains(name, ror.get(it['organization']['id'], {}))]
        top = (named or cands or [None])[0]
        rest = [it for it in (named or cands)[1:] if it is not top]
        second = rest[0]['score'] if rest else 0.0
        row = dict(string=name, rows=n['rows'], sources=' '.join(f'{s}={c}' for s, c in n['sources'].most_common()),
                   country_hint=' '.join(sorted(allowed)) or hint, slugs=' | '.join(sorted(n['slugs']))[:500],
                   diss_slugs=' '.join(sorted(n.get('diss_slugs', ()))), ror='',
                   ror_name='', ror_country='', wikidata='', score='', chosen='', decision='no_match', basis='')
        if top:
            org = top['organization']['id']
            rec = ror.get(org, {})
            row.update(ror=org, ror_name=rec.get('name', ''), ror_country=rec.get('country', ''),
                       wikidata=rec.get('wikidata', ''), score=round(top['score'], 3), chosen=top['chosen'])
            if rec.get('status') != 'active':
                row.update(decision='review', basis=f"ROR record {rec.get('status', 'missing')}")
            elif not contains(name, rec):
                row.update(decision='review', basis=f'name not contained; score {top["score"]:.2f}')
            elif top['chosen'] or (top['score'] >= 0.9 and top['score'] - second >= 0.05):
                row.update(decision='accepted', basis='chosen' if top['chosen'] else f'score {top["score"]:.2f}, next {second:.2f}')
            else:
                row.update(decision='review', basis=f'score {top["score"]:.2f}, next {second:.2f}')
        oxbridge = re.search(r'\bUniversity of (Oxford|Cambridge)$', name)
        if row['decision'] != 'accepted' and oxbridge and name != oxbridge.group(0):
            org = by_display[(oxbridge.group(0), 'GB')]
            rec = ror[org]
            row.update(ror=org, ror_name=rec['name'], ror_country='GB', wikidata=rec['wikidata'], decision='accepted',
                       basis='college or faculty of the university: identity evidence is kept at university level')
        if name in reviewed:
            h = reviewed[name]
            rec = ror.get(h['ror'], {})
            row.update(ror=h['ror'], ror_name=rec.get('name', ''), ror_country=rec.get('country', ''),
                       wikidata=rec.get('wikidata', ''), decision='reviewed' if h['ror'] else 'reviewed_none',
                       basis=h['basis'])
        stats[row['decision']] += 1
        out.append(row)
        if i % 250 == 0:
            print(f'{i}/{len(names)} names, {dict(stats)}', flush=True)
    with (args.out / 'institution-strings.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    inst = defaultdict(lambda: dict(rows=0, strings=0))
    for r in out:
        if r['decision'] in ('accepted', 'reviewed'):
            d = inst[r['ror']]
            d.update(name=r['ror_name'], country=r['ror_country'], wikidata=r['wikidata'])
            d['rows'] += r['rows']
            d['strings'] += 1
    with (args.out / 'institutions.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ror', 'name', 'country', 'wikidata', 'strings', 'rows'])
        for k, d in sorted(inst.items(), key=lambda x: -x[1]['rows']):
            w.writerow([k, d['name'], d['country'], d['wikidata'], d['strings'], d['rows']])
    rows_by = Counter()
    for r in out:
        rows_by[r['decision']] += r['rows']
    summary = dict(names=len(out), decisions=dict(stats), rows_by_decision=dict(rows_by), institutions=len(inst),
                   ror_dump=str(args.ror.name))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
