"""Materialize this review packet only. Never applies the graph or builds docs/."""
import hashlib
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = '2026-10-31'
REV = '1.232'
QUEUE = ROOT / 'data/field-research/timeline-candidates-2026-10-30/work-queues/batch-1.json'
G = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
Q = json.loads(QUEUE.read_text())
PEOPLE = {p['id']: p for p in G['people']}
SOURCES = {s['id']: s for s in G['sources']}
SPECS = {}


def source(key, title, url, note, metadata=False):
    return dict(id='tc232_' + key, title=title, citation=title, url=url,
                verification=dict(status='bibliographic_metadata_checked' if metadata else 'supporting_page_checked',
                                  checked_on=DAY, note=note))


def passage(sid, locator, claim, mode='read', limit='Complete book bodies are not claimed read.'):
    return dict(source_id=sid, locator=locator, check_scope=mode, support=claim, limits=limit)


def edge(target, text, sources, locator, kind='contribution', origin=None):
    return dict(target=target, relationship=text, source_ids=sources, evidence_note=locator,
                relationship_kind=kind, origin=origin)


def event(key, label, year, sources, support, kind='publication', track='contributions'):
    return dict(id='tc232_' + key, label=label, kind=kind, track=track,
                date=dict(year=year, precision='year'), source_ids=['graph:' + s for s in sources], support=support)


def life(url, title, locator, support):
    return dict(url=url, title=title, locator=locator, support=support, checked_on=DAY)


def person(pid, **spec):
    SPECS[pid] = spec


person('nancy_christie',
 description='A Canadian historian of family, welfare and religion. Engendering the State investigates changes in the gendered foundations of social provision. Her work with Michael Gauvreau places churches within the making of modern social policy. In her 2009 intervention on the liberal order framework, she accepts its capacity to connect historical studies but challenges its periodization and emphasis on the state. She argues that a property-based account of individualism obscures women’s participation through households, churches and voluntary associations. This is a proposed revision of the framework, rather than a rejection of all its questions.',
 works='A Full-Orbed Christianity (1996), with Michael Gauvreau; Engendering the State: Family, Work, and Welfare in Canada (2000); Christian Churches and Their Peoples, 1840–1965 (2010), with Michael Gauvreau.',
 scope='The complete 2009 review essay and JSTOR’s displayed introduction opening are read; the three books remain unread in full. Joint authorship is retained. No Oxford Brookes employment claim is adopted. Existing roster prose and source notes remain unchanged.',
 old=['lof_christie_2009', 'cdnsrc_christie_2000', 'crr_christie_gauvreau_1996', 'crr_christie_gauvreau_2010'],
 sources=[source('christie_jstor', 'Nancy Christie, Engendering the State (University of Toronto Press, 2000): JSTOR book record and displayed chapter openings.', 'https://www.jstor.org/stable/10.3138/9781442674479', 'Copyright 2000, sole authorship, contents and displayed opening of the introduction (chapter spans pp. 3–16) checked. Only its first displayed paragraph on the research question is read, not the whole introduction. Book description supplies the gendered policy shift; chapter bodies unread.'),
          source('christie_bnf', 'Bibliothèque nationale de France, Nancy Christie author heading and associated publications.', 'https://catalogue.bnf.fr/rechercher.do?index=TOUS3&numNotice=34270227&typeNotice=C', 'Indexed authority heading Christie, Nancy (1958–....) and matching Full-Orbed Christianity record checked. Birth year only; an open date does not establish present living status.', True)],
 events=[event('christie_full', 'A Full-Orbed Christianity, with Michael Gauvreau', 1996, ['crr_christie_gauvreau_1996'], 'Original coauthored book; later electronic publication not substituted.'),
         event('christie_state', 'Engendering the State', 2000, ['tc232_christie_jstor'], 'JSTOR copyright and Christie’s own 2009 citation agree on 2000.'),
         event('christie_churches', 'Christian Churches and Their Peoples, with Michael Gauvreau', 2010, ['crr_christie_gauvreau_2010'], 'Existing checked UTP publication metadata; full text unread.')],
 edges=[edge('liberal_order_framework', 'Challenges the framework’s timing, statism and property-based account of individualism.', ['lof_christie_2009'], 'Complete institutional essay re-read, especially paragraphs beginning The first issue, Since liberalism, and I think that a renewed emphasis. Supports a qualified critique, not a rejection of the framework’s synthesizing value.', 'critique'),
        edge('cdn_women_gender', 'Makes women’s associational and household activity part of the explanation of liberal rule.', ['lof_christie_2009','tc232_christie_jstor'], '2009 essay, final three substantive paragraphs; JSTOR displayed introduction opening supplements the welfare research question. No claim that women uniformly benefited from liberalism.'),
        edge('cdn_religion_reform', 'Treats churches and voluntary associations as sites where liberal values were made and contested.', ['lof_christie_2009'], '2009 essay, paragraph beginning Probably the most important site. Her intervention supplies this claim; the coauthored books are not presented as freshly read.')],
 contexts={'cdn_women_gender': 'accept: primary 2009 discussion explicitly connects women, family and voluntary organizations to liberal rule'},
 passages=[passage('lof_christie_2009','Complete review essay, excluding surrounding website navigation','Qualified critique and proposed extensions of the liberal order framework; complete local HTML SHA256 913b4b2bb6086fc0611c46ec978408102e44e4b56924f01f116ffeecef6bc651.'),
           passage('tc232_christie_jstor','Introduction entry, displayed opening paragraph; book description and copyright line','Research question and publication date; displayed text is not a full chapter.')],
 birth=1958, status='not_established', life_sources=[life('https://catalogue.bnf.fr/rechercher.do?index=TOUS3&numNotice=34270227&typeNotice=C','BnF, Nancy Christie','Authority heading and matching book','Birth year 1958 at year precision; no recorded death in the checked heading.')],
 life_limits='No positive contemporary life-status witness established. The open authority date is insufficient to call her living. Birth year stays in the research packet; no death is recorded and it must be withheld from site prose/export.')

