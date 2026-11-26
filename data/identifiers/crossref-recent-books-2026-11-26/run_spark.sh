#!/bin/bash
# spark: the recent-books round (2026-11-26), run from /mnt/data/jic823/tools/crossref-extract/recent-books-2026-11-26
set -e
PY=../../cr-venv/bin/python
$PY -I books_spark.py in out > out/books.log 2>&1
$PY -I match_reviews_recent.py /mnt/data/jic823/crossref-history-slice out ../reviews-2026-11-25/out/candidates.parquet > out/match.log 2>&1
$PY -I export_selected.py out > out/export.log 2>&1
echo ALL-DONE >> out/export.log
