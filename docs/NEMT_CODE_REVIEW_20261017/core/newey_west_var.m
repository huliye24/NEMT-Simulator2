function [v, se] = newey_west_var(x, lag)
% newey_west_var  HAC variance of the sample mean of x.
%
% Bartlett kernel with lag+1. Returns variance of the mean and its SE.
    x = x(isfinite(x));
    n = numel(x);
    if n < 2
        v = NaN; se = NaN; return;
    end
    u = x - mean(x);
    s = sum(u.^2);
    for l = 1:lag
        if l >= n, break; end
        w = 1 - l/(lag+1);
        s = s + 2*w*sum(u(l+1:end).*u(1:end-l));
    end
    v = s / (n*n);          % HAC variance of the sample mean
    se = sqrt(max(v,0));
end
