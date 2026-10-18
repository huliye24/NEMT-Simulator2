function out = stats_tools(op, varargin)
% stats_tools  Small statistics helpers, toolbox-free.
%
%   r  = stats_tools('spearman', x, y)
%   r  = stats_tools('pearson',  x, y)
%   r  = stats_tools('partial',  x, y, Z)      residualise on Z then correlate
%   ci = stats_tools('bootci',   x, nboot, alpha)   percentile CI of the mean
%   v  = stats_tools('realizedvol', close, w)      rolling realised vol
%   b  = stats_tools('nwslope',  y, X, lag)        Newey-West t-stat of X
%
%   'partial' is the increment-information test used in exp3: corr(x,y) can
%   be large purely because both track volatility; corr(resid x, resid y)
%   removes that common driver.
%
%   'nwslope' returns [beta, tStat] for the last column of X using a
%   Newey-West HAC covariance with `lag` lags. OLS standard errors are
%   badly biased in this setting because the residuals are both
%   autocorrelated and heteroskedastic; using them would manufacture
%   significance.

    switch lower(op)
        case 'spearman'
            [x,y] = deal(varargin{1}, varargin{2});
            out = corr_simple(rankcols(x), rankcols(y));

        case 'pearson'
            [x,y] = deal(varargin{1}, varargin{2});
            out = corr_simple(x, y);

        case 'partial'
            x = varargin{1}; y = varargin{2}; Z = varargin{3};
            rx = residualise(x, Z);
            ry = residualise(y, Z);
            out = corr_simple(rx, ry);

        case 'bootci'
            x = varargin{1};
            nboot = varargin{2};
            alpha = 0.05;
            if nargin >= 4+1-1 && numel(varargin) >= 3, alpha = varargin{3}; end
            x = x(isfinite(x));
            n = numel(x);
            if n == 0, out = [NaN NaN]; return; end
            rng(20240101);
            m = zeros(nboot,1);
            for b = 1:nboot
                idx = randi(n, n, 1);
                m(b) = mean(x(idx));
            end
            out = [prctile(m, 100*alpha/2), prctile(m, 100*(1-alpha/2))];

        case 'realizedvol'
            close = varargin{1}; w = varargin{2};
            r = [NaN; log(close(2:end)./close(1:end-1))];
            out = nan(numel(close),1);
            for i = w:numel(close)
                seg = r(i-w+1:i);
                seg = seg(isfinite(seg));
                if numel(seg) >= w-1
                    out(i) = sqrt(sum(seg.^2));   % summed squared returns
                end
            end

        case 'nwslope'
            y = varargin{1}; X = varargin{2}; lag = varargin{3};
            out = nw_tstat(y, X, lag);

        otherwise
            error('stats_tools: unknown op "%s"', op);
    end
end

function r = corr_simple(x, y)
    x = x(:); y = y(:);
    m = isfinite(x) & isfinite(y);
    x = x(m); y = y(m);
    if numel(x) < 3, r = NaN; return; end
    x = x - mean(x); y = y - mean(y);
    d = sqrt(sum(x.^2)*sum(y.^2));
    if d == 0, r = NaN; else, r = sum(x.*y)/d; end
end

function rk = rankcols(x)
    x = x(:);
    m = isfinite(x);
    rk = nan(size(x));
    if ~any(m), return; end
    [~, ord] = sort(x(m));
    v = nan(numel(ord),1);
    v(ord) = (1:numel(ord))';
    % average ties
    [ux,~,ic] = unique(x(m));
    for k = 1:numel(ux)
        sel = (ic == k);
        v(sel) = mean(v(sel));
    end
    rk(m) = v;
end

function r = residualise(x, Z)
    x = x(:);
    n = numel(x);
    Z = Z(~any(~isfinite(Z),2), :);
    A = [ones(n,1), Z];
    m = isfinite(x) & all(isfinite(A),2);
    if sum(m) < n
        A = A(m,:); xx = x(m);
    else
        xx = x;
    end
    b  = A \ xx;
    r  = nan(n,1);
    r(all(isfinite([ones(n,1), Z]),2)) = xx - A*b;
end

function st = nw_tstat(y, X, lag)
% OLS with Newey-West HAC standard errors.
    y = y(:);
    n = numel(y);
    A = [ones(n,1), X];
    m = isfinite(y) & all(isfinite(A),2);
    y = y(m); A = A(m,:);
    n = numel(y);
    if n <= size(A,2), st = [NaN NaN]; return; end

    b   = A \ y;
    u   = y - A*b;
    ATA = A'*A;
    S   = zeros(size(A,2));
    for l = 0:lag
        w = 1 - l/(lag+1);
        if l == 0
            G = (A.*u)' * (A.*u);
        else
            G = zeros(size(A,2));
            for t = l+1:n
                G = G + (A(t,:)'*u(t)) * (A(t-l,:)*u(t-l));
            end
            G = G + G';
        end
        S = S + w*G;
    end
    ATAinv = inv(ATA);
    V = ATAinv * S * ATAinv * (n/(n-size(A,2)));
    se = sqrt(diag(V));
    j  = size(A,2);
    st = [b(j), b(j)/se(j)];
end
