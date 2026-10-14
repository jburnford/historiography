# Fixes to the 1.134 packet after Sol's review

Sol (`sol-review-1.134.md`) said "accept with fixes". The fix agent stopped at the usage limit
after downloading the witnesses. The coordinating session then applied the fixes itself
(`scratchpad fix134.py`), using the agent's downloaded copies:
- Scott's reply, read in full;
- the first pages of Stansell and Rabinbach;
- Bercuson's article, read in full;
- Palmer's 2009 essay, the print PDF;
- the three *Dissenting Traditions* chapters.

1. **Scott's definition of discourse.** The edge to Scott and the node description now quote
   Scott's own definition (ILWCH 32, p. 40). It includes "ways of organizing lives, institutions,
   societies", and she denies that "words" alone brought families into being. The
   reduction-to-discourse objection is labelled as Palmer's reading. The description adds his
   qualification, as quoted by McCoy (2021): "to say that language matters is not to say it is
   all that matters".
2. **The four-person forum.** Two new scoped sources cover the first pages actually read:
   - `pe134_palmer_stansell_1987` (p. 24): she welcomes Scott's essay and calls the neglect of
     poststructuralism "our missed opportunity";
   - `pe134_palmer_rabinbach_1987` (p. 30): he restates Scott's critique of Stedman Jones.

   Scott's separate answers to the two (pp. 42 and 44) are noted. The label is now "Answering
   Scott, 1987–90". The relationship calls *Descent into Discourse* Palmer's "subsequent
   book-length intervention", with no reciprocal exchange implied.
3. **Bercuson's substance.** Pp. 107–108 were read and quoted:
   - the demand to "prove" a common culture before using it to explain;
   - "job, place, church, ethnic group";
   - gender versus class;
   - "Even if Thompson is right about England…".

   The `wcreq_bercuson_1981` addendum is extended. "Kealey's reply" became "Kealey's companion
   defence".
4. **The liberal-order label.** It is now "Palmer: liberal order sidesteps capitalism, 2009",
   with print-PDF locators: pp. 3–4 and 4–5, the qualification on p. 4, and "undeniable
   achievement" on p. 31. McKay's counter-position is added through Fecteau's quotation of p. 385
   (`lof_mckay_2009`). It is dated the same year and is not described as a reply.
5. **Provenance.**
   - "Not that of a defensive empiricism but of a critical, anti-Stalinist Marxism" is marked as
     Callinicos's prose.
   - The "toward[s]" composite is replaced: the edge quotes Pearson's wording ("toward") and notes
     that Rogers paraphrases it as "towards".
   - The contribution label now stops at 1979, because the 1982 Knights of Labor book rests only
     on McCoy's later quotation; the evidence note says so.
6. **Callinicos.** He "suggested that his treatment of class might underestimate" objective
   determinants. This replaces "thought he underestimated".
7. **Rosters (recommended).**
   - `scripts/apply_person_entries.py` now accepts a `roster_row` dict `{node, person_id}`, so
     the Thompson extra links `karl`/`ep_thompson` to its edge.
   - Palmer is added to the `language` roster as a critic, linked to the Descent into Discourse
     edge.
   - The Thompson edge keeps no `target_strand`.

Not done:
- Sol's suggestion to add *The Poverty of Theory*, section i, to the Thompson edge. The agent
  downloaded it, but it was not re-read here.
- Valverde's 1988 and 1995 criticisms of Palmer, which the Valverde drafter flagged. They go to
  the Canadian batch.
