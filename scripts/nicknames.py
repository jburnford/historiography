"""Standard English given-name nicknames (2026-11-12; ARCHITECTURE.md section 8, class 32).

For the POSSIBLY_SAME candidate test only (scripts/possible_same_nicknames.py): 'Katie Magee Labelle' and 'Kathryn
Magee Labelle' share a canonical first name. Never used for automatic merges, and not in link_work_people.py's
refusal of disagreeing names. A nickname maps to one or more formal names; two given names agree when they are equal
or their canonical sets meet. Diminutives that are themselves common formal names in some languages (e.g. 'Nico',
'Toni') are left out, and so are gender-ambiguous forms that would join two formal names of different people
('Chris' joins Christopher and Christine: both are listed, so 'Chris' agrees with either, but Christopher never
agrees with Christine).
"""

# formal name -> its common nicknames (English usage)
FORMAL = {
    'abigail': 'abby abbie gail', 'albert': 'al bert bertie', 'alexander': 'alex alec sandy sasha', 'alexandra': 'alex alexa sandra sandy sasha',
    'alfred': 'al alf alfie fred', 'allan': 'al', 'alan': 'al', 'andrew': 'andy drew', 'angela': 'angie', 'anthony': 'tony',
    'antonio': 'tony', 'arthur': 'art artie', 'barbara': 'barb barbie babs', 'benjamin': 'ben benny benji',
    'bernard': 'bernie', 'beverly': 'bev', 'bradley': 'brad', 'catherine': 'cathy cate kate kathy katie kay kit',
    'katherine': 'kathy kate katie kay kit kathi', 'kathryn': 'kathy kate katie kay kit', 'kathleen': 'kathy kate katie kay',
    'caroline': 'carrie carol', 'carolyn': 'carrie carol', 'charles': 'charlie chuck chas chaz', 'christine': 'chris chrissy tina',
    'christina': 'chris tina', 'christopher': 'chris kit topher', 'clifford': 'cliff', 'cynthia': 'cindy',
    'daniel': 'dan danny', 'danielle': 'dani', 'david': 'dave davy', 'deborah': 'deb debbie debby', 'dennis': 'denny',
    'donald': 'don donny', 'dorothy': 'dot dottie dolly', 'douglas': 'doug', 'edward': 'ed eddie ned ted teddy',
    'edwin': 'ed', 'eleanor': 'ellie nell nora', 'elizabeth': 'beth betsy betty eliza liz lizzie libby bess elsie',
    'emily': 'em emmy', 'eugene': 'gene', 'frances': 'fran frannie', 'francis': 'frank fran', 'franklin': 'frank',
    'frederick': 'fred freddie fritz', 'gabriel': 'gabe', 'gerald': 'gerry jerry', 'gregory': 'greg',
    'harold': 'hal harry', 'henry': 'hank harry hal', 'herbert': 'herb bert', 'isabel': 'izzy bel', 'jacob': 'jake',
    'james': 'jim jimmy jamie', 'janet': 'jan', 'jeffrey': 'jeff', 'jennifer': 'jen jenny jenn', 'jessica': 'jess jessie',
    'joan': 'joanie', 'jonathan': 'jon jonny', 'joseph': 'joe joey jos', 'joshua': 'josh', 'judith': 'judy jude',
    'kenneth': 'ken kenny', 'kimberly': 'kim', 'lawrence': 'larry', 'laurence': 'larry laurie', 'leonard': 'len lenny leo',
    'louis': 'lou', 'louise': 'lou lulu', 'margaret': 'maggie meg peggy marge margie greta molly', 'matthew': 'matt',
    'michael': 'mike mick mickey', 'nathaniel': 'nat nate', 'nathan': 'nate', 'nicholas': 'nick nicky', 'pamela': 'pam',
    'patricia': 'pat patty trish tricia', 'patrick': 'pat paddy', 'peter': 'pete', 'philip': 'phil', 'phillip': 'phil',
    'rebecca': 'becky becca', 'richard': 'dick rick ricky rich richie', 'robert': 'bob bobby rob robbie bert',
    'roberta': 'bobbie', 'ronald': 'ron ronnie', 'rosemary': 'rose rosie', 'samuel': 'sam sammy', 'samantha': 'sam',
    'sandra': 'sandy', 'stephen': 'steve stevie', 'steven': 'steve stevie', 'susan': 'sue susie suzy', 'suzanne': 'sue suzy',
    'theodore': 'ted teddy theo', 'thomas': 'tom tommy', 'timothy': 'tim timmy', 'valerie': 'val', 'victoria': 'vicky tori',
    'vincent': 'vince vinny', 'walter': 'walt wally', 'william': 'bill billy will willie liam', 'zachary': 'zach zack',
}
# spelling variants of one formal name (they agree with each other)
VARIANTS = [('catherine', 'katherine', 'kathryn', 'katharine', 'catharine', 'kathrine'), ('stephen', 'steven'),
            ('philip', 'phillip'), ('jeffrey', 'geoffrey'), ('allan', 'alan', 'allen'), ('lawrence', 'laurence'),
            ('frederick', 'frederic'), ('isabel', 'isabelle', 'isobel'), ('susan', 'suzanne')]

CANON = {}
for formal, nicks in FORMAL.items():
    for n in nicks.split():
        CANON.setdefault(n, set()).add(formal)
for group in VARIANTS:
    for a in group:
        CANON.setdefault(a, set()).update(group)
for formal in FORMAL:
    CANON.setdefault(formal, set()).add(formal)


def canon(given):
    """the formal names a first given name stands for (itself when unknown)"""
    g = (given or '').lower().strip('. ')
    out = set(CANON.get(g, ())) | {g}
    for f in list(out):                    # a formal name's spelling variants
        for v in VARIANTS:
            if f in v:
                out.update(v)
    return out


def nickname_agree(a, b):
    """True when two first given names are different but one is a nickname or variant of the other (or both of one
    formal name): 'katie' / 'kathryn', 'bill' / 'william', 'steve' / 'stephen'. Equal names and initials are not this
    test's business (False)."""
    a, b = (a or '').lower().strip('. '), (b or '').lower().strip('. ')
    if not a or not b or a == b or len(a) < 2 or len(b) < 2:
        return False
    ca, cb = canon(a), canon(b)
    if a in FORMAL and b in FORMAL:          # two formal names agree only as spelling variants
        return any(a in v and b in v for v in VARIANTS)
    return bool(ca & cb)
