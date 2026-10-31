"""Apply the narrow corrections found during the complete researcher audit."""
import json
from pathlib import Path
from record import edge

HERE=Path(__file__).resolve().parent
p=HERE/'upgrades.json';q=json.loads(p.read_text())

q['caroline_walker_bynum']['new_source_updates']={
 'tc232_bynum_paradox':{'verification':dict(status='supporting_page_checked',checked_on='2026-10-31',note='Author’s institutional posting; earlier pp. 434–435,442–447 reading extended to selected pp. 434–438,442–450 for Chenu, Grundmann, gender, practical dualism and historical particularity. Neither complete article nor selected books read in full; named intellectual resources do not assert newly read originals.')}}
q['caroline_walker_bynum']['node_fields']['scope_note']=q['caroline_walker_bynum']['node_fields']['scope_note'].replace('Later batch may add the specifically documented Laqueur reception once that endpoint exists.','The later Laqueur packet supplies the specifically documented resource/reception relationship once his endpoint exists.')

s='tq232_bynum_body1995';pid='thomas_laqueur'
e=edge(pid,'bynum',pid,'caroline_walker_bynum','Bynum uses Laqueur’s study for the Renaissance emphasis on organ systems while retaining Park and Nye’s qualification about earlier humoral models.',s,'Primary Bynum 1995 pp. 7–8/n24: explicit positive appraisal and reference supporting her discussion, followed by a named report of criticism. Resource/reception, not personal influence; Park/Nye’s objection is not silently made Bynum’s own original critique.')
q[pid]['edges']=[x for x in q[pid]['edges'] if x['proposal_id']!=e['proposal_id']]+[e]
q[pid]['existing_source_ids']=list(dict.fromkeys(q[pid]['existing_source_ids']+[s]))
read=dict(source_id=s,locator='Bynum 1995 pp. 7–8/n24, positive appraisal plus named-reader qualification')
if read not in q[pid]['review']['passage_reads']:q[pid]['review']['passage_reads'].append(read)

q['charles_s_maier']['new_source_updates']={
 'tq233_maier_metadata2000':{'verification':dict(status='bibliographic_metadata_checked',checked_on='2026-10-31',note='Harvard DASH cover/record checks the original AHR 105:3 (June 2000),807–831, DOI 10.2307/2651811. Body unread; local request rate-limited and not retried. Not argument evidence.')}}
q['stephen_greenblatt']['new_source_updates']={
 'tc234_greenblatt_interview':{'title':'Corydon Ireland, interview with Stephen Greenblatt, Harvard Gazette, 3 June 2014.','citation':'Corydon Ireland, interview with Stephen Greenblatt, Harvard Gazette, 3 June 2014.','verification':dict(status='supporting_page_checked',checked_on='2026-10-31',note='Primary professional answers extended from the earlier Self-Fashioning discussion to Cambridge influences, Williams, New Criticism and continued use of formalist training. Article header dates 3 June 2014, correcting earlier draft title. Personal/family detail excluded; selected answers, not video or complete book reading.')}}

# Update expanded scopes on unaccepted records without altering old graph sources.
for pid,sid,note in [
 ('mike_davis','tc234_davis_marxist','Publisher excerpt: earlier seminar/theory reading extended to selected later professional paragraphs on Marx’s geographical/urban and patriarchal limits. No family detail, quoted community content or numerical claims retained. Marx originals and complete book unread; criticism remains Davis’s attributed assessment.'),
 ('robert_bartlett','tc234_bartlett_race','Earlier opening pp. 39–40 reading extended through selected pp. 39–43,45–47,52–53 in authorized St Andrews repository copy. Both categories constructed; medieval cultural/descent distinctions and relation to sovereignty examined. Not full article/book or independent medieval-source reading.')]:
 q[pid].setdefault('new_source_updates',{})[sid]={'verification':dict(status='supporting_page_checked',checked_on='2026-10-31',note=note)}

p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
