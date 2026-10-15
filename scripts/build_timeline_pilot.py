"""Build the chronology research pilot without changing production data.

    python3 scripts/build_timeline_pilot.py
    python3 scripts/build_timeline_pilot.py --check

Historical decisions live in pilot-decisions.json, never in renderer code.
"""
import argparse
import calendar
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/field-research/timeline-spans-2026-10-15'
PILOT = DEST / 'pilot-decisions.json'
GRAPH = ROOT / 'historiography-1920-2000.json'
AUDIT = DEST / 'audit.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(date):
    if date['precision'] == 'year_range':
        return date['earliest'], date['latest']
    return date['year'], date['year']


def date_text(date):
    if date is None:
        return 'unknown'
    if date['precision'] == 'year_range':
        text = f"{date['earliest']}–{date['latest']}"
    elif date['precision'] == 'day':
        text = f"{date['year']}-{date['month']:02d}-{date['day']:02d}"
    elif date['precision'] == 'month':
        text = f"{date['year']}-{date['month']:02d}"
    else:
        text = str(date['year'])
    if date.get('qualifier'):
        text += ' (' + date['qualifier'].replace('_', ' ') + ')'
    if date.get('alternatives'):
        text += '; alternate citation: ' + ', '.join(str(a['year']) for a in date['alternatives'])
    return text


def validate_date(date):
    precision = date['precision']
    assert precision in {'year', 'year_range', 'month', 'day'}, date
    if precision == 'year_range':
        assert type(date['earliest']) is int and type(date['latest']) is int
        assert date['earliest'] <= date['latest']
        assert date.get('qualifier'), 'Explain what an event date range means'
        if 'preferred_year' in date:
            assert date['earliest'] <= date['preferred_year'] <= date['latest']
    else:
        assert type(date['year']) is int
        if precision in {'month', 'day'}:
            assert 1 <= date['month'] <= 12
        if precision == 'day':
            assert 1 <= date['day'] <= calendar.monthrange(date['year'], date['month'])[1]
    for alt in date.get('alternatives', []):
        assert type(alt['year']) is int and alt['basis']


