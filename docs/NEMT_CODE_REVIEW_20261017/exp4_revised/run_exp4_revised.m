function run_exp4_revised(varargin)
%RUN_EXP4_REVISED Reproducible verification of NLS numerical solvers.
% Writes CSV, JSON-style text summary and publication-grade PNG/PDF/SVG figures.

opts.output = fullfile('output','exp4_revised');
opts.makeFigures = true;
for k=1:2:numel(varargin), opts.(varargin{k})=varargin{k+1}; end
if ~exist(opts.output,'dir'), mkdir(opts.output); end

alpha=0.1; beta=1.0; L=20; A=1; fwhm=2*acosh(2)/(A*sqrt(beta/(2*alpha)));
Ns=[256 384 512 768]; Tspace=0.2; dtSpace=2e-5;

%% A. Spatial convergence at fixed physical time and negligible temporal error
spatial=[];
for N=Ns
    [x,kx,psi0]=grid_and_soliton(N,L,alpha,beta,A);
    dt=fit_dt(Tspace,dtSpace); n=round(Tspace/dt);
    psi=evolve(psi0,kx,alpha,beta,dt,n,'strang');
    m=metrics(psi,exact_soliton(x,Tspace,alpha,beta,A),psi0,L/N);
    spatial(end+1,:)=[N,L/N,fwhm/(L/N),dt,n,m.l2,m.linf,m.mass]; %#ok<AGROW>
end
writematrix_with_header(fullfile(opts.output,'spatial_convergence.csv'), ...
 {'N','dx','points_per_fwhm','dt','steps','rel_l2','rel_linf','mass_rel'},spatial);

%% B. Temporal convergence at one well-resolved grid
Nt=1024; Ttime=0.5; dts=[0.008 0.004 0.002 0.001]; methods={'euler','rk4','strang'};
[x,kx,psi0]=grid_and_soliton(Nt,L,alpha,beta,A); temporal=[];
for s=1:numel(methods)
    for q=1:numel(dts)
        dt=fit_dt(Ttime,dts(q)); n=round(Ttime/dt);
        psi=evolve(psi0,kx,alpha,beta,dt,n,methods{s});
        m=metrics(psi,exact_soliton(x,Ttime,alpha,beta,A),psi0,L/Nt);
        temporal(end+1,:)=[s,dt,n,m.l2,m.linf,m.mass,m.finite]; %#ok<AGROW>
    end
end
write_temporal(fullfile(opts.output,'temporal_convergence.csv'),temporal,methods);
orders=nan(numel(methods),4);
for s=1:numel(methods)
    r=temporal(temporal(:,1)==s & temporal(:,7)==1 & temporal(:,4)>0,:);
    if size(r,1)>=3
        p=polyfit(log(r(:,2)),log(r(:,4)),1); yh=polyval(p,log(r(:,2)));
        orders(s,:)=[s,p(1),r2score(log(r(:,4)),yh),size(r,1)];
    else, orders(s,:)=[s,NaN,NaN,size(r,1)]; end
end
write_orders(fullfile(opts.output,'temporal_orders.csv'),orders,methods);

%% C. Practical reliability boundary at a fixed physical horizon
mus=logspace(log10(0.005),log10(6),25); Tb=0.2; boundary=[]; scan=[];
for s=1:numel(methods)
  for N=Ns
    [x,kx,psi0]=grid_and_soliton(N,L,alpha,beta,A); dx=L/N;
    last=NaN; firstBad=NaN;
    for mu=mus
        target=mu*dx^2/alpha; dt=fit_dt(Tb,target); n=round(Tb/dt);
        psi=evolve(psi0,kx,alpha,beta,dt,n,methods{s});
        m=metrics(psi,exact_soliton(x,Tb,alpha,beta,A),psi0,dx);
        reliable=m.finite && m.maxratio<=10 && m.mass<=1e-3 && m.l2<=0.05;
        scan(end+1,:)=[s,N,dx,mu,dt,n,m.l2,m.mass,m.maxratio,reliable]; %#ok<AGROW>
        if reliable && isnan(firstBad), last=dt; end
        if ~reliable && isnan(firstBad), firstBad=dt; end
    end
    censored=isnan(firstBad);
    boundary(end+1,:)=[s,N,dx,last,censored]; %#ok<AGROW>
  end
end
write_scan(fullfile(opts.output,'reliability_scan.csv'),scan,methods);
write_boundary(fullfile(opts.output,'reliability_boundaries.csv'),boundary,methods);

scaling=nan(numel(methods),5);
for s=1:numel(methods)
    r=boundary(boundary(:,1)==s & boundary(:,5)==0 & isfinite(boundary(:,4)),:);
    if size(r,1)>=4
        p=polyfit(log(r(:,3)),log(r(:,4)),1); yh=polyval(p,log(r(:,3)));
        scaling(s,:)=[s,p(1),r2score(log(r(:,4)),yh),p(2),size(r,1)];
    else, scaling(s,:)=[s,NaN,NaN,NaN,size(r,1)]; end
