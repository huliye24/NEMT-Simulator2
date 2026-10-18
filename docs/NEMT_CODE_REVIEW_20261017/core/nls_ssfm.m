function psi = nls_ssfm(psi, p, noiseTable)
% nls_ssfm  Split-step Fourier evolution of the NLS equation.
%
%       i*dpsi/dt + alpha*d2psi/dx2 + beta*|psi|^2*psi = eta
%
%   Lie splitting, ordered exactly as the Python reference
%   (variables.py::_nls_step_ssfm):
%       1) nonlinear phase      psi *= exp(i*beta*|psi|^2*dt)
%       2) linear dispersion    psih *= exp(-i*alpha*omega^2*dt)
%       3) additive noise       psi += N(0, eta*sqrt(dt)) on real and imag
%
%   Both sub-steps are unitary, so mass |psi|^2 is conserved to machine
%   precision. Energy is conserved only to O(dt) because the splitting is
%   first order. See exp1 for the quantitative statement.
%
%   noiseTable : optional (n x steps) complex array. When supplied it is
%                used instead of randn so that MATLAB and Python can be
%                forced to consume identical realisations. The table must
%                already contain the sqrt(dt) scaling.

    psi = psi(:);
    n   = numel(psi);
    g   = nls_grid(n, p.dx);

    linFactor = exp(-1i * p.alpha * (g.omega.^2) * p.dt);

    for s = 1:p.steps
        % 1) nonlinear sub-step: |psi|^2 invariant => exact phase rotation
        psi = psi .* exp(1i * p.beta * (abs(psi).^2) * p.dt);

        % 2) linear sub-step in Fourier space
        if p.alpha ~= 0
            psi = ifft(linFactor .* fft(psi));
        end

        % 3) stochastic forcing
        if p.eta > 0
            if nargin >= 3 && ~isempty(noiseTable)
                psi = psi + noiseTable(:, s);
            else
                sc = p.eta * sqrt(p.dt);
                psi = psi + complex(sc*randn(n,1), sc*randn(n,1));
            end
        end

        % safety valve (off by default; exp1 measures what it hides)
        if p.useAmpClip
            a = abs(psi);
            over = a > p.clipAmp;
            if any(over)
                psi(over) = p.clipAmp * exp(1i*angle(psi(over)));
            end
        end
    end
end
