"""Batch 3 (1.234) part of Claude's verification overlay; imported by claude_review.py."""
from claude_review import DAY, VER, src, edge

R3 = {}

R3['david_arnold'] = dict(
    node_fields=dict(
        description=(
            "A historian of South Asia, and a founding member of the Subaltern Studies collective, whose work "
            "brings medicine, science and environment into the study of colonial power. Colonizing the Body "
            "(1993) studies state medicine and epidemic disease in nineteenth-century India. The introduction "
            "to Science, Technology and Medicine in Colonial India (2000) rejects a single trajectory from "
            "European discovery to passive reception overseas. Drawing on Steven Shapin’s account of knowledge "
            "as socially situated, it insists that a history of science in India must also be a history of "
            "India. It criticizes George Basalla’s diffusion model for flattening differences among colonial "
            "situations, marginalizing local agency and assuming a beneficial sequence of development, while "
            "also rejecting accounts that understate colonial disruption. His environmental histories include "
            "The Problem of Nature (1996) and The Tropics and the Traveling Gaze (2006)."),
        scope_note=(
            "Warwick research statement and bibliography, and Cambridge’s sample of the 2000 introduction, "
            "verified 2026-10-31. The Colonizing the Body passage on Foucault could not be re-read; those "
            "edges are held. Books not read in full.")),
    remove_edge_ids=['tc234_david_arnold_3', 'tc234_david_arnold_5'],
    hold_reasons=dict(
        tc234_david_arnold_3='The cited p. 7 passage of Colonizing the Body is not on the publisher page and could not be re-read.',
        tc234_david_arnold_5='The cited p. 7 passage of Colonizing the Body is not on the publisher page and could not be re-read.'),
    source_updates=dict(tc234_arnold_biblio=dict(
        url='https://warwick.ac.uk/fac/arts/history/chmst/events/conferences_workshops/da_theworks/david_arnold_the_works.pdf')),
    edge_updates=dict(tc234_david_arnold_4=dict(
        relationship='Includes environmental history among his fields, from The Problem of Nature (1996) to The Tropics and the Traveling Gaze (2006).',
        evidence_note='Warwick research page: field list and selected publications. Verified 2026-10-31.')),
    verification='Subaltern, medicine, Shapin and science edges confirmed; Foucault-based edges held; Warwick URL updated.',
    review=VER)

R3['j_r_mcneill'] = dict(
    node_fields=dict(
        description=(
            "An environmental historian who works at global and regional scales. Something New Under the Sun "
            "(2000) is an environmental history of the twentieth-century world. Mosquito Empires (2010) argues "
            "that ecological change made the Greater Caribbean hospitable to the mosquitoes that carry yellow "
            "fever and malaria. Because survivors gained immunity or resistance, these diseases took sides in "
            "the struggles for empire and revolution between 1620 and 1914, decimating forces sent from Europe. "
            "His survey of the field credits the Annales with an inspiring general approach while noting how "
            "little environmental history its founders wrote, and treats Alfred Crosby’s studies of ecological "
            "exchange as landmarks. In his 2020 AHA presidential address he argues that scientific evidence can "
            "illuminate histories poorly documented in writing, while warning against monocausal climate "
            "histories and against letting a new tool dictate the question."),
        scope_note=(
            "Cambridge front matter of Mosquito Empires and the 2020 AHA address verified 2026-10-31; the 2003 "
            "survey rests on the atlas’s earlier reading (provenance flagged for review), partly confirmed in "
            "the open-access Spanish translation. Books not read in full.")),
    sources=[src('tc234_mcneill_heineken', 'Georgetown College, “McNeill Receives Heineken Award” (2 May 2018).',
                 'https://college.georgetown.edu/news-story/mcneill-receives-heineken-award/',
                 'Read by the batch-3 check 2026-10-31: award citation for his environmental history.')],
    remove_source_ids=['tc234_mcneill_georgetown'],
    edge_updates=dict(tc234_j_r_mcneill_2=dict(
        relationship='Writes environmental history at global and regional scales, from the twentieth-century world to the Greater Caribbean.',
        source_ids=['tc234_mcneill_mosquito', 'tc234_mcneill_heineken'],
        evidence_note='Mosquito Empires front matter (description and author note); Georgetown award story. Verified 2026-10-31.')),
    verification='Environment edge confirmed; global edge re-cited; Crosby partly confirmed in OA translation; Annales edge rests on the earlier accepted reading.',
    review=VER)

