"""Prepare, but do not apply, source-reviewed historian reading bridges."""
from collections import defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RELEASE = ROOT / 'data/field-research/dissertation-citations-2026-10-11/release/2026-10-23'
REVIEW = ROOT / 'data/dissertation-layer/reviews/historian-canon-2026-10-25.json'

def load(p):
    return json.loads(p.read_text())

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def norm(t):
    t = ' '.join(re.sub(r'[^a-z0-9 ]', ' ', unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()).split())
    return re.sub(r'^(the |a |les |le |la |l )', '', t)

def matches(a, b):
    a, b = norm(a.split(':')[0]), norm(b.split(':')[0])
    return min(len(a), len(b)) >= 6 and (a in b or b in a)

# These four selections need the source's fuller bibliography, or an explicit
# translation/publication credit, beyond the biography's selected dated events.
SUPPLEMENT = {
 'jacques_le_goff': ('W:le goff|histoire et memoire', {
  'url': 'https://www.cercle-enseignement.com/Ouvrages/Gallimard/Folio-histoire/Histoire-et-memoire',
  'checked_on': '2026-10-25', 'scope': 'Gallimard author/title metadata credits Jacques Le Goff with Histoire et mémoire. This is an additional metadata bridge beyond the biography’s dated selections. The listed 1988 Folio manifestation is not substituted for all component dates; book body unread.'}),
 'alain_corbin': ('W:corbin|miasme et la jonquille', {
  'url': 'https://wellcomecollection.org/works/h8phtv63', 'checked_on': '2026-10-25',
  'scope': 'Wellcome library catalogue explicitly identifies The Foul and the Fragrant as the English translation of Le Miasme et la Jonquille by Alain Corbin. The frozen release retains the French work key but an English title label. No relabeling, edition merge or new reading; translation and original dates remain distinct.'}),
 'michael_b_katz': ('W:katz|in the shadow of the poorhouse', {
  'url': 'https://www.pennpress.org/blog/in-memoriam-michael-b-katz/', 'checked_on': '2026-10-25',
  'scope': 'The biography’s publisher memorial includes Thomas Sugrue’s explicit attribution of In the Shadow of the Poorhouse to Michael B. Katz. This names the work beyond the entry’s three dated selections; no book-body reading.'}),
 'colin_g_calloway': ('W:calloway|american revolution in indian country', {
  'url': 'https://www.cambridge.org/core/books/abs/american-revolution-in-indian-country/frontmatter/9147F7F8E1DB0D07B6B27963DE02402A',
  'checked_on': '2026-10-25', 'scope': 'Cambridge publisher author/title metadata credits Colin G. Calloway with The American Revolution in Indian Country. Print 1995 and online 2014 are distinct. This metadata supplement extends the biography’s selected named works; no book-body reading.'}),
}
EXCEPTIONS = {
 'georges_duby': 'W:duby|trois ordres ou limaginaire du feodalisme',
 'gerard_noiriel': 'W:noiriel|creuset francais',
 'jeremy_black': 'W:black|rethinking military history',
 'michel_vovelle': 'W:vovelle|ideologies et mentalites',
 'christophe_charle': 'W:charle|naissance des intellectuels',
}

