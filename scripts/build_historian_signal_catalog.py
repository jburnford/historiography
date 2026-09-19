#!/usr/bin/env python3
"""Make explicit, inspectable metadata-screening decisions for ranking signals.

These are provisional relevance rules, not independently verified awards,
biographies, or assessments of a book's influence. Overrides are editorial.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import unicodedata

try:
    from .rank_wikidata_historians import load
except ImportError:
    from rank_wikidata_historians import load


def normalize(text):
    text = unicodedata.normalize('NFKD', text).casefold()
    return ''.join(c for c in text if not unicodedata.combining(c))


def family(label, qid):
    label = normalize(label)
    label = re.sub(r'\([^)]*\)|\b\d{4}(?:[–-]\d{2,4})?\b|\b\d+(?:st|nd|rd|th)?\s+edition\b', '', label)
    return re.sub(r'\W+', ' ', label).strip() or qid


SOURCE_FAMILIES = [
    (r'brockhaus.*efron', 'brockhaus-efron'),
    (r'great soviet encyclopedia', 'great-soviet-encyclopedia'),
    (r'encyclop[aeæ]*dia britannica', 'britannica'),
    (r'(?:oxford )?dictionary of national biography', 'dictionary-national-biography'),
    (r'vem ar det', 'vem-ar-det'),
    (r'nordisk familjebok', 'nordisk-familjebok'),
    (r'meyers.*(?:lexi|encyclop)', 'meyers'),
    (r'pauly|realencyclopadie', 'pauly-wissowa'),
    (r'russian biographical dictionary', 'russian-biographical-dictionary'),
    (r'biographisches lexikon des kaiserthums', 'austrian-empire-biographical-lexicon'),
    (r'polish biographical dictionary', 'polish-biographical-dictionary'),
    (r'encyclopedia americana', 'encyclopedia-americana'),
    (r'al.?a.?lam|al-zirikli', 'al-alam'),
    (r'biographical dictionary of polish archivists', 'polish-archivists'),
    (r'jewish encyclopedia', 'jewish-encyclopedia'),
]
SELECTED_SOURCES = {
    'Q88584931': 'american-women-historians', 'Q16871348': 'akal-spanish-historians',
    'Q106768773': 'eminent-chinese-qing', 'Q112066824': 'hungarian-museologists',
    'Q113504685': 'al-alam', 'Q117831991': 'lexikon-ceske-literatury',
}
ACADEMY_FAMILIES = [
    (r'british academy', 'british-academy'),
    (r'medieval academy of america', 'medieval-academy-america'),
    (r'real academia de la historia|royal academy of history', 'real-academia-historia'),
    (r'royal historical society', 'royal-historical-society'),
    (r'academie des inscriptions', 'academie-inscriptions'),
]


def classify(prop, key, obj, objects):
    if not re.fullmatch(r'Q\d+', key):
        return False, '', 'unknown_value_not_evidence'
    label = obj.get('label') or obj.get('labelMul') or ''
    text = normalize(label + ' ' + obj.get('description', ''))
    base_family = family(label, key)
    if prop == 'P166':
        if re.search(r'alternate history|alternative history|natural history|historical military|historic person|national historic significance|military decoration', text):
            return False, '', 'award_not_evidence_of_historical_scholarship'
        if re.search(r'\bhistory\b|historian|historical (?:writing|research|scholarship)|historiograph|histoire|historia|geschichte|historien|medieval', text):
            for pattern, name in ACADEMY_FAMILIES:
                if re.search(pattern, text):
                    return True, name, 'history_fellowship_metadata'
            return True, 'award:' + base_family, 'history_award_metadata'
        for pattern, name in ACADEMY_FAMILIES:
            if re.search(pattern, text) and 'fellow' in text:
                return True, name, 'learned_academy_fellowship_metadata'
        return False, '', 'award_relevance_not_established'
    if prop == 'P39':
        if re.search(r'president|chair(?:man|person)?|secretary', text) and re.search(r'(?:histor|histoire).*(?:society|association|academy|congress)|(?:society|association|academy|division|congress).*(?:histor|histoire)', text):
            return True, 'leadership:' + base_family, 'historical_body_leadership_metadata'
        if key == 'Q18692979':
            return True, 'real-academia-historia', 'history_academy_membership_metadata'
        return False, '', 'position_relevance_not_established'
    if prop == 'P463':
        for pattern, name in ACADEMY_FAMILIES:
            if re.search(pattern, text) and name != 'royal-historical-society':
                return True, name, 'selected_learned_academy_membership_metadata'
        # "Historical academy (1724–1917)" can mean a defunct science academy.
        # Require the historical discipline in the body's NAME for this fallback.
        if re.search(r'academia.*historia|academy.*(?:history|historical)|historical academy', normalize(label)) and not re.search(r'young|junior|student|school|university|publisher', text):
            return True, 'academy:' + base_family, 'learned_academy_membership_metadata'
        return False, '', 'ordinary_or_unclassified_membership'
    if prop == 'P1343':
        if re.search(r'wikipedia|wikimedia|secret police|state security|authority (?:collection|file)|library catalog|census|register of|student|alumni', text):
            return False, '', 'catalogue_primary_record_or_nonreference_source'
        if key in SELECTED_SOURCES:
            return True, SELECTED_SOURCES[key], 'selected_biographical_reference_metadata'
        for pattern, name in SOURCE_FAMILIES:
            if re.search(pattern, text):
                return True, name, 'reference_family_metadata'
        if re.search(r'encyclop|encyklop|enzyklop|enciclop|biographical (?:dictionary|reference|lexicon)|national biography|biographisches lexikon|biografisch.*(?:lexi|dict)|allgemeine deutsche biographie|neue deutsche biographie|historian.*dictionary', text):
            return True, 'reference:' + base_family, 'reference_work_metadata'
        return False, '', 'reference_work_relevance_not_established'
    if prop == 'P800':
        context = []
        for field in ('kinds', 'subjects'):
            for uri in filter(None, obj.get(field, '').split('|')):
                other = objects.get(uri.rsplit('/', 1)[-1], {})
                context.append(other.get('label') or other.get('labelMul', ''))
        expanded = text + ' ' + normalize(' '.join(context))
        # Exclude explicit fiction/media before the historical-subject match.
        if re.search(r'\bnovel\b|\bnovella\b|\bfiction\b|\bfantasy\b|\bpoem\b|\bpoetry\b|\bfilm\b|\bmovie\b|\bopera\b|\bpainting\b|disambiguation|\btelevision\b|\bvideo game\b', text) or re.search(r'\bnovel\b|historical fiction|historical novel|poetry collection', normalize(' '.join(context))):
            return False, '', 'fiction_media_or_disambiguation_metadata'
        if re.search(r'\bhistory\b|\bhistorical\b|historiograph|\bhistoire\b|\bhistoria\b|geschichte|\bhistorie\b|\bchronicle\b|\bbiography\b|\bbiographical\b', expanded) and 'natural history' not in expanded:
            return True, 'work:' + base_family, 'historical_work_metadata_not_influence_verified'
        return False, '', 'historical_work_relevance_not_established'
    raise ValueError(prop)


def main(snapshot):
    directory = snapshot / 'ranking'
    objects, signals, _, _ = load(directory)
    used = defaultdict(set)
    for traits in signals.values():
        for prop, keys in traits.items():
            if prop != 'P101':
                used[prop].update(keys)
    overrides_path = directory / 'catalog-overrides.json'
    overrides = {(row['property'], row['qid']): row for row in json.loads(overrides_path.read_text())} if overrides_path.exists() else {}
    decisions = []
    for prop in sorted(used):
        for key in sorted(used[prop], key=lambda k: (not k.startswith('Q'), int(k[1:]) if k.startswith('Q') else k)):
            selected, group, reason = classify(prop, key, objects[key], objects)
            row = {'property': prop, 'qid': key, 'selected': selected, 'family': group,
                   'basis': reason, 'review_status': 'provisional_metadata_screen', 'source_url': ''}
            row.update(overrides.get((prop, key), {}))
            decisions.append(row)
    result = {'version': 1, 'status': 'provisional metadata relevance screen; source passages not checked',
              'decisions': decisions}
    (directory / 'signal-catalog.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Selected', sum(r['selected'] for r in decisions), 'of', len(decisions), 'property/item pairs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    main(parser.parse_args().snapshot)
