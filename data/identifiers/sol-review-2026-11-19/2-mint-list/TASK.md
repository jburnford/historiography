# Task 2 — read the mint candidates
data/identifiers/place-demo-fixes-2026-11-18/mint-place-authors.proposal.json.gz proposes minting
6,653 people (LC authority + cited by 2 or more theses) with their works; nobody has read them.
Read that folder's README.md first. Queue = the proposed people, ordered by number of authored
claims descending (queue.csv). Skip anyone already given a verdict in ../1-place-authors/verdicts.jsonl
(reuse it: append a line citing that verdict). Same classes and fields as Task 1
(scholar / official-or-participant / literary / corporate-or-not-a-person / journalist-or-popular /
unclear, identifiers with URLs, life years, existing_key). Add: mint_recommendation
(yes / no / hold) under the user's rule that the people index is for scholars; primary-source
authors and literary authors are "no" (they stay as catalogued names), and "hold" when a person
key that may be the same person already exists.
