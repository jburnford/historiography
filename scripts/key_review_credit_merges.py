"""Per-review person keys -> the person they are, by name and institution (2026-11-06). Writes a proposal.

key_reviews.py (2026-11-02) minted reviewer keys per name and printed affiliation, and a key of its own for each
review printed with no affiliation (`review-credit:hnet-review:<id>`, mostly H-Soz-u-Kult cross-posts on H-Net):
22,829 such keys carry 10,518 names (Constantin Goschler: his key plus 11). User, 2026-11-06: "we want to dedup as
much as possible"; a merge still needs a fact beyond the name (2026-10-31: identity by works and facts).

A key holding only review credits joins another key of the same name when both place the person at the same
institution. Institutions on a key come from:
- the affiliation printed with its review credits (`review-credit:<name>|<affiliation>`);
- the H-Soz-Kult signature of its H-Net cross-posts ('Rezensiert für H-Soz-Kult von <name>, <institution>'; Wayback
  copies, scripts/harvest_hsozkult_affiliations.py);
- its IHR Teachers of History listings (`ihr:`) and AHA directory and supervision records (`aha:`)
  (data/field-research/historian-positions-2026-10-29);
- employment on its ORCID record (cached records) and LC's 373 affiliations on its LC authority.
Names agree (same family name, compatible given names, a full first given name on both, and the first given names
agreeing, not only an initial: namesake_check_groups.names_agree_strict; 'Jaime Sánchez' is not 'Mark J. Sanchez').
Institutions agree on their distinctive words (key_ihr_staff.agree, with words that name another institution:
'Michigan State' is not 'Michigan', 'Freie Universität Berlin' is not 'Humboldt-Universität zu Berlin').
Keys joined this way form groups; a group merges into its best-identified key (most public identifier families,
then most anchors, then the oldest) unless its names disagree among themselves (an 'H. S. Jones' bridging H. Stuart
and Sian Jones), two different PIDs of one kind would meet, or merge_guard holds a key. Held groups are listed.

    python3 scripts/key_review_credit_merges.py --out data/identifiers/review-credit-merges-2026-11-06
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_ihr_staff import GENERIC as GENERIC_WORDS, POSITIONS, orcid_employment
from orcid_ground import STOP, norm
from key_review_reviewers import family, fold
from merge_guard import blocked_keys
from namesake_check_groups import given_words, names_agree_strict as given_names_agree

HSK = Path('/mnt/e/hsozkult-affiliations.json')
LC_NOTES = Path('/mnt/e/lc-authorities/personal-notes.parquet')
PID = ('lcnaf', 'wd', 'orcid', 'gnd', 'viaf', 'isni', 'idref', 'aha-phd', 'diss-author')
OTHER = {'hope', 'brookes', 'metropolitan', 'hallam', 'moores', 'christ', 'church', 'spa', 'polytechnic', 'ruskin',
         'anglia', 'central', 'northumbria', 'west', 'east', 'north', 'south', 'western', 'eastern', 'northern',
         'southern', 'city', 'new', 'trent', 'saint', 'st', 'mary', 'marys', 'martin', 'martins', 'royal', 'holloway',
         'queen', 'queens', 'kings', 'birkbeck', 'goldsmiths', 'economics', 'oriental', 'african', 'slavonic',
         'courtauld', 'guildhall', 'education', 'open', 'beckett', 'napier', 'caledonian', 'state', 'tech',
         'technology', 'technical', 'technische', 'freie', 'humboldt', 'international', 'christian', 'baptist',
         'catholic', 'lutheran', 'methodist', 'national', 'pacific', 'atlantic', 'community', 'county', 'valley',
         'am', 'medical', 'health', 'law', 'normal', 'teachers', 'wesleyan', 'adventist', 'pontifical', 'federal',
         'autonoma', 'autonomous', 'nacional', 'iberoamericana', 'santiago', 'campus', 'commonwealth', 'dominion', 'loyola', 'george', 'mason', 'johns', 'military',
         'naval', 'air', 'staff', 'war', 'agricultural', 'mechanical', 'rensselaer', 'wilfrid', 'laurier', 'ryerson'}
# a status, not an institution: 'independent scholar' alone places nobody
STATUS = {'independent', 'scholar', 'graduate', 'student', 'candidate', 'ph', 'phd', 'd', 'visiting', 'retired', 'adjunct',
          'assistant', 'associate', 'emerita', 'emeritus', 'doctoral', 'postdoctoral', 'fellow', 'dr', 'prof', 'writer',
          'affiliated', 'with', 'at', 'in', 'formerly', 'former', 'member'}
WEAK = {'london', 'wales', 'berlin', 'paris', 'california', 'texas', 'new', 'york'}


SUBJECTS = {'history', 'historical', 'classics', 'classical', 'philosophy', 'religion', 'religious', 'politics', 'political',
            'archaeology', 'art', 'arts', 'english', 'literature', 'languages', 'language', 'sociology', 'anthropology',
            'geography', 'government', 'relations', 'science', 'sciences', 'behavioral', 'behavioural', 'humanities',
            'social', 'studies', 'american', 'european', 'theology', 'divinity', 'education', 'journalism', 'media',
            'communication', 'cultural', 'culture', 'area', 'foreign', 'modern', 'medieval', 'ancient', 'early',
            'global', 'world', 'women', 'gender', 'jewish', 'asian', 'latin', 'department', 'dept', 'school', 'faculty',
            'universitaet', 'universitat', 'universite', 'universita', 'universidad', 'universidade', 'universiteit',
            'uniwersytet', 'zu', 'di', 'des', 'du', 'del', 'degli', 'studi', 'coll', 'univ', 'inst',
            'centre', 'center', 'institute', 'program', 'programme', 'division', 'unit', 'graduate', 'college'}


def ordered(s):
    """The distinctive words of an institution name, in order (generic, status and subject words dropped)."""
    out = []
    for t in norm(s).split():
        t = 'kings' if t in ('king', 'kings') else t
        if t in STOP or t in STATUS or t in SUBJECTS or t in GENERIC_WORDS or t in out:
            continue
        out.append(t)
    return out


def inst(s):
    return frozenset(ordered(s))


# place names that several institutions share: a bare 'Chicago' or 'Washington' must open the other name
GEO = {'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut', 'delaware', 'florida',
       'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine',
       'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska',
       'nevada', 'hampshire', 'jersey', 'mexico', 'york', 'carolina', 'dakota', 'ohio', 'oklahoma', 'oregon',
       'pennsylvania', 'rhode', 'island', 'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington',
       'wisconsin', 'wyoming', 'chicago', 'boston', 'los', 'angeles', 'philadelphia', 'toronto', 'montreal',
       'london', 'paris', 'berlin', 'munchen', 'munich', 'wien', 'vienna', 'roma', 'rome', 'madrid', 'barcelona',
       'milano', 'milan', 'amsterdam', 'sydney', 'melbourne', 'tokyo', 'beijing', 'cape', 'town', 'africa', 'south',
       'wales', 'scotland', 'ireland', 'england', 'canada', 'america', 'columbia', 'pittsburgh', 'cincinnati',
       'miami', 'dallas', 'houston', 'atlanta', 'denver', 'detroit', 'baltimore', 'san', 'francisco', 'diego',
       'new', 'orleans', 'st', 'louis', 'buenos', 'aires', 'mexico', 'sao', 'paulo', 'rio', 'janeiro', 'lisboa',
       'lisbon', 'frankfurt', 'koln', 'cologne', 'jerusalem', 'tel', 'aviv', 'delhi', 'cairo'}


def agree(a, b):
    """Same institution: the same distinctive words, or one name's words inside the other's when the extra words
    name no other institution ('Historisches Seminar, Universität Hamburg' / 'Universität Hamburg'; 'Michigan State'
    is not 'Michigan'). When the shorter name is only a place ('Chicago', 'Washington', 'South Africa') its words must
    open the longer one, with only a campus or town after them ('Missouri' / 'Missouri, Columbia'; 'Chicago' is not
    'Loyola Chicago' or 'Illinois at Chicago', 'South Africa' is not 'Monash South Africa')."""
    oa, ob = ordered(a), ordered(b)
    ta, tb = frozenset(oa), frozenset(ob)
    if not ta or not tb:
        return False
    if ta == tb:
        return not ta <= WEAK or len(ta) > 1
    small, big = (oa, ob) if len(oa) < len(ob) else (ob, oa)
    ss, sb = frozenset(small), frozenset(big)
    if not ss < sb or ss <= WEAK or (sb - ss) & OTHER:
        return False
    if ss <= GEO:
        return big[:len(small)] == small
    return True


def hsk_institution(credit, label):
    """'Bernhard Lorentz, Humboldt Universität zu Berlin' -> the institution, when the name part is the key's."""
    if not credit or ',' not in credit:
        return None
    name, rest = credit.split(',', 1)
    if fold(family(label)) not in fold(name):
        return None
    rest = re.sub(r'\s*(E-Mail|Email|<|\[).*$', '', rest).strip(' ,.')
    return rest or None


