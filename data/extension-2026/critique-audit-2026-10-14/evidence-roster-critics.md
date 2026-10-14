# Roster critics without critique edges: evidence audit (2026-10-14)

Status: COMPLETE (2026-10-14). Research only; no graph edits. Graph read at revision 1.132 (Chakrabarty person entry landed during this audit).

Scope: the 13 entries (science excluded) in
`data/extension-2026/science-studies-critique-2026-10-14/no-critique-audit.csv` that have roster
rows with role `critic` but no critique edge in or out. For each roster critic: context, works and
source ids (from `historiography-1920-2000.json`); the critic's other entry memberships; the
objection in the critic's own words, read where possible; a judgement on whether an edge
(critic's entry → this entry, `relationship_kind: critique`) is warranted.

Conventions:
- "read" = text read in this session (location given). "abstract" = publisher/OpenAlex abstract
  only. "metadata" = bibliographic only. "unread" = not obtained.
- Web texts without pagination are cited by section or paragraph; no page numbers invented.
- Years: the atlas is ending its 2000 cutoff, so post-2000 critiques are admissible; every
  critique is dated.
- Download area (untrusted): scratchpad `dl-roster-critics/`. Érudit (Anubis bot wall) and
  T&F / Wiley / SAGE / JSTOR full texts were not available; not circumvented.

---

## 1. liberal_order_framework (5 roster critics; priority)

Existing edges into the entry: gramsci → (influence, 844); karl → (comparison, 845, cites
Fecteau); economic → (comparison, 846); quebec_historiography → (contribution, 851, cites
Fecteau as "Fecteau's critique"); historicalsociology → (comparison, 852);
cdn_intellectual_cultural → (comparison, 826, McNairn's chapter, title level). No critique edge.

The 2009 debate has two venues: the volume *Liberalism and Hegemony: Debating the Canadian
Liberal Revolution*, ed. Jean-François Constant and Michel Ducharme (Toronto: UTP, 2009), and the
CHA round table on that volume (Carleton, 25 May 2009), published in revised form in *The
Underhill Review* (Fall 2009). The Underhill pages are unpaginated HTML; quotations below are
cited by section. All four Underhill texts were re-read in full this session (Carleton pages
fetched 2026-10-14).

### 1a. Bryan D. Palmer (2009) — critic's entries: cdn_working_class (historian), who_killed_debate (critic), cdn_sixties (historian)

Source: `lof_palmer_2009`, "Radical Reasoning," review essay on McKay, *Reasoning Otherwise*
(2008), *Underhill Review*, Fall 2009. **Read** (full text). The review is of McKay's left
history, but several paragraphs are directed at the framework itself.

- "As an elastic category, liberal order can contain almost anything associated with what has
  traditionally been understood about modern developing societies, premised as they are on
  property relations of inequality and bourgeois individualism."
- "The danger in deploying liberal order in this way, as a seemingly trans-historical analytic
  framework, is that it actually sidesteps the need to confront and elucidate capitalism's
  changing historical structures … Contrary to McKay's assertions, moreover, it may well be
  impossible to discern anything distinctly Canadian about the notion of liberal order."
- "The most serious problem with the liberal order perspective, then, is that it allows
  mainstream historians to avoid confronting just how critically important it is to name the
  frontline enemy: capitalism as systematic exploitation and endlessly proliferating
  oppression."
- On Gramsci: "McKay's elastic understanding of Gramsci's hegemony conflates what Gramsci
  differentiated as a 'separation of powers' associated with organizing social hegemony within
  civil society and enforcing discipline through various vehicles of state domination".
- He also notes that past leftists "never spoke of an enemy that they named 'liberal order.'"

Objection: a Marxist/working-class-history objection — the category is elastic and
trans-historical, displaces capitalism, and reads hegemony too seamlessly. It is a real critique,
not an amendment (he still calls *Reasoning Otherwise* "an undeniable achievement").

Judgement: **edge warranted**: cdn_working_class → liberal_order_framework, critique. Palmer is
a core roster figure in cdn_working_class (founding-generation, *Descent into Discourse*), and
the objection is made from the class-and-capitalism standpoint that defines that entry, so the
group edge is not a misattribution. Suggested label: "Palmer: liberal order as an elastic
category that sidesteps capitalism (2009)". Target strand: liberal_order_framework/critiques (or
property_and_capitalism). Note for the evidence note: the essay reviews *Reasoning Otherwise*
(2008), not the 2000 prospectus, and McKay's own reply is not checked here.
Alternative considered: karl → liberal_order_framework (Palmer is not on the karl or marx roster,
and 845 already uses Fecteau for the capitalism comparison) — not preferred.

### 1b. Nancy Christie (2009) — critic's entry: cdn_religion_reform (historian)

Source: `lof_christie_2009`, "Revisiting Canada's Project of Liberal Rule," *Underhill Review*,
Fall 2009 (round-table paper). **Read** (full text).

- Opening: she wishes "to recommend ways in which the theoretical paradigm … can be both
  extended, especially in terms of periodization, and made more focused and specific"; the
  framework "provides coherence to a vast literature in cultural and social history".
- Periodization: "One of the weaknesses of his proposition about liberalism is that he does not
  discuss the interplay of republicanism, civic humanism, and Ancien Régime political
  sensibilities in place before the liberal order fundamentally altered these social and
  political relations."
- Hegemony: "The idea of one hegemonic (imposed and top down) liberalism does not reflect
  historical reality"; "liberalism was not simply imposed, a view that merely echoes older
  social control theories now severely challenged."
- State: "I am somewhat perplexed by the great emphasis McKay places on the state … what McKay
  is really describing is governmentality" (crediting Bruce Curtis).
- Religion: "In McKay's formulation the church is defined as a conservative institution, but no
  one who is acquainted with the work of Jean-Marie Fecteau, Ollivier Hubert, Michael Gauvreau,
  and indeed myself on the connections between the Protestant churches and New Liberalism, can
  ignore religion as a powerful vehicle in the creation of the liberal order."
- Gender: "McKay's definition of individualism based on property ownership is a tautology which
  automatically excludes women."

Objection: framed as extension, but substantive: wrong periodization, top-down hegemony, statism,
church misclassified as conservative, women excluded by a property-based individual. Note the
character: it criticises the framework's account of religion while accepting that a liberal
order was built (religion was "a powerful vehicle in the creation of the liberal order"). A
critique-with-amendment, comparable to existing critique edges that "question" rather than
reject.

Judgement: **edge warranted (moderate)**: cdn_religion_reform → liberal_order_framework,
critique. The religious-history objection is exactly what the cdn_religion_reform entry
carries (its description already says religion was "a vehicle of the liberal order
(Christie)"). Suggested label: "Christie: the church as a builder, not an opponent, of liberal
order (2009)". If the editor prefers to keep amendments out of the critique class, the
fallback is a contribution edge with the same evidence; the roster row alone under-represents a
cross-field disagreement that the atlas otherwise lacks.

### 1c. Jean-Marie Fecteau (2009) — critic's entries: quebec_historiography (critic, normal-society debate)

Source: `lof_fecteau_2009`, "Towards a Theory of Possible History? Ian McKay's Idea of a 'Liberal
Order'," *Underhill Review*, Fall 2009 (trans. Steven Watt). **Read** (full text; sections I–III).

- Praise first: McKay's 2000 article "is an open call to debate the general interpretations
  which underlie Canadian history"; "an attempt, a major one in my opinion, at reinterpreting the
  meaning of our history".
- Section I: "the concept of a 'liberal order' is not without a certain vagueness … the
  different terms used to describe liberalism or the liberal order refer to different levels of
  reality, which end up largely being conflated."
- "This is exactly why it is difficult (and probably vain) to conceive of the liberal order as a
  unitary enterprise, founded on stable principles. That is to say: liberty, equality and
  property are not the constitutive and cumulative 'elements' of a static conceptual universe."
- Section II: McKay's "bridging" concepts and "reconnaissance" are "a major step backward in the
  search for meaning"; "a singular abdication and a depressingly defensive withdrawal in the
  face of a search for deeper meaning". Fecteau proposes instead liberalism as a "social logic"
  he calls "social regulation".

Objection: conceptual and epistemological. Liberal order conflates ideology, order and project;
its triad is unstable; reconnaissance retreats from explanatory theory. Fecteau's alternative is
the régulation sociale programme of Quebec social history.

Judgement: **edge warranted**: quebec_historiography → liberal_order_framework, critique,
alongside the existing contribution edge 851 (the graph already allows two kinds on one pair,
e.g. micro → social 108/370). Suggested label: "Fecteau: liberal order is not a unitary project;
liberalism as a social logic (2009)". Then trim 851's evidence note so that Fecteau is not
counted twice ("Fecteau's critique carry the debate" → move Fecteau to the new edge).
Alternative: fold Fecteau and Christie into one karl/marx-style "Quebec and religious
historians" edge — not recommended; they argue from different positions.

### 1d. R. W. Sandwell (2003, 2009) — critic's entry: cdn_regional (historian, British Columbia)

Sources: `lof_sandwell_2003`, "The Limits of Liberalism," *CHR* 84:3 (2003): 423–450 —
**abstract** (OpenAlex) re-read; `lof_sandwell_2009`, "Missing Canadians: Reclaiming the A-Liberal
Past," in Constant and Ducharme (2009), 246–273 — **metadata only**.

- Abstract (2003): the article "responds to Ian McKay's invitation"; it "argues that the
  reconnaissance … has already informed the work of historians of the family in Canada";
  "A-liberal values and behaviours, though often marginalized within more traditional liberal
  narratives of Canadian history, are clearly visible in the family well into the twentieth
  century", making families "'hot zones' where the new liberal order … was imposed, embraced,
  contested, rejected, or absorbed".
- Fecteau (2009, section I, read) groups Sandwell 2009 with Perry 2009 among authors "sounding
  and exploring the contours of this 'exterior' of liberalism as presented by McKay".

Objection: the 2003 abstract reads as a sympathetic extension (family history already does the
reconnaissance) with a limits claim (a-liberal values persisted). The 2009 chapter title is
sharper ("Missing Canadians") but unread.

Judgement: **roster row suffices**. Her only other entry is cdn_regional, and the objection is
from family and rural history, not regional history; cdn_regional → liberal_order_framework would
misattribute it. (cdn_childhood_youth or cdn_women_gender would fit the family argument better,
but she is on neither roster.) Revisit if the 2009 chapter is read.

### 1e. Janet Ajzenstat (2009) — no atlas entry (political scientist)

Source: `lof_ajzenstat_2009`, "Historians in Search of a Framework," *Underhill Review*, Fall
2009. **Read** (full text).

- "It is not his dependence on Gramsci that impairs McKay's account of Canadian history but his
  ignorance of facts on the ground. His prodigious output consists primarily of summaries of the
  work of others. He shuns the primary sources."
- On McKay's note (2000, n. to p. 633) that the Fathers of Confederation did not seek popular
  approval: "The assertion does not stand up to examination of the texts."
- Close (section III): "McKay, relying on Gramsci without consultation of primary texts, gives us
  a national history characterized by struggles for domination. What the texts reveal is the
  long and sure development of institutions promoting liberty and equality."

Objection: a constitutional-history, Whig-liberal objection to a Gramscian national history.

Judgement: **roster row suffices**. Ajzenstat has no entry; cdn_political_national is the nearest
group, but she is not on its roster and is a political theorist of the founding texts. A
possible later step: add her to cdn_political_national (or intellectual-cultural) and then
draw the edge; not proposed now.

### 1f. Not a roster critic, but noted

Allan Greer is a liberal_order_framework *historian* who is a settler_colonialism *critic*
(section 2). Bruce Curtis's line that the liberal order "is rather dubious, given the
multiplicities of liberalisms" is quoted by Fecteau (citing Curtis 2009, 184) — Curtis is a
liberal_order_framework roster historian, so it remains internal to the entry.

---

## 2. settler_colonialism (10 roster critics; priority)

Existing edges: liberal_order_framework → (comparison, 850); native_newcomer → (comparison, 869,
cites Greer 2019, Konishi); indigenous → (comparison, 881, cites Konishi, Kauanui, "Comparison
only"); post → (882); anticolonial → (883); africanhist → (884); → racial_formation (885);
patrick_wolfe → (contribution, 892). No critique edge. The entry's description already names the
three critical directions (Indigenous scholars; structure/region/period; Black studies), and
three strands hold them (critiques_and_limits, indigenous_scholars_critique,
slavery_black_studies). All ten critiques are post-2000 (2013–2020).

Membership problem: of the ten, only Allan Greer belongs to another entry (liberal_order_framework,
as a historian of state formation, property and the transition to capitalism). The other nine
belong to settler_colonialism alone. So, under the rule that an edge must run from the critic's
own entry, **no critique edge can be drawn today without first extending a roster**.

### 2a. Indigenous-studies critics: J. Kēhaulani Kauanui (2016), Shino Konishi (2019)

- Kauanui, "'A Structure, Not an Event': Settler Colonialism and Enduring Indigeneity," *Lateral*
  5.1 (2016) (`screq_kauanui_2016`). **Read** (full web text, csalateral.org; unpaginated, cited
  by paragraph).
  - Para. 3: "to exclusively focus on the settler colonial without any meaningful engagement with
    the indigenous—as has been the case in how Wolfe's work has been cited—can (re)produce
    another form of 'elimination of the native.'"
  - Para. 4: "Settler Colonial Studies does not, should not, and cannot replace Indigenous
    Studies."
  - Para. 6 quotes Robert Warrior (ASA 2015) on "a growing anxiety … that the rise of Settler
    Colonial Studies has become … an answer to the chronic need for more attention to and
    awareness of Native and Indigenous studies."
  - Character: Kauanui calls Wolfe's theorising brilliant ("as the late English scholar Patrick
    Wolfe brilliantly theorized") and closes that NAIS "must be engaged in relation to Settler
    Colonial Studies". The critique targets the field's uptake and its displacement of
    Indigenous studies, not the structure thesis.
- Konishi, "First Nations Scholars, Settler Colonial Studies, and Indigenous History," *AHS* 50:3
  (2019): 285–304 (`screq_konishi_2019`). **Abstract only** (OpenAlex; the UWA accepted
  manuscript returned 403). Abstract: the approach "has been subject to more critical
  evaluations, key amongst them, by some First Nations scholars"; she explores how they
  "advocate, interrogate, critique or challenge settler colonial studies" and ends with
  "Indigenous-authored extra-colonial histories, which bypass colonial expropriation and
  exploitation to focus on Indigenous worlds."

Judgement: the natural edge is **indigenous → settler_colonialism, critique** (label suggestion:
"Indigenous scholars: settler colonial studies cannot replace Indigenous studies (2016–19)").
But neither Kauanui nor Konishi is on the indigenous roster, and edge 881 was deliberately kept a
comparison. **Conditional**: draw the critique edge only if Kauanui (Kanaka Maoli scholar,
NAISA co-founder per her Lateral bio) is added to the indigenous roster as critic or
contributor; keep 881 as the comparison. Otherwise the roster rows suffice.

### 2b. Structure, region and period: Macoun & Strakosch (2013), Rowse (2014), Shoemaker (2019), Greer (2019)

- Macoun and Strakosch, "The Ethical Demands of Settler Colonial Theory," *Settler Colonial
  Studies* 3:3–4 (2013): 426–443 (`screq_macoun_strakosch_2013`). **Read** (QUT eprint, author's
  manuscript; journal pagination not available, so no page numbers given).
  - Abstract: SCT "seems unable to transcend itself, in the sense that it posits a structural
    inevitability to the settler colonial relationship. We suggest that this structuralism can be
    mobilized by settler scholars in ways that delegitimize Indigenous resistance".
  - Body: "By emphasizing continuities in colonial relationships between the past and the
    present, SCT can depict colonization as structurally inevitable, and can be deployed in ways
    that re‐inscribe settler colonialism."; "This can lead to a theoretical and political impasse
    and result in a kind of colonial fatalism."; "Foundational scholar Patrick Wolfe has been
    labelled 'very much a structuralist stuck in a poststructuralist world'." (a quotation of
    another author, not their own phrase).
  - Character: critique from within ("It is precisely by using the strengths of SCT that we can
    challenge its limitations", abstract).
- Rowse, "Indigenous Heterogeneity," *AHS* 45:3 (2014): 297–310 (`screq_rowse_2014`).
  **Abstract only.** "I begin this paper by criticising an approach to Australian history that
  emplots the colonial story as a teleology of 'elimination' and inhibits historical
  characterisation of the many forms of Australian indigeneity to which colonial history has
  given rise." (Macoun and Strakosch, read, also quote Rowse that critical settler perspectives
  can "reproduce that sorrowing form of attention in which defeat and marginality are
  highlighted at the expense of understanding the nature and limits of the Indigenous agency
  that circumstances afforded" — from an earlier Rowse text, not the 2014 article.)
- Shoemaker, "Settler Colonialism: Universal Theory or English Heritage?" *WMQ* 76:3 (2019)
  (`screq_shoemaker_2019`). **Read: opening, p. 369 and start of p. 370** (Project MUSE text via
  OpenAlex). p. 369: "If settler colonialism is a theory, then presumably people of any racial,
  ethnic, or national heritage could appear in the role of settler. Why, then, have the English
  outpaced all others as the archetypical settlers, and why has the historiography on settler
  colonialism dealt almost entirely with the modern period when migration and conquest are
  age-old phenomena in human history?"; "By shifting attention away from settler colonialism's
  consequences to query its origins, scholars could test the theory's applicability in a wider
  variety of settings and refine it." Character: a testing/refining proposal, not rejection.
- Greer, "Settler Colonialism and Beyond," *JCHA* 30:1 (2019): 61–86 (`screq_greer_2019_jcha`).
  **Abstract only** (Érudit full text behind a bot wall). "The settler colonial approach has
  much to offer historians. However, when we consider the extended, 500-year history of the
  invasion of Indigenous North America, we encounter several sorts of colonialism; the settler
  variety stands out as a dominant force in some periods and regions, but it fades to
  insignificance in others." Two other modes, "Imperial/Commercial Penetration" and
  "Extractivism"; "Extractivism, it is argued here, has become the predominant form of intrusion
  into Indigenous spaces in recent decades." (Crossref/OpenAlex date the issue 2019; OpenAlex
  gives publication year 2020.)
- Greer, "Settler Colonialism and Empire in Early America," *WMQ* 76:3 (2019): 383ff
  (`screq_greer_2019_wmq`). **Read: opening, pp. 383–385** (via OpenAlex; first lines of p. 385 only). Australia "appears as
  a kind of 'ideal type' of modern settler colonialism"; "It was with this Australian history in
  mind that Patrick Wolfe first developed his theory"; Wolfe is "The most rigorous of the settler
  colonial theorists in my opinion" with "a highly suggestive, if somewhat schematic, theory of
  race formation" (pp. 384–385; the last phrase opens p. 385). The critical argument after that is unread.

Judgement: **roster rows suffice.** Macoun, Strakosch, Rowse and Shoemaker have no other entry.
Greer's other entry, liberal_order_framework, would misattribute his argument: his objection
comes from comparative early-American/New France colonial history (modes of colonialism), not
from the liberal order framework; edge 850 (LOF → settler_colonialism comparison) already uses
Greer 2018 for property formation. If Greer were later rostered in native_newcomer (his
"Imperial/Commercial Penetration" is the fur-trade mode that edge 869 already describes), the
existing comparison 869 could be supplemented by a critique native_newcomer → settler_colonialism
("Greer: the settler mode dominates some periods and regions and fades in others (2019)");
that is a roster decision, not proposed here.

### 2c. Black studies critics: Jared Sexton (2014/2016), Tapji Garba and Sara-Maria Sorentino (2020)

- Sexton, "The Vel of Slavery," *Critical Sociology* 42:4–5 (2016): 583–597
  (`screq_sexton_2016`; OpenAlex gives online-first year 2014). **Abstract only.** "the logic of
  decolonization movements for indigenous sovereignty and against the settler states of Canada
  and the USA overlap the discursive field of contemporary post-racialism in ways that
  circumvent the challenges and possibilities offered by black radicalism"; "the freedom drive
  that abolishes slavery unsettles both colonial and decolonial forms of sovereign
  determination."
- Garba and Sorentino, "Slavery Is a Metaphor," *Antipode* 52:3 (2020): 764–782
  (`screq_garba_sorentino_2020`). **Abstract only.** Tuck and Yang's "critique of metaphor entails
  the collapse of the triad into a settler‐native dyad, the reduction of slavery to forced
  labour, and a division between the material and the symbolic that forecloses not only an
  analysis of slavery, but also the constitution of settler colonialism itself."
  Target note: Tuck and Yang are settler_colonialism roster members (strand
  recognition_refusal_resurgence), so this is a critique of a text inside the entry.

Judgement: **roster rows suffice.** None of the three is on another roster. The `black` entry is
a 1920–2000 Black-history historiography (Woodson, Du Bois, Franklin, Hine …), not Black studies
theory; rostering Sexton there to license black → settler_colonialism would distort it. Revisit
if a post-2000 Black-studies strand is added to `black` or `racial_formation`.

Settler-colonialism summary: 0 edges now; 1 conditional (indigenous → settler_colonialism, on
rostering Kauanui); 1 possible after a roster decision (native_newcomer → settler_colonialism,
Greer).

---

## 3. environment (3 roster critics)

Existing: many contribution/influence edges in (geography, annales, science, anthropology,
economic, technology, indigenous, post, person entries cronon/worster/crosby/merchant/white/
pomeranz/leopold/carson/innis; since 1.132, dipesh_chakrabarty → environment, contribution, 918).
No critique edge.

### 3a. George Sessions (1996) — no atlas entry (deep ecology philosopher)

Source: `sessions_cronon_reply`, "Reinventing Nature, The End Of Wilderness?: A Response To
William Cronon's Uncommon Ground," *The Trumpeter* 13.1 (1996). **Read** (full HTML text,
trumpeter.athabascau.ca; original pagination not available).
- Section "William Cronon and the UC Irvine 'Reinventing Nature' Conference": "Most of the
  contributor's to Cronon's anthology are sympathetic in various degrees to the anthropocentric
  postmodernist approach."
- On "The Trouble with Wilderness": Cronon "starts out by claiming that our concept of wilderness
  has to be rethought or 'reinvented' in that it is a human or social construction"; "Cronon
  still fails, I think, to realize the full biological significance of protecting biodiversity
  and the ecological integrity of the Earth."
- Sessions also concedes movement: "by beginning to take ecological realities seriously, Cronon
  is forced to move a long ways from the postmodernist 'reinventing nature' theme".

Judgement: **roster row suffices.** The critique targets william_cronon (person entry) and the
wilderness_conservation_response strand, but Sessions belongs to no entry and deep ecology is not
an atlas field. No edge.

### 3b. David M. Johns (1990) — no atlas entry

Source: `johns_deep_ecology_reply`, *Environmental Ethics* 12.3 (1990): 233–252. **Abstract
only** (PDC publisher page read 2026-10-14; PhilPapers 403): "I argue that Guha is partly wrong in
claiming that deep ecology equates environmental protection with wilderness protection and simply
wrong in calling wilderness protection untenable or incorrect as a global strategy for
environmental protection"; "a biocentrism which integrates critical social theory can provide the
basis for an ethic that undercuts the environmental degradation from overconsumption and
militarism more effectively than a human-centered system."

Judgement: **roster row suffices.** A reply to Guha's 1989 critique of deep ecology (an
environmental-ethics debate); Johns has no entry. No edge.