person('james_rodger_miller',
 description='A settler historian of Indigenous–newcomer relations, residential schools and treaty-making in Canada. His national syntheses brought government and church records together with published scholarship and interview evidence. Celia Haig-Brown’s 1997 review of Shingwauk’s Vision credits its breadth and research while questioning how examples drawn across places and decades can flatten differences among nations and schools. She also challenges its claims to balance and its treatment of resistance. This entry retains that criticism alongside the synthesis. It describes scholarly method and responsibility without reproducing testimony or community knowledge.',
 works='Skyscrapers Hide the Heavens (1989; fourth edition 2018 distinct); Shingwauk’s Vision: A History of Native Residential Schools (1996); Compact, Contract, Covenant: Aboriginal Treaty-Making in Canada (2009).',
 scope='Haig-Brown’s review is read at printed pp. 100–101; Miller’s complete books remain unread. Publisher descriptions establish the residential-school book’s archival/interview basis. The treaty book’s argument is held at existing review/metadata scope. Four disambiguated keys follow the queue’s work-level namesake resolution; no unrelated Miller titles are assigned.',
 old=['ind127_miller_1989','ind127_miller_1996','iha_miller_2009_review'],
 sources=[source('miller_haigbrown', 'Celia Haig-Brown, review of J. R. Miller, Shingwauk’s Vision, BC Studies 114 (Summer 1997): 99–102.', 'https://ojs.library.ubc.ca/index.php/bcstudies/article/view/1714', 'Printed pp. 100–101 read from the publisher’s issue review PDF, https://ojs.library.ubc.ca/index.php/bcstudies/article/download/1714/1886/7713 . PDF SHA256 38624fc0b8cbaf75d772ceb7abecae8378061cebbc7e01fd09119364c82d9cde. Source base, synthesis, methodological objections and limits of balancing/resistance discussion consulted. No narrator quotations, traditional-education content or community/family details retained. The review is Summer 1997; website posting 2013 is separate. Other reviews in the same PDF are outside this reading.'),
          source('miller_memorial', 'University of Saskatchewan Retirees Association, November 2025 newsletter, notice for James (Jim) Rodger Miller.', 'https://usra.usask.ca/documents/newsletters/2025-2021/newsletter2025-11-final.pdf', 'Members No Longer With Us, printed p. 13: heading gives 28 April 1943–11 September 2025. Identity checked through historian/emeritus description and Native-Newcomer Relations chair. Personal and family details not used.')],
 events=[event('miller_skyscrapers','Skyscrapers Hide the Heavens',1989,['ind127_miller_1989'],'Publisher explicitly dates original publication 1989; 2018 revision is distinct.'),
         event('miller_shingwauk','Shingwauk’s Vision',1996,['ind127_miller_1996','tc232_miller_haigbrown'],'Original book date; the substantive reader is Haig-Brown in 1997.'),
         event('miller_treaty','Compact, Contract, Covenant',2009,['iha_miller_2009_review'],'Book publication 2009 retained from existing bibliography, distinct from later reviews.')],
 edges=[edge('native_newcomer','Builds national syntheses of relations and residential schooling whose scale also raises questions about local and national difference.',['tc232_miller_haigbrown'],'Haig-Brown, printed pp. 100–101: broad archival/interview synthesis and criticism of homogenizing examples. The arrow records a contested contribution, not Indigenous authorship or endorsement by communities.'),
        edge('cdn_religion_reform','Makes church responsibility and its relation to state policy central problems in residential-school history.',['tc232_miller_haigbrown'],'Haig-Brown, printed p. 100 on assigning responsibility, p. 101 on balanced accounts. Her objections accompany the contribution; this is an addition to the religion field, not an assertion of agreement with a secularization thesis.')],
 contexts={'cdn_religion_reform':'accept: Haig-Brown’s substantive review discusses the church/state responsibility question; retain her methodological reservations'},
 passages=[passage('tc232_miller_haigbrown','Printed pp. 100–101 (PDF pages 9–10)','National synthesis and critique of homogenization, balance and resistance. The review’s professional arguments alone are used.'),
           passage('ind127_miller_1996','Existing publisher-description verification','Archive/interview method only.','baseline_documented_reading')],
 birth=1943, birth_date='1943-04-28', death=2025, death_date='2025-09-11', status='deceased',
 life_sources=[life('https://usra.usask.ca/documents/newsletters/2025-2021/newsletter2025-11-final.pdf','USRA November 2025 newsletter','Members No Longer With Us, printed p. 13','Heading explicitly dates birth 28 April 1943 and death 11 September 2025; professional identification matches the queue.')],
 life_limits='Institutional memorial notice; only professional identity and life dates retained. A catalogue’s open date is superseded by positive death evidence.')

person('bruce_trigger',
 description='A Canadian archaeologist and ethnohistorian whose work connects material evidence with documentary history. The Children of Aataentsic and Natives and Newcomers reconsider earlier accounts of Wendat/Huron history and colonial encounters. His 1986 historiographical essay discusses bringing interdisciplinary ethnohistory into national history. That project does not escape Indigenous criticism. In her 1999 dissertation, Emma LaRocque criticizes his foreword to Georges Sioui’s Autohistory as limiting Indigenous historical authority, and includes Trigger in a cross-cultural approach that she sees as improved on earlier racism yet still capable of distancing and Othering its subjects.',
 works='The Children of Aataentsic: A History of the Huron People to 1660 (1976; new-preface edition 1987 distinct); Natives and Newcomers (1985); “The Historians’ Indian” (1986); A History of Archaeological Thought (1989; second edition 2006 distinct).',
 scope='Contribution claims reuse the baseline’s bounded opening reading of the 1986 essay and distributor description. Criticism uses the already documented LaRocque reading at PDF pp. 135–136 and 249. No new whole-book or dissertation reading. Indigenous-authored history is not a roster affiliation for this settler scholar. Community knowledge, narratives and honorary-membership details are excluded.',
 old=['trigger_aataentsic_1976','nnreq_trigger_1985','nnreq_trigger_1986','ind126_larocque_thesis'],
 sources=[source('trigger_mcgill','McGill University Newsroom, “Bruce Trigger, 1937–2006,” 2 December 2006.','https://www.mcgill.ca/newsroom/channels/news/bruce-trigger-1937-2006-22943','Institutional notice checked for life years and death 1 December 2006, archaeology/anthropology appointment and authorship. Family information and honorary-membership characterization not used.'),
          source('trigger_thought','Cambridge-hosted references, publication witness for Bruce G. Trigger, A History of Archaeological Thought (1989).','https://www.cambridge.org/core/journals/archaeological-dialogues/article/abs/beyond-externalism-exploring-new-directions-in-the-history-of-archaeology/C1CFC5AE49478B4AA770306FB58C6902','First-edition 1989 citation checked in the displayed references. Book unread. The separately checked DOI 10.1017/CBO9780511813016 identifies the later 2006 edition (ebook 2014), so it is not assigned to this first-edition milestone.', True)],
 events=[event('trigger_children','The Children of Aataentsic',1976,['trigger_aataentsic_1976'],'Original 1976, not the distributor’s 1987 new-preface edition.'),
         event('trigger_natives','Natives and Newcomers',1985,['nnreq_trigger_1985'],'Original metadata only; book unread.'),
         event('trigger_thought','A History of Archaeological Thought',1989,['tc232_trigger_thought'],'Original publication; second edition not backdated.')],
 edges=[edge('ethnohistory','Argues for interdisciplinary ethnohistory and its integration into national historical writing.',['nnreq_trigger_1986'],'Existing bounded reading of the 1986 essay opening only, as documented in the baseline source note. No fresh full reading or claim that ethnohistory supplies Indigenous authority.'),
        edge('anthropology','Brings archaeological and ethnographic work into contact with documentary history.',['nnreq_trigger_1986'],'1986 essay opening as previously documented: an interdisciplinary research undertaking, not equivalence among disciplines or endorsement of a uniform ethnographic method.'),
        edge('bruce_trigger','Criticizes his containment of Sioui’s intervention and the distancing effects of his cross-cultural historiography.',['ind126_larocque_thesis'],'LaRocque’s 1999 dissertation, existing documented reading at PDF pp. 135–136 (foreword) and 249 (cross-cultural approach). Her concession that the approach improved on earlier racism is retained. This is reuse of audited passages, not a new reading or reproduction of Indigenous knowledge.','critique','emma_larocque')],
 contexts={'anthropology':'accept: the 1986 opening explicitly situates archaeology and anthropology in an interdisciplinary historical practice',
           'indigenous':'reject roster affiliation: this field is Indigenous-authored history and critique. Retain its LaRocque criticism through a directed criticism edge; do not roster Trigger as Indigenous-authored'},
 passages=[passage('nnreq_trigger_1986','Opening, as bounded in the existing source verification','Interdisciplinary programme; not a new full article reading.','baseline_documented_reading'),
           passage('ind126_larocque_thesis','PDF pp. 135–136 and 249, existing recorded reading','Two distinct methodological criticisms, including the concession of improvement over earlier racist material.','baseline_documented_reading')],
 birth=1937, death=2006, death_date='2006-12-01', status='deceased',
 life_sources=[life('https://www.mcgill.ca/newsroom/channels/news/bruce-trigger-1937-2006-22943','McGill Newsroom, Bruce Trigger','Notice heading and first paragraph','Birth year 1937; died 1 December 2006.')],
 life_limits='Only year precision established for birth in the consulted institutional notice; no exact birth day inferred.')

