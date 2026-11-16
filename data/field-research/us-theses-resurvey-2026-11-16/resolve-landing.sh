#!/usr/bin/env bash
# USER-RUN: read the landing pages of theses on hosts that allow general clients but exclude named AI crawlers,
# and write the file link each page declares (<meta name="citation_pdf_url">) as a fetch.sh list.
# Metadata only: one landing page per thesis, no thesis file is requested here.
#   bash resolve-landing.sh ai-excluded-landing.tsv            # -> ai-excluded-resolved-urls.tsv (same folder)
#   bash fetch.sh ai-excluded-resolved-urls.tsv /mnt/e/historiography-dissertation-pdfs/us-wget-2026-11-16
# One request at a time, the host's crawl delay (else 10 s) after each, plain curl identity. Resumable. A host that
# answers 429, or misses ten times in a row (refusals, challenge pages, pages without a file link), is stopped for
# the run; its rows go to landing-misses.tsv.
set -u
LIST="${1:?usage: bash resolve-landing.sh <landing.tsv>}"
HERE="$(cd "$(dirname "$LIST")" && pwd)"
OUTL="$HERE/ai-excluded-resolved-urls.tsv"; MISSES="$HERE/landing-misses.tsv"; TMP="$(mktemp)"
touch "$OUTL" "$MISSES"
declare -A STOPPED; declare -A MISS
while IFS=$'\t' read -r url name host delay; do
  [ -z "$url" ] && continue
  grep -q -F "	$name	" "$OUTL" "$MISSES" 2>/dev/null && continue
  if [ -n "${STOPPED[$host]:-}" ]; then printf '%s\t%s\t%s\tstopped host\n' "$url" "$name" "$host" >> "$MISSES"; continue; fi
  code=$(curl -sS -L --max-time 120 -o "$TMP" -w '%{http_code}' "$url" </dev/null 2>/dev/null)
  pdf=$(tr '\n' ' ' < "$TMP" | grep -o -i '<meta[^>]*citation_pdf_url[^>]*>' | head -1 | grep -o -i 'content="[^"]*"' | head -1 | cut -d'"' -f2 | sed 's/&amp;/\&/g')
  if [ "$code" = "200" ] && [ -n "$pdf" ]; then
    case "$pdf" in http*) ;; /*) pdf="https://$host$pdf";; esac
    printf '%s\t%s\t%s\t%s\n' "$pdf" "$name" "$(echo "$pdf" | awk -F/ '{print $3}')" "$delay" >> "$OUTL"; MISS[$host]=0; res=ok
  else
    title=$(head -c 3000 "$TMP" | tr '\n\r\t' '   ' | grep -o -i '<title>[^<]*' | head -1 | cut -c8-80)
    printf '%s\t%s\t%s\t%s %s\n' "$url" "$name" "$host" "$code" "$title" >> "$MISSES"; res="miss:$code $title"
    MISS[$host]=$(( ${MISS[$host]:-0} + 1 ))
    if [ "$code" = "429" ] || [ "${MISS[$host]}" -ge 10 ]; then STOPPED[$host]=1; echo "stopping $host for this run"; fi
  fi
  echo "$res $host $name"
  sleep "${delay%.*}"
done < "$LIST"
rm -f "$TMP"
echo "done: file links in $OUTL, misses in $MISSES"
