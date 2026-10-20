"""Unit checks for the tier-2 US dissertation adapters (synthetic fixtures; no network)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import harvest_us_history_dissertations as t1  # noqa: E402
import harvest_us_history_dissertations_tier2 as t2  # noqa: E402

CONFIG = json.loads((Path(__file__).resolve().parents[1] / 'data/field-research/us-dissertations-tier2-2026-10-14/harvest-config.json').read_text())
STREAM = {s['id']: s for s in CONFIG['streams']}
NOW = '2026-10-14T00:00:00+00:00'


def build(adapter, stream_id, cand, raw, extra=None):
    item = t2.ADAPTERS[adapter]['item'](cand, raw, extra, STREAM[stream_id], NOW)
    rec_extra = item.pop('_record')
    r, keep, reasons = t1.build_record(item, STREAM[stream_id])
    r.update(rec_extra)
    return r, keep, reasons


class TierOneUnchanged(unittest.TestCase):
    def test_tier2_reuses_tier1_functions(self):
        self.assertIs(t2.t1.build_record, t1.build_record)
        self.assertIs(t2.match_aha, t1.match_aha)
        self.assertTrue(issubclass(t2.StrictFetcher, t1.Fetcher))


class RobotsStrictness(unittest.TestCase):
    def test_unreachable_robots_means_disallow_all(self):
        with tempfile.TemporaryDirectory() as d:
            f = t2.StrictFetcher('TestAgent/1.0 (test)', 0, Path(d))

            def boom(method, url, timeout):
                raise HTTPError(url, 502, 'Bad Gateway', {}, None)
            f._raw = boom
            t2.time.sleep, saved = (lambda s: None), t2.time.sleep
            try:
                rp = f.robots_for('example.org')
            finally:
                t2.time.sleep = saved
            self.assertFalse(rp.can_fetch('https://example.org/anything'))
            self.assertIn('example.org', f.blocked)

    def test_dspace_a2_robots_allow_item_pages_not_api(self):
        text = ('User-agent: *\nDisallow: /search\nDisallow: /items/*/full\nAllow: /server/api/core/bitstreams\n'
                'Disallow: /server/api/*\nDisallow: /server/api\nDisallow: /server/oai/*\nCrawl-delay: 10\n')
        rp = t1.Robots(text, CONFIG['user_agent'])
        self.assertTrue(rp.can_fetch('https://h.edu/handle/1808/5430'))
        self.assertTrue(rp.can_fetch('https://h.edu/sitemap0.xml'))
        self.assertTrue(rp.can_fetch('https://h.edu/server/api/core/bitstreams/x/content'))
        self.assertFalse(rp.can_fetch('https://h.edu/server/api/core/items/x/bundles'))
        self.assertFalse(rp.can_fetch('https://h.edu/items/x/full'))
        self.assertEqual(rp.crawl_delay, 10)


def unc_work(affiliation='Department of History', degree='Doctor of Philosophy', rtype='Dissertation'):
    return {'title': ['Learning to be nobles'], 'creators': [{'name': ['Doe, Jane'], 'affiliation': [affiliation]}],
            'advisors': [{'name': ['Smith, Ann']}], 'date_issued': '2009-05', 'graduation_year': '2009', 'degree': degree,
            'resource_type': [rtype], 'abstract': ['x'], 'access_right': ['Open access'], 'id': 'abc123'}


class UNCAdapter(unittest.TestCase):
    cand = {'key': 'abc123'}

    def test_history_phd_kept_and_open_pdf_from_work_page(self):
        extra = t2.unc_html_meta('<meta name="citation_pdf_url" content="http://cdr.lib.unc.edu/downloads/zw12z599n" />')
        r, keep, _ = build('unc_hyrax', 'unc-history', self.cand, unc_work(), extra)
        self.assertTrue(keep)
        self.assertTrue(r['department_rule_exact'])
        self.assertEqual(r['access_category'], 'open_pdf')
        self.assertEqual(r['pdf_urls'], ['https://cdr.lib.unc.edu/downloads/zw12z599n'])
        self.assertEqual(r['item_url'], 'https://cdr.lib.unc.edu/concern/dissertations/abc123')
        self.assertEqual((r['year'], r['advisors']), (2009, ['Smith, Ann']))

    def test_art_history_and_masters_excluded(self):
        self.assertFalse(build('unc_hyrax', 'unc-history', self.cand, unc_work('Department of Art and Art History'))[1])
        self.assertFalse(build('unc_hyrax', 'unc-history', self.cand, unc_work(degree='Master of Arts'))[1])

    def test_missing_degree_is_kept_but_needs_aha_match(self):
        r, keep, _ = build('unc_hyrax', 'unc-history', self.cand, unc_work(degree=None))
        self.assertTrue(keep)
        r['degree_evidence'] = 'weak: ' + ' | '.join(r['degree'])
        self.assertRegex(r['degree'][0], STREAM['unc-history']['degree']['weak_regex'])
        built = {'unc-history': ([r], [], {'fetch': {'examined': 1}})}
        recs, _, _ = t2.finalize([STREAM['unc-history']], built, {'5210': []}, 2005)
        self.assertEqual(recs[0]['eligibility'], 'needs_review')
        self.assertIn('degree not recorded', recs[0]['eligibility_basis'])

    def test_embargo_wording_without_pdf(self):
        extra = t2.unc_html_meta('<p>This work is under embargo until 2027-05-01.</p>')
        r, keep, _ = build('unc_hyrax', 'unc-history', self.cand, unc_work(), extra)
        self.assertEqual((r['access_category'], r['pdf_urls']), ('embargoed', []))


def uva_work(program='History - Graduate School of Arts and Sciences', degree='PHD (Doctor of Philosophy)',
             visibility='open', release='2024-07-10T00:00:00Z', files=True):
    return {'id': 'c247dt148', 'visibility': visibility, 'embargo': {'releaseDate': release, 'releaseVisibility': 'open'},
            'files': [{'mimeType': 'application/pdf', 'name': '1_Doe_Jane_2022_PHD.pdf'}] if files else [],
            'publishedAt': '2022-07-10T00:00:00Z', 'program': program, 'degree': degree, 'title': 'A title',
            'author': {'firstName': 'Jane', 'lastName': 'Doe', 'department': program},
            'advisors': [{'firstName': 'Ann', 'lastName': 'Smith'}], 'abstract': 'x'}


class UVAAdapter(unittest.TestCase):
    cand = {'key': 'c247dt148'}

    def test_open_history_phd(self):
        r, keep, _ = build('uva_libra', 'uva-history', self.cand, uva_work())
        self.assertTrue(keep)
        self.assertEqual(r['access_category'], 'open_pdf')
        self.assertEqual(r['pdf_urls'], ['https://libraetd.lib.virginia.edu/public_view/c247dt148/download?file=1_Doe_Jane_2022_PHD.pdf'])
        self.assertEqual(r['authors'], ['Doe, Jane'])

    def test_access_states(self):
        self.assertEqual(build('uva_libra', 'uva-history', self.cand, uva_work(visibility='uva', release='2030-07-30T00:00:00Z', files=False))[0]['access_category'], 'embargoed')
        r = build('uva_libra', 'uva-history', self.cand, uva_work(visibility='uva', release='2138-04-30T00:00:00Z', files=False))[0]
        self.assertEqual((r['access_category'], r['pdf_urls']), ('restricted', []))
        self.assertEqual(build('uva_libra', 'uva-history', self.cand, uva_work(files=False))[0]['access_category'], 'no_public_pdf')

    def test_other_programmes_and_degrees_excluded(self):
        self.assertFalse(build('uva_libra', 'uva-history', self.cand, uva_work(program='Architectural History - School of Architecture'))[1])
        self.assertFalse(build('uva_libra', 'uva-history', self.cand, uva_work(degree='MA (Master of Arts)'))[1])
        self.assertTrue(build('uva_libra', 'uva-history', self.cand, uva_work(program='Corcoran Department of History'))[1])


def uf_hit(accesscode='public', embargoend=None, discipline='History', level='Doctorate', kw=()):
    h = {'bibid': 'UFE0024422', 'vid': '00001', 'title': 'Making a Sunbelt Place', 'creator': ['Bliss, A'],
         'subject_keyword': list(kw), 'publication_date': '2010', 'general_note': ['Adviser: Colburn, David R.', 'Thesis (Ph.D.)--University of Florida, 2010.'],
         'accesscode': accesscode, 'genre': ['theses']}
    if embargoend:
        h['embargoend'] = embargoend
    if discipline:
        h['etd_degree_discipline'] = discipline
    if level:
        h['etd_degree_level'] = level
    return h


class FloridaAdapter(unittest.TestCase):
    cand = {'key': 'UFE0024422_00001'}
    files = {'pdf': ['bliss_a.pdf'], 'txt': ['bliss_a_pdf.txt']}

    def test_public_item_gets_image_server_pdf(self):
        r, keep, _ = build('ufl_ufdc', 'florida-history', self.cand, uf_hit(), self.files)
        self.assertTrue(keep)
        self.assertEqual(r['pdf_urls'], ['https://ufdcimages.uflib.ufl.edu/UF/E0/02/44/22/00001/bliss_a.pdf'])
        self.assertEqual((r['access_category'], r['advisors']), ('open_pdf', ['Colburn, David R']))

    def test_campus_item_never_exposes_pdf_even_if_listed(self):
        r, keep, _ = build('ufl_ufdc', 'florida-history', self.cand, uf_hit(accesscode='campus', embargoend='2011-05-31'), self.files)
        self.assertTrue(keep)
        self.assertEqual((r['access_category'], r['pdf_urls'], r['pdf_open']), ('restricted', [], False))
        r = build('ufl_ufdc', 'florida-history', self.cand, uf_hit(accesscode='public', embargoend='2027-05-31'), self.files)[0]
        self.assertEqual((r['access_category'], r['pdf_urls']), ('embargoed', []))
        r = build('ufl_ufdc', 'florida-history', self.cand, uf_hit(accesscode=None), self.files)[0]
        self.assertEqual((r['access_category'], r['pdf_urls']), ('no_public_pdf', []))

    def test_department_from_subject_headings(self):
        legacy = uf_hit(discipline=None, level=None, kw=['History thesis, Ph.D', 'Dissertations, Academic | History. | UF'])
        r, keep, _ = build('ufl_ufdc', 'florida-history', self.cand, legacy)
        self.assertTrue(keep and r['department_rule_exact'])
        art = uf_hit(discipline=None, level=None, kw=['Art History thesis, Ph.D.'])
        self.assertFalse(build('ufl_ufdc', 'florida-history', self.cand, art)[1])
        ma = uf_hit(discipline=None, level='Masters', kw=['History | Dissertations, Academic | UF', 'History thesis, M.A.'])
        ma['general_note'] = ['Thesis (M.A.)--University of Florida, 2008.']
        self.assertFalse(build('ufl_ufdc', 'florida-history', self.cand, ma)[1])


def dspace_page(discipline=('History',), level='Ph.D.', status='open.access'):
    api = 'https://h.edu/server/api'
    item = f'{api}/core/items/11111111-2222-3333-4444-555555555555'
    bundle = f'{api}/core/bundles/b1'
    bit = f'{api}/core/bitstreams/99999999-2222-3333-4444-555555555555'
    md = {'dc.title': [{'value': 'Swords into ploughshares'}], 'dc.contributor.author': [{'value': 'Mack, John'}],
          'dc.date.issued': [{'value': '2009-04-21'}], 'dc.thesis.degreeLevel': [{'value': level}],
          'dc.contributor.advisor': [{'value': 'Earle, J'}], 'dc.contributor.author.email': [{'value': 'x@y.edu'}]}
    md['dc.thesis.degreeDiscipline'] = [{'value': v} for v in discipline]
    cache = {
        item: {'data': {'type': 'item', 'uuid': item.rsplit('/', 1)[1], 'handle': '1808/5430', 'metadata': md}},
        f'{item}/accessStatus': {'data': {'type': 'accessStatus', 'status': status}},
        f'{item}/bundles?size=9999': {'data': {'pageInfo': {'totalElements': 1}, '_links': {'page': [{'href': bundle}]}}},
        bundle: {'data': {'type': 'bundle', '_name': 'ORIGINAL'}},
        f'{bundle}/bitstreams?size=5': {'data': {'pageInfo': {'totalElements': 1}, '_links': {'page': [{'href': bit}]}}},
        bit: {'data': {'type': 'bitstream', '_name': 'Mack_ku_0099D.pdf', 'uuid': bit.rsplit('/', 1)[1], 'sizeBytes': 912775,
                       '_links': {'content': {'href': f'{bit}/content'}}}},
        f'{api}/authz/authorizations/canDownload_core.bitstream_{bit.rsplit("/", 1)[1]}': {'data': {'type': 'authorization'}},
    }
    state = json.dumps({'NGRX_STATE': {'core': {'cache/object': cache}}}).replace('"', '&q;')
    return f'<html><script id="dspace-angular-state" type="application/json">{state}</script></html>'


class DSpaceHtmlAdapter(unittest.TestCase):
    def parse(self, page, stream='kansas-history'):
        got = t2.dspace_item_from_state(t2.dspace_state(page), STREAM[stream]['api_base'], '1808/5430')
        cand = {'key': '1808/5430', 'url': 'https://h.edu/handle/1808/5430'}
        return build('dspace_html', stream, cand, got) + (got,)

    def test_rebuilt_item_goes_through_tier1_rules(self):
        r, keep, _, got = self.parse(dspace_page())
        self.assertTrue(keep)
        self.assertEqual(r['access_category'], 'open_pdf')
        self.assertEqual(r['pdf_urls'], ['https://h.edu/server/api/core/bitstreams/99999999-2222-3333-4444-555555555555/content'])
        self.assertEqual(r['item_url'], 'https://kuscholarworks.ku.edu/handle/1808/5430')
        self.assertIsNone(r['api_item_url'])  # /server/api/core/items is robots-disallowed on these hosts
        self.assertNotIn('dc.contributor.author.email', r['metadata'])
        self.assertEqual(got['can_download'], ['99999999-2222-3333-4444-555555555555'])

    def test_art_history_masters_and_embargo(self):
        self.assertFalse(self.parse(dspace_page(discipline=('History of Art',)))[1])
        self.assertFalse(self.parse(dspace_page(level='M.A.'))[1])
        self.assertEqual(self.parse(dspace_page(status='embargo'))[0]['access_category'], 'embargoed')

    def test_arizona_graduate_college_value_set_aside(self):
        page = dspace_page().replace('dc.thesis.degreeDiscipline', 'thesis.degree.discipline').replace('dc.thesis.degreeLevel', 'thesis.degree.level')
        page = page.replace('&q;value&q;: &q;Ph.D.&q;', '&q;value&q;: &q;doctoral&q;')
        page = page.replace('[{&q;value&q;: &q;History&q;}]', '[{&q;value&q;: &q;Graduate College&q;}, {&q;value&q;: &q;History&q;}]')
        r, keep, _, _ = self.parse(page, 'arizona-history')
        self.assertTrue(keep and r['department_rule_exact'])

    def test_missing_access_status_falls_back_to_can_download(self):
        page = dspace_page(status=None)
        r, keep, _, got = self.parse(page)
        self.assertEqual((r['access_category'], r['access_basis']), ('open_pdf', 'anonymous canDownload authorization in the page render'))
        got['can_download'] = []
        cand = {'key': '1808/5430', 'url': 'https://h.edu/handle/1808/5430'}
        self.assertEqual(build('dspace_html', 'kansas-history', cand, got)[0]['access_category'], 'restricted')

    def test_page_without_state(self):
        self.assertIsNone(t2.dspace_state('<html><ds-app></ds-app></html>'))


class OpenAlexSelection(unittest.TestCase):
    def test_selection_reasons(self):
        aha = [{'id': '1', 'dissertator': 'Mack, John N.', 'year': 2009}]
        rows = [
            {'id': 'W1', 'title': 'Swords into ploughshares', 'year': 2009, 'authors': ['John N. Mack'],
             'landing': ['https://hdl.handle.net/1808/5430'], 'concepts': [], 'topics': [('x', 'y', 'Environmental Science')]},
            {'id': 'W2', 'title': 'Catalysis of things', 'year': 2012, 'authors': ['A B'],
             'landing': ['https://kuscholarworks.ku.edu/handle/1808/9999'], 'concepts': [('Chemistry', 0.9, 0)], 'topics': []},
            {'id': 'W3', 'title': 'Kansas women, 1880-1920', 'year': 2012, 'authors': ['C D'],
             'landing': ['https://kuscholarworks.ku.edu/handle/1808/7777'], 'concepts': [], 'topics': []},
            {'id': 'W4', 'title': 'Frontier towns', 'year': 2007, 'authors': ['E F'],
             'landing': ['http://dissertations.umi.com/ku:2182', 'https://kuscholarworks.ku.edu/bitstream/1808/4010/1/umi-ku-2182_1.pdf'],
             'concepts': [], 'topics': []},
            {'id': 'W5', 'title': 'A history of nothing', 'year': 2007, 'authors': ['G H'],
             'landing': ['https://www.proquest.com/docview/1312506251'], 'concepts': [], 'topics': []},
        ]
        cands, reasons = t2.openalex_candidates(rows, 'kuscholarworks.ku.edu', aha)
        keys = {c['key']: c for c in cands}
        self.assertEqual(set(keys), {'1808/5430', '1808/7777', '1808/4010'})
        self.assertEqual(keys['1808/4010']['url'], 'https://kuscholarworks.ku.edu/handle/1808/4010')
        self.assertEqual(reasons['no repository landing URL (e.g. ProQuest only)'], 1)
        self.assertIn('aha_surname_year', keys['1808/5430']['why'])
        self.assertEqual(keys['1808/7777']['url'], 'https://kuscholarworks.ku.edu/handle/1808/7777')
        self.assertEqual(reasons['not selected'], 1)


class Scrubbing(unittest.TestCase):
    def test_personal_identifiers_removed(self):
        out = t2.scrub_obj({'depositor': 'abc1x', 'author': {'computeID': 'xy9z', 'lastName': 'Doe'}, 'ip': '1.2.3.4',
                            'note': 'contact jane@x.edu'})
        self.assertEqual(out, {'author': {'lastName': 'Doe'}, 'note': 'contact [e-mail removed]'})


if __name__ == '__main__':
    unittest.main()
