# Task 2b — mint candidates, second reviewer
Exactly Task 2 (read ../2-mint-list/TASK.md and follow it, including fields and classes), but you
work the queue from the OTHER end: build the same queue (or copy ../2-mint-list/queue.csv) and
take people in ASCENDING order of authored claims, last row first. Before each case check
../2-mint-list/verdicts.jsonl and ../1-place-authors/verdicts.jsonl and skip anyone already
given a verdict there; stop and write DONE when you meet the other reviewer's frontier.
Write only in this folder. Memory: DuckDB `SET memory_limit='1GB'`.
