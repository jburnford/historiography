#!/usr/bin/env python3
"""Regenerate the dissertation citation summaries for the main graph and every country sub-graph.

Run after ``build_dissertation_citation_graph.py`` (which writes ``graph.json`` and the
coverage and top-500 tables for every scope). The sub-graphs are the countries listed in
``graph.json`` ``meta.subgraphs`` (those with at least the build's ``--subgraph-threshold``
strict History PhDs; see ``dissertation_scope.py``).

- Main graph (``summary/``): trends and their page, the views (fields, supervision,
  universities, practice) and their page.
- Each sub-graph (``summary/countries/<CC>/``): the same, plus the atlas crosswalk.
  CA also gets the atlas trend test (its windows follow the Toronto and York programmes) and
  the idea-vs-content readership table, which serve the atlas's Canadian purpose.

``--robustness`` also re-runs the co-citation robustness test (``audit/``, slow).
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CA_EXTRAS = [['dissertation_atlas_trend_test.py', '--series', 'v19'], ['dissertation_idea_vs_content.py']]


def run(script, out, country, *extra):
    cmd = [sys.executable, str(HERE / script), '--out', str(out)] + (['--country', country] if country else []) + list(extra)
    print('==', script, country or 'main', ' '.join(extra), flush=True)
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--robustness', action='store_true', help='re-run test_cocitation_fields.py for each scope')
    parser.add_argument('--only', nargs='*', help="scopes to run: 'main' and/or country codes (default: all)")
    args = parser.parse_args()
    with (args.out / 'graph.json').open() as f:  # meta is written first, but the file is large: read it once
        meta = json.load(f)['meta']
    scopes = [None] + meta.get('subgraphs', [])
    if args.only:
        scopes = [s for s in scopes if (s or 'main') in args.only]
    print('sub-graphs:', meta.get('subgraphs'), 'threshold:', meta.get('subgraph_threshold'), flush=True)
    for country in scopes:
        run('dissertation_citation_trends.py', args.out, country)
        run('dissertation_citation_views.py', args.out, country)
        if args.robustness:
            run('test_cocitation_fields.py', args.out, country)
        run('dissertation_atlas_crosswalk.py', args.out, country, *([] if country else ['--skip-atlas']))
        run('render_citation_trends_html.py', args.out, country)
        run('render_citation_views_html.py', args.out, country)
        if country == 'CA':
            for script, *extra in CA_EXTRAS:
                run(script, args.out, country, *extra)
    print('SUMMARIES-OK', flush=True)


if __name__ == '__main__':
    main()
