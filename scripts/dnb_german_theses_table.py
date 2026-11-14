#!/usr/bin/env python3
"""Build the tracked metadata table of DNB History dissertations, degree years 2000-2027
(stage 1 of the German thesis harvest, 2026-11-14). Metadata only, no text.

Input: records.jsonl from dnb_history_diss_parse.py over the SRU pages pulled by
dnb_history_diss_pilot.py (publication years 2000-2027). DNB catalogue data are CC0 1.0.

Steps:
- keep records whose degree year (MARC 502 $d, else the year in 502 $a) is 2000-2027; records with
  no degree year are kept on their publication year and flagged ``year_basis=pub``;
- merge print/online editions (MARC 776 $w pointing at another record in the pull); the work is
  represented by its online record when it has one (that is where the links are);
- History screen of the 2026-11-14 pilot (SCOPE.md section 3), as a confidence column, nothing
  dropped:
    high   - DNB subject group 940 or 943 on the record (any edition), no archaeology/theology flag
    medium - another 9xx group or a 9xx DDC number (900, 950-990, 930 with other groups)
    low    - '930 alone' (930 the only group: ancient world and archaeology); 'no 9xx visible' (the 1,520-type records
             that match only through the sgt index); or a title with an archaeology/theology term
- degree country from the 502 place (DE, AT, CH, other:<place>, unknown); foreign degrees kept;
- degree type: diss / habil / other (habilitations are kept in the table, not downloaded);
- free links: 856 fields flagged 'kostenfrei'; when the flag carries no URL, the record's resolver
  links (URN, handle) stand in;
- held: matched to a thesis we already hold (doctorates.json, countries DE/AT/CH) by surname plus
  title prefix, or by the same repository URL/handle/URN;
- route class: from hosts.csv (german_theses_fetch.py hosts) and, for resolver links, from the
  resolution cache the download job writes.

Usage:
  python3 -I scripts/dnb_german_theses_table.py RECORDS.jsonl OUT_DIR [--fetch-dir /mnt/e/german-theses-2026-11-14]
"""
import argparse
import collections
import csv
import gzip
import json
import pathlib
import re
import sys
import unicodedata
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCTORATES = ROOT / 'data/field-research/dissertation-citations-2026-10-11/doctorates.json'

AT = re.compile(r"Wien|Vienna|Graz|Innsbruck|Salzburg|Klagenfurt|Linz\b", re.I)
CH = re.compile(r"Zürich|Zurich|Bern\b|Basel|Luzern|St\. ?Gallen|Genève|Genf|Lausanne|Neuchâtel|Fribourg|Freiburg \(Schweiz\)|Freiburg/Schweiz|Freiburg, Schweiz|Freiburg i\. ?Üe", re.I)
OTHER = re.compile(r"Paris|London|Oxford|Cambridge|Leiden|Amsterdam|Utrecht|Groningen|Wrocław|Warszawa|Kraków|Praha|Prag\b|Firenze|Florenz|Fiesole|European University Institute|Roma\b|Rom\b|Bologna|Leuven|Löwen|Gent\b|Bruxelles|Brüssel|Luxembourg|Luxemburg|Tōkyō|Tokyo|Helsinki|Uppsala|Lund\b|Kopenhagen|København|Budapest|Ljubljana|Bratislava|Brno|Tartu|Riga|Vilnius|Istanbul|Jerusalem|Tel Aviv|New York|Chicago|Toronto|Strasbourg|Straßburg|Lyon|Madrid|Barcelona|Sevilla|Lisboa|Wageningen|Nijmegen|Maastricht|Trento|Bolzano|Bozen|Liechtenstein|Olomouc|Poznań|Toruń|Łódź|Moskva|Moskau|Sankt-Peterburg|Kyiv|Kiew|Aarhus|Oslo|Stockholm|Göteborg|Bergen\b|Dublin|Edinburgh|Glasgow|Manchester|Princeton|Harvard|Yale|Berkeley|Los Angeles|Sorbonne|EHESS|Bruges|Brugge|Antwerpen|Rotterdam|Tilburg|Sheffield|Warwick|Nottingham|St Andrews|Durham|Bristol", re.I)
ARCH = re.compile(r"arch[aä]olog|ausgrabung|grabung|pr[aä]histor|vorgeschicht|fr[üu]hgeschicht|bronzezeit|eisenzeit|neolith|pal[aä]olith|mesolith|latènezeit|latenezeit|hallstatt|keramik|gr[aä]berfeld|siedlungsgrabung|excavation|archaeolog", re.I)
THEO = re.compile(r"theolog|exeges|exeget|dogmat|liturg|neutestament|alttestament|homiletik|evangelium|ekklesiolog|christolog|pneumatolog", re.I)
RESOLVER_HOSTS = {'nbn-resolving.org', 'nbn-resolving.de', 'hdl.handle.net', 'dx.doi.org', 'doi.org', ''}


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def host_of(url):
    return urllib.parse.urlparse(url).netloc.lower()


