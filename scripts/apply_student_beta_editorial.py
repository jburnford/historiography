"""Reproduce the bounded 1.125 roster correction; preserve every previous graph claim."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from validate_graph import validate
from build_site import load_baseline

ROOT=Path(__file__).resolve().parents[1]
GRAPH=ROOT/'historiography-1920-2000.json'
BASE=ROOT/'drafts/historiography-1920-2000.v1.124.json'
OUT=ROOT/'data/production-batches/student-beta-1.125'
RECORD='data/production-batches/student-beta-1.125/acceptance.json'
DAY='2026-10-10'


def serial(value):
    return json.dumps(value,ensure_ascii=False,indent=2)+'\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(before):
    if before['revision_history'][-1]['version']!='1.124':
        raise ValueError('Expected revision 1.124')
    graph=deepcopy(before)
    nodes={n['id']:n for n in graph['nodes']}
    sources=[
        dict(id='said_subaltern_foreword_1988',title='Edward W. Said, foreword to Selected Subaltern Studies, edited by Ranajit Guha and Gayatri Chakravorty Spivak (Oxford University Press, 1988).',
             url='https://books.google.com/books/about/Selected_Subaltern_Studies.html?id=JEjsQbxIOC0C',
             verification=dict(status='bibliographic_metadata_checked',checked_on=DAY,
                note='OUP bibliographic description displayed by Google Books checked: editors, 1988 imprint, ISBN 9780195052893 and Said’s foreword credit. The foreword body was not read; this establishes the contribution, not intellectual descent or membership. The direct OUP page returned an anti-bot screen.')),
        dict(id='cooper_stoler_tensions_1997',title='Frederick Cooper and Ann Laura Stoler, eds., Tensions of Empire: Colonial Cultures in a Bourgeois World (University of California Press, 1997).',
             url='https://www.ucpress.edu/books/tensions-of-empire/paper',
             verification=dict(status='supporting_page_checked',checked_on=DAY,
                note='Publisher description, February 1997 date, editor credits and contents checked. The contents credit Stoler and Cooper with the opening research-agenda chapter. The description supports an editorial context connecting colony and metropole and examining changing categories of rule. Chapter and volume bodies were not read; this is not evidence of founding postcolonial theory or of its later reception.'))]
    graph['sources'].extend(sources)
    nodes['subaltern']['representative_people'].append(dict(person_id='edward_said',role='contributor',
        context='Wrote the foreword to the 1988 Selected Subaltern Studies anthology edited by Guha and Spivak. This is a documented editorial contribution; it does not establish founding, collective membership or the direction of theoretical borrowing.',
        works='Foreword to Selected Subaltern Studies (1988)',source_ids=['said_subaltern_foreword_1988'],basis='source_review'))
    nodes['post']['representative_people'].append(dict(person_id='frederick_cooper',role='contributor',
        context='Coedited Tensions of Empire with Ann Laura Stoler (1997) and coauthored its opening research-agenda chapter. The publisher describes a historical and anthropological inquiry into relations between metropole and colony and changing categories of colonial rule. This contextual inclusion does not identify Cooper as an adherent of every postcolonial theory; his later criticisms require a separate dated claim.',
        works='Tensions of Empire (1997), coedited with Ann Laura Stoler; opening chapter, “Between Metropole and Colony: Rethinking a Research Agenda”',
        source_ids=['cooper_stoler_tensions_1997'],basis='source_review'))
    nodes['post']['strands'].append(dict(id='metropole_colony',title='Metropole and colony in a shared research agenda',
        focus='Cooper and Stoler’s 1997 edited collection supplies a contextual reading on connections between imperial centres and colonial settings and the historical formation of categories of rule. This is the publisher’s description and contents, not a passage-level check or a claim that one programme defines postcolonial history.',
        person_ids=['frederick_cooper','ann_laura_stoler'],works='Tensions of Empire (1997), especially the opening chapter credited to Stoler and Cooper',
        source_ids=['cooper_stoler_tensions_1997'],basis='editorial_distinction'))
    for nid,sid in [('subaltern','said_subaltern_foreword_1988'),('post','cooper_stoler_tensions_1997')]:
        nodes[nid]['source_ids'].append(sid)
    graph['revision_history'].append(dict(version='1.125',date=DAY,acceptance_record=RECORD,
        summary='Student beta: two bounded roster contributions from the figure audit. Said’s documented 1988 foreword joins Subaltern Studies; Cooper’s 1997 collaboration with Stoler joins the postcolonial-history context with one internal approach. Bibliographic and publisher-description limits remain explicit. No new entries, people, teaching arrows, or post-2000 claims.'))
    return graph


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    if args.check:
        record=json.loads((OUT/'acceptance.json').read_text())
        before,_=load_baseline(dict(baseline_graph=record['baseline'],baseline_sha256=record['baseline_sha256']))
        if before is None:
            raise ValueError('Hash-pinned baseline is unavailable in snapshots or git history')
        expected=transform(before)
        if json.loads(GRAPH.read_text())!=expected:
            raise ValueError('Exact editorial reconstruction differs')
    else:
        if (OUT/'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before=json.loads(GRAPH.read_text())
        expected=transform(before)
        errors,_=validate(expected,json.loads((ROOT/'seminar-pathways.json').read_text()))
        if errors:
            raise ValueError(str(errors))
        if BASE.exists() and BASE.read_bytes()!=GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        BASE.write_bytes(GRAPH.read_bytes())
        OUT.mkdir(parents=True,exist_ok=True)
        GRAPH.write_text(serial(expected))
        record=dict(revision='1.125',date=DAY,authorization='User: “I want you to do as much of this as you can” following the project review and recommendation to complete small editorial batches.',
            baseline=str(BASE.relative_to(ROOT)),baseline_sha256=sha(BASE),production_sha256=sha(GRAPH),
            resolved_audit_pairs=[dict(entry='subaltern',person='edward_said',disposition='documented_foreword_contribution'),
                                  dict(entry='post',person='frederick_cooper',disposition='bounded_editorial_collaboration')],
            evidence_limits='Foreword credit checked bibliographically; the Cooper/Stoler publisher description and contents were read. Bodies unread. No new influence or critique claim is accepted.',
            source_checks=[dict(url=s['url'],verification=s['verification']) for s in expected['sources'][-2:]],
            preservation='All previous people, edges, sources, entry prose and chronology, claim catalogue, journal catalogue and exact-2000 baseline are unchanged. Two rosters, two source lists and one strand are additive.')
        (OUT/'acceptance.json').write_text(serial(record))
    errors,warnings=validate(expected,json.loads((ROOT/'seminar-pathways.json').read_text()))
    print(f'1.125: {len(errors)} errors; {len(warnings)} warnings; exact reconstruction checked')


if __name__=='__main__':
    main()
