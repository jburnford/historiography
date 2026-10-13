import csv, json, sys, os

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(D, 'candidates.jsonl'))]

C, I, T, P = 'canadian_historian', 'historian_international', 'theorist_other_discipline', 'primary_source_author'

TYPE = {
'foucault|michel': (T, 'French philosopher-historian of power, discipline and sexuality'),
'anderson|benedict': (T, 'Political scientist of Southeast Asia; theorist of nationalism (Imagined Communities)'),
'mckay|ian': (C, 'Canadian historian of the left, antimodernism and the liberal order framework (Queen\'s)'),
'hobsbawm|eric j': (I, 'British Marxist historian of labour, nationalism and the long 19th century'),
'granatstein|jack l': (C, 'Canadian political and military historian (York)'),
'scott|james c': (T, 'American political scientist/anthropologist of the state and peasant resistance'),
'owram|douglas r': (C, 'Canadian intellectual and social historian of the West and the baby boom (Alberta)'),
'said|edward w': (T, 'Palestinian-American literary critic; founder of postcolonial studies (Orientalism)'),
'iacovetta|franca': (C, 'Canadian historian of immigration, gender and the Cold War (Toronto)'),
'stoler|ann l': (T, 'American anthropologist-historian of colonial intimacy and the archive'),
'valverde|mariana': (C, 'Canadian sociologist-criminologist; historian of moral reform (Toronto)'),
'parr|joy': (C, 'Canadian historian of gender, work, consumption and environment'),
'white|richard': (I, 'American historian of Native-European relations and the American West (Stanford)'),
'sangster|joan': (C, 'Canadian historian of women, labour and the left (Trent)'),
'berger|carl': (C, 'Canadian intellectual historian of imperialism and historiography (Toronto)'),
'palmer|bryan d': (C, 'Canadian Marxist labour historian (Trent)'),
'carter|sarah a': (C, 'Canadian historian of Indigenous peoples, women and the Prairie West (Alberta)'),
'morton|desmond': (C, 'Canadian military and political historian (McGill)'),
'perry|adele': (C, 'Canadian historian of gender, race and colonialism in British Columbia (Manitoba)'),
'christie|nancy j': (C, 'Canadian historian of religion, family and the welfare state'),
'scott|joan w': (I, 'American historian of France; theorist of gender as a category of analysis'),
'greer|allan': (C, 'Canadian historian of New France, Lower Canada and colonial property (McGill)'),
'cook|ramsay': (C, 'Canadian intellectual and political historian of nationalism (York)'),
'miller|james r': (C, 'Canadian historian of Indigenous-settler relations, treaties and residential schools (Saskatchewan)'),
'bourdieu|pierre': (T, 'French sociologist of capital, habitus and distinction'),
'loo|tina': (C, 'Canadian environmental and legal historian (UBC)'),
'hall|catherine': (I, 'British feminist historian of class, gender and empire (UCL)'),
'gauvreau|michael': (C, 'Canadian historian of religion, Quebec Catholicism and the Quiet Revolution (McMaster)'),
'thompson|edward p': (I, 'British Marxist historian of the English working class'),
'cooper|frederick': (I, 'American historian of Africa, colonialism and empire (NYU)'),
'kealey|gregory s': (C, 'Canadian labour historian and historian of state security (UNB)'),
'whitaker|reginald': (C, 'Canadian political scientist-historian of national security and immigration (York)'),
'miller|james': (C, 'Split record of J.R. Miller, Canadian historian of Indigenous-settler relations (Saskatchewan)'),
'heron|craig': (C, 'Canadian labour historian of Hamilton workers and alcohol (York)'),
'bothwell|robert': (C, 'Canadian political and diplomatic historian (Toronto)'),
'strong boag|veronica': (C, 'Canadian historian of women, childhood and adoption (UBC)'),
'ranger|terence': (I, 'British historian of Zimbabwe and colonial Africa (Oxford)'),
'vance|jonathan f': (C, 'Canadian historian of war memory and culture (Western)'),
'harris|cole r': (C, 'Canadian historical geographer of colonialism and settlement, esp. British Columbia (UBC)'),
'stacey|charles p': (C, 'Canadian official military historian and historian of external policy'),
'curtis|bruce': (C, 'Canadian historical sociologist of state formation, schooling and the census (Carleton)'),
'davis|natalie z': (I, 'Canadian-American historian of early modern France; microhistory'),
'radforth|ian': (C, 'Canadian historian of labour, the 1860 royal tour and state formation (Toronto)'),
'cronon|william': (I, 'American environmental historian (Wisconsin)'),
'barman|jean': (C, 'Canadian historian of British Columbia, education and Indigenous women (UBC)'),
'friesen|gerald': (C, 'Canadian historian of the Prairies and communication (Manitoba)'),
'innis|harold a': (C, 'Canadian political economist and economic historian; staples and communication theory'),
'backhouse|constance b': (C, 'Canadian legal historian of race, gender and law (Ottawa)'),
'english|john': (C, 'Canadian political historian and biographer of Pearson and Trudeau (Waterloo)'),
'burke|peter j': (I, 'British cultural historian of early modern Europe (Cambridge)'),
'dubinsky|karen': (C, 'Canadian historian of sexuality, tourism and transnational adoption (Queen\'s)'),
'thompson|john': (C, 'Canadian historian of the Prairie West and Canada-US relations (Duke)'),
'mills|sean': (C, 'Canadian historian of postcolonial thought, Montreal and Haiti-Quebec ties (Toronto)'),
'morgan|cecilia': (C, 'Canadian historian of gender, commemoration and Indigenous travel (Toronto/OISE)'),
'fahrni|magda': (C, 'Canadian historian of family, consumption and postwar Montreal (UQAM)'),
'keshen|jeffrey a': (C, 'Canadian historian of the world wars home front and propaganda'),
'burton|antoinette m': (I, 'American historian of British imperialism, feminism and the archive (Illinois)'),
'francis|daniel': (C, 'Canadian popular historian of myth and image (The Imaginary Indian)'),
'bradbury|bettina': (C, 'Canadian historian of working families and widowhood in Montreal (York)'),
'kelm|maryellen': (C, 'Canadian historian of Indigenous health and the West (Simon Fraser)'),
'linteau|paulandre': (C, 'Quebec historian of contemporary Quebec and Montreal (UQAM)'),
'korinek|valerie j': (C, 'Canadian historian of gender, magazines and queer history (Saskatchewan)'),
'butler|judith p': (T, 'American philosopher and gender theorist (performativity)'),
'comacchio|cynthia r': (C, 'Canadian historian of family, youth and childhood (Wilfrid Laurier)'),
'pratt|mary': (T, 'American literary scholar of travel writing and the contact zone'),
'habermas|jurgen': (T, 'German philosopher-sociologist of the public sphere'),
'bercuson|david j': (C, 'Canadian labour and military historian (Calgary)'),
'ducharme|michel': (C, 'Canadian intellectual historian of liberty and liberalism (UBC)'),
'colley|linda': (I, 'British historian of Britishness and empire (Princeton)'),
'nora|pierre': (I, 'French historian of memory (lieux de memoire)'),
'ray|arthur j': (C, 'Canadian historical geographer-historian of the fur trade and treaties (UBC)'),
'finkel|alvin': (C, 'Canadian historian of social policy, the welfare state and Alberta (Athabasca)'),
'rutherdale|robert': (C, 'Canadian historian of the Great War home front and fatherhood (Algoma)'),
'buckner|phillip a': (C, 'Canadian historian of the British world and Atlantic Canada'),
'harvey|david d': (T, 'British Marxist geographer of capitalism and space'),
'mclaren|angus': (C, 'Canadian historian of sexuality, eugenics and reproduction (Victoria)'),
'bliss|michael a': (C, 'Canadian historian of business, medicine and politics (Toronto)'),
'baillargeon|denyse': (C, 'Quebec historian of women, motherhood and medicine (Montreal)'),
'weber|max': (T, 'German sociologist of religion, bureaucracy and capitalism'),
'gleason|mona': (C, 'Canadian historian of childhood, psychology and health (UBC)'),
'campbell|lara': (C, 'Canadian historian of gender, the Depression and the sixties (Simon Fraser)'),
'igartua|jose e': (C, 'Canadian historian of English-Canadian identity and New France merchants (UQAM)'),
'hall|stuart': (T, 'Jamaican-British cultural theorist and sociologist (cultural studies)'),
'porter|roy': (I, 'British social historian of medicine and the Enlightenment'),
'careless|maurice': (C, 'Canadian historian of metropolitanism and limited identities (Toronto)'),
'raibmon|paige': (C, 'Canadian historian of Indigenous peoples of the Northwest Coast (UBC)'),
'morton|william l': (C, 'Canadian historian of Manitoba, the West and Confederation'),
'creighton|donald g': (C, 'Canadian historian of the Laurentian thesis and Macdonald (Toronto)'),
'young|brian j': (C, 'Canadian historian of Quebec law, institutions and elites (McGill)'),
'avery|donald h': (C, 'Canadian historian of immigrant workers and science in war (Western)'),
'clement|dominique': (C, 'Canadian historian-sociologist of human rights and social movements (Alberta)'),
'hamelin|jean': (C, 'Quebec historian of economy, Catholicism and the press (Laval)'),
'taylor|alan': (I, 'American historian of colonial and revolutionary North America and the War of 1812'),
'braudel|fernand': (I, 'French Annales historian of the Mediterranean and the longue duree'),
'brown|robert': (C, 'Canadian political historian and biographer of Borden (Toronto)'),
'van kirk|sylvia m': (C, 'Canadian historian of women and fur-trade society (Toronto)'),
'coates|kenneth s': (C, 'Canadian historian of the North and Indigenous peoples (Saskatchewan)'),
'marx|karl': (P, '19th-century German philosopher and political economist cited as a primary/theoretical source'),
'strange|carolyn': (C, 'Canadian historian of gender, crime and punishment (ANU)'),
'dickinson|john a': (C, 'Canadian historian of New France justice and Quebec society (Montreal)'),
'hillmer|norman': (C, 'Canadian historian of foreign policy and nationalism (Carleton)'),
'cruikshank|julie': (T, 'Canadian anthropologist of Yukon oral tradition and Indigenous knowledge (UBC)'),
'geertz|clifford': (T, 'American interpretive anthropologist (thick description)'),
'latour|bruno': (T, 'French sociologist-philosopher of science (actor-network theory)'),
'high|steven c': (C, 'Canadian oral historian of deindustrialization (Concordia)'),
'ward|peter': (C, 'Canadian social historian of race, courtship and domestic space (UBC)'),
'trigger|bruce g': (C, 'Canadian anthropologist-archaeologist and ethnohistorian of the Huron-Wendat (McGill)'),
'smith|donald b': (C, 'Canadian historian of the Mississauga and Indigenous biography (Calgary)'),
'dickason|olive p': (C, 'Canadian Metis historian of First Nations and French colonialism (Alberta/Ottawa)'),
'winter|jay': (I, 'American historian of First World War memory and mourning (Yale)'),
'prentice|alison l': (C, 'Canadian historian of education and women (OISE)'),
'harris|richard l': (C, 'Canadian urban historical geographer of suburbs and housing (McMaster)'),
'rudin|ronald': (C, 'Canadian historian of Quebec historiography, Acadia and public memory (Concordia)'),
'bouchard|gerard': (C, 'Quebec historian-sociologist of the Saguenay, nations and interculturalism (UQAC)'),
'milloy|john s': (C, 'Canadian historian of Indian policy and residential schools (Trent)'),
'cook|tim': (C, 'Canadian military historian of the world wars (Canadian War Museum)'),
'waiser|bill': (C, 'Canadian historian of Saskatchewan and First Nations (Saskatchewan)'),
'lutz|john s': (C, 'Canadian historian of Indigenous-settler relations in British Columbia (Victoria)'),
'stanley|george f': (C, 'Canadian historian of the Riel resistances and military history'),
'tosh|john': (I, 'British historian of masculinity and historical method'),
'roediger|david r': (I, 'American historian of whiteness and labour'),
'rutherdale|myra': (C, 'Canadian historian of missions, gender and northern nursing (York)'),
'chartier|roger': (I, 'French historian of the book, reading and representation'),
'bayly|christopher a': (I, 'British historian of India, empire and global history (Cambridge)'),
'kinsman|gary': (C, 'Canadian sociologist-historian of sexual regulation and national security (Laurentian)'),
'knowles|valerie': (C, 'Canadian popular historian of immigration policy and biographer (Ottawa)'),
'mcclintock|anne': (T, 'Zimbabwean-born literary and cultural theorist of gender and empire'),
'brown|jennifer s': (C, 'Canadian ethnohistorian of fur-trade families and the Metis (Winnipeg)'),
'mosse|george l': (I, 'German-American historian of nationalism, masculinity and war memory'),
'podruchny|carolyn': (C, 'Canadian historian of voyageurs and the fur trade (York)'),
'conrad|margaret r': (C, 'Canadian historian of Atlantic Canada and women (UNB)'),
'ginzburg|carlo': (I, 'Italian historian; pioneer of microhistory'),
'brewer|john': (I, 'British historian of the 18th-century state, consumption and culture'),
'arendt|hannah': (T, 'German-American political theorist (totalitarianism)'),
'berton|pierre': (C, 'Canadian popular historian and journalist'),
'wolfe|patrick': (I, 'Australian historian-anthropologist; theorist of settler colonialism'),
'levine|philippa': (I, 'British historian of gender, sexuality and the British Empire'),
'copp|terry': (C, 'Canadian military and social historian (Wilfrid Laurier)'),
'lears|jackson t': (I, 'American cultural historian of antimodernism and advertising'),
'brownlie|robin': (C, 'Canadian historian of Indian administration and First Nations in Ontario (Manitoba)'),
'mann|susan a': (C, 'Canadian historian of Quebec nationalism and women (Susan Mann Trofimenkoff)'),
'walker|james': (C, 'Canadian historian of race, Black Loyalists and human rights (Waterloo)'),
'white|hayden v': (I, 'American intellectual historian and theorist of historical narrative'),
'bhabha|homi k': (T, 'Indian-British postcolonial theorist (hybridity, mimicry)'),
'weaver|john c': (C, 'Canadian historian of urban reform, land, crime and suicide (McMaster)'),
'brubaker|rogers': (T, 'American sociologist of nationalism, ethnicity and citizenship'),
'sandwell|ruth w': (C, 'Canadian historian of rural history, energy and history education (OISE)'),
'heaman|elsbeth': (C, 'Canadian historian of exhibitions, taxation and the state (McGill)'),
'lamonde|yvan': (C, 'Quebec intellectual historian of ideas and print culture (McGill)'),
'adams|mary': (C, 'Canadian sociologist-historian of youth and heterosexuality (Queen\'s)'),
'taylor|charles': (T, 'Canadian philosopher of identity, recognition and secularism (McGill)'),
'chakrabarty|dipesh': (I, 'Indian historian of South Asia; postcolonial and Anthropocene theorist (Chicago)'),
'swyripa|frances': (C, 'Canadian historian of Ukrainian Canadians and ethno-religious identity (Alberta)'),
'roy|patricia e': (C, 'Canadian historian of British Columbia and Asian Canadians (Victoria)'),
'pierson|ruth': (C, 'Canadian historian of women and the Second World War (OISE)'),
'mitchinson|wendy': (C, 'Canadian historian of women and medicine (Waterloo)'),
'fanon|frantz': (T, 'Martinican psychiatrist and anticolonial theorist'),
'marks|lynne': (C, 'Canadian historian of religion, leisure and gender (Victoria)'),
'martel|marcel': (C, 'Canadian historian of French Canada, language politics and drugs (York)'),
'perin|roberto': (C, 'Canadian historian of Catholicism, Italian immigrants and ethnicity (York)'),
'deloria|philip j': (I, 'American (Dakota) historian of Native America and Indian representation (Harvard)'),
'struthers|james': (C, 'Canadian historian of unemployment and the welfare state (Trent)'),
'francis|douglas r': (C, 'Canadian intellectual historian of the Prairie West (Calgary)'),
'drummond|ian m': (C, 'Canadian economic historian of Ontario and imperial economic policy (Toronto)'),
'de certeau|michel': (T, 'French Jesuit theorist of everyday life and historiography'),
'bourke|joanna': (I, 'British historian of the body, emotions and war (Birkbeck)'),
'appadurai|arjun': (T, 'Indian-American anthropologist of globalization and commodities'),
'davidoff|leonore': (I, 'British-American historian-sociologist of gender, family and class'),
'morton|suzanne': (C, 'Canadian social historian of Halifax, gambling and welfare (McGill)'),
'lower|arthur': (C, 'Canadian historian of the timber trade and national history (Queen\'s)'),
'palmer|howard': (C, 'Canadian historian of ethnicity, nativism and Alberta (Calgary)'),
'warren|jeanphilippe': (C, 'Quebec sociologist-historian of ideas, the left and the sixties (Concordia)'),
'peers|douglas m': (C, 'Laura Peers: anthropologist-historian of the Ojibwa and museum collections (Oxford); record also holds Douglas M. Peers'),
'durocher|rene': (C, 'Quebec historian of contemporary Quebec and Duplessis (Montreal)'),
'eley|geoff': (I, 'British historian of Germany, the European left and social history (Michigan)'),
'portelli|alessandro': (I, 'Italian oral historian and Americanist'),
'constant|jeanfrancois': (C, 'Canadian historian of liberalism (co-editor, Liberalism and Hegemony)'),
'trouillot|michelrolph': (T, 'Haitian anthropologist of power and the production of history'),
'carlson|keith t': (C, 'Canadian ethnohistorian of the Sto:lo and Coast Salish (Saskatchewan/Fraser Valley)'),
'benjamin|walter': (T, 'German critical theorist of history, art and modernity'),
'halbwachs|maurice': (T, 'French sociologist of collective memory'),
'epp|marlene': (C, 'Canadian historian of Mennonite women, refugees and food (Waterloo)'),
'bumsted|john m': (C, 'Canadian historian of PEI, Red River and the Scots (Manitoba)'),
'macdougall|brenda': (C, 'Metis historian of Metis family and kinship in Saskatchewan (Ottawa)'),
'hewitt|steve r': (C, 'Canadian historian of the RCMP and security surveillance (Birmingham)'),
'hunt|lynn': (I, 'American historian of the French Revolution and cultural history (UCLA)'),
'armitage|david': (I, 'British historian of empire, Atlantic history and political thought (Harvard)'),
'reid|john g': (C, 'Canadian historian of Atlantic Canada, Acadia and Mi\'kma\'ki (Saint Mary\'s)'),
'walden|keith': (C, 'Canadian cultural historian of Toronto and modernity (Trent)'),
'judt|tony': (I, 'British-American historian of postwar Europe'),
'cannadine|david': (I, 'British historian of aristocracy, class and empire'),
'cohen|lizabeth': (I, 'American historian of consumption and labour (Harvard)'),
'kelley|ninette': (T, 'Canadian lawyer and refugee-policy official; co-author of a history of immigration policy'),
'crosby|alfred w': (I, 'American environmental historian (ecological imperialism)'),
'lackenbauer|whitney p': (C, 'Canadian historian of the military, Arctic sovereignty and Indigenous lands (Trent)'),
'stone|lawrence': (I, 'British-American social historian of early modern England'),
'havard|gilles': (I, 'French historian of New France and French-Indigenous relations (EHESS)'),
'anderson|kay j': (T, 'Australian-based cultural geographer of race (Vancouver\'s Chinatown)'),
'rose|sonya o': (I, 'American sociologist-historian of gender and citizenship in Britain'),
'troper|harold': (C, 'Canadian historian of immigration and Canadian Jews (OISE)'),
'mackenzie|david': (C, 'Canadian historian of external relations, Newfoundland and aviation (Ryerson/TMU)'),
'pickles|katie': (I, 'New Zealand historian of empire, gender and the IODE (Canterbury)'),
'bederman|gail': (I, 'American historian of gender and race (Notre Dame)'),
'levesque|andree': (C, 'Quebec historian of women and the left (McGill)'),
'mcneill|john': (I, 'American environmental and world historian (Georgetown)'),
'lefebvre|henri': (T, 'French Marxist philosopher of space and everyday life'),
'dummitt|christopher': (C, 'Canadian historian of masculinity and postwar Canada (Trent)'),
'patrias|carmela': (C, 'Canadian historian of immigrant workers and human rights (Brock)'),
'lux|maureen k': (C, 'Canadian historian of Indigenous health and Indian hospitals (Brock)'),
'hubert|ollivier': (C, 'Quebec historian of Catholic ritual, colleges and gender (Montreal)'),
'frager|ruth a': (C, 'Canadian historian of Jewish labour, women workers and human rights (McMaster)'),
'errington|elizabeth': (C, 'Canadian historian of Upper Canada, loyalism and women (RMC/Queen\'s)'),
'mitchell|timothy': (T, 'British-American political theorist of Egypt, expertise and oil (Columbia)'),
'benton|lauren a': (I, 'American historian of law and empire (Yale)'),
'roper|michael': (I, 'British historian of masculinity, emotion and the First World War (Essex)'),
'maceachern|alan': (C, 'Canadian environmental historian of parks and Atlantic Canada (Western)'),
'ens|gerhard j': (C, 'Canadian historian of the Red River Metis (Alberta)'),
'corbin|alain': (I, 'French historian of the senses and sensibilities'),
'daschuk|james w': (C, 'Canadian health-studies scholar and historian of disease and famine on the Plains (Regina)'),
'binnema|theodore': (C, 'Canadian environmental and Indigenous historian of the Northwestern Plains (UNBC)'),
'mccallum|mary': (C, 'Indigenous (Munsee) Canadian historian of Indigenous labour and health (Winnipeg)'),
'pitsula|james m': (C, 'Canadian historian of Saskatchewan, the KKK and social welfare (Regina)'),
'jacobson|matthew': (I, 'American historian of whiteness, immigration and empire (Yale)'),
'gramsci|antonio': (T, 'Italian Marxist theorist of hegemony'),
'baskerville|peter a': (C, 'Canadian social and economic historian of Ontario and BC (Victoria/Alberta)'),
'worster|donald': (I, 'American environmental historian of the West (Kansas)'),
'gillis|john r': (I, 'American historian of family, youth, memory and coasts (Rutgers)'),
'gaddis|john l': (I, 'American historian of the Cold War (Yale)'),
'smith|linda': (T, 'Maori scholar of education and Indigenous research methodologies'),
'behiels|michael d': (C, 'Canadian historian of Quebec neo-nationalism and francophone minorities (Ottawa)'),
'axelrod|paul': (C, 'Canadian historian of education and universities (York)'),
'milligan|gerry': (C, 'Ian Milligan: Canadian historian of the sixties and digital history (Waterloo)'),
'tulchinsky|gerald j': (C, 'Canadian historian of Canadian Jews and Montreal business (Queen\'s)'),
'williams|raymond': (T, 'Welsh cultural theorist and literary critic'),
'iriye|akira': (I, 'Japanese-American historian of international and transnational history (Harvard)'),
'mazower|mark': (I, 'British historian of 20th-century Europe and internationalism (Columbia)'),
'fingard|judith': (C, 'Canadian historian of Halifax, poverty and seafarers (Dalhousie)'),
'gordon|linda': (I, 'American historian of women, welfare and family violence (NYU)'),
'westad|odd': (I, 'Norwegian historian of the global Cold War (Yale)'),
'gentile|patrizia': (C, 'Canadian historian of beauty contests, queer history and national security (Carleton)'),
'barthes|roland': (T, 'French semiotician and literary theorist'),
'fitzpatrick|sheila': (I, 'Australian historian of Soviet Russia'),
'russell|peter a': (C, 'Canadian historian of Upper Canadian society and agriculture'),
'connell|raewyn w': (T, 'Australian sociologist of masculinities (hegemonic masculinity)'),
'titley|brian': (C, 'Canadian historian of Indian administration and education (Lethbridge)'),
'ballantyne|tony': (I, 'New Zealand historian of the British Empire and colonial knowledge (Otago)'),
'darnton|robert': (I, 'American historian of the book and 18th-century France (Harvard)'),
'thompson|paul': (I, 'British sociologist and oral historian (Voice of the Past; Essex)'),
'donaghy|greg': (C, 'Canadian historian of foreign policy (Global Affairs Canada / St. Jerome\'s)'),
'mccalla|douglas': (C, 'Canadian economic historian of Upper Canada (Guelph)'),
'pagden|anthony': (I, 'British historian of empire and political thought (UCLA)'),
'mosby|ian': (C, 'Canadian historian of food, nutrition experiments and Indigenous health (McMaster)'),
'mckillop|alexander': (C, 'Canadian intellectual historian of Victorian thought and universities (Carleton)'),
'richter|daniel k': (I, 'American historian of the Iroquois and early America (Penn)'),
'rutherford|paul': (C, 'Canadian historian of media, journalism and advertising (Toronto)'),
'aries|philippe': (I, 'French historian of childhood, family and death'),
'myers|tamara': (C, 'Canadian historian of youth, delinquency and policing (UBC)'),
'tough|frank j': (C, 'Canadian historical geographer of Native economic history and Metis scrip (Alberta)'),
'ouellet|fernand': (C, 'Canadian historian of the economy and society of Lower Canada'),
'coates|colin m': (C, 'Canadian historian of New France landscape, commemoration and environment (York/Glendon)'),
'coates|colin': (C, 'Split record of Colin M. Coates, Canadian historian (York/Glendon)'),
'reid|john': (C, 'Split record of John G. Reid, Canadian historian of Atlantic Canada'),
}

