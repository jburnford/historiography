"""Prepare final source/qualification corrections without rewriting accepted packets."""
from copy import deepcopy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = '2026-10-25'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    if (ROOT / 'data/production-batches/historian-corrections-1.180/acceptance.json').exists():
        raise ValueError('Accepted packet is frozen; use --check')
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    assert graph['revision_history'][-1]['version'] == '1.179'
    nodes = {n['id']: n for n in graph['nodes']}
    people = {p['id']: p for p in graph['people']}
    old = json.loads((ROOT / 'data/production-batches/person-entries-1.170/acceptance.json').read_text())['prior_records']['people']['sarah_carter']
    restored_note = old['identity_note'] + ' Addendum 2026-10-25: ' + people['sarah_carter']['identity_note']
    sources = [
        {'id': 'hc180_legoff_memory_1988', 'title': 'Jacques Le Goff, Histoire et mémoire: Gallimard Folio histoire manifestation, 25 October 1988.',
         'url': 'https://www.cercle-enseignement.com/Ouvrages/Gallimard/Folio-histoire/Histoire-et-memoire',
         'verification': {'status': 'bibliographic_metadata_checked', 'checked_on': DAY,
           'note': 'Gallimard teaching/publisher metadata identifies Le Goff and the 25 October 1988 Folio manifestation. This dates that French edition/collection, not the original date of every constituent essay or the invention of memory history. Book body unread.'}},
        {'id': 'hc180_katz_poorhouse_1986', 'title': 'Michael B. Katz, In the Shadow of the Poorhouse: A Social History of Welfare in America (Basic Books, 1986): library edition record.',
         'url': 'https://search.worldcat.org/title/In-the-shadow-of-the-poorhouse-%3A-a-social-history-of-welfare-in-America/oclc/1035716388',
         'verification': {'status': 'bibliographic_metadata_checked', 'checked_on': DAY,
           'note': 'Library catalogue describes Basic Books copyright 1986. The retained University of Pennsylvania Press memorial independently credits Katz with the book. Later anniversary editions remain distinct. Metadata only; book body unread.'}},
        {'id': 'hc180_calloway_revolution_1995', 'title': 'Colin G. Calloway, The American Revolution in Indian Country: Crisis and Diversity in Native American Communities (Cambridge University Press, 1995), frontmatter.',
         'url': 'https://www.cambridge.org/core/books/abs/american-revolution-in-indian-country/frontmatter/9147F7F8E1DB0D07B6B27963DE02402A',
         'verification': {'status': 'bibliographic_metadata_checked', 'checked_on': DAY,
           'note': 'Publisher frontmatter metadata credits Colin G. Calloway and print publication 1995, separately from online publication 2014. No book-body interpretation or new relationship is inferred.'}},
        {'id': 'hc180_corbin_translation_1986', 'title': 'Alain Corbin, The Foul and the Fragrant (1986): Wellcome Collection bibliographic translation concordance.',
         'url': 'https://wellcomecollection.org/works/h8phtv63',
         'verification': {'status': 'bibliographic_metadata_checked', 'checked_on': DAY,
           'note': 'Library metadata identifies the English 1986 translation of Le Miasme et la Jonquille, whose French original is 1982. This supports work/translation concordance only. The frozen dissertation French key with English label is not relabelled or silently assigned to a single edition; no counts are summed.'}},
    ]
    draft = {'prepared': DAY, 'status': 'proposal_for_review', 'proposed_edges': [],
        'new_sources': sources, 'people_identity_notes': {'sarah_carter': restored_note}}
    cfg = {'revision': '1.180', 'baseline_revision': '1.179', 'date': DAY,
        'batch_dir': 'historian-corrections-1.180', 'persons': [], 'extras': ['corrections'],
        'authorization': 'User explicitly requested the full qualifying historian expansion, life-date review, and earlier Astra review/corrections followed by push. This final additive correction preserves accepted source packets and restores qualifications before publication.',
        'summary': 'Restore Carter’s prior identity qualification; distinguish Iacovetta’s own 2019 article from the narrower Gatekeepers review; add three metadata-only reading selections and Corbin translation concordance without new people or arrows.',
        'rationale': 'All earlier acceptance packets remain frozen. Corrected attribution is explained through a directly read own article, while bibliographic witnesses supply dates and credits only. Original/edition/component dates, authority cautions and current dissertation source labels remain distinct.',
        'text_revisions': [], 'field_sets': [], 'node_list_additions': []}
    iaco = nodes['franca_iacovetta']
    new_description = 'A Canadian historian of gender, migration and class. Gatekeepers examines how everyday institutions tried to reshape newcomers in Cold War Canada, as characterized by Basok and Bastable’s review. Her own 2019 article separately examines women’s activism and negotiated cultural assertions in mediated social-work files, with uneven power and unknown outcomes. Her editorial collaborations retain their joint credit.'
    cfg['text_revisions'].append({'node': 'franca_iacovetta', 'field': 'description',
                                 'old': iaco['description'], 'new': new_description})
    more_scope = ' Gatekeepers is characterized through Basok/Bastable pp. 211–213 only for institutional gatekeeping. Claims about negotiation and gender/family ideals draw on Iacovetta’s own 2019 article, selected pp. 29–32 and 35–42, not the review’s treatment of another author. These social-work case files are mediated, outcomes are often unknown, and the Institute mainly served European newcomers; no universal account or complete monograph reading is asserted.'
    cfg['text_revisions'].append({'node': 'franca_iacovetta', 'field': 'scope_note',
        'old': iaco['scope_note'], 'new': iaco['scope_note'] + more_scope})
    additions = [
        ('franca_iacovetta', 'hc180_iacovetta_article_2019', 2019,
         '“Writing Women’s Community-based Pluralism into the History of Canadian Multiculturalism”',
         'publication', 'contributions', ['hc178_iacovetta_primary_2019'],
         'Original Zeitschrift für Kanada-Studien 39 (2019), 28–45; selected own passages checked, not a 2021 upload date.',
         ' “Writing Women’s Community-based Pluralism into the History of Canadian Multiculturalism” (2019; selected pp. 29–32 and 35–42 read).'),
        ('jacques_le_goff', 'hc180_legoff_memory_edition_1988', 1988,
         'Histoire et mémoire: French Folio manifestation', 'edition', 'editions', ['hc180_legoff_memory_1988'],
         'Publisher identifies this 1988 manifestation; no single original date is assigned to all its essays.',
         ' Histoire et mémoire (1988 French Folio manifestation; edition/collection metadata only, body unread).'),
        ('michael_b_katz', 'hc180_katz_poorhouse_1986', 1986,
         'In the Shadow of the Poorhouse', 'publication', 'contributions', ['hc180_katz_poorhouse_1986', 'hc175_michael_b_katz_2'],
         'Basic Books 1986 library metadata and publisher memorial author credit; later anniversary editions remain distinct. Book body unread.',
         ' In the Shadow of the Poorhouse: A Social History of Welfare in America (Basic Books, 1986; metadata only, later anniversary editions distinct).'),
        ('colin_g_calloway', 'hc180_calloway_revolution_1995', 1995,
         'The American Revolution in Indian Country', 'publication', 'contributions', ['hc180_calloway_revolution_1995'],
         'Publisher print year 1995, distinct from online publication 2014; frontmatter metadata only.',
         ' The American Revolution in Indian Country: Crisis and Diversity in Native American Communities (1995 print; metadata only, book body unread).'),
    ]
    for nid, eid, year, label, kind, track, refs, support, reading in additions:
        node = nodes[nid]; chronology = deepcopy(node['chronology'])
        chronology['events'].append({'id': eid, 'label': label, 'kind': kind, 'track': track,
            'date': {'year': year, 'precision': 'year'}, 'source_ids': ['graph:' + s for s in refs],
            'support': support})
        chronology['prepared_on'] = DAY
        cfg['field_sets'].append({'node': nid, 'field': 'chronology', 'expect': node['chronology'], 'value': chronology})
        old_reading = node['representative_figures_and_works']
        cfg['text_revisions'].append({'node': nid, 'field': 'representative_figures_and_works',
                                     'old': old_reading, 'new': old_reading + reading})
        cfg['node_list_additions'].append({'node': nid, 'field': 'source_ids', 'values': refs})
    cfg['node_list_additions'].append({'node': 'alain_corbin', 'field': 'source_ids',
                                      'values': ['hc180_corbin_translation_1986']})
    write(HERE / 'corrections/entry-draft.json', draft)
    write(HERE / 'batch.json', cfg)
    write(HERE / 'review-notes.json', {'prepared': DAY, 'scope': 'Astra final corrections and explicit reading-bridge bibliographic selections.',
        'carter_prior_note': old['identity_note'], 'carter_new_note_as_addendum': people['sarah_carter']['identity_note'],
        'iacovetta': 'Own 2019 article supplies the negotiation/family argument; the named review supports only the narrower Gatekeepers characterization.',
        'metadata_limits': 'Three named selections and one translation concordance are metadata-only. No new arrows, body readings or dissertation count/label merges.',
        'unresolved_life_case': 'Jennifer S. H. Brown remains unresolved; absence of a death record is not living evidence.'})


if __name__ == '__main__':
    main()
