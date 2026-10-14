# Draft: permission request to eScholarship (not sent)

For the user to review and send from their own account. Prepared 2026-10-13. Not sent: the
user said "we can't do it today".

**To:** help@escholarship.org
**Subject:** Permission for rate-limited retrieval of UC History PhD dissertations (bibliography research)

Dear eScholarship team,

I am a historian at the University of Saskatchewan and editor of *Historical Methods*. I am
building a non-commercial research dataset on what History doctoral students cite. We
extract only the bibliographies of dissertations and analyse the works cited. We have done
this for about 2,000 Canadian History PhDs and are now adding US programmes.

eScholarship holds the open dissertations of the UC History departments: Berkeley, UCLA,
San Diego, Santa Barbara, Irvine, Davis and others. Your GraphQL and OAI-PMH interfaces work
well for metadata. Automated requests for the PDFs, however, receive HTTP 403 from
CloudFront. I would like to ask permission to retrieve the open-access PDFs of History PhD
dissertations deposited since 2005, about 650 files, under these terms:

- one request at a time, at least 7 seconds apart, or any rate you prefer;
- a clearly identified user agent, at a time of your choosing;
- only items whose metadata marks them as open access, with no embargoed or
  campus-restricted items;
- no redistribution of the full texts. We keep only the parsed reference lists and
  aggregate citation counts, and cite each dissertation by its eScholarship URL.

If a bulk export or another route would suit you better, I would be glad to use it.

With thanks,
Jim Clifford
Department of History, University of Saskatchewan

## Before sending

- Check the role line and add a link to the project if wanted.
- Once permission is granted, fix the user-agent string and the rate in the harvester
  config.
