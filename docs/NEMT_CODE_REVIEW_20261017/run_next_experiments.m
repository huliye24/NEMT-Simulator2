function run_next_experiments(varargin)
% run_next_experiments  Single entry point for experiments 4 -> 5 -> 6.
%
%   run_next_experiments
%   run_next_experiments('quick',true)      grids shrunk; still gate-enforced
%   run_next_experiments('skipTests',true)  development only
%
% Every run writes a new immutable directory runs/<run_id>/ with:
%   tests/, exp4/, exp5/ (if gate allows), exp6/ (if gate allows),
%   environment.json, run.log, run_status.json, run_manifest.json,
%   SHA256SUMS.txt.
%
% Gates are enforced, not softened:
%   tests all PASS -> exp4 -> C4.3 and C4.5 PASS -> exp5
%   exp5 at least one observable passes C5.1-C5.4 -> exp6 confirmatory run.
%
% If a gate fails, downstream verdict files are written as BLOCKED and the
% run stops. No test-segment BTC data is opened before exp5 eligibility.

    opts.outputRoot=fullfile(fileparts(mfilename('fullpath')),'runs');
    opts.quick=false;
    opts.skipTests=false;
    for i=1:2:numel(varargin)
        opts.(varargin{i})=varargin{i+1};
    end
    here=fileparts(mfilename('fullpath'));
    addpath(genpath(fullfile(here,'core')));
    addpath(here);
    addpath(fullfile(here,'tests'));

    stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmss''Z'''));
    runId=stamp;
    runDir=fullfile(opts.outputRoot,runId);
    if exist(runDir,'dir')
        runId=[stamp '_' sprintf('%03d',mod(round(rand*1000),1000))];
        runDir=fullfile(opts.outputRoot,runId);
    end
    mkdir(runDir);
    logPath=fullfile(runDir,'run.log');
    diary(logPath); diary on;
    startUtc=utc_now();
    t0=tic;
    status='RUNNING'; message='';
    env=environment_info(here);
    env.runId=runId;
    env.codeHash=env.codeTreeSha256;
    env.quick=opts.quick;
    env.startUtc=startUtc;
    write_json_file(fullfile(runDir,'environment.json'),env);
    fprintf('\n######## RUN %s ########\n',runId);
    fprintf('root=%s quick=%d codeHash=%s\n',here,opts.quick,env.codeHash);

    try
        % ---------------------------------------------------------- tests
        testDir=fullfile(runDir,'tests');
        if opts.skipTests
            fprintf('[tests] SKIPPED by caller (development only)\n');
        else
            TR=run_tests(testDir);
            if ~TR.pass
                status='FAILED'; message='regression tests failed';
                finish();
                return;
            end
        end

        % ---------------------------------------------------------- exp4
        exp4Dir=fullfile(runDir,'exp4');
        fprintf('\n######## EXP4 ########\n');
        run_exp4('output',exp4Dir,'quick',opts.quick, ...
            'makeFigures',true,'codeHash',env.codeHash);
        c43=status_is_pass(fullfile(exp4Dir,'exp4_verdict.csv'),'C4.3');
        c45=status_is_pass(fullfile(exp4Dir,'exp4_verdict.csv'),'C4.5');
        if ~(c43 && c45)
            status='BLOCKED';
            message='exp4 C4.3/C4.5 SSFM safety gate failed; exp5 and exp6 blocked';
            writeBlockedExp5(fullfile(runDir,'exp5'),message);
            writeBlockedExp6(fullfile(runDir,'exp6'), ...
                'exp4 SSFM safety gate failed; exp5 never produced a selected metric', ...
                opts.quick);
            finish();
            return;
        end

        % ---------------------------------------------------------- exp5
        exp5Dir=fullfile(runDir,'exp5');
        fprintf('\n######## EXP5 ########\n');
        run_exp5('output',exp5Dir,'exp4Dir',exp4Dir,'quick',opts.quick, ...
            'makeFigures',true,'codeHash',env.codeHash);
        selFile=fullfile(exp5Dir,'exp5_selected_metric.json');
        selOK=false;
        if exist(selFile,'file')
            J=jsondecode(fileread(selFile));
            selOK=isfield(J,'selected')&&logical(J.selected);
        end
        if ~selOK || ~status_is_pass(fullfile(exp5Dir,'exp5_verdict.csv'),'C5.0_eligibility')
            status='BLOCKED';
            message='no observable passed C5.1-C5.4; exp6 blocked (no test data read)';
            writeBlockedExp6(fullfile(runDir,'exp6'),message,opts.quick);
            finish();
            return;
        end

        % ---------------------------------------------------------- exp6
        if opts.quick
            fprintf('\n[exp6] quick mode does not open the real test segment; skipped.\n');
            writeBlockedExp6(fullfile(runDir,'exp6'), ...
                'quick mode does not open the real confirmatory test segment',true);
            status='COMPLETE';
            message='quick smoke completed through exp5; exp6 skipped';
            finish();
            return;
        end
        fprintf('\n######## EXP6 ########\n');
        run_exp6('output',fullfile(runDir,'exp6'), ...
            'exp5Dir',exp5Dir,'selectedPath',selFile, ...
            'confirmatory',true,'quick',false,'makeFigures',true, ...
            'codeHash',env.codeHash);
        status='COMPLETE';
        message='experiment chain completed';
        finish();
    catch ME
        status='FAILED';
        message=sprintf('%s: %s',ME.identifier,ME.message);
        fprintf('\nRUN FAILED: %s\n',message);
        if ~isempty(ME.stack)
            for k=1:min(3,numel(ME.stack))
                fprintf('  at %s line %d\n',ME.stack(k).name,ME.stack(k).line);
            end
        end
        finish();
    end

    function finish()
        S=struct('runId',runId,'status',status,'message',message, ...
            'quick',opts.quick,'startedUtc',startUtc, ...
            'finishedUtc',utc_now(),'elapsedSeconds',toc(t0), ...
            'runDirectory',runDir,'log',logPath);
        write_json_file(fullfile(runDir,'run_status.json'),S);
        diary off;
        env.elapsedSeconds=toc(t0);
        finalize_run(runDir,status,message,env,startUtc);
        try
            fid=fopen(fullfile(opts.outputRoot,'LATEST_RUN.txt'),'w');
            fprintf(fid,'%s\n',runDir); fclose(fid);
        catch
        end
        try
            fid=fopen(fullfile(here,'output','run_status.json'),'w');
            if fid>=0, fprintf(fid,'%s\n',jsonencode(S)); fclose(fid); end
        catch
        end
        fprintf('\n######## RUN %s state=%s elapsed=%.1f s ########\n', ...
            runId,status,toc(t0));
        fprintf('outputs: %s\n',runDir);
    end
end

% ============================================================ blocked outputs
function writeBlockedExp5(dirOut,reason)
    if ~exist(dirOut,'dir'), mkdir(dirOut); end
    V={
        'C5.0_exp4_gate',0,1,'FAIL',reason;
        'C5.0_eligibility',NaN,1,'BLOCKED','not evaluated: exp4 gate failed';
        'C5.1_definition_robustness',NaN,0.75,'BLOCKED',reason;
        'C5.2_retest_reliability',NaN,0.70,'BLOCKED',reason;
        'C5.3_known_state_response',NaN,3,'BLOCKED',reason;
        'C5.4_seed_generalization',NaN,3,'BLOCKED',reason;
        'C5.5_nls_gain',NaN,0,'BLOCKED',reason;
    };
    write_verdict(fullfile(dirOut,'exp5_verdict.csv'),V);
    s=struct('experiment','exp5','status','BLOCKED','reason',reason, ...
        'createdAtUtc',utc_now(),'selected',false,'selectedMetric','');
    write_json_file(fullfile(dirOut,'exp5_selected_metric.json'),s);
    write_json_file(fullfile(dirOut,'exp5_config.json'),s);
end

function writeBlockedExp6(dirOut,reason,quick)
    if ~exist(dirOut,'dir'), mkdir(dirOut); end
    cfg=exp6_config(quick);
    V={
        'C6.1_data_integrity',NaN,cfg.thresholds.C6_1_validFraction,'BLOCKED',reason;
        'C6.2_volatility_increment',NaN,cfg.thresholds.C6_2_qlikeImprovement*100,'BLOCKED',reason;
        'C6.3_oos_explanatory',NaN,cfg.thresholds.C6_3_r2Diff,'BLOCKED',reason;
        'C6.4_extreme_event_increment',NaN,cfg.thresholds.C6_4_prImprovement,'BLOCKED',reason;
        'C6.5_direction_stability',NaN,cfg.thresholds.C6_5_signFraction,'BLOCKED',reason;
    };
    write_verdict(fullfile(dirOut,'exp6_verdict.csv'),V);
    s=struct('experiment','exp6','status','BLOCKED','reason',reason, ...
        'createdAtUtc',utc_now(),'quick',logical(quick), ...
        'testSegmentOpened',false);
    write_json_file(fullfile(dirOut,'exp6_config.json'),s);
    write_json_file(fullfile(dirOut,'exp6_conclusion.json'), ...
        struct('label','BLOCKED','legalSentence','No test conclusion: prerequisite gate failed.'));
end
