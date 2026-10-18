function psi = nls_pad(psi_re, psi_im, n_fft)
% nls_pad  Zero-pad a (real,imag) profile pair to length n_fft.
%
%   Reproduces nls_evolve() in variables.py: allocate a zero array of
%   length n_fft, then copy the incoming profile into the first entries.
%   Incoming arrays longer than n_fft are truncated to the LAST n_fft
%   samples (the Python caller does seg_re = seg_re[-n_fft:]).

    if nargin < 2 || isempty(psi_im), psi_im = []; end

    m = numel(psi_re);
    if nargin < 3 || isempty(n_fft)
        n_fft = 2^nextpow2(max(m, 2));
    end
    if 2^nextpow2(n_fft) ~= n_fft
        error('nls_pad: n_fft must be a power of two');
    end

    re = zeros(n_fft, 1);
    im = zeros(n_fft, 1);

    a = min(m, n_fft);
    if a > 0
        re(1:a) = psi_re(end-a+1:end);
    end
    b = min(numel(psi_im), n_fft);
    if b > 0
        im(1:b) = psi_im(end-b+1:end);
    end

    psi = complex(re, im);
end
