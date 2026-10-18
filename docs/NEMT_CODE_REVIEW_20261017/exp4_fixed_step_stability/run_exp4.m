function run_exp4(varargin)
% run_exp4  Experiment 4 - fixed-step stability boundary and long-time error.
%
%   run_exp4('output', outDir)
%   run_exp4('output', outDir, 'quick', true, 'makeFigures', true)
%
% The frozen design is exp4_fixed_step_stability/实验设计与探究.md. Quick mode
% only shrinks the N and dt grids; the 200 fixed steps, thresholds, solver
% definitions, initial data and CSV schemas are unchanged.
%
% Outputs (all under outDir):
%   exp4_scan.csv, exp4_boundaries.csv, exp4_long_time.csv,
%   exp4_scaling.csv, exp4_verdict.csv, exp4_config.json,
%   exp4_safety.json, exp4_bisection.csv, exp4_soliton_snapshots.csv,
%   figures fig14_*.{png,pdf,svg,fig}

    opts.output = fullfile('output','exp4');
    opts.quick = false;
    opts.makeFigures = true;
    opts.codeHash = '';
    for i = 1:2:numel(varargin)
        opts.(varargin{i}) = varargin{i+1};
    end

    here = fileparts(mfilename('fullpath'));
    root = fileparts(here);
    addpath(fullfile(root,'core'));
    addpath(here);
    if ~exist(opts.output,'dir'), mkdir(opts.output); end

    spec = exp4_spec(opts.quick);
    t0 = tic;
    fprintf('\n========================================================\n');
    fprintf(' EXP4  fixed-step stability boundary and long-time error\n');
    fprintf('========================================================\n');
    fprintf(' N=%s  |dt|=%d  steps=%d  solvers=%s  inits=%s\n', ...
        mat2str(spec.Nlist), numel(spec.dtScan), spec.steps, ...
        strjoin(spec.solvers,','), strjoin(spec.inits,','));
    if opts.quick
        fprintf(' QUICK GRID - smoke test only, not a scientific result\n');
    end

    p = NEMTParams();
    p.alpha = spec.alpha;
    p.beta = spec.beta;
    p.eta = spec.eta;
    p.steps = spec.steps;

    % ---------------------------------------------------------- Part A/B
    fprintf('[A] fixed-step 200-step scan\n');
    scan = [];
    for s = 1:numel(spec.solvers)
        for iN = 1:numel(spec.Nlist)
            N = spec.Nlist(iN);
            pL = p;
            pL.dx = spec.domainLength / N;
            inits = makeInits(N,pL);
            for ii = 1:numel(spec.inits)
                psi0 = inits.(spec.inits{ii});
                for idt = 1:numel(spec.dtScan)
                    r = scanPoint(psi0,pL,spec.dtScan(idt), ...
                                  spec.solvers{s},spec.inits{ii},spec.thresh);
                    scan(end+1,:) = [N, pL.dx, spec.dtScan(idt), s, ii, ...
                        spec.steps, r.diverged, r.nonfinite, r.maxAmpRatio, ...
                        r.massRel, r.energyRel, r.ampRel, r.phaseL2, ...
                        r.accMass, r.accEnergy, r.accAmp, r.accPhase, ...
                        r.accAll]; %#ok<AGROW>
                end
            end
        end
    end
    writeScan(fullfile(opts.output,'exp4_scan.csv'),scan,spec);

    fprintf('[B] boundaries dt_c and precision boundary dt_a\n');
    B = buildBoundaries(scan,spec);
    writeBoundaries(fullfile(opts.output,'exp4_boundaries.csv'),B,spec);

    % ---------------------------------------------------------- Part C
    fprintf('[C] common safe step and long-time runs\n');
    [commonDt, safeInfo] = commonSafeSteps(scan,spec);
    longRows = [];
    for iN = 1:numel(spec.Nlist)
        N = spec.Nlist(iN);
        dtSafe = commonDt(iN);
        if ~isfinite(dtSafe), continue; end
        pL = p;
        pL.dx = spec.domainLength / N;
        pL.dt = dtSafe;
        inits = makeInits(N,pL);
        for ii = 1:numel(spec.inits)
            psi0 = inits.(spec.inits{ii});
            for s = 1:numel(spec.solvers)
                for st = spec.longSteps
                    r = scanPoint(psi0,pL,dtSafe,spec.solvers{s}, ...
                                  spec.inits{ii},spec.thresh,st);
                    longRows(end+1,:) = [N,pL.dx,dtSafe,st,s,ii, ...
                        r.diverged,r.massRel,r.energyRel,r.ampRel, ...
                        r.phaseL2,r.phaseDrift]; %#ok<AGROW>
                end
            end
        end
    end
    writeLongTime(fullfile(opts.output,'exp4_long_time.csv'),longRows,spec);

    % ---------------------------------------------------------- Part D
    fprintf('[D] scaling regressions\n');
    S = buildScaling(B,spec);
    writeScaling(fullfile(opts.output,'exp4_scaling.csv'),S);

    % ---------------------------------------------------------- Part E
    fprintf('[E] exploratory Euler bisection\n');
    Bi = bisectEuler(B,spec,p);
    writeBisection(fullfile(opts.output,'exp4_bisection.csv'),Bi,spec);

    % ---------------------------------------------------------- snapshots
    snapRows = makeSnapshots(p,spec,commonDt);
    writeSnapshots(fullfile(opts.output,'exp4_soliton_snapshots.csv'),snapRows,spec);

    % ---------------------------------------------------------- verdict
    V = buildVerdict(B,S,scan,longRows,commonDt,safeInfo,spec);
    write_verdict(fullfile(opts.output,'exp4_verdict.csv'),V);

    safety = buildSafety(scan,longRows,commonDt,safeInfo,spec,V);
    write_json_file(fullfile(opts.output,'exp4_safety.json'),safety);

    if opts.makeFigures
        makeFigures(opts.output,spec);
    end

    cfg = struct();
    cfg.experiment = 'exp4';
    cfg.createdAtUtc = utc_now();
    cfg.quick = spec.quick;
    cfg.matlabVersion = version;
    cfg.codeHash = opts.codeHash;
    cfg.spec = rmfield(spec,'hdr');
    cfg.csvHeaders = spec.hdr;
    cfg.params = struct('alpha',p.alpha,'beta',p.beta,'eta',p.eta, ...
        'psi_window',p.psi_window,'psi_n_fft',p.psi_n_fft, ...
        'momentum_window',p.momentum_window,'seed',p.seed);
    cfg.initialValues = struct( ...
        'P1','A*sech(A*sqrt(beta/(2*alpha))*x), A=1, x=(0:N-1-N/2)*dx', ...
        'P2',sprintf(['causal logprice_z profile from gen_synthetic_price(1024,seed=%d), ' ...
                      'bar=%d, window=%d, then nls_pad to N'], ...
                     p.seed,p.psi_window+300,p.psi_window), ...
        'domainLength',spec.domainLength);
    cfg.definitions = struct( ...
        'divergence','nonfinite OR max|psi|>10*max|psi0| OR relative mass error>1', ...
        'dt_c','last non-diverged dt before first divergence; right-censored if none', ...
        'dt_a','largest dt satisfying all precision limits (P1: mass, energy, modulus, phase-removed L2; P2: mass, energy)', ...
        'common_safe_dt','largest scan dt safe and accurate for both inits and all three solvers at 200 steps', ...
        'amp_rel_err','max abs(|psi|-|psi0|)/max|psi0|', ...
        'phase_l2','||e^{-i phi}psi-psi0||/||psi0|| with phi=angle(<psi0,psi>)');
    cfg.outputDirectory = opts.output;
    write_json_file(fullfile(opts.output,'exp4_config.json'),cfg);

    fprintf('\n EXP4 done in %.1f s -> %s\n', toc(t0), opts.output);
    dispVerdict(V);
