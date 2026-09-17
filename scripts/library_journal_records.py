"""MODS parsing and conservative identity assessment for serials."""
import re
import unicodedata
from xml.etree import ElementTree as ET

MODS = '{http://www.loc.gov/mods/v3}'
MARC = '{http://www.loc.gov/MARC21/slim}'


def local(tag):
    return tag.rsplit('}', 1)[-1]


def text(element):
    return ' '.join(''.join(element.itertext()).split()) if element is not None else ''


def children(element, name):
    return [e for e in element if local(e.tag) == name]


def values(element, name):
    return [text(e) for e in children(element, name) if text(e)]


def field(element):
    return {'value': text(element), **element.attrib}


def issn(value):
    value = re.sub(r'[^0-9X]', '', value.upper())
    if len(value) != 8 or not value[:7].isdigit():
        return None
    if sum(int(v) * (8-i) for i, v in enumerate(value[:7])) % 11 != (0 if value[-1] == '0' else 11-(10 if value[-1] == 'X' else int(value[-1]))):
        return None
    return value[:4] + '-' + value[4:]


def title_key(value):
    value = unicodedata.normalize('NFKC', value).casefold().replace('&', ' and ')
    value = re.sub(r'[^\w\s]', ' ', value)
    return ' '.join(value.split())


def identifiers(element):
    return [field(e) for e in children(element, 'identifier')]


def parse_record(element, provider):
    titles = []
    for ti in children(element, 'titleInfo'):
        titles.append({'title': ' : '.join(values(ti, 'title') + values(ti, 'subTitle')),
                       'type': ti.get('type', 'primary'),
                       'parts': values(ti, 'partNumber') + values(ti, 'partName')})
    origins = []
    for origin in children(element, 'originInfo'):
        origins.append({'attributes': dict(origin.attrib),
                        'dates': [field(e) for e in children(origin, 'dateIssued')],
                        'publishers': values(origin, 'publisher'),
                        'agents': [text(e) for e in children(origin, 'agent')],
                        'places': [field(t) for p in children(origin, 'place') for t in children(p, 'placeTerm')],
                        'issuance': values(origin, 'issuance'),
                        'frequency': values(origin, 'frequency')})
    info = children(element, 'recordInfo')
    record_ids = [field(e) for ri in info for e in children(ri, 'recordIdentifier')]
    record = {'provider': provider, 'titles': titles, 'identifiers': identifiers(element),
              'origins': origins, 'notes': [field(e) for e in children(element, 'note')],
              'subjects': [{'authority': s.get('authority'),
                            'components': [{'kind': local(e.tag), 'value': text(e), **e.attrib} for e in s]}
                           for s in children(element, 'subject')],
              'classifications': [field(e) for e in children(element, 'classification')],
              'languages': [field(t) for e in children(element, 'language') for t in children(e, 'languageTerm')],
              'record_identifiers': record_ids,
              'cataloguing_agencies': [field(e) for ri in info for e in children(ri, 'recordContentSource')],
              'record_changes': [field(e) for ri in info for e in children(ri, 'recordChangeDate')],
              'record_level': 'bibliographic',
              'holdings': {'level': 'embedded_mods_if_present',
                           'elements_xml': [ET.tostring(h, encoding='unicode') for loc in children(element, 'location')
                                            for h in children(loc, 'holdingSimple')+children(loc, 'holdingExternal')],
                           'note': 'Holdings coverage is separate from publication chronology; absence here does not imply no holdings.'},
              'forms': [field(e) for p in children(element, 'physicalDescription') for e in children(p, 'form')],
              'related_items': [{'type': e.get('type'), 'other_type': e.get('otherType'),
                                  'titles': [text(t) for t in children(e, 'titleInfo')],
                                  'identifiers': identifiers(e)} for e in children(element, 'relatedItem')]}
    # Only record-level identifiers count; a predecessor's ISSN is not this record's.
    record['issns'] = sorted({n for i in record['identifiers']
                             if i.get('type') in ('issn', 'issn-l') and i.get('invalid') != 'yes'
                             if (n := issn(i['value']))})
    record['serial'] = any('serial' in o['issuance'] or 'continuing' in o['issuance'] for o in origins)
    record['date_candidates'] = []
    for index, origin in enumerate(origins):
        for d in origin['dates']:
            raw = d['value']
            # Keep approximate years and MARC sentinels raw; do not turn them into dates.
            year = int(raw) if re.fullmatch(r'\d{4}', raw) and 1000 <= int(raw) <= 2100 else None
            record['date_candidates'].append({'raw': raw, 'year': year,
                'point': d.get('point', 'unspecified'), 'qualifier': d.get('qualifier'),
                'origin_index': index, 'event_type': origin['attributes'].get('eventType'),
                'usable_exact_year': year is not None and not d.get('qualifier')})
    return record


