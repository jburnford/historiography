"""A historian's network from the graph: co-authors, reviewers, the reviewed, students, supervisors, editors (2026-11-05).

User, 2026-11-05: "show me my network of co-authors, people I've reviewed, students, supervisors etc everyone with an
edge ... editors of books I've published in"; "the goal of course would be to build these networks for a lot of the
historians in our graph". Reads build/graph (scripts/build_graph.py) and writes, for each key, a Markdown section:
- co-authors (COAUTHORED: shared titles, first and last year) and co-editors (COEDITED);
- reviewed their books: keyed reviewers (REVIEWED) and the reviewers of their books named on review works but not
  keyed (JSTOR/Crossref names as printed, key_jstor_reviews: no person keys by name);
- they reviewed (REVIEWED from the key);
- supervisors and students (ADVISED, with the thesis);
- editors of volumes they contributed chapters to, and contributors to volumes they edited (EDITOR_OF).

    python3 scripts/ego_network.py p-24137 [p-893 ...] --out network.md
"""
import argparse
from collections import defaultdict
from pathlib import Path

import duckdb

from identifiers import ROOT

G = ROOT / 'build/graph'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('keys', nargs='+')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    db = duckdb.connect()
    for t in ('person', 'work', 'coauthored', 'coedited', 'reviewed', 'reviews', 'authored', 'advised', 'editor_of'):
        db.execute(f"CREATE VIEW {t} AS SELECT * FROM '{G}/{t}.parquet'")
    label = lambda k: (db.execute('SELECT label FROM person WHERE key = ?', [k]).fetchone() or [k])[0]
    wlabel = lambda w: (db.execute('SELECT label, year FROM work WHERE key = ?', [w]).fetchone() or [w, None])
    out = []
    for k in args.keys:
        me = label(k)
        out.append(f'## {me} ({k})\n')
        rows = db.execute("""SELECT CASE WHEN "from" = ? THEN "to" ELSE "from" END, titles, first_year, last_year FROM coauthored
                             WHERE "from" = ? OR "to" = ? ORDER BY titles DESC, first_year""", [k, k, k]).fetchall()
        out.append(f'**Co-authors** ({len(rows)})\n')
        out += [f'- {label(o)} — {t} shared title{"s" if t != 1 else ""} ({a}–{b})' if a != b else
                f'- {label(o)} — {t} shared title{"s" if t != 1 else ""} ({a})' for o, t, a, b in rows] or ['- none in the graph']
        ce = db.execute("""SELECT CASE WHEN "from" = ? THEN "to" ELSE "from" END, titles, first_year, last_year FROM coedited
                             WHERE "from" = ? OR "to" = ? ORDER BY titles DESC, first_year""", [k, k, k]).fetchall()
        out.append(f'\n**Co-editors** ({len(ce)})\n')
        out += [f'- {label(o)} — {t} volume{"s" if t != 1 else ""} ({a}–{b})' if a != b else
                f'- {label(o)} — {t} volume{"s" if t != 1 else ""} ({a})' for o, t, a, b in ce] or ['- none in the graph']
        rev = db.execute("""SELECT DISTINCT "from", book FROM reviewed WHERE "to" = ?""", [k]).fetchall()
        named = db.execute("""SELECT DISTINCT w.key, w.reviewer_names, w.journal, w.year, b.label FROM authored a JOIN reviews r ON r."to" = a."to"
                              JOIN work w ON w.key = r."from" JOIN work b ON b.key = a."to"
                              WHERE a."from" = ? AND len(w.reviewer_names) > 0 ORDER BY w.year""", [k]).fetchall()
        named = [r[1:] for r in named]
        keyed_names = {label(r) for r, _ in rev}
        out.append(f'\n**Reviewed their books** ({len(rev)} keyed; {len(named)} reviews naming a reviewer)\n')
        out += [f'- {label(r)} (keyed), on *{wlabel(b)[0][:80]}*' for r, b in rev]
        out += [f'- {", ".join(n)} — {j or "?"} {y or ""}, on *{bl[:70]}*' for n, j, y, bl in named
                if not set(n) & keyed_names]
        if not rev and not named:
            out.append('- none in the graph')
        did = db.execute("""SELECT DISTINCT "to", book FROM reviewed WHERE "from" = ?""", [k]).fetchall()
        out.append(f'\n**They reviewed** ({len(did)})\n')
        out += [f'- {label(a)}, *{wlabel(b)[0][:80]}*' for a, b in did] or ['- none in the graph']
        sup = db.execute("""SELECT "from", thesis FROM advised WHERE "to" = ?""", [k]).fetchall()
        stu = db.execute("""SELECT "to", thesis FROM advised WHERE "from" = ?""", [k]).fetchall()
        out.append(f'\n**Supervisors** ({len(sup)})\n')
        out += [f'- {label(a)}' + (f' — *{wlabel(t)[0][:80]}* ({wlabel(t)[1]})' if t else '') for a, t in sup] or ['- none in the graph']
        out.append(f'\n**Students** ({len(stu)})\n')
        out += [f'- {label(a)}' + (f' — *{wlabel(t)[0][:80]}* ({wlabel(t)[1]})' if t else '') for a, t in sorted(stu, key=lambda x: wlabel(x[1])[1] or 0)] or ['- none in the graph']
        eds = db.execute("""SELECT DISTINCT "from", volume FROM editor_of WHERE "to" = ?""", [k]).fetchall()
        vols = defaultdict(list)
        for e, v in eds:
            vols[v].append(label(e))
        out.append(f'\n**Editors of volumes they contributed to** ({len(vols)} volumes)\n')
        out += [f'- *{wlabel(v)[0][:80]}*: {", ".join(es)}' for v, es in vols.items()] or ['- none in the graph']
        con = db.execute("""SELECT DISTINCT "to", volume FROM editor_of WHERE "from" = ?""", [k]).fetchall()
        out.append(f'\n**Contributors to volumes they edited** ({len(con)})\n')
        out += [f'- {label(a)}, in *{wlabel(v)[0][:70]}*' for a, v in con[:60]] or ['- none in the graph']
        out.append('\n')
    args.out.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(args.out)


if __name__ == '__main__':
    main()
