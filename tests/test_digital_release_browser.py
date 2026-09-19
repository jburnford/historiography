"""Exercise the unchanged website with the proposed digital/web additions."""
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from playwright.sync_api import sync_playwright, expect
from scripts import build_digital_release_candidate as m


class DigitalBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dest = Path(tempfile.mkdtemp(prefix='historiography-digital10-',dir='/tmp'))
        cls.outputs,graph = m.outputs()
        cls.preview = cls.dest/'preview.json'
        cls.preview.write_text(m.serial(graph))
        cls.site = cls.dest/'site'
        subprocess.run(['python3','scripts/build_site.py','--graph',str(cls.preview),'--dest',str(cls.site),
            '--baseline','drafts/historiography-1920-2000.v1.121.json'],cwd=m.ROOT,check=True,capture_output=True)
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,directory=str(cls.site),**kwargs)
            def log_message(self,*args):
                pass
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_address[1]}/'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.dest)

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width':1440,'height':1050})
        self.page.set_default_timeout(8000)
        self.errors = []
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors,[])

    def open(self,fragment=''):
        self.page.goto(self.url+fragment)
        self.page.reload()
        expect(self.page.locator('#total-entries')).not_to_have_text('—')

    def test_new_entries_and_exact_baseline(self):
        self.open()
        for field in m.FIELDS:
            expect(self.page.locator(f'svg.field .entry[data-id="{field}"]')).to_have_count(1)
        expect(self.page.locator('.latest-label')).to_contain_text('2026')
        self.open('#range=2000')
        expect(self.page.locator('#scope-eyebrow')).to_contain_text('EXACT 2000 VIEW')
        expect(self.page.locator('svg.field .intervention')).to_have_count(0)
        for field in m.FIELDS:
            expect(self.page.locator(f'svg.field .entry[data-id="{field}"]')).to_have_count(0)

    def test_authors_arguments_and_evidence_links(self):
        self.open('#node=digital_history')
        cohen = self.page.locator('.extension .work-card',has_text='A Guide to Gathering')
        expect(cohen.locator('.work-authors')).to_contain_text('Daniel J. Cohen')
        expect(cohen.locator('.work-authors')).to_contain_text('Roy Rosenzweig')
        romein = self.page.locator('.extension .work-card',has_text='State of the Field: Digital History')
        expect(romein.locator('.work-authors')).to_contain_text('Stefania Scagliola')
        expect(romein.locator('.work-authors a')).to_have_count(9)
        thomas = self.page.locator('.extension .work-card',has_text='Computing and the Historical Imagination').filter(has=self.page.locator('.work-authors',has_text='William G. Thomas III'))
        expect(thomas.locator('.claim-statement').first).to_contain_text('Thomas argues')
        self.assertIn('Cameron Blevins',self.page.locator('.extension').inner_text())
        self.assertIn('Sharon M. Leon',self.page.locator('.extension').inner_text())
        self.page.locator('.extension .claim-evidence summary').first.click()
        expect(self.page.locator('.extension .evidence-list').first.locator('a[target="_blank"]')).to_have_count(1)

    def test_web_dates_and_abstract_scope(self):
        self.open('#node=web_history')
        card = self.page.locator('.extension .work-card',has_text='Platformization')
        expect(card.locator('.work-meta')).to_contain_text('2024')
        expect(card.locator('.work-version')).to_contain_text('2025')
        card.locator('.claim-evidence summary').first.click()
        expect(card.locator('.evidence-list .badge').first).to_have_text('Abstract only checked')
        self.assertIn('Ian Milligan',self.page.locator('.extension').inner_text())

    def test_mobile_and_allowlisted_build(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.open('#node=digital_history')
        self.page.locator('.extension .claim-evidence summary').first.click()
        expect(self.page.locator('.extension .evidence-list').first).to_be_visible()
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
        files = {str(p.relative_to(self.site)) for p in self.site.rglob('*') if p.is_file()}
        self.assertEqual(files,{'index.html','styles.css','app.js','core.mjs','field.mjs','people.mjs','.nojekyll',
            'data/graph.json','data/pathways.json','data/graph-2000.json'})
        graph = json.loads((self.site/'data/graph.json').read_text())
        self.assertNotIn('snapshot_path',json.dumps(graph['claim_catalogue']['claims']))


if __name__ == '__main__':
    unittest.main()