WD = 'https://www.wikidata.org/wiki/'

# key -> dict of overrides
O = {}
def o(k, **kw): O.setdefault(k, {}).update(kw)

o('white|richard', decision='mixed', foreign='W:white|soldier as tourist|a',
  fnotes='W:white|soldier as tourist|a = Richard White, Australian historian (Sydney), The Soldier as Tourist (1987)')
o('whitaker|reginald', decision='mixed', foreign='W:whitaker|mutual hostages',
  fnotes='W:whitaker|mutual hostages is a misattribution: Mutual Hostages (1990) is by Roy, Granatstein, Iino and Takamura, not a second Whitaker')
o('miller|james', decision='merge_into:P:miller|james r',
  foreign='W:miller|democracy is in the streets;W:miller|democracy is in the streets|a;W:miller|passion of michel foucault;W:miller|ronald reagan and the techniques of deception|a;W:miller|united states and the making of modern greece;W:miller|rural schools in canada;W:miller|south by southwest;W:miller|swords for hire',
  fnotes='Democracy is in the Streets (x2) and The Passion of Michel Foucault = James E. Miller, American political theorist (Q6139769); Ronald Reagan and the Techniques of Deception (Atlantic 1984) = James Nathan Miller, journalist; US and the Making of Modern Greece = James Edward Miller, US diplomatic historian; Rural Schools in Canada (1913) = James Collins Miller; South by Southwest = James David Miller; Swords for Hire = James Miller, Scottish popular writer',
  uncertain='W:miller|half a billion dollars down the drain|a',
  qs='wrong', cq='Q112550518',
  notes='Remaining works (Skyscrapers Hide the Heavens; Shingwauk\'s Vision; Anti-Catholic Thought in Victorian Canada) are J.R. Miller. Q6139769 is the American James Miller and fits only the foreign works.',
  ev=WD+'Q6139769;'+WD+'Q112550518')
