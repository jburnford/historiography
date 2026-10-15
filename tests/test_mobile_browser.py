"""Touch navigation and exploration, served by tests/run_site_checks.py."""
import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
GRAPH = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
URL = os.environ.get('HISTORIOGRAPHY_SITE_URL', 'http://127.0.0.1:4173/')


class MobileBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 390, 'height': 844},
                                          is_mobile=True, has_touch=True, device_scale_factor=1)
        self.page.set_default_timeout(8000)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def open(self, fragment=''):
        self.page.goto(URL + fragment)
        self.page.wait_for_function("document.getElementById('workspace').dataset.route === location.hash")

    def test_navigation_filters_and_phone_widths(self):
        for width in [320, 390, 430]:
            self.page.set_viewport_size({'width': width, 'height': 844})
            self.open()
            for selector in ['[data-tab="field"]', '[data-tab="timeline"]', '[data-tab="people"]', '#nav-more']:
                link = self.page.locator(selector)
                expect(link).to_be_visible()
                self.assertGreaterEqual(link.bounding_box()['height'], 44)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        expect(self.page.locator('[data-tab="browse"]')).to_be_hidden()
        self.page.locator('#nav-more').tap()
        expect(self.page.locator('#nav-more')).to_have_attribute('aria-expanded', 'true')
        self.page.locator('[data-tab="browse"]').tap()
        expect(self.page.locator('.layer-card')).to_have_count(4)
        expect(self.page.locator('#nav-more')).to_have_attribute('aria-expanded', 'false')
        expect(self.page.locator('#layer-filter')).to_be_hidden()
        self.page.locator('#filter-options > summary').tap()
        self.page.locator('#layer-filter').select_option('intellectual_connections')
        expect(self.page.locator('#filter-count')).to_have_text('· 1 active')
        self.assertEqual(self.page.locator('#search').evaluate('e => getComputedStyle(e).fontSize'), '16px')
        self.page.locator('#nav-more').tap()
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#nav-more')).to_be_focused()
        expect(self.page.locator('#nav-more')).to_have_attribute('aria-expanded', 'false')
        self.page.set_viewport_size({'width': 1280, 'height': 900})
        expect(self.page.locator('#nav-more')).to_be_hidden()
        expect(self.page.locator('[data-tab="browse"]')).to_be_visible()
        expect(self.page.locator('#layer-filter')).to_be_visible()

    def test_circle_taps_hold_details_and_return(self):
        self.open('#tab=people')
        chart = self.page.locator('.company-chart')
        expect(chart).to_be_visible()
        expect(chart.locator('.family-anchor')).to_have_count(12)
        self.assertLessEqual(chart.bounding_box()['height'], 844 * .61)
        self.assertGreater(chart.evaluate('e => e.scrollWidth'), chart.evaluate('e => e.clientWidth'))
        family = chart.locator('[data-id="family:annales"]')
        family.scroll_into_view_if_needed()
        family.tap()
        expect(self.page.locator('.section-heading h2')).to_have_text('Annales')
        person = self.page.locator('.company-chart .dot circle.core').first
        person_id = person.locator('..').get_attribute('data-id')
        person.scroll_into_view_if_needed()
        person.tap()
        self.page.wait_for_function('(id) => location.hash.includes("hold=" + id)', arg=person_id)
        panel = self.page.locator('.company-panel')
        expect(panel).to_be_focused()
        self.assertLess(panel.bounding_box()['y'], 100)
        self.page.locator('#nav-more').tap()
        self.page.keyboard.press('Escape')
        self.assertIn('hold=' + person_id, self.page.url)
        self.page.get_by_role('button', name='Back to circles ↑', exact=True).tap()
        expect(chart).to_be_focused()
        self.page.get_by_role('button', name='People list ↓', exact=True).tap()
        expect(self.page.locator('#people-register')).to_be_focused()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))

    def test_timeline_taps_open_details_and_all_connections(self):
        self.open('#family=annales&view=map')
        chart = self.page.locator('.field-scroll')
        expect(chart).to_be_visible()
        expect(self.page.locator('.field-panel')).to_be_hidden()
        expect(self.page.locator('.mark-guide')).not_to_have_attribute('open', '')
        self.assertLessEqual(chart.bounding_box()['height'], 844 * .63)
        mark = chart.locator('.entry[data-id="annales"] .chron-hit')
        mark.scroll_into_view_if_needed()
        mark.tap()
        expect(self.page.locator('.field-panel')).to_be_focused()
        expect(self.page.locator('#field-title')).to_have_text('Annales')
        self.assertLess(self.page.locator('.field-panel').bounding_box()['y'], 100)
        self.page.get_by_role('button', name='Back to timeline ↑', exact=True).tap()
        expect(chart).to_be_focused()
        self.page.get_by_role('link', name='Follow all connections →', exact=True).tap()
        expect(self.page.locator('.relationship-list')).to_be_visible()
        expected = sum('annales' in [e['source'], e['target']] for e in GRAPH['edges'])
        expect(self.page.locator('.relationship-row')).to_have_count(expected)

    def test_complete_roster_can_be_opened_without_obscuring_connections(self):
        self.open('#node=women&section=connections')
        roster = self.page.locator('.core-people')
        expect(roster).not_to_have_attribute('open', '')
        expect(self.page.locator('.neighborhood-controls')).to_be_visible()
        node = next(n for n in GRAPH['nodes'] if n['id'] == 'women')
        roster.locator('> summary').tap()
        expect(roster.locator('li')).to_have_count(len(node['representative_people']))
        expect(roster.locator('li a').first).to_be_visible()
        roster.locator('> summary').tap()
        self.page.locator('.relationship-row .inspect-link').first.tap()
        expect(self.page.locator('#detail-title')).to_be_focused()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
