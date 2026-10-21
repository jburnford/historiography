#!/usr/bin/env python3
"""Ingest new rounds of downloaded History PhDs into the dissertation citation graph.

User requirement (2026-10-20): "make sure the pipeline is built to process new dissertations
in future rounds as we continue the downloads." This is the one command for a new round:

    python3 scripts/dissertation_ingest.py --dry-run          # report what would be added
    python3 scripts/dissertation_ingest.py                    # merge into doctorates.json only
    python3 scripts/dissertation_ingest.py --update           # merge, extract, build, link, rebuild, summaries, TF-IDF

**Sources.** ``<D>/ingest-sources.json`` lists every source in order. Each names an adapter
(``ADAPTERS`` below) and its inputs; adding a source is one registry entry plus, for a new
kind of input, a small adapter function. An adapter yields candidates: a manifest entry in
the ``doctorates.json`` shape (``country`` ISO-2, institution, id, title, authors, dates,
``history_scope``/``eligibility_basis`` or a ``history_label``, item_url, access category,
``source_harvest``) and the dissertation's PDF part(s). A source with ``"ingest": false`` is
read and reported (what it would add) but adds nothing.

**Merge (idempotent).**
- Existing ``doctorates.json`` entries are never rewritten: they stay byte-identical and in
  order; new entries are appended. For sources that produced the existing entries, the
  report counts how many the adapter reproduces exactly (a regression check).
- Duplicates are dropped across sources by (institution, id), by the SHA-256 of any PDF, and
  by country + author surname + normalised title (first 60 characters, which tolerates
  truncated repository titles) + year within one.
- An id already used by another institution is namespaced ``<institution>-<id>`` (the graph
  builder keys dissertations by id alone).
- Files: a file is taken only when it exists, is complete (no ``.part`` sibling, size equals
  the declared size), has not been modified in the last ``--settle-minutes`` (a downloader
  may still be writing), and lies inside the PDF store (``<D>/pdf``) below its top level
  (top-level files there are not dissertations). Missing and settling files are reported.
- PDFs that no existing download log in ``<D>`` records are written to
  ``<D>/downloads-ingest.jsonl`` (regenerated each run, same row shape as the download logs),
  which the extractor and the graph builder read like any other download log.
- The run report (counts per source: new, present, updated, duplicates, missing files) is
  written to ``<D>/logs/ingest-<timestamp>.json`` and ``<D>/logs/ingest-latest.json``.

**Incremental processing (``--update``).** Extracts only PDFs not yet in
``extraction.jsonl`` (by path, re-extracting a path whose SHA-256 changed), with OCR, then runs
``build_dissertation_citation_graph.py``, ``link_cited_works_to_authorities.py``, the build
again, ``dissertation_citation_summaries.py`` (main graph and every sub-graph) and
``dissertation_tfidf_families.py`` for the main graph and every sub-graph. Step logs go to
``<D>/logs/``. ``--steps`` runs a subset; ``--provisional-subgraph CC`` passes a below-threshold
country to the builder as a labelled first-pass sub-graph.
"""
import argparse
import csv
from datetime import datetime, timezone
import difflib
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D_DEFAULT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
CLOSED = ('restricted', 'embargoed', 'no_public_pdf')

# ----------------------------------------------------------------------------- helpers


def read_jsonl(path):
    """Rows of a JSONL file, tolerating a final line still being written."""
    rows = []
    if not Path(path).exists():
        return rows
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def resolve(p, d):
    """Registry paths: absolute; 'data/...' or 'scripts/...' from the repository root; else from D."""
    p = Path(os.path.expanduser(str(p)))
    if p.is_absolute():
        return p
    return ROOT / p if p.parts and p.parts[0] in ('data', 'scripts', 'tests') else d / p


def expand(patterns, d):
    out = []
    for pat in patterns if isinstance(patterns, list) else [patterns]:
        hits = sorted(glob.glob(str(resolve(pat, d)), recursive=True))
        out += [Path(h) for h in hits]
    return out


def rel_root(path):
    """A provenance path relative to the repository root when it lies inside it."""
    path = Path(path)
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def fold(text):
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in unicodedata.normalize('NFKD', text or '').casefold()
                                              if not unicodedata.combining(c))).strip()


def surname(authors):
    a = (authors or [''])[0] or ''
    s = a.split(',')[0] if ',' in a else (a.split()[-1] if a.split() else '')
    return fold(s)


def dedupe_key(entry):
    title = fold(entry.get('title'))
    if len(title) < 12:
        return None
    return (entry.get('country') or 'CA', surname(entry.get('authors')), title[:60])


