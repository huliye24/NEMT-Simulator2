function run_exp4_clean(varargin)
%RUN_EXP4_CLEAN Rigorous NLS solver verification following R4 protocol.
%
% Experiment 4 (Revised): R4 Protocol for Solver Verification
%   A. Spatial convergence (T=0.2s, fixed physical time)
%   B. Temporal convergence (N=1024, extract orders)
%   C. Reliability boundary (T=0.2s, dt_max scan)
%   D. Long-time evolution (T=5s, equal dt)
%   E. Statistical gates (R²≥0.90, slope∈[1.65,2.35])
%
% Fixes from original exp4:
%   ✓ Physical domain L=20, coarsest N=256 → 15+ pts/FWHM
%   ✓ Fixed physical time T (not fixed step count)
%   ✓ Strict statistical gates
%   ✓ Analytical soliton only (no numerical reference)
%
% Usage:
%   run_exp4_clean('output', 'output/exp4_clean')
%   run_exp4_clean('output', 'output/exp4_clean', 'makeFigures', true)

opts.output = fullfile('output','exp4_clean');
opts.makeFigures = true;
for k=1:2:numel(varargin), opts.(varargin{k})=varargin{k+1}; end
if ~exist(opts.output,'dir'), mkdir(opts.output); end

% Add core path
here = fileparts(mfilename('fullpath'));
root = fileparts(here);
addpath(fullfile(root,'core'));

% Frozen parameters from R4 protocol
alpha=0.1; beta=1.0; L=20; A=1; 
fwhm=2*acosh(2)/(A*sqrt(beta/(2*alpha)));  % ~1.178
Ns=[256 384 512 768]; 
Tspace=0.2; dtSpace=2e-5;  % Spatial convergence
Ttime=0.5;                  % Temporal convergence
dts=[0.008 0.004 0.002 0.001];
methods={'euler','rk4','strang'};
Tb=0.2;                     % Boundary scan horizon
mus=logspace(log10(0.005),log10(6),25);
Tlong=5; muLong=0.2;        % Long-time test

fprintf('\n========== EXP4 CLEAN: R4 Protocol ==========\n');
fprintf(' Domain: L=%.1f, N=%s\n', L, mat2str(Ns));
fprintf(' FWHM: %.3f, min resolution: %.1f pts/FWHM\n', fwhm, fwhm/(L/min(Ns)));
fprintf(' Methods: %s\n', strjoin(methods,', '));
fprintf(' Output: %s\n', opts.output);

%% A. Spatial convergence at fixed T and negligible temporal error
fprintf('\n[A] Spatial convergence (T=%.2f, dt=%.0e)\n', Tspace, dtSpace);
spatial=[];
for N=Ns
    [psi0,x]=grid_and_soliton(N,L,alpha,beta,A);
    dx=L/N;
    dt=fit_dt(Tspace,dtSpace); n=round(Tspace/dt);
    psi=evolve(psi0,x,alpha,beta,dt,n,'strang');
    m=metrics(psi,exact_soliton(x,Tspace,alpha,beta,A),psi0,dx);
    spatial(end+1,:)=[N,dx,fwhm/dx,dt,n,m.l2,m.linf,m.mass]; %#ok<AGROW>
    fprintf('  N=%4d  dx=%.4f  pts/FWHM=%.1f  L2=%.3e  mass=%.3e\n', ...
        N,dx,fwhm/dx,m.l2,m.mass);
end
write_table(fullfile(opts.output,'spatial_convergence.csv'), ...
 {'N','dx','points_per_fwhm','dt','steps','rel_l2','rel_linf','mass_rel'},spatial);

%% B. Temporal convergence at well-resolved N
fprintf('\n[B] Temporal convergence (N=%d, T=%.2f)\n', 1024, Ttime);
Nt=1024; [psi0,x]=grid_and_soliton(Nt,L,alpha,beta,A); temporal=[];
for s=1:numel(methods)
    fprintf('  Method: %s\n', methods{s});
    for q=1:numel(dts)
        dt=fit_dt(Ttime,dts(q)); n=round(Ttime/dt);
        psi=evolve(psi0,x,alpha,beta,dt,n,methods{s});
        m=metrics(psi,exact_soliton(x,Ttime,alpha,beta,A),psi0,L/Nt);
        temporal(end+1,:)=[s,dt,n,m.l2,m.linf,m.mass,m.finite]; %#ok<AGROW>
        fprintf('    dt=%.4f  n=%4d  L2=%.3e  finite=%d\n',dt,n,m.l2,m.finite);
    end
end
write_temporal(fullfile(opts.output,'temporal_convergence.csv'),temporal,methods);

