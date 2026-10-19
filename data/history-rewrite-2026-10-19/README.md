# History rewrite, 19 October 2026

The repository history was rewritten on 2026-10-19 to correct source links throughout. Links to
copies of texts that were not official publications now point to the DOI or publisher page, or
are removed where no official page exists. Notes that described those copies were reworded to
record only what was read. Readings are unchanged, and so is every other part of the data.

Every commit therefore has a new ID. Documents and notes written before the rewrite cite the old
IDs, for example "932f28f" for revision 1.144. `commit-map.tsv` maps each old commit to its new one,
with its date and subject. Look up a short ID by its prefix:

```bash
grep '^932f28f' data/history-rewrite-2026-10-19/commit-map.tsv
```

Embedded sha256 fingerprints were updated to match the corrected files: acceptance records, pinned
baselines and script constants. One pinned commit ID was also updated, in
`data/field-research/timeline-spans-2026-10-15/baseline/manifest.json`. The rewritten history
passed the full CI before it was published.