def entry_year(entry):
    if entry.get('year'):
        try:
            return int(entry['year'])
        except (TypeError, ValueError):
            pass
    for field in ('graduation_dates', 'copyright_dates', 'issued_dates'):
        for v in entry.get(field) or []:
            m = re.match(r'(\d{4})', str(v))
            if m:
                return int(m.group(1))
    return None


def listify(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith('['):  # some harvests stored Python list reprs
        try:
            import ast
            return list(ast.literal_eval(v))
        except (ValueError, SyntaxError):
            return [v]
    return [v]


class Store:
    """The PDF store (``<D>/pdf``, a symlink to E:) and file checks."""

    def __init__(self, d, settle_minutes, sha_cache):
        self.d = d
        self.root = Path(os.path.realpath(d / 'pdf'))
        self.settle = settle_minutes * 60
        self.cache_path = sha_cache
        self.cache = json.loads(sha_cache.read_text()) if sha_cache.exists() else {}
        self.now = time.time()

    def check(self, path, declared_bytes=None, declared_sha=None):
        """(status, info): status is 'ok' or why the file is not taken."""
        path = Path(path)
        real = Path(os.path.realpath(path))
        try:
            rel = real.relative_to(self.root)
        except ValueError:
            return 'outside_pdf_store', dict(path=str(path))
        if len(rel.parts) < 2:
            return 'top_level_file_ignored', dict(path=str(path))
        if not real.exists():
            return 'missing_file', dict(path=str(path))
        if Path(str(real) + '.part').exists() or real.suffix == '.part':
            return 'still_downloading', dict(path=str(path))
        st = real.stat()
        if self.now - st.st_mtime < self.settle:
            return 'still_downloading', dict(path=str(path))
        if declared_bytes and int(declared_bytes) != st.st_size:
            return 'size_mismatch', dict(path=str(path), bytes=st.st_size, declared=declared_bytes)
        sha = declared_sha or self.sha256(real, st)
        return 'ok', dict(rel=str(rel), bytes=st.st_size, sha256=sha)

    def sha256(self, real, st):
        key = f'{real}|{st.st_size}|{int(st.st_mtime)}'
        if key not in self.cache:
            h = hashlib.sha256()
            with open(real, 'rb') as f:
                for chunk in iter(lambda: f.read(1 << 20), b''):
                    h.update(chunk)
            self.cache[key] = h.hexdigest()
        return self.cache[key]

    def save(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=0) + '\n')


def file_spec(path, declared_bytes=None, sha256=None, part=None, name=None, checked_at=None):
    return dict(path=str(path), bytes=declared_bytes, sha256=sha256, part=part, name=name, checked_at=checked_at)


def candidate(entry, files=(), logged=False, closed=False):
    """``files``: file_spec dicts in part order. ``logged``: the files are already recorded in a
    download log inside D (no ingest-log row needed). ``closed``: no PDF is expected."""
    return dict(entry=entry, files=list(files), logged=logged, closed=closed)


def downloads_index(paths):
    """(institution, id) -> latest download row (a 'downloaded' row wins)."""
    latest = {}
    for p in paths:
        for r in read_jsonl(p):
            if 'institution' not in r or 'id' not in r:
                continue
            k = (r['institution'], r['id'])
            if r.get('status') == 'downloaded' or k not in latest:
                latest[k] = r
    return latest


def logged_files(row, d):
    if not row or row.get('status') != 'downloaded':
        return []
    files = row.get('files', [])
    multi = len(files) > 1 and all(f.get('part') for f in files)
    ordered = sorted(files, key=lambda f: f.get('part') or 0) if multi else [f for f in files if f.get('primary')] or files[:1]
    return [file_spec(d / f['path'], f.get('bytes'), f.get('sha256'), f.get('part') if multi else None, f.get('name'),
                      row.get('checked_at')) for f in ordered]


# ----------------------------------------------------------------------------- adapters

def us_entry(r, source_harvest):
    """The US manifest entry shape (fetch_us_tier2_pdfs.write_manifest)."""
    return dict(institution=r['institution'], id=r['id'], title=r['title'], authors=r['authors'],
                advisors=r.get('advisors', []), issued_dates=r.get('issued_dates', []),
                graduation_dates=r.get('graduation_dates', []), copyright_dates=r.get('copyright_dates', []),
                history_scope=r.get('history_scope', 'unchecked'), language=r.get('language', []),
                item_url=r['item_url'], source_harvest=source_harvest, country='US',
                eligibility_basis=r.get('eligibility_basis'), access_category=r.get('access_category'))


