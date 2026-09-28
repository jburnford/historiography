#!/usr/bin/env python3
"""Revision 1.124: add the fifteen figures the figure-gaps audit found missing from their fields.

The user approved all fifteen likely omissions of data/evidence-layer/audits/figure-gaps-2026-09-27
("add the 15 in", 2026-09-28). The first is the Foucault case that prompted the audit: Hunt's
The New Cultural History (1989) opens its "Models for Cultural History" with O'Brien on Foucault,
while the atlas's entry named only Geertz. Each addition is a roster record with a bounded
context and a source whose verification scope is stated; no full person nodes and no post-2000
imports. One contribution edge (Foucault -> New cultural history) and two strands are added.

    python3 scripts/apply_figure_gaps.py            # apply to the 1.123 graph and write the record
    python3 scripts/apply_figure_gaps.py --check    # exact reconstruction from the saved snapshot
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate  # noqa: E402

OUT = ROOT / "data/production-batches/figure-gaps-1.124"
RAW = OUT / "raw"
GRAPH = ROOT / "historiography-1920-2000.json"
BASE = ROOT / "drafts/historiography-1920-2000.v1.123.json"
DAY = "2026-09-28"
AUTHORIZATION = ("User: Cultural and intellectual history 'doesn't really capture the significance of Foucault'; "
                 "supplied the JSTOR contents of Hunt, ed., The New Cultural History (1989); asked for a review of the "
                 "graph for similar errors, then 'add the 15 in' (2026-09-28).")


def read(p):
    return json.loads(p.read_text())


def serial(v):
    return json.dumps(v, ensure_ascii=False, indent=2) + "\n"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def meta(note):
    return {"status": "bibliographic_metadata_checked", "checked_on": DAY, "note": note}


SOURCES = [
    dict(id="obrien_foucault_1989", title="Patricia O’Brien, “Michel Foucault’s History of Culture,” in Lynn Hunt, ed., The New Cultural History (1989), 25–46.",
         citation="Patricia O’Brien, “Michel Foucault’s History of Culture,” in Lynn Hunt, ed., The New Cultural History (University of California Press, 1989), 25–46.",
         url="https://www.jstor.org/stable/10.1525/j.ctt1ppfh6.5",
         verification={"status": "supporting_page_checked", "checked_on": DAY, "note":
                       "JSTOR contents and chapter-opening preview (p. 25) supplied by the user on 2026-09-27; Crossref chapter record "
                       "10.1525/9780520908925-003 confirms title and pages. First of the volume’s four “Models for Cultural History”. "
                       "The opening calls Foucault’s writing “an alternative model for writing the history of culture, a model that "
                       "embodies a fundamental critique of Marxist and Annaliste analysis, of social history itself.” Chapter body unread; "
                       "O’Brien’s reading is attributed, not Foucault’s self-description."}),
    dict(id="biersack_geertz_1989", title="Aletta Biersack, “Local Knowledge, Local History: Geertz and Beyond,” in Lynn Hunt, ed., The New Cultural History (1989), 72–96.",
         citation="Aletta Biersack, “Local Knowledge, Local History: Geertz and Beyond,” in Lynn Hunt, ed., The New Cultural History (University of California Press, 1989), 72–96.",
         url="https://www.jstor.org/stable/10.1525/j.ctt1ppfh6.7",
         verification={"status": "supporting_page_checked", "checked_on": DAY, "note":
                       "JSTOR contents and chapter-opening preview (p. 72) supplied by the user on 2026-09-27; Crossref chapter record "
                       "10.1525/9780520908925-005 confirms title and pages. Third of the volume’s four models; the opening says historians "
                       "acknowledge Lévi-Strauss, Turner, Douglas and “in particular, Clifford Geertz”. Chapter body unread."}),
    dict(id="prakash_post_orientalist_1990", title="Gyan Prakash, “Writing Post-Orientalist Histories of the Third World: Perspectives from Indian Historiography,” Comparative Studies in Society and History 32(2) (1990): 383–408.",
         citation="Comparative Studies in Society and History 32(2) (1990): 383–408. DOI 10.1017/S0010417500016534.",
         url="https://doi.org/10.1017/S0010417500016534",
         verification=meta("Crossref record checked (raw/prakash_1990.crossref.json): author, title, journal, volume, issue, pages, April 1990. Body unread; used for authorship and programme title only.")),
    dict(id="prakash_subaltern_postcolonial_1994", title="Gyan Prakash, “Subaltern Studies as Postcolonial Criticism,” American Historical Review 99(5) (1994): 1475–1490.",
         citation="American Historical Review 99(5) (1994): 1475–1490. DOI 10.2307/2168385.",
         url="https://doi.org/10.2307/2168385",
         verification=meta("Crossref records checked (raw/prakash_1994.crossref.json): author, title, AHR 99(5), 1475–1490, December 1994. Body unread.")),
    dict(id="hall_postcolonial_1996", title="Stuart Hall, “When Was ‘the Post-colonial’? Thinking at the Limit” (1996).",
         citation="Stuart Hall, “When Was ‘the Post-colonial’? Thinking at the Limit,” in Iain Chambers and Lidia Curti, eds., The Post-colonial Question (Routledge, 1996); reprinted in Hall, Selected Writings on Marxism (Duke University Press, 2021), 293–315.",
         url="https://doi.org/10.1215/9781478002154-015",
         verification=meta("Crossref records for the 2021 Duke reprint checked (raw/hall_1996.crossref.json), one dating the essay [1996]. The 1996 Chambers and Curti volume was not found in OpenLibrary; its pagination is not asserted. Body unread.")),
    dict(id="rorty_linguistic_turn_1967", title="Richard Rorty, ed., The Linguistic Turn: Recent Essays in Philosophical Method (University of Chicago Press, 1967).",
         citation="Richard Rorty, ed., The Linguistic Turn: Recent Essays in Philosophical Method (University of Chicago Press, 1967).",
         url="https://openlibrary.org/works/OL2018374W",
         verification=meta("OpenLibrary work record checked (raw/rorty_1967.openlibrary.json): editor, title, 1967, University of Chicago Press. Introduction and essays unread; supports the anthology and its title, not a lineage to historians’ usage.")),
    dict(id="jay_kracauer_extraterritorial", title="Martin Jay, “The Extraterritorial Life of Siegfried Kracauer.”",
         citation="Martin Jay, “The Extraterritorial Life of Siegfried Kracauer,” first published in Salmagundi (1975–76); collected in Jay, Permanent Exiles (Columbia University Press, 1985); reprinted 2016.",
         url="https://doi.org/10.2307/jj.2353881.17",
         verification=meta("Crossref records of the 2016 reprint checked (raw/jay_kracauer_1975.crossref.json) and OpenLibrary record of Permanent Exiles (1985, raw/jay_permanent_1985.openlibrary.json). The original Salmagundi issue and the essay text were not checked.")),
    dict(id="davis_martin_guerre_1983", title="Natalie Zemon Davis, The Return of Martin Guerre (Harvard University Press, 1983).",
         citation="Natalie Zemon Davis, The Return of Martin Guerre (Harvard University Press, 1983); related French edition with Jean-Claude Carrière and Daniel Vigne, 1982.",
         url="https://openlibrary.org/works/OL771624W",
         verification=meta("OpenLibrary work record checked (raw/davis_1983.openlibrary.json): Davis, title, earliest 1982 edition with the film’s screenwriters. Book unread; the English 1983 Harvard edition is cited from the standard bibliography, not collated.")),
    dict(id="broszat_bayern_1977", title="Martin Broszat et al., eds., Bayern in der NS-Zeit (Oldenbourg, 1977–1983).",
         citation="Martin Broszat, Elke Fröhlich, Falk Wiesemann et al., eds., Bayern in der NS-Zeit, 6 vols. (Oldenbourg, 1977–1983).",
         url="https://openlibrary.org/works/OL22590590W",
         verification=meta("OpenLibrary records checked (raw/broszat_1977.openlibrary.json): Bayern in der NS-Zeit, Broszat and Wiesemann, Oldenbourg, 1977. The six-volume extent and later volumes are not checked here; no volume read.")),
    dict(id="harvey_social_justice_1973", title="David Harvey, Social Justice and the City (Johns Hopkins University Press, 1973).",
         citation="David Harvey, Social Justice and the City (Edward Arnold / Johns Hopkins University Press, 1973).",
         url="https://openlibrary.org/works/OL3232636W",
         verification=meta("OpenLibrary work record checked (raw/harvey_1973.openlibrary.json): Harvey, title, 1973, Johns Hopkins. Book unread.")),
    dict(id="benjamin_arcades_project", title="Walter Benjamin, Das Passagen-Werk (1982); The Arcades Project, trans. Howard Eiland and Kevin McLaughlin (Harvard University Press, 1999).",
         citation="Walter Benjamin, Das Passagen-Werk, ed. Rolf Tiedemann (Suhrkamp, 1982); The Arcades Project (Belknap Press of Harvard University Press, 1999).",
         url="https://openlibrary.org/works/OL156207W",
         verification=meta("OpenLibrary work record checked (raw/benjamin_1999.openlibrary.json): Benjamin, Passagen-Werk, Belknap/Harvard among publishers. Unfinished work; editions not collated and text unread.")),
    dict(id="fox_genovese_plantation_1988", title="Elizabeth Fox-Genovese, Within the Plantation Household: Black and White Women of the Old South (University of North Carolina Press, 1988).",
         citation="Elizabeth Fox-Genovese, Within the Plantation Household: Black and White Women of the Old South (University of North Carolina Press, 1988).",
         url="https://openlibrary.org/works/OL2801662W",
         verification=meta("OpenLibrary work record checked (raw/fox_genovese_1988.openlibrary.json): author, title, 1988, University of North Carolina Press. Book unread.")),
]

# (entry, person, role, context, works, source_ids)
ADDITIONS = [
    ("culture", "foucault", "contributor",
     "Hunt’s The New Cultural History (1989) opens its “Models for Cultural History” with O’Brien’s chapter on Foucault, which reads his work as an alternative model for the history of culture and a critique of Marxist, Annaliste and social-historical analysis. A model offered to cultural historians, not membership of a school; his discourse, genealogy and power contexts in other entries remain distinct.",
     "Histoire de la folie (1961); Discipline and Punish (1975); The History of Sexuality I (1976)",
     ["obrien_foucault_1989", "culture", "foucault"]),
    ("post", "gyan_prakash", "historian",
     "Historian whose essays set out postcolonial historiography from Indian historiography and read Subaltern Studies as postcolonial criticism. His Subaltern Studies context remains distinct.",
     "“Writing Post-Orientalist Histories of the Third World” (1990); “Subaltern Studies as Postcolonial Criticism” (1994)",
     ["prakash_post_orientalist_1990", "prakash_subaltern_postcolonial_1994"]),
    ("post", "stuart_hall", "contributor",
     "Cultural theorist whose essays on diasporic identity and on the category of the “post-colonial” are standard resources in postcolonial critique. His cultural-studies context remains separate.",
     "“Cultural Identity and Diaspora” (1990); “When Was ‘the Post-colonial’? Thinking at the Limit” (1996)",
     ["hall_diaspora", "hall_postcolonial_1996"]),
    ("post", "paul_gilroy", "contributor",
     "The Black Atlantic criticizes national and racial closure and reads modernity through the Black Atlantic; a standard postcolonial and diaspora text for historians. His Atlantic and diaspora contexts remain.",
     "The Black Atlantic (1993)",
     ["gilroy"]),
    ("language", "richard_rorty", "contributor",
     "Rorty’s anthology of analytic philosophers’ essays on philosophical method gave the phrase “the linguistic turn” wide currency. Historians’ linguistic turn drew mainly on other, often French, resources, so this records the name’s source, not a lineage.",
     "The Linguistic Turn (1967), ed.",
     ["rorty_linguistic_turn_1967"]),
    ("frankfurt", "georg_lukacs", "precursor",
     "History and Class Consciousness (1923), with its account of reification and of Marxism as method, is the standard precursor of critical theory. Lukács was not a member of the Institute, and his later positions diverge from it.",
     "History and Class Consciousness (1923)",
     ["lukacs_orthodox_primary"]),
    ("frankfurt", "siegfried_kracauer", "contributor",
     "Critic and essayist of the Frankfurt milieu, close to Adorno and Benjamin but never a member of the Institute. His microhistory context, where Ginzburg records a retrospective affinity, remains distinct.",
     "Das Ornament der Masse (1963; essays from the 1920s)",
     ["jay_kracauer_extraterritorial"]),
    ("micro", "natalie_zemon_davis", "historian",
     "The Return of Martin Guerre reconstructs a sixteenth-century village imposture case and is a standard example of microhistory in English. Her cultural and women’s-history contexts remain.",
     "The Return of Martin Guerre (1983)",
     ["davis_martin_guerre_1983"]),
    ("micro", "martin_broszat", "historian",
     "Led the Institut für Zeitgeschichte’s Bayern in der NS-Zeit project, a founding programme for the history of everyday life under National Socialism. His structuralist interpretation of the regime is a separate context.",
     "Bayern in der NS-Zeit (1977–1983), ed. with others",
     ["broszat_bayern_1977"]),
    ("urbanhistory", "david_harvey", "contributor",
     "Geographer whose urban political economy and historical studies of the city are standard resources for urban historians. A contributor from geography, not a school member.",
     "Social Justice and the City (1973); The Condition of Postmodernity (1989)",
     ["harvey_social_justice_1973", "harvey_place_tradition"]),
    ("urbanhistory", "walter_benjamin", "contributor",
     "The unfinished Passagen-Werk on nineteenth-century Paris is a central resource for cultural histories of the city, its arcades and commodities. His Frankfurt and memory contexts remain.",
     "Das Passagen-Werk (1982); The Arcades Project (1999)",
     ["benjamin_arcades_project"]),
    ("urbanhistory", "michel_de_certeau", "contributor",
     "“Walking in the City” gives urban historians a vocabulary of spatial practice and everyday use. His practice-theory context remains.",
     "The Practice of Everyday Life (1980; English 1984)",
     ["certeau"]),
    ("women", "leonore_davidoff", "historian",
     "With Catherine Hall, analyses gender, family and class in the English middle class; a standard work of women’s and gender history. Hall’s coauthor credit is retained.",
     "With Catherine Hall, Family Fortunes (1987)",
     ["family_fortunes"]),
    ("women", "catherine_hall", "historian",
     "Coauthor with Leonore Davidoff of Family Fortunes; both credits are retained. Her imperial-history contexts remain distinct.",
     "With Leonore Davidoff, Family Fortunes (1987)",
     ["family_fortunes"]),
    ("women", "elizabeth_fox_genovese", "historian",
     "Within the Plantation Household examines Black and white women of the Old South; a standard work of Southern women’s history. Her exchange with Stone on narrative is recorded elsewhere.",
     "Within the Plantation Household (1988)",
     ["fox_genovese_plantation_1988"]),
    ("memory", "aby_warburg", "precursor",
     "Jan Assmann discusses Warburg with Halbwachs as an early theorist of social and cultural memory, alongside the Warburg Institute’s own account of his library. A precursor in Assmann’s account, not a founder of memory studies as a field.",
     "Bilderatlas Mnemosyne (1924–29, unfinished)",
     ["assmann_collective", "warburg_institution_history"]),
]

EDGE = dict(id="edge_766", source="foucault", target="culture", type="connection", relationship_kind="contribution", directed=True,
            relationship="O’Brien presents Foucault’s history of culture as a model for the new cultural history",
            map_label="Foucault’s history of culture as a model for cultural history (O’Brien in Hunt 1989)",
            evidence_note=("Hunt’s volume opens its “Models for Cultural History” with O’Brien’s chapter (pp. 25–46), whose opening calls "
                           "Foucault’s writing “an alternative model for writing the history of culture, a model that embodies a fundamental "
                           "critique of Marxist and Annaliste analysis, of social history itself.” Checked from the JSTOR chapter preview; "
                           "the chapter body is unread. This records a model the volume proposes, not uniform adoption by cultural historians."),
            source_ids=["obrien_foucault_1989", "culture"], classification_basis="editorial_review")

STRANDS = {
    "culture": dict(id="foucault_model", title="Discourse, power and the critique of social history",
                    person_ids=["foucault", "roger_chartier", "joan_wallach_scott"],
                    focus=("O’Brien presents Foucault’s history of culture as an alternative to Marxist, Annaliste and social-historical "
                           "analysis. Chartier’s appropriation of his account of discourse and Scott’s use of his conception of power are "
                           "recorded as separate relationships; this strand does not make them Foucauldians."),
                    works="Patricia O’Brien, “Michel Foucault’s History of Culture” (1989)",
                    source_ids=["obrien_foucault_1989"], basis="editorial_distinction"),
    "urbanhistory": dict(id="space_capital_culture", title="Space, capital and the cultural city",
                         person_ids=["david_harvey", "walter_benjamin", "michel_de_certeau"],
                         focus=("Urban political economy (Harvey), the city of arcades and commodities (Benjamin) and spatial practice "
                                "(de Certeau) supply the spatial and cultural turn in urban history, beside the entry’s social-science "
                                "programme. They are resources from geography, criticism and theory, not a school."),
                         works="Social Justice and the City (1973); Das Passagen-Werk (1982); The Practice of Everyday Life (1980/84)",
                         source_ids=["harvey_social_justice_1973", "benjamin_arcades_project", "certeau"], basis="editorial_distinction"),
}

FIGURES_LINES = {
    "culture": ("Natalie Zemon Davis; Clifford Geertz as an influence; Lynn Hunt, The New Cultural History (1989).",
                "Natalie Zemon Davis; Lynn Hunt, ed., The New Cultural History (1989), whose “Models for Cultural History” are "
                "Foucault (O’Brien), Thompson and Davis (Desan), Geertz (Biersack), and White and LaCapra (Kramer)."),
}
APPEND_LINES = {
    "post": " Gyan Prakash: “Writing Post-Orientalist Histories of the Third World” (1990); Stuart Hall: “When Was ‘the Post-colonial’?” (1996); Paul Gilroy: The Black Atlantic (1993).",
    "language": " Richard Rorty, ed.: The Linguistic Turn (1967).",
    "frankfurt": " Georg Lukács: History and Class Consciousness (1923), as precursor; Siegfried Kracauer.",
    "micro": " Natalie Zemon Davis: The Return of Martin Guerre (1983); Martin Broszat et al.: Bayern in der NS-Zeit (1977–83).",
    "urbanhistory": " David Harvey: Social Justice and the City (1973); Walter Benjamin: Das Passagen-Werk (1982); Michel de Certeau: “Walking in the City” (1980).",
    "women": " Leonore Davidoff and Catherine Hall: Family Fortunes (1987); Elizabeth Fox-Genovese: Within the Plantation Household (1988).",
    "memory": " Aby Warburg: Bilderatlas Mnemosyne (1924–29), as precursor.",
}

CERTEAU_CHECK = meta("OpenLibrary work records checked (raw/certeau_1984.openlibrary.json): de Certeau, Arts de faire / The Practice of Everyday Life, University of California Press. Bibliographic identity only; text unread.")


def transform(before):
    if before["revision_history"][-1]["version"] != "1.123":
        raise ValueError("Expected incoming revision 1.123")
    g = deepcopy(before)
    nodes = {n["id"]: n for n in g["nodes"]}
    people = {p["id"] for p in g["people"]}
    source_ids = {s["id"] for s in g["sources"]}
    for s in SOURCES:
        if s["id"] in source_ids:
            raise ValueError("Source already exists: " + s["id"])
    g["sources"].extend(deepcopy(SOURCES))
    known = source_ids | {s["id"] for s in SOURCES}
    certeau = next(s for s in g["sources"] if s["id"] == "certeau")
    certeau["verification_history"] = certeau.get("verification_history", []) + [certeau["verification"]]
    certeau["verification"] = CERTEAU_CHECK
    if any(e["id"] == EDGE["id"] for e in g["edges"]):
        raise ValueError("Edge id taken: " + EDGE["id"])
    g["edges"].append(deepcopy(EDGE))
    for entry, pid, role, context, works, sids in ADDITIONS:
        node = nodes[entry]
        if pid not in people:
            raise ValueError("Unknown person: " + pid)
        if any(r["person_id"] == pid for r in node["representative_people"]):
            raise ValueError(f"Already in {entry}: {pid}")
        missing = [s for s in sids if s not in known]
        if missing:
            raise ValueError(f"Unknown sources for {pid}: {missing}")
        rec = dict(person_id=pid, role=role, context=context, works=works, source_ids=sids, basis="source_review")
        if (entry, pid) == ("culture", "foucault"):
            rec["edge_id"] = EDGE["id"]
        node["representative_people"].append(rec)
        node["source_ids"] = list(dict.fromkeys(node["source_ids"] + sids))
    for entry, strand in STRANDS.items():
        if any(s["id"] == strand["id"] for s in nodes[entry]["strands"]):
            raise ValueError("Strand id taken: " + strand["id"])
        nodes[entry]["strands"].append(deepcopy(strand))
    for entry, (old, new) in FIGURES_LINES.items():
        if nodes[entry]["representative_figures_and_works"] != old:
            raise ValueError("Unexpected figures line in " + entry)
        nodes[entry]["representative_figures_and_works"] = new
    for entry, line in APPEND_LINES.items():
        nodes[entry]["representative_figures_and_works"] += line
    geertz = next(r for r in nodes["culture"]["representative_people"] if r["person_id"] == "geertz")
    geertz["source_ids"] = geertz["source_ids"] + ["biersack_geertz_1989"]
    nodes["culture"]["source_ids"] = list(dict.fromkeys(nodes["culture"]["source_ids"] + ["biersack_geertz_1989"]))
    g["revision_history"].append(dict(
        version="1.124", date=DAY,
        summary=("Figure gaps: fifteen figures the review record ties to fields the atlas never named, approved by the user. "
                 "Foucault joins New cultural history as the first of Hunt’s 1989 models, with a contribution edge and a strand; "
                 "Prakash, Hall and Gilroy join postcolonial history; Rorty the linguistic turn; Lukács (precursor) and Kracauer the "
                 "Frankfurt School; Davis and Broszat microhistory; Harvey, Benjamin and de Certeau urban history, with a strand; "
                 "Davidoff (with coauthor Catherine Hall) and Fox-Genovese women’s history; Warburg (precursor) memory studies. "
                 "No new people or full person nodes; no post-2000 imports."),
        added_source_ids=[s["id"] for s in SOURCES], added_edge_ids=[EDGE["id"]],
        audit="data/evidence-layer/audits/figure-gaps-2026-09-27/README.md",
        acceptance_record="data/production-batches/figure-gaps-1.124/acceptance.json"))
    return g


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    raw = sorted(RAW.glob("*.json"))
    if a.check:
        record = read(OUT / "acceptance.json")
        if sha(BASE) != record["baseline_sha256"]:
            raise ValueError("Baseline hash mismatch")
        if read(GRAPH) != transform(read(BASE)):
            raise ValueError("Exact reconstruction mismatch")
        for name, expected in record["evidence_hashes"].items():
            if sha(ROOT / name) != expected:
                raise ValueError("Evidence changed: " + name)
        g = read(GRAPH)
    else:
        before = read(GRAPH)
        g = transform(before)
        errors, _ = validate(g, read(ROOT / "seminar-pathways.json"))
        if errors:
            raise ValueError("\n".join(errors))
        if BASE.exists() and BASE.read_bytes() != GRAPH.read_bytes():
            raise ValueError("Refusing to replace snapshot")
        BASE.parent.mkdir(exist_ok=True)
        BASE.write_bytes(GRAPH.read_bytes())
        prior = {n["id"]: n for n in before["nodes"]}
        record = dict(
            revision="1.124", date=DAY, authorization=AUTHORIZATION,
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE),
            evidence_hashes={str(q.relative_to(ROOT)): sha(q) for q in raw},
            prior_records={
                "culture.representative_figures_and_works": prior["culture"]["representative_figures_and_works"],
                "culture.geertz": next(r for r in prior["culture"]["representative_people"] if r["person_id"] == "geertz"),
                "sources.certeau.verification": next(s for s in before["sources"] if s["id"] == "certeau")["verification"],
            },
            changes=("Sixteen roster additions (fifteen figures plus Catherine Hall’s coauthor credit), twelve sources, one "
                     "contribution edge, two strands, eight figures lines, one source verification upgrade and one source added "
                     "to Geertz’s record. No new people, person nodes, influence arrows or post-2000 imports."),
            website_handoff="Site unchanged; rebuild docs/ from the production JSON.")
        GRAPH.write_text(serial(g))
        record["production_sha256"] = sha(GRAPH)
        (OUT / "acceptance.json").write_text(serial(record))
    errors, warnings = validate(g, read(ROOT / "seminar-pathways.json"))
    print(serial(dict(errors=errors, warnings=len(warnings), nodes=len(g["nodes"]), edges=len(g["edges"]),
                      sources=len(g["sources"]), people=len(g["people"]),
                      strands=sum(len(n.get("strands") or []) for n in g["nodes"]))), end="")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
