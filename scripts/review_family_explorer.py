#!/usr/bin/env python3
"""Read-only browser review of every family against the published graph."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def review(url, out):
    graph = json.loads((ROOT / 'docs/data/graph.json').read_text())
    families = json.loads((ROOT / 'docs/data/evidence.json').read_text())['families']['families']
    nodes = {n['id']: n for n in graph['nodes']}
    rows, errors = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        for width in [1440, 390]:
            page.set_viewport_size({'width': width, 'height': 900})
            for family in families:
                page.goto(url.rstrip('/') + '/#family=' + family['id'])
                expect(page.locator('.family-explorer')).to_be_visible()
                fields = [nodes[m['id']] for m in family['members']]
                approaches = sum(len(n.get('strands', [])) for n in fields)
                people = {r['person_id'] for n in fields for r in n.get('representative_people', [])}
                expect(page.locator('.family-approach')).to_have_count(approaches)
                expect(page.locator('.family-people li[data-person]')).to_have_count(len(people))
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
                assert not overflow, (family['id'], width)
                rows.append(dict(family=family['id'], width=width, approaches=approaches,
                                 contributors=len(people), horizontal_overflow=overflow,
                                 document_height=page.evaluate('document.documentElement.scrollHeight')))
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.goto(url.rstrip('/') + '/#family=theory-and-method')
        card = page.locator('[data-approach="oral/transmission_models"]')
        expect(card).to_contain_text('Vansina')
        body = page.locator('.family-explorer').inner_text()
        field_scope_visible = nodes['publichistory']['scope_note'] in body
        assert not field_scope_visible
        extension = page.locator('[data-approach="digital_history/digital10_cohen_rosenzweig_digital_2005_2005"]')
        extension.locator('.family-approach-sources > summary').click()
        extension.locator('.sources details > summary').click()
        source_scope_visible = 'Selected introduction only.' in extension.locator('.family-approach-sources').inner_text()
        assert not source_scope_visible
        expect(extension).to_contain_text('No verification scope has been recorded')
        page.goto(url.rstrip('/') + '/#family=social-history&query=Cruikshank')
        expect(page.locator('.family-people li[data-person]')).to_have_count(1)
        expect(page.locator('.family-approach')).to_have_count(0)
        page.goto(url.rstrip('/') + '/#family=theory-and-method&range=2000')
        expect(page.locator('#edition-label')).to_contain_text('1.121')
        expect(page.locator('[data-approach^="digital_history/"]')).to_have_count(0)
        browser.close()
    assert not errors, errors
    result = dict(status='passed', checked_at=datetime.now(timezone.utc).isoformat(), url=url,
                  family_viewports=len(rows), browser_errors=errors, results=rows,
                  confirmed_findings=dict(member_field_scope_hidden_in_explorer=not field_scope_visible,
                                          source_scope_note_hidden_in_source_list=not source_scope_visible,
                                          cruikshank_search_returns_person_but_no_approach=True),
                  exact_2000_excludes_digital_extension=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:4191/')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    review(args.url, args.out)
