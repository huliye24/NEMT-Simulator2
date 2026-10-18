function R = run_tests(outDir)
% run_tests  Required pre-run regression suite.
%
%   R = run_tests(outDir)
%
% Writes tests.csv and returns R.pass. Any failing test blocks the full
% experiment chain.

    if nargin < 1 || isempty(outDir)
        outDir=fullfile(tempdir,'nemt_next_tests');
    end
    if ~exist(outDir,'dir'), mkdir(outDir); end
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(genpath(root));
    addpath(fullfile(root,'tests'));

    names={'parameter_application','time_alignment','golden_solvers', ...
           'metric_analytic','fixed_seed_reproducibility','quick_mode_contract'};
    fns={@test_parameter_application,@test_time_alignment, ...
         @test_golden_solvers,@test_metric_analytic, ...
         @test_reproducibility,@test_quick_mode_contract};
    rows=cell(numel(names),4);
    pass=true;
    fprintf('\n================ REGRESSION TESTS ================\n');
    for k=1:numel(names)
        t0=tic;
        try
            fns{k}();
            st='PASS'; msg='';
        catch ME
            st='FAIL';
            msg=sprintf('%s: %s',ME.identifier,ME.message);
            pass=false;
        end
        rows(k,:)={names{k},st,toc(t0),msg};
        fprintf('  %-28s %-4s %7.2f s %s\n',names{k},st,toc(t0),msg);
    end
    write_csv_table(fullfile(outDir,'tests.csv'), ...
        {'test','status','seconds','message'},rows);
    R=struct('pass',pass,'rows',{rows});
    fprintf('==================================================\n');
    if ~pass
        fprintf(' TESTS FAILED - experiment chain will not start\n');
    else
        fprintf(' ALL TESTS PASS\n');
    end
end