% Temporal order regression
orders=nan(numel(methods),4);
for s=1:numel(methods)
    r=temporal(temporal(:,1)==s & temporal(:,7)==1 & temporal(:,4)>0,:);
    if size(r,1)>=3
        p=polyfit(log(r(:,2)),log(r(:,4)),1); yh=polyval(p,log(r(:,2)));
        orders(s,:)=[s,p(1),r2score(log(r(:,4)),yh),size(r,1)];
        fprintf('  %s: order=%.2f  R²=%.3f  n=%d\n', ...
            upper(methods{s}),p(1),orders(s,3),orders(s,4));
    else
        orders(s,:)=[s,NaN,NaN,size(r,1)];
    end
end
write_orders(fullfile(opts.output,'temporal_orders.csv'),orders,methods);

%% C. Reliability boundary at fixed T
fprintf('\n[C] Reliability boundary (T=%.2f)\n', Tb);
boundary=[]; scan=[];
for s=1:numel(methods)
    fprintf('  Method: %s\n', methods{s});
    for N=Ns
        [psi0,x]=grid_and_soliton(N,L,alpha,beta,A); dx=L/N;
        last=NaN; firstBad=NaN;
        for mu=mus
            target=mu*dx^2/alpha; dt=fit_dt(Tb,target); n=round(Tb/dt);
            psi=evolve(psi0,x,alpha,beta,dt,n,methods{s});
            m=metrics(psi,exact_soliton(x,Tb,alpha,beta,A),psi0,dx);
            reliable=m.finite && m.maxratio<=10 && m.mass<=1e-3 && m.l2<=0.05;
            scan(end+1,:)=[s,N,dx,mu,dt,n,m.l2,m.mass,m.maxratio,reliable]; %#ok<AGROW>
            if reliable && isnan(firstBad), last=dt; end
            if ~reliable && isnan(firstBad), firstBad=dt; end
        end
        censored=isnan(firstBad);
        boundary(end+1,:)=[s,N,dx,last,censored]; %#ok<AGROW>
        if censored
            fprintf('    N=%4d  dx=%.4f  dt_r=%.4e (censored)\n',N,dx,last);
        else
            fprintf('    N=%4d  dx=%.4f  dt_r=%.4e\n',N,dx,last);
        end
    end
end
write_scan(fullfile(opts.output,'reliability_scan.csv'),scan,methods);
write_boundary(fullfile(opts.output,'reliability_boundaries.csv'),boundary,methods);

% Boundary scaling
scaling=nan(numel(methods),5);
for s=1:numel(methods)
    r=boundary(boundary(:,1)==s & boundary(:,5)==0 & isfinite(boundary(:,4)),:);
    if size(r,1)>=4
        p=polyfit(log(r(:,3)),log(r(:,4)),1); yh=polyval(p,log(r(:,3)));
        scaling(s,:)=[s,p(1),r2score(log(r(:,4)),yh),p(2),size(r,1)];
        fprintf('  %s: slope=%.2f  R²=%.3f  n=%d\n', ...
            upper(methods{s}),p(1),scaling(s,3),scaling(s,5));
    else
        scaling(s,:)=[s,NaN,NaN,NaN,size(r,1)];
    end
end
write_scaling(fullfile(opts.output,'boundary_scaling.csv'),scaling,methods);

%% D. Equal-physical-time long run
fprintf('\n[D] Long-time test (T=%.1f, mu=%.2f)\n', Tlong, muLong);
long=[];
for N=Ns
    [psi0,x]=grid_and_soliton(N,L,alpha,beta,A); dx=L/N;
    dt=fit_dt(Tlong,muLong*dx^2/alpha); n=round(Tlong/dt);
    psi=evolve(psi0,x,alpha,beta,dt,n,'strang');
    m=metrics(psi,exact_soliton(x,Tlong,alpha,beta,A),psi0,dx);
    long(end+1,:)=[N,dx,dt,n,Tlong,m.l2,m.linf,m.mass,m.maxratio]; %#ok<AGROW>
    fprintf('  N=%4d  dt=%.4e  n=%5d  L2=%.3e  mass=%.3e\n',N,dt,n,m.l2,m.mass);
end
write_table(fullfile(opts.output,'long_time.csv'), ...
 {'N','dx','dt','steps','physical_time','rel_l2','rel_linf','mass_rel','max_amp_ratio'},long);

%% E. Gates
fprintf('\n[E] Gate evaluation\n');
rk4=orders(2,:); validScale=scaling(isfinite(scaling(:,2)),:);
g1=min(spatial(:,3))>=12;
g2=all(diff(spatial(:,6))<0);
g3=rk4(4)>=3 && rk4(2)>=3.5 && rk4(2)<=4.5;
g4=~isempty(validScale) && any(validScale(:,3)>=0.90 & validScale(:,2)>=1.65 & validScale(:,2)<=2.35);
g5=max(long(:,6))<0.02 && max(long(:,8))<1e-10;

