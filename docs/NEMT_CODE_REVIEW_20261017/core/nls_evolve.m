function psi = nls_evolve(psi_re, psi_im, p, solver, noiseTable)
% nls_evolve  Pad a psi profile to n_fft and evolve it.
%
%   psi = nls_evolve(psi_re, psi_im, p)
%   psi = nls_evolve(psi_re, psi_im, p, solver)
%   psi = nls_evolve(psi_re, psi_im, p, solver, noiseTable)
%
%   solver : 'ssfm' (default) | 'euler' | 'rk4' | 'none'
%
%   Mirrors nls_evolve() in variables.py: zero-pad to a power of two, then
%   run `steps` iterations of the chosen scheme. With solver='none' the
%   padded profile is returned unchanged, which is what the Python side
%   does when nls_method == 'none'.

    if nargin < 4 || isempty(solver), solver = 'ssfm'; end
    if nargin < 5, noiseTable = []; end

    psi = nls_pad(psi_re, psi_im, p.psi_n_fft);

    if strcmpi(solver, 'none') || p.steps <= 0
        return;
    end

    switch lower(solver)
        case 'ssfm'
            fn = @(v) nls_ssfm(v, p, noiseTable);
        case 'euler'
            fn = @(v) nls_euler(v, p, noiseTable);
        case 'rk4'
            fn = @(v) nls_rk4(v, p, noiseTable);
        otherwise
            error('nls_evolve: unknown solver "%s"', solver);
    end

    % nls_ssfm/euler/rk4 already loop over p.steps internally
    psi = fn(psi);
end
