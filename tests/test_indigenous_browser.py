"""Read the expanded Indigenous entry and its preserved historical view in a browser."""
import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright, expect

URL = os.environ.get('HISTORIOGRAPHY_SITE_URL', 'http://127.0.0.1:4173/')
# The current production revision, so the test follows later releases.
CURRENT = json.loads((Path(__file__).resolve().parents[1] / 'historiography-1920-2000.json').read_text())['revision_history'][-1]['version']


class IndigenousBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1280, 'height': 900})
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.set_default_timeout(10000)

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def test_expanded_roster_source_limits_and_collective_attribution(self):
        self.page.goto(URL + '#node=indigenous')
        expect(self.page.locator('.school-tabs')).to_contain_text('50')  # 1.140: Val Napoleon
        expect(self.page.locator('.strand-guide > .strand')).to_have_count(33)
        expect(self.page.locator('.record-panel')).to_contain_text('cannot identify Indigenous authorship')
        self.page.goto(URL + '#person=edward_ahenakew')
        expect(self.page.locator('.person-profile')).to_contain_text('1923')
        expect(self.page.locator('.person-profile')).to_contain_text('1929')
        expect(self.page.locator('.person-profile')).to_contain_text('1973')
        expect(self.page.get_by_role('link', name='Full entry & relationships →')).to_be_visible()
        self.page.locator('.person-evidence > summary').first.click()
        notes = self.page.locator('.person-evidence .sources details')
        for i in range(notes.count()):
            notes.nth(i).locator('summary').click()
        expect(self.page.locator('.person-evidence').first).to_contain_text('No full-book reading')
        expect(self.page.locator('.person-evidence').first).to_contain_text('Article body unread')
        self.page.goto(URL + '#person=chief_thunderchild')
        expect(self.page.locator('.person-profile')).to_contain_text('fictional Old Keyam')
        expect(self.page.get_by_role('link', name='Full entry & relationships →')).to_have_count(0)
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 390)

    def test_archived_view_preserves_selection_and_returns_to_current_revision(self):
        self.page.goto(URL + '#node=indigenous&range=2000')
        expect(self.page.locator('#edition-label')).to_contain_text('1.121')
        expect(self.page.locator('.school-tabs')).to_contain_text('15')
        expect(self.page.locator('.strand-guide > .strand')).to_have_count(11)
        self.page.locator('.archive-banner a').click()   # no main-view toggle: the banner returns
        expect(self.page.locator('#edition-label')).to_contain_text(CURRENT)
        expect(self.page.locator('.strand-guide > .strand')).to_have_count(33)
        self.page.goto(URL + '#node=indigenous&section=connections')
        expect(self.page.locator('.core-people li')).to_have_count(50)
        expect(self.page.locator('.core-people [data-person="olive_patricia_dickason"]')).to_be_visible()

    def test_collaborators_are_discoverable_without_extra_individual_entries(self):
        self.page.goto(URL + '#node=indigenous')
        case = self.page.locator('.strand').filter(has=self.page.get_by_text('Stó:lō community–university historical practice', exact=True))
        expect(case).to_contain_text('1997')
        expect(case).to_contain_text('1998')
        for pid in ('john_lutz', 'keith_thor_carlson', 'albert_sonny_mchalsie', 'david_m_schaepe'):
            self.page.goto(URL + '#person=' + pid)
            expect(self.page.locator('.person-profile')).to_be_visible()
            expect(self.page.get_by_role('link', name='Full entry & relationships →')).to_have_count(0)
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 390)

    def test_2010_method_case_is_separately_marked_and_source_linked(self):
        self.page.goto(URL + '#node=indigenous')
        case = self.page.locator('.strand').filter(has_text='Community and academic relationships at Serpent River')
        expect(case).to_contain_text('2010')
        case.locator('> summary').click()
        for name in ('Gertrude Lewis', 'Valerie Commanda', 'Arnelda Jacobs', 'Betty Jacobs', 'Terry Jacobs', 'Peter Johnston'):
            expect(case).to_contain_text(name)
        expect(case).to_contain_text('Leddy cites Wheeler')
        self.page.goto(URL + '#focus=indigenous')
        expect(self.page.locator('svg.field .entry[data-id="indigenous"] .intervention')).to_have_count(1)
        self.page.goto(URL + '#person=lianne_leddy')
        expect(self.page.locator('.person-profile')).to_contain_text('2010')
        self.page.locator('.person-evidence > summary').first.click()
        expect(self.page.locator('.person-evidence a[href*="oralhistoryforum.ca"]')).to_be_visible()
        self.page.goto(URL + '#person=susan_neylan')
        expect(self.page.locator('.person-profile')).to_contain_text('mentorship')

    def test_family_exposes_approaches_people_and_boundary_connections(self):
        self.page.goto(URL + '#family=indigenous-histories')
        expect(self.page.locator('.family-explorer')).to_be_visible()
        # 1.128 bridges native_newcomer and settler_colonialism into this family.
        expect(self.page.locator('.family-content-summary')).to_contain_text('65 approaches')
        expect(self.page.locator('.family-approach')).to_have_count(65)
        expect(self.page.locator('.family-people li[data-person]')).to_have_count(104)  # 1.140: Val Napoleon
        expect(self.page.locator('.family-people [data-person="cole_harris"]')).to_have_count(1)
        case = self.page.locator('[data-approach="indigenous/stolo_community_university"]')
        for name in ('John Lutz', 'Keith Thor Carlson', 'David M. Schaepe'):
            expect(case).to_contain_text(name)
        case.get_by_role('link', name='John Lutz', exact=True).click()
        expect(self.page.locator('.person-profile')).to_contain_text('John Lutz')
        self.page.locator('.breadcrumbs').get_by_role('link', name='Indigenous histories', exact=True).click()
        expect(self.page.locator('.family-explorer')).to_be_visible()
        boundary = self.page.locator('.family-boundary-card[data-edge="edge_777"]')
        expect(boundary).to_contain_text('Comparison')
        expect(boundary).to_contain_text('Spatial history')
        boundary.get_by_role('link').click()
        expect(self.page.locator('.reading-panel .edge-endpoints')).to_contain_text('compared with')
        expect(self.page.locator('.reading-panel a[href*="ubcpress.ca"]')).to_be_visible()

    def test_family_search_sources_and_mobile_layout(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.goto(URL + '#family=indigenous-histories')
        expect(self.page.locator('.family-explorer')).to_be_visible()
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 390)
        self.page.locator('#search').fill('Carlson')
        expect(self.page.locator('.family-approach')).to_have_count(1)
        expect(self.page.locator('.family-people li[data-person]')).to_have_count(1)
        expect(self.page.locator('.family-approach')).to_contain_text('McHalsie')
        self.page.locator('.family-approach-sources > summary').click()
        expect(self.page.locator('.family-approach-sources')).to_contain_text('1997')
        self.page.get_by_role('link', name='Clear search', exact=True).click()
        expect(self.page.locator('.family-approach')).to_have_count(65)
        self.page.locator('.family-views').get_by_role('link', name='Timeline', exact=True).click()
        expect(self.page.locator('.field-table')).to_have_count(0)
        expect(self.page.locator('svg.field')).to_be_visible()
        self.page.locator('.family-views').get_by_role('link', name='Approaches & people', exact=True).click()
        expect(self.page.locator('.family-explorer')).to_be_visible()
        self.page.set_viewport_size({'width': 1440, 'height': 1000})
        self.page.screenshot(path='/tmp/indigenous-family-after.png')

    def test_family_historical_view_uses_archived_content(self):
        self.page.goto(URL + '#family=indigenous-histories&range=2000')
        expect(self.page.locator('#edition-label')).to_contain_text('1.121')
        expect(self.page.locator('[data-approach="indigenous/serpent_river_collaboration"]')).to_have_count(0)
        expect(self.page.locator('.family-people [data-person="lianne_leddy"]')).to_have_count(0)
        self.page.locator('.archive-banner a').click()   # no main-view toggle: the banner returns
        expect(self.page.locator('.family-approach')).to_have_count(65)


if __name__ == '__main__':
    unittest.main()
