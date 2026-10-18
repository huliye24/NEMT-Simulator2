function test_quick_mode_contract()
% Quick mode may only shrink grids. Thresholds, splits, formulas and column
% names must be identical.
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(genpath(root));
    addpath(fullfile(root,'exp4_fixed_step_stability'));
    addpath(fullfile(root,'exp5_observable_robustness'));
    addpath(fullfile(root,'exp6_btc_oos_h001'));

    s4f=exp4_spec(false); s4q=exp4_spec(true);
    assert(isequal(s4f.thresh,s4q.thresh),'exp4 thresholds changed');
    assert(isequal(s4f.hdr,s4q.hdr),'exp4 headers changed');
    assert(s4f.steps==s4q.steps,'exp4 fixed steps changed');
    assert(isequal(s4f.solvers,s4q.solvers)&&isequal(s4f.inits,s4q.inits), ...
        'exp4 solver/init definition changed');
    assert(numel(s4f.Nlist)~=numel(s4q.Nlist)&&numel(s4f.dtScan)~=numel(s4q.dtScan), ...
        'exp4 quick grid did not shrink');

    c5f=exp5_config(false); c5q=exp5_config(true);
    assert(isequal(c5f.thresholds,c5q.thresholds),'exp5 thresholds changed');
    assert(isequaln(c5f.settings,c5q.settings),'exp5 setting grid changed');
    assert(isequal(c5f.metrics,c5q.metrics),'exp5 metrics changed');
    assert(isequal(c5f.hdr,c5q.hdr),'exp5 headers changed');
    assert(c5q.nSeeds<c5f.nSeeds&&c5q.nWindows<c5f.nWindows,'exp5 quick did not shrink');
    assert(c5f.nlsSteps==c5q.nlsSteps,'exp5 NLS steps changed');

    c6f=exp6_config(false); c6q=exp6_config(true);
    assert(isequal(c6f.thresholds,c6q.thresholds),'exp6 thresholds changed');
    assert(isequal(c6f.split,c6q.split),'exp6 split changed');
    assert(isequal(c6f.headers,c6q.headers),'exp6 headers changed');
    assert(c6f.targetHorizon==c6q.targetHorizon,'exp6 horizon changed');
    assert(c6q.nBootstrap<c6f.nBootstrap&&c6q.nPlacebo<c6f.nPlacebo, ...
        'exp6 quick did not shrink replication grids');
end