end

% ============================================================ scan
function r = scanPoint(psi0,p,dt,solver,initName,thresh,steps)
    if nargin < 7 || isempty(steps), steps = p.steps; end
    pL = p;
    pL.dt = dt;
    pL.steps = steps;
    amp0 = max(abs(psi0));
    c0 = nls_conservation(psi0,pL);

    psi = evolveDirect(psi0,pL,solver);

    nonfinite = any(~isfinite(psi(:))) || any(~isfinite(psi0(:)));
    if nonfinite
        mx = Inf;
        c1 = struct('mass',NaN,'energy',NaN);
    else
        mx = max(abs(psi));
        c1 = nls_conservation(psi,pL);
    end

    massRel = abs(c1.mass - c0.mass) / max(abs(c0.mass),1e-300);
    energyRel = abs(c1.energy - c0.energy) / max(abs(c0.energy),1e-300);
    ampRel = max(abs(abs(psi) - abs(psi0))) / max(amp0,1e-300);
    phaseDrift = NaN;
    phaseL2 = NaN;
    if ~nonfinite
        ov = sum(conj(psi0).*psi);
        if abs(ov) > 0
            phaseDrift = angle(ov);
            d = psi*exp(-1i*phaseDrift) - psi0;
            phaseL2 = norm(d)/max(norm(psi0),1e-300);
        end
    end

    if ~isfinite(mx)
        maxAmpRatio = Inf;
    else
        maxAmpRatio = mx/max(amp0,1e-300);
    end
    diverged = nonfinite || ~isfinite(maxAmpRatio) || ...
               maxAmpRatio > thresh.ampDivergence || ...
               (isfinite(massRel) && massRel > 1);
    diverged = logical(diverged);

    accMass = isfinite(massRel) && massRel <= thresh.massPrecision;
    accEnergy = isfinite(energyRel) && energyRel <= thresh.energyPrecision;
    accAmp = isfinite(ampRel) && ampRel <= thresh.ampPrecision;
    accPhase = isfinite(phaseL2) && phaseL2 <= thresh.phasePrecision;
    if strcmpi(initName,'P2')
        accAll = ~diverged && accMass && accEnergy;
    else
        accAll = ~diverged && accMass && accEnergy && accAmp && accPhase;
    end

    if nonfinite
        massRel = NaN; energyRel = NaN; ampRel = NaN;
    end
    r = struct('diverged',double(diverged),'nonfinite',double(nonfinite), ...
        'maxAmpRatio',maxAmpRatio,'massRel',massRel, ...
        'energyRel',energyRel,'ampRel',ampRel,'phaseL2',phaseL2, ...
        'phaseDrift',phaseDrift,'accMass',double(accMass), ...
        'accEnergy',double(accEnergy),'accAmp',double(accAmp), ...
        'accPhase',double(accPhase),'accAll',double(accAll));
