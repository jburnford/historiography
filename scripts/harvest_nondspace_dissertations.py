#!/usr/bin/env python3
"""History doctorates from non-DSpace repositories: UQAM and Concordia (EPrints), SFU (Islandora) and UBC (cIRcle OAI-PMH).

Writes ``records.jsonl`` rows in the shape used by the DSpace harvests (doctoral
records only, with ``pdf_urls``) for ``fetch_dissertation_pdfs.py``. Public metadata
only; student e-mail identifiers in EPrints exports are dropped. Raw responses are
kept in ``raw/`` with SHA-256 hashes in ``requests.json``.

Concordia's server omits a TLS intermediate certificate: run with SSL_CERT_FILE set
to a bundle that includes GlobalSign's GCC R46 OV TLS CA 2025 intermediate.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

UA = 'HistoriographyCitationPilot/1.0 (bibliography research)'


class Fetcher:
    def __init__(self, out):
        self.out, self.log = out, []

    def __call__(self, url, name, timeout=150):
        with urlopen(Request(url, headers={'User-Agent': UA}), timeout=timeout) as response:
            body = response.read()
        (self.out / 'raw' / name).write_bytes(body)
        self.log.append(dict(url=url, file=f'raw/{name}', sha256=hashlib.sha256(body).hexdigest(),
                             checked_at=datetime.now(timezone.utc).isoformat()))
        time.sleep(1.1)
        return body


def row(institution, rid, title, authors, advisors, year, item_url, pdf_urls, scope, degree, language=None):
    return dict(institution=institution, id=str(rid), title=title, authors=authors, advisors=advisors,
                degree=[degree], degree_classification='doctoral', history_scope=scope,
                issued_dates=[str(year)] if year else [], graduation_dates=[], copyright_dates=[],
                language=[language] if language else [], item_url=item_url, pdf_urls=pdf_urls,
                fulltext_status='not individually checked')


def uqam(get):
    data = json.loads(get('https://archipel.uqam.ca/cgi/exportview/divisions/humaine8/JSON/humaine8.js', 'uqam-humaine8.json'))
    rows = []
    for e in data:
        if e.get('type') != 'thesis' or e.get('department') != 'Doctorat en histoire':
            continue
        pdfs = [f"https://archipel.uqam.ca/{e['eprintid']}/{d['pos']}/{d['main']}" for d in sorted(e.get('documents', []), key=lambda d: d.get('pos', 0))
                if d.get('security') == 'public' and 'pdf' in (d.get('format') or d.get('mime_type') or '')]
        names = [f"{c['name'].get('family', '')}, {c['name'].get('given', '')}".strip(', ') for c in e.get('creators', [])]
        advisors = [f"{c['name'].get('family', '')}, {c['name'].get('given', '')}".strip(', ')
                    for c in e.get('contributors', []) if 'advisor' in (c.get('type') or '').lower() and c.get('name')]
        rows.append(row('uqam', e['eprintid'], e.get('title'), names, advisors, str(e.get('date', ''))[:4],
                        f"https://archipel.uqam.ca/{e['eprintid']}/", pdfs, 'explicit_history_program_or_department',
                        'Doctorat en histoire', 'fre'))
    return rows


def concordia(get):
    ns = {'e': 'http://www.ndltd.org/standards/metadata/etdms/1.0/'}
    base = 'https://spectrum.library.concordia.ca'
    found = {}
    for url, name in [(f'{base}/cgi/exportview/divisions/dep=5Fhistory/ETD_MS/dep=5Fhistory.xml', 'concordia-history.xml'),
                      (f'{base}/cgi/exportview/document_subtype/thesis=5Fphd/ETD_MS/thesis=5Fphd.xml', 'concordia-phd.xml')]:
        tree = ET.fromstring(get(url, name, timeout=300))
        for rec in tree.iter('{http://www.ndltd.org/standards/metadata/etdms/1.0/}thesis'):
            level = rec.findtext('e:degree/e:level', '', ns).strip().lower()
            dname = rec.findtext('e:degree/e:name', '', ns).strip()
            disc = rec.findtext('e:degree/e:discipline', '', ns).strip()
            if level != 'phd' or disc not in ('History', 'Dept. of History'):
                continue
            ids = [i.text for i in rec.findall('e:identifier', ns) if i.text]
            item = next((i for i in ids if re.search(r'/id/eprint/\d+/?$', i)), None) or \
                next((re.sub(r'(/id/eprint/\d+)/.*', r'\1/', i) for i in ids if '/id/eprint/' in i), None)
            rid = re.search(r'/eprint/(\d+)', item or '').group(1)
            found[rid] = row('concordia', rid, rec.findtext('e:title', '', ns), [c.text for c in rec.findall('e:creator', ns) if c.text],
                             [c.text for c in rec.findall('e:contributor', ns) if c.text], rec.findtext('e:date', '', ns)[:4],
                             item, [i for i in ids if i.lower().endswith('.pdf')], 'explicit_history_program_or_department',
                             dname, rec.findtext('e:language', '', ns) or None)
    return list(found.values())


def sfu(get):
    nids = []
    for page in range(10):
        body = get(f'https://summit.sfu.ca/collection/30027?page={page}', f'sfu-collection-{page:02}.html').decode('utf-8', 'replace')
        new = [n for n in dict.fromkeys(re.findall(r'href="/item/(\d+)"', body)) if n not in nids]
        if not new:
            break
        nids += new
    rows = []
    for nid in nids:
        item = json.loads(get(f'https://summit.sfu.ca/item/{nid}?_format=json', f'sfu-item-{nid}.json'))
        thesis_type = ' '.join(v.get('value', '') for v in item.get('field_sfu_thesis_type', []))
        if not re.search(r'Ph\.?\s?D', thesis_type):
            continue
        page = get(f'https://summit.sfu.ca/item/{nid}', f'sfu-item-{nid}.html').decode('utf-8', 'replace')
        meta = lambda name: [html.unescape(m) for m in re.findall(rf'<meta name="{name}" content="([^"]*)"', page)]
        date = ' '.join(v.get('value', '') for v in item.get('field_edtf_date_created', []))
        rows.append(row('sfu', nid, ' '.join(v.get('value', '') for v in item.get('title', [])), meta('citation_author'), [],
                        date[:4], f'https://summit.sfu.ca/item/{nid}', meta('citation_pdf_url'),
                        'explicit_history_program_or_department', thesis_type))
    return rows


def ubc_page(get, url, name):
    """One cIRcle OAI page: reuse a valid saved page (its resumption token continues the
    harvest); otherwise fetch slowly, backing off on cIRcle's throttling (empty bodies, timeouts)."""
    saved = get.out / 'raw' / name
    if saved.exists() and saved.stat().st_size > 0:
        try:
            return ET.fromstring(saved.read_bytes())
        except ET.ParseError:
            pass
    for wait in (0, 60, 120, 300, 600, 900):
        time.sleep(wait)
        try:
            body = get(url, name, timeout=300)
            if body.strip():
                tree = ET.fromstring(body)
                time.sleep(4)  # cIRcle throttles after a few hundred quick requests
                return tree
        except Exception as exc:  # timeout, reset or unparseable body: back off and retry
            print(f'ubc: {name}: {type(exc).__name__}; retrying', flush=True)
    raise RuntimeError(f'cIRcle did not return {name} after repeated back-off')


