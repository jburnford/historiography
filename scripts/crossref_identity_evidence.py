#!/usr/bin/env python3
"""Job B (2026-11-17): identity evidence on existing person keys from the Crossref public data file (March 2026).

Runs on spark (6 threads, DuckDB 24 GB). Inputs from scripts/crossref_identity_inputs.py in ../in; work folder
/mnt/data/jic823/crossref-work-b/b.

  extract  Crossref contributor rows and work facts of every DOI work with a credited person key; then every
           Crossref row whose ORCID is a key's anchor or appears on those works (the ORCID's whole Crossref record)
  match    each (person key, DOI) credit -> the contributor row(s) whose printed name fits the key's label (family
           agrees and given names agree in full or by initial; nicknames and short forms are NOT accepted). An ORCID
           belongs to the row it sits on: never assigned by position.
  tables   orcid-evidence, classes (a) attach / (b) disagree / (c) one ORCID on two keys, affiliation evidence and
           dated spans, the outside-venue sweep

  python3 -I crossref_identity_evidence.py extract|match|tables|all
"""
import os
import re
import sys
import time
from collections import Counter, defaultdict

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crossref_names import fam_agree, forms, gwords, fam_norm, name_level, nfold  # noqa: E402

CR = '/mnt/data/jic823/crossref-2026-parquet'
IN = '/mnt/data/jic823/crossref-work-b/in'
W = '/mnt/data/jic823/crossref-work-b/b'


def con():
    db = duckdb.connect(f'{W}/work.duckdb')
    db.execute(f"set threads=6; set memory_limit='24GB'; set temp_directory='{W}/tmp'; set preserve_insertion_order=false")
    return db


def extract():
    db = con()
    t0 = time.time()
    db.execute(f"create or replace table bdoi as select distinct doi from '{IN}/b_authored.parquet'")
    db.execute(f"""create or replace table cra as select a.* from read_parquet('{CR}/authors/*.parquet') a
                   where a.doi in (select doi from bdoi)""")
    print('contributor rows on keyed works', db.execute('select count(*), count(distinct doi), count(orcid) from cra').fetchone(),
          f'{time.time()-t0:.0f}s', flush=True)
    db.execute(f"""create or replace table orcset as
        select distinct orcid from (select unnest(orcids) orcid from '{IN}/b_persons.parquet' union all
                                    select orcid from cra where orcid is not null)""")
    db.execute(f"""create or replace table cro as select a.* from read_parquet('{CR}/authors/*.parquet') a
                   where a.orcid in (select orcid from orcset)""")
    print('rows with those ORCIDs', db.execute('select count(*), count(distinct orcid), count(distinct doi) from cro').fetchone(),
          f'{time.time()-t0:.0f}s', flush=True)
    db.execute(f"""create or replace table crw as select doi, type, title, container, issn, isbn, publisher, year, n_authors
        from read_parquet('{CR}/works/*.parquet') where doi in (select doi from bdoi union select doi from cro)""")
    print('works', db.execute('select count(*) from crw').fetchone(), f'{time.time()-t0:.0f}s', flush=True)


def label_forms(label):
    return forms(label)


def row_level(lforms, given, family, name):
    """Best agreement of a key's label forms with one contributor row: 'full' / 'initial' / 'variant' / None."""
    if family:
        rf, rg = fam_norm(family), gwords(f'{family}, {given or ""}')
    elif name:
        fs = forms(name)
        if not fs:
            return None
        rf, _, rg = fs[0]
    else:
        return None
    best = None
    order = {'full': 3, 'initial': 2, 'variant': 1}
    for f, _, g in lforms:
        if not fam_agree(f, rf):
            continue
        lev = name_level(tuple(g), tuple(rg)) if rg else None
        if lev and (best is None or order[lev] > order[best]):
            best = lev
    return best