SIGNATURES = Path('/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz')   # JSTOR session, 2026-11-06
JSTOR_RECORDS = Path('/mnt/e/JSTOR_history_citation_graph/records.sqlite')


def jstor_signatures():
    """review DOI -> (printed creator name, institution, year) from the JSTOR full-text signatures (conf >= 0.75)."""
    import gzip
    import sqlite3
    if not SIGNATURES.exists():
        return {}
    c = sqlite3.connect(f'file:{JSTOR_RECORDS}?mode=ro', uri=True)
    doi = {i: (d.lower(), y) for i, d, y in c.execute('SELECT item_id, doi, year FROM records WHERE doi IS NOT NULL')}
    out = {}
    with gzip.open(SIGNATURES, 'rt', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r.get('institution') and (r.get('conf') or 0) >= 0.75 and r['iid'] in doi:
                d, y = doi[r['iid']]
                out[d] = (r['creator'], r['institution'], y)
    return out


def key_institutions(live, db):
    """key -> [(institution as recorded, source)] from the key's own records (see the module docstring)."""
    facts = defaultdict(list)
    pos = defaultdict(set)
    for ref, institution in db.execute(f"""SELECT DISTINCT person_ref, institution FROM read_csv_auto('{POSITIONS}', all_varchar=true)
            WHERE institution IS NOT NULL AND source IN ('ihr', 'aha_directory', 'aha_advisor')""").fetchall():
        pos[ref].add(institution)
    hsk = json.loads(HSK.read_text()) if HSK.exists() else {}
    emp = orcid_employment()
    lc_want = {a[6:]: k for k, r in live.items() for a in r['anchors'] if a.startswith('lcnaf:')}
    db.register('want', db.execute('SELECT unnest(?) AS lcid', [list(lc_want)]).df())
    for lcid, affs in db.execute(f"SELECT lcid, affiliations FROM read_parquet('{LC_NOTES}') JOIN want USING (lcid) WHERE len(affiliations) > 0").fetchall():
        for a in affs:
            if a['org']:
                facts[lc_want[lcid]].append((a['org'], 'LC 373'))
    for k, r in live.items():
        for a in r['anchors']:
            scheme, _, value = a.partition(':')
            if scheme == 'review-credit' and '|' in value:
                facts[k].append((value.split('|', 1)[1], 'review credit'))
            elif scheme == 'review-credit' and value.startswith('hnet-review:'):
                i = hsk_institution((hsk.get(value.split(':', 1)[1]) or {}).get('credit'), r['label'])
                if i:
                    facts[k].append((i, 'H-Soz-Kult signature'))
            elif scheme in ('ihr', 'aha') and a in pos:
                facts[k].extend((i, 'IHR Teachers of History' if scheme == 'ihr' else 'AHA directory/supervision') for i in pos[a])
            elif scheme == 'orcid':
                facts[k].extend((org, 'ORCID employment') for org, _, _ in emp.get(value, []))
    # JSTOR review signatures on reviews already credited to the key (institution printed under the review)
    sigs = jstor_signatures()
    if sigs:
        for k, an in db.execute(f"""SELECT a."from", w.an FROM '{ROOT}/build/graph/authored.parquet' a
                JOIN (SELECT key, unnest(anchors) AS an FROM '{ROOT}/build/graph/work.parquet' WHERE len(reviewer_names) > 0) w
                ON w.key = a."to" WHERE w.an LIKE 'doi:%'""").fetchall():
            sig = sigs.get(an[4:].lower())
            if sig and k in live and given_names_agree(sig[0], live[k]['label']):
                facts[k].append((sig[1], f'JSTOR review signature {sig[2] or ""}'.strip()))
    return facts


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    live = {k: r for k, r in state.keys.items() if r['type'] == 'person' and r['status'] in ('active', 'provisional')}
    db = duckdb.connect()
    db.execute('SET enable_progress_bar = false')
    facts = key_institutions(live, db)
    # candidate pairs: a key holding only review credits, and a key of the same name, sharing an institution
    only_rc = {k for k, r in live.items() if r['anchors'] and all(a.startswith('review-credit:') for a in r['anchors'])}
    by_family = defaultdict(list)
    for k, r in live.items():
        g = given_words(r['label'] or '')
        if g and len(g[0]) > 1:
            by_family[family(r['label'])].append(k)
    num = lambda k: int(k.split('-')[1])
    report, edges, why = Counter(), [], defaultdict(dict)
    report['review_credit_only_keys'] = len(only_rc)
    report['with_an_institution'] = sum(1 for k in only_rc if facts.get(k))
    for fam, ks in by_family.items():
        if len(ks) > 400:
            report['family_too_common_skipped'] += 1
            continue
        mine = [k for k in ks if k in only_rc and facts.get(k)]
        for k in mine:
            for t in ks:
                if t == k or (t in only_rc and num(t) < num(k)) or not facts.get(t):
                    continue
                if not given_names_agree(live[k]['label'], live[t]['label']):
                    continue
                hit = next(((i, s, j, u) for i, s in facts[k] for j, u in facts[t] if agree(i, j)), None)
                if hit:
                    edges.append((k, t))
                    why[k][t] = hit
                    why[t][k] = hit
    report['pairs'] = len(edges)
    parent = {}

    def root(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        parent[root(a)] = root(b)
    groups = defaultdict(set)
    for x in list(parent):
        groups[root(x)].add(x)
    blocked = blocked_keys(state, args.out)
    ops, held, sample = [], [], []
    for g in sorted(groups.values(), key=lambda g: min(map(num, g))):
        ks = sorted(g, key=num)
        labels = [live[k]['label'] for k in ks]
        pids = defaultdict(set)
        for k in ks:
            for a in live[k]['anchors']:
                s = a.split(':', 1)[0]
                if s in PID:
                    pids[s].add(a)
        reason = ('names disagree' if any(not given_names_agree(a, b) for a in labels for b in labels) else
                  'two different PIDs of one kind' if any(len(v) > 1 for v in pids.values()) else
                  'merge guard holds a key' if set(ks) & blocked else None)
        if reason:
            report['groups_held'] += 1
            held.append(dict(reason=reason, keys={k: live[k]['label'] for k in ks}))
            continue
        best = max(ks, key=lambda k: (len({a.split(':', 1)[0] for a in live[k]['anchors']} & set(PID)),
                                      len(live[k]['anchors']), -num(k)))
        report['groups_merged'] += 1
        report['keys_merged_away'] += len(ks) - 1
        if best not in only_rc:
            report['groups_into_identified_key'] += 1
        for k in ks:
            if k == best:
                continue
            i, s, j, u = why[k].get(best) or next(iter(why[k].values()))
            ops.append(dict(event='merge', key=k, into=best, decided_by='rule',
                            basis=f"same name ({live[k]['label']} / {live[best]['label']}); same institution: {s} {i!r} "
                                  f"and {u} {j!r} (key_review_credit_merges)"))
        if len(sample) < 120:
            sample.append(dict(into=best, label=live[best]['label'], keys={k: live[k]['label'] for k in ks},
                               facts={k: facts[k][:4] for k in ks}))
    materialise(state, dict(basis='review credit merges', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='per-review person keys merged with keys of the same name placed at the same institution', decided_by='rule',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'held.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
