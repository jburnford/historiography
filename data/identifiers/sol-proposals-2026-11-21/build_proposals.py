"""Step 3: turn the audited Sol verdict classes into key-log PROPOSALS (nothing is applied) and review tables.

    python3 data/identifiers/sol-proposals-2026-11-21/build_proposals.py <lc-undiff.csv>

Reads: clean/*.latest.jsonl.gz (clean_verdicts.py), audit/agreement.json (write_audit.py), the LC MARC check of every
mint/attach authority (<lc-undiff.csv>: 008/32 'b' = undifferentiated, count of bracketed '[Author of ...]' notes),
the source proposals, build/graph/explorer.duckdb and build/keylog-state.sqlite (both read-only).
"""
import csv, gzip, json, re, sqlite3, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
C = HERE / 'clean'
ID = ROOT / 'data/identifiers'
SRC = ID / 'sol-review-2026-11-19'
report = {}


def load(name):
    return [json.loads(l) for l in gzip.open(C / f'{name}.latest.jsonl.gz', 'rt', encoding='utf-8')]


def write_json(path, obj, gz=False):
    if gz:
        with gzip.open(path, 'wt', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    else:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def write_csv(path, rows, fields=None):
    fields = fields or (list(rows[0]) if rows else ['empty'])
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z ]+', ' ', s)


lcx = {r['lc']: r for r in csv.DictReader(open(sys.argv[1], encoding='utf-8'))}


def lc_ok(lc):
    r = lcx.get(lc)
    return bool(r) and r['status'] == '200' and r['undiff_008_32'] != 'b' and r['author_of_670s'] == '0' and r['deleted_or_replaced'] not in ('d', 's', 'x')


db = duckdb.connect(str(ROOT / 'build/graph/explorer.duckdb'), read_only=True)
db.execute("SET memory_limit='1GB'; SET threads=2")
kl = sqlite3.connect(f"file:{ROOT / 'build/keylog-state.sqlite'}?mode=ro", uri=True)


def key_rec(k):
    r = kl.execute('select status, label, anchors, replaced_by from keys where key=?', (k,)).fetchone()
    return None if r is None else dict(status=r[0], label=r[1], anchors=json.loads(r[2] or '[]'), replaced_by=r[3])


def anchor_owner(a):
    r = kl.execute('select key from anchor where anchor=?', (a,)).fetchone()
    return r[0] if r else None


def death_year(ly):
    if isinstance(ly, dict):
        v = ly.get('death')
    else:
        m = re.findall(r'1\d{3}', str(ly or ''))
        v = m[1] if len(m) > 1 else None
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 1. filtered mint
mint_src = json.load(gzip.open(ID / 'place-demo-fixes-2026-11-18/mint-place-authors.proposal.json.gz', 'rt'))
mint = {d['case']: d for d in load('mint-combined')}
FLAGS = ('authority_hold', 'catalogue_authority_mismatch', 'identity_issue', 'authority_status', '_held_reason')
keep, held_rows = set(), []
why = Counter()
for case, d in mint.items():
    lc = d['lc_authority']
    if not (d['verdict'] == 'scholar' and d['mint_recommendation'] == 'yes'):
        why[f"not scholar/yes ({d['verdict']}/{d['mint_recommendation']})"] += 1
        continue
    reason = None
    if d['confidence'] not in ('high', 'medium'):
        reason = 'low confidence'
    elif any(d.get(f) for f in FLAGS):
        reason = 'Sol flagged the authority or identity'
    elif not lc_ok(lc):
        r = lcx.get(lc, {})
        reason = ('LC authority undifferentiated or bundles several people' if r.get('status') == '200'
                  else f"LC authority not readable ({r.get('status', 'not fetched')})")
    elif (death_year(d.get('life_years')) or 9999) < 1850:
        reason = 'died before 1850: scholar of their day but a primary-source author for the theses (audit: Thomas Cooper)'
    if reason:
        why[reason] += 1
        held_rows.append(dict(case=case, lc_authority=lc, name=d.get('name'), life_years=json.dumps(d.get('life_years'), ensure_ascii=False),
                              verdict=d['verdict'], mint=d['mint_recommendation'], confidence=d['confidence'],
                              field=d.get('field_or_discipline'), held_because=reason, sol_reason=d['reason'][:300]))
        continue
    keep.add(f'lcnaf:{lc}')
    why['minted'] += 1
