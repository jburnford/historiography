#!/usr/bin/env bash
# User-run METADATA listing of Canadian repositories that allow general clients but exclude AI crawlers
# (Scholaris DSpace hosts, UQAM Archipel, Guelph Atrium). No thesis files are requested here.
# robots.txt of every host listed below allows '*' on /server/oai/request (DSpace) and /cgi/oai2 (EPrints),
# checked 2026-11-14; Crawl-delay 5 where given, this script waits 10 s between requests anyway.
#
#   bash canada-list-holdings.sh sets       # 1. ListSets of each host (a few requests per host)
#   python3 scripts/user_run_canada.py pick-sets          # 2. (in the repo) choose thesis/History sets -> canada-listing-sets.tsv
#   bash canada-list-holdings.sh records    # 3. ListRecords of the chosen sets (xoai for DSpace: has bitstream links)
#   python3 scripts/user_run_canada.py build-from-listings  # 4. History PhDs not held -> canada-ai-excluded-urls.tsv
#
# One connection, plain curl identity, resumable (pages already saved are skipped; a set whose last page has no
# resumption token is marked done). A host that answers 429, or misses ten times in a row, is stopped for the run.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT:-/mnt/e/user-run-downloads-2026-11-14/canada-listings}"
GAP="${GAP:-10}"
HOSTS="utoronto.scholaris.ca queensu.scholaris.ca uwo.scholaris.ca dal.scholaris.ca mcgill.scholaris.ca ualberta.scholaris.ca umontreal.scholaris.ca ucalgary.scholaris.ca carleton.scholaris.ca memorial.scholaris.ca usherbrooke.scholaris.ca atrium.lib.uoguelph.ca archipel.uqam.ca"
declare -A STOPPED; declare -A MISS
base_of() { case "$1" in archipel.uqam.ca) echo "https://$1/cgi/oai2";; *) echo "https://$1/server/oai/request";; esac; }

get() {  # get <host> <outfile> <curl -G args...>
  local host="$1" out="$2"; shift 2
  [ -n "${STOPPED[$host]:-}" ] && return 1
  [ -s "$out" ] && return 0
  local code
  code=$(curl -sS -G --max-time 300 --retry 1 -o "$out.part" -w '%{http_code}' "$@" </dev/null 2>>"$OUT/curl-errors.log")
  sleep "$GAP"
  if [ "$code" = "200" ] && grep -q "<OAI-PMH" "$out.part" 2>/dev/null; then
    mv "$out.part" "$out"; MISS[$host]=0; return 0
  fi
  echo "$(date -u +%FT%TZ) $host $code $(head -c 200 "$out.part" 2>/dev/null | tr '\n' ' ')" >> "$OUT/misses.log"
  rm -f "$out.part"
  MISS[$host]=$(( ${MISS[$host]:-0} + 1 ))
  if [ "$code" = "429" ] || [ "${MISS[$host]}" -ge 10 ]; then STOPPED[$host]=1; echo "stopping $host for this run ($code)"; fi
  return 1
}
token_of() { grep -o '<resumptionToken[^>]*>[^<]*</resumptionToken>' "$1" | sed 's/<[^>]*>//g' | head -1; }

mode="${1:?usage: bash canada-list-holdings.sh sets|records}"
mkdir -p "$OUT"
if [ "$mode" = "sets" ]; then
  for host in $HOSTS; do
    mkdir -p "$OUT/$host"; base=$(base_of "$host"); n=0
    get "$host" "$OUT/$host/sets-0.xml" "$base" --data-urlencode "verb=ListSets" || continue
    tok=$(token_of "$OUT/$host/sets-0.xml")
    while [ -n "$tok" ]; do
      n=$((n+1))
      get "$host" "$OUT/$host/sets-$n.xml" "$base" --data-urlencode "verb=ListSets" --data-urlencode "resumptionToken=$tok" || break
      tok=$(token_of "$OUT/$host/sets-$n.xml")
    done
    echo "$host: $((n+1)) ListSets pages"
  done
elif [ "$mode" = "records" ]; then
  SETS="$HERE/canada-listing-sets.tsv"
  [ -s "$SETS" ] || { echo "run: python3 scripts/user_run_canada.py pick-sets   first"; exit 1; }
  while IFS=$'\t' read -r host prefix spec label; do
    [ "$host" = "host" ] && continue
    d="$OUT/$host/records-$spec"; mkdir -p "$d"
    [ -e "$d/DONE" ] && continue
    base=$(base_of "$host"); n=0
    get "$host" "$d/page-0.xml" "$base" --data-urlencode "verb=ListRecords" --data-urlencode "metadataPrefix=$prefix" --data-urlencode "set=$spec" || continue
    if grep -q 'noRecordsMatch' "$d/page-0.xml"; then touch "$d/DONE"; continue; fi
    tok=$(token_of "$d/page-0.xml"); ok=1
    while [ -n "$tok" ]; do
      n=$((n+1))
      get "$host" "$d/page-$n.xml" "$base" --data-urlencode "verb=ListRecords" --data-urlencode "resumptionToken=$tok" || { ok=0; break; }
      tok=$(token_of "$d/page-$n.xml")
    done
    [ "$ok" = 1 ] && touch "$d/DONE"
    echo "$host $spec ($label): $((n+1)) pages"
  done < "$SETS"
else
  echo "usage: bash canada-list-holdings.sh sets|records"; exit 1
fi
echo "done; misses (if any) in $OUT/misses.log"
