#!/usr/bin/env python3
"""One command for the Brazil expansion (data/field-research/brazil-theses-2026-10-31).

    python3 scripts/brazil_pipeline.py status     # what each step has produced; which jobs are running
    python3 scripts/brazil_pipeline.py cleanup    # delete the unused USP OAI records (oai/USP.FFLCH.jsonl.part)
    python3 scripts/brazil_pipeline.py run        # run every step in order, resuming; skips a step already running
    python3 scripts/brazil_pipeline.py handoff    # rebuild the browser list (bot-checked universities) on E:
    python3 scripts/brazil_pipeline.py register   # match PDFs you saved in the browser-drop folder to CAPES

Steps (each is resumable and skips finished work):
  1. capes     scripts/capes_catalogue_harvest.py   CAPES catalogue, History rows (capes-raw/, not in git)
     slim      scripts/brazil_slim_capes.py         doctorate rows, no abstracts (capes/, committed)
  2. oai       scripts/brazil_oai_harvest.py        OAI History sets (robots-checked)
  3. uff       scripts/brazil_uff_ppgh.py           UFF programme thesis list
  4. usp       scripts/brazil_usp_sitemap.py        USP sitemap + item pages
  5. match     scripts/brazil_match_capes.py        repository records -> CAPES doctorates
  6. download  <folder>/download_brazil.py          open PDFs to E:
``run --from match`` starts at a later step; ``run --only download`` runs one step.
Output goes to the terminal and to <folder>/logs/pipeline-<step>.log.
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/brazil-theses-2026-10-31'
PY = sys.executable
STEPS = [
    ('capes', ['scripts/capes_catalogue_harvest.py', '--out', str(D)]),
    ('slim', ['scripts/brazil_slim_capes.py', '--out', str(D)]),
    ('oai', ['scripts/brazil_oai_harvest.py', '--out', str(D)]),
    ('uff', ['scripts/brazil_uff_ppgh.py', '--out', str(D)]),
    ('usp', ['scripts/brazil_usp_sitemap.py', '--out', str(D)]),
    ('match', ['scripts/brazil_match_capes.py', '--out', str(D)]),
    ('download', [str(D / 'download_brazil.py')]),
]


def running(script):
    out = subprocess.run(['pgrep', '-f', f'python3? .*{Path(script).name}'], capture_output=True, text=True).stdout
    return [p for p in out.split() if p.strip()]


def lines(path):
    return sum(1 for _ in open(path, encoding='utf-8')) if path.exists() else 0


def status():
    capes = sorted(p for p in (D / 'capes').glob('*.jsonl') if p.stem != 'harvest-log')
    print(f'capes     {len(capes)} year files ({sum(lines(p) for p in capes):,} doctorate rows); '
          f"2022 present: {(D / 'capes/2022.jsonl').exists()}")
    oai = sorted((D / 'oai').glob('*.jsonl'))
    print(f'oai       ' + ', '.join(f'{p.stem} {lines(p)}' for p in oai))
    print(f"uff       {lines(D / 'uff-ppgh/records.jsonl')} entries")
    urls = D / 'usp/urls.json'
    n_urls = len(json.loads(urls.read_text())) if urls.exists() else 'sitemap not finished'
    print(f"usp       {lines(D / 'usp/records.jsonl')} pages read of {n_urls}")
    cands = D / 'candidates.json'
    print(f"match     {len(json.loads(cands.read_text())) if cands.exists() else 0} matched doctorates")
    rows = {}
    if (D / 'downloads.jsonl').exists():
        for l in open(D / 'downloads.jsonl', encoding='utf-8'):
            r = json.loads(l)
            rows[r['key']] = r['status']
    print(f'download  {dict(Counter(rows.values()))}')
    for name, cmd in STEPS:
        pids = running(cmd[0])
        if pids:
            print(f'  running: {name} (pid {" ".join(pids)})')
    stray = D / 'oai/USP.FFLCH.jsonl.part'
    if stray.exists():
        print(f'  note: {stray.relative_to(ROOT)} is unused (robots-disallowed harvest); remove with `cleanup`')


def cleanup():
    stray = D / 'oai/USP.FFLCH.jsonl.part'
    if not stray.exists():
        print('nothing to clean')
        return
    if running('brazil_oai_harvest.py'):
        sys.exit('the OAI harvest is running; stop it first')
    stray.unlink()
    print(f'deleted {stray.relative_to(ROOT)}')


def run(start, only):
    names = [n for n, _ in STEPS]
    todo = [s for s in STEPS if (only and s[0] == only) or (not only and names.index(s[0]) >= names.index(start))]
    (D / 'logs').mkdir(exist_ok=True)
    for name, cmd in todo:
        if running(cmd[0]):
            print(f'== {name}: already running, skipped (wait for it, then rerun from here)')
            if name in ('usp', 'match', 'download'):
                return
            continue
        print(f'== {name}: {" ".join(cmd)}', flush=True)
        with open(D / 'logs' / f'pipeline-{name}.log', 'a', encoding='utf-8') as log:
            p = subprocess.Popen([PY, *cmd], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                print(line, end='', flush=True)
                log.write(line)
            if p.wait() != 0:
                sys.exit(f'{name} failed (exit {p.returncode}); see logs/pipeline-{name}.log')
    status()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['status', 'cleanup', 'run', 'handoff', 'register'])
    ap.add_argument('--from', dest='start', default='capes', choices=[n for n, _ in STEPS])
    ap.add_argument('--only', choices=[n for n, _ in STEPS])
    a = ap.parse_args()
    if a.command in ('handoff', 'register'):
        script = {'handoff': ['scripts/brazil_browser_handoff.py', '--out', str(D)],
                  'register': ['scripts/register_brazil_browser_downloads.py']}[a.command]
        sys.exit(subprocess.run([PY, *script], cwd=ROOT).returncode)
    {'status': status, 'cleanup': cleanup}.get(a.command, lambda: run(a.start, a.only))()


if __name__ == '__main__':
    main()
