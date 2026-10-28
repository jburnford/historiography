# Edge review C: LaRocque, L. T. Smith, McNickle, *Life Lived Like a Story* (2026-10-28)

Agent C, working read-only to `BRIEF.md` in this folder. I checked the graph on disk (`historiography-1920-2000.json`) on 2026-10-28. I used the 1.201 evidence notes (`evidence-indigenous-authored.md` §§1.7–1.9, 2.4, 2.10; `evidence-community-engaged.md` §§3, 9–10, P1) and did not open `PRIVATE-identity-review.md`. I sent no email address or identifier to any service. No identity wording is added beyond what the entries already record.

**Texts I read for this review**
- **LaRocque, *Native Writers Resisting Colonizing Practices in Canadian Historiography and Literature*** (PhD, Manitoba, 1999), project copy of the MSpace deposit (`ind126_larocque_thesis`). PDF pp. 11–13, 21, 25–26, 40, 47–52, 60–62, 67, 70–72, 102, 107–109, 119, 135–136, 190–191, 239–241, 249 and 296 read; the rest searched by keyword.
- **Jason Edward Black, review of *When the Other Is Me*,** *American Indian Culture and Research Journal* 35:4 (2011): 285–288. Read in full: https://escholarship.org/uc/item/9225r8jx (CC BY-NC).
- **Peter Iverson, introduction to McNickle, *Native American Tribalism*** (1993 reissue), OUP publisher preview. Pp. iii–xviii read in full; earlier agents read only iii–v, xv and xvii–xviii. McNickle's preface, pp. xix–xx, read.
- **McClellan, *Arctic* 45:2 (1992): 205–206,** and **Gmelch, *BC Studies* 94 (1992): 85–86.** Both reread in full to check the quotations in edges 2173–2175.
- **CHA prize-winner page for Cruikshank,** read: https://cha-shc.ca/prize-winner/julia-a-cruikshank/ . Index: https://cha-shc.ca/prize-winners/ .
- **"Decolonizing Education: A Conversation with Linda Tuhiwai Smith",** interview by Bhakti Shringarpure, *Los Angeles Review of Books*, 18 May 2021: https://lareviewofbooks.org/article/decolonizing-knowledge-a-conversation-with-linda-tuhiwai-smith . **Read in part:** the fetch tool returned a summary with exact short excerpts; paragraph numbers are the tool's count from the first question.
- **Routledge page for Smith, Tuck and Yang, eds., *Indigenous and Decolonizing Studies in Education*** (2019), table of contents only: https://www.routledge.com/Indigenous-and-Decolonizing-Studies-in-Education-Mapping-the-Long-View/Smith-Tuck-Yang/p/book/9781138585867
- **American Academy of Arts and Sciences profile of McNickle** (read through a fetch summary with one exact sentence): https://www.amacad.org/person/william-darcy-mcnickle
- **Tuck and Yang, "Decolonization Is Not a Metaphor"** (2012, open access). Searched for Smith; nothing usable.

**Blocked**
- Bloomsbury Collections, *Decolonizing Methodologies* 3rd ed. (DOI 10.5040/9781350225282): institutional login.
- Google Books API: daily quota exhausted.
- Newberry finding-aid series 8 (University of Saskatchewan materials): TLS handshake failure.
- Wayback captures: the fetch tool cannot reach web.archive.org, so I could not reread Carlson, Lutz and Schaepe (2009).

---

## 1. Emma LaRocque (`emma_larocque`)

### 1a. Existing edges

