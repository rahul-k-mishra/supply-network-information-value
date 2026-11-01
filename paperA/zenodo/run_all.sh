#!/usr/bin/env bash
# Regenerates outputs/ from code/. Run from anywhere; set PY to choose the
# interpreter (default: python).
set -euo pipefail
PY=${PY:-python}
export PYTHONDONTWRITEBYTECODE=1
ROOT=$(cd "$(dirname "$0")" && pwd)
C=$ROOT/code
O=$ROOT/outputs
SEEDS="20260812 733 40427 991 20260101"

rm -rf "$O"
mkdir -p "$O/verify" "$O/remark1" "$O/exp_A" "$O/exp_E"

echo "verify_theorem.py";   (cd "$O/verify"  && "$PY" "$C/verify_theorem.py"   > console.txt)
echo "remark1_analysis.py"; (cd "$O/remark1" && "$PY" "$C/remark1_analysis.py" > console.txt)

for s in $SEEDS; do
  echo "exp_A_idx_vs_evppi.py seed $s"
  mkdir -p "$O/exp_A/seed_$s"
  (cd "$O/exp_A/seed_$s" && "$PY" "$C/exp_A_idx_vs_evppi.py" --n-instances 2000 --seed "$s" > console.txt)
done
"$PY" "$C/pool_evppi.py" "$O"/exp_A/seed_*/exp_A_idx_vs_evppi.csv > "$O/exp_A/pooled.txt"

echo "exp_E_conjecture1.py, five seeds in parallel"
pids=()
for s in $SEEDS; do
  mkdir -p "$O/exp_E/seed_$s"
  (cd "$O/exp_E/seed_$s" && "$PY" "$C/exp_E_conjecture1.py" --n-instances 20000 --seed "$s" > console.txt) &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done
echo "done: outputs/ regenerated"
