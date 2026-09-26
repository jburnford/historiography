-- Screening queue only: length does not establish research-article genre.
SELECT r.record_id, r.doi, r.publication_year, r.print_date, r.online_date,
       r.title_text, r.volume, r.issue, r.page_raw, r.page_count,
       r.pagination_status, r.book_citation_title_hint, r.genre_status,
       string_agg(c.name, ' | ' ORDER BY c.position) AS deposited_byline
FROM research_candidates_by_length r
LEFT JOIN contributors c ON c.record_id=r.record_id AND c.role_array='author'
GROUP BY ALL
ORDER BY r.publication_year, r.volume, r.issue, r.doi;
