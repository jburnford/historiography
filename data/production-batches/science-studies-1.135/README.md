# Revision 1.135: science studies gains its critiques; the Science Wars

The user (2026-10-14): "start on the science studies project". Two decisions frame it:
- Haraway and Latour are "broadly aligned", so Haraway is not drawn as a critic of Latour.
- The user said "yes" to a Debate entry.

An outside review had found no critique edges on kuhn, latour, ssk, sts or science. The drafts
are in `data/extension-2026/science-studies-critique-2026-10-14/batch/`. The evidence files are
alongside them: `evidence-kuhn-critics.md`, `evidence-ssk-latour.md`, `evidence-science-wars.md`.

**New entry: *The Science Wars, 1994–2000*** (`sciencewars`). It is a Debate in
historiographical developments, `period_3`, reviewed through 2000, with 23 roster rows (17 new
people). Its edges:
- critiques of SSK, Latour, constructionist science studies (selected positions, not a
  field-wide indictment) and the "immoderate" Kuhn;
- replies from SSK, Latour and historians of science;
- *Telling the Truth about History* against the strong programme and Latour;
- a comparison with the truth debate.

**Further critiques:**
- the 1965–70 critics of Kuhn (science → kuhn);
- Latour against the strong programme (1992–99);
- Bloor's "Anti-Latour" (1999);
- Kuhn against the strong programme (1991);
- Trentmann against actor-network theory's view of modernity (2009, dated).

`edge_138` is trimmed to a comparison of method.

**Review.** Sol (`release/sol-review-1.136.md`, written when the batch was numbered 1.136) said
"accept with fixes". It made ten findings, all applied by the coordinating session (script
`fix_ss.py`, in the session scratchpad):
1. The historians' reply targets the debate, not their own strand.
2. The strong programme / *Golem* edge has no strand, and the two targets are distinguished in
   its evidence note.
3. The linguistic-turn edge is deferred (`include: false`).
4. The STS edge is narrowed to "selected constructionist and relativist positions".
5. Roles follow the `who_killed_debate` pattern: attackers are contributors and respondents are
   critics.
6. The Sokal–Bricmont page locators are tied to the consulted Profile printing, and Shapin's dash
   is restored.
7. Latour's *Le Monde* article (18 January 1997) is known only through Jardine and Frasca-Spada's
   translation. Le Monde's archive blocked automated reading. Their "Apology" (*SHPS* 28:4,
   1997) is registered as unread, with its content unknown, and the reply edge does not depend
   on it.
8. "Predates" is replaced by "published in 1994, before the 1996 hoax".
9. `edge_138` is trimmed for an editorial reason, not because of a limit of the applier.
10. The rationale distinguishes primary passages, mediated quotations, abstracts and dated
    later work; Croissant's "most widely read" is removed. The batch was rebased from 1.136 onto
    1.134 and ships as 1.135.

**Evidence layer.**
- Practice series v21, with landing audit `audits/landing-1.135`, folds `sciencewars` into the
  history of science.
- Its family is *Science, technology & medicine*, bridged to *Theory & method*.
- Family shares are unchanged.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/science-studies-critique-2026-10-14/batch --check`
  is exact, and the 1.134 check still passes.
- 0 errors, with the 7 baseline warnings.
- Totals: 169 entries (96 groups, 73 person entries), 939 relationships, 1,609 sources and
  1,212 shared people.
