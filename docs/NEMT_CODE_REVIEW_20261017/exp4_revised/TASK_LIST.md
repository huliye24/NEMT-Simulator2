# Exp4 Clean Task List

## Quick Commands

```bash
# Local MATLAB full run (25 min)
make run-full

# Cloud server data-only (12 min)
make run-cloud

# Quick validation (3 min)
make run-quick

# Check results
make check

# Archive & clean
make archive
```

---

## Task Definitions

### run-full
**Description**: Full local run with figures  
**Time**: 25 min  
**Requirements**: MATLAB R2020b+, 4GB RAM, 4 CPU cores

```bash
cd /path/to/NEMT_CODE_REVIEW_20261017
matlab -batch "
    addpath('core');
    run_exp4_clean('output', './results/exp4_full', 'makeFigures', true);
    exit(0);
"
```

---

### run-cloud
**Description**: Cloud server run without figures  
**Time**: 12 min  
**Requirements**: SSH access, MATLAB license

```bash
ssh cloud-server << 'EOF'
cd /path/to/exp4_revised
./run_exp4_clean_remote.sh /mnt/results/exp4_$(date +%Y%m%d) false
EOF

# Download results
scp -r cloud-server:/mnt/results/exp4_* ./local/
```

---

### run-quick
**Description**: Quick validation with coarse grid  
**Time**: 3 min  
**Requirements**: Same as run-full

**Step 1**: Edit `run_exp4_clean.m` line 26-28:
```matlab
Ns=[256 384];        % Only 2 grids
Tspace=0.1;          % Shorter
dts=[0.004 0.002];   % Fewer
```

**Step 2**: Run
```bash
matlab -batch "
    addpath('core');
    run_exp4_clean('output', './results/exp4_quick', 'makeFigures', false);
    exit(0);
"
```

---

### check
**Description**: Verify results and gates

```bash
# Check completion
tail results/exp4_*/RUN_COMPLETE.txt

# Count PASS gates (should be 5)
grep -c PASS results/exp4_*/verdict.csv

# Show all gates
cut -d, -f1,4,5 results/exp4_*/verdict.csv | tail -n +2

# Extract key metrics
awk -F, 'NR==2{printf "RK4 order: %.2f\n", $2}' \
    results/exp4_*/temporal_orders.csv

# List output files
ls -lh results/exp4_*/*.csv
```

---

### archive
**Description**: Archive results and cleanup

```bash
# Create tarball
tar -czf exp4_archive_$(date +%Y%m%d_%H%M%S).tar.gz \
    results/exp4_*/

# Verify archive
tar -tzf exp4_archive_*.tar.gz | head

# Optional: cleanup figures (keep CSV)
rm -f results/exp4_*/*.png results/exp4_*/*.pdf results/exp4_*/*.svg

# Check final size
du -sh results/exp4_*/
du -sh exp4_archive_*.tar.gz
```

---

## Advanced Tasks

### run-with-profile
**Description**: Run with MATLAB profiler

```bash
matlab -batch "
    addpath('core');
    profile on;
    run_exp4_clean('output', './results/exp4_profile', 'makeFigures', false);
    profile off;
    profsave(profile('info'), './results/profile_report');
    exit(0);
"
```

---

### run-parallel
**Description**: Run multiple configurations in parallel (requires GNU parallel)

```bash
parallel -j 3 --header : \
  'matlab -batch "addpath(\"core\"); run_exp4_clean(\"output\", \"./results/exp4_{config}\", \"makeFigures\", false);"' \
  ::: config coarse medium fine

# coarse: Ns=[256,384]
# medium: Ns=[256,384,512]
# fine: Ns=[256,384,512,768]
```

---

### compare-runs
**Description**: Compare two runs

