import sys, json, re, collections, os
sys.path.insert(0, '/tmp/claude-1000/-home-jic823-historiography/05dce7a5-f38d-4eea-a30a-ecd8fb58d371/scratchpad/wgcm')
from ev import *            # diss, cites, works, groups, cands, person_citers, work_citers, summ, N, FR, EARLY, LATE
from sources import S
from groups_content import G

OUT = '/home/jic823/historiography/data/extension-2026/canadian-historiography-groups-request-2026-10-12/drafts/'
TODAY = '2026-10-12'
SRC = {s['id']: s for s in S}
PFX = 'cdnsrc_'
EXISTING_SRC = {'scott_gender_1986', 'omi_winant', 'aries_childhood'}
ATLAS = json.load(open('/home/jic823/historiography/historiography-1920-2000.json'))
ATLAS_NODES = {n['id'] for n in ATLAS['nodes']}
ATLAS_PEOPLE = {p['id'] for p in ATLAS['people']}
PROPOSED = {g['id'] for g in groups}
def sid(x): return x if x in EXISTING_SRC else PFX + x

# ---------------- evidence helpers ----------------
GSPEC = {g['id']: g for g in groups}
def anchors(gid): return [n for n in GSPEC[gid]['primary'] + GSPEC[gid]['also'] if n in cands]
_pc = {}
def pc(n):
    if n not in _pc: _pc[n] = person_citers(n)
    return _pc[n]
def engaged_from(names):
    hits = collections.Counter(d for n in names for d in pc(n))
    return {d for d, k in hits.items() if k >= 2}
ENG = {g: engaged_from(anchors(g)) for g in PROPOSED}
def overlap(a, b):
    shared = set(anchors(a)) & set(anchors(b))
    A = engaged_from([n for n in anchors(a) if n not in shared]); B = engaged_from([n for n in anchors(b) if n not in shared])
    o = len(A & B)
    lift = round((o / len(A)) / (len(B) / N), 2) if A and B else None
    raw = len(ENG[a] & ENG[b])
    return dict(pair=[a, b], shared_anchors_removed=sorted(shared), a_engaged=len(A), b_engaged=len(B), overlap=o,
                share_of_a=round(o / len(A), 3) if A else None, lift=lift, raw_overlap_with_shared_anchors=raw, of=N)
def ov_text(a, b):
    r = overlap(a, b)
    s = (f"PhD context: {r['overlap']} of {r['a_engaged']} 2009–2026 PhDs engaging {a} also engage {b} "
         f"({r['share_of_a']:.0%}; lift {r['lift']}), counted after removing shared anchors")
    s += (f" ({', '.join(x.split(',')[0] for x in r['shared_anchors_removed'])})." if r['shared_anchors_removed'] else ".")
    return s + " Bibliographies record consultation, not influence; lifts are high for most Canadian pairs.", r
def P(key):
    from ev import pworks_key
    return {d for w in pworks_key(key) for d in cites.get(w, ())}
FOU = P('P:foucault|michel'); SCOTT = P('P:scott|joan w'); ARIES = P('P:aries|philippe'); OMIW = P('P:omi|michael') | P('P:winant|howard')
def cocite(gid, base, label):
    s = ENG[gid]; o = len(s & base)
    return dict(group=gid, cited=label, engaged=len(s), overlap=o, share=round(o / len(s), 3), baseline_share=round(len(base) / N, 3),
                lift=round((o / len(s)) / (len(base) / N), 2), of=N)
VAL, _ = work_citers(*SRC['valverde_1991']['rx'])

# ---------------- relationships ----------------
REL = {}
def rel(owner, src, tgt, kind, relationship, map_label, note, sids, strength, target_strand=None, phd=None, extra=None):
    REL.setdefault(owner, []).append(dict(source=src, target=tgt, type='critique' if kind == 'critique' else 'connection',
        relationship_kind=kind, directed=kind != 'comparison', relationship=relationship, map_label=map_label,
        **({'target_strand': target_strand} if target_strand else {}), evidence_note=note, source_ids=[sid(x) for x in sids],
        classification_basis='editorial_review', evidence_strength=strength, review_status='needs_review',
        **({'phd_context': phd} if phd else {}), **(extra or {})))

cs = cocite('cdn_women_gender', SCOTT, 'Joan W. Scott (any work)')
t, r_wg_wc = ov_text('cdn_women_gender', 'cdn_working_class')
rel('cdn_women_gender', 'women', 'cdn_women_gender', 'comparison', 'National and Quebec syntheses of women\'s history', 'Canadian and Quebec women\'s history',
    "The atlas's women entry groups national and regional syntheses (French, German, Nigerian) in a strand with different scopes and documentary bases. The Collectif Clio's Quebec synthesis (1982), which rejects a male-centred collective history, and Prentice et al.'s survey (1988) can be read alongside them. Comparison, not descent: Canadian women's history is not presented as a branch of any one national model.",
    ['clio_1982', 'prentice_1988'], 'excerpt_checked_and_metadata', target_strand='women/regional_synthesis')
