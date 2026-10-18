function tq = t_quantile(p, df)
% t_quantile  Student-t quantile using base MATLAB's incomplete beta.
%
% For 0<p<1 and integer df>0. p=0.975 gives the two-sided 95% critical value.

    if df <= 0 || ~isfinite(df)
        tq = NaN; return;
    end
    if p == 0.5, tq = 0; return; end
    if p < 0 || p > 1
        error('t_quantile: p outside [0,1]');
    end
    if p < 0.5
        tq = -t_quantile(1-p, df);
        return;
    end
    % P(T <= t) = 1 - 0.5*I_{df/(df+t^2)}(df/2, 1/2)
    target = 2*(1-p);                 % desired upper-tail mass
    x = betaincinv(target, df/2, 0.5);
    tq = sqrt(df*(1-x)/x);
end
