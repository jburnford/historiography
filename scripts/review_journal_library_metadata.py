#!/usr/bin/env python3
"""Stage conservative field-level library reconciliation from frozen saved evidence.

No network calls and no acceptance-manifest or authoritative-graph mutations.
Review staged output before hash-pinning it into the catalogue build.
"""
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import re

try:
    from .library_journal_records import title_key, issn
    from .journal_metadata_batches import fingerprint
    from .journal_subject_batches import ident
except ImportError:
    from library_journal_records import title_key, issn
    from journal_metadata_batches import fingerprint
    from journal_subject_batches import ident

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/journal-catalogue'
LIB = DATA / 'library-metadata'
OUT = DATA / 'metadata-review-2026-09-15'
DATE = '2026-09-15'

# Reviewed broad mappings of explicit LCSH main headings. Subdivisions alone do
# not establish broad scope (especially FAST's detached "History" subdivision).
HEADINGS = {
    'General history': ['History'],
    'Archaeology': ['Archaeology', 'Excavations (Archaeology)', 'Antiquities'],
    'Anthropology and ethnography': ['Anthropology', 'Ethnology', 'Ethnology and ethnography'],
    'Archives': ['Archives'],
    'Art': ['Art', 'Art, Modern', 'Art, European', 'Art, Medieval'],
    'Architectural': ['Architecture'],
    'Biography and life writing': ['Biography', 'Autobiography'],
    'Business, labor and economics': ['Economic history', 'Economics', 'Business', 'Industries', 'Labor', 'Accounting'],
    'Classical studies': ['Classical philology', 'Classical antiquities', 'Classical literature'],
    'Cultural history': ['Cultural history'],
    'Cultural studies': ['Culture', 'Popular culture'],
    'Demography and family': ['Demography', 'Population', 'Families', 'Family'],
    'Diaspora and migration': ['Emigration and immigration', 'Immigrants', 'Migration, Internal'],
    'Dress and textile': ['Clothing and dress', 'Textile fabrics'],
    'Education': ['Education', 'Higher education'],
    'Environment': ['Environmental history', 'Human ecology', 'Environmental sciences'],
    'Folklore': ['Folklore'],
    'Food history': ['Food', 'Food habits'],
    'Genocide': ['Genocide', 'Holocaust, Jewish (1939-1945)'],
    'Geography': ['Geography', 'Historical geography'],
    'Heritage and public history': ['Public history', 'Historic preservation', 'Cultural property'],
    'Humanities': ['Humanities'],
    'Ideas and historiography': ['Historiography', 'Intellectual life', 'History of ideas'],
    'Islamic studies': ['Islam', 'Islamic civilization'],
    'Jewish studies': ['Jews', 'Judaism', 'Jewish civilization'],
    'Language and linguistics': ['Linguistics', 'Philology', 'Language and languages'],
    'Legal': ['Law', 'Canon law', 'Roman law', 'Comparative law'],
    'Literature': ['Literature', 'Comparative literature', 'French literature', 'English literature', 'Spanish literature'],
    'Manuscript studies': ['Manuscripts'],
    'Maritime': ['Navigation', 'Shipping', 'Naval history'],
    'Mathematics and logic': ['Mathematics', 'Logic'],
    'Media and books': ['Books', 'Book industries and trade', 'Printing', 'Mass media', 'Journalism'],
    'Medicine and health': ['Medicine', 'Medical care', 'Public health'],
    'Memory studies': ['Collective memory'],
    'Military': ['Military history', 'Military art and science', 'War', 'Naval history'],
    'Music': ['Music', 'Musicology'],
    'Papyrology': ['Papyrology', 'Manuscripts, Greek (Papyri)'],
    'Philosophy': ['Philosophy'],
    'Politics and public policy': ['Political science', 'Political sociology', 'Political culture'],
    'Religion': ['Religion', 'Church history', 'Theology', 'Christianity', 'Buddhism'],
    'Rhetoric': ['Rhetoric'],
    'Rural and agricultural': ['Agriculture', 'Agriculture and state', 'Rural development'],
    'Science and technology': ['Science', 'Technology', 'Life sciences', 'Natural history'],
    'Slavic studies': ['Slavic philology', 'Slavs'],
    'Social': ['Social history'],
    'Social sciences': ['Social sciences'],
    'Socialism and related political traditions': ['Socialism', 'Communism'],
    'Sociology': ['Sociology'],
    'Sport': ['Sports'],
    'Transport and tourism': ['Transportation', 'Tourism'],
    'Urban': ['Cities and towns', 'City planning', 'Urbanization'],
    'Women and gender studies': ['Women', 'Feminism', 'Gender identity', 'Sex role'],
    'African American studies': ['African Americans'],
    'Indigenous studies': ['Indigenous peoples', 'Indians of North America', 'Indians of South America'],
    'International relations and diplomatic': ['International relations', 'World politics', 'Diplomacy'],
    'Ancient': ['History, Ancient'],
    'Middle Ages': ['Middle Ages', 'Civilization, Medieval'],
    'Modern and contemporary': ['History, Modern'],
    'Prehistory': ['Prehistoric peoples'],
    'Africa': ['Africa', 'South Africa', 'Southern Africa', 'West Africa', 'Africa, West', 'Africa, North'],
    'Americas': ['America'],
    'Asia': ['Asia'],
    'Asia Pacific': ['Pacific Area'],
    'Australasia and Oceania': ['Australia', 'New Zealand', 'Oceania'],
    'Britain': ['Great Britain', 'England', 'Scotland', 'Wales'],
    'Canada': ['Canada'],
    'Caucasus': ['Caucasus'],
    'Central Asia': ['Asia, Central'],
    'Central Europe': ['Europe, Central'],
    'East Asia': ['East Asia', 'China', 'Japan', 'Korea', 'Taiwan'],
    'Eastern Europe and Balkans': ['Europe, Eastern', 'Balkan Peninsula'],
    'Egypt': ['Egypt'],
    'Europe': ['Europe'],
    'France': ['France'],
    'German-speaking Europe': ['Germany', 'Austria'],
    'Greece': ['Greece'],
    'Iberia': ['Spain', 'Portugal', 'Iberian Peninsula'],
    'Ireland': ['Ireland'],
    'Italy': ['Italy'],
    'Latin America and Caribbean': ['Latin America', 'Caribbean Area', 'South America', 'Central America', 'Brazil', 'Argentina'],
    'Colombia': ['Colombia'],
    'Mexico': ['Mexico'],
    'Low Countries': ['Netherlands', 'Belgium', 'Benelux countries'],
    'Mediterranean': ['Mediterranean Region'],
    'Middle East': ['Middle East'],
    'Nordic Europe': ['Scandinavia', 'Sweden', 'Denmark', 'Norway', 'Finland', 'Iceland'],
    'Poland': ['Poland'],
    'Russia and Eurasia': ['Russia', 'Russia (Federation)', 'Soviet Union', 'Eurasia'],
    'South Asia': ['South Asia', 'India', 'Pakistan', 'Bangladesh', 'Sri Lanka'],
    'Southeast Asia': ['Southeast Asia', 'Indonesia', 'Vietnam', 'Thailand'],
    'Turkey': ['Turkey'],
    'United States': ['United States'],
    'Western Europe': ['Europe, Western'],
}

