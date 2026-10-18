function spec = exp4_spec(quick)
% exp4_spec  Frozen experiment-four grids and thresholds.
%
% Quick mode only shrinks the N/dt grids. Steps (200), thresholds, solver
% names, initial-value recipe and all CSV columns are identical.

    if nargin < 1, quick = false; end
    spec.quick = logical(quick);
    spec.Nlist = [32 64 128 256 512];
    spec.dtScan = logspace(-5,0,51);
    spec.steps = 200;
    spec.longSteps = [200 1000 5000];
    spec.solvers = {'euler','rk4','ssfm'};
    spec.inits = {'P1','P2'};
    spec.alpha = 0.1;
    spec.beta = 1.0;
    spec.eta = 0.0;
    spec.domainLength = 128;
    spec.bisectionIterations = 8;

    % Thresholds are frozen verbatim from 实验设计与探究.md.
    spec.thresh.C4_1_minN = 4;
    spec.thresh.C4_2_r2 = 0.80;
    spec.thresh.C4_3_mass = 1e-10;
    spec.thresh.C4_4_minN = 4;
    spec.thresh.C4_5_amp = 0.02;
    spec.thresh.C4_5_mass = 1e-10;
    spec.thresh.massPrecision = 1e-3;
    spec.thresh.energyPrecision = 1e-2;
    spec.thresh.ampPrecision = 0.01;
    spec.thresh.phasePrecision = 0.02;
    spec.thresh.ampDivergence = 10;

    spec.hdr.scan = {'N','dx','dt','solver','init','steps','diverged', ...
        'nonfinite','max_amp_ratio','mass_rel','energy_rel', ...
        'amp_rel_err','phase_l2','acc_mass','acc_energy','acc_amp', ...
        'acc_phase','acc_all'};
    spec.hdr.boundaries = {'N','dx','solver','init','dt_c', ...
        'dt_c_censored','dt_c_reason','dt_a','dt_a_censored', ...
        'n_stable','n_diverged','steps'};
    spec.hdr.longTime = {'N','dx','dt','steps','solver','init', ...
        'diverged','mass_rel','energy_rel','amp_rel_err','phase_l2', ...
        'phase_drift'};
    spec.hdr.scaling = {'solver','init','n_points','slope','intercept', ...
        'r2','p_value','ci95_low','ci95_high','theory_exponent'};
    spec.hdr.bisection = {'N','init','coarse_stable','coarse_diverged', ...
        'bisect_dtc','iterations'};

    if quick
        spec.Nlist = [64 128 256];
        spec.dtScan = logspace(-5,0,12);
    end
end