V={ 'R4.1_grid_resolution', min(spatial(:,3)), 12, g1, 'Coarsest grid pts/FWHM'; ...
    'R4.2_spatial_monotone', double(g2), 1, g2, 'Spatial error decreases'; ...
    'R4.3_rk4_order', rk4(2), 3.5, g3, 'RK4 temporal order [3.5,4.5]'; ...
    'R4.4_boundary_scaling', double(g4), 1, g4, 'Boundary R²≥0.90 & slope∈[1.65,2.35]'; ...
    'R4.5_equal_time_long_run', max(long(:,6)), 0.02, g5, 'Long-time Strang L2<2% & mass<1e-10'};

write_verdict(fullfile(opts.output,'verdict.csv'),V);

allPass=all([g1 g2 g3 g4 g5]);
fid=fopen(fullfile(opts.output,'RUN_COMPLETE.txt'),'w');
fprintf(fid,'Experiment 4 Clean (R4 Protocol)\nUTC: %s\nAll gates: %s\n', ...
    char(datetime('now','TimeZone','UTC')),passfail(allPass)); 
fclose(fid);

fprintf('\n========== Verdict ==========\n');
for i=1:size(V,1)
    fprintf('  %s: %s (%.3g vs %.3g) - %s\n', ...
        V{i,1},passfail(V{i,4}),V{i,2},V{i,3},V{i,5});
end
fprintf('========== Overall: %s ==========\n', passfail(allPass));

if opts.makeFigures
    make_figures(opts.output,spatial,temporal,orders,boundary,scaling,long,methods);
end
end

%% ========== Helper Functions ==========

