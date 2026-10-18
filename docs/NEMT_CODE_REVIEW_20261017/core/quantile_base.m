function q = quantile_base(x, p)
% quantile_base  Percentile without the Statistics Toolbox.
%
% Linear interpolation between order statistics (same convention as the
% default of common numerical libraries). NaNs are ignored.

    x = x(isfinite(x));
    if isempty(x)
        q = NaN; return;
    end
    x = sort(x(:));
    n = numel(x);
    if n == 1
        q = x(1); return;
    end
    pos = 1 + (n-1)*p(:);   % column keeps x(lo) and w the same shape
    lo = floor(pos);
    hi = ceil(pos);
    w = pos - lo;
    q = x(lo).*(1-w) + x(hi).*w;
    q = reshape(q, size(p));
end
