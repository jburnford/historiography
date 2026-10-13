#!/usr/bin/env python3
"""Offline dating audit and explicitly illustrative abstract review of the pilot."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re


SAMPLE = [
    ('c9b8bcb5-caaf-4de6-b945-0dbc660c1d66', ['oral history', 'archival inquiry'], ['queer history', 'political history', 'legal history'], 'This study utilizes oral history from 25 interviews', 'Interview evidence combined with a liberation newspaper and community archives; author also names queer theory.'),
    ('fc4659d2-9532-4933-9ce8-77ca22ed0264', ['quantitative source comparison', 'archival inquiry'], ['food and consumption', 'labour history'], 'a new, quantitative analysis of medieval and early modern cookery collections', 'Cookery collections compared with household diet accounts; longue durée wording alone establishes no Annales affiliation.'),
    ('d399a5b7-a763-4ec8-8c49-37c7ecf66b51', ['intellectual history', 'biography', 'ethnohistory'], ['Indigenous histories'], 'This dissertation bridges intellectual history, biography, and ethnohistory', 'Author explicitly combines three approaches to Anishinaabe historical writing; subject matter establishes no author identity.'),
    ('ae9c30e2-a92f-4a7c-8d5d-932c441953e8', ['oral history', 'visual-source analysis', 'socio-cultural analysis'], ['medical history', 'racialization', 'public history'], 'personal photographs to oral history interviews to public history displays', 'The author identifies several evidence forms for Japanese-Canadian internment healthcare; public displays are also sources.'),
    ('b5bfa42a-91cd-48fd-adb2-c63eee116eee', ['feminist intellectual history', 'life-writing analysis'], ['women and gender', 'intellectual history'], 'methodologies of feminist intellectual history and feminist theory', 'Writings, correspondence and autobiographical reflections support an inquiry into feminist intellectual community.'),
    ('0ea5f759-fb1a-4709-9972-83cb74404c4e', ['oral history', 'archival inquiry'], ['Black history', 'women and gender', 'social history'], 'oral history interviews, church records, activist organization records, and newspapers', 'Multiple evidence forms examine Black Canadian community leadership; completion year remains unresolved in harvested dates.'),
    ('3302b5f4-f4af-4277-8548-ca0c4e5c98f0', ['policy history', 'oral history', 'public opinion polling'], ['international history', 'migration', 'labour', 'gender', 'ethnicity'], 'policy history, oral history, public opinion polling, gender, ethnicity and labour studies', 'Author names several methods and perspectives; the 2006 issued date is earlier than the collection name suggests.'),
    ('d6f5a8e9-d6b5-4831-a482-bcfd339aeeb8', ['archival inquiry', 'oral history'], ['transnational history', 'queer history', 'print and visual culture'], 'draws on archival sources and oral history interviews', 'Periodical production, circulation and reception connect archival and interview evidence across three countries.'),
    ('23d8d221-f11d-4e03-8ed3-134e795fefa2', ['oral history', 'life-history inquiry'], ['migration', 'refugees', 'identity'], 'Oral histories with Ugandan Asian refugees in Canada', 'Life histories situate refugee resettlement alongside policy and voluntary organizations.'),
    ('4a07fb32-51ad-4f96-a1fa-e2a3457cd193', ['comparative history', 'archival inquiry'], ['war history', 'empire', 'community and identity'], 'A comparative study of mobilization in Australia, Canada, and New Zealand', 'Community-based voluntary societies are the historical objects here; this wording does not establish community-based research methodology.'),
]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def review(metadata, out):
    if out.exists():
        assert not any(out.iterdir()), 'Output directory must be new or empty'
    else:
        out.mkdir(parents=True)
    summary = json.loads((metadata / 'summary.json').read_text())
    assert not summary['errors']
    # Unicode paragraph/line separators inside abstracts are valid JSON strings;
    # splitlines() would mistake them for JSONL record boundaries.
    with (metadata / 'records.jsonl').open() as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == summary['unique_records']
    assert len({(r['institution'], r['id']) for r in rows}) == len(rows)
    for req in json.loads((metadata / 'requests.json').read_text()):
        assert hashlib.sha256((metadata / req['file']).read_bytes()).hexdigest() == req['sha256']
    doctoral = [r for r in rows if r['degree_classification'] == 'doctoral' and r['history_metadata_exact']]
    assert len(doctoral) == summary['degree_counts']['doctoral']
    stats = []
    dated = []
    for inst in ['york', 'usask', 'queens', 'toronto', 'western']:
        subset = [r for r in doctoral if r['institution'] == inst]
        for r in subset:
            dates = [x['value'] for x in r['metadata'].get('dc.date.convocation', [])]
            years = sorted({int(d[:4]) for d in dates if re.match(r'^\d{4}', d)})
            dated.append(dict(institution=inst, id=r['id'], title=r['title'],
                              convocation_dates=dates, degree_year=years[0] if len(years) == 1 else None,
                              year_basis='explicit convocation metadata' if len(years) == 1 else 'requires adjudication',
                              issued_dates=r['issued_dates'], copyright_dates=r['copyright_dates'],
                              created_dates=r['created_dates'], submitted_dates=r['submitted_dates'],
                              accession_dates=r['accession_dates'], item_url=r['item_url']))
        stats.append(dict(institution=inst, doctoral_records=len(subset),
                          missing_abstracts=sum(not r['abstract'] for r in subset),
                          missing_issued_dates=sum(not r['issued_dates'] for r in subset),
                          explicit_convocation_dates=sum(bool(r['metadata'].get('dc.date.convocation')) for r in subset),
                          issued_equals_accession_day=sum(bool(r['issued_dates'] and r['accession_dates']) and r['issued_dates'][0][:10] == r['accession_dates'][0][:10] for r in subset),
                          issued_year_differs_from_copyright=sum(bool(r['issued_dates'] and r['copyright_dates']) and r['issued_dates'][0][:4] != r['copyright_dates'][0][:4] for r in subset)))
    write_json(out / 'date-audit.json', dict(institutions=stats, degree_dates=dated,
        rule='Only explicit convocation metadata supplies a degree year here. Other dates require source adjudication.'))
    by_id = {r['id']: r for r in doctoral}
    reviewed = []
    for rid, methods, topics, quote, interpretation in SAMPLE:
        r = by_id[rid]
        assert quote in ' '.join(r['abstract']), (rid, quote)
        assert len(quote.split()) <= 25
        reviewed.append(dict(institution=r['institution'], id=rid, title=r['title'],
            methods=methods, topics=topics, abstract_locator=quote, interpretation=interpretation,
            checked_scope='repository abstract only', item_url=r['item_url'],
            inference_limit='No full-text method, source sufficiency, author identity or influence claim accepted.'))
    assert Counter(r['institution'] for r in reviewed) == {k: 2 for k in ['york','usask','queens','toronto','western']}
    write_json(out / 'abstract-review.json', dict(selection='Two illustrative records per institution selected to examine explicitly named methods, not a random sample or a time series.',
        reviewer='single editorial review; independent second coding pending', records=reviewed))
    fields = ['institution', 'id', 'title', 'methods', 'topics', 'abstract_locator', 'item_url', 'checked_scope']
    with (out / 'abstract-review.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: '; '.join(r[k]) if isinstance(r[k], list) else r[k] for k in fields} for r in reviewed)
    write_json(out / 'validation.json', dict(unique_records=len(rows), strict_history_doctoral_records=len(doctoral),
        degree_counts=dict(Counter(r['degree_classification'] for r in rows)),
        raw_request_hashes_pass=True, duplicate_records=0, exact_history_metadata_pass=True,
        checked_abstracts=len(reviewed), exact_quote_locators_pass=True,
        metadata_sha256=hashlib.sha256((metadata / 'records.jsonl').read_bytes()).hexdigest(),
        graph_changed=False, classification_status='illustrative abstract review only; no trends estimated'))
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    review(args.metadata, args.out)
