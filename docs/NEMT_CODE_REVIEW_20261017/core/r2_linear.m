function [r2, sse, sst] = r2_linear(y, yhat)
% r2_linear  Coefficient of determination (no toolbox).
    y = y(:); yhat = yhat(:);
    m = isfinite(y) & isfinite(yhat);
    y = y(m); yhat = yhat(m);
    if isempty(y)
        r2 = NaN; sse = NaN; sst = NaN; return;
    end
    e = y - yhat;
    sse = sum(e.^2);
    sst = sum((y - mean(y)).^2);
    if sst <= 0
        r2 = NaN;
    else
        r2 = 1 - sse/sst;
    end
end
