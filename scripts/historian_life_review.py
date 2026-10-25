"""Apply sourced life metadata without altering the historical teaching graph."""
from copy import deepcopy
from datetime import date
import re
from urllib.parse import urlsplit


def year_of(value):
    match = re.match(r'^(-?\d+)', str(value or ''))
    return int(match.group(1)) if match else None


def validate_review(review):
    checked = date.fromisoformat(review['checked_on'])
    seen = set()
    for row in review['people']:
        pid = row['person_id']
        if not pid or pid in seen:
            raise ValueError('Duplicate or missing life-review person: ' + str(pid))
        seen.add(pid)
        status = row['status']
        if status not in ('deceased', 'living', 'unresolved'):
            raise ValueError('Unknown life-review status: ' + pid)
        observed = date.fromisoformat(row['checked_on'])
        if observed > checked:
            raise ValueError('Life review postdates its recorded cutoff: ' + pid)
        if not row.get('identity_rationale') or not row.get('sources'):
            raise ValueError('Life review requires identity and source evidence: ' + pid)
        for source in row['sources']:
            url = urlsplit(source['url'])
            if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password:
                raise ValueError('Unsafe life-review source URL: ' + pid)
            if not source.get('title') or not source.get('support'):
                raise ValueError('Life source needs a title and scoped support: ' + pid)
        death = row.get('death_year')
        if status == 'deceased':
            if type(death) is not int or not 1 <= death <= observed.year:
                raise ValueError('Deceased person needs a supported, nonfuture death year: ' + pid)
            precise = row.get('death_date')
            if precise:
                if year_of(precise) != death:
                    raise ValueError('Death date and year conflict: ' + pid)
                if row.get('death_precision') == 'day' and date.fromisoformat(precise) > observed:
                    raise ValueError('Death date is after the check: ' + pid)
        elif death is not None or row.get('death_date'):
            raise ValueError('Living/unresolved record cannot assert a new death date: ' + pid)
        birth = row.get('birth_year')
        if birth is not None and (type(birth) is not int or birth > (death or observed.year)):
            raise ValueError('Birth year conflicts with life evidence: ' + pid)
    return seen


def overlay_historian_life_review(payload, review, source='data/historian-life-review.json'):
    """Enrich only the published copy; unknown status never becomes 'living'."""
    validate_review(review)
    rows = {r['person_id']: r for r in review['people']}
    applied = 0
    for person in payload.get('people', []):
        row = rows.get(person['id'])
        if row is None:
            continue
        life = deepcopy(person.get('life') or {})
        for key in ('birth', 'death', 'birth_precision', 'death_precision', 'retrieved'):
            life.setdefault(key, None)
        previous = deepcopy(life)
        if row.get('birth_year') is not None:
            # Retain a supported earlier precise date when the fresh check only
            # establishes its year; an actual disagreement requires a decision.
            if life['birth'] and year_of(life['birth']) != row['birth_year']:
                if not row.get('birth_correction'):
                    raise ValueError('Unreviewed birth-year conflict: ' + person['id'])
                life['birth'] = str(row['birth_year'])
                life['birth_precision'] = 'year'
            else:
                if not life['birth']:
                    life['birth'] = str(row['birth_year'])
                    life['birth_precision'] = 'year'
        if life['birth'] and life['birth_precision'] == 'year':
            # Legacy authority exports sometimes encode an unknown month/day
            # as January 1; preserve only the year their precision supports.
            life['birth'] = str(year_of(life['birth']))
        if row['status'] == 'deceased':
            life['death'] = row.get('death_date') or str(row['death_year'])
            life['death_precision'] = row.get('death_precision') or 'year'
        elif row['status'] == 'living' and life['death']:
            raise ValueError('Living status contradicts an existing death record: ' + person['id'])
        life['retrieved'] = row['checked_on']
        person['life'] = life
        person['life_review'] = {
            'status': row['status'], 'checked_on': row['checked_on'],
            'sources': [{k: s[k] for k in ('url', 'title', 'locator', 'support') if k in s}
                        for s in row['sources']],
            'note': row.get('limits', ''),
        }
        if previous != life:
            person['life_review']['previous_dates'] = previous
        applied += 1
    if applied:
        payload.setdefault('published_enrichment', []).append({
            'fields': ['people[].life', 'people[].life_review'],
            'source': source, 'count': applied,
            'note': 'Reviewed life metadata only. Source identities, work chronology, editorial coverage and relationship dates remain unchanged. Missing death data does not establish living status.'})
    return applied


def overlay_theorist_life_review(payload, review):
    """Apply the separately scoped theory review without replacing historian evidence."""
    ids = validate_review(review)
    allowed = {n['id'] for n in payload.get('nodes', [])
               if n.get('entry_kind') == 'person' and n.get('layer') == 'intellectual_connections'}
    if ids - allowed:
        raise ValueError('Theory life review targets a different layer: ' + ', '.join(sorted(ids - allowed)))
    return overlay_historian_life_review(payload, review, source='data/theorist-life-review.json')
