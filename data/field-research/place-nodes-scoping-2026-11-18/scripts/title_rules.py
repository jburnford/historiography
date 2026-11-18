"""Test cheap title rules on the hand-checked sets: how many wrong matches each rule removes, and at what cost.

Rules (each removes a match):
  cite     the place word sits in a citation tail: 'London:', '(London', 'Ithaca and London', 'London and New York',
           or the title carries 'Press' / 'pp.' / 'ISBN' / '£' / '$' and the place word is followed by ',' or ':'
  names    a namesake list: Jack London, the London Charivari; Prince Albert with consort/Victoria/Coburg/Monaco/
           Society/expedition/Franklin/Wettin; Colombo Plan/Powers/Conference, Cristoforo/Christopher, an Italian
           given name before Colombo; Regina followed or preceded by a capitalised name (Regina Schulte, Elis Regina),
           'Salve Regina', 'Regina v.', Latin context; Estevan de/Jose; 'SS'/'HMS' before a place name
  other    another place of the name: 'London, Ont', 'Ontario', 'Brooklyn', 'Prairie du Chien', 'Bay of Bengal'
Prints, per probe set: matches, wrong, removed-wrong, removed-right.
"""
import csv
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent

CITE = re.compile(r'(\b(London|Colombo|Regina|Gdańsk)\s*:|\((London|Colombo|Regina|Gdańsk)\b|\b(Ithaca|Oxford|New York|Chicago|Toronto|Princeton|Cambridge|Basingstoke|Abingdon) and London\b|\bLondon and (New York|Sydney)\b)')
CITE_CTX = re.compile(r'(Press|\bpp\.|\bPp\.|ISBN|£|\$\d)')
NAMES = re.compile(r'(Jack London|London Charivari|Prince Albert (and|of Monaco|I\b|II\b|Society|expedition|Sesquicentennial)|Queen (Victoria )?and Prince Albert|Prince Albert(,)? (his|the life)|of Prince Albert\b(?!,? Sask)|Prinz Albert|Colombo Plan|Colombo Powers|Colombo [Cc]onference|Cristoforo Colombo|Crist[oó]v[aã]o Colombo|Christopher Columbus|(Emanuele|Paolo|Realdo|Giacomo|Carlo|John Robert|Elisabetta|Maria|Fernando|Luigia|Michele|Adelaide) Colombo|Colombo,|Colombo\'s|Salve Regina|Regina v\b|Regina (Coeli|Maria|Mundi|Maris|di|della|Angelorum|Laudis)|Elis Regina|Victoria Regina|\b(SS|HMS) [A-Z])')
GIVEN_REGINA = re.compile(r'Regina [A-Z][a-zà-ÿ]+(?! (Riot|Manifesto|Rifle|College|Campus|Five|Municipal|Labour))|[A-Z][a-z]+ Regina\b(?!,)')
OTHER = re.compile(r'(London,? Ont|South ?[Ww]estern Ontario|Brooklyn|Prairie du Chien|Prairie Grove|Bay of Bengal|National Park)')


def flags(title, place):
    f = []
    if CITE.search(title) or (CITE_CTX.search(title) and re.search(place + r'\s*[,:]', title)):
        f.append('cite')
    if NAMES.search(title) or (place == 'Regina' and GIVEN_REGINA.search(title)):
        f.append('names')
    if OTHER.search(title):
        f.append('other')
    return f


def run(rows, label):
    tot = wrong = rm_wrong = rm_right = 0
    for title, place, verdict in rows:
        tot += 1
        bad = verdict != 'right'
        wrong += bad
        if flags(title, place):
            rm_wrong += bad
            rm_right += (not bad)
    after = (tot - wrong - rm_right) / max(1, tot - rm_wrong - rm_right)
    print(f'{label:28s} matches {tot:4d} wrong {wrong:4d} precision {100*(tot-wrong)/tot:5.1f}% | rules remove wrong {rm_wrong:4d} right {rm_right:3d} | precision after {100*after:5.1f}%')


def main():
    sample = list(csv.DictReader(open(D / 'title-handcheck.csv')))
    for p in sorted({r['probe'] for r in sample}):
        run([(r['title'], p.split('/')[0], r['class']) for r in sample if r['probe'] == p], 'sample: ' + p)
    for f, places in (('ceylon-works-checked.csv', None), ('saskatchewan-works-checked.csv', None)):
        rows = list(csv.DictReader(open(D / f)))
        by = {}
        for r in rows:
            for pl in r['matched_places'].split('+'):
                by.setdefault(pl, []).append((r['title'], pl.split(' (')[0], 'right' if r['verdict'] == 'right' else 'wrong'))
        for pl in sorted(by, key=lambda k: -len(by[k]))[:8]:
            run(by[pl], 'full: ' + pl)


if __name__ == '__main__':
    main()
