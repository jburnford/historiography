# E. P. Thompson against economistic Marxism: extra edge for 1.134

Prepared 2026-10-14. **Proposal for review only.** No atlas file was edited; nothing was
committed. The draft is in [entry-draft.json](entry-draft.json) (an extras draft: no `node`).

User, 2026-10-14: the questions-of-class pathway "should start with Thompson's turn against
vulgar marxism".

## What is proposed

- **One edge**, `pe134_thompson_rel_01`: `ep_thompson → karl` (historical materialism),
  critique, map label *Against economistic Marxism, 1957–78*. `target_strand` null (no karl
  strand maps the criticised position; `situated_histories` is the fallback), `roster_row` `{node: karl, person_id: ep_thompson}` (fix 7, after the applier gained explicit person ids).
- **One new source:** `pe134_thompson_socialist_humanism_1957` ("Socialist Humanism: An Epistle
  to the Philistines", *The New Reasoner* 1, 1957, pp. 105–143).
- **Two addenda:** `thompson_making_preface`, `ep_thompson_poverty`.
- Also cites, from the Palmer draft of the same batch, `pe134_palmer_callinicos_1992` and
  `pe134_palmer_rogers_2021` (later reading), and the existing `pl129_palmer_1993_homage`.

## Existing edges checked first

There is no `ep_thompson ↔ karl` edge. Related edges stay as they are:
`edge_309` ep_thompson → marx (contribution: class as a historical relationship, same preface);
`edge_310` ep_thompson → althusser and `edge_027` marx → althusser (the *Poverty of Theory*
polemic, not duplicated). Thompson holds a karl roster row (historian) with no `edge_id`.

## What was read

| Source | Check | What it supports |
| --- | --- | --- |
| `pe134_thompson_socialist_humanism_1957` (new) | Read in full, Marxists Internet Archive transcription (no page breaks) | "This economic automatism certainly is not Marxism"; base and superstructure "a metaphor", "a bad and dangerous model" used by Stalin "as a mechanical model"; Marx's "clumsy static model"; Lenin's "mechanistic fallacies"; the revolt "will, if successful, confirm" the founders' confidence |
| `thompson_making_preface` (addendum) | Re-read in full, University of Texas transcription | Class "a relationship and not a thing"; the "error vitiates much latter-day 'Marxist' writing"; the same error on "the other side of the ideological divide" (Smelser, Dahrendorf) |
| `ep_thompson_poverty` (addendum) | Sections vii and x re-read | Stalinism's "caricature of Marxism" with a superstructure "reduced to confirming or legitimating a base"; basis and superstructure "a static and damaging" analogy; "deeply indebted ... to Marx's own practice" |
| `pl129_palmer_1993_homage` | Part I p. 68, Part II p. 17 | In-period reading (1993–94); Thompson quoted on "abbreviated economistic notations of Marxism" (interviews, not read) |

## Wording choices

- **Within Marxism, not against historical materialism.** The 1957 essay frames the revolt as
  confirming "the revolutionary confidence of the founders", and *Poverty* calls historical
  materialism "perhaps the strongest discipline deriving from the Marxist tradition". The edge
  says so in its relationship text.
- **Marx is not exempted.** Thompson blames Stalin chiefly but also Marx's "clumsy static model"
  and "ambiguities in the thought of Marx", and Lenin's "mechanistic fallacies". The label
  keeps Marx's model in, so the arrow is not read as "the true Marx against his vulgarisers".
- **"Vulgar".** The user's word. Thompson's own terms are "economic automatism", "mechanical
  model" and, in an interview Palmer quotes, "abbreviated economistic notations of Marxism". The
  edge uses "economistic", which is close to his wording; "vulgar" appears in the 1957 essay only
  as "vulgarisation": Western Marxists "shrugged this off as the vulgarisation of a few hacks",
  but "this is not only a question of the vulgarisation of ideas".
- **The "rescue" passage is not used.** The brief suggested "I am seeking to rescue ...", but in
  the preface it answers Fabian, empirical-economic-history and "Pilgrim's Progress" orthodoxies,
  not Marxism.
- **The preface's double target.** Its "class is a thing" critique hits latter-day Marxists and
  structural-functionalist sociology alike; the evidence note says so.
- **Contested inside Marxism.** Callinicos (1992) reports that Palmer took Thompson and Williams
  "to task for abandoning the metaphor of base and superstructure". This is the hinge to the
  Palmer edges on the pathway.

## Applier note

Resolved in 1.134 (fix 7): the applier now accepts `roster_row: {node, person_id}`, so the karl/ep_thompson
roster row carries this edge.

## Validation

Validated together with the Palmer draft against the live 1.133 graph: 0 errors, the same 7
warnings as the unmodified graph; this edge becomes `edge_924`.

## Open questions

1. Strand: null, or `karl/situated_histories` (where Thompson's alternative sits)?
2. Print pagination: the 1957 essay and the preface were read in transcriptions without page
   breaks. A print check would add page numbers.

No personal identifier was sent to any service.
