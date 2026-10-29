# Project continuity

Read `MEMORY.md` before starting work. It records the current user direction, dataset state, and handoff for building the visualization after a context reset.

Read `GRAPH-FORMAT.md` before implementing data loading or rendering relationships. Use `DEVELOPMENT.md` for design ideas and `REVISION-NOTES.md` for historical editorial decisions. Earlier counts in historical audit/revision sections are not the current dataset counts.

Source routes (user, 2026-10-19 and 2026-10-29): do not read texts from shadow libraries, document-sharing or user-upload platforms (including user-uploaded documents on scribd.com), or reposts of books and articles on unrelated personal or third-party sites. If a text is reachable only that way, record it as unread. Licensed publisher previews (including Everand), JSTOR, publisher and repository copies, the author's own posting, Internet Archive lending and public-domain scans, and teaching shares of a single chapter or article are fine. Link sources by DOI or publisher page, and never name a blocked route in graph fields, notes, packets, READMEs or commit messages. `scripts/source_hosts.py` lists the blocked hosts; `tests/test_source_hosts.py` fails if the graph links or names one, so run it before applying a batch.

Keep the OpenAlex investigation paused unless the user explicitly resumes it. Preserve existing graph IDs, editorial qualifications, and snapshots. Never put the local API key or unrelated workspace files into browser assets or deployment output.
