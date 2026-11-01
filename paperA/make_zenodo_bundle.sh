#!/usr/bin/env bash
# Builds the Zenodo archive for the paper: copies the code, regenerates every
# output, records the environment, writes SHA256SUMS and zips the result.
#   bash make_zenodo_bundle.sh
# Optional: PY=/path/to/python  OUT=/path/to/output_dir
set -euo pipefail
PY=${PY:-/home/rahul/Research/.venv_aug/bin/python}
SRC=$(cd "$(dirname "$0")" && pwd)
NAME=hidden-structure-value-code-v1.0.0
OUT=${OUT:-$SRC/../zenodo_release}
STAGE=$OUT/$NAME

rm -rf "$STAGE" "$OUT/$NAME.zip"
mkdir -p "$STAGE/code"
cp "$SRC"/verify_theorem.py "$SRC"/remark1_analysis.py "$SRC"/exp_A_idx_vs_evppi.py \
   "$SRC"/pool_evppi.py "$SRC"/exp_E_conjecture1.py "$STAGE/code/"
cp "$SRC"/zenodo/README.md "$SRC"/zenodo/LICENSE "$SRC"/zenodo/requirements.txt \
   "$SRC"/zenodo/run_all.sh "$STAGE/"

PY="$PY" bash "$STAGE/run_all.sh"

"$PY" -c "import sys, platform, numpy, scipy, pandas, matplotlib
print('python', sys.version.split()[0])
print('platform', platform.system(), platform.machine())
for m in (numpy, scipy, pandas, matplotlib): print(m.__name__, m.__version__)" > "$STAGE/environment.txt"

(cd "$STAGE" && find . -type f ! -name SHA256SUMS | LC_ALL=C sort | xargs sha256sum > SHA256SUMS)
(cd "$OUT" && zip -qrX "$NAME.zip" "$NAME")
echo "built: $OUT/$NAME.zip ($(du -h "$OUT/$NAME.zip" | cut -f1))"
