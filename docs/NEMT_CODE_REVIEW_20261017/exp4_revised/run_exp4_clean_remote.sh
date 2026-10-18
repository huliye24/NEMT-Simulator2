#!/bin/bash
# Quick start script for Experiment 4 Clean on remote servers
# Usage: ./run_exp4_clean_remote.sh [output_dir] [make_figures]

set -e

# Configuration
PROJECT_ROOT="/home/user/NEMT_Simulator"
CODE_DIR="${PROJECT_ROOT}/docs/NEMT_CODE_REVIEW_20261017"
CORE_DIR="${CODE_DIR}/core"
OUTPUT_DIR="${1:-${PROJECT_ROOT}/results/exp4_clean_$(date +%Y%m%d_%H%M%S)}"
MAKE_FIGURES="${2:-false}"

# Validation
if [ ! -d "$CORE_DIR" ]; then
    echo "ERROR: NEMT core directory not found: $CORE_DIR"
    exit 1
fi

if [ ! -f "${CODE_DIR}/exp4_revised/run_exp4_clean.m" ]; then
    echo "ERROR: run_exp4_clean.m not found"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "Output directory: $OUTPUT_DIR"

# Run experiment
echo "Starting Experiment 4 Clean (R4 Protocol)..."
matlab -batch "
    cd('${CODE_DIR}');
    addpath('${CORE_DIR}');
    run_exp4_clean('output', '${OUTPUT_DIR}', 'makeFigures', ${MAKE_FIGURES});
    exit(0);
" 2>&1 | tee "${OUTPUT_DIR}/matlab.log"

# Verify output
if [ ! -f "${OUTPUT_DIR}/RUN_COMPLETE.txt" ]; then
    echo "ERROR: Experiment did not complete successfully"
    tail -20 "${OUTPUT_DIR}/matlab.log"
    exit 1
fi

# Report
echo "====== Experiment Complete ======"
cat "${OUTPUT_DIR}/RUN_COMPLETE.txt"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo "CSV files:"
ls -lh "${OUTPUT_DIR}"/*.csv 2>/dev/null || echo "  (no CSV files generated)"
echo ""
echo "Verdict:"
head -10 "${OUTPUT_DIR}/verdict.csv" 2>/dev/null || echo "  (no verdict file)"
echo ""
echo "====== Summary ======"
grep -E "^(PASS|FAIL)" "${OUTPUT_DIR}/verdict.csv" | sort | uniq -c || true