o('harvey|david d', decision='mixed', foreign='W:harvey|noble savage and the savage noble|a',
  fnotes='= David Allen Harvey, historian of the French Enlightenment (New College of Florida), Journal of the Western Society for French History 2010')
o('young|brian j', decision='mixed', foreign='W:collini|history religion and culture',
  fnotes='History, Religion and Culture: British Intellectual History 1750-1950 (2000) eds Collini, Whatmore and Brian Young = the Oxford intellectual historian Brian Young, not Brian J. Young (McGill)')
o('taylor|alan', decision='mixed',
  foreign='W:taylor|habsburg monarch 1809 1918;W:taylor|english history 1914 1940;W:taylor|troublemakers;W:taylor|origins ofthe second world war;W:taylor|struggle for mastery in europe;W:taylor|beaverbrook;W:taylor|course of german history',
  fnotes='All seven are by A.J.P. Taylor (1906-1990), British diplomatic historian')
o('brown|robert', decision='mixed', foreign='W:brown|peoples of the world',
  fnotes='The Peoples of the World (1892) = Robert Brown (1842-1895), Scottish botanist and geographer')
o('morton|william l', decision='mixed', foreign='W:mccally|physicians and nuclear war|a',
  fnotes='Physicians and Nuclear War (1982), lead author McCally; W.L. Morton died in 1980, so a different Morton')
