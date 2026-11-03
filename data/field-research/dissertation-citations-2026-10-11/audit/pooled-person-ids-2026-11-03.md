# Corpus person ids that may pool namesakes (2026-11-03, for the corpus build)

From the key-log session, after the user looked at Ian Milligan (p-592) and asked about the id `milligan|gerry`.

`milligan|gerry` (displayed "Milligan, Ian", cited by 52 theses) holds Ian Milligan's works (*Rebel Youth*, *The
Historian's Macroscope*, *History in the Age of Abundance?*) and Gerry Milligan's (Italian Renaissance literature:
"The Politics of Effeminacy in *Il Cortegiano*" 2006, *The Poetics of Masculinity in Early Modern Italy and Spain*
2010 with Jane Tylus, *Moral Combat* 2018). The works' author strings already read "Milligan, Ian", so the merge
happens in author-name resolution, before ids are formed.

`pooled-person-ids-2026-11-03.csv`: every person id cited by 5+ theses whose given name's initial disagrees with
the displayed name's (704 of 78,850). `triage`:
- `middle_name` (565): the id's given name is among the displayed given names (C. Vann Woodward `woodward|vann`,
  Kwame Anthony Appiah, Bill Waiser `waiser|william a`): probably harmless;
- `possible_pool` (139): likely two people under one id (Katherine E. / Callum G. Brown, Werner / Hugh Thomas,
  Andrew D. / David Lambert, Elizabeth / Jane Errington, Roger / John Hutchinson, Guilherme P. / Lucia Maria
  Bastos Pereira das Neves). Check the `top_works` column.
`key_log_key` is the key in data/identifiers that holds `diss-person:<id>`: after a split, the key-log session
re-anchors it (the key holds the person of its PIDs; Ian Milligan's key must not keep Gerry's id).
