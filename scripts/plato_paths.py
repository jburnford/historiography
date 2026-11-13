"""Run the linkers on a cluster copy of the workspace (2026-11-13).

Several scripts name raw inputs on the external drive as module constants ('/mnt/e/...'). On Plato the metadata the
linkers read is mirrored under $E_MIRROR with the same relative paths (e.g. $E_MIRROR/lc-authorities/personal-names.parquet).
patch() rewrites every '/mnt/e' constant of the loaded linker modules to the mirror; nothing is edited on disk.

    python scripts/plato_paths.py link_work_people link --new-facts ...     # = link_work_people.py with patched paths

Locally (no E_MIRROR set) patch() does nothing.
"""
import importlib
import os
import sys
from pathlib import Path

MODULES = ('link_cited_work_authors', 'link_work_people', 'key_review_reviewers', 'key_review_credit_merges', 'score_links')


def patch(mirror=None):
    mirror = mirror or os.environ.get('E_MIRROR')
    if not mirror:
        return 0
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    n = 0
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except Exception as e:          # a module that fails to import is not needed by the run
            print('plato_paths: skip', name, type(e).__name__, e, file=sys.stderr)
            continue
        for k, v in list(vars(mod).items()):
            if isinstance(v, (str, Path)) and str(v).startswith('/mnt/e'):
                nv = mirror.rstrip('/') + str(v)[len('/mnt/e'):]
                setattr(mod, k, Path(nv) if isinstance(v, Path) else nv)
                n += 1
    print('plato_paths: patched', n, 'constants to', mirror, file=sys.stderr, flush=True)
    return n


if __name__ == '__main__':
    mod = sys.argv[1]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    m = importlib.import_module(mod)
    patch()
    sys.argv = [mod + '.py'] + sys.argv[2:]
    m.main()
