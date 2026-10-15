"""Shared structural checks for the graph's explicit chronology records."""
import calendar

TRACKS = {'contributions', 'context', 'editions', 'reception'}
PRECISIONS = {'year', 'month', 'day', 'year_range', 'decade', 'century'}


def date_bounds(date):
    if date['precision'] == 'year_range':
        return date['earliest'], date['latest']
    year = date['year']
    return year, year + {'decade': 9, 'century': 99}.get(date['precision'], 0)


def validate_chronologies(graph):
    errors = []
    refs = {'graph:' + s['id'] for s in graph.get('sources', [])}
    refs |= {'journal:' + s['id'] for s in graph.get('journal_catalogue', {}).get('sources', [])}

    def date_check(date, where):
        if not isinstance(date, dict) or date.get('precision') not in PRECISIONS:
            errors.append(f'{where}: date needs explicit precision'); return False
        if date['precision'] == 'year_range':
            if not all(type(date.get(k)) is int for k in ('earliest', 'latest')) or date['earliest'] > date['latest']:
                errors.append(f'{where}: invalid event date range'); return False
            if not date.get('qualifier'):
                errors.append(f'{where}: explain what the event date range means')
        elif type(date.get('year')) is not int:
            errors.append(f'{where}: numeric year required'); return False
        elif date['precision'] in {'month', 'day'}:
            month = date.get('month')
            if type(month) is not int or not 1 <= month <= 12:
                errors.append(f'{where}: invalid month'); return False
            if date['precision'] == 'day' and (type(date.get('day')) is not int
                    or not 1 <= date['day'] <= calendar.monthrange(date['year'], month)[1]):
                errors.append(f'{where}: invalid day'); return False
        for alternate in date.get('alternatives', []):
            if type(alternate.get('year')) is not int or not alternate.get('basis'):
                errors.append(f'{where}: alternate date needs a year and basis')
        return True

    nodes = graph.get('nodes', [])
    journals = graph.get('journal_catalogue', {}).get('nodes', [])
    linked = {e['source'] for e in graph.get('journal_catalogue', {}).get('edges', [])}
    required = graph.get('chronology_policy', {}).get('version') == '1'
    for node in nodes + journals:
        c = node.get('chronology')
        where = node['id']
        if not c:
            if required and (node in nodes or node['id'] in linked):
                errors.append(f'{where}: explicit chronology required')
            continue
        if c.get('version') != 1 or not c.get('label') or not c.get('selection_note'):
            errors.append(f'{where}: chronology needs version, label and selection note')
        continuation = c.get('continuation', {})
        if continuation.get('status') not in {'unknown', 'not_asserted', 'supported_as_of'} or not continuation.get('basis'):
            errors.append(f'{where}: continuation needs a status and basis')
        if continuation.get('status') == 'supported_as_of' and not continuation.get('source_ids'):
            errors.append(f'{where}: supported continuation needs its own sources')
        facts = c.get('events', []) + c.get('intervals', [])
        ids = [f.get('id') for f in facts]
        if not facts or None in ids or len(ids) != len(set(ids)):
            errors.append(f'{where}: dated facts need unique local IDs')
        for event in c.get('events', []):
            ew = where + ':' + str(event.get('id'))
            if not event.get('label') or not event.get('kind') or event.get('track') not in TRACKS:
                errors.append(f'{ew}: event needs label, kind and track')
            date_check(event.get('date'), ew)
        for interval in c.get('intervals', []):
            iw = where + ':' + str(interval.get('id'))
            a = date_check(interval.get('start'), iw + ':start')
            b = interval.get('end')
            if not interval.get('subject') or not interval.get('start_meaning'):
                errors.append(f'{iw}: interval must identify its subject and start meaning')
            if b is None:
                if interval.get('end_meaning') != 'unknown':
                    errors.append(f'{iw}: null end must explicitly mean unknown')
            elif date_check(b, iw + ':end') and a:
                if date_bounds(interval['start'])[0] > date_bounds(b)[1]:
                    errors.append(f'{iw}: reversed interval')
                if interval.get('end_meaning') not in {'terminus', 'title_change', 'phase_end'}:
                    errors.append(f'{iw}: known ending requires its historical meaning')
        for fact in facts + ([continuation] if continuation.get('status') == 'supported_as_of' else []):
            fw = where + ':' + str(fact.get('id', 'continuation'))
            if not fact.get('source_ids') or not fact.get('support', fact.get('basis')):
                errors.append(f'{fw}: each chronology claim needs sources and a support note')
            for ref in fact.get('source_ids', []):
                if ref not in refs:
                    errors.append(f'{fw}: unresolved chronology source {ref}')
    return errors