end

function psi = evolveDirect(psi0,p,solver)
    switch lower(solver)
        case 'ssfm',  psi = nls_ssfm(psi0,p);
        case 'euler', psi = nls_euler(psi0,p);
        case 'rk4',   psi = nls_rk4(psi0,p);
        otherwise
            error('run_exp4: unknown solver %s',solver);
    end
end

function inits = makeInits(N,p)
    [psi1,~] = soliton_profile(N,p.dx,p.alpha,p.beta,1.0);
    [close,~] = gen_synthetic_price(1024,struct('seed',p.seed));
    [re,im] = construct_psi(close,p,'logprice_z');
    i0 = p.psi_window + 300;
    sre = re(i0-p.psi_window+1:i0);
    sim = im(i0-p.psi_window+1:i0);
    psi2 = nls_pad(sre,sim,N);
    inits = struct('P1',psi1,'P2',psi2);
end

% ============================================================ boundaries
function B = buildBoundaries(scan,spec)
    B = [];
    for s = 1:numel(spec.solvers)
        for ii = 1:numel(spec.inits)
            for N = spec.Nlist
                rows = scan(scan(:,1)==N & scan(:,4)==s & scan(:,5)==ii,:);
                [~,ord] = sort(rows(:,3));
                rows = rows(ord,:);
                dv = logical(rows(:,7));
                firstDiv = find(dv,1,'first');
                if isempty(firstDiv)
                    dtc = NaN; cens = 1; reason = 'all_stable_right_censored';
                elseif firstDiv == 1
                    dtc = NaN; cens = 0; reason = 'first_scan_point_diverged';
                else
                    dtc = rows(firstDiv-1,3); cens = 0;
                    reason = 'last_stable_before_first_divergence';
                end
                acc = logical(rows(:,18)) & ~dv;
                if any(acc)
                    idx = find(acc,1,'last');
                    dta = rows(idx,3);
                    % Right-censored if the last scan point itself passes.
                    taCens = double(idx == size(rows,1) && ~dv(end));
                else
                    dta = NaN; taCens = 0;
                end
                B(end+1,:) = [N,rows(1,2),s,ii,dtc,cens,0,dta,taCens, ...
                    sum(~dv),sum(dv),spec.steps]; %#ok<AGROW>
                B(end,7) = 0; % numeric reason code replaced on output
                B(end,7) = reasonCode(reason);
            end
        end
    end
end

function c = reasonCode(reason)
    switch reason
        case 'all_stable_right_censored', c = 1;
        case 'first_scan_point_diverged', c = 2;
        otherwise, c = 0;
    end
end