### 3c. Peter Pesic (1999) — critic's entries: environment (critic), science (critic)

Source: `pesic_proteus_1999`, *Isis* 90.1 (1999): 81–94. **Abstract only** (OpenAlex): "Although
many writers state that Francis Bacon advocated the torture of nature in order to force her to
reveal her secrets, a close study of his works contradicts this claim. His treatment of the myth
of Proteus depicts a heroic mutual struggle, not the torture of a slavish victim."

Judgement: **no edge into environment.** The target is Merchant's *Death of Nature* reading of
Bacon (carolyn_merchant → science, edge 908). Pesic's only other entry is science, which the
science-studies workstream is handling; the candidate there is **science → carolyn_merchant,
critique** ("Pesic disputes the 'torture of nature' reading of Bacon (1999)"), evidence
abstract-level; flag to that workstream rather than draw here.

### 3d. Adjacent lead (not a roster critic; unread)

The 1990 *JAH* round table: Cronon, "Modes of Prophecy and Production" (1122–31) and Worster's
reply "Seeing Beyond Culture" (1142–47). Both are person entries (william_cronon,
donald_worster). The environment-family packet records both as unread
(`pe131_cronon_modes_1990`; worster/NOTES.md). Sessions (read) quotes Worster's reply (p. 1144)
accusing Cronon and Merchant of trying to "reduce environmental history to social history" — a
quotation inside Sessions, not read at source. A reciprocal critique pair
(william_cronon ↔ donald_worster) is the strongest in-period critique the environment family
lacks, but it needs the JAH pages. **Unread; not proposed.**

