#!/usr/bin/env python3
"""Write literature.json and entry-draft.json for the settler-colonialism request.

Run settler_colonial_evidence.py first; this script reads its evidence.json for
dissertation counts. Bibliographic records below were checked on 2026-10-12
against the URL or DOI recorded with each one (Crossref, OpenAlex, publisher
pages, library catalogues, Open Library). Notes on arguments rest only on the
abstract, contents page or title named in each verification note.

    python3 data/extension-2026/settler-colonialism-request-2026-10-12/build_request.py
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
CHECKED = "2026-10-12"
ev = json.load(open(OUT / "evidence.json"))
counts = {r["key"]: r for r in ev["core_works"]}


def V(status, against, note):
    return {"status": status, "checked_on": CHECKED, "checked_against": against, "note": note}


META = "bibliographic_metadata_checked"
PAGE = "supporting_page_checked"

# Each record: id, section, citation, doi/url, verification, optional evidence_key, optional reading.
LIT = [
    # ---- origins and precursors
    dict(id="denoon_1983", section="origins_precursors", year=1983,
         citation="Donald Denoon, Settler Capitalism: The Dynamics of Dependent Development in the Southern Hemisphere (Oxford: Clarendon Press, 1983).",
         url="https://openlibrary.org/works/OL4635710W", doi=None,
         verification=V(META, "Open Library work record; reviews in AHR 90:1 (1985) doi:10.2307/1860758 and EcHR 38:1 (1985) doi:10.2307/2596683 via Crossref",
                        "Author, title, Clarendon/OUP and 1983 checked. Book unread; listed as an earlier comparative 'settler' literature, not a founding claim."),
         reading="Title-level only: comparative settler economies of the southern hemisphere."),
    dict(id="wolfe_1994", section="origins_precursors", year=1994,
         citation="Patrick Wolfe, \"Nation and MiscegeNation: Discursive Continuity in the Post-Mabo Era,\" Social Analysis 36 (1994): 93–152.",
         url="https://www.jstor.org/stable/23171805", doi=None,
         verification={"status": "unverified", "checked_on": CHECKED, "checked_against": "JSTOR page blocked automated access; OpenAlex has no record",
                       "note": "Details come from a secondary web search summary only. Do not cite until checked on JSTOR or in a library catalogue."},
         reading=None),
    dict(id="stasiulis_yuval_davis_1995", section="origins_precursors", year=1995,
         citation="Daiva Stasiulis and Nira Yuval-Davis, eds., Unsettling Settler Societies: Articulations of Gender, Race, Ethnicity and Class (London: SAGE, 1995).",
         doi="10.4135/9781446222225", url="https://doi.org/10.4135/9781446222225",
         verification=V(META, "Crossref DOI record (SAGE, edited book, 1995; editors Stasiulis and Yuval-Davis)",
                        "Metadata only. Cited by Freeman's 2011 Toronto dissertation, which uses this earlier settler-society literature rather than Wolfe."),
         evidence_key="stasiulis_yuval_davis_1995", reading="Title-level: gender, race, ethnicity and class in settler societies."),
    dict(id="wolfe_1999", section="origins_precursors", year=1999,
         citation="Patrick Wolfe, Settler Colonialism and the Transformation of Anthropology: The Politics and Poetics of an Ethnographic Event (London and New York: Cassell, 1999). Writing Past Colonialism series.",
         url="https://openlibrary.org/works/OL1895662W", doi=None,
         verification=V(META, "Open Library work record (Cassell, 1999; ISBN 0304703397 / 0304703400); existing atlas source ind127_wolfe_1999 (eoas.info)",
                        "Metadata only; book unread. Already an atlas source on the Indigenous entry."),
         evidence_key="wolfe_1999"),
    dict(id="elkins_pedersen_2005", section="origins_precursors", year=2005,
         citation="Caroline Elkins and Susan Pedersen, eds., Settler Colonialism in the Twentieth Century: Projects, Practices, Legacies (New York: Routledge, 2005).",
         url="https://catalog.americanacademy.de/bib/2854", doi="10.4324/9780203621042",
         verification=V(META, "American Academy in Berlin catalogue (New York: Routledge, 2005; xiii, 303 pp.; ISBN 0415949424/0415949432); Routledge product page (states copyright 2006); Crossref ebook DOI dated 2012; Veracini's review, History Australia 3:1 (2006), doi:10.2104/ha060027",
                        "Print year 2005 per catalogue; publisher page says 2006 and the ebook DOI 2012. Contents unread."),
         evidence_key="elkins_pedersen_2005"),
    # ---- theory and field formation
    dict(id="wolfe_2001", section="theory", year=2001,
         citation="Patrick Wolfe, \"Land, Labor, and Difference: Elementary Structures of Race,\" American Historical Review 106, no. 3 (2001): 866–905.",
         doi="10.1086/ahr/106.3.866", url="https://doi.org/10.1086/ahr/106.3.866",
         verification=V(META, "Crossref DOI record", "Metadata only; OpenAlex has an author note, not an abstract."),
         evidence_key="wolfe_2001"),
    dict(id="wolfe_2006", section="theory", year=2006,
         citation="Patrick Wolfe, \"Settler Colonialism and the Elimination of the Native,\" Journal of Genocide Research 8, no. 4 (2006): 387–409.",
         doi="10.1080/14623520601056240", url="https://doi.org/10.1080/14623520601056240",
         verification=V(META, "Crossref DOI record; OpenAlex opening lines",
                        "Metadata and opening lines only (genocide and contests for land). The 'structure, not an event' formulation is attested here through Kauanui 2016's abstract, not a page check of Wolfe."),
         evidence_key="wolfe_2006"),
    dict(id="veracini_2008", section="theory", year=2008,
         citation="Lorenzo Veracini, \"Settler Collective, Founding Violence and Disavowal: The Settler Colonial Situation,\" Journal of Intercultural Studies 29, no. 4 (2008): 363–379.",
         doi="10.1080/07256860802372246", url="https://doi.org/10.1080/07256860802372246",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: settler colonial subjectivities and disavowal, with a Lacanian reading; focused on Australia."),
         evidence_key="veracini_2008"),
    dict(id="veracini_2010", section="theory", year=2010,
         citation="Lorenzo Veracini, Settler Colonialism: A Theoretical Overview (Basingstoke: Palgrave Macmillan, 2010).",
         doi="10.1057/9780230299191", url="https://doi.org/10.1057/9780230299191",
         verification=V(META, "Crossref DOI record (Palgrave Macmillan UK, 2010); chapter 'Introduction: The Settler Colonial Situation' doi:10.1057/9780230299191_1",
                        "Metadata only."),
         evidence_key="veracini_2010"),
    dict(id="veracini_2011", section="theory", year=2011,
         citation="Lorenzo Veracini, \"Introducing: Settler Colonial Studies,\" Settler Colonial Studies 1, no. 1 (2011): 1–12.",
         doi="10.1080/2201473X.2011.10648799", url="https://doi.org/10.1080/2201473X.2011.10648799",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: the journal aims to consolidate a new field; colonial and settler colonial phenomena should be analytically disentangled and understood in dialectical relation."),
         evidence_key="veracini_2011"),
    dict(id="veracini_2013", section="theory", year=2013,
         citation="Lorenzo Veracini, \"'Settler Colonialism': Career of a Concept,\" Journal of Imperial and Commonwealth History 41, no. 2 (2013): 313–333.",
         doi="10.1080/03086534.2013.768099", url="https://doi.org/10.1080/03086534.2013.768099",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: three earlier passages. Until the 1960s settlement was seen as unrelated to colonialism, with Indigenous presence disavowed. To the late 1970s 'settler colonialism' named a diehard hyper-colonialism challenged by anti-colonial insurgencies. In the late 1970s–1980s it was linked to development."),
         evidence_key="veracini_2013"),
    dict(id="veracini_2015", section="theory", year=2015,
         citation="Lorenzo Veracini, The Settler Colonial Present (Basingstoke: Palgrave Macmillan, 2015).",
         doi="10.1057/9781137372475", url="https://doi.org/10.1057/9781137372475",
         verification=V(META, "Crossref DOI record", "Metadata only."), evidence_key="veracini_2015"),
    dict(id="wolfe_2016", section="theory", year=2016,
         citation="Patrick Wolfe, Traces of History: Elementary Structures of Race (London: Verso, 2016).",
         url="https://openlibrary.org/works/OL22320133W", doi=None,
         verification=V(META, "Open Library work record (Verso; ISBN 9781781689165/9781781689189; editions dated 2015 and 2016); reviews in Australian Historical Studies 48:1 (2017) via Crossref",
                        "Imprint year to confirm on the copy (Open Library lists 2015 and 2016)."),
         evidence_key="wolfe_2016"),
    dict(id="cavanagh_veracini_2017", section="theory", year=2017,
         citation="Edward Cavanagh and Lorenzo Veracini, eds., The Routledge Handbook of the History of Settler Colonialism (London: Routledge, 2017).",
         doi="10.4324/9781315544816", url="https://doi.org/10.4324/9781315544816",
         verification=V(META, "Crossref DOI record (Routledge; editors Cavanagh and Veracini; online 12 Aug 2016)",
                        "Crossref dates the online edition 2016; citing dissertations give 2017 (print). Includes Adam Barker's chapter on the consolidation of Canada, doi:10.4324/9781315544816-21."),
         evidence_key="cavanagh_veracini_2017"),
    dict(id="hixson_2013", section="theory", year=2013,
         citation="Walter L. Hixson, American Settler Colonialism: A History (New York: Palgrave Macmillan, 2013).",
         doi="10.1057/9781137374264", url="https://doi.org/10.1057/9781137374264",
         verification=V(META, "Crossref DOI record", "Metadata only."), evidence_key="hixson_2013"),
    dict(id="hoxie_2008", section="theory", year=2008,
         citation="Frederick E. Hoxie, \"Retrieving the Red Continent: Settler Colonialism and the History of American Indians in the US,\" Ethnic and Racial Studies 31, no. 6 (2008): 1153–1167.",
         doi="10.1080/01419870701791294", url="https://doi.org/10.1080/01419870701791294",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: postcolonial critique offers a pathway out of the marginalisation of American Indian history. 'Settler colonialism', first formulated among geographers, is its most promising aspect and frames Indigenous encounters with modernity as an ongoing struggle with colonial rule."),
         evidence_key="hoxie_2008"),
    # ---- Indigenous critique, recognition and resurgence
    dict(id="byrd_2011", section="indigenous_critique_resurgence", year=2011,
         citation="Jodi A. Byrd, The Transit of Empire: Indigenous Critiques of Colonialism (Minneapolis: University of Minnesota Press, 2011).",
         doi="10.5749/minnesota/9780816676408.001.0001", url="https://doi.org/10.5749/minnesota/9780816676408.001.0001",
         verification=V(META, "Crossref DOI record", "Metadata only."), evidence_key="byrd_2011"),
    dict(id="l_simpson_2011", section="indigenous_critique_resurgence", year=2011,
         citation="Leanne Simpson [Leanne Betasamosake Simpson], Dancing on Our Turtle's Back: Stories of Nishnaabeg Re-Creation, Resurgence and a New Emergence (Winnipeg: Arbeiter Ring, 2011).",
         url="https://openlibrary.org/works/OL16321922W", doi=None,
         verification=V(META, "Open Library work record (Arbeiter Ring Pub., 2011; ISBN 9781894037501)", "Metadata only."),
         evidence_key="l_simpson_2011"),
    dict(id="tuck_yang_2012", section="indigenous_critique_resurgence", year=2012,
         citation="Eve Tuck and K. Wayne Yang, \"Decolonization Is Not a Metaphor,\" Decolonization: Indigeneity, Education & Society 1, no. 1 (2012).",
         url="https://jps.library.utoronto.ca/index.php/des/article/view/18630", doi=None,
         verification=V(META, "Journal article page (University of Toronto Journal Production Services), published 8 Sept 2012",
                        "Title, authors, volume and issue checked; page range not shown on the page. Argument read only through Garba & Sorentino's 2020 abstract (settler–native–slave triad)."),
         evidence_key="tuck_yang_2012"),
    dict(id="coulthard_2014", section="indigenous_critique_resurgence", year=2014,
         citation="Glen Sean Coulthard, Red Skin, White Masks: Rejecting the Colonial Politics of Recognition (Minneapolis: University of Minnesota Press, 2014). Foreword by Taiaiake Alfred.",
         doi="10.5749/minnesota/9780816679645.001.0001", url="https://doi.org/10.5749/minnesota/9780816679645.001.0001",
         verification=V(META, "Crossref DOI record (lists Alfred alongside Coulthard; Alfred is the foreword author)", "Metadata only."),
         evidence_key="coulthard_2014"),
    dict(id="a_simpson_2014", section="indigenous_critique_resurgence", year=2014,
         citation="Audra Simpson, Mohawk Interruptus: Political Life Across the Borders of Settler States (Durham: Duke University Press, 2014).",
         doi="10.1215/9780822376781", url="https://doi.org/10.1215/9780822376781",
         verification=V(META, "Crossref DOI record", "Metadata only."), evidence_key="a_simpson_2014"),
    dict(id="kauanui_2016", section="indigenous_critique_resurgence", year=2016,
         citation="J. Kēhaulani Kauanui, \"'A Structure, Not an Event': Settler Colonialism and Enduring Indigeneity,\" Lateral 5, no. 1 (2016).",
         doi="10.25158/L5.1.7", url="https://doi.org/10.25158/L5.1.7",
         verification=V(PAGE, "Crossref DOI record with abstract",
                        "Abstract read: discusses the shift toward Wolfe's theory of settler colonialism as 'a structure, not an event'. Argues that engaging settler colonialism demands rethinking indigeneity, as distinct from race, ethnicity, culture and nation(ality), and Native American and Indigenous Studies."),
         evidence_key="kauanui_2016"),
    dict(id="l_simpson_2017", section="indigenous_critique_resurgence", year=2017,
         citation="Leanne Betasamosake Simpson, As We Have Always Done: Indigenous Freedom through Radical Resistance (Minneapolis: University of Minnesota Press, 2017).",
         doi="10.5749/j.ctt1pwt77c", url="https://doi.org/10.5749/j.ctt1pwt77c",
         verification=V(META, "Crossref DOI record", "Metadata only."), evidence_key="l_simpson_2017"),
    # ---- Canadian historiography
    dict(id="carter_1990", section="canadian_historiography", year=1990,
         citation="Sarah Carter, Lost Harvests: Prairie Indian Reserve Farmers and Government Policy (Montreal and Kingston: McGill-Queen's University Press, 1990).",
         doi="10.1515/9780773562431", url="https://doi.org/10.1515/9780773562431",
         verification=V(META, "Crossref DOI record (MQUP, 1990)", "Metadata only; predates the paradigm's naming."),
         evidence_key="carter_1990"),
    dict(id="harris_1997", section="canadian_historiography", year=1997,
         citation="Cole Harris, The Resettlement of British Columbia: Essays on Colonialism and Geographical Change (Vancouver: UBC Press, 1997).",
         url="https://www.ubcpress.ca/the-resettlement-of-british-columbia", doi=None,
         verification=V(META, "Existing atlas source ind127_harris_1997 (UBC Press page checked 2026-10-10)", "Reused atlas verification."),
         evidence_key="harris_1997"),
    dict(id="perry_2001", section="canadian_historiography", year=2001,
         citation="Adele Perry, On the Edge of Empire: Gender, Race, and the Making of British Columbia, 1849–1871 (Toronto: University of Toronto Press, 2001).",
         doi="10.3138/9781442688759", url="https://doi.org/10.3138/9781442688759",
         verification=V(META, "Crossref DOI record (UTP, 2001); introduction 'Analysing Gender and Race on the Edge of Empire', doi:10.3138/9781442688759-002",
                        "Metadata and chapter titles only."),
         evidence_key="perry_2001"),
    dict(id="harris_2002", section="canadian_historiography", year=2002,
         citation="Cole Harris, Making Native Space: Colonialism, Resistance, and Reserves in British Columbia (Vancouver: UBC Press, 2002).",
         url="https://www.ubcpress.ca/making-native-space", doi="10.59962/9780774850230",
         verification=V(META, "Open Library work record (UBC Press, 2002); Crossref DOI for UBC Press digital edition (2007); existing atlas source healthgeo05_harris_native_space_2002",
                        "Print 2002; the DOI dates a later digital edition."),
         evidence_key="harris_2002"),
    dict(id="razack_2002", section="canadian_historiography", year=2002,
         citation="Sherene H. Razack, ed., Race, Space, and the Law: Unmapping a White Settler Society (Toronto: Between the Lines, 2002).",
         url="https://openlibrary.org/works/OL599360W", doi=None,
         verification=V(META, "Open Library work record (Between the Lines, 2002); Perry's review, CHR 85:1 (2004), doi:10.1353/can.2004.0043",
                        "Metadata only."),
         evidence_key="razack_2002"),
    dict(id="harris_2004", section="canadian_historiography", year=2004,
         citation="Cole Harris, \"How Did Colonialism Dispossess? Comments from an Edge of Empire,\" Annals of the Association of American Geographers 94, no. 1 (2004): 165–182.",
         doi="10.1111/j.1467-8306.2004.09401009.x", url="https://doi.org/10.1111/j.1467-8306.2004.09401009.x",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: argues that an emphasis on culture in colonial-discourse studies obscures other colonial powers, and explains British Columbia's reserve system as geographical dispossession. The ability to dispossess rested on physical power and the state, its momentum on capital and settlers, and its legitimation on cultural discourse."),
         evidence_key="harris_2004"),
    dict(id="carter_2008", section="canadian_historiography", year=2008,
         citation="Sarah Carter, The Importance of Being Monogamous: Marriage and Nation Building in Western Canada to 1915 (Edmonton: University of Alberta Press / Athabasca University Press, 2008).",
         doi="10.15215/aupress/9780888644909.01", url="https://doi.org/10.15215/aupress/9780888644909.01",
         verification=V(META, "Crossref DOI record (Athabasca University Press, 2008)",
                        "Co-publication with University of Alberta Press is from the book's standard imprint and should be confirmed on the copy."),
         evidence_key="carter_2008"),
    dict(id="regan_2010", section="canadian_historiography", year=2010,
         citation="Paulette Regan, Unsettling the Settler Within: Indian Residential Schools, Truth Telling, and Reconciliation in Canada (Vancouver: UBC Press, 2010). Foreword by Taiaiake Alfred.",
         url="https://www.ubcpress.ca/unsettling-the-settler-within", doi="10.59962/9780774817790",
         verification=V(PAGE, "UBC Press page (EPUB 22 Dec 2010; paperback 25 Jan 2011; table of contents); Crossref DOI",
                        "Contents read: 'A Settler's Call to Action' and 'Deconstructing Canada's Peacemaker Myth'. Book unread."),
         evidence_key="regan_2010"),
    dict(id="daschuk_2013", section="canadian_historiography", year=2013,
         citation="James Daschuk, Clearing the Plains: Disease, Politics of Starvation, and the Loss of Aboriginal Life (Regina: University of Regina Press, 2013).",
         doi="10.1515/9780889772977", url="https://doi.org/10.1515/9780889772977",
         verification=V(META, "Crossref DOI record (University of Regina Press, 2013; new edition 2019, doi:10.1515/9780889776234)",
                        "Metadata only. Whether Daschuk frames his argument as settler colonialism is not checked."),
         evidence_key="daschuk_2013"),
    dict(id="battell_lowman_barker_2015", section="canadian_historiography", year=2015,
         citation="Emma Battell Lowman and Adam J. Barker, Settler: Identity and Colonialism in 21st Century Canada (Halifax and Winnipeg: Fernwood, 2015).",
         url="https://archives.whyte.org/en/permalink/catalogue25063", doi=None,
         verification=V(META, "Whyte Museum library catalogue record (Fernwood, 2015; xii, 145 pp.; ISBN 9781552667781)",
                        "Catalogue author order is Battell Lowman, Barker; the citation graph indexes it under both."),
         evidence_key="barker_battell_lowman_2015"),
    dict(id="burrill_2019", section="canadian_historiography", year=2019,
         citation="Fred Burrill, \"The Settler Order Framework: Rethinking Canadian Working-Class History,\" Labour/Le Travail 83 (2019): 173–197.",
         doi="10.1353/llt.2019.0007", url="https://doi.org/10.1353/llt.2019.0007",
         verification=V(PAGE, "Crossref DOI record with abstract",
                        "Abstract read: proposes a 'settler order framework' that puts the relationship between colonial and class exploitation, including settler workers' ongoing theft of Indigenous land, into Canadian working-class history. Author name Fred Burrill confirmed in Crossref and OpenAlex."),
         evidence_key="burrill_2019"),
    dict(id="harris_2020", section="canadian_historiography", year=2020,
         citation="Cole Harris, A Bounded Land: Reflections on Settler Colonialism in Canada (Vancouver: UBC Press, 2020).",
         doi="10.59962/9780774864435", url="https://doi.org/10.59962/9780774864435",
         verification=V(META, "Crossref DOI record with chapter list",
                        "Contents include 'How Did Colonialism Dispossess?' and 'Postscript: The Boundaries of Settler Colonialism' (doi:10.59962/9780774864435-017). Body unread."),
         evidence_key="harris_2020"),
    # ---- comparative and adjacent
    dict(id="mamdani_2001", section="comparative_adjacent", year=2001,
         citation="Mahmood Mamdani, \"Beyond Settler and Native as Political Identities: Overcoming the Political Legacy of Colonialism,\" Comparative Studies in Society and History 43, no. 4 (2001): 651–664.",
         doi="10.1017/S0010417501004285", url="https://www.cambridge.org/core/journals/comparative-studies-in-society-and-history/article/beyond-settler-and-native-as-political-identities-overcoming-the-political-legacy-of-colonialism/A1919DC1C4418B5229BBE876C18BFCFB",
         verification=V(PAGE, "Cambridge Core article page (vol. 43, no. 4, pp. 651–664, Oct 2001); OpenAlex opening text",
                        "Opening read: the first postcolonial generation in Africa saw colonialism's impact as mainly economic (citing Rodney), while no one wrote of how Europe ruled. Crossref did not resolve the DOI on 2026-10-12; Cambridge lists it."),
         evidence_key="mamdani_2001"),
    dict(id="belich_2009", section="comparative_adjacent", year=2009,
         citation="James Belich, Replenishing the Earth: The Settler Revolution and the Rise of the Anglo-World, 1783–1939 (Oxford: Oxford University Press, 2009).",
         url="https://openlibrary.org/works/OL2511646W", doi=None,
         verification=V(META, "Open Library work record (OUP, 2009; ISBN 9780199297276); Oxford Scholarship chapters e.g. doi:10.1093/acprof:oso/9780199297276.003.0004",
                        "Comparison only: settler expansion history, not necessarily settler-colonial theory."),
         evidence_key="belich_2009"),
    dict(id="jacobs_2009", section="comparative_adjacent", year=2009,
         citation="Margaret D. Jacobs, White Mother to a Dark Race: Settler Colonialism, Maternalism, and the Removal of Indigenous Children in the American West and Australia, 1880–1940 (Lincoln: University of Nebraska Press, 2009).",
         url="https://openlibrary.org/works/OL1924162W", doi=None,
         verification=V(META, "Open Library work record (University of Nebraska Press, 2009; ISBN 9780803211001)", "Metadata only."),
         evidence_key="jacobs_2009"),
    dict(id="ford_2010", section="comparative_adjacent", year=2010,
         citation="Lisa Ford, Settler Sovereignty: Jurisdiction and Indigenous People in America and Australia, 1788–1836 (Cambridge, MA: Harvard University Press, 2010).",
         doi="10.2307/j.ctv1smjszh", url="https://doi.org/10.2307/j.ctv1smjszh",
         verification=V(META, "Crossref DOI record (Harvard University Press, 2010)", "Metadata and chapter titles only."),
         evidence_key="ford_2010"),
    dict(id="mamdani_2020", section="comparative_adjacent", year=2020,
         citation="Mahmood Mamdani, Neither Settler nor Native: The Making and Unmaking of Permanent Minorities (Cambridge, MA: Harvard University Press, 2020).",
         doi="10.4159/9780674249998", url="https://doi.org/10.4159/9780674249998",
         verification=V(META, "Crossref DOI record; Open Library work record", "Metadata only."), evidence_key="mamdani_2020"),
    dict(id="cote_2019", section="comparative_adjacent", year=2019,
         citation="Isabelle Côté, \"Théorie postcoloniale, décolonisation et colonialisme de peuplement : quelques repères pour la recherche en français au Canada,\" Cahiers franco-canadiens de l'Ouest 31, no. 1 (2019): 25–42.",
         doi="10.7202/1059124ar", url="https://doi.org/10.7202/1059124ar",
         verification=V(PAGE, "Crossref search hit; OpenAlex record with abstract (Érudit page blocked automated access)",
                        "Abstract read: concerns integrating Indigenous perspectives into French-language teacher education in British Columbia. Francophone minorities are in a dual position, as colonised and as non-Indigenous occupants. An education article, not historical research; it is the one French-language 'colonialisme de peuplement' title cited by more than one PhD (Montréal, UQAM)."),
         evidence_key="cote_2019"),
    # ---- critiques and reassessments
    dict(id="macoun_strakosch_2013", section="critiques", year=2013,
         citation="Alissa Macoun and Elizabeth Strakosch, \"The Ethical Demands of Settler Colonial Theory,\" Settler Colonial Studies 3, nos. 3–4 (2013): 426–443.",
         doi="10.1080/2201473X.2013.810695", url="https://doi.org/10.1080/2201473X.2013.810695",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: the theory is useful for showing that colonialism is not a transcended national past and for making settler investments visible. But it 'posits a structural inevitability' that settler scholars can use to delegitimize Indigenous resistance. Settlers 'come to stay', yet their intentions need not be realized."),
         evidence_key="macoun_strakosch_2013"),
    dict(id="rowse_2014", section="critiques", year=2014,
         citation="Tim Rowse, \"Indigenous Heterogeneity,\" Australian Historical Studies 45, no. 3 (2014): 297–310.",
         doi="10.1080/1031461X.2014.946523", url="https://doi.org/10.1080/1031461X.2014.946523",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: criticises emplotting Australian colonial history as a 'teleology of elimination' that inhibits characterising diverse Indigeneities; proposes regional (North/South) and other schemata. Not cited in the PhD corpus."),
         evidence_key=None),
    dict(id="snelgrove_dhamoon_corntassel_2014", section="critiques", year=2014,
         citation="Corey Snelgrove, Rita Kaur Dhamoon and Jeff Corntassel, \"Unsettling Settler Colonialism: The Discourse and Politics of Settlers, and Solidarity with Indigenous Nations,\" Decolonization: Indigeneity, Education & Society 3, no. 2 (2014): 1–32.",
         url="https://jps.library.utoronto.ca/index.php/des/article/view/21166", doi=None,
         verification=V(META, "Journal article page (vol. 3, no. 2, published 29 Sept 2014)",
                        "Title, authors and issue checked on the journal page. The page range 1–32 and the argument come from a web-search summary of the UVic repository record: without centring Indigenous articulations and a relational, contingent view of settler colonial power, studies risk reifying settler colonial domination. Treat the argument as a lead to confirm."),
         evidence_key="snelgrove_dhamoon_corntassel_2014"),
    dict(id="sexton_2016", section="critiques", year=2016,
         citation="Jared Sexton, \"The Vel of Slavery: Tracking the Figure of the Unsovereign,\" Critical Sociology 42, nos. 4–5 (2016): 583–597.",
         doi="10.1177/0896920514552535", url="https://doi.org/10.1177/0896920514552535",
         verification=V(PAGE, "Crossref DOI record with abstract (online 2014; print volume 2016)",
                        "Abstract read: the logic of decolonization movements against settler states overlaps contemporary post-racialism in ways that circumvent Black radicalism; the abolition of slavery unsettles colonial and decolonial sovereignty. Not cited in the PhD corpus."),
         evidence_key=None),
    dict(id="greer_2019_wmq", section="critiques", year=2019,
         citation="Allan Greer, \"Settler Colonialism and Empire in Early America,\" William and Mary Quarterly 76, no. 3 (2019): 383–390.",
         doi="10.5309/willmaryquar.76.3.0383", url="https://doi.org/10.5309/willmaryquar.76.3.0383",
         verification=V(META, "Crossref DOI record; OpenAlex opening text",
                        "Opening read (Australia from 1788 under modern conceptions of territory and property). The full argument is unread; the page range is from the forum's pagination and should be confirmed."),
         evidence_key="greer_2019_wmq"),
    dict(id="greer_2019_jcha", section="critiques", year=2019,
         citation="Allan Greer, \"Settler Colonialism and Beyond,\" Journal of the Canadian Historical Association / Revue de la Société historique du Canada 30, no. 1 (2019): 61–86.",
         doi="10.7202/1070631ar", url="https://doi.org/10.7202/1070631ar",
         verification=V(PAGE, "Crossref DOI record with abstract (Érudit; online 20 July 2020)",
                        "Abstract read: the settler approach has much to offer, but across 500 years of invading Indigenous North America the settler variety dominates some periods and regions and fades in others. 'Imperial/Commercial Penetration' and 'Extractivism' are other modes; extractivism has become predominant in recent decades."),
         evidence_key="greer_2019_jcha"),
    dict(id="ostler_shoemaker_2019", section="critiques", year=2019,
         citation="Jeffrey Ostler and Nancy Shoemaker, \"Settler Colonialism in Early American History: Introduction,\" William and Mary Quarterly 76, no. 3 (2019): 361–368.",
         doi="10.5309/willmaryquar.76.3.0361", url="https://doi.org/10.5309/willmaryquar.76.3.0361",
         verification=V(META, "Crossref DOI record; OpenAlex description",
                        "The forum includes Glassburn, Greer, Miles, Ostler, Romney, Shoemaker, Smallwood, Spear, Truett and Witgen. The end page is to confirm."),
         evidence_key="ostler_shoemaker_2019"),
    dict(id="shoemaker_2019", section="critiques", year=2019,
         citation="Nancy Shoemaker, \"Settler Colonialism: Universal Theory or English Heritage?\" William and Mary Quarterly 76, no. 3 (2019): 369–374.",
         doi="10.5309/willmaryquar.76.3.0369", url="https://doi.org/10.5309/willmaryquar.76.3.0369",
         verification=V(PAGE, "Crossref DOI record; OpenAlex opening text",
                        "Opening read: if settler colonialism is a universal theory, why do studies concentrate on former British colonies in the nineteenth and twentieth centuries? She proposes testing it as an early modern English ideology of expansion. The end page is to confirm."),
         evidence_key="shoemaker_2019"),
    dict(id="konishi_2019", section="critiques", year=2019,
         citation="Shino Konishi, \"First Nations Scholars, Settler Colonial Studies, and Indigenous History,\" Australian Historical Studies 50, no. 3 (2019): 285–304.",
         doi="10.1080/1031461X.2019.1620300", url="https://doi.org/10.1080/1031461X.2019.1620300",
         verification=V(PAGE, "Crossref DOI record; OpenAlex abstract",
                        "Abstract read: explores how Indigenous scholars advocate, interrogate, critique or challenge settler colonial studies as an emerging field. Concludes with Indigenous-authored 'extra-colonial' histories that bypass colonial expropriation to focus on Indigenous worlds. Not cited in the PhD corpus."),
         evidence_key=None),
    dict(id="king_2019", section="critiques", year=2019,
         citation="Tiffany Lethabo King, The Black Shoals: Offshore Formations of Black and Native Studies (Durham: Duke University Press, 2019).",
         doi="10.1215/9781478005681", url="https://doi.org/10.1215/9781478005681",
         verification=V(META, "Crossref DOI record", "Metadata only; the argument is not checked."), evidence_key="king_2019"),
    dict(id="garba_sorentino_2020", section="critiques", year=2020,
         citation="Tapji Garba and Sara-Maria Sorentino, \"Slavery Is a Metaphor: A Critical Commentary on Eve Tuck and K. Wayne Yang's 'Decolonization Is Not a Metaphor',\" Antipode 52, no. 3 (2020): 764–782.",
         doi="10.1111/anti.12615", url="https://doi.org/10.1111/anti.12615",
         verification=V(PAGE, "Crossref DOI record with abstract",
                        "Abstract read: argues Tuck and Yang's critique of metaphor collapses a settler–native–slave triad into a settler–native dyad and reduces slavery to forced labour; offers an alternative theorisation from Black studies. Not cited in the PhD corpus."),
         evidence_key=None),
]

for r in LIT:
    k = r.get("evidence_key")
    if k and k in counts:
        c = counts[k]
        r["dissertations"] = {"phds_2009_2026": c["phds_2009_2026"], "of": ev["corpus"]["analysis_dissertations"],
                              "universities_2009_2026": c["universities_2009_2026"],
                              "first_citing_year": c["first_citing_year"], "phds_all_years": c["phds_all_years"]}
    elif k is None and "evidence_key" in r:
        pass
    r.setdefault("dissertations", None)

literature = {
    "status": "proposal_for_review",
    "prepared": CHECKED,
    "verification_vocabulary": "Same as GRAPH-FORMAT.md: bibliographic_metadata_checked = identity/edition checked; "
                               "supporting_page_checked = an abstract, contents page or opening text was read for the "
                               "specific point in the note; unverified = do not cite yet. No book was read in full.",
    "sections": {
        "origins_precursors": "Earlier settler-society and settler-capitalism scholarship, and the first uses of the name in the 1990s and 2000s.",
        "theory": "Works that name settler colonialism and theorise it as a distinct formation, or programme it as a field.",
        "indigenous_critique_resurgence": "Indigenous political theory and critique read alongside the paradigm. Several also critique it.",
        "canadian_historiography": "Canadian historical writing on dispossession, reserves, gender, health, labour and settler identity. Some of it predates the paradigm or does not adopt it.",
        "comparative_adjacent": "Comparative and adjacent works the PhD data place nearby.",
        "critiques": "Published critiques and reassessments of the paradigm.",
    },
    "records": LIT,
    "counts": {"records": len(LIT), "unverified": sum(1 for r in LIT if r["verification"]["status"] == "unverified"),
               "supporting_page_checked": sum(1 for r in LIT if r["verification"]["status"] == PAGE),
               "bibliographic_metadata_checked": sum(1 for r in LIT if r["verification"]["status"] == META)},
}
json.dump(literature, open(OUT / "literature.json", "w"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- entry draft
def src(i):
    return f"screq_{i}"


DESCRIPTION = (
    "Historical inquiry into colonial formations in which newcomers came to stay, acquired land and claimed "
    "sovereignty over Indigenous territories. Patrick Wolfe's account of settler colonialism as a structure rather "
    "than an event treats invasion as a continuing relation rather than a completed frontier past. Lorenzo "
    "Veracini's work and the journal Settler Colonial Studies (2011) distinguished settler colonial from colonial "
    "phenomena. Comparative studies of settler capitalism and settler societies, and decolonization-era uses of the "
    "term, came earlier. In Canadian historical writing the framework meets an older historiography of dispossession, "
    "reserves, gender and the state in the West and British Columbia. It also meets Indigenous political theory of "
    "recognition, sovereignty and resurgence. Its uses extend to labour, science, memory and settler identity. "
    "The field is contested from several directions. Indigenous scholars ask whether it recentres settlers and "
    "displaces Indigenous studies and Indigenous-authored histories. Historians question its structural inevitability "
    "and its fit across regions and periods, proposing other modes such as commercial penetration and extractivism. "
    "Black studies scholars question how it places slavery. Settler colonialism overlaps with Indigenous history, "
    "postcolonial critique and historical geography without being equivalent to any of them."
)

PEOPLE = [
    # person_id, label, new?, role, context, works, lit ids, graph qid
    ("patrick_wolfe", "Patrick Wolfe", False, "contributor",
     "Formulates settler colonialism as a continuing structure of dispossession; the 'structure, not an event' "
     "phrasing is attested through Kauanui's abstract. Already a comparison participant in Indigenous history.",
     "Settler Colonialism and the Transformation of Anthropology (1999); “Settler Colonialism and the Elimination of the Native” (2006)",
     ["wolfe_1999", "wolfe_2006", "kauanui_2016"], "Q109284663"),
    ("lorenzo_veracini", "Lorenzo Veracini", True, "contributor",
     "Distinguishes settler colonial from colonial phenomena and introduces Settler Colonial Studies (2011); traces "
     "the concept's earlier career.",
     "Settler Colonialism: A Theoretical Overview (2010); “Introducing: Settler Colonial Studies” (2011); “‘Settler Colonialism’: Career of a Concept” (2013)",
     ["veracini_2010", "veracini_2011", "veracini_2013"], "Q112150999"),
    ("caroline_elkins", "Caroline Elkins", True, "contributor",
     "Coeditor of a comparative twentieth-century collection; volume contents unread.",
     "Settler Colonialism in the Twentieth Century (2005), ed. with Susan Pedersen", ["elkins_pedersen_2005"], "Q2030286"),
    ("susan_pedersen", "Susan Pedersen", True, "contributor",
     "Coeditor of the same collection; editorial credit only.",
     "Settler Colonialism in the Twentieth Century (2005), ed. with Caroline Elkins", ["elkins_pedersen_2005"], "Q64711854"),
    ("glen_coulthard", "Glen Sean Coulthard", True, "contributor",
     "Indigenous political theory rejecting the colonial politics of recognition; contributes to, rather than "
     "belongs to, settler-colonial studies. Metadata-level only.",
     "Red Skin, White Masks (2014)", ["coulthard_2014"], "Q91710018"),
    ("audra_simpson", "Audra Simpson", True, "contributor",
     "Mohawk political life across the borders of settler states; metadata-level only.",
     "Mohawk Interruptus (2014)", ["a_simpson_2014"], "Q112536616"),
    ("leanne_betasamosake_simpson", "Leanne Betasamosake Simpson", True, "contributor",
     "Nishnaabeg resurgence and radical resistance; metadata-level only.",
     "Dancing on Our Turtle's Back (2011); As We Have Always Done (2017)", ["l_simpson_2011", "l_simpson_2017"], "Q22957997"),
    ("eve_tuck", "Eve Tuck", True, "contributor",
     "Coauthor of a widely cited argument against metaphorical uses of decolonization; argument read only through a "
     "critic's abstract.", "With K. Wayne Yang, “Decolonization Is Not a Metaphor” (2012)", ["tuck_yang_2012", "garba_sorentino_2020"], "Q28924966"),
    ("k_wayne_yang", "K. Wayne Yang", True, "contributor", "Coauthor; see Eve Tuck.",
     "With Eve Tuck, “Decolonization Is Not a Metaphor” (2012)", ["tuck_yang_2012"], None),
    ("jodi_a_byrd", "Jodi A. Byrd", True, "contributor", "Indigenous critiques of colonialism; metadata-level only.",
     "The Transit of Empire (2011)", ["byrd_2011"], "Q57242581"),
    ("j_kehaulani_kauanui", "J. Kēhaulani Kauanui", True, "critic",
     "Argues that engagement with Wolfe's structure thesis demands rethinking indigeneity and Native American and "
     "Indigenous Studies; a critical interlocutor rather than an adherent.",
     "“‘A Structure, Not an Event’” (2016)", ["kauanui_2016"], None),
    ("cole_harris", "Cole Harris", False, "historian",
     "Explains British Columbia's reserve system as geographical dispossession and later reflects on the boundaries "
     "of settler colonialism. Preserves his existing historical-geography and Indigenous-history profiles.",
     "Making Native Space (2002); “How Did Colonialism Dispossess?” (2004); A Bounded Land (2020)",
     ["harris_2002", "harris_2004", "harris_2020"], "Q5142660"),
    ("sarah_carter", "Sarah Carter", True, "historian",
     "Prairie reserve agriculture, government policy, marriage and nation-building; this work predates or runs "
     "beside the paradigm and is not assigned to it.",
     "Lost Harvests (1990); The Importance of Being Monogamous (2008)", ["carter_1990", "carter_2008"], "Q97628356"),
    ("adele_perry", "Adele Perry", True, "historian",
     "Gender, race and colonial British Columbia; metadata and chapter titles only.",
     "On the Edge of Empire (2001)", ["perry_2001"], "Q64626780"),
    ("james_daschuk", "James Daschuk", True, "comparison",
     "Disease, starvation policy and the loss of Indigenous life on the Plains; strongly co-cited with Wolfe and "
     "Veracini, but whether the book uses the framework is unchecked.",
     "Clearing the Plains (2013)", ["daschuk_2013"], "Q112485461"),
    ("emma_battell_lowman", "Emma Battell Lowman", True, "contributor",
     "Settler identity in contemporary Canada; catalogue-level only.",
     "With Adam J. Barker, Settler: Identity and Colonialism in 21st Century Canada (2015)", ["battell_lowman_barker_2015"], None),
    ("adam_j_barker", "Adam J. Barker", True, "contributor", "Coauthor; see Emma Battell Lowman.",
     "With Emma Battell Lowman, Settler (2015)", ["battell_lowman_barker_2015"], "Q117081597"),
    ("paulette_regan", "Paulette Regan", True, "contributor",
     "Residential schools, truth telling and the 'peacemaker myth'; contents page only.",
     "Unsettling the Settler Within (2010)", ["regan_2010"], "Q122819024"),
    ("sherene_razack", "Sherene H. Razack", True, "contributor",
     "Editor of a collection unmapping a white settler society; metadata-level only.",
     "Race, Space, and the Law (2002), ed.", ["razack_2002"], "Q21152487"),
    ("fred_burrill", "Fred Burrill", True, "historian",
     "Proposes a settler order framework for Canadian working-class history.",
     "“The Settler Order Framework” (2019)", ["burrill_2019"], None),
    ("mahmood_mamdani", "Mahmood Mamdani", True, "comparison",
     "Settler and native as political identities in African and comparative contexts.",
     "“Beyond Settler and Native as Political Identities” (2001); Neither Settler nor Native (2020)",
     ["mamdani_2001", "mamdani_2020"], "Q723502"),
    ("donald_denoon", "Donald Denoon", True, "precursor",
     "Earlier comparative study of settler capitalism; title-level only.", "Settler Capitalism (1983)", ["denoon_1983"], None),
    ("daiva_stasiulis", "Daiva Stasiulis", True, "precursor",
     "Coeditor of an earlier settler-societies collection on gender, race, ethnicity and class.",
     "Unsettling Settler Societies (1995), ed. with Nira Yuval-Davis", ["stasiulis_yuval_davis_1995"], None),
    ("nira_yuval_davis", "Nira Yuval-Davis", False, "precursor",
     "Coeditor of the same collection; her existing gender and nationalism contexts are preserved.",
     "Unsettling Settler Societies (1995), ed. with Daiva Stasiulis", ["stasiulis_yuval_davis_1995"], None),
    ("allan_greer", "Allan Greer", True, "critic",
     "Holds that settler colonialism dominates some periods and regions of northern North America and fades in "
     "others; proposes imperial/commercial penetration and extractivism as further modes.",
     "“Settler Colonialism and Beyond” (2019); “Settler Colonialism and Empire in Early America” (2019)",
     ["greer_2019_jcha", "greer_2019_wmq"], "Q2837703"),
    ("nancy_shoemaker", "Nancy Shoemaker", True, "critic",
     "Asks whether the theory is universal or an English heritage, and proposes testing it on early modern origins.",
     "“Settler Colonialism: Universal Theory or English Heritage?” (2019)", ["shoemaker_2019", "ostler_shoemaker_2019"], None),
    ("tim_rowse", "Tim Rowse", True, "critic",
     "Criticises a teleology of elimination that obscures diverse Indigeneities in Australian history.",
     "“Indigenous Heterogeneity” (2014)", ["rowse_2014"], None),
    ("shino_konishi", "Shino Konishi", True, "critic",
     "Surveys how Indigenous scholars advocate, interrogate and challenge settler colonial studies; advocates "
     "extra-colonial Indigenous-authored histories. Roster inclusion is not an identity classification.",
     "“First Nations Scholars, Settler Colonial Studies, and Indigenous History” (2019)", ["konishi_2019"], None),
    ("alissa_macoun", "Alissa Macoun", True, "critic",
     "Coauthor of a critique of the theory's structural inevitability, written from within the theory.",
     "With Elizabeth Strakosch, “The Ethical Demands of Settler Colonial Theory” (2013)", ["macoun_strakosch_2013"], None),
    ("elizabeth_strakosch", "Elizabeth Strakosch", True, "critic", "Coauthor; see Alissa Macoun.",
     "With Alissa Macoun (2013)", ["macoun_strakosch_2013"], None),
    ("tapji_garba", "Tapji Garba", True, "critic",
     "Coauthor of a Black-studies critique of Tuck and Yang's settler–native–slave triad.",
     "With Sara-Maria Sorentino, “Slavery Is a Metaphor” (2020)", ["garba_sorentino_2020"], None),
    ("sara_maria_sorentino", "Sara-Maria Sorentino", True, "critic", "Coauthor; see Tapji Garba.",
     "With Tapji Garba (2020)", ["garba_sorentino_2020"], None),
    ("jared_sexton", "Jared Sexton", True, "critic",
     "Argues that decolonial sovereignty claims can circumvent Black radicalism and the abolition of slavery.",
     "“The Vel of Slavery” (2016)", ["sexton_2016"], None),
]

rep_people = [{"person_id": pid, "role": role, "context": ctx, "works": works,
               "source_ids": [src(x) for x in lits], "basis": "source_review", "review_status": "needs_review"}
              for pid, label, new, role, ctx, works, lits, qid in PEOPLE]
new_people = [{"id": pid, "label": label,
               "citation_graph_qid": qid,
               "qid_note": "From the citation graph's tiered Wikidata grounding; not reviewed for the atlas." if qid else None}
              for pid, label, new, role, ctx, works, lits, qid in PEOPLE if new]

STRANDS = [
    ("structure_and_elimination", "Structure, not event",
     "Wolfe's account treats invasion and elimination as a continuing structure. Kauanui's abstract attests the "
     "formulation and its critique; Wolfe's own pages are not checked here.",
     ["patrick_wolfe", "j_kehaulani_kauanui"], ["wolfe_1999", "wolfe_2001", "wolfe_2006", "kauanui_2016"]),
    ("theory_and_field", "Settler colonial theory and field formation",
     "Veracini disentangles settler colonial from colonial phenomena and introduces a dedicated journal (2011); "
     "a 2013 essay traces the concept's earlier career. Field-making, not a claim of single origin.",
     ["lorenzo_veracini"], ["veracini_2008", "veracini_2010", "veracini_2011", "veracini_2013", "cavanagh_veracini_2017"]),
    ("earlier_settler_societies", "Settler capitalism and settler societies in comparison",
     "Comparative settler economies (1983) and gender, race, ethnicity and class in settler societies (1995) are earlier "
     "comparative scholarship, before the field's theoretical consolidation; Veracini's history of the concept records "
     "decolonization-era usage of the term itself.",
     ["donald_denoon", "daiva_stasiulis", "nira_yuval_davis"], ["denoon_1983", "stasiulis_yuval_davis_1995", "veracini_2013"]),
    ("comparative_twentieth_century", "Comparative and twentieth-century settler colonies",
     "Comparative collections and studies beyond the British settler dominions, including African settler and native "
     "political identities.",
     ["caroline_elkins", "susan_pedersen", "mahmood_mamdani"], ["elkins_pedersen_2005", "mamdani_2001", "mamdani_2020"]),
    ("recognition_refusal_resurgence", "Indigenous critiques of recognition, sovereignty and resurgence",
     "Indigenous political theory read alongside the paradigm. These works have their own genealogies in Indigenous "
     "thought and are not a subset of settler-colonial studies. Open question: these may belong in Indigenous history "
     "instead.",
     ["glen_coulthard", "audra_simpson", "leanne_betasamosake_simpson", "jodi_a_byrd", "eve_tuck", "k_wayne_yang"],
     ["coulthard_2014", "a_simpson_2014", "l_simpson_2011", "l_simpson_2017", "byrd_2011", "tuck_yang_2012"]),
    ("dispossession_reserves_geography", "Dispossession, reserves and colonial geography in Canada",
     "Harris explains reserve-making as geographical dispossession, backed by state power, capital and settlers, and "
     "later reflects on the framework's boundaries. Carter's prairie reserve agriculture predates the paradigm.",
     ["cole_harris", "sarah_carter"], ["harris_1997", "harris_2002", "harris_2004", "harris_2020", "carter_1990"]),
    ("gender_family_nation", "Gender, family and colonial nation-making",
     "Gender, race, marriage and child removal in colonial British Columbia, the Prairie West, the American West and "
     "Australia. Metadata level only.",
     ["adele_perry", "sarah_carter"], ["perry_2001", "carter_2008", "jacobs_2009"]),
    ("settler_identity_reconciliation", "Settler identity, truth telling and reconciliation",
     "Settler self-examination after residential schools and in contemporary Canada; Regan's contents page names the "
     "'peacemaker myth'.",
     ["paulette_regan", "emma_battell_lowman", "adam_j_barker", "sherene_razack"],
     ["regan_2010", "battell_lowman_barker_2015", "razack_2002"]),
    ("health_starvation", "Health, starvation and state policy",
     "Co-citation places Daschuk's Plains history next to Wolfe and Veracini (19 of 58 Wolfe/Veracini-citing PhDs). "
     "Its own framing is unchecked, so this is a comparison strand.",
     ["james_daschuk"], ["daschuk_2013"]),
    ("labour_settler_order", "Labour and the settler order",
     "Integrates settler workers' ongoing appropriation of Indigenous land into Canadian working-class history.",
     ["fred_burrill"], ["burrill_2019"]),
    ("critiques_and_limits", "Critiques: structure, region and period",
     "Structural inevitability (Macoun and Strakosch), a teleology of elimination (Rowse), regional and periodic fit "
     "with other modes of colonialism (Greer), universal theory or English heritage (Shoemaker).",
     ["alissa_macoun", "elizabeth_strakosch", "tim_rowse", "allan_greer", "nancy_shoemaker"],
     ["macoun_strakosch_2013", "rowse_2014", "greer_2019_jcha", "greer_2019_wmq", "shoemaker_2019", "ostler_shoemaker_2019"]),
    ("indigenous_scholars_critique", "Indigenous scholars on settler colonial studies",
     "Whether the field recentres settlers and displaces Indigenous studies and Indigenous-authored histories.",
     ["shino_konishi", "j_kehaulani_kauanui"], ["konishi_2019", "kauanui_2016", "snelgrove_dhamoon_corntassel_2014"]),
    ("slavery_black_studies", "Slavery and Black studies critiques",
     "How settler-colonial and decolonial frameworks place slavery and Black people.",
     ["tapji_garba", "sara_maria_sorentino", "jared_sexton"], ["garba_sorentino_2020", "sexton_2016", "king_2019"]),
]
strands = [{"id": sid, "title": t, "focus": f, "person_ids": pids, "source_ids": [src(x) for x in lits],
            "works": "; ".join(next(r["citation"] for r in LIT if r["id"] == x) for x in lits),
            "basis": "editorial_distinction", "review_status": "needs_review"} for sid, t, f, pids, lits in STRANDS]

# Proposed relationships. Exact existing atlas ids; vocabulary per GRAPH-FORMAT.md.
fields = {r["field"]: r for r in ev["neighbourhood"]["field_engagement_core_vs_all"]}


def lift(name):
    r = fields[name]
    return (f"PhD context: {r['core_citing_phds_engaging']} of {r['core_citing_phds']} core-citing 2009–2026 PhDs "
            f"also engage the '{name}' co-citation field ({r['share_core']:.0%} vs {r['share_all']:.0%} of all; "
            f"lift {r['lift']}). Bibliographies record consultation, not influence.")


RELS = [
    dict(source="indigenous", target="settler_colonialism", relationship_kind="comparison", directed=False,
         relationship="Indigenous historical authority and settler-colonial analysis",
         map_label="Indigenous history and settler colonialism",
         evidence_note="Konishi surveys Indigenous scholars who advocate, interrogate and challenge settler colonial "
                       "studies. Kauanui asks that it rethink indigeneity. Comparison only: Indigenous history is not a "
                       "subset of the paradigm, and the paradigm did not originate there. " + lift("Indigenous peoples, fur trade & the West"),
         sources=["konishi_2019", "kauanui_2016"], strength="abstract_checked"),
    dict(source="indigenous", target="settler_colonialism", relationship_kind="critique", directed=True,
         relationship="Indigenous scholars question a settler-centred field",
         map_label="Indigenous critiques of settler colonial studies",
         evidence_note="Konishi: Indigenous scholars critique or challenge the field and offer extra-colonial histories. "
                       "Kauanui: engagement with the structure thesis must rethink indigeneity and Indigenous Studies. "
                       "A specific critique alongside the broad comparison; it records no identity classification.",
         sources=["konishi_2019", "kauanui_2016", "snelgrove_dhamoon_corntassel_2014"], strength="abstract_checked"),
    dict(source="post", target="settler_colonialism", relationship_kind="comparison", directed=False,
         relationship="Colonial and settler colonial phenomena distinguished",
         map_label="Postcolonial critique and settler colonialism",
         evidence_note="Veracini argues that colonial and settler colonial phenomena must be analytically disentangled "
                       "and read in dialectical relation. Hoxie presents settler colonialism as the most promising "
                       "aspect of a postcolonial critique. Alternative for review: a directed contribution post → "
                       "settler_colonialism on Hoxie's account. " + lift("Empire, colonialism & postcolonial theory"),
         sources=["veracini_2011", "hoxie_2008"], strength="abstract_checked"),
    dict(source="settler_colonialism", target="nationaltradition", relationship_kind="critique", directed=True,
         relationship="Challenges settler national narratives of empty land and peaceful settlement",
         map_label="Critique of settler national narratives",
         evidence_note="Veracini's history of the concept describes earlier writing that placed pioneering in 'empty' "
                       "settings and disavowed Indigenous presence. Regan's contents page names 'Deconstructing Canada's "
                       "Peacemaker Myth'. Targets settler national narratives, not every national history.",
         sources=["veracini_2013", "regan_2010"], strength="abstract_and_contents_checked"),
    dict(source="anticolonial", target="settler_colonialism", relationship_kind="comparison", directed=False,
         relationship="Decolonization-era usage and later theory",
         map_label="Anti-colonial usage of 'settler colonialism'",
         evidence_note="Veracini dates a usage, until the late 1970s, naming a diehard hyper-colonialism challenged by "
                       "anti-colonial insurgencies. Mamdani revisits the first postcolonial generation's political "
                       "economy (Rodney) to ask how settler and native became political identities. Comparison: no "
                       "line of descent from liberation politics to the later field is asserted.",
         sources=["veracini_2013", "mamdani_2001"], strength="abstract_checked"),
    dict(source="spatialhistory", target="settler_colonialism", relationship_kind="contribution", directed=True,
         relationship="Harris: dispossession explained geographically",
         map_label="Harris: how colonialism dispossessed",
         evidence_note="Harris explains British Columbia's reserve system as geographical dispossession resting on state "
                       "power, capital and settlers, rather than primarily on discourse. He later reflects on the "
                       "boundaries of settler colonialism (postscript title). It keeps the existing spatial–Indigenous "
                       "comparison edge_777 separate. " + lift("Environment, development & the state"),
         sources=["harris_2004", "harris_2020"], strength="abstract_checked"),
    dict(source="settler_colonialism", target="cdn_working_class", relationship_kind="contribution", directed=True,
         relationship="A settler order framework for Canadian working-class history",
         map_label="Burrill: settler order framework",
         evidence_note="Burrill proposes integrating settler workers' ongoing theft of Indigenous land into the story of "
                       "the Canadian working class. One specific intervention; labour historians are not assumed to have "
                       "adopted it. " + lift("Labour & the working class"),
         sources=["burrill_2019"], strength="abstract_checked"),
    dict(source="africanhist", target="settler_colonialism", relationship_kind="comparison", directed=False,
         relationship="Settler and native as political identities in Africa",
         map_label="African settler colonies and political identity",
         evidence_note="Mamdani analyses settler and native as colonial political identities from African history. "
                       "Elkins and Pedersen's comparative volume (contents unread) is a second witness. Comparison only.",
         sources=["mamdani_2001", "elkins_pedersen_2005"], strength="abstract_checked"),
    dict(source="black", target="settler_colonialism", relationship_kind="critique", directed=True,
         relationship="Slavery and Black studies critiques of settler–native frameworks",
         map_label="Black studies critique",
         evidence_note="Garba and Sorentino argue that Tuck and Yang collapse a settler–native–slave triad. Sexton argues "
                       "that decolonial sovereignty claims can circumvent Black radicalism. These are Black studies "
                       "theory rather than Black history as the atlas entry defines it; the source node is a review "
                       "decision.",
         sources=["garba_sorentino_2020", "sexton_2016"], strength="abstract_checked_source_node_uncertain",
         deferred="Sol review 2026-10-12: the atlas's black entry is a historical field, not Black studies theory, and none "
                  "of these critics is on its roster; the critiques stay in the entry's critiques strand."),
    dict(source="settler_colonialism", target="racial_formation", relationship_kind="comparison", directed=False,
         relationship="Land, labour and elementary structures of race",
         map_label="Settler colonialism and race",
         evidence_note="Wolfe's AHR forum essay and later book compare regimes of race through land and labour. Title "
                       "level only: the weakest proposal, optional.",
         sources=["wolfe_2001", "wolfe_2016"], strength="title_level_only"),
]
relationships = []
for i, r in enumerate(RELS, 1):
    relationships.append({
        "proposal_id": f"screq_rel_{i:02d}", "source": r["source"], "target": r["target"], "deferred": r.get("deferred"),
        "type": "critique" if r["relationship_kind"] == "critique" else "connection",
        "relationship_kind": r["relationship_kind"], "directed": r["directed"],
        "relationship": r["relationship"], "map_label": r["map_label"], "evidence_note": r["evidence_note"],
        "source_ids": [src(x) for x in r["sources"]], "classification_basis": "editorial_review",
        "evidence_strength": r["strength"], "review_status": "needs_review"})

all_relationships = relationships
relationships = [{k: v for k, v in r.items() if k != "deferred"} for r in all_relationships if not r.get("deferred")]

source_records = []
for r in LIT:
    if r["verification"]["status"] == "unverified":
        continue
    source_records.append({"id": src(r["id"]), "title": r["citation"], "citation": r["citation"],
                           "url": r["url"] or (f"https://doi.org/{r['doi']}" if r.get("doi") else None),
                           "doi": r.get("doi"),
                           "verification": {k: r["verification"][k] for k in ("status", "checked_on", "note")},
                           "checked_against": r["verification"]["checked_against"]})
existing_source_reuse = {"wolfe_1999": "ind127_wolfe_1999", "harris_1997": "ind127_harris_1997",
                         "harris_2002": "healthgeo05_harris_native_space_2002"}

draft = {
    "status": "proposal_for_review",
    "prepared": CHECKED,
    "applies_to": "historiography-1920-2000.json revision 1.127 (not modified)",
    "node": {
        "id": "settler_colonialism",
        "label": "Settler colonialism",
        "entry_kind": "group",
        "entry_type": "Research field",
        "layer": "historiographical_developments",
        "period": None,
        "hunt_core_paradigm": False,
        "date_label": "Earlier settler-society studies 1983–95 · Wolfe 1999 · coverage through 2000; selected later readings: Wolfe 2006, Veracini 2010, journal 2011, critiques 2013–20; field chronology unresolved",
        "date_span": {"start": 1983, "start_kind": "earlier_roots", "end": 2020, "end_kind": "unstated",
                      "precision": "year",
                      "basis": "Selected publication milestones only. 1983 and 1995 are earlier settler-society witnesses, not the "
                               "field's origin; Wolfe 1999 is the only selected milestone inside 1920–2000. The term itself has decolonization-era "
                               "usage (Veracini 2013); the field's theoretical consolidation falls after 2000; neither endpoint "
                               "bounds the field."},
        "description": DESCRIPTION,
        "description_words": len(DESCRIPTION.split()),
        "scope_note": "A selective research field whose theoretical consolidation came mostly after 2000; the entry covers its roots through 2000 and cites selected later works as readings. Settler-colonial theory, "
                      "Indigenous political thought, Canadian histories of dispossession and comparative imperial history "
                      "have different genealogies. Roster inclusion is not adoption of the paradigm: Carter, Perry, Harris "
                      "and Daschuk wrote earlier or beside it. No single founder, origin or Canadian consensus is asserted. "
                      "Critics appear as critics. Francophone uptake in the PhD corpus is near zero.",
        "representative_figures_and_works": (
            "Earlier: Denoon, Settler Capitalism (1983); Stasiulis and Yuval-Davis, eds., Unsettling Settler Societies (1995). "
            "Wolfe, Settler Colonialism and the Transformation of Anthropology (1999) and “Settler Colonialism and the "
            "Elimination of the Native” (2006); Elkins and Pedersen, eds. (2005); Veracini, Settler Colonialism (2010) and "
            "Settler Colonial Studies (2011). Read with Coulthard (2014), A. Simpson (2014), L. B. Simpson (2011, 2017), "
            "Byrd (2011) and Tuck and Yang (2012). Canadian historiography: Carter (1990, 2008), Harris (2002, 2004, 2020), "
            "Perry (2001), Regan (2010), Daschuk (2013), Battell Lowman and Barker (2015), Burrill (2019). Critiques: "
            "Macoun and Strakosch (2013), Rowse (2014), Kauanui (2016), Greer (2019), Shoemaker (2019), Konishi (2019), "
            "Garba and Sorentino (2020)."),
        "source_ids": [src(r["id"]) for r in LIT if r["verification"]["status"] != "unverified"],
        "representative_people": rep_people,
        "strands": strands,
        "extension_coverage": {"status": "proposed", "baseline_through": 2000, "research_cutoff": CHECKED,
                               "field_review_complete": False,
                               "publication_years": sorted({r["year"] for r in LIT if r["verification"]["status"] != "unverified"})},
    },
    "relation_to_periods": (
        "The atlas's main period is 1920–2000. Only precursors (1983, 1995) and Wolfe 1999 fall inside it; the name, "
        "journal, Canadian uptake and critiques are post-2000. Recommended: an extension entry like digital_history, with "
        "period null, kept out of the exact-2000 baseline (1.121). The existing Indigenous strand "
        "'settler_colonial_interlocutor' (Wolfe 1999) can stay as the in-period cross-reference."),
    "new_people": new_people,
    "proposed_source_records": source_records,
    "existing_source_reuse": existing_source_reuse,
    "proposed_relationships": relationships,  # deferred ones are listed under relationships_considered_not_proposed
    "relationships_considered_not_proposed": [
        {"pair": f"{r['source']} → {r['target']} ({r['relationship_kind']}, {r['proposal_id']})", "reason": r["deferred"]}
        for r in all_relationships if r.get("deferred")] + [
        {"pair": "environment – settler_colonialism", "reason": "Co-citation lift 2.45 and dissertations on settler science and waste, but no checked work states the link. A lead for a later pass."},
        {"pair": "medicalhistory – settler_colonialism", "reason": "Daschuk and Mosby are strongly co-cited, but their framing is unchecked."},
        {"pair": "ethnohistory / spatialhistory – indigenous", "reason": "Existing edges edge_776 and edge_777 are untouched."},
        {"pair": "nationalismstudies, memory", "reason": "Lifts are modest (1.39) and no checked source."},
    ],
}
json.dump(draft, open(OUT / "entry-draft.json", "w"), ensure_ascii=False, indent=1)
print("literature records", len(LIT), literature["counts"])
print("description words", draft["node"]["description_words"])
print("people", len(rep_people), "new", len(new_people), "strands", len(strands), "relationships", len(relationships))
