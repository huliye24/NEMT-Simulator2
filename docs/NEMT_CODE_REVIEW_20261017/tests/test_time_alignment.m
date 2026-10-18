function test_time_alignment()
% Predictors at t must be unchanged by future tape edits; y_t must be
% unchanged by an edit before t and must equal the direct t+1..t+24 sum.
    root=fileparts(fileparts(mfilename('fullpath')));
    addpath(genpath(root));
    addpath(fullfile(root,'exp6_btc_oos_h001'));
    n=4000; seed=424242;
    t0=datetime(2019,1,1,0,0,0,'TimeZone','UTC');
    time=t0+hours(0:n-1)';
    rs=RandStream('mt19937ar','Seed',seed);
    z=randn(rs,n,1);
    baseVar=(0.006)^2; a=0.05; b=0.90; omega=baseVar*(1-a-b);
    h=zeros(n,1); h(1)=baseVar; r=zeros(n,1);
    for i=2:n
        h(i)=omega+a*r(i-1)^2+b*h(i-1);
        r(i)=sqrt(h(i))*z(i);
    end
    close=100*exp(cumsum(r));
    volume=1000*exp(0.3*randn(rs,n,1));
    D=makeD(close,volume,time);

    cfg=exp6_config(false);
    cfg.split.trainStart=t0;
    cfg.split.trainEnd=datetime(2019,2,28,23,0,0,'TimeZone','UTC');
    cfg.split.valStart=datetime(2019,3,1,0,0,0,'TimeZone','UTC');
    cfg.split.valEnd=datetime(2019,4,30,23,0,0,'TimeZone','UTC');
    cfg.split.testStart=datetime(2019,5,1,0,0,0,'TimeZone','UTC');
    cfg.split.testEnd=datetime(2019,6,10,23,0,0,'TimeZone','UTC');
    sel=test_selected();

    F=build(D,sel,cfg);
    ti=800;
    assert(F.valid(ti)==1,'test row unexpectedly invalid');
    rr=log(D.close(2:end)./D.close(1:end-1));
    yDirect=log(sqrt(sum(rr(ti:ti+23).^2)));
    assert(abs(F.y(ti)-yDirect)<1e-12,'label is not t+1..t+24 realized vol');

    % Future edit: everything before/at t must be untouched.
    closeF=close; closeF(ti+1:end)=closeF(ti+1:end).*exp(0.25*sin((1:n-ti)'/7));
    DF=makeD(closeF,volume,time);
    FF=build(DF,sel,cfg);
    pred=[FF.nemtRaw(ti),FF.nemtEvolved(ti),FF.rv24(ti),FF.rv72(ti), ...
          FF.rv168(ti),FF.absRetEMA(ti),FF.volZ(ti)];
    pred0=[F.nemtRaw(ti),F.nemtEvolved(ti),F.rv24(ti),F.rv72(ti), ...
           F.rv168(ti),F.absRetEMA(ti),F.volZ(ti)];
    assert(max(abs(pred-pred0))<1e-10,'a predictor used data after t');
    assert(abs(FF.y(ti)-F.y(ti))>1e-6,'label ignored a future return edit');

    % Past edit at t-1: y_t must not change.
    closeP=close; closeP(ti-1)=closeP(ti-1)*0.90;
    DP=makeD(closeP,volume,time);
    FP=build(DP,sel,cfg);
    assert(abs(FP.y(ti)-F.y(ti))<1e-12,'label used a return before t+1');
end

function F=build(D,sel,cfg)
    S=exp6_metric_series(D,sel);
    F=exp6_build_features(D,S,sel,cfg);
end

function D=makeD(close,volume,time)
    D=struct();
    D.close=close; D.volume=volume; D.time=time;
    D.timeMs=round(posixtime(time))*1000;
    D.open=close; D.high=close; D.low=close;
    D.quoteVolume=volume.*close;
    D.tradeCount=ones(size(close));
    D.sourceCsv='TEST'; D.sourceSha256='TEST'; D.manifestPath='TEST';
    D.rows=numel(close);
end

function sel=test_selected()
    sel=struct();
    sel.selected=true; sel.metric='W2'; sel.version='evolved';
    sel.estimator='periodogram'; sel.analysisWindow=128; sel.boundary='periodic';
    sel.psiWindow=128; sel.momentumWindow=24;
    sel.nls=struct('solver','ssfm','steps',20,'dt',5e-4,'dx',0.5, ...
        'profileLength',256,'nfft',256);
end