---

## 4. historyworkshop (2 roster critics)

Existing: edge 200 historyworkshop → language (comparison) already carries the Stedman Jones /
Kirk disagreement in its evidence note. No critique edge.

### 4a. Gareth Stedman Jones (1983) — entries: marx (critic), language (historian), historyworkshop (critic)

Sources: `languages_class`; `stedman_chartism_primary` (graph verification: opening 90–98 and
conclusion 173–178 read earlier; p. 95 "explicitly rejects replacing social with linguistic
interpretation"). Not re-read this session (another copy not fetchable); his position is
quoted below through Kirk (read).

### 4b. Neville Kirk (1987) — entries: marx (contributor), historyworkshop (critic)

Source: `kirk_class_selected_body`, "In Defence of Class: A Critique of Recent Revisionist Writing
upon the Nineteenth-Century English Working Class," *IRSH* 32 (1987): 2–47. **Read: pp. 2–4 and
46–47** (Cambridge PDF).
- p. 3: "a more precise task is attempted: to develop a critique of Gareth Stedman Jones's
  revisionist approach to labour history and the question of class, as revealed in his two
  essays on Chartism"; "In these essays Stedman Jones rejects the historiographically dominant
  'social' approach to Chartism in favour of a political interpretation."
- pp. 46–47: "Full support has been given to Stedman Jones's opposition to economic
  reductionism … Simultaneously, however, this article has suggested that, in his
  non-referential approach to language and in his refusal to make 'any simple prejudgement about
  the determining role of the social', Stedman Jones has effectively greatly underestimated the
  pressures and limits exerted by economic and social factors … In 'The Language of Chartism'
  and 'Rethinking Chartism' language and politics have been improperly wrenched loose from their
  material determinations. As a result the class-based character of Chartism has been falsely
  denied. Stedman Jones's rejection of a class-based reductionism has led not to materialism,
  but to an unconvincing idealism."
- p. 2 lists the revisionist critics of class: "Joyce (1980), Stedman Jones (1982 and 1983),
  Calhoun (1982) and Glen (1984)".

Judgement: **no edge into historyworkshop.** Neither critic criticises the History Workshop
movement; the `critic` role there records an internal debate (edge 200 already says so). The
debate is a strong, read, in-period (1983/1987) critique pair between two other entries, both
without a critique edge between them:
- **marx → language, critique** — "Kirk: Stedman Jones wrenches the language of Chartism loose
  from its material determinations (1987)". Kirk is a marx roster contributor; Stedman Jones is a
  language roster historian. Evidence: read.
- optionally **language → marx, critique** — "Stedman Jones: Chartism as a political language,
  not the expression of a class (1983)". Stedman Jones is already a marx roster *critic*. Evidence:
  Stedman Jones read earlier per the graph's verification note (pp. 90–98, 173–178); in this
  session only through Kirk's summary.
Recommend the marx → language edge; the reciprocal one only after re-reading Stedman Jones.

---

## 5. labourhistory (1 roster critic)

### 5a. Janaki Nair (1990) — entries: social (critic), subaltern (critic), gender (contributor), labourhistory (critic)

Source: `nair_chakrabarty_review`, review of Chakrabarty, *Rethinking Working Class History*,
*ILWCH* 37 (Spring 1990): 96–99. **Read** (full review, Cambridge PDF).
- p. 98: "But if the world cannot be seen in the grain of sand, are we condemned to relativism,
  however radical? Is not the capital-labor relation stable and persistent rather than
  episodic?"
- p. 98: "his text appears to reclaim the 'lonely hour of the last instance' for cultural
  traditions. But traditions too are forged and are brought to life within the context of
  capitalism."; "there is a disturbing attribution of 'immutability' to pre-bourgeois relations,
  always already given rather than rearticulated in differing circumstances."
- p. 98: "Chakrabarty's analyses of culture could have been greatly enhanced by attention to
  issues of gender, itself a cultural construct".
- p. 99: the book is "magnificent testimony to the possibility of working-class narratives
  emerging from the 'empirically additive' to become fully a part of the development of
  theory."

Judgement: **no new edge into labourhistory.** The critique targets Chakrabarty, and it is already
drawn as edge 701 social → subaltern (critique, "Nair questions fixed cultural survivals and
insufficient gender analysis"). Since revision 1.132 Chakrabarty has a person entry with
dipesh_chakrabarty → labourhistory (contribution, 916). Editorial option: retarget 701 (or add a
sibling) to **social → dipesh_chakrabarty, critique**, which is more exact than "subaltern". Not a
labourhistory edge either way; the roster row suffices there.

---

## 6. moral_regulation (2 roster critics)

Existing: foucault → moral_regulation (contribution, 858) already uses both abstracts as its
evidence ("its governmentality reformulation"); historicalsociology → (contribution, 859). No
critique edge.

- Mitchell Dean (1994), "'A Social Structure of Many Souls'," *CJS* 19:2 (1994): 145ff
  (`cdnsrc_dean_1994`). **Abstract only** (French; OpenAlex): "il pretend que plusieurs des
  problemes souleves dans ce cadre analytique peuvent plus efficacement etre formules en
  developpant la problematique de la gouvernementalite offerte par Michel Foucault" (accents as
  in the OpenAlex record).
- Hannu Ruonavaara (1997), "Moral Regulation: A Reformulation," *Sociological Theory* 15:3
  (1997): 277–293 (`cdnsrc_ruonavaara_1997`). **Abstract only**: Corrigan and Sayer "fuse
  Durkheimian and Foucauldian analysis with a basic Marxist theory. However, this framework gives
  too limited a perspective to their analysis. I suggest that moral regulation should not be seen
  as a monolithic project, as merely action by and for the State, nor as activity by the ruling
  elite only."

Neither critic has another entry. Dean's reformulation runs through Foucault; the only possible
critic's-entry edge would be **foucault → moral_regulation, critique**, which would misstate it:
Foucault did not criticise moral regulation; Dean used Foucault to reformulate Corrigan (edge 858
already records exactly that, as a contribution). Ruonavaara argues from Weber; the weber entry
does not hold him. Both are reformulations from inside the concept's sociology.

Judgement: **roster rows suffice.** No edge.

---

## 7. ethnohistory (2 roster critics)

Existing: anthropology → (contribution, 747); annales → (748); oral → (750); ethnohistory →
indigenous (comparison 749, which already cites Wilson; comparison 776); ethnohistory →
native_newcomer (866). No critique edge. Precedent: edge 420 indigenous → anthropology,
critique ("Wilson questions interpretations and translations detached from tribal and family
knowledge").

### 7a. Angela Cavender Wilson (1996) — person entry `angela_cavender_wilson`; also indigenous (historian), oral (historian)

Source: `wilson_indian_history`, "American Indian History or Non-Indian Perceptions of American
Indian History?" *AIQ* 20:1 (1996): 3–5. **Read** (full essay, UCSD-hosted JSTOR scan).
- p. 3: "American Indian history is a field dominated by white, male historians who rarely ask or
  care what the Indians they study have to say about their work. Under the guise of academic
  freedom they have maintained their comfortable chairs in archives across the country and
  published thousands of volumes on whites' interpretations of American Indian history."
- p. 3: "As long as history continues to be studied and written in this manner the field should
  more appropriately be called non-Indian perceptions of American Indian history."
- p. 4: "while archival materials may offer a glimpse into the world-view of Native people, the
  degree to which they can provide information on the American Indian half of the equation is
  quite small relative to what can be gained through an understanding of oral tradition."
- p. 5: "The idea that scholars can 'sift through' the biases of non-Indian written sources
  sufficient to get at the Indian perspective is presumptuous and erroneous. These scholars
  should not discontinue their research in the field, but they should discontinue the pretense
  that what they are writing is American Indian history."

Objection: the documentary method itself — reading non-Indian archives against their bias —
cannot yield Indigenous history without tribal and family historians. She does not use the word
"ethnohistory"; her target is archive-based American Indian history, which in the atlas is the
ethnohistory entry's documentary programme (documentary_method strand, Lurie) and claims
archives. Wilson acknowledges exceptions and the value of the written-word work (p. 5).

### 7b. Silvia Rivera Cusicanqui (1987) — entries: indigenous (contributor), oral (contributor), ethnohistory (critic)

Source: `rivera_oral`, "El potencial epistemológico y teórico de la historia oral: de la lógica
instrumental a la descolonización de la historia," *Temas Sociales* 11 (1987): 49–64. **Read:
section 1–2 (pp. 50–52) and closing** (12-page transcription linked from the CHIRAPAQ record,
historiaoralfuac.wordpress.com PDF). The transcription carries bracketed markers [49]–[64]; 16
markers for 16 pages, so each appears to close the original page — an inference, labelled as such.
- pp. 51–52: "Otros antropólogos y etnólogos, por el contrario, cerraban filas en torno a la
  emergente disciplina de la etnohistoria, que muy a pesar de sus valiosísimos aportes en torno a
  la 'originalidad' de las sociedades indígenas, se recluyó en la tarea de reconstruir cómo eran
  éstas antes de la invasión colonial europea. Su visión de la colonia —en ocasiones un tanto
  apocalíptica— se limitó a definiciones por carencia constatando la 'destrucción', el 'trauma',
  la 'desestructuración' de dichas sociedades, o bien su 'continuidad', siempre disminuida y
  recortada por la opresión colonial (ver, entre otros, Wachtel 1973; Murra 1975; Platt, 1976)."
- p. 52: "En consecuencia, no aportaron sustancialmente al conocimiento de nuevos fenómenos como
  la etnogénesis, la articulación ideológica y la redefinición estructural de las sociedades
  indias en el contexto colonial y neocolonial."
- Note 2 qualifies: Platt (1982) "desarrolla un nuevo enfoque de 'antropología histórica' que da
  cuenta de estos procesos."
- Close (p. 62, by the same marker inference): beyond "la lógica instrumental y la manipulación
  ideológica del investigador, nos aproximaremos entonces a la desalienación y descolonización
  de la historia."

Objection: Andean ethnohistory (naming Wachtel and Murra, both on the ethnohistory roster,
andean_histories strand) reconstructed pre-invasion societies and read colonial history as
destruction or diminished continuity, missing ethnogenesis and Indigenous re-articulation; the
THOA alternative is Aymara-directed oral history. A named, in-period critique; the roster's
"not an asserted affiliation" caution concerns her role, not the existence of the critique.

Judgement for ethnohistory: **edge warranted**: indigenous → ethnohistory, critique. Both critics
are on the indigenous roster (Wilson as historian, Rivera as contributor), both texts are read and
in period (1987, 1996), and Rivera names ethnohistory and its Andean authors. Suggested label:
"Rivera and Wilson: reconstruction from colonial documents without Indigenous historical
authority (1987, 1996)". Keep comparisons 749 and 776. Person-entry alternative:
angela_cavender_wilson → ethnohistory (critique) — narrower, and it would leave Rivera's sharper,
explicitly named critique unrepresented; the group edge is preferred, mirroring 420.

---

## 8. consumption (1 roster critic)

### Catherine Pagani (1993) — no other entry

Source: `pagani_clunas_review`, combined review incl. Clunas, *Superfluous Things*, *Material
History Review* 38 (Fall 1993): 88–90. **Read** (journal HTML, paras. 11–16; unpaginated).
- Para. 13: "Clunas devotes much of his introduction to discussing material culture and cites many
  of the current theoreticians. Oddly, though, he does not attempt to define the term, nor does
  he mention the pioneering writings of American material culturalist Thomas Schlereth or the
  recent work being done at the University of Leicester by Susan Pearce and her colleagues."
- Para. 16: "Superfluous Things is one of the more interesting books to appear recently and is
  particularly valuable in its approach of linking artifact with text."

Judgement: **roster row suffices; consider re-roling.** A favourable review with one definitional
quibble; Pagani has no other entry. "Critic" overstates it — `reviewer`/`comparison` would be
more exact (editorial choice). No edge.

---

## 9. cdn_immigration_ethnicity (1 roster critic)

### Roberto Perin (1983) — other entry: cdn_religion_reform (historian, Catholicism; title level)

Source: `cdnsrc_perin_1983`, "Clio as an Ethnic: The Third Force in Canadian Historiography,"
*CHR* 64:4 (1983): 441–467. **Read: opening only, p. 441** (via OpenAlex): "ACKNOWLEDGING THE
IMPORTANCE of ethnicity has become a convention in North America. Although the phenomenon has
existed at least since the turn of the century, it only attracted serious attention with the
eruption in the United States of the civil rights movement and in Canada of an increasingly
assertive Quebec nationalism during the Quiet Revolution. Is it mere coincidence that ethnic
groups began to be 'discovered' at a time when both states faced serious threats to their"
(text breaks off).

Judgement: **roster row suffices.** The critique is internal to ethnic history (the "Third Force"
historiography); cdn_religion_reform → cdn_immigration_ethnicity would misattribute it. Edge 832
(identity → cdn_immigration_ethnicity, comparison) already carries the same opening. Full text
unread (UTP Journals, paywalled).

---

## 10. cdn_black_history (1 roster critic)

### Barry Cahill (1999) — no other entry (Nova Scotia archivist)

Source: `cbh_cahill_1999`, "The Black Loyalist Myth in Atlantic Canada," *Acadiensis* 29:1
(1999): 76–87. **Read** (UNB PDF; pages from running heads).
- p. 76: "Certainly there were Blacks among the Loyalists, but the fugitive slaves of Patriots …
  did not by virtue of that fact become 'Black Loyalists'. The fugitive slaves were a
  subcategory of 'Blacks' not 'Loyalists'."
- p. 77: "the Black Loyalist myth, an invention of academic scholars, has become a potent force in
  the cultural heritage of the Black community"; "It was perfectly attuned to the ideology and
  psychology of the civil rights and human rights movements of the 1960s and 1970s".
- p. 79: "Its origins lie in James Walker's normative interpretation of the fugitive slaves as
  American Loyalists and the American Revolution as the 'slaves' war for independence'."
- p. 81: Walker and others "fail to recognize that the underlying reason for this was the
  hegemony of the Black Loyalist myth and its progressive undermining of Black history."
- Reply: Walker, "Myth, History and Revisionism," same issue, 88–105 (`cbh_walker_1999`; graph
  note says full text read earlier; not re-read here).

Judgement: **roster row suffices.** A sharp, read, in-period critique, but internal to the entry
(critic and target, Walker, both on the cdn_black_history roster, orientations_debate strand)
and Cahill has no other entry. If an internal-debate display exists for strands, this is a model
case; no edge.

---

## 11. cdn_childhood_youth (1 roster critic)

### John Bullen (1985) — no other entry

Source: `cdnsrc_bullen_1985`, "Orphans, Idiots, Lunatics, and Historians," *HS/SH* 18:35 (1985):
133–45. **Unread.** The HS/SH site returned a Cloudflare challenge (not circumvented); OpenAlex has
only the list of books reviewed (Rooke and Schnell, *Discarding the Asylum* and *Studies in
Childhood History*; Simmons, *From Asylum to Welfare*; Jones and Rutman, *In the Children's
Aid*) and marks it closed.

Judgement: **roster row suffices; role unverified.** Nothing read establishes that Bullen's essay
is a critique; the roster context already says its judgement "is not described until it is
read". No edge.

---

## 12. cdn_sixties (1 roster critic)

### Claude Couture (1991) — no other entry

Source: `c60_couture_1991`, *Le mythe de la modernisation du Québec* (Méridien, 1991).
**Metadata only.** Two reviews exist on Érudit (OpenAlex: *Recherches sociographiques* 34:1, 1993,
doi:10.7202/056750ar; *RHAF* 46:4, 1993, doi:10.7202/305156ar); Érudit's bot wall blocked them;
OpenAlex holds no abstract.

Judgement: **roster row suffices.** Argument unread. By title the target is the modernization
narrative of the Quiet Revolution, which the atlas carries in quebec_historiography (edge 880 is
the comparison to cdn_sixties); Couture is on neither quebec_historiography nor any other roster.
No edge.

---

## 13. cdn_political_national (1 roster critic)

### Adam Chapnick (2000; 2005) — no other entry

Source: `cdng_chapnick_2000`, "The Canadian Middle Power Myth," *International Journal* 55:2
(2000): 188ff. **Read: opening, p. 188** (via OpenAlex): "This vagueness is deliberate and
conceals a striking reality: Canada's status as a middle power is a myth. The history of
middlepowerhood uncovers a tradition of Canadian rhetoric crafted to justify the attainment of
disproportionate influence in international affairs. [note marker omitted] This subtle process of nationalist
self-promotion had its genesis in 1942 when diplomat Hume Wrong introduced the functional
principle". `cdng_chapnick_2005` (*The Middle Power Project*): description only (graph note).

Judgement: **roster row suffices.** Internal revisionism within diplomatic history (target: the
external_relations strand's "golden age" account, Stacey/Granatstein/Hillmer, same entry); Chapnick
has no other entry. No edge.

---

## Judgement

**Edges the evidence supports (critic's own entry → criticised entry):**
1. cdn_working_class → liberal_order_framework (Palmer 2009). Read.
2. quebec_historiography → liberal_order_framework (Fecteau 2009). Read. Keep 851 as the
   contribution and move Fecteau's critique out of its evidence note.
3. cdn_religion_reform → liberal_order_framework (Christie 2009). Read. A critique with
   amendment; contribution is the fallback kind.
4. indigenous → ethnohistory (Rivera 1987; Wilson 1996). Read; in period.

**Conditional (a roster change first):**
5. indigenous → settler_colonialism (Kauanui 2016), only if Kauanui is added to the indigenous
   roster. Konishi is abstract-level.
6. native_newcomer → settler_colonialism (Greer 2019), only if Greer is added to native_newcomer.
   Abstract-level; Érudit blocked.

**Off-target edges this audit turned up (they do not touch the 13 entries' critics' rows):**
7. marx → language (Kirk 1987 against Stedman Jones). Read. The History Workshop `critic` rows
   record this debate. Reverse edge language → marx only after Stedman Jones is re-read.
8. science → carolyn_merchant (Pesic 1999). Abstract only. Pass to the science-studies
   workstream.
9. social → dipesh_chakrabarty (Nair 1990). Read. This is a retarget or sibling of 701 now that
   1.132 has landed.

**The roster rows are enough for:** Sandwell and Ajzenstat (LOF); Macoun, Strakosch, Rowse,
Shoemaker, Sexton, Garba and Sorentino (settler colonialism); Sessions and Johns (environment);
Dean and Ruonavaara (moral regulation); Pagani; Perin; Cahill; Bullen; Couture; Chapnick. In every
case the critic has no other entry, or the other entry would misattribute the argument, or the
debate is internal to the entry. Role queries: Pagani is closer to reviewer; Bullen's critic role
is unverified.

**Lead, unread:** william_cronon ↔ donald_worster, from the 1990 *JAH* round table. This is the
environment family's missing in-period critique, and the JAH pages are needed.

## Table

| # | Proposed edge (source → target) | Kind | Label (suggested) | Key quote | Evidence status |
|---|---|---|---|---|---|
| 1 | cdn_working_class → liberal_order_framework | critique | Palmer: liberal order as an elastic category that sidesteps capitalism (2009) | "it allows mainstream historians to avoid confronting just how critically important it is to name the frontline enemy: capitalism" (Underhill Review, Fall 2009, unpaginated) | read |
| 2 | quebec_historiography → liberal_order_framework | critique | Fecteau: liberal order is not a unitary project; liberalism as a social logic (2009) | "it is difficult (and probably vain) to conceive of the liberal order as a unitary enterprise, founded on stable principles" (Underhill Review, sect. I) | read |
| 3 | cdn_religion_reform → liberal_order_framework | critique (fallback: contribution) | Christie: the church as a builder, not an opponent, of liberal order (2009) | "no one who is acquainted with the work of … can ignore religion as a powerful vehicle in the creation of the liberal order" (Underhill Review) | read |
| 4 | indigenous → ethnohistory | critique | Rivera and Wilson: reconstruction from colonial documents without Indigenous historical authority (1987, 1996) | Rivera: ethnohistory "se recluyó en la tarea de reconstruir cómo eran éstas antes de la invasión colonial europea" (pp. 51–52, by marker inference); Wilson: "The idea that scholars can 'sift through' the biases of non-Indian written sources … is presumptuous and erroneous" (p. 5) | read |
| 5 | indigenous → settler_colonialism (conditional: roster Kauanui) | critique | Indigenous scholars: settler colonial studies cannot replace Indigenous studies (2016–19) | "Settler Colonial Studies does not, should not, and cannot replace Indigenous Studies." (Kauanui 2016, para. 4) | read (Kauanui); abstract (Konishi) |
| 6 | native_newcomer → settler_colonialism (conditional: roster Greer) | critique | Greer: the settler mode dominates some periods and regions and fades in others (2019) | "the settler variety stands out as a dominant force in some periods and regions, but it fades to insignificance in others" (JCHA abstract) | abstract |
| 7 | marx → language (off-target) | critique | Kirk: Stedman Jones wrenches Chartist language loose from its material determinations (1987) | "language and politics have been improperly wrenched loose from their material determinations" (IRSH 32, p. 47) | read |
| 8 | science → carolyn_merchant (off-target; science workstream) | critique | Pesic disputes the 'torture of nature' reading of Bacon (1999) | "a close study of his works contradicts this claim" (Isis abstract) | abstract |
| 9 | social → dipesh_chakrabarty (off-target; retarget/sibling of 701) | critique | Nair: cultural survivals made immutable; gender unexamined (1990) | "a disturbing attribution of 'immutability' to pre-bourgeois relations" (ILWCH 37, p. 98) | read |
| — | none (roster suffices): Sandwell → LOF | — | — | families as "'hot zones' where the new liberal order … was imposed, embraced, contested, rejected, or absorbed" (2003 abstract) | abstract (2003); metadata (2009) |
| — | none (roster suffices): Ajzenstat → LOF | — | — | "his ignorance of facts on the ground … He shuns the primary sources." | read |
| — | none: Macoun & Strakosch, Rowse, Shoemaker → settler_colonialism | — | — | SCT "posits a structural inevitability to the settler colonial relationship" (2013 abstract) | read (Macoun; AAM, no journal pages); abstract (Rowse); read p. 369 (Shoemaker) |
| — | none: Sexton; Garba & Sorentino → settler_colonialism | — | — | "the collapse of the triad into a settler‐native dyad" (2020 abstract) | abstract |
| — | none: Sessions, Johns → environment | — | — | "Cronon still fails, I think, to realize the full biological significance of protecting biodiversity" | read (Sessions); abstract (Johns) |
| — | none: Dean, Ruonavaara → moral_regulation | — | — | "should not be seen as a monolithic project, as merely action by and for the State" (1997 abstract) | abstract |
| — | none: Pagani → consumption | — | — | "Oddly, though, he does not attempt to define the term" (para. 13) | read |
| — | none: Perin → cdn_immigration_ethnicity | — | — | "Is it mere coincidence that ethnic groups began to be 'discovered'…" (p. 441) | read (opening only) |
| — | none: Cahill → cdn_black_history (internal) | — | — | "an invention of academic scholars" (p. 77) | read |
| — | none: Bullen → cdn_childhood_youth | — | — | — | unread |
| — | none: Couture → cdn_sixties | — | — | — | metadata |
| — | none: Chapnick → cdn_political_national (internal) | — | — | "Canada's status as a middle power is a myth" (p. 188) | read (opening only) |
