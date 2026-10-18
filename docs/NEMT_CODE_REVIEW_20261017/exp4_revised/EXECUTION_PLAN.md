# Exp4 Clean Execution Plan

## Pre-execution Checklist

- [ ] MATLAB R2020b+ installed
- [ ] `core/` folder contains all .m files from review package
- [ ] Output directory writable and has ≥500MB free space
- [ ] Network connection stable (for potential data logging)

## Three Execution Modes

### Mode A: Full Local (With Figures)

**Estimate**: 25 min | CPU: 4+ cores | RAM: 4GB+

```matlab
cd('/path/to/NEMT_CODE_REVIEW_20261017');
addpath('core');
run_exp4_clean('output', './results/exp4_full', 'makeFigures', true);
```

**Output**: CSV tables + PNG/PDF/SVG plots + verdict

### Mode B: Data-Only Remote (No Figures)

**Estimate**: 8-12 min | CPU: 2+ cores | RAM: 2GB+

```bash
cd /path/to/exp4_revised
./run_exp4_clean_remote.sh /mnt/results/exp4_data false
```

**Output**: CSV tables + verdict + log

### Mode C: Quick Validation (Coarse Grid)

**For testing before full run:**

Edit `run_exp4_clean.m` line 26-28:
```matlab
Ns=[256 384];        % Coarse: only 2 grid sizes
Tspace=0.1; dtSpace=1e-4;  % Shorter time
dts=[0.004 0.002];   % Fewer dt values
```

**Estimate**: 2-3 min

## Expected Output Structure

```
output/
├── RUN_COMPLETE.txt          # Completion marker (PASS/FAIL)
├── matlab.log                # Execution log (if remote)
├── spatial_convergence.csv   # Part A
├── temporal_convergence.csv  # Part B
├── temporal_orders.csv       # Part B summary
├── reliability_scan.csv      # Part C detail
├── reliability_boundaries.csv # Part C summary
├── boundary_scaling.csv      # Part C fit
├── long_time.csv             # Part D
├── verdict.csv               # Part E (gates)
├── r4_spatial.png/pdf/svg    # Figure A (if makeFigures=true)
├── r4_temporal.png/pdf/svg   # Figure B
├── r4_boundary.png/pdf/svg   # Figure C
└── r4_long_time.png/pdf/svg  # Figure D
```

## Success Criteria

### All Gates PASS

```
R4.1_grid_resolution:   PASS
R4.2_spatial_monotone:  PASS
R4.3_rk4_order:         PASS
R4.4_boundary_scaling:  PASS
R4.5_equal_time_long_run: PASS
```

### Key Metrics

| Metric | Target | Tolerance |
|--------|--------|-----------|
| Coarsest grid pts/FWHM | ≥12 | ±0 |
| Spatial error ratio | <1 (monotone) | ±0 |
| RK4 temporal order | 4.0 | ±0.5 |
| Boundary R² | ≥0.90 | ±0.05 |
| Boundary slope | 2.0 | ±0.35 |
| Long-time L2 | <0.02 | ±0.01 |
| Long-time mass | <1e-10 | ±1e-11 |

## Failure Troubleshooting

### "undefined function" errors

1. Verify `core/` path in MATLAB path
2. List required files: `ls core/*.m | wc -l` (should be 25+)
3. Check for file permissions: `chmod +r core/*.m`

### "NaN" in results tables

1. Check for numerical instability
2. Verify α, β parameters in line 20
3. Verify L=20 domain is correct

### Verdict shows only FAIL

1. Check MATLAB console for exceptions
2. Verify output directory is writable
3. Run Mode C (quick validation) first

### Timeout after 30 min

1. Reduce Ns to [256, 384] in line 26
2. Set makeFigures=false
3. Verify MATLAB has ≥4GB RAM available

## Post-execution Steps

1. **Verify completion**:
   ```bash
   tail -5 output/RUN_COMPLETE.txt
   ```

2. **Check verdict**:
   ```bash
   cut -d, -f1,4,5 output/verdict.csv | tail -n +2
   ```

3. **Archive results**:
   ```bash
   tar -czf exp4_clean_$(date +%Y%m%d).tar.gz output/
   ```

4. **Upload to analysis**:
   ```bash
   scp -r output/ analysis_server:/mnt/exp4_results/
   ```

## Performance Optimization

### For Faster Execution (sacrifice resolution)

```matlab
Ns=[256 384];          % 2 instead of 4
Tspace=0.1;           % 0.1 instead of 0.2
Ttime=0.3;            % 0.3 instead of 0.5
mus=logspace(log10(0.05),log10(2),15);  % 15 instead of 25
Tb=0.1;                % 0.1 instead of 0.2
Tlong=2;               % 2 instead of 5
```

**Estimate**: 3-5 min instead of 12 min

### For Maximum Accuracy (slower)

```matlab
Ns=[256 384 512 768 1024];  % Add 1024
Tspace=0.3;
Ttime=1.0;
mus=logspace(log10(0.001),log10(10),35);  % 35 points
```

**Estimate**: 40-50 min instead of 12 min

## Data Analysis After Completion

### Parse verdict for CI/CD

```bash
grep FAIL output/verdict.csv | wc -l  # Should be 0
```

### Extract temporal order with uncertainty

```bash
awk -F, 'NR==2 {print "RK4 order: " $2 " (R²=" $3 ")"}' output/temporal_orders.csv
```

### Plot boundary in Python

```python
import pandas as pd, matplotlib.pyplot as plt
df = pd.read_csv('boundary_scaling.csv')
for _, row in df.iterrows():
    if row['r2'] >= 0.90:
        print(f"{row['solver']}: slope={row['slope']:.2f} (R²={row['r2']:.3f})")
```

## Cleanup

Remove after archiving:
```bash
rm -rf output/*.png output/*.pdf output/*.svg  # Keep CSV only
du -sh output/  # Verify size
```

---

**Last Updated**: 2026-10-17  
**Version**: 1.0  
**Status**: Ready for Cloud Deployment
