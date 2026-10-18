function psi = nls_euler(psi, p, noiseTable)
% nls_euler  Explicit (forward) Euler evolution of the NLS equation.
%
%       dpsi/dt = i*(alpha*laplacian(psi) + beta*|psi|^2*psi) - i*eta
%
%   Periodic boundary conditions, second order central difference for the
%   Laplacian. This is the scheme currently used by the legacy
%   matlab/nemt_core/NEMTSimulator.m in the main repository.
%
%   Explicit Euler is NOT unitary: it drifts the mass invariant and is
%   only conditionally stable. exp1 quantifies both.

    psi = psi(:);
    n   = numel(psi);
    dx2 = p.dx^2;

    for s = 1:p.steps
        lap = ([psi(2:end); psi(1)] - 2*psi + [psi(end); psi(1:end-1)]) / dx2;
        rhs = 1i * (p.alpha*lap + p.beta*(abs(psi).^2 .* psi));
        psi = psi + p.dt * rhs;

        if p.eta > 0
            if nargin >= 3 && ~isempty(noiseTable)
                psi = psi + noiseTable(:, s);
            else
                sc = p.eta * sqrt(p.dt);
                psi = psi + complex(sc*randn(n,1), sc*randn(n,1));
            end
        end

        if p.useAmpClip
            a = abs(psi);
            over = a > p.clipAmp;
            if any(over)
                psi(over) = p.clipAmp * exp(1i*angle(psi(over)));
            end
        end
    end
end