end
write_scaling(fullfile(opts.output,'boundary_scaling.csv'),scaling,methods);

%% D. Equal-physical-time long run
Tlong=5; muLong=0.2; long=[];
for N=Ns
    [x,kx,psi0]=grid_and_soliton(N,L,alpha,beta,A); dx=L/N;
    dt=fit_dt(Tlong,muLong*dx^2/alpha); n=round(Tlong/dt);
    psi=evolve(psi0,kx,alpha,beta,dt,n,'strang');
    m=metrics(psi,exact_soliton(x,Tlong,alpha,beta,A),psi0,dx);
    long(end+1,:)=[N,dx,dt,n,Tlong,m.l2,m.linf,m.mass,m.maxratio]; %#ok<AGROW>
end
writematrix_with_header(fullfile(opts.output,'long_time.csv'), ...
 {'N','dx','dt','steps','physical_time','rel_l2','rel_linf','mass_rel','max_amp_ratio'},long);

%% Gates and provenance
rk4=orders(2,:); validScale=scaling(isfinite(scaling(:,2)),:);
g1=min(spatial(:,3))>=12;
g2=all(diff(spatial(:,6))<0);
g3=rk4(4)>=3 && rk4(2)>=3.5 && rk4(2)<=4.5;
g4=~isempty(validScale) && any(validScale(:,3)>=0.90 & validScale(:,2)>=1.65 & validScale(:,2)<=2.35);
g5=max(long(:,6))<0.02 && max(long(:,8))<1e-10;
V={ 'R4.1_grid_resolution',min(spatial(:,3)),12,g1; ...
    'R4.2_spatial_monotone',double(g2),1,g2; ...
    'R4.3_rk4_order',rk4(2),3.5,g3; ...
    'R4.4_boundary_scaling',double(g4),1,g4; ...
    'R4.5_equal_time_long_run',max(long(:,6)),0.02,g5};
write_verdict(fullfile(opts.output,'verdict.csv'),V);
fid=fopen(fullfile(opts.output,'RUN_COMPLETE.txt'),'w');
fprintf(fid,'Experiment 4R complete\nUTC %s\nAll mandatory gates: %s\n', ...
    char(datetime('now','TimeZone','UTC')),passfail(all([g1 g2 g3 g4 g5]))); fclose(fid);

if opts.makeFigures
    make_figures(opts.output,spatial,temporal,orders,boundary,scaling,long,methods);
end
disp(V);
end