R3['sheila_fitzpatrick'] = dict(
    node_fields=dict(
        description=(
            "A historian of the Soviet Union and of Stalinism from below. In ‘Revisionism in Retrospect’ (2008) "
            "she gives a participant’s account of how social historians of the 1970s and 1980s challenged "
            "political scientists’ totalitarian model, crediting revisionism with an appreciation of contingency "
            "and a new approach to power and to the interplay of government and society. Stalin’s Peasants: "
            "Resistance and Survival in the Russian Village after Collectivization (1994) and Everyday "
            "Stalinism: Ordinary Life in Extraordinary Times (1999) carry that social history into village and "
            "city. In a comparative chapter with Alf Lüdtke on Nazism and Stalinism, she treats Hannah Arendt’s "
            "thesis of social atomization as a question for research: social bonds were broken but also remade, "
            "and participation involved people’s emotional investments."),
        representative_figures_and_works=(
            "The Russian Revolution (1982; revisions 1994, 2007 and 2017 distinct); Stalin’s Peasants (1994); "
            "Everyday Stalinism (1999)."),
        scope_note=(
            "Slavic Review abstract (2008), Cambridge chapter summary of the Lüdtke chapter (2008) and the "
            "Chicago CEERES bibliography verified 2026-10-31. Books not read in full.")),
    sources=[src('tc234_fitzpatrick_ceeres', 'University of Chicago CEERES, Sheila Fitzpatrick: profile and bibliography.',
                 'https://ceeres.uchicago.edu/people/sheila-fitzpatrick',
                 'Read by the batch-3 check 2026-10-31: book list with dates (1982 and revisions, 1994, 1999).',
                 status='bibliographic_metadata_checked')],
    remove_source_ids=['tc234_fitzpatrick_acu'],
    edge_updates={pid: dict(evidence_note='Cambridge chapter summary (2008), three paragraphs. Verified 2026-10-31.')
                  for pid in ['tc234_sheila_fitzpatrick_1', 'tc234_sheila_fitzpatrick_2', 'tq_sheila_fitzpatrick_arendt']},
    event_updates={f'tc234_sheila_fitzpatrick_{i}': dict(source_ids=['graph:tc234_fitzpatrick_ceeres']) for i in (1, 2, 3)},
    verification='Arendt, social and political edges confirmed; revisionism retrospective added; dates corrected (2007, 2008).',
    review=VER)

R3['patrick_geary'] = dict(
    node_fields=dict(
        description=(
            "A medieval historian of relics, memory and ethnic identity. Furta Sacra (1978) studied thefts of "
            "relics in the central Middle Ages, and his essay ‘Sacred Commodities’ (1986) asks what made relics "
            "exchangeable within a particular medieval setting rather than assuming a timeless market. Phantoms "
            "of Remembrance (1994) concerns memory and oblivion at the end of the first millennium. The Myth "
            "of Nations (2002) uses research on changing early medieval identities to criticize modern "
            "nationalist claims to ancient continuity; Steven Fanning credits its central argument while "
            "warning that its survey contains questionable assertions and broad generalizations."),
        scope_note=(
            "Cambridge opening of ‘Sacred Commodities’, Geary’s CV and Fanning’s H-France review verified "
            "2026-10-31. The IAS account refuses scripted access; the memory edge is held. Books not read in "
            "full.")),
    remove_edge_ids=['tc234_patrick_geary_2'],
    hold_reasons=dict(tc234_patrick_geary_2='Rested only on the IAS page, which refuses scripted access.'),
    remove_source_ids=['tc234_geary_ias'],
    edge_updates=dict(tc234_patrick_geary_3=dict(
        source_ids=['tq234_geary_fanning2002'],
        evidence_note='Fanning, H-France Review 2 (2002), opening and conclusion. Verified 2026-10-31.')),
    verification='Commodities and nationalism edges confirmed; IAS-based memory edge held.',
    review=VER)

