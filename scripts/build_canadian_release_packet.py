#!/usr/bin/env python3
"""Turn the reviewed Canadian group drafts into the frozen 1.128 editorial packet.

Input: the groups request's consolidated-request.json (built from drafts/ by
build_consolidated.py) and the atlas. Output: release/editorial-additions.json in the same
packet, which scripts/apply_canadian_groups.py applies to the atlas.

The conversion keeps only the atlas's own fields (GRAPH-FORMAT.md schema 1.4) and records
every dropped drafting field by name, so nothing is lost silently:
- nodes: drafting fields (period_rationale, uptake, description_words, label_note) stay in
  the drafts; no extension_coverage is registered (see EXTENSION_POLICY);
- rosters and strands: atlas fields only;
- sources: only those referenced by a node, roster row, strand or edge. The same work cited
  under several draft ids (same DOI, or the same year and title) becomes one record; the
  stronger verification is kept and the other checks are named in its note;
- people: new people get the atlas identity note; reviewed QIDs go to a separate list for
  data/people-wikidata.json, never into the graph;
- edges: numbered after the atlas's last edge, in proposal-id order.
Run from anywhere. Deterministic.
"""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKT = ROOT / 'data/extension-2026/canadian-historiography-groups-request-2026-10-12'
OUT = PKT / 'release/editorial-additions.json'
DAY = '2026-10-12'

NODE_KEYS = ['id', 'label', 'date_label', 'layer', 'period', 'hunt_core_paradigm', 'description',
             'representative_figures_and_works', 'source_ids', 'entry_kind', 'entry_type', 'scope_note',
             'date_span', 'representative_people', 'strands']
ROSTER_KEYS = ['person_id', 'role', 'context', 'works', 'source_ids', 'basis']
STRAND_KEYS = ['id', 'title', 'focus', 'person_ids', 'works', 'source_ids', 'basis']
EDGE_KEYS = ['source', 'target', 'relationship', 'type', 'relationship_kind', 'directed', 'source_ids',
             'evidence_note', 'classification_basis', 'map_label']  # target_strand is kept when it resolves
STRENGTH = {'supporting_page_checked': 2, 'bibliographic_metadata_checked': 1}
NOT_SAME_WORK = {frozenset(('qcreq_fecteau_1995', 'qcreq_rudin_1995'))}  # two 1995 BHP articles, 'La quête d'une…'
IDENTITY_NOTE = ('Canadian historiography revision 1.128 participant. Roster inclusion does not establish '
                 'external identity resolution; any Wikidata match is recorded separately.')
EXTENSION_POLICY = ('The new entries cover 1920–2000 with earlier roots; their spans end at the 2000 coverage limit. '
                    'Later works appear only as cited readings, historiographical sources and strand works. A directed '
                    'relationship evidenced only by works published after 2000 is deferred (deferred_relationships) to a '
                    'later extension release that registers works and claims. No post-2000 extension coverage or claims '
                    'are registered, and no field is reviewed through 2026.')
DEFER_REASON = ('Evidenced only by works published after 2000 (earliest {year}). GRAPH-FORMAT registers later '
                'interventions through an extension release with work and claim provenance; deferred to that release.')
