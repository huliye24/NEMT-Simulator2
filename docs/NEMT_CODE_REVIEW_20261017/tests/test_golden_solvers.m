function test_golden_solvers()
% New core must reproduce the previous lab's validated golden sample
% point-for-point. This is the regression guard for any core edit.
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(genpath(fullfile(root,'core')));
    oldDir=fullfile(fileparts(root),'exp1_solver_stability','output','exp1','golden');
    if ~exist(oldDir,'dir')
        error('previous golden directory missing: %s',oldDir);
    end
    tmp=tempname; mkdir(tmp);
    cleaner=onCleanup(@() rmdir(tmp,'s'));
    p=NEMTParams();
    io_tools('golden',tmp,p);

    files={'golden_close.csv','golden_psi0.csv','golden_psi_ssfm.csv', ...
           'golden_psi_euler.csv','golden_psi_rk4.csv','golden_sw_ssfm.csv', ...
           'golden_sw_euler.csv','golden_sw_rk4.csv','golden_power.csv'};
    mx=0;
    for k=1:numel(files)
        A=readtable(fullfile(oldDir,files{k}),'Delimiter',',');
        B=readtable(fullfile(tmp,files{k}),'Delimiter',',');
        if size(A)~=size(B)
            error('golden size mismatch for %s',files{k});
        end
        for c=1:width(A)
            if ~isnumeric(A{:,c}), continue; end
            d=max(abs(A{:,c}-B{:,c}));
            if isfinite(d), mx=max(mx,d); end
        end
    end
    assert(mx<=1e-12,sprintf('golden max abs difference %.3g > 1e-12',mx));
end
