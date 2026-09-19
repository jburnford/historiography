#!/usr/bin/env python3
"""Apply explicit LLM editorial annotations and a conservative death-date filter.

Original visibility rankings and graph data are immutable inputs. Unknown people
are an unreviewed queue, never silently classified as irrelevant.
"""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re

try:
    from .rank_wikidata_historians import csv_rows, write_csv
except ImportError:
    from rank_wikidata_historians import csv_rows, write_csv

ROLES = {'research_historian', 'historical_writer', 'conceptual_contributor',
         'adjacent_scholar', 'contextual_figure', 'identity_or_occupation_review'}
ROOT = Path(__file__).resolve().parents[1]


def death_status(dates, cutoff=1940, current_year=2026):
    deaths = [d for d in dates if d['property'] == 'P570' and d['rank'] != 'deprecated']
    if not deaths:
        return 'no_death_recorded'
    years = []
    for d in deaths:
        match = re.match(r'^([+-]?\d+)-', d['date'])
        year = int(match[1]) if match else None
        if (year is None or d['precision'] < 9 or year > current_year
                or d['calendar'] not in {'Q1985727', 'Q1985786'}
                or d.get('before', 0) or d.get('after', 0)
                or (d['calendar'] == 'Q1985786' and year == cutoff - 1)):
            return 'death_date_review'
        years.append(year)
    if max(years) < cutoff:
        return 'died_before_cutoff'
    if min(years) >= cutoff:
        return 'death_at_or_after_cutoff'
    return 'death_date_review'


def eligible(status):
    return status in {'no_death_recorded', 'death_at_or_after_cutoff'}


def review_sort(row):
    return (int(row['priority_band']), -float(row['score']), -int(row['wikipedia_editions']),
            row['label'].casefold(), row['qid'])


