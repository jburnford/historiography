#!/bin/bash
# Knowledge-graph build on Plato (2026-11-18): scripts/build_graph.py, then scripts/graph_explorer.py build, each under
# /usr/bin/time -v so the log records peak memory (Maximum resident set size) and wall time.
# Run from a clean copy of the repo (git archive of the tracked scripts, data/graph, the key-log shards and the few
# data/identifiers tables the build reads, committed in a local git repo so require_tracked passes) plus
# build/keylog-state.sqlite. No partition, node or --gres: a CPU job.
#   cd <copy>/repo && OUT_NAME=graph-base sbatch ../kg-build.slurm
#   OUT_NAME   output folder under build/ (default graph)
#   EXPLORER   1 = also build <out>/explorer.duckdb (default 1)
#SBATCH --job-name=kg-build
#SBATCH --time=06:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --output=../logs/%x-%j.out
set -euo pipefail
source /project/clifford/historiography-kg/env.sh
OUT_NAME=${OUT_NAME:-graph}
EXPLORER=${EXPLORER:-1}
cd "${SLURM_SUBMIT_DIR}"
echo "repo $(pwd) out build/${OUT_NAME} $(git log -1 --format='%h %s')"
git status --short | head -20
python -c "import duckdb, pyarrow; print('duckdb', duckdb.__version__, 'pyarrow', pyarrow.__version__)"
echo "== build_graph $(date -Is)"
/usr/bin/time -v python scripts/build_graph.py --out "build/${OUT_NAME}"
if [ "${EXPLORER}" = 1 ]; then
    echo "== graph_explorer build $(date -Is)"
    EXPLORER_GRAPH="$(pwd)/build/${OUT_NAME}" /usr/bin/time -v python scripts/graph_explorer.py build
fi
echo "== done $(date -Is)"