| Edge | Endpoints (type) | Verdict | Reason |
|---|---|---|---|
| edge_2137 | emma_larocque → indigenous / `metis_representation_criticism` (connection) | **keep** | Matches PDF pp. 37–38. The strand is right after the split: Indigenous-authored critique belongs in part 2. |
| edge_2138 | emma_larocque → jennifer_s_h_brown (critique) | **keep** | PDF p. 249 checked: the "neo cross-cultural approach … (Bailey, Jaenen, Trigger, Brown, Van Kirk)". The label says only what the text says. |
| edge_2139 | howard_adams → emma_larocque (connection) | **keep** | PDF p. 47, "Metis historian and social critic Howard Adams … 'the White Ideal'". |
| edge_2140 | edward_said → emma_larocque (connection) | **keep** | PDF p. 70 checked word for word. |
| edge_2165 | emma_larocque → native_newcomer / `historians_indian` (critique) | **keep** | PDF p. 119 checked. Walker's 1971 survey (`nnreq_walker_1971`) is in this strand. |
| edge_2166 | emma_larocque → native_newcomer / `contact_wendat_representation` (critique) | **reroute** `target_strand` → `native_newcomer/historians_indian` | See note 1 below. |
| edge_1003 (related) | **indigenous** → sylvia_van_kirk (critique) | **reroute** `source` → `emma_larocque` | See note 2 below. |
| edge_868 (related) | indigenous → native_newcomer / `indigenous_critiques_of_framing` (critique) | **keep** | A field-level summary of Sioui, Stevenson (Wheeler), LaRocque, Fixico and S. Miller. Correct after the split. |

**Note 1 (edge_2166).** The passage (PDF pp. 135–136) concerns how scholars "gauge" Native writing: Trigger's *foreword* to Sioui's *Autohistory* is "a typical example of containment". It is about reception of Indigenous historical writing, not about Trigger's Wendat or contact history, which is what `contact_wendat_representation` holds. `historians_indian` ("How historians wrote about Indigenous peoples") already holds Trigger's 1986 survey and is the better fit.
- Operation: `edge_endpoint_sets` {edge_2166, target_strand, expect `native_newcomer/contact_wendat_representation`, value `native_newcomer/historians_indian`}.
- In the evidence note, replace "the arrow goes to the strand that holds his contact-era work" with "the arrow goes to the strand that holds his account of how historians wrote about Native peoples".

**Note 2 (edge_1003).** The edge's own evidence note says it "represents Emma LaRocque's specified criticism … not a verdict of the Indigenous history entry". B made the reroute conditional on her person entry (ihB_rel_15). The entry is now live (1.201), so the condition is met.
- Operation: `edge_endpoint_sets` {edge_1003, source, expect `indigenous`, value `emma_larocque`}.
- Drop the evidence-note sentence that begins "This arrow represents…".

**Are her critiques of the academy drawn against the right fields after 1.201?** Mostly yes.
- **Her targets are part-1 settler scholarship:** Walker's survey, Trigger's foreword, the cross-cultural approach of Bailey, Jaenen, Trigger, Brown and Van Kirk, and fur-trade historians. They are correctly drawn into `native_newcomer`, or to person nodes in it.
- **Her own position sits in part 2** (`indigenous/metis_representation_criticism`; roster row in `native_newcomer/indigenous_critiques_of_framing` as a critic, not a member). That is also correct.
- **Two gaps remain:**
  1. edge_1003 still leaves from the field rather than from her (note 2).
  2. Her critiques of *postcolonial studies* and *anthropology*, which the dissertation makes explicitly, are not drawn at all (1b).
- **Book date.** *When the Other Is Me* is unread beyond Black's review. Black's header gives "Winnipeg: University of Manitoba Press, **2010**" (p. 285). This supports the 2010 printing that the chronology (`el_other_2011`) marks as unchecked. See corrections (§5).

### 1b. Proposed new edges