def degree_country(place):
    if not place:
        return 'unknown'
    if AT.search(place):
        return 'AT'
    if CH.search(place):
        return 'CH'
    m = OTHER.search(place)
    if m:
        return 'other:' + m.group(0)
    return 'DE'


def degree_type(r):
    t = (r.get('diss_type') or r.get('diss_note') or '').lower()
    if 'habil' in t:
        return 'habil'
    if 'diss' in t or 'doktor' in t or 'phd' in t or 'ph. d' in t or 'thesis' in t or 'promotion' in t:
        return 'diss'
    return 'diss?' if not t else 'other'


def year_of(r):
    d = r.get('degree_year') or ''
    m = re.search(r'(19|20)\d\d', d)
    if not m and r.get('diss_note'):
        m = re.search(r'(19|20)\d\d', r['diss_note'])
    if m:
        return int(m.group(0)), 'degree'
    try:
        return int(r.get('year_pub')), 'pub'
    except (TypeError, ValueError):
        return None, 'none'


def groups(r):
    return {g.strip()[:3] for g in r.get('sachgruppe') or [] if g.strip()}


def confidence(recs):
    sg = set().union(*(groups(r) for r in recs))
    ddc = {d.strip()[:1] for r in recs for d in r.get('ddc') or [] if d.strip()}
    title = ' '.join((r.get('title') or '') + ' ' + (r.get('subtitle') or '') for r in recs)
    nine = {g for g in sg if g.startswith('9')}
    flags = []
    if ARCH.search(title):
        flags.append('archaeology term')
    if THEO.search(title):
        flags.append('theology term')
    if nine & {'940', '943'}:
        level, why = 'high', 'subject group 940/943'
    elif nine and nine != {'930'}:
        level, why = 'medium', 'other 9xx group ' + '/'.join(sorted(nine))
    elif nine == {'930'} and sg != {'930'}:
        level, why = 'medium', '930 with other groups ' + '/'.join(sorted(sg))
    elif sg == {'930'}:
        level, why = 'low', '930 alone (ancient world/archaeology)'
    elif '9' in ddc:
        level, why = 'medium', 'DDC 9xx, no 9xx subject group'
    else:
        level, why = 'low', 'no 9xx visible (sgt index match only)'
    if flags and level != 'low':
        level = 'low'
    return level, '; '.join([why] + flags)


def free_links(r):
    """Free links in record order: 856 'kostenfrei' URLs; if the flag has no URL, the resolver links."""
    out = [u['u'] for u in r['urls'] if u.get('z') == 'kostenfrei' and u.get('u')]
    if not out and any(u.get('z') == 'kostenfrei' for u in r['urls']):
        out = [u['u'] for u in r['urls'] if u.get('x') == 'Resolving-System' and u.get('u')]
    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            res.append(u)
    return res


def norm_link(u):
    u = u.lower().strip().rstrip('/')
    u = re.sub(r'^https?://', '', u)
    m = re.search(r'(urn:nbn:[a-z0-9:\-./]+)', u)
    if m:
        return m.group(1)
    m = re.search(r'(?:hdl\.handle\.net/|/handle/)(\d[\d.]*/[^/?#]+)', u)
    if m:
        return 'hdl:' + m.group(1)
    return u


def held_index():
    """Theses we hold (doctorates.json, DE/AT/CH): surname|title prefix keys and link keys."""
    data = json.loads(DOCTORATES.read_text())
    keys, links = {}, {}
    for d in data:
        if not isinstance(d, dict) or d.get('country') not in ('DE', 'AT', 'CH'):
            continue
        sur = fold((d.get('authors') or [''])[0].split(',')[0]).split()
        tk = fold(d.get('title'))[:30]
        if sur and tk:
            keys[sur[-1] + '|' + tk] = d['id']
        for u in [d.get('item_url'), d.get('cluster_id')] + list(d.get('identifiers') or []):
            if isinstance(u, str) and u:
                links[norm_link(u)] = d['id']
    return keys, links


