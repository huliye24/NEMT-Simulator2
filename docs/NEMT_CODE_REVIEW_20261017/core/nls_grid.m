function g = nls_grid(n, dx)
% nls_grid  Angular frequency vector matching the Python implementation.
%
%   Python (variables.py::_nls_step_ssfm) uses
%       kk    = k if k <= n/2 else k - n
%       omega = 2*pi*kk/n
%   with dx implicitly 1. We reproduce exactly that ordering, including
%   the +n/2 Nyquist bin, because omega^2 makes the sign irrelevant while
%   the bin position does not.
%
%   g.omega  (n x 1) angular frequency
%   g.k      (n x 1) integer wavenumber, Nyquist stored as +n/2

    if n <= 0 || mod(n,1) ~= 0
        error('nls_grid: n must be a positive integer');
    end
    if nargin < 2 || isempty(dx), dx = 1.0; end

    k = (0:n-1)';
    k(k > n/2) = k(k > n/2) - n;
    g.k      = k;
    g.omega  = 2*pi*k/(n*dx);
    g.n      = n;
    g.dx     = dx;
end
