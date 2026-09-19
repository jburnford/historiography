#!/usr/bin/env python3
"""Keep all-era atlas matches and screen possible additions for life in/after 1900."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path
import re

try:
    from .export_wikidata_historians import write_csv, digest
except ImportError:
    from export_wikidata_historians import write_csv, digest

KNOWN_CALENDARS = {'Q1985727', 'Q1985786'}  # Gregorian and Julian.
RANKS = {'NormalRank': 'normal', 'PreferredRank': 'preferred', 'DeprecatedRank': 'deprecated'}


def screen_lifespan(dates, cutoff=1900, current_year=2026):
    """Conservative screening, not proof of scholarly activity or importance.

    A dated birth/death at or after the cutoff supplies positive evidence of life.
    A missing death never supplies such evidence. Alternatives that straddle the
    cutoff, coarse/uncertain dates, unknown calendars and impossible chronology
    remain review cases unless an independent usable date establishes inclusion.
    """
    years = {'P569': [], 'P570': []}
    nominal_years = {'P569': [], 'P570': []}
    uncertain = {'P569': False, 'P570': False}
    for row in dates:
        if row['rank'] == 'deprecated':
            continue
        prop = row['property']
        match = re.match(r'^([+-]?\d+)-', row['date'])
        year = int(match[1]) if match else None
        if year is not None and row['calendar'] in KNOWN_CALENDARS:
            nominal_years[prop].append(year)
        if year is not None and year > current_year:
            return 'date_review', 'future_date'
        if (year is None or row['precision'] < 9 or row['calendar'] not in KNOWN_CALENDARS
                or row.get('before', 0) != 0 or row.get('after', 0) != 0
                or (row['calendar'] == 'Q1985786' and year == cutoff - 1)):
            uncertain[prop] = True
        else:
            years[prop].append(year)
    birth, death = years['P569'], years['P570']
    if (nominal_years['P569'] and nominal_years['P570']
            and max(nominal_years['P569']) > min(nominal_years['P570'])):
        return 'date_review', 'birth_death_conflict'
    if birth and min(birth) >= cutoff and not uncertain['P569']:
        return 'living_1900_or_later', 'birth_at_or_after_cutoff'
    if death and min(death) >= cutoff and not uncertain['P570']:
        return 'living_1900_or_later', 'death_at_or_after_cutoff'
    if death and max(death) < cutoff and not uncertain['P570']:
        return 'died_before_1900', 'all_usable_death_dates_before_cutoff'
    if any(uncertain.values()):
        return 'date_review', 'imprecise_uncertain_or_calendar_boundary'
    if any(min(v) < cutoff <= max(v) for v in years.values() if v):
        return 'date_review', 'alternatives_straddle_cutoff'
    return 'date_review', 'missing_dates_or_earlier_birth_without_death'


def main(directory):
    import csv
    with gzip.open(directory / 'all-occupation-items.jsonl.gz', 'rt', encoding='utf-8') as handle:
        people = {row['qid']: row for row in map(json.loads, handle)}
    statements, date_rows = set(), defaultdict(list)
    items_per_property, statements_per_property = defaultdict(set), Counter()
    for path in sorted((directory / 'raw/date-pages').glob('*.json*')):
        payload = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())
        rows = payload['results']['bindings']
        if payload.get('meta', {}).get('result-size-total') != len(rows):
            raise ValueError(f'Incomplete date page: {path}')
        for row in rows:
            value = lambda k: row.get(k, {}).get('value')
            qid = value('person').rsplit('/', 1)[-1]
            if qid not in people:
                raise ValueError(f'Date query includes a new item outside saved membership: {qid}')
            statement = value('statement')
            if statement in statements:
                raise ValueError(f'Duplicate date statement: {statement}')
            statements.add(statement)
            prop = value('property').rsplit('/', 1)[-1]
            if prop not in ('P569', 'P570'):
                raise ValueError(f'Unexpected date property: {prop}')
            items_per_property[prop].add(qid)
            statements_per_property[prop] += 1
            date_rows[qid].append({
                'property': prop, 'statement_uri': statement,
                'rank': RANKS[value('rank').rsplit('#', 1)[-1]],
                'best_rank': value('bestRank') in ('true', '1'),
                'date': value('date'), 'precision': int(value('precision')),
                'calendar': value('calendar').rsplit('/', 1)[-1],
                'before': int(value('before') or 0), 'after': int(value('after') or 0),
            })
    expected = json.loads((directory / 'raw/date-counts.json').read_text())['results']['bindings']
    for row in expected:
        prop = row['property']['value'].rsplit('/', 1)[-1]
        if (len(items_per_property[prop]), statements_per_property[prop]) != (int(row['items']['value']), int(row['statements']['value'])):
            raise ValueError(f'Date coverage disagrees with count query: {prop}')

    with (directory / 'atlas-name-match-candidates.csv').open() as handle:
        matches = list(csv.DictReader(handle))
    matched = defaultdict(set)
    for row in matches:
        matched[row['qid']].add(row['person_id'])

    all_rows = []
    buckets = defaultdict(list)
    for person in people.values():
        qid = person['qid']
        dates = date_rows.get(qid, [])
        status, reason = screen_lifespan(dates)
        person['date_statements'] = dates
        person['date_screen'] = {'cutoff': 1900, 'status': status, 'reason': reason}
        person['atlas_person_match_candidates'] = sorted(matched[qid])
        if not person['has_non_deprecated_occupation']:
            continue
        def values(prop, key):
            return '|'.join(sorted({str(d[key]) for d in dates if d['property'] == prop and d['rank'] != 'deprecated'}))
        row = {
            'qid': qid, 'label': person['label'], 'label_language': person['label_language'],
            'description_en': person['description_en'], 'wikidata_url': person['url'],
            'birth_dates': values('P569', 'date'), 'death_dates': values('P570', 'date'),
            'birth_precisions': values('P569', 'precision'), 'death_precisions': values('P570', 'precision'),
            'date_screen': status, 'date_reason': reason,
            'atlas_person_match_candidates': '|'.join(sorted(matched[qid])),
            'identity_review_status': 'unreviewed_name_match' if matched[qid] else 'no_selected_label_match',
        }
        all_rows.append(row)
        buckets[status].append(row)
    columns = list(all_rows[0])
    write_csv(directory / 'historians-with-dates.csv', columns, all_rows)
    write_csv(directory / 'historians-living-1900-onward.csv', columns, buckets['living_1900_or_later'])
    write_csv(directory / 'new-candidates-1900-onward.csv', columns,
              [r for r in buckets['living_1900_or_later'] if not r['atlas_person_match_candidates']])
    write_csv(directory / 'date-review.csv', columns, buckets['date_review'])
    write_csv(directory / 'died-before-1900.csv', columns, buckets['died_before_1900'])
    enriched_matches = []
    for row in matches:
        person = people[row['qid']]
        enriched_matches.append({**row, 'date_screen': person['date_screen']['status'],
                                 'date_reason': person['date_screen']['reason']})
    write_csv(directory / 'atlas-matches-all-periods.csv', list(enriched_matches[0]), enriched_matches)
    with (directory / 'historians-with-date-evidence.jsonl.gz').open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8') as out:
                for person in people.values():
                    out.write(json.dumps(person, ensure_ascii=False, sort_keys=True) + '\n')
    outputs = ['historians-with-dates.csv', 'historians-living-1900-onward.csv',
               'new-candidates-1900-onward.csv', 'date-review.csv', 'died-before-1900.csv',
               'atlas-matches-all-periods.csv', 'historians-with-date-evidence.jsonl.gz']
    manifest = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'cutoff': 1900, 'current_year_for_future_date_checks': 2026,
        'instruction': 'Match existing atlas people across all periods; focus additions on historians living in or after 1900.',
        'date_statement_count': len(statements), 'date_counts_match_export': True,
        'date_statements_by_property': dict(statements_per_property),
        'items_with_date_by_property': {k: len(v) for k, v in items_per_property.items()},
        'non_deprecated_occupation_items': len(all_rows),
        'date_screen_counts': {k: len(v) for k, v in buckets.items()},
        'new_candidate_items_without_label_match': sum(not r['atlas_person_match_candidates'] for r in buckets['living_1900_or_later']),
        'all_periods_match_pairs': len(enriched_matches),
        'matched_atlas_people': len({r['person_id'] for r in matches}),
        'identity_status': 'Name candidates only; none are accepted identity reconciliations or additions.',
        'interpretation': 'Lifespan evidence only, not evidence of scholarly activity after 1900. Missing death is not treated as alive. Unknown/conflicting dates remain separate.',
        'input_sha256': {str(p.relative_to(directory)): digest(p) for p in sorted((directory / 'raw/date-pages').glob('*')) if p.is_file()},
        'date_counts_sha256': digest(directory / 'raw/date-counts.json'),
        'occupation_export_sha256': digest(directory / 'all-occupation-items.jsonl.gz'),
        'name_matches_sha256': digest(directory / 'atlas-name-match-candidates.csv'),
        'output_sha256': {name: digest(directory / name) for name in outputs},
    }
    (directory / 'date-filter-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if not k.endswith('sha256')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot_directory', type=Path)
    main(parser.parse_args().snapshot_directory)
