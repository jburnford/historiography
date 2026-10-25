"""Prepare this packet only; canonical application belongs to the coordinator."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
P = Path(__file__).resolve().parent
G = ROOT / 'historiography-1920-2000.json'
g = json.loads(G.read_text())
nodes = {n['id']: n for n in g['nodes']}
DAY = '2026-10-25'
assert g['revision_history'][-1]['version'] == '1.168'
assert 'sven_beckert' not in nodes

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def source(sid, title, url, note, status='supporting_page_checked'):
    return dict(id=sid, title=title, citation=title, url=url,
                verification=dict(status=status, checked_on=DAY, note=note))

S = dict(monied='dc169_beckert_monied_2001', cotton='dc169_beckert_cotton_metadata',
         lse='dc169_beckert_lse_2019', harvard='dc169_beckert_growthpolicy_2020',
         slavery='dc169_beckert_rockman_2016', capitalism='dc169_beckert_capitalism_2025')
sources = [
    source(S['monied'], 'Sven Beckert, The Monied Metropolis: New York City and the Consolidation of the American Bourgeoisie, 1850–1896 (Cambridge University Press, 2001), selected introduction and front matter.',
           'https://assets.cambridge.org/97805217/90390/excerpt/9780521790390_excerpt.pdf',
           'Official excerpt: introductory printed pp. 1–9 read; principal claim locators pp. 2–3 (formation of a coherent upper class), 4–5 (Civil War and changing political alignments), 6–9 (capital ownership, class relations, institutions and contingent class formation). This records the author’s research problem and argument; later case chapters and original archival records remain unread. Official front matter https://assets.cambridge.org/97805217/90390/frontmatter/9780521790390_frontmatter.pdf, PDF p. 4, states copyright 2001 and First published 2001, hardback ISBN 9780521790390 and paperback ISBN 9780521524100. A later paperback release is not the work’s first publication.'),
    source(S['cotton'], 'Sven Beckert, Empire of Cotton (2014): Harvard Weatherhead institutional bibliography, with publisher format dates.',
           'https://www.wcfia.harvard.edu/publications/empire-cotton',
           'Institutional bibliography identifies Beckert and dates the work 2014 (New York: Random House). Current publisher https://www.penguinrandomhouse.com/books/10461/empire-of-cotton-by-sven-beckert/ separately lists ebook 2 December 2014 and Vintage paperback 10 November 2015. Existing cd_beckert_cotton_2014 retains the 2014 Knopf citation and the limited authorised excerpt reading; neither that source nor its prize qualification is overwritten. This new record is metadata only; its institutional abstract and promotional endorsements are not treated as an independent reading.',
           'bibliographic_metadata_checked'),
    source(S['lse'], 'Tom Wilkinson, interview with Sven Beckert on Empire of Cotton, LSE South Asia blog (18 October 2019; Jaipur Literature Festival 2019 conversation).',
           'https://blogs.lse.ac.uk/southasia/2019/10/18/jlf-2019-interview-sven-beckert-empire-of-cotton/',
           'Interview body read from locally retrieved publisher HTML. Use Beckert’s answer to the question about choosing “war capitalism”: he distinguishes it from merchant/mercantile capitalism, explains armed trade, dispossession and enslavement, and describes states empowering merchants and companies. His account says the term came late in writing Empire of Cotton; the 2019 post is a retrospective explanation, not the term’s first appearance. The first South Asia answer was also read, but regional empirical claims are attributed to him rather than independently verified. Interviewer’s questions are separate. Browser renderer returned 429; direct retrieval yielded the complete dated article, retained locally with hash. Publication day is not asserted as interview delivery day.'),
    source(S['harvard'], 'Devjani Roy, GrowthPolicy interview with Sven Beckert, “Sven Beckert on inequality, jobs, and capitalism” (Harvard Kennedy School, August 2020).',
           'https://www.hks.harvard.edu/centers/mrcbg/programs/growthpolicy/sven-beckert-inequality-jobs-and-capitalism',
           'Interview body read from locally retrieved institutional HTML. Principal scope: Beckert’s second answer, beginning with the familiar Western-centred account and moving to global connections, the preindustrial history of capitalism, state formation and regional variety; opening of third answer returns to The Monied Metropolis and Gilded Age inequality. The methodological phrase “connected diversity” is Beckert’s own in answer 2. Current inequality statistics, policy forecasts and claims about future employment are not used. August 2020 is the displayed publication date; no exact delivery date is inferred. Browser renderer returned 403; complete institutional HTML was directly readable and is retained locally with hash.'),
    source(S['slavery'], 'Sven Beckert and Seth Rockman, eds., Slavery’s Capitalism: A New History of American Economic Development (University of Pennsylvania Press, 2016).',
           'https://www.pennpress.org/9780812248418/slaverys-capitalism/',
           'Publisher title, explicit joint editorial credit and contents checked. Hardcover ISBN 9780812248418 published 5 September 2016; ebook ISBN 9780812293098 published 28 July 2016; paperback is 6 February 2018. Collection body and jointly authored introduction remain unread in this packet. Publication fact only: the publisher’s general argument summary does not establish that Beckert individually wrote every contributor’s claims.',
           'bibliographic_metadata_checked'),
    source(S['capitalism'], 'Sven Beckert, Capitalism (Penguin Press, 25 November 2025), publisher publication record.',
           'https://www.penguinrandomhouse.com/books/541160/capitalism-by-sven-beckert/',
           'Publisher author/title, imprint Penguin Press, hardcover ISBN 9780735220836 and 25 November 2025 publication checked; ebook and audio formats also list that day. Title transcribed as displayed by this publisher. Book text, sample, citations and critical reception unread. Metadata supports one dated publication event and further reading only; none of the new substantive relationships is inferred from this unread book or its promotional copy.',
           'bibliographic_metadata_checked')]

def event(eid, label, year, sids, support, kind='publication'):
    return dict(id=eid, label=label, kind=kind, track='contributions',
                date=dict(year=year, precision='year'),
                source_ids=['graph:' + s for s in sids], support=support)

events = [
    event('dc169_sb_monied_2001', 'The Monied Metropolis: class formation in New York, 1850–1896', 2001, [S['monied']], 'Official copyright leaf states First published 2001. Introductory pp. 1–9 read; no claim to have checked the full archival argument.'),
    event('dc169_sb_cotton_2014', 'Empire of Cotton', 2014, [S['cotton'], 'cd_beckert_cotton_2014'], 'Institutional bibliography and publisher ebook metadata establish 2014; the 2015 Vintage paperback is a later format. Existing authorised-excerpt reading and limitations retained.'),
    event('dc169_sb_rockman_2016', 'With Seth Rockman, eds., Slavery’s Capitalism', 2016, [S['slavery']], 'Joint editorship, hardcover September 2016 and ebook July 2016 verified; collection and joint introduction unread here.', 'edited_volume'),
    event('dc169_sb_lse_2019', 'LSE interview: explaining the choice of “war capitalism”', 2019, [S['lse']], 'Posted 18 October 2019 after a Jaipur 2019 conversation. Own answer explains an argument already published in 2014; publication and delivery dates are not conflated.', 'interview'),
    event('dc169_sb_harvard_2020', 'GrowthPolicy interview: capitalism as connected diversity', 2020, [S['harvard']], 'Institutional page dates interview publication August 2020. Answer 2 supplies a first-person explanation of global method; forecasts in other answers are not adopted.', 'interview'),
    event('dc169_sb_capitalism_2025', 'Capitalism (Penguin Press): publication fact', 2025, [S['capitalism']], 'Publisher verifies 25 November 2025. Body and sample unread; this event does not imply a new reading or established reception.')]

node = dict(id='sven_beckert', label='Sven Beckert', layer='historians', period=None,
    hunt_core_paradigm=False, entry_kind='person', entry_type='Individual historian',
    date_label='The Monied Metropolis (2001) · Empire of Cotton (2014) · with Seth Rockman, Slavery’s Capitalism (2016) · interviews (2019, 2020) · Capitalism (2025, metadata only)',
    description='Studies the social and political making of capitalism across urban and global scales. The Monied Metropolis asks how New York’s divided capital-owning elites formed a coherent bourgeoisie through institutions, culture and political conflict. Empire of Cotton’s “war capitalism” stresses the connections among armed trade, land expropriation, enslavement and state power. His later first-person explanations advocate tracing relations among different regions and forms of labour rather than assuming one Western path. These are attributed historical arguments: Hilt questions parts of the industrialisation explanation, while Burnard and Riello contest the chronology and emphasis of the new history of capitalism. The existing debate entry retains those disagreements in detail.',
    representative_figures_and_works='The Monied Metropolis: New York City and the Consolidation of the American Bourgeoisie, 1850–1896 (2001; introduction pp. 1–9 read); Empire of Cotton: A Global History (2014; existing authorised excerpt and later author interviews); with Seth Rockman, eds., Slavery’s Capitalism: A New History of American Economic Development (2016; joint editorial credit checked, collection unread); LSE interview with Tom Wilkinson (2019) and Harvard GrowthPolicy interview with Devjani Roy (2020), selected methodological answers; Capitalism (Penguin Press, 2025; publication metadata only).',
    source_ids=list(S.values()) + ['cd_beckert_cotton_2014', 'cd_hilt_2017', 'cd_burnard_riello_2020'],
    scope_note='Promotes the existing roster identity sven_beckert without replacing its identity note or assigning external identifiers, life dates or a career interval. Fresh substantive reading comprises Monied Metropolis introduction pp. 1–9 and the author’s 2019/2020 interview answers; original archives, full books, the Slavery’s Capitalism introduction and Capitalism (2025) remain unread. Criticism uses the existing partial-source witnesses: Hilt pp. 516–517 and Burnard/Riello abstract and selected pages, with their recorded reading limits unchanged. Hilt’s doubts about mechanisms and Burnard/Riello’s global/Atlantic critique remain distinct; Baptist-specific torture/productivity charges are not attributed to Beckert. The three relationships record contributions, not proven transmission to every practitioner, a field origin or consensus. Later publication facts do not extend any field’s review boundary.',
    chronology=dict(version=1, label='Selected writings and explanations · 2001–2025',
        selection_note='Selected dated works and interviews, not lifespan, career boundaries or a field origin. The 2025 item is metadata only.',
        events=events, intervals=[], continuation=dict(status='not_asserted', basis='No continuous duration or ending is established by these publications.'),
        interpretation='Each event retains its source scope. Different publication formats and interview posting dates are distinguished.',
        prepared_on=DAY, editorial_record='data/production-batches/person-entries-1.169/acceptance.json'))

def edge(pid, target, label, relationship, note, sids):
    return dict(proposal_id=pid, source='sven_beckert', target=target, type='connection',
        relationship_kind='contribution', directed=True, map_label=label,
        relationship=relationship, evidence_note=note, source_ids=sids,
        classification_basis='editorial_review', roster_row=target)

edges = [
    edge('dc169_sb_urban', 'urbanhistory', 'Urban institutions and bourgeois class formation',
         'Reconstructs how New York’s divided capital-owning elites became a more coherent bourgeoisie through institutions, cultural practices and political conflict (The Monied Metropolis, 2001).',
         'Author’s introduction pp. 2–3 and 6–9 read. Shared wealth does not automatically explain common identity or political power; class formation is the historical problem. This contribution brings elite formation into urban/social history without claiming Beckert founded the field or that the complete book’s cases have been independently verified.', [S['monied']]),
    edge('dc169_sb_capitalism', 'capitalismdebates', 'War capitalism: violence, land, labour and states',
         'Contributes “war capitalism” as an account of the violent trading, land and labour arrangements from which industrial capitalism developed (Empire of Cotton, 2014; author’s explanation, 2019).',
         'The authorised excerpt remains the existing limited book witness; Beckert’s LSE answer on the term was freshly read. His historical claim about links among armed trade, dispossession, enslavement and state power is attributed, not accepted as a settled causal explanation of industrialisation. The existing Hilt and Burnard/Riello partial readings and the new_history_of_capitalism strand retain their criticisms. Baptist-specific productivity claims are not assigned to Beckert.', [S['lse'], 'cd_beckert_cotton_2014', 'cd_hilt_2017', 'cd_burnard_riello_2020']),
    edge('dc169_sb_global', 'global', 'Capitalism through connected regional diversity',
         'Explains a global method that relates merchants, plantations and manufacturing across regions, treating capitalism as connected diversity rather than a single preordained path (GrowthPolicy interview, 2020).',
         'Beckert’s second answer was read: comparative regional sites and linked labour regimes support this account of his method. A first-person research strategy does not establish universal adoption, prove every regional empirical claim, or derive a new argument from the unread 2025 book. The field’s prior approaches, Benton addition and review boundary remain intact.', [S['harvard']])]

rosters = [
    dict(node='urbanhistory', row=dict(person_id='sven_beckert', role='historian',
        context='Examines how economic elites made a coherent urban upper class through institutions, cultural practices and politics; selected introduction read.',
        works='The Monied Metropolis (2001), introduction pp. 1–9', source_ids=[S['monied']], basis='source_review')),
    dict(node='global', row=dict(person_id='sven_beckert', role='contributor',
        context='First-person explanation of global capitalism through relations among diverse regions, forms of labour and states; a selected method, with original regional cases unverified here.',
        works='Empire of Cotton (2014; existing excerpt); GrowthPolicy interview (2020), answer 2', source_ids=[S['harvard'], 'cd_beckert_cotton_2014'], basis='source_review'))]
strands = [
    dict(node='urbanhistory', strand=dict(id='dc169_bourgeois_class_formation', title='Urban elites and the formation of a bourgeoisie',
        focus='Beckert makes the coherence of New York’s capital-owning elites a historical question. Institutions, cultural boundaries and political conflicts help explain how a shared class identity was made. This selected introduction adds an urban elite-formation problem alongside existing histories of neighbourhoods, mobility and racial inequality; it does not replace them.',
        person_ids=['sven_beckert'], works='The Monied Metropolis (2001), introduction pp. 1–9', source_ids=[S['monied']], basis='editorial_distinction')),
    dict(node='global', strand=dict(id='dc169_connected_capitalisms', title='Capitalism as connected regional diversity',
        focus='In his 2020 methodological answer Beckert relates regional differences and connections: merchants, plantations, manufacturing and state power belong in the same global inquiry. His account resists treating Europe’s industrialisation as the whole history of capitalism. This strand records his stated strategy; the empirical adequacy of its global applications and criticism of the cotton argument remain open.',
        person_ids=['sven_beckert'], works='GrowthPolicy interview with Devjani Roy (2020), answer 2; Empire of Cotton (2014, existing limited excerpt)', source_ids=[S['harvard'], 'cd_beckert_cotton_2014'], basis='editorial_distinction'))]

field_events = {
    'urbanhistory': [event('dc169_urban_monied_2001', 'Beckert, The Monied Metropolis: selected later scholarship', 2001, [S['monied']], 'Introduction pp. 1–9 and official first-publication statement read. The field’s prior chronology and review boundary are preserved.')],
    'global': [event('dc169_global_interview_2020', 'Beckert: global capitalism as connected diversity, author interview', 2020, [S['harvard']], 'Own methodological answer 2 read. This selected later witness is not a new field origin or an extension of the field’s review-through year.', 'interview')]
}
field_sets = []
for target, additions in field_events.items():
    prior = deepcopy(nodes[target]['chronology'])
    value = deepcopy(prior)
    value['events'] += deepcopy(additions)
    if 'selected additional scholarship' not in value['label']:
        value['label'] += ' · selected additional scholarship'
    value['selection_note'] += ' Additive Beckert selection; all prior events and field coverage remain.'
    value['prepared_on'] = DAY
    value['editorial_record'] = 'data/production-batches/person-entries-1.169/acceptance.json'
    field_sets.append(dict(node=target, field='chronology', expect=prior, value=value))

appends = {
    'urbanhistory': ' Sven Beckert, The Monied Metropolis (2001), selected introduction on urban bourgeois class formation.',
    'global': ' Sven Beckert, GrowthPolicy interview (2020), answer 2 on global capitalism as connected diversity; later selected scholarship.'}
cfg = dict(revision='1.169', baseline_revision='1.168', date=DAY, batch_dir='person-entries-1.169', persons=['sven_beckert'], extras=[],
    summary='Promote existing Sven Beckert roster identity to the main timeline with six dated works/interviews and three scoped contributions. Add The Monied Metropolis to urban history and a first-person global-method strand; retain the existing capitalism debate and its critics. Capitalism (2025) is metadata only.',
    authorization='User explicitly identified Beckert as missing from the live main timeline. Coordinator assigned this bounded 1.169 packet on baseline 1.168. Packet preparation and review only; coordinator applies the canonical change. No publication requested.',
    rationale='Roster and named-work reading coverage did not supply an individual main-timeline entry. Selected author passages and interviews ground substantial content separately from dissertation frequency. Existing identities, collective arrows, critical qualifications and field coverage are preserved.',
    source_merges={}, edge_revisions={}, new_strands=strands, field_sets=field_sets,
    roster_list_additions=[dict(node='capitalismdebates', person_id='sven_beckert', source_ids=[S['lse'], S['harvard'], S['slavery'], S['monied'], S['capitalism']], works_append='The Monied Metropolis (2001; selected introduction); Capitalism (2025, metadata only)')],
    text_revisions=[dict(node=nid, field='representative_figures_and_works', old=nodes[nid]['representative_figures_and_works'], new=nodes[nid]['representative_figures_and_works'] + text) for nid, text in appends.items()],
    node_list_additions=[dict(node='urbanhistory', field='source_ids', values=[S['monied']]), dict(node='global', field='source_ids', values=[S['harvard']]), dict(node='capitalismdebates', field='source_ids', values=[S['lse'], S['slavery'], S['monied'], S['capitalism']])])
draft = dict(status='proposal_for_review', prepared=DAY, review_status='needs_review',
    applies_to='Revision 1.168 to 1.169: existing roster identity promoted; coordinator applies after review.',
    node=node, people_update=dict(id='sven_beckert', node_id='sven_beckert'),
    proposed_edges=edges, new_sources=sources, source_addenda={}, roster_additions=rosters,
    edges_considered_not_proposed=[
        'Keep edge_1089 dependency → capitalismdebates: primarily Frank/ReOrient, with named-reader Beckert comparison in its note; not a Beckert-only edge.',
        'Keep edge_1091 eric_williams → capitalismdebates: several named heirs and arguments; not a Beckert-only transmission edge.',
        'Keep edge_1093 quant → capitalismdebates: collective economic-historian response, including Baptist-specific productivity criticism. No wholesale retarget to Beckert.',
        'No direct Williams → Beckert, world-systems → Beckert or Pomeranz → Beckert influence inferred from thematic similarity or mediated comparison.',
        'No personal critic promotion or fresh criticism edge from an unread complete article. Existing named critics, partial-source notes and field arrows remain visible.'])
write(P / 'batch.json', cfg)
write(P / 'sven_beckert/entry-draft.json', draft)
write(P / 'chronology-additions.json', dict(read_graph_revision=g['revision_history'][-1]['version'], read_graph_sha256=hashlib.sha256(G.read_bytes()).hexdigest(), events_by_node=field_events,
    instruction='Append exactly these events when rebasing; preserve Benton and all earlier events, selection qualifications and coverage. Main capitalismdebates already contains beckert_2014 and receives no duplicate book event.'))

raw = P / 'sven_beckert/research'
urls = {
    'monied-frontmatter.pdf': 'https://assets.cambridge.org/97805217/90390/frontmatter/9780521790390_frontmatter.pdf',
    'monied-excerpt.pdf': 'https://assets.cambridge.org/97805217/90390/excerpt/9780521790390_excerpt.pdf',
    'lse-2019.html': sources[2]['url'], 'harvard-interview.html': sources[3]['url']}
witnesses = [dict(local_only_file=str((raw / name).relative_to(P)), bytes=(raw / name).stat().st_size,
    sha256=hashlib.sha256((raw / name).read_bytes()).hexdigest(), url=url) for name, url in urls.items()]
notes = dict(prepared=DAY, person_id='sven_beckert', intended_baseline_revision='1.168',
    identity_status='Existing sven_beckert reused. No new identity or changed identity_note; node_id is the sole people update.',
    scope='Selected historical writing and first-person explanations. No complete biography, whole-book reading, field origin or continuous career asserted.',
    primary_readings=[dict(source_id=s['id'], url=s['url'], reading_scope=s['verification']['note']) for s in sources],
    local_only_witnesses=witnesses, local_only_policy='Raw PDFs, extracted text and HTML are ignored under sven_beckert/research/. Only metadata, hashes, locators and scoped summaries enter the reviewable packet.',
    claim_locators=[
        dict(claim='Urban bourgeois class formation', source_id=S['monied'], locator='Printed introduction pp. 2–3, 6–9', qualification='Author’s problem and proposed explanation; later chapters and original records unread.'),
        dict(claim='War capitalism, armed trade, dispossession, enslavement and state-backed merchants', source_id=S['lse'], locator='Beckert answer to question asking why he coined war capitalism', qualification='2019 retrospective explanation of the 2014 argument, not first coinage in 2019.'),
        dict(claim='Global research method and connected diversity', source_id=S['harvard'], locator='Question/answer 2: from familiar Western account through concluding connected-diversity paragraph', qualification='First-person method; regional empirical cases and policy forecasts not independently adopted.')],
    publication_distinctions=[
        dict(work='The Monied Metropolis', decision='First published 2001, official copyright leaf PDF p. 4; later paperback format does not replace work date.'),
        dict(work='Empire of Cotton', decision='2014 work year, supported by institutional bibliography and publisher ebook date. Vintage paperback 2015 remains distinct; existing Knopf source untouched.'),
        dict(work='Slavery’s Capitalism', decision='Joint editors Sven Beckert AND Seth Rockman; hardcover 5 September 2016 and ebook 28 July 2016. Collection body and joint introduction unread.'),
        dict(work='Capitalism', decision='Penguin Press hardcover 25 November 2025, ISBN 9780735220836. Metadata-only event and bibliography, with no argument or reception claim from unread book.')],
    preserved_reception=dict(source_ids=['cd_hilt_2017', 'cd_burnard_riello_2020', 'cd_olmstead_rhode_2018'],
        existing_research='data/extension-2026/capitalism-debate-2026-10-18/evidence-slavery-capitalism.md, sections 1f–1i and SC-8',
        qualification='Existing partial-reading witnesses reused without expanding their scope. Hilt pp. 516–517 distinguishes supported and doubtful mechanisms; Burnard/Riello abstract and pp. 225–228, 232–233 provide a distinct global/Atlantic critique. Olmstead/Rhode 2018 body remains unread. Baptist-specific claims are not transferred to Beckert.'),
    edge_audit=draft['edges_considered_not_proposed'],
    dissertation_lead=dict(author_first_author_dated=112, work_dated_dissertations={'The Monied Metropolis': 26, 'Empire of Cotton': 63},
        basis='Coordinator-supplied verified frozen-canon counts for this task; not recomputed during packet preparation. Work and author sets overlap and are not added. Counts prioritize review, not agreement or influence.'),
    prior_coverage='capitalismdebates roster, new_history_of_capitalism strand and beckert_2014 chronology already present. A dissertation named-work reading bridge also exists; none substitutes for a main-timeline person entry.',
    application='No canonical, website, shared-script, documentation or publication changes made by this packet builder.')
write(P / 'sven_beckert/research-notes.json', notes)
print('Prepared Beckert:', len(sources), 'sources,', len(edges), 'edges,', len(events), 'personal facts,', len(strands), 'strands')
