#!/usr/bin/env python3
"""Harvest the History rows of the CAPES thesis catalogue (Catálogo de Teses e Dissertações - Brasil).

Brazil expansion, 2026-10-31 (user: "start the catalog; I'll figure out space"). CAPES publishes
the national catalogue of defended theses and dissertations as open data on
dadosabertos.capes.gov.br, one CSV per year (1987-2024), each up to ~500 MB. Each file is streamed
and filtered in memory; only History rows are written, so the harvest needs almost no disk.

A row is kept when its knowledge area or evaluation area is History (``AreaConhecimento`` /
``AreaAvaliacao`` before 2013, ``NM_AREA_CONHECIMENTO`` / ``NM_AREA_AVALIACAO`` from 2013) or its
programme name contains "HISTÓRIA". All degree levels are kept (doctorates are selected
downstream). Two column schemas exist: 1987-2012 (``Nivel``, ``Orientador_1``...) and 2013-2024
(``NM_GRAU_ACADEMICO``, ``NM_ORIENTADOR``, ``ID_PESSOA_ORIENTADOR``); the raw row is kept as is.

Output: ``<out>/capes-raw/<year>[-n].jsonl`` (one per resource) and ``<out>/capes-raw/harvest-log.jsonl``,
kept out of git (169 MB with abstracts); ``brazil_slim_capes.py`` writes the committed doctorate-only
copy to ``<out>/capes/``.
A finished resource is written to ``.part`` then renamed, so a rerun skips it. Files come from
the CKAN API (package_search), so new yearly releases are picked up.

Never use the full-text links (``URLTextoCompleto`` / ``DS_URL_TEXTO_COMPLETO``) to sucupira.capes.gov.br:
its robots.txt disallows everything.

    python3 scripts/capes_catalogue_harvest.py --out data/field-research/brazil-theses-2026-10-31
"""
import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = 'https://dadosabertos.capes.gov.br/api/3/action/package_search?q=teses%20dissertacoes&rows=50'
UA = 'historiography-research/1.0 (University of Saskatchewan; jic823@usask.ca)'
AREA_COLS = ('AreaConhecimento', 'AreaAvaliacao', 'NM_AREA_CONHECIMENTO', 'NM_AREA_AVALIACAO')
PROG_COLS = ('NomePrograma', 'NM_PROGRAMA')
csv.field_size_limit(10 ** 9)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def is_history(row):
    for c in AREA_COLS:
        v = (row.get(c) or '').strip().upper()
        if v in ('HISTÓRIA', 'HISTORIA'):
            return True
    return any('HISTÓRIA' in (row.get(c) or '').upper() or 'HISTORIA' in (row.get(c) or '').upper()
               for c in PROG_COLS)


def resources():
    """(package name, resource name, url) for every catalogue CSV, oldest package first."""
    req = urllib.request.Request(API, headers={'User-Agent': UA})
    pkgs = json.load(urllib.request.urlopen(req, timeout=120))['result']['results']
    out = []
    for p in pkgs:
        if 'catalogo' not in p['name']:
            continue
        for r in p['resources']:
            if (r.get('format') or '').upper() == 'CSV':
                out.append((p['name'], r['name'], r['url']))
    return sorted(out, key=lambda t: t[2])


def label(url):
    """Output stem from the file name: dados_1987.csv -> 1987, ..._2013.csv -> 2013, br-capes-btd-2017-... -> 2017."""
    name = url.rsplit('/', 1)[-1].lower()
    m = re.search(r'_((?:19|20)\d\d)\.csv$', name) or re.search(r'btd-((?:19|20)\d\d)-', name)
    return m.group(1) if m else name.replace('.csv', '')


class Counted(io.RawIOBase):
    """Byte-counting wrapper around the HTTP response, so a truncated stream can be detected."""

    def __init__(self, raw):
        self.raw, self.bytes = raw, 0

    def readable(self):
        return True

    def readinto(self, b):
        data = self.raw.read(len(b))
        self.bytes += len(data)
        b[:len(data)] = data
        return len(data)


def harvest(url, dest, log):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    t0 = time.time()
    n = k = 0
    part = dest.with_suffix('.jsonl.part')
    with urllib.request.urlopen(req, timeout=300) as resp, open(part, 'w', encoding='utf-8') as f:
        expected = int(resp.headers.get('Content-Length') or 0)
        counted = Counted(resp)
        src = io.TextIOWrapper(io.BufferedReader(counted), encoding='cp1252', errors='replace', newline='')
        for row in csv.DictReader(src, delimiter=';'):
            n += 1
            if is_history(row):
                k += 1
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
    # The server can drop a connection mid-file and the stream then just ends (2022 stopped at
    # 9,977 of ~90k rows on 2026-11-01); a short read is a failure, not the end of the file.
    if expected and counted.bytes != expected:
        part.unlink()
        raise IOError(f'short read: {counted.bytes} of {expected} bytes after {n} rows')
    part.rename(dest)
    rec = dict(url=url, file=dest.name, rows=n, history_rows=k, bytes=counted.bytes, expected_bytes=expected or None,
               seconds=round(time.time() - t0), finished=now())
    log.write(json.dumps(rec) + '\n')
    log.flush()
    print(json.dumps(rec), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--retries', type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out) / 'capes-raw'
    out.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 31):  # the CAPES portal goes unresponsive for stretches; wait it out
        try:
            res = resources()
            break
        except Exception as e:
            print(json.dumps(dict(stage='resources', attempt=attempt, error=repr(e)[:300], at=now())), file=sys.stderr, flush=True)
            time.sleep(300)
    else:
        sys.exit('CAPES API unreachable')
    print(f'{len(res)} CSV resources', flush=True)
    seen = {}
    with open(out / 'harvest-log.jsonl', 'a', encoding='utf-8') as log:
        for pkg, name, url in res:
            stem = label(url)
            seen[stem] = seen.get(stem, 0) + 1
            if seen[stem] > 1:
                stem = f'{stem}-{seen[stem]}'
            dest = out / f'{stem}.jsonl'
            if dest.exists():
                continue
            for attempt in range(1, a.retries + 1):
                try:
                    harvest(url, dest, log)
                    break
                except Exception as e:  # network drops on a slow server: retry the whole file
                    err = dict(url=url, file=dest.name, attempt=attempt, error=repr(e)[:300], at=now())
                    log.write(json.dumps(err) + '\n')
                    log.flush()
                    print(json.dumps(err), file=sys.stderr, flush=True)
                    time.sleep(min(120 * attempt, 900))
    print('CAPES-HARVEST-DONE', flush=True)


if __name__ == '__main__':
    main()
