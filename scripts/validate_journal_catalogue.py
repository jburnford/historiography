"""Validate venue relations without treating them as intellectual influence."""
from datetime import date
import re


def valid_issn(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{3}[\dX]', value):
        return False
    digits = value.replace('-', '')
    return (sum(int(c) * (8-i) for i,c in enumerate(digits[:7])) + (10 if digits[-1]=='X' else int(digits[-1]))) % 11 == 0


def validate_catalogue(catalogue, atlas_nodes):
    errors = []
    if catalogue.get('schema_version') not in ('1.0','1.1','1.2','1.3'): errors.append('Unknown journal catalogue schema')
    def refs(row, known):
        if not row.get('source_ids') or any(s not in known for s in row.get('source_ids', [])):
            errors.append(f"Journal record needs valid source references: {row.get('id')}")
    def web_url(url):
        return isinstance(url, str) and url.startswith(('http://', 'https://'))
    nodes = catalogue.get('nodes', [])
    edges = catalogue.get('edges', [])
    sources = catalogue.get('sources', [])
    for name, rows in [('nodes',nodes),('edges',edges),('sources',sources),('classifications',catalogue.get('subject_classifications',[])),('title histories',catalogue.get('title_relationships',[])),('resources',catalogue.get('discovery_resources',[]))]:
        ids = [r.get('id') for r in rows]
        if None in ids or len(set(ids)) != len(ids): errors.append('Duplicate or missing journal '+name+' IDs')
    by_id = {n['id']:n for n in nodes}
    atlas = {n['id']:n for n in atlas_nodes}
    if set(by_id) & set(atlas): errors.append('Journal IDs collide with historical atlas IDs')
    source_ids = {s['id'] for s in sources}
    for source in sources:
        if not source.get('note') or not source.get('verification') or not web_url(source.get('url')):
            errors.append('Journal source needs URL and scoped verification: '+source['id'])
        if source.get('checked_on') is not None:
            try: date.fromisoformat(source['checked_on'])
            except (ValueError, TypeError): errors.append('Invalid journal source check date')
    for node in nodes:
        refs(node, source_ids)
        if not node.get('label') or node.get('entry_kind') not in ('periodical','publication_subject'):
            errors.append('Invalid journal catalogue entry: '+node['id'])
        if node['entry_kind']=='publication_subject':
            for target in node.get('atlas_node_ids', []):
                if target not in atlas or atlas[target].get('entry_kind') != 'group':
                    errors.append('Subject correspondence must reference an atlas group')
            continue
        if node.get('publication_role') not in ('periodical_candidate','research_journal','primary_source_periodical'):
            errors.append('Invalid periodical role: '+node['id'])
        for issn in node.get('issns', []):
            if not valid_issn(issn): errors.append('Invalid ISSN: '+str(issn))
        if any(not web_url(u) for u in node.get('urls', [])): errors.append('Invalid journal URL')
        for occurrence in node.get('occurrences', []):
            if occurrence.get('source_id') not in source_ids or not occurrence.get('title') or 'row' not in occurrence:
                errors.append('Invalid source occurrence: '+node['id'])
        if 'metrics' in node or 'impact_factor' in node:
            errors.append('Journal impact metrics are excluded from the graph')
        span = node.get('date_span')
        if span:
            refs(span, source_ids)
            start, end = span.get('start'), span.get('end')
            if type(start) is not int or (end is not None and (type(end) is not int or end < start)):
                errors.append('Invalid journal date span')
            if span.get('precision') not in ('year','decade','approximate') or span.get('end_kind') not in ('unknown','terminus','title_change'):
                errors.append('Journal dates require precision and end semantics')
            if span.get('end_kind') in ('terminus','title_change') and (end is None or span.get('open_end') is True):
                errors.append('Journal ending requires a closed, evidenced end')
            if node.get('publication_start') != start or node.get('publication_end') != end:
                errors.append('Journal publication dates disagree with date span')
        elif node.get('publication_start') is not None or node.get('publication_end') is not None:
            errors.append('Journal dates require an evidenced precision model')
        evidence = node.get('bibliographic_evidence', [])
        record_keys = set()
        for record in evidence:
            refs(record, source_ids)
            key = record.get('record_key')
            if not key or key in record_keys or record.get('provider') not in ('loc', 'harvard'):
                errors.append('Invalid or repeated bibliographic evidence record')
            record_keys.add(key)
            proof = record.get('identity_review', {})
            if proof.get('basis') not in ('catalogue_issn_and_primary_title', 'openalex_primary_title_issn_and_library_primary_title'):
                errors.append('Bibliographic evidence needs a scoped identity review')
            matches = proof.get('matched_issns', [])
            if not matches or any(not valid_issn(i) or i not in record.get('issns', []) for i in matches):
                errors.append('Bibliographic identity must match valid own-record ISSNs')
            if proof.get('basis') == 'openalex_primary_title_issn_and_library_primary_title':
                if (not str(proof.get('openalex_source_id', '')).startswith('https://openalex.org/S')
                        or not proof.get('openalex_display_name')
                        or not re.fullmatch(r'[a-f0-9]{64}', proof.get('openalex_staging_sha256', ''))):
                    errors.append('OpenAlex identity concordance needs attributed source provenance')
            if not record.get('titles') or not record.get('note'):
                errors.append('Bibliographic evidence requires titles and qualifications')
            if any(k in record for k in ('marc', 'holdings', 'api_key', 'metrics')):
                errors.append('Raw holdings, MARC, credentials and metrics are excluded from accepted evidence')
        if span and span.get('start_kind') == 'catalogued_title_start':
            supported = {s for r in evidence for s in r.get('source_ids', [])
                         if any(d.get('point') == 'start' and d.get('usable_exact_year') is True
                                and d.get('year') == span['start'] and d.get('event_type') in (None, 'publication')
                                for d in r.get('date_observations', []))}
            if (not evidence or not set(span.get('source_ids', [])) <= supported
                    or span.get('end') is not None or span.get('end_kind') != 'unknown'
                    or span.get('open_end') is not None or span.get('basis') != 'bibliographic_record'):
                errors.append('Catalogued title start needs matching publication evidence and unknown end')
    triples = set()
    for edge in edges:
        refs(edge, source_ids)
        source, target = by_id.get(edge.get('source')), by_id.get(edge.get('target')) or atlas.get(edge.get('target'))
        if not source or source.get('entry_kind')!='periodical' or not target:
            errors.append('Invalid journal relationship endpoint: '+edge['id'])
            continue
        kind, basis = edge.get('relationship_kind'), edge.get('basis')
        permitted = {'founded_for':('sourced_founding_programme','primary_founding_editorial'),
                     'site_of_debate':('named_published_exchange',),
                     'principal_venue':('editorial_longitudinal_review',)}
        if kind not in permitted or basis not in permitted.get(kind, ()):
            errors.append('Invalid journal relationship kind or evidence basis: '+edge['id'])
        if edge.get('directed') is not True or not edge.get('evidence_note') or not edge.get('relationship'):
            errors.append('Journal relationship requires direction and evidence')
        target_kind = target.get('entry_kind')
        if target_kind!='group' or source.get('publication_role')!='research_journal':
            errors.append('Visual venue relation needs a researched journal and an atlas group/debate')
        span = edge.get('temporal_scope', {})
        start, end = span.get('start'), span.get('end')
        if type(start) is not int or type(end) is not int or end < start or span.get('precision') not in ('year','decade','approximate'):
            errors.append('Venue claim needs a dated, scoped interval')
        if kind=='founded_for' and (start != end or source.get('publication_start') != start):
            errors.append('Founding claim must agree with the journal founding date')
        if kind=='site_of_debate' and (not edge.get('debate_name') or len(edge.get('source_ids',[])) < 2):
            errors.append('Debate venue needs a named exchange and references to its contributions')
        if kind=='principal_venue' and (not edge.get('selection_note') or start == end):
            errors.append('Principal venue needs a sustained interval and editorial selection rationale')
        triple = (edge['source'], edge['target'], kind)
        if triple in triples: errors.append('Duplicate journal relationship')
        triples.add(triple)
    for classification in catalogue.get('subject_classifications', []):
        refs(classification,source_ids)
        journal=by_id.get(classification.get('journal_id'),{})
        subject=by_id.get(classification.get('subject_id')) or atlas.get(classification.get('subject_id'),{})
        if journal.get('entry_kind')!='periodical' or subject.get('entry_kind') not in ('publication_subject','group'):
            errors.append('Invalid journal subject classification endpoint')
        if classification.get('basis') not in ('directory_category','library_guide','publisher_scope','bibliographic_subject_index','title_indicated') or not classification.get('evidence_note'):
            errors.append('Journal classification requires a scoped evidence basis')
        if classification.get('basis')=='title_indicated':
            if classification.get('status')!='provisional' or classification.get('checked_on') is not None:
                errors.append('Title classifications must be provisional with no source-check date')
        elif classification.get('status','checked')!='checked':
            errors.append('Source classification has an inconsistent status')
        if classification.get('status')=='provisional':
            try: date.fromisoformat(classification.get('reviewed_on',''))
            except (ValueError,TypeError): errors.append('Provisional classification needs a review date')
        if 'relationship_kind' in classification or 'directed' in classification:
            errors.append('Subject classifications are metadata, not visual edges')
    review_ids = set()
    active_ids = {r['id'] for r in catalogue.get('subject_classifications', [])}
    archived_ids = set()
    for row in catalogue.get('superseded_subject_classifications', []):
        refs(row, source_ids)
        if row['id'] in active_ids or row['id'] in archived_ids:
            errors.append('Superseded classification must have a unique inactive ID')
        archived_ids.add(row['id'])
        if row.get('status')!='provisional' or not row.get('superseded_by_batch'):
            errors.append('Only explicitly superseded provisional classifications may enter history')
        if by_id.get(row.get('journal_id'),{}).get('entry_kind')!='periodical' or row.get('subject_id') not in by_id:
            errors.append('Invalid superseded classification endpoint')
        try: date.fromisoformat(row.get('superseded_on',''))
        except (ValueError,TypeError): errors.append('Invalid classification supersession date')
    for review in catalogue.get('classification_reviews',[]):
        jid=review.get('journal_id')
        if jid in review_ids or by_id.get(jid,{}).get('entry_kind')!='periodical':
            errors.append('Invalid or duplicate journal classification review')
        review_ids.add(jid)
        if review.get('outcome') not in ('checked','provisional','mixed','unresolved'):
            errors.append('Unknown classification review outcome')
        if review.get('outcome')=='unresolved' and (not review.get('reason') or not review.get('next_step')):
            errors.append('Unresolved classification needs reason and next step')
        related=[r for r in catalogue.get('subject_classifications',[]) if r['journal_id']==jid]
        statuses={r.get('status','checked') for r in related}
        expected='unresolved' if not statuses else 'mixed' if len(statuses)>1 else next(iter(statuses))
        if review.get('outcome')!=expected:
            errors.append('Classification review outcome disagrees with its classifications')
    for history in catalogue.get('title_relationships', []):
        refs(history,source_ids)
        old,new=by_id.get(history.get('predecessor'),{}),by_id.get(history.get('successor'),{})
        if old.get('entry_kind')!='periodical' or new.get('entry_kind')!='periodical' or old.get('id')==new.get('id'):
            errors.append('Title history requires two distinct periodicals')
        if type(history.get('changed_in')) is not int or not history.get('evidence_note'):
            errors.append('Title history requires a date and evidence')
    for resource in catalogue.get('discovery_resources', []):
        refs(resource, source_ids)
        if not web_url(resource.get('url')): errors.append('Invalid journal discovery URL')
    return errors
