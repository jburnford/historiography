"""New dissertation-corpus theses -> key-log PROPOSALS, in parts, staged and dry-run in order (2026-11-16). Never applies.

The corpus rebuild of 2026-11-16 (5eabf64c, after the ingest ad078e30) holds 1,818 eligible theses the key log does
not (US 615, Canada 157, Germany 1,042, Switzerland 2, Austria 1, UK 1). The Mexico ingest (2ea09b10, 2026-11-05)
was never keyed either (701 MX + 6 FR), nor 85 US theses (Harvard 51, Oklahoma 34) made eligible after the 11-03
keying. This script keys them the way scripts/key_theses.py (11-01, 11-03 Brazil, 11-03b UChicago),
scripts/key_relations.py and scripts/key_repository_supervisors.py did, with the user's rules of 2026-11-14/16:

- Thesis works: `diss-thesis:<id>` (+ `aha-diss:<record>` when the record is the AHA directory's), `year:`,
  `awarded-by:i-N`. A work joins the AHA work when the AHA id is on the corpus record (doctorates.json `aha_id`,
  set by the AHA-register match), the US harvest matched it, or key_theses.aha_by_record finds the one record.
- Authors, US / Canada / Mexico / backlog (earlier rounds): one person per thesis, `diss-author:<id>`, joining the
  AHA record's person (`aha-phd:`) and a canon key whose cited works include the thesis as published
  (key_aha.own_book); otherwise minted (`recorded`). An AHA join whose names disagree is held.
- Authors, DNB records (Germany, Austria, Switzerland, one UK thesis): SEEDS. A person key only by a link to the
  graph: the author's GND id on a key (attach), the GND record's LC/Wikidata id on a key, or a same-name key
  (family name and full first given name, no nickname) whose key-log book/article is this thesis as published
  (title words, -1..+15 years; or the record's ISBN/DOI on the key's work). One candidate only; no other PID on the
  key that contradicts; life years allow the degree (age 20+); merge guard. Otherwise the author stays a printed
  name in seeds.csv.gz (no key).
- Authored claims (`diss-auth:<id>`, key_relations' form) for every keyed thesis that lacks one: this round's and
  the backlog of earlier rounds (Brazil 11-03, UChicago 11-03b: key_relations was not rerun after them).
- Supervisors: repository advisors as key_repository_supervisors (US/CA/MX); DNB `dgs`/'Betreuer' people linked
  only when their GND id (or its LC/Wikidata) is on a key; DNB 'Gutachter' (referees) the same, written to
  refereed.csv.gz (no key-log predicate exists for refereeing).
- published_as claims (key_published_as.matches) for attached authors whose LC book is the thesis.

Parts are staged in order on the key-log cache (read-only; events stay in memory) so each later part is validated
against the state the earlier ones would leave. Output folder: proposals, held.json, seeds, refereed, report.json.

    python3 scripts/key_thesis_round.py --out data/identifiers/thesis-round-2026-11-16
"""
import argparse
import csv
import gzip
import io
import json
import re
import sqlite3
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
import keylog_snapshot as KS  # noqa: E402
from aha_links import same_listed_name, title_words  # noqa: E402
from key_aha import AHA, own_book, author_merge_ok  # noqa: E402
from key_registry import names_compatible  # noqa: E402
from key_theses import aha_matches  # noqa: E402
from key_repository_supervisors import FRANCE, advisor_names, norm as rnorm  # noqa: E402
from key_published_as import matches as published_matches  # noqa: E402
from held_lc_rules import stems  # noqa: E402
from merge_guard import guarded, blocked_keys  # noqa: E402
from lc_canon_people import content  # noqa: E402
from graph_tables import keylog  # noqa: E402

ROOT = I.ROOT
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
TABLE = 'data/field-research/dissertation-citations-2026-10-11/dissertations.csv'
DNB_RAW = Path('/mnt/e/dnb-history-diss-2026-11-14/records-2000-2027.jsonl')
DNB_TABLE = ROOT / 'data/field-research/dnb-germany-harvest-2026-11-14/theses.csv.gz'
GND_INDEX = Path('/mnt/e/gnd/gnd-persons.parquet')
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
G = ROOT / 'build/graph'
PID = ('lcnaf', 'wd', 'orcid', 'viaf', 'gnd', 'isni', 'idref')
INGEST_BEFORE, MEXICO_BEFORE = 'ad078e30^', '2ea09b10^'


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def parse(label):
    """(family, [given names]) for 'Family, Given' or 'Given Family'; None for initials-only or one word."""
    l = re.sub(r'\(.*?\)|,?\s*\d{4}\??-(\d{4})?|\b(dr|prof|professor|sir|rev)\b\.?', '', fold(label)).strip(' ,.')
    if ',' in l:
        fam, giv = l.split(',', 1)
    else:
        t = l.split()
        if len(t) < 2:
            return None
        fam, giv = t[-1], ' '.join(t[:-1])
    g = [x for x in re.split(r'[\s.\-]+', giv) if x]
    fam = re.sub(r'\s+', ' ', fam.replace('-', ' ')).strip()
    return (fam, g) if g and fam else None


def full_agree(a, b):
    """Family names equal (accents folded; 'von' particles kept as printed), the first given name written out on both
    sides and identical (no initials, never a nickname), a second given name or initial compatible where both have one."""
    for x, y in ((a, b), (a.translate(UML), b.translate(UML))):
        pa, pb = parse(x), parse(y)
        if not pa or not pb or pa[0] != pb[0]:
            continue
        ga, gb = pa[1], pb[1]
        if len(ga[0]) < 2 or len(gb[0]) < 2 or ga[0] != gb[0]:
            continue
        if len(ga) > 1 and len(gb) > 1 and ga[1][0] != gb[1][0]:
            continue
        return True
    return False


UML = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'})


def git_ids(rev):
    s = subprocess.run(['git', '-C', str(ROOT), 'show', f'{rev}:{TABLE}'], capture_output=True, text=True, check=True).stdout
    return {r['id'] for r in csv.DictReader(io.StringIO(s))}


def year_int(v):
    v = str(v or '')[:4]
    return int(v) if v.isdigit() else None