def parse_marc(element, provider):
    """Normalize bibliographic fields; keep original MARC and holdings layers distinct."""
    leader = text(element.find(MARC+'leader'))
    controls = {e.get('tag'): e.text or '' for e in element.findall(MARC+'controlfield')}
    data = [{'tag': e.get('tag'), 'ind1': e.get('ind1'), 'ind2': e.get('ind2'),
             'subfields': [{'code': s.get('code'), 'value': s.text or ''} for s in e.findall(MARC+'subfield')]}
            for e in element.findall(MARC+'datafield')]
    def sub(f, code):
        return [s['value'] for s in f['subfields'] if s['code'] == code]
    def add(parent, tag, value, **attributes):
        e = ET.SubElement(parent, MODS+tag, attributes)
        e.text = value
        return e
    holdings_record = len(leader) > 6 and leader[6] in 'uvxy'
    mods = ET.Element(MODS+'mods')
    origin = ET.SubElement(mods, MODS+'originInfo', {'eventType': 'publication'})
    ri = ET.SubElement(mods, MODS+'recordInfo')
    add(ri, 'recordIdentifier', controls.get('001', ''), source=controls.get('003', provider))
    if controls.get('005'):
        add(ri, 'recordChangeDate', controls['005'])
    if not holdings_record:
        fixed = controls.get('008', '')
        if len(fixed) >= 15 and fixed[6] in 'cdusm':
            add(origin, 'dateIssued', fixed[7:11], encoding='marc', point='start')
            # d = ceased, c = continuing, u = unknown serial status; do not infer a terminus.
            add(origin, 'dateIssued', fixed[11:15], encoding='marc', point='end')
        if len(leader) > 7 and leader[7] in 'si':
            add(origin, 'issuance', 'serial')
        if len(fixed) >= 38 and fixed[35:38].strip():
            language = ET.SubElement(mods, MODS+'language')
            add(language, 'languageTerm', fixed[35:38], type='code', authority='iso639-2b')
    for f in data:
        tag = f['tag']
        if tag in ('245', '246', '130', '222') and not holdings_record:
            kind = {'245': 'primary', '246': 'alternative', '130': 'uniform', '222': 'uniform'}[tag]
            ti = ET.SubElement(mods, MODS+'titleInfo', {'type': kind})
            add(ti, 'title', ' '.join(sub(f, 'a')).rstrip(' /:'))
            for value in sub(f, 'b'):
                add(ti, 'subTitle', value.rstrip(' /:'))
        elif tag == '022' and not holdings_record:
            for value in sub(f, 'a'):
                add(mods, 'identifier', value, type='issn')
            for value in sub(f, 'l'):
                add(mods, 'identifier', value, type='issn-l')
        elif tag == '010':
            for value in sub(f, 'a'):
                add(mods, 'identifier', value, type='lccn')
        elif tag == '035':
            for value in sub(f, 'a'):
                if value.startswith('(OCoLC)'):
                    add(mods, 'identifier', value.removeprefix('(OCoLC)'), type='oclc')
        elif tag == '040':
            for code in ('a', 'c', 'd'):
                for value in sub(f, code):
                    add(ri, 'recordContentSource', value, role=code)
        elif tag in ('050', '082') and not holdings_record:
            add(mods, 'classification', ' '.join(sub(f, 'a')+sub(f, 'b')),
                authority='lcc' if tag == '050' else 'ddc')
        elif tag in ('260', '264') and not holdings_record:
            # The raw statement is retained; only publication agents enter publisher metadata.
            if tag == '260' or f['ind2'] == '1':
                for value in sub(f, 'b'):
                    add(origin, 'publisher', value)
                for value in sub(f, 'a'):
                    place = ET.SubElement(origin, MODS+'place')
                    add(place, 'placeTerm', value, type='text')
                for value in sub(f, 'c'):
                    add(origin, 'dateIssued', value)
        elif tag in ('310', '321'):
            add(origin, 'frequency', ' '.join(s['value'] for s in f['subfields']),
                displayLabel='current' if tag == '310' else 'former')
        elif tag == '362':
            add(mods, 'note', ' '.join(s['value'] for s in f['subfields']),
                type='date/sequential designation', displayLabel='MARC 362 indicator '+str(f['ind1']))
        elif tag in ('500', '515', '533', '588'):
            add(mods, 'note', ' '.join(s['value'] for s in f['subfields']), type='MARC '+tag)
        elif tag in ('650', '651', '653', '655') and not holdings_record:
            authority = 'lcsh' if f['ind2'] == '0' else (';'.join(sub(f, '2')) or 'unrecorded')
            subject = ET.SubElement(mods, MODS+'subject', {'authority': authority})
            for s in f['subfields']:
                if s['code'] in 'avxyz':
                    kind = {'a': 'geographic' if tag == '651' else 'topic', 'v': 'genre',
                            'x': 'topic', 'y': 'temporal', 'z': 'geographic'}[s['code']]
                    add(subject, kind, s['value'])
        elif tag in ('780', '785', '776', '770', '772'):
            related = ET.SubElement(mods, MODS+'relatedItem', {'type': {
                '780': 'preceding', '785': 'succeeding', '776': 'otherFormat',
                '770': 'hasSupplement', '772': 'isSupplementOf'}[tag]})
            ti = ET.SubElement(related, MODS+'titleInfo')
            add(ti, 'title', ' '.join(sub(f, 't')))
            for value in sub(f, 'x'):
                add(related, 'identifier', value, type='issn')
            for value in sub(f, 'w'):
                add(related, 'identifier', value, type='local')
    record = parse_record(mods, provider)
    record['record_level'] = 'holdings' if holdings_record else 'bibliographic'
    record['marc'] = {'leader': leader, 'controlfields': controls, 'datafields': data}
    record['holdings'] = {'level': 'holdings_record' if holdings_record else 'embedded_fields_if_present',
                          'bibliographic_link': controls.get('004'),
                          'fields': [f for f in data if f['tag'] in ('852','853','854','855','863','864','865','866','867','868')],
                          'note': 'Enumeration, chronology and coverage are holdings evidence; never publication inception or cessation. Preserve subfield 8 linkages.'}
    if holdings_record:
        record['serial'] = False
        record['date_candidates'] = []
    return record


