#!/usr/bin/env python3
"""Harvest doctoral thesis records from Mexican OAI-PMH repositories (2026-11-04).

The user asked for Mexico on 2026-11-04 ("start mexico"). Mexico has no national thesis catalogue like
Brazil's CAPES, so the History screen is built from each repository's own records. This script keeps every
record that names a doctorate (dc:type or dc:description), in any field; the History screen runs later on
the saved records.

    python3 scripts/harvest_mexico_oai.py unam        # one source, resumable
    python3 scripts/harvest_mexico_oai.py --list

Output: data/field-research/mexico-theses-2026-11-04/oai/<source>.jsonl (one record per line) and
<source>.state.json (the next resumption token, pages and record counts). Rerunning resumes from the token;
a source whose last page is done is skipped. robots.txt was checked by hand for each host (longest match)
and the OAI paths are allowed. One request every DELAY seconds, with the contact address in the user agent.
"""
import argparse
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/mexico-theses-2026-11-04/oai'
UA = 'historiography-research/0.1 (jic823@usask.ca; dissertation citation study)'
DELAY = 2.0
CTX = ssl.create_default_context(cafile=certifi.where())

# source -> (OAI base URL, set or None, metadataPrefix[, seconds between requests]).
# UNAM's Identify names /oai/request as the base URL, but that path answers 400; /oai works.
SOURCES = {
    'unam': ('https://repositorio.unam.mx/oai', 'TesiUNAM', 'oai_dc'),
    'ciesas': ('https://repositorio.ciesas.edu.mx/oai/request', None, 'oai_dc'),
    'mora': ('https://mora.repositorioinstitucional.mx/oai/request', None, 'oai_dc'),
    'inah': ('https://repositorio.inah.gob.mx/oai/request', None, 'oai_dc'),
    'ibero': ('https://ri.ibero.mx/server/oai/request', None, 'oai_dc', 2.0),  # robots Crawl-delay 2
    'colmich': ('https://colmich.repositorioinstitucional.mx/oai/request', None, 'oai_dc'),
    'colsan': ('https://colsan.repositorioinstitucional.mx/oai/request', None, 'oai_dc'),
    'udg': ('https://riudg.udg.mx/oai/request', None, 'oai_dc'),
    'buap': ('https://repositorioinstitucional.buap.mx/oai/request', None, 'oai_dc'),
    'uv': ('https://cdigital.uv.mx/server/oai/request', None, 'oai_dc', 20.0),  # robots Crawl-delay 20
}

NS = {'oai': 'http://www.openarchives.org/OAI/2.0/', 'dc': 'http://purl.org/dc/elements/1.1/'}
DOCTORAL = re.compile(r'doctor|phd|ph\.d', re.I)


class PageFailed(Exception):
    """A page that keeps answering 5xx (one bad record can break a whole UNAM page)."""