R3['mike_davis'] = dict(
    node_fields=dict(
        description=(
            "A historian of cities, capitalism and environmental disaster. City of Quartz (1990) and Ecology of "
            "Fear (1998) examined the political economy and ecology of Los Angeles. Late Victorian Holocausts "
            "(2001) argues that the famines of the late nineteenth century arose from the interaction of El "
            "Niño droughts with imperial and market systems that left populations vulnerable, not from weather "
            "alone; it opens from Raymond Williams’s reflection on nature and human history. Davis recalls that "
            "Robert Brenner’s UCLA seminar on Capital, which moved on to crisis theory and twentieth-century "
            "economic history, gave him the confidence to pursue his own agenda. He later criticized Marx and "
            "Engels for saying nothing about cities and for leaving the patriarchy of the workers’ movement "
            "unchallenged."),
        scope_note=(
            "Verso excerpts from Late Victorian Holocausts (2017 post) and Old Gods, New Enigmas (2022 post), "
            "the UCR memorial and publications list verified 2026-10-31. Books not read in full.")),
    remove_edge_ids=['tc234_mike_davis_3'],
    hold_reasons=dict(tc234_mike_davis_3='No read passage connects Davis to the New Left as such; the node fit is an inference.'),
    remove_source_ids=['tc234_davis_biblio'],
    edge_updates=dict(
        tq_mike_davis_marxcrit=dict(target='karl_marx'),
        tq_mike_davis_williams=dict(
            relationship='Opens his history of late-Victorian famine from Raymond Williams’s reflection on nature and human history.',
            evidence_note='Verso excerpt, opening paragraph. Verified 2026-10-31.')),
    event_updates={'tc234_mike_davis_3': dict(source_ids=['graph:tc234_davis_books'])},
    verification='Marx criticism retargeted from the historical-materialism field to Karl Marx; New Left edge held; dead bibliography removed.',
    review=VER)

R3['hugh_trevor_roper'] = dict(
    node_fields=dict(
        description=(
            "A historian of early modern Britain and Europe. His 1959 essay on ‘The General Crisis of the "
            "Seventeenth Century’, prompted, as Blair Worden notes, by Eric Hobsbawm’s Marxist analysis of the "
            "century’s revolts, set the English revolution within a wider European crisis; the later preface to "
            "his essays questions a simple Calvinism-to-capitalism explanation associated with Weber and "
            "Tawney. Worden explains his resistance to deterministic accounts of revolution, including "
            "Christopher Hill’s, and his attention to contingency and personality. In his chapter for Hobsbawm "
            "and Terence Ranger’s The Invention of Tradition (1983) he argued that the kilt, clan tartans and "
            "the very idea of a distinct Highland culture, to which Scots ascribe great antiquity, are largely "
            "modern, developed after the Union with England; The Invention of Scotland (2008) extends the "
            "theme. His authentication of the forged Hitler diaries in 1983 was a serious failure of judgment."),
        scope_note=(
            "Worden’s British Academy memoir (pp. 262, 265–266, 271–272, 281–282), the Liberty Fund preface "
            "and Cambridge’s opening of the Highland chapter verified 2026-10-31. Books not read in full.")),
    sources=[src('tc234_trevor_highland',
                 'Hugh Trevor-Roper, “The Invention of Tradition: The Highland Tradition of Scotland,” in Eric Hobsbawm and Terence Ranger (eds), The Invention of Tradition (Cambridge University Press, 1983), 15–42.',
                 'https://doi.org/10.1017/CBO9781107295636.002',
                 'Chapter opening on Cambridge Core read 2026-10-31: the apparatus ‘is in fact largely modern’; a distinct Highland culture ‘is a retrospective invention’.')],
    source_updates=dict(tc234_trevor_biblio=dict(
        url='https://web.archive.org/web/20231210132004/https://www.history.ox.ac.uk/sites/default/files/history/documents/media/trevor-roper-full-bibliography.pdf')),
    edges=[
        edge('tq_hugh_trevor_roper_hobsbawm', 'eric_hobsbawm', 'hugh_trevor_roper',
             "Hobsbawm’s Marxist analysis of the mid-seventeenth-century revolts prompted Trevor-Roper’s ‘General Crisis’ essay (1959).",
             'contribution', ['tq234_trevor_worden_extended2007'],
             'Worden p. 262 (‘Without Eric Hobsbawm’s Marxist analysis … there would not have been Hugh’s essay’). Verified 2026-10-31.'),
        edge('tq_hugh_trevor_roper_highland', 'hugh_trevor_roper', 'nationalismstudies',
             'Argues that the kilt, clan tartans and the idea of a distinct Highland culture are modern inventions ascribed to antiquity.',
             'contribution', ['tc234_trevor_highland'],
             'Cambridge chapter opening, paras. 1–2. Verified 2026-10-31.')],
    event_updates={'tc234_hugh_trevor_roper_2': dict(source_ids=['graph:tc234_trevor_highland', 'graph:tc234_trevor_biblio'])},
    verification='All edges confirmed; Hobsbawm and invented-tradition edges added from read passages; bibliography replaced by its archived copy.',
    review=VER)

