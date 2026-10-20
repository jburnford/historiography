"""Scopes of the dissertation citation graph: the main graph and its country sub-graphs.

User decision, 2026-10-20: the citation graph grows with History PhDs from other parts of
the world. The **main graph** counts every strict History PhD (``in_analysis``), whatever
its country. A **country sub-graph** is produced for every country with at least
``SUBGRAPH_THRESHOLD`` strict dissertations (``build_dissertation_citation_graph.py
--subgraph-threshold``); the qualifying countries are listed in ``graph.json`` under
``meta.subgraphs``.

Output layout (under the dissertation-citations directory):
- ``summary/``: the main graph (all countries).
- ``summary/countries/<CC>/``: one directory per qualifying country, holding the same
  outputs restricted to that country's strict History PhDs plus the country-specific
  analyses (for CA: the atlas crosswalk and atlas trend test, which serve the atlas's
  purpose of teaching historiography in Canada).
- ``audit/`` and ``audit/countries/<CC>/``: the same split for audit outputs.

Every analysis script takes ``--country CC`` (absent = main graph).
"""
from pathlib import Path

SUBGRAPH_THRESHOLD = 2000
LEGACY_COUNTRY = 'CA'  # records harvested before ``country`` was recorded are Canadian
UNKNOWN_COUNTRY = 'ZZ'  # ISO 3166 user-assigned code, for records whose country is unknown


def record_country(d):
    """ISO 3166-1 alpha-2 country of a doctorate record (absent = CA, the legacy harvests)."""
    c = (d.get('country') or LEGACY_COUNTRY).strip().upper()
    return c if len(c) == 2 and c.isalpha() else UNKNOWN_COUNTRY


def add_scope_argument(parser):
    parser.add_argument('--country', type=lambda s: s.strip().upper() or None, default=None,
                        help='ISO-2 country sub-graph (e.g. CA); absent = the main graph (all countries)')


def summary_dir(out, country=None):
    return Path(out) / 'summary' if not country else Path(out) / 'summary' / 'countries' / country


def audit_dir(out, country=None):
    return Path(out) / 'audit' if not country else Path(out) / 'audit' / 'countries' / country


def in_scope(n, country=None):
    """A strict History PhD (``in_analysis``) in the main graph or in one country's sub-graph."""
    return n['type'] == 'Dissertation' and bool(n.get('in_analysis')) and (country is None or n.get('country') == country)


def strict_count(n, country=None):
    """Strict History PhDs citing a Work or Person node, in the main graph or one country."""
    if country is not None:
        return n.get('cited_by_country', {}).get(country, 0)
    return n['cited_by'] if n['type'] == 'Work' else n['cited_by_dissertations']


def check_country(graph, country):
    """A sub-graph is analysed only when its country qualifies (``meta.subgraphs``)."""
    if country is not None and country not in graph['meta'].get('subgraphs', []):
        raise SystemExit(f'{country} is not a sub-graph of this build (meta.subgraphs = {graph["meta"].get("subgraphs")}); '
                         f'sub-graphs need at least {graph["meta"].get("subgraph_threshold")} strict History PhDs')


COUNTRY_ADJECTIVE = {'CA': 'Canadian', 'US': 'American', 'GB': 'British', 'FR': 'French', 'DE': 'German'}


def scope_label(country=None):
    """'Canadian' for a sub-graph, '' for the main graph (used in page titles)."""
    return COUNTRY_ADJECTIVE.get(country, country or '') if country else ''
