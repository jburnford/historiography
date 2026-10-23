#!/usr/bin/env python3
"""Build the public release of the History PhD citation graph.

User (2026-10-23): make the knowledge graph public. The release holds derived bibliographic
metadata only: which thesis cites which work, with parsed fields (author, title, year, kind).
No text from the theses is included: no raw bibliography or note strings, no PDFs, no full text.

Reads ``graph.json``, ``cited-people.csv`` and ``work-translations.jsonl`` from the dissertation
folder (``graph.json`` needs about 11 GB of memory: run it alone) and writes
``release/<date>/``:

- ``dissertations.csv.gz``  every dissertation record in the graph
- ``works.csv.gz``          every cited work, with citing counts by region
- ``people.csv.gz``         cited people (name keys), with Wikidata QIDs where grounded
- ``citations.csv.gz``      dissertation -> work citations (from bibliographies or notes)
- ``authorship.csv.gz``     person -> work (authors of cited works, in order)
- ``work-translations.csv`` translations and editions merged through Wikidata
- ``pages/``                the comparison and network pages
- ``README.md``             data dictionary, method, measured quality, provenance and licence
- ``SHA256SUMS``

The release directory is gitignored; it is meant for a data repository with a DOI.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_layout import region  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
REGIONS = ['CA', 'US', 'FR', 'EU', 'OTHER']


def writer(path, header):
    f = gzip.open(path, 'wt', newline='', encoding='utf-8') if path.suffix == '.gz' else path.open('w', newline='', encoding='utf-8')
    w = csv.writer(f)
    w.writerow(header)
    return f, w


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', default=date.today().isoformat())
    args = ap.parse_args()
    out = D / 'release' / args.version
    out.mkdir(parents=True, exist_ok=True)
    g = json.load((D / 'graph.json').open())
    meta = g['meta']
    diss = {n['id']: n for n in g['nodes'] if n['type'] == 'Dissertation'}
    strict_region = {k: region(n.get('country')) for k, n in diss.items() if n.get('in_analysis')}
    out_deg = Counter(e['source'] for e in g['edges'] if e['type'] == 'CITES')

    f, w = writer(out / 'dissertations.csv.gz', ['dissertation_id', 'institution', 'country', 'year', 'title', 'authors', 'advisors',
                                                  'eligibility', 'in_analysis', 'bibliography_source', 'extraction_status',
                                                  'cited_works', 'item_url'])
    source = {'parsed': 'bibliography', 'parsed_notes': 'notes'}
    for k, n in diss.items():
        w.writerow([k[2:], n['institution'], n.get('country'), n.get('year'), n.get('title'), '; '.join(n.get('authors') or []),
                    '; '.join(n.get('advisors') or []), n.get('eligibility'), n.get('in_analysis'),
                    source.get(n.get('extraction_status'), 'none') if n.get('cites_counted') else 'none',
                    n.get('extraction_status'), out_deg.get(k, 0), n.get('item_url')])
    f.close()

    by_region = defaultdict(Counter)
    f, w = writer(out / 'citations.csv.gz', ['dissertation_id', 'work_id', 'via', 'section_side', 'kind', 'note_citations'])
    for e in g['edges']:
        if e['type'] != 'CITES':
            continue
        w.writerow([e['source'][2:], e['target'], e.get('via', 'bibliography'), e.get('side'), e.get('kind'), e.get('citations') or ''])
        if e['source'] in strict_region:
            by_region[e['target']][strict_region[e['source']]] += 1
    f.close()

    translations = {}
    if (D / 'work-translations.jsonl').exists():
        for line in (D / 'work-translations.jsonl').open():
            r = json.loads(line)
            translations[r['canonical']] = r['work_qid']
    first = {}
    f, w = writer(out / 'authorship.csv.gz', ['person_key', 'work_id', 'position'])
    pos = Counter()
    for e in g['edges']:
        if e['type'] == 'AUTHORED':
            pos[e['target']] += 1
            w.writerow([e['source'][2:], e['target'], pos[e['target']]])
            first.setdefault(e['target'], e['source'])
    f.close()
    names = {n['id']: n.get('name') for n in g['nodes'] if n['type'] == 'Person'}
    f, w = writer(out / 'works.csv.gz', ['work_id', 'title', 'year', 'kind', 'container', 'first_author_key', 'first_author',
                                          'cited_by_strict_phds'] + [f'cited_by_{r}' for r in REGIONS] + ['cited_by_all_records',
                                                                                                          'wikidata_work'])
    for n in g['nodes']:
        if n['type'] != 'Work':
            continue
        c = by_region.get(n['id'], Counter())
        kind = n.get('kind') if isinstance(n.get('kind'), str) else (max(n['kinds'], key=n['kinds'].get) if n.get('kinds') else '')
        w.writerow([n['id'], n.get('title'), n.get('year'), kind, n.get('container') or '', (first.get(n['id']) or '')[2:],
                    names.get(first.get(n['id'])) or '', sum(c.values())] + [c.get(r, 0) for r in REGIONS]
                   + [n.get('cited_by_all', ''), translations.get(n['id'], '')])
    f.close()
    del g

    keep = ['person_key', 'name', 'cited_by_dissertations', 'cited_by_all', 'qid', 'qid_basis']
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as src:
        f, w = writer(out / 'people.csv.gz', keep)
        for r in csv.DictReader(src):
            w.writerow([r.get(k, '') for k in keep])
        f.close()
    with (out / 'work-translations.csv').open('w', newline='', encoding='utf-8') as fh:
        tw = csv.writer(fh)
        tw.writerow(['work_id', 'canonical_work_id', 'wikidata_work', 'wikidata_author', 'title'])
        for line in (D / 'work-translations.jsonl').open():
            r = json.loads(line)
            tw.writerow([r['work_id'], r['canonical'], r['work_qid'], r['author_qid'], r['title']])
    pages = out / 'pages'
    pages.mkdir(exist_ok=True)
    for name in ('network.html', 'europe-ca-us.html', 'ca-us.html', 'network-full.html'):
        if (D / 'summary' / 'comparisons' / name).exists():
            shutil.copy2(D / 'summary' / 'comparisons' / name, pages / name)
    (out / 'README.md').write_text(readme(meta, args.version), encoding='utf-8')
    (out / 'LICENSE').write_text(LICENCE, encoding='utf-8')
    with (out / 'SHA256SUMS').open('w') as fh:
        for p in sorted(out.rglob('*')):
            if p.is_file() and p.name != 'SHA256SUMS':
                fh.write(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}\n')
    for p in sorted(out.rglob('*')):
        if p.is_file():
            print(f'{p.relative_to(out)}  {p.stat().st_size / 1e6:.1f} MB')


LICENCE = """History PhD citation graph (derived dataset)