# Concrete homonyms / title-history risks found during review. Retain their
# saved evidence for targeted resolution, never force a catalogue merge.
IDENTITY_HOLDS = {
    'Accounting History': 'Matched record is Accounting history newsletter; current journal/title chronology needs separate evidence.',
    'Legal History Review': 'English translated-title hit identifies Japanese Hoseishi kenkyu, not necessarily the intended title.',
    'Dialogos': 'Short homonymous title; Romanian record cannot establish which Dialogos the seed intended.',
    'Contradictions': 'Short homonymous title; Belgian and other journals need source-occurrence resolution.',
}

# Individually read 362 statements and title relations; these decisions apply
# only to the listed saved records and never broaden title-history rules.
CHRONOLOGY_DECISIONS = {
    'journal_f945b16485034b24': {
        'year': 1941, 'record_key': 'loc:ecfbd3ce25098b41f3d18001', 'designation': 'v. 1- May 1941-',
        'note': 'LOC 362 identifies volume 1 in May 1941. The separate Tasks of economic history supplement/relation does not replace this explicit journal start.'},
    'journal_af9eb2a59f476770': {
        'year': 1964, 'record_key': 'loc:b2c8e0d51408948dbe13fd26', 'designation': 'Vol. 51, no. 1 (June 1964)-',
        'note': 'LOC 362 dates this title to volume 51, June 1964. The earlier Mississippi Valley historical review is a predecessor; 1964 is the current-title start, not the continuing journal’s foundation.'},
}


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main_title_matches(node, record):
    def key(t):
        return re.sub(r'^the ', '', title_key(t))
    names = {key(t) for t in [node['label'], *node.get('aliases', [])]}
    # Colon-delimited subtitles may be omitted from the catalogue title, but a
    # newsletter suffix, part name or predecessor title is never removed.
    return any(not t.get('parts') and (key(t['title']) in names or
               key(t['title'].split(' : ', 1)[0]) in names)
               for t in record['titles'] if t['type'] == 'primary')


