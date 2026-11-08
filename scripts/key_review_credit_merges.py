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
            'centre', 'center', 'institute', 'program', 'programme', 'division', 'unit', 'graduate', 'college',
            # German department words ('Bereich Alte Geschichte, HU-Berlin' / 'Institut für Geschichtswissenschaften der HU')
            'institut', 'fur', 'fuer', 'der', 'die', 'und', 'bereich', 'arbeitsbereich', 'geschichte',
            'geschichtswissenschaften', 'geschichtswissenschaft', 'seminar', 'historisches', 'historische', 'lehrstuhl',
            'fachbereich', 'abteilung', 'fb', 'professur', 'alte', 'neuere', 'neueste', 'mittelalterliche'}


# German university abbreviations as signed ('Institut für Geschichtswissenschaften der HU Berlin', 'FMI, FU-Berlin')
ABBREV = {'hu': ['humboldt'], 'fu': ['freie'], 'tu': ['technische'], 'lmu': ['ludwig', 'maximilians']}


def ordered(s):
    """The distinctive words of an institution name, in order (generic, status and subject words dropped)."""
    out = []
    for t in [w for t in norm(s).split() for w in ABBREV.get(t, [t])]:
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


ROR_TABLE = ROOT / 'data/field-research/jstor-fulltext-2026-11-06/signature-institutions/signature-institutions.csv'
ROR_WRONG = set()      # strings whose grounding is known to be wrong (none: UNO -> ror 034mtvk83 is right, 2026-11-06)
_ror = None


