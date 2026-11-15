#!/usr/bin/env bash
# User-run lookup of missing Canadian History PhDs in Library and Archives Canada's Collection Search
# (Theses Canada records are in the "Library" data source). Saves result pages only; no thesis files.
# robots.txt of recherche-collection-search.bac-lac.gc.ca (read 2026-11-14): "User-agent: *  Allow: /" with
# "Content-Signal: search=yes,ai-train=no,use=reference"; named AI crawlers are disallowed, so an AI agent does
# not run this. Not training, not redistribution: the pages are parsed locally for a record link and a PDF link.
#
#   LIMIT=20 bash canada-lac-lookup.sh      # first: 20 lookups, then send the folder listing back so the
#                                           # parser can be written against real pages (query form unverified)
#   bash canada-lac-lookup.sh               # all (~1,950 at 10 s = about 5.5 hours; resumable)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
Q="$HERE/canada-lac-queue.tsv"
OUT="${OUT:-/mnt/e/user-run-downloads-2026-11-14/canada-lac}"
GAP="${GAP:-10}"; LIMIT="${LIMIT:-0}"
mkdir -p "$OUT"; n=0; miss=0
while IFS=$'\t' read -r id q; do
  [ -z "$id" ] && continue
  [ -s "$OUT/$id.html" ] && continue
  n=$((n+1)); [ "$LIMIT" -gt 0 ] && [ "$n" -gt "$LIMIT" ] && break
  code=$(curl -sS -G --max-time 120 -o "$OUT/$id.html.part" -w '%{http_code}' \
    "https://recherche-collection-search.bac-lac.gc.ca/eng/Home/Result" \
    --data-urlencode "q_any=$q" --data-urlencode "DataSource=Library" </dev/null 2>>"$OUT/curl-errors.log")
  if [ "$code" = "200" ]; then mv "$OUT/$id.html.part" "$OUT/$id.html"; miss=0
  else rm -f "$OUT/$id.html.part"; miss=$((miss+1)); echo "$id $code" >> "$OUT/misses.log"
    if [ "$code" = "429" ] || [ "$miss" -ge 10 ]; then echo "stopping ($code, $miss misses in a row)"; break; fi
  fi
  echo "[$n] $code $id"
  sleep "$GAP"
done < "$Q"
echo "done: pages in $OUT"
