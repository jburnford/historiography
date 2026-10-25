"""Explicit reviewed copy; preserve all IDs, URLs, dates and substantive claims."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent
S={
'certeau_life':('Savoie Mont Blanc University LLSETI, Michel de Certeau centenary.','Read the institutional opening biography: born in Chambéry in1925, died in Paris in1986. Used for life years only.'),
'certeau_loudun':('BnF: La Possession de Loudun, texts selected and presented by Michel de Certeau (Julliard,1970).','Checked author/editor fields and the1970publication. Scientific editing and presentation of historical texts are retained as credits; the volume body remains unread.'),
'certeau_original':('BnF, La société de consommation: selected bibliography (2024), de Certeau, Arts de faire.','The national-library bibliography explicitly gives1980as the original date of L’invention du quotidien,1: Arts de faire. Date metadata only.'),
'certeau_writing':('MSH Editions: Das Schreiben der Geschichte; original L’écriture de l’histoire (Gallimard,1975).','The publisher explicitly identifies the French original as1975. The later German translation is not dated as the original contribution. Metadata only.'),
 'tilly_coercion':('Charles Tilly, Coercion, Capital, and European States, AD990–1990, original copyright and imprint (Blackwell,1990).','Checked the indexed primary title and copyright page: first published1990, with the original title AD990–1990. The later AD990–1992revision remains distinct. The chapter body is not used as substantive evidence.'),
 'tilly_life':('Columbia University, “University Mourns Charles Tilly” (2008).','Read the full institutional obituary, dates and selected works. It states birth on May27,1929and death on April29,2008. Its inconsistent date for The Contentious French is not adopted; an existing publisher-reviewed source independently grounds that publication year.'),
 'tilly_war':('Charles Tilly, “War Making and State Making as Organized Crime,” in Bringing the State Back In, edited by Peter Evans, Dietrich Rueschemeyer and Theda Skocpol (Cambridge,1985),169–191.','Read printed169–172of the primary chapter scan. The argument is tentative and concerns European state formation. Tilly rejects reading contemporary countries’ futures directly from Europe’s past. Editor credits are retained; the rest of the chapter remains unread.'),
'mitchell_carbon':('PRH/Verso: Timothy Mitchell, Carbon Democracy (2011; later paperbacks2013and2023).','The formats and dates list the2011ebook and later paperbacks. The original2011copyright is also visible on the indexed original title page. No body reading or oil-specific relationship is inferred.'),
'mitchell_experts':('UC Press: Timothy Mitchell, Rule of Experts: Egypt, Techno-Politics, Modernity (2002).','Checked the publisher’s title, author and November2002publication date. The substantive body remains unread.'),
'mitchell_life':('Columbia Buell Center: Abundance Talks, The Alibi of Capital,22October2026.','Read the dated institutional announcement identifying Columbia’s Timothy Mitchell and his scheduled22October2026talk with Zeynep Çelik Alexander. This is positive current evidence of scheduled participation; attendance is unconfirmed.'),
'mitchell_preface':('Timothy Mitchell, Colonising Egypt, preface to the paperback edition (UC Press,1991; original1988).','Read selected passages of the paperback preface, ix–xiii, including disciplinary spatial arrangements and exhibitionary order. These are primary author passages. The preferred citation gives1988, whereas this edition’s copyright is1991. Body chapters remain unread.'),
'goody_dates':('Cambridge: “The Consequences of Literacy,” by Jack Goody and Ian Watt (1963).','Checked the joint byline and the April1963issue,5.3,304–345. Joint authorship is retained; the2009online date is not the original publication. The article body remains unread.'),
'goody_imprint':('Cambridge: The Theft of History, original front matter (2006).','The original publisher copyright and first-publication metadata confirm2006. No original date is inferred from digital hosting in2012or2014.'),
'goody_life':('Royal Anthropological Institute, Jack Goody obituary.','Read the opening obituary: Sir John Rankine (Jack) Goody was born on27July1919and died on16July2015. Its biographical context matches the Cambridge scholar.'),
'goody_theft':('Jack Goody, The Theft of History (Cambridge,2006), Introduction1–3.','Read selected opening passages on printed1–3of the publisher’s primary excerpt. The criticism concerns Europe-centred comparative frameworks and Eurasian similarities. The remaining introduction and book are unread; broad continental claims are not adopted as facts.'),
 'todorov_bibliography':('Société des Gens de Lettres, Tzvetan Todorov bibliography (1939–2017).','Read the one-page professional author bibliography, including the1982,1991and1994entries. It supplies dates and credits only. Later translated and revised manifestations remain distinct.'),
 'todorov_conquest':('Tzvetan Todorov, “The Morality of Conquest,” Diogenes32.125(January1984),89–102, opening extract.','Read three first-person opening paragraphs displayed as “Extract,” corresponding to the opening on89. This is authored primary essay text. It supports only the explicit use of the conquest of Mexico and its texts to investigate attitudes toward other societies. The full article and The Conquest of America remain unread;2024is the online posting date.'),
 'todorov_life':('BnF authority cb11926748n, Tzvetan Todorov (1939–2017).','Read the authority fields: birth on1March1939in Sofia and death on7February2017in Paris. The record distinguishes Cvetan Todorov (1899–1962).'),
 'todorov_memory':('Tzvetan Todorov, “War: the evil that men do,” UNESCO Courier web reproduction (posted2018).','Read the complete short attributed essay, especially “An act of faith in the future.” Its12October2018posting is posthumous and creates no new authorship or contribution date. Historical examples remain part of Todorov’s ethical argument rather than independent event verification.'),
 'todorov_translation':('Smithsonian Libraries: The Conquest of America, Richard Howard translation; original English publication1984.','Checked the indexed institutional title, translator and original-publication note: New York, Harper & Row,1984. The current1999manifestation is distinct from the1982French original and first English publication in1984. The body remains unread.'),
'chatterjee_books':('Columbia Anthropology, Partha Chatterjee biography and bibliography.','Read the biography and named-book dates1986,1993and2012. Political theory, anthropology and historical research remain explicit roles. Metadata creates no influence claim.'),
'chatterjee_interview':('Partha Chatterjee and Ayça Çubukçu, “Empire as a Practice of Power: An Interview,” Asia-Pacific Journal10.41.1(8October2012), article3840.','Read the primary interview on printed2–3via the Cambridge-hosted PDF, DOI10.1017/S1557466012033256. The original2012date is retained despite the2025digital migration. Chatterjee discusses joining local narrative to conceptual history and learning from Subaltern Studies. His sweeping claim about other intellectual historians is not adopted.'),
'chatterjee_life':('Partha Chatterjee, “Populism and Fascism: What’s the Difference?” The Book Review50.5(May2026).','Read the byline, May2026issue and first-person opening memorial-lecture statement. This is positive current author and lecture evidence matched to the Columbia scholar. Later political claims are not used for graph relationships.'),
'portelli_life':('Editions Agone: rencontre avec Alessandro Portelli, Humathèque/Campus Condorcet,2February2026.','Read the publisher announcement inviting Portelli to discuss workers’ cultures and social struggles with Archambault, Henry and Vigna on2February2026. This is positive evidence of scheduled author participation; attendance is unconfirmed.'),
'portelli_valle':('University of Wisconsin Press: Alessandro Portelli, The Battle of Valle Giulia (May1997).','Checked the publisher’s complete title, author and May1997publication date. Bibliographic evidence only; the book body remains unread.'),
 'tocqueville_democracy':('BnF uniform-title authority cb11948318h, De la démocratie en Amérique.','The authority identifies the original publication in Paris in1835and1840. BnF bibliographic record cb31476112c confirms Gosselin,1835–1840. The two original parts remain distinct; no English translation date is assigned.'),
 'tocqueville_life':('Académie française, Alexis de Tocqueville, biography.','Read the biography: birth on29July1805and death on16April1859. Used for life metadata only. Unverified titles and dates in its works list are not adopted; publication dates use BnF and the primary title page.'),
 'tocqueville_preface':('Alexis de Tocqueville, L’Ancien Régime et la Révolution (1856), Avant-propos5–12; digitized second edition.','Read printed5–12of the author’s preface in the1856second-edition transcription. It describes documentary and administrative archive research and continuities between the Old Regime and Revolution. The remaining book is unread. This is a public-domain primary text.'),
'hahn_borders':('Penguin: Steven Hahn, A Nation Without Borders (2016; paperback2017).','Checked the original2016ebook date,2017paperback date and full author. The body remains unread. Its exact first-author work key is included in the clean103-dissertation union.'),
'hahn_feet':('Penn Today: Steven Hahn wins the Bancroft Prize for A Nation Under Our Feet (2003).','Read the2004institutional announcement identifying the author and2003book. This author is distinct from Steven C. Hahn of St Olaf.'),
'hahn_life':('Brooklyn Public Library/Center for Brooklyn History: Kim Phillips-Fein in conversation with Steven Hahn,16July2026.','Read the calendar announcement and participant biography identifying the NYU historian and author of A Nation Under Our Feet, A Nation Without Borders and Illiberal America. It documents scheduled participation on16July2026; attendance is unconfirmed. This is not the St Olaf historian Steven C. Hahn.'),
'hahn_primary':('Peter Nichols, “Political Underground Railroad,” Penn Arts & Sciences Frontiers (May2009), with Steven Hahn’s direct comments.','Read the complete institutional feature, especially paragraphs4–8and direct author statements. Primary interview comments are distinguished from Nichols’s substantive account. The entire Political Worlds monograph remains unread; the slave-rebellion interpretation stays attributed to Hahn.'),
'hahn_roots':('Folger Shakespeare Library: Steven Hahn, The Roots of Southern Populism (Oxford University Press,1983).','Checked the primary library author, title and publication statement: New York, Oxford University Press,1983. The later2006updated edition remains distinct. No chapter body was read.')}
E={
'michel_de_certeau':['Julliard,1970. De Certeau is credited as scientific editor and presenter, not author of every historical document.','French original,1975; later translations remain distinct.','French original,1980. The companion volume2, Habiter, cuisiner, is by Luce Giard and Pierre Mayol, as the English preface at ix explains.','The English preface is dated26February1984. This translation of Arts de faire is distinct from the1980French original.'],
'charles_tilly':['Original1964book identified in the institutional selected works; the body remains unread.','Chapter in Bringing the State Back In. Evans, Rueschemeyer and Skocpol are editors, not coauthors of this chapter.','An existing source independently identifies the1986original; the full volume remains unread.','The original1990title and date are retained. The later AD990–1992revision is not folded into the first publication.'],
 'timothy_mitchell':['The institutional full-text citation identifies the1988original, distinct from the1991paperback.','Read the1991preface. This is a later manifestation with new prefatory material, not a redated1988original.','UC Press, November2002. The full book remains unread.','The2011original is distinguished from the2013and2023paperbacks. The full book remains unread.'],
'jack_goody':['Joint article in Comparative Studies in Society and History5.3(April1963),304–345; the2009digital publication is later.','The publisher preview imprint confirms1983. Selected passages at8–9were read, not the entire book.','Cambridge original,2006. Later digital posting dates do not redate the contribution.'],
 'tzvetan_todorov':['French original, Seuil,1982. Richard Howard’s first English translation in1984and the later Oklahoma edition in1999remain distinct.','Harper & Row,1984: English publication, not a new French original.','Seuil original,1991. The complete book remains unread.','Seuil original,1994. The2004revised edition is not substituted for the original date.'],
'partha_chatterjee':['Original publication,1986. The historical project concerns colonial nationalism; the full book remains unread.','Princeton original,1993. The earlier bounded primary-chapter review is preserved; no new whole-book reading is claimed.','Princeton,2012. The selected author interview is also from2012; its2025Cambridge migration does not redate it.'],
'alessandro_portelli':['History Workshop12,96–107. The related Italian1979and English1991versions remain distinct. This packet reads an adapted1991version, not an exact1981transcription.','SUNY collection,1991. Component essays have earlier histories. An adapted selected1991excerpt was read; the whole collection remains unread.','Wisconsin, May1997. The full book remains unread.'],
'alexis_de_tocqueville':['First original part,1835; second part,1840. These are original French parts, not two English reissues.','Second original part,1840. Each part originally comprised two volumes.','Original publication,1856. The preface was read in a second edition dated1856. Later translations do not redate the original.'],
'steven_hahn':['Oxford original,1983. The updated2006edition does not redate the original.','The2004institutional prize announcement identifies the original2003book.','The May2009institutional feature presents the new book and direct author comments. The full book remains unread.','Original ebook,2016; the2017paperback remains distinct.']}
A={
'certeau_practice_primary':'Additional1.188review: reread the English preface ix–x and General Introduction xi–xv via OCR of the same later paperback scan. Connections concerning practices and consumption, and the Foucault critique, use only these passages. Giard/Mayol companion-volume and Rendall translation credits remain explicit; no body-chapter or original-language collation is claimed.',
'goody_family_marriage':'Additional1.188review: reread printed8–9, including note1, from the publisher preview. The scope remains distinctions between kinship and demographic questions, regional and social variation, and a qualified challenge to uniqueness. Cited empirical studies were not independently checked; the entire book remains unread.',
'portelli_peculiarities':'Additional1.188review: reread the complete four-page adapted1991excerpt at the existing handout URL. Sections III–IVsupport the individual connections concerning memory and interviews. The1979Italian original,1981English article and related1991version remain distinct. The handout’s modernizations remain a qualification; whole books remain unread.'}
ROSTERS={
'michel_de_certeau':'The Practice of Everyday Life, English translation (1984), xii–xiv',
 'timothy_mitchell':'Colonising Egypt (1988; paperback preface1991)',
'jack_goody':'The Theft of History (2006), Introduction1–3',
 'tzvetan_todorov':'“War: the evil that men do,” posthumous UNESCO web reproduction',
'partha_chatterjee':'The Black Hole of Empire (2012); Çubukçu interview,2–3',
'alessandro_portelli':'Adapted1991“What Makes Oral History Different?”, section III',
'alexis_de_tocqueville':'L’Ancien Régime et la Révolution (1856), Avant-propos5–12',
'steven_hahn':'A Nation Under Our Feet (2003); The Political Worlds of Slavery and Freedom (2009)'}
IDENTITY={
 'timothy_mitchell':'Timothy Mitchell, Columbia historian and political theorist, is identified by Colonising Egypt, Rule of Experts and Carbon Democracy. Mitchell Dean and Juliet Mitchell are distinct existing identities. His interdisciplinary roles remain explicit. No external QID is assigned.',
 'tzvetan_todorov':'Tzvetan Todorov is identified by his named historical works and the BnF authority distinguishing the older Cvetan Todorov. Richard Howard’s translation and Anthony Pagden’s foreword retain their separate credits. His interdisciplinary roles remain explicit. No external QID is assigned.',
'alexis_de_tocqueville':'Alexis de Tocqueville is identified by his historical works and institutional biography. His political thought remains explicit, and Gustave de Beaumont retains joint credit for the penitentiary study. No external QID is assigned.',
'steven_hahn':'Steven Hahn, the NYU/Penn historian, is identified by his US slavery and populism books and the OCLC authority for the author born in1951. Steven C. Hahn of St Olaf, author of the Creek and Mary Musgrove works, is distinct. The raw key hahn|steven c remains unchanged. No external QID is assigned.'}
# Add conventional spaces only in newly supplied prose, protecting authority tokens.
def text(v):
 protected={}
 def hide(m):
  k='ZXQ'+chr(65+len(protected))+'QXZ';protected[k]=m.group();return k
 v=re.sub(r'cb\d+[a-z]|10\.\d+/[A-Za-z0-9.]+|[PW]:[^ ;,]+(?:\|[^ ;,]+)?',hide,v)
 v=re.sub(r'(?<=[A-Za-zÀ-ž])(?=\d)', ' ',v)
 v=re.sub(r'(?<=[0-9])(?=[A-Za-zÀ-ž])', ' ',v)
 v=re.sub(r'([,;])(?=\S)',r'\1 ',v)
 v=v.replace('AD990','AD 990').replace('III–IVsupport','III–IV support').replace('1991“What','1991 “What')
 for k,original in protected.items():v=v.replace(k,original)
 return v

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 cfg=json.loads((P/'batch.json').read_text())
 for pid in cfg['persons']:
  f=P/pid/'entry-draft.json';d=json.loads(f.read_text())
  for s in d['new_sources']:
   title,note=S[s['id'].removeprefix('rh188_')];s['title']=text(title);s['citation']=text(title);s['verification']['note']=text(note)
  for event,support in zip(d['node']['chronology']['events'],E[pid]):
   event['label']=text(event['label']);event['support']=text(support)
  for sid,a in d['source_addenda'].items():a['note']=text(A[sid])
  if pid=='tzvetan_todorov':d['proposed_edges'][0]['evidence_note']='The three authored opening paragraphs of “The Morality of Conquest,” printed89, explicitly identify the conquest of Mexico and its texts as the case. This limited methodological connection does not assert the unread book’s full thesis or label Todorov a member of a later school.'
  for e in d['proposed_edges']:e['evidence_note']=text(e['evidence_note'])
  for ra in d['roster_additions']:ra['row']['works']=text(ROSTERS[pid])
  if pid in IDENTITY:d['people_update']['identity_note']=text(IDENTITY[pid])
  d['node']['scope_note']=d['node']['scope_note'].replace('webpost','web posting').replace('Steven C.Hahn','Steven C. Hahn')
  d['node']['scope_note']=d['node']['scope_note'].replace('Four positively matched book keys yield the clean 103-dissertation lower bound; all other key rows remain unassigned. Four positively identified book keys yield a deduplicated eligibility lower bound of 103 dated dissertations.', 'Four positively identified book keys yield a deduplicated eligibility lower bound of 103 dated dissertations; all other key rows remain unassigned.')
  d['node']['description']=d['node']['description'].replace('Steven C.Hahn','Steven C. Hahn')
  d['node']['representative_figures_and_works']='; '.join(e['label']+' ('+str(e['date']['year'])+')' for e in d['node']['chronology']['events'])+'.'
  d['node']['date_label']=' · '.join(str(e['date']['year'])+' '+e['label'].split(':')[0] for e in d['node']['chronology']['events'][:3])
  write(f,d)
  lf=P/pid/'life-status.json';life=json.loads(lf.read_text())
  if pid in IDENTITY:life['identity_rationale']=text(IDENTITY[pid])
  byurl={s['url']:s for s in d['new_sources']}
  for s in life['sources']:
   graph=byurl[s['url']];s['title']=graph['title'];s['check_scope']=graph['verification']['note']
  if pid=='charles_tilly':life['sources'][0]['support']='The institutional obituary states death on29April2008and birth on27May1929.'
  if pid=='partha_chatterjee':life['sources'][0]['support']='Positive author testimony to delivering the current memorial lecture; the historical scholar is distinct from the politician and SNU economist namesakes.'
  if pid=='alessandro_portelli':
   life['limits']='The official publisher announcement documents scheduled participation in a past event. Attendance is unconfirmed. The positive witness is dated2026; status is not inferred from missing death data. Life metadata creates no work, career or influence interval.'
   life['sources'][0]['locator']='Dated event announcement,2February2026, and named participant paragraph'
   life['sources'][0]['support']='Positive evidence of scheduled author participation, matched to the Columbia/Sapienza oral historian; attendance is unconfirmed.'
  if pid=='alexis_de_tocqueville':
   life['limits']='Exact dates follow the Académie biography. Unverified items in its works list and a conflicting date in an older parliamentary biographical dictionary are not adopted. Life metadata creates no work, career or influence interval.'
   life['sources'][0]['locator']='Institutional biography birth and death statements';life['sources'][0]['support']='Explicit birth on29July1805and death on16April1859.'
  if pid=='steven_hahn':
   life['confidence']='medium'
   life['limits']='The July2026calendar announcement documents scheduled participation; attendance is unconfirmed. The participant biography matches the NYU/Penn historian, distinct from Steven C. Hahn. Living status remains a qualified assessment from positive current evidence, not missing death data. Life metadata creates no work, career or influence interval.'
   life['sources'][0]['locator']='Calendar announcement for16July2026and participant biography'
   life['sources'][0]['support']='Scheduled participation in the16July2026event, with attendance unconfirmed. NYU affiliation and named works match this identity.'
  for key in ['limits','identity_rationale']:life[key]=text(life[key])
  for s in life['sources']:
   for key in ['support','locator']:s[key]=text(s[key])
  write(lf,life)
  nf=P/pid/'research-notes.json';n=json.loads(nf.read_text());n['unread_limits']=d['node']['scope_note'];n['primary_reading_extent']=[{'source_id':s['id'],'url':s['url'],'extent_and_limits':s['verification']['note']} for s in d['new_sources']];n['existing_source_addenda']=d['source_addenda'];n['dates']=[{'year':e['date']['year'],'title':e['label'],'basis':e['support'],'sources':e['source_ids']} for e in d['node']['chronology']['events']];n['relationship_scope']=[{'target':e['target'],'claim':e['relationship'],'evidence':e['evidence_note']} for e in d['proposed_edges']];n['copy_review']='RT3: explicit review of every new public node, event, support, relationship, source and addendum string; RT4: Hahn calendar evidence states scheduled participation, attendance unconfirmed, with medium confidence and unchanged living status.';write(nf,n)
 cfg['rationale']='Functional historical research is the classification criterion. Original, revised, translated and collected works retain their dates and credits. Eight provisional frozen screening keys remain qualified; Hahn’s clean103-dissertation lower bound is separate from the mixed raw121. Existing IDs, edges, source qualifications, roster prose, coverage and chronologies are preserved.'
 cfg['rationale']=text(cfg['rationale']);write(P/'batch.json',cfg)
if __name__=='__main__':main()
