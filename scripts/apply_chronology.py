"""Build/apply/check revision 1.141: explicit chronology across the project.

    python3 scripts/apply_chronology.py --build
    python3 scripts/apply_chronology.py --apply
    python3 scripts/apply_chronology.py --check

Dates are explicit editorial data in project-events.psv and the reviewed pilot.
No browser-time prose parsing, inferred career bounds or field lifespan migration.
"""
import argparse
import csv
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.chronology import date_bounds, validate_chronologies

RESEARCH = ROOT / 'data/field-research/timeline-spans-2026-10-15'
OUT = ROOT / 'data/production-batches/chronology-1.141'
GRAPH = ROOT / 'historiography-1920-2000.json'
REV = '1.141'
DAY = '2026-10-15'


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def baseline_bytes():
    m = json.loads((RESEARCH / 'baseline/manifest.json').read_text())
    p = ROOT / m['snapshot']
    raw = p.read_bytes() if p.exists() else subprocess.check_output(
        ['git', 'show', m['commit'] + ':' + m['graph_path']], cwd=ROOT)
    assert digest(raw) == m['graph_sha256'], 'Baseline must be the exact 1.140 graph'
    return raw


def selected_label(events, prefix='Selected contributions'):
    dates = [date_bounds(e['date']) for e in events if e['track'] == 'contributions']
    if not dates:
        dates = [date_bounds(e['date']) for e in events]
    lo, hi = min(d[0] for d in dates), max(d[1] for d in dates)
    return f'{prefix} · {lo}' + (f'–{hi}' if hi != lo else '')


def make_chronology(node, events, label=None, intervals=None, **extra):
    person = node.get('entry_kind') == 'person'
    return dict(version=1, label=label or selected_label(events),
        selection_note=('Selected dated contributions, not career or lifespan boundaries.' if person else
                        'Selected contributions and witnesses, not a field origin, lifespan or complete history.'),
        events=events, intervals=intervals or [],
        continuation=extra.pop('continuation', dict(status='not_asserted',
            basis='No continuous historical duration or ending is established by this selection.')),
        interpretation=extra.pop('interpretation', 'Explicit selection from the existing entry and bibliography. '
            'Original source reading limits remain; no new whole-work verification or field survey is claimed.'),
        prepared_on=DAY, editorial_record='data/production-batches/chronology-1.141/acceptance.json', **extra)


