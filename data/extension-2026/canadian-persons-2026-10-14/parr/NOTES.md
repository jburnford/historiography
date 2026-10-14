# Joy Parr: person entry draft (Tier 1 Canadian persons, pe135)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). I applied it in
memory to the live 1.133 graph: the node, `node_id` on `joy_parr`, 19 new sources, 4 addenda,
six edges as `edge_919`–`edge_924`, and three roster `edge_id`s. It passes `validate_graph` with
**0 errors and the same 7 existing warnings** (168 nodes, 924 edges; no dangling source ids;
every `target_strand` exists).

## What is proposed

- **Node `joy_parr`.** The twelve standard person keys.
  - Date label: *Labouring Children 1980 · 'Nature and Hierarchy' 1985 · The Gender of
    Breadwinners 1990 · 'Gender History and Historical Practice' 1995 · Domestic Goods 1999 ·
    Sensing Changes 2010*.
  - Under the open frame the label lists dated works, with no "coverage through" suffix.
- **`people_update`.** The existing record gets `node_id: joy_parr`.
  - `data/people-wikidata.json` has no joy_parr record.
  - candidates.csv already marks Q28064772 as correct.

### Edges

| # | Target | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | cdn_women_gender | contribution | Gender history in practice, 1985–96 | gender_category_debate | yes |
| 2 | cdn_working_class | contribution | The gender of breadwinners, 1990 | gender_family_class | yes |
| 3 | cdn_childhood_youth | contribution | Labouring children, 1980 | family_economy | yes |
| 4 | gender (optional) | contribution | Gender and class compared, 1988–93 | class_family | no |
| 5 | consumption | contribution | Domestic goods, 1999 | gender_consumption | no |
| 6 | environment | contribution | Sensing changes, 2010 | none (note given) | no |

**No critique edge is proposed.** The reason is in "Critique" below and in
`edges_considered_not_proposed`.

## The PhD: confirmed

- **AHA Directory record 45612.** "Parr, Joy", Yale, Dept. of History, 1977, "The Home
  Children: British Juvenile Immigrants to Canada, 1868-1924". Adviser: Robin Winks.
- **Independently confirmed** in two places:
  - Drystek's 1980 Archivaria review (p. 241) names the same thesis as "(Yale, 1977)" and the
    source of the book's Barnardo sample.
  - The Queen's University History notice of 16 May 2024 says "PhD from Yale University in 1977".

## Verification: what was read

### Read in full

**Parr's own words**
- **"Nature and Hierarchy"** (Atlantis 11:1, 1985, pp. 39–44). Pages are assigned by PDF
  order; p. 42 is printed.

**Reviews of *The Gender of Breadwinners***
- **Hosted on joyparr.com as page scans.** I OCR'd them locally and read them against the page
  order.
  - Heron, *CHR* 72 (1991): 218–21. A labour historian; praise and criticism.
  - Dennis, *EcHR* 1991.
  - Bertaux, *JEH* 1992. Her p. 9 quotation was checked on the image.
  - Benson, *JAH* 1993. The page break was checked on the image.
  - Ling, *THES* 1991. Read, but not cited.
- **From the journals' own sites.**
  - Guildford, *Atlantis* 17:1 (1991).
  - Scheinberg, *Archivaria* 32 (1991).

