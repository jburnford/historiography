# Metadata access notes — checked 2026-09-21

Follow-up completed: [Crossref audit](../ahr-crossref-audit-2026-09-21/README.md).
The public API supplies a useful metadata-only collection, but review labels,
book relationships and some affiliations still require reconciliation.

User clarified that only review metadata is wanted, not the reviews themselves.
Future retrieval should select bibliographic fields, bylines, affiliations,
identifiers and document/section labels; exclude review bodies and abstract or
extract text. The completed coverage probe included abstract-field samples to
assess availability before this clarification; do not expand that collection.

Oxford's [legal notice](https://academic.oup.com/pages/legal-notice), dated
3 September 2026, broadly restricts automated scraping. It gives no explicit
metadata-only exemption. Its noncommercial TDM provisions depend on subscription
agreements, applicable licences or legal exceptions; these do not establish a
blanket permission for this proposed website harvest. This is an observation
about the published policy, not a ruling on the legal status of factual metadata.

The [standard reuse page](https://academic.oup.com/pages/standard-publication-reuse-rights)
still says noncommercial TDM needs no formal permission. Its further-information
link redirects to the more qualified legal notice. These pages do not provide
an unambiguous operational authorization for automated website collection.

[Crossref's REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
expressly offers publisher-deposited metadata publicly for reuse, with a separate
copyright caveat for some abstracts. Use AHR's ISSN or its DOIs to test how much
of the needed metadata is available there; select fields excluding abstracts.
Crossref is an access route, not a guarantee of complete/correct reviewer roles,
affiliations or publisher section classifications. Compare against the saved
OpenAlex samples before deciding whether direct publisher access is necessary.

For missing website-only fields, a publisher metadata export or clarification
through OUP/institutional library is an alternative. No message or permission
request has been sent to either. No publisher crawler has been started.