R3['peter_gay'] = dict(
    node_fields=dict(
        description=(
            "A historian of European intellectual and cultural life who joined social history to "
            "psychoanalysis. The Enlightenment: An Interpretation (1966, 1969), Weimar Culture (1968) and the "
            "five-volume The Bourgeois Experience: Victoria to Freud (1984–98) are his major studies, and "
            "Freud: A Life for Our Time (1988) is his biography of Freud. In a 1997 interview he describes "
            "Freud as an indispensable resource for studying the interplay of psychological processes and "
            "external circumstances, insisting that an event such as the French Revolution still requires "
            "attention to state finances, royal prestige and social conflict. He criticized psychohistory that "
            "gave inner experience too much causal weight."),
        representative_figures_and_works=(
            "The Enlightenment: An Interpretation (two volumes, 1966 and 1969); Weimar Culture (1968); The "
            "Bourgeois Experience: Victoria to Freud (five volumes, 1984–1998); Freud: A Life for Our Time (1988)."),
        scope_note=(
            "Rests on the atlas’s earlier reading of the 1997 interview and Yale’s 2004 AHA citation. The "
            "publisher excerpt on romanticism is excluded by robots.txt, so that edge is held. Books not read "
            "in full.")),
    remove_edge_ids=['tc234_peter_gay_2'],
    hold_reasons=dict(tc234_peter_gay_2='The publisher site’s robots.txt disallows the excerpt page; not read.'),
    remove_source_ids=['tc234_gay_romantics'],
    verification='Interview edges confirmed; Freud biography added; robots-excluded excerpt removed.',
    review=VER)

R3['paul_thompson'] = dict(
    node_fields=dict(scope_note=(
        "UK Data Archive thematic highlights of his life-story interview (pp. 6–8, 11–13), Taylor (2021, UEA "
        "repository) and the atlas’s earlier reader extract verified or reused 2026-10-31. The Essex profile "
        "fails a TLS check here, not a 404. Books not read in full.")),
    source_updates=dict(tq234_thompson_taylor2021=dict(
        url='https://ueaeprints.uea.ac.uk/id/eprint/79544/')),
    verification='Interview and Hobsbawm edges confirmed; social edge rests on the earlier accepted extract.',
    review=VER)

