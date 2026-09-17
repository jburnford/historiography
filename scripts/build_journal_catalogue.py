#!/usr/bin/env python3
"""Build the journal discovery graph from saved, attributable inputs; no network/API calls."""
import csv
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
try:
    from .journal_subject_batches import apply_accepted_batches
    from .journal_metadata_batches import apply_accepted_metadata
    from .journal_venue_batches import apply_accepted_venues
except ImportError:
    from journal_subject_batches import apply_accepted_batches
    from journal_metadata_batches import apply_accepted_metadata
    from journal_venue_batches import apply_accepted_venues

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/journal-catalogue'
AS_OF = '2026-09-13'


def normalized_title(title):
    text = unicodedata.normalize('NFKD', title.casefold().replace('&', ' and '))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'^the\s+', '', text)
    return ''.join(c for c in text if c.isalnum())


def stable_id(prefix, key):
    return prefix + '_' + hashlib.sha256(key.encode()).hexdigest()[:16]


def read_json(name):
    return json.loads((DATA / name).read_text())


def make_catalogue():
    aliases = read_json('title-aliases.json')
    alias_map = {normalized_title(k): v for k, v in aliases['aliases'].items()}
    ambiguous = {normalized_title(t) for t in aliases['ambiguous_titles']}
    wiki = read_json('wikipedia-seed.json')
    toronto = read_json('toronto-seed.json')
    sources = [
        dict(id='journal_source_wikipedia', title='Wikipedia: List of history journals',
             url=wiki['source_url'], revision_url=wiki['revision_url'], checked_on=AS_OF,
             verification='directory_read', note=wiki['limitation'], attribution=wiki['license']),
        dict(id='journal_source_sheet_271', title='User-supplied spreadsheet: 271 title rows',
             url='https://docs.google.com/spreadsheets/d/1Gp-wHW0Sxqas38YteBk3uennT-kjpP32XOjf_wC8WZs/edit?gid=0',
             checked_on=AS_OF, verification='csv_read', note='Titles only. Original compiler, selection rules and reuse license not established; no PJIP affiliation assumed.'),
        dict(id='journal_source_sheet_1389', title='User-supplied spreadsheet: 1,389 title rows',
             url='https://docs.google.com/spreadsheets/d/1-d7jkVFvQ-OUqyrOJgow7-ocCzpU26QRAre3ciw8a3Q/edit?gid=641273133',
             checked_on=AS_OF, verification='csv_read', note='Titles only, including a repeated title. No country, language, ISSN, publisher or scope columns; no PJIP affiliation assumed.'),
        dict(id='journal_source_ooir', title='User transcription attributed to OOIR: approximate Impact Factor 2025',
             url='https://ooir.org/journals.php?field=History+%26+Archaeology&category=History&metric=jif',
             checked_on=None, verification='user_transcription', note='Source page returned HTTP 403. Values retain the user’s approximate 2025 label; they are not independently verified JCR figures or quality tiers.'),
        dict(id='journal_source_toronto', title='University of Toronto Libraries: Collections and Resources on China — Journals',
             url=toronto['source_url'], checked_on=AS_OF, verification='directory_read', note=toronto['verification_note']),
        dict(id='journal_source_pjip', title='Practical Journal Insight Project: History',
             url='https://www.pjip.org/subjects/history', checked_on=AS_OF, verification='page_shell_only',
             note='Page identifies a 2026 ranking and CC BY-NC 4.0 reuse terms. Journal table rows were unavailable; no PJIP records imported.')
    ]
    raw_inputs = [('raw/user-sheet-271.csv', 'journal_source_sheet_271'),
                  ('raw/user-sheet-1389.csv', 'journal_source_sheet_1389'),
                  ('raw/ooir-user-transcription.tsv', 'journal_source_ooir')]
    for path, sid in raw_inputs:
        src = next(s for s in sources if s['id'] == sid)
        src.update(input_file=path, sha256=hashlib.sha256((DATA / path).read_bytes()).hexdigest())
    sources[0]['html_sha256'] = wiki['html_sha256']
    sources[4]['html_sha256'] = toronto['html_sha256']
    records, subjects, classifications = {}, {}, {}
    edges, title_relationships = [], []

    def add(title, sid, row, url=None, resource_kind='periodical_candidate', identity_hint=None):
        canonical = alias_map.get(normalized_title(title), title)
        key = normalized_title(canonical)
        unresolved = key in ambiguous
        if unresolved:
            key += '|' + (identity_hint or sid)
        if key not in records:
            records[key] = dict(id=stable_id('journal', key), entry_kind='periodical', label=canonical,
                aliases=[], source_ids=[], occurrences=[], urls=[], publication_role=resource_kind,
                identity_status='ambiguous_title' if unresolved else 'title_matched_candidate',
                issns=[], publication_start=None, publication_end=None, publication_status='unknown',
                chronology_note='Publication dates unverified. Catalogue inclusion as of 2026 is not a founding or cessation date.',
                languages=[], publisher_country=None)
        rec = records[key]
        if title not in rec['aliases']: rec['aliases'].append(title)
        if sid not in rec['source_ids']: rec['source_ids'].append(sid)
        rec['occurrences'].append(dict(source_id=sid, row=row, title=title))
        if url and url not in rec['urls']: rec['urls'].append(url)
        if resource_kind != 'periodical_candidate': rec['publication_role'] = resource_kind
        return rec

    def subject(path, sid):
        key = ' / '.join(path)
        ident = stable_id('journal_subject', key)
        if ident not in subjects:
            subjects[ident] = dict(id=ident, entry_kind='publication_subject', label=path[-1],
                                  category_path=path, source_ids=[])
        if sid not in subjects[ident]['source_ids']: subjects[ident]['source_ids'].append(sid)
        return ident

    def classify(journal, target, sid, basis, note):
        ident = stable_id('journal_classification', journal['id'] + '|' + target + '|' + basis)
        if ident not in classifications:
            classifications[ident] = dict(id=ident, journal_id=journal['id'], subject_id=target,
                basis=basis, source_ids=[],
                evidence_note=note, checked_on=AS_OF)
        if sid not in classifications[ident]['source_ids']: classifications[ident]['source_ids'].append(sid)

    for item in wiki['journals']:
        for row, occurrence in enumerate(item['occurrences'], 1):
            path = occurrence['category_path']
            rec = add(occurrence['title'], 'journal_source_wikipedia',
                      item['seed_key'] + ':' + str(row), occurrence['url'], identity_hint=occurrence['url'])
            classify(rec, subject(path, 'journal_source_wikipedia'),
                 'journal_source_wikipedia', 'directory_category',
                 'Wikipedia directory placement. This records indexing, not independently verified publisher remit, current activity or an intellectual affiliation.')

    for filename, sid in raw_inputs[:2]:
        for row, fields in enumerate(csv.reader(io.StringIO((DATA / filename).read_text())), 1):
            if fields and fields[0].strip(): add(fields[0].strip(), sid, row)

    for row, fields in enumerate(csv.DictReader(io.StringIO((DATA / raw_inputs[2][0]).read_text()), delimiter='\t'), 2):
        add(fields['title'], 'journal_source_ooir', row)

    discovery_resources = []
    for row, item in enumerate(toronto['entries'], 1):
        if item['resource_kind'] in ('research_journal', 'primary_source_periodical'):
            rec = add(item['title'], 'journal_source_toronto', row, item['url'], item['resource_kind'])
            classify(rec, subject(['Library guide', 'Chinese studies resources'], 'journal_source_toronto'),
                 'journal_source_toronto', 'library_guide',
                 'Included in a Chinese-studies resource guide. This does not establish language, country of publication, or that a historical source magazine publishes historical scholarship.')
        else:
            discovery_resources.append(dict(id=stable_id('journal_resource', item['url']),
                **item, source_ids=['journal_source_toronto'], access_status='not_checked'))

    for check in read_json('publisher-checks.json')['checks']:
        rec = add(check['title'], check['source_id'], 'publisher_about', check['url'], 'research_journal')
        rec['issns'] = check['issns']
        rec['identity_status'] = 'publisher_metadata_checked'
        if check['source_id'] == 'journal_source_jstor_jnh':
            rec['identity_status'] = 'bibliographic_metadata_checked'
        for key in ('date_span', 'publication_events', 'archive_coverage'):
            if key in check: rec[key] = check[key]
        if 'date_span' in rec:
            rec['date_span'] = {**rec['date_span'], 'source_ids': [check['source_id']]}
            rec['publication_start'] = rec['date_span']['start']
            rec['publication_end'] = rec['date_span']['end']
            rec['chronology_note'] = check['note']
            if rec['date_span']['end_kind'] == 'title_change': rec['publication_status'] = 'title_changed'
        sources.append(dict(id=check['source_id'], title=check['title'] + ': publisher remit',
                            url=check['url'], checked_on=AS_OF,
                            verification='bibliographic_record_read' if check['source_id']=='journal_source_jstor_jnh' else 'publisher_scope_read', note=check['note']))
        for target in check['atlas_node_ids']:
            classify(rec, target, check['source_id'],
                 'bibliographic_subject_index' if check['source_id']=='journal_source_jstor_jnh' else 'publisher_scope', check['note'])
        for path in check.get('subject_paths', []):
            classify(rec, subject(path, check['source_id']), check['source_id'], 'publisher_scope', check['note'])
    for check in read_json('publisher-checks.json')['checks']:
        if check.get('successor_title'):
            rec = records[normalized_title(check['title'])]
            successor = records[normalized_title(check['successor_title'])]
            title_relationships.append(dict(id=stable_id('title_history',rec['id']+'|'+successor['id']),
                predecessor=rec['id'], successor=successor['id'], changed_in=2002,
                source_ids=[check['source_id']], evidence_note=check['note']))

    venue_data = read_json('venue-relationships.json')
    sources.extend(venue_data['sources'])
    for claim in venue_data['relationships']:
        rec = add(claim['journal_title'], claim['source_ids'][0], 'venue_claim', resource_kind='research_journal')
        edge = {k:v for k,v in claim.items() if k not in ('journal_title','publication_start')}
        edge.update(source=rec['id'], directed=True, checked_on=AS_OF)
        edges.append(edge)
        if claim.get('publication_start') is not None:
            rec['publication_start'] = claim['publication_start']
            rec['date_span'] = dict(start=claim['publication_start'], end=None, precision='year',
                start_kind='publication_start', end_kind='unknown', open_end=None,
                basis='source_check', source_ids=claim['source_ids'])
            rec['chronology_note'] = 'Founding year checked; cessation and continuity not established by this record.'

    # Correspondences are deliberately sparse: a directory topic is not a school affiliation.
    correspondences = {
        'By topic / Environment': ['environment'], 'By topic / Military': ['military'],
        'By topic / Demography and family': ['demography'],
        'By period / Comparative and world': ['global'],
        'By region / Africa': ['africanhist']
    }
    for sub in subjects.values():
        sub['atlas_node_ids'] = correspondences.get(' / '.join(sub['category_path']), [])
        sub['mapping_note'] = ('Editorial correspondence in subject matter, not evidence of school membership or historical influence.'
                               if sub['atlas_node_ids'] else 'No direct correspondence assigned. May be partly covered in existing entries; review before adding a new field.')

    nodes = sorted(list(records.values()) + list(subjects.values()), key=lambda r: (r['entry_kind'], r['label'].casefold(), r['id']))
    catalogue = dict(schema_version='1.0', as_of=AS_OF,
        scope='Broad journal and periodical discovery inventory, including titles beyond 2000. Not a complete worldwide census or a list of verified active research journals.',
        identity_policy='Conservative normalized-title matching plus explicit aliases; no fuzzy automatic merges. Ambiguous short titles remain source-specific candidates. ISSN authority reconciliation pending.',
        interpretation_note='Only specific founding, debate and sustained principal-venue claims are visual edges. Subject classifications and title histories are metadata. Degree is not a quality ranking or evidence that a field lacks disagreement. Impact factors do not determine inclusion or prominence.',
        nodes=nodes, edges=edges, subject_classifications=list(classifications.values()),
        title_relationships=title_relationships, sources=sources, discovery_resources=discovery_resources)
    return apply_accepted_venues(apply_accepted_metadata(apply_accepted_batches(catalogue, DATA), DATA), DATA)


