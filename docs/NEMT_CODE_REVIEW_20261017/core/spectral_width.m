function [W, mu, power] = spectral_width(psi)
% spectral_width  Power-weighted second moment of the spectrum.
%
%   Port of spectral_width_from_power() in signal_math.py, bit-for-bit
%   wherever floating point allows. The Python side takes the REAL PART of
%   the evolved psi and computes a single-sided periodogram:
%
%       X     = fft(real(psi))
%       P_k   = |X_k|^2 / N^2            k = 0 .. N/2
%       f_k   = k / N                    (Nyquist = 0.5)
%       w_k   = P_k / sum(P)
%       mu    = sum w_k f_k
%       W     = sqrt( sum w_k (f_k - mu)^2 )
%
%   Two deliberate choices, both inherited from the Python reference and
%   both recorded here because exp3 tests whether they matter:
%     (a) only the real part of psi enters the spectrum;
%     (b) the weights are normalised over the positive half only.
%
%   Historical warning: several modules in the main repository compute
%   "spectral width" as std(power_array), which contains no frequency axis
%   at all. That is not a spectral width. Do not reintroduce it.

    x = real(psi(:));
    N = numel(x);
    if N < 2
        W = 0; mu = 0; power = [];
        return;
    end

    X     = fft(x);
    half  = N/2;
    power = (abs(X(1:half+1)).^2) / (N*N);
    total = sum(power);

    if total <= 1e-300
        W = 0; mu = 0;
        return;
    end

    f  = (0:half)' / N;
    w  = power / total;
    mu = sum(w .* f);
    W  = sqrt( sum(w .* (f - mu).^2) );
end