def select_records(node, stages, oa, collisions):
    if node['identity_status'] == 'ambiguous_title':
        return [], None, 'Ambiguous source identities remain separate.'
    if node['label'] in IDENTITY_HOLDS:
        return [], None, IDENTITY_HOLDS[node['label']]
    names = {title_key(t) for t in [node['label'], *node.get('aliases', [])]}
    candidates = [s for s in oa.get('response', {}).get('results', [])
                  if s.get('type') == 'journal' and title_key(s.get('display_name') or '') in names]
    source = candidates[0] if len(candidates) == 1 and not oa['assessment']['truncated'] else None
    if source and source['id'] in collisions:
        source = None
    known = set(node.get('issns', []))
    hints = {i for value in ([*(source.get('issn') or []), source.get('issn_l')] if source else [])
             if value and (i := issn(value))}
    accepted = []
    for stage in stages:
        for record in stage.get('records', []):
            if (record.get('serial') and record.get('record_level') == 'bibliographic'
                    and main_title_matches(node, record) and set(record['issns']) & (known or hints)):
                accepted.append(record)
    return accepted, source, '' if accepted else 'No unambiguous primary-title and own-ISSN concordance in saved records.'


def date_decision(node, records):
    if node.get('date_span') or node.get('publication_start') is not None or node.get('publication_end') is not None:
        return None, 'Preserve existing sourced chronology.'
    starts = [d for r in records for d in r['date_candidates'] if d['point'] == 'start']
    years = {d['year'] for d in starts if d['usable_exact_year']}
    if len(years) != 1 or any(not d['usable_exact_year'] for d in starts):
        return None, 'Missing, uncertain or conflicting title-start observations.'
    if any(d.get('event_type') not in (None, 'publication') for d in starts):
        return None, 'Non-publication origin dates require review.'
    year = next(iter(years))
    if node.get('archive_coverage'):
        return None, 'Existing archive coverage requires title/format reconciliation.'
    decision = CHRONOLOGY_DECISIONS.get(node['id'])
    if decision and year == decision['year'] and any(r['record_key'] == decision['record_key'] and
            any(n.get('type') == 'date/sequential designation' and n['value'] == decision['designation']
                for n in r.get('notes', [])) for r in records):
        return year, decision['note']
    # Broad identifiers sometimes cover earlier titles. Do not silently turn
    # the first date of a former-title span into this catalogue title's start.
    if any(item.get('type') in ('preceding', 'succeeding', 'continues', 'continuedBy')
           for r in records for item in r.get('related_items', [])):
        return None, 'Predecessor/successor relations require chronology review.'
    return year, 'Single exact catalogued title-start year; not a verified foundation date.'


def subject_paths(catalogue):
    result = {}
    for n in catalogue['nodes']:
        if n['entry_kind'] != 'publication_subject':
            continue
        if n['label'] == 'Middle Ages' and n['category_path'][0] != 'By period':
            continue
        result[n['label']] = n['category_path']
    return {label: result[label] for label in HEADINGS}


