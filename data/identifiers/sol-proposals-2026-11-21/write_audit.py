"""Step 2b: write the hand-audit tables (audit/audit-<job>.csv) and the agreement summary (audit/agreement.json).

Each sampled case was read by hand on 2026-11-21 against the public source (LC MARC authority from id.loc.gov,
Crossref API work records, ORCID public API records, a few publisher pages) and against build/graph/explorer.duckdb
(read-only). `agree`: y = my reading matches Sol's; n = it does not; u = I could not verify the deciding fact
(counted against the class, never as agreement). Cases not listed in EXCEPT were checked and agree; the per-job
CHECKED text says what was checked for every case of that job.
"""
import csv, json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE / 'audit'

CHECKED = {
    '1-place-authors': 'LC MARC authority (100/046/37x/670) read for every case with an authority; Sol role evidence read; class judged against the TASK definitions',
    'mint-combined': 'LC MARC authority read for every case; for hold cases the existing key, its anchors and key-log works read in explorer.duckdb',
    'attach': 'existing key read in explorer.duckdb (label, anchors, key-log works) and compared with the LC authority and Sol proof',
    '3-mixed-profiles': 'up to two not-theirs credits per key looked up in the Crossref API (authors, affiliations, editors); key-log not-theirs works resolved to their DOI and looked up',
    '4-orcid': 'both ORCID public records read (names, other names, employment); faulty DOIs looked up in Crossref (which iD sits on which row); for wrong-anchor cases the key label and key-log works read in explorer.duckdb',
    '5-seed-links': 'confirmed DOIs looked up in Crossref (byline, affiliation, ORCID, type); Sol thesis and tie evidence read',
}

# (case) -> (my reading, agree, note)
EXCEPT = {
    '1-place-authors': {
        'lcnaf:n79088527': ('scholar not established', 'u', 'Crow, Robert: LC confirms two energy-planning studies; no institution or research role found by Sol or me (Sol itself says role unverified)'),
        'lcnaf:n82090799': ('official-or-participant (defensible; also a geographer-scientist)', 'y', 'Davidson: commissioned boundary paper; class defensible'),
        'lcnaf:n2019005810': ('literary; queued LC authority is a different Mark Breslin', 'y', 'Sol correctly flags that the LC authority (construction consultant) is not the book author'),
    },
    'mint-combined': {
        'lcnaf:n79061939': ('official-or-participant / primary-source author -> no', 'n', 'Thomas Cooper 1759-1839: the 12 queued works are his own political economy lectures, trial account, slave-trade letters, reply to Burke: primary sources for theses, not scholarship; a professorship does not make them scholarship'),
        'lcnaf:n82214083': ('scholar (borderline journalist-or-popular)', 'y', 'Robert W. Peterson: newspaperman, but SABR research award and the standard Negro-leagues history; counted agree'),
        'lcnaf:n50037476': ('same', 'y', ''),
        'lcnaf:no2013106962': ('hold; proposed LC authority is an 1867 author, not John Gooch b.1945', 'y', 'mint list resolved the heading to the wrong authority'),
        'lcnaf:n83126123': ('hold; LC authority is the psychologist Helen Cowie', 'y', 'work belongs to p-100092 (ORCID); authority must not be attached'),
        'lcnaf:n83139628': ('hold; LC authority undifferentiated', 'y', 'work belongs to p-7170 (ORCID)'),
    },
    'attach': {
        'lcnaf:n84225378': ('not verifiable; LC authority undifferentiated', 'n', 'Fernandez, Alejandro: queued authority is undifferentiated ([Author of] notes); p-121459 holds a different lcnaf and has no works in the graph, so the claimed tie cannot be checked'),
        'lcnaf:n86807187': ('same for the Paris works; LC authority possibly pooled (Champollion biographer)', 'y', 'Faure: authority must not be attached'),
        'lcnaf:n2022068616': ('same person; queued LC authority is a UCSF ophthalmologist', 'y', 'Cook: attach the work only'),
        'lcnaf:n86815938': ('same person; queued LC authority is a biologist', 'y', 'Ward: attach works only; key holds n82029242'),
        'lcnaf:n78063140': ('same person; queued LC authority looks like a different Ann McGrath (climatology a.e. 1977)', 'y', 'attach works only; key holds n96083202'),
        'lcnaf:nb2011006773': ('same person; LC authority undifferentiated', 'y', 'Lawrence: works only'),
        'lcnaf:n79146317': ('same person; LC authority undifferentiated', 'y', 'Torok: works only; key holds n85264791'),
        'lcnaf:n81144633': ('anthology only belongs to p-222817; LC authority is Robert Henry Archer b.1950', 'y', 'Sol verdict unclear/hold; review list'),
        'lcnaf:nr90027407': ('same for the 2012 book; LC authority possibly a different Claude Couture (b. 1956-01-06)', 'y', 'works only'),
        'lcnaf:n86142712': ('same; key holds a wrong lcnaf (calligrapher n82009021)', 'y', 'Gaston-Martin: needs detach of n82009021 + attach of n86142712: review list'),
        'lcnaf:n00103478': ('same; LC authority undifferentiated', 'y', 'Clifford Wilson: works only'),
    },
    '3-mixed-profiles': {
        'p-11448': ('mixed plausible', 'u', 'Morrison: NTRS gives only "Morrison, H. D." with a Brown and Root-Northrup co-author (1971); the expansion Harry Doyle that Sol cites is not on the page I read'),
        'p-17236': ('mixed', 'y', 'Farr: Crossref 404 for the chapter DOIs, but the DOI prefix is the ISBN of The Surveyors\' Expert Witness Handbook, whose Routledge page names Martin Farr, chartered surveyor, FRICS'),
        'p-19316': ('two-people plausible', 'u', 'Schwartz: Hebrew Studies review DOI not in Crossref; CV PDF not read'),
        'p-11830': ('two-people plausible', 'u', 'Almodovar: Dialnet bibliography unreachable'),
    },
    '4-orcid': {
        'h-055': ('wrong LABEL, not wrong anchor', 'n', 'p-24939 holds Pinar Ceylan iD AND her works (WWF cotton/wheat sustainability reports, Ottoman price papers); detaching the iD strands her works; fix = relabel to Ceylan and remove the one Pamuk credit'),
        'h-145': ('wrong LABEL, not wrong anchor', 'n', 'p-18660 "Roberto Moll Neto" holds Steven Forti iD and ~250 of Forti\'s far-right/Spanish politics works; fix = relabel to Steven Forti and remove the Trump e Bolsonaro credit'),
        'h-147': ('wrong LABEL, not wrong anchor', 'n', 'same key p-18660 as h-145'),
        'b-206': ('wrong LABEL, not wrong anchor', 'n', 'p-26146 "Muhsine Perihan" holds Perihan Oyar iD and 17 dentistry papers; fix = relabel'),
        'b-053': ('anchors of p-13778/p-25642 reversed vs labels; which side the works follow not settled', 'n', 'p-13778 (Lacueva label, Saldana iD) carries 70 works; detaching would strand them; needs a per-work reading'),
        'b-009': ('ambiguous: joint works of Joram and Singh', 'u', 'all 4 works are co-authored by both; label vs anchor cannot be settled from the works'),
    },
    '5-seed-links': {
        'dnb-134676574X': ('yes (identity right)', 'y', 'Osorio-Barrios: thesis is molecular biology (TUM), not history: a scope question about the seed list, not a Sol error'),
    },
}


