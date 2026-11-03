import gzip
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from gnd_person_index import nodes, row  # noqa: E402

# The dump's layout: blank nodes (name variants) and records in one array, two-space indented.
DUMP = '''[ [ {
  "@id" : "_:node1",
  "https://d-nb.info/standards/elementset/gnd#surname" : [ {
    "@value" : "Bauer"
  } ]
}, {
  "@id" : "https://d-nb.info/gnd/100000231",
  "@type" : [ "https://d-nb.info/standards/elementset/gnd#DifferentiatedPerson" ],
  "http://www.w3.org/2002/07/owl#sameAs" : [ {
    "@id" : "http://viaf.org/viaf/66737403"
  }, {
    "@id" : "https://isni.org/isni/0000000080882007"
  }, {
    "@id" : "http://www.wikidata.org/entity/Q324487"
  }, {
    "@id" : "http://id.loc.gov/rwo/agents/n89664715"
  }, {
    "@id" : "https://d-nb.info/gnd/1325000884"
  } ],
  "https://d-nb.info/standards/elementset/gnd#dateOfBirth" : [ {
    "@value" : "1600-05-31",
    "@type" : "http://www.w3.org/2001/XMLSchema#date"
  } ],
  "https://d-nb.info/standards/elementset/gnd#preferredNameForThePerson" : [ {
    "@value" : "Baur, Johann \\"Wilhelm\\""
  } ]
}, {
  "@id" : "https://d-nb.info/gnd/100000355",
  "@type" : [ "https://d-nb.info/standards/elementset/gnd#DifferentiatedPerson" ],
  "http://www.w3.org/2002/07/owl#sameAs" : [ {
    "@id" : "http://viaf.org/viaf/22476932"
  } ]
} ] ]
'''


class Nodes(unittest.TestCase):
    def test_records(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'dump.jsonld.gz'
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                f.write(DUMP)
            rows = [r for r in map(row, nodes(str(path))) if r]
        self.assertEqual(len(rows), 1)            # the VIAF-only record has no LC or Wikidata link
        r = rows[0]
        self.assertEqual((r['gnd'], r['kind'], r['name'], r['birth']),
                         ('100000231', 'DifferentiatedPerson', 'Baur, Johann "Wilhelm"', '1600-05-31'))
        self.assertEqual((r['lc'], r['wd'], r['viaf'], r['isni'], r['gnd_alt']),
                         (['n89664715'], ['Q324487'], ['66737403'], ['0000000080882007'], ['1325000884']))


if __name__ == '__main__':
    unittest.main()
