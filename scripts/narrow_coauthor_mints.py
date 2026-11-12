"""Co-author mints, narrowed (2026-11-11; §8 class 6): a PROPOSAL from data/identifiers/work-people-2026-11-11/coauthor-mints.

Owner (2026-11-11): co-authors of a historian's work get a person node even outside history, but not a node for every
author of a merely cited work, and their other works are not pulled in. The 11-11 mint proposal (link_work_people.py
mints) is narrowed here to the people who rest on more than one printed name:
- **printed ORCID**: the ORCID is printed in the source record of at least one of the person's mentions (OpenAlex
  `raw_orcid`, i.e. deposited by the publisher). An ORCID that OpenAlex attached from its own author profile
  (`author.orcid` with no `raw_orcid`) is not printed: such a person counts only as a name group below, and the
  inferred ORCID becomes a member `orcid-inferred:` instead of an anchor;
- **grouped**: mentions on two or more works joined by strict full-name agreement and a shared fact (the same
  OpenAlex author id, the same historian co-author, the same printed institution ROR; link_work_people.mints).
Dropped: single-work or name-only people; organisation names (link_work_people.ORG and a wider list of corporate
words); every mention on a work whose key-log author matches no printed name (rechecked against the current graph);
known source errors (KNOWN_ERRORS: the OpenAlex record of w-549919 names Iva Lučić where the author is Iva Peša,
p-6823); and the general class behind it, an OpenAlex author attribution that disagrees with the printed record:
- the ORCID OpenAlex gives (`author.orcid`) differs from the printed one (`raw_orcid`);
- the printed name at the position (`raw_author_name`) disagrees with OpenAlex's display name for the author (family
  name differs): the OpenAlex profile carries another person;
- the same OpenAlex author id or ORCID appears, elsewhere among the graph's author positions, at a position the key
  log credits to an existing person key or under a printed family name that disagrees with the mint's name;
- the mention's ORCID only inferred (no `raw_orcid`) while the person's other mentions print it: kept only when
  its printed name agrees in full; otherwise dropped.
Roles (2026-11-12): a mention is not a co-author, and is dropped, when its position is a foreword writer or series
editor (link_work_people contributors: role contributor), when the historian is credited on the work (key log or by
identifier) only under another role than author (`role` of AUTHORED: volume-editor, edition-editor, translator,
introducer, series-editor, contributor), or when its printed name agrees with a person in CONTRIBUTED or EDITED on the
work, an AUTHORED credit with a non-author role, or a printed editor of the work in data/graph/volume-editors.csv.gz
(series-editor state included).
Twin check (after the duplicate merges of person-dup-merges-2026-11-11 and the cited-author promotion
cited-work-authors-promote-2026-11-11, assumed applied): a person whose ORCID is already on a key, or whose name agrees
in full (family name, first given name written out and identical) with a live person key or an LC heading the
promotion would mint, is held as a possible twin.

    python3 scripts/narrow_coauthor_mints.py scan      # raw ORCIDs of the mentions' OpenAlex records (E:, read only)
    python3 scripts/narrow_coauthor_mints.py build     # proposal + held + report + sample
"""
import argparse
import csv
import gzip
import json
import multiprocessing as mp
import random
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
from link_cited_work_authors import forms, nfold  # noqa: E402
from propose_person_dup_merges import strict_agree, name_forms  # noqa: E402