FAMILY = 'Historiography in Canada'
BRIDGES = {  # user decision 2026-10-12: Canadian entries in a Canada family, bridged to their thematic family
    'cdn_national_tradition': 'Political, national & international',
    'cdn_intellectual_cultural': 'Cultural & intellectual history',
    'cdn_religion_reform': 'Cultural & intellectual history',
    'liberal_order_framework': 'Political, national & international',
    'moral_regulation': 'Social history',
    'cdn_working_class': 'Social history',
    'cdn_women_gender': 'Social history',
    'cdn_childhood_youth': 'Social history',
    'cdn_immigration_ethnicity': 'Social history',
    'cdn_black_history': 'Social history',
    'native_newcomer': 'Indigenous histories',
    'quebec_historiography': 'Political, national & international',
    'cdn_military': 'War & the military',
    'cdn_political_national': 'Political, national & international',
    'who_killed_debate': 'Theory & method',
    'cdn_regional': 'Social history',
    'cdn_sixties': 'Political, national & international',
}
RECORD_ONLY = [('none:canadian_history', 'General Canadian history venues (record only): CHA reports and journal, JCS, H-Canada.')]
NOTE = 'Proposed 2026-10-12 with revision 1.128 (Historiography in Canada family); context or venue evidence only.'
FOLDS = [  # entry, folds_into, relation: context for entries without direct evidence, never evidence
    ('cdn_national_tradition', 'nationaltradition', 'subfield'), ('cdn_intellectual_cultural', 'intellectualhistory', 'subfield'),
    ('cdn_intellectual_cultural', 'culture', 'subfield'), ('cdn_religion_reform', 'none:religious_history', 'subfield'),
    ('liberal_order_framework', 'political', 'method_within'), ('liberal_order_framework', 'historicalsociology', 'method_within'),
    ('moral_regulation', 'historicalsociology', 'method_within'), ('moral_regulation', 'social', 'method_within'),
    ('cdn_working_class', 'labourhistory', 'subfield'), ('cdn_women_gender', 'women', 'subfield'), ('cdn_women_gender', 'gender', 'subfield'),
    ('cdn_childhood_youth', 'none:childhood_youth', 'subfield'), ('cdn_immigration_ethnicity', 'none:ethnic_history', 'subfield'),
    ('cdn_immigration_ethnicity', 'none:migration_history', 'subfield'), ('cdn_black_history', 'black', 'subfield'),
    ('native_newcomer', 'ethnohistory', 'subfield'), ('quebec_historiography', 'nationaltradition', 'subfield'),
    ('cdn_military', 'military', 'subfield'), ('cdn_political_national', 'political', 'subfield'),
    ('cdn_political_national', 'none:diplomatic_international', 'subfield'), ('who_killed_debate', 'political', 'subfield'),
    ('who_killed_debate', 'social', 'subfield'), ('cdn_regional', 'none:local_regional_history', 'subfield'),
    ('cdn_sixties', 'political', 'subfield'), ('cdn_sixties', 'social', 'subfield'),
    ('settler_colonialism', 'none:imperial_colonial_history', 'method_within'),
]
JOURNAL_THEMES = [  # journal title (as in the catalogue) -> new entry; venue rows, proposed
    ('Revue d’histoire de l’Amérique française', 'quebec_historiography'), ('Bulletin d’histoire politique', 'quebec_historiography'),
    ('Les Cahiers des dix', 'quebec_historiography'), ('Mens', 'quebec_historiography'),
    ('Labour/Le Travail', 'cdn_working_class'), ('Canadian Military History', 'cdn_military'),
    ('Ontario History', 'cdn_regional'), ('Acadiensis', 'cdn_regional'),
    ('Études d’histoire religieuse', 'cdn_religion_reform'),
    ('Sessions d’étude - Société canadienne d’histoire de l’Église catholique', 'cdn_religion_reform'),
    ('Journal of the Canadian Historical Association', 'none:canadian_history'),
    ('Historical Papers / Communications historiques', 'none:canadian_history'),
    ('Report of the Annual Meeting of the Canadian Historical Association', 'none:canadian_history'),
    ('Journal of Canadian Studies', 'none:canadian_history'),
]
HNET_THEMES = [('H-Canada', 269, 'none:canadian_history')]
OTHER_FAMILIES = {'settler_colonialism': ('Empire, colonialism & the global', 'Indigenous histories')}