function reason = reasonText(c)
    switch c
        case 1, reason = 'all_stable_right_censored';
        case 2, reason = 'first_scan_point_diverged';
        otherwise, reason = 'last_stable_before_first_divergence';
    end
end

% ============================================================ safe step
function [commonDt, info] = commonSafeSteps(scan,spec)
    commonDt = nan(numel(spec.Nlist),1);
    info.commonDt = commonDt;
    info.ssfmDt = nan(numel(spec.Nlist),1);
    for iN = 1:numel(spec.Nlist)
        N = spec.Nlist(iN);
        ds = unique(scan(scan(:,1)==N,3));
        for k = numel(ds):-1:1
            rows = scan(scan(:,1)==N & scan(:,3)==ds(k),:);
            if size(rows,1) < numel(spec.solvers)*numel(spec.inits)
                continue;
            end
            if all(rows(:,18)==1) && all(rows(:,7)==0)
                commonDt(iN) = ds(k);
                break;
            end
        end
        for k = numel(ds):-1:1
            rows = scan(scan(:,1)==N & scan(:,3)==ds(k) & scan(:,4)==3,:);
            if size(rows,1) ~= numel(spec.inits), continue; end
            if all(rows(:,18)==1) && all(rows(:,7)==0)
                info.ssfmDt(iN) = ds(k);
                break;
            end
        end
    end
    info.commonDt = commonDt;
    info.N = spec.Nlist;
end

% ============================================================ scaling
function S = buildScaling(B,spec)
    S = cell(0,10);
    for s = 1:numel(spec.solvers)
        for ii = 1:numel(spec.inits)
            rows = B(B(:,3)==s & B(:,4)==ii & isfinite(B(:,5)),:);
            n = size(rows,1);
            if n < 3
                S(end+1,:) = {spec.solvers{s},spec.inits{ii},n,NaN,NaN, ...
                    NaN,NaN,NaN,NaN,2}; %#ok<AGROW>
                continue;
            end
            x = log(rows(:,2));
            y = log(rows(:,5));
            X = [ones(n,1),x];
            b = X\y;
            yh = X*b;
            r2 = r2_linear(y,yh);
            resid = y-yh;
            sse = sum(resid.^2);
            sx = sum((x-mean(x)).^2);
            df = n-2;
            if df > 0 && sx > 0
                se = sqrt((sse/df)/sx);
                tstat = b(2)/se;
                pval = t_two_sided_p(tstat,df);
                tcrit = t_quantile(0.975,df);
                lo = b(2)-tcrit*se;
                hi = b(2)+tcrit*se;
            else
                pval = NaN; lo = NaN; hi = NaN;
            end
            S(end+1,:) = {spec.solvers{s},spec.inits{ii},n,b(2),b(1), ...
                r2,pval,lo,hi,2}; %#ok<AGROW>
        end
    end
end

% ============================================================ bisection
function Bi = bisectEuler(B,spec,p)
    Bi = [];
    ii = find(strcmp(spec.inits,'P1'),1);
    for iN = 1:numel(spec.Nlist)
        N = spec.Nlist(iN);
        row = B(B(:,1)==N & B(:,3)==1 & B(:,4)==ii,:);
        if isempty(row), continue; end
        reason = reasonText(row(1,7));
        if ~strcmp(reason,'last_stable_before_first_divergence'), continue; end
        lo = row(1,5);
        rows = B(B(:,1)==N & B(:,3)==1 & B(:,4)==ii,:);
        ds = spec.dtScan;
        iLo = find(abs(ds-lo) < 1e-15,1);
        if isempty(iLo) || iLo >= numel(ds), continue; end
        hi = ds(iLo+1);
        pL = p; pL.dx = spec.domainLength/N;
        [psi1,~] = soliton_profile(N,pL.dx,pL.alpha,pL.beta,1.0);
        for it = 1:spec.bisectionIterations
            mid = sqrt(lo*hi);
            r = scanPoint(psi1,pL,mid,'euler','P1',spec.thresh);
            if r.diverged
                hi = mid;
            else
                lo = mid;
            end
        end
        Bi(end+1,:) = [N,ii,ds(iLo),ds(iLo+1),lo,spec.bisectionIterations]; %#ok<AGROW>
    end
end