def build_packet():
    graph = json.loads(baseline_bytes())
    pilot = json.loads((RESEARCH / 'pilot-decisions.json').read_text())
    nodes = {n['id']: n for n in graph['nodes']}
    journal_nodes = {n['id']: n for n in graph['journal_catalogue']['nodes']}
    sources = {s['id']: s for s in graph['sources']}
    new_sources = []
    for check in pilot['source_checks']:
        metadata = check['access'] not in {'selected_primary_text', 'translated_primary_text', 'selected_primary_text_and_metadata'}
        new_sources.append(dict(id='chronology_' + check['id'], title=check['title'], url=check['url'],
            verification=dict(status='bibliographic_metadata_checked' if metadata else 'supporting_page_checked',
                checked_on=DAY, note=check['extent'] + ' ' + check['observation']),
            scope_note='Bounded chronology check; not a new reading or certification of every associated historical claim.'))
    def ref(value):
        return value.replace('pilot:', 'graph:chronology_', 1) if value.startswith('pilot:') else value
    records = {}
    for entry in pilot['entries']:
        n = nodes.get(entry['id'], journal_nodes.get(entry['id']))
        events = deepcopy(entry['events'])
        intervals = deepcopy(entry['historical_intervals'])
        for fact in events + intervals:
            fact['source_ids'] = [ref(s) for s in fact['source_ids']]
        records[n['id']] = make_chronology(n, events, entry['display_label'], intervals,
            continuation=entry['continuation'], interpretation=entry['decision'],
            retain=entry['retain'], unresolved=entry['unresolved'])
    grouped = {}
    rows = []
    for line in (RESEARCH / 'project-events.psv').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        assert len(parts) in (6, 7), parts
        ident, raw_date, kind, track, label, ids = parts[:6]
        note = parts[6] if len(parts) == 7 else ''
        assert ident in nodes and ident not in records, ident
        for sid in ids.split(','):
            assert sid in sources, (ident, sid)
        if '/' in raw_date:
            a, b = map(int, raw_date.split('/'))
            date = dict(earliest=a, latest=b, precision='year_range',
                        qualifier='dated_sequence' if 'sequence' in kind else 'issue_or_event_date_range')
        else:
            date = dict(year=int(raw_date), precision='year')
        event_id = 'event_' + digest((raw_date + '|' + kind + '|' + label).encode())[:12]
        event = dict(id=event_id, label=label, kind=kind, track=track, date=date,
            source_ids=['graph:' + sid for sid in ids.split(',')],
            support=(note + ' ' if note else '') + 'Date retained from the existing entry/bibliographic evidence. '
                'See the cited source records for their original reading and metadata limits.',
            basis='existing_entry_and_bibliography')
        grouped.setdefault(ident, []).append(event)
        rows.append((ident, event))
    for ident, events in grouped.items():
        records[ident] = make_chronology(nodes[ident], events)
    assert set(nodes) <= records.keys(), 'Every graph entry must have explicit chronology'

    # Add already accepted, explicitly dated later work/strands. These are source-linked
    # structured publication observations, never years inferred from free text.
    for ident, node in nodes.items():
        c = records[ident]
        for strand in node.get('strands', []):
            year = strand.get('work_publication_year')
            sids = strand.get('source_ids', [])
            if type(year) is not int or not sids:
                continue
            refs = ['graph:' + s for s in sids]
            exists = any(date_bounds(e['date']) == (year, year)
                and set(e['source_ids']) & set(refs) for e in c['events'])
            if not exists:
                c['events'].append(dict(id='strand_' + strand['id'], label=strand.get('works') or strand['title'],
                    kind='publication', track='contributions', date=dict(year=year, precision='year'),
                    source_ids=refs, support='Existing accepted strand work_publication_year; '
                    'source-specific claims and reading limits remain in the strand and source records.',
                    work_ids=strand.get('work_ids', []), basis='accepted_structured_work_date'))
        c['events'].sort(key=lambda e: (*date_bounds(e['date']), e['track'], e['id']))
        if ident not in {e['id'] for e in pilot['entries']}:
            c['label'] = selected_label(c['events'])

    linked = {e['source'] for e in graph['journal_catalogue']['edges']}
    for ident in sorted(linked - records.keys()):
        journal = journal_nodes[ident]
        d = journal.get('date_span') or {}
        events, intervals = [], []
        if type(d.get('start')) is int:
            date = dict(year=d['start'], precision=d.get('precision', 'year'))
            refs = ['journal:' + s for s in d.get('source_ids', [])]
            assert refs, ident
            meaning = d.get('start_kind', 'recorded_start')
            title_start = meaning == 'catalogued_title_start'
            wording = 'Catalogued title/edition start' if title_start else 'Recorded publication start'
            events.append(dict(id='recorded_start', label=wording, kind=meaning, track='contributions',
                date=date, source_ids=refs, support=journal.get('chronology_note') or
                'Existing source-checked publication date; not an inferred foundation of its research field.'))
            end = dict(year=d['end'], precision=d.get('precision', 'year')) if type(d.get('end')) is int else None
            intervals.append(dict(id='publication_title_interval', subject='Recorded journal title/edition',
                start=date, end=end, start_meaning=meaning,
                end_meaning=d.get('end_kind', 'unknown') if end else 'unknown', source_ids=refs,
                support='Existing journal date_span and its source basis. Unknown cessation does not establish publication to the present.'))
            label = wording + ' · ' + str(d['start']) + (('–' + str(d['end']) + ' · ' + d['end_kind'].replace('_', ' '))
                if end else ' · ending unestablished')
        else:
            edges = [e for e in graph['journal_catalogue']['edges'] if e['source'] == ident
                and type(e.get('temporal_scope', {}).get('start')) is int]
            assert edges, ident
            year = min(e['temporal_scope']['start'] for e in edges)
            refs = list(dict.fromkeys('journal:' + s for e in edges if e['temporal_scope']['start'] == year
                for s in e.get('source_ids', [])))
            events.append(dict(id='earliest_venue_role', label='Earliest currently evidenced venue role',
                kind='venue_role', track='contributions', date=dict(year=year, precision='year', qualifier='earliest_evidenced'),
                source_ids=refs, support='Date of the accepted venue relationship, not a first issue. Publication start and cessation remain unverified.'))
            label = f'Venue role evidenced from {year} · publication bounds unverified'
        records[ident] = make_chronology(journal, events, label, intervals,
            continuation=dict(status='unknown', basis='The existing catalogue does not establish present-day publication continuity.'),
            unresolved=['Retain exact title/edition, source and holdings distinctions; no unrecorded cessation or current-status claim.'])
    overrides = json.loads((RESEARCH / 'project-overrides.json').read_text())
    for change in overrides['journal_interval_revisions']:
        record = records[change['id']]
        interval = next(i for i in record['intervals'] if i['id'] == change['interval_id'])
        interval.update(end=change['end'], end_meaning=change['end_meaning'],
            source_ids=interval['source_ids'] + change['source_ids_append'], support=change['support'])
        record['label'] = change['label']
    packet = dict(revision=REV, baseline_revision='1.140', date=DAY,
        authorization='User: “Can you build this out to the whole project?” after reviewing the 16-case historical pilot.',
        baseline_sha256=digest(baseline_bytes()), chronologies=records, new_sources=new_sources,
        label_revisions=overrides['label_revisions'],
        note='All chronology is explicit KG data. Selections are not inferred career/field intervals; existing graph semantics and editorial coverage are preserved.')
    test_graph = transform(graph, packet)
    errors = validate_chronologies(test_graph)
    assert not errors, '\n'.join(errors)
    return packet