rel('cdn_women_gender', 'cdn_women_gender', 'gender', 'contribution', 'Canadian debates over gender as a category', 'Canadian debates over gender history',
    f"Pierson's 1991 essay opens on feminist historians' turn to deconstruction and discourse analysis, naming Scott's theory of gender as the most acclaimed example. Parr (1995) and the 1995–96 Left History exchange (Sangster; Iacovetta and Kealey; Dubinsky and Marks) argued over gender history and women's history; those texts were checked at title level only. PhD context: {cs['overlap']} of {cs['engaged']} PhDs engaging this group cite Scott ({cs['share']:.0%} vs {cs['baseline_share']:.0%} of all; lift {cs['lift']}).",
    ['pierson_1991', 'parr_1995', 'sangster_1995', 'iacovetta_kealey_1996', 'dubinsky_marks_1996', 'scott_gender_1986'], 'opening_text_checked; debate_titles_only', target_strand='gender/gender', phd=cs)
rel('cdn_women_gender', 'cdn_women_gender', 'quebec_historiography', 'critique', 'Women\'s history questions a male-centred Quebec history', 'Women\'s history and Quebec historiography',
    "The Collectif Clio's introduction argues that a history centred on male figures had been presented as the collective history of the whole population. Lévesque's 1997 assessment says women's history redefined traditional Quebec history and hopes the slowness of some colleagues to integrate women is a matter of time and generation. A specific critique of how Quebec historiography treated women, not a rejection of that historiography.",
    ['clio_1982', 'levesque_1997'], 'excerpt_and_abstract_checked')
rel('cdn_women_gender', 'cdn_women_gender', 'cdn_working_class', 'contribution', 'Gender as a dimension of class and family economies', 'Gender in Canadian labour history',
    "Parr's comparison of a textile town where most wage earners were women with a furniture town challenges conventional views of the distinctiveness of gender and class roles (author's book page). Bradbury's Working Families (age, gender and family survival) and Sangster's Dreams of Equality (women on the left) are title-level. Contribution of gender analysis to labour history; it does not claim the new labour history lacked it entirely. " + t,
    ['parr_1990', 'bradbury_1993', 'sangster_1989'], 'description_checked; others_metadata', phd=r_wg_wc)
rel('cdn_women_gender', 'cdn_women_gender', 'consumption', 'comparison', 'Postwar domestic goods, magazines and households', 'Postwar domesticity and consumption',
    "Parr's Domestic Goods (1999), Korinek's reading of Chatelaine (2000) and Fahrni's Household Politics (2005) place women and households at the centre of postwar consumption. Title-level only: none of these books was read, so the comparison is a teaching pointer to the consumption entry, not a claim about their arguments.",
    ['parr_1999', 'korinek_2000', 'fahrni_2005'], 'bibliographic_metadata_only')
t, r_wg_nn = ov_text('cdn_women_gender', 'native_newcomer')
rel('cdn_women_gender', 'cdn_women_gender', 'native_newcomer', 'comparison', 'Women in fur-trade society', 'Fur-trade women',
    "Van Kirk's \"Many Tender Ties\" (1980) is cited by 60 of the 1303 PhDs and is among the most-cited works for this group's engaged PhDs, but its primary home is native_newcomer. Comparison only; title-level. " + t,
    ['vankirk_1980'], 'bibliographic_metadata_only', phd=r_wg_nn)

ca = cocite('cdn_childhood_youth', ARIES, 'Philippe Ariès (any work)')
rel('cdn_childhood_youth', 'demography', 'cdn_childhood_youth', 'comparison', 'Childhood and family as historical subjects', 'History of childhood and family',
    f"The demography umbrella's strand on childhood evidence (Ariès; Pollock) and its household studies can be read alongside Canadian childhood and family history, which grew from social and family history (Parr, ed., 1982; Bradbury, ed., 1992) more than from family reconstitution. PhD context: {ca['overlap']} of {ca['engaged']} PhDs engaging this group cite Ariès ({ca['share']:.0%} vs {ca['baseline_share']:.0%}; lift {ca['lift']}). Comparison; no descent from Ariès is asserted.",
    ['parr_1982', 'bradbury_1992', 'aries_childhood'], 'bibliographic_metadata_only', target_strand='demography/childhood_evidence', phd=ca)
t, r = ov_text('cdn_childhood_youth', 'cdn_women_gender')
rel('cdn_childhood_youth', 'cdn_women_gender', 'cdn_childhood_youth', 'comparison', 'Girls, mothers and families', 'Women, children and families',
    "Much of the childhood and family field grew within women's history: Strong-Boag on girls and women (1988), Bradbury on family economies (1993), Comacchio on saving mothers and children (1993), Baillargeon on the medicalization of maternity (2004). Shared people are rosters, not edges. " + t,
    ['strongboag_1988', 'bradbury_1993', 'comacchio_1993', 'baillargeon_2004'], 'bibliographic_metadata_only', phd=r)
t, r = ov_text('cdn_childhood_youth', 'cdn_sixties')
rel('cdn_childhood_youth', 'cdn_childhood_youth', 'cdn_sixties', 'comparison', 'The baby boom as a generation', 'Baby boom and the Sixties',
    "Owram's history of the baby-boom generation (1996) is the most-cited work for this group's engaged PhDs and also anchors cdn_sixties. Title-level. " + t,
    ['owram_1996'], 'bibliographic_metadata_only', phd=r)

fv = dict(cited='Michel Foucault (any work)', valverde_1991_citing_phds=len(VAL), also_cite_foucault=len(VAL & FOU),
          share=round(len(VAL & FOU) / len(VAL), 3), baseline_share=round(len(FOU) / N, 3), of=N)
