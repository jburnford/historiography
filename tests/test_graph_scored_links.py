"""Scorer-only links loader (scripts/graph_scored_links.py, 2026-11-12)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from graph_scored_links import scored_layer  # noqa: E402
from reviewed_authors import build as reviewed  # noqa: E402


def row(work, pos, key, decision, score='7.0', role='author', rule_state='', rule_key='', source='openalex'):
    return dict(work=work, role=role, position=str(pos), printed_name='X', person_key=key, score=score, runner_up_score='',
                decision=decision, n_candidates='1', top_fields='topic=high', rule_state=rule_state, rule_key=rule_key,
                source=source)


def run(rows, wi=None, review_works=(), keylog=(), linked=None, cands=None, ra=None):
    rels = {'AUTHORED': [{'from': a, 'to': b} for a, b in keylog], 'EDITED': []}
    linked = linked or {'AUTHORED': [], 'EDITED': []}
    cands = cands if cands is not None else []
    rep = {}
    scored_layer(lambda p: rows, Path('x'), lambda k: k or None, lambda w: w, wi or {}, set(review_works), rels, linked,
                 cands, rep, ra=ra)
    return linked, cands, rep['scored_links']


class Scored(unittest.TestCase):
    def test_scorer_only_link_loads(self):
        linked, _, rep = run([row('w1', 0, 'p-1', 'link')], wi={'w1': {'kind': 'article', 'label': 'An article'}})
        [r] = linked['AUTHORED']
        self.assertEqual((r['source'], r['state'], r['score']), ('scored-links', 'scored', 7.0))

    def test_review_work_excluded_for_author_role(self):
        for wi, rv in (({'w1': {'kind': 'review', 'label': 'x'}}, ()), ({'w1': {'kind': 'article', 'label': 'Review of Y'}}, ()),
                       ({'w1': {'kind': 'article', 'label': 'x'}}, ('w1',))):
            linked, _, _ = run([row('w1', 0, 'p-1', 'link')], wi=wi, review_works=rv)
            self.assertEqual(linked['AUTHORED'], [])
        linked, _, _ = run([row('w1', 0, 'p-1', 'link', role='reviewer', source='review')], wi={'w1': {'kind': 'review', 'label': 'x'}})
        self.assertEqual(len(linked['AUTHORED']), 1)                 # the reviewer of a review is its author

    def test_review_link_with_known_reviewed_author(self):
        # pass seven: the review w1 reviews book b1 by p-2 (Becher's case: the reviewed author printed as the author)
        ra = reviewed([('w1', 'b1')], [('p-2', 'b1')], [], {'p-1': 'Reviewer, Ann', 'p-2': 'Becher, Ursula'})
        wi = {'w1': {'kind': 'review', 'label': 'x'}}
        linked, _, rep = run([row('w1', 0, 'p-2', 'link'), row('w1', 1, 'p-1', 'link')], wi=wi, ra=ra)
        self.assertEqual([r['from'] for r in linked['AUTHORED']], ['p-1'])
        self.assertEqual(rep['link|author|review|is_reviewed_author:book-credit'], 1)
        # printed reviewed author only (no book node): family and initial
        ra = reviewed([], [], [('w1', 'Ursula A. J. Becher')], {'p-1': 'Reviewer, Ann', 'p-2': 'Becher, Ursula'})
        linked, _, _ = run([row('w1', 0, 'p-2', 'link'), row('w1', 1, 'p-1', 'link')], wi=wi, ra=ra)
        self.assertEqual([r['from'] for r in linked['AUTHORED']], ['p-1'])
        # nobody known: excluded as before
        ra = reviewed([], [], [], {})
        linked, _, rep = run([row('w1', 1, 'p-1', 'link')], wi=wi, ra=ra)
        self.assertEqual(linked['AUTHORED'], [])
        self.assertEqual(rep['link|author|review|reviewed_author_unknown'], 1)

    def test_same_as_rule_annotates(self):
        ex = {'from': 'p-1', 'to': 'w1', 'source': 'name-only:openalex'}
        linked, _, rep = run([row('w1', 0, 'p-1', 'link', rule_state='linked', rule_key='p-1')],
                             linked={'AUTHORED': [ex], 'EDITED': []})
        self.assertEqual(len(linked['AUTHORED']), 1)
        self.assertEqual(ex['score'], 7.0)

    def test_rule_names_another_key(self):
        linked, _, rep = run([row('w1', 0, 'p-1', 'link', rule_state='linked', rule_key='p-2')])
        self.assertEqual(linked['AUTHORED'], [])
        self.assertEqual(rep['link|rule_names_another_key'], 1)

    def test_exact_and_keylog_not_loaded(self):
        linked, _, _ = run([row('w1', 0, 'p-1', 'exact', score=''), row('w2', 0, 'p-1', 'link')], keylog=[('p-1', 'w2')])
        self.assertEqual(linked['AUTHORED'], [])

    def test_review_rows_become_candidates(self):
        rows = [row('w1', 0, f'p-{i}', 'review', score=str(i)) for i in range(1, 6)]
        _, cands, _ = run(rows, cands=[{'from': 'p-5', 'to': 'w1'}])
        self.assertEqual([c['from'] for c in cands[1:]], ['p-4', 'p-3', 'p-2'])
        self.assertTrue(all(c['reason'] == 'scored-review' for c in cands[1:]))



class Classified(unittest.TestCase):
    """pass eight: the classifier's certified links (classified.csv.gz rows with load = True only)"""
    @staticmethod
    def crow(work, pos, key, load='True', role='reviewer', p='0.9961'):
        return dict(position=str(pos), work=work, role=role, pos='0', printed_name='X', decision='link', person_key=key,
                    probability=p, stratum='multi', load=load, model='fs test')

    def load(self, rows, keylog=(), linked=None, ra=None):
        from graph_scored_links import classified_layer
        rels = {'AUTHORED': [{'from': a, 'to': b} for a, b in keylog], 'EDITED': []}
        linked = linked or {'AUTHORED': [], 'EDITED': []}
        rep = {}
        classified_layer(lambda p: rows, Path('x'), lambda k: k or None, lambda w: w, rels, linked, rep, ra=ra)
        return linked, rep['classified_links']

    def test_only_load_true_rows(self):
        linked, rep = self.load([self.crow('w1', 1, 'p-1'), self.crow('w2', 2, 'p-2', load='False')])
        [r] = linked['AUTHORED']
        self.assertEqual((r['from'], r['source'], r['state'], r['score'], r['role']), ('p-1', 'classified-links', 'classified', 0.9961, 'author'))
        self.assertEqual(rep['added|AUTHORED'], 1)

    def test_credited_pairs_skipped(self):
        linked, rep = self.load([self.crow('w1', 1, 'p-1'), self.crow('w2', 2, 'p-1')], keylog=[('p-1', 'w1')],
                               linked={'AUTHORED': [{'from': 'p-1', 'to': 'w2'}], 'EDITED': []})
        self.assertEqual(len(linked['AUTHORED']), 1)            # only the existing linked row
        self.assertEqual(rep['pair_already_credited'], 2)

    def test_reviewed_author_refused(self):
        ra = reviewed([('w1', 'b1')], [('p-2', 'b1')], [], {'p-2': 'Becher, Ursula'})
        linked, rep = self.load([self.crow('w1', 1, 'p-2')], ra=ra)
        self.assertEqual(linked['AUTHORED'], [])
        self.assertEqual(rep['reviewed_author_refused|book-credit'], 1)


