"""Claude's independent verification overlay for the timeline-canon packets (2026-10-31).

The user judged both researcher passes too fast and asked Claude to take over. Every
edge, factual sentence and new source was re-checked against the source by an allowed
route (verify-batch{1,2,3}.json in this folder record the passages, quotes and
failures). This file writes claude-review.json, which apply-quality-upgrades.py applies
after the researcher upgrades.

Rules applied:
- An edge stands when its passage was read in this verification, or when it rests on an
  atlas source whose reading was accepted in an earlier revision.
- An edge resting only on a new source that no one could open here (bot checks,
  paywalls, 403s) is re-cited to a source that was read, or held.
- Descriptions state the person's best-known argument plainly. Reading limits stay in
  scope_note, not in the public text.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY = '2026-10-31'
VER = 'Claude verification 2026-10-31'


def src(id, title, url, note, status='supporting_page_checked'):
    return dict(id=id, title=title, citation=title, url=url,
                verification=dict(status=status, checked_on=DAY, note=note))


def edge(pid, source, target, relationship, kind, source_ids, note, etype=None, directed=True):
    return dict(proposal_id=pid, source=source, target=target, relationship=relationship,
                type=etype or ('critique' if kind == 'critique' else 'connection'),
                relationship_kind=kind, directed=directed, source_ids=source_ids,
                evidence_note=note, classification_basis='editorial_review')


R = {}

# ---------------------------------------------------------------- batch 1 (1.232)

R['nancy_christie'] = dict(
    node_fields=dict(
        description=(
            "A Canadian historian of family, welfare and religion whose work asks how liberal authority "
            "was made through everyday institutions. In her 2009 contribution to the liberal-order debate, "
            "Christie credits Ian McKay’s framework with connecting cultural and social research while "
            "disputing its periodization, its emphasis on the state and its property-based account of "
            "individualism. Drawing on Bruce Curtis’s distinction between liberalism and governmentality, "
            "she asks for a more precise account of power. She proposes treating churches, voluntary "
            "associations and households as places where liberal values were made and contested, so that "
            "women’s participation, not only their exclusion, becomes part of the explanation. Engendering "
            "the State (2000) and her books with Michael Gauvreau on Protestant churches and social welfare "
            "place these institutions at the centre of Canadian social history."),
        scope_note=(
            "Complete 2009 essay re-read and verified 2026-10-31. Books identified by publisher and Crossref "
            "metadata; not read in full. Curtis's particular text is not named in the essay.")),
    remove_edge_ids=['tq_nancy_christie_habermas'],
    hold_reasons=dict(tq_nancy_christie_habermas=(
        "Habermas appears only parenthetically as a borrowed term; the civil-society idea in that sentence "
        "is attributed to Locke. Too slight for an edge.")),
    edge_updates=dict(tc232_nancy_christie_2=dict(
        relationship="Proposes making women’s associational and household activity part of the explanation of liberal rule.",
        source_ids=['lof_christie_2009'],
        evidence_note="2009 essay, final three substantive paragraphs (‘if a greater focus was placed’): a programmatic proposal. Verified 2026-10-31.")),
    verification='Edges 1, 3, McKay and Curtis confirmed against the 2009 essay; women/gender edge reworded as a proposal; Habermas edge held.',
    review=VER)

R['james_rodger_miller'] = dict(
    node_fields=dict(
        description=(
            "A settler historian of Indigenous–newcomer relations, residential schooling and treaties in "
            "Canada. Skyscrapers Hide the Heavens (1989) is his history of Indian–white relations in Canada. "
            "Shingwauk’s Vision (1996), a cross-Canada history of residential schooling, shifts the focus of "
            "responsibility from the churches toward the federal government and, ultimately, Euro-Canadian "
            "society. Celia Haig-Brown’s review credits the book’s breadth and research while criticizing how "
            "examples drawn across places and decades flatten differences among nations and schools, and "
            "questioning its claims to balance and its treatment of resistance. Compact, Contract, Covenant "
            "(2009) carries his work into the history of treaty-making."),
        scope_note=(
            "Haig-Brown (1997) pp. 100–101 and Holst (1997) pp. 270–271 verified 2026-10-31. Gélinas's review "
            "of the treaty book could not be read (bot check) and is no longer cited. Books not read in full. "
            "No testimony or community knowledge reproduced.")),
    sources=[src('tc232_miller_holst1997',
                 'Wayne A. Holst, review of Shingwauk’s Vision, Arctic 50:3 (1997), 270–271.',
                 'https://doi.org/10.14430/arctic1145',
                 'Open-access review read 2026-10-31: places the main responsibility on the government and the people of Canada (p. 271).')],
    remove_source_ids=['tq232_miller_gelinas2010'],
    edge_updates=dict(
        tc232_james_rodger_miller_1=dict(
            relationship="Writes national histories of Indigenous–newcomer relations, including a contested synthesis of residential schooling.",
            source_ids=['tc232_miller_haigbrown', 'tc232_miller_holst1997'],
            evidence_note="Haig-Brown pp. 100–101; Holst pp. 270–271. Verified 2026-10-31; treaty-making half not claimed from an unread review."),
        tc232_james_rodger_miller_2=dict(
            relationship="Shifts the focus of responsibility for residential schools from the churches toward the federal government and Euro-Canadian society; Haig-Brown identifies and questions the shift.",
            source_ids=['tc232_miller_haigbrown', 'tc232_miller_holst1997'],
            evidence_note="Haig-Brown printed p. 100 (‘to shift the focus of blame from the churches to the government’); Holst p. 271. Verified 2026-10-31.")),
    verification='Both edges verified and reworded to what the reviews say; Gélinas removed (unreadable). Existing source iha_miller_2009_review has a citation/URL mismatch outside this packet.',
    review=VER)

R['bruce_trigger'] = dict(
    node_fields=dict(
        description=(
            "A Canadian archaeologist and ethnohistorian of the Wendat (Huron) and of colonial encounters in "
            "northeastern North America. The Children of Aataentsic (1976) combines archaeology, history and "
            "ethnology to argue that Iroquoian societies had changed substantially in the centuries before "
            "European contact, so that the impact of contact cannot be assessed without understanding that "
            "earlier change. Natives and Newcomers (1985) reconsiders Canada’s ‘heroic age’ of exploration "
            "and colonization in the same way, and A History of Archaeological Thought (1989) is his history "
            "of his own discipline. He wrote the foreword to Georges E. Sioui’s For an Amerindian Autohistory "
            "(1992). Emma LaRocque criticizes that foreword as an example of containment, and argues that the "
            "cross-cultural approach to which Trigger belonged, though an improvement on earlier racist "
            "scholarship, could still distance and Other its subjects."),
        scope_note=(
            "McGill-Queen’s description of The Children of Aataentsic, library records for the 1992 foreword "
            "and LaRocque’s dissertation PDF pp. 135–136 and 249 verified 2026-10-31. Wolf’s review could not "
            "be read and is no longer cited. Books not read in full. Settler scholar; no community knowledge, "
            "narratives or honorary details.")),
    sources=[
        src('tc232_trigger_mqup', 'McGill-Queen’s University Press, The Children of Aataentsic: book description.',
            'https://www.mqup.ca/Books/T/The-Children-of-Aataentsic3',
            'Read 2026-10-31: integrates archaeology, history and ethnology; argues European impact cannot be assessed without understanding precontact change.'),
        src('tc232_trigger_sioui_foreword',
            'Georges E. Sioui, For an Amerindian Autohistory, trans. Sheila Fischman, foreword by Bruce G. Trigger (McGill-Queen’s University Press, 1992).',
            'https://openlibrary.org/books/OL1507570M',
            'Library record (LC/Harvard MARC) read 2026-10-31: ‘foreword by Bruce G. Trigger’, 1992.',
            status='bibliographic_metadata_checked')],
    remove_source_ids=['tq232_trigger_wolf1987'],
    edge_updates=dict(
        tc232_bruce_trigger_1=dict(
            relationship="Integrates archaeology, history and ethnology to reconstruct Wendat history before and after European contact.",
            source_ids=['tc232_trigger_mqup', 'trigger_aataentsic_1976'],
            evidence_note="McGill-Queen’s description, main paragraph. Verified 2026-10-31."),
        tc232_bruce_trigger_2=dict(
            relationship="Argues that European impact on Indigenous societies cannot be assessed without understanding change before contact, against images of a static precontact society.",
            source_ids=['tc232_trigger_mqup'],
            evidence_note="McGill-Queen’s description, middle of main paragraph. Verified 2026-10-31.")),
    edges=[edge('tq_bruce_trigger_sioui', 'bruce_trigger', 'georges_e_sioui',
                "Wrote the foreword to Sioui’s For an Amerindian Autohistory (1992), a foreword LaRocque later criticized.",
                'contribution', ['tc232_trigger_sioui_foreword', 'ind126_larocque_thesis'],
                "Library record of the 1992 edition; LaRocque PDF pp. 135–136. Scholarly publication fact only.")],
    verification='Wolf-based edges re-cited to the publisher description (read); foreword edge added from library metadata; LaRocque reading re-verified.',
    review=VER)

R['caroline_walker_bynum'] = dict(
    node_fields=dict(
        description=(
            "A historian of medieval European religion, gender and the body. Holy Feast and Holy Fast (1987) "
            "argues that food lay at the heart of much late-medieval women’s piety: women renounced ordinary "
            "food through fasting to prepare for the extraordinary food of the eucharist, and offered "
            "themselves as food in miracles of feeding. Where earlier scholars had treated fasting, stigmata "
            "and inedia in isolation or through modern medical and psychological theories, she showed how "
            "these practices enabled women to exert control within the family and religious life. In ‘Why "
            "All the Fuss about the Body?’ (1995) she engages sympathetically with Judith Butler’s "
            "performative account of gender, but insists that medieval and modern ideas of body and "
            "identity be compared in their own settings; the Middle Ages, she writes, was characterized by "
            "‘a cacophony of discourses’. Jesus as Mother (1982) and Fragmentation and Redemption (1991) are "
            "her other major collections on gender and the body in medieval religion."),
        scope_note=(
            "UC Press description of Holy Feast and Holy Fast and the 1995 Critical Inquiry essay (pp. 1, 7–8, "
            "27–30) verified 2026-10-31. ‘Why Paradox?’ (2012) could not be read and is no longer cited. "
            "Books not read in full.")),
    sources=[src('tc232_bynum_holyfeast', 'University of California Press, Holy Feast and Holy Fast: book description.',
                 'https://www.ucpress.edu/books/holy-feast-and-holy-fast/paper',
                 'Read 2026-10-31: food at the heart of women’s piety; earlier scholars applied modern medical or psychological theories.')],
    remove_source_ids=['tc232_bynum_paradox'],
    edge_updates=dict(
        tc232_caroline_walker_bynum_1=dict(
            relationship="Compares medieval and modern accounts of body and identity to study historically specific meanings of gender.",
            source_ids=['tq232_bynum_body1995'],
            evidence_note="Critical Inquiry 1995 pp. 1, 27–30. Verified 2026-10-31."),
        tc232_caroline_walker_bynum_2=dict(
            relationship="Shows that food practices were central to medieval women’s piety, against isolated or medicalized readings of fasting and miracles.",
            source_ids=['tc232_bynum_holyfeast'],
            evidence_note="UC Press description of Holy Feast and Holy Fast. Verified 2026-10-31."),
        tc232_caroline_walker_bynum_3=dict(
            relationship="Reads medieval culture as many competing discourses rather than one consistent worldview.",
            source_ids=['tq232_bynum_body1995'],
            evidence_note="Critical Inquiry 1995 p. 7 (‘a cacophony of discourses’). Verified 2026-10-31.")),
    event_updates={'tc232_caroline_walker_bynum_2': dict(source_ids=['graph:tc232_bynum_holyfeast'])},
    verification='Three ‘Why Paradox?’ edges re-cited to sources read here; Butler edge confirmed pp. 27–30.',
    review=VER)

R['barbara_h_rosenwein'] = dict(
    node_fields=dict(
        description=(
            "A medieval historian whose studies of property, immunity and power led to an influential "
            "approach to the history of emotions. ‘Worrying about Emotions in History’ (2002) revisits "
            "Lucien Febvre’s call for a history of feeling and rejects the grand narrative, associated with "
            "Norbert Elias, of a movement from unrestrained medieval emotion to modern self-control. In its "
            "place she proposes emotional communities: overlapping groups that value and express emotions "
            "in different ways. In a 2010 interview she questions William Reddy’s sharp distinction between "
            "emotional regimes and emotional refuges; Reddy’s reply allowing plural regimes stands beside "
            "her objection. Emotional Communities in the Early Middle Ages (2006) is the book-length study."),
        scope_note=(
            "Rests on the atlas’s earlier accepted readings of the 2002 article (pp. 821–822, 826–828, "
            "842–845) and the 2010 interview answers. Not re-readable here (publisher paywalls). The "
            "Stearns criticism cites pp. 824–826, outside the recorded reading, and is held.")),
    remove_edge_ids=['tq_barbara_h_rosenwein_stearns'],
    hold_reasons=dict(tq_barbara_h_rosenwein_stearns=(
        'Cited pp. 824–826 lie outside the recorded reading of the 2002 article; no allowed route to re-read them.')),
    remove_source_ids=['tc232_rosenwein_profile'],
    event_updates={'tc232_rosenwein_space': dict(source_ids=['graph:dc166_rosenwein_loyola'])},
    verification='Edges rest on readings accepted at 1.166; Stearns edge held; duplicate Loyola source removed.',
    review=VER)

R['joanna_bourke'] = dict(
    node_fields=dict(
        description=(
            "A historian of modern Britain, war, the body and emotion. Dismembering the Male (1996) studies "
            "men’s bodies and masculinity in the First World War. An Intimate History of Killing (1999), "
            "drawing on letters, diaries and memoirs of British, American and Australian combatants in the "
            "two world wars and Vietnam, argues that the structure of war encouraged pleasure in killing and "
            "that ordinary men could become enthusiastic killers without being brutalized. Her later work on "
            "fear and pain asks what emotions do: expressions of fear follow learned conventions yet can "
            "change the feeling they name, a point she develops through William Reddy’s concept of the "
            "emotive."),
        scope_note=(
            "Basic Books description of Killing, Birkbeck account, existing Dismembering description and her "
            "own methodological post on fear verified 2026-10-31. Books not read in full.")),
    source_updates=dict(tc232_bourke_killing=dict(
        title='Basic Books, An Intimate History of Killing: book description.',
        citation='Basic Books, An Intimate History of Killing: book description.',
        url='https://www.hachettebookgroup.com/titles/joanna-bourke/an-intimate-history-of-killing/9780465007387',
        verification=dict(status='supporting_page_checked', checked_on=DAY,
                          note='Read 2026-10-31: structure of war encourages pleasure in killing; ordinary men become enthusiastic killers without being brutalized.'))),
    remove_source_ids=['tc232_bourke_dementia'],
    edge_updates=dict(tc232_joanna_bourke_2=dict(
        source_ids=['tc232_bourke_birkbeck', 'bourke_dismembering', 'tc232_bourke_killing'],
        evidence_note='Birkbeck account; Basic Books description of Killing. Verified 2026-10-31.')),
    verification='All three edges confirmed; Killing re-sourced to the publisher; uncited lecture removed.',
    review=VER)

R['keith_thomas'] = dict(
    node_fields=dict(
        description=(
            "A historian of early modern English beliefs, social relations and attitudes. Religion and the "
            "Decline of Magic (1971) asks why beliefs in magic, astrology and witchcraft made sense in "
            "sixteenth- and seventeenth-century England and why they declined; the inquiry began, he "
            "recalls, from a puzzle about astrology and led him to anthropology. His 1963 essay ‘History and "
            "Anthropology’ grew from a review of Evans-Pritchard that Lawrence Stone encouraged him to "
            "expand. Thomas names Christopher Hill and R. H. Tawney as formative influences, and was drawn "
            "to Lucien Febvre’s inquiry into people’s assumptions rather than to quantitative Annales "
            "history. He later called his work a descriptive ethnography of early modern England and "
            "conceded that his explanation of magic’s decline was incomplete. Jan Machielsen and Michelle "
            "Pfeffer’s 2023 reassessment, building on Hildred Geertz’s criticism, questions the book’s "
            "categories of religion and magic. Man and the Natural World (1983) traced changing English "
            "attitudes to nature."),
        scope_note=(
            "Macfarlane interview timestamps and Machielsen/Pfeffer reassessment verified 2026-10-31. Stone "
            "edge rests on the atlas’s earlier accepted reading. Books not read in full.")),
    edge_updates=dict(tc232_keith_thomas_2=dict(
        relationship="Investigates past belief in magic and religion; his categories and account of decline have since been contested.",
        evidence_note="Machielsen and Pfeffer (2023), opening and section III. Verified 2026-10-31.")),
    verification='All seven timestamps confirmed; culture edge reworded (the contesting is the reviewers’, not his).',
    review=VER)

R['john_h_elliott'] = dict(
    node_fields=dict(
        description=(
            "A historian of early modern Spain and its empire. His first two books, The Revolt of the "
            "Catalans and Imperial Spain, 1469–1716, both appeared in 1963; a biography of the Count-Duke "
            "of Olivares followed in 1986. His interest in state formation and ‘composite monarchies’ "
            "runs from the Catalan revolt to Scots and Catalans (2018), and Empires of the Atlantic World "
            "(2006) compares British and Spanish America. Richard Kagan and Geoffrey Parker’s memoir records "
            "his admiration for Lucien Febvre’s regional synthesis and his doubts about how Fernand Braudel "
            "joined structures to events; the wish to disprove Braudel, with a belief in political "
            "biography, drove the Olivares project. His 1980 review of Carlo Ginzburg questioned how far a "
            "single case could represent a wider society. Ginzburg rejected Elliott’s opposition of micro- "
            "to macrohistory, and Natalie Zemon Davis rejected a zero-sum choice between histories of "
            "Martin Guerre and Martin Luther."),
        representative_figures_and_works=(
            "The Revolt of the Catalans (1963); Imperial Spain, 1469–1716 (1963); The Count-Duke of Olivares "
            "(1986); “A Europe of Composite Monarchies” (1992); Empires of the Atlantic World: Britain and "
            "Spain in America, 1492–1830 (2006)."),
        scope_note=(
            "Lady Margaret Hall memorial and Kagan/Parker British Academy memoir (pp. 163–166, 177, 204–206, "
            "230–231) verified 2026-10-31. The Making History interview could not be read and is no longer "
            "cited. Books not read in full.")),
    remove_source_ids=['tc232_elliott_interview'],
    source_updates=dict(tq232_elliott_kaganparker2024=dict(
        title='Richard L. Kagan and Geoffrey Parker, “John Huxtable Elliott, 1930–2022,” Biographical Memoirs of Fellows of the British Academy 21 (2023).',
        citation='Richard L. Kagan and Geoffrey Parker, “John Huxtable Elliott, 1930–2022,” Biographical Memoirs of Fellows of the British Academy 21 (2023).')),
    edge_updates=dict(
        tc232_john_h_elliott_1=dict(
            relationship="Compares the British and Spanish empires in America.",
            source_ids=['tc232_elliott_lmh'],
            evidence_note='LMH memorial, paragraph on Empires of the Atlantic World (2006). Verified 2026-10-31.'),
        tc232_john_h_elliott_2=dict(
            relationship="Studies state formation and composite monarchies, from the Catalan revolt to Scots and Catalans (2018).",
            source_ids=['tc232_elliott_lmh'],
            evidence_note='LMH memorial, paragraphs on 1963 books and ‘composite monarchies’. Verified 2026-10-31.')),
    verification='Interview-based edges re-cited to the LMH memorial; memoir edges (Febvre, Braudel, Ginzburg both ways, Davis) confirmed.',
    review=VER)

R['john_m_mackenzie'] = dict(
    node_fields=dict(
        description=(
            "A historian of empire who made its cultural presence in Britain, and its environmental history "
            "overseas, central subjects of imperial history. As founding editor of Manchester University "
            "Press’s Studies in Imperialism series he set out to examine how imperialism shaped the dominant "
            "societies as well as those they ruled; Propaganda and Empire (1984) studied the manipulation of "
            "British public opinion. The Empire of Nature (1988) connected hunting and conservation with "
            "British rule in Africa and India. Orientalism: History, Theory and the Arts (1995) challenged "
            "Edward Said’s generalizations through empirical study of the arts, as Berny Sèbe describes; "
            "Said in turn criticized an approach he associated with MacKenzie that treated culture as "
            "propaganda. His exchanges with Bernard Porter, after Porter’s The Absent-Minded Imperialists "
            "(2004), became among the most-read items in the Journal of Imperial and Commonwealth History."),
        scope_note=(
            "Sèbe’s accepted manuscript (Birmingham repository) pp. 3–5, 14–15, Johnson’s discussion and "
            "Said’s 2003 review verified 2026-10-31. The publisher’s series and memorial pages refuse "
            "scripted access. Books not read in full.")),
    source_updates=dict(tq232_mackenzie_sebe2019=dict(
        url='https://research.birmingham.ac.uk/en/publications/20efde29-e95b-4737-bd16-33927b1103e4')),
    edge_updates=dict(tc232_john_m_mackenzie_1=dict(
        source_ids=['tq232_mackenzie_sebe2019', 'tc232_mackenzie_series'],
        evidence_note='Sèbe accepted manuscript p. 5 quotes the series’ founding statement. Verified 2026-10-31.')),
    life_update=dict(claude_note=(
        'Claude 2026-10-31: the publisher memorial refused scripted access; a web search found the death '
        '(18 September 2026) reported only in an encyclopedia entry. Death kept at year precision.')),
    verification='Edges confirmed via Sèbe and Said; Porter debate limited to what Sèbe p. 15 says.',
    review=VER)

R['callum_g_brown'] = dict(
    node_fields=dict(scope_note=(
        "Glasgow research statement, Morris (2003) abstract and Brown’s 2017 accepted manuscript pp. 2–5 "
        "verified 2026-10-31. Books not read in full.")),
    verification='All edges and sentences confirmed.',
    review=VER)

# ---------------------------------------------------------------- batch 2 (1.233)

R['jonathan_israel'] = dict(
    node_fields=dict(description=(
        "A historian of the Dutch Republic, European Jewry and the Enlightenment whose radical-Enlightenment "
        "interpretation gives philosophical ideas a strong explanatory role. In a 2023 interview, Israel "
        "argues that the reception of Spinoza helped create a radical current committed to secularism, "
        "democratic republicanism and freedom of expression, which he opposes to a moderate Enlightenment. "
        "The coherence and reach of that current are disputed. Antoine Lilti stresses the diversity of the "
        "most heterodox Enlightenment writings and the ambiguity of ‘Spinozism’ as a historian’s category. "
        "David Bell credits Israel’s range and his insistence on ideas, but argues that he infers influence "
        "from similarity, takes passages out of context and overstates the ideological causes of the French "
        "Revolution.")),
    verification='Interview, Lilti and Bell confirmed; ‘equality’ replaced by the values the interview names.',
    review=VER)

R['geoffrey_parker'] = dict(
    node_fields=dict(
        description=(
            "A historian of early modern Europe, war and the Spanish monarchy whose work connects military "
            "organization with the resources and reach of states. The Army of Flanders and the Spanish Road "
            "(1972) began as a Cambridge doctorate under John Elliott, from Elliott’s question of how Spain "
            "sustained its army in the Netherlands. The Military Revolution (1988) extended Michael Roberts’s "
            "thesis to fortification and the scale of armies, and made it an argument about the rise of the "
            "West; it has remained a debate rather than a settled explanation. Global Crisis (2013) connects "
            "the political upheavals of the seventeenth century with climatic change across regions."),
        scope_note=(
            "Kagan/Parker memoir pp. 231–233, Ohio State research statement and the atlas’s earlier reading "
            "of Rogers’s introduction verified or reused 2026-10-31. Jeremy Black’s 2020 piece could not be "
            "read (bot check); that criticism is held. Books not read in full.")),
    remove_edge_ids=['tq_geoffrey_parker_black'],
    hold_reasons=dict(tq_geoffrey_parker_black='The Critic page is behind a bot check; the passages were not read.'),
    remove_source_ids=['tq233_parker_black2020', 'wedgwood_woolrych'],
    verification='Elliott supervision confirmed (BA memoir p. 232); Black edge held.',
    review=VER)

R['t_m_devine'] = dict(
    node_fields=dict(
        description=(
            "A historian of Scottish society, economy and diaspora. The Tobacco Lords (1975) studied Glasgow’s "
            "tobacco merchants, Clanship to Crofters’ War (1994) the social transformation of the Highlands, "
            "and The Scottish Nation (1999) is his history of modern Scotland. In ‘Did Slavery Make Scotia "
            "Great?’ (2011) he reopens Eric Williams’s question about slavery and economic development, "
            "arguing that Scotland’s stake cannot be measured by the few slaving voyages from its ports but "
            "must include the wider plantation economies. With Jenny Wormald he called for comparative, "
            "internationalized Scottish history rather than an insular national narrative."),
        scope_note=(
            "2011 article (Edinburgh repository) pp. 40–44 and the Devine/Wormald handbook introduction "
            "(publisher preview) verified 2026-10-31. Morton and Griffiths (2013) could not be read and is "
            "no longer cited. Books not read in full.")),
    sources=[src('tq233_devine_scotnation', 'T. M. Devine, The Scottish Nation, 1700–2000 (Allen Lane, 1999): library record.',
                 'https://openlibrary.org/works/OL7974797W', 'Open Library work record, first published 1999 (Allen Lane).',
                 status='bibliographic_metadata_checked')],
    remove_source_ids=['tc233_scotland_frame', 'tc233_devine_slavery'],
    edge_updates=dict(
        tc233_t_m_devine_2=dict(
            relationship="Studies the social and economic transformation of modern Scotland, including what Atlantic slavery contributed to its development.",
            source_ids=['tq233_devine_slavery_extended2011'],
            evidence_note='Devine 2011 pp. 40–44 (repository copy). Verified 2026-10-31.'),
        tc233_t_m_devine_3=dict(
            relationship="Writes national histories of Scotland while calling, with Jenny Wormald, for comparative and internationalized Scottish history.",
            source_ids=['tq233_devine_wormald2012', 'tq233_devine_scotnation'],
            evidence_note='Devine and Wormald, Oxford Handbook introduction (publisher preview). Verified 2026-10-31.')),
    event_updates={'tc233_t_m_devine_3': dict(source_ids=['graph:tq233_devine_scotnation'])},
    verification='Slavery and Williams edges confirmed; national-tradition edge re-cited to the handbook introduction; Morton/Griffiths removed (unreadable).',
    review=VER)

R['richard_j_evans'] = dict(
    node_fields=dict(
        description=(
            "A historian of modern Germany who has also defended historical knowledge in public. In Defence of "
            "History (1997) answers the writers who brought postmodernist epistemology into historical "
            "theory; he names Hayden White, Frank Ankersmit, Keith Jenkins, Patrick Joyce, Dominick LaCapra "
            "and Beverley Southgate. He wrote it because the standard textbooks were still Carr’s What Is "
            "History? and Elton’s The Practice of History, which he found inadequate. Its introduction accepts "
            "White’s point that historians can learn from outside scrutiny of how historical knowledge is "
            "made, while rejecting Joyce’s claim that historians must accept postmodernity as an inescapable "
            "condition. Death in Hamburg (1987) connects cholera with social inequality and civic government. "
            "He served as an expert witness on the falsification of history in the 2000 Irving libel trial, "
            "and The Coming of the Third Reich (2003) began his history of Nazi Germany."),
        scope_note=(
            "Evans’s response to his critics (IHR History in Focus) verified 2026-10-31. Introduction passages "
            "rest on the atlas’s earlier accepted reading of the 1997 book. Wolfson and Cambridge accounts "
            "for Death in Hamburg and the trial. Books not read in full.")),
    sources=[src('tq233_evans_ihr',
                 'Richard J. Evans, “Author’s response” to Antony Easthope’s review of In Defence of History, History in Focus 2: What is History? (Institute of Historical Research).',
                 'https://archives.history.ac.uk/history-in-focus/Whatishistory/evans3.html',
                 'Read 2026-10-31: names White, Ankersmit, Jenkins, Joyce, LaCapra and Southgate; Carr and Elton as the outdated textbooks.')],
    edge_updates=dict(tc233_richard_j_evans_1=dict(
        source_ids=['evans', 'tq233_evans_ihr'],
        evidence_note='Existing accepted introduction reading; Evans’s IHR response. Verified 2026-10-31.')),
    verification='Truth-debate edge strengthened with the IHR response; White/Joyce/Cannadine rest on the accepted 2026-09-12 reading.',
    review=VER)

R['thomas_laqueur'] = dict(
    node_fields=dict(
        description=(
            "A cultural historian of the body, sexuality and death. Making Sex (1990) argues that a ‘one-sex’ "
            "model, in which men and women were thought to share the same basic body, gave way in the "
            "eighteenth century to a ‘two-sex’ model grounded in biological difference: sex difference "
            "itself has a history. The thesis has been both influential and contested. Brooke Holmes, drawing "
            "on work by Katharine Park, Robert Nye, Joan Cadden and Helen King, argues that the evidence shows "
            "more varied and coexisting models, and traces the book’s narrative of epochal rupture to "
            "Foucault’s history of sexuality. Caroline Walker Bynum drew on it while noting Park and Nye’s "
            "qualification. Solitary Sex (2003) is a cultural history of masturbation, and The Work of the "
            "Dead (2015) asks what the care and naming of the dead do for the living."),
        scope_note=(
            "Holmes (2019, open access) introduction and later passage, Bynum (1995) pp. 7–8 and the Berkeley "
            "interview verified 2026-10-31. Books not read in full.")),
    remove_source_ids=['hunt_culture_intro_primary'],
    edge_updates=dict(tc233_thomas_laqueur_1=dict(
        relationship="Argues that sex difference has a history, from a ‘one-sex’ to a ‘two-sex’ model of the body.",
        source_ids=['tq233_laqueur_holmes2019', 'tc233_laqueur_interview'],
        evidence_note='Holmes 2019, introduction paragraphs 1–2 summarizing the thesis; Berkeley interview. Verified 2026-10-31.')),
    verification='Model now stated from Holmes (read); Foucault and Bynum edges confirmed.',
    review=VER)

R['charles_s_maier'] = dict(
    node_fields=dict(
        description=(
            "A historian of modern Europe and of political organization. His first book, Recasting Bourgeois "
            "Europe (1975), compares France, Germany and Italy after the First World War and argues that they "
            "did not return to the prewar order but achieved a new balance between state authority and "
            "organized interests. The Unmasterable Past (1988) addressed history, the Holocaust and German "
            "national identity. In later work he treats territoriality as a historical resource: borders, "
            "sovereignty and technologies of communication shape both government and belonging, and a "
            "networked world has not abolished the state. A conference report records John Breuilly’s "
            "challenge to the coherence of an ‘age of territoriality’, and Partha Chatterjee’s contrast with "
            "the overlapping sovereignties of Mughal India and the flexible sovereignty of colonial rule."),
        representative_figures_and_works=(
            "Recasting Bourgeois Europe (1975); The Unmasterable Past (1988); “Consigning the Twentieth Century "
            "to History” (2000); Among Empires (2006); Once Within Borders (2016)."),
        scope_note=(
            "Project MUSE description of Recasting Bourgeois Europe, the 2017 Harvard Gazette interview and the "
            "GHIL conference report pp. 183–184 verified 2026-10-31. Harvard research and profile pages refuse "
            "scripted access; the memory edge is held. Books not read in full.")),
    sources=[src('tq233_maier_recasting', 'Project MUSE, Recasting Bourgeois Europe: book description (Princeton University Press).',
                 'https://muse.jhu.edu/book/42799',
                 'Read 2026-10-31: first book (1975); three nations achieved a new balance of state authority and interest-group representation.')],
    remove_edge_ids=['tc233_charles_s_maier_3'],
    hold_reasons=dict(tc233_charles_s_maier_3='Harvard research statement refuses scripted access; no readable source for the memory programme.'),
    remove_source_ids=['tq233_maier_metadata2000', 'tc233_maier_research'],
    source_updates=dict(tc233_maier_2000=dict(
        title='Charles S. Maier, “Consigning the Twentieth Century to History: Alternative Narratives for the Modern Era,” American Historical Review 105:3 (June 2000).',
        citation='Charles S. Maier, “Consigning the Twentieth Century to History: Alternative Narratives for the Modern Era,” American Historical Review 105:3 (June 2000).',
        url='https://doi.org/10.2307/2651811',
        verification=dict(status='bibliographic_metadata_checked', checked_on=DAY,
                          note='Crossref metadata 2026-10-31. The earlier URL pointed to a different author’s 2004 article.'))),
    verification='Wrong 2000 article URL fixed; first book added from MUSE; memory edge held; Chatterjee wording corrected.',
    review=VER)

R['e_h_carr'] = dict(
    node_fields=dict(
        description=(
            "A historian of Soviet Russia and of international relations whose What Is History? (1961) became "
            "the standard British introduction to historical method. Carr argued that historians select and "
            "give meaning to facts through their questions, so that research and interpretation proceed "
            "together; his position was long read as a challenge to objectivist history. G. R. Elton’s The "
            "Practice of History (1967) was written in open opposition, and John Tosh called the Carr–Elton "
            "controversy the best starting point for debate about the standing of historical knowledge. "
            "Richard Evans wrote In Defence of History (1997) because Carr’s and Elton’s books were still the "
            "standard textbooks and, in his view, inadequate for later debates. The Twenty Years’ Crisis "
            "(1939) belongs to his work on international relations, and his History of Soviet Russia began "
            "with The Bolshevik Revolution (1950)."),
        scope_note=(
            "Munslow’s IHR reappraisal, Munro (2015) abstract and Evans’s IHR response verified 2026-10-31. "
            "The chapter-one reading rests on an earlier atlas source whose provenance needs review. Books not "
            "read in full.")),
    sources=[
        src('tq233_carr_munslow', 'Alun Munslow, “What is History?” reappraisal, History in Focus 2: What is History? (Institute of Historical Research).',
            'https://archives.history.ac.uk/history-in-focus/Whatishistory/carr1.html',
            'Read 2026-10-31: Tosh on the Carr–Elton controversy; Jenkins on both books setting the agenda.'),
        src('tq233_carr_munro2015', 'Doug Munro, “Macmillan and The Practice of History,” Historical Journal 58:3 (2015).',
            'https://doi.org/10.1017/S0018246X14000582',
            'Abstract read 2026-10-31: the adversarial relationship between The Practice of History and What is History?')],
    edge_updates=dict(
        tc233_e_h_carr_1=dict(
            source_ids=['carr_facts_primary', 'tq233_carr_munslow'],
            evidence_note='Earlier atlas reading of chapter 1; Munslow’s IHR reappraisal. Verified 2026-10-31.'),
        tq_e_h_carr_evans=dict(
            source_ids=['evans', 'tq233_evans_ihr'],
            evidence_note='Evans’s IHR response (Carr and Elton as outdated textbooks); earlier accepted introduction reading.'),
        tq_e_h_carr_laterdebate=dict(
            source_ids=['evans', 'tq233_carr_munslow', 'tq233_carr_munro2015'],
            evidence_note='Munslow (Tosh quotation), Munro abstract, Evans. Verified 2026-10-31.')),
    verification='Reception and Elton debate re-grounded in IHR and Munro; chapter-one source flagged for provenance review.',
    review=VER)

R['judith_r_walkowitz'] = dict(
    node_fields=dict(scope_note=(
        "Minerva interview verified 2026-10-31; the Johns Hopkins page refuses scripted access. Books not read in full.")),
    edge_updates=dict(
        tc233_judith_r_walkowitz_1=dict(source_ids=['tq233_walkowitz_minerva'],
                                        evidence_note='Minerva interview, answers on the first two books. Verified 2026-10-31.'),
        tc233_judith_r_walkowitz_2=dict(source_ids=['tq233_walkowitz_minerva'],
                                        evidence_note='Minerva interview introduction (comparative women’s history). Verified 2026-10-31.')),
    verification='All edges confirmed against the Minerva interview.',
    review=VER)

R['paul_kennedy'] = dict(
    node_fields=dict(
        description=(
            "A historian of international power, strategy and political economy. The Rise and Fall of the "
            "Great Powers (1987) argues that great powers decline relative to others when their strategic "
            "commitments outrun their economic base; readers summarized this as ‘imperial overstretch’, and "
            "in the late 1980s it was read as a warning to the United States. Michael Cox notes that the idea "
            "was not wholly new, and Kennedy himself traced one stimulus to Mahan’s use of an earlier "
            "reflection on Spain’s dispersed empire. In the same roundtable Varsha Venkatasubramanian "
            "criticized the book’s neglect of non-state actors and of politics’ effects on economic "
            "development; Kennedy accepted her point about India and conceded that the book may contain too "
            "much economic determinism. His earlier books studied British naval mastery and the Anglo-German "
            "antagonism before 1914."),
        scope_note=(
            "ISSF roundtable (Cox, Venkatasubramanian, author’s response) and the 2009 Yale panel verified "
            "2026-10-31. Books not read in full.")),
    verification='Overstretch stated from the ISSF roundtable (read); all edges confirmed.',
    review=VER)

R['t_c_smout'] = dict(
    node_fields=dict(
        description=(
            "A historian of Scottish society who helped establish environmental history in Scotland. A History "
            "of the Scottish People, 1560–1830 (1969) and A Century of the Scottish People (1986) are his "
            "social histories of Scotland. His 1990 British Academy lecture ‘The Highlands and the Roots of "
            "Green Consciousness’ questions the story that appreciation of Highland landscapes was simply "
            "imported into an indifferent society. In later environmental work he draws on E. A. Wrigley’s "
            "account of the shift from organic to fossil-fuel economies, and names William Cronon’s "
            "city-and-hinterland history as a model for studies of Scottish cities still to be written."),
        scope_note=(
            "British Academy lecture pp. 237–238 and the 2012 handbook chapter pp. 19–21, 26–28 (publisher "
            "preview) verified 2026-10-31. Morton and Griffiths (2013) could not be read and is no longer "
            "cited. Books not read in full.")),
    remove_edge_ids=['tc233_t_c_smout_2'],
    hold_reasons=dict(tc233_t_c_smout_2='Rested only on Morton and Griffiths (2013), which is behind a bot check.'),
    edge_updates=dict(tc233_t_c_smout_3=dict(
        source_ids=['tc233_smout_leith'],
        evidence_note='St Andrews Historian 2024 account of the 1969 synthesis. Verified 2026-10-31.')),
    verification='Environment, Wrigley and Cronon edges confirmed; national-tradition edge held.',
    review=VER)

# Batch 3 (1.234) is added by claude_review_batch3.py once its verification is in.
try:
    from claude_review_batch3 import R3
    R.update(R3)
except ImportError:
    pass


def add_life_identity(R):
    """The site's life-review build needs an identity rationale and a known status for every record.

    The researcher life files lack the rationale, and two use `not_established`; the site
    validator's term for that is `unresolved` (no new death asserted, birth year still withheld).
    """
    ext = HERE.parents[1]
    for b in (1, 2, 3):
        folder = ext / f'timeline-canon-batch{b}-2026-10-31'
        for pid in json.loads((folder / 'batch.json').read_text())['persons']:
            d = json.loads((folder / pid / 'entry-draft.json').read_text())
            life = json.loads((folder / pid / 'life-status.json').read_text())
            works = R.get(pid, {}).get('node_fields', {}).get('representative_figures_and_works') \
                or d['node']['representative_figures_and_works']
            note = (d.get('people_update') or {}).get('identity_note') or ''
            rationale = (f"{d['node']['label']}, {d['node']['entry_type'].lower()} identified by {works.rstrip('.')}. "
                         f"{note} Life sources matched to the same scholar by institution and works; no namesake merger.").strip()
            u = R.setdefault(pid, dict(review=VER)).setdefault('life_update', {})
            u['identity_rationale'] = rationale
            if life['status'] == 'not_established':
                u['status'] = 'unresolved'
                u['status_note'] = 'Researcher status not_established; recorded as unresolved for the site (birth year withheld, no death asserted).'


if __name__ == '__main__':
    add_life_identity(R)
    (HERE / 'claude-review.json').write_text(json.dumps(R, ensure_ascii=False, indent=2) + '\n')
    print(f'claude-review.json: {len(R)} people')