cf = cocite('moral_regulation', FOU, 'Michel Foucault (any work)')
rel('moral_regulation', 'foucault', 'moral_regulation', 'influence', 'Foucauldian analysis in moral regulation and its governmentality reformulation', 'Foucault and moral regulation',
    f"Ruonavaara's abstract describes Corrigan and Sayer's framework as fusing Durkheimian and Foucauldian analysis with basic Marxist theory; Dean's abstract argues that problems in Corrigan's account are better formulated through Foucault's problematic of governmentality. PhD context: {fv['also_cite_foucault']} of {fv['valverde_1991_citing_phds']} PhDs citing Valverde 1991 also cite Foucault ({fv['share']:.0%} vs {fv['baseline_share']:.0%} of all PhDs). Influence is asserted on the concept's formulation, not on every Canadian study in the roster.",
    ['ruonavaara_1997', 'dean_1994'], 'abstract_checked', phd=dict(valverde=fv, group=cf))
rel('moral_regulation', 'historicalsociology', 'moral_regulation', 'contribution', 'State formation as cultural revolution', 'Corrigan and Sayer: The Great Arch',
    "Ruonavaara: Corrigan and Sayer introduced moral regulation to sociological debate in their historical sociology of English state formation, The Great Arch (1985). Adams applies it to state formation through Ontario VD policy. Corrigan and Sayer are not in the historicalsociology roster; this edge records a contribution from comparative historical sociology, not membership.",
    ['corrigan_sayer_1985', 'ruonavaara_1997', 'adams_1994'], 'abstract_checked')
rel('moral_regulation', 'moral_regulation', 'queer', 'contribution', 'Sexual regulation and the national-security campaign against queers', 'Kinsman: regulating desire',
    "Kinsman's The Regulation of Desire (1987) and Kinsman and Gentile's history of the security campaign that spied on, interrogated and harassed gays and lesbians from the 1950s to the late 1990s (publisher page read) contribute Canadian studies of sexual regulation. Complements the queer entry's regulation strand; it does not claim Canadian priority.",
    ['kinsman_1987', 'kinsman_gentile_2010'], 'publisher_page_checked', target_strand='queer/regulation')
t, r = ov_text('moral_regulation', 'liberal_order_framework')
rel('moral_regulation', 'moral_regulation', 'liberal_order_framework', 'comparison', 'Two projects on rule and the state', 'Moral regulation and the liberal order framework',
    "Boundary edge. The user decided (2026-10-12) that the liberal order framework is 'a different project closer to history of capitalism'. McKay's prospectus maps Canada as a project of liberal rule; moral regulation studies the governance of conduct and selves. They share state formation (Corrigan and Sayer; Adams; Curtis's census history), so a comparison rather than a contribution in either direction. " + t,
    ['mckay_2000', 'adams_1994', 'curtis_2001'], 'abstract_checked', phd=r, extra={'decision': 'Kept separate: "a different project closer to history of capitalism" (user, 2026-10-12).'})
t, r = ov_text('moral_regulation', 'cdn_religion_reform')
rel('moral_regulation', 'moral_regulation', 'cdn_religion_reform', 'comparison', 'Protestant reformers as regulators and as religious actors', 'Moral reform and the churches',
    "Valverde studies the moral fervour of Protestant social reformers (publisher description); the religion-and-reform entry studies the same churches and social gospel as religious history (Christie and Gauvreau 1996, title-level). The two fields read the reformers differently; no critique is asserted because the checked texts do not state one. " + t,
    ['valverde_1991', 'christie_gauvreau_1996'], 'description_checked; other_metadata', phd=r)
t, r = ov_text('moral_regulation', 'cdn_women_gender')
rel('moral_regulation', 'moral_regulation', 'cdn_women_gender', 'comparison', 'Women, girls, sexuality and the law', 'Regulating women and girls',
    "Feminist legal and sexual histories sit in both fields: Backhouse (1991), Lévesque (1989), Dubinsky (1993), Strange (1995), Sangster (2001), and Little's study of the moral scrutiny of single mothers (1994, abstract read). Shared people are rosters, not edges. " + t,
    ['backhouse_1991', 'levesque_1989', 'dubinsky_1993', 'strange_1995', 'little_1994'], 'abstract_checked; others_metadata', phd=r)
t, r = ov_text('moral_regulation', 'cdn_childhood_youth')
rel('moral_regulation', 'moral_regulation', 'cdn_childhood_youth', 'comparison', 'Youth, normality and the psy-sciences', 'Regulating the young',
    "Adams studies discourses on youth, delinquency, indecent literature and sex education as producers of heterosexual norms (publisher description); Gleason studies psychology and the normal family. " + t,
    ['adams_1997', 'gleason_1999'], 'description_checked', phd=r)
t, r = ov_text('moral_regulation', 'cdn_immigration_ethnicity')
rel('moral_regulation', 'moral_regulation', 'cdn_immigration_ethnicity', 'comparison', 'Moral reform, racial purity and law', 'Racial purity and regulation',
    "Valverde's reformers linked sexual health to racial purity (publisher description); Backhouse's Colour-Coded traces racism through law (title-level). " + t,
    ['valverde_1991', 'backhouse_1999'], 'description_checked; other_metadata', phd=r)
