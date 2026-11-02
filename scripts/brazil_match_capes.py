#!/usr/bin/env python3
"""Match Brazilian repository records to CAPES History doctorates (Brazil expansion, 2026-11-01).

Inputs, all under ``<out>`` (data/field-research/brazil-theses-2026-10-31):
- ``capes/*.jsonl`` from ``capes_catalogue_harvest.py``. A doctorate is a row whose level is
  DOUTORADO and whose knowledge area is HISTÓRIA (the CAPES record is the History screen).
- ``oai/<INST>.jsonl`` from ``brazil_oai_harvest.py`` (Dublin Core).
- ``uff-ppgh/records.jsonl`` from ``brazil_uff_ppgh.py``.

A repository record matches a CAPES doctorate of the same institution when the folded titles
agree on their first 60 characters (repositories truncate and re-punctuate titles), or when the
author's name tokens agree and the titles are at least 0.85 similar. Years must be within two
(CAPES files a thesis by base year; repositories by deposit). One record per doctorate: an exact
title match wins over a fuzzy one.

Output: ``<out>/candidates.json``, one entry per matched doctorate: the CAPES fields the ingest
needs (ids, author, advisors, title, year, programme, abstract) plus the repository record (item
URL, any direct PDF). ``<out>/match-report.json`` gives counts per institution.

    python3 scripts/brazil_match_capes.py --out data/field-research/brazil-theses-2026-10-31
"""
import argparse
import difflib
import glob
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# CAPES institution acronyms (SG_ENTIDADE_ENSINO / SiglaIes) for each repository source.
INST = {'USP': {'USP'}, 'UFRJ': {'UFRJ'}, 'UFMG': {'UFMG'}, 'UERJ': {'UERJ'}, 'UFU': {'UFU'},
        'UFPA': {'UFPA'}, 'FGV': {'FGV/RJ', 'FGV-RJ', 'FGV'}, 'UFES': {'UFES'}, 'UFPE': {'UFPE'},
        'UFF': {'UFF'}, 'UFRGS': {'UFRGS'}, 'UNB': {'UNB'}, 'UNESP': {'UNESP', 'UNESP/ASS', 'UNESP/FR', 'UNESP/MAR'}}


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def name_tokens(name):
    """'Silva, Maria José da' and 'MARIA JOSE DA SILVA' -> {'silva', 'maria', 'jose'}."""
    return {t for t in fold(name.replace(',', ' ')).split() if len(t) > 2}


def doc_key(d):
    """Stable key of a CAPES doctorate: br-<institution>-<CAPES production id>, or year + author before 2013."""
    key = d['capes_id'] or f"{d['year']}-{'-'.join(fold(d['author']).split()[:4])}"
    return f"br-{fold(d['inst']).replace(' ', '')}-{key}"


