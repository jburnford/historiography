"""Check staged subject research without importing it into the public graph."""
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_batch(batch, catalogue, prior_sources=None):
    errors = []
    journals = {n['id'] for n in catalogue['nodes'] if n['entry_kind']=='periodical'}
    sources = {s['id']:s for s in catalogue['sources']}
    sources.update(prior_sources or {})
    try:
        date.fromisoformat(batch.get('checked_on',''))
    except (ValueError,TypeError):
        errors.append('Batch needs a valid review date')
    if not batch.get('batch_id'):
        errors.append('Batch needs an ID')
    for source in batch.get('sources',[]):
        sid = source.get('id')
        if not sid or not source.get('title') or not source.get('note') or not source.get('verification'):
            errors.append('Source needs identity and scoped verification')
        if not isinstance(source.get('url'),str) or not source['url'].startswith(('https://','http://')):
            errors.append(f'Invalid source URL: {sid}')
        if sid in sources and sources[sid] != source:
            errors.append(f'Conflicting source ID: {sid}')
        try:
            date.fromisoformat(source.get('checked_on',''))
        except (ValueError,TypeError):
            errors.append(f'Research source needs a valid check date: {sid}')
        sources[sid] = source
    seen = set()
    for row in batch.get('classifications',[]):
        jid = row.get('journal_id')
        if jid not in journals:
            errors.append(f'Unknown journal: {jid}')
        path = row.get('subject_path')
        if not isinstance(path,list) or not path or any(not isinstance(x,str) or not x.strip() for x in path):
            errors.append(f'Invalid subject path: {jid}')
            continue
        key = (jid,tuple(path),row.get('basis'))
        if key in seen:
            errors.append(f'Duplicate classification: {jid} / {path}')
        seen.add(key)
        basis,status = row.get('basis'),row.get('status')
        if basis=='title_indicated':
            if status!='provisional': errors.append(f'Title evidence must be provisional: {jid}')
        elif basis in ('publisher_scope','directory_category','library_guide','bibliographic_subject_index'):
            if status!='checked': errors.append(f'Source check must carry checked status: {jid}')
        else:
            errors.append(f'Unsupported classification basis: {jid}')
        if not row.get('evidence_note') or not row.get('source_ids') or any(s not in sources for s in row.get('source_ids',[])):
            errors.append(f'Classification needs evidence and valid sources: {jid}')
        if any(k in row for k in ('relationship_kind','directed','impact_factor')):
            errors.append(f'Subject metadata cannot introduce graph edges or ranking: {jid}')
    for row in batch.get('unresolved',[]):
        if row.get('journal_id') not in journals or not row.get('reason') or not row.get('next_step'):
            errors.append('Unresolved outcome needs known journal, reason and next step')
    return errors


def main():
    catalogue = json.loads((ROOT/'data/journal-catalogue/catalogue.json').read_text())
    paths = sorted((ROOT/'data/journal-catalogue/subject-classification-batches').glob('sol-*.json'))
    prior,errors,counts = {},[],Counter()
    for path in paths:
        batch = json.loads(path.read_text())
        errors.extend(f'{path.name}: {e}' for e in check_batch(batch,catalogue,prior))
        prior.update({s['id']:s for s in batch.get('sources',[])})
        counts.update(r['status'] for r in batch.get('classifications',[]) if 'status' in r)
        counts['unresolved_records'] += len(batch.get('unresolved',[]))
    for error in errors: print('ERROR:',error)
    print(f'{len(paths)} staged batches; classification rows/outcomes: {dict(counts)}; {len(errors)} structural errors.')
    print('No staged data imported. Structural checks do not verify subject accuracy.')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