rel('moral_regulation', 'moral_regulation', 'medicalhistory', 'comparison', 'Disease, eugenics and the body as objects of regulation', 'Medicine and moral regulation',
    "Adams reads Ontario's 1918 commission on venereal disease and feeble-mindedness as targeting bourgeois-defined immorality as much as infection (abstract). McLaren on eugenics and Mitchinson on women and their doctors are title-level. Comparison with the medical history entry, not a claim that medical history is regulatory history.",
    ['adams_1994', 'mclaren_1990', 'mitchinson_1991'], 'abstract_checked; others_metadata')

co = cocite('cdn_immigration_ethnicity', OMIW, 'Michael Omi or Howard Winant')
rel('cdn_immigration_ethnicity', 'racial_formation', 'cdn_immigration_ethnicity', 'comparison', 'Race as a historically made category', 'Racial formation and Canadian race history',
    f"Anderson (1987, abstract read) treats racial categories as cultural ascriptions whose construction cannot be taken for granted and shows government inscribing 'Chinese' and 'Chinatown' in practice and space; racial formation treats race as historically specific and produced through social and political relations. Parallel, not derivation: PhD context shows Omi or Winant cited by {co['overlap']} of {co['engaged']} PhDs engaging this group (and by {round(co['baseline_share']*N)} of {N} overall).",
    ['anderson_1987', 'backhouse_1999', 'omi_winant'], 'abstract_checked', phd=co)
rel('cdn_immigration_ethnicity', 'cdn_immigration_ethnicity', 'black', 'contribution', 'African-Canadian historiography', 'African-Canadian history',
    "Walker's 1997 essay (full text read) identifies five orientations in African-Canadian historiography by the role they assign to Black people (Clients, Victims, Achievers, Community, Survivors), and dates the Community orientation to the social-history movement and his own Black Loyalists (1976). Winks (1971) and Trudel (1960) are earlier works. A Canadian contribution to Black history; it does not make Black history a subfield of immigration history.",
    ['walker_1997a', 'walker_1976', 'winks_1971', 'trudel_1960'], 'full_text_checked')
rel('cdn_immigration_ethnicity', 'identity', 'cdn_immigration_ethnicity', 'comparison', 'Ethnicity, recognition and the politics of its discovery', 'Ethnic history and identity histories',
    "Perin's opening asks whether it is coincidence that ethnic groups were 'discovered' when the US faced the civil rights movement and Canada an assertive Quebec nationalism. The identity umbrella groups historical recovery with struggles over exclusion and recognition and is itself open to criticism. Comparison; Perin's full argument was not read.",
    ['perin_1983'], 'opening_text_checked', target_strand='identity/multicultural')
t, r = ov_text('cdn_immigration_ethnicity', 'cdn_working_class')
rel('cdn_immigration_ethnicity', 'cdn_immigration_ethnicity', 'cdn_working_class', 'comparison', 'Immigrant workers and labour radicalism', 'Immigrant workers',
    "Avery's 'Dangerous Foreigners' (1979; reviewed by Bruno Ramirez in International Labor and Working-Class History) and Ramirez's On the Move (1991) study immigrant workers; Iacovetta's 'Manly Militants' (1995) reviews how historians wrote about immigrants (title-level). " + t,
    ['avery_1979', 'ramirez_1991', 'iacovetta_1995'], 'bibliographic_metadata_only', phd=r)
t, r = ov_text('cdn_immigration_ethnicity', 'cdn_women_gender')
rel('cdn_immigration_ethnicity', 'cdn_immigration_ethnicity', 'cdn_women_gender', 'comparison', 'Immigrant, ethnic and racialized women', 'Immigrant and ethnic women',
    "Iacovetta (1992), Swyripa (1993) and Epp, Iacovetta and Swyripa, eds., Sisters or Strangers? (2004) work at the meeting of the two fields. Title-level. " + t,
    ['iacovetta_1992', 'swyripa_1993', 'epp_2004'], 'bibliographic_metadata_only', phd=r)
t, r = ov_text('cdn_immigration_ethnicity', 'native_newcomer')
rel('cdn_immigration_ethnicity', 'cdn_immigration_ethnicity', 'native_newcomer', 'comparison', 'Citizenship programmes for newcomers and Indigenous peoples', 'Citizenship, immigrants and Indigenous peoples',
    "Bohaker and Iacovetta (abstract read) show that from 1950 to 1966 the Indian Affairs branch sat in the Department of Citizenship and Immigration and modelled its activities on citizenship campaigns for immigrants. A post-2000 comparison across the two fields. " + t,
    ['bohaker_iacovetta_2009'], 'abstract_checked', phd=r)

