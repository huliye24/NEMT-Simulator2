function test_parameter_application()
% Different (alpha,beta) must actually enter both Euler and SSFM updates.
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(fullfile(root,'core'));
    [psi0,~]=soliton_profile(64,1,0.1,1.0,1.0);
    p1=NEMTParams('alpha',0.1,'beta',1.0,'dt',0.01,'steps',1,'dx',1);
    p2=NEMTParams('alpha',0.25,'beta',2.0,'dt',0.01,'steps',1,'dx',1);
    a1=nls_euler(psi0,p1); a2=nls_euler(psi0,p2);
    assert(max(abs(a1-a2))>1e-5,'Euler ignores alpha/beta');
    s1=nls_ssfm(psi0,p1); s2=nls_ssfm(psi0,p2);
    assert(max(abs(s1-s2))>1e-5,'SSFM ignores alpha/beta');
    p3=p2; p3.alpha=p2.alpha;
    assert(p3.alpha==0.25 && p3.beta==2.0,'name-value parameters not stored');
    p4=p3; p4.steps=2;
    assert(max(abs(nls_euler(psi0,p4)-nls_euler(psi0,p3)))>1e-8,'steps has no effect');
end
