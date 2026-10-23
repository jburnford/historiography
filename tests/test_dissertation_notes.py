import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import extract_dissertation_notes as N  # noqa: E402


def spans(*parts):
    """('text', italic) pairs; a plain string is roman."""
    return [(p, False) if isinstance(p, str) else p for p in parts]


def note(number, *parts, page=10):
    return dict(number=number, page=page, spans=spans(*parts))


def test_split_citations_at_top_level_semicolons():
    parts = N.split_citations(spans('Morton, ', ('A History of the Canadian West', True), ', p. 508-509; John Dunn, ',
                                    ('The Oregon Territory', True), ' (London; 1844), p. 31'))
    assert len(parts) == 2  # the semicolon inside parentheses does not cut


def test_note_authors_natural_order_and_signal_words():
    assert N.note_authors('Arthur S. Morton') == ['Arthur S. Morton']
    assert N.note_authors('Alexander Ross, and Kenneth A. Spaulding') == ['Alexander Ross', 'Kenneth A. Spaulding']
    assert N.note_authors('See Edward Said') == ['Edward Said']
    assert N.note_authors('Similarly') == []
    assert N.note_authors('Morton relève plusieurs cas, et il appelle les batailleurs de') == []


def test_canonical_names():
    assert N.canonical('Arthur S. Morton') == ('Morton, Arthur S.', 'Morton')
    assert N.canonical('Pierre BOURDIEU') == ('BOURDIEU, Pierre', 'BOURDIEU')
    assert N.canonical('HALBWACHS F.') == ('HALBWACHS, F', 'HALBWACHS')
    assert N.canonical('Morton, A. S.') == ('Morton, A. S', 'Morton')  # a final period is dropped


def test_parse_note_citation_with_italic_title():
    r = N.parse_citation(spans('Alexander Ross, ', ('The Red River Settlement', True), ', London, Smith, Elder, 1856, p. 35.'), 4)
    assert r['surnames'] == ['Ross'] and r['title'] == 'The Red River Settlement' and r['year'] == 1856


def test_prose_before_a_quoted_phrase_is_not_an_author():
    r = N.parse_citation(spans('Adam Thom « fait confiance » à Sarah Ballenden et provoque le procès.'), 4)
    assert not r or not r.get('surnames')


def test_unstyled_typescript_citation():
    r = N.parse_citation(spans('Robert Sellar, History of the County of Huntingdon, Huntingdon, 1888, pp. 512-5.'), 4)
    assert r['surnames'] == ['Sellar'] and r['title'].startswith('History of the County of Huntingdon') and r['kind'] == 'unstyled'


def test_place_of_publication_is_not_an_author():
    r = N.parse_citation(spans('London, “Algebraic notation in dramatic texts”, ', ('Mnemosyne', True), ' 12 (1959).'), 4)
    assert not r or not r.get('surnames')


def test_title_residue_is_stripped():
    r = N.parse_citation(spans('Pierre Gerbet, ', ('Dictionnaire historique de l’Europe unie, op. cit.', True), ', p. 12.'), 4)
    assert r['title'] == 'Dictionnaire historique de l’Europe unie'


def test_reconstruct_counts_ibid_short_titles_and_op_cit():
    notes = [
        note(1, 'Arthur S. Morton, ', ('A History of the Canadian West to 1870-71', True), ', London, Nelson, 1939, p. 508.'),
        note(2, ('Ibid.', True), ', p. 510.'),
        note(3, 'Morton, ', ('A History of the Canadian West', True), ', p. 512; Marcel Giraud, ', ('Le Métis canadien', True),
             ', Paris, Institut d’ethnologie, 1945, p. 3.'),
        note(4, 'Giraud, op. cit., p. 7.'),
    ]
    works, cites = N.reconstruct(notes)
    by = {w['surnames'][0]: w for w in works}
    assert set(by) == {'Morton', 'Giraud'}
    assert by['Morton']['citations'] == 3 and by['Giraud']['citations'] == 2
    assert by['Morton']['year'] == 1939 and by['Morton']['first_page'] == 11  # 1-based, as in entries.jsonl
    assert cites == 5


def test_classical_abbreviations_are_not_works():
    works, _ = N.reconstruct([note(1, 'Cic. ', ('Off.', True), ' 1.22; Suet. ', ('Iul.', True), ' 44.')])
    assert works == []


def test_run_on_citations_are_cut_at_a_new_author_and_title():
    works, _ = N.reconstruct([note(1, 'Laure Adler, ', ('La vie quotidienne dans les maisons closes', True),
                                   ', Paris, Hachette, 1990, p. 3. See also Alain Corbin, ', ('Les filles de noce', True),
                                   ', Paris, Aubier, 1978.')])
    assert [(w['surnames'][0], w['year']) for w in works] == [('Adler', 1990), ('Corbin', 1978)]


def test_abbreviations_and_initials_do_not_cut():
    assert len(N.split_citations(spans('Arthur S. Morton, ', ('A History of the Canadian West', True), ', vol. II. p. 3.'))) == 1
    assert len(N.split_citations(spans('Morton, op. cit., p. 3. Voir ', ('A History of the Canadian West', True)))) == 1
    # 'Ibid., vol. II.' followed by a new author and title is two citations
    assert len(N.split_citations(spans('Ibid., vol. II. A. S. Morton, ', ('A History of the Canadian West', True)))) == 2
