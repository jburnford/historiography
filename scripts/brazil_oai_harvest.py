#!/usr/bin/env python3
"""Harvest Dublin Core records of History theses from Brazilian university repositories (OAI-PMH).

Brazil expansion, 2026-11-01. The CAPES catalogue (``capes_catalogue_harvest.py``) lists every
History doctorate with its advisor, but its full-text links point to Sucupira, whose robots.txt
disallows everything. The PDFs are taken from the universities' own repositories instead: this
script harvests their History collections over OAI-PMH (the protocol meant for harvesting), and
``brazil_match_capes.py`` matches the records to CAPES doctorates by author and title. Each OAI
base is checked against its host's robots.txt at run time and skipped if disallowed.

USP is not here: teses.usp.br's robots.txt has ``Disallow: /oai``. A USP FFLCH harvest was started
by mistake on 2026-11-01 (the first check read www.teses.usp.br, whose robots.txt is a redirect
page) and stopped; its records are not used. USP is reached through its sitemap and item pages.

``REPOS`` names each repository's OAI base and the sets (collections) that hold History theses,
found with ListSets on 2026-11-01. Output: ``<out>/oai/<INST>.jsonl``, one record per line
(header identifier, datestamp, sets, and every ``dc:`` element as a list). A finished set is
recorded in ``<out>/oai/done.json`` and skipped on a rerun.

    python3 scripts/brazil_oai_harvest.py --out data/field-research/brazil-theses-2026-10-31
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = 'historiography-research/1.0 (University of Saskatchewan; jic823@usask.ca)'
NS = {'o': 'http://www.openarchives.org/OAI/2.0/', 'dc': 'http://purl.org/dc/elements/1.1/'}
REPOS = {
    'UFRJ': ('https://pantheon.ufrj.br/oai/request', ['col_11422_12271', 'col_11422_66', 'col_11422_67', 'col_11422_112']),
    'UFMG': ('https://repositorio.ufmg.br/server/oai/request', ['col_1843_292']),
    'UERJ': ('https://www.bdtd.uerj.br:8443/oai/request', ['col_1_3597', 'col_1_3640']),
    'UFU': ('https://repositorio.ufu.br/oai/request', ['col_123456789_5500']),
    'UFPA': ('https://repositorio.ufpa.br/server/oai/request', ['col_2011_6869', 'col_2011_9590']),
    'FGV': ('https://repositorio.fgv.br/server/oai/request', ['col_10438_8686']),
    'UFES': ('https://repositorio.ufes.br/server/oai/request', ['col_10_17522']),
    'UFPE': ('https://repositorio.ufpe.br/oai/request', ['col_123456789_314']),
}


def get(url, tries=6):
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e:
            print(f'  retry {attempt}: {e!r}'[:200], file=sys.stderr, flush=True)
            time.sleep(30 * attempt)
    raise IOError(f'gave up: {url}')


def robots_rules(body):
    """(allow, path pattern) rules of the ``User-agent: *`` groups."""
    rules, agents, in_rules = [], [], False
    for line in body.splitlines():
        line = line.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        key, val = (s.strip() for s in line.split(':', 1))
        key = key.lower()
        if key == 'user-agent':
            if in_rules:
                agents, in_rules = [], False
            agents.append(val)
        elif key in ('allow', 'disallow'):
            in_rules = True
            if '*' in agents and val:
                rules.append((key == 'allow', val))
    return rules


def robots_allows(url):
    """RFC 9309 matching (the longest matching rule wins, Allow on a tie), not urllib.robotparser,
    which takes the first match: teses.usp.br lists ``Allow: /`` before ``Disallow: /oai``.
    A missing robots.txt allows."""
    parts = urllib.parse.urlsplit(url)
    try:
        body = get(f'{parts.scheme}://{parts.netloc}/robots.txt', tries=2).decode('utf-8', 'replace')
    except Exception:
        return True
    if '<html' in body.lower():
        return True
    path = parts.path or '/'
    best = (-1, True)
    for allow, pat in robots_rules(body):
        rx = '^' + re.escape(pat).replace(r'\*', '.*').replace(r'\$', '$')
        if re.match(rx, path) and (len(pat) > best[0] or (len(pat) == best[0] and allow)):
            best = (len(pat), allow)
    return best[1]


def records(base, oai_set, delay):
    url = f'{base}?verb=ListRecords&metadataPrefix=oai_dc&set={urllib.parse.quote(oai_set)}'
    while url:
        x = ET.fromstring(get(url))
        err = x.find('o:error', NS)
        if err is not None:
            if err.get('code') == 'noRecordsMatch':
                return
            raise IOError(f'OAI error {err.get("code")}: {err.text}')
        for r in x.iterfind('.//o:record', NS):
            h = r.find('o:header', NS)
            if h.get('status') == 'deleted':
                continue
            dc = {}
            for el in r.iterfind('.//o:metadata/*/*', NS):
                tag = el.tag.split('}')[-1]
                if el.text and el.text.strip():
                    dc.setdefault(tag, []).append(el.text.strip())
            yield dict(identifier=h.findtext('o:identifier', '', NS), datestamp=h.findtext('o:datestamp', '', NS),
                       sets=[s.text for s in h.iterfind('o:setSpec', NS)], dc=dc)
        tok = x.find('.//o:resumptionToken', NS)
        url = (f'{base}?verb=ListRecords&resumptionToken={urllib.parse.quote(tok.text)}'
               if tok is not None and tok.text else None)
        time.sleep(delay)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--delay', type=float, default=2.0)
    a = ap.parse_args()
    out = Path(a.out) / 'oai'
    out.mkdir(parents=True, exist_ok=True)
    done_path = out / 'done.json'
    done = json.loads(done_path.read_text()) if done_path.exists() else {}
    for inst, (base, sets) in REPOS.items():
        if a.only and inst not in a.only:
            continue
        if not robots_allows(base):
            print(f'{inst}: robots.txt disallows {base}; skipped', flush=True)
            continue
        for s in sets:
            key = f'{inst}:{s}'
            if key in done:
                continue
            part = out / f'{inst}.{s}.jsonl.part'
            n = 0
            try:
                with open(part, 'w', encoding='utf-8') as f:
                    for rec in records(base, s, a.delay):
                        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                        n += 1
            except Exception as e:
                print(f'{key} FAILED after {n}: {e!r}'[:300], flush=True)
                continue
            with open(out / f'{inst}.jsonl', 'a', encoding='utf-8') as f:
                f.write(part.read_text(encoding='utf-8'))
            part.unlink()
            done[key] = n
            done_path.write_text(json.dumps(done, indent=1))
            print(f'{key} {n} records', flush=True)
    print('OAI-HARVEST-DONE', flush=True)


if __name__ == '__main__':
    main()
