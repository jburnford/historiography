#!/usr/bin/env bash
# Download the AHA direct-PDF lists politely. Run by the user, from WSL:
#   bash fetch.sh open-urls.tsv          # sites whose robots.txt allows any client
#   bash fetch.sh ai-excluded-urls.tsv   # sites that allow general clients but exclude named AI crawlers
# One file at a time, a pause after every request (the site's crawl delay, else 10 s), plain curl identity.
# Safe to stop (Ctrl-C) and rerun: finished files are skipped. A site that answers with a refusal (401/403/429)
# or three times in a row with something that is not a PDF is dropped for the rest of the run and its links are written to
# back-to-browser.tsv, so nothing is retried against a site that said no.
set -u
LIST="${1:?usage: bash fetch.sh <list.tsv> [output folder]}"
OUT="${2:-/mnt/e/historiography-dissertation-pdfs/aha-wget-2026-11-14}"
mkdir -p "$OUT"
LOG="$OUT/fetch-log.tsv"; BACK="$OUT/back-to-browser.tsv"
declare -A STOPPED; declare -A MISS
n=0; ok=0
while IFS=$'\t' read -r url name host delay; do
  [ -z "$url" ] && continue
  n=$((n+1))
  if [ -n "${STOPPED[$host]:-}" ]; then printf '%s\t%s\t%s\n' "$url" "$name" "$host" >> "$BACK"; continue; fi
  if [ -s "$OUT/$name" ]; then continue; fi
  code=$(curl -sS -L --max-time 600 --retry 1 -o "$OUT/$name.part" -w '%{http_code} %{content_type}' "$url" </dev/null 2>>"$OUT/curl-errors.log")
  ctype="${code#* }"; code="${code%% *}"
  if [ "$code" = "200" ] && [ "$(head -c 4 "$OUT/$name.part" 2>/dev/null)" = "%PDF" ]; then
    mv "$OUT/$name.part" "$OUT/$name"; ok=$((ok+1)); res=ok; MISS[$host]=0
  else
    # what came back instead of a PDF: content type and, for a web page, its title (for diagnosis only)
    what=$(head -c 3000 "$OUT/$name.part" 2>/dev/null | tr '\n\r\t' '   ' | grep -o -i '<title>[^<]*' | head -1 | cut -c8-90)
    rm -f "$OUT/$name.part"; res="failed:$code [$ctype] $what"
    printf '%s\t%s\t%s\n' "$url" "$name" "$host" >> "$BACK"
    MISS[$host]=$(( ${MISS[$host]:-0} + 1 ))
    case "$code" in
      401|403|429) STOPPED[$host]=1; echo "stopping $host for this run (refused: $code)";;
      *) if [ "${MISS[$host]}" -ge 3 ]; then STOPPED[$host]=1; echo "stopping $host for this run (3 answers in a row that were not PDFs)"; fi;;
    esac
  fi
  printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$res" "$host" "$name" >> "$LOG"
  echo "[$n] $res $host $name"
  sleep "${delay%.*}"
done < "$LIST"
echo "done: $ok new PDFs in $OUT; anything refused is listed in $BACK"
