"""Record the primary researcher's completed claim review, not independent acceptance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

# Individual judgments from the complete review of the final prose, relationships,
# locators, attribution, chronologies and holds. These are not generated from counts.
JUDGMENTS={
 'nancy_christie':'McKay criticism is qualified by the framework’s synthesizing value. Curtis’s particular text stays unidentified; Habermas is a selective resource. Gauvreau coauthorship and employer hold remain.',
 'james_rodger_miller':'Haig-Brown objections accompany the synthesis. Gélinas frames the treaty book as a political history without claiming a wholly new interpretation. Ray comparison supplies no influence edge. No testimony or treaty knowledge retained.',
 'bruce_trigger':'Wolf supplies a named methodological reading, not proof of Wolf’s influence. LaRocque’s two objections and her qualified acknowledgment remain together. Settler identity is distinct from Indigenous-authored historiography; OCAP exclusions checked.',
 'caroline_walker_bynum':'Primary retrospective and body essay ground historical particularity and qualified Butler engagement. Chenu/Grundmann resources have no endpoints. Expanded source scope corrected; later packet carries the Laqueur connection after his endpoint exists.',
 'barbara_h_rosenwein':'Febvre resource, Elias critique and Peter/Carol Stearns criticism keep separate scopes. Reddy’s plural-regime answer remains beside her objection. Reused documented passages are not presented as fresh complete readings.',
 'joanna_bourke':'Fear contribution now rests on a primary methodological argument about expression, embodiment and emotives. Earlier war/gender descriptions remain explicitly mediated. No unsupported Stearns link from shared terminology; no patient content retained.',
 'keith_thomas':'Own interview supports Hill/Tawney resources, Febvre’s particular Annales strand and Stone’s encouragement. Thomas’s admitted explanatory limits coexist with Machielsen/Pfeffer reception. Hildred and Clifford Geertz remain distinct.',
 'john_h_elliott':'Kagan/Parker mediation is explicit for Febvre, qualified Braudel criticism and the exchange with Ginzburg/Davis. Death-date correction to 9 March is retained alongside the earlier notice, with full source conflict in life evidence.',
 'john_m_mackenzie':'Sèbe’s accepted manuscript supplies empirical challenge to Said and Porter-debate framing. Earlier Said criticism remains separately scoped; no transfer of all criticisms of Hall. Edited collection and original/reissue dates remain distinct.',
 'callum_g_brown':'Primary atheism article supports criticism of Taylor and Febvre; originals remain unread. Morris criticism is an abstract-only witness. Scotland edition label and Death 2001 are retained despite differing profile shorthand.',
 'jonathan_israel':'Bell’s substantive review supplies transmission/context/causation objections while crediting range. Lilti remains abstract/notes only. Contextualism is an undirected comparison, not affiliation or Skinner’s personal response.',
 'geoffrey_parker':'Black’s methodological criticism excludes personal polemic. Elliott’s concrete guidance comes through Parker’s coauthored memoir. Rogers remains a participant-editor witness. No universal global mortality estimate adopted.',
 't_m_devine':'Extended primary slavery argument distinguishes direct voyages from plantation economy. Joint introduction credits Wormald equally. Morton/Griffiths question national framing; no wholesale Williams adoption or nationalist political allegiance inferred.',
 'richard_j_evans':'Primary introduction supports specific agreement with White, criticism of Joyce’s inevitability claim, and Cannadine’s draft contribution. Hamburg/trial contexts remain institutional accounts, not independently read evidence or full books.',
 'thomas_laqueur':'Holmes’s interpretation and criticism are attributed. Bynum’s explicit use and positive appraisal retain the Park/Nye qualification as reported criticism. No personal transmission, one-model consensus or unread reply assumed.',
 'charles_s_maier':'Primary interview supports territoriality and its qualifications. Breuilly/Chatterjee comparison is conference-report mediated. DASH is metadata only; status corrected. Charles and Pauline Maier remain distinct.',
 'e_h_carr':'Chapter-one selection/interpretation argument retains transcription limits. Evans supplies dated later reception, not a self-described 1961 postmodernism. Soviet/international books do not create unverified argument edges.',
 'judith_r_walkowitz':'Own Spanish interview supports White, Thompson and qualified Foucault engagement. Interviewer suggestions do not create extra links. Her simultaneous urban narrative and caution about selective reception qualify the project descriptions.',
 'paul_kennedy':'2026 own response acknowledges India and economic-determinism criticisms. Mahan/Campbell stimulus is mediated and uses the existing strategic-tradition endpoint. Publication-year 1987 and appearance early 1988 remain distinguished.',
 't_c_smout':'Primary chapter explicitly uses Wrigley and identifies Cronon as a model for research still needed. This is no automatic transfer of findings. Earlier green-consciousness argument and national-frame criticism remain separate.',
 'david_arnold':'New primary introduction supplies situated science and a specific, qualified Basalla critique. Shapin is a named conceptual resource. Narrow Foucault witness remains distinct; older professional page does not prove current living status.',
 'j_r_mcneill':'Reused survey supports qualified Annales resource and Crosby appraisal; criticism by other readers is not reassigned. Fresh address methods distinguish scientific opportunity from monocausal explanation. John and William are not merged.',
 'sheila_fitzpatrick':'Joint opening extract credits Lüdtke equally and qualifies Arendt’s atomization hypothesis while retaining support from below. Retrospective is abstract/notes only. Everyday scale does not prove microhistory affiliation.',
 'patrick_geary':'Fanning’s substantive opening/conclusion credits thesis but cautions about factual generalization. Full national/medieval books remain unread and no review becomes an influence. Institutional memory account is still marked as mediation.',
 'mike_davis':'Primary seminar account supports Marx resource via Brenner; later critical remarks remain Davis’s assessments. Williams use is explicit. Sweeping city assertion and quantitative claims are not endorsed as independent findings.',
 'hugh_trevor_roper':'Worden supplies specific limits of court/country and explains contingency, Elliott’s draft intervention and Continental research plans. Original manuscripts unread. Earlier abandonment is not explained by the later authentication failure.',
 'peter_gay':'Freud resource coexists with criticism of reductionist psychohistory. Neumann stimulus is own testimony. Outside circumstances remain causal; no clinical or theoretical consensus asserted. Professional excerpt is not a full recording.',
 'paul_thompson':'Own thematic excerpt and Taylor’s substantive reassessment distinguish early reliability from later subjectivity, and scholarly archive reuse from fixed worker categories. Hobsbawm commission does not credit him with endorsing oral method. Coauthors retained; no narrator content.',
 'kathleen_wilson':'Primary 2004 introduction replaces a projected-only national argument with read historical-method framing. Chakrabarty, Hall and Foucault uses are specified. Coercion and negotiation coexist; no invented QID or birth year.',
 'charles_e_rosenberg':'Interviewer’s teacher attribution is distinguished from own answers. Social medicine and diagnosis categories are methodological claims; prompted Foucault/Gramsci names do not establish influence. No present clinical or policy assertion retained.',
 'robert_bartlett':'Expanded primary reading shows both categories socially constructed, acknowledges descent idioms and distinguishes sovereignty. Heng criticism remains separate. Racial-formation school rejection is specifically about Omi/Winant, not exclusion of all race history.',
 'stephen_greenblatt':'Own interview credits Williams and retains formalist training. Culture excerpt supports constraint/mobility. Monfasani criticism and author reply coexist without validating the disputed thesis. Interview date corrected; theorist type and linguistic-turn hold remain.'
}

def main():
    q=read(HERE/'upgrades.json');progress=read(HERE/'progress.json')
    assert set(JUDGMENTS)==set(q)=={x['person_id'] for x in progress['people']}
    rows=[]
    for person in progress['people']:
        pid=person['person_id'];b=person['batch']
        folder=ROOT/f'data/extension-2026/timeline-canon-batch{b}-2026-10-31'/pid
        d=read(folder/'entry-draft.json');notes=read(folder/'research-notes.json');life=read(folder/'life-status.json')
        assert d['node']['description']==q[pid]['node_fields']['description']
        assert q[pid]['review']['passage_reads'] and q[pid]['review']['remaining_limits']
        status='researcher_review_complete'
        q[pid]['review'].update(status=status,audit_note=JUDGMENTS[pid])
        d['quality_review']=deepcopy(q[pid]['review']);notes['quality_review']=deepcopy(q[pid]['review'])
        person['status']=status
        content={k:d[k] for k in ['node','proposed_edges','new_sources','roster_additions']}
        rows.append(dict(person_id=pid,batch=b,status=status,audit_note=JUDGMENTS[pid],
            passage_reads=deepcopy(q[pid]['review']['passage_reads']),remaining_limits=deepcopy(q[pid]['review']['remaining_limits']),
            reviewed_fields=list(content)+['context_decisions','life-status.json'],
            reviewed_content_sha256=digest(content),context_decisions_sha256=digest(notes['context_decisions']),life_evidence_sha256=digest(life)))
        write(folder/'entry-draft.json',d);write(folder/'research-notes.json',notes)
    progress.update(status='researcher_review_complete',independent_review='Pending Claude; this is a researcher self-audit, not an independent pass',final_audit='final-audit.json')
    write(HERE/'upgrades.json',q);write(HERE/'progress.json',progress)
    write(HERE/'final-audit.json',dict(status='researcher_review_complete',checked_on='2026-10-31',
        reviewer='Codex primary researcher',independent_review='Pending Claude acceptance; no independent review asserted',
        standard='Specific historical arguments, substantive primary or named scholarly readings, scoped resources and criticism, supported additive contexts and clear metadata/reading boundaries. No relationship or reading-length quota.',
        scope='All 32 final biographies, proposed relationships and locators, new-source scopes, context decisions, publication chronology and life evidence. Earlier canonical edges/sources remain protected.',
        people=rows))

if __name__=='__main__':main()