def adapter_canadian_harvest(src, d):
    """Canadian DSpace, EPrints, Islandora, Laval and UBC harvests: the entry shape and the
    doctoral filter of fetch_dissertation_pdfs.py; PDFs (or UBC texts) from D's download logs."""
    sys.path.insert(0, str(HERE))
    from fetch_dissertation_pdfs import doctoral_records
    logs = downloads_index(expand(src.get('logs', []), d))
    for path in expand(src['records'], d):
        for r in doctoral_records([path.relative_to(ROOT) if path.is_relative_to(ROOT) else path]):
            entry = dict(institution=r['institution'], id=r['id'], title=r['title'], authors=r['authors'],
                         advisors=r.get('advisors', []), issued_dates=r.get('issued_dates', []),
                         graduation_dates=r.get('graduation_dates', []), copyright_dates=r.get('copyright_dates', []),
                         history_scope=r.get('history_scope', 'explicit_history_program_or_department'
                                             if r.get('history_metadata_exact') else 'unchecked'),
                         language=r.get('language', []), item_url=r['item_url'], source_harvest=r['source_harvest'])
            row = logs.get((r['institution'], r['id']))
            yield candidate(entry, logged_files(row, d), logged=True, closed=not row or row.get('status') != 'downloaded')


def adapter_us_records(src, d):
    """US harvest records (tier 1, tier 2): doctoral records of a records.jsonl, any access
    category; PDFs from D's download log for that harvest."""
    logs = downloads_index(expand(src.get('logs', []), d))
    for path in expand(src['records'], d):
        sh = str(path.parent.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path.parent)
        for r in read_jsonl(path):
            if r.get('degree_classification') != 'doctoral':
                continue
            row = logs.get((r['institution'], r['id']))
            files = logged_files(row, d)
            yield candidate(us_entry(r, sh), files, logged=True, closed=r.get('access_category') in CLOSED)


def adapter_us_expansion_manifest(src, d):
    """The user's ChatGPT US collection: ``collection-manifest*.csv`` (verified distinct History
    PhDs with complete PDF sets; written by audit_us_dissertation_collection.py), joined to the
    harvest records for full metadata. Paths in the manifest may point to old local locations;
    they are followed through their symlinks to the copy on E:. SHA-256 comes from the source
    download logs where recorded."""
    meta = {}
    for path in expand(src.get('records', []), d):
        sh = str(path.parent.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path.parent)
        for r in read_jsonl(path):
            k = (r.get('institution'), r.get('id'))
            if k not in meta or r.get('eligibility') == 'history_phd':
                meta[k] = dict(r, _source_harvest=r.get('source_harvest') or sh)
    shas = {}
    for path in expand(src.get('logs', []), d):
        for r in read_jsonl(path):
            if r.get('status') != 'downloaded':
                continue
            for f in r.get('files', []):
                if f.get('path') and f.get('sha256'):
                    shas[os.path.realpath(path.parent / f['path'])] = (f['sha256'], f.get('bytes'), r.get('checked_at'))
    seen = set()
    for manifest in expand(src['manifests'], d):
        with open(manifest, newline='', encoding='utf-8') as fh:
            for m in csv.DictReader(fh):
                k = (m['institution'], m['id'])
                if k in seen:
                    continue
                seen.add(k)
                r = meta.get(k) or {}
                authors = r.get('authors') or [a.strip() for a in (m.get('authors') or '').split(';') if a.strip()]
                year = m.get('year') or r.get('year')
                rec = dict(r, institution=m['institution'], id=m['id'], title=r.get('title') or m['title'], authors=authors,
                           history_scope=r.get('history_scope') or 'explicit_history_program_or_department',
                           eligibility_basis=m.get('eligibility_basis') or r.get('eligibility_basis'),
                           access_category='open_pdf', item_url=m.get('item_url') or r.get('item_url'),
                           issued_dates=r.get('issued_dates') or ([str(year)] if year else []),
                           advisors=listify(r.get('advisors')), language=listify(r.get('language')))
                entry = us_entry(rec, r.get('_source_harvest') or rel_root(manifest.parent))
                entry.update(year=int(year) if str(year or '').isdigit() else None, degree=listify(r.get('degree')),
                             aha_id=m.get('aha_id') or r.get('aha_id') or None)
                paths = json.loads(m['paths'] or '[]')
                files = []
                for i, p in enumerate(paths):
                    sha, size, at = shas.get(os.path.realpath(p), (None, None, None))
                    files.append(file_spec(p, size, sha, i + 1 if len(paths) > 1 else None, Path(p).name, at))
                yield candidate(entry, files)