ROOT = I.ROOT
SRC = ROOT / 'data/identifiers/work-people-2026-11-11/coauthor-mints'
OUT = ROOT / 'data/identifiers/work-people-2026-11-11/coauthor-mints-narrowed'
P2 = ROOT / 'data/identifiers/cited-work-authors-promote-2026-11-11/proposal.json'
P1 = ROOT / 'data/identifiers/person-dup-merges-2026-11-11/proposal.json'
G = ROOT / 'build/graph'
WPS = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/workpeople')
SCR = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/proposals')
RAW = SCR / 'coauthor-raw-orcids.jsonl'
CACHE = ROOT / 'build/keylog-state.sqlite'
ID_RE = re.compile(r'"id":\s*"https://openalex\.org/W(\d+)"')
ORG = re.compile(r'(?i)\b(team|group|consortium|collaborat\w*|network|committee|investigators|project|society|association|'
                 r'council|institut\w*|universit\w*|department|centre|center|museum|library|foundation|press|muse|periodical|'
                 r'veranstaltung|commission|working party|archives|ministry|agency|corporation|laboratory|editorial board|'
                 r'gmbh|ltd|inc|anonymous|unknown author|et al)\b|[()&/@]|\d')
KNOWN_ERRORS = {('w-549919', 1): 'OpenAlex/publisher record names Iva Lučić (ORCID 0000-0003-0835-5896, inferred by '
                                 'OpenAlex); the author is Iva Peša, p-6823 (owner, 2026-11-11)'}


def source_file(name):
    if name.startswith('doi-lookup-'):
        return Path('/mnt/e/openalex-people-2026-11-09/doi-lookup') / (name[len('doi-lookup-'):] + '.jsonl.gz')
    if name.startswith('history-'):
        return Path('/mnt/e/openalex-history-2026-11-08/history') / (name[len('history-'):] + '.jsonl.gz')
    raise ValueError(name)


def _scan_one(args):
    path, want = args
    want = set(want)
    out = []
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            m = ID_RE.search(line, 0, 200)
            if not m or 'W' + m.group(1) not in want:
                continue
            d = json.loads(line)
            for i, a in enumerate(d.get('authorships') or []):
                au = a.get('author') or {}
                out.append(dict(oa_work='W' + m.group(1), pos=i, oa_author=(au.get('id') or '').rsplit('/', 1)[-1],
                                display=au.get('display_name'), raw=a.get('raw_author_name'),
                                orcid=(au.get('orcid') or '').rsplit('/', 1)[-1],
                                raw_orcid=(a.get('raw_orcid') or '').rsplit('/', 1)[-1]))
    return str(path), out


def load_proposal():
    with gzip.open(SRC / 'proposal.json.gz', 'rt', encoding='utf-8') as f:
        return json.load(f)


def mentions_of(prop):
    """person placeholder -> [(work, pos)]"""
    out = {}
    for o in prop['ops']:
        if o['event'] == 'mint' and o['type'] == 'person':
            out[o['key']] = [(a.split(':')[1], int(a.split(':')[2])) for a in o['anchors'] if a.startswith('coauthor-mention:')]
    return out


def scan(args):
    prop = load_proposal()
    ms = {m for v in mentions_of(prop).values() for m in v}
    db = duckdb.connect()
    db.execute(f"SET memory_limit='3GB'; SET threads=3")
    db.execute('CREATE TABLE m(work VARCHAR, pos BIGINT)')
    db.executemany('INSERT INTO m VALUES (?, ?)', sorted(ms))
    oa = {w for (w,) in db.execute(f"""SELECT DISTINCT p.oa_work FROM read_parquet('{WPS}/positions*.parquet', union_by_name=true) p
            JOIN m USING (work, pos) WHERE p.oa_work IS NOT NULL AND p.oa_work <> ''""").fetchall()}
    print(len(ms), 'mentions;', len(oa), 'OpenAlex records', flush=True)
    by_file = defaultdict(list)
    for p in sorted((WPS / 'oa').glob('*.jsonl')):
        with open(p, encoding='utf-8') as f:
            for line in f:
                w = line[10:40].split('"')[0]
                if w in oa:
                    by_file[source_file(p.stem)].append(w)
    print(len(by_file), 'source files', flush=True)
    n = 0
    with open(RAW, 'w', encoding='utf-8') as o, mp.get_context('fork').Pool(3) as pool:
        for path, rows in pool.imap_unordered(_scan_one, [(p, ws) for p, ws in by_file.items()]):
            for r in rows:
                o.write(json.dumps(r, ensure_ascii=False) + '\n')
            n += len(rows)
    print(n, 'authorships written to', RAW)