o('harris|richard l', decision='mixed',
  foreign='W:harris|seigneurial system in early canada;W:harris|pays reveche;W:harris|atlas historioue du canada;W:harris|cuban internationalism che guevara and the survival of cubas socialist regime|a',
  fnotes='Seigneurial System in Early Canada, Le pays reveche and Atlas historique du Canada = R. Cole Harris (move to P:harris|cole r); Cuban Internationalism, Che Guevara... (2009) = Richard L. Harris, political scientist of Latin America',
  notes='Person key carries initial L (from the Cuba author?); the person intended is Richard Harris, McMaster urban geographer (Q58216127).')
o('ward|peter', decision='mixed', foreign='W:ward|britishness since 1870',
  fnotes='Britishness Since 1870 (2004) = Paul Ward, British historian (Huddersfield)')
o('taylor|charles', decision='mixed', foreign='W:taylor|radical tories',
  fnotes='Radical Tories: The Conservative Tradition in Canada (1982) = Charles Taylor (1935-1997), Canadian journalist and author, not the philosopher')
o('chakrabarty|dipesh', decision='mixed', foreign='W:chakrabarty|subject to colonialism',
  fnotes='Subject to Colonialism: African Self-Fashioning and the Colonial Library (2001) = Gaurav Desai; misattribution')