def reviewed_subjects(record):
    if 'marc' not in record:
        return record['subjects']
    subjects = []
    for field in record['marc']['datafields']:
        # MARC 655 is genre/form, including place of publication. It cannot
        # support a region-studied classification even when labelled LCSH.
        if field['tag'] not in ('650', '651'):
            continue
        authority = 'lcsh' if field['ind2'] == '0' else next(
            (s['value'] for s in field['subfields'] if s['code'] == '2'), 'unrecorded')
        components = [{'kind': {'a': 'geographic' if field['tag'] == '651' else 'topic',
                        'v': 'genre', 'x': 'topic', 'y': 'temporal', 'z': 'geographic'}[s['code']],
                       'value': s['value']} for s in field['subfields'] if s['code'] in 'avxyz']
        subjects.append({'authority': authority, 'components': components})
    return subjects


def mapped_headings(record, paths):
    mappings = []
    for subject in reviewed_subjects(record):
        if subject.get('authority') != 'lcsh' or not subject['components']:
            continue
        if subject['components'][0].get('kind', 'topic') not in ('topic', 'geographic'):
            continue
        head = title_key(subject['components'][0]['value'])
        for label, terms in HEADINGS.items():
            if head not in {title_key(t) for t in terms}:
                continue
            if paths[label][0] == 'By region' and subject['components'][0].get('kind') != 'geographic':
                continue
            # A record indexed by a narrower history (e.g. History--Study and
            # teaching) is retained verbatim rather than broadened to all history.
            if label == 'General history' and any(title_key(c['value']) != 'periodicals'
                                                  for c in subject['components'][1:]):
                continue
            if label == 'Food history' and not any(title_key(c['value']) == 'history'
                                                   for c in subject['components'][1:]):
                continue
            mappings.append((paths[label], subject))
    return mappings


