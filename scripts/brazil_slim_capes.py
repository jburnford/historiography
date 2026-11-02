#!/usr/bin/env python3
"""Slim copy of the CAPES History rows for the repository (Brazil expansion, 2026-11-02).

``capes_catalogue_harvest.py`` writes the History rows of the CAPES catalogue, all levels and all
columns including abstracts, to ``<out>/capes-raw/`` (169 MB; kept out of git and moved to E:
like the French ABES export). This writes ``<out>/capes/<year>.jsonl`` with the doctorate rows
only and the columns the matcher, the browser handoff and the ingest adapter read (no abstracts),
plus a copy of the harvest log. ``brazil_match_capes.capes_doctorates`` reads either.

    python3 scripts/brazil_slim_capes.py --out data/field-research/brazil-theses-2026-10-31 [--raw DIR]
"""
import argparse
import json
import shutil
from pathlib import Path

KEEP = (
    # 2013 on
    'AN_BASE', 'CD_PROGRAMA', 'NM_PROGRAMA', 'SG_ENTIDADE_ENSINO', 'NM_ENTIDADE_ENSINO', 'ID_PRODUCAO_INTELECTUAL',
    'NM_PRODUCAO', 'DT_TITULACAO', 'ID_PESSOA_DISCENTE', 'NM_DISCENTE', 'NM_GRAU_ACADEMICO', 'NM_ORIENTADOR',
    'ID_PESSOA_ORIENTADOR', 'NM_AREA_CONHECIMENTO', 'NM_AREA_AVALIACAO', 'NR_PAGINAS', 'NM_IDIOMA',
    'DS_PALAVRA_CHAVE', 'DS_URL_TEXTO_COMPLETO',
    # 1987-2012
    'AnoBase', 'CodigoPrograma', 'NomePrograma', 'SiglaIes', 'NomeIes', 'Autor', 'TituloTese', 'Nivel', 'DataDefesa',
    'AreaConhecimento', 'AreaAvaliacao', 'NumeroPaginas', 'Idioma', 'PalavrasChave', 'URLTextoCompleto',
    'Orientador_1', 'Orientador_2', 'Orientador_3', 'Orientador_4',
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--raw', help='raw rows (default <out>/capes-raw)')
    a = ap.parse_args()
    out = Path(a.out)
    raw = Path(a.raw) if a.raw else out / 'capes-raw'
    slim = out / 'capes'
    slim.mkdir(exist_ok=True)
    total = 0
    for f in sorted(raw.glob('*.jsonl')):
        if f.stem == 'harvest-log':
            shutil.copyfile(f, slim / f.name)
            continue
        rows = []
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            if (r.get('NM_GRAU_ACADEMICO') or r.get('Nivel') or '').upper() == 'DOUTORADO':
                rows.append({k: r[k] for k in KEEP if r.get(k)})
        (slim / f.name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
        total += len(rows)
    print(f'{total} doctorate rows written to {slim}')


if __name__ == '__main__':
    main()
