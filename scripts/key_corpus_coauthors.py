"""Co-authors LC lists without a relator, confirmed by the theses that cite them -> authored claims (2026-11-04).

key_lc_works.py reads a 700 added entry as authorship only with an author relator: older LC records give none,
and a bare 700 may be a co-author, an editor, a translator or the writer of a preface. So the graph credits
*Family Fortunes* to Leonore Davidoff alone (Catherine Hall is a bare 700), *Leviathan and the Air-Pump* to Steven
Shapin, *Histoire du Québec contemporain* to Paul-André Linteau; the coverage audit (citation-coverage-2026-11-04b)
counts those citations as `matched_not_theirs` for Hall, Schaffer, Durocher and Robert.

The dissertations are the second witness. A claim `lc-authored:<lccn>:<lcid>` (key_lc_works' form) is written when:
- a cited work the crosswalks match to a graph work lists, as one of its authors, a corpus id whose key holds the
  LC authority `lcid`;
- the LC record (an edition of that work) has a 100 or 700 heading that resolves to `lcid` (lc_resolve_authorities,
  as key_lc_works reads headings) and that key_lc_works did not already read as authored or edited;
- the statement of responsibility (245 $c), when the record has one, names the person (not an honoree or subject:
  Stuart Hall in *Without Guarantees*), and not only in a translating, prefacing, introducing, illustrating or
  annotating clause; a person it names in an editing clause gets `edited` (key_lc_works.editor_by_statement, or
  '..., editors') instead.
Persons whose keys hold no LC authority are counted (`coauthor_no_lc`) and left for another route.

    python3 scripts/key_corpus_coauthors.py --crosswalk X1 X2 ... --out data/identifiers/corpus-coauthors-2026-11-04
    python3 scripts/identifiers.py apply data/identifiers/corpus-coauthors-2026-11-04/proposal.json
"""
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise
from key_lc_works import editor_by_statement, former_heading
from lc_resolve_authorities import load_names, resolve

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
GRAPH = ROOT / 'build/graph'
LC_INDEX = Path('/mnt/e/lc-bib-2016/index')
LC_NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
OTHER_ROLE = re.compile(r'\b(translat|traduc|tradu[çc]|trad\.|übers|ubers|prefac|pref\.|préf|pref[áa]c|introd|foreword|avant-propos|'
                        r'notes?\b|annot|comment|illustr|photograph|apresenta|posf[áa]c|postface|afterword|selected|sele[çc])', re.I)


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


EDIT_ROLE = re.compile(r'\b(editors?|eds?\.?|edited|org\.|orgs?\b|organiz|organis|dir\.|direction|hrsg|herausg|coord|compil)', re.I)


def named(family, responsibility):
    fam = fold(family).split()
    return bool(fam) and fam[0] in fold(responsibility)


def edit_role(family, responsibility):
    """The statement names the person in a clause that says editing ('Schmuel Spector, Robert Rozett, editors')."""
    fam = fold(family).split()[0] if fold(family).split() else ''
    parts = [p for p in fold(responsibility).split(';') if fam and fam in p]
    return bool(parts) and all(EDIT_ROLE.search(p) for p in parts)


