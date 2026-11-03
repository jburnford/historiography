"""Works people claim in their ORCID records -> the key log (2026-11-03). Writes a proposal.

User, 2026-11-03, on his own key (Jim Clifford: the graph held his book and thesis, his ORCID record twenty more
works): "we should pull in the orcid data to the graph". The graph's works came only from LC's catalogue, reviews,
theses and the works dissertations cite, so uncited articles were stranded. For every live person key holding an
ORCID whose record is cached (data/orcid-2026-09-21/records, harvested 2026-09-21), each claimed work of a
scholarly type (journal article, book chapter, book, edited book, book review, thesis, conference paper, report,
working paper, encyclopedia entry; not lectures, newspaper or 'other' items; a review is labelled 'Review of
<the title ORCID gives, the book's>') becomes
- the work with its DOI (`doi:<doi>`, lower case), one work however many people claim it; a DOI new to the
  log that is the claimant's own keyed work of the same title (an LC book with a publisher DOI) goes on that work;
  else
- the person's own keyed work with the same title (key_lc_works.title_key of the main title, years within two:
  their LC book, their thesis, a cited article), which gains the anchor `orcid-work:<orcid>:<put-code>`; else
- a new work anchored `orcid-work:<orcid>:<put-code>` (members `year:`, `orcid-type:`);
and the person an `authored` claim (`edited` for an edited book), `orcid-claim:<orcid>:<put-code>`, recorded (one
source, the person's own). A preprint is left out when the person claims a work of the same title.

    python3 scripts/key_orcid_works.py --out data/identifiers/orcid-works-2026-11-03
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_lc_works import title_key

RECORDS = ROOT / 'data/orcid-2026-09-21/records'
TYPES = {'journal-article', 'book-chapter', 'book', 'edited-book', 'book-review', 'dissertation-thesis',
         'conference-paper', 'report', 'working-paper', 'encyclopedia-entry', 'preprint'}


def works_of(orcid):
    path = RECORDS / f'{orcid}.json'
    if not path.exists():
        return None
    groups = ((json.loads(path.read_text()).get('activities-summary') or {}).get('works') or {}).get('group') or []
    out = []
    for g in groups:
        s = g['work-summary'][0]
        if s.get('type') not in TYPES:
            continue
        t = ((s.get('title') or {}).get('title') or {}).get('value') or ''
        sub = ((s.get('title') or {}).get('subtitle') or {}) or {}
        if sub.get('value'):
            t = f'{t}: {sub["value"]}'
        if not t.strip():
            continue
        ids = (g.get('external-ids') or {}).get('external-id', [])
        doi = next((e['external-id-value'].strip().lower() for e in ids if e['external-id-type'] == 'doi'
                    and e['external-id-value'].strip().lower().startswith('10.')), '')
        date = s.get('publication-date') or {}
        y = (date.get('year') or {}).get('value') if date else None
        t = t.strip()
        if s['type'] == 'book-review' and not t.lower().startswith(('review', 'rev.', 'compte rendu')):
            t = f'Review of {t}'                 # ORCID titles a review with the book's title
        out.append(dict(put=str(s['put-code']), type=s['type'], title=t[:250], doi=doi,
                        year=int(y) if (y or '').isdigit() else None))
    titles = {title_key(w['title']) for w in out if w['type'] != 'preprint'}
    return [w for w in out if w['type'] != 'preprint' or title_key(w['title']) not in titles]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    own = defaultdict(list)                       # person key -> (main title key, year, work key) of their works
    for _, subj, pred, obj in state.relations():
        if pred in ('authored', 'edited') and len(subj) == 1 and len(obj) == 1:
            w = state.keys[obj[0]]
            years = [int(m.split(':')[-1]) for m in state.members.get(obj[0], ()) if m.split(':')[-1].isdigit()]
            own[subj[0]].append((title_key(w['label'].split(':')[0]), years[0] if years else None, obj[0]))
    report, by_doi, clusters, claims = Counter(), defaultdict(list), [], []
    joins, doi_own = defaultdict(set), defaultdict(set)
    people = sorted((k for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')),
                    key=lambda k: int(k[2:]))
    for k in people:
        orcids = sorted(a[6:] for a in state.keys[k]['anchors'] if a.startswith('orcid:'))
        if len(orcids) != 1:
            continue
        o = orcids[0]
        ws = works_of(o)
        if ws is None:
            report['record_not_cached'] += 1
            continue
        report['people'] += 1
        for w in ws:
            report[f'type:{w["type"]}'] += 1
            role = 'edited' if w['type'] == 'edited-book' else 'authored'
            claim = dict(anchor=f'orcid-claim:{o}:{w["put"]}', subject=f'orcid:{o}', predicate=role)
            if claim['anchor'] in state.anchor:
                report['claim_exists'] += 1
                continue
            mt = title_key(w['title'].split(':')[0])
            same = sorted({wk for t, y, wk in own.get(k, ()) if t and len(mt.split()) >= 2 and t == mt
                           and (not y or not w['year'] or abs(y - w['year']) <= 2)})
            if w['doi']:
                by_doi[w['doi']].append(w)
                if len(same) == 1 and f'doi:{w["doi"]}' not in state.anchor:
                    doi_own[w['doi']].add(same[0])     # their LC book under its DOI: one work
                claim['object'] = f'doi:{w["doi"]}'
                claims.append(claim)
                continue
            anchor = f'orcid-work:{o}:{w["put"]}'
            if len(same) == 1:
                joins[same[0]].add(anchor)
                report['joined_own_work'] += 1
            else:
                clusters.append(dict(type='work', label=w['title'], anchors={anchor},
                                     members={f'orcid-type:{w["type"]}'} | ({f'year:{w["year"]}'} if w['year'] else set()),
                                     aliases=set(), resolution='established', basis=f'work claimed in ORCID record {o}'))
                report['work_minted_no_doi'] += 1
            claim['object'] = anchor
            claims.append(claim)
    for doi, ks in sorted(doi_own.items()):
        if len(ks) == 1:
            joins[next(iter(ks))].add(f'doi:{doi}')
            report['doi_joined_own_work'] += 1
    joined_dois = {a for v in joins.values() for a in v if a.startswith('doi:')}
    for wk, anchors in sorted(joins.items()):       # one cluster per keyed work: all ORCID entries for it together
        clusters.append(dict(type='work', label=state.keys[wk]['label'], anchors=anchors | {sorted(state.keys[wk]['anchors'])[0]},
                             members=set(), aliases=set(), resolution='established',
                             basis='works claimed in ORCID that are the claimant\'s keyed work of that title'))
    for doi, ws in sorted(by_doi.items()):
        if f'doi:{doi}' in joined_dois or f'doi:{doi}' in state.anchor:   # claims reach a keyed DOI directly
            report['doi_already_keyed'] += f'doi:{doi}' in state.anchor
            continue
        w = ws[0]
        clusters.append(dict(type='work', label=w['title'], anchors={f'doi:{doi}'},
                             members={f'orcid-type:{w["type"]}'} | ({f'year:{w["year"]}'} if w['year'] else set()),
                             aliases=set(), resolution='established', basis='work claimed in ORCID (DOI)'))
        report['doi_works'] += 1
    ops, assign, held = plan(state, clusters)
    for i, c in enumerate(claims):
        ops.append(dict(event='mint', key=f'new:claim-{i}', type='claim', label='', resolution='recorded', anchors=[c['anchor']],
                        relation=dict(subject=c['subject'], predicate=c['predicate'], object=c['object']),
                        basis='claimed in the person\'s ORCID record (cached 2026-09-21)'))
    report['claims'] = len(claims)
    materialise(state, dict(basis='orcid works', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    import gzip
    (args.out / 'proposal.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis="works claimed in keyed people's ORCID records (cached 2026-09-21)", decided_by='build', ops=ops),
        ensure_ascii=False).encode() + b'\n'))
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
