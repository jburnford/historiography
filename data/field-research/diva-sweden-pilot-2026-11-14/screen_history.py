#!/usr/bin/env python3
"""History screen for the SwePub SSIF 601 + 50203 pull, and the tracked theses table.

Screen (first rule that fires):
 1. local doctoral subject (DiVA 'forskarutbildningsämne') in the History family
    (Historia, Idé- och lärdomshistoria, Historiska studier, Kyrkohistoria, Teknikhistoria,
    Historiedidaktik, history of education, historical demography ...)          -> history
       high if the SSIF codes agree or are absent, medium if they say archaeology only
 2. local subject Economic history                                                -> economic_history
 3. local subject in archaeology (Arkeologi, Osteoarkeologi, Egyptologi ...)      -> archaeology
 4. local subject Antikens kultur och samhällsliv / Classical archaeology and
    ancient history                                                               -> ancient (archaeology title words -> archaeology)
 5. SSIF 60101 / 60102 / 60104 present                                            -> history
       high if no other-discipline local subject, medium otherwise
 6. SSIF 60103 (and no 60101/2/4)                                                 -> archaeology (high)
 7. SSIF 60105 only                                                               -> ancient (medium)
 8. SSIF 50203                                                                    -> economic_history
 9. no 5-digit code under 601/50203: title words                                  -> history / archaeology (low) or unclear
'history' includes history of science and ideas and of technology (user rule 2026-11-04).
Economic history, ancient, unclear: reported separately for the user's call.

Usage: screen_history.py THESES.csv ROUTES.csv OUT_THESES.csv.gz"""
import csv, gzip, re, sys, collections as C

theses_csv, routes_csv, out = sys.argv[1:4]
HIST = re.compile(r"^(historia|history|historical studies|historiska studier|idéhistoria|history of ideas|"
                  r"idé- och lärdomshistoria|history of sciences? and ideas|historiska studier av teknik.*|"
                  r"history of science, technology and environment|historia med .*|history of education|"
                  r"history of technology|teknikhistoria|church history|kyrkohistoria|history and history teaching|"
                  r"didactics of history|historiedidaktik|historical demography|historisk demografi|rättshistoria|"
                  r"legal history|vetenskapshistoria|history of science|medicinens historia|history of medicine|"
                  r"history with .*|historia och historiedidaktik)$")
ECON = re.compile(r"^(ekonomisk historia|economic history)$")
ARCH = re.compile(r"arkeolog|archaeolog|osteo|egyptolog|assyriolog|numismat")
ANC = re.compile(r"^(antikens kultur och samhällsliv|classical archaeology and ancient history|antikvetenskap|"
                 r"ancient history|antikens historia|ancient culture and society|classical studies)$")
ARCH_T = re.compile(r"arkeolog|archaeolog|osteolog|bronze age|bronsålder|iron age|järnålder|stone age|stenålder|"
                    r"neolithic|neolitisk|mesolithic|mesolitisk|burial|gravfält|gravar|excavat|utgrävning|"
                    r"settlement site|boplats|runestone|runsten|ceramic|keramik|isotop", re.I)
HIST_T = re.compile(r"histor|1[5-9]\d\d|\b(17|18|19)\d0-?tal|century|sekel|seklet|medeltid|medieval|"
                    r"kolonial|colonial|krig|war\b|reformation|stormakts|folkhem|efterkrigs", re.I)


def screen(t):
    subs = [s.split(":", 1)[1].strip().lower() for s in t["local_subjects"].split(" | ") if ":" in s]
    five = set(t["ssif5"].split())
    hist5 = five & {"60101", "60102", "60104"}
    if any(HIST.match(s) for s in subs):
        conf = "medium" if (five and not hist5 and five & {"60103", "60105"}) else "high"
        return "history", conf, "local subject: " + next(s for s in subs if HIST.match(s))
    if any(ECON.match(s) for s in subs):
        return "economic_history", "high", "local subject: economic history"
    if any(ARCH.search(s) for s in subs):
        return "archaeology", "high", "local subject: " + next(s for s in subs if ARCH.search(s))
    if any(ANC.match(s) for s in subs):
        if ARCH_T.search(t["title"] + " " + t["subtitle"]):
            return "archaeology", "medium", "local subject ancient + archaeology title words"
        return "ancient", "medium", "local subject: classical/ancient"
    other = [s for s in subs if s]
    if hist5:
        if other:
            return "history", "medium", f"SSIF {' '.join(sorted(hist5))}; other local subject: {other[0]}"
        return "history", "high", f"SSIF {' '.join(sorted(hist5))}"
    if "60103" in five:
        return "archaeology", "high", "SSIF 60103"
    if "60105" in five:
        if ARCH_T.search(t["title"] + " " + t["subtitle"]):
            return "archaeology", "medium", "SSIF 60105 + archaeology title words"
        return "ancient", "medium", "SSIF 60105 only"
    if "50203" in five:
        return "economic_history", "high", "SSIF 50203"
    title = t["title"] + " " + t["subtitle"]
    if ARCH_T.search(title):
        return "archaeology", "low", "no 5-digit code; archaeology title words"
    if other:
        return "unclear", "low", f"no 5-digit code; local subject {other[0]}"
    if HIST_T.search(title):
        return "history", "low", "no 5-digit code; history title words"
    return "unclear", "low", "no 5-digit code, no local subject, no title signal"


routes = {r["record_id"]: r for r in csv.DictReader(open(routes_csv))}
rows = list(csv.DictReader(open(theses_csv)))
cols = ["record_id", "duplicate_ids", "urn", "author", "author_orcid", "author_life", "title", "subtitle", "language",
        "year", "defence_date", "university_code", "university", "university_basis", "in_list", "ssif5", "ssif3",
        "autoclassified", "local_subjects", "screen", "confidence", "confidence_reason", "n_supervisor",
        "n_assistant_supervisor", "n_opponent", "swepub_open_access", "fulltext_url", "fulltext_status",
        "resolved_link", "link_host", "link_kind", "route_class", "embargo_end", "isbn", "doi", "series", "publisher",
        "source"]
c = C.Counter()
with gzip.open(out, "wt", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for t in rows:
        s, conf, why = screen(t)
        t.update(screen=s, confidence=conf, confidence_reason=why, **{k: routes[t["record_id"]][k] for k in
                 ("resolved_link", "link_host", "link_kind", "route_class")})
        c[(s, conf)] += 1
        w.writerow(t)
for k, v in sorted(c.items()):
    print(k, v)