def toks(name):
    return {t for t in re.split(r'[^a-z]+', nfold(re.sub(r'[\u2010-\u2015\-]', ' ', name or ''))) if len(t) >= 3}


def _squash(name):
    return re.sub(r'[^a-z]', '', nfold(name or ''))


def _family_words(name):
    name = re.sub(r'\(.*?\)', ' ', name or '')
    part = name.split(',')[0] if ',' in name else ' '.join(name.split()[-2:])
    return {t for t in re.split(r'[^a-z]+', nfold(re.sub(r'[\u2010-\u2015\u2212\-]', ' ', part))) if len(t) >= 3}


def same_name(a, b):
    """Two printings may be one name unless neither printing's family-name words (3+ letters) occur anywhere in the
    other (letters only, accents, hyphens, apostrophes and word order ignored): 'Iva Lučić' / 'Iva Peša' differ;
    'Cristina Rihuete' / 'Cristina Rihuete Herrada', 'Skinner Quentin' / 'Quentin Skinner', 'Mike Savage' /
    'Savage, Michael Antony' do not. Given names are not compared (short forms and initials vary between printings)."""
    fa, fb = _family_words(a), _family_words(b)
    if not fa or not fb:
        return True
    sa, sb = _squash(a), _squash(b)
    return any(t in sb for t in fa) or any(t in sa for t in fb)


def fam(label):
    return toks(label)


def full_agree(la, lb):
    return any(fa == fb and strict_agree(ga, gb) for fa, ga in name_forms(la) for fb, gb in name_forms(lb))


