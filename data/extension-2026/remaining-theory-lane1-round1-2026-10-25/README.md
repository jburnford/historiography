# Remaining theory, lane 1 round 1 — revision 1.184

Prepared against 1.183 for coordinator integration and independent substantive
review. The owned release adds eight theorist entries in `intellectual_connections`:
Bourdieu, Habermas, Arendt, Butler, Harvey, Halbwachs, Pratt and Bhabha. Existing
IDs are reused for six; Arendt and Pratt receive positively matched new identities
and sourced group contexts. No authority identifiers are guessed.

`release/editorial-additions.json` contains eight nodes, 18 relationships, 16 new
sources, two new people, six additive roster contexts and 31 selected dated facts.
The in-memory candidate has 323 nodes, 1,524 relationships, 2,852 sources and 1,417
people. `validation.json` passes with no errors or new warnings. All old IDs,
edges, sources, identity-note prefixes, roster prose, group chronologies, descriptions,
strands and coverage remain exact. No apply, commit or push was performed.

Each person directory contains `entry-draft.json`, `research-notes.json` and a
standardized `life-status.json`. Existing primary readings are reused with their
precise earlier scope, rather than being described as new full-book readings.
New readings use separate source records and preserve earlier publisher-only limits.

- Bourdieu: retained selected Outline pages, selected Distinction conclusion transcription and complete four-page biographical-illusion review. English Outline is revised/reordered; Richard Nice’s translation credits and 1972/1977, 1979/1984 dates remain distinct.
- Habermas: retained complete 1964/1974 encyclopedia article and selected Fraser criticism. Translators Sara and Frank Lennox, Hohendahl’s notes, Burger/Lawrence’s translation/assistance and 1981 German volumes retain separate credits. The incoming critique explicitly names Fraser rather than asserting a feminist consensus.
- Arendt: complete displayed GHI translated selection of the 1964 Gaus interview, not complete broadcast or books. Public action and factual-accountability claims use her own answers; Eichmann controversy testimony remains attributed. Bard’s bibliography supplies separate book dates.
- Butler: primary printed pp. 521–522 and 530–531 of the 1988 essay, with nearby fragments inspected. Constraints and sanctions remain central; no unrestricted personal choice, innate binary or entire Gender Trouble reading is asserted. Current institutional pronouns are retained.
- Harvey: new 2008 essay opening, retained visually checked 1989 pp. 302–304 and Massey’s named 1995 criticism. Paywalled remainder, complete monographs and 1991 lecture remain unread; regional resistance qualification remains alongside criticism.
- Halbwachs: retained selected French conclusion and Canguilhem’s specific statistical reception, with newly inspected digital pp. 208–209 inside the existing reading extent. Electronic pagination, 1925 original/1952 reedition, posthumous 1950 publication and Coser’s edited/translated 1992 selection stay separate. The unread 1912 book is not replaced by a memory source.
- Pratt: selected reformatted opening of the 1991 article through contact-zone, autoethnography and transculturation definitions; later pedagogy and full monographs unread. Guaman Poma is Pratt’s named reading, not a newly read original or an inference of her Indigenous identity.
- Bhabha: complete substantive publisher interview, conversation September 2013/web repost December 2017, not the unread mimicry article or book chapters. Edited Nation and Narration retains 1990 editor credit; cultures and migrant trajectories are not treated as seamless or uniform.

Life records identify four deceased (Bourdieu, Habermas, Arendt, Halbwachs) and
four living in checked current primary sources (Butler, Harvey, Pratt, Bhabha),
with medium confidence and timing limits for undated or event-listing evidence.
Habermas’s March 2026 death is explicitly verified; Halbwachs’s conflicting exact
days are left at supported 1945 year precision. Life dates do not enter work
chronologies. Missing death information never establishes life.

Raw downloads and extracted text are ignored under `research/.gitignore`; only
metadata, locators, hashes and paraphrased source notes are reviewable. OpenAlex
remains paused. `check-packet.py` builds only this owned release and transforms
in memory. Once accepted, preserve frozen bytes and use the coordinator’s acceptance
rather than regenerating the packet.
