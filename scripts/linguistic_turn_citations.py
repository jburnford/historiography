#!/usr/bin/env python3
"""Has the linguistic turn dissipated? Citation of its classics in History PhDs over time.

User question (2026-10-22): "how much the linguistic turn has dissipated … how much Derrida and
Foucault get cited vs softer citations to Scott or no citations to any of the linguistic turn
classics". For each strict History PhD in the graph (``dissertations.csv``: ``in_analysis``),
its bibliography entries (or notes-rebuilt entries) are matched against four groups:

- **theory**: the poststructuralist and linguistic canon itself: Derrida, Saussure, Barthes,
  Lacan, Kristeva, Lyotard, Baudrillard, Paul de Man, and Foucault's discourse works
  (*Archaeology of Knowledge*, *Order of Things*, *Birth of the Clinic*, *L'ordre du discours*,
  'What is an Author?', 'Nietzsche, Genealogy, History');
- **historians**: the historians' linguistic and cultural turn: Hayden White's theory of
  narrative, LaCapra, Ankersmit, Toews, Spiegel, Keith Jenkins, Patrick Joyce, Stedman Jones's
  *Languages of Class*, Sewell, Hunt's *New Cultural History* / *Beyond the Cultural Turn*,
  Chartier's representations essays, Rorty's *The Linguistic Turn*, Appleby, Hunt and Jacob,
  Berkhofer;
- **scott**: Joan Scott's 'Gender: A Useful Category', 'The Evidence of Experience' and *Gender
  and the Politics of History* (the soft, often ritual citation);
- **foucault_power**: Foucault's other works (*Discipline and Punish*, *History of Sexuality*,
  *Madness and Civilization*, lectures, governmentality), kept apart because they are cited as
  frameworks of power rather than of language.

Presence per thesis (user rule: one count per thesis, not per note). Output per country and
five-year period: theses, and the share citing each group, the 'soft only' share (historians or
Scott, no theory) and the share citing none of the four. Matching is by folded author text and
title words; a citation is not engagement.
"""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dissertation_scope import summary_dir  # noqa: E402


def fold(t):
    t = unicodedata.normalize('NFKD', (t or '').replace('œ', 'oe').replace('Œ', 'Oe'))
    t = ''.join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', t)).strip()


# (group, label, author pattern on folded author text, title pattern on folded title or None = any title)
RULES = [
    ('theory', 'Derrida', r'\bderrida\b', None),
    ('theory', 'Saussure', r'\bsaussure\b', r'linguisti|cours'),
    ('theory', 'Barthes', r'\bbarthes\b', None),
    ('theory', 'Lacan', r'\blacan\b', None),
    ('theory', 'Kristeva', r'\bkristeva\b', None),
    ('theory', 'Lyotard', r'\blyotard\b', None),
    ('theory', 'Baudrillard', r'\bbaudrillard\b', None),
    ('theory', 'de Man', r'\bman\b.*\bpaul\b|\bpaul de man\b|\bde man\b', r'blindness|allegories of reading|resistance to theory|rhetoric of romanticism|aesthetic ideology'),
    ('theory', 'Foucault (discourse)', r'\bfoucault\b',
     r'archaeolog|archeolog|order of things|mots et les choses|ordre du discours|order of discourse|discourse on language|'
     r'what is an author|qu est ce qu un auteur|nietzsche|birth of the clinic|naissance de la clinique'),
    ('historians', 'Hayden White', r'\bwhite\b',
     r'metahistory|content of the form|tropics of discourse|figural realism|practical past|historical text as literary|'
     r'burden of history|value of narrativity|fictions of factual|historical emplotment'),
    ('historians', 'LaCapra', r'\blacapra\b|\bla capra\b', None),
    ('historians', 'Ankersmit', r'\bankersmit\b', None),
    ('historians', 'Toews', r'\btoews\b', r'linguistic turn'),
    ('historians', 'Spiegel', r'\bspiegel\b', r'past as text|historicism|social logic|practicing history|linguistic turn|postmodern'),
    ('historians', 'Keith Jenkins', r'\bjenkins\b', r're ?thinking history|postmodern|why history|refiguring history|the postmodern history reader'),
    ('historians', 'Patrick Joyce', r'\bjoyce\b', r'visions of the people|democratic subjects|rule of freedom|end of social history|post ?modern'),
    ('historians', 'Stedman Jones', r'\bstedman\b|\bjones\b', r'languages of class'),
    ('historians', 'Sewell', r'\bsewell\b', r'logics of history|work and revolution|theory of structure|events as transformations|concept s of culture'),
    ('historians', 'Hunt (cultural turn)', r'\bhunt\b|\bbonnell\b', r'new cultural history|beyond the cultural turn'),
    ('historians', 'Chartier (representations)', r'\bchartier\b', r'monde comme representation|edge of the cliff|bord de la falaise|between practices and representations|cultural history between'),
    ('historians', 'Rorty (Linguistic Turn)', r'\brorty\b', r'linguistic turn'),
    ('historians', 'Appleby, Hunt and Jacob', r'\bappleby\b', r'telling the truth about history'),
    ('historians', 'Berkhofer', r'\bberkhofer\b', r'beyond the great story'),
    ('scott', 'Joan Scott', r'\bscott\b', r'useful category|evidence of experience|gender and the politics of history|genre une categorie utile'),
    ('foucault_power', 'Foucault (power and other)', r'\bfoucault\b', None),  # after the discourse rule
]
COMPILED = [(g, lab, re.compile(a), re.compile(t) if t else None) for g, lab, a, t in RULES]
GROUPS = ['theory', 'historians', 'scott', 'foucault_power']


