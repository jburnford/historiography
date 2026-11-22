"""Job 6 (people on the Sri Lanka and Canada place pages): audited Sol verdicts -> proposals 06a-06f (2026-11-21/22).

Reads j6/clean6.jsonl and j6/works6.csv (clean6.py) and j6/audit6.csv (hand audit), the explorer snapshot read-only.
Nothing is applied and nothing writes the key log.

  06a-place-people-credits.csv          linked credits to demote to author_candidates (03 / Morgan form)
  06b-place-people-withdraw.proposal.json  key-log authored claims to withdraw (the same class, key-log side)
  06b-place-people-withdraw.csv          the claims, one row each, with Sol's reason
  06c-place-people-role-review.csv       credits that are the key's in another role (editor, compiler, translator,
                                        foreword or introduction, edition of primary texts): review, no events
  06d-two-people-one-key-review.csv      keys whose anchors or credits mix two people, with the evidence: review
  06e-relabel.proposal.json              label defects -> relabel events (current published name; LC/ORCID/university)
  ../../graph/places/tag-removals.csv    work-level place-tag removals (title-rule tags read as not about the place)
  06f-tag-removals-held.csv              the not-about-place readings of LC and review-of tags: held for review
"""
import csv, json, re, collections
from pathlib import Path
import duckdb

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = HERE.parents[3]
R = {r['case']: r for r in map(json.loads, open(HERE / 'clean6.jsonl', encoding='utf-8'))}
W = list(csv.DictReader(open(HERE / 'works6.csv', encoding='utf-8')))
PROV = 'Sol (Codex) review 2026-11-19/21, job 6-place-people; audited 2026-11-22'
ROLE = re.compile(r'edit|compil|translat|introduc|foreword|preface|selection|interview|collector|transcrib|arrang|direct', re.I)
# action classes (audit6.csv): the credit is not the key's in any role -> demote / withdraw; the key had another role ->
# role review. Two-people and unclear cases are never acted on here.
ACT = {'some-works-not-theirs', 'works-not-about-place', 'label-defect', 'sound'}


REVIEWER = re.compile(r"\breviewer\b|\breviewed\b|wrote (this|the)( \d+)? review|signed (the )?review|review essay|"
                      r"\breview (of|by)\b|\breviews\b|journal review", re.I)


EDITS_ITEM = re.compile(r"edited by|supplied the editorial|annotated|co-?editors? of (this|the) (bibliography|issue)|guest editor|"
                        r"translator of", re.I)


def cause(w, kind):
    t = w['why']
    if kind not in ('book', 'thesis') and REVIEWER.search(t):
        return "review by another person credited to the reviewed book's author or contributor"
    if kind in ('chapter', 'article', 'review') and ROLE.search(t) and not EDITS_ITEM.search(t):
        return "another author's text inside a volume the key edited or introduced (chapter, reprinted document, excerpt)"
    if ROLE.search(t):
        if re.search(r'translat', t, re.I):
            return 'role: translator'
        if re.search(r'foreword|introduc|preface', t, re.I) and not re.search(r'edit', t, re.I):
            return 'role: foreword or introduction'
        if re.search(r'primary|reproduc|republish|reprint|letters|lecture|documents|storyteller|interview', t, re.I):
            return 'role: edition of primary texts or reprint'
        return 'role: editor or compiler of the volume'
    if re.search(r'\breview', t, re.I):
        return "review by another person credited to the reviewed book's author or contributor"
    if re.search(r'chapter|contribut|series|section|list', t, re.I):
        return "part of another author's work (chapter, series text, front matter)"
    if re.search(r'thesis|supervisor|dissertation', t, re.I):
        return "another person's thesis"
    return 'another person of the same name or another author'


c = duckdb.connect(str(ROOT / 'build/graph/explorer.duckdb'), read_only=True)
c.execute("SET memory_limit='1GB'; SET threads=2")
label = lambda k: (c.execute('SELECT label FROM nodes WHERE key = ?', [k]).fetchone() or [None])[0]