def make_audit(catalogue):
    journals = [n for n in catalogue['nodes'] if n['entry_kind'] == 'periodical']
    subjects = [n for n in catalogue['nodes'] if n['entry_kind'] == 'publication_subject']
    classifications = catalogue['subject_classifications']
    linked = {e['journal_id'] for e in classifications}
    checked = {e['journal_id'] for e in classifications if e.get('status','checked')=='checked'}
    provisional = {e['journal_id'] for e in classifications if e.get('status')=='provisional'}
    groups = []
    for sub in subjects:
        ids = sorted({e['journal_id'] for e in classifications if e['subject_id'] == sub['id']})
        checked_ids = {e['journal_id'] for e in classifications if e['subject_id']==sub['id'] and e.get('status','checked')=='checked'}
        provisional_ids = {e['journal_id'] for e in classifications if e['subject_id']==sub['id'] and e.get('status')=='provisional'}
        groups.append(dict(subject_id=sub['id'], category_path=sub['category_path'],
                           journal_count=len(ids), checked_journal_count=len(checked_ids),
                           provisional_only_journal_count=len(provisional_ids-checked_ids),
                           journal_ids=ids, atlas_node_ids=sub['atlas_node_ids']))
    occurrences = Counter(o['source_id'] for j in journals for o in j['occurrences'])
    reviewed_on = max([catalogue.get('metadata_reviewed_on') or AS_OF] +
                      [e.get('checked_on') or AS_OF for e in catalogue['edges']])
    return dict(as_of=reviewed_on, periodical_candidates=len(journals), publication_subjects=len(subjects),
        bibliographic_metadata_periodicals=sum(bool(j.get('bibliographic_evidence')) for j in journals),
        periodicals_with_issns=sum(bool(j.get('issns')) for j in journals),
        periodicals_with_publication_start=sum(j.get('publication_start') is not None for j in journals),
        catalogued_title_starts=sum(j.get('date_span', {}).get('start_kind')=='catalogued_title_start' for j in journals),
        periodicals_with_library_subject_headings=sum(any(r.get('subjects') for r in j.get('bibliographic_evidence', [])) for j in journals),
        periodicals_with_languages=sum(bool(j.get('languages')) for j in journals),
        source_occurrences=dict(occurrences), relationships=len(catalogue['edges']),
        relationship_kinds=dict(Counter(e['relationship_kind'] for e in catalogue['edges'])),
        subject_classifications=len(classifications),
        checked_classification_rows=sum(e.get('status','checked')=='checked' for e in classifications),
        provisional_classification_rows=sum(e.get('status')=='provisional' for e in classifications),
        superseded_provisional_rows=len(catalogue.get('superseded_subject_classifications', [])),
        unresolved_source_check_attempts=len(catalogue.get('source_check_attempts', [])),
        checked_classified_periodicals=len(checked),
        provisional_only_periodicals=len(provisional-checked),
        classification_review_outcomes=dict(Counter(r['outcome'] for r in catalogue.get('classification_reviews',[]))),
        directory_classified_periodicals=len({e['journal_id'] for e in classifications if e['basis'] in ('directory_category','library_guide')}),
        publisher_scope_checked_periodicals=len({e['journal_id'] for e in classifications if e['basis']=='publisher_scope'}),
        unclassified_journal_ids=[j['id'] for j in journals if j['id'] not in linked],
        ambiguous_title_ids=[j['id'] for j in journals if j['identity_status']=='ambiguous_title'],
        discovery_resources=len(catalogue['discovery_resources']), subjects=groups,
        limitations=['Counts refer to candidate records, not authority-deduplicated journals.',
                    'Checked classifications include directory categories and scoped index evidence, not only publisher remit checks.',
                    'Provisional title classifications are discovery suggestions; publisher scope remains unverified.',
                    'Missing atlas correspondences flag a review task, not proven absence of all related scholarship.',
                    'Language and publisher country remain unknown unless evidenced. Region studied is a separate concept.',
                    'Do not remove unclassified or non-Western titles because they do not fit the current atlas.',
                    'Historical primary-source periodicals remain distinct from venues publishing historical research.'])