def classify(e):
    author = fold(e.get('author') or ' '.join(e.get('authors') or []) or e.get('raw', '')[:80])
    title = fold(e.get('title'))
    for g, lab, a, t in COMPILED:
        if a.search(author) and (t is None or (title and t.search(title))):
            return g, lab
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--from-year', type=int, default=1975)
    args = p.parse_args()
    out = args.out
    theses = {}
    for r in csv.DictReader((out / 'dissertations.csv').open()):
        if r['in_analysis'] == 'True' and r['year'] and int(r['year']) >= args.from_year:
            theses[r['id']] = dict(year=int(r['year']), country=r['country'], status=r['extraction_status'])
    final = {}
    for line in (out / 'extraction.jsonl').open():
        x = json.loads(line)
        final[x['id']] = x.get('entries') or 0
    hits = defaultdict(set)    # thesis -> groups
    labels = defaultdict(set)  # thesis -> labels
    sources = [(out / 'entries.jsonl', lambda did: theses.get(did, {}).get('status') == 'parsed')]
    if (out / 'notes-entries.jsonl').exists():
        sources.append((out / 'notes-entries.jsonl', lambda did: theses.get(did, {}).get('status') == 'parsed_notes'))
    for path, wanted in sources:
        for line in path.open():
            did = line.split('"', 4)[3]
            if not wanted(did):
                continue
            low = line.lower()
            if not any(k in low for k in ('derrida', 'saussure', 'barthes', 'lacan', 'kristeva', 'lyotard', 'baudrillard', 'man',
                                          'foucault', 'white', 'lacapra', 'capra', 'ankersmit', 'toews', 'spiegel', 'jenkins', 'joyce',
                                          'jones', 'sewell', 'hunt', 'bonnell', 'chartier', 'rorty', 'appleby', 'berkhofer', 'scott')):
                continue
            e = json.loads(line)
            if path.name == 'entries.jsonl' and e['n'] >= final.get(did, 0):
                continue  # a row left over from an earlier extraction
            c = classify(e)
            if c:
                hits[did].add(c[0])
                labels[did].add(c[1])
    rows = []
    for country in ['ALL', 'CA', 'US', 'FR']:
        bins = defaultdict(list)
        for did, t in theses.items():
            if country == 'ALL' or t['country'] == country:
                bins[(t['year'] // 5) * 5].append(did)
        for start in sorted(bins):
            ds = bins[start]
            n = len(ds)
            share = lambda f: round(100 * sum(1 for d in ds if f(hits.get(d, set()))) / n, 1)  # noqa: E731
            row = dict(country=country, period=f'{start}-{start + 4}', theses=n,
                       theory=share(lambda h: 'theory' in h), historians=share(lambda h: 'historians' in h),
                       scott=share(lambda h: 'scott' in h), foucault_power=share(lambda h: 'foucault_power' in h),
                       soft_only=share(lambda h: not ('theory' in h) and ('historians' in h or 'scott' in h)),
                       none=share(lambda h: not h))
            for lab in ('Derrida', 'Foucault (discourse)', 'Foucault (power and other)', 'Hayden White', 'Joan Scott', 'LaCapra', 'Barthes'):
                row[lab] = round(100 * sum(1 for d in ds if lab in labels.get(d, set())) / n, 1)
            rows.append(row)
    dest = summary_dir(out) / 'linguistic-turn'
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / 'linguistic-turn-by-period.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (dest / 'rules.json').write_text(json.dumps(RULES, indent=1))
    for r in rows:
        if r['theses'] >= 40:
            print(f"{r['country']:3} {r['period']} n={r['theses']:5}  theory {r['theory']:5}  historians {r['historians']:5}  scott {r['scott']:5}  "
                  f"F-power {r['foucault_power']:5}  soft-only {r['soft_only']:5}  none {r['none']:5} | Derrida {r['Derrida']:4} "
                  f"F-disc {r['Foucault (discourse)']:4} White {r['Hayden White']:4} Scott {r['Joan Scott']:4}")


if __name__ == '__main__':
    main()