```
{ id: "erC_01", source: "emma_larocque", target: "post", target_strand: null, type: "critique",
  label: "Native Canadians 'cannot enjoy fully \"post-coloniality\"'; a postcolonial reader that represents Natives 'only through non-Native Canadians' is 'unacceptable' (1999)",
  map_label: "Not yet post-colonial, 1999",
  evidence: "PDF pp. 50–51: Ashcroft, Griffiths and Tiffin treat white Canadian literature as post-colonial; in The Post-Colonial Studies Reader 'no Native writers or scholars are included … I find it unacceptable'; 'Obviously, Native Canadians cannot enjoy fully \"post-coloniality\" since their colonial experience is imbricated with the past and present.' p. 40: The Empire Writes Back treats 're/settler whites' as 'the colonized resisting the mother country'. p. 70: she will avoid the 'obscure language which has become such an uncontrollable part of post-colonial criticism'. Continued in the 2010 book, p. 167, as quoted by Black (2011, p. 285): 'some scholars live in the illusion that … by their postcolonial powers of analysis, they have neutralized the colonial experience'. A critique of the field's scope and practice; she also uses its resources (Said, edge_2140), so it is not a rejection.",
  source: ["ind126_larocque_thesis", "NEW erC_black_2011 (AICRJ 35:4, 285–288, https://escholarship.org/uc/item/9225r8jx)"],
  read_status: "dissertation pages read; 2010 book as quoted by a named reader read in full" }

{ id: "erC_02", source: "emma_larocque", target: "georges_e_sioui", target_strand: null, type: "critique",
  label: "Finds Sioui's call for 'an ethical approach to history' appealing but his autohistory 'at times obscure' on method, and his 'ideological portrait of Amerindians' too close to the Noble Savage (1999)",
  map_label: "Autohistory questioned, 1999",
  evidence: "PDF pp. 240–241: 'Sioui's thesis on \"autohistory\" is at times obscure, especially when he turns to the issue of historical methodology'; 'it is not at all clear whether he is espousing a \"division of labour\" between white and Native (or Huron?) historians' (quoting Sioui p. 36); 'Parts of Sioui's proposal … is appealing, for example, his call for \"an ethical approach to history\"'; 'I have difficulty with his idealization … to the extent the portrait resembles the Noble Savage'. Qualified critique between two Indigenous historians, distinct from her critique of Trigger's foreword to the same book (edge_2166).",
  source: ["ind126_larocque_thesis"], read_status: "pages read" }

{ id: "erC_03", source: "fanon", target: "emma_larocque", target_strand: null, type: "connection",
  label: "Takes Fanon and Memmi as 'the classic sources' on internalised colonisation, while noting that The Wretched of the Earth does not treat Native North Americans (1999)",
  map_label: "Fanon and Memmi, 1999",
  evidence: "PDF p. 48: 'Frantz Fanon and Albert Memmi are the classic sources for discussion on the processes of internalization'; p. 12: classic (Fanon, Memmi) and contemporary works 'have convincingly shown that colonization produces a pervasive structural and psychological relationship between the colonizer and the colonized'; p. 40 (qualification): 'Frantz Fanon in Wretched of the Earth does not deal with the treatment of Native North Americans either'. Parallel to edge_2140 (Said). Memmi has no node.",
  source: ["ind126_larocque_thesis"], read_status: "pages read" }

{ id: "erC_04", source: "emma_larocque", target: "anthropology", target_strand: null, type: "critique",
  label: "Reads Mandelbaum's The Plains Cree (1940) as dividing Cree technology 'into disparate pieces, giving the impression of a people frozen in time', a book taught without discussion of its 'Eurocentric assumptions' (1999)",
  map_label: "Ethnography as freezing, 1999",
  evidence: "PDF pp. 107–108, after Duchemin on Mackenzie's 'ethnographical curiosities': 'This is very similar to my reading of David Mandelbaum's treatment of Cree \"tools\" in The Plains Cree … one of the earlier anthropologists in the 1930s'; 'This book was first published in 1940 but I do not recall any discussion about its Eurocentric assumptions.' OCAP: her personal and family recollections on p. 108 are not used. Mandelbaum has no node (people record absent; maurice_mandelbaum is a different person). Black (2011, p. 286) independently lists 'anthropologists (David Mandelbaum)' among the colonial authors treated in the 2010 book, chs. 2–3.",
  source: ["ind126_larocque_thesis", "NEW erC_black_2011"], read_status: "pages read; reader read in full" }

{ id: "erC_05", source: "emma_larocque", target: "native_newcomer", target_strand: "native_newcomer/fur_trade_national_economy", type: "critique",
  label: "Charges fur-trade historians with a 'double standard': Indians generalised as of 'covetous disposition' while European self-interest is overlooked; E. E. Rich 'persistently uses colonial phrases' such as 'crafty' and 'shrewd enough' (1999)",
  map_label: "Fur-trade double standards, 1999",
  evidence: "PDF p. 102: 'It is quite common, for example, for fur trade historians to generalize Indians as having a \"covetous disposition,\" quite obviously employing the double standard by over-looking European self-interests.' p. 109: 'fur trade historian E.E. Rich persistently uses colonial phrases such as \"crafty,\" \"shrewd enough,\" \"sophisticated enough\" or \"hardened enough\"'; 'Even the more objective John C. Ewers qualifies his compliments … \"sharp enough\"'; she cites Walker (1971, p. 34) as noticing the same contradiction. The existing native_newcomer roster row already cites pp. 102, 109; no edge carries it. Rich has no node or row: the coordinator may add a precursor row for him in this strand, or set target_strand null.",
  source: ["ind126_larocque_thesis", "nnreq_walker_1971"], read_status: "pages read" }

{ id: "erC_06", source: "olive_patricia_dickason", target: "emma_larocque", target_strand: null, type: "connection",
  label: "Counts Dickason's The Myth of the Savage, by 'the prolific pace-setting scholar', among Native 'counter produced works' on the Indian image: 'clearly anti-colonial' (1999)",
  map_label: "Dickason as resistance scholarship, 1999",
  evidence: "PDF p. 190: works 'range from my slim Defeathering The Indian … to the voluminous The Myth of the Savage by the prolific pace-setting scholar Olive Patricia Dickason. Such productions have not been well understood as the resistance works that they in fact are.' p. 191: the title 'represents more closely Western rather than Native tradition. Still, I consider it an expression of resistance for it is clearly anti-colonial.' p. 21 (already in B's notes): a qualified use of Dickason's 'strain of tolerance' reading. A reading and alignment, not a debt claim.",
  source: ["ind126_larocque_thesis", "ind126_dickason_myth"], read_status: "pages read" }

{ id: "erC_07", STAGE 2 / include:false (coordinator and user to decide),
  source: "emma_larocque", target: "settler_colonialism", target_strand: null, type: "connection",
  label: "Rejects the native/settler binary of Fanon and postcolonial studies: Native peoples 'were the original settlers', other Canadians 'immigrant re/settlers'; Native peoples resist being 'dominated by \"settler colonies\"' (1999)",
  map_label: "Original settlers, re/settlers, 1999",
  evidence: "PDF pp. 25–26: 'Fanon has used the terms \"native\" in opposition to the word \"settler.\" Post-colonial studies generally refer to \"indigenous\" against \"invader-settlers.\" I take the view that Native peoples were the original settlers in the sense of inherent indigenous presence on this land … I refer to all other State-created Canadians as immigrant re/settlers.' p. 51: 'Natives have been protesting their subjugated or exiled position within the conditions of being dominated by \"settler colonies.\"' This is her own use and reworking of 'settler' vocabulary in 1999, before the field was named. It is NOT engagement with Wolfe, Veracini or settler colonial studies: none appear in the dissertation, by keyword search.",
  source: ["ind126_larocque_thesis"], read_status: "pages read" }
```

