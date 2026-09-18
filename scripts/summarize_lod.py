#!/usr/bin/env python3
"""Audit a finished LOD snapshot and produce a readable report, without network."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from mine_lod import ROOT, ROLE, WD, WDT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    load = lambda name: json.loads((run/name).read_text())
    summary = load('summary.json')
    people = {p['qid']:p for p in load('people.json')}
    selection = load('selection.json')
    docs = load('bibliographic-resources.json')
    recent = [d for d in docs if d['window_years']]
    subjects = {s['uri']:s['labels'] for s in load('subjects.json')}
    manifest = load('manifest.json')
    identities = load('identity-review.json')
    observations = load('observations.json')['statements']
    assert all(not m['cap_reached'] and m['rows'] < m['row_limit'] for m in manifest)
    for m in manifest:
        assert hashlib.sha256((run/m['snapshot']).read_bytes()).hexdigest() == m['sha256'], m['id']
    request_ids = {m['id'] for m in manifest}
    assert len(request_ids) == len(manifest)
    assert len({o['id'] for o in observations}) == len(observations)
    assert all(o['review_status']=='unreviewed' and set(o['source_requests']) <= request_ids and o['source_requests']
               for o in observations)
    assert all(all(s in subjects for s in d['subjects']) for d in recent)
    for path, expected in load('inputs.json').items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path

    def candidates(d, role=None):
        return {q for c in d['contributions'] if role is None or c['role']==ROLE+role
                for q in selection['authority_to_candidate_qids'][c['authority']]}

    themes = {}
    for theme, ids in selection['themes'].items():
        matched = [d for d in recent if candidates(d)&set(ids)]
        themes[theme] = {'sampled_people':len(ids), 'recent_records':len(matched),
                         'recent_author_records':sum(bool(candidates(d,'aut')&set(ids)) for d in matched),
                         'people_with_recent_records':len({q for d in matched for q in candidates(d)&set(ids)}),
                         'records_with_subjects':sum(bool(d['subjects']) for d in matched)}
    role_counts = {role:sum(any(c['role']==ROLE+role for c in d['contributions']) for d in recent)
                   for role in ['aut','edt','pbd','trl','aui']}
    topic_counts = Counter(s for d in recent for s in set(d['subjects']))
    quality = {'source_hashes_verified':len(manifest), 'all_queries_below_recorded_caps':True,
               'unique_observation_ids':True, 'all_observation_provenance_resolves':True,
               'all_recent_subject_ids_resolve':True, 'protected_inputs_unchanged':True,
               'theme_sample_metrics':themes, 'recent_resource_counts_by_sampled_role':role_counts,
               'identity_flags':dict(Counter(flag for r in identities for flag in r['flags'])),
               'role_caveat':'Only contributions involving the sampled authority identifiers are counted; these are not complete credit lists.'}
    (run/'audit.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n')
    with (run/'people.csv').open('w',newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['qid','label','discovery_cohorts','idref','gnd','bnf','viaf','lc','control','inherited_atlas_person_ids'])
        for q,p in sorted(people.items()):
            writer.writerow([q,p['label'],'; '.join(p['cohorts']),
                *['; '.join(p['identifiers'].get(k,[])) for k in ['P269','P227','P268','P214','P244']],
                bool(p.get('control')),'; '.join(m['person_id'] for m in p['atlas_matches'])])
    clean = lambda text: text.replace('|','/').replace('\n',' ').replace('\x98','').replace('\x9c','')
    lines = ['# First LOD mining harvest', '',
        'This is source-observation staging, not accepted scholarly classifications or a new atlas release.', '',
        f"Completed {summary['completed_at']}. Queries have individually recorded retrieval times; the endpoints are not one synchronized snapshot.", '',
        '## What was harvested', '',
        f"- **{summary['discovered_people']:,} distinct discovery candidates**, plus inherited atlas matches and controls: **{len(people):,} people** in total.",
        f"- **{summary['sampled_people']} sampled people**, through **{summary['sampled_authorities']} IdRef authority identifiers**.",
        f"- **{len(docs):,} Sudoc bibliographic resources** across all returned years for those identifiers and the specified contribution roles.",
        f"- **{len(recent):,} records with a structured year in 2020–2026**, of which **{summary['recent_resources_exact_single_year']:,}** have one unambiguous exact year.",
        f"- **{summary['recent_resources_with_subjects']:,} recent records have subject links**, spanning **{len(subjects):,} distinct subject identifiers**.",
        f"- **{len(observations):,} deduplicated source statements** with query-level provenance; **{len(manifest)} successful queries**.", '',
        'Records are not deduplicated intellectual works. Translations, reissues, different formats and cataloguing duplicates can all increase these counts. Continuing series and editorial-board records can also appear: Davis’s 2020 Early Modern Cultural Studies record is one example. Resource types and contribution roles need review before counting books or original scholarship. Year 2026 is partial; a catalogue year does not prove an item has already been released.', '',
        '## Discovery and sampling', '',
        '| Discovery route | Distinct candidate people |', '| --- | ---: |']
    for name,n in summary['cohort_counts'].items():
        lines.append(f'| {name} | {n} |')
    lines += ['', 'Routes overlap. Narrow fields use P101 or P106→P425; broad gender/women’s studies additionally require the exact historian occupation. The broad route is explicitly adjacent-field discovery, not a gender-history membership assertion.', '',
        'The 42 previously accepted atlas–Wikidata identities were carried forward as an identity baseline, not re-matched by name. The other atlas people have not yet been systematically reconciled. Scott, Davis and Clifford are explicit controls. No absence from a field query excludes a control.', '',
        'For bibliographies, select available controls then fill each 30-person theme quota using a fixed SHA-256 ordering of QIDs. This is reproducible convenience sampling of linked records, not a representative sample of historians, languages, living scholars or contemporary field activity.', '',
        '| Sample group | People sampled | People with recent records | Recent records | With sampled author role |', '| --- | ---: | ---: | ---: | ---: |']
    for theme,v in themes.items():
        lines.append(f"| {theme} | {v['sampled_people']} | {v['people_with_recent_records']} | {v['recent_records']} | {v['recent_author_records']} |")
    lines += ['', 'Sample groups and publications can overlap. These columns describe the selected identifiers, not the total output of a field. Control-group placement is not a new field assignment.', '',
              '## What happened to the controls', '']
    for q in ['Q291798','Q266185','Q112545811']:
        p = people[q]; found = [d for d in recent if q in candidates(d)]
        lines += [f"### {p['label']} ({q})", '',
                  f"Discovery cohorts: {', '.join(p['cohorts']) or 'none; retained as a control'}. Recent linked records: {len(found)}. These links remain identity candidates until reviewed.", '']
        for d in sorted(found,key=lambda d:(-max(d['window_years']),d['uri']))[:4]:
            text = clean((d['citations'] or [d['uri']])[0])
            topics = '; '.join(' / '.join(subjects[s]) or s for s in d['subjects'][:5]) or 'No subject link returned'
            lines.append(f"- {', '.join(map(str,d['window_years']))}: [{text}]({d['uri'].removesuffix('/id')}). Subjects: {clean(topics)}.")
        if not found:
            lines.append('No recent Sudoc record returned under these identifiers and roles; this is not evidence of no recent scholarship.')
        lines.append('')
    lines += ['## Identity and date review', '',
        f"**{summary['identity_links_flagged']} sampled identity links carry review flags**, including **{summary['identity_birth_conflicts']} birth-year conflicts**. All sampled links remain `needs_review`, including those without flags.", '',
        'The staging graph retains Wikidata people and IdRef authority URIs separately. The CSV’s candidate-person column is a join through the recorded identifier, not an accepted identity merge. Review identity flags before attributing bibliographic records to people.', '',
        'Date status counts across all returned bibliographic resources:', '']
    for status,n in summary['date_status_counts'].items():lines.append(f'- {status}: {n:,}')
    lines += ['', 'Recent extraction uses structured dc:date values. It never extracts a year from a title, subject-period string or citation. Multiple or non-exact dates remain ambiguous. The identity audit checks available birth-year conflicts and shared/multiple identifiers; it does not prove identity from matching names.', '',
        '## Files and reproduction', '',
        '- `people.csv` / `people.json`: discovery provenance, external identifiers and inherited atlas mappings.',
        '- `selection.json`: exact theme samples and candidate authority joins.',
        '- `recent-resources.csv`: inspectable recent records, raw role URIs, dates and original subject labels.',
        '- `bibliographic-resources.json`: all-period records for the sampled authorities; no inferred first-publication dates.',
        '- `identity-review.json`: authority labels, birth values and identity review flags.',
        '- `observations.json`: unreviewed RDF-like source statements with provenance; no inferred field, membership or influence edges.',
        '- `subjects.json`: subject IDs and original labels; no automatic subject-to-field mapping.',
        '- `manifest.json`, `queries/`, `raw/`: exact queries, cached results, retrieval timestamps and SHA-256 hashes.',
        '- `summary.json`, `audit.json`, `inputs.json`: scope counts, integrity checks and protected input fingerprints.', '',
        'From the repository root, run:', '', '```sh',
        'python3 scripts/mine_lod.py --run PATH_TO_SNAPSHOT --offline',
        'python3 scripts/summarize_lod.py PATH_TO_SNAPSHOT',
        "python3 -m unittest discover -s tests -p 'test_lod_mining.py' -v", '```', '',
        'Omit `--offline` to fetch missing queries. Existing cache entries must match the exact query and endpoint; changed plans/inputs require a new run directory. A query hitting its row cap fails rather than masquerading as a complete harvest. IdRef queries respect its sorted-result ceiling. The raw cache should remain outside published site assets.', '',
        '## Next batch', '',
        'Review flagged identities first, then classify a small sample of recent records as original work, translation, reissue or unresolved publication. Use the observed subjects as discovery leads and record any person-to-field interpretation separately with evidence. Expand the bibliographic sample only after evaluating these outcomes; no field-size or productivity ranking is justified by this harvest.', '',
        'The authoritative atlas, ontology fixtures, site assets and OpenAlex data were not modified by the miner. The requested 2020–2026 window applies to catalogued publication years, not the validity dates of Wikidata classifications.']
    (run/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(quality,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
