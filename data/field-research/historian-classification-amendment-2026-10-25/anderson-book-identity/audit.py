#!/usr/bin/env python3
"""Reproduce the read-only frozen-release Anderson title-family audit."""
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RELEASE = ROOT / 'data/field-research/dissertation-citations-2026-10-11/release/2026-10-23'
PERSON = 'anderson|benedict r'
MAIN = 'W:anderson|imagined communities'
EUROPE = set('AT BE BG CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LI LT LU LV MC ME MK MT NL NO PL PT RO RS SE SI SK UA'.split())

def region(country):
    return country if country in {'CA', 'US'} else 'EUROPE' if country in EUROPE else 'OTHER'

def read(name):
    with gzip.open(RELEASE / (name + '.csv.gz'), 'rt', newline='') as handle:
        return list(csv.DictReader(handle))

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = dict(line.split('  ', 1)[::-1] for line in (RELEASE / 'SHA256SUMS').read_text().splitlines())
    checked_files = ['works.csv.gz', 'citations.csv.gz', 'dissertations.csv.gz', 'people.csv.gz', 'authorship.csv.gz', 'work-translations.csv']
    hashes = {name: sha(RELEASE / name) for name in checked_files}
    assert all(hashes[name] == manifest[name] for name in hashes), 'Frozen release checksum mismatch'
    works = [w for w in read('works') if w['first_author_key'] == PERSON]
    review = json.loads((HERE / 'decisions.json').read_text())
    decisions = review['decisions']
    assert len(works) == len(decisions) == 57
    assert [d['raw_record'] for d in decisions] == works, 'A raw work row or its ordering changed'
    assert len({d['work_id'] for d in decisions}) == 57
    sources = {s['id'] for s in json.loads((HERE / 'sources.json').read_text())['sources']}
    assert all(set(d['source_ids']) <= sources for d in decisions)
    assert all(d['assigned_to_book_union'] == (d['classification'] == 'imagined_communities_confirmed') for d in decisions)
    dissertations = {d['dissertation_id']: d for d in read('dissertations')}
    strict = {k for k, d in dissertations.items() if d['in_analysis'] == 'True'}
    dated = {k for k in strict if dissertations[k]['year']}
    assert all(dissertations[k]['year'].isdigit() and len(dissertations[k]['year']) == 4 for k in dated)
    keys = {d['work_id'] for d in decisions}
    citations = defaultdict(set)
    for c in read('citations'):
        if c['work_id'] in keys:
            assert c['dissertation_id'] in dissertations
            citations[c['work_id']].add(c['dissertation_id'])
    # Validate the frozen raw numbers; never rewrite them.
    for w in works:
        ids = citations[w['work_id']]
        assert len(ids & strict) == int(w['cited_by_strict_phds']), w['work_id']
        assert len(ids) == int(w['cited_by_all_records']), w['work_id']
    groups = defaultdict(set)
    for d in decisions:
        groups[d['classification']].add(d['work_id'])
    def union(work_keys, eligible=dated):
        return set().union(*(citations[k] for k in work_keys)) & eligible
    author = union(keys)
    book_keys = groups['imagined_communities_confirmed']
    book = union(book_keys)
    main_ids = union({MAIN})
    other = union(groups['other_benedict_confirmed'])
    held = union(groups['ambiguous_held'])
    other_author = union(groups['other_author_confirmed'])
    verified_benedict = book | other
    assert len(dated) == 6794 and len(author) == 716 and len(main_ids) == 641 and len(book) == 685
    populations = {'GLOBAL': dated}
    populations.update({r: {k for k in dated if region(dissertations[k]['country']) == r} for r in ['CA', 'US', 'EUROPE', 'OTHER']})
    assert {r: len(s) for r, s in populations.items()} == {'GLOBAL':6794,'CA':2212,'US':2168,'EUROPE':2025,'OTHER':389}
    def percentage(n, denominator):
        return round(100 * n / denominator, 9) if denominator else None
    metrics = {}
    for r, population in populations.items():
        p, m, b = len(author & population), len(main_ids & population), len(book & population)
        metrics[r] = {
            'dated_in_analysis_dissertations': len(population),
            'frozen_first_author_P': p,
            'strict_main_book_key_W': m,
            'confirmed_book_title_family_union': b,
            'additional_book_dissertations_beyond_main_key': b-m,
            'main_key_share_of_frozen_P_percent': percentage(m, p),
            'confirmed_book_union_share_of_frozen_P_percent': percentage(b, p),
            'frozen_P_share_of_sample_percent': percentage(p, len(population)),
            'main_key_share_of_sample_percent': percentage(m, len(population)),
            'confirmed_book_union_share_of_sample_percent': percentage(b, len(population)),
        }
    person_rows = [p for p in read('people') if p['person_key'] == PERSON]
    authorship = [a for a in read('authorship') if a['person_key'] == PERSON]
    output = {
        'checked_on':'2026-10-25',
        'release':str(RELEASE.relative_to(ROOT)),
        'person_key':PERSON,
        'main_work_key':MAIN,
        'input_sha256_verified_against_release_SHA256SUMS': hashes,
        'population_rule': 'Dissertation in_analysis == True and a four-digit year; each dissertation_id counted once in each union.',
        'region_rule': 'Exact build_dissertation_site.py CA/US/EUROPE/OTHER country mapping; EUROPE is geography, not EU membership.',
        'classification_work_key_counts': dict(sorted(Counter(d['classification'] for d in decisions).items())),
        'metrics': metrics,
        'identity_audit_dated_dissertation_unions': {
            'confirmed_benedict_any_work_including_book':len(verified_benedict),
            'confirmed_other_benedict_work_union_including_overlap_with_book':len(other),
            'ambiguous_held_work_union_including_overlap_with_verified':len(held),
            'confirmed_other_author_work_union_including_overlap_with_verified':len(other_author),
            'frozen_P_without_confirmed_benedict_work_in_this_review':len(author - verified_benedict),
            'held_or_other_author_only_dissertations':sorted(author - verified_benedict),
            'confirmed_other_benedict_work_but_no_confirmed_book':len(other-book),
            'frozen_P_without_confirmed_book':len(author-book),
        },
        'undated_and_raw_scope': {
            'main_key_in_analysis_with_or_without_year':len(union({MAIN}, strict)),
            'main_key_all_release_records':len(citations[MAIN]),
            'first_author_57_keys_in_analysis_with_or_without_year':len(union(keys,strict)),
            'first_author_57_keys_all_release_records':len(set().union(*(citations[k] for k in keys))),
            'frozen_people_row_unchanged':person_rows,
            'authorship_rows_for_person':len(authorship),
            'authorship_rows_outside_first_author_scope':[a for a in authorship if a['work_id'] not in keys],
        },
        'qualifications': [
            'Confirmed means author/title-family identity from the listed sources, not a claim to have read the books or verified how each dissertation uses them.',
            'The main work key already coalesces editions. Its raw year 1991 does not mean all 641 citations are to the 1991 edition.',
            'Book-family union includes positively identified translations and complete-title variants. Article-labelled variants retain raw labels; the union does not distinguish whole-book from excerpt or component use.',
            'Incomplete subtitles, imprint fragments, generic titles and unmatched identities are held, even if a book mapping seems plausible.',
            'All 716 dated first-author P records remain the frozen denominator, including confirmed contamination and unresolved records. This audit does not repair or merge raw IDs.',
            'Work-key citation counts overlap; class and work counts must not be added as dissertation counts.',
            'Counts describe bibliography presence and not approval, intellectual influence or a full reading of the work.',
            'Positive source matches establish title identity only; frozen year, kind, container, credited author strings and raw counts remain unchanged.',
        ],
    }
    dump('counts.json', output)
    dump('citation-unions.json', {
        'checked_on':'2026-10-25',
        'scope':'Frozen-release dissertation IDs only; all arrays deduplicated and lexically sorted.',
        'dated_in_analysis_first_author_P_dissertation_ids':sorted(author),
        'dated_in_analysis_main_book_key_dissertation_ids':sorted(main_ids),
        'dated_in_analysis_confirmed_book_union_dissertation_ids':sorted(book),
        'additional_book_dissertation_ids_beyond_main_key':sorted(book-main_ids),
        'per_work':[{ 'index':d['index'], 'work_id':d['work_id'], 'classification':d['classification'],
            'dated_in_analysis_count':len(citations[d['work_id']] & dated),
            'dated_in_analysis_dissertation_ids':sorted(citations[d['work_id']] & dated),
            'in_analysis_count_with_or_without_year':len(citations[d['work_id']] & strict),
            'all_release_records_count':len(citations[d['work_id']])} for d in decisions],
    })
    assert hashes == {name:sha(RELEASE/name) for name in checked_files}, 'Frozen inputs changed during audit'
    print(json.dumps({'classifications':output['classification_work_key_counts'], 'metrics':metrics, 'identity_audit':output['identity_audit_dated_dissertation_unions'], 'raw_scope':output['undated_and_raw_scope']}, indent=2))

if __name__ == '__main__':
    main()
