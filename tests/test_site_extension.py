"""Browser checks for the post-2000 extension view, run against a preview build of the
release candidate (data/extension-2026/release-candidate-06). Skipped when the candidate,
its preview builder or Playwright Chromium is unavailable.

The cases follow renderer-cases.json: an exact 2000 baseline, a partial extension domain,
complete coauthor credit, original-versus-reprint dates, abstract-only evidence labelled as
such, a legacy roster person discoverable through a new strand, and no research captures
in the public build.
"""
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
RC = ROOT / 'data/extension-2026/release-candidate-06'
PREVIEW = Path('/tmp/historiography-extension-06-preview.json')


class ExtensionViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (RC / 'candidate.json').exists():
            raise unittest.SkipTest('release candidate not present')
        subprocess.run(['python3', 'scripts/build_extension_release_candidate.py', '--check', '--preview', str(PREVIEW)],
                       cwd=ROOT, check=True, capture_output=True)
        cls.dest = Path(tempfile.mkdtemp(prefix='historiography-ext-', dir='/tmp'))
        subprocess.run(['python3', 'scripts/build_site.py', '--graph', str(PREVIEW), '--dest', str(cls.dest),
                        '--baseline', 'historiography-1920-2000.json'], cwd=ROOT, check=True, capture_output=True)
        handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(cls.dest), **k)
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.server.RequestHandlerClass.log_message = lambda *a: None
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_address[1]}/'
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.baseline = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
        cls.candidate = json.loads((RC / 'candidate.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop(); cls.server.shutdown(); shutil.rmtree(cls.dest, ignore_errors=True)

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1050})
        self.page.set_default_timeout(8000)
        self.errors, self.requests = [], []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('request', lambda r: self.requests.append(r.url))

    def tearDown(self):
        self.page.close(); self.assertEqual(self.errors, [])

    def open(self, fragment=''):
        self.page.goto(self.url + fragment); self.page.reload()
        expect(self.page.locator('#total-entries')).not_to_have_text('—')
        self.page.wait_for_timeout(300)

    def test_baseline_exact_and_partial_domain(self):
        self.open('#range=2000')
        expect(self.page.locator('#scope-eyebrow')).to_contain_text('EXACT 2000 VIEW')
        expect(self.page.locator('svg.field .intervention')).to_have_count(0)
        expect(self.page.locator('.ext-zone')).to_have_count(0)
        self.open('#tab=people&range=2000')
        expect(self.page.locator('.register-head .count')).to_contain_text(f"of {len(self.baseline['people'])} people")
        self.open('')
        ext = self.candidate['extension_scope']
        years = sum(len(set(n['node']['extension_coverage']['publication_years'])) for n in self.candidate['updated_nodes'])
        expect(self.page.locator('svg.field .intervention')).to_have_count(years)
        expect(self.page.locator('.ext-zone')).to_have_count(1)
        expect(self.page.locator('.cutoff-label')).to_contain_text(ext['research_cutoff'])
        expect(self.page.locator('.latest-label')).to_contain_text(str(ext['latest_selected_publication']))
        expect(self.page.locator('.ext-label')).to_contain_text(f"{len(ext['field_ids'])} of")
        marked = set(self.page.locator('svg.field .entry:has(.intervention)').evaluate_all('els => els.map(e => e.dataset.id)'))
        self.assertEqual(marked, set(ext['field_ids']))
        self.open('#tab=people')
        expect(self.page.locator('.register-head .count')).to_contain_text(f"of {len(self.baseline['people']) + len(self.candidate['people_additions'])} people")

    def test_coauthors_dates_and_evidence_scope(self):
        self.open('#node=medicalhistory')
        card = self.page.locator('.extension .work-card', has_text='persistence of history')
        for name in ['Rebecca Wynter', 'Niyah Campbell', 'Sarah Chaney', 'Sarah Marks']:
            expect(card.locator('.work-authors')).to_contain_text(name)
        expect(card.locator('.work-authors')).not_to_contain_text('Sylvia')
        for subject in ['Hickling', 'Burke', 'Fernando']:
            expect(card.locator('.work-authors')).not_to_contain_text(subject)
        expect(self.page.locator('.extension .badge.status-release_candidate')).to_be_visible()
        mccallum = self.page.locator('.extension .work-card', has_text='Starvation')
        mccallum.locator('.claim-evidence summary').first.click()
        expect(mccallum.locator('.evidence-list .badge').first).to_have_text('Abstract only checked')
        expect(self.page.locator('.extension .claim-card')).to_have_count(5)
        self.open('#node=spatialhistory')
        legg = self.page.locator('.extension .work-card', has_text='Historical geographies')
        for name in ['Legg', 'Ding', 'Ferretti', 'Morin', 'Novaes']:
            expect(legg.locator('.work-authors')).to_contain_text(name)
        mck = self.page.locator('.extension .work-card', has_text='Demonic Grounds')
        expect(mck.locator('.work-meta')).to_contain_text('2006')
        expect(mck.locator('.work-version')).to_contain_text('2020')
        expect(mck.locator('.work-version')).to_contain_text('original date')
        mck.locator('.claim-evidence summary').first.click()
        expect(mck.locator('.evidence-list').first).to_contain_text('121')
        machado = self.page.locator('.extension .work-card', has_text='Exemplos brasileiros')
        expect(machado.locator('.work-meta')).to_contain_text('language: pt')
        expect(self.page.locator('.extension .claim-card')).to_have_count(7)
        for status in self.page.locator('.extension .claim-card .badge[class*=status-]').all_inner_texts():
            self.assertEqual(status.lower(), 'needs review')

    def test_existing_person_gains_new_work_through_strand(self):
        self.open('#person=ian_gregory')
        expect(self.page.locator('.person-affiliation').first).to_be_visible()
        expect(self.page.locator('.strand-title', has_text='Historical GIS').first).to_be_visible()
        expect(self.page.locator('.person-profile')).to_contain_text('Healey')

    def test_public_build_has_no_research_captures(self):
        files = {str(p.relative_to(self.dest)) for p in self.dest.rglob('*') if p.is_file()}
        self.assertEqual(files, {'index.html', 'styles.css', 'app.js', 'core.mjs', 'field.mjs', 'people.mjs', '.nojekyll',
                                 'data/graph.json', 'data/pathways.json', 'data/graph-2000.json'})
        self.open('#node=spatialhistory')
        self.page.locator('.extension .claim-evidence summary').first.click()
        fetched = {u.replace(self.url, '') for u in self.requests}
        self.assertFalse(any('extension-2026' in u or '/raw/' in u for u in fetched), fetched)
        published = json.loads((self.dest / 'data/graph.json').read_text())
        self.assertNotIn('snapshot_path', json.dumps(published['claim_catalogue'].get('claims', [])))


if __name__ == '__main__':
    unittest.main()