person('caroline_walker_bynum',
 description='A historian of medieval European religion whose studies make gender, embodiment and material practices questions of historical interpretation. In her 2012 scholarly autobiography, she explains the movement from studying maternal imagery used by male religious authorities to comparing writings by and about religious women. She resists both a simple scale of women’s status and explanations that make religious practice merely pathological or compensatory. Her method seeks cultural assumptions while preserving incompatible voices and the strangeness of the past. Those retrospective arguments support this entry; the selected monographs are not presented as fully read.',
 works='Jesus as Mother: Studies in the Spirituality of the High Middle Ages (1982 essay collection; earlier article distinct); Holy Feast and Holy Fast (1987); Fragmentation and Redemption (1991).',
 scope='Primary 2012 retrospective read in selected passages at printed pp. 434–435 and 442–447. The earlier essay and the 1982, 1987 and 1991 books remain unread in full. Claims about critics are Bynum’s responses and are not certified descriptions of all feminist history. The existing Beyond the Cultural Turn qualification remains.',
 old=['bonnell_hunt_primary'],
 sources=[source('bynum_paradox','Caroline Walker Bynum, “Why Paradox? The Contradictions of My Life as a Scholar,” Catholic Historical Review 98:3 (July 2012): 433–455.','https://doi.org/10.1353/cat.2012.0222','Author’s institutional posting https://www.ias.edu/sites/default/files/hs/Bynum_Articles/Bynum_Why%20Paradox_CHR.pdf consulted at printed pp. 434–435 and 442–447. Selected retrospective method discussion and account of her own books read; no full article/book reading. Article and 1982 collection are distinct. Criticism of reductive models remains attributed to Bynum.'),
          source('bynum_cv','Caroline Walker Bynum, Institute for Advanced Study: biography and bibliography.','https://www.ias.edu/hs/bynum/cv','Professional biography and bibliography checked for ongoing research, 1982/1987/1991 publication dates and a June 2026 conversation. Life evidence is recorded separately in the research packet. Later editions and translation languages are not independently dated. Book bodies unread.',True)],
 events=[event('bynum_mother','Jesus as Mother: essay collection',1982,['tc232_bynum_cv'],'Collection publication, distinct from the earlier article discussed in her retrospective.'),
         event('bynum_feast','Holy Feast and Holy Fast',1987,['tc232_bynum_cv'],'Original 1987; later paperback/reprints not substituted.'),
         event('bynum_fragments','Fragmentation and Redemption',1991,['tc232_bynum_cv'],'Original essay collection; no claim to new reading of its constituent essays.')],
 edges=[edge('gender','Uses comparison of male and female religious writing to investigate historically specific gendered meanings.',['tc232_bynum_paradox'],'Printed pp. 442–443: her retrospective account differentiates the male imagery inquiry from the later study of women. Not a fresh reading of the monographs.'),
        edge('women','Challenges reduction of medieval women’s religiosity to pathology or a single measure of status.',['tc232_bynum_paradox'],'Printed pp. 444–447, selected argument read. Contribution records her critical intervention within women’s history, not her assent to every feminist approach.'),
        edge('culture','Insists that cultural interpretation preserve conflicting voices and the historical foreignness of the past.',['tc232_bynum_paradox'],'Printed pp. 434–435. Methodological statement, not affiliation with a single cultural school.')],
 contexts={'gender':'accept: primary 2012 retrospective distinguishes the two gendered research questions',
           'women':'accept with critical qualification: opposition to reductive status scales is itself an intervention in women’s history',
           'culture':'accept: explicit primary discussion of culture, interpretation and irreconcilable voices'},
 passages=[passage('tc232_bynum_paradox','Printed pp. 434–435; selected pp. 442–447','Retrospective method, gender comparisons and criticism of reductive interpretations. Earlier books and critics’ original texts are not newly read.')],
 birth=1941, status='living', life_sources=[life('https://www.ias.edu/hs/bynum/cv','IAS, Caroline Walker Bynum','Biographical paragraph; current research and final bibliography item','Birth year 1941; current work and a June 2026 conversation provide positive activity evidence.')],
 life_limits='Institutional biography with current research and 2026 author activity; birth year is research-only because no death is recorded.')

