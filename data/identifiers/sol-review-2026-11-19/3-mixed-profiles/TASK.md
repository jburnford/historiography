# Task 3 — person keys carrying another person's works via a mixed OpenAlex author profile
Model case: p-3125 (Kenneth Morgan, economic historian): data/identifiers/place-demo-fixes-2026-11-18/
p-3125-morgan-profile-credits.csv and that folder's README.md explain the class (one OpenAlex
author profile under his ORCID also holds a geneticist's papers, Kenneth O. Morgan's books and
unrelated items) and how 134 keys with the same pattern were found; rebuild that list of keys
(queue.csv; if the README does not give the list, derive it the way it describes and say how).
For each key: list its credited works from build/graph/explorer.duckdb (e_authored_f joined to
nodes) with the source of each credit where visible, establish who the person is from
identifiers (ORCID record, LC authority, university page), and class every credited work:
theirs / not-theirs (say whose, if known) / unclear. Verdict per key: clean / mixed (n works not
theirs) / two-people-one-key (the key log itself, not just the credits, mixes people) / unclear.
Add fields: works (list of {work, title, year, class, why}), other_person (name + identifiers).
