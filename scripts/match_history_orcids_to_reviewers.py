#!/usr/bin/env python3
"""Build unaccepted reviewer/ORCID candidates; never modify either source database."""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / 'data/history-journal-profession-review-2026-09-22'
INDEX = ROOT / 'data/history-orcid-fanout-2026-09-22/generated/v1/orcid-index.duckdb'
AUTHORITY = ROOT / 'data/orcid-2026-09-21/historians-orcid-enriched.csv'
CATALOG = Path('/home/jic823/hnet-reviews/data/export/catalog.duckdb')
DEMO = '0000-0002-1825-0097'
FIELDS = ['source', 'era', 'review_id', 'reviewer', 'reviewer_affiliation',
          'reviewer_qid', 'reviewer_wd_status', 'review_title', 'book_title',
          'book_author', 'review_date', 'source_url']


def normalized(value):
    """Conservative candidate key: Unicode preserved; no initials or accent folding."""
    value = unicodedata.normalize('NFKC', value or '').casefold()
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in value).split())


def affiliation_overlap(left, right):
    a, b = normalized(left), normalized(right)
    short, long = sorted((a, b), key=len)
    # A literal phrase clue, not institutional resolution or employment proof.
    if len(short) < 12 or len(short.split()) < 2:
        return False
    generic = {'history', 'department', 'faculty', 'school', 'of', 'the', 'historical',
               'studies', 'historian', 'independent', 'scholar', 'retired', 'emeritus'}
    if set(short.split()) <= generic:
        return False
    return ' ' + short + ' ' in ' ' + long + ' '