### 1c. Reception
- **Black (2011):** "the most foundational and most recent works in decolonial theory (particularly in Native studies and postcolonial studies literature)" are her "framework" (p. 285). He places the book in "Native studies" talk-back scholarship and says its Canadian focus is what makes it "unique" (pp. 285–286).
- No historian's reading of the 2010 book was found through an allowed route.

---

## 2. Linda Tuhiwai Smith (`linda_tuhiwai_smith`)

### 2a. Existing edges

| Edge | Endpoints (type) | Verdict | Reason |
|---|---|---|---|
| edge_760 | linda_tuhiwai_smith → indigenous / `methods` (connection) | **keep; flag the source** | See note 3 below. |
| edge_1719 | ranginui_walker → linda_tuhiwai_smith (connection) | **keep** | Rests on her own 2022 words (transcript pp. 8–9, read by the earlier dossier). The label is accurate. No `map_label` (display only). |
| edge_2171 | linda_tuhiwai_smith → community_engaged_indigenous (connection) | **keep** | Leddy (2010, n. 6 and n. 32) and Kovach (2010, p. 42) are named readers. The label attributes Kovach's qualification to Kovach. Right field: the readers are part-3 practitioners. |
| edge_419 (related) | post → indigenous, "Smith explicitly uses Said" | **keep for now; reroute held** | B's ihB_rel_28: reroute to edward_said → linda_tuhiwai_smith only after the 1999 introduction is verified through an allowed route (§2c). |
| edge_127 (related) | indigenous → identity (critique), Smith's agenda | **keep for now; reroute held** | Same condition (ihB_rel_29). |

