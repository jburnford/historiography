# Historiography atlas: student trial

Use this with the local **revision 1.127 student beta**, prepared 10 October 2026.
Allow 20–30 minutes. Ask students to work individually for the first ten minutes,
then compare what they found. Include phones and laptops, and more than one browser.

## Before the session

Build and serve the public directory:

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 0.0.0.0 --directory docs
```

On the serving computer, open http://127.0.0.1:4173/. Other devices on the same
network use that computer's network address and port 4173. Campus network policies
may prevent this; check access before the session. Serve only `docs/`.
The public website has not yet been updated with this beta.

Give students the starting URL and tasks below. Keep the facilitator notes for
discussion afterwards. Do not demonstrate the navigation first: difficulty finding
something is useful evidence. If someone is stuck, record where and offer a hint
so they can continue.

## Tasks for students

1. Spend a minute on the opening page. Explain what the two kinds of marks show
   and what you think the headline comparison says. Find a reason to be cautious
   about that comparison.
2. Choose a family of history that interests you. Open an entry, find one of its
   relationships and follow its source. Explain the claim in your own words and
   identify what the source does and does not establish.
3. Find a seminar pathway. Use it to follow three entries. Return to your starting
   entry, then use the browser's Back and Forward buttons. Copy a link to the
   page you found and open it in another tab.
4. Find Digital history. Compare the “Through 2000” and partial later views.
   Explain what changed and whether the later view makes the field's origins or
   end date more certain.
5. Find Paul E. Lovejoy's profile. Open a journal record and its explanation of
   the identity link. Explain how confidently you would attribute the item to
   this person. Then try Geoff Eley and compare the kinds of record available.
6. Choose a familiar person or field. Identify one missing item, misleading
   connection, confusing label or interpretation you would challenge. Give the
   exact entry, relationship or record, and a source if you have one.
7. Try the site on a narrow screen, at 200% zoom, or using only the keyboard.
   Find an entry and open its source without relying on the chart. Report where
   you lose your place, cannot reach a control or cannot read the content.

For every problem, record the route or URL, what you did, what happened and what
you expected. “I clicked X and could not get back to Y” is more useful than
“the navigation is bad.” Mark tasks you could not finish. Do not include private
information, account details or student names in screenshots or logs.

## Facilitator notes

Use [the feedback sheet](feedback/student-testing-template.csv), assigning anonymous
participant codes. Distinguish a broken interaction, a difficult interaction,
a mistaken inference and an editorial disagreement. Suggested priorities:
**blocking** (cannot finish), **major** (misleading or repeated difficulty),
**minor** (recoverable friction), **suggestion**.

Listen for these distinctions after students have given their own answers:

- The [coverage audit](data/evidence-layer/audits/coverage-2026-10-10/README.md)
  records the earlier false absences. The [repair report](data/evidence-layer/repairs/2026-10-10/README.md)
  distinguishes corrected mappings, recovered page ranges and earlier chart bins
  from the remaining backfile gaps. Record any inference that an empty bar dates
  a field's origin or means scholarship is absent.
- Orange marks express the atlas's selected dates; green bars describe a selected
  publication record. Neither measures importance or influence.
- Journal “research candidates” use a page-length proxy, with an article-number
  exception for the Journal of Digital History. Missing pagination and editorial
  classifications affect the comparison. The sensitivity note is on the landing.
- A comparison or shared roster is not intellectual descent. Source-check labels
  describe the evidence consulted, rather than certify every claim.
- “Through 2000” is the archived 1.121 graph, not a date filter over the latest
  graph. Later coverage is selected and incomplete; four fields are partially extended.
- The publication-record pilot covers eight profiles. A probable atlas identity
  remains probable even when a source credit has an identifier. A book reviewed
  is different from a review written. An absent record is not an absent publication.

Useful direct links if a student needs a hint: `#family=all`,
`#node=digital_history`, `#person=paul_e_lovejoy`, `#person=geoff_eley`.
The other pilot profiles are Serge Noiret, Lorraine Daston, Jay Winter,
Peter Galison, Ida Altman and Joel Mokyr.

After the trial, group repeated problems, retain the original observations and
fix blockers and misleading labels first. Treat historical corrections as
source-backed editorial proposals. Do not promote probable identities or change
classifications merely because a student expected a different result.

## Maintainer checks

```bash
python3 scripts/validate_graph.py
python3 -m unittest tests.test_graph_validation tests.test_people_validation tests.test_evidence_asset tests.test_practice_families tests.test_student_beta
node tests/test_site_core.mjs
python3 tests/run_site_checks.py
```

The browser runner needs Playwright and its Chromium installation and serves
`docs/` on a temporary localhost port. It checks the existing views plus deferred
loading, identity labels, narrow-screen records and recovery from failed downloads.
Human testing is still needed for comprehension, keyboard usability and browsers
other than Chromium.

## Indigenous-history discussion

Use the current partial view to open Indigenous history. Find one interwar work
and one earlier witness. Compare Chief Thunderchild's narration, Ahenakew's recording
and writing, and Cuthand's editorial criticism. Open the source-check notes and
explain which dates refer to recording, publication and later editing. Compare
Sioui's autohistory with another regional approach without assuming a shared origin.

The [deep-dive report](data/field-research/indigenous-deep-dive-2026-10-10/README.md)
provides checked examples and remaining candidates. Ask whether the Ethnohistory
chart can identify Indigenous authorship; its venue counts include outside scholarship.
The archived “Through 2000” view preserves the earlier selection and lacks these
corrections, even where the added works themselves predate 2000.

Compare the Stó:lō community–university approach with Leddy’s selected 2010
Serpent River case. Identify knowledge contributions, academic instruction,
authorship and mentorship. Explain why the 1997 planning date differs from the
1998 first class, and why the 2010 issue date differs from the 2011 upload timestamp.
The [foundations report](data/field-research/indigenous-foundations-2026-10-10/README.md)
records the source limits. Look for the 2010 intervention mark in the partial view;
the archived 2000 view should omit it.

## Publication-evidence repair checks

The [repair report](data/evidence-layer/repairs/2026-10-10/README.md) distinguishes
implemented fixes from the remaining backfile and genre checks. In the local beta:

- Open Annales on desktop and mobile; its record should include 1929 and explain
  the remaining 1933–1938 gap.
- Switch to Deposited journal articles; the war family should include 1937-era
  records. Explain why some are absent from the research-candidate view.
- Inspect Oral history, Labour history and Indigenous history. Check whether the
  coverage notes distinguish collected items, qualifying candidates and source limits.
- Check a zero-count field and a method entry. The text should not equate a blank
  count with absent scholarship or describe every candidate person's work as method use.

### Family explorer check

Open `#family=indigenous-histories`. Find the Stó:lō collaboration and John Lutz
without opening the broad field entry first. Search for Carlson, inspect the source
limits, follow a contributor profile and return via its family breadcrumb. Follow
the colonial-geography comparison to its evidence. Switch to Timeline and List,
then the exact-2000 view; Leddy’s 2010 case should disappear in that archived view.
Repeat on a phone and another family. The family count includes ethnohistory; it
is different from the Indigenous-history entry’s own roster and approach counts.
