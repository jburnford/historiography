#!/usr/bin/env python3
"""Build a review-only promotion packet from fixed editorial decisions and witnesses.

No production writer, authority acceptance, or automatic roster-to-edge conversion.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate

PACKET = ROOT / 'data/extension-2026/promotions-01'
OBSERVED = '2026-09-19T00:10:41+00:00'
DAY = '2026-09-18'  # Local research date, America/Regina.


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# A selected intervention is not a lifespan, a field's origin, or a complete career.
WORKS = {
    'scott': ('work:scott_gender_1986', 'Gender: A Useful Category of Historical Analysis', 1986, ['joan_wallach_scott'], 'scott_gender_1986'),
    'davis': ('work:davis_margins_1995', 'Women on the Margins: Three Seventeenth-Century Lives', 1995, ['natalie_zemon_davis'], 'davis_margins'),
    'hunt': ('work:hunt_introduction_1989', 'Introduction: History, Culture, and Text', 1989, ['lynn_hunt'], 'hunt_culture_intro_primary'),
    'family': ('work:davidoff_hall_family_fortunes_1987', 'Family Fortunes: Men and Women of the English Middle Class 1780–1850', 1987, ['leonore_davidoff', 'catherine_hall'], 'family_fortunes'),
    'higginbotham': ('work:higginbotham_metalanguage_1992', 'African-American Women’s History and the Metalanguage of Race', 1992, ['evelyn_brooks_higginbotham'], 'higginbotham_race'),
    'smith': ('work:smith_decolonizing_1999', 'Decolonizing Methodologies: Research and Indigenous Peoples', 1999, ['linda_tuhiwai_smith'], 'smith_decolonizing'),
    'daston': ('work:daston_galison_image_1992', 'The Image of Objectivity', 1992, ['lorraine_daston', 'peter_galison'], 'daston_galison_image'),
}

SELECTION = [
    ('joan_wallach_scott', 'scott',
     'Develops gender as a historical analysis of social relationships and power. Her 1986 formulation connects symbols, normative claims, institutions and subjectivity while insisting on historical variation.',
     'Existing cross-field presence warrants a visible argument, not just another name in a roster. This draft covers the 1986 intervention; later experience and secularism arguments need their own claims.'),
    ('natalie_zemon_davis', 'davis',
     'Uses contrasting seventeenth-century lives to investigate religion, writing and relations of power across Europe and its colonial outposts. Women on the Margins makes individual lives a route into broader historical questions.',
     'Comparative biography provides a connection beyond gender history. This draft is supported by a newly checked book description; its methodological interpretation still needs a fresh body-text check. Other career contributions remain in the preserved contexts.'),
    ('lynn_hunt', 'hunt',
     'Reassesses the explanatory models of social history in her introduction to The New Cultural History. She recognizes turns toward culture within Marxist and Annales histories while questioning the priority assigned to social experience.',
     'Connects the cultural turn to disputes within social explanation. Hunt authored this introduction and edited the collection; she did not author all its essays. Her political-culture work remains a separate inherited context.'),
    ('catherine_hall', 'family',
     'With Leonore Davidoff, relates English middle-class formation to gender, family, religion and economic life in Family Fortunes. Class identities and gender relations are investigated together rather than in separate historical accounts.',
     'Equal coauthor credit with Davidoff. The 1987 work is distinct from Hall’s later introduction and later imperial history. Newly checked evidence is the indexed prologue abstract and publisher description of a later edition.'),
    ('leonore_davidoff', 'family',
     'With Catherine Hall, makes family and gender central to the history of English middle-class formation in Family Fortunes. The study connects social identities with institutions, economic opportunities and domestic relations.',
     'Equal coauthor credit with Hall; both resolve to one work. Do not infer that either scholar wrote a particular passage alone. The original intervention dates to 1987, not the reissue consulted here.'),
    ('evelyn_brooks_higginbotham', 'higginbotham',
     'Argues that race structures the meanings of gender, class and sexuality. Her 1992 intervention challenges insufficient racial analysis in feminist theory and develops an account of race as socially constructed, contested power.',
     'A theoretical contribution within Black history as well as feminist historiography. Her opening acknowledges useful feminist resources and earlier Black scholarship; it does not license an indiscriminate critique edge to every cited theorist.'),
    ('linda_tuhiwai_smith', 'smith',
     'Places research within colonial histories and Indigenous struggles over knowledge and self-determination. Decolonizing Methodologies addresses the responsibilities, community relationships and authority involved in research with Indigenous peoples.',
     'Connects Indigenous historical authority with the politics of research. This is a situated methodological programme, not a claim that Indigenous research is uniform or that every Western method is rejected.'),
    ('lorraine_daston', 'daston',
     'With Peter Galison, investigates changing scientific ideals of objectivity through images and atlas-making. Their 1992 article distinguishes mechanical objectivity from other historically formed components of the concept.',
     'Adds a substantive history-of-science contribution beyond gender history. Galison retains equal authorship and argument credit. Their historical analysis does not assert that scientific objectivity is simply impossible.'),
]


def build():
    baseline = json.loads((ROOT / 'data/extension-2026/baseline.json').read_text())
    if digest(ROOT / baseline['graph_path']) != baseline['graph_sha256']:
        raise ValueError('Production graph differs from the reviewed baseline; re-review before rebuilding.')
    graph = json.loads((ROOT / baseline['graph_path']).read_text())
    people = {p['id']: p for p in graph['people']}
    nodes = {n['id']: n for n in graph['nodes']}
    sources = {s['id']: s for s in graph['sources']}
    batch = {'schema_version': '0.2', 'fixture_only': True, 'status': 'staging_only',
             'production_graph_imports': 0, 'entities': [], 'source_records': [], 'claims': [],
             'identity_mappings': [], 'as_of': DAY}
    entities = {}

    def entity(identifier, label, kind, **extra):
        if identifier not in entities:
            entities[identifier] = {'id': identifier, 'label': label, 'type': kind, **extra}
        return identifier

    def person(pid):
        if pid in people:
            return entity('person:' + pid, people[pid]['label'], 'person', legacy_person_id=pid,
                          identity_status='existing_local_identity; no new external match')
        if pid == 'patricia_hill_collins':
            return entity('candidate-person:' + pid, 'Patricia Hill Collins', 'person',
                          identity_status='new local referent named by Smith; external authority unresolved')
        raise ValueError(pid)

    def strand(address):
        parent, sid = address.split('/')
        row = next(s for s in nodes[parent]['strands'] if s['id'] == sid)
        return entity('concept:' + address, row['title'], 'concept', concept_kind=['topic'],
                      legacy_strand_address=address,
                      qualification='Addressable research concept for this particular strand; not the entire teaching umbrella.')

    def concept(key, label):
        return entity('candidate-concept:' + key, label, 'concept', concept_kind=['topic'],
                      identity_status='scoped local topic proposal, not an accepted external equivalence')

    for key, (wid, title, year, authors, legacy) in WORKS.items():
        entity(wid, title, 'work', first_publication_year=year, legacy_source_ids=[legacy],
               identity_status='local work proposal; manifestation/authority reconciliation pending',
               author_ids=[person(p) for p in authors],
               date_note='Original intervention year; neither edition date nor field origin.')

    def witness(key, provider, url, raw, note):
        batch['source_records'].append({
            'id': 'witness:promotions01:' + key, 'provider': provider, 'url': url,
            'snapshot_path': 'data/extension-2026/promotions-01/raw/' + raw,
            'observed_at': OBSERVED, 'observed_at_note': 'Batch assembly timestamp; local checks on 18 September 2026.',
            'describes_work': WORKS[key][0], 'access_note': note})

    witness('scott', 'Warwick-hosted primary article scan',
            'https://warwick.ac.uk/fac/arts/history/students/modules/archive/sexuality_and_the_body/bibliography/joan_scott_gender_1986.pdf',
            'scott-selected.pdf', 'Printed 1067–1068 retained; OCR plus visual check of 1067. No whole-article check asserted.')
    witness('davis', 'ACLS Humanities EBook / Fulcrum',
            'https://www.fulcrum.org/concern/monographs/44558d48n', 'davis_family_open.txt',
            'Overview and contents only; book reader restricted. Platform lists 1997 manifestation. 1995 copyright and 1997 printing are separately visible in primary_search.txt; no later-edition redating of work.')
    witness('hunt', 'Reposted UC Press primary introduction scan',
            'https://horomicos.wordpress.com/wp-content/uploads/2018/10/652_hunt_cult_hist.pdf',
            'hunt-selected.pdf', 'Title page and printed introduction 1–5 retained; OCR read. 1989 metadata corroborated in hunt_publisher.txt and primary_search.txt. Introduction authorship differs from collection editorship.')
    witness('family', 'Taylor & Francis indexed prologue abstract and Routledge description',
            'https://www.taylorfrancis.com/chapters/mono/10.4324/9780203605097-7/prologue-leonore-davidoff-catherine-hall',
            'davis_search.txt', 'ABSTRACT read in indexed primary publisher result; direct opening returned footer only (davis_family_open.txt). Later-edition witness; original 1987 date confirmed by Routledge. No full prologue or later introduction checked.')
    witness('higginbotham', 'Wooster-hosted primary Signs article scan',
            'https://blackwomenintheblackfreedomstruggle.voices.wooster.edu/wp-content/uploads/sites/210/2019/01/EBH_The-Metalanguage-of-Race.pdf',
            'higginbotham-selected.pdf', 'Printed 251–253 retained. Initial PDF text clipped words; claims use fresh raster OCR of complete pages. Page 252 visually checked.')
    witness('smith', 'University of Bergen-hosted primary book scan',
            'https://www.uib.no/sites/w3.uib.no/files/attachments/smith_decolonizing_methodologies_compressed.pdf',
            'smith-selected.pdf', 'Copyright and introduction 1–5 retained. Pages 2–5 visually checked alongside OCR; 1999 first publication/second impression distinguished.')
    witness('daston', 'Galison Harvard author-hosted primary article',
            'https://galison.scholars.harvard.edu/sites/g/files/omnuum9431/files/andrewhsmith/files/daston-imageobjectivity-1992.pdf',
            'daston.txt', 'Selected extracted text. Use complete scope paragraph on 81 and opening paragraph on 82 only; other extracted lines are clipped. Both authors credited.')

    def claim(key, subj, pred, obj, work, statement, qualification, locator, status='passage_checked', attribution=None):
        year = WORKS[work][2]
        scope = {'passage_checked':'passage', 'abstract_checked':'abstract',
                 'description_checked':'metadata', 'metadata_checked':'metadata'}[status]
        c = {'id':'claim:promotions01:' + key, 'subject':subj, 'predicate':pred, 'object':obj,
             'statement':statement, 'attributed_to': attribution or 'Editorial interpretation of the named author(s), with the scope stated below',
             'basis':'source_assertion' if pred == 'authored' else 'editorial_interpretation',
             'qualification':qualification, 'intervention_year':year, 'valid_time':None,
             'review':{'status':'needs_review', 'rationale':'Concrete editorial proposal; no automatic acceptance from roster presence, citation count or this check.'},
             'history':[{'on':DAY,'status':'needs_review','action':'Proposed from the specifically recorded witness and locator.'}],
             'evidence':[{'source_record_id':'witness:promotions01:' + work,
                          'locator':locator, 'scope':scope, 'support':statement,
                          'check_status':status, 'checked_on':DAY,
                          'support_assessment':'limited_description_support' if status == 'description_checked' else 'supports_scoped_proposal',
                          'limitation':qualification}]}
        batch['claims'].append(c)
        return c['id']

    loc = {'scott':'Printed 1067–1068; selected PDF pages 1–2',
           'davis':'Overview and author heading, lines 30–48 of captured Fulcrum page',
           'hunt':'Title page and printed introduction 1–5; selected PDF pages 1–4',
           'family':'Prologue ABSTRACT in indexed publisher result; first Routledge result for original year and both credits',
           'higginbotham':'Printed 251–253; selected PDF pages 1–3',
           'smith':'Copyright and introduction 1–5; selected PDF pages 1–4',
           'daston':'Author heading and printed 81 scope paragraph, 82 opening paragraph; captured lines 44–74'}
    status = {k: ('abstract_checked' if k == 'family' else 'description_checked' if k == 'davis' else 'passage_checked') for k in WORKS}
    for key, (wid, title, year, authors, legacy) in WORKS.items():
        for pid in authors:
            claim('authored_' + pid + '_' + key, person(pid), 'authored', wid, key,
                  people[pid]['label'] + ' is credited as ' + ('a coauthor' if len(authors)>1 else 'author') + ' of this work.',
                  'Credit identifies the work; it does not establish influence, exclusive authorship of a passage, or agreement by acknowledged readers.',
                  loc[key], 'metadata_checked')

    # Independent historical claims. No relation is inferred from node promotion.
    claim('scott_gender', person('joan_wallach_scott'), 'contributes_to', strand('gender/gender'), 'scott',
          'Scott proposes gender as a historical analysis of social relationships and power.',
          'Selected formulation only; no generic causal influence on all gender history.', loc['scott'])
    claim('foucault_scott', person('foucault'), 'contributes_to', WORKS['scott'][0], 'scott',
          'Scott explicitly draws on Foucault’s dispersed conception of power.',
          'A bounded conceptual resource identified by Scott on 1067; neither exclusive derivation nor wholesale adherence.', 'Printed 1067, paragraph before definition and note 36')
    claim('rosaldo_scott', person('michelle_rosaldo'), 'contributes_to', WORKS['scott'][0], 'scott',
          'Scott uses Rosaldo’s emphasis on meanings acquired through concrete social interaction.',
          'Specific acknowledged conceptual resource; Rosaldo remains queryable without a teaching node.', 'Printed 1067, opening paragraph and note 35')
    claim('davis_biography', person('natalie_zemon_davis'), 'contributes_to', strand('biography/comparative_margins'), 'davis',
          'Davis connects three contrasting lives with religious, social and colonial settings.',
          'Description supports the proposed comparative-biography scope; body-text verification remains outstanding. No new Certeau/Foucault borrowing or narrative-revival influence inferred.', loc['davis'], status['davis'])
    claim('hunt_culture', person('lynn_hunt'), 'contributes_to', concept('cultural_social_explanation', 'Cultural interpretation and the explanatory priorities of social history'), 'hunt',
          'Hunt assesses the movement toward cultural explanation within Marxist and Annales histories.',
          'Introduction 1–5 only; a scoped topic within the cultural-history discussion, not every strand of the culture umbrella.', 'Printed introduction 1–5')
    claim('hunt_priority', WORKS['hunt'][0], 'qualifies', concept('priority_social_experience', 'The explanatory priority assigned to social experience in Marxist cultural history'), 'hunt',
          'Hunt recognizes Thompson’s cultural mediation while questioning the continuing priority of productive relations and social experience.',
          'Her critique is of a stated explanatory ordering, not a claim that Thompson ignored culture. Do not convert this into an unqualified rejection of Marxism.', 'Printed introduction 4–5')
    for pid in ['catherine_hall','leonore_davidoff']:
        claim(pid + '_class', person(pid), 'contributes_to', strand('social/gender_family_class'), 'family',
              people[pid]['label'] + ', jointly with the other author of Family Fortunes, connects class formation with gender and family.',
              'Joint argument; later-edition prologue abstract only. 1780–1850 is the studied period, 1987 the original intervention, not a historical validity interval.', loc['family'], status['family'])
    claim('family_gender', WORKS['family'][0], 'contributes_to', strand('gender/class_family'), 'family',
          'Family Fortunes treats class and gender as interacting dimensions of English middle-class formation.',
          'One joint work shared by both authors and both field contexts; not two independent confirmations. Later-edition abstract, with original year corroborated separately.', loc['family'], status['family'])
    claim('higginbotham_race', person('evelyn_brooks_higginbotham'), 'contributes_to', strand('black/racial_analysis'), 'higginbotham',
          'Higginbotham develops race as a metalanguage shaping gender, class and sexuality and as a contested instrument of power.',
          'Her opening programme combines feminist theory with Black intellectual traditions; no single undifferentiated school affiliation.', 'Printed 252–253')
    claim('higginbotham_critique', WORKS['higginbotham'][0], 'critiques', concept('feminist_race_omission', 'Insufficient racial analysis in the feminist theory addressed by Higginbotham in 1992'), 'higginbotham',
          'Higginbotham challenges feminist accounts that acknowledge women of colour without integrating race into their analysis.',
          'Her wording admits exceptions and credits useful feminist resources. Footnote 1 does not establish a personal critique of Scott or Butler.', 'Printed 251–252')
    for pid in ['darlene_clark_hine','carroll_smith_rosenberg']:
        claim(pid + '_feedback', person(pid), 'contributes_to', WORKS['higginbotham'][0], 'higginbotham',
              'Higginbotham thanks ' + people[pid]['label'] + ' for reading an earlier version and offering intellectual feedback.',
              'Acknowledged feedback, not coauthorship or agreement with every claim; no teaching-node promotion required.', 'Printed 251, acknowledgment before note 1')
    claim('smith_authority', person('linda_tuhiwai_smith'), 'proposes_programme', strand('indigenous/methods'), 'smith',
          'Smith places research protocols and control over knowledge within Indigenous self-determination and specific community histories.',
          'Introduction 1–5 only; research authority is not identical to all Indigenous historical practices or all identity politics.', 'Introduction 1–5, especially printed 4–5')
    claim('collins_smith', person('patricia_hill_collins'), 'contributes_to', WORKS['smith'][0], 'smith',
          'Smith invokes Patricia Hill Collins’s outsider-within positioning in discussing Indigenous researchers’ institutional and community relationships.',
          'Explicit named conceptual resource on page 5; the cited Collins work and external person authority have not been reconciled. Not a claim of coauthorship or universal identity of experiences.', 'Introduction printed 5')
    for pid in ['lorraine_daston','peter_galison']:
        claim(pid + '_objectivity', person(pid), 'contributes_to', strand('science/objectivity_images'), 'daston',
              people[pid]['label'] + ', jointly with the other author, historicizes mechanical objectivity through scientific image-making.',
              'Joint article, with scope concentrated on atlas-making and late nineteenth-century ideals. Neither sole authorship nor a complete history of objectivity.', 'Printed 81 final paragraph and 82 opening paragraph; complete extracted paragraphs only')
    claim('objectivity_scope', WORKS['daston'][0], 'qualifies', concept('unitary_objectivity', 'Objectivity understood as a single historically invariant ideal'), 'daston',
          'Daston and Galison distinguish historically layered components of objectivity.',
          'They explicitly set aside adjudicating whether objectivity exists. No automatic SSK association or general relativist position follows.', 'Printed 82 opening paragraph, captured lines 59–74')

    proposals = []
    for pid, key, description, note in SELECTION:
        if people[pid].get('node_id') or pid in nodes:
            raise ValueError('Already promoted or node ID occupied: ' + pid)
        wid, title, year, authors, legacy = WORKS[key]
        aid = entity('entry-proposal:' + pid, people[pid]['label'], 'atlas_entry', proposed_node_id=pid)
        claim('presents_' + pid, aid, 'entry_presents', person(pid), key,
              'Propose a teaching entry for ' + people[pid]['label'] + ' centred on the stated intervention.',
              note, loc[key], status[key], 'Editorial selection, not an assertion made by the historical author')
        contexts = []
        for n in graph['nodes']:
            for r in n.get('representative_people', []):
                if r['person_id'] == pid:
                    contexts.append({'kind':'roster','entry_id':n['id'],'record':copy.deepcopy(r)})
            for s in n.get('strands', []):
                if pid in s['person_ids']:
                    contexts.append({'kind':'strand','address':n['id']+'/'+s['id'],'record':copy.deepcopy(s)})
        node = {'id':pid, 'label':people[pid]['label'], 'date_label':f'Selected intervention · {year}',
                'layer':'intellectual_connections', 'period':None, 'hunt_core_paradigm':False,
                'description':description, 'representative_figures_and_works':f'{title} ({year}). ' + ('Joint work; retain all coauthor credits.' if len(authors)>1 else ''),
                'source_ids':[legacy], 'entry_kind':'person', 'entry_type':'Individual thinker or historian',
                'scope_note':note}
        person_ref = person(pid)
        related = [c['id'] for c in batch['claims'] if c['subject'] in (person_ref, wid, aid) or c['object'] == wid]
        proposals.append({'person_id':pid, 'status':'needs_review', 'node':node, 'work_ids':[wid],
                          'claim_ids':related, 'date_semantics':'Selected work date, not career boundary or field origin.',
                          'legacy_person_record':copy.deepcopy(people[pid]), 'legacy_contexts':contexts,
                          'authority_review':'No QID accepted; gender classifications not imported.'})
    batch['entities'] = list(entities.values())
    errors = validate(batch, json.loads((ROOT/'ontology/contract-v0.2.json').read_text()), ROOT)
    if errors:
        raise ValueError('\n'.join(errors))
    historical = [c for c in batch['claims'] if c['predicate'] not in ('authored','entry_presents')]
    rels = {'status':'staging_only','production_graph_imports':0,
            'note':'These are research relationships with addressable work/concept endpoints, not legacy umbrella edges. Node promotion is independent.',
            'relationships':historical}
    tasks = [
        {'id':'davis_body','person_id':'natalie_zemon_davis','action':'Read and preserve prologue/conclusion passages before accepting the comparative-biography interpretation. Preserve the imaginary status of the prologue dialogue; no invented historical meeting.'},
        {'id':'family_original','person_ids':['catherine_hall','leonore_davidoff'],'action':'Check original or reliably aligned prologue/body pages; separate 1987 argument from later introductions. Review separate-spheres objections independently.'},
        {'id':'scott_thompson','person_id':'joan_wallach_scott','action':'Retain edge_313 and edge_314. Check a precise Scott–Thompson critique passage before proposing an individually attributed replacement/addition; no automatic critique from roster role.'},
        {'id':'hunt_politics','person_id':'lynn_hunt','action':'Freshly check 1984 political-culture passages for separate political-history links; current read covers the 1989 introduction only.'},
        {'id':'collins_identity','person_id':'patricia_hill_collins','action':'Reconcile person and the exact work cited by Smith. Named reference is a local candidate, not an accepted QID.'},
        {'id':'balance_next','action':'Continue with remaining pre-2000 Black, Indigenous, postcolonial, economic, labour and other contributions; the eleven zero-woman fields and missing non-European historians remain open. Do not let Anglo-American accessible texts become the default canon.'},
    ]
    output = {'batch.json':batch, 'node-proposals.json':{'status':'staging_only','proposals':proposals},
              'relationship-proposals.json':rels, 'remaining-checks.json':tasks}
    for name, data in output.items():
        (PACKET/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    return batch, proposals, historical


def manifest():
    inputs = [ROOT/'historiography-1920-2000.json', ROOT/'seminar-pathways.json', ROOT/'data/extension-2026/baseline.json',
              ROOT/'ontology/contract.json', ROOT/'ontology/contract-v0.2.json',
              ROOT/'ontology/validate.py', ROOT/'ontology/validate_research.py', Path(__file__),
              ROOT/'scripts/validate_promotion_batch.py', ROOT/'tests/test_promotion_batch.py']
    files = inputs + sorted(p for p in PACKET.rglob('*') if p.is_file() and p.name != 'manifest.json')
    data = {'status':'staging_only','as_of':DAY,'production_graph_imports':0,
            'files':{str(p.relative_to(ROOT)):digest(p) for p in files}}
    (PACKET/'manifest.json').write_text(json.dumps(data,indent=2)+'\n')


if __name__ == '__main__':
    b, p, h = build()
    manifest()
    print(f'{len(p)} node proposals; {len(WORKS)} works; {len(h)} historical claims; {len(b["claims"])} total claims; no production writes')