**Note 3 (edge_760).** The edge rests on `promotion01_smith`. That source's `citation` field still names the host of the scanned copy. B's correction C1 classed that copy as a reading-pack upload, a route the provenance rule excludes and says never to name. `smith_decolonizing.verification.note` says "University-hosted 24-page scanned extract downloaded".
- The relationship is general ("Self-determination and authority over research") and is also supported by Kovach and Leddy reading her, so the edge can stand.
- The source text needs cleaning: `source_field_sets` on `promotion01_smith.citation` and `smith_decolonizing.verification.note`, removing the host description. The page claims should be marked "awaiting re-verification through the publisher".

### 2b. Proposed new edge

```
{ id: "erC_08", STAGE 2 / include:false (read through a tool excerpt; recheck the paragraph before stage 1),
  source: "fanon", target: "linda_tuhiwai_smith", target_strand: null, type: "connection",
  label: "Names Fanon first among the writers she read when, writing Decolonizing Methodologies, 'there was no literature about decolonizing' (2021 interview)",
  map_label: "Fanon among her resources",
  evidence: "LARB, 18 May 2021, para. 28 (tool count): 'There is Frantz Fanon, obviously', with Malcolm X and 'Paulo Freire later'. The question was about Ngũgĩ wa Thiong'o ('You influenced him or he influenced you?'). Nearby, she says that when she began the book there was no literature on decolonizing, so she 'went far and wide' (tool paraphrase plus exact phrase). Her 2022 transcript (p. 5) also invokes Freire. Freire, Ngũgĩ and Malcolm X have no nodes.",
  source: "NEW erC_larb_smith_2021 (https://lareviewofbooks.org/article/decolonizing-knowledge-a-conversation-with-linda-tuhiwai-smith)",
  read_status: "read in part (exact excerpts via fetch tool)" }
```

**Settler colonial studies: no edge proposed.**
- In the 2021 interview the term is the interviewer's: "Indigenous studies takes away the 'post' because settler colonialism is alive and well" (para. 50). Smith answers "Yes. It is also, in reality, such a small piece of time … Colonialism has occupied 500 or 600 years … We can decolonize" (para. 51).
- She does not use "settler colonialism" in her own sentences there (tool check). An assent to an interviewer's premise is not enough for an edge.
- She co-edited *Indigenous and Decolonizing Studies in Education* (Routledge, 2019) with Eve Tuck and K. Wayne Yang. Both are on the `settler_colonialism` roster; neither is a node. The editors' joint introduction is unread (publisher TOC only), so the collaboration is recorded as held, not as an edge.

### 2c. Held
- ***Decolonizing Methodologies* (1999), introduction pp. 1–5 (Said, Foucault, Collins; insider/outsider), through an allowed route.** Bloomsbury Collections is login-only and the Google Books quota is exhausted. This decides edges 419, 127 and 760.
- **Introductions to the 2012 and 2021 editions** (BL catalogue contents only), and the Smith–Tuck–Yang introduction (2019). These are the likeliest places for her own words on settler colonialism.
- ***A Civilising Mission?* (2001, with Judith Simon):** co-produced Native Schools history, catalogue-level only. If read, it is a packaged-entry candidate under the user's rule, not an edge from Smith alone.

---

## 3. D'Arcy McNickle (`darcy_mcnickle`)

### 3a. Existing edges