This work is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).
You are free to share and adapt it for any purpose, provided you give appropriate credit, provide
a link to the licence, and indicate if changes were made.

Licence text: https://creativecommons.org/licenses/by/4.0/legalcode

The dissertations from which these metadata were derived remain under their authors' and
repositories' own terms; no text from them is included in this dataset.
"""


def readme(meta, version):
    ib = meta.get('in_analysis_by_country', {})
    europe = sum(v for k, v in ib.items() if region(k) in ('FR', 'EU'))
    return f"""# History PhD citation graph: public release {version}

Which works History PhD dissertations cite, for {meta['dissertations']:,} dissertation records from
universities in Canada, the United States, Europe and elsewhere. {meta['in_analysis']:,} are strict History
PhDs in the analysis set (Canada {ib.get('CA', 0):,}, United States {ib.get('US', 0):,}, Europe {europe:,}, of
which France {ib.get('FR', 0):,}). The graph has {meta['works']:,} cited works, {meta['persons']:,} cited-person name
keys and {meta['cites_edges']:,} citation links.

**Derived metadata only.** The release holds parsed bibliographic fields: who cites what, with
author, title, year and kind of each cited work. It contains no text from the dissertations: no
bibliography or footnote strings, no PDFs, no full text. Every dissertation record links to its
repository page (`item_url`).

## Files