# Drafting artefacts never reach the atlas: placement bookkeeping, question numbers, references
# to drafts and drafters, and "Target is proposed" notes. The drafts keep them. Every change is
# logged in the packet's `publication_edits`.
END = r'[.!?](?=\s|$)'          # a sentence end, not a decimal point or an initial
CLEAN = [
    (r'\s*\[Merged with \w+ from [^:\]]+: ', ' '), (r'\]$', ''),
    (r' on the Q46 definition', ' on a narrower definition'),
    (r'\s*\((?:answer to |see |user decision[^()]*?)?Q\d{1,2}(?:[,;]? ?(?:and )?Q\d{1,2})*\)', ''),
    (r'[;,]\s*Q\d{1,2}\b(?=[);,])', ''), (r'\(Q\d{1,2}[;,]\s*', '('),
    (r'\s*\((?=[^()]{0,40}\))[^()]*\b(?:answers|research) Q\d{1,2}\)', ''),
    (r'\s*\((?:candidates\.csv|groups\.json scope)\)', ''),
    (r'\s*in drafts/[\w]+', ''),
    (r'\s*Target is proposed\.', ''), (r';\s*target is proposed\.', '.'),
    (r'\s*Both endpoints (?:are )?proposed(?: entries| or new)?\.', ''), (r';\s*both endpoints proposed(?: or new)?\.', '.'),
    (r'\s*Source endpoint is a proposed entry\.', ''),
    (r'\bthe proposed ([^.;,()]*?) entry', r'the \1 entry'), (r'is a separate proposed entry', 'is a separate entry'),
    (r'\bare proposed as\b', 'are'), (r'\bboth drafts\b', 'both entries'),
    (r'(^|(?<=[.!?]))\s*The relationship edge for Burrill is.*?' + END + r'(?:\s*[^.!?]*?wcreq_rel_05[^.!?]*' + END + ')?', r'\1'),
    (r';\s*the [^;.!?]*?\bdrafter\b.*?' + END, '.'),
    (r'Primary placement[^;.]*?; (shown|kept|listed)', lambda m: m.group(1).capitalize()),
    (r'(^|(?<=[.!?]))\s*Primary placement.*?' + END, r'\1'),
    (r'[;,]\s*(?:also |and )?primary placement.*?(' + END + ')', r'\1'),
    (r'(^|(?<=[.!?]))\s*[^.!?]*?\b(?:drafter|groups\.json)\b.*?' + END, r'\1'),
    (r'[;,]\s*the [\w-]+ draft proposes.*?(' + END + ')', r'\1'),
    (r'\s*\(volumes (\d{4}–\d{2,4}) in this draft\)', r' (volumes \1 selected here)'),
    (r'\bin this draft\b', 'here'), (r'\bthis draft\b', 'this entry'),
    (r';\s*also in the settler-colonialism draft\.', '.'),
    (r'have (?:their )?primary placements? in', 'are treated mainly in'),
    (r'have primary placements elsewhere', 'are treated mainly elsewhere'),
    (r'keep their primary placements there', 'remain treated mainly there'),
    (r'where (s?he) has (?:her|his) primary placement', r'where \1 is treated mainly'),
    (r'(his|her) primary placement is', r'\1 main entry is'),
    (r'primary placement', 'main entry'),
    # No extension is registered (EXTENSION_POLICY): later works are readings, not extension coverage.
    (r'post-2000 extension partial', 'selected later readings'), (r'mostly post-2000 extension', 'selected later readings'),
    (r'Most of these works are post-2000 \(partial extension\)', 'Most of these works are later readings, after 2000'),
    (r'Post-2000 works are a partial extension', 'Post-2000 works are selected later readings'),
    (r'Post-2000 works are extension', 'Post-2000 works are later readings'),
    (r'All post-2000 \(extension\)', 'All after 2000'), (r'Post-2000 extension', 'After 2000'),
    (r'(?i)post-2000 works? sits? in extension_coverage', 'later works are readings'),
    (r'are in the partial extension', 'are later readings'),
    (r'covers the post-2000 extension', 'is a later reading'), (r'\(post-2000 extension\)', '(after 2000)'),
    (r'; post-2000 extension\)', '; after 2000)'), (r'\(extension; ', '(after 2000; '),
    (r'as extension coverage', 'as a later reading'), (r'carry the strand into the extension', 'carry the strand past 2000'),
    (r'so this is an extension comparison', 'so this comparison rests on later work'),
    (r', extension(?=[,):])', ', after 2000'), (r'\(extension\)', '(after 2000)'),
]
IDS = {}  # raw entry and strand ids in prose -> their labels (filled in main)


def unid(text):
    return re.sub(r'\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b', lambda m: IDS.get(m.group(0), m.group(0)), text)