person('barbara_h_rosenwein',
 description='A medieval historian whose studies of property and immunity developed into an inquiry into the history of emotions. Her 2002 article proposes overlapping emotional communities in place of a single story of movement from uncontrolled medieval feeling to modern restraint. Her 2010 interview also questions a regime/refuge model that too sharply separates power from emotional alternatives. Reddy’s answer allowing plural regimes remains a distinct qualification, rather than being erased by that objection. This entry uses the atlas’s earlier bounded readings of the article and interview; the medieval monographs supply separate bibliographic milestones.',
 works='Negotiating Space (1999); “Worrying about Emotions in History” (2002); Emotional Communities in the Early Middle Ages (2006; paperback 2007 distinct); answers in Jan Plamper’s interview (2010).',
 scope='The recorded 2002 primary pages and Rosenwein’s 2010 answers at pp. 255–256 are reused with their original limits. Books remain unread. Existing source notes retain Reddy’s plural-regime qualification. The Loyola bibliography is freshly checked for Negotiating Space (1999); life evidence is separate from the chronology.',
 old=['dc166_rosenwein_worrying_2002','dc166_plamper_interview_2010','dc166_rosenwein_loyola'],
 sources=[source('rosenwein_profile','Loyola University Chicago, Barbara H. Rosenwein: emerita profile and bibliography, current reading.','https://www.luc.edu/history/people/facultyandstaffdirectory/emeritusfaculty/profiles/rosenweinbarbarah.shtml','Current professional description, 2023 textbook activity and bibliography checked: Negotiating Space 1999, Emotional Communities 2006. This separate current witness leaves the old source record exact. The inconsistent dates once recorded for Generations of Feeling are outside this chronology.',True),
          source('rosenwein_authority','Persée, authority record for Barbara H. Rosenwein.','https://www.persee.fr/authority/43203','Authority heading 1945– and description of the Loyola historian checked. Birth at year precision only; open heading alone does not establish living status.',True)],
 events=[event('rosenwein_space','Negotiating Space',1999,['tc232_rosenwein_profile'],'Institutional bibliography gives original 1999; body unread.'),
         event('rosenwein_worry','“Worrying about Emotions in History”',2002,['dc166_rosenwein_worrying_2002'],'June 2002 issue; current repost dates are not original publication.'),
         event('rosenwein_communities','Emotional Communities in the Early Middle Ages',2006,['dc166_rosenwein_loyola'],'Original 2006; paperback 2007 is separate.')],
 edges=[edge('history_of_emotions','Proposes overlapping emotional communities and questions a single historical trajectory toward restraint.',['dc166_rosenwein_worrying_2002','dc166_plamper_interview_2010'],'Existing recorded primary reading: 2002 pp. 821–822, 826–828, 842–845; 2010 Rosenwein answers pp. 255–256. Her objection to regime/refuge remains distinct from Reddy’s pp. 240–243 plural-regime qualification.'),
        edge('elias','Challenges the civilizing-process narrative of a progression from medieval emotional excess toward modern restraint.',['dc166_rosenwein_worrying_2002'],'Existing bounded article reading, especially pp. 826–828 and 842–845. This is Rosenwein’s historiographical objection, not a rereading or blanket rejection of all Elias scholarship.','critique')],
 contexts={},
 passages=[passage('dc166_rosenwein_worrying_2002','Recorded pp. 821–822, 826–828 and 842–845','Communities model and criticism of the grand restraint narrative.','baseline_documented_reading'),
           passage('dc166_plamper_interview_2010','Rosenwein pp. 255–256; Reddy qualification pp. 240–243','Preserve distinct interviewees and competing models.','baseline_documented_reading')],
 birth=1945, status='living', life_sources=[life('https://www.persee.fr/authority/43203','Persée, Rosenwein','Authority heading','Birth year 1945.'),life('https://www.luc.edu/history/people/facultyandstaffdirectory/emeritusfaculty/profiles/rosenweinbarbarah.shtml','Loyola, Rosenwein','Present professional account and 2023 edition','Positive institutional description of active scholarship; dated recent textbook activity.')],
 life_limits='Present professional account supports living status but is not a civil-register check. Only the birth year is recorded, and it stays out of entry prose.')

person('joanna_bourke',
 description='A historian of modern Britain and of bodily experience, violence and emotion. Dismembering the Male studies men’s bodies and masculinity during and after the Great War; An Intimate History of Killing asks how combatants experienced the act of killing. Her later cultural histories investigate how pain and fear acquire meanings in changing social settings. In her 2023 lecture on dementia, she asks how historical narratives shape personhood and warns that making vulnerable people visible can also compromise their dignity. The lecture supplies a bounded methodological example, rather than a reading of all her books.',
 works='Dismembering the Male (1996); An Intimate History of Killing (1999); Fear: A Cultural History (2005; 2006 paperback distinct).',
 scope='Existing Dismembering publisher description, Birkbeck’s account of her research and the opening of her own 2023 lecture support distinct claims. Complete selected books remain unread. No patient testimony, personal case details or medical claims are adopted from the lecture. The 2003 Fear and Anxiety article is metadata-only.',
 old=['bourke_dismembering'],
 sources=[source('bourke_birkbeck','Birkbeck, Professor Joanna Bourke: fellowship oration (elected 2024).','https://www.bbk.ac.uk/about-us/fellows/joanna-bourke','Professional sections of the institutional oration checked, including its account of An Intimate History of Killing and subsequent fear/pain histories. Family detail, quoted poetry and evaluative superlatives excluded. This is an institutional account, not Bourke’s own testimony.'),
          source('bourke_dementia','Joanna Bourke, “Dementia: A Cultural History,” Gresham College, 11 May 2023: transcript.','https://www.gresham.ac.uk/sites/default/files/transcript/2023-05-11-1800_BOURKE-T.pdf','Transcript opening PDF p. 1 and opening of p. 2 read for historical meaning, personhood and representation/consent questions. Patient cases, testimony, medical statistics and recommendations are not retained or independently assessed. Lecture text only; no audio/video claim.'),
          source('bourke_fear','Joanna Bourke, Fear: A Cultural History (Virago, 2005): bibliographic witness.','https://www.gresham.ac.uk/watch-now/breast-history','Author’s Gresham bibliography dates Fear (London: Virago, 2005). Book body unread; later paperback 2006 is separate.',True),
          source('bourke_birth','University of Münster history library, acquisitions February 2021.','https://www.uni-muenster.de/imperia/md/content/geschichte/historischesseminar/bibliothek/neuerwerbungen_februar_2021.pdf','Indexed institutional library entry for Fear gives author authority Bourke, Joanna, 1963– and identifies the 2006 paperback. Birth year only; not living evidence.',True),
          source('bourke_killing','Cambridge University Press, Sport and the Military, select bibliography: publication witness for Joanna Bourke, An Intimate History of Killing.','https://www.cambridge.org/core/books/abs/sport-and-the-military/select-bibliography/8112D03AE50DA8FADCFA1A79C4E99CF6','Displayed bibliography gives London: Granta Books, 1999. Metadata witness only, distinct from the Birkbeck oration’s substantive account; book unread.',True)],
 events=[event('bourke_male','Dismembering the Male',1996,['bourke_dismembering'],'1996 publication metadata, not a new chapter reading.'),
         event('bourke_killing','An Intimate History of Killing',1999,['tc232_bourke_killing'],'Cambridge-hosted bibliography gives London: Granta Books, 1999; complete body unread.'),
         event('bourke_fear','Fear: A Cultural History',2005,['tc232_bourke_fear'],'Author bibliography supplies original Virago 2005; later paperback distinct.')],
 edges=[edge('history_of_emotions','Uses historically changing meanings of fear and vulnerability to question assumptions about personhood.',['tc232_bourke_dementia'],'2023 primary transcript, PDF p. 1 closing methodological discussion and opening of p. 2. A specific later example of emotions history, not a medical or psychological universal.'),
        edge('military','Makes bodily injury and the experience of violence problems for the cultural history of war.',['tc232_bourke_birkbeck','bourke_dismembering'],'Birkbeck professional account, paragraphs on Killing and Fear, alongside existing Dismembering description. Named institutional account of the work; no fresh full book reading.'),
        edge('gender','Examines men’s bodies and masculinity as historical problems of wartime society.',['bourke_dismembering'],'Existing scoped publisher description; no new chapter-level reading. Retained as a description-supported context, rather than an influence claim.')],
 contexts={'history_of_emotions':'accept: own 2023 lecture supplies a bounded methodological passage; institutional account independently locates the turn to emotion'},
 passages=[passage('tc232_bourke_dementia','PDF p. 1 and opening p. 2','Historical framing and the ethics of representing vulnerable people; medical content excluded.'),
           passage('tc232_bourke_birkbeck','Professional research discussion, paragraphs on An Intimate History of Killing and Fear','Institutional account, not first-person testimony.')],
 birth=1963, status='living', life_sources=[life('https://www.uni-muenster.de/imperia/md/content/geschichte/historischesseminar/bibliothek/neuerwerbungen_februar_2021.pdf','Münster history library','Indexed author authority under Fear','Birth year 1963.'),life('https://www.bbk.ac.uk/about-us/fellows/joanna-bourke','Birkbeck fellowship oration','Elected 2024; present professional account','Positive recent institutional activity supports living status.')],
 life_limits='Year precision from a library authority heading; living assessment from positive professional activity rather than the heading’s open end.')