def transform(graph, packet):
    graph = deepcopy(graph)
    assert graph['revision_history'][-1]['version'] == '1.140'
    graph['schema_version'] = '1.6'
    graph['chronology_policy'] = dict(version='1', basis='Explicit dated events, named historical intervals and separate editorial coverage.',
        interpretation='A selection extent is not a lifespan, period of influence or complete field history. '
        'Unknown endpoints remain unknown. Date labels are descriptive, never instructions to the current renderer.')
    for node in graph['nodes'] + graph['journal_catalogue']['nodes']:
        if node['id'] in packet['chronologies']:
            node['chronology'] = deepcopy(packet['chronologies'][node['id']])
    for change in packet.get('label_revisions', []):
        node = next(n for n in graph['nodes'] if n['id'] == change['id'])
        assert node['label'] == change['old']
        node['label'] = change['new']
        node['aliases'] = list(dict.fromkeys(node.get('aliases', []) + [change['old']]))
    graph['sources'] += deepcopy(packet['new_sources'])
    graph['revision_history'].append(dict(version=REV, date=DAY,
        summary='Explicit chronology for all 187 entries and 38 linked journals: dated contributions, context, '
        'editions and reception; sourced journal title intervals; review years separate from historical duration.',
        acceptance_record='data/production-batches/chronology-1.141/acceptance.json',
        added_node_ids=[], added_edge_ids=[], revised_edge_ids=[]))
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build', action='store_true')
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    packet_path = OUT / 'editorial-additions.json'
    if args.build:
        packet = build_packet()
        OUT.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(serial(packet))
    else:
        packet = json.loads(packet_path.read_text())
        assert packet == build_packet(), 'Editorial packet must reproduce from its explicit decisions'
        before = json.loads(baseline_bytes())
        after = transform(before, packet)
        raw = serial(after).encode()
        if args.apply:
            current = GRAPH.read_bytes()
            previous = OUT / 'acceptance.json'
            assert current == baseline_bytes() or (previous.exists() and
                digest(current) == json.loads(previous.read_text())['graph_sha256']), 'Apply only to the exact baseline or the unchanged local draft of this release'
            GRAPH.write_bytes(raw)
            acceptance = dict(revision=REV, baseline_revision='1.140',
                baseline_sha256=packet['baseline_sha256'], graph_sha256=digest(raw),
                packet_sha256=digest(packet_path.read_bytes()),
                entries=len(before['nodes']), linked_journals=len(packet['chronologies']) - len(before['nodes']),
                events=sum(len(c['events']) for c in packet['chronologies'].values()),
                intervals=sum(len(c['intervals']) for c in packet['chronologies'].values()),
                sources_added=len(packet['new_sources']), authorization=packet['authorization'])
            (OUT / 'acceptance.json').write_text(serial(acceptance))
        else:
            acceptance = json.loads((OUT / 'acceptance.json').read_text())
            assert digest(raw) == acceptance['graph_sha256']
            assert digest(packet_path.read_bytes()) == acceptance['packet_sha256']
            assert GRAPH.read_bytes() == raw, 'Current graph differs from the reconstructed chronology release'
    print(f'{REV}: ' + str(len(packet['chronologies'])) + ' explicit chronologies; all source references resolve.')


if __name__ == '__main__':
    main()