def build():
    manifest = json.loads((DEST / 'baseline/manifest.json').read_text())
    snapshot = ROOT / manifest['snapshot']
    raw = snapshot.read_bytes() if snapshot.exists() else subprocess.check_output(
        ['git', 'show', manifest['commit'] + ':' + manifest['graph_path']], cwd=ROOT)
    graph_hash = hashlib.sha256(raw).hexdigest()
    graph = json.loads(raw)
    audit = json.loads(AUDIT.read_text())
    decisions = json.loads(PILOT.read_text())
    assert graph_hash == audit['input']['sha256'], 'The pilot uses the pinned 1.140 inventory'
    assert sha(DEST / 'baseline/field.mjs') == audit['input']['renderer_sha256']
    assert decisions['status'] == 'research_candidate_not_applied'
    nodes = {n['id']: n for n in graph['nodes'] + graph['journal_catalogue']['nodes']}
    before = {n['id']: n for n in audit['entries'] + audit['journals']}
    sources = {
        **{'graph:' + s['id']: s for s in graph['sources']},
        **{'journal:' + s['id']: s for s in graph['journal_catalogue']['sources']},
        **{'pilot:' + s['id']: s for s in decisions['source_checks']},
    }
    claim_sources = {s['id']: s for s in graph['claim_catalogue']['source_records']}
    entries = decisions['entries']
    assert len(entries) == len({e['id'] for e in entries}) == 16
    assert sum(e['id'] in {n['id'] for n in graph['nodes']} for e in entries) == 14
    refs = set()
    packet_entries = []
    for entry in entries:
        ident = entry['id']
        assert ident in nodes and ident in before, ident
        assert entry['decision'] and entry['retain'] and entry['unresolved']
        assert entry['continuation']['status'] in {'not_asserted', 'unknown', 'supported_as_of'}
        event_ids = [e['id'] for e in entry['events']]
        assert len(event_ids) == len(set(event_ids)), ident
        for event in entry['events']:
            assert event['track'] in {'contributions', 'context', 'editions', 'reception'}
            assert event['kind'] and event['support'] and event['source_ids']
            validate_date(event['date'])
        for interval in entry['historical_intervals']:
            validate_date(interval['start'])
            assert interval['subject'] and interval['support'] and interval['source_ids']
            assert interval['start_meaning'] and interval['end_meaning']
            if interval['end'] is None:
                assert interval['end_meaning'] == 'unknown'
            else:
                validate_date(interval['end'])
                assert bounds(interval['start'])[0] <= bounds(interval['end'])[1]
        for fact in entry['events'] + entry['historical_intervals']:
            for ref in fact['source_ids']:
                assert ref in sources, (ident, ref)
                refs.add(ref)
        selected = [bounds(e['date']) for e in entry['events'] if e['track'] == 'contributions']
        extent = {'start': min(b[0] for b in selected), 'end': max(b[1] for b in selected),
                  'meaning': 'extent_of_selected_contribution_events_not_historical_duration'}
        packet_entries.append({**entry, 'label': nodes[ident]['label'],
            'before': before[ident], 'coverage_unchanged': nodes[ident].get('coverage'),
            'selected_contribution_extent': extent})
    by_id = {e['id']: e for e in packet_entries}
    # Check the material historical distinctions, not just record shape.
    assert by_id['sciencewars']['selected_contribution_extent'] == {
        'start': 1994, 'end': 1999,
        'meaning': 'extent_of_selected_contribution_events_not_historical_duration'}
    assert next(e for e in by_id['sciencewars']['events'] if e['id'] == 'critique_2004')['track'] == 'reception'
    assert by_id['wittgenstein']['selected_contribution_extent']['end'] == 1953
    assert by_id['roger_chartier']['selected_contribution_extent']['end'] == 1989
    assert by_id['j_m_s_careless']['selected_contribution_extent']['end'] == 1989
    assert by_id['who_killed_debate']['selected_contribution_extent']['start'] == 1991
    assert by_id['indigenous']['coverage_unchanged']['reviewed_through'] == 2000
    assert next(e for e in by_id['indigenous']['events'] if e['id'] == 'leddy_2010')['date']['year'] == 2010
    parr = {e['id']: e for e in by_id['joy_parr']['events']}
    assert parr['sensing_hardcover_2009']['date']['year'] == 2009
    assert parr['sensing_pdf_2010']['date']['year'] == 2010
    assert len([e for e in by_id['aldo_leopold']['events'] if e['track'] == 'contributions']) == 1
    for ident in ['digital_history', 'web_history']:
        assert by_id[ident]['historical_intervals'] == []
        assert by_id[ident]['coverage_unchanged']['reviewed_through'] == 2000
    assert by_id['journal_65dd21715536a35f']['historical_intervals'][0]['end_meaning'] == 'title_change'
    evidence = {}
    for ref in sorted(refs):
        s = sources[ref]
        evidence[ref] = {'record': s}
        if s.get('claim_source_record_id'):
            evidence[ref]['accepted_claim_source_record'] = claim_sources[s['claim_source_record_id']]
    packet = {
        **{k: v for k, v in decisions.items() if k != 'entries'},
        'inputs': {'graph_revision': audit['input']['revision'],
                   'graph_sha256': graph_hash, 'audit_sha256': sha(AUDIT),
                   'decisions_sha256': sha(PILOT), 'builder_sha256': sha(Path(__file__))},
        'summary': {'graph_entries': 14, 'journal_entries': 2,
                    'dated_events': sum(len(e['events']) for e in entries),
                    'historical_intervals': sum(len(e['historical_intervals']) for e in entries),
                    'referenced_source_records': len(evidence)},
        'entries': packet_entries, 'evidence': evidence,
    }

    def link(ref):
        return f"[{ref}]({sources[ref]['url']})"

    def cell(text):
        return str(text).replace('|', '&#124;').replace('\n', ' ')

    lines = [
        '# Historical chronology pilot — 2026-10-15', '',
        'Research candidate for 14 graph entries and two journals; **not applied to the graph or site**.', '',
        'Historical decisions are authored in [pilot-decisions.json](pilot-decisions.json). '
        '[pilot.json](pilot.json) preserves the baseline, source records and reading limits; '
        '[pilot-summary.csv](pilot-summary.csv) supports comparison. See '
        '[pilot contract](pilot-contract.md) for the meaning of each field.', '',
        'The event sets are a minimum for prototyping, not a replacement for every existing work '
        'or strand. Selected ranges are computed from contribution events only. Context, '
        'editions on a separate track and reception cannot silently extend them. '
        'These ranges do not assert careers, complete field histories or periods of influence.', '',
        'New external checks are limited to the observations and access limits recorded in '
        'the decision file. Other support reuses the existing graph’s explicitly qualified '
        'source notes; this pilot does not claim to have reread those works.', '',
        '## Decisions at a glance', '',
        '| Entry | Previous solid bar | Proposed selection / title start |',
        '| --- | --- | --- |',
    ]
    summary = io.StringIO()
    writer = csv.writer(summary, lineterminator='\n')
    writer.writerow(['id', 'label', 'previous_solid_start', 'previous_solid_end',
                     'contribution_selection_start', 'contribution_selection_end',
                     'historical_interval_count', 'continuation_status', 'display_label', 'decision'])
    for entry in packet_entries:
        old = entry['before']['rendered']
        extent = entry['selected_contribution_extent']
        lines.append('| ' + ' | '.join(map(cell, [entry['label'],
            f"{old['start']}–{old['solid_end']}", entry['display_label']])) + ' |')
        writer.writerow([entry['id'], entry['label'], old['start'], old['solid_end'],
            extent['start'], extent['end'], len(entry['historical_intervals']),
            entry['continuation']['status'], entry['display_label'], entry['decision']])
    for entry in packet_entries:
        lines += ['', f"## {entry['label']} (`{entry['id']}`)", '',
            '**Decision:** ' + entry['decision'], '',
            '**Before:** ' + entry['before']['date_label'], '',
            '**Proposed label:** ' + entry['display_label'], '',
            '**Coverage:** ' + ('Unchanged: ' + str(entry['coverage_unchanged']['reviewed_through'])
                + '. ' + entry['coverage_unchanged']['basis'] if entry['coverage_unchanged']
                else 'No editorial survey year asserted for this entry.'), '',
            '| Date | Event | Track | Evidence and limits |', '| --- | --- | --- | --- |']
        for event in entry['events']:
            evidence_text = event['support'] + ' ' + ', '.join(link(r) for r in event['source_ids'])
            lines.append('| ' + ' | '.join(map(cell, [date_text(event['date']),
                event['label'] + ' — ' + event['kind'].replace('_', ' '),
                event['track'], evidence_text])) + ' |')
        lines += ['', '**Historical intervals:**']
        if not entry['historical_intervals']:
            lines += ['', 'None established for this pilot. Selected events remain visible.']
        for interval in entry['historical_intervals']:
            lines += ['', f"- {interval['subject']}: {date_text(interval['start'])} to "
                f"{date_text(interval['end'])}; end means {interval['end_meaning'].replace('_', ' ')}. "
                + interval['support'] + ' ' + ', '.join(link(r) for r in interval['source_ids'])]
        lines += ['', '**Continuation:** ' + entry['continuation']['status'].replace('_', ' ')
            + '. ' + entry['continuation']['basis'], '', '**Retain:**', '']
        lines += ['- ' + item for item in entry['retain']]
        lines += ['', '**Unresolved:**', '']
        lines += ['- ' + item for item in entry['unresolved']]
    return {
        'pilot.json': json.dumps(packet, ensure_ascii=False, indent=2) + '\n',
        'pilot-review.md': '\n'.join(lines) + '\n',
        'pilot-summary.csv': summary.getvalue(),
    }, packet['summary']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs, summary = build()
    for name, content in outputs.items():
        target = DEST / name
        if args.check:
            assert target.exists() and target.read_text() == content, f'{name} differs; rebuild the pilot'
        else:
            target.write_text(content)
    print(('Verified' if args.check else 'Built') + ' historical timeline pilot: ' + json.dumps(summary))


if __name__ == '__main__':
    main()