o('deloria|philip j', decision='mixed',
  foreign='W:deloria|if you think about it you will see that it is true;W:deloria|introduction to black elk speaks 1979;W:deloria|low bridge;W:deloria|relativity relatedness and reality;W:deloria|singing for a spirit',
  fnotes='All five = Vine Deloria Jr. (Spirit and Reason reader 1999; For This Land 1999; Singing for a Spirit 1999)',
  uncertain='W:deloria|foreword;W:deloria|vine v',
  notes='Foreword to Coming Down From Above (2008) may be Vine Deloria Jr.; the New Warriors chapter on Vine V. Deloria Sr. is probably by Philip J. Deloria.')
o('mann|susan a', decision='mixed',
  foreign='W:mann|talented women of the zhang family;W:mann|precious records;W:mann|local merchants and the chinese bureaucracy 1750 1950;W:mann|obstacles to the development of a capitalist agriculture|a',
  fnotes='Zhang Family, Precious Records, Local Merchants = Susan L. Mann, historian of China (UC Davis); Obstacles to the Development of a Capitalist Agriculture (1978) = Susan Archer Mann (sociologist) with James Dickinson',
  notes='Record is Susan Mann (Trofimenkoff); W:trofimenkoff works belong here. Key initial "a" probably comes from Susan Archer Mann.')