function [psi,x]=grid_and_soliton(N,L,alpha,beta,A)
dx=L/N; x=((0:N-1)'-N/2)*dx;
psi=A./cosh(A*sqrt(beta/(2*alpha))*x)+0i;
end

function y=exact_soliton(x,t,alpha,beta,A)
y=A./cosh(A*sqrt(beta/(2*alpha))*x).*exp(1i*beta*A^2*t/2);
end

function dt=fit_dt(T,target)
dt=T/ceil(T/target);
end

function psi=evolve(psi,x,alpha,beta,dt,n,method)
N=numel(psi); dx=x(2)-x(1);
switch method
  case 'euler'
    for j=1:n
        lap=([psi(2:end); psi(1)] - 2*psi + [psi(end); psi(1:end-1)])/dx^2;
        psi=psi+dt*1i*(alpha*lap+beta*abs(psi).^2.*psi);
        if any(~isfinite(psi)), break; end
    end
  case 'rk4'
    f=@(v) 1i*(alpha*(([v(2:end);v(1)]-2*v+[v(end);v(1:end-1)])/dx^2)+beta*abs(v).^2.*v);
    for j=1:n
        k1=f(psi); k2=f(psi+dt*k1/2); k3=f(psi+dt*k2/2); k4=f(psi+dt*k3);
        psi=psi+dt*(k1+2*k2+2*k3+k4)/6;
        if any(~isfinite(psi)), break; end
    end
  case 'strang'
    kk=[0:N/2-1 -N/2:-1]'; omega=2*pi*kk/L; 
    linFactor=exp(-1i*alpha*omega.^2*dt/2);
    for j=1:n
        psi=ifft(linFactor.*fft(psi));
        psi=psi.*exp(1i*beta*abs(psi).^2*dt);
        psi=ifft(linFactor.*fft(psi));
        if any(~isfinite(psi)), break; end
    end
end
end

function m=metrics(psi,ref,psi0,dx)
m.finite=double(all(isfinite(psi)));
if ~m.finite, m.l2=Inf;m.linf=Inf;m.mass=Inf;m.maxratio=Inf;return;end
ov=sum(conj(ref).*psi); if abs(ov)>0, psi=psi*exp(-1i*angle(ov)); end
m.l2=norm(psi-ref)/norm(ref); m.linf=max(abs(psi-ref))/max(abs(ref));
m.mass=abs(sum(abs(psi).^2)-sum(abs(psi0).^2))/sum(abs(psi0).^2);
m.maxratio=max(abs(psi))/max(abs(psi0));
end

function r=r2score(y,yh)
r=1-sum((y-yh).^2)/sum((y-mean(y)).^2);
end

function s=passfail(x)
if x,s='PASS';else,s='FAIL';end
end

function write_table(path,h,A)
fid=fopen(path,'w');fprintf(fid,'%s\n',strjoin(h,','));fclose(fid);
writematrix(A,path,'WriteMode','append');
end

function write_temporal(path,A,names)
fid=fopen(path,'w');
fprintf(fid,'solver,dt,steps,rel_l2,rel_linf,mass_rel,finite\n');
for i=1:size(A,1)
    fprintf(fid,'%s,%.17g,%d,%.17g,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));
end
fclose(fid);
end

function write_orders(path,A,names)
fid=fopen(path,'w');
fprintf(fid,'solver,order,r2,n_points\n');
for i=1:size(A,1)
    fprintf(fid,'%s,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));
end
fclose(fid);
end

function write_scan(path,A,names)
fid=fopen(path,'w');
fprintf(fid,'solver,N,dx,mu,dt,steps,rel_l2,mass_rel,max_amp_ratio,reliable\n');
for i=1:size(A,1)
    fprintf(fid,'%s,%d,%.17g,%.17g,%.17g,%d,%.17g,%.17g,%.17g,%d\n', ...
        names{A(i,1)},A(i,2:end));
end
fclose(fid);
end

function write_boundary(path,A,names)
fid=fopen(path,'w');
fprintf(fid,'solver,N,dx,dt_reliable,censored\n');
for i=1:size(A,1)
    fprintf(fid,'%s,%d,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));
end
fclose(fid);
end

function write_scaling(path,A,names)
fid=fopen(path,'w');
fprintf(fid,'solver,slope,r2,intercept,n_points\n');
for i=1:size(A,1)
    fprintf(fid,'%s,%.17g,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));
end
fclose(fid);
end

function make_figures(out,S,T,O,B,G,L,names)
% Spatial convergence
f=figure('Visible','off','Color','w','Position',[100 100 800 600]); 
ax=axes(f);
loglog(ax,S(:,2),S(:,6),'o-','LineWidth',2,'MarkerSize',8);
grid(ax,'on'); xlabel(ax,'dx','FontSize',12); 
ylabel(ax,'Phase-aligned relative L2','FontSize',12);
title(ax,'Spatial Convergence: Resolved Exact Soliton','FontSize',14);
save_fig(f,out,'r4_spatial'); close(f);

% Temporal convergence
f=figure('Visible','off','Color','w','Position',[100 100 800 600]); 
ax=axes(f); hold(ax,'on'); grid(ax,'on');
for s=1:numel(names)
    r=T(T(:,1)==s & T(:,7)==1 & T(:,4)>0,:);
    if ~isempty(r)
        loglog(ax,r(:,2),r(:,4),'o-','LineWidth',2,'MarkerSize',8, ...
            'DisplayName',sprintf('%s (p=%.2f)',upper(names{s}),O(s,2)));
    end
end
xlabel(ax,'dt','FontSize',12); ylabel(ax,'Relative L2','FontSize',12);
legend(ax,'Location','best','FontSize',10);
title(ax,'Temporal Convergence at Fixed N and T','FontSize',14);
save_fig(f,out,'r4_temporal'); close(f);

% Reliability boundary
f=figure('Visible','off','Color','w','Position',[100 100 800 600]); 
ax=axes(f); hold(ax,'on'); grid(ax,'on');
for s=1:numel(names)
    r=B(B(:,1)==s & isfinite(B(:,4)),:);
    if ~isempty(r)
        loglog(ax,r(:,3),r(:,4),'o','MarkerSize',10,'LineWidth',2, ...
            'DisplayName',upper(names{s}));
        g=G(s,:);
        if isfinite(g(2))
            xx=logspace(log10(min(r(:,3))),log10(max(r(:,3))),100);
            loglog(ax,xx,exp(g(4))*xx.^g(2),'--','LineWidth',1.5, ...
                'HandleVisibility','off');
        end
    end
end
xlabel(ax,'dx','FontSize',12); ylabel(ax,'Largest Reliable dt','FontSize',12);
legend(ax,'Location','best','FontSize',10);
title(ax,'Reliability Boundary at Fixed Physical Horizon','FontSize',14);
save_fig(f,out,'r4_boundary'); close(f);

% Long-time test
f=figure('Visible','off','Color','w','Position',[100 100 800 600]); 
ax=axes(f);
yyaxis(ax,'left');
semilogy(ax,L(:,1),L(:,6),'o-','LineWidth',2,'MarkerSize',8);
ylabel(ax,'Relative L2','FontSize',12);
yyaxis(ax,'right');
semilogy(ax,L(:,1),L(:,8),'s-','LineWidth',2,'MarkerSize',8);
ylabel(ax,'Mass Drift','FontSize',12);
xlabel(ax,'N','FontSize',12); grid(ax,'on');
title(ax,'Strang Long-time Error at Common T=5','FontSize',14);
save_fig(f,out,'r4_long_time'); close(f);
end

function save_fig(f,out,name)
exportgraphics(f,fullfile(out,[name '.png']),'Resolution',300);
exportgraphics(f,fullfile(out,[name '.pdf']),'ContentType','vector');
saveas(f,fullfile(out,[name '.svg']));
end