person('keith_thomas',
 description='A social and cultural historian of early modern England. Religion and the Decline of Magic investigates beliefs that modern readers may dismiss while asking why they made sense within past social worlds. Jan Machielsen and Michelle Pfeffer’s 2023 reassessment reads the book as both an engagement with anthropology and an accumulation of historically particular voices. They also show why its categories and account of decline remain contested, including Hildred Geertz’s criticism of its assumptions about magic. This named reading keeps its achievement and its limits together; the selected books are not claimed read in full.',
 works='“History and Anthropology” (1963); Religion and the Decline of Magic (1971); Man and the Natural World (1983); The Ends of Life (2009).',
 scope='Interpretation uses Machielsen and Pfeffer’s opening and selected sections II–III, plus the existing limited Stone reading. Thomas’s 1963 article is metadata-only and all selected books are unread in full. Geertz’s original criticism and Thomas’s original reply are not newly read. The account does not reduce Thomas’s work to one anthropological theory.',
 old=['stone_revival'],
 sources=[source('thomas_reassessment','Jan Machielsen and Michelle Pfeffer, “A Work Out of Time: Religion and the Decline of Magic at Fifty,” Past & Present 261 (November 2023): 259–296.','https://doi.org/10.1093/pastj/gtad012','Publisher open-access text: opening, selected section II paragraphs on anthropology, functionalism and Geertz (notes 56–73), and section III discussion of categories and Geertz (notes 111–121) read. Both authors credited. Their reading, including their qualifications of Geertz’s criticism, is not a new reading of Thomas, Geertz or the 1975 exchange. Online 18 August and November 2023 issue remain distinct.'),
          source('thomas_ba','British Academy, Sir Keith Thomas FBA: professional biography and selected books.','https://www.thebritishacademy.ac.uk/fellows/profiles/keith-thomas-FBA/','Summary/current post checked for current honorary fellowship and original book dates 1971, 1983, 2009. Life evidence is recorded separately in the research packet. The page’s 2003/1991 publication tiles refer to later editions, not the originals.',True),
          source('thomas_anthro','Keith Thomas, “History and Anthropology,” Past & Present 24 (April 1963): 3–24.','https://doi.org/10.1093/past/24.1.3','Publisher and JSTOR issue metadata checked for author/title/date/pages; article body unread. Substantive methodological characterization comes from Machielsen and Pfeffer, not from metadata.',True)],
 events=[event('thomas_anthro','“History and Anthropology”',1963,['tc232_thomas_anthro'],'Original April 1963 publication; body unread.'),
         event('thomas_magic','Religion and the Decline of Magic',1971,['tc232_thomas_ba','tc232_thomas_reassessment'],'Original 1971; later Penguin tiles not used as first publication.'),
         event('thomas_nature','Man and the Natural World',1983,['tc232_thomas_ba'],'Original 1983, not the 1991 edition displayed elsewhere on the same page.')],
 edges=[edge('anthropology','Uses anthropology to make historical belief intelligible while retaining an empirically particular form of inquiry.',['tc232_thomas_reassessment'],'Machielsen and Pfeffer, section II, paragraphs associated with notes 56–73. The named readers distinguish theoretical borrowing from ethnographic accumulation and retain Geertz’s objection; no direct reading of the original 1963 manifesto is claimed.'),
        edge('culture','Investigates past belief and its meanings while exposing contested categories of religion, magic and historical change.',['tc232_thomas_reassessment'],'Reassessment opening and section III, notes 111–121. Contribution records a critically assessed inquiry, not acceptance of its decline narrative or its categories as timeless.'),
        edge('revival','Provides Stone with an example of arranging historical stories around an argument.',['stone_revival'],'Existing source’s bounded primary Stone reading, pp. 3–6 and 13–24 only, and the preserved Keith Thomas roster context. Not Thomas’s assent to all of Stone’s narrative-revival diagnosis.')],
 contexts={'anthropology':'accept with the reassessment’s limits: theoretical engagement and ethnographic accumulation are differentiated',
           'culture':'accept: the named readers explicitly examine meanings and historical categories, with criticism retained'},
 passages=[passage('tc232_thomas_reassessment','Opening; section II, notes 56–73; section III, notes 111–121','Named substantive reading and methodological criticism; original books and exchange remain unread.'),
           passage('stone_revival','Previously read pp. 3–6 and 13–24 only','Existing narrative-debate context, not a new reading.','baseline_documented_reading')],
 birth=1933, status='living', life_sources=[life('https://www.thebritishacademy.ac.uk/fellows/profiles/keith-thomas-FBA/','British Academy, Sir Keith Thomas','Summary and Current post','Birth year 1933; present honorary fellow account supports living status.')],
 life_limits='Current professional description, not a civil-register search; birth year stays research-only.')