R3['kathleen_wilson'] = dict(
    sources=[src('tc234_wilson_strolling', 'Kathleen Wilson, Strolling Players of Empire (Cambridge University Press, 2022).',
                 'https://doi.org/10.1017/9781108786317',
                 'Cambridge Core record checked by the batch-3 check 2026-10-31: published 2022.',
                 status='bibliographic_metadata_checked')],
    source_updates=dict(tc234_wilson_cv=dict(
        title='Kathleen Wilson, curriculum vitae (linked from her Stony Brook faculty page).',
        citation='Kathleen Wilson, curriculum vitae (linked from her Stony Brook faculty page).',
        url='https://docs.google.com/document/d/1A9kKR4qcTFOX2scuzqgB3C5MBmdgtSz9pWP3WYok_n4/edit?usp=sharing')),
    node_fields=dict(
        date_label='The Sense of the People (1995) · The Island Race (2003) · A New Imperial History: edited collection (2004) · Strolling Players of Empire (2022)',
        representative_figures_and_works='The Sense of the People (1995); The Island Race (2003); A New Imperial History (edited, 2004); Strolling Players of Empire (2022).'),
    event_updates={'tc234_kathleen_wilson_4': dict(date=dict(year=2022, precision='year'),
                                                   source_ids=['graph:tc234_wilson_strolling'])},
    verification='Introduction pp. 1–8 confirmed (Chakrabarty, Hall, Foucault); dead CV replaced by the author-linked copy; Strolling Players dated 2022.',
    review=VER)

R3['charles_e_rosenberg'] = dict(
    node_fields=dict(
        description=(
            "A historian of medicine and science. The Cholera Years (1962), on the United States in 1832, 1849 "
            "and 1866, is credited with leading historians to study not only a disease and its victims but "
            "society’s response to it, through politics, law and social mores. The Care of Strangers (1987), a "
            "history of the American hospital, and Explaining Epidemics (1992) continued that social history "
            "of medicine. In a 2013 interview he places his work within a social-medicine tradition that treats "
            "medical ideas and access to care as embedded in society, questions tidy genealogies in which "
            "translated theorists alone changed historical research, and distinguishes psychiatric diagnostic "
            "categories that organize research and care from explanations of mechanism."),
        scope_note=(
            "Harvard Gazette (2001), the Mantovani interview (SciELO, 2016) and the Cambridge chapter summary "
            "verified 2026-10-31; interview page numbers not visible in the HTML. Books not read in full.")),
    remove_source_ids=['tc234_rosenberg_profile'],
    event_updates={f'tc234_charles_e_rosenberg_{i}': dict(source_ids=['graph:tc234_rosenberg_harvard']) for i in (1, 2, 3)},
    edge_updates=dict(
        tc234_charles_e_rosenberg_1=dict(evidence_note='Mantovani interview (2013, published 2016), answers on social medicine and psychiatric diagnosis. Verified 2026-10-31; print page numbers not visible.'),
        tc234_charles_e_rosenberg_2=dict(evidence_note='Mantovani interview, historiographical answers. Verified 2026-10-31; print page numbers not visible.')),
    verification='Both edges confirmed; Cholera Years contribution added from the Gazette; Rosen as influence, diagnosis as psychiatric.',
    review=VER)

R3['robert_bartlett'] = dict(
    node_fields=dict(
        description=(
            "A medieval historian of conquest, law and historical categories. Trial by Fire and Water (1986) "
            "studied the medieval judicial ordeal, and The Making of Europe (1993) traced conquest, colonization "
            "and cultural change between 950 and 1350. His 2001 article on race and ethnicity treats both terms "
            "as social constructions and warns against using present administrative labels as ready-made "
            "historical explanations. Comparing medieval terminology, he emphasizes culture, law, language and "
            "religion in the making of identities, while examining genealogical idioms of descent, and separates "
            "collective identity from any automatic demand for sovereign statehood. Geraldine Heng later "
            "questions the sharpness of his distinction between medieval cultural difference and biological "
            "racism."),
        scope_note=(
            "2001 article (St Andrews repository) pp. 39–43, 45–47, 52–53 and Heng’s discussion verified "
            "2026-10-31. Books identified by publisher metadata; not read in full.")),
    source_updates=dict(tc234_bartlett_race=dict(url='https://research-repository.st-andrews.ac.uk/handle/10023/1869')),
    remove_source_ids=['tq234_bartlett_race_extended2001'],
    edge_updates={pid: dict(source_ids=['tc234_bartlett_race']) for pid in ['tc234_robert_bartlett_1', 'tq_robert_bartlett_nationhood']},
    verification='Both edges confirmed in the repository copy; duplicate article record merged.',
    review=VER)

