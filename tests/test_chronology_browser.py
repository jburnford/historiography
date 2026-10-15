"""Explicit chronology, evidence access and all-family mobile/desktop acceptance."""
import json
import os
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('HISTORIOGRAPHY_SITE_URL', 'http://127.0.0.1:4173/')


class ChronologyBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1000})
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.page.close()

    def open(self, route):
        self.page.goto(URL + route)
        self.page.wait_for_function('document.getElementById("workspace").dataset.route === location.hash')

    def test_retrospective_and_review_year_do_not_extend_selected_exchange(self):
        self.open('#focus=sciencewars')
        selected = self.page.locator('.entry.selected')
        expect(selected.locator('.track-reception[data-year="2004"]')).to_have_count(1)
        expect(selected.locator('.chron-review')).to_have_count(1)
        expect(selected.locator('.unreviewed, .bar-shape')).to_have_count(0)
        expect(self.page.locator('.datewhy')).to_contain_text('1994 to 1999')
        self.page.locator('.chronology-details > summary').click()
        event = self.page.locator('[data-chronology-event="critique_2004"]')
        expect(event).to_contain_text('retrospective publication')
        event.locator('details > summary').click()
        expect(event.locator('a[href="https://doi.org/10.1086/421123"]')).to_be_visible()
        self.page.screenshot(path='/tmp/chronology-sciencewars-desktop.png', full_page=False)

    def test_journal_title_change_and_unknown_end_are_visibly_distinct(self):
        self.open('#focus=journal_647183c1e131cf7a')
        selected = self.page.locator('.entry.selected')
        expect(selected.locator('.chron-unknown')).to_have_count(1)
        expect(selected.locator('rect.chron-interval')).to_have_count(0)
        expect(self.page.locator('.datewhy')).to_contain_text('ending unestablished')
        self.open('#focus=journal_65dd21715536a35f')
        expect(self.page.locator('.entry.selected .interval-context')).to_have_count(1)
        expect(self.page.locator('.entry.selected .chron-unknown')).to_have_count(1)
        expect(self.page.locator('.datewhy')).to_contain_text('title change')

    def test_edition_dates_and_sources_on_phone(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open('#focus=joy_parr')
        self.page.locator('.chronology-details > summary').click()
        expect(self.page.locator('[data-chronology-event="sensing_hardcover_2009"]')).to_contain_text('2009-12-15')
        expect(self.page.locator('[data-chronology-event="sensing_pdf_2010"]')).to_contain_text('2010-07-01')
        edition = self.page.locator('[data-chronology-event="sensing_hardcover_2009"]')
        edition.locator('details > summary').click()
        expect(edition.locator('a[href="https://www.ubcpress.ca/sensing-changes"]')).to_be_visible()
        edition.scroll_into_view_if_needed()
        self.page.screenshot(path='/tmp/chronology-parr-mobile.png', full_page=False)
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 391)
        self.open('#person=joy_parr')
        expect(self.page.locator('.pm-entry[data-id="joy_parr"] .chron-event[data-year="2010"]')).to_have_count(1)

    def test_all_family_timelines_keep_their_entries_at_phone_and_desktop_widths(self):
        evidence = json.loads((ROOT / 'docs/data/evidence.json').read_text())
        families = evidence['families']['families']
        for width in [390, 1440]:
            self.page.set_viewport_size({'width': width, 'height': 900})
            for family in families:
                with self.subTest(width=width, family=family['id']):
                    self.open('#family=' + family['id'] + '&view=map')
                    expect(self.page.locator('svg.field')).to_be_visible()
                    self.assertGreater(self.page.locator('svg.field .entry.explicit').count(), 0)
                    expect(self.page.locator('svg.field .entry:not(.explicit)')).to_have_count(0)
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width + 1)


if __name__ == '__main__':
    unittest.main()