CONSIDERED = {
 'cdn_women_gender': [
  dict(pair='cdn_women_gender – moral_regulation', reason='Proposed in drafts/moral_regulation (one edge per pair).'),
  dict(pair='cdn_women_gender – cdn_childhood_youth', reason='Proposed in drafts/cdn_childhood_youth.'),
  dict(pair='cdn_women_gender – cdn_immigration_ethnicity', reason='Proposed in drafts/cdn_immigration_ethnicity.'),
  dict(pair='cdn_women_gender – settler_colonialism', reason="Perry's On the Edge of Empire is the most-cited work for this group's engaged PhDs but is primary in the settler packet; leave the edge to that packet."),
  dict(pair='language → cdn_women_gender', reason="Palmer's and Pierson's engagement with discourse analysis is checked only at title or opening level; a debate strand is enough for now."),
  dict(pair='cdn_women_gender – medicalhistory', reason='Mitchinson and Baillargeon fit, but the medical framing is unchecked; moral_regulation carries the medicine comparison.'),
  dict(pair='cdn_women_gender – cdn_religion_reform', reason="Danylewycz, Marks and Christie link them; no checked text states the link."),
 ],
 'cdn_childhood_youth': [
  dict(pair='cdn_childhood_youth – moral_regulation', reason='Proposed in drafts/moral_regulation.'),
  dict(pair='cdn_childhood_youth – native_newcomer / settler_colonialism', reason='Residential schooling of Indigenous children is the obvious link, but no work in this draft studies it; leave to those entries.'),
  dict(pair='cdn_childhood_youth – quebec_historiography', reason='Marshall, Ménard, Baillargeon and Myers are Quebec studies, but no checked text frames them against Quebec historiography.'),
  dict(pair='cdn_childhood_youth – medicalhistory', reason='Comacchio, Baillargeon and Gleason on health fit; framing unchecked.'),
  dict(pair='cdn_childhood_youth – cdn_working_class', reason='Parr (1980) and Bradbury (1993) on child labour and family economies; covered via cdn_women_gender → cdn_working_class.'),
 ],
 'moral_regulation': [
  dict(pair='karl → moral_regulation', reason="Ruonavaara mentions a 'basic Marxist theory' in The Great Arch, but the historicalsociology contribution edge covers the root."),
  dict(pair='language – moral_regulation', reason='groups.json suggested it; the Foucault influence edge is the checked link.'),
  dict(pair='culture – moral_regulation', reason='groups.json suggested it; no checked text states it.'),
  dict(pair='gender – moral_regulation', reason='Covered through cdn_women_gender; no direct checked link.'),
 ],
 'cdn_immigration_ethnicity': [
  dict(pair='cdn_immigration_ethnicity – moral_regulation', reason='Proposed in drafts/moral_regulation.'),
  dict(pair='cdn_immigration_ethnicity → cdn_national_tradition (critique)', reason="Perin's 'third force' title suggests a critique of a dualist national historiography, but only the opening paragraph was read."),
  dict(pair='cdn_immigration_ethnicity – quebec_historiography', reason='Ramirez and Helly are Quebec studies; no checked framing.'),
  dict(pair='cdn_immigration_ethnicity – cdn_sixties', reason='Lift is high (shared anchors Palmer and Iacovetta) but no checked text.'),
  dict(pair='cdn_immigration_ethnicity – urbanhistory', reason="Anderson's Chinatown and Harney's neighbourhoods fit; framing unchecked."),
 ],
}

# ---------------- people/placement helpers ----------------
NAME2CAND = {}
for n in cands:
    last = n.split(',')[0].lower().replace('-', ' ')
    NAME2CAND.setdefault(last, []).append(n)
def placement(label):
    last = label.split()[-1].lower().replace('-', ' ')
    if last == 'boag': last = 'strong boag'
    hits = []
    for c in NAME2CAND.get(last, []):
        first = c.split(',')[1].strip().split()[0].lower().rstrip('.') if ',' in c else ''
        toks = label.lower().replace('.', '').split()[:-1]
        if first and any(t.startswith(first[:3]) for t in toks): hits.append(c)
    if not hits: return None, None
    c = hits[0]
    prim = [g['id'] for g in groups if c in g['primary']]
    also = [g['id'] for g in groups if c in g['also']]
    env = json.load(open('/home/jic823/historiography/data/extension-2026/canadian-historiography-groups-request-2026-10-12/groups.json'))['existing_entry_placements']
    for k, v in env.items():
        if c in v['primary']: prim.append(k)
        if c in v['also']: also.append(k)
    return c, dict(candidate_name=c, citing_phds_2009_2026=int(cands[c]['history_phds_2009_2026']), primary=prim, also=also, qid=cands[c]['qid'], qid_status=cands[c]['qid_status'])