if __name__ == '__main__':
    unittest.main()


class ModelLayer(unittest.TestCase):
    """2026-11-13: classifier decision = link rows and Qwen verdicts (graph_scored_links.model_layer)"""
    @staticmethod
    def crow(pid, work, key, role='reviewer', pos='0', tbl='wp', src='review'):
        return dict(position=str(pid), work=work, role=role, pos=pos, decision='link', person_key=key, probability='0.99',
                    stratum='multi', model='gbt test', tbl=tbl, list_source=src)

    @staticmethod
    def qrow(pid, work, decision, role='reviewer', rule_key=''):
        return dict(position=str(pid), work=work, role=role, decision=decision, rule_key=rule_key, votes='3/3',
                    confidence='high', reason='r')

    def load(self, crows, qrows, qpos, linked=None, keylog=()):
        from graph_scored_links import model_layer
        rels = {'AUTHORED': [{'from': a, 'to': b} for a, b in keylog], 'EDITED': []}
        linked = linked or {'AUTHORED': [], 'EDITED': []}
        cands, rep = [], {}
        files = {'c': crows, 'q': qrows, 'p': qpos}

        class P:
            def __init__(self, n):
                self.n = n

            def exists(self):
                return True
        model_layer(lambda p: files[p.n], P('c'), P('q'), P('p'), lambda k: k or None, lambda w: w, {}, set(), rels,
                    linked, cands, rep)
        return linked, cands, rep['model_links']

    def rule(self, key, work, pos='0', role='reviewer', state='linked'):
        return {'from': key, 'to': work, 'claim': f'work-people:{role}:{pos}', 'source': f'work-people:{role}', 'state': state}

    def test_loads_new_and_counts_same(self):
        linked = {'AUTHORED': [self.rule('p-1', 'w1')], 'EDITED': []}
        lk, cands, rep = self.load([self.crow(1, 'w1', 'p-1'), self.crow(2, 'w2', 'p-2')],
                                   [self.qrow(3, 'w3', 'p-3')], [dict(position='3', tbl='wp', list_source='review', pos='0')], linked)
        srcs = sorted(r['source'] for r in lk['AUTHORED'])
        self.assertEqual(srcs, ['classified-links', 'qwen-links', 'work-people:reviewer'])
        self.assertEqual(rep['clf|already_linked|work-people:reviewer'], 1)

    def test_qwen_not_keyed_demotes_rule_and_classifier(self):
        linked = {'AUTHORED': [self.rule('p-1', 'w1'), self.rule('p-9', 'w9', state='exact')], 'EDITED': []}
        lk, cands, rep = self.load([self.crow(1, 'w1', 'p-5', pos='1')], [self.qrow(1, 'w1', 'not-keyed'), self.qrow(2, 'w9', 'not-keyed')],
                                   [dict(position='1', tbl='wp', list_source='review', pos='0'),
                                    dict(position='2', tbl='wp', list_source='review', pos='0')], linked)
        self.assertEqual([r['from'] for r in lk['AUTHORED']], ['p-9'])        # identifier link kept
        self.assertEqual({c['from'] for c in cands}, {'p-1', 'p-5'})   # rule and classifier keys become candidates
        self.assertEqual(rep['qwen_not_keyed|rule_row_exact_kept'], 1)

    def test_conflict_links_neither(self):
        linked = {'AUTHORED': [self.rule('p-1', 'w1')], 'EDITED': []}
        lk, cands, rep = self.load([], [self.qrow(1, 'w1', 'p-2')], [dict(position='1', tbl='wp', list_source='review', pos='0')], linked)
        self.assertEqual(lk['AUTHORED'], [])
        self.assertEqual({c['from'] for c in cands}, {'p-1', 'p-2'})
        self.assertEqual(rep['conflicts'], 1)

    def test_keylog_position_skipped(self):
        lk, cands, rep = self.load([], [self.qrow(1, 'w1', 'p-2', rule_key='p-1')],
                                   [dict(position='1', tbl='no', list_source='openalex', pos='0')], keylog=[('p-1', 'w1')])
        self.assertEqual(lk['AUTHORED'], [])
        self.assertEqual(rep['qwen_key|keylog_credits_position'], 1)
