# Identifier plan: internal keys, library and Wikidata identifiers, and a path to LOD

**v2, 2026-10-30.**

**Status:**
- The key store, minter and carry-forward are built and tested (`scripts/identifiers.py`, 12 tests).
  The atlas proposal builder (`scripts/key_atlas.py`) has run as a dry run: 12,013 keys, and a
  re-run is a no-op. See [data/identifiers/README.md](data/identifiers/README.md).
- **Atlas keys minted (12,013), from commit a048719,** in `data/identifiers/events.jsonl`. Uncommitted.
  Atlas items are curated and published, so open decisions A and B do not affect them.
- **Canon map keyed** (rollout step 3), under decision A = one series with a status:
  - 2,633 new person keys, and 427 people joined to atlas keys;
  - 208 deferred to a merge-review queue;
  - `docs/data/dissertations/canon-map.json` now carries `key` / `key_status`. Uncommitted, not pushed.
- The LC pilot is running.

v1, written earlier the same day, proposed minting our own resolvable PIDs.
It was reviewed by Fable ("sound with changes") and then redirected by the user. The decisions below
replace v1.

The goal is one historiographical knowledge graph, with a pathway to linked open data. LOD
publication and CIDOC-CRM modelling come later. Identifiers are designed now so that nothing built
from here on has to be renumbered. [IDENTITY-PLAN.md](IDENTITY-PLAN.md) decides *which* records are
the same entity. This plan decides *what the result is called, and for how long*.

## 1. Decisions (user, 2026-10-30)

1. **No resolver of our own.** We do not mint public PIDs or run an ARK/w3id service. Public
   identifiers come from existing linked-data authorities:
   - the **Library of Congress** now;
   - **Wikidata**, built out later.
2. **Library of Congress first.** "Most important historians have a book." A person with an LC name
   authority uses it as their public identifier. LC publishes:
   - the authority record: `http://id.loc.gov/authorities/names/n87908321`;
   - a real-world-object URI for the person: `http://id.loc.gov/rwo/agents/n87908321`. This is the
     right target for a future `sameAs`.

   Both dereference to RDF.
3. **Wikidata later.** Contribute items and identifiers once the LC layer is in place. The cheapest
   first step is adding LC identifiers to existing items that lack them.
4. **Works.** One key per work. Editions and translations are recorded as metadata on the work
   wherever we have them.
5. **Edges.** Every edge gets a key.
6. **Splits.** The old key is retired and its successors are listed. It is never handed to one side.
7. **Unresolved entities** get internal keys. The user proposed `ur-1`, `ur-2`, …; see open
   decision A.

## 2. Three layers of identifier

| Layer | What it names | Who issues it | Example |
| --- | --- | --- | --- |
| **Occurrence ID** | One record in one source: an H-Net credit, a Crossref contributor, a bibliography line, an AHA record | Derived from the source; already exists | `hnet:mention:…`, `crossref:<doi>:author:2`, `aha:dissertation:…` |
| **Internal key** | An entity the project asserts or publishes: person, work, journal, institution, atlas entry, edge, timeline event | Us; stable, never reused; published in DOI'd dataset releases, not resolvable on its own | `p-1042`, `w-88130`, `c-2657` |
| **External identifier** | The same entity in an authority | LC, national libraries, Wikidata, ORCID, ROR, ISSN, DOI, ISBN | `lcnaf:n87908321`, `wd:Q…`, `orcid:…` |

**Internal keys stay primary even when an external identifier exists.**
- QIDs get merged and deleted. LC authority records get deprecated and replaced.
- Several things will never have an external identifier: edges, editorial entries, and most of the
  unresolved long tail.

External identifiers are attached with a status and a **match strength**:
- `exact`: an identifier chain, or a reviewed decision;
- `close`: a probable route, such as Open Library → QID at about 97.5% precision;
- `evidence_only`: related, but not the same entity.

Only `exact` will ever be exported as `sameAs`.

### Public identifier preference for people

1. **LC name authority**, read through the person's own catalogued book (section 6). For non-English
   authors: GND, BnF or IdRef (all LOD).
2. **Wikidata QID**, where it exists. LC authority records often carry the QID, ISNI and ORCID in
   field 024, which links the two for free.
3. **ORCID**, for historians whose work is mainly articles.
4. **Internal key only**, with its evidence chain. This applies to historians with no book, no ORCID
   and no QID. It is a legitimate final state and never blocks inclusion.

**Library authority caveats**
- LC records marked *undifferentiated* (008/32 = `b`) can cover several namesakes. They are never
  used as identifiers.
- VIAF clusters merge and split, so VIAF is a link, not a key.

## 3. Entity types and scope