def match():
    import pyarrow as pa
    import pyarrow.parquet as pq
    db = con()
    t0 = time.time()
    labels = dict(db.execute(f"select key, label from '{IN}/b_persons.parquet'").fetchall())
    rows = defaultdict(list)
    cur = db.execute('select doi, role, seq, given, family, name, orcid, orcid_authenticated, affiliation, ror from cra')
    while True:
        b = cur.fetchmany(500000)
        if not b:
            break
        for r in b:
            rows[r[0]].append(r)
    print('rows loaded', len(rows), f'{time.time()-t0:.0f}s', flush=True)
    fcache = {}
    out = defaultdict(list)
    stats = Counter()
    cur = db.execute(f"select distinct person, doi, rel, year, \"work\" from '{IN}/b_authored.parquet'")
    for person, doi, rel, wyear, work in cur.fetchall():
        rs = rows.get(doi)
        if not rs:
            stats['no-crossref-record'] += 1
            continue
        lf = fcache.get(person)
        if lf is None:
            lf = fcache[person] = label_forms(labels.get(person) or '')
        want = ('author',) if rel == 'authored' else ('editor', 'author')
        hits = []
        for r in rs:
            if r[1] not in want and r[1] not in ('author', 'editor'):
                continue
            lev = row_level(lf, r[3], r[4], r[5])
            if lev:
                hits.append((lev, r))
        if not hits:
            stats['no-row-fits-name'] += 1
            continue
        # one person per row: several fitting rows with different ORCIDs or different printed names = ambiguous
        distinct = {(nfold(r[3] or ''), nfold(r[4] or ''), r[6]) for _, r in hits}
        if len(hits) > 1 and len({h[1][6] for h in hits if h[1][6]}) > 1:
            stats['ambiguous-rows'] += 1
            continue
        if len(distinct) > 1 and len({nfold(r[3] or '') for _, r in hits}) > 1:
            stats['ambiguous-rows'] += 1
            continue
        lev, r = max(hits, key=lambda h: ({'full': 3, 'initial': 2, 'variant': 1}[h[0]], h[1][6] is not None))
        stats['matched|' + lev] += 1
        for c, v in (('person', person), ('doi', doi), ('work', work), ('rel', rel), ('role', r[1]), ('seq', r[2]),
                     ('given', r[3]), ('family', r[4]), ('name', r[5]), ('orcid', r[6]), ('authenticated', r[7]),
                     ('affiliation', r[8]), ('ror', r[9]), ('level', lev), ('graph_year', wyear)):
            out[c].append(v)
    pq.write_table(pa.table(out), f'{W}/matched.parquet', compression='zstd')
    print('match', dict(stats), f'{time.time()-t0:.0f}s', flush=True)
    import json
    json.dump(dict(stats), open(f'{W}/match-stats.json', 'w'), indent=1)


