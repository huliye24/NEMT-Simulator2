# Experiment 4R — verified NLS discretisation and solver credibility

The original experiment 4 is invalidated.  Its domain/grid combination sampled the
soliton with fewer than five points across its amplitude FWHM, mixed unequal physical
end times, and tested a power law using only R-squared.

## Equation and reference solution

We solve

`i psi_t + alpha psi_xx + beta |psi|^2 psi = 0`, with `alpha=0.1`, `beta=1`,

using the exact bright soliton

`psi(x,t)=sech(sqrt(5)x) exp(i t/2)`.

The periodic domain is `[-10,10)`.  The coarsest grid, `N=256`, has about 15
intervals across the amplitude FWHM (1.178), so every reported grid resolves the
profile.

## Parts

1. **Spatial convergence** — Strang SSFM, fixed `T=0.2`, `dt=2e-5`,
   `N=[256 384 512 768]`.  Report phase-aligned relative L2 and Linf error.
2. **Temporal convergence** — fixed `N=1024`, `T=0.5`,
   `dt=[0.008 0.004 0.002 0.001]`, Euler/RK4/Strang.  Regress log(error) on
   log(dt); no unstable/non-finite point enters a fit.
3. **Reliability boundary** — fixed physical horizon `T=0.2`, not a fixed step
   count.  Scan nondimensional step `mu=alpha*dt/dx^2` over 25 log-spaced values.
   A point is reliable only if it is finite, max amplitude is below 10 times the
   initial maximum, mass drift is <=1e-3, and exact-solution relative L2 error is
   <=5%.  Fit `dt_r ~ dx^p` only when at least four uncensored boundaries exist.
4. **Long-time soliton test** — Strang SSFM to the same physical time `T=5` for
   every N, at `mu=0.2`.  Compare with the analytic solution.

## Gates

- R4.1: coarsest grid has at least 12 intervals per amplitude FWHM.
- R4.2: spatial convergence error decreases monotonically.
- R4.3: RK4 temporal order is in `[3.5,4.5]` when at least three valid points exist.
- R4.4: boundary scaling has `R^2>=0.90` and slope in `[1.65,2.35]`.
- R4.5: long-time Strang maximum phase-aligned L2 error is below 2% and mass drift
  below `1e-10`, at a common physical end time.

No downstream experiment may use experiment 4R unless all mandatory gates pass.