def stage_review():
    snapshot = ROOT / 'drafts/historiography-1920-2000.v1.110.json'
    catalogue = read(snapshot)['journal_catalogue']
    plan = read(LIB / 'plan.json')
    if hashlib.sha256((json.dumps(catalogue, ensure_ascii=False, indent=2)+'\n').encode()).hexdigest() != plan['catalogue_sha256']:
        raise ValueError('Library snapshot differs from preserved catalogue')
    queue = {e['node']['id']: e for e in plan['queue']}
    oa_audit = read(ROOT / 'feedback/journals/openalex-metadata-full-audit.json')
    collisions = oa_audit['cross_candidate_source_collisions']
    paths = subject_paths(catalogue)
    stage_hashes, raw_hashes = {}, {}
    selected = {}
    reviews = []
    for node in catalogue['nodes']:
        if node['entry_kind'] != 'periodical':
            continue
        jid = node['id']
        stages = []
        for provider in ('loc', 'harvard'):
            path = LIB / 'records' / provider / (jid + '.json')
            stage = read(path)
            if stage['catalogue_sha256'] != plan['catalogue_sha256'] or stage['plan_fingerprint'] != fingerprint(queue[jid]):
                raise ValueError('Staging snapshot mismatch')
            stage_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
            stages.append(stage)
        op = DATA / 'openalex-metadata-staging' / (jid + '.json')
        oa = read(op)
        if oa['catalogue_sha256'] != plan['catalogue_sha256']:
            raise ValueError('OpenAlex staging snapshot mismatch')
        stage_hashes[str(op.relative_to(ROOT))] = hashlib.sha256(op.read_bytes()).hexdigest()
        records, source, reason = select_records(node, stages, oa, collisions)
        selected[jid] = (node, stages, records, source)
        reviews.append(dict(journal_id=jid, title=node['label'], outcome='eligible' if records else 'deferred',
                            reason=reason, selected_record_keys=[r['record_key'] for r in records],
                            retrieval_exceptions=[{'provider': s['provider'], 'status': s['status'],
                                'truncated': s.get('truncated', False)} for s in stages
                                if s['status'] != 'retrieved' or s.get('truncated')]))
    # Reject cross-candidate library identifier reuse too, even if OpenAlex's
    # candidate-selection report did not flag it.
    owners = defaultdict(set)
    for jid, (_, _, records, _) in selected.items():
        for r in records:
            for value in r['issns']:
                owners[value].add(jid)
    shared = {k: sorted(v) for k, v in owners.items() if len(v) > 1}
    blocked = {jid for ids in shared.values() for jid in ids}
    sources, updates, classifications = {}, [], {}
    all_rows = catalogue['subject_classifications']
    existing_classifications = {r['id'] for r in all_rows}
    old_checked = {(r['journal_id'], r['subject_id']) for r in all_rows if r.get('status', 'checked') == 'checked'}
    for review in reviews:
        jid = review['journal_id']
        node, stages, records, source = selected[jid]
        if jid in blocked:
            review.update(outcome='deferred', reason='Library ISSN shared with another catalogue candidate; resolve before import.')
            continue
        if not records:
            continue
        evidence, source_ids = [], []
        for record in records:
            st = next(s for s in stages if s['provider'] == record['provider'])
            provenances = [a['provenance'] for a in st['attempts'] if a.get('provenance', {}).get('sha256') in record['retrieved_via']]
            if not provenances:
                raise ValueError('Record has no raw evidence provenance')
            for prov in provenances:
                p = ROOT / prov['raw_file']
                if hashlib.sha256(p.read_bytes()).hexdigest() != prov['sha256']:
                    raise ValueError('Raw evidence hash mismatch')
                raw_hashes[str(p.relative_to(ROOT))] = prov['sha256']
            sid = ident('journal_source_library', record['record_key'])
            sources[sid] = dict(id=sid, title=f"{record['provider'].upper()} bibliographic record: {node['label']}",
                url=provenances[0]['url'], checked_on=DATE, verification='bibliographic_metadata_checked',
                record_key=record['record_key'], evidence_sha256=sorted(set(record['retrieved_via'])),
                note='Primary title and own ISSN concordance reviewed against catalogue identifiers or a unique exact-title OpenAlex journal candidate. Library headings describe cataloguing scope, not exhaustive publisher remit. Title/format chronology and shared cataloguing provenance remain distinct.')
            source_ids.append(sid)
            proof = dict(basis='catalogue_issn_and_primary_title' if node['issns'] else 'openalex_primary_title_issn_and_library_primary_title',
                         matched_issns=sorted(set(record['issns']) & (set(node['issns']) or
                            {v for v in [*(source.get('issn') or []), source.get('issn_l')] if v})))
            if not node['issns']:
                proof.update(openalex_source_id=source['id'], openalex_display_name=source['display_name'],
                             openalex_staging_sha256=stage_hashes[str((DATA/'openalex-metadata-staging'/(jid+'.json')).relative_to(ROOT))])
            evidence.append(dict(source_ids=[sid], provider=record['provider'], record_key=record['record_key'],
                record_identifiers=record['record_identifiers'], identifiers=record['identifiers'], titles=record['titles'],
                issns=record['issns'], origins=record['origins'], languages=record['languages'],
                subjects=reviewed_subjects(record), related_items=record['related_items'],
                date_observations=record['date_candidates'],
                chronology_notes=[n for n in record['notes'] if n.get('type') in ('date/sequential designation', 'MARC 515', 'MARC 588')],
                identity_review=proof, note='Attributed bibliographic observations. Related-title identifiers and holdings coverage are not this title’s identifiers or lifespan. No independent-source claim.'))
            for path, heading in mapped_headings(record, paths):
                subid = ident('journal_subject', ' / '.join(path))
                cid = ident('journal_classification', jid+'|'+subid+'|bibliographic_subject_index')
                if cid in existing_classifications or (jid, subid) in old_checked:
                    continue
                row = classifications.setdefault(cid, dict(journal_id=jid, subject_path=path,
                    basis='bibliographic_subject_index', status='checked', source_ids=[], evidence_note='', headings=[]))
                if sid not in row['source_ids']:
                    row['source_ids'].append(sid)
                heading_text = ' -- '.join(c['value'] for c in heading['components'])
                if heading_text not in row['headings']:
                    row['headings'].append(heading_text)
        year, reason = date_decision(node, records)
        fields = {'bibliographic_evidence': evidence}
        if not node['issns']:
            fields['issns'] = sorted({v for r in records for v in r['issns']})
        if not node['languages']:
            languages = sorted({v['value'] for r in records for v in r['languages']
                                if v.get('type') == 'code' and re.fullmatch('[a-z]{3}', v['value'])
                                and v['value'] not in ('und', 'zxx', 'mul')})
            if languages:
                fields['languages'] = languages
        if node['identity_status'] == 'title_matched_candidate':
            fields['identity_status'] = 'bibliographic_metadata_checked'
        if year is not None:
            date_sources = [e['source_ids'][0] for e in evidence if any(d['point']=='start' and d['usable_exact_year'] for d in e['date_observations'])]
            fields.update(publication_start=year, date_span=dict(start=year, end=None, precision='year',
                start_kind='catalogued_title_start', end_kind='unknown', open_end=None,
                basis='bibliographic_record', source_ids=date_sources),
                chronology_note='Library catalogue start for the matched title/edition; not independently verified founding. Cessation and current activity remain unknown. Holdings and OpenAlex indexed ranges are separate. '+reason)
        review.update(outcome='reviewed_bibliographic_identity', date_action='add_catalogued_title_start' if year else 'preserve_or_defer',
                      date_reason=reason, proposed_start=year, fields_added=sorted(fields))
        updates.append(dict(journal_id=jid, expected_node_fingerprint=fingerprint(node), source_ids=source_ids, fields=fields))
    for row in classifications.values():
        row['evidence_note'] = ('Reviewed LCSH main heading(s): ' + '; '.join(row.pop('headings')) +
            '. Supports the stated broad subject category as bibliographic indexing, not exclusive or historical publisher remit. No atlas affiliation inferred.')
    replacements = []
    classified = {(r['journal_id'], ident('journal_subject', ' / '.join(r['subject_path']))) for r in classifications.values()}
    for row in all_rows:
        if row.get('status') == 'provisional' and (row['journal_id'], row['subject_id']) in classified:
            replacements.append(row['id'])
    subject_sources = {s for row in classifications.values() for s in row['source_ids']}
    subject_batch = dict(batch_id='root-web-005', checked_on=DATE,
        sources=[sources[s] for s in sorted(subject_sources)], classifications=list(classifications.values()),
        unresolved=[], replaces_provisional_ids=replacements,
        reviewed_journal_ids=sorted({r['journal_id'] for r in classifications.values()}))
    metadata_batch = dict(batch_id='root-library-001', checked_on=DATE,
        source_catalogue_sha256=plan['catalogue_sha256'], sources=list(sources.values()), updates=updates)
    audit = dict(reviewed_on=DATE, source_catalogue_sha256=plan['catalogue_sha256'],
        policy='Conservative primary-title and own-ISSN concordance, cross-candidate collision rejection, literal LCSH main-heading mappings, protected existing dates and deferred title histories. Full initial inventory screened; exceptions retain next work.',
        counts=dict(candidates_reviewed=len(reviews), bibliographic_identities=len(updates),
            catalogue_start_additions=sum('date_span' in u['fields'] for u in updates),
            issn_additions=sum('issns' in u['fields'] for u in updates),
            language_additions=sum('languages' in u['fields'] for u in updates),
            checked_subject_rows=len(classifications), subject_candidates=len(subject_batch['reviewed_journal_ids']),
            superseded_provisional_rows=len(replacements), deferred_identities=sum(r['outcome']=='deferred' for r in reviews)),
        openalex_collisions=collisions, library_issn_collisions=shared, reviews=reviews,
        stage_sha256=stage_hashes, used_raw_sha256=raw_hashes,
        next_step='Resolve deferred identities, translated/alternate titles and title-history dates; inspect unmapped headings and retrieve targeted evidence where saved records cannot resolve the issue.')
    write(OUT / 'root-library-001.json', metadata_batch)
    write(OUT / 'root-web-005.json', subject_batch)
    write(OUT / 'review.json', audit)
    write(OUT / 'subject-mapping.json', {'checked_on': DATE, 'authority': 'lcsh', 'match': 'main component only', 'headings': HEADINGS, 'paths': paths})
    print(json.dumps(audit['counts'], indent=2))


if __name__ == '__main__':
    stage_review()