o('walker|james', decision='mixed', foreign='W:scott|sales and advertising expenditure for interwar american department stores|a',
  fnotes='= Peter Scott and James T. Walker, British business historians (2011)',
  qs='missing', cq='Q59654592', ev=WD+'Q59654592', notes='Q59654592 "James W. St.G. Walker, Canadian historian (b. 1940)" found by exact label; occupation historian.')
o('peers|douglas m', decision='mixed',
  foreign='W:peers|privates off parade|a;W:peers|india under colonial rule;W:peers|between mars and mammon;W:peers|india and the british empire',
  fnotes='All four = Douglas M. Peers, historian of British India (Waterloo)',
  notes='Key says douglas m but name, QID and most works are Laura Peers. Re-key the record to Laura Peers.')
o('benjamin|walter', decision='mixed', foreign='W:benjamin|great epidemic in new berne and vicinity september and october 1864 by one who p',
  fnotes='1864 pamphlet on the New Bern yellow-fever epidemic by a 19th-century author surnamed Benjamin; not Walter Benjamin (b. 1892)')
o('macdougall|brenda', decision='mixed', foreign='W:macdougall|peoples network;W:macdougall|all red dream|a',
  fnotes='The People\'s Network (2013) and The All-Red Dream (2007) = Robert MacDougall, historian of telephony (Western)',
  uncertain='W:macdougall|power and co management agreements|a',
  qs='wrong', cq='none_found',
  notes='Q112524794 is Robert MacDougall (b. 1971), who wrote only the two foreign works. No Wikidata item for Brenda Macdougall found by exact label or vector search.')
o('kelley|ninette', decision='mixed', foreign='W:kelley|cosmopolitan expression of josephus prophetic perspective in the jewish war|a',
  fnotes='= Nicole Kelley, scholar of early Judaism (Harvard Theological Review 2004)')
o('mcneill|john', decision='mixed',
  foreign='W:mcneill|presbyterian church in canada;W:mcneill|medieval handbooks of penance;W:mcneill|progress and present position of russia in the east',
  fnotes='Presbyterian Church in Canada 1875-1925 and Medieval Handbooks of Penance = John T. McNeill, church historian; Progress and Present Position of Russia in the East (1854) = Sir John McNeill, diplomat')
o('stanley|george f', decision='mixed', foreign='W:stanley|country fan resents the way juno awards sniffed at top talent|a',
  fnotes='1979 newspaper letter about the Juno Awards by an unidentified Stanley; not the historian')
o('gaddis|john l', decision='mixed', foreign='W:foot|for posterity|a',
  fnotes='For Posterity (1948), lead author Foot; predates Gaddis (b. 1941)')
o('worster|donald', decision='mixed',
  foreign='W:worster|people places patterns processes;W:worster|region of scattered settlements and bounded possibilities|a;W:worster|remapping tutira|a;W:worster|timber colony',
  fnotes='All four = Graeme Wynn, UBC historical geographer (Timber Colony 1981; People, Places, Patterns, Processes 1990; Remapping Tutira 1997; Canadian Geographer 1987). Probably a ditto-dash parsing error')
o('baskerville|peter a', decision='mixed', foreign='W:baskerville|naitre vivre grandir',
  fnotes='Naitre, vivre, grandir: Sainte-Justine 1907-2007 = Denyse Baillargeon; misattribution')
o('roper|michael', decision='mixed',
  foreign='W:roper|holy household;W:roper|oedipus and the devil;W:roper|oedipus the devil;W:roper|discipline and respectability|a;W:obelkevich|disciplines of faith;W:harris|art of survival',
  fnotes='All = Lyndal Roper, historian of Reformation Germany (Oxford): The Holy Household 1989, Oedipus and the Devil 1994 (x2), Discipline and Respectability 1985, Disciplines of Faith (co-ed. 1987), The Art of Survival (co-ed. with Ruth Harris 2006)',
  uncertain='W:roper|introduction|a', notes='The 1994 "Introduction" is probably Lyndal Roper\'s introduction to Oedipus and the Devil.')
o('williams|raymond', decision='mixed',
  foreign='W:williams|religions of immigrants from india and pakistan;W:williams|asian indian and pakistani religions in the united states|a;W:williams|south asian christians in britain canada and the united states|a',
  fnotes='All three = Raymond Brady Williams, scholar of South Asian religion in America (Wabash College)')
o('mitchell|timothy', decision='mixed', foreign='W:mitchell|frederic churchs the icebergs|a',
  fnotes='= Timothy Mitchell, American art historian (1989 essay on Frederic Church)')