def main(snapshot, cutoff=1940, output=None):
    ranking = snapshot / 'ranking'
    review = ranking / 'editorial-review'
    output = output or review
    output.mkdir(parents=True, exist_ok=True)
    rows = csv_rows(ranking / 'ranked-candidates.csv')
    with (review / 'decisions.tsv').open(encoding='utf-8', newline='') as handle:
        decisions = list(csv.DictReader(handle, delimiter='\t'))
    annotations = {d['qid']: d for d in decisions}
    assert len(annotations) == len(decisions), 'Duplicate reviewed identity'
    evidence = json.loads((review / 'article-evidence.json').read_text()) + json.loads((review / 'targeted-evidence.json').read_text())
    sources = {r['qid']: r for r in evidence}
    assert set(sources) == set(annotations), 'Every reviewed candidate must have an evidence capture'
    for d in decisions:
        assert d['role'] in ROLES and int(d['priority_band']) in range(1, 5)
        assert d['field_or_debate'] and d['work_or_contribution'] and d['editorial_reason']
        assert sources[d['qid']]['article_lead']
    candidate_ids = {r['qid'] for r in rows}
    assert set(annotations) <= candidate_ids
    date_lookup = {}
    with gzip.open(snapshot / 'historians-with-date-evidence.jsonl.gz', 'rt', encoding='utf-8') as handle:
        for line in handle:
            person = json.loads(line)
            if person['qid'] in candidate_ids:
                date_lookup[person['qid']] = person['date_statements']
    assert set(date_lookup) == candidate_ids
    reviewed, unreviewed, excluded, date_review = [], [], [], []
    all_filtered = []
    for original in rows:
        key = original['qid']
        row = dict(original)
        row['original_visibility_rank'] = row.pop('rank')
        row['death_cutoff'] = cutoff
        row['death_filter_status'] = death_status(date_lookup[key], cutoff)
        row['review_status'] = 'llm_editorial_review' if key in annotations else 'unreviewed'
        row.update({name: annotations.get(key, {}).get(name, '') for name in
                    ('role', 'priority_band', 'field_or_debate', 'work_or_contribution', 'editorial_reason')})
        row['review_source_url'] = sources[key]['url'] if key in sources else ''
        row['supporting_source_url'] = 'https://plato.stanford.edu/entries/arendt/' if key == 'Q60025' else ''
        row['review_basis'] = 'biography_and_selected_work_passages; editorial_inference' if key in annotations else ''
        row['relationship_status'] = 'candidate_only_no_edge_accepted'
        row['atlas_coverage_note'] = ('main_named_works_post_2000_extension' if key in {'Q233479', 'Q107085771'}
                                      else 'date_specific_placement_requires_review')
        if key == 'Q60025':
            row['review_basis'] += '; user_requested_priority_for_totalitarianism'
        if key in annotations:
            reviewed.append(row)
        if row['death_filter_status'] == 'died_before_cutoff':
            excluded.append(row)
        elif row['death_filter_status'] == 'death_date_review':
            date_review.append(row)
        else:
            all_filtered.append(row)
            if key not in annotations:
                unreviewed.append(row)
    reviewed.sort(key=review_sort)
    kept_reviewed = [r for r in reviewed if eligible(r['death_filter_status'])]
    priority = [r for r in kept_reviewed if int(r['priority_band']) == 1]
    secondary = [r for r in kept_reviewed if int(r['priority_band']) == 2]
    context = [r for r in kept_reviewed if int(r['priority_band']) >= 3]
    shortlist = priority + secondary
    def numbered(items):
        # Display order within editorial bands, not a numerical ranking of historical merit.
        return [{'review_order': i, **r} for i, r in enumerate(items, 1)]
    base_columns = list(all_filtered[0])
    columns = ['review_order', *base_columns]
    outputs = {
        'reviewed-all.csv': (numbered(reviewed), columns),
        'reviewed-shortlist.csv': (numbered(shortlist), columns),
        'reviewed-priority.csv': (numbered(priority), columns),
        'reviewed-secondary.csv': (numbered(secondary), columns),
        'reviewed-context.csv': (numbered(context), columns),
        'reviewed-earlier-roots.csv': (numbered([r for r in reviewed if r['death_filter_status'] == 'died_before_cutoff']), columns),
        'candidates-death-filtered.csv.gz': (all_filtered, base_columns),
        'unreviewed-death-filtered.csv.gz': (unreviewed, base_columns),
        'excluded-deaths-before-cutoff.csv.gz': (excluded, base_columns),
        'death-date-review.csv.gz': (date_review, base_columns),
    }
    for name, (records, cols) in outputs.items():
        write_csv(output / name, records, cols)
    cohort = {r['qid'] for r in json.loads((review / 'review-cohort.json').read_text())}
    summary = {
        'death_cutoff': cutoff, 'original_addition_candidates': len(rows),
        'death_filter_counts': dict(Counter(r['death_filter_status'] for r in reviewed + unreviewed
                                          + [r for r in excluded + date_review if r['qid'] not in annotations])),
        'default_candidates': len(all_filtered), 'excluded_before_cutoff': len(excluded), 'death_date_review': len(date_review),
        'reviewed_people': len(reviewed), 'original_first_100_reviewed': len(cohort & set(annotations)),
        'targeted_extra_reviews': len(set(annotations) - cohort),
        'first_100_role_counts': dict(Counter(r['role'] for r in reviewed if r['qid'] in cohort)),
        'first_100_priority_counts': dict(Counter(r['priority_band'] for r in reviewed if r['qid'] in cohort)),
        'default_reviewed_priority': len(priority), 'default_reviewed_secondary': len(secondary),
        'default_reviewed_context_or_hold': len(context), 'default_unreviewed': len(unreviewed),
        'reviewed_excluded_before_cutoff': sum(r['death_filter_status'] == 'died_before_cutoff' for r in reviewed),
        'reviewed_death_date_review': sum(r['death_filter_status'] == 'death_date_review' for r in reviewed),
        'unchanged_existing_match_file': '../ranked-existing-match-leads.csv',
    }
    assert len(all_filtered) + len(excluded) + len(date_review) == len(rows)
    assert len(kept_reviewed) + len(unreviewed) == len(all_filtered)
    assert sum(summary['death_filter_counts'].values()) == len(rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    md = ['# Reviewed candidates for the historiography graph', '',
          f'Reviewed {len(reviewed)} people: every person in the original first 100, plus {len(annotations)-len(cohort)} targeted candidates buried by the visibility score.', '',
          f'Default view excludes recorded deaths before {cutoff}; uncertain death dates are held for review. Earlier figures remain in reviewed-earlier-roots.csv. No recorded death is not proof of life after the cutoff.', '',
          'Priority is an editorial assessment of a named contribution to historical scholarship, method or debate. Philosophers and other conceptual contributors qualify. Wikipedia and the original four-part score order people only within an editorial band; this order is not a scale of historical merit.', '',
          'Hannah Arendt is a priority node candidate for the totalitarianism debate. Churchill and H. G. Wells remain substantial historical-writer candidates in the second band. The evidence does not yet accept any graph edge.', '',
          '## Priority candidates', '',
          '| Order | Person | Field or debate | Reason for review | Original visibility rank |',
          '| ---: | --- | --- | --- | ---: |']
    def safe(text):
        return text.replace('|', '\\|').replace('[', '\\[').replace(']', '\\]')
    for i, r in enumerate(priority, 1):
        md.append(f"| {i} | [{safe(r['label'])}]({r['review_source_url']}) | {safe(r['field_or_debate'])} | {safe(r['work_or_contribution'])} | {r['original_visibility_rank']} |")
    md += ['', '## Further substantive candidates', '',
           '| Person | Role | Work or contribution to assess |', '| --- | --- | --- |']
    for r in secondary:
        md.append(f"| [{safe(r['label'])}]({r['review_source_url']}) | {r['role'].replace('_', ' ')} | {safe(r['work_or_contribution'])} |")
    md += ['', '## Limits', '',
           'This is an LLM editorial triage based chiefly on biographies and selected descriptions of works, with source captures and individual reasons. It is not a full primary-source audit, a complete review of all candidates, or an endorsement of the reviewed arguments. Field labels are leads, not accepted atlas edges.', '',
           'The death filter does not date intellectual activity: Iorga and Javakhishvili pass because they died in 1940; Mommsen, Hrushevsky, Mitre, Duhem and Liang Qichao remain important earlier-root candidates. Nicolas Tackett and the named Applebaum books need the planned post-2000 extension. Existing graph people and all-period identity leads are preserved.', '']
    (output / 'REVIEWED-LIST.md').write_text('\n'.join(md))
    inputs = [ranking / 'ranked-candidates.csv', ranking / 'ranked-existing-match-leads.csv',
              snapshot / 'historians-with-date-evidence.jsonl.gz', review / 'decisions.tsv',
              review / 'article-evidence.json', review / 'targeted-evidence.json',
              review / 'review-cohort.json', review / 'targeted-cohort.json',
              review / 'REVIEW-PROMPT.md']
    inputs += sorted(p for p in (review / 'raw').glob('*') if p.is_file())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        'version': 2, 'review_date': '2026-09-17', 'reviewer': 'Codex assistant; LLM editorial judgment',
        'death_cutoff': cutoff, 'script_sha256': digest(Path(__file__)),
        'atlas_sha256': digest(ROOT / 'historiography-1920-2000.json'),
        'inputs_sha256': {str(p.relative_to(snapshot)): digest(p) for p in inputs},
        'outputs_sha256': {name: digest(output / name) for name in list(outputs) + ['summary.json', 'REVIEWED-LIST.md']},
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--death-cutoff', type=int, default=1940)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    main(args.snapshot, args.death_cutoff, args.output)