def adapter_browser_manifest(src, d):
    """Browser-collected US PDFs (handoff spec in
    data/field-research/us-dissertations-browser-handoff-2026-10-20/README.md): one CSV row per
    dissertation, PDFs at ``<root>/<institution>/<file_name>``. Eligibility: PhD/DPhil degree and
    a History department as recorded, plus an AHA directory match (surname, title similarity
    >= 0.9, year within one) when found."""
    manifest = resolve(src['manifest'], d)
    if not manifest.exists():
        return
    root = resolve(src.get('root', manifest.parent), d)
    aha = aha_index(resolve(src['aha'], d)) if src.get('aha') else {}
    with open(manifest, newline='', encoding='utf-8-sig') as fh:
        for m in csv.DictReader(fh):
            if not (m.get('file_name') and m.get('title')):
                continue
            inst = re.sub(r'[^a-z0-9]+', '', (m.get('institution') or '').lower()) or 'unknown'
            author = (m.get('author') or '').strip()
            phd = bool(re.search(r'\bPh\.?\s?D\b|\bD\.?Phil\b|Doctor of Philosophy', m.get('degree') or '', re.I))
            hist = bool(re.search(r'\bhistory\b', m.get('department') or '', re.I))
            year = m.get('year') if str(m.get('year') or '').strip().isdigit() else None
            match = aha_match(aha, author, m['title'], year)
            basis = f"browser-collected: degree '{m.get('degree', '')}', department '{m.get('department', '')}'"
            if match:
                basis += f'; AHA History PhD record matched ({match})'
            entry = dict(institution=inst, id=Path(m['file_name']).stem, title=m['title'].strip(), authors=[author] if author else [],
                         advisors=[], issued_dates=[year] if year else [], graduation_dates=[], copyright_dates=[],
                         history_scope='explicit_history_program_or_department' if (phd and hist) or match else 'unchecked',
                         language=[], item_url=m.get('repository_item_url') or m.get('pdf_url'),
                         source_harvest=str(manifest), country='US', eligibility_basis=basis, access_category='open_pdf',
                         year=int(year) if year else None, degree=[m.get('degree')] if m.get('degree') else [],
                         aha_id=match, rights=m.get('license_or_rights_statement') or None)
            yield candidate(entry, [file_spec(root / inst / m['file_name'], name=m['file_name'])])