def load_hosts(path):
    if not path.exists():
        return {}
    with path.open(newline='') as f:
        return {r['host']: r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('records')
    ap.add_argument('out', type=pathlib.Path)
    ap.add_argument('--fetch-dir', type=pathlib.Path, default=pathlib.Path('/mnt/e/german-theses-2026-11-14'))
    ap.add_argument('--from-year', type=int, default=2000)
    ap.add_argument('--to-year', type=int, default=2027)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    recs = {}
    for line in open(a.records, encoding='utf-8'):
        r = json.loads(line)
        recs.setdefault(r['id'], r)
    par = {i: i for i in recs}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for r in recs.values():
        for x in r['related']:
            for w in x['w']:
                if w.startswith('(DE-101)') and w[8:] in recs:
                    par[find(r['id'])] = find(w[8:])
    works = collections.defaultdict(list)
    for i in recs:
        works[find(i)].append(recs[i])
    hosts = load_hosts(a.out / 'hosts.csv')
    resolved = {}
    rc = a.fetch_dir / 'resolved.json'
    if rc.exists():
        resolved = json.loads(rc.read_text())
    held_keys, held_links = held_index()

    rows = []
    for group in works.values():
        group.sort(key=lambda r: (r.get('media') != 'c', not free_links(r), r['id']))
        rep = group[0]
        years = [year_of(r) for r in group]
        y, basis = next((yb for yb in years if yb[1] == 'degree'), None) or \
            min((yb for yb in years if yb[0]), default=(None, 'none'))
        if y is None or not (a.from_year <= y <= a.to_year):
            continue
        level, why = confidence(group)
        univ = next((r.get('univ') or r.get('diss_note') for r in group if r.get('univ') or r.get('diss_note')), '')
        links = []
        for r in group:
            links += [u for u in free_links(r) if u not in links]
        pdf_links = {u['u'] for r in group for u in r['urls'] if u.get('q') == 'application/pdf' and u.get('z') == 'kostenfrei'}
        # host of the first free link, through the resolver cache when it is a resolver link
        host, final = '', ''
        for u in links:
            h = host_of(u)
            if h in RESOLVER_HOSTS:
                t = resolved.get(u) or ''
                if t:
                    final, host = t, host_of(t)
                    break
                if not host:
                    host = 'resolver:' + (h or 'none')
            else:
                final, host = u, h
                break
        hrow = hosts.get(host, {})
        route = hrow.get('class', 'B' if not host.startswith('resolver:') else 'resolver-unresolved') if links else ''
        sur = fold((rep.get('author') or '').split(',')[0]).split()
        tk = fold(rep.get('title'))[:30]
        held = held_keys.get((sur[-1] if sur else '') + '|' + tk, '')
        if not held:
            for u in links + [x['u'] for r in group for x in r['urls'] if x.get('x') == 'Resolving-System']:
                if norm_link(u) in held_links:
                    held = held_links[norm_link(u)]
                    break
        sups = []
        for r in group:
            for s in r['supervisors']:
                v = s['name'] + (f" [{s['gnd']}]" if s['gnd'] else '')
                if v not in sups:
                    sups.append(v)
        rows.append({
            'dnb_id': rep['id'],
            'other_edition_ids': '|'.join(r['id'] for r in group[1:]),
            'author': rep.get('author', ''),
            'author_gnd': rep.get('author_gnd') or next((r.get('author_gnd') for r in group if r.get('author_gnd')), ''),
            'title': (rep.get('title') or '') + (' : ' + rep['subtitle'] if rep.get('subtitle') else ''),
            'university': univ,
            'degree_country': degree_country(univ),
            'degree_type': degree_type(rep),
            'degree_year': y,
            'year_basis': basis,
            'pub_year': rep.get('year_pub', ''),
            'language': '|'.join(rep.get('lang') or [rep.get('lang008', '')]),
            'subject_groups': '|'.join(sorted(set().union(*(groups(r) for r in group)))),
            'confidence': level,
            'confidence_reason': why,
            'urn': next((r.get('urn') for r in group if r.get('urn')), ''),
            'doi': next((r.get('doi') for r in group if r.get('doi')), ''),
            'supervisors': '|'.join(sups),
            'free_links': ' '.join(links),
            'free_link_is_pdf': 'yes' if pdf_links & set(links) else '',
            'host': host,
            'resolved_link': final if final and final not in links else '',
            'route_class': route,
            'held_id': held,
        })
    rows.sort(key=lambda r: (r['degree_year'], r['dnb_id']))
    # same author and title on two works not linked by MARC 776 (e.g. a corrected second online
    # version): keep the first (the one with a free link), mark the rest
    first_of = {}
    for r in sorted(rows, key=lambda r: (not r['free_links'], r['dnb_id'])):
        k = (fold(r['author']), fold(r['title'])[:60])
        r['duplicate_of'] = first_of.get(k, '') if k[0] and k[1] else ''
        first_of.setdefault(k, r['dnb_id'])
    path = a.out / 'theses.csv.gz'
    with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    c = collections.Counter
    summary = {
        'works': len(rows),
        'catalogue_records': len(recs),
        'by_confidence': dict(c(r['confidence'] for r in rows)),
        'by_degree_type': dict(c(r['degree_type'] for r in rows)),
        'by_degree_country': dict(c(r['degree_country'] if not r['degree_country'].startswith('other') else 'other' for r in rows)),
        'by_year_basis': dict(c(r['year_basis'] for r in rows)),
        'with_free_link': sum(1 for r in rows if r['free_links']),
        'free_link_by_confidence': dict(c(r['confidence'] for r in rows if r['free_links'])),
        'free_link_by_route_class': dict(c(r['route_class'] for r in rows if r['free_links'])),
        'held_already': sum(1 for r in rows if r['held_id']),
        'same_author_title_duplicates': sum(1 for r in rows if r['duplicate_of']),
        'per_degree_year': dict(sorted(c(r['degree_year'] for r in rows).items())),
    }
    (a.out / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
