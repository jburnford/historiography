"""Tests for scripts/dissertation_ingest.py: source adapters, file checks and the idempotent merge.

Run: python3 -m pytest tests/test_dissertation_ingest.py -q
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import dissertation_ingest as ing  # noqa: E402
import extract_dissertation_bibliographies as ext  # noqa: E402

OLD = time.time() - 3600


def pdf(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'%PDF-1.4\n' + body.encode() + b'\n%%EOF\n')
    os.utime(path, (OLD, OLD))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def us_record(inst, rid, title, author, year, access='open_pdf'):
    return dict(institution=inst, id=rid, title=title, authors=[author], advisors=[], issued_dates=[str(year)],
                graduation_dates=[], copyright_dates=[], history_scope='explicit_history_program_or_department',
                language=['en'], item_url=f'https://repo.example/{rid}', degree_classification='doctoral',
                eligibility='history_phd', eligibility_basis='AHA History PhD record matched', access_category=access,
                year=year)


@pytest.fixture
def world(tmp_path):
    """A dissertation-citations directory D with a PDF store outside it (as on E:), one existing
    US entry with a logged PDF, and an expansion manifest whose paths go through a symlink."""
    store = tmp_path / 'E'
    d = tmp_path / 'D'
    d.mkdir()
    (d / 'pdf').symlink_to(store, target_is_directory=True)
    harvest = tmp_path / 'harvest'
    harvest.mkdir()
    old = us_record('duke', 'a1', 'Babel on the Hudson: Community Formation in Dutch Manhattan', 'Sivertsen, Karen', 2007)
    (harvest / 'records.jsonl').write_text(json.dumps(old) + '\n')
    sha_a1 = pdf(store / 'duke' / 'a1.pdf', 'a1')
    (d / 'downloads-us.jsonl').write_text(json.dumps(dict(
        institution='duke', id='a1', status='downloaded',
        files=[dict(path='pdf/duke/a1.pdf', bytes=(store / 'duke/a1.pdf').stat().st_size, sha256=sha_a1, primary=True)])) + '\n')
    manifest = [ing.us_entry(old, str(harvest))]
    (d / 'doctorates.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    # expansion: files under a local folder whose pdf/ is a symlink into the store
    exp = tmp_path / 'expansion'
    (store / 'exp' / 'mich').mkdir(parents=True)
    (exp / 'mich').mkdir(parents=True)
    (exp / 'mich' / 'pdf').symlink_to(store / 'exp' / 'mich', target_is_directory=True)
    return dict(d=d, store=store, harvest=harvest, exp=exp, tmp=tmp_path, sha_a1=sha_a1)


def write_manifest(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['institution', 'id', 'title', 'authors', 'year', 'aha_id', 'item_url',
                                          'eligibility_basis', 'files', 'bytes', 'paths'])
        w.writeheader()
        for r in rows:
            w.writerow(r)


def mrow(inst, rid, title, author, year, paths):
    return dict(institution=inst, id=rid, title=title, authors=author, year=year, aha_id='1', item_url=f'https://x/{rid}',
                eligibility_basis='AHA History PhD record matched', files=len(paths), bytes=0, paths=json.dumps([str(p) for p in paths]))


def run(world, sources, dry=False, settle=0):
    d = world['d']
    store = ing.Store(d, settle, d / 'logs' / 'sha.json')
    manifest, appended, rows, report = ing.merge(d, sources, store)
    ing.write_outputs(d, manifest, appended, rows, report, dry)
    return appended, rows, report


def test_existing_entries_reproduced_and_untouched(world):
    d = world['d']
    before = (d / 'doctorates.json').read_text()
    src = dict(name='tier', adapter='us_records', verify_existing=True, records=str(world['harvest'] / 'records.jsonl'),
               logs=[str(d / 'downloads-us.jsonl')])
    appended, rows, report = run(world, [src])
    r = report['sources']['tier']
    assert (r['present'], r['present_identical'], r['new']) == (1, 1, 0)
    assert appended == [] and rows == []
    assert (d / 'doctorates.json').read_text() == before


def test_expansion_new_entry_symlinked_path_multipart_and_idempotent(world):
    d, exp, store = world['d'], world['exp'], world['store']
    p1, p2 = exp / 'mich' / 'pdf' / 'm1.pdf', exp / 'mich' / 'pdf' / 'm1.1.pdf'
    pdf(p1, 'part one')
    pdf(p2, 'part two with bibliography')
    write_manifest(exp / 'collection-manifest.csv', [
        mrow('michigan', 'm1', 'The Second Bank of the United States', 'Shortt, George', 1929, [p1, p2]),
        mrow('duke', 'a1', 'Babel on the Hudson', 'Sivertsen, Karen', 2007, [store / 'duke' / 'a1.pdf'])])
    src = dict(name='exp', adapter='us_expansion_manifest', manifests=str(exp / 'collection-manifest*.csv'), records=[], logs=[])
    before = (d / 'doctorates.json').read_text()
    appended, rows, report = run(world, [src])
    r = report['sources']['exp']
    assert (r['new'], r['present'], r['present_same_file']) == (1, 1, 1)
    e = appended[0]
    assert e['country'] == 'US' and e['pdf_paths'] == ['exp/mich/m1.pdf', 'exp/mich/m1.1.pdf']
    assert e['history_scope'].startswith('explicit_history') and e['eligibility_basis'] == 'AHA History PhD record matched'
    files = rows[0]['files']
    assert [f['path'] for f in files] == ['pdf/exp/mich/m1.pdf', 'pdf/exp/mich/m1.1.pdf']
    assert [f['part'] for f in files] == [1, 2] and files[0]['primary'] and not files[1]['primary']
    after = (d / 'doctorates.json').read_text()
    assert after.startswith(before.rstrip()[:-1].rstrip())  # old entries byte-identical, in order
    log1 = (d / 'downloads-ingest.jsonl').read_text()
    # second run: nothing new, same outputs
    appended2, rows2, report2 = run(world, [src])
    assert appended2 == [] and report2['sources']['exp']['present'] == 2
    assert (d / 'doctorates.json').read_text() == after
    assert (d / 'downloads-ingest.jsonl').read_text() == log1
    # the extractor reads the declared parts together
    assert ext.declared_parts(rows2[0], d) == [str(d / 'pdf/exp/mich/m1.pdf'), str(d / 'pdf/exp/mich/m1.1.pdf')]


def test_dedupe_by_sha_and_title_and_id_namespacing(world):
    exp, store = world['exp'], world['store']
    a = exp / 'mich' / 'pdf' / 'x.pdf'
    pdf(a, 'same body')
    b = store / 'exp' / 'other' / 'y.pdf'
    pdf(b, 'same body')  # identical bytes under another id
    c = exp / 'mich' / 'pdf' / 'z.pdf'
    pdf(c, 'a different scan')
    dcol = exp / 'mich' / 'pdf' / 'a1.pdf'
    pdf(dcol, 'another dissertation that reuses an id')
    write_manifest(exp / 'collection-manifest.csv', [
        mrow('michigan', 'x', 'Cotton and Empire in the Gulf South', 'Smith, Ann', 2014, [a]),
        mrow('rice', 'y', 'Something Else Entirely Here', 'Jones, Bob', 2014, [b]),
        mrow('rice', 'z', 'COTTON AND EMPIRE IN THE GULF SOUTH.', 'Smith, Ann B.', 2015, [c]),
        mrow('rice', 'a1', 'A Wholly Different Thesis Title', 'Brown, Cy', 2001, [dcol])])
    src = dict(name='exp', adapter='us_expansion_manifest', manifests=str(exp / 'collection-manifest.csv'), records=[], logs=[])
    appended, rows, report = run(world, [src])
    r = report['sources']['exp']
    assert r['duplicate_sha'] == 1 and r['duplicate_title'] == 1 and r['id_namespaced'] == 1
    assert sorted(e['id'] for e in appended) == ['rice-a1', 'x']


def test_file_checks_part_recent_top_level_missing(world):
    exp, store = world['exp'], world['store']
    part = exp / 'mich' / 'pdf' / 'p.pdf'
    pdf(part, 'growing')
    Path(str(part.resolve()) + '.part').write_bytes(b'')
    recent = exp / 'mich' / 'pdf' / 'r.pdf'
    pdf(recent, 'fresh')
    os.utime(recent, None)
    top = store / 'personal.pdf'
    pdf(top, 'not a dissertation')
    write_manifest(exp / 'collection-manifest.csv', [
        mrow('michigan', 'p', 'Title Number One Is Long Enough', 'A, B', 2010, [part]),
        mrow('michigan', 'r', 'Title Number Two Is Long Enough', 'C, D', 2010, [recent]),
        mrow('michigan', 't', 'Title Number Three Is Long Enough', 'E, F', 2010, [top]),
        mrow('michigan', 'm', 'Title Number Four Is Long Enough', 'G, H', 2010, [exp / 'mich' / 'pdf' / 'gone.pdf'])])
    src = dict(name='exp', adapter='us_expansion_manifest', manifests=str(exp / 'collection-manifest.csv'), records=[], logs=[])
    appended, rows, report = run(world, [src], settle=5)
    probs = report['sources']['exp']['file_problems']
    assert probs == {'still_downloading': 2, 'top_level_file_ignored': 1, 'missing_file': 1}
    assert appended == []


def test_registered_top_level_files_are_taken_only_with_matching_sha(world):
    """Browser downloads stay at the top of the store; a download log with their SHA-256 admits them."""
    exp, store = world['exp'], world['store']
    good, changed = store / 'qtgood0001.pdf', store / 'qtchanged01.pdf'
    sha_good = pdf(good, 'registered uc dissertation')
    sha_changed = pdf(changed, 'registered then overwritten')
    pdf(changed, 'a different file now')
    log = exp / 'manual-uc' / 'downloads.jsonl'
    log.parent.mkdir(parents=True)
    log.write_text(''.join(json.dumps(dict(institution='ucla', id=i, status='downloaded',
                                           files=[dict(path=str(p), bytes=p.stat().st_size, sha256=s)])) + '\n'
                           for i, p, s in [('g', good, sha_good), ('c', changed, sha_changed)]))
    write_manifest(exp / 'collection-manifest.csv', [
        mrow('ucla', 'g', 'A Registered Browser Download Title', 'A, B', 2015, [good]),
        mrow('ucla', 'c', 'An Overwritten Browser Download Title', 'C, D', 2016, [changed])])
    src = dict(name='exp', adapter='us_expansion_manifest', manifests=str(exp / 'collection-manifest.csv'),
               records=[], logs=[str(log)])
    appended, rows, report = run(world, [src])
    assert [e['id'] for e in appended] == ['g']
    assert report['sources']['exp']['file_problems'] == {'top_level_sha_mismatch': 1}


def test_base_adapter_country_label_tolerant_log_and_dry(world):
    d, store, tmp = world['d'], world['store'], world['tmp']
    clusters = [
        dict(cluster_id='https://theses.hal.science/tel-1', title='Les ouvriers de Lyon au XIXe siecle', creators=['Dupont, Marie'],
             year=2019, country='France', source_key='theses.hal.science', link='https://theses.hal.science/tel-1',
             language='fr', history_label='history', history_basis=['history-discipline category'], repository='HAL'),
        dict(cluster_id='https://x.uni-wien.ac.at/1', title='Wiener Arbeiterbewegung und Stadtpolitik', creators=['Huber, Hans'],
             year=2018, country='Germany/Austria/Switzerland', source_key='x', link='https://x.uni-wien.ac.at/1',
             language='de', history_label='history', repository='Wien'),
        dict(cluster_id='https://y.example.org/2', title='Possibly history of something or other', creators=['Z, Z'],
             year=2018, country='unknown', source_key='y', link='https://y.example.org/2', language='en',
             history_label='possible', repository='Y')]
    (tmp / 'clusters.jsonl').write_text(''.join(json.dumps(c) + '\n' for c in clusters))
    rows = []
    for i, c in enumerate(clusters):
        p = store / 'base' / f'f{i}.pdf'
        sha = pdf(p, f'base {i}')
        rows.append(dict(cluster_id=c['cluster_id'], status='downloaded',
                         files=[dict(path=f'pdf/base/f{i}.pdf', bytes=p.stat().st_size, sha256=sha)]))
    text = ''.join(json.dumps(r) + '\n' for r in rows) + '{"cluster_id": "https://half-written'
    (d / 'downloads-base.jsonl').write_text(text)
    src = dict(name='base', adapter='base_clusters', clusters=str(tmp / 'clusters.jsonl'), logs=['downloads-base.jsonl'],
               labels=['history'], ingest=False)
    appended, _, report = run(world, [src])
    r = report['sources']['base']
    assert (r['candidates'], r['new'], appended) == (2, 2, [])
    assert r['by_country'] == {'FR': 1, 'AT': 1}
    src['ingest'] = True
    appended, rows2, report = run(world, [src])
    assert {e['country'] for e in appended} == {'FR', 'AT'}
    assert all(e['history_label'] == 'history' and e['institution'].startswith('base:') for e in appended)
    assert all(r['files'][0]['path'].startswith('pdf/base/') for r in rows2)


def test_browser_manifest_with_aha_match(world):
    tmp, store = world['tmp'], world['store']
    root = store / 'us-browser'
    pdf(root / 'berkeley' / 'smith-2014-empire.pdf', 'browser pdf')
    with (root / 'manifest.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['institution', 'department', 'author', 'title', 'year', 'degree', 'repository_item_url', 'pdf_url',
                    'file_name', 'license_or_rights_statement', 'notes'])
        w.writerow(['Berkeley', 'History', 'Smith, Ann', 'Empire of Cotton in the Gulf', '2014', 'Ph.D.',
                    'https://escholarship.org/uc/item/1', 'https://escholarship.org/1.pdf', 'smith-2014-empire.pdf', 'CC BY 4.0', ''])
    aha = tmp / 'aha.csv'
    aha.write_text('id,dissertator,department,orgcd,title,status,year,advisors,advisor_ids\n'
                   '777,"Smith, Ann","Univ. of California, Berkeley, Dept. of History",1,Empire of Cotton in the Gulf,completed,2014,,\n')
    src = dict(name='browser', adapter='browser_manifest', manifest=str(root / 'manifest.csv'), root=str(root), aha=str(aha))
    appended, rows, report = run(world, [src])
    e = appended[0]
    assert (e['institution'], e['id'], e['aha_id'], e['country']) == ('berkeley', 'smith-2014-empire', '777', 'US')
    assert e['history_scope'] == 'explicit_history_program_or_department'
    assert e['pdf_paths'] == ['us-browser/berkeley/smith-2014-empire.pdf']


def test_absent_sources_are_no_ops(world):
    src = dict(name='browser', adapter='browser_manifest', manifest=str(world['tmp'] / 'nope.csv'))
    appended, rows, report = run(world, [src])
    assert report['sources']['browser']['candidates'] == 0 and appended == []


def test_base_country_fallbacks():
    assert ing.base_country(dict(country='Hong Kong')) == 'HK'
    assert ing.base_country(dict(country='International', link='https://eprints.lse.ac.uk/1')) == 'GB'
    assert ing.base_country(dict(country='unknown', link='https://example.org/1')) == 'ZZ'


def test_restricted_run_keeps_other_sources_rows(world):
    d, exp = world['d'], world['exp']
    p1 = exp / 'mich' / 'pdf' / 'k.pdf'
    pdf(p1, 'kept row')
    write_manifest(exp / 'collection-manifest.csv', [mrow('michigan', 'k', 'A Thesis Whose Row Must Survive', 'Doe, J', 2010, [p1])])
    src = dict(name='exp', adapter='us_expansion_manifest', manifests=str(exp / 'collection-manifest.csv'), records=[], logs=[])
    other = dict(name='browser', adapter='browser_manifest', manifest=str(world['tmp'] / 'none.csv'))
    run(world, [src, other])
    before = (d / 'downloads-ingest.jsonl').read_text()
    store = ing.Store(d, 0, d / 'logs' / 'sha.json')
    manifest, appended, rows, report = ing.merge(d, [src, other], store, only=['browser'])
    ing.write_outputs(d, manifest, appended, rows, report, False)
    assert (d / 'downloads-ingest.jsonl').read_text() == before


def test_oxford_ora_adapter_takes_downloaded_rows_with_supervisors(world):
    ox = world['tmp'] / 'ox'
    ox.mkdir()
    p = world['tmp'] / 'E' / 'ora' / 'ora-ora-abc.pdf'
    sha = pdf(p, 'ox')
    rows = [dict(doi='10.5287/ora-abc', id='ora-ora-abc', url='https://ora.ox.ac.uk/objects/uuid:1', year=2022,
                 title='The Fourth Republic and the practicing of democracy in Brazil, 1930-1968',
                 authors=['Silva, Ana'], supervisors=['Posada-Carbó, Eduardo'], department='History Faculty',
                 award_type='DPhil', history_scope='explicit_history_department', basis='department: History Faculty',
                 status='downloaded', path=str(p), bytes=p.stat().st_size, sha256=sha),
            dict(doi='10.5287/ora-def', id='ora-ora-def', url='u', year=2021, title='No open file here at all',
                 history_scope='explicit_history_department', basis='b', status='no_open_pdf')]
    (ox / 'downloads.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    src = dict(name='oxford_ora', adapter='oxford_ora', root=str(ox))
    appended, _, report = run(world, [src])
    assert report['sources']['oxford_ora']['candidates'] == 1
    (e,) = appended
    assert (e['institution'], e['country'], e['advisors']) == ('uk:oxford', 'GB', ['Posada-Carbó, Eduardo'])
    assert e['history_scope'] == 'explicit_history_department' and e['year'] == 2022


def test_france_thesesfr_adapter_takes_downloaded_rows_and_latest_retry(world):
    fr = world['tmp'] / 'fr'
    fr.mkdir()
    p = world['tmp'] / 'E' / 'fr' / '2023SORUL048.pdf'
    sha = pdf(p, 'fr')
    cands = [dict(nnt='2023SORUL048', titres={'fr': 'Les ouvriers de Lorraine, 1871-1914', 'en': 'Lorraine workers'},
                  date_soutenance='2023-11-20', discipline='Histoire contemporaine',
                  etablissements_soutenance=[{'nom': 'Sorbonne Université'}],
                  auteurs=[{'nom': 'Martin', 'prenom': 'Claire'}],
                  directeurs_these=[{'nom': 'Dupont', 'prenom': 'Jean'}, {'nom': 'inconnu', 'prenom': ''}]),
             dict(nnt='2021UBFCC029', titres={'fr': 'Réservé'}, date_soutenance='2021-06-01', discipline='Histoire')]
    (fr / 'candidates.json').write_text(json.dumps(cands))
    rows = [dict(nnt='2023SORUL048', status='not_pdf', links=['https://theses.hal.science/tel-04318036']),
            dict(nnt='2021UBFCC029', status='error', error='HTTPError: HTTP Error 403: '),
            dict(nnt='2023SORUL048', status='downloaded', url='https://theses.hal.science/tel-04318036/document',
                 path=str(p), bytes=p.stat().st_size, sha256=sha, checked_at='2026-10-30T17:36:25Z')]
    (fr / 'downloads.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    src = dict(name='france_thesesfr', adapter='france_thesesfr', root=str(fr))
    appended, _, report = run(world, [src])
    assert report['sources']['france_thesesfr']['candidates'] == 1
    (e,) = appended
    assert (e['institution'], e['country'], e['id']) == ('fr:sorbonne-universite', 'FR', 'thesesfr-2023SORUL048')
    assert e['title'] == 'Les ouvriers de Lorraine, 1871-1914' and e['year'] == 2023
    assert e['authors'] == ['Martin, Claire'] and e['advisors'] == ['Dupont, Jean']
    assert e['history_scope'] == 'explicit_history_discipline'