| File | One row per | Fields |
| --- | --- | --- |
| `dissertations.csv.gz` | dissertation record | `dissertation_id` (repository item id), `institution`, `country` (ISO 3166-1 alpha-2), `year`, `title`, `authors`, `advisors` (as catalogued), `eligibility` (`history_phd`, `needs_review`, `adjacent`), `in_analysis` (strict History PhD with a usable bibliography), `bibliography_source` (`bibliography`, `notes`, `none`), `extraction_status`, `cited_works`, `item_url` |
| `works.csv.gz` | cited work | `work_id` (`W:` first-author surname key, main-title key), `title`, `year`, `kind`, `container` (journal or book, for articles and chapters), `first_author_key`, `first_author`, `cited_by_strict_phds`, `cited_by_CA` / `_US` / `_FR` / `_EU` (rest of Europe) / `_OTHER` (strict PhDs citing, by region), `cited_by_all_records` (every dissertation record citing it, strict or not), `wikidata_work` (QID where translations were merged) |
| `people.csv.gz` | cited-person name key | `person_key` (surname, given name or initial), `name`, `cited_by_dissertations`, `cited_by_all`, `qid` (Wikidata, where grounded), `qid_basis` (grounding tier) |
| `citations.csv.gz` | citation link | `dissertation_id`, `work_id`, `via` (`bibliography` or `notes`), `section_side` (`primary`, `secondary`, `unspecified`, from the bibliography's own headings), `kind`, `note_citations` (for notes: how many notes cite the work) |
| `authorship.csv.gz` | author of a cited work | `person_key`, `work_id`, `position` |
| `work-translations.csv` | edition or translation merged into another | `work_id`, `canonical_work_id`, `wikidata_work`, `wikidata_author`, `title` |
| `pages/` | | comparison and network pages (self-contained HTML) |

Counts are presence: a dissertation citing a work counts once, however often it cites it.

## Method

All extraction is rule-based Python, reproducible from the repositories' PDFs. No language model
parsed the dissertations.

- **Bibliographies.** PyMuPDF reads each PDF's text layer: font sizes, italics and line positions.
  Scanned theses are read through Tesseract OCR. The closing bibliography is found by its heading
  in English, French and about a dozen further languages (German,
  Spanish, Portuguese, Swedish, Italian, Dutch, Catalan, Greek, Latvian, Turkish). Entries are split by hanging indents and spacing.
  Author, title, container, year and kind are read from italics, quotation marks and punctuation.
- **Notes.** Theses without a usable bibliography have one rebuilt from their footnotes or
  endnotes. A citation is counted once per thesis; *ibid.* and *op. cit.* count towards the work
  they refer to.
- **Works and people.** A work is its first author's surname plus its main title. Near-identical
  titles are merged. Translations and editions are merged through Wikidata (QLever) title
  matching for the most cited works. Names printed without a comma (`GINZBURG Carlo`, `Robert
  Dallek`) are read using each bibliography's own alphabetical order. People are name keys merged
  by catalogue title evidence; Wikidata QIDs are given only where the grounding passed its tier
  rules.
- **Scope.** The analysis set is dissertations from an explicit History programme or department.
  Bibliographies printed at the front of older typescripts are found but held out (their parsing
  measured too poorly), as are spans that swallowed body text.

## Measured quality

Independent judged samples, field precision:

| Source | First author | Title | Year |
| --- | --- | --- | --- |
| Bibliographies (Canada, main audit) | 85% | 86% | 90% |
| Notes, non-BASE (60 works) | 90% | 85% | 46% |
| Notes, BASE theses (40 works) | 85% | 88% | 69% |
| BASE non-English bibliographies (100 entries, before the 2026-10-21 name fix) | 63% | 58% | 75% |

Non-English bibliographies (mostly from the BASE harvest) parse less cleanly, so European counts
are, if anything, low. Full audit files and rubric are in the project repository.

## Caveats

- **Citation is not engagement.** A citation may be a frame, a foil or a ritual reference.
  Bibliographies list works consulted; notes list works cited.
- **Coverage is what repositories make openly available.** It is not a census of History PhDs.
  Restricted and embargoed dissertations appear as catalogue records only.
- **Person keys are not authority-reviewed identities.** Different people with the same surname
  and initial can share a key.

## Provenance and licence

Dissertation records and PDFs come from university repositories and their open-access
aggregations (BASE, the Bielefeld Academic Search Engine), with the AHA directory of History PhDs used
to confirm US degree programmes.
Each record keeps its repository URL. The dissertations remain under their authors' and
repositories' terms; this release redistributes none of their text.

This derived dataset is released under the Creative Commons Attribution 4.0 International licence
(CC BY 4.0, <https://creativecommons.org/licenses/by/4.0/>; see `LICENSE`).

Citation: History PhD citation graph, release {version}. Project lead: Jim Clifford, University of
Saskatchewan. Built with `scripts/build_public_release.py`.
"""


if __name__ == '__main__':
    main()