ops, cur = [], None
for op in mint_src['ops']:
    if op['type'] == 'person':
        cur = next((a for a in op['anchors'] if a.startswith('lcnaf:')), None)
    if cur in keep:
        ops.append(op)
write_json(HERE / '01-mint-scholars.proposal.json.gz', dict(
    basis='Filtered from place-demo-fixes-2026-11-18/mint-place-authors.proposal.json.gz: only authorities Sol (outside review, 2026-11-19/21) '
          'classed scholar with mint_recommendation yes at high/medium confidence, whose LC authority is differentiated (no bracketed '
          'multi-person notes) and who died in or after 1850. The standing rule (LC authority + 2 or more citing theses) is unchanged. '
          'NOT APPLIED: for the user.', decided_by='rule', ops=ops), gz=True)
write_csv(HERE / '01b-mint-yes-held.csv', held_rows)
report['mint'] = dict(candidates=len(mint), outcome=dict(why), persons=sum(o['type'] == 'person' for o in ops),
                      claims=sum(o['type'] == 'claim' for o in ops), events=len(ops))

# ---------------------------------------------------------------- 2. attaches to existing keys
SAME = {'same', 'confirmed', 'same-for-queued-works', 'same-for-book'}
CAUTION = re.compile(r'unresolved|separate (lc )?authority|different|distinct|requires? review|check |needs?|possible|mislabel|not the', re.I)
claims_by_lc = defaultdict(list)
for op in mint_src['ops']:
    if op['type'] == 'claim':
        claims_by_lc[op['relation']['subject']].append(op)
j1 = {d['case']: d for d in load('1-place-authors')}
q1 = {r['case']: r for r in csv.DictReader(open(SRC / '1-place-authors/queue.csv', encoding='utf-8'))}
cands, review = [], []
for case, d in mint.items():
    ek = d.get('existing_key')
    if not ek:
        continue
    key, st = (ek, 'same') if isinstance(ek, str) else (ek.get('key'), ek.get('status'))
    proof = ek if isinstance(ek, str) else (ek.get('proof') or '')
    if st in SAME and d['verdict'] != 'unclear':
        cands.append(('mint', case, d, key, json.dumps(proof, ensure_ascii=False)))
    else:
        review.append(dict(source='mint', case=case, name=d.get('name'), key=key, sol_status=st, sol_verdict=f"{d['verdict']}/{d['mint_recommendation']}",
                           why='Sol: not plainly the same person (or verdict unclear)', proof=json.dumps(proof, ensure_ascii=False)[:400]))
for case, d in j1.items():
    if d.get('existing_key') and case not in mint:
        cands.append(('job1', case, d, d['existing_key'], json.dumps(d.get('existing_key_proof'), ensure_ascii=False)))