| Edge | Endpoints (type) | Verdict | Reason |
|---|---|---|---|
| edge_775 | darcy_mcnickle → indigenous / `native_history_institutions` (connection) | **revise** | See note 4 below. |
| edge_1699 | vine_deloria_jr → darcy_mcnickle (critique) | **keep** | Correctly marked as mediated (Beck p. 24 n., citing Parker p. 195). It is program-level, not a rejection of McNickle's writing. No `map_label` (display only). |
| edge_2163 | darcy_mcnickle → ethnohistory (connection) | **keep** | Iverson p. v checked: "has become an extremely influential place". Hoxie's remark is correctly kept as reported. The field placement is reasonable after the split: the Newberry centre's later programme under Jennings and Hoxie is part-1 scholarship. |

**Note 4 (edge_775): exact new wording.** The current relationship ("Historical synthesis and institution-building") is generic. The evidence note still says the sources "do not establish particular book arguments", which the 1.201 reading of the preface superseded.
- **relationship:** "Wrote against administrators' 'certainty that native America had vanished before the march of progress' (1973) and helped build Native history's institutions; Iverson (1993) called Native American Tribalism 'a book ahead of its time'."
- **map_label:** "Against the vanishing Indian, 1949–73"
- **evidence_note:** keep the 1.201 sentences. Replace "Institutional and bibliographic evidence does not establish particular book arguments …" with: "Iverson, introduction to the 1993 reissue, p. vi (read 2026-10-28): the book's 'general theme seems less innovative or path-breaking perhaps today. However, that changed perception is a commentary on how the field has been altered in ways generally presaged by this book'. Iverson also judges that McNickle's 'early analysis of the Settlement Act in Alaska now appears overly optimistic' (p. vi)."
- `source_ids` unchanged (ihb_iverson_1993 is already there).

### 3b. Proposed new edges
None. Nothing read in McNickle's own words or a named reader's supports a further edge.
- **Settler colonialism:** no text read connects him to the frame, and none should be synthesised from his anti-termination argument.
- **Iverson pp. xiii–xviii:** they survey "new directions" in American Indian history, Indian-centred history and "a more ethnohistorical approach" (p. xviii). They do not attribute those to McNickle, so no influence edge is drawn.

### 3c. Chronology addition
- **1966: head of the anthropology department, University of Saskatchewan, Regina.**
  - kind: post; track: context.
  - Source: AAAS profile, exact sentence: "That same year, he became head of the anthropology department at the University of Saskatchewan, Regina." The existing `ind126_mcnickle` finding-aid record also notes "University of Saskatchewan work" (indexed only).
  - The end year (retired June 1971, per Newberry indexed text in search results) is unverified, because the finding-aid series page failed (TLS). Record 1966 only, as a year event, not an interval.
  - A Canadian post: relevant to the Canada focus. No edge.

### 3d. Held
- **"American Indians Who Never Were"** (1970/71, critique of anthropology): versions unresolved (dossier `held-cases.json`); text unread.
- **Parker, *Singing an Indian Song* (1992), and Parker (1990) bibliography:** eScholarship returned 403 earlier.
- **Collier, Tax, Thomas, Fey, Clyde Warrior and Iverson:** relationships documented but no nodes (dossier).
- ***The Indian Tribes of the United States* (1962):** unread.
- **Iverson p. xv:** this page also places McNickle within Métis history. That is ancestry content and stays out under OCAP finding 3.

---

## 4. *Life Lived Like a Story* (`life_lived_like_a_story`)

### 4a. CHA prize
- **Confirmed:** the CHA's own page lists it under **1992**, prize titled on the page "The CHA Best Scholarly Book in Canadian History Prize".
  - Winner line: "Julia A. Cruikshank", *Life Lived Like a Story: Life Stories of Three Yukon Native Elders* (UBC Press/University of Nebraska Press).
  - Source: https://cha-shc.ca/prize-winner/julia-a-cruikshank/ (index: https://cha-shc.ca/prize-winners/, 1992 entry).
- **The CHA page credits Cruikshank alone; Sidney, Smith and Ned are not named.** Record the award as the CHA records it, and keep the entry's packaging and four-way credit as the book credits them.
- **Same year's honourable mentions:** Schmalz, *The Ojibwa of Southern Ontario*; Gauvreau; Mitchinson.
- The prize's 1992-era name (Wikipedia says the Sir John A. Macdonald Prize) is **not** confirmed on a CHA page I read. Do not state it.

