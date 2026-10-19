# Evidence: Eric Hobsbawm (1917–2012), later career and reception (post-2000 wave 2)

Research phase only. No graph edits, no git. Compiled 2026-10-18 against the live graph `historiography-1920-2000.json` (revision 1.145). New source id prefix: `w2_hob_`.

**Reading labels used:** read in full; read in part (pages/sections); publisher excerpt; abstract only; mediated (reader named); metadata only. "WebFetch extraction" = text obtained through the WebFetch tool's extraction, no pagination visible.

---

## 0. Atlas state checked (python on the live graph)

**Node `eric_hobsbawm`**
- date_label: "Labouring Men 1964 · The Invention of Tradition, coedited, 1983"
- description: "Studies labour, popular protest, capitalist transformation and national identifications across different scales. Cultural evidence and explanatory synthesis coexist; his responses to criticism revise some claims while retaining others."
- representative_figures_and_works: "Labouring Men (1964); with Terence Ranger, The Invention of Tradition (1983); response to Stone on narrative (1980)."
- scope_note: "The 1980 narrative reply, Bandits in its revised 2000 form, and Nations and Nationalism (1990/1992) distinguish debate, self-revision and historical synthesis. Later concessions about myth and political power are not projected into 1969. Colombian interlocutors and European comparative models supply named resources. Labouring Men and the main nationalism cases remain unread; selected primary support does not audit his entire career or generalizations."
- source_ids: hobsbawm_labouring, hobsbawm_ranger, hobsbawm_revival, hobsbawm_historians_group, hobsbawm_bandits_revised, hobsbawm_nations_primary.
- chronology (3 events, label "Selected contributions · 1964–1983"): `event_33f70ef447fd` Labouring Men 1964; `event_ad7acfd6df28` Bandits 1969; `event_49c108985ab5` The Invention of Tradition 1983. **No point after 1983; none after 2000.**

**Edges touching `eric_hobsbawm` (17)** — none carries a `target_strand`.
| id | source → target | type / kind | sources |
|---|---|---|---|
| edge_322 | eric_hobsbawm → marx | connection / contribution | hobsbawm_labouring, _ranger, _revival, _historians_group, _bandits_revised |
| edge_494 | christopher_hill → eric_hobsbawm | connection / contribution | hobsbawm_revival |
| edge_495 | fernand_braudel → eric_hobsbawm | connection / contribution | hobsbawm_revival |
| edge_496 | geertz → eric_hobsbawm | connection / contribution | hobsbawm_revival |
| edge_497 | eric_hobsbawm → revival | critique / critique | hobsbawm_revival |
| edge_498 | anthropology → eric_hobsbawm | critique / critique (Blok) | hobsbawm_bandits_revised |
| edge_499 | social → eric_hobsbawm | connection / contribution (Sánchez, Meertens) | hobsbawm_bandits_revised |
| edge_500 | eric_hobsbawm → social | connection / contribution | hobsbawm_bandits_revised |
| edge_501 | nationalismstudies → eric_hobsbawm | connection / contribution (Gellner, Hroch) | hobsbawm_nations_primary |
| edge_502 | eric_hobsbawm → nationalismstudies | critique / critique (Gellner) | hobsbawm_nations_primary |
| edge_503 | eric_hobsbawm → nationalismstudies | connection / contribution | hobsbawm_nations_primary |
| edge_644 | gramsci → eric_hobsbawm | connection / contribution | hobsbawm_great_gramsci |
| edge_678 | eric_hobsbawm → truthdebate | connection / contribution (manuscript reader, 1994) | appleby_hunt_jacob |
| edge_738 | eric_hobsbawm → labourhistory | connection / contribution | hobsbawm_labouring |
| edge_917 | dipesh_chakrabarty → eric_hobsbawm | critique / critique (2000) | post, pe132_*, guha_elementary |
| edge_979 | ranajit_guha → eric_hobsbawm | critique / critique (1983) | guha_elementary, pe132_*, pe137_*, post |
| edge_1065 | catherine_hall → eric_hobsbawm | critique / critique (2014) | w1_hall_gendering_property_2014 |

Note: existing pairs already used (both directions) that a new edge must not duplicate by type: Hobsbawm→marx (connection), Hobsbawm→revival (critique), Hobsbawm→social (connection), social→Hobsbawm (connection), nationalismstudies→Hobsbawm (connection), Hobsbawm→nationalismstudies (connection AND critique), Hobsbawm→truthdebate (connection), Hobsbawm→labourhistory (connection), anthropology→Hobsbawm (critique), and the person critiques.

Group edges whose text names Hobsbawm (not touching his node): edge_080 marx→social; edge_194 marx→newleft (Gutman); edge_229 marx→nationalismstudies ("Hobsbawm and Anderson…").

**Roster rows naming him (person_id eric_hobsbawm)**: `marx` (edge_id edge_322); `social` (no edge_id); `revival` (role critic); `nationalismstudies`; `truthdebate` (manuscript reader); `labourhistory`. Strands with him: marx/labour; social/class; social/bandit_debate; revival/analysis_presentation; revival/story_argument; nationalismstudies/traditions; labourhistory/class_experience.
**No roster row** on: historicalsociology, global, political, intellectualhistory, memory, nationaltradition, historyworkshop, economic, post, subaltern.

**People records**: eric_hobsbawm exists (node_id). perry_anderson, richard_j_evans, gareth_stedman_jones, terence_ranger, michael_mann exist. **No** tony_judt, neal_ascherson, terry_eagleton.

**Existing source records:** existing source links are handled by a separate cleanup. `pe132_hobsbawm_primitive_rebels` is Open Library metadata only (text not read).

---

## 1. Access and routes

- **Opened (official pages, curl + HTML text extraction unless noted; no pagination on web pages):**
  - NYRB: Judt 1995 review (complete); Hobsbawm, "The New Threat to History" 1993 (complete).
  - LRB: Anderson 2002 (complete); Eagleton 2011 (complete).
  - *The Guardian* obituary, 1 Oct. 2012 (complete).
  - *Times Higher Education*: Morgan's *Fractured Times* review, 11 Apr. 2013 (complete); conference report "Hobsbawm's contribution to academia celebrated", 3 May 2014 (complete).
  - Cambridge Core open reader: Mayer's review of Evans, *IRSH* 2020 (complete).
  - *Historein* 4 (2003–4), open access (CC BY-NC-SA 4.0) PDF from the journal's EKT platform: Lawrence Black's review of *Interesting Times*, pp. 215–217 read.
  - *Jacobin*: Palmer 2020, opening paragraphs only (paywall).
  - Publishers Weekly page for *On History* (WebFetch summary only).
  - Hachette India page for *Globalisation, Democracy and Terrorism* (WebFetch summary of blurb).
  - Crossref and OpenAlex metadata/abstracts (no mailto sent).
  - Wikidata MCP: Tony Judt only (search_items + get_statements).
- **Blocked or not used:**
  - *Catalyst* URL for Palmer's full review: 404.
  - History Today review of Evans (403).
  - Google Books API: quota exhausted, so no *On History* or *Primitive Rebels* preview.
  - *Le Monde diplomatique* French page for the 2004 "manifesto": 404. No authorised full text was located, so it is not used.
  - OUP product page for *History after Hobsbawm*: empty.
  - Foreign Affairs capsule review (Fukuyama 1995): text not extractable.
  - Guardian/Observer review of Evans (Ascherson): URL not found.
- **Not read: every Hobsbawm book named below** (*Primitive Rebels*, the four Age of… volumes, *Industry and Empire*, *On History*, *Interesting Times*, *Globalisation, Democracy and Terrorism*, *How to Change the World*, *Fractured Times*), plus Evans's biography. All are dated and characterised through the named readers recorded below. **Only primary text newly read in full:** "The New Threat to History" (1993).

## 2. Sources read

### 2a. Tony Judt, "Downhill All the Way," *New York Review of Books*, 25 May 1995 (page datePublished 1995-05-25; volume/issue not checked) — review of *The Age of Extremes: A History of the World, 1914–1991* (Pantheon, 627 pp., per the NYRB book header)