**Other reviews**
- Drystek on *Labouring Children*, *Archivaria* 11.
- Brush on *Domestic Goods*, EH.NET 2000 (MITH archive copy).
- Owram on *Domestic Goods*, *BC Studies* 129, 2001.
- Jackson on *Sensing Changes*, *Senses and Society* 2011 (author's site).
- Rumiel on *Sensing Changes*, *Left History* 2011 (Internet Archive capture).

**The *Left History* exchange.** All four papers were read in full in Internet Archive
captures; the York site is behind a bot check.
- Sangster 1995.
- Dubinsky and Marks 1996.
- Iacovetta and Kealey 1996.
- Sangster 1996.

The atlas's `gender_category_debate` strand says "the replies were not read". They now are, and
four addenda record what they say about Parr. The strand's focus text could be updated at
release; this draft does not edit it.

### Read in part

- **CSSH 1988.** First-page extract and notes 1–3 (Cambridge Core).
- **ILWCH 1999.** Abstract (Cambridge Core).
- **CHR 2026 "great books" forum on *The Gender of Breadwinners*.** Abstract only; used as a
  labelled later reading.

### Not read

None of her books was read: *Labouring Children*, *The Gender of Breadwinners*, *Domestic
Goods*, *Sensing Changes*, *Gender and History in Canada*.
- **Where the books are quoted, they are quoted through reviewers.** The reviewer's page
  reference is kept, and the entry says so.
- **Access attempts that failed:**
  - The De Gruyter chapter PDFs (UTP 1990 introduction; UBC 2010 introduction) sat behind a
    bot wall.
  - The Internet Archive copies are borrow-only, and their search-inside returned "Item not
    available".
  - The Google Books API quota was exhausted.

Other texts not read:
- **"Gender History and Historical Practice" (CHR 1995).** MUSE returned a verification wall.
  Its words come from Iacovetta and Kealey (who cite CHR pp. 362–63 and 365) and from Sangster
  1996 (who cites the 1996 reprint, pp. 11, 14 and 21).
- **"Smells Like?" (*Environmental History* 2006).** Metadata only.
- **Her *Technology and Culture* articles (1997, 2003, 2005).**
- **Reviews:**
  - The *AHR* review by Patricia Roy (1991) is closed.
  - The Bloomfield (*UHR* 1991) and Brac (*RHAF* 2001) reviews sat behind Érudit's bot wall.
  - McGinnis (*Atlantis* 1981) was glanced at only; it is not cited.

## The "1995 CHR exchange"

I found no exchange in the CHR itself. Crossref shows that Parr's essay sits in CHR 76:3 (September
1995) between historiographical essays by Bernard, Akenson, Shore, Waite and Wynn. The exchange
that took the essay up was in *Left History* (1995–96).
- **Iacovetta and Kealey quote it.**
- **Dubinsky and Marks cite it.**
- **Sangster criticises it** (1996):
  - n. 2: Parr groups feminist and anti-feminist critics together.
  - n. 3: Sangster had been reproached for not criticising "Valverde and Joy Parr".
  - pp. 244–46: the tie between gender history and post-structuralism.

## Critique

The brief asks for a critique edge where Parr criticised an atlas entry's position in her own
words. The 1985 essay is the candidate.
- **What she criticises.** Labour historians, women's historians and historians of childhood
  alike "have reified the skill-unskill boundary" (p. 42).
- **Her worked example** of an inadequate Marxist analysis is *Women at Work* (1975), a
  women's-history collection (p. 43). The words "tells us nothing about why women end up at the
  bottom" are themselves quoted from Phillips and Taylor and Hartmann (n. 20).
- **Why no edge.** Because no labour-history work is named, an edge aimed at
  `cdn_working_class` would overstate her target.
- **Where the criticism is recorded.** It is quoted on rel_02 and sits beside `edge_889`, the
  existing entry-level feminist critique.
- **Reviewer's option.** Re-type rel_02 as a critique.

In-period critics **of** Parr are recorded with their own words:
- Heron (1991): "suppressed the impact of class"; the "women's town" portrait "may be slightly
  misleading"; she neglects Canadian literature, the wars and the state.
- Scheinberg (1991): a seven-woman sample.
- Drystek (1980): "almost uniformly negative approach".
- Sangster (1996): post-structuralism and a hierarchy over women's history.
- Owram (2001): consumer sovereignty.

## Founder claims

The draft makes none.
- **1985.** Parr places her own call among "a good many others" (p. 39).
- **Childhood (rel_03).** It notes that Sutherland (1976) precedes her.
- **Women's and gender history (rel_01).** It names Pierson and Scott as part of the Canadian
  gender debate.

## Open questions for the editor

1. **Edge 4 → gender.** It is optional; `edge_840` already links the Canadian field to the
   international entry. Keep it only if international reception (*JAH*, *EcHR*, *JEH*) should
   show on the person.
2. **Strand for edge 1.** The draft uses `gender_category_debate`. The alternative is
   `work_family_state`.
3. **Technology.** This is the strongest unread lead. She won SHOT's Edelstein Prize (*Sensing
   Changes*) and the da Vinci Medal (2018), and wrote "Classics Reconsidered: Ruth Schwartz
   Cowan's *More Work for Mother*" (T&C 2005). Reading the 2005 essay could support an edge to
   `technology/households`, possibly as a critique.
4. **Environment strand.** No strand fits embodied or sensory environmental history; edge 6 has
   `target_strand` null.
5. **No external personal data was sent.** No email, mailto or other identifier went to any
   service. The services used were Crossref, OpenAlex (with the repo key), Open Library,
   id.loc.gov, Internet Archive metadata and Wayback, Cambridge Core public pages, journal OJS
   sites, joyparr.com and web search.