**Proposed chronology event**
- **label:** "CHA Best Scholarly Book in Canadian History Prize, awarded (as the CHA lists it) to Julia A. Cruikshank for Life Lived Like a Story"
- **date:** 1992 (precision: year); kind: award; track: reception
- **source:** NEW `erC_cha_prize_1992`
- **support:** "CHA prize-winner page, read 2026-10-28; collaborators not named on the page."
- **Coverage note:** the basis can add "CHA prize 1992".

### 4b. Existing edges

| Edge | Endpoints (type) | Verdict | Reason |
|---|---|---|---|
| edge_2173 | life_lived_like_a_story → community_engaged_indigenous / `yukon_collaboration` (connection) | **keep** | McClellan p. 206 ("a work of true collaboration between native and non-native") and Gmelch p. 86 ("a valuable model of how collaboration …") rechecked word for word. The 1974 family request (McClellan p. 205) is quoted only in the entry description. |
| edge_2174 | life_lived_like_a_story → oral (connection) | **keep** | Gmelch p. 85 rechecked ("examining the actual way they talked about, remembered, and interpreted their lives"). "Western life-history form" is supported: Gmelch writes "the Western life history/autobiography genre" (p. 85) and "the limitations of the conventional life history or autobiographical form when applied to people outside the Western tradition" (p. 86). |
| edge_2175 | life_lived_like_a_story → anthropology (connection) | **keep** | McClellan p. 206 rechecked: "a sophisticated and ground-breaking contribution to anthropological scholarship and practice"; the book "points to the kind of relationship between native Americans and anthropologists that both groups can increasingly hope for". |
| edge_750 (related) | **oral → ethnohistory**, "Cruikshank and Yukon elders: collaborative life histories" | **reroute** `source` → `life_lived_like_a_story`; set `target_strand` → `ethnohistory/collaboration_authority` | See note 5 below. |

**Note 5 (edge_750).** After packaging, this field-to-field edge rests on the book alone, and edge_2174 now carries the book's link to `oral`.
- **Why `ethnohistory`:** a named reader puts the book there. Carlson, Lutz and Schaepe (2009, p. 2 and n. 4): "Attention to cultural context has been a hallmark of the new ethnohistorical literature, as exemplified by Julie Cruikshank", citing the book with all four names. That is per C's 1.201 note (read 2026-10-27); I could not reread it (Wayback blocked to my tool). Iverson (1993, p. xvi, read) adds a US reading in his survey of American Indian history: "Julie Cruikshank's recent collaboration with three elderly Yukon women has produced an extraordinary tapestry of Native life in Life Lived Like a Story".
- **Operations:**
  - `edge_endpoint_sets` {edge_750, source, expect `oral`, value `life_lived_like_a_story`}
  - {edge_750, target_strand, expect null, value `ethnohistory/collaboration_authority`}
- **New relationship:** "Read as ethnohistory: the Stó:lō field-school editors take Cruikshank's work with the three elders as exemplary of 'the new ethnohistorical literature' (2009); Iverson's survey of American Indian history praises the collaboration (1993)."
- **Add source:** `ihb_iverson_1993`.
- **Alternative**, if the coordinator prefers not to reroute: keep edge_750 as is and add this as a new edge (erC_09).

### 4c. Proposed new edges
None beyond the reroute. Two smaller items:
- **Chronology:** 1993, reception, "Iverson's survey of American Indian history names the collaboration", `ihb_iverson_1993`, p. xvi.
- **Settler colonialism:** none of the readings (McClellan, Gmelch, Iverson, CHA, Carlson et al., Leddy) frames the book this way. No edge.

### 4d. Held
- **The book itself:** no allowed open text.
- **Women's and gender history.** McClellan opens "Anyone who truly wants to understand something about individual native women of the far North should read this" (p. 205). Gmelch reports a conclusion about how outsiders classify Native women's work (p. 86). Neither places the book in a women's-history field. The second is close to community knowledge, so it is held for OCAP review, not drawn.
- **Carlson, Lutz and Schaepe (2009):** to be reread when the Wayback capture is reachable.

