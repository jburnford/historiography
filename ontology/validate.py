"""Validate the ontology prototype using only Python's standard library.

This checks the declared structural/semantic contract, never historical truth.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def validate(data, contract, base=ROOT):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def index(collection):
        result = {}
        for row in data.get(collection, []):
            identifier = row.get('id')
            require(bool(identifier) and identifier not in result,
                    f'{collection}: missing or duplicate id {identifier}')
            result[identifier] = row
        return result

    entities, sources, claims = (index(k) for k in ('entities', 'source_records', 'claims'))
    require(data.get('schema_version') == contract['version'], 'schema version mismatch')
    require(isinstance(data.get('fixture_only'), bool), 'fixture_only must be explicit')
    all_ids = list(entities) + list(sources) + list(claims)
    require(len(all_ids) == len(set(all_ids)), 'IDs must be unique across entity, claim and source namespaces')

    def date_bounds(value, where):
        if not isinstance(value, dict):
            errors.append(f'{where}: date requires a precision-bearing object')
            return None
        precision, literal = value.get('precision'), value.get('value')
        require(isinstance(value.get('approximate'), bool), f'{where}: approximate must be explicit')
        try:
            if precision == 'year' and isinstance(literal, str) and len(literal) == 4:
                year = int(literal)
                return dt.date(year, 1, 1), dt.date(year, 12, 31)
            if precision == 'day' and isinstance(literal, str):
                day = dt.date.fromisoformat(literal)
                return day, day
        except (ValueError, TypeError):
            pass
        errors.append(f'{where}: invalid or unsupported date/precision')
        return None

    def evidence(items, where):
        require(isinstance(items, list) and bool(items), f'{where}: evidence required')
        for item in items if isinstance(items, list) else []:
            require(item.get('source_record_id') in sources, f'{where}: unknown evidence source')
            for key in ('locator', 'support', 'scope'):
                require(bool(item.get(key)), f'{where}: evidence {key} required')

    def review(value, where):
        require(value.get('status') in contract['review_statuses'], f'{where}: invalid review status')
        require(bool(value.get('rationale')), f'{where}: review rationale required')
        if value.get('status') in ('accepted', 'rejected'):
            require(bool(value.get('reviewer')), f'{where}: reviewed decision needs reviewer')
            try:
                dt.date.fromisoformat(value.get('reviewed_on', ''))
            except (ValueError, TypeError):
                errors.append(f'{where}: reviewed decision needs date')

    for identifier, entity in entities.items():
        require(entity.get('type') in contract['entity_types'], f'{identifier}: unknown entity type')
        require(bool(entity.get('label')), f'{identifier}: label required')
        if entity.get('type') == 'concept':
            kinds = entity.get('concept_kind', [])
            require(isinstance(kinds, list) and bool(kinds) and
                    all(k in contract['concept_kinds'] for k in kinds), f'{identifier}: invalid concept kind')
        else:
            require('concept_kind' not in entity, f'{identifier}: only concepts have concept kinds')

    for identifier, source in sources.items():
        require(bool(source.get('provider')), f'{identifier}: source provider required')
        require(bool(source.get('url') or source.get('snapshot_path')), f'{identifier}: source location required')
        try:
            observed = dt.datetime.fromisoformat(source.get('observed_at', ''))
            require(observed.tzinfo is not None, f'{identifier}: observation timezone required')
        except (ValueError, TypeError):
            errors.append(f'{identifier}: invalid observation time')
        if source.get('snapshot_path'):
            path = (base / source['snapshot_path']).resolve()
            require(path.is_relative_to(base.resolve()) and path.is_file(),
                    f'{identifier}: missing or out-of-scope snapshot')
        for upstream in source.get('derived_from', []):
            require(upstream in sources and upstream != identifier, f'{identifier}: invalid upstream source')

    def acyclic(graph, description):
        visiting, done = set(), set()

        def visit(identifier):
            if identifier in visiting:
                errors.append(f'{description}: cycle at {identifier}')
                return
            if identifier in done:
                return
            visiting.add(identifier)
            for child in graph.get(identifier, []):
                visit(child)
            visiting.remove(identifier)
            done.add(identifier)

        for identifier in graph:
            visit(identifier)

    acyclic({k: v.get('derived_from', []) for k, v in sources.items()}, 'source provenance')
    for mapping in data.get('identity_mappings', []):
        require(mapping.get('entity_id') in entities, 'identity mapping: unknown entity')
        require(mapping.get('source_record_id') in sources, 'identity mapping: unknown source')
        require(bool(mapping.get('scheme')) and bool(mapping.get('value')), 'identity mapping: scheme/value required')
        require(entities.get(mapping.get('entity_id'), {}).get('type') != 'atlas_entry',
                'identity mapping: atlas entry is not an external entity identity')
        review(mapping.get('review', {}), 'identity mapping')

    for identifier, claim in claims.items():
        subject = entities.get(claim.get('subject'), {})
        predicate = contract['predicates'].get(claim.get('predicate'))
        require(bool(subject), f'{identifier}: unknown subject')
        require(bool(predicate), f'{identifier}: unknown predicate')
        require(bool(claim.get('attributed_to')), f'{identifier}: attribution required')
        require(claim.get('basis') in contract['bases'], f'{identifier}: invalid basis')
        review(claim.get('review', {}), identifier)
        evidence(claim.get('evidence'), identifier)
        require('valid_time' in claim, f'{identifier}: historical validity must be explicit or null')
        if predicate:
            require(subject.get('type') in predicate['subject_types'], f'{identifier}: subject type not allowed')
            obj = claim.get('object')
            if isinstance(obj, dict):
                require('date' in predicate['object_types'], f'{identifier}: date object not allowed')
                date_bounds(obj, identifier)
            else:
                target = entities.get(obj, {})
                require(bool(target), f'{identifier}: unknown object')
                require(target.get('type') in predicate['object_types'], f'{identifier}: object type not allowed')
                if 'object_concept_kinds' in predicate:
                    require(bool(set(target.get('concept_kind', [])) & set(predicate['object_concept_kinds'])),
                            f'{identifier}: object concept kind not allowed')
                if claim.get('predicate') == 'exact_match':
                    require(bool(set(subject.get('concept_kind', [])) & set(target.get('concept_kind', []))),
                            f'{identifier}: exact match requires compatible concept kinds')
            if predicate.get('requires_qualification'):
                require(bool(claim.get('qualification')), f'{identifier}: qualification required')
            if 'allowed_bases' in predicate:
                require(claim.get('basis') in predicate['allowed_bases'], f'{identifier}: basis not allowed for predicate')
        interval = claim.get('valid_time')
        if interval is not None:
            if not isinstance(interval, dict):
                errors.append(f'{identifier}: invalid historical interval')
            else:
                evidence(interval.get('evidence'), identifier + ' historical interval')
                start = date_bounds(interval['start'], identifier) if interval.get('start') else None
                end = date_bounds(interval['end'], identifier) if interval.get('end') else None
                require(bool(start or end), f'{identifier}: unknown interval should be null')
                require(not start or not end or start[0] <= end[1], f'{identifier}: reversed historical interval')
        if claim.get('basis') == 'inference':
            require(bool(claim.get('premises')) and bool(claim.get('rule_id')), f'{identifier}: inference needs rule and premises')
            for premise in claim.get('premises', []):
                require(premise in claims and premise != identifier, f'{identifier}: unknown/self premise')
            if claim.get('review', {}).get('status') == 'accepted':
                require(claim.get('rule_id') in contract['enabled_inference_rules'], f'{identifier}: inference rule not enabled')
                require(all(claims.get(p, {}).get('review', {}).get('status') == 'accepted'
                            for p in claim.get('premises', [])), f'{identifier}: inference has unaccepted premise')
        if claim.get('review', {}).get('status') == 'accepted':
            scopes = {e.get('scope') for e in claim.get('evidence', [])}
            if claim.get('predicate') == 'member_of':
                require('membership_record' in scopes, f'{identifier}: explicit membership evidence required')
            if claim.get('predicate') in ('research_connection', 'uses_approach'):
                require(bool(scopes & {'passage', 'inherited_editorial', 'explicit_field_statement'}),
                        f'{identifier}: interpretive connection requires appropriately scoped evidence')

    acyclic({k: v.get('premises', []) for k, v in claims.items()}, 'claim premises')
    for case in data.get('cases', []):
        require(bool(case.get('question')), 'case requires competency question')
        require(all(c in claims for c in case.get('claim_ids', [])), 'case references unknown claim')
    return errors


def accepted_claims(data):
    """Review-state view only; callers must validate and honor fixture_only."""
    return [c for c in data['claims'] if c['review']['status'] == 'accepted']


def production_claims(data):
    if data.get('fixture_only'):
        raise ValueError('Ontology fixture cannot be exported as production data')
    errors = validate(data, json.loads((ROOT / 'contract.json').read_text()))
    if errors:
        raise ValueError('; '.join(errors))
    return accepted_claims(data)


if __name__ == '__main__':
    data = json.loads((ROOT / 'cases.json').read_text())
    errors = validate(data, json.loads((ROOT / 'contract.json').read_text()))
    for error in errors:
        print(error)
    print(f'{len(data["cases"])} cases; {len(data["claims"])} claims; {len(errors)} contract errors; fixture only')
    raise SystemExit(bool(errors))