def reading(job, d):
    v = d['verdict'] + (f"/{d['mint_recommendation']}" if 'mint_recommendation' in d else '')
    if job == 'attach':
        ek = d['existing_key']
        v = f"same as {ek['key'] if isinstance(ek, dict) else ek}"
    return v


summary = {}
for job, fname in [('1-place-authors', 'sample-1-place-authors.json'), ('mint-combined', 'sample-mint-combined.json'),
                   ('attach', 'sample-attach.json'), ('3-mixed-profiles', 'sample-3-mixed-profiles.json'),
                   ('4-orcid', 'sample-4-orcid.json'), ('5-seed-links', 'sample-5-seed-links.json')]:
    S = json.loads((A / fname).read_text())
    rows, by = [], defaultdict(Counter)
    for d in S:
        sol = reading(job, d)
        mine, agree, note = EXCEPT.get(job, {}).get(d['case'], (sol, 'y', ''))
        stratum = d.get('_stratum') or d.get('_src')
        if job == '4-orcid' and d['verdict'] == 'same-person-two-keys':
            stratum = 'same-person-two-keys'
        elif job == '4-orcid' and d['verdict'] == 'same-person-two-iDs':
            stratum = 'same-person-two-iDs'
        rows.append(dict(case=d['case'], stratum=stratum, sol_verdict=sol, sol_confidence=d.get('confidence'), my_reading=mine,
                         agree=agree, note=note or CHECKED[job], checked_at='2026-11-21'))
        by[stratum][agree] += 1
    with open(A / f'audit-{job}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    tot = Counter(r['agree'] for r in rows)
    summary[job] = dict(checked=CHECKED[job], n=len(rows), agree=tot['y'], disagree=tot['n'], unverified=tot['u'],
                        by_class={k: dict(n=sum(c.values()), agree=c['y'], disagree=c['n'], unverified=c['u'],
                                          rate=round(c['y'] / sum(c.values()), 3), usable=c['y'] / sum(c.values()) >= 0.95)
                                  for k, c in by.items()})
(A / 'agreement.json').write_text(json.dumps(summary, indent=1))
for j, s in summary.items():
    print(j, s['n'], s['agree'], s['disagree'], s['unverified'])
    for k, c in s['by_class'].items():
        print('   ', k, c)