def main():
    queue = load(ROOT / 'data/field-research/dissertation-content-2026-10-25/expanded-scope.json')['people']
    queue += [dict(person_id='sarah_carter', source_key='P:carter|sarah a', name='Sarah Carter')]
    base = load(HERE / 'baseline.json')
    existing = base['links']
    exception_counts = load(HERE / 'exception-counts.json')
    public = {row['index']['key']: row['index'] for row in base['sources']}
    graph = load(ROOT / 'historiography-1920-2000.json')
    canonical_nodes = {n['id']: n for n in graph['nodes']}
    sources = {s['id']: s for s in graph['sources']}
    works, by_author = {}, defaultdict(list)
    with gzip.open(RELEASE / 'works.csv.gz', 'rt') as f:
        for w in csv.DictReader(f):
            works[w['work_id']] = w
            by_author[w['first_author_key']].append(w)
    decisions, accepted, unresolved = {}, [], []
    for p in queue:
        pid, source = p['person_id'], p['source_key']
        paths = list((ROOT / 'data/extension-2026').glob('**/' + pid + '/entry-draft.json'))
        if len(paths) != 1:
            unresolved.append(dict(person_id=pid, reason='Expected one prepared biography', paths=[str(x.relative_to(ROOT)) for x in paths]))
            continue
        path = paths[0]
        draft = load(path)
        node = canonical_nodes.get(pid, draft['node'])
        events = node['chronology']['events']
        available_sources = {**{s['id']: s for s in draft.get('new_sources', [])}, **sources}
        if 'dated_dissertations' in p:
            assert public[source]['n'] == p['dated_dissertations'], pid
        if pid in existing['people']:
            decision = existing['people'][pid]
            keys = decision['works']
            status = 'retain_existing_unchanged'
        elif pid == 'sarah_carter':
            keys = ['W:carter|lost harvests', 'W:carter|importance of being monogamous', 'W:carter|capturing women']
            status = 'accept_named_work_bridge'
        elif pid in EXCEPTIONS:
            keys = [EXCEPTIONS[pid]]
            status = 'accept_reviewed_lowcount_work_bridge'
        elif pid in SUPPLEMENT:
            keys = [SUPPLEMENT[pid][0]]
            status = 'accept_named_work_bridge_with_metadata_supplement'
        else:
            eligible = [w for w in by_author[source[2:]] if w['work_id'] in public and any(matches(w['title'], e['label']) for e in events)]
            eligible.sort(key=lambda w: -public[w['work_id']]['n'])
            if not eligible:
                unresolved.append(dict(person_id=pid, reason='No exported named work matched a sourced biography event'))
                continue
            keys = [eligible[0]['work_id']]
            status = 'accept_named_work_bridge'
        verified = []
        for key in keys:
            w = works[key]
            assert w['first_author_key'] == source[2:], (pid, key, w['first_author_key'])
            ev = [e for e in events if matches(w['title'], e['label'])
                  or (pid == 'alain_corbin' and matches(key.split('|', 1)[1], e['label']))]
            witnesses = []
            for sid in dict.fromkeys(s.removeprefix('graph:') for e in ev for s in e['source_ids']):
                s = available_sources[sid]
                witnesses.append(dict(source_id=sid, url=s.get('url'), verification=s.get('verification', {})))
            supplement = SUPPLEMENT.get(pid)
            if supplement:
                canonical_witness = next((s for s in available_sources.values()
                                          if s.get('url') == supplement[1]['url']), None)
                witnesses.append({**supplement[1], **({'source_id': canonical_witness['id'],
                    'verification': canonical_witness.get('verification', {})}
                    if canonical_witness else {})})
            if not witnesses:
                unresolved.append(dict(person_id=pid, work=key, reason='No matched event/source or reviewed supplemental witness'))
                break
            verified.append(dict(work_id=key, release_title=w['title'], release_year=w['year'], release_first_author=w['first_author'],
                release_first_author_key=w['first_author_key'], release_raw_strict_dissertations=int(w['cited_by_strict_phds']),
                public_dated_dissertations=public.get(key, exception_counts.get(key, {})).get('n'),
                source_scope='reviewed_counts_only_exception' if key not in public else 'existing_exported_source',
                biography_events=[dict(id=e['id'], label=e['label'], date=e['date'], support=e.get('support', ''), source_ids=e['source_ids']) for e in ev],
                primary_evidence=witnesses))
        else:
            note = 'The teaching link identifies ' + node['label'] + ' through ' + '; '.join(works[k]['title'] for k in keys) + '. '
            note += 'The displayed total covers one frozen first-author name key; selected works verify this bridge, not every attributed citation. No variant-key totals, authority identities or influence claims are merged.'
            if pid == 'sarah_carter':
                note += ' The exact Sarah Carter key is retained; Dan T. Carter’s The Politics of Rage is excluded.'
            if pid == 'alain_corbin':
                note += ' The frozen French work key retains its English translation label; original and translation dates remain distinct.'
            if pid not in existing['people']:
                decisions[pid] = dict(source=source, works=keys, review_note=note)
            accepted.append(dict(person_id=pid, label=node['label'], source=source, decision=status,
                public_dated_first_author_dissertations=public[source]['n'],
                biography_packet=str(path.relative_to(ROOT)), biography_packet_sha256=digest(path),
                biography_reading_scope=node.get('scope_note'),
                teaching_context_ids=list(dict.fromkeys([r['node'] for r in draft.get('roster_additions', [])] + [pid])),
                verified_work_credits=verified, review_note=existing['people'].get(pid, {}).get('review_note', note)))
    review = dict(schema='teaching_reading_bridge_review/1', date='2026-10-25', snapshot='2026-10-23',
        status='prepared_not_applied', target_historians=89, target_scope='88 expanded-scope people plus Sarah Carter; theory and unresolved identities remain separate.',
        graph_revision=graph['revision_history'][-1]['version'] if 'version' in graph['revision_history'][-1] else graph['revision_history'][-1],
        graph_sha256=digest(ROOT / 'historiography-1920-2000.json'),
        people=accepted, proposed_people_additions=decisions, unresolved=unresolved,
        preserve=dict(existing_people=25, existing_entry_selections=5, baseline='data/field-research/dissertation-content-2026-10-25/reading-bridge-integration/baseline.json'),
        limits=['Named-work metadata verifies identity for the bridge; it is not full-book reading or a citation-by-citation attribution audit.',
                'All old source IDs, index metadata and n/series/n_region remain immutable; append only reviewed exceptions.',
                'Release all-credit counts and dated first-author counts stay separate; no sums across variant or translation keys.',
                'No existing people links, five field selections, questions, family analyses or frozen release/explorer records are changed.'])
    REVIEW.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
    (HERE/'candidate-people.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2)+'\n')
    candidate_links = {**existing, 'people': {**existing['people'], **decisions}}
    (HERE/'candidate-links.json').write_text(json.dumps(candidate_links, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(accepted=len(accepted), additions=len(decisions), unresolved=unresolved), indent=2))

if __name__ == '__main__':
    main()