def tables():
    db = con()
    t0 = time.time()
    db.execute(f"create or replace view m as select m.*, w.year cr_year, w.type cr_type, w.title cr_title, w.container cr_container from '{W}/matched.parquet' m left join crw w using (doi)")
    db.execute(f"create or replace view pr as select * from '{IN}/b_persons.parquet'")
    db.execute("""create or replace table anchored as select o orcid, key from pr, unnest(orcids) u(o)""")
    # ---- 1. orcid evidence per (key, ORCID)
    db.execute("""create or replace table ev as
        select m.person, m.orcid, count(distinct m.doi) n_works, min(coalesce(m.cr_year, m.graph_year)) y_min,
               max(coalesce(m.cr_year, m.graph_year)) y_max, bool_or(coalesce(m.authenticated, false)) authenticated,
               string_agg(distinct trim(coalesce(m.given,'') || ' ' || coalesce(m.family, m.name, '')), ' | ') names_on_record,
               count(distinct m.doi) filter (where m.level='full') n_full, count(distinct m.doi) filter (where m.level='initial') n_initial,
               count(distinct m.doi) filter (where m.level='variant') n_variant,
               list(distinct m.doi)[1:5] dois
        from m where m.orcid is not null group by all""")
    # whole-record name check: share of every Crossref row with this ORCID whose family agrees with the key's family
    db.execute("create or replace table orc_names as select orcid, family, given, count(*) n from cro group by all")
    print('ev', db.execute('select count(*), count(distinct person), count(distinct orcid) from ev').fetchone(), flush=True)
    import pyarrow as pa
    import pyarrow.parquet as pq
    labels = dict(db.execute('select key, label from pr').fetchall())
    on = defaultdict(list)
    for o, fam, giv, n in db.execute('select * from orc_names').fetchall():
        on[o].append((fam, giv, n))
    share = {}
    for p, o in db.execute('select distinct person, orcid from ev').fetchall():
        lf = forms(labels.get(p) or '')
        tot = agree = 0
        for fam, giv, n in on.get(o, ()):
            tot += n
            if fam and any(fam_agree(f, fam_norm(fam)) for f, _, _ in lf):
                agree += n
        share[(p, o)] = (agree / tot if tot else None, tot)
    db.execute('create or replace table orc_share(person varchar, orcid varchar, name_share double, orcid_rows bigint)')
    db.executemany('insert into orc_share values (?,?,?,?)', [(p, o, s, t) for (p, o), (s, t) in share.items()])
    db.execute("""create or replace table ev2 as
        select ev.*, s.name_share, s.orcid_rows, p.label, p.orcids key_orcids, p.cited key_cited, p.works key_works,
               (select list(a.key) from anchored a where a.orcid = ev.orcid) orcid_anchored_on,
               len(p.orcids) > 0 has_anchor, list_contains(p.orcids, ev.orcid) is_anchor
        from ev join orc_share s using (person, orcid) join pr p on p.key = ev.person""")
    # keys on which the same ORCID appears (name-matched rows)
    db.execute("""create or replace table okeys as select orcid, list(distinct person) keys, count(distinct person) nk
                  from ev group by orcid""")
    db.execute("""create or replace table ev3 as select ev2.*, okeys.keys orcid_on_keys, okeys.nk orcid_n_keys,
            (select count(*) from ev2 x where x.person = ev2.person and x.n_works >= 2 and not x.is_anchor) key_n_orcids_2plus
        from ev2 join okeys using (orcid)""")
    db.execute("""create or replace table ev4 as select *,
        case when is_anchor then 'agrees'
             when not has_anchor and n_works >= 2 and n_full >= 1 and orcid_n_keys = 1
                  and (orcid_anchored_on is null or len(orcid_anchored_on) = 0) then 'a'
             when has_anchor and not is_anchor then 'b'
             else '' end cls,
        orcid_n_keys >= 2 or (len(coalesce(orcid_anchored_on, [])) > 0 and not list_contains(orcid_anchored_on, person)) in_c
        from ev3""")
    db.execute(f"copy (select person, label, orcid, n_works, y_min, y_max, authenticated, names_on_record, n_full, n_initial, n_variant, name_share, orcid_rows, key_orcids, orcid_anchored_on, orcid_on_keys, key_n_orcids_2plus, cls, in_c, key_cited, key_works, dois from ev4 order by person, orcid) to '{W}/orcid-evidence.csv.gz' (header, compression gzip)")
    print('classes', db.execute('select cls, in_c, count(*) from ev4 group by all order by all').fetchall(), flush=True)
    # ---- (c) pairs: two keys with one ORCID (name-matched on works of both, or anchored on one and on works of the other)
    db.execute("""create or replace table cpairs as
        with s as (select orcid, person from ev union select orcid, key from anchored where orcid in (select orcid from ev))
        select a.orcid, a.person k1, b.person k2 from s a join s b on a.orcid = b.orcid and a.person < b.person""")
    db.execute("""create or replace table cp as
        select c.*, p1.label l1, p2.label l2, p1.cited c1, p2.cited c2, p1.works w1, p2.works w2, p1.orcids o1, p2.orcids o2,
               p1.anchors a1, p2.anchors a2,
               (select count(distinct x.doi) from m x join m y on x.doi = y.doi where x.person = c.k1 and y.person = c.k2) shared_dois,
               (select count(distinct x.doi) from m x where x.person = c.k1 and x.orcid = c.orcid) n1,
               (select count(distinct y.doi) from m y where y.person = c.k2 and y.orcid = c.orcid) n2
        from cpairs c join pr p1 on p1.key = c.k1 join pr p2 on p2.key = c.k2""")
    # affiliations of each key (row-level, any work), normalised
    db.execute(r"""create or replace table aff as
        select person, doi, coalesce(cr_year, graph_year) as "year", trim(a) institution, nullif(ror, '') ror,
               regexp_replace(lower(strip_accents(trim(a))), '[^a-z0-9]+', ' ', 'g') inorm
        from m, unnest(string_split(affiliation, ' | ')) u(a) where affiliation is not null""")
    db.execute(f"copy (select person, institution, ror, year, doi from aff order by person, year) to '{W}/affiliation-evidence.csv.gz' (header, compression gzip)")
    db.execute(r"""create or replace table affspan as
        select person, coalesce(ror, inorm) inst_id, any_value(institution) institution, any_value(ror) ror,
               min(year) y_from, max(year) y_to, count(distinct doi) n_works
        from aff group by person, coalesce(ror, inorm)""")
    db.execute(f"copy (select * from affspan order by person, y_from) to '{W}/affiliation-spans.csv.gz' (header, compression gzip)")
    db.execute("""create or replace table cp2 as select cp.*,
        (select count(*) from affspan s1 join affspan s2 on s1.inst_id = s2.inst_id where s1.person = cp.k1 and s2.person = cp.k2
            and s1.y_from <= s2.y_to + 3 and s2.y_from <= s1.y_to + 3) shared_aff
        from cp""")
    db.execute(f"copy (select * from cp2 order by least(coalesce(c1,0), coalesce(c2,0)) desc) to '{W}/orcid-two-keys.csv.gz' (header, compression gzip)")
    print('c pairs', db.execute('select count(*), count(*) filter (where shared_dois>0 or shared_aff>0) from cp2').fetchone(), flush=True)
    # ---- 3. sweep: Crossref works with a key's anchored ORCID, DOI not in the graph
    db.execute(f"""create or replace table sweep as
        select a.key person, r.doi, r.given, r.family, r.role, r.orcid, r.orcid_authenticated authenticated, w.type, w.title, w.container, w.issn, w.publisher, w.year
        from anchored a join cro r on r.orcid = a.orcid left join crw w on w.doi = r.doi
        where r.doi not in (select doi from '{IN}/b_graph_dois.parquet')""")
    db.execute(f"copy (select * from sweep order by person, year) to '{W}/outside-sweep.parquet' (format parquet)")
    print('sweep', db.execute('select count(*), count(distinct person), count(distinct doi) from sweep').fetchone(),
          f'{time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    os.makedirs(f'{W}/tmp', exist_ok=True)
    cmd = sys.argv[1]
    for step in (('extract', 'match', 'tables') if cmd == 'all' else (cmd,)):
        globals()[step]()
