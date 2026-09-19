# Named-person corrections — revision 1.121

Applied the user's requested field connections in production data:

- Geoff Eley joins New social history; Keith Nield receives the coauthor credit for their 1980 intervention. Eley's Sonderweg and public-sphere contexts remain.
- E. A. Wrigley joins Economic history, retaining demography, quantitative and social-history roles.
- Immanuel Wallerstein's contextual role in Dependency / world-systems changes from `contributor` to `historian`, the current schema's practitioner category. His existing `worldsystems` strand, works, sources and qualifications survive. This is a historical practice, not an exclusive professional credential.
- Paul E. Lovejoy is added as a shared historian in African history and Atlantic/diaspora history, grounded in his 1997 programme. He is distinct from Arthur O. Lovejoy. No full person node is created.
- Maxine Berg joins Consumption & material culture, with Helen Clifford credited as coeditor of *Consumers and Luxury* (1999). Berg's economic and technology contexts remain.

Seven roster additions, five strands, three shared people and five sources; no new influence edges. **126 nodes, 765 edges, 846 sources, 833 people, 738 strands and thirteen pathways.** Original node IDs, earlier sources/people, relationships, existing strands, pathways, journal catalogue and claim catalogue survive. The only changed prior roster record is Wallerstein's role/context, saved in [acceptance.json](acceptance.json).

Evidence is deliberately bounded: Eley/Nield publisher metadata, Berg/Clifford institutional bibliography, Wrigley's Economic History Society account, Lovejoy's indexed author abstract and York identity profile. None becomes a full-work reading. The 1980 Eley/Nield issue is not dated to its 2008 online posting. Coedited chapters are not attributed wholesale to their editors. The Lovejoy PDF certificate failure is recorded; no insecure retrieval used.

The broader [medical/geography continuation](../../extension-2026/health-geography-05/README.md) has 16 works and 18 historical proposals, with four concrete entry drafts. That post-2000 packet remains staging; this correction does not claim the production atlas now covers all of 2026.

Validate with `python3 scripts/apply_roster_corrections.py --check`. Its exact reconstruction uses the protected incoming 1.120 snapshot and verifies the evidence hashes. The focused roster/research/graph/people suite passes 25 tests; structural validation has zero errors and the same four existing warnings.

**Fable handoff:** rebuild from the production JSON when ready. The data uses existing roles and roster/strand schema; no website source/build edits were made here. No push or deployment.