% ============================================================ snapshots
function S = makeSnapshots(p,spec,commonDt)
    S = cell(0,6);
    N = 128;
    if ~any(spec.Nlist==N)
        [~,j] = min(abs(spec.Nlist-N));
        N = spec.Nlist(j);
    end
    iN = find(spec.Nlist==N,1);
    dt = commonDt(iN);
    if ~isfinite(dt), dt = min(spec.dtScan); end
    pL = p; pL.dx = spec.domainLength/N; pL.dt = dt;
    [psi0,x] = soliton_profile(N,pL.dx,pL.alpha,pL.beta,1.0);
    snapSteps = [0 100 200];
    for s = 1:numel(spec.solvers)
        psi = psi0;
        last = 0;
        for k = snapSteps
            if k > last
                pS = pL; pS.steps = k - last;
                psi = evolveDirect(psi,pS,spec.solvers{s});
                last = k;
            end
            for j = 1:N
                S(end+1,:) = {N,dt,spec.steps,k,spec.solvers{s},abs(psi(j))}; %#ok<AGROW>
            end
        end
    end
    % x values are deterministic and can be reconstructed; record them too.
    for j = 1:N
        S(end+1,:) = {N,dt,spec.steps,-1,'x',x(j)}; %#ok<AGROW>
    end
end