ABBREV = re.compile(r'\b(?:e\.g|i\.e|cf|pp?|nos?|vols?|eds?|c|ca|St|Dr|Mr|Mrs|Jr|vs)\.|\b[A-Z]\.(?=\s?[A-Z])|\d\.(?=\d)')
MARK = '\u2024'  # one-dot leader stands in for an abbreviation's full stop while cleaning


def clean(text, where, log):
    if not isinstance(text, str):
        return text
    out = ABBREV.sub(lambda m: m.group(0).replace('.', MARK), text)
    for pat, rep in CLEAN:
        out = re.sub(pat, rep, out)
    out = unid(out).replace('the ‘The ', 'the ‘')
    out = re.sub(r'\s{2,}', ' ', out).replace(' .', '.').replace(MARK, '.').strip()
    if out != text:
        log.append(dict(where=where, before=text, after=out))
    return out


def read(path):
    return json.loads(Path(path).read_text())


def fold(text):
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def doi_of(s):
    doi = (s.get('doi') or '').strip()
    if not doi and 'doi.org/' in (s.get('url') or ''):
        doi = s['url'].split('doi.org/', 1)[1]
    return doi.lower()


def title_key(s):
    cit = s.get('citation') or s.get('title') or ''
    m = re.search(r"[‘'\"“]([^’'\"”]{8,})[’'\"”]", cit)
    return (s.get('year'), fold(m.group(1) if m else cit)[:40])


def referenced(entries, rels):
    refs = set()
    for e in entries:
        n = e['node']
        refs.update(n.get('source_ids') or [])
        for r in n.get('representative_people') or []:
            refs.update(r.get('source_ids') or [])
        for s in n.get('strands') or []:
            refs.update(s.get('source_ids') or [])
    for r in rels:
        refs.update(r.get('source_ids') or [])
    return refs


def merge_sources(sources):
    """Union same-work records; return (canonical id per id, groups)."""
    parent = {s['id']: s['id'] for s in sources}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def join(a, b):
        if frozenset((a, b)) in NOT_SAME_WORK:
            return
        parent[find(a)] = find(b)

    for key in (doi_of, title_key):
        seen = {}
        for s in sources:
            k = key(s)
            if not k or (isinstance(k, tuple) and not k[1]):
                continue
            if k in seen:
                join(s['id'], seen[k])
            else:
                seen[k] = s['id']
    groups = defaultdict(list)
    for s in sources:
        groups[find(s['id'])].append(s)
    canon = {}
    for members in groups.values():
        best = max(members, key=lambda s: (STRENGTH.get(s['verification']['status'], 0),
                                           bool(s.get('doi')), -len(s['id']), s['id']))
        for s in members:
            canon[s['id']] = best['id']
    return canon, groups


def atlas_source(s, members):
    v = s['verification']
    note = v.get('note') or ''
    if v.get('checked_against'):
        note = f"{note} Checked against: {v['checked_against']}.".strip()
    others = [m for m in members if m['id'] != s['id']]
    for m in others:  # keep every draft's documented check, not only its status
        mv = m['verification']
        extra = (mv.get('note') or '').strip()
        if mv.get('checked_against'):
            extra = f"{extra} Checked against: {mv['checked_against']}.".strip()
        note += (f" Same work also checked as {m['id']} ({mv['status']}, {mv.get('checked_on') or DAY}; "
                 f"{', '.join(m.get('drafts') or [])}): {extra}")
    url = s.get('url') or (f"https://doi.org/{s['doi']}" if s.get('doi') else None)
    out = dict(id=s['id'], title=s.get('citation') or s.get('title'), url=url, citation=s.get('citation') or s.get('title'),
               verification=dict(status=v['status'], checked_on=v.get('checked_on') or DAY, note=note.strip()))
    scope = s.get('supports') or s.get('claim') or s.get('reading')
    if isinstance(scope, str) and scope.strip():
        out['scope_note'] = scope.strip()
    return out


def remap(ids, canon):
    return list(dict.fromkeys(canon.get(i, i) for i in ids or []))


