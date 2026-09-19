"""Additional constraints for the versioned 0.2 research contract.

The frozen 0.1 validator and its fixtures remain unchanged.
"""
import datetime as dt
from ontology.validate import validate as validate_base


def validate(data, contract, base):
    errors = validate_base(data, contract, base)
    entities = {e['id']: e for e in data['entities']}
    if data.get('status') != 'staging_only' or data.get('fixture_only') is not True:
        errors.append('Research 0.2 is staging-only; production migration is not implemented.')
    for source in data['source_records']:
        work = source.get('describes_work')
        if work and entities.get(work, {}).get('type') != 'work':
            errors.append(f'{source["id"]}: source witness must describe a known work')
    for claim in data['claims']:
        rule = contract['predicates'].get(claim['predicate'], {})
        if not rule.get('requires_statement'):
            continue
        for key in ('statement', 'history', 'intervention_year'):
            if not claim.get(key):
                errors.append(f'{claim["id"]}: {key} required')
        year = claim.get('intervention_year')
        if type(year) is not int or not 1 <= year <= 9999:
            errors.append(f'{claim["id"]}: intervention_year must be an explicit year')
        for ev in claim['evidence']:
            for key in ('check_status', 'checked_on', 'limitation', 'support_assessment'):
                if not ev.get(key):
                    errors.append(f'{claim["id"]}: citation {key} required')
            scopes = {'passage_checked': 'passage', 'abstract_checked': 'abstract',
                      'metadata_checked': 'metadata', 'description_checked': 'metadata',
                      'indexed_excerpt_checked': 'metadata'}
            if ev.get('check_status') not in scopes or ev.get('scope') != scopes.get(ev.get('check_status')):
                errors.append(f'{claim["id"]}: citation check status/scope mismatch')
            try:
                dt.date.fromisoformat(ev.get('checked_on', ''))
            except (ValueError, TypeError):
                errors.append(f'{claim["id"]}: invalid citation check date')
        if claim['review']['status'] == 'accepted':
            if not any(e.get('check_status') in ('passage_checked', 'abstract_checked')
                       and e.get('support_assessment') not in (None, 'not_established')
                       for e in claim['evidence']):
                errors.append(f'{claim["id"]}: metadata cannot establish an interpretive relation')
    return errors
