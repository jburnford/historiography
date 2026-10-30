"""Birth dates of people presumed living are withheld from the published site copy (user, 2026-10-30)."""
import unittest

from scripts.historian_life_review import withhold_living_birth


def person(pid, birth=None, death=None, status=None, previous=None):
    p = {'id': pid, 'life': {'birth': birth, 'death': death, 'birth_precision': 'day' if birth else None,
                             'death_precision': 'day' if death else None}}
    if status:
        p['life_review'] = {'status': status}
        if previous:
            p['life_review']['previous_dates'] = previous
    return p


class WithholdLivingBirth(unittest.TestCase):
    def test_rules(self):
        payload = {'people': [
            person('living', '1942-07-08'),
            person('reviewed_living', '1950', status='living', previous={'birth': '1950-01-01', 'birth_precision': 'day'}),
            person('dead', '1901-01-04', '1989-05-31'),
            person('reviewed_dead', '1930', status='deceased'),
            person('old', '1880'),
            person('no_birth', None, None),
        ]}
        self.assertEqual(withhold_living_birth(payload, 2026), 2)
        life = {p['id']: p['life'] for p in payload['people']}
        self.assertIsNone(life['living']['birth'])
        self.assertIsNone(life['living']['birth_precision'])
        self.assertIsNone(life['reviewed_living']['birth'])
        self.assertIsNone(payload['people'][1]['life_review']['previous_dates']['birth'])
        self.assertEqual(life['dead']['birth'], '1901-01-04')
        self.assertEqual(life['reviewed_dead']['birth'], '1930')
        self.assertEqual(life['old']['birth'], '1880')
        self.assertEqual(payload['published_enrichment'][-1]['count'], 2)

    def test_published_graph_has_no_living_birth_dates(self):
        """Holds once the site is rebuilt with the rule (scripts/build_site.py)."""
        import json
        from pathlib import Path
        graph = json.loads((Path(__file__).resolve().parents[1] / 'docs/data/graph.json').read_text())
        if not any(e.get('source') == 'withheld' for e in graph.get('published_enrichment', [])):
            self.skipTest('site not yet rebuilt with the living-birth rule')
        for p in graph['people']:
            life = p.get('life') or {}
            if life.get('birth') and not life.get('death') and (p.get('life_review') or {}).get('status') != 'deceased':
                self.assertLess(int(str(life['birth'])[:4].lstrip('-')), 2026 - 120, p['id'])


if __name__ == '__main__':
    unittest.main()
