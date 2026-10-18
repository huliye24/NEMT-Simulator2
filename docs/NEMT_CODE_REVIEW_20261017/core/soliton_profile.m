function [psi, x] = soliton_profile(N, dx, alpha, beta, A)
% soliton_profile  Exact t=0 cubic-NLS soliton on a periodic grid.
%
%   [psi, x] = soliton_profile(N, dx, alpha, beta, A)
%
%   psi(x,0) = A * sech(A*sqrt(beta/(2*alpha)) * x)
%
%   The analytic solution only rotates its phase; |psi| must remain
%   invariant. The grid spans N*dx with the profile centred at x=0.

    if nargin < 5 || isempty(A), A = 1.0; end
    x = ((0:N-1)' - N/2) * dx;
    kappa = A * sqrt(beta / (2*max(alpha, 1e-12)));
    psi = A ./ cosh(kappa * x) + 0i;
end
