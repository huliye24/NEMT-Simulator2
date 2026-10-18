function psi = nls_rk4(psi, p, noiseTable)
% nls_rk4  Classical fourth order Runge-Kutta evolution of the NLS equation.
%
%   Same spatial discretisation as nls_euler (periodic, central difference)
%   but a much better time integrator. Included in exp1 as a middle ground:
%   RK4 is far more accurate than Euler at the same dt, yet - unlike the
%   split-step scheme - it is still not unitary, so it still leaks mass.

    psi = psi(:);
    n   = numel(psi);
    dx2 = p.dx^2;

    f = @(v) 1i * ( p.alpha*(([v(2:end); v(1)] - 2*v + [v(end); v(1:end-1)])/dx2) ...
                   + p.beta*(abs(v).^2 .* v) );

    for s = 1:p.steps
        k1 = f(psi);
        k2 = f(psi + (p.dt/2)*k1);
        k3 = f(psi + (p.dt/2)*k2);
        k4 = f(psi + p.dt*k3);
        psi = psi + (p.dt/6)*(k1 + 2*k2 + 2*k3 + k4);

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