def parse_page(raw, provider):
    root = ET.fromstring(raw)
    diagnostics = [text(e) for e in root.iter() if local(e.tag) == 'diagnostic']
    if diagnostics:
        raise ValueError('SRU diagnostic response')
    count_tag = 'numberOfRecords' if provider == 'loc' else 'numFound'
    counts = [text(e) for e in root.iter() if local(e.tag) == count_tag]
    if not counts or not counts[0].isdigit():
        raise ValueError('Missing result count; response is not a valid catalogue page')
    records = [parse_record(e, provider) for e in root.iter() if e.tag == MODS+'mods']
    records += [parse_marc(e, provider) for e in root.iter() if e.tag == MARC+'record']
    return {'total': int(counts[0]), 'records': records}


def assess(node, record, hinted_issns=()):
    known = {n for v in node.get('issns', []) if (n := issn(v))}
    found = set(record['issns'])
    hinted = set(hinted_issns)
    names = {title_key(n) for n in [node['label'], *node.get('aliases', [])]}
    # Abbreviations and uniform titles alone do not establish identity.
    titles = {title_key(t['title']) for t in record['titles'] if t['type'] in ('primary', 'alternative')}
    title_match = bool(names & titles)
    status = 'unmatched'
    if not record['serial']:
        status = 'not_a_serial'
    elif known & found:
        status = 'catalogue_issn_match'
    elif known and found:
        status = 'identifier_conflict'
    elif hinted & found:
        status = 'openalex_identifier_hint_match'
    elif title_match:
        status = 'title_candidate'
    if node.get('identity_status') == 'ambiguous_title' and status not in ('unmatched', 'not_a_serial', 'identifier_conflict'):
        status = 'ambiguous_catalogue_identity'
    return {'status': status, 'title_match': title_match, 'accepted': False,
            'matched_catalogue_issns': sorted(known & found),
            'matched_hint_issns': sorted(hinted & found)}


