"""Browser acceptance checks. Requires Playwright Chromium and a running preview.

Run: python3 -m unittest tests.test_site_browser -v
Optional URL: HISTORIOGRAPHY_SITE_URL=http://127.0.0.1:4173/
"""
import json
import os
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
        expect(self.page.locator('.field-page, .layer-card, .entry-card, .focus-layout, .school-layout, .person-card, .person-profile, .pathway-card, .pathway-layout, .about, .empty').first).to_be_visible()

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
        expect(self.page.locator('.field-page')).to_be_visible()
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
        self.page.locator('#neighbor-layer').select_option('intellectual_connections')
        self.assertTrue(all('Thinkers' in n.inner_text() for n in self.page.locator('.neighbor-node').all()))
        self.page.screenshot(path=str(self.artifacts / 'neighborhood-desktop.png'), full_page=True)
        self.page.get_by_role('button', name='List', exact=True).click()
        expect(self.page.locator('.relationship-list')).to_be_visible()

    def test_pathways_and_direct_links(self):
        self.open('#tab=pathways')
        expect(self.page.locator('.pathway-card')).to_have_count(13)
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
        expect(self.page.locator('.field-page')).to_be_visible()

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
        self.open()
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
        bb = last.locator('.bar-shape').bounding_box()
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

        # Dates describe the label, never influence; an open-ended label runs to the coverage wall.
        self.open('#focus=annales')
        note = self.page.locator('.datewhy')
        expect(note).to_contain_text('From 1929')
        expect(note).to_contain_text('limit of this atlas')
        expect(note).not_to_contain_text('influential through')
        bar = self.page.locator('.entry.selected .bar-shape').bounding_box()
        wall = self.page.locator('.coverage-wall').bounding_box()
        self.assertAlmostEqual(bar['x'] + bar['width'], wall['x'], delta=2, msg='Annales must run solid to the 2000 wall')
        expect(self.page.locator('.entry.selected .bar-fade')).to_have_count(1)
        # "Earlier roots" enters as already established: a lead-in, no start cap, and honest words.
        self.open('#focus=military')
        expect(self.page.locator('.entry.selected .bar-lead')).to_have_count(1)
        expect(self.page.locator('.entry.selected .bar-cap.start')).to_have_count(0)
        expect(self.page.locator('.datewhy')).to_contain_text('Earlier roots, undated')
        expect(self.page.locator('.datewhy')).to_contain_text('not its origin')

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
        self.page.locator('.entry.selected .bar-shape').click()
        expect(self.page.locator('.entry.selected')).to_have_count(0)

        self.open('#focus=annales')
        # Chart chrome (the coverage caption) is empty space as far as holding is concerned.
        self.page.locator('.coverage-label').click()
        expect(self.page.locator('.entry.selected')).to_have_count(0)

        self.open('#focus=annales&path=paradigms_and_limits')
        self.page.keyboard.press('Escape')
        expect(self.page.locator('.entry.selected')).to_have_count(0)
        expect(self.page.locator('.path-panel')).to_be_visible()
        self.assertIn('path=paradigms_and_limits', self.page.url)
        self.page.locator('.band-release text').first.click()
        expect(self.page.locator('.ghost')).to_have_count(0)

    def test_life_dates_from_wikidata(self):
        """Deaths are drawn only for people, with provenance, and posthumous reception is hatched."""
        self.open('#focus=marc_bloch')
        panel = self.page.locator('.field-panel')
        expect(panel.locator('.life')).to_contain_text('Born 1886 · died 1944')
        expect(panel.locator('.life a')).to_have_attribute('href', 'https://www.wikidata.org/wiki/Q156585')
        expect(panel.locator('.life')).to_contain_text('retrieved 2026-09-17')
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(1)
        self.open('#focus=gramsci')
        expect(self.page.locator('.entry.selected .posthumous')).to_have_count(1)
        expect(self.page.locator('.field-panel .posthumous-note')).to_contain_text('after 1937')
        self.open('#focus=derrida')
        expect(self.page.locator('.field-panel .life')).to_contain_text('died 2004')
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(0)
        self.open('#focus=annales')
        expect(self.page.locator('.field-panel .life')).to_have_count(0)
        expect(self.page.locator('.entry.selected .death-mark')).to_have_count(0)
        self.open('#focus=roger_chartier')
        expect(self.page.locator('.field-panel .life')).to_contain_text('living at retrieval')
        self.open('#focus=ivy_pinchbeck')
        expect(self.page.locator('.field-panel .life')).to_contain_text('c. 1898')
        self.open('#person=eric_hobsbawm')
        expect(self.page.locator('.person-profile h2 .lifespan')).to_have_text('1917–2012')
        self.open('#person=julia_cherry_spruill')
        expect(self.page.locator('.person-profile h2 .lifespan')).to_have_count(0)

    def test_hero_compacts_off_the_field(self):
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

    def test_public_contents_allowlist(self):
        actual = {str(p.relative_to(ROOT / 'docs')) for p in (ROOT / 'docs').rglob('*') if p.is_file()}
        self.assertEqual(actual, {'index.html', 'styles.css', 'app.js', 'core.mjs', 'field.mjs', '.nojekyll', 'data/graph.json', 'data/pathways.json'})
        for private_path in ['openalex-api-key.txt', 'MEMORY.md', 'Clifford/', '.git/config']:
            response = self.page.request.get(URL + private_path)
            self.assertEqual(response.status, 404, private_path)


if __name__ == '__main__':
    unittest.main()
