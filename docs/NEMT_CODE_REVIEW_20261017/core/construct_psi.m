function [psi_re, psi_im] = construct_psi(close, p, method)
% construct_psi  Build the NLS complex amplitude from a price series.
%
%   [re, im] = construct_psi(close, p, method)
%
%   method:
%     'logprice_z'  real = rolling z-score of log price   (REFERENCE)
%                   imag = rolling z-score of log return
%                   This is exactly what variables.py builds and is the
%                   baseline every other method is compared against in exp3.
%
%     'price_z'     real = rolling z-score of raw price
%                   imag = rolling z-score of log return
%                   Tests whether the log transform matters at all.
%
%     'return_z'    real = rolling z-score of log return
%                   imag = rolling z-score of log return (detrended twice)
%                   Tests whether the level or the increment should be psi.
%
%     'zero_imag'   real = rolling z-score of log price
%                   imag = 0
%                   The legacy MATLAB / early Python construction. exp3
%                   checks the claim that a zero imaginary part kills the
%                   phase dynamics of the NLS.
%
%     'analytic'    real = rolling z-score of log price
%                   imag = Hilbert transform of that same series
%                   A genuine quadrature pair, i.e. a true analytic signal.
%
%   All rolling statistics are CAUSAL: the value at bar i uses only bars
%   (i-w+1 .. i). Sample standard deviation (divide by w-1), matching
%   variables.py. Leading bars with insufficient history are NaN.

    if nargin < 3 || isempty(method), method = 'logprice_z'; end
    close = close(:);
    n     = numel(close);

    logp = nan(n,1);
    ok   = close > 0;
    logp(ok) = log(close(ok));

    rets = nan(n,1);
    rets(2:end) = logp(2:end) - logp(1:end-1);

    w  = p.psi_window;
    mw = p.momentum_window;

    z_re = rollingZ(logp, w);
    z_rt = rollingZ(rets, mw);

    switch lower(method)
        case 'logprice_z'
            psi_re = z_re;
            psi_im = z_rt;

        case 'price_z'
            psi_re = rollingZ(close, w);
            psi_im = z_rt;

        case 'return_z'
            psi_re = z_rt;
            psi_im = rollingZ(rets - movmean_nan(rets, w), mw);

        case 'zero_imag'
            psi_re = z_re;
            psi_im = zeros(n,1);

        case 'analytic'
            psi_re = z_re;
            psi_im = nan(n,1);
            v = z_re;
            v(~isfinite(v)) = 0;
            h = imag(hilbert_nodetool(v));
            psi_im(:) = h;

        otherwise
            error('construct_psi: unknown method "%s"', method);
    end
end

function z = rollingZ(x, w)
    n = numel(x);
    z = nan(n,1);
    for i = w:n
        seg = x(i-w+1:i);
        if any(~isfinite(seg)), continue; end
        m  = mean(seg);
        sd = sqrt( sum((seg-m).^2) / (w-1) );
        if sd <= 1e-15
            z(i) = 0;
        else
            z(i) = (x(i) - m) / sd;
        end
    end
end

function m = movmean_nan(x, w)
    n = numel(x);
    m = nan(n,1);
    for i = w:n
        seg = x(i-w+1:i);
        seg = seg(isfinite(seg));
        if ~isempty(seg), m(i) = mean(seg); end
    end
end

function z = hilbert_nodetool(x)
% Analytic signal without the Signal Processing Toolbox.
% One-sided spectrum multiplier: DC and Nyquist keep weight 1, the
% positive frequencies keep weight 2, negative frequencies are zeroed.
    x = x(:);
    N = numel(x);
    X = fft(x);
    H = zeros(N,1);
    H(1) = 1;
    if mod(N,2) == 0
        H(2:N/2)     = 2;
        H(N/2+1)     = 1;
    else
        H(2:(N+1)/2) = 2;
    end
    z = ifft(X .* H);
end