def compare(node, records, openalex):
    """Field observations, not a confidence score or a majority-vote import."""
    span = node.get('date_span') or {}
    start = span.get('start') if span.get('start') is not None else node.get('publication_start')
    end = span.get('end') if span.get('end') is not None else node.get('publication_end')
    usable = [r for r in records if r['identity']['status'] == 'catalogue_issn_match']
    tentative = [r for r in records if r['identity']['status'] in ('title_candidate', 'openalex_identifier_hint_match')]
    observations = []
    for r in usable + tentative:
        for date in r['date_candidates']:
            if date['point'] not in ('start', 'end') or not date['usable_exact_year']:
                continue
            existing = start if date['point'] == 'start' else end
            observations.append({'provider': r['provider'], 'record_key': r['record_key'],
                'identity_status': r['identity']['status'], 'point': date['point'], 'year': date['year'],
                'event_type': date['event_type'],
                'comparison_with_curated': 'missing_curated_value' if existing is None else (
                    'agrees' if date['year'] == existing else 'differs'),
                'existing_value': existing})
    shared = []
    for i, a in enumerate(usable + tentative):
        for b in (usable + tentative)[i+1:]:
            if a['provider'] == b['provider']:
                continue
            def authority_ids(r):
                return {(v.get('type'), re.sub(r'\s+', '', v['value'])) for v in r['identifiers']
                        if v.get('type') in ('lccn', 'oclc')}
            overlap = sorted(authority_ids(a) & authority_ids(b))
            if overlap:
                shared.append({'records': [a['record_key'], b['record_key']], 'shared_ids': overlap,
                               'note': 'Possibly shared cataloguing provenance, not independent confirmations.'})
    oa_dates = []
    for source in openalex:
        oa_dates.append({'source_id': source['id'], 'first_indexed_year': source.get('first_publication_year'),
                         'last_indexed_year': source.get('last_publication_year')})
    pairs = []
    for i, a in enumerate(observations):
        for b in observations[i+1:]:
            if a['provider'] != b['provider'] and a['point'] == b['point']:
                pairs.append({'records': [a['record_key'], b['record_key']], 'point': a['point'],
                              'years': [a['year'], b['year']],
                              'result': 'agrees' if a['year'] == b['year'] else 'differs',
                              'identity_review_required': a['identity_status'] != 'catalogue_issn_match' or b['identity_status'] != 'catalogue_issn_match'})
    for observation in observations:
        observation['openalex_comparisons'] = [
            {'source_id': s['source_id'], 'indexed_year': s['first_indexed_year' if observation['point'] == 'start' else 'last_indexed_year'],
             'same_number': observation['year'] == s['first_indexed_year' if observation['point'] == 'start' else 'last_indexed_year'],
             'note': 'Publication chronology and indexed coverage have different meanings.'} for s in oa_dates]
    subject_pairs = []
    for i, a in enumerate(usable+tentative):
        for b in (usable+tentative)[i+1:]:
            if a['provider'] == b['provider']:
                continue
            def headings(r):
                return {(s['authority'] or '', tuple((c['kind'], title_key(c['value'])) for c in s['components']))
                        for s in r['subjects']}
            overlap = sorted(headings(a) & headings(b))
            subject_pairs.append({'records': [a['record_key'], b['record_key']],
                                  'exact_heading_overlap': overlap,
                                  'note': 'Literal same-authority heading overlap only. Non-overlap is not a subject conflict; no taxonomy equivalence inferred.'})
    return {'existing_start': start, 'existing_end': end, 'existing_date_span': span or None,
            'date_observations': observations, 'openalex_indexed_ranges': oa_dates,
            'shared_cataloguing_provenance': shared,
            'cross_library_date_comparisons': pairs,
            'cross_library_subject_comparisons': subject_pairs,
            'library_candidate_records': len(usable + tentative),
            'catalogue_issn_matched_records': len(usable),
            'subject_observations': [{'provider': r['provider'], 'record_key': r['record_key'],
                                     'identity_status': r['identity']['status'], 'subjects': r['subjects']}
                                    for r in usable + tentative],
            'action': 'Review field-level observations; preserve better dates. No automatic changes.',
            'independence_note': 'Library records may be shared via LC/OCLC; OpenAlex may reuse upstream metadata. Agreement does not prove independent verification.'}
