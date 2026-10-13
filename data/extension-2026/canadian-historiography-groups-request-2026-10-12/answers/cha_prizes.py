#!/usr/bin/env python3
"""CHA prize winners as evidence of professional recognition, set beside doctoral uptake.

Prizes record what the profession judges important (the user, 2026-10-12): a committee that
launches a prize has decided its field matters, so a prize's first award is a dated
institutional milestone. Citations by History PhDs (2009-2026) record what the next generation
uses. This script:
1. parses the saved CHA winner pages (citation and jury text);
2. matches winners to the scholar packet, the draft rosters and the atlas people;
3. matches winning works to the citation graph (title key) for their PhD uptake;
4. writes the prize timeline (first and last award listed on the CHA site) and the
   recognition-versus-uptake table.

Inputs: the saved pages (--pages; fetched from https://cha-shc.ca/prize-winners/ on 2026-10-12)
and winners.json. Writes cha-prizes.json and cha-prize-works.csv beside this script. Run from
the repository root. The CHA site's earliest listed year may not be a prize's true first award,
and the Clio Prizes are listed only in part.
"""
import argparse
from collections import Counter, defaultdict
import csv
import html
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
sys.path.insert(0, str(ROOT / 'scripts'))
from build_dissertation_citation_graph import title_key  # noqa: E402

FIELD = {  # prize -> the proposed group or atlas entry it institutionalises
    'Indigenous History': 'native_newcomer / indigenous', 'Political History': 'cdn_political_national',
    'Womens and Gender': 'cdn_women_gender', 'Hilda Neatby': 'cdn_women_gender', 'Migration, Ethnicity': 'cdn_immigration_ethnicity',
    'Labour History': 'cdn_working_class', 'Neil Sutherland': 'cdn_childhood_youth', 'Sexuality': 'moral_regulation / queer',
    'Business History': 'business history (no group)', 'Environment': 'environment (North American)', 'Public History': 'publichistory',
    'Oral History': 'oral', 'Media and Communication': 'media history (no group)', 'Fecteau': 'quebec_historiography / social',
    'Garneau': 'general (best book, all fields)', 'Best Scholarly Book': 'general (best book, Canadian history)',
    'Clio': 'cdn_regional', 'Corey': 'Canadian–American relations', 'Journal Prize': 'general (JCHA article)',
    'meilleur livre': 'general (best French-language book)'}


# Reviewed corrections where the automatic match took a stray variant record (checked 2026-10-12 against
# the citation graph; the winning book is named on the CHA page).
OVERRIDES = {('gauvreau', 2006): r'catholic origins of quebec|origines catholiques de la r',
             ('iacovetta', 2008): r'^gatekeepers:? reshaping', ('ducharme', 2011): r'concept de libert',
             ('luby', 2021): r'^dammed:', ('reiter', 2020): r'wounded feelings'}


def fold(t):
    t = unicodedata.normalize('NFKD', t or '')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', ''.join(c for c in t if not unicodedata.combining(c)).lower())).strip()


