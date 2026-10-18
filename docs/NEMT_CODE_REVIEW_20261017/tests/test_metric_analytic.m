function test_metric_analytic()
% Analytic direction checks for the five observables.
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(genpath(fullfile(root,'core')));
    addpath(fullfile(root,'exp5_observable_robustness'));
    n=256; t=(0:n-1)';
    cfg=struct('estimator','periodogram','window',n,'boundary','periodic');

    sine=sin(2*pi*10*t/n);
    old=rng; rng(12345,'twister'); white=randn(n,1); rng(old);
    fLo=linspace(20,80,n)'; fHi=linspace(60,120,n)';
    chirpLo=sin(2*pi*cumsum(fLo)/n);
    chirpHi=sin(2*pi*cumsum(fHi)/n);

    Ms=obs_metrics(sine,cfg);
    Mw=obs_metrics(white,cfg);
    Ml=obs_metrics(chirpLo,cfg);
    Mh=obs_metrics(chirpHi,cfg);

    assert(abs(Ms.Cspec-10/n)<0.02,'sine centroid wrong');
    assert(Mw.Hspec>Ms.Hspec,'white entropy not above pure sine');
    assert(Mw.Tail20>0.10 && Mw.Tail20<0.30,'white Tail20 outside plausible band');
    assert(Ms.Tail20<0.05,'low-frequency sine has large tail mass');
    assert(Mh.Cspec>Ml.Cspec,'higher chirp does not raise centroid');
    assert(Mh.Tail20>Ml.Tail20,'higher chirp does not raise tail mass');
    assert(Mh.Hspec>Ms.Hspec,'chirp entropy not above pure sine');

    % W2 must be exactly the previous lab's definition for the reference
    % periodogram/periodic case.
    psi=complex(randn(n,1),randn(n,1));
    Wref=spectral_width(psi);
    M=obs_metrics(psi,cfg);
    assert(abs(Wref-M.W2)<1e-12,'W2 does not match spectral_width');

    % IPR analytic limits.
    cst=ones(n,1); Mconst=obs_metrics(cst,cfg);
    spike=zeros(n,1); spike(128)=1; Mspike=obs_metrics(spike,cfg);
    assert(abs(Mconst.IPR-1/n)<1e-12,'constant profile IPR != 1/N');
    assert(abs(Mspike.IPR-1)<1e-12,'single-spike IPR != 1');
end