person('john_h_elliott',
 description='A historian of early modern Spain, Europe and the Americas. His work moves between political choices within composite monarchies and comparisons across imperial settings. In his Making History interview, he explains comparison as a way to challenge national exceptionalisms and discusses the autonomy possible within composite polities. Empires of the Atlantic World places British and Spanish America within a comparative inquiry. This entry uses bounded interview extracts and institutional bibliographies; it does not infer a global framework from the mere presence of two empires or present the selected books as fully read.',
 works='Imperial Spain, 1469–1716 (1963); “A Europe of Composite Monarchies” (1992); Empires of the Atlantic World: Britain and Spain in America, 1492–1830 (2006).',
 scope='Only indexed primary interview passages on comparison, exceptionalisms and composite monarchy are read; direct full-transcript access returned 403 and was not retried by another route. Book bodies and the 1992 article body remain unread. The IHR profile’s inconsistent 1929/1930 birth labels are not used; the British Academy supplies 1930.',
 old=[],
 sources=[source('elliott_interview','Danny Millum, interview with Sir John Elliott, Institute of Historical Research, Making History project.','https://archives.history.ac.uk/makinghistory/resources/interviews/Elliott_John.html','Indexed primary transcript passages only: JE answer beginning Marc Bloch made a famous speech and final answer discussing composite monarchy/autonomy. Direct full opening returned 403; no full transcript or audio reading/listening. Bloch’s speech is an interview reference, not an established direct influence at the time Elliott first used comparison.'),
          source('elliott_ba','British Academy, Sir John Elliott FBA: memorial profile and books.','https://www.thebritishacademy.ac.uk/fellows/profiles/john-elliott-FBA/','Birth 1930, death 2022 and bibliography for Imperial Spain 1963/Empires 2006 checked. Professional identity matches author and institutional roles. No full book reading.',True),
          source('elliott_composite','J. H. Elliott, “A Europe of Composite Monarchies,” Past & Present 137 (November 1992): 48–71.','https://doi.org/10.1093/past/137.1.48','Publisher article and issue records checked for author, original November 1992 date, pp. 48–71 and DOI. Article body unread; metadata supplies no passage evidence.',True),
          source('elliott_lmh','Lady Margaret Hall, “In memory of Sir John Elliott (1930–2022).”','https://www.lmh.ox.ac.uk/news/memory-sir-john-elliott-1930-2022','Institutional memorial opening and discussion of Empires/composite monarchies checked in indexed text. Death stated as 10 March in the 2022 notice; life years in heading. Full books unread.')],
 events=[event('elliott_spain','Imperial Spain, 1469–1716',1963,['tc232_elliott_ba'],'Original 1963 publication.'),
         event('elliott_composite','“A Europe of Composite Monarchies”',1992,['tc232_elliott_composite'],'Publisher gives original November 1992, distinct from later collected reprints; body unread.'),
         event('elliott_empires','Empires of the Atlantic World',2006,['tc232_elliott_ba'],'2006 comparative study; complete book unread.')],
 edges=[edge('atlantic','Compares British and Spanish American empires as a way to question exceptionalist national histories.',['tc232_elliott_interview','tc232_elliott_lmh'],'Indexed primary interview answer on comparison and exceptionalisms; LMH memorial explicitly identifies the comparative Atlantic book. The book’s body remains unread; no specific conclusion about imperial similarities or differences is certified.'),
        edge('political','Uses composite monarchy to examine autonomy within larger structures of political rule.',['tc232_elliott_interview'],'Indexed primary answer on composite monarchy and political coalitions. His contemporary analogy is not a policy prescription adopted by the atlas; the 1992 article body remains unread.')],
 contexts={'atlantic':'accept: the interview’s comparative method and institutional account explicitly identify the Atlantic comparison',
           'political':'accept: primary interview discusses political structure and autonomy in composite monarchies',
           'global':'hold: comparison of Atlantic empires does not by itself establish the atlas’s broader global-history claims'},
 passages=[passage('tc232_elliott_interview','Indexed JE answers beginning Marc Bloch made a famous speech; For instance, the idea of the composite monarchy','Two bounded primary extracts only.','indexed_primary_extract'),
           passage('tc232_elliott_lmh','Opening and paragraph on Empires of the Atlantic World','Institutional account identifies the comparative book and its 2006 date.','indexed_supporting_passage')],
 birth=1930, death=2022, death_date='2022-03-10', status='deceased',
 life_sources=[life('https://www.thebritishacademy.ac.uk/fellows/profiles/john-elliott-FBA/','British Academy, Sir John Elliott','Life-date fields','Birth 1930 and death 2022.'),life('https://www.lmh.ox.ac.uk/news/memory-sir-john-elliott-1930-2022','Lady Margaret Hall memorial','Opening','Death 10 March 2022.')],
 life_limits='British Academy resolves the inconsistent birth-year labels on the IHR profile. Exact birth day not established here.')

person('john_m_mackenzie',
 description='A historian of empire whose cultural and environmental studies connect imperial power with life in Britain and overseas. As founding editor of Studies in Imperialism, he helped make metropolitan culture a central problem of imperial history. Alison Frank Johnson reads The Empire of Nature as connecting hunting and conservation to British rule in Africa and India. His work is also contested: Edward Said’s review of Catherine Hall criticizes an approach associated with MacKenzie that treats culture as propaganda. That specific criticism is retained without making MacKenzie’s method identical to Hall’s or treating cultural imperial history as membership in British cultural studies.',
 works='Propaganda and Empire (1984; paperback 1986 distinct); Imperialism and Popular Culture (edited collection, 1986; later paperback 1987 distinct); The Empire of Nature (1988; later 1997 edition distinct); Orientalism: History, Theory and the Arts (1995).',
 scope='Series programme read at the publisher; Alison Frank Johnson’s selected substantive discussion of the environmental work read. Said’s criticism reuses the baseline’s documented 2003 review reading. The four book bodies remain unread; the publisher memorial’s paperback/reissue dates are not adopted as original dates. Direct arguments in Orientalism and the Porter exchange remain held.',
 old=['w1_said_always_on_top_2003'],
 sources=[source('mackenzie_series','Manchester University Press, Studies in Imperialism: series programme.','https://manchesteruniversitypress.co.uk/series/studies-in-imperialism/','About the series, first two paragraphs and founding-editor credit read. Publisher’s present account attributes its originating cultural programme to MacKenzie. This is institutional/editorial testimony, not a whole-book reading or evidence that every contributor followed an identical method.'),
          source('mackenzie_johnson','Alison Frank Johnson, “Europe without Borders: Environmental and Global History in a World after Continents,” Contemporary European History 31:1 (February 2022): 129–141; online 16 September 2021.','https://doi.org/10.1017/S096077732100028X','Selected discussion beginning As a historian of the British Empire, through MacKenzie’s environmental turn, plus notes 23–25 read. Named substantive reader, not MacKenzie’s own words read directly in the 1988 book. Original Empire of Nature 1988 distinguished from 1997 lectures/reissues. No Indigenous community narratives used.'),
          source('mackenzie_memorial','Manchester University Press, “Celebrating the life and contribution of John M MacKenzie,” 23 September 2026.','https://manchesteruniversitypress.co.uk/blog/2026/09/23/remembering-john-m-mackenzie/','Opening professional memorial and life years checked: 1943–2026; original Propaganda and Empire explicitly 1984. Final sales list mixes later editions (1986, 1987, 1997) and is not a first-edition bibliography. Only year precision for death.'),
          source('mackenzie_popular','John M. MacKenzie, ed., Imperialism and Popular Culture (Manchester University Press, 1986): original-publication witness.','https://www.cambridge.org/core/books/british-end-of-the-british-empire/introduction/12B3EC4281C390551A0297D46F7B4C34','Publisher-hosted introduction, note 36, checked for editor credit and original 1986 date. The edited volume body is unread; the later publisher sales list’s 1987 is not adopted as first publication.',True)],
 events=[event('mackenzie_propaganda','Propaganda and Empire',1984,['tc232_mackenzie_memorial'],'Original 1984 explicitly stated in memorial opening; 1986 paperback distinct.'),
         event('mackenzie_popular','Imperialism and Popular Culture: edited collection',1986,['tc232_mackenzie_popular'],'Editor credit retained; 1986 publication witness distinct from later sales date.'),
         event('mackenzie_nature','The Empire of Nature',1988,['tc232_mackenzie_johnson'],'Johnson’s note 23 gives 1988 original; 1997 lectures/reissues not backdated.')],
 edges=[edge('culture','Makes the cultural effects of imperialism within dominant societies an explicit research programme.',['tc232_mackenzie_series'],'Publisher series programme, opening paragraph and founding-editor credit. Editorial/institutional testimony supports a specific contribution, not a claim that every Briton was equally imperialist.'),
        edge('environment','Connects hunting and conservation to imperial power and environmental change.',['tc232_mackenzie_johnson'],'Johnson’s selected substantive discussion and notes 23–25. Attribution remains mediated by this named reader; original monograph and later autobiographical essay unread.'),
        edge('john_m_mackenzie','Criticizes treating culture as imperial propaganda rather than analysing its relation to colonial violence.',['w1_said_always_on_top_2003'],'Existing documented complete Said review of Hall, 2003: its paragraph associates a propaganda approach with John MacKenzie. Scope is that criticism in the review; do not transfer Said’s other criticisms of Hall or assume a new reading of MacKenzie’s books.','critique','edward_said')],
 contexts={'post':'hold affiliation: Said’s criticism supplies a contested cross-field link, not evidence that MacKenzie adopted a postcolonial position',
           'environment':'accept: Johnson gives a substantive account of the environmental monograph',
           'culturalstudies':'reject affiliation: cultural imperial history does not establish membership in British cultural studies; add the broader culture context instead',
           'culture':'accept alternative: publisher series programme explicitly supports the cultural contribution'},
 passages=[passage('tc232_mackenzie_series','About the series, opening two paragraphs','Institutional/editorial programme attributed to the founding editor.'),
           passage('tc232_mackenzie_johnson','Paragraphs beginning As a historian of the British Empire; notes 23–25','Named reading of environmental work, with original date.'),
           passage('w1_said_always_on_top_2003','Previously documented complete review; culture/propaganda paragraph','Specific Said criticism of a MacKenzie-associated approach, not all criticism of Hall.','baseline_documented_reading')],
 birth=1943, death=2026, status='deceased', life_sources=[life('https://manchesteruniversitypress.co.uk/blog/2026/09/23/remembering-john-m-mackenzie/','Manchester University Press memorial','Opening paragraph, published 23 September 2026','Life years 1943–2026 and explicit notice of death.')],
 life_limits='Death established at year precision only. Publication date of the memorial is not the death date.')