ops, rows = [], []
cnt = Counter()
for src, case, d, key, proof in cands:
    rec = key_rec(key)
    lc = d.get('lc_authority')
    if rec is None or rec['status'] not in ('active', 'provisional', 'unsupported'):
        review.append(dict(source=src, case=case, name=d.get('name'), key=key, sol_status='same', why=f"key not live in the key log ({rec and rec['status']})", proof=proof[:400]))
        cnt['key not live'] += 1
        continue
    if case == 'lcnaf:n86142712' or (src == 'job1' and 'separate calligrapher' in proof):
        review.append(dict(source=src, case=case, name=d.get('name'), key=key, sol_status='same', why='the key holds a wrong lcnaf (Sol); needs detach + attach by hand', proof=proof[:400]))
        cnt['wrong lcnaf on key'] += 1
        continue
    if CAUTION.search(proof):
        review.append(dict(source=src, case=case, name=d.get('name'), key=key, sol_status='same', why='Sol proof carries a caution about part of the credits or the authority', proof=proof[:400]))
        cnt['proof cautions: review'] += 1
        continue
    key_lcnaf = [a for a in rec['anchors'] if a.startswith('lcnaf:')]
    att_lc = None
    if lc and not key_lcnaf and lc_ok(lc) and not CAUTION.search(proof) and anchor_owner(f'lcnaf:{lc}') is None:
        att_lc = f'lcnaf:{lc}'
    # works: the claims the mint proposal made for this authority, or the job-1 queue works
    if lc and f'lcnaf:{lc}' in claims_by_lc:
        works = [(c['relation']['object'], c['basis']) for c in claims_by_lc[f'lcnaf:{lc}']]
    else:
        works = [(w['work'], f"LC main entry on '{w.get('title', '')[:120]}'") for w in json.loads(q1.get(case, {}).get('works') or '[]')]
    have = {r[0] for r in db.execute('select "to" from e_authored_f where "from"=? union select "to" from e_edited_f where "from"=?', [key, key]).fetchall()}
    new_ops = []
    for obj, basis in works:
        node = obj
        if obj.startswith('lccn:'):
            r = db.execute('select key from anchors where anchor=?', [obj]).fetchone()
            node = r[0] if r else obj
        if node in have or obj in have:
            cnt['work already credited'] += 1
            continue
        anchor = f"lc-authored:{(obj.split(':', 1)[1] if ':' in obj else obj).replace(' ', '')}:{att_lc[6:] if att_lc else key}"
        if anchor_owner(anchor):
            cnt['claim anchor exists'] += 1
            continue
        new_ops.append(dict(event='mint', key=f'new:a{len(ops)}x{len(new_ops)}', type='claim', label='', resolution='recorded',
                            anchors=[anchor], relation=dict(subject=key, predicate='authored', object=obj), decided_by='review',
                            basis=f"{basis}; author identified as {key} by outside review (Sol, {d.get('checked_at')}), audited 2026-11-21 (39/40)"[:600]))
    if att_lc:
        ops.append(dict(event='attach', key=key, anchors=[att_lc], aliases=[], members=[], decided_by='review',
                        basis=f"outside review (Sol {d.get('checked_at')}): LC authority {lc} is this person: {proof[:300]}"[:700]))
        cnt['lcnaf attached'] += 1
    ops.extend(new_ops)
    cnt['claims'] += len(new_ops)
    rows.append(dict(source=src, case=case, name=d.get('name'), key=key, key_label=rec['label'], lcnaf_attached=att_lc or '',
                     lcnaf_not_attached_because='' if att_lc else ('no authority' if not lc else 'key already holds ' + ','.join(key_lcnaf) if key_lcnaf
                                                                   else 'authority undifferentiated' if not lc_ok(lc) else 'Sol proof cautions' if CAUTION.search(proof)
                                                                   else 'authority already on another key'),
                     claims=len(new_ops), proof=proof[:400]))
write_json(HERE / '02-attach-existing-keys.proposal.json', dict(
    basis='Catalogued LC authors whom outside review (Sol, 2026-11-19/21) identified with an existing person key: the LC authority is '
          'attached only when it is differentiated, the key holds no LC authority and the proof carries no caution; authored claims '
          'for the catalogued works the key does not already hold. Audit 39/40. NOT APPLIED.', decided_by='review', ops=ops))
write_csv(HERE / '02-attach-existing-keys.csv', rows)
write_csv(HERE / '02b-existing-key-review.csv', review)
report['attach'] = dict(candidates=len(cands), keys=len(rows), review=len(review), counts=dict(cnt), events=len(ops))

# ---------------------------------------------------------------- 3. mixed profiles
mixed = load('3-mixed-profiles')
mrows, krows = [], []
for d in mixed:
    for w in d['works']:
        if w.get('class') != 'not-theirs':
            continue
        r = dict(person=d['person'], work=w['work'], source=w.get('credit_source'), printed_ids='', year=w.get('year'),
                 kind='', title=(w.get('title') or '')[:200], verdict=d['verdict'], credit_evidence=w.get('credit_evidence'),
                 reason=(w.get('why') or '')[:400])
        keylog = w.get('credit_evidence') not in ('linked',)
        if d['verdict'] == 'mixed' and not keylog:
            r['proposed'] = 'demote to author_candidates'
            mrows.append(r)
        else:
            r['proposed'] = ('withdraw the key-log claim (review)' if keylog else 'demote to author_candidates (class held: review)')
            r['claim'] = w.get('claim')
            krows.append(r)