# earlier tables: 03 (person = name there) and the Morgan file (person = key)
prior = set()
for f in (OUT / '03-mixed-profile-credits.csv', ROOT / 'data/identifiers/place-demo-fixes-2026-11-18/p-3125-morgan-profile-credits.csv'):
    for r in csv.DictReader(open(f, encoding='utf-8')):
        prior.add((r['person'], r['work']))
unsafe = set()
import gzip
with gzip.open(ROOT / 'data/graph/author-works/unsafe-profile-credits.csv.gz', 'rt', encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        unsafe.add((r['person'], r['work']))

WHOLE_VOLUME = {('p-72739', 'Cities and urbanizati'), ('p-72739', 'The Canadian city : e'), ('p-206510', 'The annotated bibliog'),
                ('p-47905', 'The Same but Differe'), ('p-91788', 'Les pays dans le pay')}
demote, withdraw, wrows, role, held_dupe = [], [], [], [], collections.Counter()
seen = set()
for w in W:
    if w['theirs'] != 'no' or w['verdict'] not in ACT:
        continue
    k = (w['key'], w['work'])
    if k in seen:
        continue
    seen.add(k)
    kind = (c.execute('SELECT kind FROM nodes WHERE key = ?', [w['work']]).fetchone() or [None])[0]
    why = cause(w, kind)
    # records that stand for the whole volume or issue the key edited (the snapshot types them article/chapter): role review
    if any(w['key'] == k and w['title'].startswith(t) for k, t in WHOLE_VOLUME):
        why = 'role: editor or compiler of the volume'
    base_kind = kind or ''
    base = dict(person=w['key'], work=w['work'], source=w['credit_source'], printed_ids='', year=w['year'], kind=base_kind,
                title=w['title'][:200])
    if why.startswith('role:'):
        role.append(dict(base, key_label=label(w['key']), cause=why, claim=w['claim'], proposed=
                         'review: keep the link with the role ' + why[6:] + ' (the explorer leaves edition-editor, translator and '
                         'introducer credits out of place-page counts)', reason=w['why'][:400], place=w['place']))
        continue
    if (w['key'], w['work']) in prior or (label(w['key']), w['work']) in prior or k in unsafe:
        held_dupe['already in 03, the Morgan file or unsafe-profile-credits'] += 1
        continue
    if w['credit_source'] == 'keylog':
        claims = [x for x in [w['claim']] if x]
        allc = c.execute('SELECT all_claims FROM e_authored_t WHERE "from" = ? AND "to" = ?', list(k)).fetchone()
        claims = sorted(set(claims) | set((allc[0] if allc and allc[0] else [])))
        for cl in claims:
            withdraw.append(dict(event='withdraw', key=cl))
        wrows.append(dict(base, key_label=label(w['key']), claims=' '.join(claims), cause=why, reason=w['why'][:400], place=w['place']))
    else:
        demote.append(dict(base, proposed='demote to author_candidates', reason=f"{why}: {w['why'][:380]}"))

F = ['person', 'work', 'source', 'printed_ids', 'year', 'kind', 'title', 'proposed', 'reason']


def wcsv(name, rows, fields=None):
    fields = fields or list(rows[0])
    with open(OUT / name, 'w', newline='', encoding='utf-8') as fh:
        x = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        x.writeheader()
        x.writerows(rows)


wcsv('06a-place-people-credits.csv', demote, F)
wcsv('06b-place-people-withdraw.csv', wrows)
json.dump(dict(basis='Key-log authored claims that outside review (Sol, job 6, 2026-11-19/21) read as not the key\'s work in any '
                     'role: reviews by other people credited to the reviewed author (journal deposits list the reviewer first and '
                     'the reviewed authors after), chapters and front matter of other authors\' books, other people\'s theses, '
                     'namesakes. Audit of the class 30/30 (j6/audit6.csv). Editor, translator, compiler and foreword credits are '
                     'NOT withdrawn (06c). NOT APPLIED.', decided_by='review', ops=withdraw),
          open(OUT / '06b-place-people-withdraw.proposal.json', 'w'), indent=1, ensure_ascii=False)
wcsv('06c-place-people-role-review.csv', role)

# ---- two people on one key: review list with the evidence -------------------------------------------------------
tp = []
for r in R.values():
    if r['verdict'] != 'two-people-one-key':
        continue
    ws = [w for w in W if w['case'] == r['case']]
    tp.append(dict(case=r['case'], key=r['key'], key_label=r['graph_label'], place=r['place'], rank=r['rank'],
                   anchors=' '.join(r['anchors']), sol_person=(r['person'] or {}).get('name'),
                   credits_judged=len(ws), credits_not_this_person=sum(w['theirs'] == 'no' for w in ws),
                   not_this_person_sources=' '.join(f"{k}:{v}" for k, v in collections.Counter(w['credit_source'] for w in ws if w['theirs'] == 'no').most_common()),
                   reason=r['reason'], evidence=' | '.join(f"{e.get('fact', '')[:200]} <{e.get('url')}>" for e in (r['evidence'] or [])[:6]),
                   works_not_this_person=' | '.join(f"{w['work']} {w['title'][:60]}" for w in ws if w['theirs'] == 'no')[:3000],
                   note=''))
NOTES = {
    'p-15977': 'the key holds only the ORCID of a scholar of Russian and Baltic Orthodoxy (ORCID record checked 2026-11-22: James White); every Canada credit is a name-only or ORCID-profile credit of three other James Whites (federal geographer 1909-24, UBC family scientist, GSC geologist). Demoting all 19 Canada credits would take the key off the Canada list.',
    'p-23277': "Sol's yes/no is relative to the Health Canada food scientist, not to the key's anchors: the ORCID on the key is Peter Scott of Reading (checked 2026-11-22). The food-survey credits are the ones that are not the anchored person's.",
    'p-26148': 'anchors (LC n2024045449, ORCID 0000-0003-3852-7329 = Richard Jones, Salford, checked) are the journalism scholar; the Canada reviews belong to Richard Jones of Laval.',
    'p-16673': 'anchors (LC n95082501, ORCID 0000-0002-5183-9469 = Jim Phillips, Glasgow, checked) are the Scottish economic historian; the Nova Scotia legal-history claims belong to Jim Phillips of Toronto (Osgoode).',
    'p-2582': 'ORCID 0000-0003-0674-6287 on the key is Mark Humphries of Swansea (checked); the Canada credits are Mark Osborne Humphries (Laurier). Wrong-anchor class, as in sol-proposals 04b.',
    'p-94241': 'ORCID 0000-0002-4895-1759 on the Marcocci key is Jorge Flores (checked); the four Ceylon works are Flores\'s.',
    'p-63677': 'ORCID 0000-0002-9724-9456 on the key is a Patrick Peebles in neonatology (record name checked); the Sri Lanka works are the LC-authorised scholar\'s.',
    'p-909': "the anchor diss-person:martel|heather e is Heather E. Martel's dissertation name on Marcel Martel's key.",
    'p-3125': 'already handled for the linked credits by place-demo-fixes-2026-11-18/p-3125-morgan-profile-credits.csv; the genetics credits are a McGill Kenneth Morgan.',
    'p-4045': 'ORCID 0000-0003-1754-2642 (Robert Young, checked) and LC n85198162 are Robert J. C. Young; the Canadian federalism credits are Robert Andrew Young (Western).',
}
for t in tp:
    t['note'] = NOTES.get(t['key'], '')
wcsv('06d-two-people-one-key-review.csv', sorted(tp, key=lambda t: (t['place'], t['rank'])))

# ---- label defects -> relabel ------------------------------------------------------------------------------------
RELABEL = {   # key: (label, basis) -- hand-checked against the LC authority (fetched 2026-11-22) and the cited pages
    'p-105919': ('Rhodri Windsor-Liscombe', "LC n79050134 100 'Liscombe, Rhodri Windsor, 1946-'; 400 'Windsor-Liscombe, Rhodri'; 670 UBC 2009 '(Rhodri Windsor-Liscombe)': the current published form (UBC profile)"),
    'p-127954': ('François-Marc Gagnon', "LC n79024885 670 title page '(François-Marc Gagnon)'; the key's label drops the hyphen of the published name"),
    'p-144420': ('El Chenier', "LC no2008115371 400 'Chenier, El'; 670 SFU AtoM 2024 'authorized form of name: Chenier, El': the current name (name-change rule: the earlier name stays a fact, not a label or alias)"),
    'p-249602': ('Micheline Dumont', "LC n80156078: 670 Les couventines 1986 t.p. '(Micheline Dumont)'; 400 'Dumont, Micheline, 1935-'; the key's label is the older catalogue form with the birth year"),
    'p-69797': ('Robert-Lionel Séguin', "LC n50005364 100 'Séguin, Robert-Lionel': the label lost the accent"),
    'p-99454': ('Vijaya Samaraweera', "the label repeats the inverted name with stray punctuation ('Samaraweera, Vijaya.; Samaraweera, Vijaya'); Oxford ORA thesis record and the 1972 Historical Journal byline print Vijaya Samaraweera"),
}
ops = [dict(event='relabel', key=k, label=l, basis=b) for k, (l, b) in RELABEL.items()]
json.dump(dict(basis='Label defects found by outside review (Sol, job 6, 2026-11-19/21), audit 8/8: lost accents and hyphens, a mangled '
                     'repeated label, an older catalogue form with a birth year, and a name change (the current name becomes the label; '
                     'the earlier name is not added as a label or alias). p-12418 Biedermann is in place-demo-fixes-2026-11-18/'
                     'relabel-biedermann.proposal.json; p-1661 Blake is a plain catalogue inversion (class issue, not relabelled one by '
                     'one). NOT APPLIED.', decided_by='review', ops=ops),
          open(OUT / '06e-relabel.proposal.json', 'w'), indent=1, ensure_ascii=False)

# ---- not about the place -> work-level tag removals --------------------------------------------------------------
rm, rm_held = [], []
for w in W:
    if w['about_place'] != 'no':
        continue
    pl = 'place:Q854' if w['place'] == 'Q854' else 'place:Q16'
    tags = c.execute('''SELECT a."to", a.source, a.heading FROM e_about_place_t a WHERE a."from" = ? AND (a."to" = ? OR a."to" IN
                        (SELECT des FROM place_desc WHERE anc = ?) OR a."to" IN (SELECT period FROM place_period WHERE territory = ?))''',
                     [w['work'], pl, pl, pl]).fetchall()
    for to, src, head in tags:
        row = dict(work=w['work'], qid=to.split(':', 1)[1], source=src, heading=(head or '')[:120], title=w['title'][:150],
                   reason=w['why'][:300], case=w['case'], provenance=PROV)
        (rm if src == 'title-rule' else rm_held).append(row)
uniq = {(r['work'], r['qid'], r['source']): r for r in rm}
with open(ROOT / 'data/graph/places/tag-removals.csv', 'w', newline='', encoding='utf-8') as fh:
    x = csv.DictWriter(fh, fieldnames=['work', 'qid', 'source', 'heading', 'title', 'reason', 'case', 'provenance'])
    x.writeheader()
    x.writerows(sorted(uniq.values(), key=lambda r: (r['qid'], r['work'])))
wcsv('06f-tag-removals-held.csv', rm_held)
rep = dict(demote=len(demote), demote_keys=len({r['person'] for r in demote}), withdraw_claims=len(withdraw),
           withdraw_credits=len(wrows), withdraw_keys=len({r['person'] for r in wrows}), role_review=len(role),
           role_by_cause=dict(collections.Counter(r['cause'] for r in role)), held_dupes=dict(held_dupe),
           demote_by_cause=dict(collections.Counter(r['reason'].split(':')[0] for r in demote)),
           withdraw_by_cause=dict(collections.Counter(r['cause'] for r in wrows)), two_people=len(tp), relabel=len(ops),
           tag_removals=len(uniq), tag_removals_held=len(rm_held),
           tag_removals_held_by_source=dict(collections.Counter(r['source'] for r in rm_held)))
json.dump(rep, open(HERE / 'build6-report.json', 'w'), indent=1)
print(json.dumps(rep, indent=1))
