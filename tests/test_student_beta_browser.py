"""Student-facing pilot and loading behavior; run with tests/run_site_checks.py."""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

URL = os.environ.get('HISTORIOGRAPHY_SITE_URL','http://127.0.0.1:4173/')


class StudentBetaBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        cls.browser=cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page=self.browser.new_page(viewport={'width':1280,'height':900})
        self.errors=[]
        self.requests=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.on('request',lambda r:self.requests.append(r.url))
        self.page.set_default_timeout(10000)

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors,[])

    def test_landing_defers_full_graph_and_profile_metadata(self):
        self.page.goto(URL)
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.assertTrue(any(u.endswith('/data/overview.json') for u in self.requests))
        self.assertFalse(any(u.endswith('/data/graph.json') for u in self.requests))
        self.assertFalse(any(u.endswith('/data/people-records.json') for u in self.requests))
        self.page.locator('svg .family-row').first.click()
        expect(self.page.locator('.family-crumbs')).to_be_visible()
        self.assertEqual(sum(u.endswith('/data/graph.json') for u in self.requests),1)
        self.page.locator('.reset').click()
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.assertEqual(sum(u.endswith('/data/graph.json') for u in self.requests),1)

    def test_profile_record_tiers_and_source_links_on_mobile(self):
        self.page.goto(URL+'#person=paul_e_lovejoy')
        expect(self.page.locator('.publication-records')).to_be_visible()
        self.page.locator('.publication-group summary').first.click()
        expect(self.page.locator('.publication-group').first).to_contain_text('Probable match')
        link=self.page.locator('.publication-group a').first
        self.assertTrue(link.get_attribute('href').startswith('https://doi.org/'))
        self.page.locator('.identity-evidence summary').first.click()
        expect(self.page.locator('.identity-evidence').first).to_contain_text('Source credit: Identifier-supported match')
        self.page.set_viewport_size({'width':390,'height':844})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
        self.page.evaluate("location.hash='#person=geoff_eley'")
        expect(self.page.locator('.person-profile h2')).to_contain_text('Geoff Eley')
        expect(self.page.locator('.publication-records')).to_be_visible()
        self.assertEqual(sum(u.endswith('/data/people-records.json') for u in self.requests),1)

    def test_profile_failure_can_be_retried(self):
        attempts=[]
        def respond(route):
            attempts.append(1)
            route.fulfill(status=503,body='Unavailable') if len(attempts)==1 else route.continue_()
        self.page.route('**/data/people-records.json',respond)
        self.page.goto(URL+'#person=geoff_eley')
        self.page.get_by_role('button',name='Try again').click()
        expect(self.page.locator('.publication-records')).to_be_visible()
        self.assertEqual(len(attempts),2)

    def test_detailed_graph_failure_keeps_landing_and_can_be_retried(self):
        attempts=[]
        def respond(route):
            attempts.append(1)
            route.fulfill(status=503,body='Unavailable') if len(attempts)==1 else route.continue_()
        self.page.route('**/data/graph.json',respond)
        self.page.goto(URL)
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.page.get_by_role('link',name='Browse entries',exact=True).click()
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.page.get_by_role('button',name='Try again').click()
        expect(self.page.locator('.layer-card').first).to_be_visible()
        self.assertEqual(len(attempts),2)

    def test_sensitivity_caveat_is_available_with_the_comparison(self):
        self.page.goto(URL)
        self.page.get_by_text('How sensitive is this comparison?',exact=True).click()
        expect(self.page.locator('.landing-audit')).to_contain_text('percentage points')
        expect(self.page.locator('.landing-audit')).to_contain_text('Calculated lengths are missing')

    def test_annales_interwar_and_military_deposit_coverage_are_visible(self):
        self.page.goto(URL+'#node=annales')
        expect(self.page.locator('.record-panel')).to_contain_text('1929')
        expect(self.page.locator('.record-panel')).to_contain_text('1933–1938')
        expect(self.page.locator('.record-panel')).to_contain_text('1900')
        self.page.goto(URL+'#record=deposited')
        expect(self.page.locator('.landing-page')).to_contain_text('including reviews and short items')
        row=self.page.locator('[data-family="war-and-the-military"]')
        expect(row).to_be_visible()
        self.assertTrue(any('1935–1939' in x for x in row.locator('.record-bar title').all_text_contents()))
        self.page.set_viewport_size({'width':390,'height':844})
        expect(self.page.locator('.family-card').first).to_be_visible()
        expect(self.page.locator('.family-cards')).to_contain_text('bars from 1900')
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)

if __name__=='__main__':
    unittest.main()