F = ['person', 'work', 'source', 'printed_ids', 'year', 'kind', 'title', 'proposed', 'reason']
write_csv(HERE / '03-mixed-profile-credits.csv', mrows, F)
write_csv(HERE / '03b-mixed-profile-review.csv', krows, F + ['verdict', 'credit_evidence', 'claim'])
report['mixed'] = dict(demote_rows=len(mrows), demote_keys=len({r['person'] for r in mrows}), review_rows=len(krows),
                       review_keys=len({r['person'] for r in krows}), review_keylog_rows=sum(r['credit_evidence'] != 'linked' for r in krows),
                       evidence_values=dict(Counter(w.get('credit_evidence') for d in mixed for w in d['works'])))

# ---------------------------------------------------------------- 4. ORCID
orc = load('4-orcid')
old = json.loads((ID / 'crossref-identity-2026-11-17/02-orcid-split-key-merges.json').read_text())
merges = list(old['ops'])
done = {(o['key'], o['into']) for o in merges}
NEW = {'h-045': ('p-123840', 'p-25726'), 'h-057': ('p-181319', 'p-6865'), 'h-085': ('p-284704', 'p-94580'), 'h-120': ('p-263215', 'p-143732')}
for r in orc:
    if r['verdict'] != 'same-person-two-keys':
        continue
    if r['case'] in NEW:
        k, into = NEW[r['case']]
        merges.append(dict(event='merge', key=k, into=into, decided_by='review',
                           basis=f"outside review (Sol 2026-11-19, {r['case']}): one person: {r['deciding_fact'][:400]} Shared work {r.get('shared_work')}; audited 2026-11-21"[:900]))
write_json(HERE / '04a-orcid-merges.proposal.json', dict(
    basis='crossref-identity-2026-11-17/02 (4 merges, each confirmed by Sol c-004/c-020/c-023/c-090) plus 4 merges Sol established from a '
          'shared work and the ORCID record (h-045 Sood, h-057 Raven, h-085 Peschanski, h-120 Lo Basso). NOT APPLIED.', decided_by='review', ops=merges))
# exclusions: deposit-error and placeholder
labels = {}


def label(k):
    if k not in labels:
        r = key_rec(k)
        labels[k] = (r or {}).get('label', '')
    return labels[k]


ex = []
for r in orc:
    if r['verdict'] not in ('deposit-error', 'placeholder-iD'):
        continue
    names = r.get('names_on_records') or {}
    for k in r['keys']:
        held = set((key_rec(k) or {}).get('anchors', []))
        fam = set(fold(label(k)).split())
        for o in r['orcids']:
            if f'orcid:{o}' in held:
                continue
            if r['verdict'] == 'placeholder-iD' and o != '0000-0002-1825-0097':
                continue  # the other iD of a placeholder case is not judged
            nm = set(fold(names.get(o, '')).split())
            if r['verdict'] == 'deposit-error' and o != '0000-0002-1825-0097' and fam & nm:
                continue  # the iD's own record names this key's family: same-name iD, left to a person-level reading
            ex.append(dict(key=k, key_label=label(k), orcid=o, orcid_record_name=names.get(o, ''), case=r['case'], verdict=r['verdict'],
                           dois=' '.join(r.get('faulty_dois') or []), rule='never attach this iD to this key',
                           deciding_fact=r['deciding_fact'][:300]))
write_csv(HERE / '04d-orcid-exclusions.csv', ex)
wa = [r for r in orc if r['verdict'] == 'wrong-anchor-on-key']
write_csv(HERE / '04b-wrong-anchor-review.csv', [dict(case=r['case'], keys=' '.join(r['keys']), orcids=' '.join(r['orcids']),
                                                     names=json.dumps(r['names_on_records'], ensure_ascii=False), sol=r['deciding_fact'][:400])
                                                for r in wa])
att01 = json.loads((ID / 'crossref-identity-2026-11-17/01-orcid-attaches.json').read_text())['ops']
expairs = {(e['key'], e['orcid']) for e in ex}
contra = [o for o in att01 if (o['key'], o['anchors'][0][6:]) in expairs]
report['orcid'] = dict(merges=len(merges), exclusions=len(ex), exclusion_keys=len({e['key'] for e in ex}),
                       wrong_anchor_cases=len(wa), attaches_01=len(att01), attaches_01_contradicted=len(contra))

