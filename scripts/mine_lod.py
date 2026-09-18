#!/usr/bin/env python3
"""Bounded, resumable LOD mining into source-observation staging. No atlas writes."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WD = 'http://www.wikidata.org/entity/'
WDT = 'http://www.wikidata.org/prop/direct/'
RDFS = 'http://www.w3.org/2000/01/rdf-schema#'
SKOS = 'http://www.w3.org/2004/02/skos/core#'
DC = 'http://purl.org/dc/elements/1.1/'
DCT = 'http://purl.org/dc/terms/'
ROLE = 'http://id.loc.gov/vocabulary/relators/'
PREFIX = '''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wikibase: <http://wikiba.se/ontology#>
'''
IPREFIX = '''PREFIX marcrel: <http://id.loc.gov/vocabulary/relators/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX bio: <http://purl.org/vocab/bio/0.1/>
'''


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def chunks(values, size):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def qid(uri):
    return uri.rsplit('/', 1)[-1]


def year_window(dates, start, end):
    """Never extract a year from a title or permissively parse a date range."""
    raw = set(dates)
    years = {int(d) for d in raw if re.fullmatch(r'[0-9]{4}', d)}
    recent = sorted(y for y in years if start <= y <= end)
    if not raw:
        return 'missing_date', []
    if len(years) != len(raw) or len(years) > 1:
        return ('ambiguous_date_with_recent_candidate' if recent else 'ambiguous_date'), recent
    return ('catalogued_year_in_window' if recent else 'outside_window'), recent


class Client:
    def __init__(self, run, offline, budget):
        self.run, self.offline, self.budget = run, offline, budget
        self.attempts = 0
        self.requests = {}

    def query(self, name, query, endpoint, limit):
        path = self.run / 'raw' / (name + '.json')
        query_path = self.run / 'queries' / (name + '.rq')
        if path.exists():
            package = json.loads(path.read_text())
            if package['query'] != query or package['endpoint'] != endpoint:
                raise ValueError(f'{name}: cache mismatch; use a new run directory')
        else:
            if self.offline:
                raise RuntimeError(f'{name}: offline snapshot missing')
            query_path.parent.mkdir(parents=True, exist_ok=True)
            query_path.write_text(query)
            package = None
            for attempt in range(2):
                if self.attempts >= self.budget:
                    raise RuntimeError('Network request budget reached; rerun to resume cached work')
                self.attempts += 1
                body = self.run / 'raw' / (name + '.pending')
                body.parent.mkdir(parents=True, exist_ok=True)
                cmd = ['curl', '-sS', '--max-time', '45', '--connect-timeout', '15',
                       '-H', 'Accept: application/sparql-results+json',
                       '-H', 'User-Agent: HistoriographyLODResearch/0.1', '--get',
                       '--data-urlencode', 'query@' + str(query_path),
                       '-o', str(body), '-w', '%{http_code}']
                if endpoint.endswith('idref.fr/sparql'):
                    cmd += ['--data-urlencode', 'format=json']
                result = subprocess.run(cmd + [endpoint], capture_output=True, text=True)
                status = result.stdout.strip()
                if result.returncode == 0 and status == '200':
                    response = json.loads(body.read_text())
                    if 'bindings' not in response.get('results', {}):
                        raise ValueError(f'{name}: unexpected SPARQL result')
                    package = {'endpoint': endpoint, 'query': query,
                               'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                               'response': response}
                    write(path, package)
                    body.unlink()
                    break
                with (self.run / 'attempts.jsonl').open('a') as log:
                    log.write(json.dumps({'query': name, 'http_status': status,
                                          'curl_exit': result.returncode, 'error': result.stderr,
                                          'at': dt.datetime.now(dt.timezone.utc).isoformat()}) + '\n')
                if status not in ('429', '500', '502', '503', '504', '000'):
                    break
                if attempt == 0:
                    time.sleep(2)
            if package is None:
                raise RuntimeError(f'{name}: query failed ({status}); successful requests are cached')
        query_path.parent.mkdir(parents=True, exist_ok=True)
        query_path.write_text(query)
        rows = package['response']['results']['bindings']
        self.requests[name] = {'id': name, 'endpoint': endpoint,
                               'retrieved_at': package['retrieved_at'], 'rows': len(rows),
                               'row_limit': limit, 'cap_reached': len(rows) >= limit,
                               'snapshot': str(path.relative_to(self.run)),
                               'sha256': digest(path.read_bytes()),
                               'query_file': str(query_path.relative_to(self.run))}
        write(self.run / 'manifest.json', list(self.requests.values()))
        if len(rows) >= limit:
            raise RuntimeError(f'{name}: row cap reached; split query before claiming completeness')
        print(f'{name}: {len(rows)} rows', flush=True)
        return rows


def discovery_query(fields, adjacent, limit):
    values = ' '.join('wd:' + q for q in fields)
    extra = '?person wdt:P106 wd:Q201788 .' if adjacent else ''
    # Keep this text identical to the four seeded discovery snapshots.
    return PREFIX + '''SELECT DISTINCT ?person ?field ?occupation ?route ?label WHERE {
 VALUES ?field { ''' + values + ''' }
 { ?person wdt:P101 ?field . BIND("field_of_work" AS ?route) }
 UNION { ?person wdt:P106 ?occupation . ?occupation wdt:P425 ?field . BIND("occupation_field" AS ?route) }
 ?person wdt:P31 wd:Q5 . ''' + extra + '''
 OPTIONAL { ?person rdfs:label ?label FILTER(LANG(?label)="en") }
} ORDER BY ?person ?field ?occupation ?route LIMIT ''' + str(limit)


def choose_authors(people, plan):
    selections = {}
    for theme, cohorts in plan['themes'].items():
        eligible = [q for q, p in people.items()
                    if p['identifiers'].get('P269') and set(p['cohorts']) & set(cohorts)]
        controls = [q for q, c in plan['controls'].items()
                    if c['theme'] == theme and people[q]['identifiers'].get('P269')]
        ordered = sorted(set(eligible) - set(controls),
                         key=lambda q: digest((plan['selection_seed'] + ':' + q).encode()))
        selections[theme] = controls + ordered[:max(0, plan['authors_per_theme'] - len(controls))]
    return selections


def identity_flags(person, authority_record, linked_people):
    """Conservative review flags; absence of a flag never accepts a match."""
    flags = []
    if not authority_record.get('labels'):
        flags.append('authority_label_missing')
    if len(linked_people) > 1:
        flags.append('authority_shared_by_wikidata_items')
    if len(person['identifiers'].get('P269', [])) > 1:
        flags.append('multiple_idref_identifiers_on_wikidata_item')
    def years(values):
        return {m.group(1) for value in values
                if (m := re.match(r'^\+?([0-9]{4})(?:-|$)', value))}
    wikidata_births = years(person.get('birth_values', []))
    idref_births = years(authority_record.get('birth_values', []))
    if wikidata_births and idref_births and not (wikidata_births & idref_births):
        flags.append('birth_year_conflict')
    return flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=ROOT / 'data/lod-mining/2026-09-18-pilot-complete')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    run = args.run.resolve()
    run.mkdir(parents=True, exist_ok=True)
    plan = json.loads((ROOT / 'lod-mining-plan.json').read_text())
    inputs = {f: digest((ROOT / f).read_bytes()) for f in
              ['historiography-1920-2000.json', 'data/people-wikidata.json', 'lod-mining-plan.json']}
    config = run / 'inputs.json'
    if config.exists() and json.loads(config.read_text()) != inputs:
        raise ValueError('Input changed: use a new run directory')
    write(config, inputs)
    client = Client(run, args.offline, plan['request_budget'])
    limit = plan['row_limit']
    people, observations = {}, {}

    def person(q):
        return people.setdefault(q, {'qid': q, 'label': '', 'cohorts': [], 'discoveries': [],
                                     'identifiers': {}, 'field_of_work': [], 'occupations': [],
                                     'birth_values': [], 'death_values': [], 'atlas_matches': []})

    def observe(s, p, obj, request):
        obj = {k: v for k, v in obj.items() if k in ('type', 'value', 'datatype', 'xml:lang')}
        key = digest(json.dumps([s, p, obj], sort_keys=True).encode())[:24]
        obs = observations.setdefault(key, {'id': key, 'subject': s, 'predicate': p,
                                            'object': obj, 'basis': 'source_observation',
                                            'review_status': 'unreviewed', 'source_requests': []})
        if request not in obs['source_requests']:
            obs['source_requests'].append(request)

    for name, fields in plan['discovery_fields'].items():
        req = 'mine_' + name
        rows = client.query(req, discovery_query(fields, name == 'gender_adjacent', limit),
                            'https://qlever.dev/api/wikidata', limit)
        for r in rows:
            q = qid(r['person']['value']); p = person(q)
            if name not in p['cohorts']:
                p['cohorts'].append(name)
            p['label'] = r.get('label', {}).get('value', p['label'])
            p['discoveries'].append({'cohort': name, 'field': r['field']['value'],
                                     'route': r['route']['value'],
                                     'occupation': r.get('occupation', {}).get('value'), 'request': req})
            if r['route']['value'] == 'field_of_work':
                observe(WD+q, WDT+'P101', r['field'], req)
            else:
                observe(WD+q, WDT+'P106', r['occupation'], req)
                observe(r['occupation']['value'], WDT+'P425', r['field'], req)

    grounded = json.loads((ROOT / 'data/people-wikidata.json').read_text())
    for row in grounded['people']:
        if row['status'] == 'accepted' and row.get('wikidata'):
            p = person(row['wikidata']['qid'])
            p['atlas_matches'].append({'person_id': row['person_id'], 'status': 'inherited_reviewed_match',
                                       'source': 'data/people-wikidata.json'})
            p['label'] = p['label'] or row['label']
    for q, control in plan['controls'].items():
        person(q)['control'] = control
        person(q)['label'] = person(q)['label'] or control['label']
    properties = ' '.join('wdt:' + p for p in
                          ['P269','P227','P268','P214','P244','P213','P101','P106','P569','P570'])
    for number, group in enumerate(chunks(sorted(people), 30)):
        req = f'people_{number:03}'
        query = PREFIX + '''SELECT ?person ?prop ?value ?label ?defaultLabel WHERE {
 VALUES ?person { ''' + ' '.join('wd:'+q for q in group) + ''' }
 VALUES ?prop { ''' + properties + ''' } ?person ?prop ?value .
 OPTIONAL { ?person rdfs:label ?label FILTER(LANG(?label)="en") }
 OPTIONAL { ?person rdfs:label ?defaultLabel FILTER(LANG(?defaultLabel)="mul") }
} ORDER BY ?person ?prop ?value LIMIT ''' + str(limit)
        for r in client.query(req, query, 'https://qlever.dev/api/wikidata', limit):
            p = person(qid(r['person']['value'])); prop = qid(r['prop']['value']); value = r['value']['value']
            p['label'] = r.get('label', r.get('defaultLabel', {})).get('value', p['label'])
            target = (p['field_of_work'] if prop == 'P101' else p['occupations'] if prop == 'P106'
                      else p['birth_values'] if prop == 'P569' else p['death_values'] if prop == 'P570'
                      else p['identifiers'].setdefault(prop, []))
            if value not in target:
                target.append(value)
            observe(r['person']['value'], r['prop']['value'], r['value'], req)
    write(run/'people.json', sorted(people.values(), key=lambda p: p['qid']))

    selections = choose_authors(people, plan)
    selected = sorted({q for group in selections.values() for q in group})
    authority_people = {}
    for q in selected:
        for identifier in people[q]['identifiers'].get('P269', []):
            if not re.fullmatch(r'[0-9]{8}[0-9X]', identifier):
                raise ValueError(f'Unexpected IdRef identifier: {identifier}')
            authority_people.setdefault('http://www.idref.fr/'+identifier+'/id', []).append(q)
    write(run/'selection.json', {'themes': selections, 'distinct_people': selected,
                                 'authority_to_candidate_qids': authority_people,
                                 'method': 'controls then stable SHA-256 ordering; not representative; identifiers unreviewed'})
    resources, authority_records = {}, {}
    # The IdRef Virtuoso service permits at most 10,000 sorted result rows.
    idref_limit = min(limit, 9999)
    roles = ' '.join('marcrel:'+r for r in plan['bibliographic_roles'])
    for number, group in enumerate(chunks(sorted(authority_people), 8)):
        values = ' '.join('<'+uri+'>' for uri in group)
        req = f'idref_identity_{number:03}'
        query = IPREFIX + '''SELECT ?authority ?label ?birth WHERE { VALUES ?authority { '''+values+''' }
 ?authority skos:prefLabel ?label . OPTIONAL { ?authority bio:event ?event . ?event a bio:Birth; bio:date ?birth }
} ORDER BY ?authority ?label ?birth LIMIT '''+str(idref_limit)
        for r in client.query(req, query, 'https://data.idref.fr/sparql', idref_limit):
            authority = r['authority']['value']
            a = authority_records.setdefault(authority, {'uri': authority, 'labels': [], 'birth_values': []})
            if r['label']['value'] not in a['labels']:
                a['labels'].append(r['label']['value'])
            if 'birth' in r and r['birth']['value'] not in a['birth_values']:
                a['birth_values'].append(r['birth']['value'])
            observe(authority, SKOS+'prefLabel', r['label'], req)
        req = f'idref_bibliography_{number:03}'
        query = IPREFIX + '''SELECT DISTINCT ?authority ?doc ?role ?date ?citation WHERE {
 VALUES ?authority { '''+values+''' } VALUES ?role { '''+roles+''' }
 ?doc ?role ?authority . FILTER(STRSTARTS(STR(?doc),"http://www.sudoc.fr/") || STRSTARTS(STR(?doc),"https://www.sudoc.fr/"))
 OPTIONAL { ?doc dc:date ?date } OPTIONAL { ?doc dct:bibliographicCitation ?citation }
} ORDER BY ?authority ?doc ?role ?date ?citation LIMIT '''+str(idref_limit)
        for r in client.query(req, query, 'https://data.idref.fr/sparql', idref_limit):
            uri = r['doc']['value']
            d = resources.setdefault(uri, {'uri': uri, 'entity_status': 'bibliographic_resource_not_resolved_work',
                                          'dates': [], 'citations': [], 'contributions': [], 'subjects': []})
            contribution = {'authority': r['authority']['value'], 'role': r['role']['value']}
            if contribution not in d['contributions']:
                d['contributions'].append(contribution)
            observe(uri, r['role']['value'], r['authority'], req)
            for field, dest, prop in [('date','dates',DC+'date'),('citation','citations',DCT+'bibliographicCitation')]:
                if field in r:
                    if r[field]['value'] not in d[dest]:
                        d[dest].append(r[field]['value'])
                    observe(uri, prop, r[field], req)

    recent = []
    for d in resources.values():
        d['date_status'], d['window_years'] = year_window(d['dates'], plan['start_year'], plan['end_year'])
        if d['window_years']:
            recent.append(d['uri'])
    subjects = {}
    for number, group in enumerate(chunks(sorted(recent), 35)):
        req = f'idref_subjects_{number:03}'
        query = IPREFIX + '''SELECT DISTINCT ?doc ?subject ?label WHERE {
 VALUES ?doc { '''+' '.join('<'+u+'>' for u in group)+''' } ?doc dct:subject ?subject .
 OPTIONAL { ?subject skos:prefLabel ?label }
} ORDER BY ?doc ?subject ?label LIMIT '''+str(idref_limit)
        for r in client.query(req, query, 'https://data.idref.fr/sparql', idref_limit):
            uri, subject = r['doc']['value'], r['subject']['value']
            if subject not in resources[uri]['subjects']:
                resources[uri]['subjects'].append(subject)
            s = subjects.setdefault(subject, {'uri': subject, 'labels': []})
            if 'label' in r and r['label']['value'] not in s['labels']:
                s['labels'].append(r['label']['value'])
                observe(subject, SKOS+'prefLabel', r['label'], req)
            observe(uri, DCT+'subject', r['subject'], req)

    write(run/'authority-records.json', sorted(authority_records.values(), key=lambda r:r['uri']))
    # Compare against every harvested QID, not only the sampled people.
    all_authority_people = {}
    for q, p in people.items():
        for identifier in p['identifiers'].get('P269', []):
            all_authority_people.setdefault('http://www.idref.fr/'+identifier+'/id', []).append(q)
    identity_review = []
    for authority, candidates in authority_people.items():
        record = authority_records.get(authority, {})
        for q in candidates:
            identity_review.append({'qid':q, 'wikidata_label':people[q]['label'],
                'authority':authority, 'authority_labels':record.get('labels', []),
                'wikidata_birth_values':people[q]['birth_values'], 'authority_birth_values':record.get('birth_values', []),
                'review_status':'needs_review',
                'flags':identity_flags(people[q], record, all_authority_people[authority])})
    write(run/'identity-review.json', identity_review)
    write(run/'bibliographic-resources.json', sorted(resources.values(), key=lambda d:d['uri']))
    write(run/'subjects.json', sorted(subjects.values(), key=lambda s:s['uri']))
    write(run/'observations.json', {'schema':'lod-source-observations-0.1', 'status':'staging_unreviewed',
                                   'identity_policy':'No IdRef person is merged with a Wikidata person by this export.',
                                   'manifest':'manifest.json', 'statements':sorted(observations.values(), key=lambda o:o['id'])})
    with (run/'recent-resources.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['uri','date_status','window_years','dates','citation','candidate_people','contributions','subject_labels'])
        writer.writeheader()
        for uri in sorted(recent):
            d = resources[uri]
            candidates = sorted({q for c in d['contributions'] for q in authority_people[c['authority']]})
            writer.writerow({'uri':uri, 'date_status':d['date_status'], 'window_years':'; '.join(map(str,d['window_years'])),
                             'dates':'; '.join(d['dates']), 'citation':' | '.join(d['citations']),
                             'candidate_people':'; '.join(people[q]['label'] or q for q in candidates),
                             'contributions':'; '.join(c['authority']+' '+qid(c['role']) for c in d['contributions']),
                             'subject_labels':'; '.join(' / '.join(subjects[s]['labels']) or s for s in d['subjects'])})
    known_authorities = set(authority_records)
    summary = {'completed_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'status':'staging; no accepted atlas changes',
               'discovered_people':sum(bool(p['cohorts']) for p in people.values()), 'people_including_baseline_and_controls':len(people),
               'cohort_counts':{c:sum(c in p['cohorts'] for p in people.values()) for c in plan['discovery_fields']},
               'authority_coverage':{prop:sum(bool(p['identifiers'].get(prop)) for p in people.values()) for prop in ['P269','P227','P268','P214','P244']},
               'sampled_people':len(selected), 'sampled_authorities':len(authority_people),
               'authority_labels_retrieved':len(known_authorities), 'authority_labels_missing':sorted(set(authority_people)-known_authorities),
               'shared_selected_authorities':{a:qs for a,qs in authority_people.items() if len(qs)>1},
               'identity_links_flagged':sum(bool(r['flags']) for r in identity_review),
               'identity_birth_conflicts':sum('birth_year_conflict' in r['flags'] for r in identity_review),
               'bibliographic_resources_all_years':len(resources), 'recent_resources_including_ambiguous':len(recent),
               'recent_resources_exact_single_year':sum(d['date_status']=='catalogued_year_in_window' for d in resources.values()),
               'date_status_counts':{s:sum(d['date_status']==s for d in resources.values()) for s in sorted({d['date_status'] for d in resources.values()})},
               'recent_resources_with_subjects':sum(bool(resources[u]['subjects']) for u in recent),
               'distinct_recent_subjects':len(subjects), 'observations':len(observations), 'successful_queries':len(client.requests),
               'network_attempts_this_invocation':client.attempts, 'limits':plan['limits']}
    for filename, expected in inputs.items():
        if digest((ROOT/filename).read_bytes()) != expected:
            raise RuntimeError('Protected input changed during harvest: '+filename)
    summary['protected_input_hashes_unchanged'] = True
    write(run/'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
