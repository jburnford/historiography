"""LC Books All index (scripts/lc_bib_index.py): binary MARC read with the harvest's rules."""
import gzip
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lc_authority_pilot import bib_headings  # noqa: E402
from lc_bib_index import facts, parse, records  # noqa: E402
from lc_catalogue_harvest import record_facts  # noqa: E402

FIELDS = [
    ('001', None, '13763021'),
    ('008', None, '040527s2005    miua     b    001 0 eng  '),
    ('010', '  ', [('a', '  2004025472')]),
    ('020', '  ', [('a', '0472114913 (cloth : alk. paper)')]),
    ('020', '  ', [('a', '9780472030675')]),
    ('245', '04', [('a', 'The Heimat abroad :'), ('b', 'the boundaries of Germanness /'), ('c', 'edited by …')]),
    ('264', ' 1', [('a', 'Ann Arbor :'), ('b', 'University of Michigan Press,'), ('c', '2005.')]),
    ('100', '1 ', [('a', 'Ricœur, Paul,'), ('d', '1913-2005,'), ('e', 'author.'),
                   ('0', 'http://id.loc.gov/authorities/names/n50014624')]),
    ('700', '1 ', [('a', "O'Donnell, Krista,"), ('d', '1967-'), ('e', 'editor.')]),
    ('700', '12', [('a', 'Marx, Karl,'), ('d', '1818-1883.'), ('t', 'Kapital.')]),     # a work, not a person
    ('700', '3 ', [('a', 'Smith family.')]),                                            # a family
]


def binary(fields):
    data, directory = b'', b''
    for tag, ind, val in fields:
        body = (val if ind is None else ind + ''.join(f'\x1f{c}{v}' for c, v in val)).encode() + b'\x1e'
        directory += f'{tag}{len(body):04d}{len(data):05d}'.encode()
        data += body
    base = 24 + len(directory) + 1
    leader = f'{base + len(data) + 1:05d}nam a22{base:05d}   4500'.encode()
    return leader + directory + b'\x1e' + data + b'\x1d'


def xml(fields):
    out = ['<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/"><srw:numberOfRecords>1'
           '</srw:numberOfRecords><record xmlns="http://www.loc.gov/MARC21/slim">']
    esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;')  # noqa: E731
    for tag, ind, val in fields:
        if ind is None:
            out.append(f'<controlfield tag="{tag}">{esc(val)}</controlfield>')
        else:
            out.append(f'<datafield tag="{tag}" ind1="{ind[0]}" ind2="{ind[1]}">'
                       + ''.join(f'<subfield code="{c}">{esc(v)}</subfield>' for c, v in val) + '</datafield>')
    return ''.join(out) + '</record></srw:searchRetrieveResponse>'


class BooksAllIndex(unittest.TestCase):
    def test_binary_record_gives_what_the_harvest_takes_from_sru(self):
        rec, heads = facts(parse(binary(FIELDS))[1])
        sru_heads, n = bib_headings(xml(FIELDS))
        sru = record_facts(xml(FIELDS))
        for h, extra in zip(sru_heads, sru.pop('heading_extra')):
            h.update(extra)
        self.assertEqual(heads, sru_heads)
        self.assertEqual({k: rec[k] for k in ('control', 'title', 'isbns', 'lccn')}, sru)
        self.assertEqual([h['heading'] for h in heads], ['Ricœur, Paul, 1913-2005', "O'Donnell, Krista, 1967-"])
        self.assertEqual(heads[0]['uri'], 'http://id.loc.gov/authorities/names/n50014624')
        self.assertEqual((rec['date1'], rec['lang'], rec['publisher']), ('2005', 'eng', 'University of Michigan Press'))
        self.assertEqual(rec['isbns'], ['9780472114917', '9780472030675'])

    def test_decomposed_diacritics_are_composed_as_sru_returns_them(self):
        fields = [('001', None, '1'), ('100', '1 ', [('a', 'Reulecke, Ju\u0308rgen.')])]
        _, heads = facts(parse(binary(fields))[1])
        self.assertEqual(heads[0]['heading'], 'Reulecke, J\u00fcrgen.')

    def test_records_split_on_the_terminator_across_chunks(self):
        blob = gzip.compress(binary(FIELDS) * 3)
        with gzip.open(io.BytesIO(blob)) as fh:
            got = list(records(fh, chunk=50))
        self.assertEqual(len(got), 3)
        self.assertEqual(facts(parse(got[2])[1])[0]['control'], '13763021')


if __name__ == '__main__':
    unittest.main()