---

## 5. Corrections
- **C-1, `emma_larocque` chronology `el_other_2011` and date_label.** Black's review (AICRJ 35:4, 2011, p. 285) gives the imprint as UMP **2010**. The UMP page gives March 2011 for current formats. Proposed:
  - year 2010 for first publication, support "Black 2011 review header; UMP page dates current formats to March 2011";
  - date_label "When the Other Is Me 2010".
- **C-2, `promotion01_smith.citation` and `smith_decolonizing.verification.note`.** Remove the host description of the excluded scan (§2a, note 3).
- **C-3, edge_2166 evidence note.** Its strand rationale (§1a, note 1).
- **C-4, edge_775 evidence note.** Its stale "does not establish particular book arguments" sentence (§3a, note 4).
- **C-5 (CHA attribution).** Any future text on the prize must say the CHA lists Cruikshank alone, so that the award is not presented as a four-way credit the CHA did not make.

## 6. Held, overall (needs a passage nobody could read)
- LaRocque: *When the Other Is Me* (2010) body, to see whether she uses "settler colonial" after 2000.
- LaRocque: "The Colonization of a Native Woman Scholar" (1996).
- LaRocque: "Métis and Feminist" (2007), for `womens` / `cdn_women_gender`.
- LaRocque: her footnote on Stalker and Prentice, eds., *The Illusion of Inclusion* (PDF p. 296 n.). It is a read critique, but its target is a women-in-academia collection, not a women's-history field. Held for a target decision.
- LaRocque: her remark on "new pressure for Native scholars to do 'traditional epistemologies', to validate any and all research through 'elders'" (PDF p. 241). It is read, but it is not a critique of `community_engaged_indigenous` as such. Do not synthesise one.
- Smith: the 1999 introduction, the 2012 and 2021 introductions, the 2019 Smith–Tuck–Yang introduction, and *A Civilising Mission?*.
- McNickle: the 1970/71 essay, Parker (1990, 1992), and the Newberry series 8 page (Regina dates).
- *Life Lived*: the book, and the 2009 Stó:lō text reread.

## 7. Summary (5 lines)
1. LaRocque: 6 own edges kept except edge_2166, which should retarget to `historians_indian`. edge_1003 (to Van Kirk) should now leave from her, not from `indigenous`. Her critiques of settler scholarship land in the right part-1 field after 1.201.
2. LaRocque: 7 new edges from read dissertation pages. They are critiques of postcolonial studies (also in the 2010 book via Black), Sioui's autohistory, Mandelbaum's ethnography and fur-trade historians, plus Fanon and Dickason as resources. Her 1999 "original settlers / re/settlers" reworking of settler vocabulary is offered as a stage-2 `settler_colonialism` link; it is not Wolfe-era engagement.
3. Smith: 3 edges kept. The `promotion01_smith` citation still names an excluded scan host and needs cleaning. No settler-colonialism edge: only the interviewer uses the term (LARB 2021), and the 2019 volume co-edited with Tuck and Yang is unread. Fanon → Smith goes to stage 2.
4. McNickle: edge_775 should be reworded to his read argument plus Iverson's "a book ahead of its time" (p. vi). Add a 1966 Regina anthropology post (AAAS). No new edges and no settler-colonial link.
5. *Life Lived Like a Story* won the CHA Best Scholarly Book in Canadian History Prize in **1992**, listed to "Julia A. Cruikshank" alone (https://cha-shc.ca/prize-winner/julia-a-cruikshank/). Its 3 edges check out word for word. edge_750 should be rerouted to leave from the package into `ethnohistory/collaboration_authority` (Carlson et al. 2009; Iverson 1993 p. xvi).

**Counts.** 20 edges reviewed: 15 touch the four entries and 5 are field-level edges resting on their work.
- 16 kept, 1 revised (edge_775) and 3 rerouted (edge_2166, edge_1003, edge_750).
- 8 new edges proposed: 6 for stage 1 (erC_01 to erC_06) and 2 for stage 2 (erC_07, erC_08).