```bash
RUN1=results/exp4_baseline
RUN2=results/exp4_new

# Compare verdicts
diff <(cut -d, -f1,4 $RUN1/verdict.csv) \
     <(cut -d, -f1,4 $RUN2/verdict.csv)

# Compare temporal orders
diff <(tail -n +2 $RUN1/temporal_orders.csv) \
     <(tail -n +2 $RUN2/temporal_orders.csv)

# Show numerical drift
paste <(cut -d, -f2 $RUN1/spatial_convergence.csv) \
      <(cut -d, -f2 $RUN2/spatial_convergence.csv) | \
  awk '{print $1, $2, $2-$1}'
```

---

### generate-report
**Description**: Generate summary report

```bash
cat > results/REPORT.md << 'EOF'
# Experiment 4 Results

**Date**: $(date)
**Host**: $(hostname)
**MATLAB**: $(matlab -batch "disp(version); exit(0);" 2>&1 | head -1)

## Gates
$(cut -d, -f1,4,5 results/exp4_*/verdict.csv | tail -n +2)

## Key Metrics
- RK4 Order: $(awk -F, 'NR==2{print $2}' results/exp4_*/temporal_orders.csv)
- Boundary R²: $(awk -F, 'NR==2{print $3}' results/exp4_*/boundary_scaling.csv)
- Long-time L2: $(tail -1 results/exp4_*/long_time.csv | cut -d, -f6)

## Files
$(ls -lh results/exp4_*/*.csv | wc -l) CSV files generated
$(du -sh results/exp4_*/)

EOF
cat results/REPORT.md
```

---

### upload-to-archive
**Description**: Upload to remote archive server

```bash
ARCHIVE_SERVER=archive.example.com
ARCHIVE_PATH=/mnt/nemt/exp4_results

# Create dated tarball
tar -czf exp4_$(date +%Y%m%d_%H%M%S).tar.gz results/exp4_*/

# Upload
scp exp4_*.tar.gz $ARCHIVE_SERVER:$ARCHIVE_PATH/

# Verify
ssh $ARCHIVE_SERVER "ls -lh $ARCHIVE_PATH/exp4_*.tar.gz | tail -1"
```

---

## Troubleshooting Tasks

### diagnose-failure
**Description**: Investigate failed run

```bash
# Check MATLAB log
cat results/exp4_*/matlab.log | grep -A 5 -i error

# Check for NaN/Inf
grep -i nan results/exp4_*/*.csv || echo "No NaN found"

# Verify file completeness
REQUIRED="spatial_convergence temporal_convergence temporal_orders reliability_scan boundary_scaling long_time verdict"
for f in $REQUIRED; do
    [ -f results/exp4_*/$f.csv ] && echo "✓ $f" || echo "✗ $f MISSING"
done

# Check gate logic
awk -F, 'NR>1{print $1, $2, $3, $4}' results/exp4_*/verdict.csv | \
  column -t
```

---

### reset-environment
**Description**: Clean environment for fresh run

```bash
# Remove old results
rm -rf results/exp4_*

# Verify core files
ls core/*.m | wc -l  # Should be 25+

# Check MATLAB path
matlab -batch "addpath('core'); which write_verdict; exit(0);"

# Test import
matlab -batch "addpath('core'); help run_exp4_clean; exit(0);"
```

---

### monitor-progress
**Description**: Monitor running experiment

```bash
# Watch completion file (blocks until complete)
watch -n 5 'ls -lh results/exp4_*/RUN_COMPLETE.txt 2>/dev/null || echo "Still running..."'

# Monitor log in real-time
tail -f results/exp4_*/matlab.log

# Check process
ps aux | grep matlab | grep -v grep
```

---

## Notes

- All paths assume working directory is `NEMT_CODE_REVIEW_20261017`
- Adjust `/path/to/` placeholders to your actual paths
- `make` targets are conceptual (no actual Makefile provided)
- For Windows, replace `bash` commands with PowerShell equivalents

---

**Last Updated**: 2026-10-17  
**Version**: 1.0