person('callum_g_brown',
 description='A social and cultural historian of religion and nonreligion in Scotland, Britain and other western societies. The Death of Christian Britain challenges a long, gradual account of secularization by emphasizing a rupture in the 1960s. In his Glasgow research statement, Brown describes the gendered and discursive character of religious identity and advocates combining documentary research, oral history, quantitative methods and discourse analysis. These are his stated methods and interpretations, not a consensus account of secularization. His Canadian roster context remains a comparison with Canadian scholarship rather than a claim that the British book is a Canadian national history.',
 works='Religion and Society in Scotland since 1707 (1997, publisher labels edition 2); The Death of Christian Britain (2001; second edition 2009 distinct); Postmodernism for Historians (2005); Religion and Society in Twentieth-Century Britain (2006).',
 scope='Primary Glasgow research statement read; selected book dates checked in publisher/institutional records. Complete books remain unread. Glasgow’s narrative says 2000 for Death, while its 2001/2009 bibliography and first-edition publisher listing support 2001; the discrepancy is recorded. The garbled citation key is retained only in the research bridge and does not change the historian’s identity.',
 old=['crr_brown_2001'],
 sources=[source('brown_glasgow','Callum G. Brown, University of Glasgow: research statement and bibliography.','https://www.gla.ac.uk/schools/humanities/staff/callumbrown/','Primary Research interests paragraphs and bibliography checked. Explicitly supports mixed methods and gendered/discursive religious identity; current research activity and 2025 publication listed. Narrative’s 2000 date for Death conflicts with the first-edition 2001 witness, so is not adopted. Its early Becoming Atheist date is also not used. No full book reading.'),
          source('brown_death','Callum G. Brown, The Death of Christian Britain, first edition (Routledge, 2001): publisher record.','https://www.routledge.com/The-Death-of-Christian-Britain/Brown/p/book/9780415181495','Indexed first-edition record checked for 2001 and summary’s 1960s rupture. Direct opening 403; no bypass or whole-book reading. Distinct from 2009 second edition and later ebook dates.',True),
          source('brown_scotland','Callum G. Brown, Religion and Society in Scotland since 1707 (Edinburgh University Press, 1997), edition 2 listing.','https://edinburghuniversitypress.com/book-religion-and-society-in-scotland-since-1707.html','Publisher record gives October 1997 and edition 2. This title is not silently dated to the earlier differently titled The Social History of Religion in Scotland since 1730. Book body unread.',True),
          source('brown_birth','University of Strathclyde Archives and Special Collections, Callum Brown authority record.','https://atom25.lib.strath.ac.uk/brown-callum-b-1953-historian','Institutional authority heading gives birth 1953; career description identifies Glasgow/Dundee/Strathclyde historian and matching publications. Birth year, not living evidence.',True)],
 events=[event('brown_scotland','Religion and Society in Scotland since 1707: listed edition 2',1997,['tc232_brown_scotland'],'1997 edition as expressly labelled by publisher; no claim that its differently titled predecessor first appeared then.',track='editions'),
         event('brown_death','The Death of Christian Britain: first edition',2001,['tc232_brown_death'],'First-edition publisher record supports 2001 despite Glasgow narrative’s 2000.'),
         event('brown_postmodern','Postmodernism for Historians',2005,['tc232_brown_glasgow'],'Glasgow bibliography gives 2005; book unread, so no specific epistemological position inferred.'),
         event('brown_society','Religion and Society in Twentieth-Century Britain',2006,['tc232_brown_glasgow'],'Bibliography identifies original Pearson/Longman 2006; later Routledge edition distinct.')],
 edges=[edge('cdn_religion_reform','Offers a British comparison that challenges gradual secularization through a proposed 1960s rupture.',['crr_brown_2001','tc232_brown_glasgow'],'Existing bounded summary plus Brown’s primary Glasgow research statement. Retain comparison status in the existing roster; contribution arrow records the comparative resource, not a Canadian national-history claim.'),
        edge('culture','Combines discourse analysis with oral, documentary and quantitative research in the cultural history of religious identity.',['tc232_brown_glasgow'],'Primary Research interests opening and methods paragraphs. Brown’s stated programme, not proof that every selected book equally employs all four methods.')],
 contexts={'truthdebate':'hold: the title Postmodernism for Historians and use of discourse analysis do not establish a particular position in the atlas’s debate; body unread',
           'culture':'accept alternative: primary research statement explicitly identifies cultural history and combined methods'},
 passages=[passage('tc232_brown_glasgow','Research interests, opening/methods paragraphs and secularization retrospective','Primary methodological statement; bibliography is separately metadata.'),
           passage('crr_brown_2001','Existing recorded summary','1960s rupture interpretation, not new full-book reading.','baseline_documented_reading')],
 birth=1953, status='living', life_sources=[life('https://atom25.lib.strath.ac.uk/brown-callum-b-1953-historian','Strathclyde Archives, Callum Brown','Authorized name and Dates of existence','Birth year 1953; historian identity matched through career and title.'),life('https://www.gla.ac.uk/schools/humanities/staff/callumbrown/','Glasgow, Callum Brown','Current research statement and 2025 bibliography','Explicit current research/publishing and supervision provide positive activity evidence.')],
 life_limits='1953 is year precision only. Current activity supports living status; birth year is withheld from entry prose/export.')