| Type | Key | Scope and notes |
| --- | --- | --- |
| Person | `p-N` | Atlas roster people, established registry individuals, published cited people, dissertation authors and supervisors, positions-table people. |
| Work | `w-N` | Books, articles, chapters and reviews, at **work level**. Editions and translations are recorded in the work's metadata (ISBN, LCCN, OCLC, DOI, JSTOR id, language, year). **Dissertations are works** (kind `doctoral_thesis`), so a thesis cited in a bibliography is not a second entity. A review is a work with a `reviews` link to the reviewed work; the H-Net or RiH record is its occurrence. Atlas sources that cite a work point to that work's key. |
| Journal | `j-N` | **Title level**, matching the catalogue's existing 1,778 title nodes. Their opaque hash ids become aliases. Lineages are `title_relationships` between journals, not entities. ISSN and JSTOR codes are external identifiers. |
| Institution | `i-N` | ROR as the external identifier, QID where ROR has none. Replaces `I:` slugs. |
| Atlas entry | `e-N` | Entries are editorial documents. A person entry (266 share a slug with a roster person) is an entry **about** that person (`e-… is_about p-…`), not a second person. |
| Claim / edge | `c-N` | Every atlas edge (2,657, with `edge_NNN` as aliases), every `claim_catalogue` claim (143), journal venue edges, and later the citation and review links we publish. |
| Timeline event | `t-N` | The 2,289 chronology events. |

**Not entities:**
- **Position rows** are evidence. Their person column takes a `p-` key.
- **Occurrences** keep their source IDs.
- **`strand_redirects`** and slugs become aliases.

**Changing type.** A key never changes type. If something was typed wrongly, the old key is retired
with `replaced_by` pointing to a new key of the right type.

## 4. Key format and minting

- **Format.** `<type>-<integer>`, lowercase, no padding, never reused.
- **Readable labels.** Editorial slugs (`geertz`, `adam_smith`, `edge_001`) stay valid as aliases, so
  existing site links keep working.
- **One minter.** A single script, holding a lock file, assigns numbers. Agents and builds never
  mint directly. They write proposal files, which the minter applies in order.
- **The record is an append-only event log** (`data/identifiers/events.jsonl`), tracked in Git. One
  line per event:

  ```json
  {"event": "mint", "key": "p-1042", "type": "person", "label": "…", "members": [...], "basis": "…", "commit": "…", "date": "…"}
  ```

  Event types are `mint`, `attach`, `detach`, `merge`, `split`, `retype`, `withdraw`, `relabel`,
  `status`. Appends merge cleanly in Git, which a sorted CSV does not. A DuckDB table, the current
  state, is derived from the log on every build.
- **Statuses.**

  | Status | Meaning |
  | --- | --- |
  | `active` | In use. |
  | `provisional` | Assigned by a build, awaiting a held decision. |
  | `merged` | Retired; `replaced_by` names the surviving key. |
  | `split` | Retired; successors are listed. |
  | `withdrawn` | An error; the record stays. |
  | `unsupported` | No remaining evidence; reported, not deleted. |

## 5. Carrying keys forward between builds

v1 matched on any shared occurrence. Fable showed this would hold almost every build: the registry's
probable links changed by about 280 between v10 and v12. v2 works as follows:

1. **Match on anchors only.** Anchors are atlas IDs, ORCID, QID (after resolving redirects), LC
   authority (after following deprecations), AHA id and reviewed pilot IDs. Occurrences are members,
   not matching keys.
2. **Before matching,** resolve Wikidata redirects and LC deprecated → replacement records. Log both
   as events.
3. **Deterministic anchor merges apply automatically**, logged with `decided_by: rule`. Example: an
   ORCID and a QID joined through Wikidata's ORCID statement.
4. **Hold only contradictions at the accepted tier.** The held entity keeps its previous keys with
   status `provisional`, and the case goes to a review queue.
5. **The build never fails** on a hold.

**Tests.**
- Two builds from identical inputs assign identical keys.
- Adding a member that sorts first changes no key. This fails today: the registry's `individual_id` is
  the lexicographic minimum member, so a new `ol:` author joining an `orcid:` cluster renames the
  individual.

## 6. The Library of Congress route

The route was tested end to end on 2026-10-30:
1. A book's **LCCN** (26,609 H-Net/RiH books have one).
2. → The LC catalogue record, via LC's SRU service (MARCXML).
3. → The personal-name headings, from fields 100/700 (e.g. `Bentzien, Hans, 1927-`).
4. → The **id.loc.gov label service**, which turns the heading into its authority URI.
5. → The authority record itself: the undifferentiated flag, 024 identifiers (ISNI, ORCID,
   sometimes QID) and 670 sources.

The 670 sources often cite the author's first book or dissertation.

**Rules.**
- A credit is tied to a heading only inside its own book, through the registry's name gate. A name
  never matches on its own.
- Ambiguous cases are left unresolved: two compatible headings on one record, or an undifferentiated
  authority.