def route(name_match, qid_match):
    return 'name_and_existing_qid' if name_match and qid_match else 'name_only' if name_match else 'existing_qid_only'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def export_csv(path, rows, fields=None):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: canonical(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'data/history-orcid-reviewer-matches-2026-09-22')
    args = parser.parse_args()
    out = args.out
    if (out / 'summary.json').exists():
        raise SystemExit('Completed output exists; choose a new --out directory.')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'generated').mkdir(exist_ok=True)
    inputs = [CATALOG, INDEX, AUTHORITY, SELECTION / 'selected-journals.json',
              SELECTION / 'orcid-candidates.csv', ROOT / 'data/grounding-repair/decisions.json',
              ROOT / 'data/grounding-repair/occurrences.json']
    input_hashes = {str(p): sha(p) for p in inputs}
    with (SELECTION / 'orcid-candidates.csv').open() as stream:
        candidates = {r['orcid_id']: r for r in csv.DictReader(stream)}
    assert len(candidates) == 22429 and DEMO not in candidates
    journals = json.loads((SELECTION / 'selected-journals.json').read_text())['journals']
    assert len(journals) == 405
    journal_labels = {r['journal_key']: r['label'] for r in journals}
    con = duckdb.connect(str(INDEX), read_only=True)
    con.execute('CREATE TEMP TABLE selected(journal_key VARCHAR PRIMARY KEY)')
    con.executemany('INSERT INTO selected VALUES (?)', [(k,) for k in journal_labels])
    evidence_cursor = con.execute('''SELECT e.credit_evidence_id, e.orcid_id, e.name,
        e.given_name, e.family_name, e.affiliation_json, e.first_source_observation_id,
        r.record_id, r.doi, r.title_text, r.publication_year, e.authenticated_orcid_deposited
        FROM orcid_evidence e JOIN records r USING(record_id)
        WHERE e.orcid_id <> ? AND EXISTS (SELECT 1 FROM journal_memberships m
          JOIN selected s USING(journal_key) WHERE m.record_id=e.record_id)
        ORDER BY e.credit_evidence_id''', [DEMO])
    cols = [d[0] for d in evidence_cursor.description]
    evidence = [dict(zip(cols, r)) for r in evidence_cursor.fetchall()]
    memberships = defaultdict(list)
    for rid, key in con.execute('SELECT m.record_id,m.journal_key FROM journal_memberships m JOIN selected s USING(journal_key)').fetchall():
        memberships[rid].append(key)
    con.close()
    by_orcid, by_name = defaultdict(list), defaultdict(set)
    affiliations = defaultdict(set)
    for e in evidence:
        e['selected_journal_keys'] = sorted(memberships[e['record_id']])
        e['selected_journal_labels'] = [journal_labels[k] for k in e['selected_journal_keys']]
        by_orcid[e['orcid_id']].append(e)
        if normalized(e['name']):
            by_name[normalized(e['name'])].add(e['orcid_id'])
        for aff in json.loads(e['affiliation_json'] or '[]'):
            if aff.get('name'):
                affiliations[e['orcid_id']].add(aff['name'])
    assert set(by_orcid) == set(candidates)
    qid_orcids, orcid_qids, authority_rows = defaultdict(set), defaultdict(set), defaultdict(list)
    with AUTHORITY.open() as stream:
        for a in csv.DictReader(stream):
            identifier = a['orcid'].lower().removeprefix('https://orcid.org/').removeprefix('http://orcid.org/')
            if identifier in candidates:
                qid_orcids[a['qid']].add(identifier)
                orcid_qids[identifier].add(a['qid'])
                authority_rows[identifier].append(a)
    pilot = json.loads((ROOT / 'data/grounding-repair/decisions.json').read_text())
    decisions = defaultdict(list)
    for d in pilot['decisions']:
        decisions[d['occurrence_id']].append(d)
    pilot_reviews = defaultdict(list)
    for o in json.loads((ROOT / 'data/grounding-repair/occurrences.json').read_text()):
        if o['role'] == 'reviewer' and o['occurrence_id'] in decisions:
            pilot_reviews[(o['source'], o['era'], o['review_id'])].append({
                'occurrence_id': o['occurrence_id'], 'decisions': decisions[o['occurrence_id']]})
    cat = duckdb.connect(str(CATALOG), read_only=True)
    reviews = [dict(zip(FIELDS, row)) for row in cat.execute(
        'SELECT ' + ','.join(FIELDS) + ' FROM reviews WHERE is_real ORDER BY source,era,review_id').fetchall()]
    cat.close()
    assert len({(r['source'], r['era'], r['review_id']) for r in reviews}) == len(reviews)
    matched, unmatched, review_snapshot = [], [], []
    for r in reviews:
        key = (r['source'], r['era'], r['review_id'])
        fingerprint = hashlib.sha256(canonical(r).encode()).hexdigest()
        name_ids = by_name.get(normalized(r['reviewer']), set())
        qid_ids = qid_orcids.get(r['reviewer_qid'], set())
        ids = name_ids | qid_ids
        if not ids:
            unmatched.append({'source': r['source'], 'era': r['era'], 'review_id': r['review_id'],
                              'reviewer': r['reviewer'], 'metadata_fingerprint': fingerprint})
            continue
        review_snapshot.append(r)
        for identifier in sorted(ids):
            overlaps = sorted(a for a in affiliations[identifier] if affiliation_overlap(r['reviewer_affiliation'], a))
            qids = sorted(orcid_qids[identifier])
            conflict = bool(r['reviewer_qid'] and qids and r['reviewer_qid'] not in qids)
            flags = json.loads(candidates[identifier]['quality_flags'])
            if conflict or flags or len(qids) > 1 or key in pilot_reviews:
                priority = '0_check_conflict_or_prior_decision'
            elif len(ids) > 1:
                priority = '1_disambiguate_multiple_orcids'
            elif overlaps:
                priority = '2_name_or_qid_with_affiliation_clue'
            elif identifier in name_ids and identifier in qid_ids:
                priority = '3_name_and_existing_qid'
            else:
                priority = '4_needs_independent_attribution'
            matched.append({
                **r, 'metadata_fingerprint': fingerprint,
                'candidate_orcid': identifier,
                'candidate_route': route(identifier in name_ids, identifier in qid_ids),
                'candidate_count_for_review': len(ids),
                'saved_wikidata_qids_for_orcid': qids,
                'existing_qid_disagrees_with_saved_orcid_qids': conflict,
                'selected_deposited_names': candidates[identifier]['selected_deposited_names'],
                'selected_affiliation_phrase_overlaps': overlaps,
                'selected_affiliations': sorted(affiliations[identifier]),
                'quality_flags': flags,
                'prior_pilot_reviewer_decisions': pilot_reviews.get(key, []),
                'selected_credit_evidence_ids': [e['credit_evidence_id'] for e in by_orcid[identifier]],
                'priority': priority, 'identity_status': 'candidate_unreviewed',
            })
    matched.sort(key=lambda r: (r['priority'], normalized(r['reviewer']), r['source'] or '', r['era'] or '', r['review_id'], r['candidate_orcid']))
    export_csv(out / 'reviewer-orcid-candidates.csv', matched)
    export_csv(out / 'generated/unmatched-reviewers.csv', unmatched)
    export_csv(out / 'generated/matched-review-metadata.csv', review_snapshot)
    used_ids = {r['candidate_orcid'] for r in matched}
    with (out / 'generated/publication-evidence.jsonl').open('w') as stream:
        for e in evidence:
            if e['orcid_id'] in used_ids:
                stream.write(canonical(e) + '\n')
    with (out / 'generated/saved-authority-evidence.jsonl').open('w') as stream:
        for identifier in sorted(used_ids):
            for a in authority_rows[identifier]:
                stream.write(canonical(a) + '\n')
    assert len({(r['source'], r['era'], r['review_id'], r['candidate_orcid']) for r in matched}) == len(matched)
    assert all(r['identity_status'] == 'candidate_unreviewed' for r in matched)
    assert all(sha(p) == input_hashes[str(p)] for p in inputs), 'Input changed during run; outputs are not a completed release.'
    def nreviews(predicate):
        return len({(r['source'], r['era'], r['review_id']) for r in matched if predicate(r)})
    summary = {
        'scope': 'Reviewer credits in current is_real H-Net/RiH catalog; selected 405-journal ORCIDs only. No book-author matching or person acceptance.',
        'review_records_inspected': len(reviews),
        'review_records_with_candidates': len(review_snapshot),
        'review_records_without_candidates': len(unmatched),
        'candidate_pairs': len(matched), 'distinct_candidate_orcids': len(used_ids),
        'distinct_reviewer_name_strings_with_candidates': len({r['reviewer'] for r in matched}),
        'candidate_pair_routes': dict(Counter(r['candidate_route'] for r in matched)),
        'review_records_without_existing_qid_with_candidates': nreviews(lambda r: not r['reviewer_qid']),
        'review_records_with_affiliation_phrase_clue': nreviews(lambda r: bool(r['selected_affiliation_phrase_overlaps'])),
        'ungrounded_review_records_with_affiliation_phrase_clue': nreviews(lambda r: not r['reviewer_qid'] and bool(r['selected_affiliation_phrase_overlaps'])),
        'review_records_with_multiple_candidate_orcids': nreviews(lambda r: r['candidate_count_for_review'] > 1),
        'review_records_with_existing_qid_disagreement': nreviews(lambda r: r['existing_qid_disagrees_with_saved_orcid_qids']),
        'review_records_with_prior_pilot_decisions': nreviews(lambda r: bool(r['prior_pilot_reviewer_decisions'])),
        'review_records_with_quality_flagged_orcid': nreviews(lambda r: bool(r['quality_flags'])),
        'priority_pair_counts': dict(Counter(r['priority'] for r in matched)),
        'input_sha256': input_hashes, 'script_sha256': sha(__file__),
        'validation': {'inputs_unchanged': True, 'unique_review_orcid_pairs': True,
                       'only_selected_orcids': used_ids <= set(candidates), 'all_candidates_unaccepted': True},
        'limitations': ['No normalized full-name match establishes identity.',
                       'Existing reviewer QIDs and saved Wikidata/ORCID links are source assertions, not independent verification.',
                       'Affiliation phrase overlap is a clue; department strings, institutional changes and dates need review.',
                       'Dates and titles are bibliographic context; reviewed-book author credits are not matched.',
                       'Catalog row IDs and metadata fingerprints are retained; these are not graph occurrence IDs.',
                       'Incomplete name normalization deliberately misses accents, initials and reordered names.'],
    }
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('input_sha256', 'limitations')}, indent=2))


if __name__ == '__main__':
    main()
