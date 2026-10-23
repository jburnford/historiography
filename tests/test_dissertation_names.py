import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dissertation_names import bibliography_order, normalise_first_authors, split_name  # noqa: E402

# Real comma-less first authors sampled from entries.jsonl (2026-10-21) and from notes.
CASES = [
    ('Bart CROMBEZ', None, 'CROMBEZ'), ('MONNIER Raymonde', None, 'MONNIER'), ('KENDON Adam', None, 'KENDON'),
    ('Scarlett BEAUVALET-BOUTOUYRIE', None, 'BEAUVALET-BOUTOUYRIE'), ('Pierre BARRAL', None, 'BARRAL'),
    ('EL HOUCINE Rahmoune', None, 'EL HOUCINE'), ('HAO Yufan', None, 'HAO'), ('JACKSON Julian', None, 'JACKSON'),
    ('Emmanuel LE ROY LADURIE', None, 'LE ROY LADURIE'), ('D’ALLEMAGNE Henry-René', None, 'D’ALLEMAGNE'),
    ('Sassoon D', None, 'Sassoon'), ('Sassoon D.', None, 'Sassoon'), ('De Niro MJ', None, 'De Niro'),
    ('Soeradi E.S', None, 'Soeradi'), ('HALBWACHS F.', None, 'HALBWACHS'),
    ('M. MASSENZIO', None, 'MASSENZIO'), ('P. De Souza', None, 'De Souza'), ('E.G. Gimpelson', None, 'Gimpelson'),
    ('J.-P. Sartre', None, 'Sartre'), ('Arthur J. RAY', None, 'RAY'), ('Peter LEE', None, 'LEE'),
    ('Nicole BRUNETON- GOVERNATORI', None, 'BRUNETON-GOVERNATORI'),
    ('Tadié Jean-Yves', 'surname_first', 'Tadié'), ('Zhang Kuitang', 'surname_first', 'Zhang'),
    ('Zigurds L. Zile', 'natural', 'Zile'), ('Robert Dallek', 'natural', 'Dallek'), ('John L.H. Keep', 'natural', 'Keep'),
    ('Alexis de Tocqueville', 'natural', 'de Tocqueville'), ('Hans-Albin Larsson', 'natural', 'Larsson'),
    ('Robert Dallek', None, None),  # no order signal: left as it was
    ('Léon XIII', 'natural', None), ('LÉON XIII', None, None), ('Pius XI', 'natural', None),
    ('American Friends Service Committee', None, None), ('Latina Feminist Group', None, None), ('FRANCE', None, None),
]


@pytest.mark.parametrize('name,order,surname', CASES)
def test_split_name(name, order, surname):
    got = split_name(name, order)
    assert (got[0] if got else None) == surname


def test_bibliography_order_reads_alphabetisation():
    natural = ['Robert Dallek', 'Ilya Ehrenburg', 'Sheila Fitzpatrick', 'Peter Kenez', 'John Reed', 'Liudmila Stern', 'Mikhail Zelenov']
    surname_first = ['Accornero Guya', 'Confino Michael', 'Tadié Jean-Yves', 'Tort Patrick', 'Zhang Kuitang', 'Zile Zigurds']
    assert bibliography_order(natural) == 'natural'
    assert bibliography_order(surname_first) == 'surname_first'
    assert bibliography_order(natural[:4]) is None  # too few to tell


def test_normalise_first_authors_rewrites_in_place():
    entries = [dict(authors=[n], surnames=[n]) for n in
               ['Robert Dallek', 'Ilya Ehrenburg', 'Sheila Fitzpatrick', 'Peter Kenez', 'John Reed', 'Liudmila Stern', 'Mikhail Zelenov']]
    entries.append(dict(authors=['GINZBURG Carlo'], surnames=['GINZBURG Carlo']))
    entries.append(dict(authors=['Kotkin, Stephen'], surnames=['Kotkin']))
    assert normalise_first_authors(entries) == 8
    assert entries[0]['authors'][0] == 'Dallek, Robert' and entries[0]['surnames'][0] == 'Dallek'
    assert entries[7]['surnames'][0] == 'GINZBURG'
    assert entries[8]['authors'][0] == 'Kotkin, Stephen'
