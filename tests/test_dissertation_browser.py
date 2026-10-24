"""Student routes, coverage, keyboard/touch use and lazy dissertation loading."""
import json
import os
from pathlib import Path
import unittest
from urllib.parse import quote
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('HISTORIOGRAPHY_SITE_URL', 'http://127.0.0.1:4173/')


class DissertationBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.artifacts = ROOT / 'site/test-results'
        cls.artifacts.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1000})
        self.page.set_default_timeout(10000)
        self.errors = []
        self.requests = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('request', lambda r: self.requests.append(r.url))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def open(self, fragment):
        self.page.goto(URL + fragment)
        self.page.wait_for_function("() => document.getElementById('workspace').dataset.route === location.hash")

    def test_landing_navigation_and_wording(self):
        self.open('')
        expect(self.page.locator('.landing-families a')).to_have_count(12)
        expect(self.page.locator('[data-tab="dissertations"]')).to_be_visible()
        self.assertEqual([r for r in self.requests if '/data/dissertations/' in r], [])
        for fragment in ('', '#tab=about', '#tab=people'):
            self.open(fragment)
            text = self.page.locator('body').inner_text()
            self.assertNotIn('Reading this map', text)
            self.assertNotIn('THE MAP AND THE RECORD', text)
            self.assertNotIn('atlas entries', text)
        self.page.screenshot(path=str(self.artifacts/'reading-landing-desktop.png'), full_page=True)

    def test_deep_link_loads_selected_data_and_exact_denominators(self):
        self.open('#tab=dissertations&source=P%3Acronon%7Cwilliam')
        expect(self.page.locator('.reading-detail>h3')).to_have_text('Cronon, William')
        expect(self.page.locator('.reading-counts')).to_contain_text('6,794')
        expect(self.page.locator('.reading-detail section').first).to_contain_text('2020–2026')
        self.assertFalse(any('/data/graph.json' in r for r in self.requests))
        chunks = [r for r in self.requests if '/data/dissertations/' in r and not r.endswith(('index.json', 'links.json'))]
        self.assertEqual(len(chunks), 1)
        self.page.locator('.reading-coverage>summary').click()
        expect(self.page.locator('.reading-coverage')).to_contain_text('313 without years')
        expect(self.page.locator('.reading-coverage')).to_contain_text('7,107')
        self.assertGreater(self.page.locator('.reading-examples a[href^="https://"]').count(), 0)
        self.page.screenshot(path=str(self.artifacts/'reading-cronon-desktop.png'), full_page=True)

    def test_keyboard_search_work_and_teaching_round_trip(self):
        self.open('#tab=dissertations')
        query = self.page.get_by_label('Find a historian or work')
        query.fill('Cronon')
        query.press('ArrowDown')
        expect(self.page.locator('.reading-results a').first).to_be_focused()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.reading-detail>h3')).to_have_text('Cronon, William')
        self.page.locator('.reading-work-list a', has_text='Metropolis').click()
        expect(self.page.locator('.reading-detail>h3')).to_contain_text('Metropolis')
        self.page.locator('.reading-teaching a[href="#person=william_cronon"]').click()
        expect(self.page.locator('.person-profile')).to_be_visible()
        expect(self.page.locator('.reading-context')).to_be_visible()
        self.page.locator('.reading-context h4 a').click()
        expect(self.page.locator('.reading-detail>h3')).to_have_text('Cronon, William')

    def test_two_entry_pilots_and_archive(self):
        for nid, people in [('environment', ['William Cronon','Donald Worster']), ('archival_turn', ['Ann Laura Stoler','Michel-Rolph Trouillot'])]:
            self.open('#node='+nid)
            panel = self.page.locator('[data-reading-entry] .reading-context')
            expect(panel).to_be_visible()
            for name in people:
                expect(panel).to_contain_text(name)
            expect(panel).to_contain_text('do not measure the readership of the whole field')
        self.open('#node=environment&range=2000')
        expect(self.page.locator('.archive-banner')).to_be_visible()
        expect(self.page.locator('.reading-context')).to_have_count(0)

    def test_richard_white_later_work_and_reading_round_trip(self):
        self.open('#focus=richard_white')
        expect(self.page.locator('.entry.selected [data-event="rw157_railroaded"]')).to_have_count(1)
        expect(self.page.locator('.entry.selected [data-event="rw157_jane"]')).to_have_count(1)
        expect(self.page.locator('.field-panel')).to_contain_text('2022')
        self.open('#person=richard_white')
        expect(self.page.locator('.person-profile')).to_contain_text('Railroaded (2011)')
        expect(self.page.locator('.person-map [data-event="rw157_jane"]')).to_have_count(1)
        for nid in ['economic','capitalismdebates']:
            context = self.page.locator('.person-affiliation').filter(has=self.page.locator('.person-evidence')).filter(has=self.page.locator('h3 a[href*="node='+nid+'"]'))
            expect(context).to_contain_text('Railroaded')
            context.locator('.person-evidence > summary').click()
            context.get_by_role('link',name='Inspect the existing relationship').click()
            expect(self.page.locator('.reading-panel')).to_contain_text('2011')
            expect(self.page.locator('.reading-panel')).to_contain_text('complete book is unread')
            self.open('#person=richard_white')
        self.page.screenshot(path=str(self.artifacts/'reading-white-connections.png'),full_page=True)
        self.page.locator('.reading-context a',has_text='Railroaded').click()
        expect(self.page.locator('.reading-detail>h3')).to_have_text('White, Railroaded')
        expect(self.page.locator('.reading-counts>div').first).to_contain_text('51')
        self.page.locator('.reading-teaching a[href="#person=richard_white"]').click()
        expect(self.page.locator('.person-profile')).to_be_visible()

    def test_reviewed_books_credit_and_posthumous_editions(self):
        for nid, eid, text in [('jean_obrien','cw159_022','Firsting and Lasting'),
                              ('ian_mckay','cw159_064','Jamie Swift'),
                              ('natalie_zemon_davis','cw159_125','Randolph Starn')]:
            self.open('#focus='+nid)
            expect(self.page.locator('.entry.selected [data-event="'+eid+'"]').first).to_be_visible()
            self.open('#node='+nid)
            expect(self.page.locator('.reading-panel')).to_contain_text(text)
        self.open('#node=foucault')
        expect(self.page.locator('.reading-panel')).to_contain_text('posthumous')
        expect(self.page.locator('.reading-panel')).to_contain_text('James D. Faubion')

    def test_phone_navigation_and_contained_charts(self):
        for width in (320,390,430,768):
            self.page.set_viewport_size({'width':width,'height':844})
            self.open('#tab=dissertations&source=P%3Astoler%7Cann%20l')
            expect(self.page.locator('.reading-detail>h3')).to_have_text('Stoler, Ann Laura')
            expect(self.page.locator('[data-tab="dissertations"]')).to_be_visible()
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width+1)
            if width<700:
                box=self.page.locator('.reading-table-scroll').first
                self.assertGreater(box.evaluate('e=>e.scrollWidth'),box.evaluate('e=>e.clientWidth'))
        self.page.set_viewport_size({'width':390,'height':844})
        self.page.screenshot(path=str(self.artifacts/'reading-stoler-phone.png'), full_page=True)

    def test_missing_source_and_failed_fetch_have_recovery(self):
        failed = [False]
        def intercept(route):
            if not failed[0]:
                failed[0]=True
                route.fulfill(status=503,body='temporarily unavailable')
            else:
                route.continue_()
        self.page.route('**/data/dissertations/index.json',intercept)
        self.open('#tab=dissertations')
        self.page.get_by_role('button',name='Try again',exact=True).click()
        expect(self.page.get_by_label('Find a historian or work')).to_be_visible()
        self.open('#tab=dissertations&source=unknown')
        expect(self.page.locator('.reading-source')).to_contain_text('not in the current explorer snapshot')
        query=self.page.get_by_label('Find a historian or work')
        query.fill('no-such-historian-zzzz')
        expect(self.page.locator('.reading-results')).to_contain_text('0 matching sources')


if __name__ == '__main__':
    unittest.main()
