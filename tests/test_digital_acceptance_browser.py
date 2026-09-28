"""Reuse frozen browser cases against accepted data and check the current public build."""
from unittest.mock import patch
from playwright.sync_api import expect
from scripts import accept_digital_release as release
from tests import test_digital_release_browser as frozen


class AcceptedDigitalBrowserTests(frozen.DigitalBrowserTests):
    @classmethod
    def setUpClass(cls):
        generated,_ = release.checked_candidate()
        accepted = release.transform(release.read(release.baseline_path()),generated['candidate.json'],generated['reconciled-research.json'])
        with patch.object(frozen.m,'outputs',return_value=(generated,accepted)):
            super().setUpClass()

    def test_accepted_status_and_existing_fields(self):
        for field in ('digital_history','web_history','medicalhistory','spatialhistory'):
            self.open('#node='+field)
            expect(self.page.locator('.extension .badge.status-partial_accepted')).to_be_visible()
            statuses = self.page.locator('.extension .claim-card .badge[class*=status-]').all_inner_texts()
            self.assertTrue(statuses)
            self.assertEqual({s.lower() for s in statuses},{'accepted'})

    def test_production_build_matches_checked_preview(self):
        if not (release.OUT/'acceptance.json').exists():
            self.skipTest('Before local acceptance/build')
        # A later accepted revision (1.124 onward) republishes the graph. The release's other
        # public files must still match its checked preview; the graph must be that later revision.
        current = release.read(release.GRAPH)
        superseded = release.candidate.fingerprint(current) != release.read(release.OUT/'acceptance.json')['production_sha256']
        if superseded:
            later = current['revision_history'][-1]
            self.assertTrue((release.ROOT/later['acceptance_record']).is_file(), later['version'])
        for path in self.site.rglob('*'):
            if path.is_file():
                rel = path.relative_to(self.site)
                if superseded and rel.as_posix() == 'data/graph.json':
                    continue
                public = release.ROOT/'docs'/rel
                self.assertEqual(public.read_bytes(),path.read_bytes(),str(public))