**Pilot.** `scripts/lc_authority_pilot.py` → `data/field-research/lc-authority-pilot-2026-10-30/`,
running on 2026-10-30. It covers 500 books: 250 whose authors the registry already links to an LCNAF
through Wikidata, and 250 others. The first group measures **precision against an independent route**.
The second measures **what is new**. Outcomes:

| Outcome | Meaning |
| --- | --- |
| `agrees_with_registry` | Same LCNAF as the registry already reaches through Wikidata. |
| `conflicts_with_registry` | A different LCNAF from the registry's. |
| `qid_lacks_lcnaf` | Wikidata contribution candidate: add the identifier. |
| `new_for_known_individual` | New LCNAF for a person the registry already knows. |
| `new_for_unresolved_credit` | New LCNAF for a credit with no registry identity yet. |
| no record, unresolved heading, ambiguous, undifferentiated | No identifier from this route. |

**Pilot result:** 489 of 500 books found. Where the registry already had an LCNAF, the route agreed
247 of 247 times; both registry conflicts were registry errors. 94% coverage in the non-gold half.
See [the pilot README](data/field-research/lc-authority-pilot-2026-10-30/README.md).

**Dates.** The route also yields **life dates**. Headings carry them (`Clifford, Jim, 1980-`), and
many authority records hold structured dates in field 046. Harvest both with their source and
precision. They fill birth years for people who have no QID.

If precision holds, the route joins the registry as an `anchored` route in v13. ISBN-only books
(about 11,500 without an LCCN) can use the same SRU service by ISBN.

## 7. Wikidata (later)

- Contribute **bibliographic facts only**, each with an LC or catalogue reference:
  - name;
  - human, historian;
  - heading dates;
  - LC, ISNI and VIAF identifiers;
  - a book or two.
- **Do not contribute:**
  - identity statements (ethnicity, nation), per OCAP practice;
  - facts from non-public sources (RHS lists);
  - interpretive edges;
  - editorial entries.
- First, add LC identifiers to existing items that lack them (`qid_lacks_lcnaf`). After that, create
  items for well-documented book authors.
- Batches of a few hundred are ordinary editing. Larger runs go through a Wikidata proposal or bot
  request first.

## 8. Rollout

1. **Now:** rules for new code (section 9) and the LC pilot.
2. **Identifier store and minter.** Key the atlas first:
   - 368 entries, 1,438 people, 2,657 edges, 3,400 sources (as works);
   - `claim_catalogue`, the chronology events, and `strand_redirects` as aliases.

   This set is small, curated and already public.
3. **Canon map.** Replace the `P:` name keys in `docs/data/dissertations/canon-map.json`:
   - 3,268 people, 2,213 with QIDs, 1,055 with no external identifier;
   - the map is public now and is the clearest current breach of the rules.
4. **Registry v13.** In order:
   1. Stabilise the probable routes and handle redirects.
   2. Add the LC route if the pilot passes.
   3. Key individuals through section 5, seeded from the atlas person keys.
   4. Add the stability tests.
5. **Journals** (title level) and **institutions** (ROR).
6. **Dissertations as works.** Every harvest route's identifier becomes a member. Authors and
   supervisors are keyed through the registry (AHA ids, ORCID, LC). The 11,014 AHA-minted pilot
   individuals enter here.
7. **Works** with identifiers (DOI, ISBN, LCCN, OCLC, JSTOR). LC's BIBFRAME work URIs
   (`id.loc.gov/resources/works/…`) are candidate external identifiers for books.
8. **Later:** Wikidata contribution, then the LOD export. Internal keys get a URI base at export
   time, with tombstones for retired keys: `merged` → redirect; `split` and `withdrawn` → gone, with
   successors listed.

## 9. Rules for new code, starting now

- Keep every source occurrence ID stable and source-derived. Never use row numbers or file order.
- Do not publish name keys (`P:surname|given`, `W:…`) or union-find roots as identifiers in new
  public assets.
- Record merges and splits as decisions with a basis. Never overwrite.
- Store external identifiers in their own columns, with status, match strength and evidence. Never
  use them as the key.
- Never reuse an atlas slug, `edge_NNN` or any key for a different thing.
- Never write Indigenous identity data into any identifier record or external contribution.

## 10. Open decisions

**A. DECIDED 2026-10-30: one series, with `unresolved` as a status.** The original question
follows.

**A. One key series with a status, or an `ur-` prefix for unresolved entities?**
- *Recommended (with Fable): one series.* An unresolved person is `p-N` with status `unresolved`.
  When resolved, only the status and the attached identifiers change; the key does not.
- *With `ur-N`:* every resolution retires the `ur` key into a new one. Any dataset release that
  cited the `ur` key then needs the alias table to follow it.

**B. Which unresolved entities get keys?**
- *Recommended: everything we publish or review.* That means canon-map people, rosters, positions,
  and review queues.
- The 1.27M cited-person and 2M cited-work name keys stay build-local until they are published or
  resolved. Those clusters regroup on every rebuild, and keying them all would import that churn.
