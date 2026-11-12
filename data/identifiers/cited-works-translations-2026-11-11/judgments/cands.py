"""Candidate translations among unmatched cited works: title language vs the author's LC language profile."""
import re
import sys
import unicodedata

import duckdb
from langdetect import DetectorFactory, detect_langs

DetectorFactory.seed = 0
S = '/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations'
MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 3

STOP = {
    'por': 'o os a as do da dos das de em no na nos nas um uma para com e ao aos pela pelo pelas pelos entre sobre história historia sociedade seu sua não nao como ou memória brasil brasileira século trabalho',
    'spa': 'el los la las del de en un una para con y al por entre sobre historia sociedad su no como o memoria siglo trabajo españa',
    'fre': 'le les la des du de en un une pour avec et au aux par entre sur histoire société son sa ne pas comme ou mémoire siècle travail l d',
    'ger': 'der die das des dem den und zur zum im in ein eine für mit von auf über geschichte gesellschaft zwischen als oder nicht',
    'ita': 'il lo la gli le del della dei delle di in un una per con e al alla tra fra su storia società suo sua non come o memoria secolo',
    'eng': 'the of and in a an to for on with from by history society between as or not its their century work',
    'swe': 'och i en ett för med av på till om från historia samhälle mellan som eller inte',
}
STOP = {k: set(v.split()) for k, v in STOP.items()}
LD = {'pt': 'por', 'es': 'spa', 'fr': 'fre', 'de': 'ger', 'it': 'ita', 'en': 'eng', 'sv': 'swe', 'nl': 'dut', 'ca': 'cat', 'da': 'dan', 'no': 'nor', 'pl': 'pol'}


def lang_of(title):
    t = (title or '').lower()
    words = re.findall(r"[a-zà-ÿ]+", t.replace("'", ' ').replace('’', ' '))
    score = {k: sum(w in s for w in words) for k, s in STOP.items()}
    if re.search('[ãõç]', t) or re.search(r'\b(ção|ções)', t):
        score['por'] = score.get('por', 0) + 2
    if re.search('[ñ¿¡]', t) or re.search(r'ción\b|ciones\b', t):
        score['spa'] = score.get('spa', 0) + 2
    if re.search('[äöüß]', t):
        score['ger'] = score.get('ger', 0) + 1
    if re.search('[èêàç]', t) and 'por' not in [k for k, v in score.items() if v]:
        score['fre'] = score.get('fre', 0) + 1
    try:
        ld = detect_langs(title)
        for x in ld[:1]:
            if x.lang in LD and x.prob > 0.8:
                score[LD[x.lang]] = score.get(LD[x.lang], 0) + 1.5
    except Exception:
        pass
    best = sorted(score.items(), key=lambda kv: -kv[1])
    if not best or best[0][1] < 1.5 or (len(best) > 1 and best[1][1] == best[0][1]):
        return '', best[0][1] if best else 0
    return best[0][0], best[0][1]


def nt0(s):
    s = unicodedata.normalize('NFKD', (s or '').replace('œ', 'oe').replace('Œ', 'Oe').replace('æ', 'ae').replace('ß', 'ss')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', re.sub(r"['’]", ' ', s)).strip()


def first_author(a):
    a = (a or '').split(';')[0].strip()
    fam, _, giv = a.partition(',')
    fam = re.sub(r'\b(jr|júnior|junior|filho|neto)\b\.?', '', fam, flags=re.I).strip() or fam
    return nt0(fam), nt0(giv)[:1]


def main():
    db = duckdb.connect(f'{S}/t.duckdb')
    db.execute("SET memory_limit='3GB'; SET threads=3")
    rows = db.execute(f"SELECT work_id, n, authors, title, yr, kind, br, ca, gb, us, oth FROM unmatched WHERE n >= {MIN}").fetchall()
    out = []
    for wid, n, authors, title, yr, kind, br, ca, gb, us, oth in rows:
        fam, ini = first_author(authors)
        lang, sc = lang_of(title)
        out.append((wid, n, authors, title, yr, kind, br, ca, gb, us, oth, fam, ini, fam + '|' + ini, lang, sc))
    db.execute("CREATE OR REPLACE TABLE ucand (work_id VARCHAR, n INT, authors VARCHAR, title VARCHAR, yr INT, kind VARCHAR, br INT, ca INT, gb INT, us INT, oth INT, fam VARCHAR, ini VARCHAR, ak VARCHAR, tlang VARCHAR, tscore DOUBLE)")
    db.executemany("INSERT INTO ucand VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", out)
    print(len(out))


if __name__ == '__main__':
    main()