% ============================================================ verdict
function V = buildVerdict(B,S,scan,longRows,commonDt,safeInfo,spec)
    V = cell(0,5);
    iE = find(strcmp(spec.solvers,'euler'),1);
    iP1 = find(strcmp(spec.inits,'P1'),1);
    iS = find(strcmp(spec.solvers,'ssfm'),1);

    eBound = B(B(:,3)==iE & B(:,4)==iP1,:);
    nFiniteC = sum(isfinite(eBound(:,5)));
    c41 = nFiniteC >= spec.thresh.C4_1_minN;
    V(end+1,:) = {'C4.1_boundary_measurable',nFiniteC, ...
        spec.thresh.C4_1_minN,passFail(c41), ...
        sprintf('Euler/P1: %d/%d N have finite dt_c; every scan point used %d fixed steps (>=20)', ...
                nFiniteC,numel(spec.Nlist),spec.steps)};

    srow = S(strcmp(S(:,1),'euler') & strcmp(S(:,2),'P1'),:);
    if isempty(srow)
        r2v=NaN; sl=NaN; pv=NaN; lo=NaN; hi=NaN; nPts=0;
    else
        r2v=srow{1,6}; sl=srow{1,4}; pv=srow{1,7}; lo=srow{1,8}; hi=srow{1,9}; nPts=srow{1,3};
    end
    c42 = isfinite(r2v) && r2v >= spec.thresh.C4_2_r2 && nPts >= 3;
    if nPts < 3
        st42 = 'INCONCLUSIVE';
    else
        st42 = passFail(c42);
    end
    V(end+1,:) = {'C4.2_scaling_powerlaw',r2v,spec.thresh.C4_2_r2,st42, ...
        sprintf('Euler/P1 log(dt_c)~log(dx): slope=%.4g, p=%.4g, 95%% CI=[%.4g,%.4g], n=%d', ...
                sl,pv,lo,hi,nPts)};

    ss = scan(scan(:,4)==iS & isfinite(scan(:,10)),:);
    if isempty(ss), massMax=NaN; else, massMax=max(ss(:,10)); end
    c43 = isfinite(massMax) && massMax < spec.thresh.C4_3_mass;
    V(end+1,:) = {'C4.3_ssfm_mass_conservation',massMax, ...
        spec.thresh.C4_3_mass,passFail(c43), ...
        sprintf('max relative mass error over %d finite SSFM scan points (both inits)',size(ss,1))};

    nAccBeforeDiv = 0;
    for iN = 1:numel(spec.Nlist)
        row = B(B(:,1)==spec.Nlist(iN) & B(:,3)==iE & B(:,4)==iP1,:);
        if isempty(row), continue; end
        if isfinite(row(1,5)) && isfinite(row(1,8)) && row(1,8) < row(1,5)
            nAccBeforeDiv = nAccBeforeDiv + 1;
        end
    end
    c44 = nAccBeforeDiv >= spec.thresh.C4_4_minN;
    V(end+1,:) = {'C4.4_precision_before_divergence',nAccBeforeDiv, ...
        spec.thresh.C4_4_minN,passFail(c44), ...
        sprintf('Euler/P1: %d/%d N have dt_a < dt_c',nAccBeforeDiv,numel(spec.Nlist))};

    lr = longRows(longRows(:,5)==iS & longRows(:,6)==iP1 & longRows(:,4)==5000,:);
    if isempty(lr)
        ampMax=NaN; massMaxL=NaN; nLong=0;
    else
        ampMax=max(lr(:,10)); massMaxL=max(lr(:,8)); nLong=size(lr,1);
    end
    c45 = nLong == numel(spec.Nlist) && isfinite(ampMax) && ...
          ampMax < spec.thresh.C4_5_amp && massMaxL < spec.thresh.C4_5_mass;
    if isempty(lr)
        st45='INCONCLUSIVE';
    else
        st45=passFail(c45);
    end
    V(end+1,:) = {'C4.5_long_time_trust',ampMax,spec.thresh.C4_5_amp,st45, ...
        sprintf(['SSFM/P1 at 5000 steps, common safe dt: max modulus error=%.4g, ' ...
                 'max mass error=%.4g (<%.0e); N blocks=%d/%d; common dt=%s'], ...
                ampMax,massMaxL,spec.thresh.C4_5_mass,nLong,numel(spec.Nlist), ...
                mat2str(commonDt',4))};
end

function s = passFail(tf)
    if tf, s='PASS'; else, s='FAIL'; end
end

% ============================================================ safety
function safety = buildSafety(scan,longRows,commonDt,info,spec,V)
    safety = struct();
    safety.experiment = 'exp4';
    safety.createdAtUtc = utc_now();
    safety.N = spec.Nlist;
    safety.dx = spec.domainLength./spec.Nlist;
    safety.steps200 = spec.steps;
    safety.common_safe_dt = info.commonDt';
    safety.ssfm_safe_dt = info.ssfmDt';
    safety.common_safe_source = ['largest 200-step scan dt passing stability and ' ...
        'precision for both P1/P2 and all three solvers'];
    safety.ssfm_safe_source = ['largest 200-step scan dt passing stability and ' ...
        'precision for SSFM on both P1/P2'];

    iS = find(strcmp(spec.solvers,'ssfm'),1);
    iP1 = find(strcmp(spec.inits,'P1'),1);
    needN = [64 128 256];
    needDt = nan(1,3);
    for k=1:3
        j = find(spec.Nlist==needN(k),1);
        if ~isempty(j), needDt(k) = info.ssfmDt(j); end
    end
    safety.exp5_N = needN;
    safety.exp5_dt = needDt;
    safety.exp5_steps = 20;
    safety.exp5_solver = 'ssfm';
    safety.exp5_note = ['steps=20 is a strict subset of the 200-step and 5000-step ' ...
        'runs used to approve this SSFM step; dt is the largest SSFM-accurate ' ...
        '200-step value for that N.'];
    safety.C4_3_pass = strcmp(V{strcmp(V(:,1),'C4.3_ssfm_mass_conservation'),4},'PASS');
    safety.C4_5_pass = strcmp(V{strcmp(V(:,1),'C4.5_long_time_trust'),4},'PASS');
    safety.C4_3_observed = V{strcmp(V(:,1),'C4.3_ssfm_mass_conservation'),2};
    safety.C4_5_observed = V{strcmp(V(:,1),'C4.5_long_time_trust'),2};
    safety.long_time_rows = size(longRows,1);
    safety.note = 'run_next_experiments enforces C4.3 and C4.5 before exp5.';
end

% ============================================================ CSV writers
function writeScan(path,A,spec)
    n = size(A,1);
    rows = cell(n,size(A,2));
    for r=1:n
        rows{r,1}=A(r,1); rows{r,2}=A(r,2); rows{r,3}=A(r,3);
        rows{r,4}=spec.solvers{A(r,4)}; rows{r,5}=spec.inits{A(r,5)};
        for c=6:18
            rows{r,c}=A(r,c);
        end
    end
    write_csv_table(path,spec.hdr.scan,rows);
end

function writeBoundaries(path,B,spec)
    n=size(B,1); rows=cell(n,size(B,2));
    for r=1:n
        rows{r,1}=B(r,1); rows{r,2}=B(r,2);
        rows{r,3}=spec.solvers{B(r,3)}; rows{r,4}=spec.inits{B(r,4)};
        rows{r,5}=B(r,5); rows{r,6}=B(r,6);
        rows{r,7}=reasonText(B(r,7));
        rows{r,8}=B(r,8); rows{r,9}=B(r,9);
        rows{r,10}=B(r,10); rows{r,11}=B(r,11); rows{r,12}=B(r,12);
    end
    write_csv_table(path,spec.hdr.boundaries,rows);
end

function writeLongTime(path,A,spec)
    n=size(A,1); rows=cell(n,size(A,2));
    for r=1:n
        rows{r,1}=A(r,1); rows{r,2}=A(r,2); rows{r,3}=A(r,3);
        rows{r,4}=A(r,4); rows{r,5}=spec.solvers{A(r,5)};
        rows{r,6}=spec.inits{A(r,6)};
        for c=7:12, rows{r,c}=A(r,c); end
    end
    write_csv_table(path,spec.hdr.longTime,rows);
end

function writeScaling(path,S)
    write_csv_table(path, ...
        {'solver','init','n_points','slope','intercept','r2','p_value', ...
         'ci95_low','ci95_high','theory_exponent'},S);
end

function writeBisection(path,Bi,spec)
    n=size(Bi,1);
    if n==0
        write_csv_table(path,spec.hdr.bisection,cell(0,size(Bi,2)));
        return;
    end
    rows=cell(n,size(Bi,2));
    for r=1:n
        rows{r,1}=Bi(r,1); rows{r,2}=spec.inits{Bi(r,2)};
        for c=3:6, rows{r,c}=Bi(r,c); end
    end
    write_csv_table(path,spec.hdr.bisection,rows);
end

function writeSnapshots(path,S,spec)
    n=size(S,1); rows=cell(n,size(S,2));
    for r=1:n
        rows{r,1}=S{r,1}; rows{r,2}=S{r,2}; rows{r,3}=S{r,3};
        rows{r,4}=S{r,4}; rows{r,5}=S{r,5}; rows{r,6}=S{r,6};
    end
    write_csv_table(path,{'N','dt','steps_scan','snapshot_step','series','value'},rows);
end

% ============================================================ figures
function makeFigures(out,spec)
    figs = {@figStability,@figScaling,@figLong,@figSoliton};
    args = {{out,spec},{out,spec},{out,spec},{out,spec}};
    for k=1:numel(figs)
        try
            figs{k}(args{k}{:});
        catch ME
            fprintf('  exp4 fig%d failed: %s\n',k,ME.message);
        end
    end
end

function figStability(out,spec)
    T = readtable(fullfile(out,'exp4_scan.csv'),'Delimiter',',', ...
        'TextType','string','VariableNamingRule','preserve');
    B = readtable(fullfile(out,'exp4_boundaries.csv'),'Delimiter',',', ...
        'TextType','string','VariableNamingRule','preserve');
    names = {'Euler','RK4','SSFM'};
    fig=figure('Visible','off','Color','w','Position',[80 80 1500 430]);
    for s=1:numel(spec.solvers)
        subplot(1,3,s); hold on; grid on;
        T1 = T(T.solver==spec.solvers{s} & T.init=="P1",:);
        ok = T1.diverged==0;
        scatter(T1.dt(ok),T1.N(ok),22,[0.25 0.55 0.85],'s','filled');
        scatter(T1.dt(~ok),T1.N(~ok),30,[0.85 0.30 0.20],'x','LineWidth',1.1);
        b = B(B.solver==spec.solvers{s} & B.init=="P1" & isfinite(B.dt_c),:);
        if ~isempty(b)
            semilogx(b.dt_c,b.N,'k-o','LineWidth',1.2,'MarkerFaceColor','k');
        end
        b2 = B(B.solver==spec.solvers{s} & B.init=="P1" & isfinite(B.dt_a),:);
        if ~isempty(b2)
            semilogx(b2.dt_a,b2.N,'k--s','LineWidth',1.0);
        end
        set(gca,'XScale','log','YScale','log');
        xlabel('dt'); ylabel('N');
        title(names{s});
        ylim([min(spec.Nlist)*0.8 max(spec.Nlist)*1.25]);
        xlim([min(spec.dtScan) max(spec.dtScan)]);
        if s==1
            legend({'stable','diverged','dt_c','dt_a'},'Location','best');
        end
    end
    sgtitle('Exp4: P1 fixed-200-step stability map');
    save_figure_set(fig,out,'fig14_stability_map'); close(fig);
end

function figScaling(out,spec)
    B = readtable(fullfile(out,'exp4_boundaries.csv'),'Delimiter',',', ...
        'TextType','string','VariableNamingRule','preserve');
    S = readtable(fullfile(out,'exp4_scaling.csv'),'Delimiter',',', ...
        'TextType','string','VariableNamingRule','preserve');
    fig=figure('Visible','off','Color','w','Position',[100 100 780 560]); hold on; grid on;
    cols = [0.12 0.35 0.65; 0.85 0.45 0.10; 0.15 0.55 0.30];
    marks = {'o','s','^'};
    for s=1:numel(spec.solvers)
        b = B(B.solver==spec.solvers{s} & B.init=="P1" & isfinite(B.dt_c),:);
        if isempty(b), continue; end
        loglog(b.dx,b.dt_c,marks{s},'Color',cols(s,:), ...
            'MarkerFaceColor',cols(s,:),'DisplayName',upper(spec.solvers{s}));
    end
    r = S(S.solver=="euler" & S.init=="P1",:);
    if ~isempty(r) && isfinite(r.slope(1))
        b = B(B.solver=="euler" & B.init=="P1" & isfinite(B.dt_c),:);
        xx=linspace(min(b.dx),max(b.dx),50);
        yy=exp(r.intercept(1))*xx.^r.slope(1);
        loglog(xx,yy,'k--','LineWidth',1.3);
        title(sprintf('Euler P1 slope=%.3f, R^2=%.3f, p=%.3g', ...
            r.slope(1),r.r2(1),r.p_value(1)));
    end
    xlabel('dx = 128/N'); ylabel('dt_c');
    legend('Location','best');
    save_figure_set(fig,out,'fig14_scaling'); close(fig);
end

function figLong(out,spec)
    T = readtable(fullfile(out,'exp4_long_time.csv'),'Delimiter',',', ...
        'TextType','string','VariableNamingRule','preserve');
    T = T(T.solver=="ssfm" & T.init=="P1",:);
    fig=figure('Visible','off','Color','w','Position',[80 80 1200 430]);
    subplot(1,2,1); hold on; grid on;
    ns = unique(T.N);
    cols=lines(numel(ns));
    for k=1:numel(ns)
        r=T(T.N==ns(k),:);
        [~,o]=sort(r.steps); r=r(o,:);
        semilogy(r.steps,max(r.mass_rel,1e-18),'-o','Color',cols(k,:), ...
            'DisplayName',sprintf('N=%d',ns(k)));
    end
    yline(1e-10,'k--','1e-10');
    set(gca,'XScale','log','YScale','log');
    xlabel('steps'); ylabel('relative mass error');
    legend('Location','best'); title('SSFM mass');
    subplot(1,2,2); hold on; grid on;
    for k=1:numel(ns)
        r=T(T.N==ns(k),:);
        [~,o]=sort(r.steps); r=r(o,:);
        semilogy(r.steps,max(r.amp_rel_err,1e-18),'-o','Color',cols(k,:));
    end
    yline(0.02,'k--','2%');
    set(gca,'XScale','log','YScale','log');
    xlabel('steps'); ylabel('max modulus error / max|\psi_0|');
    title('SSFM P1 modulus');
    sgtitle('Exp4: long-time check at per-N common safe dt');
    save_figure_set(fig,out,'fig14_long_time'); close(fig);
end

function figSoliton(out,spec)
    T = readtable(fullfile(out,'exp4_soliton_snapshots.csv'),'Delimiter',',', ...
        'TextType','string','VariableNamingRule','preserve');
    x = T(T.series=="x",:);
    x = x.value;
    if isempty(x), error('no x snapshot'); end
    N = T.N(1);
    fig=figure('Visible','off','Color','w','Position',[80 80 1000 600]); hold on; grid on;
    cols=[0.12 0.35 0.65;0.85 0.45 0.10;0.15 0.55 0.30];
    for s=1:numel(spec.solvers)
        r=T(T.series==spec.solvers{s} & T.snapshot_step==200,:);
        semilogy(x,r.value,'-','Color',cols(s,:),'LineWidth',1.6, ...
            'DisplayName',upper(spec.solvers{s}));
    end
    r0=T(T.series==spec.solvers{1} & T.snapshot_step==0,:);
    plot(x,r0.value,'k:','LineWidth',1.2,'DisplayName','initial');
    xlabel('x'); ylabel('|\psi|');
    title(sprintf('Exp4 soliton snapshot, N=%d, 200 steps',N));
    legend('Location','best');
    save_figure_set(fig,out,'fig14_soliton'); close(fig);
end

function dispVerdict(V)
    fprintf('\n ---------------- verdict ----------------\n');
    for i=1:size(V,1)
        fprintf('  %-38s obs=%-12.4g thr=%-12.4g %s\n', ...
            V{i,1},V{i,2},V{i,3},V{i,4});
    end
    fprintf(' -----------------------------------------\n');
end
