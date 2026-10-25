# Revision 1.191 — named-person relationship endpoints

Accepted on 2026-10-25 from baseline 1.190. The [acceptance record](acceptance.json)
pins baseline, frozen packet and resulting canonical hashes, and retains complete
prior edge and touched node records.

The packet corrects **74 legacy relationship endpoints** and clears **two obsolete
roster edge pointers**. No node, edge, source, person, chronology event or life
record is added. Resulting graph: **357 entries, 1,595 relationships, 2,951 sources
and 1,426 indexed people**. The 42 biographies still contribute 89 new relationships;
all 42 are connected. The earlier 1.190 `edge_1498` correction is preserved, making
75 rerouted older edges across the two repair packets.

The [independent network review](../../field-research/remaining-canon-2026-10-25/network-review.json)
identifies specific people already named by inherited claims. Edge IDs, claims,
citations, direction, classification and substantive reading qualifications remain
exact; genuinely collective and mixed claims stay on their fields. The only
dependent edge metadata edits clear `edge_1155`’s obsolete group-specific
`target_strand` with null and remove only `edge_1291`’s obsolete contextual-routing
clause. Ginzburg’s comparison remains undirected, without a Freud-to-Ginzburg
transmission assertion, and the Morelli connection remains unchecked.

The Durkheimian sociology roster’s Latour row and the Practice roster’s Philip
Huang row clear only their old `edge_id` strings through guarded string revisions.
Every other row field, including prose, roles, works and citations, remains exact.
Every other pre-existing edge, node field, chronology, source, person record and
coverage qualification remains unchanged. No engine change or new reading is
claimed. Earlier accepted packet bytes stay frozen.

The in-memory validation has **zero errors**. Warnings increase **11 → 25**:
14 additional repeated endpoint/type warnings expose distinct retained records
now sharing personal endpoints. Astra independently reproduced the full transform
and accepted these warnings under the no-merge/preserve-ID rule. No new
unconnected-node warning appears. See the [frozen validation](../../extension-2026/remaining-network-2026-10-25/validation.json),
[full prior-record provenance](../../extension-2026/remaining-network-2026-10-25/correction/approved-revisions.json)
and [repair README](../../extension-2026/remaining-network-2026-10-25/README.md).

Astra approves the exact packet. Canonical acceptance, rebuilt life reviews and
the 52-file build are complete locally. Post-repair QA passes 54 targeted data
cases, 63 browser cases and 61 JavaScript checks. A clean checkout reproduces
all public files and life masters and passes 28 focused cases. Ready for
authorized publication; deployment is checked after push.

Packet SHA256: `82698080150be7785dd6e86c26b98fe42edbb883a45027f3c19dd407c7b78375`.
Canonical SHA256 after acceptance: `07cb6bc74d8a46f1006c432b1cb404ccd43d909db23c90127aa3056585e353ce`.
