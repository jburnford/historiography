"""Merge explicitly accepted research batches, retaining provisional evidence status."""
import copy
import hashlib
import json
import re
from pathlib import Path
try:
    from .check_journal_classification_batches import check_batch
except ImportError:
    from check_journal_classification_batches import check_batch


def ident(prefix, text):
    return prefix+'_'+hashlib.sha256(text.encode()).hexdigest()[:16]


def merge_batches(catalogue, batches, expected_ids):
    result = copy.deepcopy(catalogue)
    nodes = {n['id']:n for n in result['nodes']}
    sources = {s['id']:s for s in result['sources']}
    rows = {r['id']:r for r in result['subject_classifications']}
    outcomes, batch_ids = {}, set()
    for batch in batches:
        errors = check_batch(batch, result, sources)
        if errors: raise ValueError('; '.join(errors))
        bid = batch['batch_id']
        if bid in batch_ids: raise ValueError('Repeated classification batch ID')
        batch_ids.add(bid)
        touched = {r['journal_id'] for r in batch.get('classifications', [])}
        unresolved = {r['journal_id'] for r in batch.get('unresolved', [])}
        if touched & unresolved: raise ValueError('Journal is both classified and unresolved')
        if set(outcomes) & (touched | unresolved): raise ValueError('Journal occurs in multiple review batches')
        for source in batch.get('sources', []): sources[source['id']] = copy.deepcopy(source)
        for row in batch.get('classifications', []):
            jid, path = row['journal_id'], row['subject_path']
            sid = ident('journal_subject', ' / '.join(path))
            if sid not in nodes:
                nodes[sid] = dict(id=sid, entry_kind='publication_subject', label=path[-1],
                    category_path=path, source_ids=[], atlas_node_ids=[],
                    mapping_note='Subject vocabulary from classification review; consult each classification’s checked/provisional status. No atlas-field correspondence inferred.')
            for ref in row['source_ids']:
                if ref not in nodes[sid]['source_ids']: nodes[sid]['source_ids'].append(ref)
            cid = ident('journal_classification',jid+'|'+sid+'|'+row['basis'])
            if cid in rows: raise ValueError('Classification conflicts with an existing record')
            rows[cid] = dict(id=cid, journal_id=jid, subject_id=sid, basis=row['basis'],
                status=row['status'], source_ids=row['source_ids'], evidence_note=row['evidence_note'],
                reviewed_on=batch['checked_on'], checked_on=batch['checked_on'] if row['status']=='checked' else None,
                review_batch_id=bid)
        for jid in touched:
            statuses = sorted({r['status'] for r in batch['classifications'] if r['journal_id']==jid})
            outcomes[jid] = dict(journal_id=jid,outcome='checked' if statuses==['checked'] else 'provisional' if statuses==['provisional'] else 'mixed',
                reviewed_on=batch['checked_on'],review_batch_id=bid,classification_statuses=statuses)
        for row in batch.get('unresolved', []):
            outcomes[row['journal_id']] = dict(**row,outcome='unresolved',reviewed_on=batch['checked_on'],review_batch_id=bid)
    if set(outcomes) != set(expected_ids):
        raise ValueError(f'Queue mismatch: {len(set(expected_ids)-set(outcomes))} missing, {len(set(outcomes)-set(expected_ids))} unexpected')
    result.update(schema_version='1.1',
        nodes=sorted(nodes.values(),key=lambda r:(r['entry_kind'],r['label'].casefold(),r['id'])),
        sources=list(sources.values()), subject_classifications=list(rows.values()),
        classification_reviews=sorted(outcomes.values(),key=lambda r:r['journal_id']))
    return result


def apply_accepted_batches(catalogue, data_directory):
    directory = Path(data_directory)
    manifest_path = directory/'accepted-subject-batches.json'
    if not manifest_path.exists(): return catalogue
    manifest = json.loads(manifest_path.read_text())
    batches = []
    for entry in manifest['batches']:
        filename = entry['filename']
        if not re.fullmatch(r'sol-\d{3}\.json',filename): raise ValueError('Invalid accepted batch filename')
        raw = (directory/'subject-classification-batches'/filename).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']: raise ValueError('Accepted batch changed: '+filename)
        batches.append(json.loads(raw))
    result = merge_batches(catalogue,batches,manifest['reviewed_journal_ids'])
    source_manifest = directory/'accepted-source-checks.json'
    if source_manifest.exists():
        accepted = json.loads(source_manifest.read_text())
        seen = set()
        for entry in accepted['batches']:
            filename = entry['filename']
            if not re.fullmatch(r'(sol|root)-web-\d{3}\.json', filename) or filename in seen:
                raise ValueError('Invalid or repeated source-check filename')
            seen.add(filename)
            raw = (directory/'source-check-batches'/filename).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=entry['sha256']:
                raise ValueError('Accepted source check changed: '+filename)
            result = merge_source_check(result, json.loads(raw))
    return result


def merge_source_check(catalogue, batch):
    """Replace explicitly reviewed title suggestions; retain their records as history."""
    if any(r.get('status')!='checked' for r in batch.get('classifications', [])):
        raise ValueError('Source-check updates require checked evidence')
    successful = {r['journal_id'] for r in batch.get('classifications', [])}
    replacements = batch.get('replaces_provisional_ids', [])
    rows = {r['id']:r for r in catalogue['subject_classifications']}
    if len(replacements)!=len(set(replacements)):
        raise ValueError('Repeated provisional replacement')
    for rid in replacements:
        if rid not in rows or rows[rid].get('status')!='provisional' or rows[rid]['journal_id'] not in successful:
            raise ValueError('Only successful checks may supersede existing provisional rows')
    base = copy.deepcopy(catalogue)
    base['subject_classifications'] = [r for r in base['subject_classifications'] if r['id'] not in replacements]
    result = merge_batches(base, [batch], batch['reviewed_journal_ids'])
    archive = copy.deepcopy(catalogue.get('superseded_subject_classifications', []))
    archive.extend(dict(copy.deepcopy(rows[rid]), superseded_by_batch=batch['batch_id'],
                        superseded_on=batch['checked_on']) for rid in replacements)
    reviews = {r['journal_id']:copy.deepcopy(r) for r in catalogue.get('classification_reviews', [])}
    history = copy.deepcopy(catalogue.get('classification_review_history', []))
    for review in result['classification_reviews']:
        jid = review['journal_id']
        if jid not in successful:
            continue
        if jid in reviews:
            history.append(dict(reviews[jid], superseded_by_batch=batch['batch_id']))
        statuses = sorted({r.get('status','checked') for r in result['subject_classifications'] if r['journal_id']==jid})
        review.update(outcome='mixed' if len(statuses)>1 else statuses[0], classification_statuses=statuses)
        reviews[jid] = review
    attempts = copy.deepcopy(catalogue.get('source_check_attempts', []))
    attempts.extend(dict(r, review_batch_id=batch['batch_id'], reviewed_on=batch['checked_on'])
                    for r in batch.get('unresolved', []))
    result.update(schema_version='1.2', superseded_subject_classifications=archive,
                  classification_reviews=sorted(reviews.values(),key=lambda r:r['journal_id']),
                  classification_review_history=history, source_check_attempts=attempts)
    return result
