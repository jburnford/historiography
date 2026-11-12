"""Unit tests for the class-15 edition-role rules (scripts/edition_roles.py) and the class-17 title fold
(scripts/work_first_years.py). Synthetic LC records only; no data files are read."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

import edition_roles as er  # noqa: E402
from work_first_years import tfold  # noqa: E402


def head(pos, tag, heading, lcid='', rel=()):
    fam, _, giv = heading.partition(',')
    return dict(pos=pos, tag=tag, heading=heading, family=er.fold(fam).strip(), given=er.fold(giv).strip(),
                lcid=lcid, rel=set(rel))


class FakeLC:
    def __init__(self, recs):
        self.rec = {k: (v['title'], '1990', v['resp'], 'eng') for k, v in recs.items()}
        self.heads = {k: v['heads'] for k, v in recs.items()}


def role(rec, lcids, label, credit='edited'):
    L = FakeLC({'r': rec})
    return er.classify_record(L, 'r', set(lcids), er.family_of(label), er.given_of(label), credit)


class Names(unittest.TestCase):
    def test_family(self):
        self.assertEqual(er.family_of('Lerner, Max'), 'lerner')
        self.assertEqual(er.family_of('François-Xavier Guerra'), 'guerra')
        self.assertEqual(er.family_of('Di Tella, Torcuato S'), 'di tella')
        self.assertEqual(er.family_of('Smith, Adam, 1723-1790'), 'smith')


class Edited(unittest.TestCase):
    def test_introducer_of_a_classic(self):
        rec = dict(title='An inquiry into the nature and causes of the wealth of nations',
                   resp='by Adam Smith; edited, with an introduction, notes ... by Edwin Cannan ... with an introduction by Max Lerner',
                   heads=[head(0, '100', 'Smith, Adam, 1723-1790', 'n1'), head(1, '700', 'Cannan, Edwin, 1861-1935', 'n2', ['ed']),
                          head(2, '700', 'Lerner, Max, 1902-1992', 'n3')])
        self.assertEqual(role(rec, ['n3'], 'Lerner, Max')['role'], 'introducer')
        self.assertEqual(role(rec, ['n2'], 'Cannan, Edwin')['role'], 'edition-editor')

    def test_translator(self):
        rec = dict(title='The Protestant ethic', resp='Max Weber ; translated by Talcott Parsons',
                   heads=[head(0, '100', 'Weber, Max, 1864-1920', 'w'), head(1, '700', 'Parsons, Talcott', 'p', ['tr'])])
        self.assertEqual(role(rec, ['p'], 'Parsons, Talcott')['role'], 'translator')

    def test_selected_and_edited_single_author(self):
        rec = dict(title='Selected writings', resp='Karl Marx ; selected and edited by David McLellan',
                   heads=[head(0, '100', 'Marx, Karl, 1818-1883', 'm'), head(1, '700', 'McLellan, David', 'd', ['ed'])])
        self.assertEqual(role(rec, ['d'], 'McLellan, David')['role'], 'edition-editor')

    def test_collective_volume_with_introduction(self):
        rec = dict(title='The invention of tradition', resp='edited by Eric Hobsbawm and Terence Ranger',
                   heads=[head(0, '700', 'Hobsbawm, E. J.', 'h'), head(1, '700', 'Ranger, T. O.', 'r')])
        self.assertEqual(role(rec, ['h'], 'Hobsbawm, Eric')['role'], 'volume-editor')

    def test_festschrift(self):
        rec = dict(title='Essays in honour of Natalie Zemon Davis', resp='edited by A. B. Smith',
                   heads=[head(0, '700', 'Smith, A. B.', 's', ['ed'])])
        r = role(rec, ['s'], 'Smith, A. B.')
        self.assertEqual(r['role'], 'volume-editor')
        self.assertIn('festschrift', r['basis'])

    def test_author_who_also_edits_keeps_authorship(self):
        rec = dict(title='Collected essays', resp='Natalie Zemon Davis ; edited by the author',
                   heads=[head(0, '100', 'Davis, Natalie Zemon', 'd')])
        self.assertEqual(role(rec, ['d'], 'Davis, Natalie Zemon')['role'], 'author-editor')

    def test_older_editor_main_entry(self):
        rec = dict(title='Studies in social history', resp='edited by J. H. Plumb',
                   heads=[head(0, '100', 'Plumb, J. H.', 'p', ['ed'])])
        self.assertEqual(role(rec, ['p'], 'Plumb, J. H.')['role'], 'volume-editor')

    def test_by_author_no_main_entry(self):
        rec = dict(title='Lettres', resp='by Voltaire ; edited by Theodore Besterman', heads=[head(0, '700', 'Voltaire, 1694-1778', 'v'), head(1, '700', 'Besterman, Theodore', 'b', ['ed'])])
        self.assertEqual(role(rec, ['b'], 'Besterman, Theodore')['role'], 'edition-editor')


class Clauses(unittest.TestCase):
    def test_phrases(self):
        cases = [("by Adam Smith; edited ... by Edwin Cannan ... with an introduction by Max Lerner", 'lerner', 'introducer'),
                 ("by Adam Smith; edited ... by Edwin Cannan ... with an introduction by Max Lerner", 'cannan', 'editor'),
                 ("Max Weber ; herausgegeben von Wolfgang J. Mommsen und Wolfgang Schluchter", 'schluchter', 'editor'),
                 ("Karl Marx and Friedrich Engels ; with an introduction by Martin Malia", 'engels', 'author'),
                 ("Alan Trachtenberg ; consulting editor, Eric Foner", 'foner', 'series-editor'),
                 ("Introdução geral de Sérgio Buarque de Holanda", 'holanda', 'introducer'),
                 ("Edited and with an introd. by Andrew S. Skinner", 'skinner', 'editor'),
                 ("Michel Foucault ; tradução de Raquel Ramalhete", 'ramalhete', 'translator'),
                 ("Boris Fausto, organizador", 'fausto', 'editor')]
        for resp, fam, want in cases:
            self.assertEqual(er.clause_role(resp, fam), want, resp)

    def test_series_editor_of_another_authors_book(self):
        rec = dict(title='The incorporation of America', resp='Alan Trachtenberg ; consulting editor, Eric Foner',
                   heads=[head(0, '100', 'Trachtenberg, Alan', 't'), head(1, '700', 'Foner, Eric, 1943-', 'f')])
        self.assertEqual(role(rec, ['f'], 'Eric Foner')['role'], 'series-editor')

    def test_collective_work_under_its_director(self):
        rec = dict(title='História geral da civilização brasileira', resp='sob a direção de Sérgio Buarque de Holanda',
                   heads=[head(0, '100', 'Holanda, Sérgio Buarque de, 1902-1982', 'h'), head(1, '700', 'Fausto, Boris, 1930-', 'b', ['joint ed'])])
        self.assertEqual(role(rec, ['b'], 'Fausto, Boris')['role'], 'volume-editor')

    def test_coauthor_in_statement(self):
        rec = dict(title='The communist manifesto', resp='Karl Marx and Friedrich Engels ; with an introduction by Martin Malia',
                   heads=[head(0, '100', 'Marx, Karl, 1818-1883', 'm'), head(1, '700', 'Malia, Martin E.', 'x'),
                          head(2, '700', 'Engels, Friedrich, 1820-1895', 'e')])
        self.assertEqual(role(rec, ['e'], 'Friedrich Engels')['role'], 'author-editor')


class AuditRound1(unittest.TestCase):
    def test_corporate_first_clause_is_not_an_author(self):
        rec = dict(title='Handbook on the history of European banks',
                   resp='European Association for Banking History ; chief editor, Manfred Pohl ; assistant editor, Sabine Freitag',
                   heads=[head(0, '700', 'Pohl, Manfred, 1944-', 'p'), head(1, '700', 'Freitag, Sabine', 'f')])
        self.assertEqual(role(rec, ['p'], 'Pohl, Manfred')['role'], 'volume-editor')

    def test_same_family_editor_of_an_autobiography(self):
        rec = dict(title='A memoir of the new left', resp='edited by Aeron Haynie, Timothy S. Miller ; with a foreword by Douglas Dowd',
                   heads=[head(0, '100', 'Haynie, Charles A., 1935-2001', 'c'), head(1, '700', 'Haynie, Aeron, 1964-', 'a'),
                          head(2, '700', 'Miller, Timothy S.', 'm')])
        self.assertEqual(role(rec, ['m'], 'Miller, Timothy S.')['role'], 'edition-editor')

    def test_by_author_then_ed_by(self):
        rec = dict(title='A course of six lectures', resp='By Michael Faraday.  Ed. by William Crookes',
                   heads=[head(0, '100', 'Faraday, Michael, 1791-1867', 'f'), head(1, '700', 'Crookes, William, 1832-1919', 'c', ['ed'])])
        self.assertEqual(role(rec, ['c'], 'Crookes, William')['role'], 'edition-editor')

    def test_consulting_editor_without_main_entry(self):
        rec = dict(title='The Life history of the United States', resp='Consulting editor: Henry F. Graff',
                   heads=[head(0, '700', 'Graff, Henry F. (Henry Franklin), 1921-', 'g', ['ed'])])
        self.assertEqual(role(rec, ['g'], 'Graff, Henry')['role'], 'series-editor')


class QualifiedEditors(unittest.TestCase):
    """2026-11-12 (class 23): a qualified role word ('cartographic editor', 'assistant editor', 'maps edited by') is
    another job on the book, not editing the volume; role contributor (not counted as the person's own work)."""
    WYNN = ('edited by Phillip A. Buckner and John G. Reid ; Eric Leinberger, cartographer ; '
            'Graeme Wynn, cartographic editor ; Mitchell A. McNutt, picture editor')

    def test_clause_after_name(self):
        self.assertEqual(er.clause_role(self.WYNN, 'wynn'), 'qualified-editor')
        self.assertEqual(er.clause_role(self.WYNN, 'mcnutt'), 'qualified-editor')
        self.assertEqual(er.clause_role(self.WYNN, 'buckner'), 'editor')
        self.assertEqual(er.clause_role(self.WYNN, 'reid'), 'editor')
        for resp, fam in (('Paul G. Pierpaoli Jr., associate editor', 'pierpaoli'),
                          ('John Beynon, Douglas Eisner, assistant editors', 'beynon'),
                          ('John Beynon, Douglas Eisner, assistant editors', 'eisner'),
                          ('Susan Allred Whetstone, photo-editor', 'whetstone'),
                          ('Jack Rabin, founding editor', 'rabin'),
                          ('Michael Berenbaum, executive editor', 'berenbaum')):
            self.assertEqual(er.clause_role(resp, fam), 'qualified-editor', resp)

    def test_clause_before_name(self):
        self.assertEqual(er.clause_role('edited by A. B. Smith ; assistant editor, Sabine Freitag', 'freitag'), 'qualified-editor')
        self.assertEqual(er.clause_role('edited by Paul Harvey ; bibliography edited by Randall Stephens', 'stephens'), 'qualified-editor')
        self.assertEqual(er.clause_role('edited by Jane Roe ; Maps edited by John Doe', 'doe'), 'qualified-editor')
        self.assertEqual(er.clause_role('edited by Jane Roe ; Maps edited by John Doe', 'roe'), 'editor')

    def test_nearest_role_word_governs(self):
        resp = 'Frederick F. Wherry, editor, Juliet Schor, consulting editor'
        self.assertEqual(er.clause_role(resp, 'wherry'), 'editor')
        self.assertEqual(er.clause_role(resp, 'schor'), 'series-editor')

    def test_plain_and_allowed_qualifiers_stay_editors(self):
        for resp, fam in (('John Smith and Jane Doe, editors', 'smith'), ('Jane Roe, co-editor', 'roe'),
                          ('Mary Poe, guest editor', 'poe'), ('D. M. Bose, chief editor', 'bose'),
                          ('Henry J. Aaron and Michael J. Boskin, editors', 'aaron')):
            self.assertEqual(er.clause_role(resp, fam), 'editor', resp)

    def test_role_first_clause(self):
        # the role after a name opens the next name's credit when the clause opens with a role (hand check 2026-11-12)
        self.assertEqual(er.clause_role('editor-in-chief, Edwin R.A. Seligman, associate editor, Alvin Johnson', 'seligman'), 'editor')
        self.assertEqual(er.clause_role('editor-in-chief, Edwin R.A. Seligman, associate editor, Alvin Johnson', 'johnson'), 'qualified-editor')
        self.assertEqual(er.clause_role('edited by Joseph H. Greenberg, associate editors, Charles A. Ferguson & Edith A. Moravcsik',
                                        'greenberg'), 'editor')
        self.assertEqual(er.clause_role('edited by Joseph H. Greenberg, associate editors, Charles A. Ferguson & Edith A. Moravcsik',
                                        'moravcsik'), 'qualified-editor')
        # a clause that opens with names: the role after each name is its own
        resp = 'Salo W. Baron, George S. Wise, editors, Lenn E. Goodman, associate editor'
        self.assertEqual(er.clause_role(resp, 'goodman'), 'qualified-editor')
        self.assertEqual(er.clause_role(resp, 'baron'), 'editor')

    def test_singular_role_after_a_list_is_the_last_name(self):
        resp = 'Newt Gingrich, William R. Forstchen and Albert S. Haner, contributing editor'
        self.assertEqual(er.clause_role(resp, 'haner'), 'qualified-editor')
        self.assertNotEqual(er.clause_role(resp, 'forstchen'), 'qualified-editor')
        self.assertEqual(er.clause_role('Phelan Powell ; Arthur M. Schlesinger, Jr., senior consulting editor', 'schlesinger'),
                         'series-editor')

    def test_list_with_other_words_is_not_governed(self):
        # 'with' stands between Buckner and the cartographic editor: Buckner keeps 'edited by'
        self.assertEqual(er.clause_role('edited by Phillip A. Buckner with Graeme Wynn, cartographic editor', 'buckner'), 'editor')

    def test_role_of_the_credit(self):
        rec = dict(title='The Atlantic region to Confederation : a history', resp=self.WYNN,
                   heads=[head(0, '700', 'Buckner, Phillip A. (Phillip Alfred), 1942-', 'b'), head(1, '700', 'Reid, John G. (John Graham), 1948-', 'r'),
                          head(2, '700', 'Wynn, Graeme, 1946-', 'w')])
        r = role(rec, ['w'], 'Wynn, Graeme')
        self.assertEqual((r['role'], r['basis']), ('contributor', 'lc-245c-qualified-editor'))
        self.assertEqual(role(rec, ['w'], 'Wynn, Graeme', 'authored')['role'], 'contributor')
        self.assertEqual(role(rec, ['b'], 'Buckner, Phillip A.')['role'], 'volume-editor')

    def test_sole_qualified_editor_keeps_the_volume(self):
        # hand check 2026-11-12: no main entry and no other editor named: the qualified editor is the volume's editor
        rec = dict(title='Business and social progress', resp='Clarence C. Walton, contributing editor',
                   heads=[head(0, '700', 'Walton, Clarence C.', 'w')])
        self.assertEqual(role(rec, ['w'], 'Walton, Clarence')['role'], 'volume-editor')
        self.assertTrue(er.names_an_editor('editor, S. Rachman ; founding editor, H.J. Eysenck'))
        self.assertFalse(er.names_an_editor('Keith Lye, consultant editor ; Jane Roe, assistant editor'))
        self.assertEqual(er.clause_role('Candace S. Greene, proceedings editor', 'greene'), 'editor')

    def test_re_edited_is_editing(self):
        self.assertEqual(er.clause_role('re-edited by Frederick J. Furnivall', 'furnivall'), 'editor')

    def test_picture_editor_of_a_monograph(self):
        rec = dict(title='A history', resp='Alan Trachtenberg ; picture editor, Jane Roe',
                   heads=[head(0, '100', 'Trachtenberg, Alan', 't'), head(1, '700', 'Roe, Jane', 'j')])
        self.assertEqual(role(rec, ['j'], 'Roe, Jane')['role'], 'contributor')


class Authored(unittest.TestCase):
    def test_absent_person(self):
        rec = dict(title="Le Mexique de l'Ancien Régime à la Révolution", resp='François-Xavier Guerra ; préface de François Chevalier',
                   heads=[head(0, '100', 'Guerra, François-Xavier', 'g')])
        self.assertEqual(role(rec, ['t'], 'Di Tella, Torcuato S', 'authored')['role'], 'absent')

    def test_translator_credited_as_author(self):
        rec = dict(title='Vigiar e punir', resp='Michel Foucault ; tradução de Raquel Ramalhete',
                   heads=[head(0, '100', 'Foucault, Michel', 'f'), head(1, '700', 'Ramalhete, Raquel', 'r')])
        self.assertEqual(role(rec, ['r'], 'Ramalhete, Raquel', 'authored')['role'], 'translator')


class Fold(unittest.TestCase):
    def test_tfold(self):
        self.assertEqual(tfold("Comment on écrit l'histoire : essai d'épistémologie"), 'comment on ecrit lhistoire')
        self.assertEqual(tfold('The Great Plains'), 'great plains')


if __name__ == '__main__':
    unittest.main()
