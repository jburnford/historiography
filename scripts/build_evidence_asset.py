"""Build the site's evidence asset from the latest evidence-layer builds.

Writes data/evidence-layer/site-evidence.json (tracked, small). build_site.py copies it to
docs/data/evidence.json. Generated evidence builds are gitignored, so the site reads this
committed derivative instead, and CI can rebuild docs/ from tracked files alone. Contents are
aggregates only: counts per atlas entry, fold relations, method signals, review-invocation
lifts, plus corpus coverage. No review, abstract or article text, and no personal data.

    python3 scripts/build_evidence_asset.py --series v17 --methods methods-v3 --mentions mentions-v2
"""
import argparse
import csv
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data/evidence-layer/generated"
OUT = ROOT / "data/evidence-layer/site-evidence.json"
GRAPH = ROOT / "historiography-1920-2000.json"
CROSSWALK = ROOT / "data/evidence-layer/practice-crosswalk.csv"
BIN = 5


DISPLAY = {"diplomatic_international": "Diplomatic & international history",
           "imperial_colonial_history": "Imperial & colonial history", "jewish_studies": "Jewish studies",
           "socialism_left_politics": "History of socialism & the left", "maritime_ocean_history": "Maritime & ocean history",
           "rural_agrarian": "Rural & agrarian history", "local_regional_history": "Local & regional history",
           "book_library_history": "Book & library history", "literature_film": "Literature & film",
           "film_media": "Film & media history", "childhood_youth": "History of childhood & youth",
           "history_of_emotions": "History of emotions", "history_of_knowledge": "History of knowledge",
           "genocide_studies": "Genocide studies", "american_studies": "American studies",
           "ethnic_history": "Ethnic history", "migration_history": "Migration history",
           "transnational_history": "Transnational history", "human_rights": "History of human rights"}


def label_of(target, entries, cw_labels):
    """Atlas label, or a readable name for a field the atlas lacks."""
    if target in entries:
        return entries[target]
    key = target.split(":", 1)[-1]
    if key in DISPLAY:
        return DISPLAY[key]
    words = key.replace("_", " ")
    words = words if any(w in words for w in ("history", "studies")) else words + " history"
    return words[:1].upper() + words[1:]


