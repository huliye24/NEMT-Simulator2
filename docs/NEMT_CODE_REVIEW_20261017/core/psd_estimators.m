function P = psd_estimators(x, method, nfft, win)
% psd_estimators  One-sided power spectral density estimates.
%
%   P = psd_estimators(x, method)
%   P = psd_estimators(x, method, nfft)
%   P = psd_estimators(x, method, nfft, win)
%
%   method : 'periodogram' | 'welch' | 'sine'
%   nfft   : FFT length (power of two); default next power of two
%   win    : segment/taper length for Welch and sine estimates. Default
%            min(nfft, numel(x)). Supplying a shorter win makes both
%            estimators average over more segments on a longer signal. A
%            zero-padded FFT keeps the frequency grid comparable.
%
%   All three return a column of length nfft/2+1 and are scaled so that
%   they stay comparable: P_k = |X_k|^2 / N^2 as in spectral_width.m.
%
%   'periodogram' is what the reference implementation uses. It is an
%   inconsistent estimator: its variance does not decrease with N. The
%   other two exist so that exp3 can ask whether any conclusion about
%   spectral width survives a better estimator.
%
%   'sine' uses Riedel-Sidorenko sine tapers, a toolbox-free stand-in for
%   multitaper. K = 3 tapers is the usual compromise.

    if nargin < 2 || isempty(method), method = 'periodogram'; end
    x = x(:);
    if nargin < 3 || isempty(nfft)
        nfft = 2^nextpow2(max(numel(x), 2));
    end
    if 2^nextpow2(nfft) ~= nfft
        error('psd_estimators: nfft must be a power of two');
    end
    if nargin < 4 || isempty(win)
        win = min(nfft, numel(x));
    end
    win = min([win, numel(x), nfft]);
    if win < 8
        P = oneSided(x, nfft);
        return;
    end

    switch lower(method)
        case 'periodogram'
            P = oneSided(x, nfft);

        case 'welch'
            n    = numel(x);
            hop  = max(1, floor(win/2));
            w    = hamming(win, 'periodic');
            U    = (w'*w)/win;                 % window power correction
            starts = 1:hop:(n-win+1);
            if isempty(starts), starts = 1; end
            acc  = zeros(nfft/2+1, 1);
            for s = starts
                seg = x(s:s+win-1);
                seg = seg - mean(seg);         % detrend each segment
                acc = acc + oneSided(seg .* w, nfft);
            end
            P = acc / (numel(starts) * U);

        case 'sine'
            K = 3;
            acc = zeros(nfft/2+1, 1);
            seg0 = x(end-win+1:end);
            seg0 = seg0 - mean(seg0);
            for k = 1:K
                t = (1:win)';
                v = sqrt(2/(win+1)) * sin(pi*k*t/(win+1));   % sine taper
                acc = acc + oneSided(seg0 .* v, nfft);
            end
            P = acc / K;

        otherwise
            error('psd_estimators: unknown method "%s"', method);
    end
end

function P = oneSided(x, nfft)
    n = numel(x);
    z = zeros(nfft, 1);
    m = min(n, nfft);
    z(1:m) = x(end-m+1:end);
    X = fft(z);
    P = (abs(X(1:nfft/2+1)).^2) / (nfft*nfft);
end
