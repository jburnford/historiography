"""Historians' CVs as a benchmark for the graph (2026-11-03). Read-only.

User, 2026-11-03: "a few random CVs we can use; they're not a gold standard as they could be out of date" (Ian
Milligan's, updated November 2026, "probably close to gold"). For each CV (text from pdftotext) and the person's
name, against the built graph (build/graph/historiography.lbug):
- every key whose label agrees with the name (key_registry.names_compatible), with its PIDs, and how many of its
  works the CV names (main title found in the CV text): keys whose works the CV confirms are that person, so a
  person on several such keys is a split to merge, and a key with works the CV does not name may hold a
  namesake's or an out-of-date CV's;
- the CV's titles (quoted titles, and the italic-less book lines under headings like 'Books') missing from the
  graph, by kind;
- the CV's doctorate line beside the graph's thesis and advisor; supervision names beside ADVISED students.
Writes <out>/<person>.json and a summary table.

    python3 scripts/cv_benchmark.py --cv /mnt/e/historiography-dissertation-pdfs/Milligan_CV.pdf 'Milligan, Ian' ... \\
        --out data/identifiers/cv-benchmark-2026-11-03
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

from identifiers import ROOT
from key_lc_works import title_key
from key_registry import names_compatible

QUOTED = re.compile(r'[“"]([^”"]{12,250})[”"]')
BOOKISH = re.compile(r'^\s*(books?|monographs?|authored books|edited (books|volumes|collections)|books? and edited)', re.I)
SECTION = re.compile(r'^\s*([A-Z][A-Za-z ,&/()-]{3,60})\s*$')
DOCTORATE = re.compile(r'ph\.?\s?d|d\.?\s?phil|doctor(ate)? of philosophy', re.I)


def norm(t):
    """All of a text's words, lower case, accents and punctuation dropped (title_key keeps only ten words)."""
    import unicodedata
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return ' ' + ' '.join(re.findall(r'[a-z0-9]+', t)) + ' '


def cv_titles(text):
    """(kind, title) the CV lists: quoted titles (articles, chapters), and in book sections the text before the
    first period or parenthesis of each entry."""
    out, section = [], ''
    for line in text.splitlines():
        if SECTION.match(line) and len(line.split()) <= 8:
            section = line.strip()
        for m in QUOTED.finditer(line):
            out.append(('quoted', m.group(1).strip(' .,')))
        if BOOKISH.match(section) and re.search(r'[A-Za-z]{4}', line) and not QUOTED.search(line):
            t = re.split(r'\s[(]|\.\s|\(\d{4}|,\s(?:University|Oxford|Cambridge|Toronto|Montreal|McGill)', line.strip())[0]
            if len(title_key(t).split()) >= 3:
                out.append(('book', t.strip(' .,*')))
    seen, uniq = set(), []
    for k, t in out:
        if title_key(t) not in seen:
            seen.add(title_key(t))
            uniq.append((k, t))
    return uniq


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--cv', nargs=2, action='append', metavar=('PDF', 'NAME'), required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    import ladybug as lb
    conn = lb.Connection(lb.Database(str(ROOT / 'build/graph/historiography.lbug'), read_only=True))

    def q(s, **p):
        r = conn.execute(s, p) if p else conn.execute(s)
        out = []
        while r.has_next():
            out.append(r.get_next())
        return out
    args.out.mkdir(parents=True, exist_ok=True)
    summary = []
    for pdf, name in args.cv:
        text = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
        ntext = norm(text)
        family = name.split(',')[0].strip()
        keys = [r for r in q('MATCH (p:Person) WHERE lower(p.label) CONTAINS $f RETURN p.key, p.label, p.resolution, p.wd, p.lcnaf, p.orcid',
                               f=family.lower()) if names_compatible(r[1], name)]
        people = []
        for key, label, res, wd, lc, orcid in keys:
            works = q('MATCH (p:Person {key: $k})-[:AUTHORED|EDITED]->(w:Work) RETURN w.key, w.kind, w.year, w.label', k=key)
            named = [w for w in works if len(norm(w[3].split(':')[0]).split()) >= 3 and norm(w[3].split(':')[0]) in ntext]
            students = [r[0] for r in q('MATCH (p:Person {key: $k})-[:ADVISED]->(s:Person) RETURN s.label', k=key)]
            advisor = [r[0] for r in q('MATCH (a:Person)-[:ADVISED]->(p:Person {key: $k}) RETURN a.label', k=key)]
            people.append(dict(key=key, label=label, resolution=res, wd=wd, lc=lc, orcid=orcid, works=len(works),
                               works_on_cv=len(named), not_on_cv=[f'{w[1]} {w[2]} {w[3][:90]}' for w in works if w not in named],
                               advisor=advisor, students=students,
                               students_on_cv=[s for s in students if s.split(',')[0].split()[-1].lower() in text.lower()]))
        labels = {title_key(w[3].split(':')[0]) for p in people
                  for w in q('MATCH (x:Person {key: $k})-[:AUTHORED|EDITED]->(w:Work) RETURN w.key, w.kind, w.year, w.label', k=p['key'])}
        titles = cv_titles(text)
        missing = [(k, t) for k, t in titles if title_key(t.split(':')[0]) not in labels]
        doctorate = [l.strip() for l in text.splitlines() if DOCTORATE.search(l)][:3]
        rec = dict(cv=Path(pdf).name, name=name, keys=people, cv_titles=len(titles), cv_titles_missing=len(missing),
                   missing_sample=[f'{k}: {t[:100]}' for k, t in missing[:40]], doctorate_lines=doctorate)
        (args.out / f'{title_key(name).replace(" ", "-")}.json').write_text(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
        summary.append(dict(name=name, keys=[(p['key'], p['resolution'], p['works'], p['works_on_cv']) for p in people],
                            cv_titles=len(titles), in_graph=len(titles) - len(missing)))
    (args.out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n')
    for s in summary:
        print(json.dumps(s, ensure_ascii=False))


if __name__ == '__main__':
    main()
