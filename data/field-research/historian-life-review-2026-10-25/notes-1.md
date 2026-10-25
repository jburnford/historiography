# Queue 1 life-status review — 25 October 2026

All 34 assigned identities reviewed: **24 deceased, 10 living, 0 unresolved**.
`results-1.json` contains the person-level findings, exact source URLs and locators,
access scope, prior date-sheet values, precision, identity distinctions and limits.
`build-results-1.py` serializes these manual decisions and asserts queue coverage;
it does not update the graph or the date sheet.

Six deaths missing from the old date sheet are now sourced: Fernand Ouellet
(28 June 2021), Gu Jiegang (25 December 1980), Ibn Khaldun (1406, year only),
J. M. S. Careless (6 April 2009), Julia Cherry Spruill (1986, year only), and
Ramsay Cook (14 July 2016). The recent death of Carlo Ginzburg on 17 June 2026
is freshly confirmed by his Scuola Normale obituary; the old sheet already had it.

Day conflicts are kept explicit: Labrousse is 23 May in the old sheet and a
contemporary Belgian Academy obituary but 24 May in BnF. Febvre is 25 September
in the old sheet/Collège de France but 26 September in EPHE; an Annales memorial
calls it the night of 25–26 September. Their unambiguous death years (1988 and
1956) are recommended. Earlier precise values remain in `previous_death_data`.

Living classifications use positive institutional or author evidence, usually
from 2026. Patrick Joyce's official 2026 Academy admission citation is available
in the booklet hosted by Trinity; the Academy news URL itself returned 403.
Georges E. Sioui has a current scholarly publisher biography, a first-person
2026 album note and a July 2026 collaborator interview. These sources do not
establish the exact last personal-contact date; limits are recorded.

Targeted death searches rejected obituary namesakes of Adele Perry, Allan Greer,
Catherine Hall and Jean O'Brien. Ouellet's 2019/2020 namesake notices are also
rejected. Dorothy Thompson is the Chartism historian, Mary Ritter Beard is the
American women's historian, and Skinner is the intellectual historian.

No absent Wikidata death statement is treated as proof of life. No publication
or influence timeline is extended from a lifespan. Hartman's old birth value
`1961-01-01` has **year precision** and must remain 1961, not an invented birthday.
No OpenAlex work, graph edits, date-sheet edits, browser builds or publication.