o('russell|peter a', decision='mixed',
  foreign='W:russell|constitutionalodyssey;W:russell|nationalism in canada;W:russell|democratic approach to civil liberties|a;W:russell|can canada retrieve the principles of its first confederation|a;W:russell|correspondence of the honourable peter russell',
  fnotes='Constitutional Odyssey, Nationalism in Canada (ed.), A Democratic Approach to Civil Liberties, Can Canada Retrieve... = Peter H. Russell, political scientist (Q7174457); Correspondence of the Honourable Peter Russell (1932) = Peter Russell (1733-1808), Upper Canada administrator (Q7176713), a primary source',
  uncertain='W:russell|northern transitions', qs='wrong', cq='none_found',
  notes='Q124850303 is a German-based architect born 1963. No Wikidata item found for Peter A. Russell (agricultural/social historian of Upper Canada).',
  ev=WD+'Q124850303;'+WD+'Q7174457;'+WD+'Q7176713')
o('thompson|paul', decision='mixed',
  foreign='W:thompson|zulu rebellion of 1906|a;W:laband|battles of isandlwana and rorkes drift;W:thompson jr|most stirring and significant episode;W:thompson|nature ofwork',
  fnotes='Zulu Rebellion of 1906 and Battles of Isandlwana (with Laband) = Paul S. Thompson, South African historian; A Most Stirring and Significant Episode (2013) = H. Paul Thompson Jr.; The Nature of Work (1983) = Paul Thompson, sociologist of work (Strathclyde)',
  uncertain='W:savard|cultiver sa difference rapport sur les arts dans la vie franco ontarienne;W:thompson|life and death of trevor aston|a',
  qs='missing', cq='Q4460339', ev=WD+'Q4460339', notes='Q4460339 "British sociologist and oral historian" (b. 1935) found by exact label.')
o('thompson|john', decision='mixed', foreign='W:melville|boys week day book',
  fnotes='The Boy\'s Week-day Book (1836) is a 19th-century work, not by John Herd Thompson', uncertain='W:thompson|nicholas flood davin|a')
o('reid|john', decision='merge_into:P:reid|john g',
  foreign='W:reid|bibliotheca scoto celtica;W:reid|law for the elephant;W:reid|law of blood;W:reid|better kind of hatchet;W:reid|in a rebellious spirit;W:reid|missions and missionary society of the methodist episcopal church',
  fnotes='Bibliotheca Scoto-Celtica (1832) = John Reid, Scottish bibliographer; Law for the Elephant, A Law of Blood, A Better Kind of Hatchet, In a Rebellious Spirit = John Phillip Reid, American legal historian (NYU); Missions and Missionary Society of the Methodist Episcopal Church = J.M. Reid, 19th-century Methodist',
  qs='missing', cq='Q6234582', ev=WD+'Q6234582', notes='Mount Allison, Atlantic philanthropy, Nova Scotia pocket history, Viola Barnes biography and Mi\'kma\'ki essays are John G. Reid.')
o('coates|colin', decision='merge_into:P:coates|colin m', qs='missing', cq='none_found',
  notes='All works are Colin M. Coates (Heroines and History, landscape of early Quebec, Moving Natures).')
o('coates|colin m', qs='missing', cq='none_found', notes='No Wikidata item found by exact label (only an Australian speed skater, a footballer and a painter).')

# Uncertain-only flags
o('berger|carl', uncertain='W:berger|nationalism in canada', notes='Nationalism in Canada (1966) was edited by Peter H. Russell; Berger may be a contributor or this is a misattribution.')
o('walden|keith', uncertain='W:walden|invasion of canada 1812 1813', notes='The Invasion of Canada 1812-1813 is Pierre Berton\'s book; probably a review by Walden or a misattribution.')
o('tough|frank j', uncertain='W:tough|servants of the honourable company', qs='missing', cq='none_found',
  notes='Servants of the Honourable Company (1997) is Edith Burley\'s book; probably a review by Tough. No Wikidata item found.')
o('gillis|john r', uncertain='W:gillis|lovely letter from cecie the 1907 1915 vancouver diary and world war i letters o', notes='Vancouver diary edition (1998) is unlikely to be John R. Gillis; editor not confirmed.')
o('connell|raewyn w', uncertain='W:connell|ours is in colour|a', notes='"Ours Is In Colour: The New Left of the 1960s" (2014) is probably not Raewyn Connell.')
o('anderson|kay j', uncertain='W:anderson|indian days|a', qs='missing', cq='Q64175707', ev=WD+'Q64175707',
  notes='"Indian Days" (1978) predates Kay Anderson\'s career (b. 1958). Q64175707 "Australian geographer, b. 1958" found by exact label.')
o('mccallum|mary', uncertain='W:brown|racism in health system|a', notes='2014 news report on the Sinclair inquest; McCallum was probably quoted, not the author.')

# QID corrections / statuses
o('morgan|cecilia', qs='wrong', cq='none_found',
  notes='Q80511347 is an Argentine zoologist. Weak candidate Q87860728 is a bare "researcher" item with an empty ORCID record; not confirmed, so not proposed.',
  ev=WD+'Q80511347;'+WD+'Q87860728')
o('burton|antoinette m', qs='wrong', cq='Q4775575', ev=WD+'Q133344893;'+WD+'Q4775575',
  notes='Q133344893 is Eric Burton (b. 1987). Q4775575 = Antoinette Burton, American historian, b. 1961, University of Illinois.')
o('milloy|john s', qs='wrong', cq='none_found', ev=WD+'Q6248831',
  notes='Q6248831 is John Milloy, Ontario politician (b. 1965). No item found for the Trent historian John S. Milloy.')
o('lutz|john s', qs='wrong', cq='Q124739580', ev=WD+'Q132923033;'+WD+'Q124739580',
  notes='Q132923033 is Martin Lutz. Q124739580 = John S. Lutz, historian and university teacher, b. 1959.')
o('levine|philippa', qs='wrong', cq='Q48031813', ev=WD+'Q134459842;'+WD+'Q48031813',
  notes='Q134459842 is Ari Daniel Levine, sinologist. Q48031813 = Philippa Levine, British historian, b. 1957 (USC, UT Austin).')
o('martel|marcel', qs='wrong', cq='Q6756163', ev=WD+'Q113752161;'+WD+'Q6756163',
  notes='Q113752161 is Heather Martel. Q6756163 = Marcel Martel, Canadian historian, b. 1965.')