def parse_page(path):
    t = path.read_text(encoding='utf-8', errors='replace')
    m = re.search(r'<main.*?</main>', t, re.S) or re.search(r'<article.*?</article>', t, re.S)
    text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(0) if m else t))).strip()
    text = re.sub(r'^.*?Latest Winners.*?(?=(?:The |Best |Political |Prize |Prix |Canadian |Network |Public |Media ))', '', text, count=1)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pages', type=Path, required=True)
    ap.add_argument('--winners', type=Path, required=True)
    args = ap.parse_args()
    winners = json.loads(args.winners.read_text())[1:]
    g = json.loads((OUT / 'graph.json').read_text())
    nodes = {n['id']: n for n in g['nodes']}
    diss = {k for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis') and n['year'] and 2009 <= n['year'] <= 2026}
    citing = defaultdict(set)
    authored = defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            citing[e['target']].add(e['source'])
        elif e['type'] == 'AUTHORED':
            authored[e['target']].add(e['source'])
    by_title = defaultdict(list)
    for k, n in nodes.items():
        if n['type'] == 'Work' and citing.get(k):
            by_title[title_key(n['title'])].append(k)
    surname_works = defaultdict(set)
    for w, ps in authored.items():
        if citing.get(w):
            for p in ps:
                surname_works[fold(p[2:].split('|')[0]).split()[-1] if fold(p[2:].split('|')[0]) else ''].add(w)
    cands = {fold(' '.join(reversed(r['name'].split(', ')))) : r for r in csv.DictReader(
        (ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12/candidates.csv').open())}
    roster = {}
    with (HERE.parent / 'people.csv').open() as f:
        for r in csv.DictReader(f):
            roster[fold(r['label'])] = r
    atlas = {fold(p['label']): p for p in json.loads((ROOT / 'historiography-1920-2000.json').read_text())['people']}

    rows, timeline = [], defaultdict(list)
    for name, prize, year, link in winners:
        y = int(year) if year.isdigit() else None
        timeline[prize].append(y)
        page = args.pages / (re.sub(r'[^a-z0-9-]', '_', link.rstrip('/').split('/')[-1]) + '.html') if link else None
        text = parse_page(page) if page and page.exists() else ''
        # citation: '<prize> <year> <names> , <Title> . <imprint>' -- take the text after the first ' , '
        seg = text.split(f'{prize} {year}', 1)[-1] if text else ''
        title = ''
        seg2 = re.sub(r'^.*?\b(?:translated|traduit) by [^,]+,\s*', ' , ', seg)
        # the title ends at '. ' before an imprint (Place: Publisher), a journal, a year or 'This/Ce' jury text
        # CHA citations put a space before the closing period: 'Title . Publisher' or '“Title .” Journal' or '« Titre ». Revue'
        m = None
        first = re.split(r'\s*(?:&|,| and | et |/)\s*', name)[0].strip()
        if first:  # anchor on the winner's own name, as older pages list several names and mentions
            m = re.search(re.escape(first) + r'[^,]{0,80}?\s*,\s*(?:(?:editors?|eds?\.?|dir\.?)\s*,\s*)?[“"«‘]?\s*(.+?)(?=\s\.[”"»’]?\s|\s[»”]\.\s|[”"»],|\sHonou?rable|\sMention|\s\(|\s[A-Z][a-zé]+(?:\s[A-Z]\.)*\s[A-Z][a-zé’\'-]+\s,|$)', seg2[:1500])
        if not m:
            m = re.search(r'\s,\s*(.+?)(?:\s\.[”"»’]?|\s[»”]\.)\s', seg2)
        if m:
            title = m.group(1).strip().strip('“”"«»‘’ ').strip()
        people = [fold(x) for x in re.split(r',| and | et |&|/', name) if fold(x)]
        works = by_title.get(title_key(title), []) if title else []
        if text:  # match without parsing: same-title records by a winner (surname and first initial) whose main title is on the page
            page_words = set(fold(seg[:2000]).split())
            groups = defaultdict(list)
            for person in people:
                parts = person.split()
                if len(parts) < 2:
                    continue
                for w in surname_works.get(parts[-1], ()):
                    if not any(p.startswith('P:') and p[2:].split('|')[-1][:1] == parts[0][:1] for p in authored[w]):
                        continue
                    toks = [x for x in fold(title_key(nodes[w]['title'])).split() if len(x) >= 3]
                    if len(toks) >= 2:
                        hit = sum(x in page_words for x in toks) / len(toks)
                        if hit >= 0.8:
                            groups[(hit, title_key(nodes[w]['title']))].append(w)
            if groups:
                def up(ws):
                    return len(set().union(*(citing[x] for x in ws)))
                (hit, _), cand = max(groups.items(), key=lambda kv: (kv[0][0], up(kv[1])))
                if not works or up(cand) > up(works):
                    works = cand
        ov = next((rx for (sur, yr), rx in OVERRIDES.items() if yr == y and any(sur in pp for pp in people)), None)
        if ov:
            works = [w for w, n in nodes.items() if n['type'] == 'Work' and citing.get(w) and re.search(ov, n['title'] or '', re.I)]
            title = nodes[works[0]]['title'] if works else title
            if works and not title:
                title = nodes[works[0]]['title']
        uptake = len(set().union(*(citing[w] for w in works))) if works else 0
        rows.append(dict(prize=prize, year=y, winner=name, title=title, field=next((v for k, v in FIELD.items() if k.lower() in prize.lower()), ''),
                         phds_2009_2026=uptake, matched_works=len(works),
                         in_scholar_packet=any(p in cands for p in people), in_draft_rosters=any(p in roster for p in people),
                         in_atlas_people=any(p in atlas for p in people), url=link))
    tl = {p: dict(first_listed=min(y for y in ys if y), last_listed=max(y for y in ys if y), awards=len(ys),
                  field=next((v for k, v in FIELD.items() if k.lower() in p.lower()), '')) for p, ys in timeline.items()}
    with (HERE / 'cha-prize-works.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    books = [r for r in rows if re.search(r'book|livre|garneau|clio|corey', r['prize'], re.I)]
    out = dict(source='https://cha-shc.ca/prize-winners/ (fetched 2026-10-12)', winners=len(rows),
               titles_parsed=sum(1 for r in rows if r['title']), matched_to_graph=sum(1 for r in rows if r['matched_works']),
               timeline=dict(sorted(tl.items(), key=lambda kv: kv[1]['first_listed'])),
               recognition_vs_uptake=dict(
                   book_winners=len(books), book_winners_matched=sum(1 for r in books if r['matched_works']),
                   median_uptake_matched_books=sorted(r['phds_2009_2026'] for r in books if r['matched_works'])[len([r for r in books if r['matched_works']]) // 2] if any(r['matched_works'] for r in books) else None),
               winners_not_in_lists=[dict(r) for r in rows if r['phds_2009_2026'] >= 15 and not (r['in_scholar_packet'] or r['in_draft_rosters'] or r['in_atlas_people'])])
    (HERE / 'cha-prizes.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k != 'winners_not_in_lists'}, indent=1, ensure_ascii=False)[:5000])


if __name__ == '__main__':
    main()
