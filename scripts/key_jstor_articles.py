"""JSTOR research articles, review essays and review articles -> work keys (2026-11-06). Writes a proposal.

The JSTOR full-text delivery (request 7d08e73a, 2026-11-06; data/field-research/jstor-fulltext-2026-11-06/BRIEF.md)
gives the notes of 108,343 research articles, 211 review essays and 1,519 review articles. Their citations become
CITES edges (JSTOR legal, 2026-11-06: no issue with releasing the citation graph), so each citing item needs a work
key. Items already keyed by DOI keep their key. The rest get a work key anchored on the DOI (`doi:10.2307/...`,
lower case), or on the JSTOR item id (`jstor-item:<uuid>`) when JSTOR gives no DOI, labelled with the title as
JSTOR gives it, with `year:` and `journal:` members from the request metadata
(/mnt/e/JSTOR_history_citation_graph/records.sqlite). Authors are left to the DOI routes (ORCID, Crossref) and
later rules; no person is credited here. Metadata only: no text is read.

    python3 scripts/key_jstor_articles.py --out data/identifiers/jstor-articles-2026-11-06
"""
import argparse
import gzip
import json
import sqlite3
from collections import Counter
from pathlib import Path

from identifiers import DEFAULT_DIR, State, materialise

RECORDS = Path('/mnt/e/JSTOR_history_citation_graph/records.sqlite')
GENRES = ('research_article_as_deposited', 'review_essay_as_deposited', 'review_article_as_deposited')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    c = sqlite3.connect(f'file:{RECORDS}?mode=ro', uri=True)
    rows = c.execute(f"""SELECT item_id, doi, title, journal_title, year, genre FROM records
        WHERE included AND genre IN ({','.join('?' * len(GENRES))}) ORDER BY item_id""", GENRES).fetchall()
    report, ops, seen = Counter(), [], set()
    for iid, doi, title, journal, year, genre in rows:
        report['items'] += 1
        anchor = f'doi:{doi.strip().lower()}' if doi and doi.strip() else f'jstor-item:{iid}'
        if anchor in state.anchor:
            report['already_keyed'] += 1
            continue
        if anchor in seen:
            report['duplicate_anchor'] += 1
            continue
        seen.add(anchor)
        report['minted_' + genre.split('_as_')[0]] += 1
        report['minted_with_doi' if anchor.startswith('doi:') else 'minted_jstor_item_only'] += 1
        members = [m for m in (f'year:{year}' if year else '', f'journal:{journal}' if journal else '') if m]
        ops.append(dict(event='mint', key=f'new:{len(ops)}', type='work',
                        label=(title or '').strip()[:400] or f'[untitled JSTOR item in {journal}, {year}]',
                        resolution='recorded', anchors=[anchor], aliases=[], members=members,
                        basis=f'JSTOR {genre.split("_as_")[0].replace("_", " ")} in {journal} ({year}), cited-notes source '
                              f'(JSTOR full-text request 7d08e73a)'))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    body = json.dumps(dict(basis='JSTOR articles and review essays with notes -> work keys', decided_by='rule', ops=ops),
                      ensure_ascii=False) + '\n'
    if len(body) > 50_000_000:          # proposals over ~50 MB are committed gzipped (GitHub's 100 MB limit)
        with gzip.open(args.out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
            f.write(body)
    else:
        (args.out / 'proposal.json').write_text(body)
    (args.out / 'report.json').write_text(json.dumps(dict(sorted(report.items())), indent=1) + '\n')
    print(json.dumps(dict(sorted(report.items()))))


if __name__ == '__main__':
    main()
