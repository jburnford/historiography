"""Review labels -> reviewed book (scripts/review_books.py, pass seven 2026-11-12; class 29)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from review_books import (choose, clean_label, fold, label_isbns, match_label, match_title, printed_names,  # noqa: E402
                          review_like)


def book(key, title, year, src='graph', lccn=None):
    return dict(book=key, title=title, year=year, mt=match_title(title), src=src, lccn=lccn, lcnaf=None)


class Labels(unittest.TestCase):
    def test_clean_and_review_like(self):
        self.assertEqual(clean_label('Review of Failures to Compute')[0], 'Failures to Compute')
        self.assertEqual(clean_label('Book Review: What Unions No Longer Do')[0], 'What Unions No Longer Do')
        self.assertEqual(clean_label('Bolesław Prus and the Jews by Agnieszka Friedrich (review)')[0],
                         'Bolesław Prus and the Jews by Agnieszka Friedrich')
        self.assertTrue(review_like('Reseña de: Javier MUÑOZ SORO, Cuadernos para el Diálogo', 'article'))
        self.assertTrue(review_like('Dark Age Nunneries. By Steven Vanderputten. Ithaca: Cornell, 2018. 309 pp.', 'article'))
        self.assertTrue(review_like('LUBY, Britanny (2020) Dammed. The Politics of Loss', 'article'))
        self.assertFalse(review_like('A History of Modern France', 'article'))
        self.assertTrue(review_like('A History of Modern France', 'review'))

    def test_printed_names(self):
        self.assertEqual(printed_names('Sex in Middlesex. By Roger Thompson (Amherst: University of Massachusetts Press'),
                         ['Roger Thompson'])
        self.assertEqual(printed_names('Title. By J. H. Elliott and Ludovic de Feo. Oxford: OUP'),
                         ['J. H. Elliott', 'Ludovic de Feo'])
        self.assertEqual(printed_names('Commerce and Peace. Edited by Béla Kapossy, Isaac Nakhimovsky, and Richard Whatmore.'),
                         ['Béla Kapossy', 'Isaac Nakhimovsky', 'Richard Whatmore'])
        self.assertEqual(printed_names('LUBY, Britanny (2020) Dammed. The Politics'), ['Britanny Luby'])
        self.assertEqual(printed_names('Review of Michael J. Yochim’s Yellowstone and the Snowmobile'), ['Michael J. Yochim'])
        self.assertEqual(printed_names('Review of Between Mao and McCarthy by Charlotte Brooks'), ['Charlotte Brooks'])
        self.assertEqual(printed_names('Chain of Gold: Greek Rhetoric in the Roman Empire'), [])
        # hand check, pass seven: the name after 'Reviewed by' is the reviewer
        self.assertEqual(printed_names('Travin D.Ya. Why Has Russia Lagged Behind? 2021. Reviewed by B.N. Mironov'), [])

    def test_not_reviews(self):
        self.assertFalse(review_like('Response by the author - Gabrielle Hecht, Residual Governance: How South Africa', 'review'))
        self.assertFalse(review_like("Extract from: 'Crossing cultures: contemporary Australian short stories'", 'article'))

    def test_isbn(self):
        self.assertEqual(label_isbns('Pp. 288. ISBN 9780674240995. Hbk'), {'9780674240995'})
        self.assertEqual(label_isbns('127 pp. ISBN: 92-2-109790-0'), {'9221097900'})
        self.assertEqual(label_isbns('1649-1699, 252 pp.'), set())


class Match(unittest.TestCase):
    fams = {'b1': {'luby'}, 'b2': {'peace', 'labelle'}, 'lc1': {'luby'}, 'b3': {'smith'}, 'b4': {'jones'}}

    def test_title_and_family(self):
        fl = fold('LUBY, Britanny (2020) Dammed. The Politics of Loss and Survival in Anishinaabe Territory')
        b = book('b1', 'Dammed: The Politics of Loss and Survival in Anishinaabe Territory', 2020)
        self.assertEqual([x[0]['book'] for x in match_label(fl, 2021, set(), [b], self.fams)], ['b1'])
        # the family must be printed outside the title
        self.assertEqual(match_label(fold('Dammed: The Politics of Loss and Survival in Anishinaabe Territory'), 2021, set(),
                                     [b], self.fams), [])
        # year window: review 0-6 years after (one before tolerated)
        self.assertEqual(match_label(fl, 2030, set(), [b], self.fams), [])

    def test_short_titles_refused(self):
        b = book('b3', 'Rome', 2000)
        self.assertEqual(match_label(fold('Rome. By John Smith'), 2001, set(), [b], self.fams), [])

    def test_choose(self):
        a = book('b1', 'Dammed: The Politics of Loss', 2020)
        c = book('lc1', 'Dammed: the politics of loss', 2020, src='lc', lccn='2020123')
        pick, groups = choose([(c, 'label-title-family', 'luby'), (a, 'label-title-family', 'luby')], 2021)
        self.assertEqual(pick[0]['book'], 'b1')            # the graph node before the catalogue record
        d = book('b3', 'Histoire de France moderne', 1990)
        e = book('b4', 'Histoire de France moderne', 1991)
        pick, groups = choose([(d, 'label-title-family', 'smith'), (e, 'label-title-family', 'jones')], 1992)
        self.assertIsNone(pick)                             # two different books: held
        self.assertEqual(len(groups), 2)


if __name__ == '__main__':
    unittest.main()