function [x,kx,psi]=grid_and_soliton(N,L,alpha,beta,A)
dx=L/N; x=((0:N-1)'-N/2)*dx;
kk=[0:N/2-1 -N/2:-1]'; kx=2*pi*kk/L;
psi=A./cosh(A*sqrt(beta/(2*alpha))*x)+0i;
end
function y=exact_soliton(x,t,alpha,beta,A) %#ok<INUSD>
y=A./cosh(A*sqrt(beta/(2*alpha))*x).*exp(1i*beta*A^2*t/2);
end
function dt=fit_dt(T,target), dt=T/ceil(T/target); end
function psi=evolve(psi,k,alpha,beta,dt,n,method)
for j=1:n
    switch method
      case 'euler', psi=psi+dt*rhs(psi,k,alpha,beta);
      case 'rk4'
        q1=rhs(psi,k,alpha,beta); q2=rhs(psi+dt*q1/2,k,alpha,beta);
        q3=rhs(psi+dt*q2/2,k,alpha,beta); q4=rhs(psi+dt*q3,k,alpha,beta);
        psi=psi+dt*(q1+2*q2+2*q3+q4)/6;
      case 'strang'
        psi=ifft(fft(psi).*exp(-1i*alpha*k.^2*dt/2));
        psi=psi.*exp(1i*beta*abs(psi).^2*dt);
        psi=ifft(fft(psi).*exp(-1i*alpha*k.^2*dt/2));
    end
    if any(~isfinite(psi)), break; end
end
end
function y=rhs(psi,k,alpha,beta)
y=1i*(alpha*ifft(-(k.^2).*fft(psi))+beta*abs(psi).^2.*psi);
end
function m=metrics(psi,ref,psi0,dx)
m.finite=double(all(isfinite(psi)));
if ~m.finite, m.l2=Inf;m.linf=Inf;m.mass=Inf;m.maxratio=Inf;return;end
ov=sum(conj(ref).*psi); if abs(ov)>0, psi=psi*exp(-1i*angle(ov)); end
m.l2=norm(psi-ref)/norm(ref); m.linf=max(abs(psi-ref))/max(abs(ref));
m.mass=abs(sum(abs(psi).^2)-sum(abs(psi0).^2))/sum(abs(psi0).^2);
m.maxratio=max(abs(psi))/max(abs(psi0));
end
function r=r2score(y,yh), r=1-sum((y-yh).^2)/sum((y-mean(y)).^2); end
function s=passfail(x), if x,s='PASS';else,s='FAIL';end,end
function writematrix_with_header(path,h,A)
fid=fopen(path,'w');fprintf(fid,'%s\n',strjoin(h,','));fclose(fid);writematrix(A,path,'WriteMode','append');
end
function write_temporal(path,A,names)
fid=fopen(path,'w');fprintf(fid,'solver,dt,steps,rel_l2,rel_linf,mass_rel,finite\n');
for i=1:size(A,1),fprintf(fid,'%s,%.17g,%d,%.17g,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));end;fclose(fid);
end
function write_orders(path,A,names)
fid=fopen(path,'w');fprintf(fid,'solver,order,r2,n_points\n');for i=1:size(A,1),fprintf(fid,'%s,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));end;fclose(fid);
end
function write_scan(path,A,names)
fid=fopen(path,'w');fprintf(fid,'solver,N,dx,mu,dt,steps,rel_l2,mass_rel,max_amp_ratio,reliable\n');
for i=1:size(A,1),fprintf(fid,'%s,%d,%.17g,%.17g,%.17g,%d,%.17g,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));end;fclose(fid);
end
function write_boundary(path,A,names)
fid=fopen(path,'w');fprintf(fid,'solver,N,dx,dt_reliable,censored\n');for i=1:size(A,1),fprintf(fid,'%s,%d,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));end;fclose(fid);
end
function write_scaling(path,A,names)
fid=fopen(path,'w');fprintf(fid,'solver,slope,r2,intercept,n_points\n');for i=1:size(A,1),fprintf(fid,'%s,%.17g,%.17g,%.17g,%d\n',names{A(i,1)},A(i,2:end));end;fclose(fid);
end
function write_verdict(path,V)
fid=fopen(path,'w');fprintf(fid,'criterion,observed,threshold,status\n');for i=1:size(V,1),fprintf(fid,'%s,%.17g,%.17g,%s\n',V{i,1},V{i,2},V{i,3},passfail(V{i,4}));end;fclose(fid);
end
function make_figures(out,S,T,O,B,G,L,names)
f=figure('Visible','off','Color','w'); ax=axes(f);loglog(ax,S(:,2),S(:,6),'o-','LineWidth',1.5);grid(ax,'on');xlabel(ax,'dx');ylabel(ax,'phase-aligned relative L2');title(ax,'Spatial convergence: resolved exact soliton');save_set(f,out,'r4_spatial');close(f);
f=figure('Visible','off','Color','w');ax=axes(f);hold(ax,'on');grid(ax,'on');for s=1:numel(names),r=T(T(:,1)==s,:);loglog(ax,r(:,2),r(:,4),'o-','DisplayName',sprintf('%s, p=%.2f',upper(names{s}),O(s,2)));end;xlabel(ax,'dt');ylabel(ax,'relative L2');legend(ax,'Location','best');title(ax,'Temporal convergence at fixed N and T');save_set(f,out,'r4_temporal');close(f);
f=figure('Visible','off','Color','w');ax=axes(f);hold(ax,'on');grid(ax,'on');for s=1:numel(names),r=B(B(:,1)==s & isfinite(B(:,4)),:);loglog(ax,r(:,3),r(:,4),'o','DisplayName',upper(names{s}));g=G(s,:);if isfinite(g(2)),xx=logspace(log10(min(r(:,3))),log10(max(r(:,3))),100);loglog(ax,xx,exp(g(4))*xx.^g(2),'--','HandleVisibility','off');end;end;xlabel(ax,'dx');ylabel(ax,'largest reliable dt');legend(ax,'Location','best');title(ax,'Reliability boundary at fixed physical horizon');save_set(f,out,'r4_boundary');close(f);
f=figure('Visible','off','Color','w');ax=axes(f);yyaxis(ax,'left');semilogy(ax,L(:,1),L(:,6),'o-','LineWidth',1.5);ylabel(ax,'relative L2');yyaxis(ax,'right');semilogy(ax,L(:,1),L(:,8),'s-','LineWidth',1.5);ylabel(ax,'mass drift');xlabel(ax,'N');grid(ax,'on');title(ax,'Strang long-time error at common T=5');save_set(f,out,'r4_long_time');close(f);
end
function save_set(f,out,name)
exportgraphics(f,fullfile(out,[name '.png']),'Resolution',220);exportgraphics(f,fullfile(out,[name '.pdf']),'ContentType','vector');saveas(f,fullfile(out,[name '.svg']));
end