- URL: https://www.nybooks.com/articles/1995/05/25/downhill-all-the-way/
- **Reading label: read in full** (complete text and endnotes obtained from the NYRB page HTML by curl and text extraction; no print pagination visible). A short middle passage (on Hobsbawm's admissions of error) was skimmed rather than read closely.
- Quotations (exact; no page numbers available):
  - The "Hobsbawm generation": "Among historians in the English-speaking world there is a discernible “Hobsbawm generation.” It consists of men and women who took up the study of the past at some point in the “long nineteen-sixties,” between, say, 1959 and 1975, and whose interest in the recent past was irrevocably shaped by Eric Hobsbawm’s writings, however much they now dissent from many of his conclusions."
  - Primitive Rebels: "*Primitive Rebels*, which first appeared in 1959, introduced young urban students to a world of rural protest in Europe and overseas that has now become much more familiar to us, in large measure thanks to the work of scholars whose imaginations were first fired by Hobsbawm’s little book." (Judt's dating and characterisation; *Primitive Rebels* itself unread.)
  - British books: "*Labouring Men*, *Industry and Empire* and *Captain Swing* (with George Rude) substantially recast the economic history of Britain and the story of the British labor movement".
  - Trilogy: "his great trilogy on the “long nineteenth century,” from 1789 to 1914, the first volume of which, *The Age of Revolution, 1789–1848*, appeared in 1962. … Its overall scheme, interpreting the era as one of social upheaval dominated by the emergence and rise to influence of the bourgeoisie of northwest Europe, eventually became the “conventional” interpretation, now exposed to steady criticism and revision. It was followed in 1975 by *The Age of Capital* … That book remains, in my view, Hobsbawm’s single greatest work … In *The Age of Empire*, which appeared twelve years later, there was an unmistakable elegiac air".
  - Structure of *Age of Extremes*: three sections, "The Age of Catastrophe" (1914 to Hitler's defeat), "The Golden Age" (c. 1950 to mid-1970s), "The Landslide". Preface quoted: “I avoided working on the era since 1914 for most of my career.”
  - Analytical economic historian: "This book is also a reminder that Eric Hobsbawm is by training and inclination an economic historian, and an analytical one at that. He is at his best when discussing the Depression, or the nature and consequences of the postwar “boom,” and mostly avoids military or political narrative." "His account of the dramatic collapse of Communist regimes in 1989 verges on the economically determinist".
  - Range: "though unashamedly Eurocentric, Eric Hobsbawm has a unique range" (Latin America especially); endnote 2 defends him against reviewers who criticise a Eurocentric world history: "to criticize Hobsbawm, as some reviewers have done, for understanding this and writing accordingly, seems to me incoherent."
  - The critique ("its defect, for there is really only one"): "he is understandably inclined to see the main outlines and conflicts of the era much as he saw them when they were unfolding. In particular, the categories right/left, fascist/Communist, progressive and reactionary seem to be very firmly set, and pretty much as they first presented themselves to Hobsbawm in the Thirties." "the phenomenon of Bolshevism is accorded no critical analytical attention except on its own restricted terms."
  - Eastern Europe: "“real socialism” in the lands between Germany and Russia merits just six pages in a book nearly six hundred pages long"; on the claim that Sovietisation followed US pressure in 1947–48: "To suggest that this process was instituted only as a direct consequence of American intervention … is simply wrong."
  - Nationalism: "nationalism (like religion) is a rather neglected subject in this book. … whatever one thinks of national sentiment (and Hobsbawm accords it very little sympathy, here as in his other works), its place in the history of our time surely merits more than dismissive remarks".
  - Terror: "one longs for a fuller and more historically and humanly sensitive description of the whole tragedy."
  - Verdict: "a challenging, often brilliant, and always cool and intelligent account of the world we have now inherited. If it is not up to his very best work it should be recalled just how demanding a standard he has set." "I missed, in his version of the twentieth century, the ruthlessly questioning eye which has made him so indispensable a guide to the nineteenth."
- Supports: dates and a named reader's characterisation of *Primitive Rebels* (1959), *The Age of Revolution* (1962), *The Age of Capital* (1975), *The Age of Empire* (1987); *Age of Extremes* (1994) as a world history of 1914–91 by an "analytical" economic historian; a named, substantive critique (Communism's categories, Eastern Europe, nationalism). *Age of Extremes* itself is **unread** here except for the preface sentence Judt quotes.

### 2b. Perry Anderson, "The Age of EJH," *London Review of Books* 24:19 (3 October 2002) — review of *Interesting Times: A Twentieth-Century Life* (Allen Lane, Sept. 2002)

- URL: https://www.lrb.co.uk/the-paper/v24/n19/perry-anderson/the-age-of-ejh
- **Reading label: read in full** (complete text from LRB page HTML via curl and text extraction, 6,494 words; no pagination). Also one published letter beneath it (not used).
- Quotations (exact):
  - The memoir as companion to *Age of Extremes*: "Eric Hobsbawm has entered the lists with a work he invites us to read as the ‘flip side’ of *Age of Extremes*, his great history of the 20th century: ‘not world history illustrated by the experiences of an individual, but world history shaping that experience’ … Published at the age of 85 … We are dealing with a kind of fifth volume, in more personal register, of a continuous project."
  - Structure: three parts (youth to Cambridge; CPGB membership "from the late 1930s to its dissolution in the early 1990s"; surveys of profession and travels).
  - Reticence: "Of Hobsbawm’s personal path through it we are told very little: nothing at all of his intellectual development, virtually nothing of his emotional life, scarcely a hint even of his political ideas."
  - On staying in the Party after 1956 (Hobsbawm quoted): "I still belong to the tail-end of the first generation of Communists, the ones for whom the October Revolution was the central point of reference in the political universe." Anderson: "Most people would see in it evidence of an exceptional integrity and strength of character".
  - Criticism, the accounting to an establishment: "the unspoken addressee is as if an established order to which an accounting of the self is due in exchange. This appears to be the logic of that absence of close political discussion, or any real intellectual engagement with the issues that haunted the trajectory of European Communism".
  - Criticism, others' traditions: "His treatment of the traditions of others is much less impressive. Here a lack of generosity disfigures too many judgments." (Raphael Samuel; E. P. Thompson, of whom Hobsbawm says he made a "‘criminal’ diversion of energies into theoretical dispute"; the New Lefts; 1960s student radicals.) "Scarcely an item in this rather sour retrospect withstands careful scrutiny."
  - *Marxism Today* and Labour: Hobsbawm's 1980s campaign "to rescue the Labour Party from the perils of Bennery. Here legitimate pride and fatal delusion are curiously interwoven." "Hobsbawm recounts with relish, but overestimates, his role in the media outcry that finished off Benn". *Marxism Today* "played the role of a sorcerer’s apprentice, not least in preparing the cult of Thatcher as a model of radical government that was taken over with a vengeance by New Labour."
  - On the historiographical part: "He gives a good account of the rise of the analytic social history associated with the Annales and Past & Present at the expense of earlier high-political narratives, regretting its later retreat with the cultural turn of the 1980s." … "To see how original his own thinking about the study of the past has been – more than Braudel’s, by whom he says he was somewhat overawed – one needs to turn to his collection *On History*."
  - Coda: "a magnificent coda on 11 September" … US "global empire"; Hobsbawm "calls on newer generations to shun the fetishes of identity, and make common cause with the poor and weak." Hobsbawm quoted: "‘Let us not disarm, even in unsatisfactory times. Social injustice still needs to be denounced and fought. The world will not get better on its own.’"
  - Verdict: "the abiding impression is of the largeness of this mind, and the complex distinction of the life it reports."
- Supports: *Interesting Times* (Sept. 2002) dated and characterised by a named reader; Anderson's critique of the memoir's politics and of Hobsbawm's judgments of the New Left/Thompson/Samuel; Hobsbawm's own (memoir) account of the rise of Annales/*Past & Present* social history and its "retreat with the cultural turn" — **as reported by Anderson**; *On History* as his main statement on the study of the past (Anderson's judgment). *Interesting Times* itself is **unread**.

### 2c. Eric Hobsbawm, "The New Threat to History," *New York Review of Books*, 16 December 1993 (volume/issue not checked) — PRIMARY

- URL: https://www.nybooks.com/articles/1993/12/16/the-new-threat-to-history/ (page metadata: datePublished 1993-12-16).
- Headnote on the page: "The following lecture was given at the beginning of the academic year at the Central European University, which recently opened in Budapest." Hobsbawm opens: "It is an honor to be asked to open this academic year of the Central European University." → **lecture delivered** (autumn 1993, CEU Budapest; exact day not given) and **published** 16 Dec. 1993.
- **Reading label: read in full** (complete text from the NYRB page HTML by curl; no pagination).
- Catalogue/bookseller listings (not authoritative) give *On History* (1997) an opening chapter "Outside and Inside History"; the opening sentence "So I come to you as an outsider who is also, in an oblique way, an insider" fits that title, but **the identity of the NYRB text with the *On History* chapter is NOT verified** here (Google Books API quota exhausted; no publisher contents page found). Cite the 1993 NYRB text in its own right.
- Quotations (exact):
  - History and nationalist ideology: "For history is the raw material for nationalist or ethnic or fundamentalist ideologies, as poppies are the raw material for heroin addiction. The past is an essential element, perhaps the essential element in these ideologies. If there is no suitable past, it can always be invented."
  - "In this situation historians find themselves in the unexpected role of political actors. I used to think that the profession of history, unlike that of, say, nuclear physics, could at least do no harm. Now I know it can. … We have a responsibility to historical facts in general, and for criticizing the politico-ideological abuse of history in particular."
  - Postmodernism: "the rise of “postmodernist” intellectual fashions in Western universities, particularly in departments of literature and anthropology, which imply that all “facts” claiming objective existence are simply intellectual constructions. In short, that there is no clear difference between fact and fiction. But there is, and for historians, even for the most militantly antipositivist ones among us, the ability to distinguish between the two is absolutely fundamental. We cannot invent our facts. Either Elvis Presley is dead or he isn’t."
  - Interpretation vs fact: denial of the Armenian massacre is dismissed "from serious historical discourse, although there is no equally unambiguous way to choose between different ways of interpreting the phenomenon".
  - Anachronism: "The most usual ideological abuse of history is based on anachronism rather than lies." (Greek claims on Macedonia; Croatian schoolbook history; Ayodhya; Kosovo 1389.)
  - Identity politics: "Myth and invention are essential to the politics of identity by which groups of people today … try to find some certainty in an uncertain and shaking world by saying. “We are different from and better than the Others.”" … "History is not ancestral memory or collective tradition. It is what people learned from priests, schoolmasters, the writers of history books, and the compilers of magazine articles and TV programs. It is very important for historians to remember their responsibility, which is, above all, to stand aside from the passions of identity politics—even if they also feel them."
  - Critique from within (Israel, Ireland): "here we have mythological or nationalist history being criticized from within." "We must resist the formation of national, ethnic, and other myths, as they are being formed. It will not make us popular." (Masaryk and the forged Czech manuscripts.)
- Supports: (i) a Hobsbawm **critique** of postmodernist relativism (truthdebate); (ii) a Hobsbawm **critique** of national myth-making and schoolbook national history (nationaltradition); (iii) a dated lecture event (1993). Note: the critique of postmodernism is stated briefly ("I need say little about the first of these responsibilities"); the lecture's main subject is nationalist abuse of history.

### 2d. *On History* (1997): dating only

- Publishers Weekly review page https://www.publishersweekly.com/9781565843936 (New Press, $25; reviewed 1 Sept. 1997): **read via WebFetch extraction (summary; tool declined verbatim reproduction)**. PW reports 21 reprinted essays and lectures; a major theme is ideological abuse of history by those who blur recorded reality and fiction, which Hobsbawm criticises as postmodernist practice; PW quotes him: "Arguments about counterfactual alternatives cannot be settled by evidence". **Mediated (Publishers Weekly), no exact quotation verified beyond that one sentence as quoted by PW.** Weidenfeld & Nicolson (London) edition also 1997 (Guardian obituary gives "On History (1997)").
- *On History* itself **unread**. Anderson (2002) names it as the place to see "how original his own thinking about the study of the past has been".

### 2e. Martin Kettle and Dorothy Wedderburn, "Eric Hobsbawm obituary," *The Guardian*, 1 October 2012

- URL: https://www.theguardian.com/books/2012/oct/01/eric-hobsbawm . Subtitle: "Historian in the Marxist tradition with a global reach". (Wedderburn died 20 Sept. 2012, before publication, as the page notes.)
- **Reading label: read in full** (curl, HTML text extraction).
- Dates and facts stated (the obituarists' account): born Alexandria 9 June 1917, died 1 October 2012; *Primitive Rebels* 1959 ("his first major work … a strikingly original account, particularly for those times, of southern European rural secret societies and millenarian cultures"); *Labouring Men* 1964; *Industry and Empire* 1968; *Captain Swing* with Rudé; *Bandits*; the Age of… series: *The Age of Revolution: 1789-1848* (1962), *The Age of Capital: 1848-1875* (1975), *The Age of Empire: 1875-1914* (1987), *The Age of Extremes: 1914-91* (1994); "The books were not conceived as a tetralogy"; Companion of Honour 1998; *On History* (1997) and *Uncommon People* (1998); "A highly successful autobiography, *Interesting Times*, followed in 2002, and *Globalisation, Democracy and Terrorism* in 2007"; "In his 94th year he published *How to Change the World*, a vigorous defence of Marx's continuing relevance in the aftermath of the banking collapse of 2008-10"; president of the Hay festival at 93.
- Quotations: "In his later years he became arguably Britain's most respected historian of any kind, recognised if not endorsed on the right as well as the left". The Age of… series "distilled the history of the capitalist world from 1789 to 1991". Neal Ascherson quoted: "Hobsbawm's capacity to store and retrieve detail has now reached a scale normally approached only by large archives with big staffs". *Primitive Rebels*, *Captain Swing* and *Bandits* "are reminders that Hobsbawm was both a bridge between European and British historiography and a forerunner of the notable rise of the study of social history in post-1968 Britain." On politics: "his increasing certainty that the European labour movement had ceased to be capable of bearing the transformational role assigned to it by earlier Marxists. These uncompromisingly revisionist articles were collected under the general heading *The Forward March of Labour Halted*." "he was without question the single most influential intellectual forerunner of Labour's increasingly iconoclastic 1990s revisionism" (obituarists' judgment). Hobsbawm quoted from his "1993 Creighton lecture": "Every historian has his or her lifetime, a private perch from which to survey the world".
- Supports: dates for the whole later career (obituarists' account, not a reading of the books); 1998 CH (office/honour); death 2012.

### 2f. Terry Eagleton, "Indomitable," *London Review of Books* 33:5 (3 March 2011) — review of *How to Change the World: Marx and Marxism 1840–2011* (Little, Brown, 470 pp., January 2011)

- URL: https://www.lrb.co.uk/the-paper/v33/n05/terry-eagleton/indomitable
- **Reading label: read in full** (curl, HTML text extraction; 2,814 words).
- Quotations (exact):
  - Composition: "Most of the pieces collected in this book have been published before, though about two-thirds of them have not appeared in English. … not least three substantial surveys of the history of Marxism from 1880 to 1983. … flanked by other chapters, on such topics as pre-Marxian socialism, Marx on pre-capitalist formations, Gramsci, Marx and labour".
  - Position: "Eric Hobsbawm, who was born in the year of the Bolshevik revolution, remains broadly committed to the Marxist camp – a fact worth mentioning as it would be easy to read this book without realising it. This is because of its judiciousness, not its shiftiness."
  - Marx and the utopians: "Hobsbawm, by contrast, insists on Marx’s substantial debt to these thinkers". The *Manifesto*: "Hobsbawm denies that it is a deterministic document" (Eagleton disputes the inquiry into "what kind of inevitability is at stake"). Hobsbawm quoted: the idea that Marxism leads inevitably to such monstrosities "‘has about as much justification as the thesis that all Christianity must logically and necessarily always lead to papal absolutism, or all Darwinism to the glorification of free capitalist competition’".
  - Engels's *Condition*: claimed "as the first study anywhere to deal with the working class as a whole".
  - Marxism and science in the 1930s (Needham, Bernal), later "ousted by the more cultural and philosophical tenets of so-called Western Marxism".
  - Criticism: "Like many historians he is not at his sharpest in the realm of ideas, and he is wrong to suggest that the disciples of Louis Althusser treated Marx’s *Capital* as though it were primarily a work of epistemology. Nor would Hegel’s Geist treat feminism, not least Marxist feminism, with such cold-eyed indifference, or consign one of the most fertile currents of modern Marxism – Trotskyism – to a few casual asides. Hobsbawm also thinks that Gramsci is the most original thinker produced by the West since 1917."
  - Hobsbawm quoted: "‘If one thinker left a major indelible mark on the 20th century,’ … ‘it was he.’"
- Supports: *How to Change the World* (Jan. 2011) as a history of Marxism and its reception 1840–2011, much of it translated from Italian; a named reader's critique (ideas, feminism, Trotskyism). Book itself **unread**.

### 2g. Roger Morgan, review of *Fractured Times: Culture and Society in the 20th Century* (Little, Brown, 336 pp., published 25 March 2013), *Times Higher Education*, 11 April 2013

- URL: https://www.timeshighereducation.com/node/112584 (page datePublished "April 11, 2013").
- **Reading label: read in full** (curl, HTML text extraction). The page's appended sidebar profile contains an error ("in 2012, aged 94, he would publish *How to Change the World*"; the book appeared January 2011 per LRB and Guardian) — not used.
- Quotations (exact): "the posthumous publication of this stimulating collection of essays … Of the roughly two dozen texts assembled here, some originally appeared in the London Review of Books or elsewhere (some only in German); some began as lectures connected with music festivals or art exhibitions; and several are published for the first time." Hobsbawm quoted: "an era of history which has lost its bearings, and which in the early years of the new millennium looks forward with more troubled perplexity than I recall in a long lifetime, guideless and mapless, to an unrecognisable future". Three forces undermining "classical bourgeois high culture": the science-and-technology revolution, the consumer society, and "the decisive entry of the masses on the political scene as customers as well as voters". Morgan's criticism: the claim about the arts' pre-1914 status "is really enormous. It has to be tackled head on or quietly ignored. Hobsbawm chose the latter course"; on music Hobsbawm is "unfairly castigating concert programmes".
- Supports: posthumous publication 25 March 2013; a reception point April 2013. Book **unread**.

### 2h. David Mayer, review of Richard J. Evans, *Eric Hobsbawm: A Life in History* (Little, Brown / Oxford University Press, New York, 2019; xiii, 785 pp.), *International Review of Social History* 65:3 (2020), published online 19 Nov. 2020, DOI 10.1017/S0020859020000619

- URL: https://doi.org/10.1017/S0020859020000619 (Cambridge Core reader page, open).
- **Reading label: read in full** (Cambridge Core HTML, text extraction; review has no internal pagination; it cites Evans's pages).
- Quotations (exact):
  - "Eric J. Hobsbawm was the most famous historian of the second half of the twentieth century – perhaps not in terms of his significance in any single country or language sphere, yet arguably as somebody read in all major world regions and across many languages."
  - Evans "had full access to the papers from Hobsbawm's estate. These, together with interviews and other abundant archival material (including declassified intelligence reports), allow for an extraordinarily detailed reconstruction".
  - Criticism: "Hobsbawm's ideas get surprisingly little coverage (sometimes it is little more than a blurb). This is not the kind of intellectual biography that offers readers a comprehensive summary of the opus of its subject."
  - "As Bryan D. Palmer pointed out in a recent extended review, Evans is imprecise in writing that, between Hobsbawm and E.P. Thompson, John Saville, Rodney Hilton, and many others there were, as Evans claims, “no real political differences beyond the merely symbolic one of membership in the Party” (p. 351)." Footnote 1: Bryan D. Palmer, "Hobsbawm's Century," *Catalyst* 4:1 (2020), pp. 60–100.
  - Gender: Hobsbawm's family arrangements parallel "the criticism of gender blindness voiced repeatedly about his landmark books."
  - Evans "particularly appreciates the Hobsbawm who, during the 1980s, after publishing the essay “The Forward March of Labour Halted” (1978), became an intellectual catalyst of the defeat of the left within the Labour Party".
  - The global Hobsbawm: "an author with the singular ability to become a point of reference not only for general readers, but also for several generations of historians, not least in the countries of the Global South"; Evans's reviews are "almost entirely by anglophone authors, while the numerous translations are duly mentioned, but only as a list."
- Supports: Evans's 2019 biography (dated; characterised through Mayer); "Forward March of Labour Halted" dated 1978; Palmer's 2020 review (existence and one point, mediated through Mayer). Evans's biography itself **unread**.

### 2i. Bryan D. Palmer, "Eric Hobsbawm's Century," *Jacobin*, 8 July 2020 (also *Catalyst* 4:1, 2020, pp. 60–100, per Mayer)

- URL: https://jacobin.com/2020/07/eric-hobsbawn-life-history-richard-evans (the Catalyst URL cited by Mayer now returns 404).
- **Reading label: publisher excerpt** (first four paragraphs visible before the paywall).
- Quotations (exact): "Were the British Marxist historians a coherent lot, congealed in the sameness of their affiliation to historical materialism?" … "to assume that the British Marxist historians produced histories out of some common template obscures important distinctions relating to research methods, stylistic sensibilities, and analytic orientations." "First among equals in this extraordinary Marxist contingent was Eric J. Hobsbawm. Widely recognized as the world’s premier Marxist historian, Hobsbawm’s intellectual range was unrivaled." "Well received throughout the Global South, where his writings were eagerly translated and sold exceedingly well".
- Supports: very little beyond existence and framing; see §8.

### 2j. Lawrence Black, review of *Interesting Times: A Twentieth-Century Life* (London: Allen Lane / Penguin, 2002; xv + 448 pp.), *Historein* 4 (2003–4), Book Reviews, pp. 215–226 (Black's review begins p. 215); DOI for the section 10.12681/historein.91

- URL: https://doi.org/10.12681/historein.91 (open access, CC BY-NC-SA 4.0, EKT platform PDF).
- **Reading label: read in part**, pp. 215–217 (the review continues; the rest was not read).
- Quotations (exact, with pages):
  - p. 215: "Of the British Marxist historians, Hill might have been the “dean” (423), E.P. Thompson the inspiration, Raphael Samuel the imagination, but in many ways Hobsbawm was the pre-eminent figure. His style was more accessible and range greater, from the detail of political shoemakers to authoritative and commanding overviews of international history from the 18th century to present – the quartet of Age of Revolution, Capital, Empire and Extremes (1962-94)." The memoir "comprises an effective personal companion to The Age of Extremes."
  - p. 215: "He was a founder of what would become a leading historical journal, Past and Present, in 1952, publishing “The Machine Breakers” in its first number; a key protagonist in the standard of living in the industrial revolution debates in economic history from the 1950s, something of a Cold War battleground; through to the “Forward march of Labour halted?” lecture delivered in 1978 on the dawn of the Thatcher era. A modernizer in history’s subject matter (the history from below of workers, rebels and underworlds), Hobsbawm has also influenced historians’ approaches, notably in The Invention of Tradition."
  - p. 215: "The Age of Extremes (1994) has been published in 37 languages."
  - p. 216: "Niall Ferguson (in the Daily Telegraph) has claimed Hobsbawm has skirted the awkward issue of his association with communism in the 20th century. This is not a new charge and has also come from those to the Left, who have pointed out that whilst Soviet communism was “actually existing,” Hobsbawm was chary of writing about it and the period … Thus The Age of Extremes only emerged in 1994, in the post-Soviet world."
  - p. 216: "His acceptance of a Companion of Honour from the Queen in 1998 … chafed with many on the left and is an episode not discussed."
  - p. 217: "In but not of the Communist Party, Hobsbawm was less a British and more an international communist".
- Supports: a second reader of *Interesting Times*; P&P founding (1952) and the standard-of-living debate (an economic-history contribution); the 1978 lecture; CH 1998; translation reach of *Age of Extremes*. Black's quotations of the memoir carry its page numbers (e.g. "(423)").

### 2k. "Hobsbawm’s contribution to academia celebrated," *Times Higher Education*, 3 May 2014 (conference report; reporter not named in the extracted text)

- URL (as read): https://timeshighereducation.com/cn/node/121433 (page datePublished "May 3, 2014"; the canonical www article URL was not checked).
- **Reading label: read in full** (short news report, curl extraction). Speakers' words are **mediated through the reporter**.
- Content and quotations:
  - The "History After Hobsbawm conference, held at Senate House on 29 April to 1 May", opened by John Arnold (Birkbeck). "Subsequent speakers and panellists explored how we can draw on and develop his insights into capitalism and class, protest and property, nationalism and tradition."
  - "Opening the event with the first Hobsbawm Memorial Lecture, Mark Mazower … argued that the historian’s “omnivorous mind, razor-sharp analytic intellect and keen consciousness of the relationship between a writer and his audience” had “radically enrich[ed]” the discipline and inaugurated a continuing “golden age of historical synthesis”."
  - Jan Rüger (convenor): "In his trilogy on the 19th century the two contexts [empire and Europe] are continuously bound up with one another – there is no clear boundary separating Britain and Europe in the Age of Empire."
  - Gareth Stedman Jones: a strong commitment to Marxism "generally mixes badly with the writing of good history", since "what is produced is too often circumscribed or weighed down by a cluster of dogmatic assumptions about exploitation, the nature of capitalism, the development of class struggle and a determinist approach to culture and politics". Yet despite "an untroubled and unapologetic attachment to ‘Marxism’", Hobsbawm combined it with "unending curiosity" about subjects "ranging from ‘the General Crisis of the Seventeenth Century’ to the rise of professional football in Latin America".
- Supports: the 2014 conference as a dated, **delivered** event (report published after it); the first Hobsbawm Memorial Lecture (Mazower, delivered at the opening). Catherine Hall's *HWJ* essay (already in the atlas, `w1_hall_gendering_property_2014`) "started life as a lecture" at this conference. The resulting volume, John H. Arnold, Matthew Hilton and Jan Rüger, eds., *History after Hobsbawm: Writing the Past for the Twenty-First Century* (OUP), is dated 2017 by Southgate's *EcHR* review (DOI 10.1111/ehr.12766, metadata) and 2018 by Price's *JBS* review (DOI 10.1017/jbr.2018.210, metadata). **Metadata only**: the publication year is unsettled (2017 vs 2018).

### 2l. Metadata and abstracts (Crossref/OpenAlex, no mailto)

- E. J. Hobsbawm, "The General Crisis of the European Economy in the 17th Century," *Past and Present* 5 (1954): 33–53, DOI 10.1093/past/5.1.33. Also "Discussion of H. R. Trevor-Roper: 'The General Crisis of the Seventeenth Century' II," *P&P* 18 (1960): 12–14, DOI 10.1093/past/18.1.12. **Metadata only.** See FLAG §9 (transition debate / capitalismdebates).
- E. J. Hobsbawm, "The British Standard of Living 1790–1850," *Economic History Review* 10 (1957), from p. 46, DOI 10.2307/2600061. **Metadata only.**
- Eric Hobsbawm, "Marxist Historiography Today," in Chris Wickham, ed., *Marxist History-writing for the Twenty-first Century* (British Academy, 2007; online 28 June 2007), DOI 10.5871/bacad/9780197264034.003.0008. **Abstract only** (publisher abstract via Crossref): "there has been a rise in the so-called anti-Rankean reaction in history, of which Marxism is an important but not always fully acknowledged element … This new perspective on the past is a return to ‘total history’, in which the focus is not merely on the ‘history of everything’ but history as an indivisible web wherein all human activities are interconnected." According to bookseller and catalogue snippets, Hobsbawm gave a closing address at a British Academy colloquium on Marxist historiography on 13 Nov. 2004. **Not verified** that this is that address, and no lecture event is proposed from it.
- Reviews of *Primitive Rebels* in 1959–60 (Crossref metadata only): *EcHR* 12 (1959), DOI 10.2307/2599319; *British Journal of Sociology* 11 (1960), DOI 10.2307/587051; *AJS* 66 (1960) 97–98, DOI 10.1086/222830 (US title *Social Bandits and Primitive Rebels*). These corroborate the 1959 date. Unread.
- *Globalisation, Democracy and Terrorism*: Hachette India page (Abacus paperback, 3 Apr. 2008, 192 pp.); WebFetch summary of the blurb: essays on globalisation, democracy, terrorism, war and peace, nationalism, the Middle East and Western imperialism. First published 2007 per Guardian obituary (Little, Brown). **Publisher description / mediated.**

---

## 3. Proposed edges

Duplicate checks were run with python against the validator's triple rule (`source, target, type`; `scripts/validate_graph.py` l. 67–69), against all pairs in either direction, and against roster `edge_id`s. **None of the proposed new edges repeats a triple**, so the warning baseline does not grow.

### H1. `eric_hobsbawm` → `nationaltradition`: critique (STRONG)
- type critique; relationship_kind critique; directed true.
- target_strand: `nationaltradition/narration_authority` ("National narratives and the appearance of reality"). Alternative: none. `national_exclusions` is Guha/Chatterjee/Ogot's elite-nationalism critique and is a poorer fit.
- relationship: "History as 'raw material for nationalist or ethnic or fundamentalist ideologies': national myths, anachronism and schoolbook history to be resisted by historians as they form (1993 lecture), the theme of The Invention of Tradition (1983) turned into a professional duty".
- map_label: "Against national myth-making, 1993".
- Evidence: §2c, read in full (primary). Quotations: "For history is the raw material for nationalist or ethnic or fundamentalist ideologies … If there is no suitable past, it can always be invented"; "The most usual ideological abuse of history is based on anachronism rather than lies"; "History is not ancestral memory or collective tradition. It is what people learned from priests, schoolmasters, the writers of history books…"; "We must resist the formation of national, ethnic, and other myths, as they are being formed." The *Invention of Tradition* link rests only on the existing `hobsbawm_ranger` record (publisher description) and the lecture's own "it can always be invented". Do not quote the 1983 introduction, which is unread.
- Sources: `w2_hob_new_threat_1993`; `hobsbawm_ranger`.
- Duplicate check: no edge between `eric_hobsbawm` and `nationaltradition` in either direction. Comparable edges with different endpoints: edge_228 `nationalismstudies → nationaltradition` (critique); edge_977 `ranajit_guha → nationaltradition`; edge_1074 `catherine_hall → nationaltradition`. Hobsbawm's own nationalism-studies edges 501–503 have a different target. No roster `edge_id` clash: Hobsbawm has no `nationaltradition` row.

### H2. `eric_hobsbawm` → `global`: contribution (MODERATE; books unread, readers agree)
- type connection; kind contribution; directed true.
- target_strand: `global/world` ("World-historical synthesis"; McNeill).
- relationship: "The Age of… volumes (1962–1994): a synthesis of 'the capitalist world from 1789 to 1991', world history from a self-declared nineteenth-century historian, praised for range and criticised as Eurocentric (readers 1995–2014)".
- map_label: "The Age of… synthesis, 1962–94".
- Evidence (all **mediated**; the four volumes are unread):
  - **Guardian 2012:** the series "distilled the history of the capitalist world from 1789 to 1991"; "The books were not conceived as a tetralogy".
  - **Judt 1995:** the trilogy's scheme "eventually became the “conventional” interpretation"; "though unashamedly Eurocentric, Eric Hobsbawm has a unique range". His endnote 2 calls it "incoherent" to criticise a world history for centring what Europeans did.
  - **Anderson 2002:** quotes Hobsbawm on *Interesting Times* as the flip side of *Age of Extremes*: "not world history illustrated by the experiences of an individual, but world history shaping that experience".
  - **Black 2003–4, p. 215:** "authoritative and commanding overviews of international history from the 18th century to present".
  - **THE 2014:** Mazower's "golden age of historical synthesis"; Rüger: no clear boundary between Britain and Europe "in the Age of Empire".
- Counterweight to keep in the evidence note: Judt's "unashamedly Eurocentric", and the existing critiques edge_917 (Chakrabarty) and edge_973 (Said on world-historical syntheses; Hobsbawm not named there, so do not link it).
- Sources: `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012`, `w2_hob_anderson_2002`, `w2_hob_black_historein`, `w2_hob_the_conference_2014`.
- Duplicate check: no `eric_hobsbawm`–`global` edge in either direction. No Hobsbawm roster row on `global`.

### H3. `political` → `eric_hobsbawm`: critique, named reader Tony Judt (MODERATE–STRONG)
- type critique; kind critique; directed true. A group-node proxy: Judt has no node. Same pattern as `economic → kenneth_pomeranz` and `intellectualhistory → lynn_hunt` (edge_1058). Add a `political` roster row for Judt (§5).
- target_strand: none (a critique of Hobsbawm, not of a political-history strand).
- relationship: "Judt: The Age of Extremes keeps the categories of the 1930s, gives Bolshevism 'no critical analytical attention except on its own restricted terms', allots Eastern Europe 'just six pages', neglects nationalism and religion, and 'mostly avoids military or political narrative' (1995)".
- map_label: "Judt: Age of Extremes, 1995".
- Evidence: §2a, read in full. Exact quotations as listed there, including "the categories right/left, fascist/Communist, progressive and reactionary seem to be very firmly set, and pretty much as they first presented themselves to Hobsbawm in the Thirties", and "To suggest that this process was instituted only as a direct consequence of American intervention … is simply wrong". Qualification to keep: Judt calls the book "a challenging, often brilliant, and always cool and intelligent account" and the Age of Capital "Hobsbawm’s single greatest work". Judt also praises the economic analysis, so the critique is aimed at political history.
- Why `political` is the proxy: Judt's charge is that the political history (Communism, fascism, Eastern Europe, national sentiment) is weaker than the economic analysis ("distinctly superior to his political surveys"). Judt's own field (postwar Europe, French intellectuals) has no atlas node.
- Optional second reader, if the parent wants a broader edge: Lawrence Black, p. 216, reports Ferguson and critics "to the Left" on his reticence about Soviet communism (mediated through Black). Recommendation: keep the edge Judt-only.
- Sources: `w2_hob_judt_1995`.
- Duplicate check: no `political`–`eric_hobsbawm` edge in either direction. No roster `edge_id`.

### H4. `eric_hobsbawm` → `economic`: contribution (MODERATE; mediated)
- type connection; kind contribution; directed true.
- target_strand: `economic/british` ("British economic and social history"). Do NOT use `economic/marxist`: that is the transition/capitalism-debate region; see flag.
- relationship: "Industrial Britain and its workers: the standard-of-living debate (Economic History Review, 1957) and Industry and Empire (1968), which readers credit with recasting British economic history".
- map_label: "Standard of living and Industry and Empire".
- Evidence (mediated; texts unread):
  - **Judt 1995:** "*Labouring Men*, *Industry and Empire* and *Captain Swing* (with George Rude) substantially recast the economic history of Britain and the story of the British labor movement"; "by training and inclination an economic historian, and an analytical one at that".
  - **Guardian 2012:** "his engagement in the once celebrated 'standard of living' debate about the economic consequences of the early industrial revolution, in which he and RM Hartwell traded arguments in successive numbers of the Economic History Review"; *Industry and Empire* (1968) as "a compelling summation of much of his work on Britain and the industrial revolution".
  - **Black, p. 215:** "a key protagonist in the standard of living in the industrial revolution debates in economic history from the 1950s, something of a Cold War battleground".
  - **Crossref metadata:** *EcHR* 10 (1957), DOI 10.2307/2600061.
  - Existing reading in edge_1065: Hall credits *Industry and Empire* on colonial markets (p. 23).
- Sources: `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012`, `w2_hob_black_historein`, `w2_hob_standard_living_1957` (metadata).
- Duplicate check: no `eric_hobsbawm`–`economic` edge in either direction. Hobsbawm has no `economic` roster row. Not a capitalismdebates edge.
- Caveat for the evidence note: no Hobsbawm economic-history text was read. This is a pre-2000 gap repair, not later work.

### H5 (OPTIONAL / HOLD). `marx` → `eric_hobsbawm`: critique, named reader Perry Anderson (WEAK–MODERATE)
- A within-tradition critique. Anderson (2002) judges the memoir's account of fellow Marxists (Thompson, Samuel, the New Left) "sour". Quotations: "His treatment of the traditions of others is much less impressive. Here a lack of generosity disfigures too many judgments"; "Scarcely an item in this rather sour retrospect withstands careful scrutiny". He also criticises the absence of "any real intellectual engagement with the issues that haunted the trajectory of European Communism".
- Why hold:
  - Anderson's place in the atlas is the `historicalsociology` roster, not `marx`.
  - The critique concerns a memoir's political judgments more than historical method.
  - Anderson also praises Hobsbawm's thinking about history ("more than Braudel’s").
- If used: type critique, kind critique, directed true; no strand; duplicate check passes (only edge_322 `eric_hobsbawm → marx` connection exists). Recommend instead: a reception chronology point and a description sentence (§4, §6).

### Edge revisions (not new edges)

- **R1. edge_678** (`eric_hobsbawm → truthdebate`, connection/contribution): broaden it rather than add a parallel triple.
  - Proposed relationship: "A defence of historical facts against 'postmodernist' fashions ('We cannot invent our facts', 1993), and an acknowledged reader of Telling the Truth about History (1994)".
  - map_label: "We cannot invent our facts, 1993".
  - target_strand: `truthdebate/evidence_representation`. Alternative: `disciplinary_scrutiny`.
  - Add source `w2_hob_new_threat_1993` and keep `appleby_hunt_jacob`.
  - Evidence-note text: the 1993 passage is brief ("I need say little about the first of these responsibilities"); the lecture's main subject is nationalist abuse of history. The 1994 acknowledgment still "records assistance, not agreement".
  - A separate `eric_hobsbawm → truthdebate` **critique** edge would not repeat a triple. It is rejected because existing contributions to `truthdebate` (Cronon edge_903, Hunt edge_1055) are modelled as connection/contribution, and a critique arrow would wrongly read as Hobsbawm criticising the historians who defended the facts.
- **R2. edge_644** (`gramsci → eric_hobsbawm`): optional source append, `w2_hob_eagleton_2011`. Eagleton reports Hobsbawm's later judgment that "Gramsci is the most original thinker produced by the West since 1917" (*How to Change the World*, 2011, mediated). Black p. 215 reports a photograph of him "addressing a Gramsci conference in 1958" (mediated through the memoir). Evidence-note addendum: "reception continues into How to Change the World (2011), as Eagleton reports".
- **R3. edge_322** (`eric_hobsbawm → marx`): no new edge for *How to Change the World*, since it would repeat the triple. Use a roster works_append (§5) and optionally add `w2_hob_eagleton_2011` to edge_322's sources. Recorded choice: works_append plus source append, no new edge.

**Net:**
- 4 new edges proposed (H1–H4); H5 held.
- 3 edge revisions (R1–R3).
- Totals for Hobsbawm: 17 incident edges now; 21 with H1–H4.
- New incoming critique: H3 (Judt 1995).

---

## 4. Proposed chronology events

Track and kind vocabulary follows the brief. "Dated through" names the reader; books not read are flagged. Existing ids are kept.

| # | id | label | kind | track | date | sources | support (reading label) |
|---|---|---|---|---|---|---|---|
| 1 | `hob_primitive_rebels_1959` | Primitive Rebels | publication | contributions | 1959 (year) | `pe132_hobsbawm_primitive_rebels`, `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012` | Metadata (Open Library; 1959–60 journal reviews in Crossref) and two readers: Judt (it "introduced young urban students to a world of rural protest") and the Guardian ("his first major work"). Book unread. |
| 2 | `hob_age_of_revolution_1962` | The Age of Revolution, 1789–1848 | publication | contributions | 1962 | `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012`, `w2_hob_black_historein` | Dated by Judt, the Guardian and Black (p. 215). Unread. |
| 3 | `event_33f70ef447fd` (existing) | Labouring Men | publication | contributions | 1964 | `hobsbawm_labouring` | Existing (metadata). |
| 4 | `hob_industry_empire_1968` (optional) | Industry and Empire | publication | contributions | 1968 | `w2_hob_guardian_obit_2012`, `w2_hob_judt_1995` | Guardian date; Judt characterisation. Unread. Include only if H4 is accepted. |
| 5 | `event_ad7acfd6df28` (existing) | Bandits | publication | contributions | 1969 | `hobsbawm_bandits_revised` | Existing. |
| 6 | `hob_age_of_capital_1975` | The Age of Capital, 1848–1875 | publication | contributions | 1975 | `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012` | Judt: "in my view, Hobsbawm’s single greatest work". Unread. |
| 7 | `event_49c108985ab5` (existing) | The Invention of Tradition, coedited with Ranger | publication | contributions | 1983 | `hobsbawm_ranger` | Existing. |
| 8 | `hob_age_of_empire_1987` | The Age of Empire, 1875–1914 | publication | contributions | 1987 | `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012` | Judt: "an unmistakable elegiac air". Unread. |
| 9 | `hob_nations_nationalism_1990` | Nations and Nationalism since 1780 | publication | contributions | 1990 (2nd ed. 1992) | `hobsbawm_nations_primary` | Existing reading of the publisher preview (copyright page, preface, intro pp. 1–13). |
| 10 | `hob_new_threat_lecture_1993` | "The New Threat to History", opening lecture of the academic year, Central European University, Budapest; published NYRB 16 Dec. 1993 | lecture_delivery (or publication) | contributions | 1993 (year; delivered at the start of the 1993–94 academic year, exact day not given; published 1993-12-16) | `w2_hob_new_threat_1993` | Primary, read in full; delivered (the text says "It is an honor to be asked to open this academic year"). |
| 11 | `hob_age_of_extremes_1994` | The Age of Extremes: The Short Twentieth Century, 1914–1991 | publication | contributions | 1994 | `w2_hob_judt_1995`, `w2_hob_guardian_obit_2012`, `w2_hob_black_historein` | Three readers. Black p. 215: "published in 37 languages". US title "A History of the World, 1914–1991" (Pantheon). Unread. |
| 12 | `hob_judt_downhill_1995` | Tony Judt, "Downhill All the Way" (NYRB) | reception_publication | reception | 1995-05-25 (day) | `w2_hob_judt_1995` | Read in full. |
| 13 | `hob_on_history_1997` | On History | publication | contributions | 1997 | `w2_hob_guardian_obit_2012`, `w2_hob_pw_on_history_1997` | Dated by the Guardian and Publishers Weekly (Sept. 1997, New Press). Mediated; book unread. |
| 14 | `hob_companion_honour_1998` (optional) | Companion of Honour | office (honour) | context | 1998 | `w2_hob_guardian_obit_2012`, `w2_hob_black_historein` | Guardian; Black p. 216. Mediated. |
| 15 | `hob_interesting_times_2002` | Interesting Times: A Twentieth-Century Life | publication | contributions | 2002-09 (month) | `w2_hob_anderson_2002`, `w2_hob_black_historein` | LRB header gives "September 2002", Allen Lane. Memoir unread. |
| 16 | `hob_anderson_age_of_ejh_2002` | Perry Anderson, "The Age of EJH" (LRB) | reception_publication | reception | 2002-10-03 (day) | `w2_hob_anderson_2002` | Read in full. |
| 17 | `hob_globalisation_terrorism_2007` | Globalisation, Democracy and Terrorism | publication | contributions | 2007 | `w2_hob_guardian_obit_2012`, `w2_hob_gdt_publisher` | Guardian date; publisher blurb (Abacus pb 2008). Mediated. |
| 18 | `hob_how_to_change_world_2011` | How to Change the World: Marx and Marxism 1840–2011 | publication | contributions | 2011-01 (month) | `w2_hob_eagleton_2011`, `w2_hob_guardian_obit_2012` | The LRB header gives "January 2011", Little, Brown. Eagleton's review (3 Mar. 2011) was read in full and may be added as a reception point. Book unread. |
| 19 | `hob_death_2012` | Death of Eric Hobsbawm (b. 1917) | context (death) | context | 2012-10-01 (day) | `w2_hob_guardian_obit_2012` | Read in full. Use only if the schema shows life events (check Davis 1.143 practice; otherwise put it in date_label or the description). |
| 20 | `hob_fractured_times_2013` | Fractured Times: Culture and Society in the Twentieth Century | posthumous_publication | contributions | 2013-03-25 (day) | `w2_hob_the_fractured_2013` | THE review page: "Published 25 March 2013"; review read in full. Book unread. |
| 21 | `hob_history_after_hobsbawm_2014` | "History after Hobsbawm" conference, Senate House, London (Birkbeck and Past & Present), with Mazower's first Hobsbawm Memorial Lecture | symposium | reception | 2014-04-29 to 2014-05-01 (day; delivered) | `w2_hob_the_conference_2014`, `w1_hall_gendering_property_2014` | THE report read in full (3 May 2014; mediated speakers). Hall's essay began as a lecture there. |
| 22 | `hob_evans_biography_2019` | Richard J. Evans, Eric Hobsbawm: A Life in History | retrospective_publication | reception | 2019 (year) | `w2_hob_mayer_irsh_2020` | Mayer's review read in full: OUP New York 2019, xiii + 785 pp.; estate papers and declassified intelligence reports. Biography unread. |

**Counts:**
- 3 existing events plus 17–19 new ones, depending on the optional items. Recommended core set is about 18 events in total: drop #4 and #14 if H4 is rejected, and drop #19 if life events are not used.
- **After 2000:** #15, #16, #17, #18, #20, #21 and #22, plus #19 if used, so **7–8 events, at least a third of the total**.
- Chronology label: "Selected contributions and reception · 1959–2019".

---

## 5. Proposed roster rows

- **`global` (new row):** `eric_hobsbawm`, role historian.
  - context: "The Age of… volumes (1962–1994), read by reviewers as a synthesis of the capitalist world from 1789 to 1991; praised for range and analytical economic grasp, and judged 'unashamedly Eurocentric' by Judt, who nonetheless defends their focus."
  - works: "The Age of Revolution (1962); The Age of Capital (1975); The Age of Empire (1987); The Age of Extremes (1994)".
  - sources: H2's sources. edge_id → H2. Add `eric_hobsbawm` to `global/world` person_ids.
- **`nationaltradition` (new row):** `eric_hobsbawm`, role critic.
  - context: "Treats national and ethnic pasts as raw material for ideology and asks historians to resist myths, anachronism and invented continuities as they form."
  - works: "The Invention of Tradition (1983, ed. with Ranger); 'The New Threat to History' (1993)".
  - sources: `w2_hob_new_threat_1993`, `hobsbawm_ranger`. edge_id → H1. Optionally add him to `narration_authority` person_ids.
- **`political` (new row + new people record):** `tony_judt`, role critic.
  - context: "Reviewing The Age of Extremes (1995), he finds the political history of Communism, fascism and Eastern Europe framed by the categories of the 1930s, and nationalism and religion neglected, while praising the economic analysis."
  - works: "'Downhill All the Way', New York Review of Books, 25 May 1995".
  - sources: `w2_hob_judt_1995`. edge_id → H3.
  - **People record:** `{id: tony_judt, label: "Tony Judt", identity_note: "British-American historian (1948–2010), NYU Remarque Institute; reviewer of Hobsbawm's Age of Extremes (NYRB, 1995). Wikidata Q312279 checked (search_items, get_statements) on 2026-10-18: born London 2 Jan. 1948, died New York 6 Aug. 2010, historian, NYU; to be recorded in data/people-wikidata.json in the usual way."}`
- **`economic` (new row):** `eric_hobsbawm`, role historian.
  - context: "The British standard-of-living debate of the 1950s and Industry and Empire (1968), which readers credit with recasting the economic history of industrial Britain; no economic text read here."
  - works: "'The British Standard of Living 1790–1850' (1957); Industry and Empire (1968)".
  - edge_id → H4. Add him to the `british` strand only if H4 is accepted.
- **`marx` (works_append to the existing row, edge_322):**
  - works append: "; Interesting Times (2002); How to Change the World: Marx and Marxism 1840–2011 (2011)".
  - context append: "His last collections defend Marx's continuing relevance and trace Marxism's fortunes from 1840 to 2011 (as Eagleton and the Guardian obituary describe them)."
  - sources append: `w2_hob_eagleton_2011`.
- **`truthdebate` (existing row; update):**
  - context: "Defends the distinction between fact and fiction against 'postmodernist' fashions in a 1993 lecture, and acknowledged reader of the 1994 manuscript; its conclusions are not assigned to him."
  - works append: "'The New Threat to History' (1993)".
  - sources append: `w2_hob_new_threat_1993`.
- **`biography` (optional new row):** `richard_j_evans` (existing people record), role historian.
  - context: "A full life of Hobsbawm drawn from the estate papers and declassified intelligence reports; Mayer finds his ideas given 'surprisingly little coverage'."
  - works: "Eric Hobsbawm: A Life in History (2019)".
  - sources: `w2_hob_mayer_irsh_2020`. Strand: none, or `collective_labour_lives`, which concerns Torr, Hill and Morton. Mediated only.

---

## 6. Proposed text revisions

**date_label:** "Primitive Rebels 1959 · The Age of… 1962–1994 · Interesting Times 2002 · How to Change the World 2011"

**description (draft):**
> "A historian of labour, popular protest, capitalist transformation and nations. After *Primitive Rebels* (1959) and *Labouring Men* (1964), his four Age of… volumes (1962–1994) became, for reviewers, a synthesis of the capitalist world from 1789 to 1991; Tony Judt praised *The Age of Capital* and criticised *The Age of Extremes* for viewing Communism and Eastern Europe through the categories of the 1930s (1995). With Terence Ranger he edited *The Invention of Tradition* (1983); in a 1993 lecture he told historians to resist national myths as they formed and to hold to the difference between fact and fiction. Later works include *On History* (1997), the memoir *Interesting Times* (2002), which Perry Anderson read as a fifth volume of the same project, and *How to Change the World* (2011), a history of Marxism. His responses to criticism revise some claims while retaining others."

**representative_figures_and_works (draft):** "Primitive Rebels (1959); Labouring Men (1964); The Age of Revolution (1962), The Age of Capital (1975), The Age of Empire (1987), The Age of Extremes (1994); Industry and Empire (1968); Bandits (1969; revised 2000); with Terence Ranger, The Invention of Tradition (1983); Nations and Nationalism since 1780 (1990); response to Stone on narrative (1980); 'The New Threat to History' (1993); On History (1997); Interesting Times (2002); Globalisation, Democracy and Terrorism (2007); How to Change the World (2011); Fractured Times (2013). Readings: Judt (1995); Anderson (2002); Black (2003–4); Eagleton (2011); Mayer on Evans (2020)."

**scope_note (draft; replace):** "The 1980 narrative reply, the 1993 Budapest lecture, Bandits in its revised 2000 form, and Nations and Nationalism (1990/1992) are read in his own words. They distinguish debate, self-revision and historical synthesis. The Age of… volumes, Primitive Rebels, Industry and Empire, On History, Interesting Times, How to Change the World and Fractured Times remain unread here. They are dated and characterised through named readers (Judt, Anderson, Black, Eagleton, Morgan, the Guardian obituarists; Mayer on Evans's 2019 biography). Later concessions about myth and political power are not projected into 1969. Selected primary support does not audit his entire career or generalizations."

---

## 7. New source records

| id | citation | url | status | verification note |
|---|---|---|---|---|
| `w2_hob_new_threat_1993` | Eric Hobsbawm, "The New Threat to History," *New York Review of Books*, 16 Dec. 1993 (lecture opening the academic year, Central European University, Budapest). | https://www.nybooks.com/articles/1993/12/16/the-new-threat-to-history/ | supporting_page_checked | Complete text read (NYRB page via curl; no pagination). Headnote identifies the CEU lecture. Quoted passages: history as "raw material" for nationalist ideologies; "Now I know it can"; "postmodernist" fashions and "We cannot invent our facts"; anachronism; "History is not ancestral memory or collective tradition"; resist myths "as they are being formed". Identity with the *On History* chapter "Outside and Inside History" not verified. |
| `w2_hob_judt_1995` | Tony Judt, "Downhill All the Way," *New York Review of Books*, 25 May 1995 (review of *The Age of Extremes: A History of the World, 1914–1991*, Pantheon). | https://www.nybooks.com/articles/1995/05/25/downhill-all-the-way/ | supporting_page_checked | Complete text and endnotes read (curl; no pagination). "Hobsbawm generation"; dates and judgments of *Primitive Rebels*, the trilogy and *Age of Capital*; the critique of Communism's categories, Eastern Europe ("just six pages") and nationalism; "unashamedly Eurocentric … unique range". *Age of Extremes* itself unread. |
| `w2_hob_anderson_2002` | Perry Anderson, "The Age of EJH," *London Review of Books* 24:19, 3 Oct. 2002 (review of *Interesting Times*, Allen Lane, Sept. 2002). | https://www.lrb.co.uk/the-paper/v24/n19/perry-anderson/the-age-of-ejh | supporting_page_checked | Complete text read (curl; 6,494 words; no pagination). Memoir as a "fifth volume" of a continuous project. Critique: lack of generosity to Samuel, Thompson and the New Left; the *Marxism Today*/Labour campaign; the missing intellectual engagement. Praise for *On History*'s originality. Memoir unread. |
| `w2_hob_black_historein` | Lawrence Black, review of Eric Hobsbawm, *Interesting Times* (2002), *Historein* 4 (2003–4): 215–[c. 218]. | https://doi.org/10.12681/historein.91 | supporting_page_checked | Open access (CC BY-NC-SA 4.0); pp. 215–217 read. Quartet "1962-94"; P&P 1952 and "The Machine Breakers"; standard-of-living debate; 1978 lecture; *Age of Extremes* in 37 languages; CH 1998; critics' charge of reticence on Soviet communism (p. 216). The DOI covers the whole book-review section; check the end page before citing. |
| `w2_hob_guardian_obit_2012` | Martin Kettle and Dorothy Wedderburn, "Eric Hobsbawm obituary," *The Guardian*, 1 Oct. 2012. | https://www.theguardian.com/books/2012/oct/01/eric-hobsbawm | supporting_page_checked | Complete text read (curl). Dates for the books 1959–2011, CH 1998, Hay presidency, death 1 Oct. 2012. Quotes Ascherson and the 1993 Creighton lecture. Obituarists' judgments attributed. |
| `w2_hob_eagleton_2011` | Terry Eagleton, "Indomitable," *London Review of Books* 33:5, 3 Mar. 2011 (review of *How to Change the World: Marx and Marxism 1840–2011*, Little, Brown, Jan. 2011). | https://www.lrb.co.uk/the-paper/v33/n05/terry-eagleton/indomitable | supporting_page_checked | Complete text read (curl; 2,814 words). Contents (two-thirds not previously in English; three surveys of Marxism 1880–1983); Hobsbawm's positions as Eagleton reports them; criticism (ideas, Althusser, feminism, Trotskyism; Gramsci judgment). Book unread. |
| `w2_hob_the_fractured_2013` | Roger Morgan, review of *Fractured Times: Culture and Society in the 20th Century* (Little, Brown, 2013), *Times Higher Education*, 11 Apr. 2013. | https://www.timeshighereducation.com/node/112584 | supporting_page_checked | Complete review read (curl). Book published 25 March 2013; posthumous collection of about two dozen texts; preface quotations; Morgan's criticisms. The sidebar error dating HTCW to 2012 is ignored. |
| `w2_hob_the_conference_2014` | "Hobsbawm’s contribution to academia celebrated," *Times Higher Education*, 3 May 2014. | https://timeshighereducation.com/cn/node/121433 | supporting_page_checked | Complete report read. History After Hobsbawm, Senate House, 29 Apr.–1 May 2014; Mazower's first Hobsbawm Memorial Lecture; Rüger; Stedman Jones (speakers' words mediated by the reporter). |
| `w2_hob_mayer_irsh_2020` | David Mayer, review of Richard J. Evans, *Eric Hobsbawm: A Life in History* (2019), *International Review of Social History* 65:3 (2020). | https://doi.org/10.1017/S0020859020000619 | supporting_page_checked | Complete review read (Cambridge Core open reader). Evans's sources (estate papers, declassified intelligence reports); critique ("ideas get surprisingly little coverage"); Palmer's 2020 objection about Evans p. 351; the global Hobsbawm. Evans unread. |
| `w2_hob_pw_on_history_1997` | Publishers Weekly, review of Eric J. Hobsbawm, *On History* (New Press, 1997). | https://www.publishersweekly.com/9781565843936 | bibliographic_metadata_checked | WebFetch summary only (the tool declined verbatim reproduction): New Press, Sept. 1997; 21 reprinted essays and lectures; theme of ideological abuse of history and blurring of fact and fiction. Used for dating only. |
| `w2_hob_gdt_publisher` | Eric Hobsbawm, *Globalisation, Democracy and Terrorism* (Little, Brown, 2007; Abacus pb 2008). | https://www.hachetteindia.com/Home/bookdetails/Info/9780349120669/globalisation_-democracy-and-terrorism | bibliographic_metadata_checked | Publisher page (Abacus paperback, 3 Apr. 2008, 192 pp.); blurb summarised by WebFetch. 2007 first publication per the Guardian obituary. |
| `w2_hob_standard_living_1957` (only if H4) | E. J. Hobsbawm, "The British Standard of Living 1790–1850," *Economic History Review* 10 (1957), from p. 46. | https://doi.org/10.2307/2600061 | bibliographic_metadata_checked | Crossref metadata only; not read. |
| `w2_hob_palmer_2020` (optional; not needed for any edge) | Bryan D. Palmer, "Eric Hobsbawm's Century," *Jacobin*, 8 July 2020 (also *Catalyst* 4:1, 2020, 60–100). | https://jacobin.com/2020/07/eric-hobsbawn-life-history-richard-evans | supporting_page_checked (excerpt) | Opening paragraphs read before the paywall: differentiation among British Marxist historians; Hobsbawm "First among equals". |

---

## 8. Considered, not proposed

- **`eric_hobsbawm → truthdebate` critique** (new triple). Rejected: it would misread as a critique of the defenders of facts. Handled by revising edge_678 (R1).
- **`eric_hobsbawm → memory` critique** ("History is not ancestral memory or collective tradition", 1993). Rejected: it would reuse the H1 quotation for a second edge, and the lecture is about nationalist myth, not memory studies.
- **`eric_hobsbawm → intellectualhistory`** (*How to Change the World* as a history of Marxist ideas and their reception). Rejected:
  - the book is unread;
  - Eagleton, the only reader, says he "is not at his sharpest in the realm of ideas";
  - a works_append on `marx` is used instead.
- **`historicalsociology → eric_hobsbawm` critique** (Anderson as proxy). Rejected: Anderson's critique concerns the memoir's politics, not historical sociology. See H5 (held) for the `marx` variant.
- **`historyworkshop → eric_hobsbawm` critique** (Stedman Jones 2014: Marxism "mixes badly with the writing of good history"). Rejected:
  - the words come through a THE reporter;
  - it was a conference talk, and Stedman Jones speaks as historian of ideas, not for the Workshop;
  - he also praises Hobsbawm's "unending curiosity".
  It could become a roster note on `marx` for `gareth_stedman_jones` if wanted.
- **`bryan_d_palmer → eric_hobsbawm`** (2020 review essay). Rejected: only the paywalled opening was read; Mayer reports one point about Evans, not Hobsbawm.
- **`eric_hobsbawm → historicalsociology`, `→ political`** (contribution). Rejected: no reader read here places his work in those fields. The *Forward March of Labour Halted* (1978) and *Marxism Today* essays are political interventions, recorded in the description only if wanted.
- **2004 "Manifesto for the renewal of history"** (British Academy closing address, 13 Nov. 2004, per catalogue snippets). Not proposed: no authorised full text was located. The British Academy chapter "Marxist Historiography Today" (2007) is abstract only, and its identity with the 2004 address is unverified.
- **Fukuyama, *Foreign Affairs* 1995 capsule review**: not extractable. **Neal Ascherson on Evans (*Observer*, 2019)**: URL not found. **History Today on Evans**: 403. None used.
- ***Fractured Times* as a `culture` edge**: rejected; collection unread, and one reviewer only.

## 9. Flags for the parent / cross-model reviewer

1. **Existing source links** are handled by a separate cleanup.
2. **Transition debate / capitalismdebates (coordination).** Hobsbawm, "The General Crisis of the European Economy in the 17th Century," *Past and Present* 5 (1954): 33–53, DOI 10.1093/past/5.1.33 (metadata only); its second instalment, "The Crisis of the Seventeenth Century—II," *Past and Present* 6 (1954): 44–65, DOI 10.1093/past/6.1.44 (Crossref metadata checked 2026-10-19: Hobsbawm, Past and Present 6, 1954, 44–65; added after the cross-model review, which cites the Edinburgh Hobsbawm bibliography for its identification as part two, a page not reachable here); plus his 1960 contribution to the Trevor-Roper discussion (P&P 18: 12–14, DOI 10.1093/past/18.1.12). Stedman Jones (THE 2014, mediated) names "the General Crisis of the Seventeenth Century" among his subjects. **No edge proposed to `capitalismdebates` or any coordinated person.** The capitalism-debate owner may consider a `capitalismdebates` roster row or a `general_crisis` mention. All three items are unread and stay metadata-only; a future placement must explain the general-crisis debate's relation to the transition debate rather than equate the two.
3. **On History contents.** Not verified that the 1993 NYRB lecture is the *On History* chapter "Outside and Inside History". Only catalogue and bookseller listings suggest it. Cite the NYRB text by itself.
4. ***History after Hobsbawm* volume date** varies between reviewers' metadata (2017 vs 2018). If the volume is cited, check the OUP imprint.
5. **Life-event modelling.** Whether to include a death event (#19) depends on atlas practice. The Davis 1.143 entry should be checked for precedent.
6. **Judt proxy.** H3 uses `political` as the proxy for one named reviewer. Sol may prefer a roster-only treatment. Judt's review is read in full, and its political-history focus is explicit ("distinctly superior to his political surveys"), so the proxy has a stated basis.
7. **Edge count.** Four new edges, with H5 held, sits at the low end of the 4–8 target. The edge count was already high (17). The main gap was the chronology, now 18–22 points with 7–8 after 2000.