class Stage:
    """The cache's state with the parts staged so far (events in memory only)."""

    def __init__(self):
        I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
        self.state = KS.read_state()
        self.db = sqlite3.connect(f'file:{KS.DB}?mode=ro', uri=True)
        self.seq0 = self.state.seq

    def run(self, name, proposal):
        events, names = I.materialise(self.state, proposal, 'dry-run', 'dry-run', inplace=True)
        return dict(part=name, ops=len(proposal['ops']), events=len(events),
                    by_event=dict(Counter(e['event'] for e in events)),
                    minted_by_type=dict(Counter(e['type'] for e in events if e['event'] == 'mint')))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    R = Counter()
    held, notes = [], {}
    st = Stage()
    state = st.state
    sql = st.db

    def live(k):
        return k in state.keys and state.keys[k]['status'] in ('active', 'provisional')

    def one(anchor):
        ks = state.lookup(anchor)
        return ks[0] if len(ks) == 1 else None

    # ---------------------------------------------------------------- theses to key
    with (D / 'dissertations.csv').open(newline='', encoding='utf-8') as f:
        table = {r['id']: r for r in csv.DictReader(f)}
    docs = {d['id']: d for d in json.loads((D / 'doctorates.json').read_text())}
    before_ingest, before_mexico = git_ids(INGEST_BEFORE), git_ids(MEXICO_BEFORE)
    todo = []
    for tid, t in table.items():
        if t['eligibility'] != 'history_phd' and t['in_analysis'] != 'True':
            continue
        if f'diss-thesis:{tid}' in state.anchor:
            continue
        group = 'ingest' if tid not in before_ingest else 'mexico' if tid not in before_mexico else 'us-backlog'
        todo.append(dict(t, group=group, doc=docs.get(tid, {})))
    R['theses_to_key'] = len(todo)
    for t in todo:
        R[f'theses:{t["group"]}:{t["country"]}:{"strict" if t["in_analysis"] == "True" else "history_phd_not_strict"}'] += 1

    # institution keys, as key_theses.institution_key (from the alias table)
    def institution_key(slug, country):
        for alias in (f'diss-inst:{slug}', f'diss-inst:{(country or "").lower()}:{slug}', f'diss-inst:uk:{slug}'):
            if alias in state.alias:
                return state.alias[alias]
        return None

    # AHA: the corpus record's own aha_id, then the US harvests' match, then key_theses' by-record crosswalk
    harvest = aha_matches({t['id'] for t in todo})
    inst_names = {}
    for k, m in sql.execute("SELECT key, member FROM members WHERE member >= 'inst-name:' AND member < 'inst-name;'"):
        inst_names[m[len('inst-name:'):]] = k
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        aha_rec = {r['id']: r for r in csv.DictReader(f)}
    by_inst = defaultdict(list)
    for r in aha_rec.values():
        if r['department'] in inst_names and (r['year'] or '').isdigit() and r['title'] and r['title'] != '[No title]':
            by_inst[inst_names[r['department']]].append((r, title_words(r['title'])))
    aha_of = {}
    for t in todo:
        d = t['doc']
        if d.get('ingest_source') == 'dnb_germany':
            continue
        if d.get('aha_id'):
            aha_of[t['id']] = (str(d['aha_id']), 'corpus record aha_id')
        elif t['id'] in harvest:
            aha_of[t['id']] = harvest[t['id']]
    hits = {}
    for t in todo:
        if t['id'] in aha_of or t['doc'].get('ingest_source') == 'dnb_germany' or not t['year'].isdigit():
            continue
        ik = institution_key(t['institution'], t['country'])
        if not ik:
            continue
        w = title_words(t['title'])
        c = [r for r, w2 in by_inst.get(ik, ()) if abs(int(r['year']) - int(t['year'])) <= 1
             and len(w & w2) >= 2 and len(w & w2) >= 0.8 * min(len(w), len(w2))]
        if len(c) == 1:
            hits[t['id']] = c[0]
    reached = Counter(r['id'] for r in hits.values())
    for tid, r in hits.items():
        if reached[r['id']] == 1:
            aha_of[tid] = (r['id'], 'institution, year and title')
    used = Counter(rid for rid, _ in aha_of.values())
    for tid in [t for t, (rid, _) in aha_of.items() if used[rid] > 1]:
        held.append(dict(kind='aha_record_on_two_theses', thesis=tid, record=aha_of.pop(tid)[0]))

    # ---------------------------------------------------------------- canon own-book candidates (key_aha.canon_works, via SQL)
    canon_ids = {}
    for a, k in sql.execute("SELECT anchor, key FROM anchor WHERE anchor >= 'diss-person:' AND anchor < 'diss-person;'"):
        if live(k):
            canon_ids.setdefault(a[len('diss-person:'):], k)
    db = duckdb.connect()
    db.execute('CREATE TABLE k(person_key VARCHAR)')
    db.executemany('INSERT INTO k VALUES (?)', [(g,) for g in canon_ids])
    rows = db.execute(f"""
        WITH a AS (SELECT person_key, work_id FROM read_csv('{D / 'authored.csv.gz'}', all_varchar=true)
                   WHERE person_key IN (SELECT person_key FROM k))
        SELECT a.person_key, w.title, w.year FROM a
        JOIN read_csv('{D / 'works.csv'}', all_varchar=true, max_line_size=10000000) w USING (work_id)
        WHERE w.title IS NOT NULL""").fetchall()
    cw = defaultdict(list)
    for g, title, year in rows:
        c = set(content(title))
        if len(c) >= 3:
            cw[g].append((c, int(year) if (year or '').isdigit() else None))
    canon = defaultdict(list)
    for g, k in canon_ids.items():
        if cw.get(g):
            canon[g.split('|')[0]].append((k, state.keys[k]['label'], cw[g]))
    del rows, cw

    # ---------------------------------------------------------------- works side for DE: key-log authored works of people
    people = {}
    for k, label, anchors in db.execute(f"SELECT key, label, anchors FROM '{G}/person.parquet'").fetchall():
        people[k] = (label, anchors or [])
    by_name = defaultdict(set)

    def name_index(label):
        out_ = set()
        for x in (label, label.translate(UML)):
            p_ = parse(x)
            if p_ and len(p_[1][0]) > 1:
                out_.add((p_[0], p_[1][0]))
        return out_
    for k, (label, _) in people.items():
        for nk in name_index(label):
            by_name[nk].add(k)

    def same_name_keys(name):
        return sorted({k for nk in name_index(name) for k in by_name.get(nk, ())}, key=I._num)
    works_of = defaultdict(list)
    for pk, wk, title, year, kind, isbn, anchors in db.execute(f"""SELECT a."from", w.key, w.label, w.year, w.kind, w.isbn, w.anchors
            FROM {keylog(G, 'authored')} a JOIN '{G}/work.parquet' w ON w.key = a."to" """).fetchall():
        works_of[pk].append((wk, title or '', year, kind, isbn or '', anchors or []))
    df = Counter()
    for t in table.values():
        df.update(stems(t['title']))
    life = {}
    with gzip.open(LIFE, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            life[r['key']] = (year_int(r['birth']), year_int(r['death']))

    # DNB: roles (dgs/'Betreuer' supervisors, 'Gutachter' referees) and ISBNs from the raw catalogue records
    editions = {}
    with gzip.open(DNB_TABLE, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            editions[r['dnb_id']] = [r['dnb_id']] + [x for x in re.split(r'[;|, ]+', r['other_edition_ids']) if x]
    raw = {}
    if DNB_RAW.exists():
        with DNB_RAW.open(encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                raw[r['id']] = r
    else:
        R['dnb_raw_records_missing'] = 1
    gnd_ids = set()
    for t in todo:
        d = t['doc']
        if d.get('ingest_source') == 'dnb_germany':
            gnd_ids.add(d.get('author_gnd') or '')
            for e in editions.get(d.get('dnb_id', ''), [d.get('dnb_id', '')]):
                for p in (raw.get(e) or {}).get('supervisors', []) + (raw.get(e) or {}).get('contributors', []):
                    gnd_ids.add(p.get('gnd') or '')
    gnd_ids.discard('')
    gnd_idx = {}
    if GND_INDEX.exists():
        db.execute('CREATE TABLE gq(x VARCHAR)')
        db.executemany('INSERT INTO gq VALUES (?)', [(x,) for x in sorted(gnd_ids)])
        for g, name, birth, lc, wd in db.execute(f"SELECT p.gnd, p.name, p.birth, p.lc, p.wd FROM '{GND_INDEX}' p JOIN gq ON p.gnd = gq.x").fetchall():
            gnd_idx[g] = dict(name=name, birth=year_int(birth), lc=lc or [], wd=wd or [])

    def gnd_keys(g, name):
        """Person keys reached by a GND id: the gnd: anchor on a key, else the GND record's LC/Wikidata id on a key
        whose label agrees with the printed name. Returns (keys, route)."""
        k = one(f'gnd:{g}')
        if k and state.keys[k]['type'] == 'person':
            return {k}, 'gnd anchor on the key'
        rec = gnd_idx.get(g)
        if not rec:
            return set(), ''
        ks = set()
        for x in [f'lcnaf:{l}' for l in rec['lc']] + [f'wd:{q}' for q in rec['wd']]:
            kk = one(x)
            if kk and state.keys[kk]['type'] == 'person' and names_compatible(state.keys[kk]['label'], name):
                ks.add(kk)
        return ks, 'GND record names an LC/Wikidata id on the key' if ks else ''

    def pid_clash(k, gnd):
        own = {a for a in state.keys[k]['anchors'] if a.startswith('gnd:')}
        return bool(gnd and own and f'gnd:{gnd}' not in own)

    def age_ok(k, year):
        b, _ = life.get(k, (None, None))
        return not (b and year and year - b < 20)

    blocked = blocked_keys(state, exclude=out)

    # ---------------------------------------------------------------- part 1 (works) and parts 2/3 (authors)
    # the same doctorate already in the graph as a thesis work (another repository's record, an ORCID thesis): same
    # family name, 80% of the shorter title's words, years within two, one work, its one key-log author's name agreeing
    def famkey(name):
        n = fold(name)
        return re.sub(r'[^a-z]', '', n.split(',')[0] if ',' in n else (n.split() or [''])[-1])
    graph_theses = defaultdict(list)
    for wk, label, wy, pkeys in db.execute(f"""SELECT w.key, w.label, w.year, list(a."from") FROM '{G}/work.parquet' w
            LEFT JOIN {keylog(G, 'authored')} a ON a."to" = w.key WHERE w.kind = 'thesis' GROUP BY ALL""").fetchall():
        for pk in {x for x in pkeys if x}:
            if pk in people:
                graph_theses[famkey(people[pk][0])].append((wk, label or '', wy, pk))
    same_thesis = {}
    by_fam_round = defaultdict(list)
    for t in sorted(todo, key=lambda x: x['id']):
        by_fam_round[famkey(t['author'] or '')].append(t)
    for fam, ts in by_fam_round.items():
        for i, a in enumerate(ts):
            for b in ts[i + 1:]:
                wa, wb = title_words(a['title']), title_words(b['title'])
                sh = len(wa & wb)
                ya, yb = year_int(a['year']), year_int(b['year'])
                if wa and wb and sh >= 2 and sh >= 0.8 * min(len(wa), len(wb)) and (ya is None or yb is None or abs(ya - yb) <= 2) \
                        and b['id'] not in same_thesis:
                    same_thesis[b['id']] = None
                    held.append(dict(kind='two_records_of_one_thesis_in_this_round', thesis=b['id'], kept=a['id'], author=b['author'],
                                     titles=[a['title'][:150], b['title'][:150]], years=[a['year'], b['year']],
                                     reason='a second corpus record of the thesis (DNB print/online not merged, or a part); not keyed'))
    for t in todo:
        if t['id'] in aha_of or t['id'] in same_thesis:
            continue
        w, y = title_words(t['title']), year_int(t['year'])
        found = set()
        for wk, label, wy, pk in graph_theses.get(famkey(t['author'] or ''), ()):
            w2 = title_words(label)
            sh = len(w & w2)
            if w and w2 and sh >= 2 and sh >= 0.8 * min(len(w), len(w2)) and (y is None or wy is None or abs(y - wy) <= 2):
                found.add((state.lookup(wk)[0] if len(state.lookup(wk)) == 1 else wk,
                           state.lookup(pk)[0] if len(state.lookup(pk)) == 1 else pk))
        if not found:
            continue
        works_ = {x for x, _ in found}
        keys_ = {x for _, x in found}
        k1 = next(iter(keys_))
        clash = len(keys_) == 1 and k1 in state.keys and pid_clash(k1, t['doc'].get('author_gnd') or '')
        if len(works_) == 1 and len(keys_) == 1 and live(k1) and not clash and k1 not in blocked and \
                age_ok(k1, year_int(t['year'])) and names_compatible(state.keys[k1]['label'], t['author'] or ''):
            same_thesis[t['id']] = (next(iter(works_)), k1)
        else:
            held.append(dict(kind='same_thesis_in_graph_unclear', thesis=t['id'], author=t['author'],
                             found=sorted(found), gnd=t['doc'].get('author_gnd'),
                             reason=('the DNB record\'s author GND id differs from the GND id on the key the graph credits '
                                     'with this thesis (a namesake credit?)' if clash else
                                     'several works or authors, names disagree, life years, or the merge guard')))
            same_thesis[t['id']] = None
    R['same_thesis_in_graph'] = sum(1 for v in same_thesis.values() if v)
    R['same_thesis_in_graph_held'] = sum(1 for v in same_thesis.values() if v is None)

    work_clusters, author_clusters, seeds, twins = [], [], [], []
    same_ops = []
    for t in sorted(todo, key=lambda x: x['id']):
        tid, d = t['id'], t['doc']
        if tid in same_thesis:
            if same_thesis[tid]:
                wk, pk = same_thesis[tid]
                same_ops.append(dict(event='attach', key=wk, anchors=[f'diss-thesis:{tid}'], aliases=[],
                                     members=[f'year:{t["year"]}'] if t['year'] and f'year:{t["year"]}' not in state.members.get(wk, ()) else [],
                                     basis=f'the same doctorate as this graph thesis: {t["institution"]} {t["year"]}, same family name, '
                                           f'title words shared (key_thesis_round same-thesis rule)'))
                anchors = [f'diss-author:{tid}'] + ([f'gnd:{d["author_gnd"]}'] if d.get('author_gnd') and f'gnd:{d["author_gnd"]}' not in state.anchor
                                                    and not any(a.startswith('gnd:') for a in state.keys[pk]['anchors']) else [])
                same_ops.append(dict(event='attach', key=pk, anchors=anchors, aliases=[], members=[],
                                     basis=f'author of the same doctorate, already keyed as the author of {wk}'))
                twins.append((tid, pk, wk, 'same thesis already in the graph'))
                author_clusters.append(dict(type='person', label=state.keys[pk]['label'], anchors=set(anchors), members=set(),
                                            aliases=set(), _t=t, _route='same thesis already in the graph', _same=True))
            continue
        dnb = d.get('ingest_source') == 'dnb_germany'
        title = (t['title'] or '').strip()
        year = year_int(t['year'])
        members = {f'year:{t["year"]}'} if t['year'] else set()
        inst = institution_key(t['institution'], t['country'])
        if inst:
            members.add(f'awarded-by:{inst}')
            R['works_with_institution_key'] += 1
        else:
            R['works_without_institution_key'] += 1
        work = {f'diss-thesis:{tid}'}
        author = {f'diss-author:{tid}'}
        basis_w = f'dissertation graph thesis ({t["institution"]}, {t["year"]})'
        route = None
        if tid in aha_of:
            rid, basis = aha_of[tid]
            akey = one(f'aha-phd:{rid}')
            alabel = state.keys[akey]['label'] if akey else (aha_rec.get(rid) or {}).get('dissertator', '')
            if same_listed_name(t['author'] or '', alabel) or names_compatible(t['author'] or '', alabel):
                work.add(f'aha-diss:{rid}')
                author.add(f'aha-phd:{rid}')
                basis_w += f'; AHA record {rid} by {basis}'
                route = 'aha'
                if akey:
                    other = [a for a in state.keys[akey]['anchors'] if a.startswith('diss-author:')]
                    if other:
                        held.append(dict(kind='aha_person_already_holds_another_harvested_thesis', thesis=tid, key=akey,
                                         label=alabel, other=other))
                        author.discard(f'aha-phd:{rid}')
                        route = None
                R[f'aha_match:{basis}'] += 1
            else:
                held.append(dict(kind='aha_record_names_differ', thesis=tid, record=rid, author=t['author'], aha=alabel,
                                 reason='thesis not keyed: the AHA record of this doctorate prints another name (a name change or '
                                        'a wrong match); a key labelled with the thesis name could show an earlier name'))
                R['aha_names_differ_held'] += 1
                continue
        work_clusters.append(dict(type='work', label=title or f'Dissertation {tid}', anchors=work, members=members,
                                  aliases=set(), resolution='established', basis=basis_w, _t=t))
        if not dnb:
            if route is None:
                books = own_book(dict(dissertator=t['author'], title=title, year=t['year']), canon)
                if len(books) == 1:
                    k = next(iter(books))
                    author |= {a for a in state.keys[k]['anchors'] if a.startswith('diss-person:')}
                    route = 'canon own book'
                elif books:
                    held.append(dict(kind='own_book_on_several_canon_keys', thesis=tid, author=t['author'], keys=sorted(books)))
            author_clusters.append(dict(type='person', label=t['author'] or f'Author of dissertation {tid}', anchors=author,
                                        members=set(), aliases=set(), resolution='established',
                                        basis=f'author of dissertation graph thesis {tid}', _t=t, _route=route))
            continue
        # ---- DNB seed rule
        name, g = t['author'] or '', d.get('author_gnd') or ''
        cands = defaultdict(set)
        if g:
            ks, why = gnd_keys(g, name)
            for k in ks:
                cands[k].add(why)
        isbns = set()
        for e in editions.get(d.get('dnb_id', ''), [d.get('dnb_id', '')]):
            isbns |= {re.sub(r'[^0-9X]', '', x) for x in (raw.get(e) or {}).get('isbn', [])}
        doi = (d.get('doi') or '').lower()
        tt = stems(title)
        for k in same_name_keys(name):
            if not live(k) or not full_agree(name, state.keys[k]['label']):
                continue
            for wk, wt, wy, kind, wisbn, wanch in works_of.get(k, ()):
                if kind == 'thesis' or fold(wt).startswith('review'):
                    continue
                if doi and f'doi:{doi}' in wanch:
                    cands[k].add(f'the record\'s DOI is on {wk}'); twins.append((tid, k, wk, 'doi')); break
                if isbns and wisbn and isbns & {re.sub(r'[^0-9X]', '', x) for x in wisbn.split(';')}:
                    cands[k].add(f'the record\'s ISBN is on {wk}'); twins.append((tid, k, wk, 'isbn')); break
                bb = stems(wt)
                sh = tt & bb
                if year and wy and tt and bb and -1 <= wy - year <= 15 and len(sh) >= 2 and \
                        len(sh) / min(len(tt), len(bb)) >= 0.4 and (len(sh) >= 3 or max(df[s] for s in sh) <= 25):
                    cands[k].add(f'thesis as published: {kind} {wk} "{wt[:120]}" ({wy})')
                    twins.append((tid, k, wk, 'title'))
                    break
        good = {k: v for k, v in cands.items() if live(k)}
        reasons = []
        if len(good) > 1:
            reasons.append('several candidate keys')
        for k in good:
            pk_, pn_ = parse(state.keys[k]['label']), parse(name)
            translit = ('gnd anchor on the key' in good[k] and pk_ and pn_ and pk_[0][:6] == pn_[0][:6]
                        and pk_[1][0][:1] == pn_[1][0][:1])     # the same GND id; a transliteration (Rusakovskij / Rusakovskiy)
            if not names_compatible(state.keys[k]['label'], name) and not translit:
                reasons.append(f'name on {k} disagrees')
            if pid_clash(k, g):
                reasons.append(f'{k} holds another GND id')
            if not age_ok(k, year):
                reasons.append(f'{k} life years put the degree before age 20')
            if k in blocked:
                reasons.append(f'{k} is behind the merge guard')
        same_name = [k for k in same_name_keys(name) if live(k) and full_agree(name, state.keys[k]['label'])]
        if good and not reasons:
            k = next(iter(good))
            anchors = {f'diss-author:{tid}'} | ({f'gnd:{g}'} if g and one(f'gnd:{g}') in (None, k) else set())
            anchors.add(sorted(state.keys[k]['anchors'])[0])
            author_clusters.append(dict(type='person', label=state.keys[k]['label'], anchors=anchors, members=set(),
                                        aliases=set(), resolution='established', _t=t,
                                        _route='; '.join(sorted(good[k])),
                                        basis=f'author of DNB dissertation {d.get("dnb_id")} ({tid}): ' + '; '.join(sorted(good[k]))))
        elif good:
            held.append(dict(kind='dnb_author_candidate_failed_checks', thesis=tid, author=name, gnd=g,
                             candidates={k: sorted(v) for k, v in good.items()}, reasons=reasons))
            seeds.append(dict(t=t, gnd=g, reason='held: ' + '; '.join(reasons), same_name=len(same_name)))
        else:
            seeds.append(dict(t=t, gnd=g, reason='no GND id on a key and no keyed work of a same-name person is this thesis',
                              same_name=len(same_name)))

    # pooled canon ids and anchors new to the log claimed twice (key_aha.drop_shared)
    claims = defaultdict(list)
    for i, c in enumerate(author_clusters):
        for a in c['anchors']:
            if a.startswith('diss-person:'):
                claims[a].append(i)
    for a, idx in claims.items():
        if len(idx) > 1:
            held.append(dict(kind='canon_key_claimed_by_several_theses', anchor=a, labels=[author_clusters[i]['label'] for i in idx]))
            for i in idx:
                author_clusters[i]['anchors'].discard(a)
                author_clusters[i]['_route'] = None
    keyhits = defaultdict(list)          # two new theses' authors reaching one existing key: plan() holds them
    for i, c in enumerate(author_clusters):
        for a in c['anchors']:
            if a in state.anchor:
                keyhits[state.anchor[a]].append(i)

    def split(clusters):
        return [{k: v for k, v in c.items() if not k.startswith('_')} for c in clusters]

    report_parts, files = [], {}

    def write(name, basis, ops, decided_by='build'):
        prop = dict(basis=basis, decided_by=decided_by, ops=ops)
        (out / f'{name}.json').write_text(json.dumps(prop, ensure_ascii=False) + '\n')
        files[name] = len(ops)
        return prop

    # part 1b: the same doctorate already in the graph (attach anchors to the existing work and author; staged after 01)
    author_clusters_same = [c for c in author_clusters if c.get('_same')]
    author_clusters = [c for c in author_clusters if not c.get('_same')]
    # part 1: thesis works, per group
    for group in ('ingest', 'mexico', 'us-backlog'):
        cl = [c for c in work_clusters if c['_t']['group'] == group]

        def wmerge_ok(cluster, keys):
            kinds = sorted(tuple(sorted({a.split(':', 1)[0] for a in state.keys[k]['anchors']})) for k in keys)
            return kinds == [('aha-diss',), ('diss-thesis',)]
        ops, assign, q = I.plan(state, split(cl), guarded(state, wmerge_ok, blocked=blocked))
        held += [dict(q_, part=f'01-works-{group}') for q_ in q]
        R[f'works:{group}:attach_to_aha_work'] = sum(1 for o in ops if o['event'] == 'attach')
        R[f'works:{group}:mint'] = sum(1 for o in ops if o['event'] == 'mint')
        prop = write(f'01-works-{group}', f'dissertation graph theses as works ({group}; key_thesis_round)', ops)
        report_parts.append(st.run(f'01-works-{group}', prop))

    prop = write('01b-same-thesis-in-graph', 'the same doctorate already keyed as a graph thesis (another repository record or '
                 'an ORCID thesis): thesis and author anchors attached to the existing work and person keys', same_ops)
    report_parts.append(st.run('01b-same-thesis-in-graph', prop))
    for c in author_clusters_same:
        R[f'authors:{c["_t"]["group"]}:{c["_t"]["country"]}:attach:same thesis already in the graph'] += 1

    # parts 2 (attaches to existing people) and 3 (mints), per group
    for group in ('ingest', 'mexico', 'us-backlog'):
        cl = [c for c in author_clusters if c['_t']['group'] == group]
        att = [c for c in cl if any(a in state.anchor for a in c['anchors'])]
        new = [c for c in cl if not any(a in state.anchor for a in c['anchors'])]
        ops, assign, q = I.plan(state, split(att), guarded(state, author_merge_ok(state), blocked=blocked))
        held += [dict(q_, part=f'02-author-attaches-{group}') for q_ in q]
        for c in att:
            R[f'authors:{group}:{c["_t"]["country"]}:attach:{(c["_route"] or "?").split(":")[0][:60]}'] += 1
        prop = write(f'02-author-attaches-{group}', f'thesis authors joined to existing person keys ({group})', ops)
        report_parts.append(st.run(f'02-author-attaches-{group}', prop))
        for c in new:
            R[f'authors:{group}:{c["_t"]["country"]}:mint'] += 1
        ops, assign, q = I.plan(state, split(new))
        held += [dict(q_, part=f'03-author-mints-{group}') for q_ in q]
        prop = write(f'03-author-mints-{group}', f'thesis authors minted, one per thesis as in earlier rounds ({group})', ops)
        report_parts.append(st.run(f'03-author-mints-{group}', prop))
    for s in seeds:
        R[f'authors:{s["t"]["group"]}:{s["t"]["country"]}:seed'] += 1

    # part 4: authored claims (diss-auth), this round and the backlog of earlier rounds
    def authored_ops(tids):
        ops = []
        for tid in tids:
            w = state.lookup(f'diss-thesis:{tid}')
            a = state.lookup(f'diss-author:{tid}')
            if len(w) != 1 or len(a) != 1 or f'diss-auth:{tid}' in state.anchor:
                R['authored:skipped_unresolved_or_present'] += 1
                continue
            existing = None
            for x in state.keys[w[0]]['anchors']:
                if x.startswith('aha-diss:'):
                    c = one(f'aha-auth:{x[9:]}')
                    if c and state.lookup(f'aha-phd:{x[9:]}') == a:
                        existing = c
            if existing:
                ops.append(dict(event='attach', key=existing, anchors=[f'diss-auth:{tid}'], aliases=[], members=[],
                                basis='a second source makes the same assertion'))
                if state.keys[existing]['resolution'] != 'established':
                    ops.append(dict(event='status', key=existing, resolution='established', basis='two sources agree'))
                R['authored:second_source_on_aha_claim'] += 1
            else:
                ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded',
                                anchors=[f'diss-auth:{tid}'], relation=dict(subject=f'diss-author:{tid}', predicate='authored',
                                                                         object=f'diss-thesis:{tid}')))
                R['authored:minted'] += 1
        return ops
    round_tids = [t['id'] for t in todo]
    prop = write('04-authored-claims', 'authored claims for keyed theses (key_relations form, diss-auth:<id>)', authored_ops(round_tids))
    report_parts.append(st.run('04-authored-claims', prop))
    backlog = []
    for a, k in sql.execute("SELECT anchor, key FROM anchor WHERE anchor >= 'diss-thesis:' AND anchor < 'diss-thesis;'"):
        tid = a[len('diss-thesis:'):]
        if f'diss-auth:{tid}' not in state.anchor and tid not in set(round_tids):
            backlog.append(tid)
    R['authored_backlog_theses'] = len(backlog)
    before = R['authored:minted']
    prop = write('04b-authored-claims-backlog', 'authored claims for theses keyed in earlier rounds without one (Brazil 2026-11-03, '
                 'UChicago 2026-11-03b: key_relations was not rerun)', authored_ops(sorted(backlog)))
    R['authored_backlog_minted'] = R['authored:minted'] - before
    report_parts.append(st.run('04b-authored-claims-backlog', prop))

    # part 5: supervisors. (a) repository advisors (key_repository_supervisors' rule) for this round's non-DNB theses
    supervisors = defaultdict(set)
    sup_rows = []
    idref = {}
    if FRANCE.exists():
        for c in json.loads(FRANCE.read_text()):
            for a in c.get('directeurs_these') or []:
                if a.get('idref'):
                    idref[c['nnt'], rnorm(f"{a.get('prenom', '')} {a.get('nom', '')}")] = a['idref']
    for t in todo:
        d = t['doc']
        if d.get('ingest_source') == 'dnb_germany':
            continue
        names = list(dict.fromkeys(n for a in d.get('advisors') or [] for n in advisor_names(a)))
        if not names:
            continue
        if len(names) > 2:
            R['supervisors:committee_lists_skipped'] += 1
            continue
        work = state.lookup(f'diss-thesis:{t["id"]}')
        if len(work) != 1:
            continue
        for name in names:
            anchor = f'idref:{idref[d["nnt"], rnorm(name)]}' if d.get('nnt') and (d['nnt'], rnorm(name)) in idref else \
                f'capes-person:{d["capes_advisor_id"]}' if d.get('capes_advisor_id') and len(names) == 1 else \
                f'repo-advisor:{d["institution"]}|{rnorm(name)}'
            sup_rows.append((anchor, name, t['id'], work[0], t['group']))
    # existing supervisors of these works (AHA advisors: aha-sup claims whose object is the work's aha-diss anchor)
    wanted_works = {w for *_, w, _ in sup_rows}
    for c, s, o in sql.execute("SELECT claim, subject, object FROM relation WHERE predicate = 'supervised' AND "
                               "(object LIKE 'aha-diss:%' OR object LIKE 'diss-thesis:%')"):
        ow = state.lookup(o)
        if len(ow) == 1 and ow[0] in wanted_works and live(c):
            for sk in state.lookup(s):
                supervisors[ow[0]].add(sk)
    joins, label = defaultdict(set), {}
    for anchor, name, tid, work, group in sup_rows:
        label.setdefault(anchor, name)
        if anchor in state.anchor:
            joins[anchor].add(state.anchor[anchor])
            continue
        same = [k for k in supervisors.get(work, ()) if names_compatible(state.keys[k]['label'], name)]
        if len(same) == 1:
            joins[anchor].add(same[0])
        elif len(same) > 1:
            joins[anchor].add('several')
    sup_ops, sup_clusters, owner, by_key = [], [], {}, defaultdict(set)
    for anchor in sorted(label):
        ks = joins.get(anchor, set())
        if len(ks) > 1 or 'several' in ks:
            held.append(dict(kind='repository_advisor_reaches_several_keys', anchor=anchor, name=label[anchor],
                             keys=sorted(k for k in ks if k != 'several')))
            continue
        if ks:
            k = next(iter(ks))
            owner[anchor] = k
            if anchor not in state.anchor:
                by_key[k].add(anchor)
                R['supervisors:advisor_joined_same_thesis'] += 1
            else:
                R['supervisors:advisor_already_keyed'] += 1
        else:
            owner[anchor] = None
            sup_clusters.append(dict(type='person', label=label[anchor], anchors={anchor}, members=set(), aliases=set(),
                                     resolution='recorded', basis='supervisor named in the thesis repository record'))
            R['supervisors:advisor_minted'] += 1
    for k, anchors in sorted(by_key.items()):
        sup_clusters.append(dict(type='person', label=state.keys[k]['label'], anchors=anchors | {sorted(state.keys[k]['anchors'])[0]},
                                 members=set(), aliases=set(), resolution='established',
                                 basis=f'supervisor in thesis repository records of theses the log already gives to '
                                       f'{state.keys[k]["label"]} (same thesis, names agree)'))
    ops, assign, q = I.plan(state, sup_clusters)
    held += [dict(q_, part='05-supervisors-repository') for q_ in q]
    claims_seen = set()
    for anchor, name, tid, work, group in sup_rows:
        k = owner.get(anchor, 'skip')
        if k == 'skip':
            continue
        c = f'repo-sup:{tid}:{anchor}'
        if c in state.anchor or c in claims_seen or (k and k in supervisors.get(work, ())):
            R['supervisors:supervised_already'] += 1
            continue
        claims_seen.add(c)
        R[f'supervisors:supervised_claims:{group}'] += 1
        ops.append(dict(event='mint', key=f'new:claim-{len(claims_seen)}', type='claim', label='', resolution='recorded',
                        anchors=[c], relation=dict(subject=anchor, predicate='supervised', object=f'diss-thesis:{tid}'),
                        basis='supervisor named in the thesis repository record (doctorates.json advisors)'))
    prop = write('05-supervisors-repository', 'supervisors named by thesis repositories (US, Canada, Mexico; key_repository_supervisors rule)', ops)
    report_parts.append(st.run('05-supervisors-repository', prop))

    # (b) DNB supervisors (dgs / 'Betreuer') and referees ('Gutachter'): linked only to keys their GND id reaches
    dnb_ops, referee_rows, dnb_people = [], [], []
    for t in todo:
        d = t['doc']
        if d.get('ingest_source') != 'dnb_germany':
            continue
        work = state.lookup(f'diss-thesis:{t["id"]}')
        if len(work) != 1:                       # a held thesis (not keyed in this round)
            continue
        seen = set()
        for e in editions.get(d.get('dnb_id', ''), [d.get('dnb_id', '')]):
            r = raw.get(e) or {}
            for role, people_ in (('supervisor', r.get('supervisors', [])),
                                  ('referee', [p for p in r.get('contributors', []) if 'Gutachter' in (p.get('role_text') or '')])):
                for p in people_:
                    nm, g = p.get('name') or '', p.get('gnd') or ''
                    if (role, g or nm) in seen:
                        continue
                    seen.add((role, g or nm))
                    ks, why = gnd_keys(g, nm) if g else (set(), '')
                    ks = {k for k in ks if live(k)}
                    ok = len(ks) == 1 and names_compatible(state.keys[next(iter(ks))]['label'], nm) and \
                        age_ok(next(iter(ks)), year_int(t['year']) and year_int(t['year']) - 10)
                    k = next(iter(ks)) if ok else ''
                    dnb_people.append(dict(thesis=t['id'], dnb_id=e, role=role, name=nm, gnd=g, key=k,
                                           status='linked' if k else ('no GND id' if not g else
                                                                      'GND id reaches no key' if not ks else 'GND reaches a key that fails a check'),
                                           route=why if k else ''))
                    R[f'dnb_people:{role}:{"linked" if k else "unlinked"}'] += 1
                    if not k:
                        continue
                    subj = f'gnd:{g}' if one(f'gnd:{g}') == k else sorted(state.keys[k]['anchors'])[0]
                    if role == 'supervisor':
                        c = f'dnb-sup:{t["id"]}:{g}'
                        if c in state.anchor or len(work) != 1:
                            continue
                        dnb_ops.append(dict(event='mint', key=f'new:{len(dnb_ops)}', type='claim', label='', resolution='recorded',
                                            anchors=[c], relation=dict(subject=subj, predicate='supervised', object=f'diss-thesis:{t["id"]}'),
                                            basis=f'supervisor (Betreuer, MARC 700 $4 dgs) in DNB record {e}; GND {g} ({why})'))
                    else:
                        referee_rows.append(dict(person=subj, person_key=k, thesis=f'diss-thesis:{t["id"]}', dnb_id=e, gnd=g,
                                                 name=nm, role_text='Gutachter', source='dnb-marc-700'))
    prop = write('05b-supervisors-dnb', 'DNB thesis supervisors (Betreuer) linked to keys holding their GND id', dnb_ops)
    report_parts.append(st.run('05b-supervisors-dnb', prop))

    # part 6: published_as for attached authors whose LC book is the thesis (key_published_as.matches)
    pub_ops = []
    for c in author_clusters + author_clusters_same:
        if not c.get('_route'):
            continue
        t = c['_t']
        a = state.lookup(f'diss-author:{t["id"]}')
        if len(a) != 1:
            continue
        hits = []
        for wk, wt, wy, kind, _, wanch in works_of.get(a[0], ()):
            if any(x.startswith('lccn:') for x in wanch) and kind != 'thesis' and \
                    published_matches(t['title'], year_int(t['year']), wt, wy):
                hits.append((wk, sorted(x for x in wanch if x.startswith('lccn:'))[0]))
        if len(hits) == 1:
            anchor = f'pub-as:diss-thesis:{t["id"]}:{hits[0][1][5:]}'
            if anchor not in state.anchor and len(state.lookup(hits[0][1])) == 1:
                pub_ops.append(dict(event='mint', key=f'new:{len(pub_ops)}', type='claim', label='', resolution='recorded',
                                    anchors=[anchor], relation=dict(subject=f'diss-thesis:{t["id"]}', predicate='published_as',
                                                                    object=hits[0][1])))
                twins.append((t['id'], a[0], hits[0][0], 'published_as'))
        elif len(hits) > 1:
            held.append(dict(kind='thesis_matches_several_books', thesis=t['id'], key=a[0], books=[h[0] for h in hits]))
    prop = write('06-published-as', 'dissertations published as books: attached authors whose LC book is the thesis (key_published_as rule)', pub_ops)
    report_parts.append(st.run('06-published-as', prop))

    # part 7 (optional, a separate decision): DNB seeds whose name is borne by ONE key in the graph, that key's own
    # (key-log) articles, books, chapters or reviews dated from 3 years before to 25 after the degree, and at least one
    # of them sharing a rare title stem with the thesis (topic as support only). The user's attach rule names "name +
    # an article/book/review by the same person consistent in time"; the seed rule asks for a link to a graph work.
    # Written apart so it can be refused without touching parts 1-6.
    fam_count = Counter(nk[0] for nk in by_name)
    opt_ops, opt_rows = [], []
    for s_ in seeds:
        t = s_['t']
        if not s_['reason'].startswith('no GND'):
            continue
        name, g, year = t['author'] or '', s_['gnd'], year_int(t['year'])
        cands = [k for k in same_name_keys(name) if live(k) and full_agree(name, state.keys[k]['label'])]
        all_bearers = set(same_name_keys(name))
        if len(cands) != 1 or len(all_bearers) != 1 or not year:
            continue
        k = cands[0]
        fam_n = max((fam_count[nk[0]] for nk in name_index(name)), default=0)
        dated = [(wk, wt, wy, kind) for wk, wt, wy, kind, _, _ in works_of.get(k, ())
                 if kind in ('article', 'book', 'chapter', 'review', 'other') and wy and year - 3 <= wy <= year + 25]
        undated_or_out = [w for w in works_of.get(k, ()) if not (w[2] and year - 3 <= w[2] <= year + 25)]
        tt = stems(t['title'])
        topical = [(wk, wt, wy) for wk, wt, wy, kind in dated if any(df[x] <= 25 for x in tt & stems(wt))]
        theses_on_key = [w for w in works_of.get(k, ()) if w[3] == 'thesis']
        why = []
        if not dated:
            why.append('no work in the window')
        if not topical:
            why.append('no rare title stem shared')
        if theses_on_key:
            why.append('key already authors a thesis')
        if pid_clash(k, g):
            why.append('another GND id on the key')
        if not age_ok(k, year):
            why.append('life years')
        if k in blocked:
            why.append('merge guard')
        if fam_n > 30:
            why.append(f'common family name ({fam_n} keys)')
        opt_rows.append(dict(thesis_id=t['id'], printed_author=name, year=t['year'], key=k, key_label=state.keys[k]['label'],
                             works_in_window=len(dated), works_outside=len(undated_or_out), topical=len(topical),
                             example=(topical or dated or [('', '', '', '')])[0][1][:120], family_keys=fam_n,
                             decision='propose' if not why else 'no: ' + '; '.join(why)))
        if why:
            continue
        anchors = [f'diss-author:{t["id"]}'] + ([f'gnd:{g}'] if g and g and f'gnd:{g}' not in state.anchor else [])
        opt_ops.append(dict(event='attach', key=k, anchors=anchors, aliases=[], members=[],
                            basis=f'author of DNB dissertation {t["doc"].get("dnb_id")}: the only key with this full name; its '
                                  f'works from {min(w[2] for w in dated)} to {max(w[2] for w in dated)} fall in the career window '
                                  f'and share a rare title word with the thesis'))
        opt_ops.append(dict(event='mint', key=f'new:opt-{len(opt_ops)}', type='claim', label='', resolution='recorded',
                            anchors=[f'diss-auth:{t["id"]}'], relation=dict(subject=f'diss-author:{t["id"]}', predicate='authored',
                                                                         object=f'diss-thesis:{t["id"]}')))
    prop = write('07-dnb-name-and-works-OPTIONAL', 'OPTIONAL: DNB thesis authors joined to the one key bearing their full name, '
                 'whose own works fall in the career window and share a rare title word (user attach rule: name + works in time)', opt_ops)
    report_parts.append(st.run('07-dnb-name-and-works-OPTIONAL', prop))
    R['optional_dnb_name_and_works_attaches'] = sum(1 for o in opt_ops if o['event'] == 'attach')
    with gzip.open(out / 'dnb-name-and-works-candidates.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(opt_rows[0]) if opt_rows else ['thesis_id'])
        w.writeheader()
        w.writerows(opt_rows)
    R['optional_dnb_single_bearer_candidates'] = len(opt_rows)

    # ---------------------------------------------------------------- side tables
    with gzip.open(out / 'seeds.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['thesis_id', 'dnb_id', 'country', 'year', 'institution', 'printed_author', 'author_gnd', 'same_name_keys', 'reason'])
        for s in seeds:
            t = s['t']
            w.writerow([t['id'], t['doc'].get('dnb_id'), t['country'], t['year'], t['institution'], t['author'], s['gnd'],
                        s['same_name'], s['reason']])
    with gzip.open(out / 'refereed.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['person', 'person_key', 'thesis', 'dnb_id', 'gnd', 'name', 'role_text', 'source'])
        w.writeheader()
        w.writerows(referee_rows)
    with gzip.open(out / 'dnb-people.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['thesis', 'dnb_id', 'role', 'name', 'gnd', 'key', 'status', 'route'])
        w.writeheader()
        w.writerows(dnb_people)
    with gzip.open(out / 'twins.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['thesis_id', 'person_key', 'work_key', 'route'])
        w.writerows(sorted(set(twins)))
    with gzip.open(out / 'author-decisions.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['thesis_id', 'group', 'country', 'year', 'institution', 'printed_author', 'outcome', 'key', 'route', 'ocap_review'])
        for c in author_clusters + author_clusters_same:
            t = c['_t']
            ks = state.lookup(f'diss-author:{t["id"]}')
            w.writerow([t['id'], t['group'], t['country'], t['year'], t['institution'], t['author'],
                        'attach' if c.get('_route') else 'mint', ks[0] if len(ks) == 1 else '', c.get('_route') or '',
                        bool(t['doc'].get('ocap_review'))])
        for s in seeds:
            t = s['t']
            w.writerow([t['id'], t['group'], t['country'], t['year'], t['institution'], t['author'], 'seed', '', s['reason'], False])
    (out / 'held.json').write_text(json.dumps(held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    ocap = [dict(id=t['id'], institution=t['institution'], year=t['year'], title=t['title'])
            for t in todo if t['doc'].get('ocap_review')]
    R['held_items'] = len(held)
    R['held_by_kind'] = 0
    summary = dict(key_log_seq=st.seq0, counts=dict(sorted((k, v) for k, v in R.items() if k != 'held_by_kind')),
                   held_by_kind=dict(Counter(h['kind'] for h in held)), dry_run=report_parts, files=files, ocap_review=ocap,
                   seeds=len(seeds), referee_rows=len(referee_rows), twins=len(set(twins)))
    (out / 'report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:6000])


if __name__ == '__main__':
    main()