def ror_of(s):
    """The ROR organisation of an institution string, from the JSTOR session's accepted groundings of printed
    signature institutions (exact string, normalised), or None."""
    global _ror
    if _ror is None:
        import csv
        _ror = {}
        if ROR_TABLE.exists():
            with ROR_TABLE.open(newline='', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    if r['decision'] == 'accepted' and r['ror']:
                        for t in (r['string'], r['cleaned']):
                            k = ' '.join(norm(t).split())
                            if k and k not in ROR_WRONG:
                                _ror[k] = r['ror']
    return _ror.get(' '.join(norm(s).split()))


def agree(a, b):
    """Same institution: the same ROR organisation when both strings are grounded (two different RORs never agree);
    otherwise the same distinctive words, or one name's words inside the other's when the extra words
    name no other institution ('Historisches Seminar, Universität Hamburg' / 'Universität Hamburg'; 'Michigan State'
    is not 'Michigan'). When the shorter name is only a place ('Chicago', 'Washington', 'South Africa') its words must
    open the longer one, with only a campus or town after them ('Missouri' / 'Missouri, Columbia'; 'Chicago' is not
    'Loyola Chicago' or 'Illinois at Chicago', 'South Africa' is not 'Monash South Africa')."""
    ra, rb = ror_of(a), ror_of(b)
    if ra and rb:
        return ra == rb
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
    if rest and set(fold(rest).split()) <= set(fold(name).split()) | set(fold(label).replace(',', ' ').split()):
        return None             # 'Gerhard Wettig, Gerhard': a piece of the name, not an institution
    return rest or None


SIGNATURES = Path('/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz')   # JSTOR session, 2026-11-06
QWEN_REVIEWERS = Path('/mnt/e/jstor-fulltext-2026-11-06/review-reviewers-qwen.parquet')
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
    # the Qwen re-read (2026-11-07): reviewers the rules missed ('new') or read differently ('changed'), kept only
    # where Qwen located the signature in the text ('where' set) and printed an institution; the rules win where
    # both give one
    if QWEN_REVIEWERS.exists():
        db = duckdb.connect()
        for iid, name, inst in db.execute(f"""SELECT iid, name, institution FROM '{QWEN_REVIEWERS}'
                WHERE status IN ('new', 'changed') AND "where" IS NOT NULL AND institution IS NOT NULL AND name IS NOT NULL""").fetchall():
            if iid in doi and doi[iid][0] not in out:
                d, y = doi[iid]
                out[d] = (' '.join(name.split()), inst, y)
    return out


# university systems: a bare system name places nobody, whatever the campus (2026-11-07, Fable review: the senior
# James Lockhart's 1969-2003 reviews reached a 2016 PhD through 'University of California')
SYSTEMS = [frozenset(x.split()) for x in ('california', 'wisconsin', 'london', 'wales', 'paris', 'quebec',
           'state new york', 'suny', 'cuny', 'city new york', 'puerto rico')]   # flagship names ('Minnesota') are not systems


def is_system(s):
    return inst(s) in SYSTEMS


SLACK = 10       # years either side of a dated fact (user, 2026-11-07: use dates wherever possible)


def year_of(v):
    m = re.match(r'^\s*(\d{4})', str(v or ''))
    return int(m.group(1)) if m else None


def dated(year, fact, window=None):
    """A fact (institution, source, lo, hi) places the key at an event in `year`, using the best dates the key has
    (user, 2026-11-07: use dates wherever possible):
    - the key has a career window (PhD year, life years; career_window.py): the year must fall inside it; the place
      may be recorded at any point of that career (long tenures: a 2015 credit at Swarthmore places a 1982 reviewer
      there);
    - the key has no dates: the fact itself must be dated, within SLACK years of the event.
    The career window is what separates generations of namesakes (the 2016 PhD James Lockhart is not the reviewer of
    1969-2003)."""
    from career_window import in_window
    _, _, lo, hi = fact
    if year is None:
        return False
    if window is not None and any(x is not None for x in window):
        return in_window(year, window)
    if lo is None and hi is None:
        return False
    lo = lo if lo is not None else hi
    hi = hi if hi is not None else lo
    return lo - SLACK <= year <= hi + SLACK


def overlap(a, b):
    """Two dated facts overlap within SLACK years; an undated side never refuses here (the merge also needs the names
    and no conflicting identifiers)."""
    a0, a1 = (a[0] if a[0] is not None else a[1]), (a[1] if a[1] is not None else a[0])
    b0, b1 = (b[0] if b[0] is not None else b[1]), (b[1] if b[1] is not None else b[0])
    if None in (a0, a1, b0, b1):
        return True
    return a0 - SLACK <= b1 and b0 - SLACK <= a1


def key_institutions(live, db, state=None):
    """key -> [(institution as recorded, source, first year, last year)] from the key's own records (see the module
    docstring). Years (2026-11-07): ORCID employment start/end; the AHA supervision year and the IHR staff-list year;
    LC 373 start/end; the years of the reviews printed with a review credit; the H-Soz-Kult review's year. The AHA
    directory is the 2026 snapshot, taken back to the PhD year (career_window + 8) or forty years; supervision is the
    span of the theses supervised there. A review this route linked earlier is never a placing fact (no cascade)."""
    facts = defaultdict(list)
    span = defaultdict(list)      # (ref, institution, source) -> years observed there
    for ref, institution, src, obs in db.execute(f"""SELECT person_ref, institution, source, observed_year
            FROM read_csv_auto('{POSITIONS}', all_varchar=true)
            WHERE institution IS NOT NULL AND source IN ('ihr', 'aha_directory', 'aha_advisor')""").fetchall():
        span[ref, institution, src].append(year_of(obs) or (2026 if src == 'aha_directory' else None))
    from career_window import career_windows
    windows = career_windows(state) if state is not None else {}
    pos = defaultdict(list)
    for (ref, institution, src), ys in span.items():
        ys = [y for y in ys if y]
        lo, hi = (min(ys), max(ys)) if ys else (None, None)
        pos[ref].append((institution, src, lo, hi))
    hsk = json.loads(HSK.read_text()) if HSK.exists() else {}
    emp = orcid_employment()
    # review years under each review-credit anchor (the claims whose subject is the anchor)
    credit_years = defaultdict(set)
    if state is not None:
        wy = dict(db.execute(f"SELECT key, year FROM '{ROOT}/build/graph/work.parquet' WHERE year IS NOT NULL").fetchall())
        for c, r in state.relation.items():
            if r['subject'].startswith('review-credit:') and state.keys[c]['status'] not in ('withdrawn', 'merged'):
                for w in state.lookup(r['object']):
                    if wy.get(w):
                        credit_years[r['subject']].add(wy[w])
    lc_want = {a[6:]: k for k, r in live.items() for a in r['anchors'] if a.startswith('lcnaf:')}
    db.register('want', db.execute('SELECT unnest(?) AS lcid', [list(lc_want)]).df())
    for lcid, affs in db.execute(f"SELECT lcid, affiliations FROM read_parquet('{LC_NOTES}') JOIN want USING (lcid) WHERE len(affiliations) > 0").fetchall():
        for a in affs:
            if a['org']:
                facts[lc_want[lcid]].append((a['org'], 'LC 373', year_of(a['start']), year_of(a['end'])))
    for k, r in live.items():
        for a in r['anchors']:
            scheme, _, value = a.partition(':')
            ys = sorted(credit_years.get(a, ()))
            lo, hi = (ys[0], ys[-1]) if ys else (None, None)
            if scheme == 'review-credit' and '|' in value:
                facts[k].append((value.split('|', 1)[1], 'review credit', lo, hi))
            elif scheme == 'review-credit' and value.startswith('hnet-review:'):
                i = hsk_institution((hsk.get(value.split(':', 1)[1]) or {}).get('credit'), r['label'])
                if i:
                    facts[k].append((i, 'H-Soz-Kult signature', lo, hi))
            elif scheme in ('ihr', 'aha') and a in pos:
                for i, src, plo, phi in pos[a]:
                    if src == 'aha_directory':
                        # the 2026 directory: at the institution now; taken back to the start of the career when the key
                        # dates it (PhD year, age 20), else forty years
                        wlo = (windows.get(k) or (None, None))[0]
                        plo = (wlo + 8) if wlo is not None else 1986
                    facts[k].append((i, {'ihr': 'IHR Teachers of History', 'aha_directory': 'AHA directory',
                                         'aha_advisor': 'AHA supervision'}[src], plo, phi))
            elif scheme == 'orcid':
                facts[k].extend((org, 'ORCID employment', year_of(st), year_of(en) or (2026 if year_of(st) else None))
                                for org, st, en in emp.get(value, []))
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
    facts = key_institutions(live, db, state)
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
                hit = next(((i, s, j, u) for i, s, a0, a1 in facts[k] for j, u, b0, b1 in facts[t]
                            if agree(i, j) and not is_system(i) and not is_system(j) and overlap((a0, a1), (b0, b1))), None)
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
