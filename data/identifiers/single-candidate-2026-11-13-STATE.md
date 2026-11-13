# State 2026-11-13 (fetch resume, pass-nine adoption, reviews of edited volumes)

## Done
- **Fetches (stopped).**
  - Crossref, chapters of edited volumes (`nameonly-siblings --tier keylog`): 429 after 16 calls at 07:43; retried once at
    08:13 (accepted); about 250 more calls; stopped by PID at about 08:43 for the machine move (not refused). Key-log tier:
    2,565 of 4,385 volumes done (~1,820 left); linked tier (5,724 volumes) not started. Moving Natures (w-2333986) was
    fetched on 11-12 and Crossref returns 0 chapters for it; Historical GIS Research in Canada (w-916866) fetched today.
    Refusals in `build/crossref-volume-chapters-2026-11-12/refusals.jsonl`.
  - Crossref fuller records (`nameonly-fuller`): not started (0 of 1,556).
  - LC SRU (`lc_sru_recent.py fetch`): every request dropped (24 at 07:43, 24 at 08:15 after the 30-minute wait): stopped for
    the day; no new record cached (cache still 377). Refusal records `build/fetch-2026-11-13/lc-refusal-try{1,2}.json`.
- **Code.**
  - `scripts/link_work_people.py`: `PoliteCrossref` treats a dropped connection as a refusal (recorded, run stops);
    `adopted_kinds`, `ADOPT_DEFAULT`, `A_LEVELS`; `p9_fires` adds `single-subject-subfield-tie` and `single-subject-tie`;
    adopted links write `evidence=subject[+subfield]+<ties>` to the signals; `--adopt` defaults to both.
  - `scripts/lc_sru_recent.py`: dropped connections (more than half of the last 20, or three in a row) stop the run as a
    refusal instead of pausing five minutes.
  - `scripts/build_graph.py`: `adopted_evidence` (role_basis `evidence: subject + subfield + review tie` on work-people and
    name-only rows of the adopted branches); REVIEWED adds reviewer -> volume editor rows, column `target_role`.
  - `scripts/graph_explorer.py`: the linked label prints the evidence for adopted rows; REVIEWED rows to a volume editor say
    "(reviewed the volume they edited)"; `reviewed.target_role` defaults to 'author' on older builds.
  - `tests/test_link_single_candidate.py`: class `Adopted` (5 tests).
- **Relinks** (on the pre-apply build/graph of 11-12; credits resolve through the morning's merges at build time):
  name-only (positions with today's chapters, extra, link with the adopted rules, report, export), work-people
  (volume-people, link --new-facts --topic-min 20, report, export), `lc_catalogue_credits.py credits` and `measure`.
- **Builds:** check build `build/graph-check19` (post-apply key log); `build/graph-check18` is a partial build stopped by
  PID (ignore; not deleted). Live build and explorer: see the hand-back report.

## Not done
- Linked-tier volume fetch, fuller-records fetch, LC SRU fetch and index (resume below).
- `scripts/key_lc_authority_ties.py` not rerun: both readers already skip a tied authority that a key holds as an anchor
  (`link_work_people.WPPeople`: `not self.lc_key.get(lcnaf)`; `lc_catalogue_credits.person_authorities`: `NOT IN pl`), so
  the 3,120 attached ties are not double counted once the linkers read a post-apply build. The linkers ran on the
  pre-apply build, so those authorities still acted as ties there (and the LC credits name them `tied`).
- The PhD-9 to PhD-5 reviewer-credit count (optional) was not made.

## Resume (from /home/jic823/historiography)
Scratch inputs copied to `build/scratch-2026-11-13/` (nameonly: targets, crossref/jstor/ojs records, oa, oa-refs;
workpeople: positions*, contributors, oa, oa-title, oa-refs; p9data). Point a new scratch at them:
```
S=build/scratch-2026-11-13
mkdir -p $S/nameonly10 $S/workpeople10
for f in crossref.jsonl jstor.jsonl oa oa-refs.jsonl ojs.jsonl targets.parquet; do ln -sfn $PWD/$S/nameonly/$f $S/nameonly10/$f; done
for f in contributors.parquet oa oa-refs.jsonl oa-title positions-crossref.parquet positions-title.parquet positions.parquet; do ln -sfn $PWD/$S/workpeople/$f $S/workpeople10/$f; done
export WP_P9=$PWD/$S/p9data
# Crossref (one client; check ps first): key-log tier, fuller names, then the linked tier (cap 5,000 volume calls a day)
WP_SCRATCH=$PWD/$S/nameonly10 python3 -u scripts/link_work_people.py nameonly-siblings --tier keylog --max 5000 --gap 1
WP_SCRATCH=$PWD/$S/nameonly10 python3 -u scripts/link_work_people.py nameonly-fuller --max 2000 --gap 1 --workers 2
WP_SCRATCH=$PWD/$S/nameonly10 python3 -u scripts/link_work_people.py nameonly-siblings --tier linked --max 3000 --gap 1
# (or run build/fetch-2026-11-13/crossref.sh after changing its WP_SCRATCH line)
# LC (one client, 2 s): plan is in build/lc-sru-2026-11-12/
python3 -u scripts/lc_sru_recent.py fetch --cap 10000 --delay 2.0 && python3 scripts/lc_sru_recent.py index
# relink (one heavy job at a time; free -g >= 13), adopted rules are the default
WP_SCRATCH=$PWD/$S/nameonly10 sh -c 'for c in nameonly-positions nameonly-extra "link --nameonly --gold-no-oa --topic-min 20" nameonly-report nameonly-export; do python3 -u scripts/link_work_people.py $c || exit 1; done'
WP_SCRATCH=$PWD/$S/workpeople10 sh -c 'for c in volume-people "link --new-facts --topic-min 20" report export; do python3 -u scripts/link_work_people.py $c || exit 1; done'
python3 scripts/lc_catalogue_credits.py credits && python3 scripts/lc_catalogue_credits.py measure
python3 build/fetch-2026-11-13/adopted_summary.py      # counts by combination and band, 40 at random
# builds
flock .keylog.lock python3 scripts/build_graph.py --untracked-ok --out build/graph-check20
flock .keylog.lock python3 scripts/build_graph.py
python3 scripts/graph_explorer.py build
# explorer: stop the process listening on 4180 (ss -ltnp | grep 4180, kill <pid>), then
nohup python3 scripts/graph_explorer.py serve > build/explorer.log 2>&1 &
```
