# Reviewed subset for revision 1.200

The user resumed the remaining historian reviews, then requested, “we’ll pause
after this and push.” This release closes the 35 whole dossiers already underway
or completed at that pause point. It leaves 101 of the pinned 136-person request
pending. The earlier 21 completed dossiers remain unchanged. Tocqueville remains
excluded by explicit direction.

Each included person has one dossier owner and an independent passage and
coverage review. `publication-selection-1.200.json` fixes the subset; the packet
generator refuses any dossier without a current PASS and exact reviewed hashes.
The mutable progress file is deliberately outside the packet’s input manifest so
that implementation and pause status can be recorded without altering evidence.

The supplement adds relationships between existing endpoints. It preserves every
old node, person, relationship, roster, chronology, life fact and source record.
The only change to an old source is an append-only scoped reading note, with its
previous verification record retained by the generic acceptance receipt. Two
dossiers reread Buckner2000: both notes are concatenated in queue order. No note
replaces an earlier qualification or claims that an unread original was read.
Wood also reread the new source supplied by Richter. That reading note appends
to Richter’s new source record, with both owner dossiers unchanged and the exact
crosswalk recorded as `new_source_reading_addenda` in the merge manifest. It is
not counted as an amendment to a pre-existing graph source.

All approved proposals are retained once with their exact relationship text,
direction, category, source IDs and evidence note. Comparison uniqueness is
checked with unordered endpoints; all other categories retain direction.
For 21 approved critique rows (Wood eight, Ibn Khaldun two, Lears eleven), the
derived packet corrects the redundant legacy `type` from `connection` to
`critique` to match the approved `relationship_kind` and graph schema. The
manifest records each change as `legacy_type_normalizations`; frozen owner
files and all other proposal fields remain unchanged.
Cross-dossier pair/category checks found no duplicate claims. The Richter/Wood,
Charle/Roche, Davis/Faust, Morgan/Berlin, May/Cott and Bederman/Cott/Lears cases
are owned in one dossier and explicitly represented in the others.

New source records with the same ID must be byte-equivalent as parsed JSON.
Only records cited by included relationships enter the graph. Additional records
supporting held cases, reception leads or negative searches remain in the frozen
owner dossiers, with their IDs and owners recorded as excluded uncited sources
in the packet manifest. This filter does not change owner evidence or reviews.

Named mediation, coauthors, translated or reprinted editions, indexed-only
access, discontinuous pages, original-unread and recording-unchecked limits stay
explicit. Missing graph people are held, with no substitute people or fields and
no edge quota. A bounded dossier does not certify a complete intellectual network.

Raw third-party text, PDFs, HTML and images remain ignored locally. Only cited
records, paraphrased research decisions and retrieval metadata are committable.
The public site continues to use its explicit build allowlist. OpenAlex and
dissertation extraction/analysis remain paused; no corpus rerun is part of this
release.

The merge, application, preservation result and browser fixture receive their own
independent reviews. Publication follows those checks, and the remaining work
stays paused until the user resumes it.
