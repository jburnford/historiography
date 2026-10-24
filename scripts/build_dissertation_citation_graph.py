#!/usr/bin/env python3
"""Build a citation graph from parsed History doctorate bibliographies.

Nodes: Dissertation, Work (a cited book, article, chapter or thesis, merged across
dissertations), Person (cited authors, dissertation authors and supervisors share
one name key: folded surname plus first initial) and Institution.
Edges: CITES (Dissertation->Work, with the bibliography section and its
primary/secondary side), AUTHORED (Person->Work), WROTE (Person->Dissertation),
SUPERVISED (Person->Dissertation), AWARDED_BY (Dissertation->Institution).

Each Dissertation carries ``eligibility``: ``history_phd`` (explicit History
doctorate; for the fifteen first-harvest universities this is the Sol review's
``doctoral_history_eligible``), ``needs_review`` (combined department, conflicting or
collection-only scope; reviewed decisions in ``eligibility-overrides.csv`` take precedence) or ``adjacent`` (another programme).

Name keys are not identities: two scholars sharing a surname and initial collapse.
Person keys use the surname and full first given name ('scott|joan'); initial-only
citations join that key only when a single full name shares surname and initial.
``atlas_person_candidate`` marks a Person whose key equals exactly one atlas roster
label's key; it is a candidate link for review, not a resolved identity.
Primary/secondary sides come from the dissertation's own subheadings, when present.

Scope (user decision, 2026-10-20; see ``dissertation_scope.py``): one **main graph** of
every History PhD found, from any country, and a **country sub-graph** for each country
with at least ``--subgraph-threshold`` (default 2000) strict History PhDs. Every
Dissertation carries ``country`` (ISO-2; manifest entries without one are the legacy
Canadian harvests, ``CA``). Eligibility is country-neutral: each record is judged on its
own basis (the Canadian eligibility review and overrides; the harvest's ``history_scope``
and ``eligibility_basis``, e.g. an AHA History PhD match for the US tier-2 records; a
BASE ``history_label`` hook for later). ``in_analysis`` marks the strict set, a parsed,
non-excluded bibliography of a ``history_phd``, regardless of country; ``subgraph`` names
the dissertation's country when that country has a sub-graph.

Counts on Work and Person nodes: ``cited_by`` (Works) and ``cited_by_dissertations``
(Persons) count strict History PhDs of the main graph; ``cited_by_country`` gives the same
count per country ({'CA': n, 'US': m}); ``cited_by_all`` counts every dissertation with a
counted bibliography, of any eligibility and country. Summaries are written for the main
graph to ``summary/`` and for each sub-graph to ``summary/countries/<CC>/``.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import csv
import difflib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from xml.sax.saxutils import escape

from dissertation_scope import SUBGRAPH_THRESHOLD, record_country, summary_dir
from dissertation_names import normalise_first_authors

# Entry fields the build uses; the rest (notably the raw citation text) is dropped at load to save memory.
ENTRY_FIELDS = ('dissertation', 'institution', 'n', 'page', 'first_page', 'section', 'author', 'authors', 'surnames', 'title',
                'container', 'year', 'kind', 'section_side', 'author_from_dash', 'from_notes', 'citations')
CITABLE = {'book', 'article', 'chapter', 'thesis', 'book_or_serial', 'unstyled'}
STOPWORDS = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'de'}


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', text.replace('’', "'").replace("'", ''))).strip()


VOLUME = re.compile(r'[,.]?\s*\b(?:vol(?:ume)?|tome|t|book|part|partie)\.?\s*(?:[ivxlc]+|\d+)\.?\s*$', re.I)


def title_key(title):
    main = re.split(r'\s*[:?!;—–]\s+|\s*\.\s+|\s+-\s+', title or '', maxsplit=1)[0]
    main = VOLUME.sub('', main)  # 'The History of Sexuality, Volume 1' = 'The History of Sexuality'
    words = fold(main).split()
    while words and words[0] in STOPWORDS:
        words = words[1:]
    return ' '.join(words)[:80]


HONORIFIC = re.compile(r'\b(?:Jr|Sr|II|III|IV|Dr|Prof|Professor|Rev|Reverend|Rt|Right|Hon|Honourable|Honorable|Sir|Dame|Lady|Lord|'
                       r'Mr|Mrs|Ms|Miss|Mme|Mlle|Colonel|Col|Lt|Lieut|Lieutenant|Major|Maj|General|Gen|Brigadier|Brig|Captain|Capt|'
                       r'Admiral|Adm|Commander|Cdr|Sergeant|Sgt|Corporal|Cpl|Private|Pte|Father|Fr|Abbé|Abbe|Mgr|Monseigneur|Sister|'
                       r'Soeur|Sœur|Brother|Frère|Bishop|Archbishop|Cardinal|Chief)\b\.?(?=\s|,|$)', re.I)


GLUED = re.compile(r'\b(?:[A-Z]{2}|[B-DF-HJ-NP-TV-Z]{3,4})\b(?![a-z])')  # glued initials such as 'JL', 'JJL'


def person_key(name, inverted):
    """'Surname, Given' (inverted) or 'Given Surname' -> 'surname|given' (full first given
    name) or 'surname|g' (initial only); corporate or single names fold whole."""
    name = re.sub(r'\s+', ' ', name or '').strip(' ,.')
    if inverted == 'auto':  # repository author/advisor fields: inverted when a comma is present
        inverted = ',' in name
    if inverted and ',' in name:
        # Honorifics and ranks are removed from the given names only: 'Cardinal, Harold'
        # keeps its surname. Hyphenated forenames stay whole ('Jean-François' != 'Jean-Marie').
        sur, given = name.split(',', 1)
        sur = re.sub(r',?\s*\b(?:Jr|Sr|II|III|IV)\b\.?$', '', sur).strip(' ,.')
        given = re.sub(r'\s+', ' ', HONORIFIC.sub('', given)).strip(' ,.')
        given = re.sub(r'(?<=[A-Za-zÀ-ÿ])-(?=[A-Za-zÀ-ÿ]{2})', '', given)
        given = GLUED.sub(lambda m: ' '.join(m.group(0)), given)  # 'JL' -> 'J L'
        if not sur:
            return None, None
    else:
        toks = GLUED.sub(lambda m: ' '.join(m.group(0)), name).split()
        if not toks:
            return None, None
        while len(toks) > 1 and HONORIFIC.fullmatch(toks[0]):
            toks = toks[1:]
        while len(toks) > 1 and re.fullmatch(r'(?:Jr|Sr|II|III|IV)\.?', toks[-1]):
            toks = toks[:-1]
        display = ' '.join(toks)  # keep hyphens for display; the key joins hyphenated forenames
        toks = [toks[0]] + [re.sub(r'(?<=[A-Za-zÀ-ÿ])-(?=[A-Za-zÀ-ÿ]{2})', '', t) for t in toks[1:-1]] + [toks[-1]] \
            if len(toks) > 2 else [re.sub(r'(?<=[A-Za-zÀ-ÿ])-(?=[A-Za-zÀ-ÿ]{2})', '', toks[0])] + toks[1:]
        name = ' '.join(toks)
        if not name:
            return None, None
        if len(toks) == 1 or not inverted and len(toks) > 4:
            return fold(name), name
        sur, given = (toks[-1], ' '.join(toks[:-1])) if not inverted else (name, '')
        name = display
    s, g = fold(sur), fold(given).split()
    if not s:
        return None, None
    if not g:
        return s, name
    if len(g[0]) == 1 and len(g) >= 2 and len(g[1]) > 1:
        g = g[1:]  # 'J. Elizabeth Elbourne' goes by Elizabeth
    if len(g[0]) == 1:
        return f'{s}|{g[0]}', name
    # Full first name, plus a printed middle *initial* ('russell|peter a'). Full middle
    # words are ignored: in bibliographies they are as often title words leaking into
    # the author field ('Anderson, Benedict Imagined') as middle names.
    middle = len(g) in (2, 3) and len(g[1]) == 1
    return f'{s}|{g[0]}' + (f' {g[1]}' if middle else ''), name


def name_detail(display):
    """2 = full first given name, 1 = initials only, 0 = no given name."""
    g = given_names(display) if ',' in display else []
    return 2 if g and len(g[0]) > 1 else 1 if g else 0


def initials(display):
    return ''.join(t[0] for t in given_names(display))


NICKNAMES = {'jim': 'james', 'jimmy': 'james', 'bill': 'william', 'will': 'william', 'bob': 'robert', 'rob': 'robert',
             'bert': 'robert', 'dick': 'richard', 'rick': 'richard', 'tom': 'thomas', 'mike': 'michael', 'dave': 'david',
             'ted': 'edward', 'ed': 'edward', 'ned': 'edward', 'tony': 'anthony', 'joe': 'joseph', 'dan': 'daniel',
             'don': 'donald', 'doug': 'douglas', 'greg': 'gregory', 'jeff': 'jeffrey', 'ken': 'kenneth', 'larry': 'lawrence',
             'len': 'leonard', 'nick': 'nicholas', 'pat': 'patrick', 'pete': 'peter', 'ron': 'ronald', 'sam': 'samuel',
             'steve': 'stephen', 'chris': 'christopher', 'andy': 'andrew', 'alex': 'alexander', 'charlie': 'charles',
             'chuck': 'charles', 'fred': 'frederick', 'gerry': 'gerald', 'jerry': 'gerald', 'hank': 'henry', 'harry': 'henry',
             'liz': 'elizabeth', 'beth': 'elizabeth', 'betty': 'elizabeth', 'kate': 'katherine', 'kathy': 'katherine',
             'peggy': 'margaret', 'meg': 'margaret', 'sue': 'susan', 'jenny': 'jennifer', 'cathy': 'catherine', 'reg': 'reginald'}


def dominant_initials(names, printed_only=False):
    """Most frequent multi-letter initials signature among a person's spellings
    (printed_only: ignore spellings attached only as evidence from a cited work)."""
    sigs = Counter()
    for n, c in names.items():
        if re.search(r'\.\s+[A-ZÀ-Ý][a-zà-ÿ]{2,}', n.split(',', 1)[-1]):
            continue  # title debris after the name ('Thompson, Elizabeth. Public')
        sig = initials(GLUED.sub(lambda m: ' '.join(m.group(0)), n))
        if len(sig) > 1 and (c > 0 or not printed_only):
            sigs[sig] += max(c, 1)
    return sigs.most_common(1)[0][0] if sigs else None


def resolve_initials(persons):
    """Less specific name keys join one more specific person with the same surname.
    1. 'russell|peter' joins the single 'russell|peter <middle>' key, if only one exists.
    2. Initial-only 'miller|j' joins the full-name person whose spellings most often
       carry the same initials ('J.R.' = 'James Rodger'); if several do, the one holding at
       least 80% of their spellings; else the single full-name person with that first
       initial. Ambiguous names stay separate."""
    def parts(k):
        sur, given = k.split('|', 1)
        return sur, given.split()
    alias = {}
    # 0. Nickname forms with the same surname and middle initial ('miller|jim r' = 'miller|james r').
    weight = {k: sum(max(v, 1) for v in p['names'].values()) for k, p in persons.items()}
    nick = defaultdict(list)
    for k in persons:
        if '|' in k:
            sur, g = parts(k)
            if len(g) == 2 and len(g[0]) > 1:
                nick[(sur, NICKNAMES.get(g[0], g[0]), g[1])].append(k)
    for keys in nick.values():
        if len(keys) > 1:
            head = max(keys, key=lambda k: (parts(k)[1][0] not in NICKNAMES, weight[k]))
            alias.update({k: head for k in keys if k != head})
    mids = defaultdict(list)
    for k in persons:
        if '|' in k and k not in alias:
            sur, g = parts(k)
            if len(g) == 2 and len(g[0]) > 1:
                mids[(sur, g[0])].append(k)
    for k in persons:
        if '|' in k:
            sur, g = parts(k)
            if len(g) == 1 and len(g[0]) > 1 and len(mids.get((sur, g[0]), [])) == 1:
                alias[k] = mids[(sur, g[0])][0]
    # Supervisors and dissertation authors appear in repository metadata with fuller names
    # ('McKay, Ian G') than in bibliographies ('McKay, Ian'): such non-cited keys join the
    # cited person with the same surname and first name who holds 80% of those citations.
    cited_w = {k: p['roles'].get('cited_author', 0) for k, p in persons.items()}
    by_first = defaultdict(list)
    for k in persons:
        if '|' in k and len(parts(k)[1][0]) > 1:
            by_first[(parts(k)[0], NICKNAMES.get(parts(k)[1][0], parts(k)[1][0]))].append(k)
    targets = set(alias.values())
    for k, p in persons.items():
        if '|' not in k or k in alias or k in targets or cited_w[k] or len(parts(k)[1][0]) < 2:
            continue
        cands = [c for c in by_first[(parts(k)[0], NICKNAMES.get(parts(k)[1][0], parts(k)[1][0]))] if c != k and cited_w[c]]
        mid = parts(k)[1][1] if len(parts(k)[1]) > 1 else None
        cands = [c for c in cands if not (mid and len(parts(c)[1]) > 1 and parts(c)[1][1] != mid)] or cands
        if cands:
            lead = max(cands, key=lambda c: cited_w[c])
            if cited_w[lead] >= 0.8 * sum(cited_w[c] for c in cands):
                alias[k] = alias.get(lead, lead)
    full = defaultdict(list)
    for k in persons:
        if '|' in k and k not in alias:
            sur, g = parts(k)
            if len(g[0]) > 1:
                full[sur].append(k)
    for k, p in persons.items():
        if '|' not in k:
            continue
        sur, g = parts(k)
        if len(g[0]) != 1:
            continue
        cands = [c for c in full.get(sur, []) if parts(c)[1][0][0] == g[0]]
        sig = dominant_initials(p['names'])
        strong = [c for c in cands if sig and dominant_initials(persons[c]['names'], printed_only=True) == sig]
        if os.environ.get('DEBUG_KEYS') and k in os.environ['DEBUG_KEYS'].split(','):
            print('DEBUG', k, sig, [(c, dominant_initials(persons[c]['names'], printed_only=True), dict(persons[c]['names'].most_common(4))) for c in cands][:6], file=sys.stderr)
        weight = {c: sum(max(v, 1) for v in persons[c]['names'].values()) for c in strong}
        lead = max(strong, key=weight.get) if strong else None
        if len({NICKNAMES.get(parts(c)[1][0], parts(c)[1][0]) for c in strong}) == 1 and len(strong) > 1:
            # 'Jim' and 'James R.' with the same printed initials J.R.: one person
            for c in strong:
                if c != lead:
                    alias[c] = lead
            strong = [lead]
        if len(strong) == 1:
            alias[k] = strong[0]
        elif strong and weight[lead] >= 0.8 * sum(weight.values()):  # one dominant bearer of these initials
            alias[k] = lead
        elif len(cands) == 1 and not strong:
            alias[k] = cands[0]
    return alias


def given_names(display):
    if ',' in display:
        return fold(display.split(',', 1)[1]).split()
    return fold(display).split()[:-1]


def atlas_index():
    """Atlas roster people keyed like Person nodes (surname plus full first given name)."""
    path = Path(__file__).resolve().parents[1] / 'historiography-1920-2000.json'
    index = defaultdict(list)
    for p in json.loads(path.read_text()).get('people', []):
        key, _ = person_key(p['label'], False)
        if key and '|' in key and len(key.split('|')[1]) > 1:
            index[key].append(p['id'])
    return {k: v[0] for k, v in index.items() if len(v) == 1}


def eligibility_index():
    path = Path(__file__).resolve().parents[1] / 'data/field-research/canadian-dissertations-2026-10-11/review/combined-index.jsonl'
    index = {}
    if path.exists():
        for line in path.open():
            r = json.loads(line)
            index[(r['institution'], r['id'])] = ('history_phd' if r['doctoral_history_eligible'] else
                'adjacent' if r['scope_status'] in ('other_or_adjacent_programme', 'non_thesis_material') or r['degree_review'] != 'doctoral'
                else 'needs_review', r['scope_status'])
    return index


def override_index(out):
    """Reviewed record-level decisions (eligibility-overrides.csv) take precedence."""
    path = out / 'eligibility-overrides.csv'
    if not path.exists():
        return {}
    with path.open(newline='') as f:
        return {(r['institution'], r['id']): r for r in csv.DictReader(f)}


def exclusion_index(out):
    """Reviewed decisions to keep a parsed thesis on record but out of the graph (graph-exclusions.csv)."""
    path = out / 'graph-exclusions.csv'
    if not path.exists():
        return {}
    with path.open(newline='') as f:
        return {(r['institution'], r['id']): r for r in csv.DictReader(f)}


# Hook for BASE records (data/field-research/base-history-theses-2026-10-19), not yet
# ingested: their classifier's ``history_label``. The 'history' label measured 74% precision
# on a hand check, so its mapping must be reviewed before BASE records enter the manifest.
BASE_LABEL_ELIGIBILITY = {'history': 'history_phd', 'possible': 'needs_review', 'other': 'adjacent'}


def eligibility(d, index, overrides=None):
    """Country-neutral: every record is judged on its own eligibility basis.
    1. Reviewed record-level overrides (eligibility-overrides.csv).
    2. The Canadian first-harvest eligibility review (combined-index.jsonl).
    3. A BASE ``history_label`` (hook; BASE is not yet ingested).
    4. The harvest's ``history_scope``, with its ``eligibility_basis`` when the harvest
       records one (US tier-2: 'AHA History PhD record matched')."""
    o = (overrides or {}).get((d['institution'], d['id']))
    if o:
        return o['eligibility'], 'reviewed_override: ' + o['note']
    if (d['institution'], d['id']) in index:
        return index[(d['institution'], d['id'])]
    if d.get('history_label') is not None:
        return BASE_LABEL_ELIGIBILITY.get(d['history_label'], 'needs_review'), f"base_history_label: {d['history_label']}"
    scope = d.get('history_scope') or ''
    status = scope or 'unchecked'
    if d.get('eligibility_basis'):
        status += f"; {d['eligibility_basis']}"
    return ('history_phd' if scope.startswith('explicit_history') else 'needs_review'), status


def dissertation_year(d):
    for field in ('graduation_dates', 'copyright_dates', 'issued_dates'):
        for v in d.get(field) or []:
            m = re.match(r'(\d{4})', v)
            if m:
                return int(m.group(1)), field
    return None, None


def merge_titles(works_by_surname, counts=None):
    """Merge near-identical title keys under the same first-author surname. Clusters form around
    the shortest key; with ``counts`` (citations per raw key) each cluster is then named after its
    most cited spelling, so a work id does not carry one bibliography's typo
    ('imagine communities'; 2026-10-23). Membership is the same either way."""
    alias = {}
    for sur, keys in works_by_surname.items():
        keys = sorted(keys, key=lambda k: (-len(k), k))
        reps = []
        for k in sorted(keys, key=len):
            target = None
            for r in reps:
                if k.endswith('|a') != r.endswith('|a'):
                    continue
                short, long_ = sorted((k, r), key=len)
                if (len(short.split()) >= 3 and long_.startswith(short)) or \
                        difflib.SequenceMatcher(None, k, r).ratio() > 0.92:
                    target = r
                    break
            if target:
                alias[(sur, k)] = (sur, target)
            else:
                reps.append(k)
    if counts:
        members = defaultdict(list)
        for k, r in alias.items():
            members[r].append(k)
        for r, ks in members.items():
            best = max(ks + [r], key=lambda k: (counts.get(k, 0), -len(k[1]), k[1]))
            for k in ks + [r]:
                if k == best:
                    alias.pop(k, None)
                else:
                    alias[k] = best
    return alias


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--subgraph-threshold', type=int, default=SUBGRAPH_THRESHOLD,
                        help='strict History PhDs a country needs for its own sub-graph (default %(default)s)')
    parser.add_argument('--provisional-subgraph', nargs='*', default=[], metavar='CC',
                        help='also give these countries a sub-graph when they fall below the threshold, labelled '
                             "'first pass, below threshold' in meta.provisional_subgraphs and in a NOTE.json in their "
                             'summary directory (the threshold itself is unchanged)')
    parser.add_argument('--notes', choices=['include', 'exclude'], default='include',
                        help='theses without a usable bibliography use the bibliography rebuilt from their notes '
                             '(extract_dissertation_notes.py: status parsed_notes; CITES edges carry via=notes)')
    args = parser.parse_args()
    out = args.out
    docs = {d['id']: d for d in json.load((out / 'doctorates.json').open())}
    extraction = {e['id']: e for e in map(json.loads, (out / 'extraction.jsonl').open())}
    entries = {}
    for line in (out / 'entries.jsonl').open():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:  # truncated line from an interrupted run
            continue
        if e['dissertation'] in extraction:  # re-extraction replaces earlier rows
            entries[(e['dissertation'], e['n'])] = {k: e[k] for k in ENTRY_FIELDS if k in e}  # 'raw' text is not needed
    # A re-extraction that yields fewer entries leaves the earlier run's higher-numbered rows
    # behind: keep only rows within the final extraction's entry count.
    entries = [e for e in entries.values() if e['n'] < (extraction[e['dissertation']].get('entries') or 0)]
    # Comma-less first authors ('GINZBURG Carlo', 'Robert Dallek') get a surname read from the
    # name and the thesis's own alphabetisation (dissertation_names.py, 2026-10-21).
    per_thesis = defaultdict(list)
    for e in entries:
        per_thesis[e['dissertation']].append(e)
    renamed = sum(normalise_first_authors(sorted(rows, key=lambda e: e['n'])) for rows in per_thesis.values())
    print(f'comma-less first authors normalised: {renamed}', flush=True)
    # Front bibliographies (find_span_anywhere, bib_placement 'front') are older OCR typescripts whose
    # entries split badly (judged audit 2026-10-22: first author 40%, title 57%), so they stay out of
    # the graph, as suspect spans do, until the parser is improved. 'back' placements are kept.
    for did, x in list(extraction.items()):
        if x['status'] == 'parsed' and x.get('bib_placement') == 'front':
            extraction[did] = dict(x, status='front_unverified')
    # Bibliographies rebuilt from notes (2026-10-21), only for theses whose own bibliography was
    # not parsed. Their entries replace any partial bibliography rows (few_entries, suspect_span).
    notes_used = set()
    if args.notes == 'include' and (out / 'notes-extraction.jsonl').exists():
        notes_x = {}
        for line in (out / 'notes-extraction.jsonl').open():
            r = json.loads(line)
            notes_x[r['id']] = r
        for did, r in notes_x.items():
            x = extraction.get(did)
            if x and x['status'] != 'parsed' and r['status'] == 'parsed_notes':
                extraction[did] = dict(x, status='parsed_notes', bibliography_status=x['status'], entries=r['works'])
                notes_used.add(did)
        entries = [e for e in entries if e['dissertation'] not in notes_used]
        for line in (out / 'notes-entries.jsonl').open():
            e = json.loads(line)
            if e['dissertation'] in notes_used:
                e = {k: e[k] for k in ENTRY_FIELDS if k in e}
                entries.append(dict(e, n=f"notes-{e['n']}", page=e.get('first_page', e.get('page'))))
        print(f'theses with a bibliography rebuilt from notes: {len(notes_used)}', flush=True)

    # Work identity: first-author surname + main title, then fuzzy merge within surname.
    raw_key = {}
    by_sur = defaultdict(set)
    for e in entries:
        if e['kind'] not in CITABLE or not e.get('surnames') or not e.get('title'):
            continue
        sur, tk = fold(e['surnames'][0]), title_key(e['title'])
        if not sur or len(tk) < 3:
            continue
        if e['kind'] in ('article', 'chapter'):
            tk += '|a'  # an article and a book with the same title are different works
        raw_key[(e['dissertation'], e['n'])] = (sur, tk)
        by_sur[sur].add(tk)
    alias = merge_titles(by_sur, Counter(raw_key.values()))
    # Translations and editions of one work, mapped through Wikidata (map_work_translations.py,
    # 2026-10-22): each cluster's works are merged into its most cited work id.
    translation_of = {}
    if (out / 'work-translations.jsonl').exists():
        for line in (out / 'work-translations.jsonl').open():
            r = json.loads(line)
            if r['work_id'] != r['canonical']:
                translation_of[r['work_id']] = r['canonical']
        # The mapping was made from an earlier build: a work id is one of its raw keys, but which raw
        # key represents a merged work can change between builds, so carry old ids to new ones.
        now = {'W:' + '|'.join(k): 'W:' + '|'.join(alias.get(k, k)) for ks in [set(raw_key.values())] for k in ks}
        translation_of = {now.get(a, a): now.get(b, b) for a, b in translation_of.items()}
        translation_of = {a: b for a, b in translation_of.items() if a != b}
        print(f'works merged as translations or editions: {len(translation_of)}', flush=True)

    nodes, edges = {}, []
    persons = defaultdict(lambda: dict(names=Counter(), roles=Counter()))
    works = defaultdict(lambda: dict(titles=Counter(), years=Counter(), kinds=Counter(), containers=Counter(), author_variants=Counter(),
                                     authors=[], citing=set(), sides=Counter(), institutions=set()))

    def add_person(name, inverted, role):
        key, display = person_key(name, inverted)
        if key:
            persons[key]['names'][display] += 1
            persons[key]['roles'][role] += 1
        return key

    elig_index = eligibility_index()
    overrides = override_index(out)
    exclusions = exclusion_index(out)
    for did, d in docs.items():
        if did not in extraction:
            continue
        year, year_field = dissertation_year(d)
        x = extraction[did]
        elig, scope_status = eligibility(d, elig_index, overrides)
        nodes[f'D:{did}'] = dict(id=f'D:{did}', type='Dissertation', title=d['title'], authors=d['authors'],
                                 institution=d['institution'], country=record_country(d), year=year, year_source=year_field,
                                 eligibility=elig, scope_status=scope_status,
                                 ancient_topic=bool(overrides.get((d['institution'], did), {}).get('ancient_topic')),
                                 advisors=d.get('advisors', []), history_scope=d.get('history_scope'),
                                 item_url=d['item_url'], extraction_status=x['status'],
                                 bibliography_entries=x.get('entries', 0),
                                 graph_excluded=exclusions.get((d['institution'], did), {}).get('reason'))
        # Only parsed, non-excluded bibliographies give CITES edges; in_analysis marks the strict set.
        n = nodes[f'D:{did}']
        n['cites_counted'] = x['status'] in ('parsed', 'parsed_notes') and not n['graph_excluded']
        n['in_analysis'] = n['cites_counted'] and elig == 'history_phd'  # strict set, any country
        nodes[f'I:{d["institution"]}'] = dict(id=f'I:{d["institution"]}', type='Institution', name=d['institution'])
        edges.append(dict(source=f'D:{did}', target=f'I:{d["institution"]}', type='AWARDED_BY'))
        for a in d['authors']:
            k = add_person(a, 'auto', 'dissertation_author')
            if k:
                edges.append(dict(source=f'P:{k}', target=f'D:{did}', type='WROTE'))
        for a in d.get('advisors', []):
            for part in re.split(r'\s*;\s*', a):
                part = re.sub(r'\s*\([^)]*\)', '', part).strip(' ,')  # '(Supervisor1)', '(History)'
                k = add_person(part, 'auto', 'supervisor')
                if k:
                    edges.append(dict(source=f'P:{k}', target=f'D:{did}', type='SUPERVISED'))

    cites = set()
    for e in entries:
        key = raw_key.get((e['dissertation'], e['n']))
        if not key or e['dissertation'] not in docs or not nodes.get(f'D:{e["dissertation"]}', {}).get('cites_counted'):
            continue
        key = alias.get(key, key)
        wid = 'W:' + '|'.join(key)
        wid = translation_of.get(wid, wid)
        w = works[wid]
        w['titles'][e['title']] += 1
        w['kinds'][e['kind']] += 1
        w['sides'][e['section_side']] += 1
        if e.get('year'):
            w['years'][e['year']] += 1
        if e.get('container'):
            w['containers'][e['container']] += 1
        w['author_variants'][tuple(e['authors'][:6])] += 1
        if (e['dissertation'], wid) in cites:
            continue
        cites.add((e['dissertation'], wid))
        w['citing'].add(e['dissertation'])
        w['institutions'].add(e['institution'])
        edges.append(dict(source=f'D:{e["dissertation"]}', target=wid, type='CITES', side=e['section_side'],
                          section=' > '.join(e['section']), page=e['page'], kind=e['kind'],
                          **({'via': 'notes', 'citations': e.get('citations')} if e.get('from_notes') else {})))

    # A work's authors come from its fullest citation: "Miller, James Rodger" in one
    # bibliography names the "Miller, J.R." of every other citation of that work.
    # Title evidence from catalogues (link_cited_works_to_authorities.py) can supply the
    # full name and identifiers of a work's first author.
    authorities = {}
    if (out / 'work-authorities.jsonl').exists():
        authorities = {r['work_id']: r for r in map(json.loads, (out / 'work-authorities.jsonl').open())}
    person_ids = defaultdict(lambda: dict(qids=Counter(), ids=set()))
    for wid, w in works.items():
        best = max(w['author_variants'].items(), key=lambda kv: (name_detail(kv[0][0]) if kv[0] else 0, kv[1]))[0]
        w['authors'] = [add_person(a, True if i == 0 else 'auto', 'cited_author') for i, a in enumerate(best)]
        auth = authorities.get(wid)
        if auth and w['authors'] and w['authors'][0] and '|' in w['authors'][0]:
            sur = w['authors'][0].split('|')[0]
            if auth.get('full_name') and name_detail(best[0]) < 2:
                key, _ = person_key(auth['full_name'], 'auto')
                if key and key.split('|')[0] == sur:
                    persons[key]['names'][auth['full_name']] += 0
                    persons[key]['roles']['cited_author'] += 1
                    w['authors'][0] = key
            if auth.get('identity'):
                pid = person_ids[w['authors'][0]]
                if auth['identity'].get('qid'):
                    pid['qids'][auth['identity']['qid']] += 1
                pid['ids'] |= set(auth['identity']['ids'])
        if w['authors'] and w['authors'][0]:
            first = persons[w['authors'][0]]['names']
            for variant in w['author_variants']:
                if variant and variant[0] not in first and fold(variant[0].split(',')[0]) == w['authors'][0].split('|')[0]:
                    first[variant[0]] += 0  # record the spelling as evidence without inflating counts
    strict = {k[2:] for k, n in nodes.items() if n['type'] == 'Dissertation' and n['in_analysis']}
    country_of = {k[2:]: n['country'] for k, n in nodes.items() if n['type'] == 'Dissertation'}
    strict_by_country = Counter(country_of[d] for d in strict)
    subgraphs = sorted(c for c, k in strict_by_country.items() if k >= args.subgraph_threshold)
    provisional = {}
    for c in (cc.strip().upper() for cc in args.provisional_subgraph):
        if c not in subgraphs and strict_by_country.get(c):
            provisional[c] = (f'first pass, below threshold: {strict_by_country[c]} strict History PhDs '
                              f'< {args.subgraph_threshold}')
    subgraphs = sorted(set(subgraphs) | set(provisional))
    for k, n in nodes.items():
        if n['type'] == 'Dissertation':
            n['subgraph'] = n['country'] if n['in_analysis'] and n['country'] in subgraphs else None

    def by_country(citing):
        return dict(sorted(Counter(country_of[x] for x in citing).items()))
    for wid, w in works.items():
        citing = w['citing'] & strict
        nodes[wid] = dict(id=wid, type='Work', title=w['titles'].most_common(1)[0][0],
                          year=w['years'].most_common(1)[0][0] if w['years'] else None,
                          kind=w['kinds'].most_common(1)[0][0], container=w['containers'].most_common(1)[0][0] if w['containers'] else None,
                          cited_by=len(citing), cited_by_all=len(w['citing']),
                          **({'cited_by_country': by_country(citing)} if citing else {}),
                          institutions=len({nodes[f'D:{x}']['institution'] for x in citing}),
                          cited_as=dict(w['sides']), title_variants=len(w['titles']))
        for k in dict.fromkeys(a for a in w['authors'] if a):
            edges.append(dict(source=f'P:{k}', target=wid, type='AUTHORED'))
    # Initial-only names join the single full-name person sharing surname and initial.
    alias = resolve_initials(persons)
    # Wikidata grounding of cited people (ground_cited_people_wikidata.py), by tier.
    tiers = {}
    if (out / 'person-wikidata.jsonl').exists():
        for line in (out / 'person-wikidata.jsonl').open():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:  # line still being written by a grounding run
                continue
            k = r['person'][2:]
            if r.get('qid') and k in persons and not person_ids.get(k, {}).get('qids'):
                person_ids[k]['qids'][r['qid']] += 1
                tiers[k] = r['tier']
    # Reviewed decisions (person-wikidata-decisions.csv) override automatic grounding.
    if (out / 'person-wikidata-decisions.csv').exists():
        with (out / 'person-wikidata-decisions.csv').open(newline='') as f:
            for r in csv.DictReader(f):
                k = r['person'][2:]
                if k in persons and r['decision'] == 'accept':
                    person_ids[k]['qids'] = Counter({r['qid']: 1})
                    tiers[k] = 'reviewed_' + r['basis']
                elif k in persons and r['decision'] == 'reject':
                    person_ids[k]['qids'].pop(r['qid'], None)
                    tiers.pop(k, None)
    by_qid = defaultdict(list)
    for k, pid in person_ids.items():
        if len(pid['qids']) == 1 and k in persons:
            by_qid[next(iter(pid['qids']))].append(k)
    for qid, keys in by_qid.items():
        keys = [alias.get(k, k) for k in keys]
        head = max(set(keys), key=lambda k: (len(k.split('|')[-1]), sum(persons[k]['roles'].values())))
        for k in set(keys) - {head}:
            alias[k] = head
    for k in list(alias):  # follow chains, stopping at any cycle
        seen = {k}
        while alias[k] in alias and alias[alias[k]] not in seen:
            seen.add(alias[k])
            alias[k] = alias[alias[k]]
    for k in list(alias):
        if alias.get(alias.get(k)) == k:  # two-way cycle: the more specific key stays a person
            alias.pop(max((k, alias[k]), key=len), None)
    for k, target in alias.items():
        if k in person_ids:
            person_ids[target]['qids'].update(person_ids[k]['qids'])
            person_ids[target]['ids'] |= person_ids[k]['ids']
        if k in tiers and target not in tiers:
            tiers[target] = tiers[k]
    for short, full in alias.items():
        if short not in persons:
            continue
        persons[full]['names'].update(persons[short]['names'])
        persons[full]['roles'].update(persons[short]['roles'])
        del persons[short]
    seen_edges, merged = set(), []
    for e in edges:
        if e['source'].startswith('P:') and e['source'][2:] in alias:
            e['source'] = 'P:' + alias[e['source'][2:]]
        sig = (e['source'], e['target'], e['type'])
        if e['type'] != 'CITES' and sig in seen_edges:
            continue
        seen_edges.add(sig)
        merged.append(e)
    edges[:] = merged
    for w in works.values():
        w['authors'] = [alias.get(a, a) for a in w['authors']]
    # Reviewed splits of merged namesakes (person-splits.csv, 2026-10-23): named works move from a
    # person whose name key gathers several people (Richard White of Stanford, Toronto and Sydney)
    # to a separate person. Applied after every merge above, so a split is never merged back.
    # Draft rows from namesake_review_queue.py (person-splits-drafts.csv) apply once marked 'accept'.
    rules = defaultdict(list)
    for name, accepted_only in (('person-splits.csv', False), ('person-splits-drafts.csv', True)):
        if not (out / name).exists():
            continue
        with (out / name).open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if not accepted_only or r.get('decision', '').strip().lower() == 'accept':
                    rules[r['person']].append((title_key(r['work_title']), r))
    if rules:
        moves = {}
        for wid, w in works.items():
            k = w['authors'][0] if w['authors'] else None
            base = next((p for p in rules if k and (k == p or k.startswith(p + ' '))), None)
            if not base:
                continue
            tk = wid.split('|', 1)[1].removesuffix('|a') if '|' in wid else ''
            hit = next((r for key, r in rules[base] if key and (tk == key or tk.startswith(key))), None)
            if not hit:
                continue
            new = hit['new_person']
            moves[(f'P:{k}', wid)] = f'P:{new}'
            w['authors'][0] = new
            persons[new]['names'][hit['new_name']] += 1
            persons[new]['roles']['cited_author'] += 1
            if hit.get('qid'):
                person_ids[new]['qids'] = Counter({hit['qid']: 1})
                tiers[new] = 'reviewed_split'
        for e in edges:
            if e['type'] == 'AUTHORED' and (e['source'], e['target']) in moves:
                e['source'] = moves[(e['source'], e['target'])]
        print(f'person splits: {len(moves)} works moved to {len(set(moves.values()))} separate people', flush=True)
    cited_by_person = defaultdict(set)
    for e in edges:
        if e['type'] == 'AUTHORED':
            cited_by_person[e['source']] |= works[e['target']]['citing']
    atlas = atlas_index()
    for k, p in persons.items():
        name = p['names'].most_common(1)[0][0]
        match = atlas.get(k)
        nodes[f'P:{k}'] = dict(id=f'P:{k}', type='Person', key=k, name=name,
                               roles=dict(p['roles']), cited_by_dissertations=len(cited_by_person[f'P:{k}'] & strict),
                               cited_by_all=len(cited_by_person[f'P:{k}']),
                               **({'cited_by_country': by_country(cited_by_person[f'P:{k}'] & strict)}
                                  if cited_by_person[f'P:{k}'] & strict else {}),
                               name_variants=len(p['names']), name_key_kind='full_first_name' if '|' in k and len(k.split('|')[1]) > 1 else
                               'initial_only' if '|' in k else 'corporate_or_single_name',
                               **({'atlas_person_candidate': match} if match else {}),
                               **({'qid': person_ids[k]['qids'].most_common(1)[0][0], 'qid_conflict': len(person_ids[k]['qids']) > 1,
                                   'qid_basis': tiers.get(k, 'catalogue_title_match')}
                                  if person_ids.get(k, {}).get('qids') else {}),
                               **({'identifiers': sorted(person_ids[k]['ids'])} if person_ids.get(k, {}).get('ids') else {}))

    (out / 'person-names.json').write_text(json.dumps(
        {f'P:{k}': [n for n, _ in p['names'].most_common(12)] for k, p in persons.items()}, ensure_ascii=False) + '\n')
    graph = dict(meta=dict(description=__doc__.strip().split('\n')[0],
                           dissertations=sum(1 for n in nodes.values() if n['type'] == 'Dissertation'),
                           eligibility=dict(Counter(n['eligibility'] for n in nodes.values() if n['type'] == 'Dissertation')),
                           with_bibliography=sum(1 for n in nodes.values() if n['type'] == 'Dissertation' and n['extraction_status'] == 'parsed'),
                           with_notes_bibliography=sum(1 for n in nodes.values() if n['type'] == 'Dissertation' and n['extraction_status'] == 'parsed_notes'),
                           in_analysis_from_notes=sum(1 for n in nodes.values() if n['type'] == 'Dissertation' and n['in_analysis']
                                                      and n['extraction_status'] == 'parsed_notes'),
                           by_country=dict(sorted(Counter(n['country'] for n in nodes.values() if n['type'] == 'Dissertation').items())),
                           in_analysis=len(strict), in_analysis_by_country=dict(sorted(strict_by_country.items())),
                           subgraph_threshold=args.subgraph_threshold, subgraphs=subgraphs,
                           **({'provisional_subgraphs': provisional} if provisional else {}),
                           works=len(works), persons=len(persons), cites_edges=len(cites),
                           caveats=['Heuristic bibliography parsing; see audit for measured precision.',
                                    'Person nodes are name keys (surname, first name, middle initial) merged by catalogue title evidence and tiered Wikidata grounding; they are not authority-reviewed identities.',
                                    'Bibliographies list works consulted, not every footnote citation, and not influence.',
                                    'Theses without a usable bibliography (extraction_status parsed_notes) cite the works rebuilt from their '
                                    'notes: cited works only, not works consulted; their CITES edges carry via=notes.']),
                 nodes=list(nodes.values()), edges=edges)
    with (out / 'graph.json').open('w') as f:  # streamed: one 1+ GB string would double the peak memory
        json.dump(graph, f, ensure_ascii=False)
        f.write('\n')
    write_graphml(out / 'graph.graphml', graph)

    # Per-country strict counts: one column per sub-graph country, the rest pooled in cited_by_other.
    def country_cols(n):
        c = n.get('cited_by_country', {})
        return [c.get(cc, 0) for cc in subgraphs] + [sum(v for cc, v in c.items() if cc not in subgraphs)]
    country_heads = [f'cited_by_{cc}' for cc in subgraphs] + ['cited_by_other']
    with (out / 'works.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['work_id', 'cited_by_dissertations', 'cited_by_all', 'institutions', 'authors', 'title', 'year', 'kind', 'container', 'cited_as'] + country_heads)
        for n in sorted((n for n in nodes.values() if n['type'] == 'Work'), key=lambda n: (-n['cited_by'], -n['cited_by_all'])):
            authors = '; '.join(nodes[f'P:{a}']['name'] for a in dict.fromkeys(works[n['id']]['authors']) if a)
            wr.writerow([n['id'], n['cited_by'], n['cited_by_all'], n['institutions'], authors, n['title'], n['year'], n['kind'], n['container'], json.dumps(n['cited_as'])] + country_cols(n))
    with (out / 'cited-people.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['person_key', 'name', 'cited_by_dissertations', 'cited_by_all', 'roles', 'qid', 'qid_basis', 'atlas_person_candidate'] + country_heads)
        for n in sorted((n for n in nodes.values() if n['type'] == 'Person'), key=lambda n: (-n['cited_by_dissertations'], -n['cited_by_all'])):
            wr.writerow([n['key'], n['name'], n['cited_by_dissertations'], n['cited_by_all'], json.dumps(n['roles']), n.get('qid', ''), n.get('qid_basis', ''), n.get('atlas_person_candidate', '')] + country_cols(n))
    with (out / 'dissertations.csv').open('w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['id', 'institution', 'eligibility', 'scope_status', 'year', 'year_source', 'author', 'title', 'extraction_status', 'bibliography_entries', 'cited_works_in_graph', 'graph_excluded', 'in_analysis', 'country', 'subgraph'])
        out_deg = Counter(e['source'] for e in edges if e['type'] == 'CITES')
        for n in sorted((n for n in nodes.values() if n['type'] == 'Dissertation'), key=lambda n: (n['institution'], n['year'] or 0)):
            wr.writerow([n['id'][2:], n['institution'], n['eligibility'], n['scope_status'], n['year'], n['year_source'], '; '.join(n['authors']), n['title'],
                         n['extraction_status'], n['bibliography_entries'], out_deg[n['id']], n['graph_excluded'] or '', n['in_analysis'], n['country'], n['subgraph'] or ''])
    write_summary(out, docs, extraction, entries, nodes, edges, works, cited_by_person, subgraphs)
    for c in subgraphs:  # a provisional sub-graph's outputs carry its label; a qualifying one drops a stale label
        note = summary_dir(out, c) / 'NOTE.json'
        if c in provisional:
            note.write_text(json.dumps(dict(country=c, status=provisional[c], built=datetime.now().strftime('%Y-%m-%d')),
                                       indent=1) + '\n')
        elif note.exists():
            note.unlink()
    print(json.dumps(graph['meta'], indent=1))


def write_summary(out, docs, extraction, entries, nodes, edges, works, cited_by_person, subgraphs, top=500):
    """Small, tracked tables, for the main graph (summary/) and each country sub-graph
    (summary/countries/<CC>/): coverage by university and the most-cited works and people."""
    downloads = {}
    for log in sorted(out.glob('downloads*.jsonl')):
        for line in log.open():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:  # a line still being written by a running download
                continue
            if d.get('status') == 'downloaded' or d.get('id') not in downloads:
                downloads[d.get('id')] = d.get('status')
    citable = Counter(e['dissertation'] for e in entries if e['kind'] in CITABLE)
    rows = defaultdict(Counter)
    country = {}
    for did, d in docs.items():
        r = rows[d['institution']]
        r['doctorates_harvested'] += 1
        # US records carry their access category; closed ones were never requested.
        closed = d.get('access_category') in ('restricted', 'embargoed', 'no_public_pdf')
        st = downloads.get(did, d['access_category'] if closed else 'not_attempted')
        r['pdf_downloaded' if st == 'downloaded' else 'pdf_restricted_or_missing' if st in
          ('restricted', 'no_public_pdf_bitstream', 'http_404', 'embargoed', 'no_public_pdf') else 'pdf_pending_or_error'] += 1
        x = extraction.get(did)
        if x:
            r['bibliography_parsed' if x['status'] == 'parsed' else 'bibliography_from_notes' if x['status'] == 'parsed_notes'
              else 'bibliography_not_parsed'] += 1
            if x.get('ocr'):
                r['ocr'] += 1
        n = nodes.get(f'D:{did}')
        if n and n['in_analysis']:
            r['history_phd_in_graph'] += 1
        country[d['institution']] = record_country(d)
        r['citable_entries'] += citable.get(did, 0)
    cols = ['doctorates_harvested', 'pdf_downloaded', 'pdf_restricted_or_missing', 'pdf_pending_or_error',
            'bibliography_parsed', 'bibliography_from_notes', 'bibliography_not_parsed', 'ocr', 'history_phd_in_graph', 'citable_entries']
    authors_of = defaultdict(list)
    for e in edges:
        if e['type'] == 'AUTHORED':
            authors_of[e['target']].append(nodes[e['source']]['name'])
    diss = {k[2:]: n for k, n in nodes.items() if n['type'] == 'Dissertation'}
    all_works = [n for n in nodes.values() if n['type'] == 'Work']
    all_people = [n for n in nodes.values() if n['type'] == 'Person' and n['name_key_kind'] != 'corporate_or_single_name']

    for scope in [None] + list(subgraphs):
        summary = summary_dir(out, scope)
        summary.mkdir(parents=True, exist_ok=True)
        with (summary / 'coverage-by-university.csv').open('w', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['institution'] + cols + ['country'])
            countries = [scope] if scope else sorted(set(country.values()), key=lambda c: (c not in subgraphs, c))
            for c in countries:
                insts = sorted(i for i in rows if country[i] == c)
                for inst in insts:
                    wr.writerow([inst] + [rows[inst][k] for k in cols] + [c])
                wr.writerow(['TOTAL' if scope else f'TOTAL_{c}'] + [sum(rows[i][k] for i in insts) for k in cols] + [c])
            if not scope:
                wr.writerow(['TOTAL'] + [sum(rows[i][k] for i in rows) for k in cols] + ['all'])
        # Counts within the scope: strict History PhDs, all counted dissertations, universities.
        strict = {d for d, n in diss.items() if n['in_analysis'] and (scope is None or n['country'] == scope)}
        counted = {d for d, n in diss.items() if n['cites_counted'] and (scope is None or n['country'] == scope)}
        if scope is None:
            wcount = {n['id']: (n['cited_by'], n['cited_by_all'], n['institutions']) for n in all_works}
            pcount = {n['id']: (n['cited_by_dissertations'], n['cited_by_all']) for n in all_people}
        else:
            wcount = {}
            for n in all_works:
                citing = works[n['id']]['citing']
                s = citing & strict
                wcount[n['id']] = (len(s), len(citing & counted), len({diss[x]['institution'] for x in s}))
            pcount = {n['id']: (len(cited_by_person[n['id']] & strict), len(cited_by_person[n['id']] & counted)) for n in all_people}
        # The main tables add the per-country split: one column per sub-graph, the rest pooled.
        extra_heads = [f'cited_by_{cc}' for cc in subgraphs] + ['cited_by_other'] if scope is None else []

        def extra(n):
            if scope is not None:
                return []
            c = n.get('cited_by_country', {})
            return [c.get(cc, 0) for cc in subgraphs] + [sum(v for cc, v in c.items() if cc not in subgraphs)]
        ranked = sorted(all_works, key=lambda n: (-wcount[n['id']][0], -wcount[n['id']][1]))[:top]
        with (summary / f'top-{top}-works.csv').open('w', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['rank', 'cited_by_history_phds', 'cited_by_all', 'universities', 'authors', 'title', 'year', 'kind'] + extra_heads)
            for i, n in enumerate(ranked, 1):
                k, a, u = wcount[n['id']]
                wr.writerow([i, k, a, u, '; '.join(authors_of[n['id']]), n['title'], n['year'], n['kind']] + extra(n))
        ranked = sorted(all_people, key=lambda n: (-pcount[n['id']][0], -pcount[n['id']][1]))[:top]
        with (summary / f'top-{top}-people.csv').open('w', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['rank', 'cited_by_history_phds', 'cited_by_all', 'name', 'person_key', 'qid', 'qid_basis', 'roles'] + extra_heads)
            for i, n in enumerate(ranked, 1):
                k, a = pcount[n['id']]
                wr.writerow([i, k, a, n['name'], n['key'], n.get('qid', ''), n.get('qid_basis', ''), json.dumps(n['roles'])] + extra(n))


def write_graphml(path, graph):
    keys = ['type', 'label', 'institution', 'year', 'kind', 'cited_by', 'cited_by_dissertations']
    with path.open('w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        for k in keys:
            f.write(f'<key id="{k}" for="node" attr.name="{k}" attr.type="string"/>\n')
        f.write('<key id="etype" for="edge" attr.name="type" attr.type="string"/>\n'
                '<key id="side" for="edge" attr.name="side" attr.type="string"/>\n<graph edgedefault="directed">\n')
        for n in graph['nodes']:
            label = n.get('title') or n.get('name') or n['id']
            vals = dict(n, label=label)
            data = ''.join(f'<data key="{k}">{escape(str(vals[k]))}</data>' for k in keys if vals.get(k) is not None)
            f.write(f'<node id="{escape(n["id"])}">{data}</node>\n')
        for i, e in enumerate(graph['edges']):
            side = f'<data key="side">{e["side"]}</data>' if 'side' in e else ''
            f.write(f'<edge id="e{i}" source="{escape(e["source"])}" target="{escape(e["target"])}"><data key="etype">{e["type"]}</data>{side}</edge>\n')
        f.write('</graph>\n</graphml>\n')


if __name__ == '__main__':
    main()