R3['stephen_greenblatt'] = dict(
    node_fields=dict(
        description=(
            "A literary scholar and theorist whose New Historicism reads literature within the whole field of a "
            "period’s culture. Renaissance Self-Fashioning (1980) examines how More, Tyndale, Wyatt, Spenser, "
            "Marlowe and Shakespeare fashioned selves, finding that new questions about identity shaped "
            "sixteenth-century writing. He calls New Historicism ‘madly eclectic’: it grew from impatience with "
            "American formalism and with Marxist criticism, and drew on Foucault to escape the base/superstructure "
            "dichotomy, as well as on Walter Benjamin, Michel de Certeau and Clifford Geertz. He credits Raymond "
            "Williams with showing how to connect art to the world in which it is made. Sarah Maza questions how "
            "far New Historicism and historians’ cultural history actually meet across disciplinary lines, and "
            "John Monfasani criticized The Swerve for opposing medieval darkness to Renaissance modernity; "
            "Greenblatt replied defending the Renaissance and the importance of atomism."),
        scope_note=(
            "Aletria e-mail interview (2018) pp. 124–125, the 2014 Harvard Gazette interview, the Chicago "
            "description of Renaissance Self-Fashioning, Maza (2004) and the Reviews in History exchange verified "
            "2026-10-31. Books not read in full.")),
    sources=[
        src('tq234_greenblatt_aletria',
            'Luiz Fernando Ferreira Sá and Miriam Piedade Mansur Andrade, “Acts of Literature II” (e-mail interview with Stephen Greenblatt, March 2018), Aletria 28:3 (2018).',
            'https://periodicos.ufmg.br/index.php/aletria/article/download/18815/15777/50210',
            'Open access, read 2026-10-31: pp. 124–125, New Historicism ‘madly eclectic’; Foucault, Benjamin, de Certeau, Marin and Geertz as resources.'),
        src('tq234_greenblatt_ucp', 'University of Chicago Press, Renaissance Self-Fashioning: book description.',
            'https://press.uchicago.edu/ucp/books/book/chicago/R/bo3680145.html',
            'Read 2026-10-31: examines the structure of selfhood in More, Tyndale, Wyatt, Spenser, Marlowe and Shakespeare.')],
    remove_source_ids=['tq234_greenblatt_culture1995'],
    source_updates=dict(tc234_greenblatt_maza=dict(
        title='Sarah Maza, “Stephen Greenblatt, New Historicism, and Cultural History, or, What We Talk About When We Talk About Interdisciplinarity,” Modern Intellectual History 1:2 (2004).',
        citation='Sarah Maza, “Stephen Greenblatt, New Historicism, and Cultural History, or, What We Talk About When We Talk About Interdisciplinarity,” Modern Intellectual History 1:2 (2004).')),
    edge_updates=dict(tc234_stephen_greenblatt_1=dict(
        relationship='Reads literature within the whole field of a period’s culture, from theology and travel narratives to police reports.',
        source_ids=['tq234_greenblatt_aletria', 'tc234_greenblatt_interview'],
        evidence_note='Aletria p. 124, first answer; Harvard Gazette interview. Verified 2026-10-31.')),
    edges=[
        edge('tq_stephen_greenblatt_foucault', 'foucault', 'stephen_greenblatt',
             'Greenblatt credits Foucault with helping New Historicism escape the base/superstructure dichotomy.',
             'contribution', ['tq234_greenblatt_aletria'], 'Aletria pp. 124–125, first answer. Verified 2026-10-31.'),
        edge('tq_stephen_greenblatt_geertz', 'geertz', 'stephen_greenblatt',
             'Greenblatt names Clifford Geertz among the resources of New Historicism’s eclectic method.',
             'contribution', ['tq234_greenblatt_aletria'], 'Aletria pp. 124–125, first answer. Verified 2026-10-31.')],
    event_updates={'tc234_stephen_greenblatt_1': dict(source_ids=['graph:tq234_greenblatt_ucp', 'graph:tq234_greenblatt_aletria'])},
    verification='Culture edge re-cited from an excluded route to the open-access interview; Foucault and Geertz edges added; self-fashioning stated.',
    review=VER)