# ---------------- build ----------------
def words(s): return len(re.findall(r"\S+", s))
def build(gid):
    c = G[gid]
    used = set()
    roster = []
    for pid, label, role, ctx, wks, sids in c['roster']:
        used |= set(sids)
        cand, plc = placement(label)
        roster.append(dict(person_id=pid, name=label, role=role, context=ctx, works=wks, source_ids=[sid(x) for x in sids],
                           basis='source_review', review_status='needs_review', existing_atlas_person=pid in ATLAS_PEOPLE,
                           **({'placement': plc} if plc else {'placement': None})))
    strands = []
    for stid, title, focus, pids, sids in c['strands']:
        used |= set(sids)
        strands.append(dict(id=stid, title=title, focus=focus, person_ids=pids, source_ids=[sid(x) for x in sids],
                            works='; '.join(SRC[x]['cit'] for x in sids if x in SRC), basis='editorial_distinction', review_status='needs_review'))
    rels = []
    considered = list(CONSIDERED[gid])
    i = 0
    for r in REL.get(gid, []):
        pair = frozenset((r['source'], r['target']))
        same_pair = [o for o in OTHER_RELS if frozenset((o['source'], o['target'])) == pair]
        dup = [o for o in same_pair if o['relationship_kind'] == r['relationship_kind']]
        if same_pair and not dup:
            o = same_pair[0]
            r = dict(r, evidence_note=r['evidence_note'] + f" Coexists with {o['proposal_id']} ({o['relationship_kind']}) in drafts/{o['draft']}: a broad {o['relationship_kind']} and this specific {r['relationship_kind']} can stand together, as GRAPH-FORMAT.md allows.")
        if dup:
            o = dup[0]
            considered.append(dict(pair=f"{r['source']} – {r['target']}",
                reason=f"Already proposed by another drafter as {o['proposal_id']} ({o['relationship_kind']}) in drafts/{o['draft']}; not duplicated. Evidence from this draft that could be merged into it: {r['evidence_note']} Sources: {', '.join(r['source_ids'])}."))
            used |= {x[len(PFX):] for x in r['source_ids'] if x.startswith(PFX)}
            continue
        i += 1
        used |= {x[len(PFX):] for x in r['source_ids'] if x.startswith(PFX)} | {x for x in r['source_ids'] if x in EXISTING_SRC}
        for end in (r['source'], r['target']):
            assert end in ATLAS_NODES or end in PROPOSED, end
        r = dict(proposal_id=f"{c['short']}_rel_{i:02d}", **r,
                 endpoint_status={e: ('existing_atlas_entry' if e in ATLAS_NODES else 'proposed_group') for e in (r['source'], r['target'])})
        rels.append(r)
    declared_by_others = [dict(draft=o['draft'], proposal_id=o['proposal_id'], source=o['source'], target=o['target'],
                               relationship_kind=o['relationship_kind'], relationship=o.get('relationship'))
                          for o in OTHER_RELS if gid in (o['source'], o['target'])]
    # relationships owned by other drafts that touch this group
    elsewhere = []
    for owner, rs in REL.items():
        if owner == gid: continue
        for r in rs:
            if gid in (r['source'], r['target']):
                elsewhere.append(dict(owner_draft=owner, source=r['source'], target=r['target'], relationship_kind=r['relationship_kind'], relationship=r['relationship']))
    for x in used:
        assert x in SRC or x in EXISTING_SRC, (gid, x)
    pids_r = {r['person_id'] for r in roster}
    for st in strands:
        for p in st['person_ids']: assert p in pids_r, (gid, p)
    src_ids = sorted(used - EXISTING_SRC, key=lambda x: (SRC[x]['year'], x))
    verified = [x for x in src_ids if SRC[x]['st'] != 'unverified']
    unverified = [s['id'] for s in S if gid_short(gid) in s['g'] and s['st'] == 'unverified']
    node = dict(id=gid, label=c['label'], entry_kind='group', entry_type=c['entry_type'], layer='historiographical_developments',
                period=c['period'], period_rationale=c['period_rationale'], hunt_core_paradigm=False,
                date_label=c['date_label'], date_span=c['date_span'], description=c['description'], description_words=words(c['description']),
                scope_note=c['scope_note'], representative_figures_and_works=c['rfw'],
                source_ids=[sid(x) for x in src_ids] + sorted(x for x in used if x in EXISTING_SRC),
                representative_people=roster, strands=strands,
                extension_coverage=dict(status='proposed', baseline_through=2000, research_cutoff=TODAY, field_review_complete=False,
                                        publication_years=c['extension_years'], note='Post-2000 works are selected extension milestones, not a reviewed post-2000 field.'))
    entry = dict(status='proposal_for_review', prepared=TODAY, applies_to='historiography-1920-2000.json (not modified)',
                 request='../../groups.json (user-reviewed structure, 2026-10-12)', node=node,
                 new_people=[dict(id=r['person_id'], label=r['name'], wikidata_qid=(r['placement'] or {}).get('qid'),
                                  qid_status=(r['placement'] or {}).get('qid_status'),
                                  qid_note='From the scholars packet (candidates.csv); not reviewed for the atlas.' if r['placement'] else 'Not in the scholars packet; no QID looked up.')
                             for r in roster if not r['existing_atlas_person']],
                 existing_source_reuse=sorted(x for x in used if x in EXISTING_SRC),
                 proposed_relationships=rels, relationships_proposed_in_other_drafts=elsewhere,
                 relationships_declared_in_other_drafters_drafts=declared_by_others,
                 relationships_considered_not_proposed=considered, open_questions=c['open_questions'],
                 unverified_sources_excluded=[sid(x) for x in unverified])
    # literature
    recs = []
    for x in src_ids + unverified:
        s = SRC[x]; ds, ws = work_citers(*s['rx'])
        recs.append(dict(id=sid(x), section=s['sec'], year=s['year'], citation=s['cit'], url=s.get('url') or (f"https://doi.org/{s['doi']}" if s.get('doi') else None),
                         doi=s.get('doi'), verification=dict(status=s['st'], checked_on=TODAY, checked_against=s['ca'], note=s['note']),
                         reading=s['reading'], used_in_proposed_sources=x in src_ids,
                         shared_with_drafts=sorted(GFULL[g] for g in s['g'] if GFULL[g] != gid),
                         same_work_in_other_drafters_drafts=same_work(s),
                         dissertations=dict(summ(ds), matched_work_records=len(ws)) if ds else dict(phds_2009_2026=0, of=N)))
    counts = collections.Counter(r['verification']['status'] for r in recs)
    lit = dict(status='proposal_for_review', prepared=TODAY,
               verification_vocabulary='As GRAPH-FORMAT.md: bibliographic_metadata_checked = identity/edition checked against the named record; supporting_page_checked = an abstract, description, contents page, opening text or full text was read for the point in the note; unverified = do not cite yet. No book was read in full.',
               id_note='Ids use the shared prefix cdnsrc_ across the four drafts by the same drafter (cdn_women_gender, cdn_childhood_youth, moral_regulation, cdn_immigration_ethnicity), so a work cited in two drafts has one id. Existing atlas sources are reused by their atlas ids.',
               dissertation_counts='Strict History PhDs completed 2009–2026 (n=1303) whose bibliographies cite any matched title variant; counted by dissertation, not citation. Title matching is regex-based on the citation graph and may miss variants.',
               records=recs, existing_atlas_sources_reused=sorted(x for x in used if x in EXISTING_SRC), counts=dict(records=len(recs), **counts))
    return entry, lit, verified, unverified