def other_role(family, responsibility):
    """The statement names the person only in a translating, prefacing or similar clause."""
    if not responsibility or not family:
        return False
    fam = fold(family).split()[0] if fold(family).split() else ''
    parts = [p for p in re.split(r'[;,]| and | e | et | y | und ', fold(responsibility)) if fam and fam in p]
    return bool(parts) and all(OTHER_ROLE.search(p) for p in parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--crosswalk', type=Path, nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute("SET memory_limit = '4GB'")
    db.execute("SET temp_directory = '/mnt/e/duckdb-tmp'")
    files = ', '.join(f"'{x}'" for x in args.crosswalk)
    db.execute(f"CREATE TABLE x AS SELECT DISTINCT work_id, key FROM read_csv([{files}], all_varchar=true, union_by_name=true)")
    db.execute(f"CREATE TABLE anc AS SELECT a, key AS wk FROM (SELECT key, unnest(anchors) AS a FROM '{GRAPH}/work.parquet')")
    db.execute(f"""CREATE TABLE xk AS SELECT DISTINCT x.work_id, coalesce(w.key, anc.wk) AS wk FROM x
                   LEFT JOIN '{GRAPH}/work.parquet' w ON w.key = x.key LEFT JOIN anc ON anc.a = x.key""")
    db.execute(f"""CREATE TABLE pk AS SELECT substr(a, 13) AS p, key, label, lcnaf FROM
                   (SELECT key, label, lcnaf, unnest(anchors) AS a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    db.execute(f"""CREATE TABLE au AS SELECT "from" AS pk, "to" AS wk FROM '{GRAPH}/authored.parquet'
                   UNION SELECT "from", "to" FROM '{GRAPH}/edited.parquet'""")
    # (person key, its LC authority, graph work) where a citation of the work lists the person and the graph does not
    rows = db.execute(f"""
        SELECT DISTINCT pk.key, pk.label, pk.lcnaf, xk.wk, a.person_key
        FROM read_csv('{CORPUS}/authored.csv.gz') a JOIN xk USING (work_id) JOIN pk ON pk.p = a.person_key
        WHERE xk.wk IS NOT NULL AND NOT EXISTS (SELECT 1 FROM au WHERE au.pk = pk.key AND au.wk = xk.wk)""").fetchall()
    report = Counter(missing_links=len(rows))
    want = defaultdict(set)                            # graph work -> {(key, lcid, label, corpus id)}
    for key, label, lcid, wk, p in rows:
        if not lcid:
            report['coauthor_no_lc'] += 1
            continue
        want[wk].add((key, lcid, label, p))
    db.execute('CREATE TABLE ww(wk VARCHAR)')
    db.executemany('INSERT INTO ww VALUES (?)', [(w,) for w in want])
    lccns = defaultdict(set)                           # lccn -> graph works
    for wk, a in db.execute(f"""SELECT key, a FROM (SELECT key, unnest(anchors) AS a FROM '{GRAPH}/work.parquet')
                                WHERE key IN (SELECT wk FROM ww) AND a LIKE 'lccn:%'""").fetchall():
        lccns[a[5:]].add(wk)
    db.execute('CREATE TABLE lc(c VARCHAR)')
    db.executemany('INSERT INTO lc VALUES (?)', [(c,) for c in lccns])
    heads = db.execute(f"""SELECT trim(h.control), h.tag, h.heading, h.uri, h.relators, h.family, r.responsibility
        FROM read_parquet('{LC_INDEX}/headings-*.parquet') h LEFT JOIN read_parquet('{LC_INDEX}/records-*.parquet') r
          ON r.control = h.control
        WHERE trim(h.control) IN (SELECT c FROM lc) AND h.tag IN ('100', '700')""").fetchall()
    lcids = {lcid for ws in want.values() for _, lcid, _, _ in ws}
    names = load_names(LC_NAMES, lcids | {u.rstrip('/').split('/')[-1] for *_, u, _, _, _ in heads if u})
    state = State.load(args.state)
    ops, seen, sample = [], set(), []
    for control, tag, heading, uri, relators, family, responsibility in heads:
        lcid, via = resolve(dict(heading=heading, uri=uri or ''), names)
        if not lcid or (via == 'variant' and not former_heading(heading, names[0][lcid]['label'])):
            continue
        for wk in lccns[control]:
            for key, klc, label, p in want[wk]:
                if klc != lcid:
                    continue
                if responsibility and not named(family, responsibility):
                    report['not_in_statement'] += 1           # an honoree or subject (Stuart Hall, Without Guarantees)
                    continue
                if other_role(family, responsibility):
                    report['other_role'] += 1
                    continue
                role = (editor_by_statement(tag, relators, family, responsibility)
                        or ('edited' if edit_role(family, responsibility) else 'authored'))
                anchor = f"lc-{role}:{control}:{lcid}"
                if anchor in state.anchor or anchor in seen:
                    report['claim_exists'] += 1
                    continue
                seen.add(anchor)
                report[role] += 1
                ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded',
                                anchors=[anchor], relation=dict(subject=f'lcnaf:{lcid}', predicate=role, object=f'lccn:{control}'),
                                basis=f'LC record {control} lists {heading} ({tag}, no relator) and theses citing the work '
                                      f'list {p} as its author'))
                if len(sample) < 40:
                    sample.append(dict(person=label, heading=heading, lccn=control, role=role, responsibility=responsibility))
    report['people'] = len({o['relation']['subject'] for o in ops})
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='co-authors LC lists without a relator, confirmed by the citing theses', decided_by='rule', ops=ops),
        ensure_ascii=False) + '\n')
    (args.out / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()