# ---------------------------------------------------------------- 5. seeds
seeds = load('5-seed-links')
ROLE = {'author': 'authored', 'reviewer': 'authored', 'co-reviewer': 'authored', 'volume-editor': 'edited', 'editor': 'edited',
        'co-editor': 'edited', 'coeditor': 'edited', 'edition-editor': 'edited', 'coordinator': 'edited'}
mint_ops, claim_ops, srows = [], [], []
rc = Counter()
for d in seeds:
    if d['verdict'] != 'yes':
        continue
    sid, th = d['seed'], d['thesis']
    roles = d.get('work_roles') or {}
    if isinstance(roles, list):
        roles = {k: v for x in roles if isinstance(x, dict) for k, v in x.items()}
    dois = [w if isinstance(w, str) else w.get('doi') for w in d.get('works_confirmed') or []]
    if sid.startswith('dnb-'):
        mint_ops.append(dict(event='mint', key=f'new:s{len(mint_ops)}', type='person', label=d['seed_name'], resolution='recorded',
                             anchors=[f'diss-author:{sid}'], aliases=[], members=[], decided_by='review',
                             basis=f"author of DNB thesis {sid} ({th.get('university')}, {th.get('year')}); seed keyed because outside review (Sol 2026-11-19) "
                                   f"linked published work(s) {' '.join(dois[:5])}: {d['reason'][:250]}"[:800]))
        mint_ops.append(dict(event='mint', key=f'new:s{len(mint_ops)}', type='claim', label='', resolution='recorded',
                             anchors=[f'diss-auth:{sid}'], relation=dict(subject=f'diss-author:{sid}', predicate='authored', object=f'diss-thesis:{sid}'),
                             decided_by='review', basis='DNB thesis record (thesis-round-2026-11-16 seed)'))
    n = 0
    for doi in dois:
        role = str(roles.get(doi, 'author')).lower()
        pred = ROLE.get(role)
        if pred is None:
            rc[f'skipped role {role}'] += 1
            continue
        claim_ops.append(dict(event='mint', key=f'new:w{len(claim_ops)}', type='claim', label='', resolution='recorded',
                              anchors=[f'crossref-{pred}:{doi.lower()}:{sid}'],
                              relation=dict(subject=f'diss-author:{sid}', predicate=pred, object=f'doi:{doi.lower()}'), decided_by='review',
                              basis=f"Crossref byline; tie to the thesis author by outside review (Sol 2026-11-19, {d['confidence']}): {d['reason'][:250]}"[:700]))
        n += 1
        rc[pred] += 1
    srows.append(dict(seed=sid, name=d['seed_name'], set='DNB' if sid.startswith('dnb-') else 'MX', confidence=d['confidence'], claims=n,
                      dois=' '.join(dois), roles=json.dumps(roles, ensure_ascii=False)))
write_json(HERE / '05a-seed-mints-dnb.proposal.json', dict(
    basis='DNB thesis-author seeds (thesis-round-2026-11-16) keyed now that outside review linked them to a published work (seed rule '
          'of 2026-11-14). Needs thesis-round 01-works-ingest applied first (the diss-thesis: anchors). NOT APPLIED.', decided_by='review', ops=mint_ops))
write_json(HERE / '05b-seed-work-claims.proposal.json', dict(
    basis='Authored/edited claims linking thesis authors (DNB seeds of 05a; Mexican authors of thesis-round 03-author-mints-mexico) to the '
          'Crossref works outside review confirmed (Sol 2026-11-19, audit 24/24 yes). Works are named by doi: (unkeyed works enter as '
          'two-layer nodes). NOT APPLIED.', decided_by='review', ops=claim_ops))
write_csv(HERE / '05-seed-links.csv', srows)
report['seeds'] = dict(yes=len(srows), dnb_mints=sum(o['type'] == 'person' for o in mint_ops), mx=sum(r['set'] == 'MX' for r in srows),
                       claims=len(claim_ops), by_role=dict(rc))
(HERE / 'build-report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
print(json.dumps(report, indent=1, ensure_ascii=False))