GFULL = {'cwg': 'cdn_women_gender', 'ccy': 'cdn_childhood_youth', 'mreg': 'moral_regulation', 'cie': 'cdn_immigration_ethnicity'}
MINE = set(GFULL.values())

# ---- other drafters' drafts (read-only) ----
import glob
OTHER_RELS, OTHER_SRCS = [], []
for f in sorted(glob.glob(OUT + '*/entry-draft.json')):
    g = f.split('/')[-2]
    if g in MINE: continue
    try: d = json.load(open(f))
    except Exception: continue
    for r in d.get('proposed_relationships', []):
        OTHER_RELS.append(dict(r, draft=g))
    for r in d.get('proposed_source_records', []) or []:
        OTHER_SRCS.append(dict(r, draft=g))
for f in sorted(glob.glob(OUT + '*/literature.json')):
    g = f.split('/')[-2]
    if g in MINE: continue
    try: d = json.load(open(f))
    except Exception: continue
    for r in d.get('records', []) or []:
        OTHER_SRCS.append(dict(r, draft=g))
def _norm(t): return re.sub(r'[^a-z]', '', (t or '').lower())
def _key_title(cit):
    m = re.search(r'[,"“]\s*(?:eds?\.,\s*)?["“]?([^"”(]{12,})', cit or '')
    return _norm(m.group(1))[:40] if m else ''
def same_work(s):
    out = set()
    kt = _key_title(s['cit'])
    for o in OTHER_SRCS:
        oc = o.get('citation') or o.get('title') or ''
        if (s.get('doi') and o.get('doi') and s['doi'].lower() == str(o['doi']).lower()) or (kt and len(kt) >= 20 and kt in _norm(oc) and str(s['year']) in oc):
            out.add(f"{o['draft']}:{o['id']}")
    return sorted(out)
def gid_short(gid): return G[gid]['short']

def evidence(gid):
    e = dict(prepared=TODAY, corpus='data/field-research/dissertation-citations-2026-10-11/graph.json; Dissertation nodes with in_analysis true and year 2009–2026', denominator=N,
             early_window='2009–2014', early_n=len(EARLY), late_window='2020–2026', late_n=len(LATE),
             francophone_universities=sorted(FR), francophone_university_phds=len([d for d in diss if diss[d]['inst'] in FR]),
             method='Engagement = PhDs citing works by at least two of the group\'s anchor people (groups.json primary + also), with identity cleanup from the scholars packet, as in groups_evidence.py. Pairwise overlaps drop anchors shared by both groups before recomputing engagement, so shared people do not inflate them.',
             engagement=dict(summ(ENG[gid]), anchors=anchors(gid)),
             anchor_citing_phds={n: len(pc(n)) for n in anchors(gid)},
             pairwise_overlap_shared_anchors_removed=[overlap(gid, b) for b in sorted(PROPOSED) if b != gid],
             theory_cocitation=[cocite(gid, FOU, 'Michel Foucault (any work)'), cocite(gid, SCOTT, 'Joan W. Scott (any work)'),
                                cocite(gid, ARIES, 'Philippe Ariès (any work)'), cocite(gid, OMIW, 'Michael Omi or Howard Winant')],
             caveats=['Bibliographies record consultation, not influence or adoption.', 'Anchor-based engagement favours groups with more anchors; compare trends, not levels.',
                      'Lifts between Canadian groups are high in general because the corpus is mostly Canadian history PhDs.', 'Francophone coverage: Laval has only 9 in-analysis PhDs.'])
    if gid == 'moral_regulation':
        e['valverde_1991_foucault'] = fv
    return e