def write_outputs(catalogue):
    audit = make_audit(catalogue)
    for path, obj in [(DATA / 'catalogue.json', catalogue), (ROOT / 'feedback/journals/import-audit.json', audit)]:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    by_id = {n['id']:n for n in catalogue['nodes']}
    with (DATA / 'catalogue.csv').open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['id','title','aliases','publication_role','identity_status','publication_start','publication_end','publication_status','checked_subject_classifications','provisional_subject_classifications','source_ids','issns','languages','date_basis','date_start_kind','bibliographic_record_count','library_subject_heading_count'])
        for journal in catalogue['nodes']:
            if journal['entry_kind']!='periodical': continue
            subjects = {status:[by_id.get(c['subject_id'],{}).get('label',c['subject_id']) for c in catalogue['subject_classifications'] if c['journal_id']==journal['id'] and c.get('status','checked')==status] for status in ('checked','provisional')}
            evidence = journal.get('bibliographic_evidence', [])
            span = journal.get('date_span', {})
            writer.writerow([journal['id'],journal['label'],' | '.join(journal['aliases']),journal['publication_role'],journal['identity_status'],journal['publication_start'],journal['publication_end'],journal['publication_status'],' | '.join(subjects['checked']),' | '.join(subjects['provisional']),' | '.join(journal['source_ids']),' | '.join(journal.get('issns', [])),' | '.join(journal.get('languages', [])),span.get('basis',''),span.get('start_kind',''),len(evidence),sum(len(r.get('subjects', [])) for r in evidence)])
    text = ['# Journal inventory and coverage review', '',
            f"As of {audit['as_of']}: {audit['periodical_candidates']} candidate periodicals; {audit['publication_subjects']} publication subjects; {audit['relationships']} relationships.", '',
            f"Reviewed bibliographic profiles: {audit['bibliographic_metadata_periodicals']}. ISSNs: {audit['periodicals_with_issns']}. Publication starts: {audit['periodicals_with_publication_start']} (including {audit['catalogued_title_starts']} catalogued title/edition starts, not verified founding dates). Library subject headings: {audit['periodicals_with_library_subject_headings']}.", '',
            f"Source-checked classification: {audit['checked_classified_periodicals']} candidates. Provisional title evidence only: {audit['provisional_only_periodicals']}. No classification: {len(audit['unclassified_journal_ids'])}.", '',
            'Provisional classifications are title-based suggestions, not publisher remit checks. They must stay separately identifiable in filters and exports. Regional counts below include both statuses and are discovery leads, not a verified distribution of journal remits.', '',
            '## Regional and subject review queue', '',
            'These source classifications can reveal missing fields and traditions. No direct atlas correspondence means review is needed; it does not prove that related material is absent from all existing notes.', '',
            '| Subject | Source-checked candidates | Provisional-only candidates | Existing atlas correspondence |',
            '| --- | ---: | ---: | --- |']
    for s in audit['subjects']:
        text.append(f"| {' / '.join(s['category_path'])} | {s['checked_journal_count']} | {s['provisional_only_journal_count']} | {', '.join(s['atlas_node_ids']) or 'Review coverage'} |")
    text += ['', '## Remaining data work', '',
             '- Reconcile ISSNs, translated titles and historical title changes; preserve candidate IDs and aliases.',
             '- Check publisher scope for unclassified and provisionally classified titles, prioritizing regional and language gaps over impact-factor rank.',
             '- Use the Toronto guide’s Chinese, Taiwanese and Hong Kong discovery resources to find further research journals; databases and collections are not individual journals.',
             '- Record language of publication, publisher location, region studied and historiographical tradition separately.',
             '- Verify publication dates and current status. Catalogue year 2026 must never become a journal’s founding year or an assumed end date.',
             '- Expand the atlas only after researching the traditions indicated by these venues. A journal title is a lead, not evidence for an intellectual genealogy.', '']
    (ROOT / 'feedback/journals/coverage-review.md').write_text('\n'.join(text))
    print(json.dumps({k:v for k,v in audit.items() if k not in ('subjects','unclassified_journal_ids','ambiguous_title_ids','limitations')}, indent=2))


if __name__ == '__main__':
    write_outputs(make_catalogue())