def main():
    req = read(PKT / 'consolidated-request.json')
    graph = read(ROOT / 'historiography-1920-2000.json')
    atlas_people = {p['id']: p for p in graph['people']}
    atlas_sources = {s['id'] for s in graph['sources']}
    atlas_nodes = {n['id'] for n in graph['nodes']}
    entries, rels = req['entries'], req['relationships']
    for n in graph['nodes'] + [e['node'] for e in entries]:
        if '_' in n['id']:
            IDS[n['id']] = n['label']
    for e in entries:  # strand ids name strands of their own entry; entry ids take precedence
        for st in e['node'].get('strands') or []:
            if '_' in st['id']:
                IDS.setdefault(st['id'], f"‘{st['title']}’")

    refs = referenced(entries, rels)
    pool = [s for s in req['sources'] if s['id'] in refs and s['id'] not in atlas_sources]
    canon, groups = merge_sources(pool)
    sources = [atlas_source(g[0] if len(g) == 1 else next(m for m in g if m['id'] == canon[m['id']]), g)
               for g in groups.values()]
    sources.sort(key=lambda s: s['id'])
    missing = sorted(refs - atlas_sources - set(canon))
    if missing:
        raise SystemExit(f'Unresolved source ids: {missing}')

    dropped = defaultdict(set)
    adjusted, edits = [], []
    nodes = []
    for e in entries:
        n = e['node']
        node = {k: n[k] for k in NODE_KEYS if k in n}
        dropped['node'].update(set(n) - set(NODE_KEYS))
        for k in ('description', 'scope_note', 'representative_figures_and_works', 'date_label'):
            if k in node:
                node[k] = clean(node[k], f"{n['id']}.{k}", edits)
        node['source_ids'] = remap(n.get('source_ids'), canon)
        node['representative_people'] = []
        for r in n.get('representative_people') or []:
            row = {k: r[k] for k in ROSTER_KEYS if k in r}
            row['source_ids'] = remap(r.get('source_ids'), canon)
            for k in ('context', 'works'):
                row[k] = clean(row.get(k, ''), f"{n['id']}.row.{r['person_id']}.{k}", edits)
            dropped['roster'].update(set(r) - set(ROSTER_KEYS))
            node['representative_people'].append(row)
        node['strands'] = []
        for s in n.get('strands') or []:
            st = {k: s[k] for k in STRAND_KEYS if k in s}
            st['source_ids'] = remap(s.get('source_ids'), canon)
            for k in ('title', 'focus', 'works'):
                st[k] = clean(st.get(k, ''), f"{n['id']}.strand.{s['id']}.{k}", edits)
            dropped['strand'].update(set(s) - set(STRAND_KEYS))
            node['strands'].append(st)
        span = node.get('date_span')
        if span:  # enduring fields run to the coverage limit; later works are readings (EXTENSION_POLICY)
            if span.get('end') is not None or span.get('end_kind') not in (None, 'coverage_limit'):
                adjusted.append(f"{node['id']}: date_span end {span.get('end')} ({span.get('end_kind')}) -> 2000 coverage_limit")
            span['end'], span['end_kind'] = 2000, 'coverage_limit'
            span['basis'] = clean(span.get('basis', ''), f"{n['id']}.date_span.basis", edits)
            span['basis'] = (span.get('basis', '') + ' Drawn to the atlas coverage limit (2000); later works are cited '
                             'readings, not registered extension coverage (revision 1.128).').strip()
        nodes.append(node)

    used_people = {r['person_id'] for n in nodes for r in n['representative_people']} | {
        p for n in nodes for s in n['strands'] for p in s['person_ids']}
    people, wikidata = [], []
    for p in req['new_people']:
        if p['id'] in atlas_people:
            raise SystemExit(f"New person already in atlas: {p['id']}")
        if p['id'] not in used_people:
            continue
        people.append(dict(id=p['id'], label=p['label'], identity_note=IDENTITY_NOTE))
        qid = p.get('scholar_packet_qid') or (p.get('wikidata_qid') if p.get('qid_status') in ('correct', 'checked') else None) or p.get('qid')
        if qid:
            wikidata.append(dict(person_id=p['id'], label=p['label'], status='accepted',
                                 wikidata=dict(qid=qid, label=p['label'], method=f'canadian_groups_1.128_{DAY}',
                                               basis=p.get('qid_note') or 'Reviewed in the Canadian scholars packet (candidates.csv).')))
    known = set(atlas_people) | {p['id'] for p in people}
    unknown = sorted(used_people - known)
    if unknown:
        raise SystemExit(f'Unknown people: {unknown}')

    edges = []
    last = max(int(e['id'].split('_')[1]) for e in graph['edges'])
    endpoints = atlas_nodes | {n['id'] for n in nodes}
    cited = {x['id']: x for x in graph['sources'] + sources}

    record_year = {x['id']: x.get('year') for x in req['sources'] if x.get('year')}

    def work_year(sid):
        """Publication year: the record's own year, else the last year in its citation (the imprint),
        never a subject date inside a title."""
        sid_years = [record_year.get(k) for k, v in canon.items() if v == sid and record_year.get(k)]
        if record_year.get(sid) or sid_years:
            return record_year.get(sid) or max(sid_years)
        rec = cited.get(sid, {})
        found = re.findall(r'\b(1[6-9]\d\d|20[0-2]\d)\b', rec.get('citation') or rec.get('title') or '')
        return int(found[-1]) if found else None
    strand_addresses = {f"{n['id']}/{st['id']}" for n in graph['nodes'] + nodes for st in n.get('strands') or []}
    deferred = []
    for r in sorted(rels, key=lambda r: r['proposal_id']):
        if r['source'] not in endpoints or r['target'] not in endpoints:
            raise SystemExit(f"Bad endpoint in {r['proposal_id']}")
        edge = dict(id=None, **{k: r[k] for k in EDGE_KEYS if k in r})
        edge['source_ids'] = remap(r.get('source_ids'), canon)
        for k in ('relationship', 'evidence_note', 'map_label'):
            if k in edge:
                edge[k] = clean(edge[k], f"{r['proposal_id']}.{k}", edits)
        years = [work_year(i) for i in edge['source_ids']]
        if edge['directed'] and years and all(y and y > 2000 for y in years):
            deferred.append(dict(edge, proposal_id=r['proposal_id'], reason=DEFER_REASON.format(year=min(years))))
            adjusted.append(f"{r['proposal_id']}: deferred, later intervention ({min(years)})")
            continue
        strand = (r.get('target_strand') or '').strip()
        if strand:
            if strand in strand_addresses and strand.startswith(r['target'] + '/'):
                edge['target_strand'] = strand
            else:
                adjusted.append(f"{r['proposal_id']}: target_strand {strand!r} dropped (not a strand of target {r['target']})")
        edge['proposal_id'] = r['proposal_id']
        dropped['edge'].update(set(r) - set(EDGE_KEYS) - {'proposal_id', 'target_strand'})
        edges.append(edge)
    for i, edge in enumerate(edges, start=last + 1):
        edge['id'] = f'edge_{i:03d}'
    for d in deferred:
        d.pop('id', None)
    # Proposal ids left in prose become final edge ids (or a note that the relationship is deferred).
    final = {e['proposal_id']: e['id'] for e in edges}
    final.update({d['proposal_id']: 'a deferred relationship' for d in deferred})

    def proposal_ids(text, where):
        out = re.sub(r'\s*\((?:[^()]*?\s)?([a-z]+(?:_[a-z]+)*_rel_\d{2})\)', lambda m: m.group(0) if m.group(1) in final else '', text)
        out = re.sub(r';\s*see ([a-z]+(?:_[a-z]+)*_rel_\d{2})(?=[.;])', lambda m: m.group(0) if m.group(1) in final else '', out)
        for pid in {d['proposal_id'] for d in deferred}:  # clauses pointing at a deferred edge go
            out = re.sub(r',?\s*(?:reached|linked) from here by (?:the \w+ edge )?' + pid, '', out)
            out = re.sub(r',?\s*which also proposes the specific contribution ' + pid + r" into [^.;]*", '', out)
        out = re.sub(r'\b[a-z]+(?:_[a-z]+)*_rel_\d{2}\b', lambda m: final.get(m.group(0), m.group(0)), out)
        if out != text:
            edits.append(dict(where=where, before=text, after=out))
        return out
    for n in nodes:
        for k in ('description', 'scope_note', 'representative_figures_and_works'):
            if k in n:
                n[k] = proposal_ids(n[k], f"{n['id']}.{k}")
        for row in n['representative_people']:
            row['context'] = proposal_ids(row['context'], f"{n['id']}.row.{row['person_id']}.context")
        for st in n['strands']:
            st['focus'] = proposal_ids(st['focus'], f"{n['id']}.strand.{st['id']}.focus")
    for e in edges + deferred:
        e['evidence_note'] = proposal_ids(e['evidence_note'], f"{e['proposal_id']}.evidence_note")

    families = [dict(family=FAMILY, member=gid, member_kind='atlas_entry', bridge_family=b, status='reviewed',
                     note='User decision 2026-10-12: the Canada family is the primary home, bridged to the thematic family.')
                for gid, b in BRIDGES.items() if gid in {n['id'] for n in nodes}]
    for gid, (fam, bridge) in OTHER_FAMILIES.items():
        families.append(dict(family=fam, member=gid, member_kind='atlas_entry', bridge_family=bridge, status='reviewed',
                             note='User decision 2026-10-12: settler colonialism is an international field, bridged to Indigenous histories.'))
    for member, note in RECORD_ONLY:
        families.append(dict(family=FAMILY, member=member, member_kind='record_only', bridge_family='', status='proposed', note=note))
    labels = {n['id']: n['label'] for n in graph['nodes'] + nodes}
    folds = [dict(entry=e, entry_label=labels[e], folds_into=t, relation=r, status='proposed', note=NOTE) for e, t, r in FOLDS]
    crosswalk = [dict(source='journal_title', source_label=title, volume='', volume_unit='research-length items', axis='theme',
                      target=t, target_label=labels[t] if t in labels else 'No atlas entry: ' + t.split(':')[1].replace('_', ' '),
                      status='proposed', note=NOTE) for title, t in JOURNAL_THEMES]
    crosswalk += [dict(source='hnet', source_label=net, volume=str(n), volume_unit='reviews', axis='theme', target=t,
                       target_label='No atlas entry: ' + t.split(':')[1].replace('_', ' '), status='proposed', note=NOTE)
                  for net, n, t in HNET_THEMES]
    unplaced = sorted({n['id'] for n in nodes} - {f['member'] for f in families})
    if unplaced:
        raise SystemExit(f'No family for {unplaced}')

    packet = dict(
        schema='atlas_editorial_packet/1', revision='1.128', baseline_revision=graph['revision_history'][-1]['version'],
        prepared=DAY, request=str((PKT / 'consolidated-request.json').relative_to(ROOT)),
        extension_policy=EXTENSION_POLICY,
        nodes=nodes, people=people, sources=sources, edges=edges,
        source_id_merges={k: v for k, v in sorted(canon.items()) if k != v},
        people_wikidata=wikidata, families=families, deferred_relationships=deferred, approach_folds=folds, crosswalk_rows=crosswalk,
        dropped_drafting_fields={k: sorted(v) for k, v in sorted(dropped.items())}, adjustments=adjusted, publication_edits=edits,
        counts=dict(nodes=len(nodes), people=len(people), sources=len(sources), edges=len(edges),
                    roster_rows=sum(len(n['representative_people']) for n in nodes),
                    strands=sum(len(n['strands']) for n in nodes), merged_source_ids=sum(k != v for k, v in canon.items()),
                    people_wikidata=len(wikidata), deferred_relationships=len(deferred), publication_edits=len(edits), folds=len(folds), crosswalk_rows=len(crosswalk)))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(packet, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(packet['counts']))
    print('dropped:', json.dumps(packet['dropped_drafting_fields']))
    print('\n'.join(adjusted))


if __name__ == '__main__':
    main()