def fetch(url, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            code = getattr(e, 'code', None)
            if code and code < 500 and code != 429:
                raise
            if attempt == tries - 1:
                raise PageFailed(f'{e!r} on {url}') from e
            wait = 30 * (attempt + 1)
            print(f'  {e!r}; retry in {wait} s', file=sys.stderr, flush=True)
            time.sleep(wait)


def one_by_one(base, prefix, token, delay):
    """A ListRecords page that keeps failing: list its identifiers and fetch each record by GetRecord.
    Returns the records, the next token and the identifiers that still fail."""
    page = ET.fromstring(fetch(f"{base}?{urllib.parse.urlencode({'verb': 'ListIdentifiers', 'resumptionToken': token})}"))
    ids = [h.findtext('oai:identifier', '', NS) for h in page.iterfind('.//oai:header', NS) if h.get('status') != 'deleted']
    tok = page.find('.//oai:resumptionToken', NS)
    nxt = tok.text.strip() if tok is not None and tok.text and tok.text.strip() else None
    recs, failed = [], []
    for i in ids:
        time.sleep(delay)
        try:
            recs += records(fetch(f"{base}?{urllib.parse.urlencode({'verb': 'GetRecord', 'identifier': i, 'metadataPrefix': prefix})}", tries=2))[0]
        except (PageFailed, SystemExit):  # SystemExit: an OAI error for this one id (UdG: idDoesNotExist)
            failed.append(i)
    return recs, nxt, failed


def records(page):
    root = ET.fromstring(page)
    err = root.find('oai:error', NS)
    if err is not None:
        if err.get('code') == 'noRecordsMatch':
            return [], None, None
        raise SystemExit(f"OAI error {err.get('code')}: {err.text}")
    out = []
    for rec in root.iterfind('.//oai:record', NS):
        header = rec.find('oai:header', NS)
        if header is None or header.get('status') == 'deleted':
            continue
        dc = rec.find('.//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
        fields = {}
        if dc is not None:
            for el in dc:
                tag = el.tag.rsplit('}', 1)[-1]
                if el.text and el.text.strip():
                    fields.setdefault(tag, []).append(el.text.strip())
        out.append({'oai_id': header.findtext('oai:identifier', '', NS),
                    'datestamp': header.findtext('oai:datestamp', '', NS),
                    'sets': [s.text for s in header.iterfind('oai:setSpec', NS)], **fields})
    tok = root.find('.//oai:resumptionToken', NS)
    token = tok.text.strip() if tok is not None and tok.text and tok.text.strip() else None
    size = tok.get('completeListSize') if tok is not None else None
    return out, token, size


def harvest(source):
    base, oai_set, prefix, *rest = SOURCES[source]
    delay = rest[0] if rest else DELAY
    OUT.mkdir(parents=True, exist_ok=True)
    state_path, data_path = OUT / f'{source}.state.json', OUT / f'{source}.jsonl'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'token': None, 'pages': 0, 'seen': 0, 'kept': 0}
    if state.get('done'):
        print(f'{source}: already complete ({state["kept"]} doctoral of {state["seen"]})')
        return
    with data_path.open('a', encoding='utf-8') as out:
        while True:
            if state['token']:
                q = {'verb': 'ListRecords', 'resumptionToken': state['token']}
            else:
                q = {'verb': 'ListRecords', 'metadataPrefix': prefix, **({'set': oai_set} if oai_set else {})}
            try:
                recs, token, size = records(fetch(f'{base}?{urllib.parse.urlencode(q)}'))
            except PageFailed as e:
                if not state['token']:
                    raise
                print(f'  page failed ({e}); fetching its records one by one', file=sys.stderr, flush=True)
                recs, token, failed = one_by_one(base, prefix, state['token'], delay)
                size = None
                state.setdefault('failed_ids', []).extend(failed)
                print(f'  {len(recs)} records recovered, {len(failed)} failed: {failed}', file=sys.stderr, flush=True)
            kept = [r for r in recs if any(DOCTORAL.search(v) for v in r.get('type', []) + r.get('description', []))]
            for r in kept:
                out.write(json.dumps(r, ensure_ascii=False) + '\n')
            out.flush()
            state.update(token=token, pages=state['pages'] + 1, seen=state['seen'] + len(recs),
                         kept=state['kept'] + len(kept), size=size or state.get('size'))
            state['done'] = token is None
            state_path.write_text(json.dumps(state, indent=1))
            if state['pages'] % 25 == 0 or token is None:
                print(f"{time.strftime('%H:%M:%S')} {source}: page {state['pages']}, {state['seen']} seen of "
                      f"{state.get('size')}, {state['kept']} doctoral", flush=True)
            if token is None:
                return
            time.sleep(delay)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('sources', nargs='*')
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()
    if args.list or not args.sources:
        for s, (base, oai_set, prefix, *rest) in SOURCES.items():
            print(s, base, oai_set or '(all)', prefix, rest[0] if rest else DELAY)
        return
    for s in args.sources:
        harvest(s)


if __name__ == '__main__':
    main()
