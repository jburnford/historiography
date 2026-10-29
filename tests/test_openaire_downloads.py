"""Offline checks for export routing and honest download outcomes."""
from pathlib import Path
from copy import deepcopy
from contextlib import contextmanager
import json
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import download_openaire_export as job
from build_uk_dissertation_download_queue import oxford_candidate
from discover_uk_eprints_history import entries, history_code
from discover_edinburgh_history import discovery_items


class OpenAIREDownloadTests(unittest.TestCase):
    def test_network_recovery_preserves_real_access_holds(self):
        self.assertTrue(job.retryable_network_hold({'status': 'host_stopped', 'reason': 'era.ed.ac.uk: five consecutive network/5xx errors'}))
        self.assertTrue(job.retryable_network_hold({'status': 'error', 'reason': 'HTTP 503 on native API'}))
        self.assertTrue(job.retryable_network_hold({'status': 'error', 'reason': 'incomplete body 10 of20bytes'}))
        for status, reason in [('host_stopped', 'HTTP403 bot challenge'),
                               ('host_stopped', 'HTTP429'), ('restricted', 'HTTP401'),
                               ('robots_disallowed', 'robots disallows'),
                               ('error', 'HTTP404 on native API'),
                               ('partial_download', 'restricted second volume')]:
            self.assertFalse(job.retryable_network_hold({'status': status, 'reason': reason}))

    def test_edinburgh_discovery_preserves_native_pagination(self):
        item = {'uuid': 'example', 'name': 'Example thesis'}
        page = {'number': 0, 'totalPages': 11, 'totalElements': 1026}
        data = {'_embedded': {'searchResult': {'_embedded': {'objects': [
            {'_embedded': {'indexableObject': item}}]}, 'page': page}}}
        items, paging = discovery_items(data)
        self.assertEqual(items, [item])
        self.assertEqual(paging['totalElements'], 1026)

    def test_edinburgh_native_publisher_and_degree_do_not_accept_masters_or_foreign_publisher(self):
        item = {'metadata': {'dc.title': [{'value': 'Example thesis'}],
                            'dc.publisher': [{'value': 'The University of Edinburgh'}],
                            'dc.type.qualificationname': [{'value': 'PhD Doctor of Philosophy'}]}}
        fields = job.dspace_degree_fields(item, 'era.ed.ac.uk')
        self.assertEqual(job.verification(self.row('unused'), [{'fields': fields}])['status'], 'verified_uk_doctoral')
        item['metadata']['dc.type.qualificationname'] = [{'value': 'MPhil Master of Philosophy'}]
        item['metadata']['dc.type.qualificationlevel'] = [{'value': 'Doctoral'}]
        fields = job.dspace_degree_fields(item, 'era.ed.ac.uk')
        self.assertEqual(job.verification(self.row('unused'), [{'fields': fields}])['status'], 'needs_metadata_review')
        item['metadata']['dc.type.qualificationname'] = [{'value': 'PhD Doctor of Philosophy'}]
        item['metadata']['dc.publisher'] = [{'value': 'A foreign university'}]
        fields = job.dspace_degree_fields(item, 'era.ed.ac.uk')
        self.assertEqual(job.verification(self.row('unused'), [{'fields': fields}])['status'], 'needs_metadata_review')

    def test_edinburgh_rest_uses_native_api_and_original_pdf_bundle(self):
        uid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        api = 'https://era.ed.ac.uk/server/api'
        item = {'name': 'Example thesis', 'metadata': {
            'dc.title': [{'value': 'Example thesis'}],
            'dc.publisher': [{'value': 'The University of Edinburgh'}],
            'dc.type.qualificationname': [{'value': 'PhD Doctor of Philosophy'}]},
            '_links': {'bundles': {'href': api + '/core/items/' + uid + '/bundles'}}}
        file_url = api + '/core/bitstreams/native-file/content'
        bundles = {'_embedded': {'bundles': [{'name': 'ORIGINAL', '_embedded': {
            'bitstreams': {'_embedded': {'bitstreams': [
                {'name': 'thesis.pdf', '_links': {'content': {'href': file_url}}}]}}}}]}}
        job.LOCAL.pages = []
        with patch.object(job.transport, 'follow', side_effect=[json.dumps(item), json.dumps(bundles)]) as request:
            files = job.university_dspace_candidates('https://era.ed.ac.uk/items/' + uid, '', [])
        self.assertEqual(files, [file_url])
        self.assertTrue(all(call.args[0].startswith(api) for call in request.call_args_list))
        self.assertEqual(job.verification(self.row('unused'), job.LOCAL.pages)['status'], 'verified_uk_doctoral')

    def test_birmingham_native_degree_codes_preserve_phd_mphil_distinction(self):
        page = {'fields': {'eprints.title': ['Example thesis'],
                           'eprints.institution': ['University of Birmingham'],
                           'eprints.thesis_type': ['d_ph']}}
        self.assertEqual(job.verification(self.row('unused'), [page])['status'], 'verified_uk_doctoral')
        page['fields']['eprints.thesis_type'] = ['m_ph']
        page['fields']['dc.type'] = ['Doctoral']
        self.assertEqual(job.verification(self.row('unused'), [page])['status'], 'needs_metadata_review')

    def test_native_history_discovery_excludes_natural_history_and_masters(self):
        self.assertTrue(history_code('D111'))
        self.assertTrue(history_code('HC'))
        self.assertFalse(history_code('QH'))
        self.assertFalse(history_code('subjects'))
        body = ('<p><span class="person_name">A Historian</span> (2020).'
                '<a href="http://etheses.bham.ac.uk//id/eprint/123/"><em>Example thesis.</em></a>'
                'University of Birmingham. Ph.D.</p>'
                '<p><a href="http://etheses.bham.ac.uk//id/eprint/124/">A masters thesis</a> M.Phil.</p>')
        found = list(entries(body, 'Medieval History', 'etheses.bham.ac.uk'))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['url'], 'https://etheses.bham.ac.uk/id/eprint/123')
        self.assertEqual(found[0]['authors'], 'A Historian')

    def figshare_item(self):
        return {'id': 123, 'title': 'Example thesis', 'defined_type_name': 'thesis',
                'url_public_html': 'https://sussex.figshare.com/articles/thesis/example/123',
                'custom_fields': [{'name': 'Institution', 'value': 'University of Sussex'},
                                  {'name': 'Qualification name', 'value': ['dphil']},
                                  {'name': 'Qualification level', 'value': ['doctoral']},
                                  {'name': 'Department affiliated with', 'value': ['History Theses']}],
                'files': [{'id': 456, 'name': 'complete.pdf',
                           'download_url': 'https://ndownloader.figshare.com/files/456'}]}

    def test_figshare_declared_file_id_has_one_identity_across_portal_hosts(self):
        self.assertEqual(job.normalize('https://sussex.figshare.com/ndownloader/files/456'),
                         job.normalize('https://ndownloader.figshare.com/files/456'))

    def test_sussex_api_requires_history_department_and_doctoral_qualification_before_download(self):
        api = 'https://api.figshare.com/v2/articles/123'
        item = self.figshare_item()
        with patch.object(job.transport, 'ARGS', SimpleNamespace(out=Path('/unused'))), \
                patch.object(job.transport, 'follow', return_value=json.dumps(item)), \
                patch.object(job, 'save_public_sussex_file', return_value=
                            {'path': 'saved.pdf', 'pages': 217, 'sha256': 'body'}) as request:
            result = job.fetch(self.row(api), {}, Path('/unused'))
        self.assertEqual(result['status'], 'downloaded')
        self.assertEqual(result['degree_verification']['status'], 'verified_uk_doctoral')
        self.assertEqual(request.call_args.args[0], item['files'][0])
        item['custom_fields'][-1]['value'] = ['Physics and Astronomy Theses']
        with patch.object(job.transport, 'follow', return_value=json.dumps(item)) as request:
            result = job.fetch(self.row(api), {}, Path('/unused'))
        self.assertEqual(result['status'], 'out_of_scope')
        self.assertEqual(request.call_count, 1)
        item['custom_fields'][-1]['value'] = ['History Theses']
        item['custom_fields'][1]['value'] = ['mphil']
        with patch.object(job.transport, 'follow', return_value=json.dumps(item)) as request:
            result = job.fetch(self.row(api), {}, Path('/unused'))
        self.assertEqual(result['status'], 'out_of_scope')
        self.assertEqual(request.call_count, 1)

    def test_sussex_delivery_grant_requires_exact_native_file_bucket_and_signature(self):
        grant = ('https://s3-eu-west-1.amazonaws.com/pstorage-sussex-87467812357921/456/thesis.pdf'
                 '?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Signature=signed&X-Amz-Expires=10')
        self.assertTrue(job.authorized_sussex_delivery(grant, 456))
        self.assertFalse(job.authorized_sussex_delivery(grant, 457))
        self.assertFalse(job.authorized_sussex_delivery(grant.split('?')[0], 456))
        self.assertFalse(job.authorized_sussex_delivery(grant.replace('pstorage-sussex-87467812357921', 'another-bucket'), 456))
        self.assertFalse(job.authorized_sussex_delivery(grant.replace('https:', 'http:'), 456))

    def test_sussex_content_403_stops_delivery_without_alternate_file_request(self):
        file = self.figshare_item()['files'][0]
        grant = ('https://s3-eu-west-1.amazonaws.com/pstorage-sussex-87467812357921/456/thesis.pdf'
                 '?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Signature=signed&X-Amz-Expires=10')
        host = SimpleNamespace(stopped=None, robots_block=None, rules=[])
        @contextmanager
        def request(h, url, accept):
            if url == file['download_url']:
                raise HTTPError(url, 302, 'Redirect', {'Location': grant}, None)
            raise HTTPError(url, 403, 'Forbidden', {}, None)
            yield  # context manager protocol, no response body offered
        with patch.object(job.transport, 'get_host', return_value=host), \
                patch.object(job.transport, 'ensure_robots'), \
                patch.object(job.transport, 'request', side_effect=request) as calls, \
                patch.object(job.transport, 'stop_host') as stop, \
                patch.object(job.transport, 'save_pdf') as save:
            with self.assertRaises(job.transport.Outcome) as error:
                job.save_public_sussex_file(file, Path('/unused'), [])
        self.assertEqual(error.exception.status, 'host_stopped')
        self.assertEqual(calls.call_count, 2)
        stop.assert_called_once()
        save.assert_not_called()

    def test_sussex_api_embargo_is_preserved(self):
        item = self.figshare_item(); item['is_embargoed'] = True
        with patch.object(job.transport, 'follow', return_value=json.dumps(item)) as request:
            result = job.fetch(self.row('https://api.figshare.com/v2/articles/123'), {}, Path('/unused'))
        self.assertEqual(result['status'], 'restricted')
        self.assertEqual(request.call_count, 1)

    def test_diversity_reserve_recognizes_oxford_without_excluding_other_repositories(self):
        self.assertTrue(oxford_candidate({'links': ['https://ora.ox.ac.uk/objects/uuid:example']}))
        self.assertTrue(oxford_candidate({'links': ['https://doi.org/10.5287/ora-example']}))
        self.assertFalse(oxford_candidate({'links': ['https://doi.org/10.17863/cam.example']}))
        self.assertFalse(oxford_candidate({'links': ['https://discovery.ucl.ac.uk/id/eprint/123']}))

    def test_ucl_alias_and_native_eprints_html_title(self):
        page = {'fields': {'eprints.type': ['thesis'],
                           'eprints.institution': ['UCL (University College London)'],
                           'eprints.thesis_type': ['Doctoral']},
                'page_title': 'Example thesis \n -\n UCL Discovery'}
        checked = job.verification(self.row('unused'), [page])
        self.assertEqual(checked['status'], 'verified_uk_doctoral')
        self.assertEqual(checked['awarding_institution'], ['University College London'])
        page['page_title'] = 'Another thesis - UCL Discovery'
        self.assertEqual(job.verification(self.row('unused'), [page])['status'], 'needs_metadata_review')
        page['page_title'] = 'Example thesis - Unrelated site'
        self.assertEqual(job.verification(self.row('unused'), [page])['status'], 'needs_metadata_review')

    def test_existing_pdf_uses_available_item_page_for_degree_metadata(self):
        direct = 'https://discovery.ucl.ac.uk/id/eprint/1546150/1/thesis.pdf'
        item = 'https://discovery.ucl.ac.uk/id/eprint/1546150/'
        row = self.row(direct); row['candidate_links'] = [item, direct]
        index = {direct: {'files': [], 'source_log': 'existing-holdings'}}
        with patch.object(job.transport, 'follow') as request:
            result = job.fetch(row, index, Path('/unused'))
        self.assertEqual(result['status'], 'already_held')
        self.assertEqual(request.call_args.args[0], item)

    def test_native_doctoral_type_is_valid_but_conflicting_mphil_is_held(self):
        page = {'fields': {'citation_title': ['Example thesis'],
                           'citation_dissertation_institution': ['University of St Andrews'],
                           'dc.type': ['Thesis', 'Doctoral', 'PhD Doctor of Philosophy']}}
        self.assertEqual(job.verification(self.row('unused'), [page])['status'], 'verified_uk_doctoral')
        page['fields']['type of award'] = ['MPhil']
        self.assertEqual(job.verification(self.row('unused'), [page])['status'], 'needs_metadata_review')

    def test_cambridge_download_uses_rest_without_frontend_scraping(self):
        row = self.row('https://www.repository.cam.ac.uk/handle/1810/example')
        with patch.object(job, 'cambridge_rest_attempt', return_value={'status': 'downloaded', 'files': []}) as api, \
                patch.object(job.transport, 'try_link') as frontend:
            job.fetch(row, {}, Path('/unused'))
        api.assert_called_once()
        frontend.assert_not_called()

    def test_cambridge_missing_restricted_part_is_not_a_complete_download(self):
        row = self.row('https://www.repository.cam.ac.uk/handle/1810/example')
        urls = ['https://api.repository.cam.ac.uk/part1', 'https://api.repository.cam.ac.uk/part2']
        with patch.object(job.transport, 'ARGS', SimpleNamespace(out=Path('/unused'))), \
                patch.object(job, 'university_dspace_candidates', return_value=urls), \
                patch.object(job.transport, 'follow', side_effect=[{'path': 'part1.pdf', 'pages': 100},
                             job.transport.Outcome('restricted', 'HTTP401')]):
            result = job.fetch(row, {}, Path('/unused'))
        self.assertEqual(result['status'], 'partial_download')
        self.assertEqual(len(result['files']), 1)

    def test_cambridge_angular_fallback_uses_official_rest_host_and_original_pdfs(self):
        job.LOCAL.pages = []
        uid = 'ff4137bb-fa41-44f1-82a9-a5e1766d1f40'
        api = 'https://api.repository.cam.ac.uk/server/api'
        item = {'name': 'Example thesis', 'metadata': {
            'dc.title': [{'value': 'Example thesis'}],
            'dc.type.qualificationname': [{'value': 'Doctor of Philosophy (PhD)'}],
            'dc.publisher.institution': [{'value': 'University of Cambridge'}]},
            '_links': {'bundles': {'href': api + '/core/items/' + uid + '/bundles'}}}
        file_url = api + '/core/bitstreams/file-id/content'
        bundles = {'_embedded': {'bundles': [
            {'name': 'ORIGINAL', '_embedded': {'bitstreams': {'_embedded': {'bitstreams': [
                {'name': 'thesis.pdf', '_links': {'content': {'href': file_url}}}]}}}},
            {'name': 'TEXT', '_embedded': {'bitstreams': {'_embedded': {'bitstreams': [
                {'name': 'thesis.pdf.txt', '_links': {'content': {'href': 'not-a-pdf'}}}]}}}}]}}
        with patch.object(job.transport, 'follow', side_effect=[json.dumps(item), json.dumps(bundles)]) as request:
            result = job.university_dspace_candidates('https://www.repository.cam.ac.uk/items/' + uid, '', [])
        self.assertEqual(result, [file_url])
        self.assertTrue(all(call.args[0].startswith(api) for call in request.call_args_list))
        self.assertEqual(job.verification(self.row('unused'), job.LOCAL.pages)['status'], 'verified_uk_doctoral')

    def test_cambridge_recovery_does_not_retry_actual_restrictions_or_real_api_404(self):
        self.assertTrue(job.retryable_cambridge_recovery({'status': 'not_found', 'reason': 'HTTP404 https://www.repository.cam.ac.uk/server/api/core/items/id'}))
        self.assertTrue(job.retryable_cambridge_recovery({'status': 'error', 'reason': 'HTTP 504 https://www.repository.cam.ac.uk/handle/1810/id'}))
        self.assertFalse(job.retryable_cambridge_recovery({'status': 'restricted', 'reason': 'HTTP401 https://www.repository.cam.ac.uk/server/api/core/items/id'}))
        self.assertFalse(job.retryable_cambridge_recovery({'status': 'not_found', 'reason': 'HTTP404 https://api.repository.cam.ac.uk/server/api/core/items/id'}))

    def test_robots_timeout_retry_preserves_real_access_holds(self):
        timeout = {'status': 'robots_disallowed', 'reason': 'robots.txt unreachable (TimeoutError: The read operation timed out)'}
        self.assertTrue(job.retryable_robots_timeout(timeout))
        self.assertTrue(job.retryable_robots_timeout({'status': 'already_held', 'metadata_status': timeout}))
        self.assertFalse(job.retryable_robots_timeout({'status': 'robots_disallowed', 'reason': 'robots.txt disallows /items/1'}))
        self.assertFalse(job.retryable_robots_timeout({'status': 'robots_disallowed', 'reason': 'robots.txt answered HTTP 403'}))
        self.assertFalse(job.retryable_robots_timeout({'status': 'host_stopped', 'reason': 'HTTP 429'}))

    def test_cambridge_heading_metadata_verifies_doctoral_award(self):
        job.LOCAL.pages = []
        parser = job.RepositoryParser()
        parser.feed('<meta name="citation_title" content="Example thesis">'
                    '<h2>Qualification</h2><div>Doctor of Philosophy (PhD)</div>'
                    '<h2>Awarding Institution</h2><div>University of Cambridge</div>')
        result = job.verification(self.row('https://www.repository.cam.ac.uk/items/example'), job.LOCAL.pages)
        self.assertEqual(result['status'], 'verified_uk_doctoral')
        self.assertEqual(result['awarding_institution'], ['University of Cambridge'])

    def row(self, link):
        return {'id': 'example', 'csv_row': 2, 'Title': 'Example thesis',
                'Authors': 'Author', 'Related Organizations': 'University',
                'Publication Year': '2020', 'DOI': '', 'candidate_links': [link]}

    def test_export_doi_and_download_link_have_one_canonical_identity(self):
        self.assertEqual(job.urls({'Download From': 'http://dx.doi.org/10.5287/ABC#details',
                                   'DOI': '10.5287/abc'}), ['https://doi.org/10.5287/abc'])

    def test_missing_link_is_reported_without_network(self):
        with patch.object(job.transport, 'try_link') as request:
            row = self.row(''); row['candidate_links'] = []
            result = job.fetch(row, {}, Path('/unused'))
        self.assertEqual(result['status'], 'missing_link')
        request.assert_not_called()

    def test_failed_declared_part_prevents_complete_download_status(self):
        attempt = {'status': 'downloaded', 'files': [{'path': 'first.pdf'}],
                   'part_problems': ['restricted: second part requires login']}
        with patch.object(job.transport, 'try_link', return_value=attempt):
            result = job.fetch(self.row('https://repository.example/item'), {}, Path('/unused'))
        self.assertEqual(result['status'], 'partial_download')

    def test_retired_eprints_file_can_use_item_page_after_404(self):
        attempts = [{'status': 'not_found', 'reason': 'HTTP404'},
                    {'status': 'downloaded', 'files': [{'path': 'replacement.pdf'}]}]
        with patch.object(job.transport, 'try_link', side_effect=attempts) as request:
            result = job.fetch(self.row('https://eprints.nottingham.ac.uk/10427/1/old.pdf'), {}, Path('/unused'))
        self.assertEqual(result['status'], 'downloaded')
        self.assertEqual(request.call_args_list[1].args[1], 'https://eprints.nottingham.ac.uk/10427/')

    def test_access_stop_never_triggers_item_fallback_or_alternate_doi(self):
        row = self.row('https://eprints.nottingham.ac.uk/10427/1/old.pdf')
        row['candidate_links'].append('https://doi.org/10.1234/example')
        with patch.object(job.transport, 'try_link', return_value={'status': 'host_stopped', 'reason': 'HTTP403'}) as request:
            result = job.fetch(row, {}, Path('/unused'))
        self.assertEqual(result['status'], 'host_stopped')
        self.assertEqual(request.call_count, 1)

    def test_count_requires_doctoral_award_british_awarder_and_matching_title(self):
        row = self.row('https://repository.example/item')
        page = {'fields': {'citation_title': ['Example thesis'],
                           'type of award': ['DPhil'],
                           'awarding institution': ['University of Oxford']}}
        self.assertEqual(job.verification(row, [page])['status'], 'verified_uk_doctoral')
        page['fields']['type of award'] = ['MPhil']
        self.assertEqual(job.verification(row, [page])['status'], 'needs_metadata_review')
        page['fields']['type of award'] = ['PhD']
        page['fields']['awarding institution'] = ['York University']
        self.assertEqual(job.verification(row, [page])['status'], 'needs_metadata_review')
        page['fields']['awarding institution'] = ['University of Oxford']
        page['fields']['citation_title'] = ['An unrelated deposited work']
        self.assertEqual(job.verification(row, [page])['status'], 'needs_metadata_review')

    def test_count_excludes_duplicate_files_short_abstracts_and_partial_works(self):
        row = {'status': 'downloaded', 'title': 'Example', 'authors': 'Author',
               'degree_verification': {'status': 'verified_uk_doctoral',
                                       'awarding_institution': ['University of Oxford']},
               'files': [{'sha256': 'same-pdf', 'pages': 300}]}
        duplicate = deepcopy(row); duplicate['title'] = 'A different exported title'
        short = deepcopy(row); short['files'] = [{'sha256': 'abstract', 'pages': 4}]
        partial = deepcopy(row); partial['status'] = 'partial_download'
        self.assertEqual(len(job.unique_doctorates([row, duplicate, short, partial])), 1)

    def test_native_identity_deduplicates_two_pdf_versions_of_one_dissertation(self):
        row = {'status': 'downloaded', 'title': 'Example', 'authors': 'Author',
               'degree_verification': {'status': 'verified_uk_doctoral',
                                       'awarding_institution': ['University of Oxford']},
               'files': [{'sha256': 'version-one', 'pages': 300}]}
        second = deepcopy(row); second['files'][0]['sha256'] = 'version-two'
        self.assertEqual(len(job.unique_doctorates([row, second])), 1)

    def test_repository_parser_retains_award_metadata_without_security_tokens(self):
        job.LOCAL.pages = []
        parser = job.RepositoryParser()
        parser.feed('<meta name="csrf-token" content="do-not-store">'
                    '<meta name="citation_title" content="Example">'
                    '<dl><dt>Type of award:</dt><dd>DPhil</dd>'
                    '<dt>Awarding institution:</dt><dd>University of Oxford</dd></dl>')
        fields = job.LOCAL.pages[0]['fields']
        self.assertEqual(fields['type of award'], ['DPhil'])
        self.assertEqual(fields['awarding institution'], ['University of Oxford'])
        self.assertNotIn('csrf-token', fields)


if __name__ == '__main__':
    unittest.main()
