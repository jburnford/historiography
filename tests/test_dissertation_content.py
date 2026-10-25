"""Dissertation-guided content must retain prior evidence and count populations."""
import hashlib
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/field-research/dissertation-content-2026-10-25'
PACKETS = [ROOT / 'data/extension-2026' / name for name in (
    'dissertation-frameworks-2026-10-25',
    'dissertation-emotions-2026-10-25',
    'dissertation-imperial-law-2026-10-25',
)]


def read(path):
    return json.loads(path.read_text())


def json_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


class DissertationContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = Batch(PACKETS[0]).baseline()
        cls.after = Batch(PACKETS[-1]).check()
        cls.nodes = {n['id']: n for n in cls.after['nodes']}
        cls.people = {p['id']: p for p in cls.after['people']}

    def test_old_claims_qualifications_dates_and_rosters_survive(self):
        self.assertEqual(self.before['edges'], self.after['edges'][:len(self.before['edges'])])
        sources = {s['id']: s for s in self.after['sources']}
        for old in self.before['sources']:
            current = sources[old['id']]
            for field in ('title', 'citation', 'url'):
                self.assertEqual(old.get(field), current.get(field), old['id'])
            self.assertIn(old.get('verification', {}).get('note', ''),
                          current.get('verification', {}).get('note', ''), old['id'])
        for old in self.before['nodes']:
            current = self.nodes[old['id']]
            for field in ('coverage', 'date_span', 'date_label', 'description'):
                self.assertEqual(old.get(field), current.get(field), f'{old["id"]}:{field}')
            self.assertIn(old['representative_figures_and_works'], current['representative_figures_and_works'])
            events = {e['id']: e for e in current['chronology']['events']}
            for event in old['chronology']['events']:
                self.assertEqual(event, events[event['id']], event['id'])
            self.assertEqual(old['chronology']['intervals'], current['chronology']['intervals'])
            for strand in old.get('strands', []):
                self.assertIn(strand, current['strands'])
            roster = {r['person_id']: r for r in current.get('representative_people', [])}
            for row in old.get('representative_people', []):
                self.assertEqual(row, roster[row['person_id']])
        for field in ('scope', 'periods', 'layers', 'claim_catalogue', 'journal_catalogue'):
            self.assertEqual(self.before[field], self.after[field], field)

    def test_new_people_and_emotions_have_bounded_substantive_content(self):
        added = set(self.nodes) - {n['id'] for n in self.before['nodes']}
        self.assertEqual(added, {'james_c_scott', 'history_of_emotions', 'lauren_benton'})
        for nid in ('james_c_scott', 'lauren_benton'):
            node = self.nodes[nid]
            self.assertEqual(self.people[nid]['node_id'], nid)
            self.assertNotIn('coverage', node)
            self.assertGreaterEqual(len([e for e in node['chronology']['events']
                if e['track'] == 'contributions']), 3)
            self.assertGreaterEqual(len([e for e in self.after['edges']
                if nid in (e['source'], e['target'])]), 2)
            self.assertEqual(node['chronology']['continuation']['status'], 'not_asserted')
        self.assertNotIn('node_id', self.people['henri_lefebvre'])
        self.assertNotIn('node_id', self.people['barbara_h_rosenwein'])
        emotions = self.nodes['history_of_emotions']
        self.assertEqual(emotions['entry_kind'], 'group')
        self.assertTrue({'william_m_reddy', 'barbara_h_rosenwein'} <=
                        {r['person_id'] for r in emotions['representative_people']})
        self.assertIn('henri_lefebvre', {r['person_id'] for r in self.nodes['spatialhistory']['representative_people']})

    def test_each_batch_reconstructs_without_ignored_snapshots(self):
        for packet in PACKETS:
            batch = Batch(packet)
            batch.base = ROOT / 'drafts/absent-dissertation-content-baseline-test.json'
            self.assertFalse(batch.base.exists())
            self.assertEqual(batch.check()['revision_history'][-1]['version'], batch.rev)

    def test_new_reading_links_keep_old_selections_and_all_numeric_shards(self):
        old = read(REVIEW / 'reading-links-before.json')
        current = read(ROOT / 'data/dissertation-layer/links.json')
        for key, row in old['people'].items():
            self.assertEqual(row, current['people'][key], key)
        for key, row in old['entries'].items():
            self.assertEqual(row, current['entries'][key], key)
        self.assertEqual(old['entry_comparisons'], {k: current['entry_comparisons'][k]
                                                   for k in old['entry_comparisons']})
        early_additions = {
            'james_c_scott', 'henri_lefebvre', 'lauren_benton',
            'william_m_reddy', 'barbara_h_rosenwein'}
        baseline = read(REVIEW / 'reading-bridge-integration/baseline.json')
        self.assertEqual(set(baseline['links']['people']), set(old['people']) | early_additions)
        self.assertEqual(len(baseline['links']['people']), 25)
        for pid, row in baseline['links']['people'].items():
            self.assertEqual(row, current['people'][pid], pid)
        for key in ('entries', 'entry_comparisons'):
            self.assertEqual(current[key], baseline['links'][key], key)
        scope = read(REVIEW / 'expanded-scope.json')
        historians = {p['person_id'] for p in scope['people']} | {'sarah_carter', 'benedict_anderson', 'immanuel_wallerstein', 'sidney_mintz'}
        remaining = read(ROOT / 'data/dissertation-layer/reviews/remaining-canon-2026-10-25.json')
        remaining_ids = {p['person_id'] for p in remaining['people']}
        self.assertEqual(set(current['people']), set(baseline['links']['people']) | historians | remaining_ids)
        self.assertEqual(len(current['people']), 157)

        site = ROOT / 'data/dissertation-layer/site'
        index = read(site / 'index.json')
        indexed = {s['key']:s for s in index['sources']}
        self.assertEqual(len(baseline['sources']), 4048)
        self.assertEqual(len(indexed), 4059)
        self.assertEqual(json_hash({k:v for k,v in index.items()
            if k not in ('sources', 'reviewed_selection_count')}), baseline['index_context_sha256'])
        new_books = {
            'P:duby|georges': 'W:duby|trois ordres ou limaginaire du feodalisme',
            'P:noiriel|gerard': 'W:noiriel|creuset francais',
            'P:black|jeremy': 'W:black|rethinking military history',
            'P:vovelle|michel': 'W:vovelle|ideologies et mentalites',
            'P:charle|christophe': 'W:charle|naissance des intellectuels',
            'P:giddens|anthony': 'W:giddens|consequences of modernity',
            'P:freud|sigmund': 'W:freud|three essays on the theory of sexuality',
            'P:adorno|theodor w': 'W:adorno|dialectic of enlightenment',
            'P:goody|jack': 'W:goody|development of the family and marriage in europe'}
        self.assertEqual(set(indexed) - {s['index']['key'] for s in baseline['sources']},
                         set(new_books.values()) | {'W:anderson|under three flags', 'W:anderson|spectre of comparisons'})
        shards = {}
        for old_source in baseline['sources']:
            row = old_source['index']
            with self.subTest(source=row['key']):
                self.assertEqual(indexed[row['key']], row)
                self.assertEqual(index['sources'][old_source['index_position']], row)
                if row['asset'] not in shards:
                    shards[row['asset']] = read(site / row['asset'])
                source = shards[row['asset']]['sources'][str(row['id'])]
                self.assertEqual(json_hash({k:source[k] for k in ('n','series','n_region')}),
                                 old_source['numeric_sha256'])
                self.assertEqual(json_hash({k:v for k,v in source.items() if k != 'works'}),
                                 old_source['source_without_works_sha256'])
                expected_works = ([indexed[new_books[row['key']]]['id']]
                                  if row['key'] in new_books else old_source['work_ids'])
                if row['key'] == 'P:anderson|benedict r':
                    expected_works = [*expected_works, indexed['W:anderson|under three flags']['id'], indexed['W:anderson|spectre of comparisons']['id']]
                self.assertEqual(source['works'], expected_works)

    def test_emotions_mapping_preserves_existing_evidence_and_family_shares(self):
        before = read(REVIEW / 'evidence-baseline.json')
        after = read(ROOT / 'data/evidence-layer/site-evidence.json')
        self.assertEqual(before['strip'], after['families']['strip'])
        for family in after['families']['families']:
            self.assertEqual(before['families'][family['id']], family['series'])
        for key, counts in before['entry_counts'].items():
            self.assertEqual(counts, {k: after['entries'][key][k] for k in counts}, key)
        family = next(f for f in after['families']['families'] if f['id'] == 'cultural-and-intellectual-history')
        self.assertIn({'id': 'history_of_emotions', 'primary': True}, family['members'])
        self.assertNotIn('none:history_of_emotions', {r['id'] for r in family['record_only']})
        self.assertEqual(after['entries']['history_of_emotions']['status'], 'direct')


class DissertationWorkBackfillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = Batch(ROOT / 'data/extension-2026/dissertation-work-backfill-2026-10-25')
        cls.before, cls.after = cls.batch.baseline(), cls.batch.check()
        cls.nodes = {n['id']: n for n in cls.after['nodes']}

    def test_bibliography_metadata_does_not_create_arrows_or_rewrite_old_facts(self):
        self.assertEqual(self.before['edges'], self.after['edges'])
        self.assertEqual(self.before['sources'], self.after['sources'][:len(self.before['sources'])])
        old_ids = {n['id'] for n in self.before['nodes']}
        self.assertEqual(old_ids, set(self.nodes))
        appended = []
        for old in self.before['nodes']:
            current = self.nodes[old['id']]
            prior_events = {e['id']: e for e in old['chronology']['events']}
            events = {e['id']: e for e in current['chronology']['events']}
            for eid, event in prior_events.items():
                self.assertEqual(event, events[eid], eid)
            appended.extend(events[eid] for eid in events.keys() - prior_events.keys())
            for field in ('coverage', 'date_label', 'scope_note', 'description'):
                self.assertEqual(old.get(field), current.get(field), f'{old["id"]}:{field}')
        self.assertEqual(len(appended), 9)
        self.assertEqual(next(n for n in self.before['nodes'] if n['id'] == 'foucault'), self.nodes['foucault'])

    def test_joint_author_translation_and_collection_credits_survive(self):
        events = {e['id']: e for e in self.nodes['carlo_ginzburg']['chronology']['events']}
        original = next(e for e in events.values() if e['id'].startswith('dc168_work_'))
        translation = events['dc168_ginzburg_poni_french_1981']
        self.assertEqual(original['date']['year'], 1979)
        self.assertEqual(translation['date']['year'], 1981)
        for event in [original, translation]:
            self.assertIn('Poni', event['label'])
        row = next(r for r in self.nodes['micro']['representative_people'] if r['person_id'] == 'carlo_poni')
        self.assertIn('With Carlo Ginzburg', row['works'])
        self.assertNotIn('With Carlo Poni', row['works'])
        selected = self.nodes['reinhart_koselleck']['representative_figures_and_works']
        for credit in ['Todd Samuel Presner', 'Hayden White', 'Michael Werner', 'Alexandre Escudier',
                       'Diane Meur', 'Marie-Claire Hoock', 'Jochen Hoock']:
            self.assertIn(credit, selected)

    def test_eight_object_review_and_two_holds_remain_frozen(self):
        notes = read(self.batch.pkt / 'research-notes.json')
        review_path = ROOT / notes['review']
        self.assertEqual(hashlib.sha256(review_path.read_bytes()).hexdigest(), notes['review_sha256'])
        review = read(review_path)
        self.assertEqual({r['work_id'] for r in notes['accepted_objects']},
                         {r['work_id'] for r in review['results'] if r['decision'] == 'actual_new_work_gap'})
        self.assertEqual(review['decision_counts'], {
            'actual_new_work_gap': 8, 'already_represented_translation_edition': 9, 'unresolved': 2})
        self.batch.base = ROOT / 'drafts/absent-backfill-baseline-test.json'
        self.assertEqual(self.batch.check()['revision_history'][-1]['version'], '1.168')


if __name__ == '__main__':
    unittest.main()