def capes_doctorates(out):
    for f in sorted(glob.glob(str(out / 'capes' / '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            level = (r.get('NM_GRAU_ACADEMICO') or r.get('Nivel') or '').upper()
            area = fold(r.get('NM_AREA_CONHECIMENTO') or r.get('AreaConhecimento') or '')
            if level != 'DOUTORADO' or area != 'historia':
                continue
            new = 'AN_BASE' in r
            advisors = ([r['NM_ORIENTADOR']] if new else
                        [r.get(f'Orientador_{i}') for i in range(1, 5)])
            yield dict(
                capes_id=r.get('ID_PRODUCAO_INTELECTUAL') or None,
                year=int((r.get('AN_BASE') or r.get('AnoBase'))[:4]),
                inst=(r.get('SG_ENTIDADE_ENSINO') or r.get('SiglaIes') or '').strip().upper(),
                inst_name=r.get('NM_ENTIDADE_ENSINO') or r.get('NomeIes'),
                programme=r.get('NM_PROGRAMA') or r.get('NomePrograma'),
                programme_code=r.get('CD_PROGRAMA') or r.get('CodigoPrograma'),
                author=(r.get('NM_DISCENTE') or r.get('Autor') or '').strip(),
                author_capes_id=r.get('ID_PESSOA_DISCENTE') or None,
                advisors=[a.strip() for a in advisors if a and a.strip()],
                advisor_capes_id=r.get('ID_PESSOA_ORIENTADOR') or None,
                title=(r.get('NM_PRODUCAO') or r.get('TituloTese') or '').strip(),
                defence_date=r.get('DT_TITULACAO') or r.get('DataDefesa'),
                language=r.get('NM_IDIOMA') or r.get('Idioma'),
                pages=r.get('NR_PAGINAS') or r.get('NumeroPaginas'),
                keywords=r.get('DS_PALAVRA_CHAVE') or r.get('PalavrasChave'),
                abstract=r.get('DS_RESUMO') or r.get('ResumoTese'),
                abstract_en=r.get('DS_ABSTRACT'),
                # For people only (the browser handoff): sucupira.capes.gov.br disallows crawlers.
                fulltext_url=(r.get('DS_URL_TEXTO_COMPLETO') or r.get('URLTextoCompleto') or '').strip() or None)


def repo_records(out):
    """(source institution, record dict with title/authors/year/url/pdf/raw)."""
    for f in sorted(glob.glob(str(out / 'oai' / '*.jsonl'))):
        inst = Path(f).stem
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            dc = r['dc']
            ids = dc.get('identifier', [])
            url = next((i for i in ids if i.startswith('http')), None)
            years = [int(m) for d in dc.get('date', []) for m in re.findall(r'\b(19[89]\d|20[0-2]\d)\b', d)]
            yield inst, dict(source=f'oai:{inst}', oai_id=r['identifier'], titles=dc.get('title', []),
                             authors=dc.get('creator', []), years=years, url=url, pdf=None,
                             types=dc.get('type', []), rights=dc.get('rights', []))
    usp = out / 'usp' / 'records.jsonl'
    if usp.exists():
        for line in open(usp, encoding='utf-8'):
            r = json.loads(line)
            m = r.get('meta') or {}
            if not m:
                continue
            doi = (m.get('dc.identifier.doi') or [''])[0]
            years = [int(y) for y in re.findall(r'^10\.11606/[TD]\.8\.(\d{4})\.', doi)]
            yield 'USP', dict(source='usp-tde', oai_id=None, titles=m.get('dc.title', []) + m.get('dc.title.alternative', []),
                              authors=m.get('dc.creator', []), years=years, url=r['url'],
                              pdf=r['pdfs'][0] if r.get('pdfs') else None, pdfs=r.get('pdfs', []),
                              types=m.get('dc.type', []), rights=[], doi=doi or None)
    uff = out / 'uff-ppgh' / 'records.jsonl'
    if uff.exists():
        for line in open(uff, encoding='utf-8'):
            r = json.loads(line)
            if not r['level'].lower().startswith('dout'):
                continue
            y = re.findall(r'(19|20)\d\d', r['defence_date'])
            yield 'UFF', dict(source='uff-ppgh', oai_id=None, titles=[r['title']], authors=[r['author']],
                              years=[int(r['defence_date'][-4:])] if y else [], url=r['pdf'], pdf=r['pdf'],
                              types=['doctoralThesis'], rights=[], committee=r['committee'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out)
    docs = list(capes_doctorates(out))
    by_inst = defaultdict(list)
    for i, d in enumerate(docs):
        by_inst[d['inst']].append(i)
    best = {}  # doc index -> (score, record)
    seen = Counter()
    for src, rec in repo_records(out):
        seen[src] += 1
        pool = [i for code in INST.get(src, {src}) for i in by_inst.get(code, [])]
        rtitles = [fold(t) for t in rec['titles'] if t]
        rnames = [name_tokens(n) for n in rec['authors']]
        for i in pool:
            d = docs[i]
            if rec['years'] and not any(abs(y - d['year']) <= 2 for y in rec['years']):
                continue
            dt = fold(d['title'])
            if not dt:
                continue
            score = 0
            if any(t[:60] == dt[:60] for t in rtitles):
                score = 2
            else:
                dn = name_tokens(d['author'])
                same_person = any(len(dn & n) >= 2 for n in rnames)
                if same_person and any(difflib.SequenceMatcher(None, t, dt).ratio() >= 0.85 for t in rtitles):
                    score = 1
            if score and score > best.get(i, (0,))[0]:
                best[i] = (score, rec)
    cands = []
    report = defaultdict(Counter)
    for i, (score, rec) in sorted(best.items()):
        d = docs[i]
        slim = {k: v for k, v in d.items() if k not in ('abstract', 'abstract_en', 'keywords')}  # abstracts stay in capes-raw
        cands.append(dict(slim, key=doc_key(d), match='title' if score == 2 else 'author+fuzzy_title', repository=rec))
        report[rec['source']]['matched'] += 1
    for src, n in seen.items():
        report[f'oai:{src}' if src != 'UFF' else 'uff-ppgh']['records'] += 0
    for d in docs:
        report['capes'][d['inst']] += 1
    (out / 'candidates.json').write_text(json.dumps(cands, ensure_ascii=False, indent=0))
    rep = dict(capes_doctorates=len(docs), matched=len(cands), records_read=dict(seen),
               matched_by_source={k: v['matched'] for k, v in report.items() if k != 'capes'})
    (out / 'match-report.json').write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
