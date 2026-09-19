#!/usr/bin/env python3
"""Rebuild a transparent discovery ranking from saved QLever results (offline).

This does not assign identities, accept field edges, or edit the curated atlas.
Scores measure available discovery evidence, not historical merit.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PROPERTIES = ('P101', 'P1343', 'P166', 'P39', 'P463', 'P800')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    if not path.exists() and Path(str(path) + '.gz').exists():
        path = Path(str(path) + '.gz')
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def bindings(path):
    data = read_json(path)
    rows = data['results']['bindings']
    if len(rows) != data['meta']['result-size-total']:
        raise ValueError(f'Incomplete response: {path}')
    return [{k: v['value'] for k, v in row.items()} for row in rows]


def pages(raw, pattern):
    return sorted(set(list(raw.glob(pattern + '.json')) + list(raw.glob(pattern + '.json.gz'))))


def qid(uri):
    if uri.startswith('http://www.wikidata.org/.well-known/genid/'):
        return uri  # Wikidata somevalue: retain, but never award evidence points.
    result = uri.rsplit('/', 1)[-1]
    if not re.fullmatch(r'Q\d+', result):
        raise ValueError(f'Unexpected entity: {uri}')
    return result


def csv_rows(path):
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, columns=None):
    columns = columns or list(rows[0])
    if path.suffix == '.gz':
        with path.open('wb') as output:
            with gzip.GzipFile(filename='', fileobj=output, mode='wb', mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as handle:
                    writer = csv.DictWriter(handle, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
        return
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def score_components(wikipedia, recognition, references, works):
    """Diminishing returns; absence earns no evidence points, not a negative score."""
    if min(wikipedia, recognition, references, works) < 0:
        raise ValueError('Counts must be nonnegative')
    return {
        'wikipedia_score': 65 * math.log1p(min(wikipedia, 50)) / math.log(51),
        'recognition_score': 15 * math.log1p(min(recognition, 3)) / math.log(4),
        'reference_score': 10 * math.log1p(min(references, 2)) / math.log(3),
        'works_score': 10 * math.log1p(min(works, 3)) / math.log(4),
    }


def ranked(rows):
    ordered = sorted(rows, key=lambda r: (-r['score'], -r['wikipedia_editions'],
                                        r['label'].casefold(), int(r['qid'][1:])))
    previous = None
    rank = 0
    for index, row in enumerate(ordered, 1):
        if row['score'] != previous:
            rank = index
        previous = row['score']
        row = dict(row)
        row['rank'] = rank
        yield {'rank': row.pop('rank'), **row}


def load(directory):
    raw = directory / 'raw'
    objects = {}
    for path in pages(raw, 'objects-*') + pages(raw, 'metadata-*') + pages(raw, 'context-*'):
        for item in bindings(path):
            key = qid(item.pop('object'))
            old = objects.setdefault(key, {})
            for field, value in item.items():
                # A live label update is retained in the later supplemental capture.
                old[field] = value
    signals = defaultdict(lambda: defaultdict(set))
    counts, people_per_property = Counter(), defaultdict(set)
    expected = {r['property'].rsplit('/', 1)[-1]: (int(r['people']), int(r['rows']))
                for r in bindings(raw / 'signal-counts-after.json')}
    for prop in PROPERTIES:
        files = ([raw / 'references-full.json'] if prop == 'P1343'
                 else pages(raw, prop + '-??'))
        for path in files:
            for item in bindings(path):
                person, obj = qid(item['person']), qid(item['object'])
                if item['property'].rsplit('/', 1)[-1] != prop:
                    raise ValueError(f'Property mismatch: {path}')
                if obj in signals[person][prop]:
                    raise ValueError(f'Duplicate signal: {person} {prop} {obj}')
                if obj not in objects:
                    raise ValueError(f'Missing object metadata: {obj}')
                signals[person][prop].add(obj)
                counts[prop] += 1
                people_per_property[prop].add(person)
        if prop != 'P1343' and (len(people_per_property[prop]), counts[prop]) != expected[prop]:
            raise ValueError(f'Counts disagree for {prop}')
    # P1343 was captured again in ONE unpaginated query because the live index
    # changed during OFFSET paging. Its response metadata verifies full length.
    articles = {}
    article_total = 0
    all_urls = set()
    for path in pages(raw, 'wikipedia-??'):
        for item in bindings(path):
            person = qid(item['person'])
            if person in articles:
                raise ValueError(f'Duplicate Wikipedia person: {person}')
            urls = sorted(set(item['articles'].split('|')))
            sites = [urlsplit(url).hostname for url in urls]
            if any(not re.fullmatch(r'[^.]+\.wikipedia\.org', site or '') for site in sites):
                raise ValueError('Non-Wikipedia sitelink')
            if len(sites) != len(set(sites)) or len(urls) != int(item['articleCount']):
                raise ValueError('Repeated edition or incorrect article count')
            if all_urls.intersection(urls):
                raise ValueError('Article assigned to multiple items')
            all_urls.update(urls)
            articles[person] = urls
            article_total += len(urls)
    wiki_expected = bindings(raw / 'wikipedia-counts.json')[0]
    if (len(articles), article_total) != (int(wiki_expected['people']), int(wiki_expected['articles'])):
        raise ValueError('Wikipedia totals do not reconcile')
    return objects, signals, articles, dict(counts)


def main(snapshot):
    directory = snapshot / 'ranking'
    objects, signals, articles, counts = load(directory)
    catalog = read_json(directory / 'signal-catalog.json')
    selected = {(r['property'], r['qid']): r for r in catalog['decisions'] if r['selected']}
    people = csv_rows(snapshot / 'historians-with-dates.csv')
    snapshot_ids = {r['qid'] for r in people}
    candidates = {r['qid'] for r in csv_rows(snapshot / 'new-candidates-1900-onward.csv')}
    rows, evidence = [], []
    usage = Counter()
    def label(key):
        obj = objects[key]
        return obj.get('label') or obj.get('labelMul') or key
    def labels(keys):
        return ' | '.join(f'{label(key)} [{key}]' for key in sorted(keys, key=lambda k: (label(k).casefold(), k)))
    for person in people:
        key = person['qid']
        traits = signals[key]
        urls = articles.get(key, [])
        recognition = {(selected[(prop, obj)]['family'])
                       for prop in ('P166', 'P39', 'P463') for obj in traits[prop]
                       if (prop, obj) in selected}
        references = {selected[('P1343', obj)]['family'] for obj in traits['P1343']
                      if ('P1343', obj) in selected}
        works = {selected[('P800', obj)]['family'] for obj in traits['P800']
                 if ('P800', obj) in selected}
        components = score_components(len(urls), len(recognition), len(references), len(works))
        selected_traits = {prop: sorted(obj for obj in traits[prop] if (prop, obj) in selected)
                           for prop in ('P166', 'P39', 'P463', 'P1343', 'P800')}
        preferred = next((url for url in urls if urlsplit(url).hostname == 'en.wikipedia.org'),
                         urls[0] if urls else '')
        selected_recognition = set().union(*(set(selected_traits[prop]) for prop in ('P166', 'P39', 'P463')))
        field_history = any(re.search(r'histor|histoire|geschichte|medieval|archaeolog',
                                     label(obj), re.I) for obj in traits['P101'])
        description_history = bool(re.search(r'historian|historiograph', person['description_en'], re.I))
        history_basis = []
        if works:
            history_basis.append('historical_work_metadata')
        if any('history_' in selected[(prop, obj)]['basis'] or 'historical_' in selected[(prop, obj)]['basis']
               for prop in ('P166', 'P39', 'P463') for obj in selected_traits[prop]):
            history_basis.append('historical_recognition_metadata')
        if field_history:
            history_basis.append('field_metadata')
        if description_history:
            history_basis.append('english_description')
        row = {
            'score': round(sum(components.values()), 6),
            **{k: round(v, 6) for k, v in components.items()},
            **person,
            'wikipedia_editions': len(urls), 'wikipedia_url': preferred,
            'wikipedia_languages': '|'.join(sorted(urlsplit(url).hostname.split('.')[0] for url in urls)),
            'recognition_families': len(recognition), 'reference_families': len(references),
            'historical_work_families': len(works),
            'recognition_evidence': labels(selected_recognition),
            'reference_evidence': labels(selected_traits['P1343']),
            'historical_work_evidence': labels(selected_traits['P800']),
            'field_of_work_leads': labels(traits['P101']),
            'all_award_items': len(traits['P166']), 'all_position_items': len(traits['P39']),
            'all_membership_items': len(traits['P463']), 'all_reference_items': len(traits['P1343']),
            'all_notable_work_items': len(traits['P800']),
            'non_wikipedia_scholarly_evidence': 'yes' if works or selected_recognition or references else 'not_established_by_screen',
            'history_relevance_screen': 'history_metadata_present' if history_basis else 'occupation_only_requires_review',
            'history_relevance_basis': '|'.join(history_basis),
            'description_review_flag': ('historian_not_explicit_in_english_description'
                                        if not re.search(r'historian|historiograph', person['description_en'], re.I) else ''),
            'score_status': 'discovery_priority_v1_metadata_screened',
        }
        rows.append(row)
        evidence.append({'qid': key, 'wikipedia_articles': urls,
                         'signals': {p: sorted(traits[p]) for p in PROPERTIES},
                         'selected_signals': selected_traits,
                         'recognition_families': sorted(recognition),
                         'reference_families': sorted(references), 'work_families': sorted(works)})
        for prop in PROPERTIES:
            for obj in traits[prop]:
                usage[(prop, obj)] += 1
    all_ranked = list(ranked(rows))
    additions = list(ranked([r for r in rows if r['qid'] in candidates]))
    matches = list(ranked([r for r in rows if r['atlas_person_match_candidates']]))
    dated = list(ranked([r for r in rows if r['date_screen'] == 'living_1900_or_later']))
    if {r['qid'] for r in additions} != candidates:
        raise ValueError('Candidate population changed')
    write_csv(directory / 'ranked-candidates.csv', additions)
    write_csv(directory / 'ranked-top-1000.csv', additions[:1000])
    supported = list(ranked([r for r in rows if r['qid'] in candidates and r['history_relevance_screen'] == 'history_metadata_present']))
    write_csv(directory / 'ranked-history-supported.csv.gz', supported)
    write_csv(directory / 'ranked-all-periods.csv.gz', all_ranked)
    write_csv(directory / 'ranked-existing-match-leads.csv', matches)
    columns = list(additions[0])
    write_csv(directory / 'ranked-date-review.csv.gz', list(ranked([r for r in rows if r['date_screen'] == 'date_review'])), columns)
    # Self-contained evidence accompanies CSVs without inflating every row with all URLs.
    with (directory / 'ranking-evidence.jsonl.gz').open('wb') as output:
        with gzip.GzipFile(filename='', fileobj=output, mode='wb', mtime=0) as handle:
            for row in sorted(evidence, key=lambda r: int(r['qid'][1:])):
                handle.write((json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n').encode())
    flat_links = [{'qid': r['qid'], 'language': urlsplit(url).hostname.split('.')[0], 'article_url': url}
                  for r in additions for url in articles.get(r['qid'], [])]
    write_csv(directory / 'candidate-wikipedia-articles.csv', flat_links,
              ['qid', 'language', 'article_url'])
    catalog_rows = []
    for decision in catalog['decisions']:
        prop, obj = decision['property'], decision['qid']
        catalog_rows.append({**decision, 'label': label(obj), 'description': objects[obj].get('description', ''),
                             'people_in_saved_inventory': usage[(prop, obj)]})
    write_csv(directory / 'signal-catalog.csv', catalog_rows)
    overview = {
        'weights': {'wikipedia': 65, 'recognition': 15, 'references': 10, 'works': 10},
        'scope': 'existing saved non-deprecated exact historian occupation inventory',
        'all_period_people': len(rows), 'date_qualified': len(dated), 'new_candidates': len(additions),
        'matched_qids_all_periods': len(matches),
        'candidate_signal_coverage': {name: sum(r[col] > 0 for r in additions) for name, col in
                                      [('wikipedia', 'wikipedia_editions'), ('recognition', 'recognition_families'),
                                       ('references', 'reference_families'), ('works', 'historical_work_families')]},
        'candidate_nonzero_scores': sum(r['score'] > 0 for r in additions),
        'candidate_all_four_signals': sum(all(r[k] > 0 for k in ('wikipedia_editions', 'recognition_families', 'reference_families', 'historical_work_families')) for r in additions),
        'candidate_history_metadata_present': len(supported),
        'candidate_wikipedia_thresholds': {str(n): sum(r['wikipedia_editions'] >= n for r in additions) for n in (1, 2, 5, 10, 20, 50)},
        'matched_date_qualified_wikipedia_thresholds': {str(n): sum(r['wikipedia_editions'] >= n for r in matches if r['date_screen'] == 'living_1900_or_later') for n in (0, 1, 2, 5, 10)},
        'matched_date_qualified_count': sum(r['date_screen'] == 'living_1900_or_later' for r in matches),
        'extracted_signal_counts': counts,
        'incidental_live_items_outside_saved_population': sorted((set(signals) | set(articles)) - snapshot_ids),
        'selected_catalog_items': Counter(r['property'] for r in catalog['decisions'] if r['selected']),
        'diagnostic_people': {r['qid']: {k: r[k] for k in ('rank','label','score','wikipedia_editions','recognition_score','reference_score','works_score')}
                              for r in additions if r['qid'] in ('Q107085771', 'Q5075487')},
    }
    (directory / 'summary.json').write_text(json.dumps(overview, ensure_ascii=False, indent=2) + '\n')
    md = ['# Ranked historian candidates', '',
          'Discovery priority, not a judgment of scholarly merit. All candidates have date evidence of life in or after 1900.',
          'Possible matches to existing atlas people are set aside for identity review. Historical field edges remain unverified.', '',
          'Weights: Wikipedia 65; recognition 15; reference coverage 10; historical-work metadata 10. See README.md for formulas and limitations.', '',
          '| Rank | Historian | Score | Wikipedia editions | Recognition | References | Works | History relevance |',
          '| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in additions[:100]:
        name = r['label'].replace('|', '\\|').replace('[', '\\[').replace(']', '\\]')
        review = 'Additional metadata' if r['history_relevance_screen'] == 'history_metadata_present' else '**Occupation needs review**'
        md.append(f"| {r['rank']} | [{name}]({r['wikipedia_url'] or r['wikidata_url']}) | {r['score']:.2f} | {r['wikipedia_editions']} | {r['recognition_score']:.2f} | {r['reference_score']:.2f} | {r['works_score']:.2f} | {review} |")
    (directory / 'TOP-100.md').write_text('\n'.join(md) + '\n')
    outputs = ['ranked-candidates.csv', 'ranked-top-1000.csv', 'ranked-all-periods.csv.gz',
               'ranked-existing-match-leads.csv', 'ranked-date-review.csv.gz', 'ranking-evidence.jsonl.gz',
               'candidate-wikipedia-articles.csv', 'signal-catalog.csv', 'summary.json', 'TOP-100.md', 'ranked-history-supported.csv.gz']
    inputs = [snapshot / name for name in ('historians-with-dates.csv', 'new-candidates-1900-onward.csv')]
    inputs += [directory / 'signal-catalog.json', directory / 'catalog-overrides.json'] + sorted(directory.glob('raw/*.json*')) + sorted(directory.glob('raw/*.rq'))
    manifest = {'version': 1, 'endpoint': 'https://qlever.dev/api/wikidata', 'retrieval_date': '2026-09-17',
                'live_index_warning': 'Requests are separate captures, not a transactional snapshot. P1343 uses the later complete unpaginated capture.',
                'script_sha256': sha(Path(__file__)),
                'catalog_script_sha256': sha(ROOT / 'scripts/build_historian_signal_catalog.py'),
                'atlas_sha256': sha(ROOT / 'historiography-1920-2000.json'),
                'inputs_sha256': {str(p.relative_to(snapshot)): sha(p) for p in inputs},
                'outputs_sha256': {name: sha(directory / name) for name in outputs}}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(overview, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    main(parser.parse_args().snapshot)
