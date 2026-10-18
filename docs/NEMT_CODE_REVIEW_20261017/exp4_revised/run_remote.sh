#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ubuntu/nemt_matlab_lab/next_experiments_20261017
OLD_RUN="$ROOT/runs/20261017T073704Z"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_exp4R"
RUN_DIR="$ROOT/runs/$RUN_ID"
mkdir -p "$RUN_DIR/exp4_revised"

cat > "$OLD_RUN/INVALIDATED.md" <<'EOF'
# INVALIDATED — 2026-10-17

Experiment 4 and its downstream BLOCKED decision are scientifically invalid.
The soliton was spatially under-resolved, the long-time comparison used unequal
physical end times, the scaling gate did not test the theoretical exponent, and
two figures failed to apply logarithmic axes.  Files are retained only as an
audit trail and must not be cited as evidence.
EOF

cp -a "$ROOT/exp4_revised/." "$RUN_DIR/code_snapshot/" 2>/dev/null || {
  mkdir -p "$RUN_DIR/code_snapshot"
  cp -a "$ROOT/exp4_revised/." "$RUN_DIR/code_snapshot/"
}
sha256sum "$ROOT/exp4_revised/run_exp4_revised.m" \
  "$ROOT/exp4_revised/EXPERIMENT_PROTOCOL.md" > "$RUN_DIR/INPUT_SHA256SUMS.txt"

LOG="$RUN_DIR/matlab.log"
CMD="addpath('$ROOT/exp4_revised'); run_exp4_revised('output','$RUN_DIR/exp4_revised','makeFigures',true);"
nohup /home/ubuntu/MATLAB/R2023b/bin/matlab -licmode online -batch "$CMD" > "$LOG" 2>&1 &
PID=$!
printf '%s\n' "$PID" > "$RUN_DIR/matlab.pid"
printf '%s\n' "$RUN_DIR"
printf '%s\n' "$PID"