def build(args):
    R = Counter()
    prop = load_proposal()
    ops = prop['ops']
    persons = {o['key']: o for o in ops if o['event'] == 'mint' and o['type'] == 'person'}
    claims_by_mention = {}
    for o in ops:
        if o['event'] == 'mint' and o['type'] == 'claim':
            a = o['anchors'][0]                         # coauthor-claim:<work>:<pos>
            _, w, p = a.split(':')
            claims_by_mention[(w, int(p))] = o
    attaches = [o for o in ops if o['event'] == 'attach']
    R['in_persons'] = len(persons)
    R['in_claims'] = len(claims_by_mention)
    R['in_possible_same_marks'] = len(attaches)
    men = mentions_of(prop)
    db = duckdb.connect()
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCR}/duck'")
    db.execute('CREATE TABLE m(work VARCHAR, pos BIGINT)')
    db.executemany('INSERT INTO m VALUES (?, ?)', sorted({x for v in men.values() for x in v}))
    pos = {}
    for w, p, role, name, orcid, oa_author, oa_work, n_auth, pid in db.execute(f"""SELECT DISTINCT ON (work, pos) p.work, p.pos,
            p.role, p.name, p.orcid, p.oa_author, p.oa_work, p.n_auth, p.pid FROM read_parquet('{WPS}/positions*.parquet', union_by_name=true) p
            JOIN m USING (work, pos) WHERE p.role IN ('author', 'jstor-author')""").fetchall():
        pos[(w, p)] = dict(role=role, name=name, orcid=orcid or '', oa_author=oa_author or '', oa_work=oa_work or '', n_auth=n_auth, pid=pid)
    # ---- roles (2026-11-12): series editors, foreword writers and other contributors are not co-authors, and a printed
    # list on a work the historian is credited with only under another role (volume editor, edition editor, translator,
    # introducer, series editor, contributor) is not a co-author list
    from link_work_people import agree_level
    contrib_pids = set()
    if (WPS / 'contributors.parquet').exists():
        contrib_pids = {x for (x,) in db.execute(f"SELECT pid FROM '{WPS}/contributors.parquet' WHERE role = 'contributor'").fetchall()}
    mworks = sorted({w for w, _ in pos})
    db.execute('CREATE TABLE mw(w VARCHAR)')
    db.executemany('INSERT INTO mw VALUES (?)', [(w,) for w in mworks])
    roles_on = defaultdict(set)
    for w, role in db.execute(f"""SELECT "to", coalesce(role, 'author') FROM '{G}/authored.parquet'
            WHERE "to" IN (SELECT w FROM mw) AND (evidence = 'keylog' OR state = 'exact')""").fetchall():
        roles_on[w].add(role)
    plab = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    other_role_names = defaultdict(list)       # printed or keyed names on the work in a non-author role
    for k, w, src in db.execute(f"""SELECT "from", "to", 'contributed' FROM '{G}/contributed.parquet' WHERE "to" IN (SELECT w FROM mw)
            UNION ALL SELECT "from", "to", 'edited' FROM '{G}/edited.parquet' WHERE "to" IN (SELECT w FROM mw)
            UNION ALL SELECT "from", "to", 'authored:' || role FROM '{G}/authored.parquet' WHERE "to" IN (SELECT w FROM mw)
                  AND role IS NOT NULL AND role <> 'author'""").fetchall():
        other_role_names[w].append((plab.get(k, ''), src))
    VE = ROOT / 'data/graph/volume-editors.csv.gz'
    if VE.exists():
        for w, nm, st in db.execute(f"""SELECT volume, printed_name, state FROM read_csv('{VE}', all_varchar=true)
                WHERE volume IN (SELECT w FROM mw)""").fetchall():
            other_role_names[w].append((nm or '', 'volume-editors:series-editor' if st == 'series-editor' else 'volume-editors:editor'))

    def role_drop(m, p):
        if p.get('pid') in contrib_pids:
            return 'contributor-position'
        rs = roles_on.get(m[0], set())
        if rs and 'author' not in rs:
            return 'historian-credit-role-' + sorted(rs)[0]
        for nm, src in other_role_names.get(m[0], ()):
            if nm and p['name'] and agree_level(p['name'], nm) in ('full', 'variant', 'initial'):
                return 'printed-name-in-role-' + src.replace(':', '-')
        return None
    raw = {}
    with open(RAW, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            raw[(r['oa_work'], r['pos'])] = r
    # positions of the same OpenAlex author ids / ORCIDs elsewhere among the graph's author positions
    ids = {(v['oa_author']) for v in pos.values() if v['oa_author']}
    orcs = {v['orcid'] for v in pos.values() if v['orcid']}
    db.execute('CREATE TABLE ida(x VARCHAR)')
    db.executemany('INSERT INTO ida VALUES (?)', [(x,) for x in ids | orcs])
    elsewhere = defaultdict(list)
    for w, p, name, orcid, oa_author, credited in db.execute(f"""SELECT work, pos, name, orcid, oa_author, credited
            FROM read_parquet('{WPS}/positions*.parquet', union_by_name=true)
            WHERE role IN ('author', 'jstor-author') AND (oa_author IN (SELECT x FROM ida) OR orcid IN (SELECT x FROM ida))""").fetchall():
        rec = (w, p, name, credited or '')
        if oa_author in ids:
            elsewhere['oa:' + oa_author].append(rec)
        if orcid in orcs:
            elsewhere['orcid:' + orcid].append(rec)
    # key-log authors of each work vs the printed names (current graph; merged keys resolved through the cache)
    con = sqlite3.connect(f'file:{CACHE}?mode=ro', uri=True)

    def current(k, _c={}):
        if k not in _c:
            seen, todo, out = set(), [k], []
            while todo:
                x = todo.pop()
                if x in seen:
                    continue
                seen.add(x)
                row = con.execute('SELECT status, replaced_by FROM keys WHERE key = ?', (x,)).fetchone()
                if not row:
                    continue
                if row[0] in I.RETIRED:
                    todo.extend(json.loads(row[1] or '[]'))
                else:
                    out.append(x)
            _c[k] = tuple(out)
        return _c[k]
    works = {w for w, _ in pos}
    db.execute('CREATE TABLE ws(w VARCHAR)')
    db.executemany('INSERT INTO ws VALUES (?)', [(w,) for w in works])
    klog = defaultdict(set)
    for k, w in db.execute(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE evidence = 'keylog' AND "to" IN (SELECT w FROM ws)""").fetchall():
        klog[w].add(k)
    matched = defaultdict(set)
    for w, credited, state, key in db.execute(f"""SELECT p.work, p.credited, r.state, r.key FROM read_parquet('{WPS}/positions*.parquet', union_by_name=true) p
            LEFT JOIN '{WPS}/results.parquet' r USING (pid) WHERE p.work IN (SELECT w FROM ws)""").fetchall():
        if credited:
            matched[w].update(current(credited))
        if state in ('exact', 'linked') and key:
            for x in key.split(';'):
                matched[w].update(current(x))
    unmatched = {w for w in works if {c for k in klog.get(w, ()) for c in current(k)} - matched[w]}
    R['works_with_unmatched_keylog_author'] = len(unmatched)
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())

    # ---- per person
    keep, held, drop_mentions = {}, [], Counter()
    for ph, o in persons.items():
        ms = men[ph]
        lab = o['label']
        orc = next((a[len('orcid:'):] for a in o['anchors'] if a.startswith('orcid:')), '')
        bas = o['basis']
        grouped_on = re.search(r'mentions joined on ([^;]+)', bas)
        grouped_on = grouped_on.group(1).split(', ') if grouped_on else []
        if ORG.search(lab):
            R['drop_organisation_name'] += 1
            held.append(dict(person=ph, label=lab, reason='organisation or non-personal name'))
            continue
        good, why_drop = [], {}
        printed = False
        for m in ms:
            p = pos.get(m)
            if m in KNOWN_ERRORS:
                why_drop[m] = 'known-source-error'
                continue
            if m[0] in unmatched:
                why_drop[m] = 'work-has-keylog-author-matching-no-printed-name'
                continue
            if p is None:
                why_drop[m] = 'position-not-found'
                continue
            rd = role_drop(m, p)
            if rd:
                why_drop[m] = rd
                continue
            r = raw.get((p['oa_work'], m[1])) if p['role'] == 'author' else None
            if r and r['orcid'] and r['raw_orcid'] and r['orcid'] != r['raw_orcid']:
                why_drop[m] = 'openalex-orcid-differs-from-printed'
                continue
            if r and r['raw'] and r['display'] and not same_name(r['raw'], r['display']):
                why_drop[m] = 'printed-name-differs-from-openalex-author'
                continue
            bad = False
            for key in (['oa:' + p['oa_author']] if p['oa_author'] else []) + (['orcid:' + p['orcid']] if p['orcid'] else []):
                for (w2, p2, name2, cred2) in elsewhere.get(key, ()):
                    if (w2, p2) == m:
                        continue
                    if cred2 or (name2 and not same_name(name2, lab)):
                        bad = True
                        break
                if bad:
                    break
            if bad:
                why_drop[m] = 'openalex-author-or-orcid-on-another-persons-position'
                continue
            if r and orc and r['raw_orcid'] == orc:
                printed = True
            good.append((m, p, r))
        # inferred-only ORCID mentions of a printed-ORCID person: keep only with full name agreement
        if printed:
            g2 = []
            for m, p, r in good:
                if r and r['raw_orcid'] != orc and not same_name(r['raw'] or p['name'], lab):
                    why_drop[m] = 'orcid-only-inferred-and-name-not-in-full'
                    continue
                g2.append((m, p, r))
            good = g2
        for m, why in why_drop.items():
            drop_mentions[why] += 1
        works_kept = {m[0] for m, _, _ in good}
        if printed and good:
            basis = 'printed-orcid'
        elif len(works_kept) >= 2 and grouped_on:
            basis = 'grouped:' + '+'.join(sorted(grouped_on))
        else:
            why = ('single-work-or-name-only' if not grouped_on and not orc else
                   'orcid-only-inferred-single-work' if orc and not printed and len(works_kept) < 2 else
                   'orcid-only-inferred-no-shared-fact' if orc and not printed else
                   'fewer-than-two-works-after-drops')
            R[f'drop_{why}'] += 1
            if why != 'single-work-or-name-only':
                held.append(dict(person=ph, label=lab, orcid=orc, reason=why, dropped=sorted(f'{w}:{p}:{x}' for (w, p), x in why_drop.items())))
            continue
        keep[ph] = dict(op=o, mentions=[m for m, _, _ in good], basis=basis, orcid=orc if printed else '',
                        inferred_orcid='' if printed else orc, dropped=why_drop)
    R['mentions_dropped_by_reason'] = dict(drop_mentions)
    R['kept_before_twin_check'] = len(keep)
    R['kept_by_basis_before_twin_check'] = dict(Counter(v['basis'].split(':')[0] for v in keep.values()))

    # ---- twin check: current live person keys, ORCIDs on keys, LC headings minted by the promotion
    by_fam = defaultdict(list)
    for k, lab in con.execute("SELECT key, label FROM keys WHERE type = 'person' AND status NOT IN ('merged', 'split', 'withdrawn', 'retyped')"):
        for f, g in name_forms(lab):
            by_fam[f].append((k, g, lab))
    if P2.exists():
        for o in json.loads(P2.read_text())['ops']:
            if o['event'] == 'mint' and o['type'] == 'person':
                for f, g in name_forms(o['label']):
                    by_fam[f].append((o['anchors'][0], g, o['label']))
    merged_away = set()
    if P1.exists():
        merged_away = {o['key'] for o in json.loads(P1.read_text())['ops'] if o['event'] == 'merge'}
    final = {}
    for ph, v in keep.items():
        lab = v['op']['label']
        if v['orcid']:
            row = con.execute('SELECT key FROM anchor WHERE anchor = ?', ('orcid:' + v['orcid'],)).fetchone()
            if row:
                R['held_orcid_already_on_a_key'] += 1
                held.append(dict(person=ph, label=lab, orcid=v['orcid'], reason='ORCID already on a key', key=row[0]))
                continue
        twins = sorted({k for f, g in name_forms(lab) for k, g2, l2 in by_fam.get(f, ()) if k not in merged_away and strict_agree(g, g2)})
        if twins:
            R['held_twin_full_name'] += 1
            held.append(dict(person=ph, label=lab, orcid=v['orcid'], reason='a person key (or a promoted LC heading) bears the same full name',
                             twins=twins[:5], twin_labels=[label.get(k, k) for k in twins[:5]]))
            continue
        final[ph] = v
    R['people_to_mint'] = len(final)
    R['people_by_basis'] = dict(Counter(v['basis'].split(':')[0] for v in final.values()))
    R['people_grouped_by_fact'] = dict(Counter(v['basis'] for v in final.values() if v['basis'].startswith('grouped')))

    # ---- ops
    out_ops = []
    kept_ph = set(final)
    for ph, v in final.items():
        o = dict(v['op'])
        anchors = ([f"orcid:{v['orcid']}"] if v['orcid'] else []) + [f'coauthor-mention:{w}:{p}' for w, p in sorted(v['mentions'])]
        members = list(o.get('members', [])) + ([f"orcid-inferred:{v['inferred_orcid']}"] if v['inferred_orcid'] else [])
        why = ('ORCID printed in the source record' if v['basis'] == 'printed-orcid' else
               f"name agreed in full across {len({w for w, _ in v['mentions']})} works and joined on {v['basis'][len('grouped:'):]}")
        o.update(anchors=anchors, members=members, resolution='established' if v['orcid'] else 'recorded',
                 basis=f"{why}; " + o['basis'].split('; ', 1)[1] if '; ' in o['basis'] else why)
        out_ops.append(o)
        for m in sorted(v['mentions']):
            c = dict(claims_by_mention[m])
            c['relation'] = dict(c['relation'], subject=anchors[0])
            out_ops.append(c)
    for a in attaches:
        tgt = a['members'][0][len('possible-same:'):]
        if a['key'] in kept_ph and tgt in kept_ph:
            out_ops.append(a)
            R['possible_same_marks_kept'] += 1
    R['claims'] = sum(1 for o in out_ops if o['event'] == 'mint' and o['type'] == 'claim')
    proposal = dict(basis='co-authors of historian keys, narrowed (owner 2026-11-11): printed ORCID or a name group joined by a '
                          'shared fact across two or more works; source errors and twins held; dead end: only the co-authored '
                          'works (narrow_coauthor_mints.py)', decided_by='rule', ops=out_ops)
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
        f.write(json.dumps(proposal, ensure_ascii=False) + '\n')
    with gzip.open(OUT / 'held.json.gz', 'wt', encoding='utf-8') as f:
        f.write(json.dumps(held, ensure_ascii=False, default=str) + '\n')
    rnd = random.Random(20261111)
    sample = rnd.sample(sorted(final), min(60, len(final)))
    with open(OUT / 'sample-60.csv', 'w', newline='', encoding='utf-8') as f:
        w_ = csv.writer(f)
        w_.writerow(['placeholder', 'label', 'orcid', 'basis', 'works', 'printed_names', 'historian_coauthors'])
        for ph in sample:
            v = final[ph]
            hist = re.search(r'historian key \(([^)]*)\)', v['op']['basis'])
            w_.writerow([ph, v['op']['label'], v['orcid'] or ('inferred:' + v['inferred_orcid'] if v['inferred_orcid'] else ''),
                         v['basis'], ' '.join(sorted({w for w, _ in v['mentions']})),
                         ' | '.join(sorted({pos[m]['name'] for m in v['mentions'] if m in pos})),
                         '; '.join(f'{h} {label.get(h, "")}' for h in (hist.group(1).split(', ') if hist else []))])
    # error-class examples
    ex = defaultdict(list)
    for ph, v in keep.items():
        for m, why in v['dropped'].items():
            if len(ex[why]) < 8:
                ex[why].append(dict(label=v['op']['label'], work=m[0], pos=m[1], printed=pos.get(m, {}).get('name')))
    R['dropped_mention_examples'] = dict(ex)
    if not args.no_validate:
        import keylog_snapshot as KS
        I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
        st = KS.read_state()
        R['keylog_seq'] = st.seq
        for name, path in (('p1', P1), ('p2', P2)):
            if path.exists():
                # 2026-11-12: both were applied that day; a proposal already in the log is skipped, not replayed
                try:
                    ev, _ = I.materialise(st, json.loads(path.read_text()), 'dry-run', 'dry-run', inplace=True)
                    R[f'dry_run_after_{name}_events'] = len(ev)
                except Exception as e:
                    R[f'dry_run_after_{name}'] = f'skipped (already applied or does not apply: {type(e).__name__})'
        ev, names = I.materialise(st, proposal, 'dry-run', 'dry-run', inplace=True)
        R['dry_run_events'] = len(ev)
    rep = {k: v for k, v in sorted(R.items())}
    rep['rule'] = __doc__.split('\n\n')[1]
    (OUT / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('rule', 'dropped_mention_examples')}, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cmd', choices=['scan', 'build'])
    ap.add_argument('--no-validate', action='store_true')
    args = ap.parse_args()
    (scan if args.cmd == 'scan' else build)(args)


if __name__ == '__main__':
    main()
