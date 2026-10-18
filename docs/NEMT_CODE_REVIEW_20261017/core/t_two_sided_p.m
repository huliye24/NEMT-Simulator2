function p = t_two_sided_p(t, df)
% t_two_sided_p  Two-sided p-value for a t statistic, base MATLAB only.
    if ~isfinite(t) || df <= 0
        p = NaN; return;
    end
    x = df/(df + t.^2);
    p = betainc(x, df/2, 0.5);
end
