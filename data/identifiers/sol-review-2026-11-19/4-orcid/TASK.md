# Task 4 — ORCID questions on person keys
Read data/identifiers/crossref-identity-2026-11-17/README.md first. Three queues, in this order
(queue.csv with a column for the class):
(h) held.json: 34 held ORCID attaches and 140 held merges, each with a reason;
(b) orcid-evidence.csv.gz rows flagged as class (b): the key's existing ORCID anchor differs from
    the ORCID printed on its works (336 keys);
(c) orcid-two-keys.csv.gz pairs not already decided in (h).
For each case read both ORCID records (public pages on orcid.org: names, other names,
employment, works) and the works involved, and give a verdict:
same-person-two-iDs / deposit-error (publisher put the wrong iD on the work; say which work) /
wrong-anchor-on-key (the key's own anchor belongs to someone else) / co-authors-not-same /
placeholder-iD / same-person-two-keys (merge candidate: needs a shared work or identifier, state it) /
unclear. Add fields: keys, orcids, names_on_records, deciding_fact.
Known trap: ORCID 0000-0002-1825-0097 is ORCID's documentation example iD, deposited as a
placeholder by some publishers: never evidence of identity.
