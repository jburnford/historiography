# Task 7 — doctoral theses held out of the History corpus: read each one's public record
User rulings (2026-11-16/17): history PhDs only; economic history, history of science, history
of education and ancient history count as History; archaeology does not; plain economics does
not; NOT yet ruled: church history / history of religions, art history, philology/text
editions, theses from other subjects carrying a History code. Rule code: scripts/ancient_ruling.py;
registers and holds: data/field-research/dnb-germany-harvest-2026-11-14/ (screen and
screen-overrides files), data/field-research/france-theses-resurvey-2026-11-15/,
the Sweden DiVA/SwePub harvest folder under data/field-research/, the Canadian and UK
eligibility-overrides files, and data/field-research/dissertation-citations-2026-10-11/README.md
(sections on holds; do NOT read entries.jsonl, graph.json, graph.graphml or any thesis text/PDF).
Build queue.csv of every held thesis with its hold ground (Germany ~141 with a PDF: archaeology
112, philology 12, religion 17; France ~97; Sweden ~25; Edinburgh ~27; Canada: Toronto 32
philosophy-of-science, UVic 9 art history, 12 classics; plus held-without-PDF lists if listed).
For each, open its public catalogue/repository record (DNB, theses.fr, DiVA, the university
repository) and read title, abstract, department/discipline, supervisor's field. Verdict:
history (should be released under the rulings: say which ruling) / archaeology /
philology-or-text-edition / religion-or-church-history / art-history / economics /
philosophy / other-field / unclear. Add fields: thesis id, source, title, year, university,
department, abstract_summary (one sentence, your words), ground_now, agrees_with_hold (yes/no),
borderline (yes/no + why). Do not fetch PDFs; never go past a login or embargo.