def aha_index(path):
    idx = {}
    if not path.exists():
        return idx
    with open(path, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            idx.setdefault(surname([r['dissertator']]), []).append(r)
    return idx


def aha_match(idx, author, title, year):
    for r in idx.get(surname([author]), []):
        if year and r.get('year', '').isdigit() and abs(int(r['year']) - int(year)) > 1:
            continue
        if difflib.SequenceMatcher(None, fold(title), fold(r['title'])).ratio() >= 0.9:
            return r['id']
    return None


BASE_COUNTRIES = {
    'France': 'FR', 'Germany': 'DE', 'Spain': 'ES', 'Sweden': 'SE', 'United States': 'US', 'Greece': 'GR', 'Italy': 'IT',
    'Belgium': 'BE', 'Ireland': 'IE', 'Turkey': 'TR', 'United Kingdom': 'GB', 'Brazil': 'BR', 'Switzerland': 'CH',
    'Australia': 'AU', 'Finland': 'FI', 'Hong Kong': 'HK', 'Portugal': 'PT', 'Serbia': 'RS', 'Colombia': 'CO',
    'Mexico': 'MX', 'Netherlands': 'NL', 'Hungary': 'HU', 'Argentina': 'AR', 'Norway': 'NO', 'Latvia': 'LV',
    'South Korea': 'KR', 'Cyprus': 'CY', 'Slovenia': 'SI', 'South Africa': 'ZA', 'Poland': 'PL', 'Lithuania': 'LT',
    'Austria': 'AT', 'Singapore': 'SG', 'Luxembourg': 'LU', 'Malta': 'MT', 'Japan': 'JP', 'New Zealand': 'NZ',
    'Canada': 'CA', 'Indonesia': 'ID', 'Denmark': 'DK', 'Czech Republic': 'CZ', 'Chile': 'CL', 'Peru': 'PE'}
TLD_COUNTRY = {'uk': 'GB'}


def base_country(cluster):
    """ISO-2 country of a BASE cluster: its repository country, else the link's country-code
    top-level domain (for 'Germany/Austria/Switzerland', 'International', 'unknown'), else ZZ."""
    c = BASE_COUNTRIES.get(cluster.get('country') or '')
    if c:
        return c
    host = re.sub(r'^https?://', '', cluster.get('link') or cluster.get('cluster_id') or '').split('/')[0].split(':')[0]
    tld = host.rsplit('.', 1)[-1].lower() if '.' in host else ''
    if len(tld) == 2 and tld.isalpha():
        return TLD_COUNTRY.get(tld, tld.upper())
    return 'ZZ'


def adapter_base_clusters(src, d):
    """BASE theses (data/field-research/base-history-theses-2026-10-19): clusters.jsonl for
    metadata, D/downloads-base.jsonl (still being appended by the downloader: read tolerantly)
    for the PDFs. Only clusters whose history_label is in ``labels`` are taken. Eligibility
    follows the builder's BASE_LABEL_ELIGIBILITY hook on ``history_label``."""
    labels = set(src.get('labels', ['history']))
    overrides = src.get('country_overrides', {})  # source_key -> ISO-2, where BASE's repository country is wrong
    cpaths = expand(src['clusters'], d)
    harvest = str(cpaths[0].parent.relative_to(ROOT)) if cpaths and cpaths[0].is_relative_to(ROOT) else str(cpaths[0].parent)
    clusters = {c['cluster_id']: c for p in cpaths for c in read_jsonl(p)}
    downloaded = {}
    for p in expand(src['logs'], d):
        for r in read_jsonl(p):
            if r.get('cluster_id') and (r.get('status') == 'downloaded' or r['cluster_id'] not in downloaded):
                downloaded[r['cluster_id']] = r
    for cid, row in downloaded.items():
        c = clusters.get(cid)
        if not c or c.get('history_label') not in labels or row.get('status') != 'downloaded' or not row.get('files'):
            continue
        year = c.get('year')
        entry = dict(institution='base:' + (c.get('source_key') or 'unknown'),
                     id='base-' + hashlib.sha1(cid.encode()).hexdigest()[:16], title=c.get('title') or '',
                     authors=c.get('creators') or [], advisors=[], issued_dates=[str(year)] if year else [],
                     graduation_dates=[], copyright_dates=[], history_scope='base_history_label',
                     language=[c['language']] if c.get('language') else [], item_url=c.get('link') or cid,
                     source_harvest=harvest,
                     country=overrides.get(c.get('source_key')) or base_country(c), eligibility_basis=f"BASE history_label: {c.get('history_label')} "
                                                             f"({'; '.join(c.get('history_basis') or [])})",
                     access_category='open_pdf', year=year, history_label=c.get('history_label'),
                     repository=c.get('repository'), cluster_id=cid)
        f = row['files'][0]  # further files of a cluster are not declared parts: only the first is read
        yield candidate(entry, [file_spec(d / f['path'], f.get('bytes'), f.get('sha256'), None,
                                          Path(f['path']).name, row.get('checked_at'))])


def adapter_japan_records(src, d):
    """Japanese doctoral dissertations (data/field-research/japan-dissertations-2026-10-20):
    records.jsonl from classify_japan_dissertations.py (``history_label``, ``country: JP``); PDFs
    from its download logs (rows with a full-text file path)."""
    recs = {}
    for p in expand(src['records'], d):
        for r in read_jsonl(p):
            if r.get('history_label') in set(src.get('labels', ['history'])):
                recs[(r['institution'], r['id'])] = r
    files = {}
    for p in expand(src.get('logs', []), d):
        for row in read_jsonl(p):
            path = row.get('path') or row.get('dest') or row.get('file')
            ok = row.get('status') in ('downloaded', 'ok') and row.get('mode', 'fulltext') == 'fulltext'
            if path and ok:
                full = Path(path) if Path(path).is_absolute() else (ROOT / path if str(path).startswith('data/') else d / path)
                files.setdefault((row.get('institution'), row.get('id')), file_spec(full, row.get('bytes'), row.get('sha256')))
    for k, r in recs.items():
        if k not in files:
            continue
        entry = dict(institution=r['institution'], id=r['id'], title=r['title'], authors=r.get('authors', []),
                     advisors=r.get('advisors', []), issued_dates=r.get('issued_dates', []),
                     graduation_dates=r.get('graduation_dates', []), copyright_dates=r.get('copyright_dates', []),
                     history_scope=r.get('history_scope'), language=r.get('language', []), item_url=r.get('item_url'),
                     source_harvest=r.get('source_harvest'), country='JP', eligibility_basis=r.get('eligibility_basis'),
                     access_category=r.get('access_category'), year=r.get('year'), history_label=r.get('history_label'))
        yield candidate(entry, [files[k]])


ADAPTERS = {
    'canadian_harvest': adapter_canadian_harvest,
    'us_records': adapter_us_records,
    'us_expansion_manifest': adapter_us_expansion_manifest,
    'browser_manifest': adapter_browser_manifest,
    'base_clusters': adapter_base_clusters,
    'japan_records': adapter_japan_records,
}

# ----------------------------------------------------------------------------- merge


def merge(d, sources, store, only=None, include_disabled=False):
    """Returns (new manifest list, ingest-log rows, report). Never modifies existing entries."""
    manifest = json.loads((d / 'doctorates.json').read_text())
    keys = {(e['institution'], e['id']): i for i, e in enumerate(manifest)}
    id_owner = {e['id']: e['institution'] for e in manifest}
    logs = [p for p in sorted(d.glob('downloads*.jsonl')) if p.name != 'downloads-ingest.jsonl']
    logged = downloads_index(logs)
    sha_owner = {}
    for k, row in logged.items():
        if row.get('status') == 'downloaded':
            for f in row.get('files', []):
                if f.get('sha256'):
                    sha_owner.setdefault(f['sha256'], k)
    by_title = {}
    for e in manifest:
        dk = dedupe_key(e)
        if dk:
            by_title.setdefault(dk, []).append(((e['institution'], e['id']), entry_year(e)))
    renamed = {}  # (institution, original id) -> id used in the manifest
    rows, report, appended = {}, dict(sources={}), []
    # Rows of sources not read in this run (--sources) are kept as they are.
    run_names = {s['name'] for s in sources if not only or s['name'] in only}
    previous = {(r['institution'], r['id']) for r in read_jsonl(d / 'downloads-ingest.jsonl')}
    for r in read_jsonl(d / 'downloads-ingest.jsonl'):
        if r.get('source', '').split(':', 1)[-1] not in run_names and (r['institution'], r['id']) in keys:
            rows[(r['institution'], r['id'])] = r
    for src in sources:
        name = src['name']
        if only and name not in only:
            continue
        ingest = src.get('ingest', True) or include_disabled
        rep = report['sources'][name] = dict(adapter=src['adapter'], ingest=ingest, candidates=0, new=0, new_with_pdf=0,
                                             present=0, present_identical=0, present_differs=0, updated_file_added=0, present_ingest_logged=0, present_same_file=0,
                                             present_second_copy_same_sha=0, present_second_copy_other_sha=0,
                                             duplicate_sha=0, duplicate_title=0, id_namespaced=0,
                                             file_problems={}, examples={}, by_institution={}, by_country={})

        def note(kind, cand, extra=None):
            ex = rep['examples'].setdefault(kind, [])
            if len(ex) < 8:
                ex.append(dict(institution=cand['entry']['institution'], id=cand['entry']['id'],
                               title=(cand['entry'].get('title') or '')[:90], **(extra or {})))

        for cand in ADAPTERS[src['adapter']](src, d):
            rep['candidates'] += 1
            e = cand['entry']
            k = (e['institution'], renamed.get((e['institution'], e['id']), e['id']))
            if k in keys and (cand['logged'] or not cand['files']):
                # Already in the manifest, with its files (if any) in D's own download logs.
                rep['present'] += 1
                if src.get('verify_existing'):
                    old = manifest[keys[k]]
                    same = json.dumps(old, ensure_ascii=False) == json.dumps(e, ensure_ascii=False)
                    rep['present_identical' if same else 'present_differs'] += 1
                    if not same:
                        note('present_differs', cand, dict(fields=sorted(f for f in set(old) | set(e) if old.get(f) != e.get(f))))
                continue
            good, problems = [], []
            for f in cand['files']:
                status, info = store.check(f['path'], f.get('bytes'), f.get('sha256'))
                if status == 'ok':
                    good.append(dict(f, **info))
                else:
                    problems.append(status)
                    rep['file_problems'][status] = rep['file_problems'].get(status, 0) + 1
                    note(status, cand, dict(path=info.get('path')))
            complete = bool(good) and not problems  # every declared part present
            if k in keys:
                rep['present'] += 1
                lrow = logged.get(k)
                if complete and not cand['logged'] and (not lrow or lrow.get('status') != 'downloaded'):
                    if k not in rows:
                        rows[k] = ingest_row(k, src, good)
                        rep['present_ingest_logged' if k in previous else 'updated_file_added'] += 1
                        for f in good:
                            sha_owner.setdefault(f['sha256'], k)
                elif complete and not cand['logged']:
                    have = {f.get('sha256') for f in lrow.get('files', [])}
                    paths = {os.path.realpath(d / f['path']) for f in lrow.get('files', [])}
                    if all(os.path.realpath(f['path']) in paths for f in good):
                        rep['present_same_file'] += 1  # the source lists the very file D's log already records
                    elif any(f['sha256'] in have for f in good):
                        rep['present_second_copy_same_sha'] += 1
                    else:
                        rep['present_second_copy_other_sha'] += 1
                        note('present_second_copy_other_sha', cand)
                continue
            dup = next((sha_owner[f['sha256']] for f in good if f['sha256'] in sha_owner), None)
            if dup:
                rep['duplicate_sha'] += 1
                note('duplicate_sha', cand, dict(duplicate_of=list(dup)))
                continue
            dk = dedupe_key(e)
            y = entry_year(e)
            tdup = next((other for other, oy in by_title.get(dk, []) if y is None or oy is None or abs(y - oy) <= 1), None) if dk else None
            if tdup:
                rep['duplicate_title'] += 1
                note('duplicate_title', cand, dict(duplicate_of=list(tdup)))
                continue
            if not complete and not cand['closed']:
                continue  # an expected PDF is missing, incomplete or still downloading: reported above
            if not ingest:
                rep['new'] += 1
                rep['new_with_pdf'] += bool(good)
                rep['by_country'][e.get('country', 'CA')] = rep['by_country'].get(e.get('country', 'CA'), 0) + 1
                continue
            if e['id'] in id_owner and id_owner[e['id']] != e['institution']:
                renamed[(e['institution'], e['id'])] = new_id = f"{e['institution']}-{e['id']}"
                e = dict(e, id=new_id)
                k = (e['institution'], new_id)
                rep['id_namespaced'] += 1
            if good:
                e = dict(e, pdf_paths=[f['rel'] for f in good], ingest_source=name)
            else:
                e = dict(e, ingest_source=name)
            keys[k] = len(manifest) + len(appended)
            appended.append(e)
            id_owner[e['id']] = e['institution']
            if dk:
                by_title.setdefault(dk, []).append((k, y))
            rep['new'] += 1
            rep['by_institution'][e['institution']] = rep['by_institution'].get(e['institution'], 0) + 1
            rep['by_country'][e.get('country', 'CA')] = rep['by_country'].get(e.get('country', 'CA'), 0) + 1
            if good:
                rep['new_with_pdf'] += 1
                for f in good:
                    sha_owner.setdefault(f['sha256'], k)
                if not cand['logged']:
                    rows[k] = ingest_row(k, src, good)
    return manifest, appended, list(rows.values()), report


def ingest_row(k, src, files):
    multi = len(files) > 1
    return dict(institution=k[0], id=k[1], status='downloaded', source=f"dissertation_ingest:{src['name']}",
                checked_at=next((f['checked_at'] for f in files if f.get('checked_at')), None),
                files=[dict(name=f.get('name') or Path(f['rel']).name, path='pdf/' + f['rel'], bytes=f['bytes'],
                            sha256=f['sha256'], primary=i == 0, part=(f.get('part') or i + 1) if multi else None)
                       for i, f in enumerate(files)])


def write_outputs(d, manifest, appended, rows, report, dry_run):
    path = d / 'doctorates.json'
    original = path.read_text()
    text = json.dumps(manifest + appended, ensure_ascii=False, indent=1) + '\n'
    if appended:
        # Existing entries byte-identical and in order: the old text minus its closing ']' is a prefix.
        assert text.startswith(original.rstrip()[:-1].rstrip()), 'existing manifest entries would change'
    else:
        assert text == original, 'existing manifest entries would change'
    log_text = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    report.update(manifest_entries_before=len(manifest), manifest_entries_after=len(manifest) + len(appended),
                  appended=len(appended), ingest_log_rows=len(rows))
    if dry_run:
        return
    if text != original:
        tmp = path.with_suffix('.json.tmp')
        tmp.write_text(text)
        tmp.replace(path)
    lp = d / 'downloads-ingest.jsonl'
    if not lp.exists() or lp.read_text() != log_text:
        lp.write_text(log_text)


# ----------------------------------------------------------------------------- incremental processing


def extraction_jobs(d):
    """Primary files of manifest entries whose path is not yet in extraction.jsonl, or whose
    SHA-256 changed since extraction."""
    ids = {(e['institution'], e['id']) for e in json.loads((d / 'doctorates.json').read_text())}
    done = {}
    for x in read_jsonl(d / 'extraction.jsonl'):
        done[x['file']] = x.get('sha256')
    jobs = []
    for k, row in downloads_index(sorted(d.glob('downloads*.jsonl'))).items():
        if k not in ids or row.get('status') != 'downloaded':
            continue
        for f in row.get('files', []):
            if f.get('primary') and (f['path'] not in done or (done[f['path']] and f.get('sha256') and done[f['path']] != f['sha256'])):
                jobs.append(f['path'])
    return sorted(set(jobs))


def run_step(name, cmd, d, stamp, env=None):
    log = d / 'logs' / f'ingest-{stamp}-{name}.log'
    print(f'== {name}: {" ".join(map(str, cmd))} (log {log.relative_to(d)})', flush=True)
    t = time.time()
    with log.open('w') as fh:
        rc = subprocess.run(list(map(str, cmd)), stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
    print(f'   {name}: exit {rc} after {time.time() - t:.0f} s', flush=True)
    if rc:
        raise SystemExit(f'{name} failed (exit {rc}); see {log}')


def pipeline(d, args, stamp):
    py = sys.executable
    steps = args.steps
    if 'extract' in steps:
        jobs = extraction_jobs(d)
        jf = d / 'logs' / f'ingest-{stamp}-extract-jobs.txt'
        jf.write_text(''.join(j + '\n' for j in jobs))
        print(f'{len(jobs)} files to extract', flush=True)
        if jobs:
            env = dict(os.environ, TESSDATA_PREFIX=os.environ.get('TESSDATA_PREFIX', '/usr/share/tesseract-ocr/5/tessdata'))
            run_step('extract', [py, HERE / 'extract_dissertation_bibliographies.py', '--out', d, '--only-file', jf,
                                 '--workers', args.workers] + (['--ocr'] if args.ocr else []), d, stamp, env)
    build = [py, HERE / 'build_dissertation_citation_graph.py', '--out', d] + \
        (['--provisional-subgraph'] + args.provisional_subgraph if args.provisional_subgraph else [])
    if 'build' in steps:
        run_step('build-1', build, d, stamp)
    if 'link' in steps:
        run_step('link', [py, HERE / 'link_cited_works_to_authorities.py', '--out', d], d, stamp)
        run_step('build-2', build, d, stamp)
    if 'summaries' in steps:
        run_step('summaries', [py, HERE / 'dissertation_citation_summaries.py', '--out', d], d, stamp)
    if 'tfidf' in steps:
        with (d / 'graph.json').open() as f:
            meta = json.load(f)['meta']
        for country in [None] + meta.get('subgraphs', []):
            run_step(f'tfidf-{country or "main"}', [py, HERE / 'dissertation_tfidf_families.py', '--out', d]
                     + (['--country', country] if country else []), d, stamp)


def summarise(report):
    lines = []
    for name, r in report['sources'].items():
        lines.append(f"{name:14} {'ingest' if r['ingest'] else 'DRY  '} candidates {r['candidates']:6}  new {r['new']:5} "
                     f"(pdf {r['new_with_pdf']})  present {r['present']:5} (identical {r['present_identical']}, differs "
                     f"{r['present_differs']})  file added to existing {r['updated_file_added']}  already ingested {r['present_ingest_logged']}  "
                     f"same file {r['present_same_file']}  second copies "
                     f"{r['present_second_copy_same_sha']}+{r['present_second_copy_other_sha']}  dup sha {r['duplicate_sha']}  "
                     f"dup title {r['duplicate_title']}  file problems {r['file_problems'] or '-'}")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=D_DEFAULT, help='dissertation-citations directory (D)')
    ap.add_argument('--registry', type=Path, help='source registry (default <D>/ingest-sources.json)')
    ap.add_argument('--sources', nargs='*', help='only these sources (names in the registry)')
    ap.add_argument('--include-disabled', action='store_true', help='also ingest sources marked "ingest": false')
    ap.add_argument('--dry-run', action='store_true', help='report what would be added; write nothing but the report')
    ap.add_argument('--update', action='store_true', help='after merging, extract, build, link, rebuild, summaries, TF-IDF')
    ap.add_argument('--steps', nargs='*', default=['extract', 'build', 'link', 'summaries', 'tfidf'],
                    help='pipeline steps for --update (default all)')
    ap.add_argument('--settle-minutes', type=float, default=10, help='skip files modified more recently (still downloading)')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--no-ocr', dest='ocr', action='store_false')
    ap.add_argument('--provisional-subgraph', nargs='*', default=[], metavar='CC',
                    help='countries below the threshold to analyse as labelled first-pass sub-graphs')
    args = ap.parse_args()
    d = args.out.resolve()
    os.chdir(ROOT)  # harvest provenance (source_harvest) is recorded relative to the repository root
    (d / 'logs').mkdir(exist_ok=True)
    registry = json.loads((args.registry or d / 'ingest-sources.json').read_text())
    unknown = [s for s in args.sources or [] if s not in {x['name'] for x in registry['sources']}]
    if unknown:
        ap.error(f'unknown sources {unknown}')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    store = Store(d, args.settle_minutes, d / 'logs' / 'ingest-sha-cache.json')
    manifest, appended, rows, report = merge(d, registry['sources'], store, args.sources, args.include_disabled)
    store.save()
    write_outputs(d, manifest, appended, rows, report, args.dry_run)
    report.update(run_at=datetime.now(timezone.utc).isoformat(), dry_run=args.dry_run, sources_run=args.sources or 'all')
    rp = d / 'logs' / f"ingest-{stamp}{'-dry-run' if args.dry_run else ''}.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    if not args.dry_run:
        (d / 'logs' / 'ingest-latest.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    print(summarise(report))
    print(f"manifest {report['manifest_entries_before']} -> {report['manifest_entries_after']} entries "
          f"({'dry run, nothing written' if args.dry_run else 'written'}); report {rp.relative_to(d)}", flush=True)
    if args.update and not args.dry_run:
        pipeline(d, args, stamp)
        print('INGEST-UPDATE-OK', flush=True)


if __name__ == '__main__':
    main()
