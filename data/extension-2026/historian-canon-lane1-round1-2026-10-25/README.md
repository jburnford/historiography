# Lane 1, round 1: historian biographies — candidate 1.171

Frozen review packet for baseline 1.170. Ten historian entries, twenty scoped relations, thirty-four dated publication/translation facts, nineteen new source records, four new people and ten additive group roster contexts. No canonical application or browser build was run.

`batch.json` and each person's `entry-draft.json` follow `scripts/apply_person_entries.py`. `release/editorial-additions.json` is the concrete reviewable release; `validation.json` records an in-memory transform with no errors and the eleven existing baseline warnings. Original edges and sources remain byte-equivalent as objects, and existing descriptions, strands, chronologies, coverage and date labels remain unchanged.

Every person folder contains `research-notes.json` and a separate standardized `life-status.json`. Sources retain passage/metadata scopes. Existing qualified readings are copied into the research notes without asserting a fresh full reading. Life evidence is separate from selected-work chronology. Queue counts retain their exact keys and dated first-author scope; this packet does not recompute or combine them.

Review boundaries needing particular attention:

- Ariès: the childhood concept is not absence of parental affection. Death is retained at year precision because the archival authority and contemporary obituary disagree over February 8/9, 1984.
- Bederman: direct CUNY PDF retrieval failed. Only the indexed primary passage around printed pp. 42–43 was consulted, supplemented by Anne-Marie Harvey's expressly named substantive discussion at pp. 42–43. Neither early article nor the whole monograph is claimed read. Birth year remains unestablished.
- Colley: original Marsh subtitle and the paperback variant remain distinct. Her interview's conversation about method supports the interpretation, not a full monograph reading.
- Le Goff: Thompson's primary p. 56 and n. 2 support a specific acknowledged resource, not a wholesale genealogy. The EPHE notice's conflicting dates for Les Intellectuels are excluded.
- Prost: Philippe Billois retains collaborator credit in the three-volume 1977 study; it is distinct from the shorter Gallimard book. Arguments are mediated by Agulhon and Voldman. The recent life witness is a signed 2025 tribune, not an interview.
- Sangster: the original 1995/96 interventions, their existing date qualifications and the later retrospective are kept separate; the 1992 joint reply to Bliss is not reassigned to the 1998 Granatstein controversy.

Primary downloads/extractions, when accessible, are ignored under `research/.gitignore`. Retained notes record locators, limitations and hashes. `prepare-packet.py` writes only the owned research packet. The coordinator owns application, chronology integration and the reading bridge.

A subsequent direct primary reading is documented in `bederman-reading-addendum.json`; it is reserved for an additive source note in round 2, without rewriting this applied release.
