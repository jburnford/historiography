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

    def test_beckert_and_carter_have_timeline_bios_and_distinct_reading_keys(self):
        for pid, name, key, count in [('sven_beckert', 'Sven Beckert', 'P:beckert|sven', 112),
                                      ('sarah_carter', 'Sarah Carter', 'P:carter|sarah a', 152)]:
            self.open('#focus=' + pid)
            expect(self.page.locator('.entry.selected')).to_have_count(1)
            expect(self.page.locator('.field-panel h2')).to_contain_text(name)
            self.open('#person=' + pid)
            expect(self.page.locator('.person-profile')).to_contain_text(name)
            context = self.page.locator('.person-profile .reading-context')
            expect(context).to_contain_text(str(count) + ' dated dissertations')
            context.locator('h4 a').click()
            self.assertIn('source=' + quote(key, safe=''), self.page.url)
            expect(self.page.locator('.reading-counts>div').first).to_contain_text(str(count))

    def test_anderson_book_comparison_on_profile_entry_and_phone(self):
        self.open('#person=benedict_anderson')
        panel = self.page.locator('.reading-person-context')
        expect(panel).to_be_visible()
        expect(panel).to_contain_text('685 of the 716')
        expect(panel).to_contain_text('95.7%')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('641 of 6,794')
        panel.get_by_label('Compare', exact=True).select_option('authors')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('716 of 6,794')
        panel.locator('.reading-context-regions > summary').click()
        for value in ('292', '262', '129', '33'):
            expect(panel.locator('.reading-context-regions')).to_contain_text(value)
        panel.get_by_label('Compare', exact=True).select_option('works')
        panel.get_by_label('Follow a selected work').select_option('W:anderson|under three flags')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('16 of 6,794')
        panel.get_by_label('Follow a selected work').select_option('W:anderson|spectre of comparisons')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('14 of 6,794')
        # The full entry presents the same personal comparison without a fake group roster.
        self.open('#node=benedict_anderson')
        panel = self.page.locator('.reading-person-context')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('14 of 6,794')
        for width in (320, 1440, 390):
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.page.wait_for_timeout(250)
            expect(panel).to_contain_text('95.7%')
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width + 1)
        panel.locator('.reading-selected-heading h4 a').click()
        expect(self.page.locator('.reading-detail>h3')).to_contain_text('Spectre')
        self.page.locator('.reading-teaching a[href="#person=benedict_anderson"]').click()
        expect(self.page.locator('.reading-person-context .reading-selected-heading')).to_contain_text('14 of 6,794')

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

    def test_economic_work_comparison_and_teaching_round_trip(self):
        self.open('#node=economic')
        panel=self.page.locator('.reading-field-context')
        expect(panel).to_have_count(1)
        expect(panel.locator('.reading-selected-heading')).to_contain_text('Wrigley')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('42 of 6,794')
        # Field comparisons need only the small links asset, not the source index/buckets.
        self.assertEqual([u.rsplit('/',1)[-1] for u in self.requests if '/data/dissertations/' in u],['links.json'])
        choice=panel.get_by_label('Follow an author')
        choice.focus()
        self.page.keyboard.press('ArrowDown')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('Mokyr')
        expect(choice).to_be_focused()
        for key,n in [('P:berg|maxine',56),('P:crafts|nicholas f',15)]:
            choice.select_option(key)
            expect(panel.locator('.reading-selected-heading')).to_contain_text(str(n)+' of 6,794')
        panel.get_by_label('Compare',exact=True).select_option('works')
        choice=panel.get_by_label('Follow a selected work')
        choice.select_option('W:north|institutions institutional change and economic performance')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('22 of 6,794')
        panel.locator('.reading-context-exact > summary').click()
        expect(panel.locator('.reading-context-exact tbody tr')).to_have_count(8)
        panel.locator('.reading-context-regions > summary').click()
        expect(panel.locator('.reading-context-regions tbody tr')).to_have_count(12)
        expect(panel.locator('.reading-context-regions')).to_contain_text('15')
        panel.screenshot(path=str(self.artifacts/'reading-economic-desktop.png'))
        panel.locator('.reading-selected-heading h4 a').click()
        expect(self.page.locator('.reading-detail>h3')).to_contain_text('North, Institutions')
        self.page.locator('.reading-teaching a[href="#person=douglass_north"]').click()
        expect(self.page.locator('.person-profile .reading-context')).to_contain_text('Institutions')
        self.open('#node=capitalismdebates')
        panel=self.page.locator('.reading-field-context')
        panel.get_by_label('Follow a selected work').select_option('W:johnson|river of dark dreams')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('64 of 6,794')
        panel.locator('.reading-selected-heading h4 a').click()
        expect(self.page.locator('.reading-detail>h3')).to_contain_text('Johnson, River of Dark Dreams')
        self.page.locator('.reading-teaching a[href="#node=capitalismdebates"]').click()
        expect(self.page.locator('.reading-selected-heading')).to_contain_text('Johnson, River of Dark Dreams')

    def test_crafts_low_count_search_and_return_to_author_comparison(self):
        self.open('#tab=dissertations')
        self.page.get_by_label('Find a historian or work').fill('Crafts')
        expect(self.page.locator('.reading-results')).to_contain_text('reviewed selection below the usual cutoff')
        self.page.locator('.reading-results a[href*="P%3Acrafts"]').click()
        expect(self.page.locator('.reading-counts')).to_contain_text('15')
        expect(self.page.locator('.reading-analysis-note')).to_contain_text('have not been produced')
        self.page.locator('.reading-work-list a[href*="british%20economic"]').click()
        expect(self.page.locator('.reading-counts>div').first).to_contain_text('4')
        self.page.locator('.reading-teaching a[href="#node=economic"]').click()
        panel=self.page.locator('.reading-field-context')
        panel.get_by_label('Follow an author').select_option('P:crafts|nicholas f')
        for width in (320,1440,390):
            self.page.set_viewport_size({'width':width,'height':900})
            self.page.wait_for_timeout(300)
            expect(panel.locator('.reading-selected-heading')).to_contain_text('15 of 6,794')
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width+1)
        panel.screenshot(path=str(self.artifacts/'reading-crafts-phone.png'))
        panel.locator('.reading-selected-heading h4 a').click()
        self.page.locator('.reading-teaching a[href="#node=economic"]').click()
        expect(self.page.get_by_label('Follow an author')).to_have_value('P:crafts|nicholas f')

    def test_field_reading_on_phones_resize_and_archive(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.open('#node=capitalismdebates')
        panel=self.page.locator('.reading-field-context')
        panel.get_by_label('Follow a selected work').select_option('W:beckert|empire of cotton')
        for width in (320,430,768,1440,390):
            self.page.set_viewport_size({'width':width,'height':900})
            # The app redraws when crossing its phone breakpoint; retain the choice.
            self.page.wait_for_timeout(300)
            expect(panel.locator('.reading-selected-heading')).to_contain_text('Beckert, Empire of Cotton')
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width+1)
        panel.locator('.reading-context-exact > summary').click()
        expect(panel.locator('.reading-context-exact .reading-scroll-hint')).to_be_visible()
        scroll=panel.locator('.reading-context-exact .reading-table-scroll')
        self.assertGreater(scroll.evaluate('e=>e.scrollWidth'),scroll.evaluate('e=>e.clientWidth'))
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),391)
        panel.screenshot(path=str(self.artifacts/'reading-capitalism-phone.png'))
        self.open('#node=capitalismdebates&section=connections')
        expect(self.page.locator('.reading-field-context')).to_have_count(1)
        self.open('#node=economic&range=2000')
        expect(self.page.locator('.archive-banner')).to_be_visible()
        expect(self.page.locator('.reading-context')).to_have_count(0)

    def test_emotions_work_and_author_comparison_keeps_distinct_populations(self):
        self.open('#node=history_of_emotions')
        panel = self.page.locator('.reading-field-context')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('42 of 6,794')
        panel.get_by_label('Follow a selected work').select_option('W:rosenwein|worrying about emotions in history|a')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('36 of 6,794')
        panel.get_by_label('Compare', exact=True).select_option('authors')
        panel.get_by_label('Follow an author').select_option('P:rosenwein|barbara h')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('90 of 6,794')
        panel.get_by_label('Follow an author').select_option('P:reddy|william m')
        expect(panel.locator('.reading-selected-heading')).to_contain_text('61 of 6,794')
        for width in (320, 390, 768, 1440):
            self.page.set_viewport_size({'width': width, 'height': 900})
            expect(panel.locator('.reading-selected-heading')).to_contain_text('61 of 6,794')
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width + 1)
        panel.locator('.reading-selected-heading h4 a').click()
        expect(self.page.locator('.reading-detail>h3')).to_have_text('Reddy, William M')
        self.page.locator('.reading-teaching a[href="#node=history_of_emotions"]').click()
        expect(self.page.locator('.reading-field-context')).to_be_visible()

    def test_new_content_profiles_and_joint_bibliography_credits(self):
        for pid, count in [('james_c_scott', 455), ('henri_lefebvre', 174),
                           ('lauren_benton', 135), ('william_m_reddy', 61),
                           ('barbara_h_rosenwein', 90)]:
            self.open('#person=' + pid)
            panel = self.page.locator('.person-profile .reading-context')
            expect(panel).to_be_visible()
            expect(panel).to_contain_text(str(count))
        self.open('#person=carlo_poni')
        expect(self.page.locator('.person-profile')).to_contain_text('With Carlo Ginzburg')
        self.open('#node=reinhart_koselleck')
        expect(self.page.locator('.reading-panel')).to_contain_text('Alexandre Escudier')
        expect(self.page.locator('.reading-panel')).to_contain_text('Todd Samuel Presner')
        self.open('#focus=reinhart_koselleck')
        expect(self.page.locator('.entry.selected [data-event="dc168_work_04"]')).to_have_count(1)

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


    def test_canon_map_loads_on_demand_and_finds_a_person(self):
        self.open('#tab=dissertations')
        expect(self.page.locator('.reading-canon-link a')).to_have_attribute('href', '#tab=canon')
        self.assertFalse(any(r.endswith('/data/dissertations/canon-map.json') for r in self.requests))
        self.open('#tab=canon')
        expect(self.page.locator('.canon-map h2')).to_have_text('Canon map')
        self.page.wait_for_selector('.canon-node')
        self.assertFalse(any('/data/graph.json' in r for r in self.requests))
        self.assertEqual(self.page.title(), 'Canon map · History in Conversation')
        find = self.page.locator('.canon-find')
        find.fill('Innis, Harold A.')
        find.dispatch_event('change')
        expect(self.page.locator('.canon-detail h3')).to_have_text('Innis, Harold A.')
        expect(self.page.locator('.canon-detail a[href^="#tab=dissertations&source="]')).to_have_count(1)
        partner = self.page.locator('.canon-partners button').first
        name = partner.inner_text()
        partner.click()
        expect(self.page.locator('.canon-detail h3')).to_have_text(name)
        before = self.page.locator('.canon-threshold-value').inner_text()
        self.page.locator('.canon-threshold').fill('0')
        expect(self.page.locator('.canon-threshold-value')).not_to_have_text(before)
        self.page.select_option('.canon-measure', 'assoc')
        self.assertGreater(self.page.locator('.canon-node').count(), 1000)
        self.assertGreater(self.page.locator('.canon-pairs tbody tr').count(), 100)
        self.page.screenshot(path=str(self.artifacts/'canon-map-desktop.png'))


if __name__ == '__main__':
    unittest.main()
