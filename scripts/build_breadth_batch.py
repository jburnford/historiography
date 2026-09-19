#!/usr/bin/env python3
"""Rebuild the first breadth packet offline from preserved, selected evidence.

Reference occurrences and note bundles are discovery leads, never work entities
or influence edges. Selection is authored separately from metadata harvesting.
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate

OUT = ROOT / 'data/extension-2026/breadth-01'
DAY = '2026-09-18'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def captured_lines(text):
    """Web extraction can put several numbered lines on one physical line."""
    return [(int(m.group(1)), m.group(2).strip()) for m in
            re.finditer(r'L(\d+)(?:@P\d+)?:\s*(.*?)(?=L\d+(?:@P\d+)?:|\Z)', text, re.S)]


def note_bundles(text):
    result = []
    current = None
    for line, content in captured_lines(text):
        match = re.match(r'\*\s+(\d+)\s+(.*)', content, re.S)
        if match:
            current = dict(number=int(match[1]), first_line=line, raw_text=match[2])
            result.append(current)
        elif current:
            # The captured note section ends at the next heading, not site furniture.
            if content.startswith('#'):
                break
            current['raw_text'] += '\n'+content
    return result


def build():
    selected = read(OUT/'survey-selection.json')
    fields = read(OUT/'field-dossiers.json')
    harvest = {r['survey_id']: r for r in read(OUT/'crossref-harvest.json')}
    data = dict(schema_version='0.2', fixture_only=True, status='staging_only',
                production_graph_imports=0, entities=[], source_records=[], claims=[])
    references, author_observations = [], []
    for field in fields:
        data['entities'].append(dict(id=field['concept_id'], label=field['label'],
            type='concept', concept_kind=['topic'], classification_status='provisional',
            candidate_ledger_ids=field['candidate_ledger_ids'],
            existing_entry_id=field.get('existing_entry_id'),
            qualification=field['scope']))
    concept_ids = {f['id']: f['concept_id'] for f in fields}
    for row in selected:
        work = 'work:'+row['id']
        path = (OUT/row['capture']).resolve()
        data['entities'].append(dict(id=work, label=row['title'], type='work',
            identity_status=row['identity_status'], selected_survey_id=row['id'],
            reuse_note=('Same local work ID as legacy bridge' if row['id'] in
                ('daston_2017', 'ostling_heidenblad') else 'Unresolved work proposal'),
            intervention_year_observation=row['year'], date_note=row.get('date_note'),
            doi_lead=row.get('doi')))
        source_id = 'source:breadth:'+row['id']
        data['source_records'].append(dict(id=source_id, provider='Captured scholarly or publisher evidence; access scope on citation',
            url=row['url'], snapshot_path=str(path.relative_to(ROOT)), sha256=digest(path),
            observed_at=DAY+'T00:00:00+00:00', observation_time_precision='day; time unspecified',
            describes_work=work))
        if row['statement']:
            check = row['evidence_scope']
            scope = {'passage_checked':'passage', 'abstract_checked':'abstract'}.get(check, 'metadata')
            limitation = ('Only the indicated passages were checked; not a complete review or proof of reception.'
                if scope == 'passage' else 'Limited to '+check.replace('_', ' ')+
                '; inspect the relevant body text before a stronger claim. No reception inferred.')
            data['claims'].append(dict(id='claim:breadth:'+row['id'], subject=work,
                predicate='assesses_scope', object=concept_ids[row['field_id']],
                statement=row['statement'], attributed_to=work, basis='editorial_interpretation',
                qualification='Source-specific assessment, not a definition of the whole field. '+fields_by_id(fields, row['field_id'])['scope'],
                intervention_year=row['year'], valid_time=None,
                review=dict(status='needs_review', rationale='First breadth reading; external identity, argument and reception review incomplete.'),
                history=[dict(date=DAY, action='proposed', reason='Selected evidence; no graph admission')],
                evidence=[dict(source_record_id=source_id, locator=row['locator'], scope=scope,
                    support=row['statement'], check_status=check, checked_on=DAY,
                    limitation=limitation, support_assessment='bounded_proposal' if scope != 'metadata' else 'not_established')]))
        if row['id'] not in harvest:
            continue
        cached = harvest[row['id']]
        message = read(ROOT/cached['path'])['message']
        for role in ('author', 'editor'):
            for ordinal, author in enumerate(message.get(role, []), 1):
                author_observations.append(dict(id=f"credit:{row['id']}:{role}:{ordinal}",
                    survey_id=row['id'], field_id=row['field_id'], role=role,
                    provider_record=author, source_path=cached['path'], locator=f'{role}[{ordinal-1}]',
                    person_id=None, identity_status='unresolved_credit_not_distinct_person',
                    gender={'status':'not_researched','value':None,'source':None},
                    selection_status='source_credit_only', graph_connection_status='none'))
        for ordinal, ref in enumerate(message.get('reference', []), 1):
            references.append(dict(id=f"reference:{row['id']}:{ordinal}", field_id=row['field_id'],
                citing_survey_id=row['id'], source_path=cached['path'], locator=f'reference[{ordinal-1}]',
                kind='provider_reference_occurrence', raw_record=ref,
                doi_lead=ref.get('DOI'), title_lead=ref.get('article-title') or ref.get('volume-title'),
                review_status='needs_review', work_id=None,
                warning='May be incomplete or malformed; not a unique work or proof of relevance/influence.'))
    for survey, field, filename in [('romein_2020','digital_history','digital_history_notes.txt'),
                                    ('tisdall_2022','childhood_youth','childhood_notes.txt')]:
        path = OUT/'raw'/filename
        for note in note_bundles(path.read_text()):
            references.append(dict(id=f"note:{survey}:{note['number']}", field_id=field,
                citing_survey_id=survey, source_path=str(path.relative_to(ROOT)),
                locator=f"note {note['number']}; extracted line {note['first_line']}",
                kind='note_bundle', raw_record=note, work_id=None, review_status='needs_parsing',
                warning='May contain multiple works, ibid references, commentary or software; not a work count.'))
    # Bibliography entries are separate lines in this specific preserved capture.
    path = OUT/'raw/digital_methods_refs.txt'
    for line, text in captured_lines(path.read_text()):
        if line < 1415 or not re.search(r'\b(?:18|19|20)\d{2}\b', text):
            continue
        if 'Google Scholar' not in text:
            continue
        references.append(dict(id=f'reference:milligan_2022:line:{line}', field_id='digital_history',
            citing_survey_id='milligan_2022', source_path=str(path.relative_to(ROOT)),
            locator=f'extracted line {line}', kind='bibliography_line', raw_record={'text':text},
            work_id=None, review_status='needs_parsing',
            warning='Captured bibliography line; identity, source role and relevance not yet reviewed.'))
    errors = validate(data, read(ROOT/'ontology/contract-v0.2.json'), ROOT)
    if errors:
        raise ValueError('\n'.join(errors))
    return data, references, author_observations


def fields_by_id(fields, identifier):
    return next(f for f in fields if f['id'] == identifier)


def render(data, references, authors):
    fields = read(OUT/'field-dossiers.json')
    selected = read(OUT/'survey-selection.json')
    counts = Counter(r['field_id'] for r in references)
    scopes = Counter(r['evidence_scope'] for r in selected)
    review_queue=[]
    grouped={f['id']:[r['id'] for r in references if r['field_id']==f['id']] for f in fields}
    # Equal first-pass allocation, not importance ranking. Missing lists incur work.
    for round_number in range(20):
        for field in fields:
            queue=grouped[field['id']]
            if round_number < len(queue):
                review_queue.append(dict(reference_id=queue[round_number], field_id=field['id'],
                    order=len(review_queue)+1, reason='Round-robin allocation; not prominence'))
    priority=[r['id'] for r in references if 'Complicating' in json.dumps(r,ensure_ascii=False) and 'Great Man' in json.dumps(r,ensure_ascii=False)]
    write('review-queue.json',dict(allocation='Up to 20 occurrences per field in round-robin order; unfilled fields need bibliography acquisition.',
        queue=review_queue, representation_recovery_leads=priority,
        fields_without_reference_leads=[f['id'] for f in fields if not counts[f['id']]],
        warning='Queue order is workflow allocation; no importance score. Recovery leads require reading.'))
    audit=[]
    (OUT/'dossiers').mkdir(exist_ok=True)
    for field in fields:
        rows=[r for r in selected if r['field_id']==field['id']]
        audit.append(dict(field_id=field['id'], status='pending', production_ready=False,
            discovered_people_count=None, selected_people_count=None, accepted_connections_count=0,
            gender_counts=None, unknown_demographics='All newly extracted credit observations remain not researched; identities unresolved.',
            representation_question=field['representation_question'], required_next_action=field['next_action']))
        lines=[f"# {field['label']}: first breadth dossier", '',
            '**Partial evidence review; staging only. Two selected works do not establish field coverage through 2026.**','',
            field['scope'], '', field['synthesis'], '', '## Selected evidence','']
        for row in rows:
            lines += [f"- [{row['title']}]({row['url']}) ({row['year']}): **{row['evidence_scope']}**. {row['statement'] or 'Metadata only; no argument claim proposed.'} Locator: {row['locator']}."]
        lines += ['', '## Connections to investigate', '',field['connections'], '',
            'These are research questions; co-citation, shared subject matter and this dossier do not establish influence edges.', '',
            '## Gaps and next reading', '',field['gaps'], '',field['next_action'], '',
            f"Discovery queue: {counts[field['id']]} reference occurrences/note bundles, not unique or reviewed works. No complete 2001–2019 or 2020–2026 census.", '',
            '## Representation review', '',field['representation_question'], '',
            'Pending: identities and demographic evidence have not been audited. Examine candidate selection and substantive graph connections across this field; do not infer gender from names. See [project policy](../../../../REPRESENTATION-REVIEW.md).','']
        (OUT/'dossiers'/f"{field['id']}.md").write_text('\n'.join(lines))
    write('representation-audit.json',audit)
    summary=dict(fields=len(fields), selected_works=len(selected), new_local_work_ids=len(selected)-2,
        reused_legacy_work_ids=2, scoped_claim_proposals=len(data['claims']), accepted_claims=0,
        evidence_scopes=dict(scopes), reference_occurrences=len(references),
        reference_kinds=dict(Counter(r['kind'] for r in references)), references_by_field=dict(counts),
        credit_observations=len(authors), distinct_people_count=None, demographic_audit='pending',
        fully_reviewed_fields=0, production_imports=0)
    write('summary.json',summary)
    (OUT/'coverage.csv').write_text('field_id,selected_works,reference_occurrences,review_status,representation_status,production_ready\n'+
        ''.join(f"{f['id']},2,{counts[f['id']]},partial,pending,false\n" for f in fields))
    report=['# First balanced breadth batch', '',
        f"Twelve preliminary field dossiers, {len(selected)} selected survey/programme works, {len(data['claims'])} scoped proposals. Zero accepted claims, production imports or fully reviewed fields. Two work IDs are reused from the earlier knowledge pilot; 22 are new local work proposals, not verified external identities.", '',
        f"The discovery queue contains {len(references)} occurrences: "+', '.join(f'{v} {k}' for k,v in summary['reference_kinds'].items())+'. These are not distinct works, and most have not received relevance review. Notes may bundle several works or no work.', '',
        'Source access: '+', '.join(f'{v} {k}' for k,v in scopes.items())+'. Checks refer only to the indicated evidence, not complete works. Erll remains metadata-only and has no argument claim. Description/excerpt proposals have support unestablished pending closer reading.', '',
        'The first queue allocates up to twenty leads per field. Fields with no extracted bibliography incur an explicit acquisition task. No raw counts become prominence scores. Knowledge alone supplies 180 Crossref references; equal attention requires active acquisition elsewhere.', '',
        '## Dossiers', '', '| Field | Selected works | Reference occurrences |', '| --- | ---: | ---: |']
    report += [f"| [{f['label']}](dossiers/{f['id']}.md) | 2 | {counts[f['id']]} |" for f in fields]
    report += ['', '## Representation and selection', '',
        'The user reported only 7 and 6 women in two model-generated top-50 lists. [The project policy](../../../REPRESENTATION-REVIEW.md) now requires auditing discovery, selection and substantive connections across every field. Current demographic counts are unknown: author/editor credits are unresolved observations, not distinct people, and gender is not inferred. Each dossier records a specific omission question. The audit remains pending and no field is production-ready.', '',
        'A targeted recovery lead from the digital-history bibliography is Sharon Leon’s chapter on the “Great Man” narrative. Its argument must be read before it can support a claim. Model recall, Wikipedia visibility and bibliographic abundance cannot establish the selection baseline.', '',
        '## Model and provenance', '',
        '[Contract 0.2](../../../ontology/RESEARCH-0.2.md) adds exact intervention predicates without changing the frozen 0.1 pilot. The bridge preserves 18 old historical claims and two discovery tasks, their original wording, scoped citations and compound strand endpoints. Consulted witnesses are source records, not invented publications.', '',
        'Crossref dates remain provider observations: the Rothberg platform record has 2020 dates for a work selected as 2009; these do not overwrite its chronology. The childhood/education article is 2023 despite 2022 in its DOI. Claims retain null historical intervals; source dates do not establish field origins.', '',
        'Rebuild offline with `python3 scripts/bridge_extension_research.py` and `python3 scripts/build_breadth_batch.py`; validate with `python3 scripts/validate_breadth_batch.py`. Metadata acquisition is a separate bounded script. Captures are web-tool extracts, sometimes partial or indexed, not assurances of full-text access. Hashes pin the evidence used.', '',
        '## Remaining work', '',
        'Resolve authors/work editions; parse and screen the reference queue; obtain missing bibliographies and independent regional/language perspectives; read the passages behind provisional claims; audit representation and reception; review 2001–2019 and 2020–2026 separately. Childhood and youth retain separate candidate identities: this joint dossier has childhood evidence and a youth gap. Existing global/memory/GIS/trans/childhood representations must not be described as wholly absent. The original LOD precision/provenance defects remain unresolved, and OpenAlex remains paused.','']
    (OUT/'REPORT.md').write_text('\n'.join(report))


def manifest():
    inputs = [ROOT/'ontology/contract-v0.2.json', ROOT/'ontology/validate_research.py',
        ROOT/'ontology/contract.json', ROOT/'ontology/validate.py',
        ROOT/'scripts/build_breadth_batch.py', ROOT/'scripts/bridge_extension_research.py',
        ROOT/'scripts/harvest_breadth_metadata.py', ROOT/'scripts/validate_breadth_batch.py',
        ROOT/'tests/test_breadth_batch.py', ROOT/'REPRESENTATION-REVIEW.md',
        OUT.parent/'pilot-evidence.json', OUT.parent/'capitalism-evidence.json',
        OUT.parent/'raw/pilot_passages_02.txt']
    inputs += [p for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json']
    write('manifest.json',dict(as_of=DAY, status='staging_only', files={
        str(p.relative_to(ROOT)):digest(p) for p in sorted(set(inputs))}))


if __name__ == '__main__':
    data, refs, authors=build()
    write('batch.json',data)
    write('reference-leads.json',refs)
    write('credit-observations.json',authors)
    render(data,refs,authors)
    manifest()
    print(json.dumps(read(OUT/'summary.json'),indent=2))
