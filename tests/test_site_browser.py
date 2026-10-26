"""Browser acceptance checks. Requires Playwright Chromium and a running preview.

Run: python3 -m unittest tests.test_site_browser -v
Optional URL: HISTORIOGRAPHY_SITE_URL=http://127.0.0.1:4173/
"""
import json
import os
import re
from urllib.parse import parse_qs
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
GRAPH = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
PATHWAYS = json.loads((ROOT / 'seminar-pathways.json').read_text())
GRAPH_LABELS = {n['id']: n['label'] for n in GRAPH['nodes']}
URL = os.environ.get('HISTORIOGRAPHY_SITE_URL', 'http://127.0.0.1:4173/')


class AtlasBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.artifacts = ROOT / 'site' / 'test-results'
        cls.artifacts.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1050})
        self.page.set_default_timeout(7000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def open(self, fragment=''):
        self.page.goto(URL + fragment)
        self.page.wait_for_function("() => document.getElementById('workspace').dataset.route === location.hash")
        expect(self.page.locator('.landing-page, .field-page, .layer-card, .entry-card, .focus-layout, .school-layout, .person-card, .person-profile, .pathway-card, .pathway-layout, .register-section, .about, .empty').first).to_be_visible()

    def test_landing_families_strip_and_record_views(self):
        """The front door: twelve families, the atlas's dating beside the record's share."""
        self.open()
        expect(self.page.locator('.landing-page')).to_be_visible()
        expect(self.page.locator('svg.landing-svg .family-row')).to_have_count(12)
        expect(self.page.locator('.strip-bar.atlas .seg')).to_have_count(12)
        expect(self.page.locator('.strip-bar.record .seg')).to_have_count(13)
        expect(self.page.locator('.strip-bar.record .seg.unclaimed')).to_contain_text('%')
        expect(self.page.locator('.landing-page')).to_contain_text('must not be summed')
        self.assertTrue(self.page.locator('#toolbar').is_hidden())
        box = self.page.locator('.landing-rows')
        self.assertLessEqual(box.evaluate('el => el.scrollWidth'), box.evaluate('el => el.clientWidth'))
        self.page.get_by_role('button', name='Established title contexts', exact=True).click()
        expect(self.page.get_by_role('button', name='Established title contexts', exact=True)).to_have_attribute('aria-pressed', 'true')
        self.assertIn('record=established', self.page.url)
        self.page.locator('details.landing-table > summary').click()
        expect(self.page.locator('details.landing-table table:not(.strip-table) tbody tr')).to_have_count(12)
        # The headline strip as text (its labels are hidden on mobile): 12 families + unclaimed.
        expect(self.page.locator('details.landing-table table.strip-table tbody tr')).to_have_count(13)
        self.page.screenshot(path=str(self.artifacts / 'landing-desktop.png'), full_page=True)
        # Opening a family from low on the page brings its field view into view.
        self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        self.page.locator('svg.landing-svg .family-row').last.click()
        self.page.wait_for_function('() => location.hash.includes("family=")')
        self.page.wait_for_function('''() => new Promise(done => {
            let last = window.scrollY, still = 0;
            const tick = () => { still = window.scrollY === last ? still + 1 : 0; last = window.scrollY;
                                 still >= 5 ? done(true) : requestAnimationFrame(tick); };
            tick(); })''')
        self.assertLess(self.page.evaluate('window.scrollY'), 700)

    def test_overview_search_filters_keyboard_and_reset(self):
        self.open('#tab=browse')
        expect(self.page.locator('.layer-card')).to_have_count(4)
        self.page.screenshot(path=str(self.artifacts / 'overview-desktop.png'), full_page=True)
        search = self.page.locator('#search')
        search.fill('Metahistory')
        self.page.wait_for_timeout(150)
        expect(self.page.locator('.entry-card h3')).to_contain_text(['Hayden White'])
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'search')
        search.fill('no-such-entry-xyz')
        expect(self.page.locator('.empty')).to_contain_text('No entries match')
        search.fill('')
        self.page.locator('#period-filter').select_option('period_1')
        expect(self.page.locator('.context-note')).to_contain_text('no assigned period')
        self.page.locator('#layer-filter').select_option('intellectual_connections')
        thinkers = sum(n['layer'] == 'intellectual_connections' for n in GRAPH['nodes'])
        expect(self.page.locator('.count')).to_have_text(f'{thinkers} of {len(GRAPH["nodes"])} entries')
        self.page.locator('.reset').click()
        self.open('#tab=browse')
        self.page.locator('#hunt-filter').check()
        expect(self.page.locator('.entry-card')).to_have_count(4)
        self.page.locator('.entry-card h3 a').first.focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.school-layout')).to_be_visible()
        self.page.locator('.reset').click()
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.open('#tab=browse')
        expect(self.page.locator('.layer-card')).to_have_count(4)
        self.assertEqual(self.page.locator('#search').input_value(), '')
        self.assertFalse(self.page.locator('#hunt-filter').is_checked())

    def test_neighborhood_evidence_directions_and_history(self):
        self.open('#node=women&section=connections')
        incoming = [e for e in GRAPH['edges'] if e['target'] == 'women' and e.get('directed')]
        expect(self.page.locator('.neighbor-node.incoming')).to_have_count(len(incoming))
        for kind, arrows in [('comparison', False), ('unclassified', False), ('contribution', True), ('critique', True), ('influence', True)]:
            edge = next((e for e in GRAPH['edges'] if e.get('relationship_kind', 'unclassified') == kind), None)
            if edge is None: continue
            self.open(f"#node={edge['source']}&kind={kind}")
            paths = self.page.locator('.connection')
            if arrows:
                self.assertGreater(paths.count(), 0)
            else:
                expect(paths).to_have_count(0)
                self.assertGreater(self.page.locator('.associated-card').count(), 0)
            for path in paths.all():
                self.assertEqual(bool(path.get_attribute('marker-end') or path.get_attribute('marker-start')), arrows)
            self.open(f"#edge={edge['id']}")
            expect(self.page.locator('.reading-panel')).to_contain_text(edge['relationship'])
            if edge.get('evidence_note'):
                expect(self.page.locator('.reading-panel')).to_contain_text(edge['evidence_note'])
        self.open('#node=women&section=connections')
        self.page.locator('.edge-label').first.click()
        expect(self.page.locator('#detail-title')).to_be_focused()
        self.page.go_back()
        expect(self.page.locator('#detail-title')).to_have_text(next(n['label'] for n in GRAPH['nodes'] if n['id'] == 'women'))
        self.page.locator('#neighbor-layer').select_option('historians')
        self.assertGreater(self.page.locator('.neighbor-node').count(), 0)
        self.assertTrue(all('Historians' in n.inner_text() for n in self.page.locator('.neighbor-node').all()))
        self.page.screenshot(path=str(self.artifacts / 'neighborhood-desktop.png'), full_page=True)
        self.page.get_by_role('button', name='List', exact=True).click()
        expect(self.page.locator('.relationship-list')).to_be_visible()

    def test_pathways_and_direct_links(self):
        self.open('#tab=pathways')
        expect(self.page.locator('.pathway-card')).to_have_count(len(json.loads((ROOT / 'seminar-pathways.json').read_text())['pathways']))
        for pathway in PATHWAYS['pathways']:
            self.open(f"#pathway={pathway['id']}")
            expect(self.page.locator('.reading-sequence>li')).to_have_count(len(pathway['node_ids']))
            expect(self.page.locator('.exercise')).to_contain_text(pathway['exercise'])
        self.open('#pathway=paradigms_and_limits')
        self.page.locator('.reading-sequence h3 a').first.click()
        expect(self.page.locator('.school-layout')).to_be_visible()
        self.page.get_by_role('link', name='Back to pathway', exact=True).click()
        expect(self.page.locator('.pathway-layout')).to_be_visible()
        self.open('#node=missing&edge=missing')
        expect(self.page.locator('.landing-page')).to_be_visible()

    def test_every_entry_and_missing_source_metadata(self):
        # Ensures long labels, null chronology, and inherited references all render.
        for n in GRAPH['nodes']:
            self.open(f"#node={n['id']}")
            expect(self.page.locator('#detail-title')).to_have_text(n['label'])
            expect(self.page.locator('.reading-panel .description')).to_have_text(n['description'])
            if not n.get('period'):
                expect(self.page.locator('.period-note')).to_have_text('No assigned period')
        null_source = next(s for s in GRAPH['sources'] if s.get('url') is None)
        n = next(n for n in GRAPH['nodes'] if null_source['id'] in n.get('source_ids', []))
        self.open(f"#node={n['id']}")
        source = self.page.locator('.reading-panel .sources>li').filter(has_text=null_source.get('citation') or null_source['title']).first
        expect(source).to_be_visible()
        expect(source.locator('a')).to_have_count(0)

    def test_mobile_layout_and_view_switch(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        for fragment in ['', '#layer=intellectual_connections', '#pathway=paradigms_and_limits', '#node=marx', '#person=eric_hobsbawm', '#tab=people', '#node=women&section=connections']:
            self.open(fragment)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'), fragment)
        expect(self.page.locator('.relationship-list')).to_be_visible()
        self.page.get_by_role('button', name='Map', exact=True).click()
        expect(self.page.locator('.focus-graph')).to_be_visible()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.locator('.edge-label').first.click()
        expect(self.page.locator('#detail-title')).to_be_focused()
        self.page.screenshot(path=str(self.artifacts / 'relationship-mobile.png'), full_page=True)
        self.open()
        self.page.screenshot(path=str(self.artifacts / 'overview-mobile.png'), full_page=True)

    def test_school_people_profiles_search_and_roles(self):
        self.open('#node=marx')
        expect(self.page.locator('.person-card h3')).to_contain_text(['E. P. Thompson', 'Eric Hobsbawm', 'Christopher Hill', 'Dorothy Thompson'])
        self.page.screenshot(path=str(self.artifacts / 'marxist-historians-desktop.png'), full_page=True)
        self.page.get_by_role('link', name='Eric Hobsbawm', exact=True).click()
        expect(self.page.locator('.person-profile h2')).to_contain_text('Eric Hobsbawm')
        self.assertGreater(self.page.locator('.person-affiliation').count(), 1)
        self.page.go_back()
        expect(self.page.locator('.school-layout')).to_be_visible()
        self.page.get_by_role('link', name='Connections', exact=False).filter(has=self.page.locator('span')).click()
        expect(self.page.locator('.focus-layout')).to_be_visible()
        self.open('#node=bielefeld')
        card=self.page.locator('.person-card').filter(has=self.page.get_by_role('link', name='Geoff Eley', exact=True))
        expect(card).to_contain_text('Critical intervention')
        expect(card).to_contain_text('not represented as its adherent')
        self.open('#tab=people')
        self.page.locator('#search').fill('Hobsbawm')
        expect(self.page.get_by_role('link', name='Eric Hobsbawm', exact=True)).to_be_visible()
        self.page.get_by_role('link', name='Eric Hobsbawm', exact=True).focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.person-profile h2')).to_contain_text('Eric Hobsbawm')
        for person in GRAPH['people']:
            self.open(f"#person={person['id']}")
            expect(self.page.locator('.person-profile h2')).to_contain_text(person['label'])
        self.page.set_viewport_size({'width':390,'height':844})
        self.open('#node=annales')
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.screenshot(path=str(self.artifacts / 'annales-historians-mobile.png'), full_page=True)

    def test_all_focused_connections_visible_without_pagination(self):
        for node in GRAPH['nodes']:
            node_id = node['id']
            # Old page parameters must no longer hide any relationships.
            self.open(f'#node={node_id}&section=connections&inPage=2&outPage=2&otherPage=2&page=2')
            edges = [e for e in GRAPH['edges'] if node_id in (e['source'], e['target'])]
            expected = {e['id'] for e in edges}
            reached = self.page.locator('.flow-neighbor, .associated-card').evaluate_all('(els)=>els.map(e=>e.dataset.edge)')
            self.assertEqual(set(reached), expected, node_id)
            self.assertEqual(len(reached), len(expected), node_id)
            expect(self.page.locator('[data-lane], .neighborhood .pagination')).to_have_count(0)
            expect(self.page.locator('.relationship-summary strong')).to_have_text(f'{len(edges)} relationships in this view')
            reps = node.get('representative_people', [])
            shown = self.page.locator('.core-people li').evaluate_all('(els)=>els.map(e=>e.dataset.person)')
            self.assertEqual(shown, [r['person_id'] for r in reps], node_id)

            selected = self.page.locator('.flow-focus')
            if selected.count():
                centre = selected.bounding_box()
                for side in ['incoming', 'outgoing']:
                    previous = None
                    for neighbor in self.page.locator(f'.flow-neighbor.{side}').all():
                        box = neighbor.bounding_box()
                        self.assertTrue(box['x'] + box['width'] < centre['x'] if side == 'incoming' else box['x'] > centre['x'] + centre['width'])
                        if previous: self.assertLessEqual(previous['y'] + previous['height'], box['y'], node_id)
                        previous = box
            if node_id in ['marx','annales','science']:
                self.page.screenshot(path=str(self.artifacts / f'{node_id}-all-connections-desktop.png'), full_page=True)
                self.page.get_by_role('button', name='List', exact=True).click()
                expect(self.page.locator('.relationship-row')).to_have_count(len(edges))

    def test_field_strands_and_kuhn_visibility(self):
        self.open('#node=economic')
        for title in ['French serial and conjunctural history','Cliometrics and historical measurement','Institutions and economic change']:
            self.page.locator('.strand > summary').filter(has_text=title).click()
        expect(self.page.locator('.strand[open]')).to_have_count(3)
        expect(self.page.locator('.strand[open]').filter(has_text='French serial')).to_contain_text('Ernest Labrousse')
        self.open('#node=science&section=connections')
        expect(self.page.locator('.core-people')).to_contain_text('Thomas Kuhn')
        expect(self.page.locator('.flow-neighbor[data-edge="edge_131"]')).to_contain_text('Kuhn')
        self.page.locator('.flow-label[href*="edge_131"]').click()
        expect(self.page.locator('.reading-panel')).to_contain_text('1962')

    def test_field_view_focus_list_and_filters(self):
        """The field is the front door: it must draw what it counts, in both views."""
        self.open('#family=all')
        expect(self.page.locator('svg.field')).to_be_visible()
        drawn = self.page.locator('.entry, .chip').count()
        summary = self.page.locator('.field-summary').inner_text()
        placed = int(summary.split()[0]) + int(summary.split('·')[1].split()[0]) \
            if 'without' in summary else int(summary.split()[0])
        self.assertEqual(drawn, placed, f'drew {drawn} but claimed {placed}')
        # The chart is laid out for the column it sits in: no horizontal scroll, no clipped labels.
        box = self.page.locator('.field-scroll')
        self.assertLessEqual(box.evaluate('el => el.scrollWidth'), box.evaluate('el => el.clientWidth'))
        clipped = self.page.evaluate("""() => { const r = document.querySelector('.field-scroll').getBoundingClientRect();
            return [...document.querySelectorAll('.bar-label')].filter(t => { const b = t.getBoundingClientRect(); return b.right > r.right + 1 || b.left < r.left - 1; }).length }""")
        self.assertEqual(clipped, 0, 'labels must stay inside the visible chart')
        self.assertEqual(self.page.locator('svg.field').get_attribute('role'), 'group')
        self.page.screenshot(path=str(self.artifacts / 'field-desktop.png'), full_page=True)

        # The panel travels with the reader: hovering deep in the chart keeps it on screen.
        # A bar in the last full band, well below the first screen; the panel must still be in view.
        last = self.page.locator('.entry[data-id="micro"]')
        last.scroll_into_view_if_needed()
        bb = last.locator('.chron-hit').bounding_box()
        self.page.mouse.move(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
        self.page.wait_for_timeout(200)
        panel = self.page.locator('.field-panel').bounding_box()
        self.assertGreaterEqual(panel['y'], 0)
        self.assertLess(panel['y'], 400)
        expect(self.page.locator('.field-panel h2')).to_have_text(last.get_attribute('aria-label').split(',')[0])
        # Keyboard focus previews like hover does.
        self.page.mouse.move(0, 0)
        self.page.locator('.entry[data-id="annales"]').focus()
        expect(self.page.locator('.field-panel h2')).to_have_text('Annales')

        # Holding an entry reclaims space and draws only its relationships.
        self.open('#focus=annales')
        expect(self.page.locator('.field-panel h2')).to_have_text('Annales')
        edges = self.page.locator('.edge').count()
        self.assertGreater(edges, 0)
        self.assertGreater(self.page.locator('.ghost').count(), 0)
        expect(self.page.locator('.entry.selected')).to_have_count(1)
        self.page.screenshot(path=str(self.artifacts / 'field-focus-desktop.png'), full_page=True)

        # Every relationship opens to its evidence and references without leaving the field.
        rows = self.page.locator('details.rel')
        self.assertEqual(rows.count(), sum(1 for e in GRAPH['edges'] if 'annales' in (e['source'], e['target']))
                         + sum(1 for e in GRAPH['journal_catalogue']['edges'] if e['target'] == 'annales'))
        first = rows.first
        edge_id = first.get_attribute('data-edge')
        first.locator('> summary').click()
        edge = next(e for e in GRAPH['edges'] + GRAPH['journal_catalogue']['edges'] if e['id'] == edge_id)
        expect(first.locator('.evidence')).to_contain_text(edge['evidence_note'][:60])
        first.locator('.rel-sources > summary').click()
        expect(first.locator('.sources li')).to_have_count(len(edge['source_ids']))

        # Hiding a kind is shareable and actually removes those edges.
        self.open('#focus=annales&hide=comparison')
        self.assertLess(self.page.locator('.edge').count(), edges)

        # A pathway can be laid over the field: numbered members, only their own edges.
        pathway = next(p for p in PATHWAYS['pathways'] if p['id'] == 'paradigms_and_limits')
        self.open('#path=paradigms_and_limits')
        expect(self.page.locator('.field-panel h2')).to_have_text(pathway['title'])
        expect(self.page.locator('.entry.related, .chip.related')).to_have_count(len(pathway['node_ids']))
        labels = self.page.locator('.entry.related .bar-label').evaluate_all('els => els.map(e => e.textContent)')
        self.assertTrue(all(l.split('.')[0].isdigit() for l in labels), labels)
        members = set(pathway['node_ids'])
        for e in GRAPH['edges']:
            drawn_edge = self.page.locator(f'.edge[data-edge="{e["id"]}"]').count() == 1
            self.assertEqual(drawn_edge, e['source'] in members and e['target'] in members, e['id'])
        self.page.locator('.path-panel ol a').first.click()
        expect(self.page.locator('.field-panel h2')).to_have_text(GRAPH_LABELS[pathway['node_ids'][0]])
        expect(self.page.locator('.path-strip')).to_contain_text('Entry 1 of')
        self.open('#pathway=paradigms_and_limits')
        self.page.get_by_role('link', name='see these entries together on the field', exact=False).click()
        expect(self.page.locator('.path-panel')).to_be_visible()

        # The list view is the accessible equivalent and carries every entry, grouped by band.
        self.open('#view=list')
        self.assertGreater(self.page.locator('details.band-list').count(), 1)
        self.assertEqual(self.page.locator('.field-table tbody tr').count(), drawn)

        # Current dates are explicit contributions; review coverage is a separate marker.
        self.open('#focus=annales')
        note = self.page.locator('.datewhy')
        expect(note).to_contain_text('Journal founded 1929')
        expect(note).to_contain_text('reviewed through 2000')
        expect(self.page.locator('.entry.selected .chron-event')).to_have_count(4)
        expect(self.page.locator('.entry.selected .chron-review')).to_have_count(1)
        expect(self.page.locator('.entry.selected rect.unreviewed')).to_have_count(0)
        self.open('#focus=military')
        expect(self.page.locator('.entry.selected .bar-lead')).to_have_count(0)
        expect(self.page.locator('.entry.selected .track-context[data-year="1832"]')).to_have_count(1)
        expect(self.page.locator('.datewhy')).to_contain_text('not a field origin')

    def test_open_frame_marks(self):
        """Explicit chronology: no wall or inferred tail; separate review markers and cutoff."""
        self.open('#focus=annales')
        expect(self.page.locator('svg.field')).to_be_visible()
        self.assertEqual(self.page.locator('.coverage-wall').count(), 0)
        self.assertEqual(self.page.locator('rect.unreviewed').count(), 0)
        self.assertGreater(self.page.locator('.chron-review').count(), 0)
        self.assertEqual(self.page.locator('line.frame-cutoff').count(), 1)
        expect(self.page.locator('.field-panel')).to_contain_text('reviewed through 2000')
        self.assertTrue(self.page.locator('#range-toggle').is_hidden())
        expect(self.page.locator('#edition-label')).to_contain_text(GRAPH['revision_history'][-1]['version'])

    def test_archive_reachable_from_reading_this_map(self):
        """The exact 1920–2000 view (1.121) survives as an archive, reached from Reading this map."""
        self.open('#tab=about')
        link = self.page.locator('a.archive-link')
        expect(link).to_have_count(1)
        link.click()
        expect(self.page.locator('.archive-banner')).to_be_visible()
        expect(self.page.locator('#edition-label')).to_contain_text('1.121')
        self.assertTrue(self.page.locator('#range-toggle').is_hidden())
        # The archive keeps its closed frame: the 2000 wall, no faded tails, no open-frame cutoff line.
        self.open('#focus=annales&range=2000')
        expect(self.page.locator('.coverage-wall')).to_have_count(1)
        expect(self.page.locator('rect.unreviewed')).to_have_count(0)
        bar = self.page.locator('.entry.selected .bar-shape').bounding_box()
        wall = self.page.locator('.coverage-wall').bounding_box()
        self.assertAlmostEqual(bar['x'] + bar['width'], wall['x'], delta=2, msg='Archived Annales runs solid to the 2000 wall')
        expect(self.page.locator('.datewhy')).to_contain_text('limit of this map')
        self.page.locator('.archive-banner a').click()
        expect(self.page.locator('.archive-banner')).to_have_count(0)
        expect(self.page.locator('#edition-label')).to_contain_text(GRAPH['revision_history'][-1]['version'])

    def test_about_distinguishes_coverage_gaps_from_existing_profiles_and_critiques(self):
        self.open('#tab=about')
        about = self.page.locator('.about')
        individuals = sum(n['entry_kind'] == 'person' for n in GRAPH['nodes'])
        uncriticised = sum(not any(e['target'] == n['id'] and e.get('relationship_kind') == 'critique'
                                  and e.get('directed') for e in GRAPH['edges']) for n in GRAPH['nodes'])
        expect(about).to_contain_text(f'{individuals} standalone person entries among {len(GRAPH["people"]):,} indexed people')
        expect(about).to_contain_text(f'{uncriticised} of {len(GRAPH["nodes"])} entries have no incoming relationship classified as critique')
        expect(about).to_contain_text('those exchanges are already represented')
        expect(about).to_contain_text('reviews through 2024')
        expect(about).not_to_contain_text('“science wars” are missing')
        expect(about).not_to_contain_text('there is no Chinese, Japanese, Korean')
        profiles = about.locator('.person-coverage a[href^="#person="]')
        people = {p['id']: p for p in GRAPH['people']}
        for href in profiles.evaluate_all('links => links.map(a => a.getAttribute("href"))'):
            self.assertFalse(people[href.split('=', 1)[1]].get('node_id'), 'Profile-only examples must remain profile-only')
        label = profiles.first.inner_text()
        profiles.first.click()
        expect(self.page.locator('.person-profile')).to_contain_text(label)
        self.open('#tab=about')
        about.locator('a[href="#node=sciencewars&section=connections"]').click()
        expect(self.page.locator('.focus-layout')).to_contain_text('The Science Wars')
        self.assertTrue(any(e['source'] == 'sciencewars' and e['target'] == 'kuhn'
                            and e.get('relationship_kind') == 'critique' for e in GRAPH['edges']))
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open('#tab=about')
        about.locator('a[href="#node=masao_maruyama"]').click()
        expect(self.page.locator('.reading-header h2')).to_contain_text('Masao Maruyama')
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 391)

    def test_gemini_promotions_open_from_profiles_and_remain_on_the_timeline(self):
        packets = ['gemini-nonwestern-2026-10-24', 'gemini-black-atlantic-2026-10-24',
                   'gemini-micro-intellectual-2026-10-24']
        nodes = [node for packet in packets for node in json.loads(
            (ROOT / 'data/extension-2026' / packet / 'release/editorial-additions.json').read_text())['nodes']]
        self.assertTrue(nodes)
        people = {p['node_id']: p for p in GRAPH['people'] if p.get('node_id')}
        for node in nodes:
            self.open('#person=' + people[node['id']]['id'])
            profile = self.page.locator('.person-profile')
            expect(profile.locator('.section-heading h2')).to_contain_text(people[node['id']]['label'])
            profile.locator('.button-link.primary', has_text='Full entry').click()
            expect(self.page.locator('.reading-header h2')).to_contain_text(node['label'])
            expect(self.page.locator('.entry-chronology')).to_be_visible()
            self.open('#family=all&view=map&focus=' + node['id'])
            expect(self.page.locator('.entry.selected')).to_have_count(1)
            expect(self.page.locator('.field-panel')).to_contain_text(node['label'])
        self.open('#node=cheikh_anta_diop&section=connections&view=map')
        expect(self.page.locator('.reading-panel')).to_contain_text('culturels, techniques et industriels')
        expect(self.page.locator('.reading-panel')).to_contain_text('revised 1974 edition')
        for width in (1100, 1440):
            self.page.set_viewport_size({'width': width, 'height': 1000})
            self.page.wait_for_timeout(250)
            for side in ('incoming', 'outgoing'):
                boxes = self.page.locator('.flow-neighbor.' + side).evaluate_all(
                    'cards => cards.map(c => {const b=c.getBoundingClientRect(); return {top:b.top,bottom:b.bottom};})')
                for previous, current in zip(boxes, boxes[1:]):
                    self.assertLessEqual(previous['bottom'], current['top'])

    def test_gemini_promotions_fit_phones_and_keep_earlier_dates_explicit(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        packet = json.loads((ROOT / 'data/extension-2026/gemini-nonwestern-2026-10-24/release/editorial-additions.json').read_text())
        early = next(n for n in packet['nodes'] if 'Khald' in n['label'])
        self.open('#family=all&view=map&focus=' + early['id'])
        expect(self.page.locator('.entry.selected .chron-before').first).to_be_visible()
        self.assertIn('1377', self.page.locator('.entry.selected').inner_html())
        for nid in [early['id'], 'saidiya_hartman', 'quentin_skinner']:
            self.open('#node=' + nid + '&section=connections')
            expect(self.page.locator('.reading-header h2')).to_contain_text(GRAPH_LABELS[nid])
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 391)
        self.page.screenshot(path=str(self.artifacts / 'gemini-historians-phone.png'), full_page=True)

    def test_releasing_a_held_entry(self):
        """Four ways out of a hold: the panel link, the bar itself, empty space, Escape."""
        total = self.page.locator('.entry, .chip')
        self.open('#focus=annales')
        expect(self.page.locator('.entry.selected')).to_have_count(1)
        self.page.locator('.field-panel .release').click()
        expect(self.page.locator('.entry.selected')).to_have_count(0)
        self.assertEqual(self.page.locator('.ghost').count(), 0)
        self.assertNotIn('focus=', self.page.url)

        self.open('#focus=annales')
        self.page.locator('.entry.selected .chron-hit').click()
        expect(self.page.locator('.entry.selected')).to_have_count(0)

        self.open('#focus=annales')
        # Chart chrome (the research-cutoff caption) is empty space as far as holding is concerned.
        self.page.locator('.cutoff-label').click()
        expect(self.page.locator('.entry.selected')).to_have_count(0)

        self.open('#focus=annales&path=paradigms_and_limits')
        self.page.keyboard.press('Escape')
        expect(self.page.locator('.entry.selected')).to_have_count(0)
        expect(self.page.locator('.path-panel')).to_be_visible()
        self.assertIn('path=paradigms_and_limits', self.page.url)
        self.page.locator('.band-release text').first.click()
        expect(self.page.locator('.ghost')).to_have_count(0)

    def test_life_dates_from_wikidata(self):
        """Life dates keep provenance; publication and reception require explicit dated facts."""
        self.open('#focus=marc_bloch')
        panel = self.page.locator('.field-panel')
        expect(panel.locator('.life')).to_contain_text('Born 1886 · died 1944')
        expect(panel.locator('.life a')).to_have_attribute('href', 'https://www.wikidata.org/wiki/Q156585')
        expect(panel.locator('.life')).to_contain_text('checked 2026-10-25')
        # From revision 1.150 a death within the axis is drawn on explicit chronologies too, and ends
        # the dotted line of contributions (user: Nietzsche and Wittgenstein extended past their deaths).
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(1)
        self.open('#focus=wittgenstein')
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(1)
        expect(self.page.locator('.entry.selected .posthumous-event[data-year="1953"]')).to_have_count(1)
        self.open('#focus=gramsci')
        expect(self.page.locator('.entry.selected .posthumous')).to_have_count(0)
        expect(self.page.locator('.entry.selected .track-reception[data-year="1974"]')).to_have_count(1)
        self.open('#focus=derrida')
        expect(self.page.locator('.field-panel .life')).to_contain_text('died 2004')
        # The open frame's axis runs past 2004, so his death is drawn ...
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(1)
        # ... while the archived 2000 view still states it in the panel only.
        self.open('#focus=derrida&range=2000')
        expect(self.page.locator('#edition-label')).to_contain_text('1.121')
        expect(self.page.locator('.field-panel .life')).to_contain_text('died 2004')
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(0)
        self.open('#focus=annales')
        expect(self.page.locator('.field-panel .life')).to_have_count(0)
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(0)
        self.open('#focus=roger_chartier')
        expect(self.page.locator('.field-panel .life')).to_contain_text('living in checked sources')
        self.open('#focus=ivy_pinchbeck')
        expect(self.page.locator('.field-panel .life')).to_contain_text('Born 1898')
        self.open('#person=eric_hobsbawm')
        expect(self.page.locator('.person-profile h2 .lifespan')).to_have_text('1917–2012')
        self.open('#person=julia_cherry_spruill')
        expect(self.page.locator('.person-profile h2 .lifespan')).to_have_text('1899–1986')

    def test_remaining_canon_life_sources_on_profiles_and_timeline(self):
        """Both life overlays reach people and timeline details with their own witnesses."""
        cases = [
            ('jurgen_habermas', '1929–2026', 'died 2026',
             'https://www.bundesregierung.de/breg-de/aktuelles/bundeskanzler-merz-zum-tod-von-juergen-habermas-2410956',
             'older living biographies are not adopted.', True),
            ('hannah_arendt', '1906–1975', 'died 1975',
             'https://hac.bard.edu/about/hannaharendt/',
             'Year precision retained', True),
            ('jack_goody', '1919–2015', 'died 2015',
             'https://therai.org.uk/archives-and-manuscripts/obituaries/jack-goody/',
             'no work, career or influence interval.', True),
            ('peter_brown', '1935–', 'living in checked sources',
             'https://www.plough.com/articles/augustines-friendship-for-freedom',
             'explicitly dated July 2026 primary interview.', False),
        ]
        for person_id, lifespan, status, witness, limit, deceased in cases:
            with self.subTest(person=person_id):
                self.open(f'#person={person_id}')
                profile = self.page.locator('.person-profile')
                expect(profile.locator('h2 .lifespan')).to_have_text(lifespan)
                expect(profile.locator('.life')).to_contain_text(status)
                expect(profile.locator('.life')).to_contain_text('checked 2026-10-25')
                sources = profile.locator('.life-sources')
                sources.locator('summary').click()
                expect(sources.locator(f'a[href="{witness}"]')).to_be_visible()
                expect(sources).to_contain_text(limit)

                self.open(f'#focus={person_id}')
                panel = self.page.locator('.field-panel')
                expect(panel.locator('.life')).to_contain_text(status)
                expect(panel.locator(f'.life-sources a[href="{witness}"]')).to_have_count(1)
                expect(self.page.locator('.entry.selected .death-mark')).to_have_count(int(deceased))

    def test_remaining_canon_taylor_layer_and_named_chatterjee_critique(self):
        """The new person endpoints preserve the resource layer and named criticism."""
        self.open('#node=charles_taylor')
        expect(self.page.locator('.reading-panel .entry-type')).to_have_text('Individual theorist')
        self.open('#focus=charles_taylor')
        expect(self.page.locator('.field-panel .eyebrow')).to_have_text('Individual theorist')
        expect(self.page.locator('.field-panel .life')).to_contain_text('living in checked sources')

        self.open('#edge=edge_1498')
        panel = self.page.locator('.reading-panel')
        expect(panel.locator('#detail-title')).to_have_text('Critique')
        endpoints = panel.locator('.edge-endpoints a')
        expect(endpoints).to_have_text(['Partha Chatterjee', 'Benedict Anderson'])
        for index, node_id in enumerate(['partha_chatterjee', 'benedict_anderson']):
            route = parse_qs(endpoints.nth(index).get_attribute('href').lstrip('#'))
            self.assertEqual(route.get('node'), [node_id])
        expect(panel).to_contain_text('primary The Nation and Its Fragments pp. 4–7 freshly reread')
        expect(panel).to_contain_text('material/spiritual distinction remains his historically situated claim.')
        expect(panel).not_to_contain_text('no individual graph node')
        expect(panel.locator('.sources')).to_contain_text('The Nation and Its Fragments')

    def test_response_audit_turner_and_bloch_named_connections(self):
        """The named responses are reachable on the map and timeline, with their limits."""
        def relation(source, target, kind):
            matches = [e for e in GRAPH['edges'] if e['source'] == source
                       and e['target'] == target and e.get('relationship_kind') == kind]
            self.assertEqual(len(matches), 1, (source, target, kind))
            return matches[0]

        def inspect(edge, source_ids, qualifications):
            self.assertEqual(edge['source_ids'], source_ids)
            self.open('#edge=' + edge['id'])
            panel = self.page.locator('.reading-panel')
            expect(panel.locator('.edge-endpoints a')).to_have_text(
                [GRAPH_LABELS[edge['source']], GRAPH_LABELS[edge['target']]])
            for text in qualifications:
                expect(panel).to_contain_text(text)
            for source_id in source_ids:
                source = next(s for s in GRAPH['sources'] if s['id'] == source_id)
                expect(panel.locator('.sources > li').filter(
                    has_text=source.get('citation') or source['title'])).to_have_count(1)

        turner = 'frederick_jackson_turner'
        critics = ['j_m_s_careless', 'donald_creighton', 'william_cronon',
                   'richard_white', 'richard_hofstadter', 'philip_j_deloria', 'alan_taylor']
        critiques = [relation(critic, turner, 'critique') for critic in critics]
        self.assertEqual([critiques[0]['id'], critiques[1]['id']], ['edge_951', 'edge_957'])
        self.open('#node=' + turner + '&section=connections&view=map')
        for edge in critiques:
            expect(self.page.locator(f'.flow-neighbor.incoming[data-edge="{edge["id"]}"]')) \
                .to_contain_text(GRAPH_LABELS[edge['source']])
            expect(self.page.locator(f'.connection.incoming[data-edge="{edge["id"]}"]')) \
                .to_have_attribute('marker-end', 'url(#arrow-critique)')
        self.open('#family=all&view=map&focus=' + turner)
        for edge in critiques:
            expect(self.page.locator(f'svg.field .edge.critique[data-edge="{edge["id"]}"]')) \
                .to_have_count(1)
            expect(self.page.locator(f'details.rel[data-edge="{edge["id"]}"] > summary')) \
                .to_contain_text(GRAPH_LABELS[edge['source']])
        inspect(critiques[3], ['rea_turner_white_1994_transcription', 'rea_turner_white_steele_1995'],
                ['Richard W. Steele', 'the full chapter remains unread'])
        inspect(critiques[4], ['rea_turner_bogue_1994'], ['expressly mediated by Bogue'])
        resource = relation(turner, 'william_cronon', 'influence')
        inspect(resource, ['rea_turner_cronon_1987'],
                ['not endorsement of the frontier thesis or a teacher–student relationship'])

        bloch_edges = [relation('lucien_febvre', 'marc_bloch', 'influence'),
                       relation('durkheim', 'marc_bloch', 'influence'),
                       relation('marc_bloch', 'durkheim', 'critique'),
                       relation('marc_bloch', 'georges_duby', 'influence')]
        self.open('#node=marc_bloch&section=connections&view=map')
        for edge in bloch_edges:
            side = 'outgoing' if edge['source'] == 'marc_bloch' else 'incoming'
            expect(self.page.locator(f'.flow-neighbor.{side}[data-edge="{edge["id"]}"]')) \
                .to_have_count(1)
        # The school's debt and criticism must not become personal Émile Durkheim arrows.
        expect(self.page.locator('.neighbor-node[href*="node=emile_durkheim"]')).to_have_count(0)
        self.open('#family=all&view=map&focus=marc_bloch')
        for edge in bloch_edges:
            expect(self.page.locator(f'svg.field .edge[data-edge="{edge["id"]}"]')).to_have_count(1)
            expect(self.page.locator(f'details.rel[data-edge="{edge["id"]}"]')).to_have_count(1)
        inspect(bloch_edges[0], ['bloch_apologie_primary'],
                ['written 1941; published 1949', 'other ideas cannot be assigned to only one of them'])
        inspect(bloch_edges[1], ['bloch_apologie_primary'],
                ['does not substitute Émile Durkheim personally for Simiand'])
        school = self.page.locator('.reading-panel .edge-endpoints a').first
        self.assertEqual(parse_qs(school.get_attribute('href').lstrip('#')).get('node'), ['durkheim'])
        inspect(bloch_edges[2], ['bloch_apologie_primary'], ['gratitude and respect'])
        inspect(bloch_edges[3], ['duby_college_context'], ['not evidence of personal supervision'])

    def test_le_goff_named_debts_and_critical_exchange(self):
        """Le Goff's sources and critics remain navigable in both relationship views."""
        pairs = [('marc_bloch', 'jacques_le_goff', 'influence'),
                 ('fernand_braudel', 'jacques_le_goff', 'influence'),
                 ('lucien_febvre', 'jacques_le_goff', 'contribution'),
                 ('pierre_nora', 'jacques_le_goff', 'contribution'),
                 ('natalie_zemon_davis', 'jacques_le_goff', 'critique'),
                 ('philippe_aries', 'jacques_le_goff', 'critique'),
                 ('jacques_le_goff', 'georges_duby', 'critique')]
        edges = []
        for source, target, kind in pairs:
            matches = [e for e in GRAPH['edges'] if (e['source'], e['target'],
                       e.get('relationship_kind')) == (source, target, kind)]
            self.assertEqual(len(matches), 1, (source, target, kind))
            edges.append(matches[0])
        self.open('#node=jacques_le_goff&section=connections&view=map')
        for edge in edges:
            side = 'outgoing' if edge['source'] == 'jacques_le_goff' else 'incoming'
            other = edge['target'] if side == 'outgoing' else edge['source']
            expect(self.page.locator(f'.flow-neighbor.{side}[data-edge="{edge["id"]}"]')) \
                .to_contain_text(GRAPH_LABELS[other])
        self.open('#family=all&view=map&focus=jacques_le_goff')
        for edge in edges:
            expect(self.page.locator(f'svg.field .edge[data-edge="{edge["id"]}"]')).to_have_count(1)
            expect(self.page.locator(f'details.rel[data-edge="{edge["id"]}"]')).to_have_count(1)
        self.open('#edge=' + edges[-1]['id'])
        panel = self.page.locator('.reading-panel')
        expect(panel.locator('.edge-endpoints a')).to_have_text(['Jacques Le Goff', 'Georges Duby'])
        expect(panel).to_contain_text('balances criticism with praise')
        expect(panel).to_contain_text('Klapisch-Zuber')
        expect(panel.locator('.sources')).to_contain_text('Entretien avec Jacques Le Goff')

    def test_joan_scott_named_debts_and_critical_exchange(self):
        """Thompson's positive resource and Scott's criticism coexist in both views."""
        def relation(source, target, kind):
            matches = [e for e in GRAPH['edges'] if (e['source'], e['target'],
                       e.get('relationship_kind')) == (source, target, kind)]
            self.assertEqual(len(matches), 1)
            return matches[0]
        resource = relation('ep_thompson', 'joan_wallach_scott', 'influence')
        critique = relation('joan_wallach_scott', 'ep_thompson', 'critique')
        self.open('#node=joan_wallach_scott&section=connections&view=map')
        expect(self.page.locator(f'.flow-neighbor.incoming[data-edge="{resource["id"]}"]')) \
            .to_contain_text('E. P. Thompson')
        expect(self.page.locator(f'.flow-neighbor.outgoing[data-edge="{critique["id"]}"]')) \
            .to_contain_text('E. P. Thompson')
        self.open('#family=all&view=map&focus=joan_wallach_scott')
        for edge in (resource, critique):
            expect(self.page.locator(f'svg.field .edge[data-edge="{edge["id"]}"]')).to_have_count(1)
            expect(self.page.locator(f'details.rel[data-edge="{edge["id"]}"]')).to_have_count(1)
        self.open('#edge=' + critique['id'])
        panel = self.page.locator('.reading-panel')
        expect(panel.locator('.edge-endpoints a')).to_have_text(['Joan Wallach Scott', 'E. P. Thompson'])
        expect(panel).to_contain_text('does not claim that he ignored culture')
        expect(panel.locator('.sources')).to_contain_text('The Evidence of Experience')
        expect(panel.locator('.sources')).to_contain_text('July 2024')
        self.open('#edge=' + resource['id'])
        expect(self.page.locator('.reading-panel')).to_contain_text('cancel her criticism')
        expect(self.page.locator('.reading-panel .sources')).to_contain_text('Finding Critical History')
        # The repaired route keeps the jointly authored reply reachable personally.
        self.open('#edge=edge_1127')
        expect(self.page.locator('.reading-panel .edge-endpoints a')).to_have_text(
            ['Joan Wallach Scott', 'Geoff Eley'])
        expect(self.page.locator('.reading-panel')).to_contain_text('Keith Nield retains equal authorial credit')

    def test_stedman_jones_named_resources_and_reception(self):
        """Personal resources, criticism and mentoring remain distinct and sourced."""
        def relation(source, target, kind):
            matches = [e for e in GRAPH['edges'] if (e['source'], e['target'],
                       e.get('relationship_kind')) == (source, target, kind)]
            self.assertEqual(len(matches), 1)
            return matches[0]
        node = 'gareth_stedman_jones'
        incoming = [relation('eric_hobsbawm', node, 'influence'),
                    relation('dorothy_thompson', node, 'critique'),
                    relation('bryan_d_palmer', node, 'critique'),
                    relation('geoff_eley', node, 'critique'),
                    relation('jon_lawrence', node, 'critique'),
                    relation('patrick_joyce', node, 'critique'),
                    relation('james_vernon', node, 'critique')]
        outgoing = [relation(node, 'eric_hobsbawm', 'critique'),
                    relation(node, 'jon_lawrence', 'influence')]
        self.open('#node=' + node + '&section=connections&view=map')
        for side, edges in [('incoming', incoming), ('outgoing', outgoing)]:
            for edge in edges:
                other = edge['source'] if side == 'incoming' else edge['target']
                expect(self.page.locator(f'.flow-neighbor.{side}[data-edge="{edge["id"]}"]')) \
                    .to_contain_text(GRAPH_LABELS[other])
        self.open('#family=all&view=map&focus=' + node)
        for edge in incoming + outgoing:
            expect(self.page.locator(f'svg.field .edge[data-edge="{edge["id"]}"]')).to_have_count(1)
            expect(self.page.locator(f'details.rel[data-edge="{edge["id"]}"]')).to_have_count(1)
        self.open('#edge=' + incoming[1]['id'])
        panel = self.page.locator('.reading-panel')
        expect(panel.locator('.edge-endpoints a')).to_have_text(['Dorothy Thompson', 'Gareth Stedman Jones'])
        expect(panel).to_contain_text('Explicitly mediated through Fontes')
        expect(panel).to_contain_text('remain unread here')
        expect(panel.locator('.sources')).to_contain_text('Fontes')
        self.open('#edge=' + incoming[4]['id'])
        expect(self.page.locator('.reading-panel')).to_contain_text('Miles Taylor')
        expect(self.page.locator('.reading-panel')).to_contain_text('Mayfield and Thorne')

    def test_response_audit_web_history_comparison_is_connected_and_undirected(self):
        """Winters connects the former isolate without turning comparison into descent."""
        edges = [e for e in GRAPH['edges'] if {e['source'], e['target']}
                 == {'web_history', 'digital_history'}]
        self.assertEqual(len(edges), 1)
        edge = edges[0]
        self.assertEqual(edge['relationship_kind'], 'comparison')
        self.assertFalse(edge['directed'])
        self.assertEqual(edge['source_ids'], ['digital10_source_digital07_winters_web_archives_2018'])
        for node, other in [('web_history', 'digital_history'), ('digital_history', 'web_history')]:
            self.open(f'#node={node}&section=connections&view=map')
            card = self.page.locator(f'.associated-card[data-edge="{edge["id"]}"]')
            expect(card).to_contain_text(GRAPH_LABELS[other])
            expect(card.locator('.kind-comparison')).to_contain_text('Comparison')
            expect(self.page.locator(f'.connection[data-edge="{edge["id"]}"]')).to_have_count(0)
        card.locator('.edge-label').click()
        panel = self.page.locator('.reading-panel')
        expect(panel.locator('#detail-title')).to_have_text('Comparison')
        expect(panel.locator('.edge-endpoints')).to_contain_text('compared with · no direction')
        for qualification in ['2018', 'not a current census', 'a field-founding lineage',
                              'an equivalence between the two fields', 'Final book pagination is not used']:
            expect(panel).to_contain_text(qualification)
        witness = panel.locator('.sources > li').filter(has=self.page.locator(
            'a[href="https://sas-space.sas.ac.uk/9202/1/Web%20archives%20and%20digital%20history.pdf"]'))
        expect(witness).to_have_count(1)
        witness.locator('details > summary').click()
        expect(witness).to_contain_text('whole chapter not newly read')
        expect(witness).to_contain_text('Repository manuscript pp. 4–6')

        self.open('#family=all&view=map&focus=web_history')
        expect(self.page.locator('.entry.selected[data-id="web_history"]')).to_have_count(1)
        expect(self.page.locator('.entry.related[data-id="digital_history"]')).to_have_count(1)
        path = self.page.locator(f'svg.field .edge.comparison[data-edge="{edge["id"]}"]')
        expect(path).to_have_count(1)
        self.assertFalse(path.get_attribute('marker-start') or path.get_attribute('marker-end'))
        row = self.page.locator(f'details.rel.comparison[data-edge="{edge["id"]}"]')
        row.locator('> summary').click()
        expect(row.locator('.evidence')).to_contain_text('not a current census')
        row.locator('.rel-sources > summary').click()
        expect(row.locator('.sources > li')).to_have_count(1)
        expect(row.locator('.sources a')).to_have_attribute(
            'href', 'https://sas-space.sas.ac.uk/9202/1/Web%20archives%20and%20digital%20history.pdf')

    @staticmethod
    def family_scope(slug):
        """The family field's entries and relationships, by the rule in landing.mjs familyGraph:
        its members, person entries adjacent by any edge, and journals linked to those."""
        evidence = json.loads((ROOT / 'docs/data/evidence.json').read_text())
        graph = json.loads((ROOT / 'docs/data/graph.json').read_text())   # the published graph the page reads
        family = next(f for f in evidence['families']['families'] if f['id'] == slug)
        keep = {m['id'] for m in family['members']}
        kind = {n['id']: n.get('entry_kind') for n in graph['nodes']}
        ids = set(keep)
        for e in graph['edges']:
            if e['source'] in keep and kind.get(e['target']) == 'person': ids.add(e['target'])
            if e['target'] in keep and kind.get(e['source']) == 'person': ids.add(e['source'])
        ids &= set(kind)
        edges = [e for e in graph['edges'] if e['source'] in ids and e['target'] in ids]
        jc = graph.get('journal_catalogue') or {'nodes': [], 'edges': []}
        journal_ids = {n['id'] for n in jc['nodes']}
        journal_edges = [e for e in jc.get('edges', []) if e['source'] in journal_ids and e['target'] in ids]
        return len(ids) + len({e['source'] for e in journal_edges}), len(edges) + len(journal_edges)

    def test_family_drilldown_filters_the_field(self):
        self.open()
        self.page.locator('.family-row[data-family="annales"]').focus()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.field-page .section-heading h2')).to_have_text('Annales')
        self.assertIn('family=annales', self.page.url)
        expect(self.page.locator('svg.field')).to_be_visible()
        self.page.locator('.family-views').get_by_role('link', name='Approaches & people', exact=True).click()
        expect(self.page.locator('.family-explorer')).to_be_visible()
        self.page.locator('.family-views').get_by_role('link', name='Timeline', exact=True).click()
        expect(self.page.locator('svg.field .entry[data-id="annales"]')).to_have_count(1)
        expect(self.page.locator('svg.field .entry[data-id="military"]')).to_have_count(0)
        entries, relationships = self.family_scope('annales')
        summary = self.page.locator('.field-summary').inner_text()
        placed = int(summary.split()[0]) + (int(summary.split('·')[1].split()[0]) if 'without' in summary else 0)
        self.assertEqual(placed, entries, summary)
        self.assertIn(f'{relationships} relationships', summary)
        self.page.locator('.family-views').get_by_role('link', name='People circles', exact=True).click()
        expect(self.page.locator('svg.company')).to_be_visible()
        expect(self.page.locator('.company-panel')).to_contain_text('Annales')
        self.page.get_by_role('link', name='This family’s timeline →', exact=True).click()
        expect(self.page.locator('svg.field .entry[data-id="annales"]')).to_have_count(1)
        self.assertIn('family=annales', self.page.url)
        expect(self.page.locator('.family-note')).to_have_count(0)   # Annales has nothing shared, bridged or missing
        self.open('#family=annales&view=list')
        expect(self.page.locator('.field-table tbody tr')).to_have_count(entries)
        expect(self.page.locator('.field-table thead').first).to_contain_text('All relationships')
        # Holding an entry the family does not draw leaves the family for the full field.
        self.open('#family=annales&focus=annales')
        row = self.page.locator('.field-panel details.rel').filter(has=self.page.locator('.outside-tag')).first
        row.locator('> summary').click()
        link = row.get_by_role('link', name=re.compile('in the full field'))
        target = parse_qs(link.get_attribute('href').lstrip('#'))['focus'][0]
        link.click()
        expect(self.page).not_to_have_url(re.compile('family='))
        expect(self.page.locator(f'svg.field [data-id="{target}"].selected')).to_have_count(1)
        self.open('#family=annales&focus=military')
        expect(self.page.locator('.field-page .section-heading h2')).to_have_text('Historiography on one time axis')
        expect(self.page.locator('svg.field .entry.selected[data-id="military"]')).to_have_count(1)
        self.open('#family=social-history&view=map')
        expect(self.page.locator('.family-note')).to_contain_text('Cultural & intellectual history')   # bridges named
        expect(self.page.locator('svg.field .entry[data-id="women"]')).to_have_count(1)
        self.page.get_by_role('link', name='← All families').click()
        expect(self.page.locator('.landing-page')).to_be_visible()
        self.open('#family=all')
        expect(self.page.locator('svg.field .entry[data-id="military"]')).to_have_count(1)
        self.open('#family=annales')
        self.open('#family=nosuch')   # unknown family: the full field, not an error
        expect(self.page.locator('.field-page .section-heading h2')).to_have_text('Historiography on one time axis')
        expect(self.page.locator('.family-crumbs')).to_have_count(0)
        expect(self.page.locator('svg.field .entry[data-id="military"]')).to_have_count(1)

    def test_landing_cards_on_mobile(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open()
        expect(self.page.locator('.family-cards li')).to_have_count(12)
        self.assertTrue(self.page.locator('.landing-rows').is_hidden())
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.screenshot(path=str(self.artifacts / 'landing-mobile.png'), full_page=True)
        self.page.locator('.family-card').filter(has_text='Environment').click()
        expect(self.page).to_have_url(re.compile('family=environment'))
        self.page.screenshot(path=str(self.artifacts / 'family-mobile.png'), full_page=True)
        # On narrow screens the router defaults to the list view; landing links must still stay on the landing.
        self.open()
        self.page.get_by_role('button', name='Reviews', exact=True).click()
        expect(self.page.locator('.family-cards li')).to_have_count(12)
        self.assertIn('record=reviews', self.page.url)
        self.open('#family=annales&query=thompson')
        self.page.get_by_role('link', name='← All families').click()
        expect(self.page.locator('.landing-page')).to_be_visible()

    def test_hero_compacts_off_the_field(self):
        self.open()
        expect(self.page).to_have_title('History in Conversation')
        expect(self.page.locator('#page-title')).to_have_text('History in Conversation')
        expect(self.page.locator('.subtitle')).to_have_text('Historians, ideas and debates through time.')
        self.page.get_by_role('link', name='Explore the people circles →', exact=True).click()
        expect(self.page.locator('svg.company.overview')).to_be_visible()
        expect(self.page.locator('[data-tab="people"]')).to_have_attribute('aria-current', 'page')
        self.page.locator('.main-nav').get_by_role('link', name='Timeline', exact=True).click()
        expect(self.page.locator('svg.field')).to_be_visible()
        expect(self.page.locator('[data-tab="timeline"]')).to_have_attribute('aria-current', 'page')
        expect(self.page).to_have_title('Timeline · History in Conversation')
        self.open()
        self.assertEqual(self.page.evaluate('document.body.dataset.compact'), '')
        expect(self.page.locator('.deck')).to_be_visible()
        for fragment in ['#node=marx', '#tab=browse', '#person=eric_hobsbawm', '#tab=pathways']:
            self.open(fragment)
            self.assertEqual(self.page.evaluate('document.body.dataset.compact'), '1', fragment)
            expect(self.page.locator('.deck')).to_be_hidden()
        self.open('#node=marx')
        self.page.get_by_role('link', name='Hold in the field', exact=False).click()
        expect(self.page.locator('.entry.selected')).to_have_count(1)

    def test_person_profile_map(self):
        """Every profile opens with a compact map of the entries that name the person."""
        self.open('#tab=people&person=dipesh_chakrabarty')
        pm = self.page.locator('.person-map')
        expect(pm.locator('svg.pm-svg')).to_be_visible()
        # The map sits between the heading and "Where to read them".
        self.assertTrue(self.page.evaluate("""() => { const m = document.querySelector('.person-map');
            const h = [...document.querySelectorAll('.person-profile > h3')].find(x => x.textContent === 'Where to read them');
            return Boolean(m.compareDocumentPosition(h) & Node.DOCUMENT_POSITION_FOLLOWING)
              && Boolean(document.querySelector('.person-profile > .section-heading').compareDocumentPosition(m) & Node.DOCUMENT_POSITION_FOLLOWING); }"""))
        self.assertGreaterEqual(pm.locator('a.pm-entry').count(), 4)
        own = [e for e in GRAPH['edges'] if 'dipesh_chakrabarty' in (e['source'], e['target'])]
        expect(pm.locator('path.pm-edge')).to_have_count(len(own))
        expect(pm.locator('a.pm-entry.own')).to_have_count(1)
        expect(pm.locator('a.pm-entry[data-id="subaltern"]')).to_contain_text('HISTORIAN')
        self.assertIn('as representative historian', pm.locator('a.pm-entry[data-id="subaltern"]').get_attribute('aria-label'))
        self.assertIn('Dipesh Chakrabarty', pm.locator('svg.pm-svg').get_attribute('aria-label'))
        # Hover and keyboard focus both read the entry and the role out.
        pm.locator('a.pm-entry[data-id="eric_hobsbawm"] .chron-hit').hover()
        expect(pm.locator('.pm-readout')).to_contain_text('criticises')
        pm.locator('a.pm-entry[data-id="subaltern"]').focus()
        expect(pm.locator('.pm-readout')).to_contain_text('Subaltern Studies')
        self.page.keyboard.press('Enter')
        self.page.wait_for_function("() => location.hash.includes('node=subaltern')")
        self.open('#tab=people&person=dipesh_chakrabarty')
        expect(self.page.locator('.person-profile .button-link.primary')).to_have_text('Full entry & relationships →')
        self.page.locator('.person-map .pm-open').click()
        self.page.wait_for_function("() => location.hash.includes('focus=dipesh_chakrabarty')")
        expect(self.page.locator('.entry.selected')).to_have_count(1)
        # A roster-only person: their roster entries, no own entry, no edges.
        roster = [n['id'] for n in GRAPH['nodes'] if any(r['person_id'] == 'anna_clark' for r in n.get('representative_people', []))]
        self.assertGreaterEqual(len(roster), 3)
        self.open('#person=anna_clark')
        expect(self.page.locator('.person-map a.pm-entry')).to_have_count(len(roster))
        expect(self.page.locator('.person-map path.pm-edge')).to_have_count(0)
        expect(self.page.locator('.person-map a.pm-entry.own')).to_have_count(0)
        expect(self.page.locator('.person-map .pm-open')).to_have_text('Find them in the field →')
        # The archive draws its own people against the 2000 wall.
        self.open('#person=dipesh_chakrabarty&range=2000')
        expect(self.page.locator('.person-map line.pm-wall')).to_have_count(1)
        expect(self.page.locator('.person-map path.pm-edge')).to_have_count(0)
        # A phone: stacked rows, nothing wider than the page.
        self.page.set_viewport_size({'width': 390, 'height': 844})
        for fragment in ['#tab=people&person=dipesh_chakrabarty', '#person=doug_owram', '#person=foucault']:
            self.open(fragment)
            expect(self.page.locator('.person-map svg.pm-svg')).to_be_visible()
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'), fragment)
            box = self.page.locator('.pm-scroll')
            self.assertLessEqual(box.evaluate('el => el.scrollWidth'), box.evaluate('el => el.clientWidth'), fragment)
        self.page.screenshot(path=str(self.artifacts / 'person-map-mobile.png'), full_page=True)

    @staticmethod
    def people_families():
        """Families by primary membership, as people.mjs familyIndex reads them from the published files."""
        evidence = json.loads((ROOT / 'docs/data/evidence.json').read_text())['families']['families']
        graph = json.loads((ROOT / 'docs/data/graph.json').read_text())
        rosters = {n['id']: [r['person_id'] for r in n['representative_people']] for n in graph['nodes'] if n.get('representative_people')}
        primary = {m['id']: f['id'] for f in evidence for m in f['members'] if m['primary'] and m['id'] in rosters}
        of = {}
        for entry, people in rosters.items():
            for pid in people: of.setdefault(pid, set()).add(primary[entry])
        return evidence, rosters, of

    def test_people_families_two_levels(self):
        """The people tab opens on the families; a family opens its own ring; back and the hash round-trip."""
        evidence, rosters, of = self.people_families()
        multi = sorted(pid for pid, fs in of.items() if len(fs) > 1)
        self.open('#tab=people')
        chart = self.page.locator('.company-chart svg.company.overview')
        expect(chart.locator('a.family-anchor')).to_have_count(12)
        expect(chart.locator('.dot')).to_have_count(len(multi))
        self.assertEqual(sorted(chart.locator('.dot').evaluate_all('els => els.map(e => e.dataset.id)')), multi)
        self.assertIn('families', chart.get_attribute('aria-label'))
        expect(self.page.locator('.company-panel .family-list a')).to_have_count(12)
        # Hover a person: their families light up and the panel names them.
        chart.locator('.dot[data-id="ep_thompson"] circle.core').hover()
        expect(self.page.locator('.company-panel h2')).to_contain_text('E. P. Thompson')
        expect(chart.locator('a.family-anchor.hi')).to_have_count(len(of['ep_thompson']))
        # Keyboard focus on a family previews it in the panel.
        self.page.mouse.move(0, 0)
        chart.locator('a.family-anchor[data-id="family:environment"]').focus()
        expect(self.page.locator('.company-panel h2')).to_have_text('Environment')
        # Click a family: its ring, with the entries it shares in outline.
        social = next(f for f in evidence if f['id'] == 'social-history')
        chart.locator('a.family-anchor[data-id="family:social-history"]').click()
        self.page.wait_for_function("() => location.hash.includes('family=social-history')")
        expect(self.page.locator('.section-heading h2')).to_have_text('Social history')
        ring = self.page.locator('.company-chart svg.company')
        expect(ring.locator('a.anchor')).to_have_count(sum(1 for m in social['members'] if m['id'] in rosters))
        expect(ring.locator('a.anchor.bridged')).to_have_count(sum(1 for m in social['members'] if not m['primary'] and m['id'] in rosters))
        named = {pid for m in social['members'] if m['id'] in rosters for pid in rosters[m['id']]}
        expect(ring.locator('.dot')).to_have_count(len(named))
        # Hold a person: the panel lists their other families, which open with the hold kept.
        ring.locator('.dot[data-id="ep_thompson"] circle.core').click()
        self.page.wait_for_function("() => location.hash.includes('hold=ep_thompson')")
        expect(ring.locator('.dot.selected')).to_have_count(1)
        expect(self.page.locator('.company-panel .panel-families')).to_contain_text('Cultural & intellectual history')
        self.page.locator('.company-panel .panel-families').get_by_role('link', name='Cultural & intellectual history').click()
        self.page.wait_for_function("() => location.hash.includes('family=cultural-and-intellectual-history') && location.hash.includes('hold=ep_thompson')")
        expect(self.page.locator('.section-heading h2')).to_have_text('Cultural & intellectual history')
        expect(self.page.locator('.company-chart .dot.selected[data-id="ep_thompson"]')).to_have_count(1)
        # Back through history, then the back control.
        self.page.go_back()
        self.page.wait_for_function("() => location.hash.includes('family=social-history')")
        expect(self.page.locator('.section-heading h2')).to_have_text('Social history')
        self.page.locator('.family-crumbs').get_by_role('link', name='← All families').click()
        self.page.wait_for_function("() => !location.hash.includes('family=')")
        expect(self.page.locator('svg.company.overview a.family-anchor')).to_have_count(12)
        # The profile breadcrumb returns to the family level and its hold.
        self.open('#tab=people&family=social-history&hold=ep_thompson')
        self.page.locator('.company-panel').get_by_role('link', name='Profile: where to read them →').click()
        expect(self.page.locator('.person-profile h2')).to_contain_text('E. P. Thompson')
        self.page.locator('.breadcrumbs').get_by_role('link', name='Social history').click()
        self.page.wait_for_function("() => location.hash.includes('family=social-history') && location.hash.includes('hold=ep_thompson') && !location.hash.includes('person=')")
        expect(self.page.locator('.company-chart .dot.selected[data-id="ep_thompson"]')).to_have_count(1)
        # Old links: a held entry opens its family; family=all keeps every entry on one ring.
        self.open('#tab=people&hold=women')
        expect(self.page.locator('.company-chart a.anchor.selected[data-id="women"]')).to_have_count(1)
        expect(self.page.locator('.family-crumbs')).to_be_visible()
        self.open('#tab=people&family=all')
        expect(self.page.locator('.company-chart a.anchor')).to_have_count(len(rosters))
        self.open('#tab=people&family=nosuch')
        expect(self.page.locator('svg.company.overview a.family-anchor')).to_have_count(12)
        # A search lights up matching people and counts them per family.
        self.open('#tab=people&query=Foucault')
        self.assertGreater(self.page.locator('svg.company.overview .dot:not(.mute)').count(), 0)
        expect(self.page.locator('svg.company.overview a.family-anchor tspan.n').first).to_contain_text('match')
        self.page.screenshot(path=str(self.artifacts / 'people-families.png'), full_page=True)

    def test_people_without_evidence_and_on_phones(self):
        """Without evidence the people tab is one ring; phones retain circles and the family list."""
        self.page.route('**/data/evidence.json', lambda route: route.abort())
        self.open('#tab=people')
        _, rosters, _ = self.people_families()
        expect(self.page.locator('.company-chart a.anchor')).to_have_count(len(rosters))
        expect(self.page.locator('.family-anchor')).to_have_count(0)
        self.open('#tab=people&family=social-history')
        expect(self.page.locator('.company-chart a.anchor')).to_have_count(len(rosters))
        self.page.unroute('**/data/evidence.json')
        self.page.set_viewport_size({'width': 420, 'height': 900})
        self.page.goto(URL + '#tab=people')
        self.page.reload()   # a hash change alone would keep the failed load
        self.page.wait_for_function("() => document.getElementById('workspace').dataset.route === location.hash")
        expect(self.page.locator('.company-chart')).to_be_visible()
        expect(self.page.locator('.company-panel .family-list a')).to_have_count(12)
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.locator('.company-panel .family-list').get_by_role('link', name='Environment').click()
        self.page.wait_for_function("() => location.hash.includes('family=environment')")
        expect(self.page.locator('.company-panel .panel-entries a')).to_have_count(2)
        expect(self.page.locator('.register-section')).to_be_visible()

    def test_archive_pathway_lists_only_archive_entries(self):
        """The 2000 archive predates some pathway entries: they are left out, not looked up."""
        archive = {n['id'] for n in json.loads((ROOT / 'docs/data/graph-2000.json').read_text())['nodes']}
        pathways = json.loads((ROOT / 'docs/data/pathways.json').read_text())['pathways']
        caribbean = next(p for p in pathways if p['id'] == 'caribbean_african_anticolonial')
        present = [i for i in caribbean['node_ids'] if i in archive]
        self.assertLess(len(present), len(caribbean['node_ids']))
        self.open('#range=2000&pathway=caribbean_african_anticolonial')
        expect(self.page.locator('.reading-sequence>li')).to_have_count(len(present))
        self.assertEqual(self.page.locator('.reading-sequence h3 a').evaluate_all("els => els.map(a => new URLSearchParams(a.getAttribute('href').slice(1)).get('node'))"), present)
        expect(self.page.locator('.section-heading .eyebrow')).to_contain_text(f'{len(present)} ENTRIES')
        self.open('#range=2000&tab=pathways')
        expect(self.page.locator('.pathway-card')).to_have_count(sum(1 for p in pathways if any(i in archive for i in p['node_ids'])))
        expect(self.page.locator('.section-heading')).to_contain_text(f"{sum(1 for p in pathways if any(i in archive for i in p['node_ids']))} routes")
        self.open('#range=2000&path=caribbean_african_anticolonial')
        expect(self.page.locator('.path-panel ol').first.locator('> li')).to_have_count(len(present))
        # The live view keeps the full list after visiting the archive.
        self.page.goto(URL + '#pathway=caribbean_african_anticolonial')
        self.page.wait_for_function("() => document.getElementById('workspace').dataset.route === location.hash")
        expect(self.page.locator('.reading-sequence>li')).to_have_count(len(caribbean['node_ids']))
        expect(self.page.locator('[data-tab="pathways"] span')).to_have_text(str(len(pathways)))

    def test_public_contents_allowlist(self):
        actual = {str(p.relative_to(ROOT / 'docs')) for p in (ROOT / 'docs').rglob('*') if p.is_file()}
        expected = {'index.html', 'styles.css', 'app.js', 'core.mjs', 'field.mjs', 'people.mjs', '.nojekyll', 'data/graph.json', 'data/pathways.json'}
        expected.update({'records.mjs', 'data/overview.json'})
        expected.update({'dissertations.mjs', 'dissertations.css', 'data/dissertations/index.json', 'data/dissertations/links.json'})
        expected.update(f'data/dissertations/{i:02x}.json' for i in range(32))
        if (Path(__file__).resolve().parents[1] / 'data/evidence-layer/site-people.json').exists():
            expected.add('data/people-records.json')
        expected.update({'landing.mjs', 'chronology.mjs'})
        published = json.loads((ROOT / 'docs/data/graph.json').read_text())
        scope = published.get('scope', {})
        if (scope.get('archive') or scope.get('extension') or {}).get('baseline_asset'):
            expected.add('data/graph-2000.json')   # the exact 2000 view, published only as an archive
        if (ROOT / 'data/evidence-layer/site-evidence.json').exists():
            expected.add('data/evidence.json')     # evidence-layer aggregates, published when built
        self.assertEqual(actual, expected)
        for private_path in ['openalex-api-key.txt', 'MEMORY.md', 'Clifford/', '.git/config']:
            response = self.page.request.get(URL + private_path)
            self.assertEqual(response.status, 404, private_path)


if __name__ == '__main__':
    unittest.main()