o('hunt|lynn', qs='wrong', cq='Q2613433', ev=WD+'Q131110548;'+WD+'Q2613433',
  notes='Q131110548 is Megan Hunt (Edinburgh). Q2613433 = Lynn Hunt, American historian, b. 1945 (UCLA, Penn).')
o('hubert|ollivier', qs='wrong', cq='Q56856757', ev=WD+'Q113485997;'+WD+'Q56856757',
  notes='Q113485997 is Etienne Hubert, French archaeologist. Q56856757 = Ollivier Hubert, historian, b. 1968, Universite de Montreal.')
o('mills|sean', qs='uncertain', ev=WD+'Q89475062',
  notes='Q89475062 is a conflated item: its ORCID (0000-0001-7866-7225) belongs to Sean R. Mills, a tactile-psychophysics researcher (Southampton/Oxford), while its BAnQ/VIAF IDs probably belong to the historian. Do not use until the item is split or the IDs are checked.')
o('perry|adele', qs='uncertain', ev=WD+'Q64626780',
  notes='Q64626780 is a bare "researcher" item with only a Semantic Scholar ID. It is probably the historian, but nothing confirms it.')
o('rutherdale|myra', notes='The item description says "British university teacher" and citizenship UK, which looks like a data error; the authority IDs (VIAF/GND/ISNI) match the author of these works.')
o('peers|douglas m', qs='correct')
o('milligan|gerry', notes='Key says gerry but name, QID and every work are Ian Milligan. Re-key the record.')
o('errington|elizabeth', notes='Elizabeth Jane Errington; QID label "Jane Errington".')
o('valverde|mariana', notes='Sociologist/criminologist by discipline; cited almost entirely for The Age of Light, Soap, and Water.')
o('cruikshank|julie', notes='Borderline type: anthropologist, but cited for Yukon oral history.')
o('trigger|bruce g', notes='Borderline type: anthropologist-archaeologist, cited for Huron-Wendat history.')
o('harris|cole r', notes='Borderline type: historical geographer.')
o('kelley|ninette', qs='missing', cq='none_found')
o('miller|james r', notes='QID supplied by user; also the merge target for P:miller|james.')

# Missing QIDs: found or none
for k, q, n in [
  ('mcclintock|anne', 'Q4768629', 'Zimbabwean-born cultural studies scholar, b. 1954; found by exact label.'),
  ('brewer|john', 'Q55938720', 'British historian, b. 1947; found by exact label.'),
]:
    O.setdefault(k, {}).update(qs='missing', cq=q, ev=WD+q, notes=n)
o('brewer|john', qs='missing', cq='Q55938720', ev=WD+'Q55938720', decision='mixed',
  foreign='W:brewer|sociology and theology reconsidered|a',
  fnotes='Sociology and Theology Reconsidered (2007) = John D. Brewer, sociologist (Queen\'s Belfast, Q6228652)',
  notes='Q55938720 "British historian, b. 1947" found by exact label.')
for k in ['curtis|bruce','fahrni|magda','rutherdale|robert','campbell|lara','igartua|jose e','raibmon|paige','van kirk|sylvia m',
          'ward|peter','knowles|valerie','podruchny|carolyn','brownlie|robin','sandwell|ruth w','heaman|elsbeth','adams|mary',
          'struthers|james','constant|jeanfrancois','hewitt|steve r','mackenzie|david','bederman|gail','patrias|carmela','frager|ruth a',
          'ens|gerhard j','binnema|theodore','gentile|patrizia','titley|brian','myers|tamara']:
    d = O.setdefault(k, {})
    d.setdefault('qs', 'missing'); d.setdefault('cq', 'none_found')
O['knowles|valerie']['notes'] = 'Only Q75822760 (b. 1911, no other data) matches the label; not confirmable as the Ottawa writer.'
O['mackenzie|david']['notes'] = 'Q16084410 (David MacKenzie 1927-2008) is the American historian of Serbia, not this person.'
O['ward|peter'].setdefault('notes', 'W. Peter Ward (UBC).')

out = []
seen = set()
for r in rows:
    k = r['person_key'][2:]
    seen.add(k)
    t, desc = TYPE[k]
    ov = O.get(k, {})
    qid = r['qid'] or ''
    qs = ov.get('qs', 'correct' if qid else 'missing')
    cq = ov.get('cq', '')
    ev = ov.get('ev', (WD + qid) if qid else '')
    out.append({
        'person_key': r['person_key'], 'name': r['name'],
        'decision': ov.get('decision', 'ok'),
        'foreign_work_ids': ov.get('foreign', ''), 'foreign_work_notes': ov.get('fnotes', ''),
        'uncertain_work_ids': ov.get('uncertain', ''),
        'qid_status': qs, 'qid_checked': qid, 'corrected_qid': cq,
        'person_type': t, 'description': desc, 'evidence_urls': ev, 'notes': ov.get('notes', ''),
    })
missing = set(O) - seen
assert not missing, missing
# validate foreign work ids exist in rows
wids = {r['person_key'][2:]: {w['work_id'] for w in r['works']} for r in rows}
bad = []
for row in out:
    k = row['person_key'][2:]
    for f in ('foreign_work_ids', 'uncertain_work_ids'):
        for w in filter(None, row[f].split(';')):
            if w not in wids[k]:
                bad.append((k, w))
if bad:
    print('BAD IDS', bad); sys.exit(1)
cols = ['person_key','name','decision','foreign_work_ids','foreign_work_notes','uncertain_work_ids','qid_status','qid_checked','corrected_qid','person_type','description','evidence_urls','notes']
with open(os.path.join(D, 'identity-review.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
import collections
print(len(out))
print(collections.Counter(r['decision'].split(':')[0] for r in out))
print(collections.Counter(r['qid_status'] for r in out))
print(collections.Counter(r['person_type'] for r in out))
print(collections.Counter((r['qid_status'], r['corrected_qid'] not in ('', 'none_found')) for r in out))
print(sum(1 for r in out if r['uncertain_work_ids'] and r['decision']=='ok'))
