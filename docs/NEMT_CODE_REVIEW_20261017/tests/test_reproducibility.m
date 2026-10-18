function test_reproducibility()
% Same seed + same config -> byte-identical observation CSV.
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(genpath(root));
    addpath(fullfile(root,'exp5_observable_robustness'));
    addpath(fullfile(root,'exp6_btc_oos_h001'));
    cfg=exp5_config(true);
    cfg.nSeeds=2; cfg.seeds=cfg.seedRoot+(0:1); cfg.nWindows=4;
    cfg.nBars=4096; cfg.firstBar=512; cfg.stride=256;
    dtByN=struct('N256',5e-4);

    tmp=tempname; mkdir(tmp);
    cleaner=onCleanup(@() rmdir(tmp,'s'));
    for rep=1:2
        obs=exp5_collect(cfg,dtByN);
        M=[obs.process,obs.seed,obs.bar,obs.stateScore,obs.stateBin, ...
           obs.rawRef,obs.postRef];
        write_csv_table(fullfile(tmp,sprintf('obs%d.csv',rep)), ...
            {'process','seed','bar','state_score','state_bin','W2_raw', ...
             'Hspec_raw','Cspec_raw','Tail20_raw','IPR_raw','W2_post', ...
             'Hspec_post','Cspec_post','Tail20_post','IPR_post'},M);
    end
    h1=file_sha256(fullfile(tmp,'obs1.csv'));
    h2=file_sha256(fullfile(tmp,'obs2.csv'));
    assert(strcmp(h1,h2),'fixed-seed runs are not byte-identical');
end