def notes(gid, entry, lit, verified, unverified):
    c = G[gid]; n = entry['node']
    L = [f"# {c['label']} (`{gid}`): drafting notes", '', f"Prepared {TODAY}. Proposal only; the atlas is not modified.", '',
         f"- **Entry:** {c['entry_type']}, `{c['period']}`. Date label: {c['date_label']}.",
         f"- **Description:** {n['description_words']} words. **Roster:** {len(n['representative_people'])} people. **Strands:** {len(n['strands'])}.",
         f"- **Sources:** {len(verified)} verified ({sum(1 for x in verified if SRC[x]['st']=='supporting_page_checked')} with a supporting page read, {sum(1 for x in verified if SRC[x]['st']=='bibliographic_metadata_checked')} metadata only); {len(unverified)} unverified and excluded" + (f" ({', '.join(unverified)})" if unverified else '') + '.',
         f"- **PhD engagement:** {len(ENG[gid])} of {N} PhDs ({len(ENG[gid])/N:.0%}); {summ(ENG[gid])['share_2009_14']:.1%} (2009–14) → {summ(ENG[gid])['share_2020_26']:.1%} (2020–26); {summ(ENG[gid])['francophone_university_phds']} at francophone universities.",
         '', '## Proposed relationships', '']
    for r in entry['proposed_relationships']:
        arrow = '—' if r['relationship_kind'] == 'comparison' else '→'
        L.append(f"- `{r['source']}` {arrow} `{r['target']}` ({r['relationship_kind']}): {r['relationship']}. Evidence: {r['evidence_strength']}.")
    if entry['relationships_proposed_in_other_drafts']:
        L += ['', 'Proposed in my other drafts (one edge per pair): ' + '; '.join(f"`{r['source']}`–`{r['target']}` ({r['relationship_kind']}, in {r['owner_draft']})" for r in entry['relationships_proposed_in_other_drafts']) + '.']
    if entry['relationships_declared_in_other_drafters_drafts']:
        L += ['', "Edges touching this entry in other drafters' drafts: " + '; '.join(f"`{r['source']}`–`{r['target']}` ({r['relationship_kind']}, {r['proposal_id']} in {r['draft']})" for r in entry['relationships_declared_in_other_drafters_drafts']) + '.']
    dups = [x for x in entry['relationships_considered_not_proposed'] if x['reason'].startswith('Already proposed by another drafter')]
    if dups:
        L += ['', 'Not duplicated (already proposed by another drafter; my evidence is recorded for merging): ' + '; '.join(f"`{x['pair']}`" for x in dups) + '.']
    L += ['', '## Judgement calls', ''] + [f"- {x}" for x in JUDGEMENT[gid]] + ['', '## Questions for the user', ''] + [f"- {q}" for q in c['open_questions']]
    return '\n'.join(L) + '\n'

JUDGEMENT = {
 'cdn_women_gender': [
  "Women's history and gender history are one entry with a debate strand, following groups.json; the label keeps both.",
  "The Collectif Clio and Lévesque are placed here, with a critique edge to quebec_historiography, so that francophone women's history is not only a Quebec topic.",
  "Claims about the 1995–96 Left History exchange stay at title level because the journal site blocked automated access.",
  "Parr's 1995 CHR essay is used for the debate strand only by title; its opening paragraph does not state the argument.",
  "Palmer is a 'critic' only of discourse analysis in social history, by title; no claim that he criticised a named Canadian gender historian.",
  "Van Kirk, Perry and Christie appear only as comparison edges or strand sources, not roster rows, because their primary placements are elsewhere.",
 ],
 'cdn_childhood_youth': [
  "Entry type 'Topic field' per the user's decision; period_3 for expansion, with Sutherland 1976 as the earliest selected milestone.",
  "Sutherland is characterised only through the WLU Press description (reformers committed to social improvement); the rest of his argument is unread.",
  "Owram, Parr, Bradbury, Strong-Boag, Sangster and Baillargeon are roster rows with their primary placements noted; rosters are not edges.",
  "Francophone work (Marshall, Ménard, Baillargeon) and Montreal work in English (Myers, Bradbury) are included in the main strands, not a separate Quebec strand.",
  "No critic row: Gleason 2016 critiques approaches to agency from within the field; no external critique was checked.",
 ],
 'moral_regulation': [
  "The liberal order boundary is kept explicit: the comparison edge is lof_rel_08 in the liberal_order_framework draft (not duplicated here; my evidence is recorded for merging), Curtis is kept out of the roster, and McKay is cited only for the boundary.",
  "Corrigan and Sayer are precursors (international roots), characterised only through Ruonavaara's abstract; The Great Arch was not read.",
  "Foucault is an influence edge, not a roster row; Dean and Ruonavaara are critics because their abstracts reformulate the concept.",
  "Valverde and Weir (1988) is excluded as unverified even though it is often treated as the first Canadian statement.",
  "Kinsman and Gentile (2010) and Sangster (2001) are post-2000 extension works.",
 ],
 'cdn_immigration_ethnicity': [
  "Black Canadian history is a strand here, not a sub-field; the contribution edge goes to the atlas's black entry. A separate Canadian Black history entry is an open question.",
  "Walker's 'Allegories and Orientations' is cited as Dalhousie Review 77:2 (1997), checked in full text; the request's CHR 1999 citation was wrong.",
  "Anderson is a contributor, not a critic of Ward: no checked text states a critique.",
  "Harney's Daedalus essay is excluded as unverified; Gathering Place stands in.",
  "Racial formation is a comparison edge: Omi and Winant are almost never cited by these PhDs, so derivation is not asserted.",
 ],
}

if __name__ == '__main__':
    report = {}
    for gid in ['cdn_women_gender', 'cdn_childhood_youth', 'moral_regulation', 'cdn_immigration_ethnicity']:
        entry, lit, verified, unverified = build(gid)
        d = OUT + gid + '/'; os.makedirs(d, exist_ok=True)
        json.dump(entry, open(d + 'entry-draft.json', 'w'), ensure_ascii=False, indent=1)
        json.dump(lit, open(d + 'literature.json', 'w'), ensure_ascii=False, indent=1)
        json.dump(evidence(gid), open(d + 'evidence.json', 'w'), ensure_ascii=False, indent=1)
        open(d + 'NOTES.md', 'w').write(notes(gid, entry, lit, verified, unverified))
        report[gid] = dict(words=entry['node']['description_words'], roster=len(entry['node']['representative_people']), strands=len(entry['node']['strands']),
                           verified=len(verified), unverified=unverified, rels=len(entry['proposed_relationships']), lit=lit['counts'])
    print(json.dumps(report, indent=1))
