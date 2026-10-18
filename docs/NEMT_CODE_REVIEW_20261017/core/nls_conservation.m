function c = nls_conservation(psi, p)
% nls_conservation  Invariants of the noise-free NLS.
%
%       mass   M = integral |psi|^2 dx
%       energy H = integral ( alpha*|dpsi/dx|^2 - (beta/2)*|psi|^4 ) dx
%
%   H is the Hamiltonian: with this sign convention i*psi_t = dH/dpsi*,
%   hence both M and H are conserved by the exact flow. Any drift observed
%   numerically is discretisation error, not physics.
%
%   The spatial derivative is evaluated spectrally so that it does not add
%   its own O(dx^2) error on top of the time integrator error we want to
%   measure in exp1.

    psi = psi(:);
    n   = numel(psi);
    g   = nls_grid(n, p.dx);

    dpsi = ifft(1i * g.omega .* fft(psi));

    M = sum(abs(psi).^2) * p.dx;
    H = sum( p.alpha*(abs(dpsi).^2) - (p.beta/2)*(abs(psi).^4) ) * p.dx;

    c.mass   = M;
    c.energy = H;
end