def families_block(fam, entries, cw_labels):
    """Landing data: editorial families and their share-of-period record series (aggregates only)."""
    ids = {d["label"]: d["id"] for d in fam["definitions"]}
    out = []
    for d in fam["definitions"]:
        series = {}
        for view in fam["views"]:
            v = fam["views"][view]
            got = v["families"].get(d["label"], {})
            series[view] = [[int(b), got.get(b, 0), v["totals"][b]] for b in sorted(v["totals"], key=int)]
        out.append({"id": d["id"], "label": d["label"],
                    "members": [{"id": m["id"], "primary": m["primary"]} for m in d["members"]
                                if m["kind"] == "atlas_entry"],
                    "record_only": [{"id": m["id"], "label": label_of(m["id"], entries, cw_labels),
                                     "primary": m["primary"]} for m in d["members"] if m["kind"] == "record_only"],
                    "series": series})
    s = fam["strip"]
    n = max(s["items"], 1)
    return {"note": "Families are editorial groupings. A field that bridges two families counts in both, so family "
                    "shares overlap and must not be summed. The headline strip is the exception: it splits each "
                    "item across its primary families.",
            "established_journals": fam["established_journals"], "bins": fam["bins"],
            "strip": {"period": s["period"], "items": s["items"],
                      "shares": {ids[k]: round(v / n, 4) for k, v in s["families"].items()},
                      "unclaimed": round(s["unclaimed"] / n, 4)},
            "families": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--series", required=True)
    ap.add_argument("--methods", required=True)
    ap.add_argument("--mentions", required=True)
    ap.add_argument("--audit",default="data/evidence-layer/repairs/2026-10-10/sensitivity/summary.json")
    args = ap.parse_args()
    g = json.loads(GRAPH.read_text())
    entries = {n["id"]: n["label"] for n in g["nodes"] if n.get("entry_kind") == "group"}
    with open(CROSSWALK) as f:
        cw_labels = {r["target"]: r["target_label"] for r in csv.DictReader(f)}
    series = json.loads((GEN / args.series / "summary.json").read_text())
    methods = json.loads((GEN / args.methods / "summary.json").read_text())["methods"]
    mentions = json.loads((GEN / args.mentions / "summary.json").read_text())

    reviews = defaultdict(lambda: defaultdict(int))
    journals = defaultdict(lambda: defaultdict(int))
    with open(GEN / args.series / "series.csv") as f:
        for r in csv.DictReader(f):
            if r["axis"] != "theme" or not r["year"]:
                continue
            y = int(r["year"])
            b = y // BIN * BIN
            if r["source"] in ("hnet", "rih") and 1990 <= y <= 2026:
                reviews[r["target"]][b] += int(r["items"])
            elif r["source"] == "journal" and r["kind"] == "research_proxy" and 1900 <= y <= 2026:
                journals[r["target"]][b] += int(r["items"])
    invoked = {x["target"]: x["reviews"] for x in mentions["approach_invocations"]}
    lifts = mentions["approach_top_themes"]
    folded = series["atlas_entries_folded"]

    def bins(d):
        return {str(k): v for k, v in sorted(d.items())}

    out_entries = {}
    for e in sorted(entries):
        rec = {}
        if e in folded:
            f = folded[e]
            rec["status"] = f["status"]
            key = "roots_in" if f["status"] == "cross_field_method_with_roots" else "practised_within"
            rec[key] = [{"id": t, "label": label_of(t, entries, cw_labels)} for t in f.get(key, [])]
            rec["relations"] = sorted({r["relation"] for r in f["relations"]})
        else:
            rec["status"] = "direct"
            rec["reviews_by_5yr"] = bins(reviews.get(e, {}))
            rec["journal_items_by_5yr"] = bins(journals.get(e, {}))
            rec["reviews_total"] = sum(reviews.get(e, {}).values())
            rec["journal_items_total"] = sum(journals.get(e, {}).values())
        c=series['entry_coverage'].get(e)
        if c is None:   # an entry added after this series was built: nothing has been mapped to it yet
            c=dict(mapped_title_contexts=0, deposited_records=0, first_deposit=None, first_candidate=None,
                   qualifying_records=0, missing_length=0, added_after_series=args.series)
        note=f"{c['mapped_title_contexts']} mapped title contexts; {c['deposited_records']:,} distinct deposited records."
        if c['missing_length']:
            note += f" {c['missing_length']:,} article memberships lack calculable lengths; coverage is partial."
        if not c['mapped_title_contexts']:
            note += " Teaching venues and selected publication evidence have different scopes; this is not evidence of absent scholarship."
        special={
            'annales':' Original-title Crossref deposits cover 1929–1932; 1933–1938 remains a confirmed collection gap.',
            'military':' The military-journal lineage now has deposits from 1937. Older first-page-only records do not qualify for the ten-page proxy; use Deposited journal articles to see them. Journal of Military History deposits currently stop in 2009.',
            'indigenous':' Western Historical Quarterly is treated as a broad regional venue, not wholly Indigenous history. Ethnohistory pagination recovery is partial. Venue-level counts include outside scholarship and cannot identify Indigenous authorship or date the origins of Indigenous historical knowledge.',
            'labourhistory':' Labour/Le Travail is now mapped; recovered publisher ranges restore some early candidates, including 1976. The older backfile remains partial.',
            'women':' Signs and Feminist Studies remain outside this selected publication scope; teaching-venue links do not imply harvested records.',
            'nation':' Nations and Nationalism remains outside this selected publication scope.',
            'marx':' New Left Review remains outside this selected publication scope.',
            'anticolonial':' A mapped teaching venue has no collected deposits; blank counts do not mean no journal or scholarship exists.'}
        note+=special.get(e,'')
        if c.get('added_after_series'):
            note+=f" Added to the atlas after evidence series {c['added_after_series']} was built; no publication evidence is mapped to it yet."
        rec['coverage']={**c,'note':note}
        if e in methods:
            m = methods[e]
            rec["method"] = {"title_hits": m["title_hits_research_items"],
                             "abstract_hits_not_in_title": (m.get("abstract") or {}).get("abstract_hits_not_in_title"),
                             "practitioners": m["practitioners"],
                             "practitioner_items": m["practitioner_research_items"],
                             "practitioner_items_in_method_venues": m["practitioner_items_in_method_venues"],
                             "share_elsewhere": m["share_elsewhere"],
                             "identity_tiers_by_basis":m["practitioners_by_basis_and_identity_tier"]}
        if e in invoked:
            rec["invoked_in_reviews"] = invoked[e]
            # An entry's own theme is trivially over-represented; show the other fields.
            rec["invoked_most_in"] = [{"id": x["theme"], "label": label_of(x["theme"], entries, cw_labels),
                                       "lift": x["lift"]} for x in lifts.get(e, []) if x["theme"] != e][:3]
        out_entries[e] = rec

    lacks = [{"id": x["target"], "label": label_of(x["target"], entries, cw_labels), "reviews": x["reviews"]}
             for x in series["review_themes"] if x["target"].startswith("none:")][:12]
    hn, rih, jn = series["per_source"]["hnet"], series["per_source"]["rih"], series["per_source"]["journal"]
    asset = {
        "schema_version": "1.0",
        "built": dt.date.today().isoformat(),
        "builds": {"series": args.series, "methods": args.methods, "mentions": args.mentions},
        "coverage": {
            "reviews": f"H-Net ({hn['years'][0]}–{hn['years'][1]}, {hn['items']:,} reviews) and Reviews in History "
                       f"({rih['years'][0]}–{rih['years'][1]}, {rih['items']:,})",
            "journals": f"Crossref metadata for {series['selected_title_contexts']} selected journal/title contexts ({jn['items']:,} records); research candidates "
                        "are journal-article records of at least ten pages using deposited or explicitly sourced publisher ranges, with an article-number exception for the Journal of Digital History",
            "general_reviews": hn["items_by_axis"].get("general", 0),
        },
        "caveats": [
            "Counts measure participation, not influence; a review is not agreement.",
            "Mapping networks, subject headings and journals to atlas entries is editorial and partly unreviewed; "
            "journal counts are venue-level (a journal tagged with a field counts all its qualifying research candidates).",
            "These corpora are not the profession: H-Net is US-centred from 1993, Reviews in History is British, "
            "and Crossref coverage is uneven.",
        ],
        "fields_the_atlas_lacks": lacks,
        "families": families_block(series["families"], entries, cw_labels),
        "entries": out_entries,
    }
    audit_path = ROOT / args.audit
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        assert ('data/evidence-layer/generated/'+args.series+'/summary.json') in audit['inputs'], 'Sensitivity audit does not match this series'
        baseline = {r['family']: r for r in audit['sensitivity'] if r['scenario'] == 'pages_10'}
        def maximum(names):
            return max(abs(r['share_2000_2024'] - baseline[r['family']]['share_2000_2024']) * 100
                       for r in audit['sensitivity'] if r['scenario'] in names)
        length_delta = maximum({'pages_8','pages_12','pages_15'})
        mapping_delta = maximum({'subject_mapping_only'})
        asset['sensitivity'] = {
            'note': f'An offline audit reproduces every published journal bin. Compared with the ten-page default, '
                    f'thresholds of eight, twelve or fifteen pages move each family’s 2000–2024 share by at most {length_delta:.1f} percentage points. '
                    f'Using directory subjects without journal-level themes moves a share by as much as {mapping_delta:.1f} points. '
                    'Neither scenario verifies article genres.',
            'pagination_note': 'Calculated lengths are missing for '+', '.join(f"{r['share']:.0%} of journal-article records in {r['period']}" for r in audit['missing_pagination'])+'. Source coverage can change comparisons across time; genres remain unverified.',
        }
    OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=1) + "\n")
    print(f"{OUT.relative_to(ROOT)}: {len(out_entries)} entries, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