def ubc(get):
    """cIRcle OAI-PMH (ETDMS): theses 2008+ and the 1919–2007 retrospective set; doctoral, discipline History."""
    ns = {'o': 'http://www.openarchives.org/OAI/2.0/', 'e': 'http://www.ndltd.org/standards/metadata/etdms/1.0/'}
    base = 'https://circle.library.ubc.ca/oai/request'
    rows, scanned = [], 0
    for set_spec in ('col_2429_24', 'col_2429_831'):
        params = f'verb=ListRecords&metadataPrefix=oai_etdms&set={set_spec}'
        for page in range(2000):
            tree = ubc_page(get, f'{base}?{params}', f'ubc-{set_spec}-{page:04}.xml')
            for rec in tree.iter('{http://www.openarchives.org/OAI/2.0/}record'):
                header = rec.find('o:header', ns)
                if header.get('status') == 'deleted':
                    continue
                scanned += 1
                t = rec.find('.//e:thesis', ns)
                if t is None:
                    continue
                level = (t.findtext('e:degree/e:level', '', ns) or '').strip().lower()
                name = (t.findtext('e:degree/e:name', '', ns) or '').strip()
                disc = [d.text.strip() for d in t.findall('e:degree/e:discipline', ns) if d.text]
                if not (level == 'doctoral' or 'Doctor of Philosophy' in name) or 'History' not in disc:
                    continue
                ids = [i.text for i in t.findall('e:identifier', ns) if i.text]
                rid = header.findtext('o:identifier', '', ns).rsplit(':', 1)[-1]
                rows.append(row('ubc', rid.replace('/', '_'), t.findtext('e:title', '', ns),
                                [c.text for c in t.findall('e:creator', ns) if c.text],
                                [c.text for c in t.findall('e:contributor', ns) if c.text],
                                (t.findtext('e:date', '', ns) or '')[:4],
                                next((i for i in ids if 'hdl.handle.net' in i), None),
                                [i for i in ids if i.lower().endswith('.pdf')],
                                'explicit_history_program_or_department', name, t.findtext('e:language', '', ns) or None))
            token = tree.find('.//o:resumptionToken', ns)
            if token is None or not (token.text or '').strip():
                break
            params = f'verb=ListRecords&resumptionToken={token.text.strip()}'
    print(f'ubc: scanned {scanned} theses, {len(rows)} History doctorates', flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sources', nargs='+', default=['uqam', 'concordia', 'sfu'])
    args = parser.parse_args()
    (args.out / 'raw').mkdir(parents=True, exist_ok=True)
    get = Fetcher(args.out)
    rows, errors = [], []
    for source in args.sources:
        try:
            got = globals()[source](get)
            print(source, len(got), flush=True)
            rows += got
        except Exception as exc:
            errors.append(dict(source=source, error=f'{type(exc).__name__}: {exc}'))
            print(errors[-1], flush=True)
    with (args.out / 'records.jsonl').open('w') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    (args.out / 'requests.json').write_text(json.dumps(get.log, indent=1) + '\n')
    (args.out / 'summary.json').write_text(json.dumps(dict(checked_at=datetime.now(timezone.utc).isoformat(), errors=errors,
        counts={s: sum(r['institution'] == s for r in rows) for s in args.sources}), indent=1) + '\n')


if __name__ == '__main__':
    main()
