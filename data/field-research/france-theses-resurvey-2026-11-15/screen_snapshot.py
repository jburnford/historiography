"""Screen an ABES open-data snapshot ("Theses soutenues en France depuis 1985", data.gouv.fr) for History doctorates.

Streams the file (gz or plain NDJSON; no full load). Writes:
  OUT/disciplines.csv            every discipline string with a history/economics-history word, count, verdict
  OUT/history-screen.jsonl.gz    defended theses whose discipline passes (slim rows, with the verdict as 'screen')
Corrected screen (2026-11-15). Kept: History in all its period/area forms, history of religions, history of
international relations, history of science/technology/mathematics (incl. "Philosophie, epistemologie. Histoire
des sciences"), economic history (user, 2026-11-15), ancient history disciplines that do not use the word or
pair it with languages ("Langues, histoire et civilisations des mondes anciens", "Sciences historiques (et
philologiques)", "Etudes medievales"), and the generic Paris doctoral label "Histoire et civilisations : histoire
des mondes modernes, ... de l'art, de la musique". Excluded as before: art, architecture, film, music, law,
literature/language and philosophy histories, archaeology and prehistory; also anthropology, geography and
semiology disciplines that only mention history. Verdicts: history | science | economic | ancient | '' (out).
usage: python3 -I screen_snapshot.py SNAPSHOT OUTDIR
"""
import collections
import csv
import gzip
import json
import re
import sys
import unicodedata
from pathlib import Path


def fold(s):
    s = (s or '').replace('\u2019', "'").replace('\u02bc', "'")
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', s).strip()


HIST = re.compile(r'histoire|histor|hstoire|hisoire|histoires')
GENERIC = re.compile(r'mondes? modernes?|monde contemporain|histoire et civilisations?')
SCI = re.compile(r'histoire des sciences|histoire de sciences|histoires des sciences|histoire des techniques|'
                 r'histoire des mathematiques|philosophie des sciences|philosophie des mathematiques|epistemologie|'
                 r'history of science|history and philosophy of science|histoire et philosophie des sciences|'
                 r'didactique des sciences')
ECON = re.compile(r'histoire econom|economic history|histoire et economie|economie et histoire|'
                  r'histoire sociale et econom|histoire des faits economiques|histoire de la pensee economique|'
                  r'cliometr|histoire de l.economie|economie, histoire')
ANCIENT = re.compile(r'mondes anciens|sciences historiques|etudes medievales|^antiquite|civilisations? antiques?|'
                     r'sciences de l.antiquite|etudes anciennes|mondes antiques')
OUT = re.compile(r"histoire de l'art|histoire des arts|\barts?\b|artistique|architect|cinema|film|audiovisu|musi|"
                 r"droit|juridique|litter|langue|linguist|philosoph|archeo|prehist|protohist|anthropolog|ethnolog|"
                 r"geograph|semiolog|histolog|theatre|danse|patrimoine|histoire de l.ecrit|histoire du livre")


def verdict(disc):
    d = fold(disc)
    if 'histolog' in d or 'phrehist' in d or 'de lart' in d:
        return ''
    if SCI.search(d) and HIST.search(d):
        return 'science'
    if ECON.search(d):
        return 'economic'
    if ANCIENT.search(d) and not re.search(r'archeo|prehist|art\b', d):
        return 'ancient'
    if not HIST.search(d):
        return ''
    if GENERIC.search(d) and d.startswith(('histoire et civilisation', 'histoire des civilisations',
                                           'histoire. histoire et civilisation', 'sciences humaines et humanites. histoire',
                                           'histoire, civilisation')):
        return 'history'
    if d.startswith(('histoire des religions', 'histoire religieuse')):
        return 'history'
    if OUT.search(d):
        return ''
    return 'history'


def main():
    src, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    counts = collections.Counter()
    status = collections.Counter()
    ddc_other = collections.Counter()
    n = 0
    opener = gzip.open if src.suffix == '.gz' else open
    with opener(src, 'rt', encoding='utf-8') as f, \
            gzip.open(outdir / 'history-screen.jsonl.gz', 'wt', encoding='utf-8') as out:
        for line in f:
            n += 1
            try:
                d = json.loads(line)
            except Exception:
                continue
            disc = d.get('discipline') or ''
            fd = fold(disc)
            v = verdict(disc)
            ddc = [x for x in (d.get('oai_set_specs') or []) if str(x).startswith('ddc:9') and not str(x).startswith('ddc:91')]
            if not v and 'econom' in fd:
                subj = ' '.join(fold(x) for x in (d.get('sujets_rameau') or []))
                if ddc or re.search(r'histoire economique|-- histoire|economic history', subj):
                    v = 'economic-subject'
            if not v and ddc:
                ddc_other[disc] += 1
            if HIST.search(fd) or v or ('econom' in fd and 'hist' in fd):
                counts[(disc, v)] += 1
            if not v:
                continue
            status[(v, d.get('status'), d.get('accessible'))] += 1
            if d.get('status') != 'soutenue':
                continue
            slim = {k: d.get(k) for k in ('nnt', 'titres', 'date_soutenance', 'discipline', 'accessible', 'cas',
                                         'embargo', 'code_etab', 'etablissements_soutenance', 'auteurs', 'auteur',
                                         'directeurs_these', 'langues', 'source', 'oai_set_specs')}
            slim['screen'] = v
            out.write(json.dumps(slim, ensure_ascii=False) + '\n')
    with (outdir / 'disciplines.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['discipline', 'screen', 'n'])
        for (disc, v), c in counts.most_common():
            w.writerow([disc, v or 'excluded', c])
    with (outdir / 'ddc-history-other-disciplines.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['discipline', 'n_with_ddc_9xx_not_91x'])
        for disc, c in ddc_other.most_common():
            w.writerow([disc, c])
    print('lines', n)
    for k, v in sorted(status.items(), key=lambda x: -x[1]):
        print(v, k)


if __name__ == '__main__':
    main()