def write(path, value):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    if G['revision_history'][-1]['version'] != '1.231':
        raise ValueError('Baseline changed; rebase/renumber this unaccepted proposal explicitly.')
    if set(SPECS) != {p['person_id'] for p in Q['persons']}:
        raise ValueError('Queue coverage mismatch')
    bridge = []
    for selection in Q['persons']:
        pid = selection['person_id']; sp = SPECS[pid]
        edges = []
        for i, e0 in enumerate(sp['edges'], 1):
            e = dict(e0); origin = e.pop('origin') or pid
            e.update(source=origin, proposal_id=f'tc232_{pid}_{i}', directed=e['relationship_kind'] != 'comparison',
                     type='critique' if e['relationship_kind'] == 'critique' else 'connection', classification_basis='editorial_review')
            edges.append(e)
        new = pid not in PEOPLE
        pu = dict(id=pid, label=selection['name'], node_id=pid, new=new)
        if new:
            pu['identity_note'] = 'Author identified through the matching institutional professional account and publications in this packet. Queue-supplied person ID retained; no namesake union inferred.'
        life_only_ids = {'tc232_christie_bnf','tc232_rosenwein_authority','tc232_bourke_birth','tc232_brown_birth'}
        graph_sources = [s for s in sp['sources'] if s['id'] not in life_only_ids]
        source_ids = list(dict.fromkeys(sp['old'] + [s['id'] for s in graph_sources]))
        node = dict(id=pid, label=selection['name'], layer='historians', entry_kind='person', entry_type=selection['entry_type'],
                    period=None, hunt_core_paradigm=False,
                    date_label=' · '.join(f"{e['label']} ({e['date']['year']})" for e in sp['events']),
                    description=sp['description'], representative_figures_and_works=sp['works'], source_ids=source_ids,
                    scope_note=sp['scope'], chronology=dict(version=1,label='Selected publications and editions',
                    selection_note='Selected work milestones, not a lifespan or continuous career. Original publications, edited collections and later editions retain separate dates and credits.',
                    events=sp['events'],intervals=[],continuation=dict(status='not_asserted',basis='Selected publications do not establish a continuous interval or endpoint of scholarly activity.'),
                    interpretation='Argument claims retain primary, indexed-extract, named-reader and inherited reading limits; bibliographic witnesses establish publication facts only.',
                    prepared_on=DAY,editorial_record='data/production-batches/person-entries-1.232/acceptance.json'))
        additions=[]
        for ctx, decision in sp['contexts'].items():
            if not decision.startswith('accept:') and not decision.startswith('accept alternative:') and not decision.startswith('accept with'):
                continue
            if ctx in selection['existing_context_ids']: continue
            matching = [e for e in edges if e['source']==pid and e['target']==ctx and e['relationship_kind']=='contribution']
            if len(matching) != 1: raise ValueError('New roster needs one scoped contribution: '+pid+'/'+ctx)
            e=matching[0]
            additions.append(dict(node=ctx, proposal_id=e['proposal_id'], row=dict(person_id=pid,role='historian',context=e['relationship'],
                    works=sp['works'],source_ids=e['source_ids'],basis='source_review')))
        draft=dict(status='proposal_for_review',prepared=DAY,applies_to='Baseline 1.231 to candidate 1.232',review_status='needs_independent_review',
                   node=node,people_update=pu,proposed_edges=edges,new_sources=graph_sources,source_addenda={},roster_additions=additions,
                   edges_considered_not_proposed=[f'{k}: {v}' for k,v in sp['contexts'].items() if not v.startswith('accept')])
        # These are provenance leads, not fresh authority checks or graph identity fields.
        identity=dict(qid=selection['qid'],origin='User queue/brief',fresh_check_status='not_checked',
                      attempted_method='Special:EntityData; local robots policy disallows the route. SPARQL endpoint robots retrieval returned 403. Neither restriction bypassed.',
                      grounding='Matched institutional professional identity and works, with the brief’s namesake decisions retained.')
        existing=[]
        for n in G['nodes']:
            rows=[r for r in n.get('representative_people',[]) if r['person_id']==pid]
            if rows:existing.append(dict(node=n['id'],rows=rows))
        note=dict(person_id=pid,label=selection['name'],selection=selection,identity=identity,existing_coverage=existing,
                  reading_limit=sp['scope'],passage_checks=sp['passages'],existing_source_ids_reused=sp['old'],new_source_scopes=graph_sources,
                  research_only_life_witnesses=[s for s in sp['sources'] if s['id'] in life_only_ids],
                  context_decisions=sp['contexts'],relations=edges,events=sp['events'],life_status_record=f'{pid}/life-status.json',
                  reading_bridge_keys=selection['keys_with_counted_works'],review_status='needs_independent_review')
        ls=dict(person_id=pid,label=selection['name'],status=sp['status'],birth_year=sp['birth'],birth_precision='day' if sp.get('birth_date') else 'year',
                death_year=sp.get('death'),death_precision=('day' if sp.get('death_date') else 'year') if sp.get('death') else None,
                checked_on=DAY,sources=sp['life_sources'],limits=sp['life_limits'],
                export_rule='Withhold birth year when no death is recorded unless born more than 120 years ago. Do not place such birth years in entry prose.')
        for k in ['birth_date','death_date']:
            if sp.get(k):ls[k]=sp[k]
        write(HERE/pid/'entry-draft.json',draft);write(HERE/pid/'research-notes.json',note);write(HERE/pid/'life-status.json',ls)
        for key in selection['keys_with_counted_works']:
            bridge.append(dict(key=key,person_id=pid,entry_id=pid,counting_scope='Dated strict History PhDs; first-author works; queue build 2026-10-30. Selection only, never influence evidence.',
                               work_leads=selection['bibliography_leads'],namesake_qualification=selection['note'],entry_draft=f'{pid}/entry-draft.json'))
    write(HERE/'reading-bridge.json',dict(schema='timeline_reading_bridge/1',status='proposal_for_review',source_queue=str(QUEUE.relative_to(ROOT)),rows=bridge))
    write(HERE/'batch.json',dict(revision=REV,baseline_revision='1.231',date=DAY,batch_dir='person-entries-1.232',persons=[p['person_id'] for p in Q['persons']],extras=[],
          summary='Add ten individually sourced timeline entries from the dissertation-selected queue, with bounded contributions and criticism, additive contexts, publication chronology and separate life evidence.',
          authorization='User said continue on 31 October after reading SOL-BRIEF. Research packet only; Claude reviews and accepts. No canonical application, docs build, commit or push authorized by this packet.',
          rationale='Selection counts are not influence evidence. Existing identities and editorial qualifications stay; new people are required only for Elliott and MacKenzie. Context proposals are reviewed individually, with holds and alternative contexts recorded. OpenAlex remains paused.'))
    write(HERE/'research-notes.json',dict(status='proposal_for_review',baseline_revision='1.231',revision=REV,
          selection_source=str(QUEUE.relative_to(ROOT)),brief='data/field-research/timeline-candidates-2026-10-30/SOL-BRIEF.md',
          independent_review='Pending Claude acceptance. No independent review or canonical application claimed.',
          preservation='Graph and docs are pinned in protected-manifest.json. Candidate transformation is performed in memory only.',
          source_policy='Authorized publisher, institutional, repository and author routes only. Denials respected. Historical source notes are retained without reopening the paused investigation.',
          ocap='Professional arguments and methodology only; no oral narratives, teachings, narrator quotations or community genealogies. Trigger is not rostered as Indigenous-authored.',
          reading_bridge='reading-bridge.json lists every keys_with_counted_works value, including four Miller variants and Brown’s garbled key.'))
    runpy.run_path(str(ROOT/'data/extension-2026/timeline-canon-batches-2026-10-31/apply-quality-upgrades.py'),run_name='quality_upgrade')['apply_batch'](1)
    print('Prepared',len(SPECS),'person drafts and',len(bridge),'reading-bridge rows; no canonical writes.')


if __name__=='__main__':
    main()
