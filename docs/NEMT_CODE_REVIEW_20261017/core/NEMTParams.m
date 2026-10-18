classdef NEMTParams
% NEMTParams  Parameters of the NLS market model.
%
%   Governing equation:
%       i*dpsi/dt + alpha*d2psi/dx2 + beta*|psi|^2*psi = eta
%
%   Defaults are deliberately identical to NEMTConfig in
%   nemt_os/services/research/variables.py so that the MATLAB and the
%   Python implementation agree bit-for-bit on the golden sample.
%   NEVER change a default here without regenerating the golden sample
%   (see core/io_tools.m -> golden_sample).
%
%   Notation warning from the theory book (chapter 4.1): psi has two
%   conflicting meanings in the repository. In this lab psi always means
%   the NLS complex amplitude, never the growth-rate momentum indicator.

    properties
        % --- NLS coefficients ---
        alpha (1,1) double = 0.1      % diffusion / liquidity
        beta  (1,1) double = 1.0      % nonlinear feedback / leverage
        eta   (1,1) double = 0.0      % external noise strength (0 = deterministic)

        % --- discretisation ---
        dt    (1,1) double = 0.01     % time step
        dx    (1,1) double = 1.0      % space step
        steps (1,1) double = 20       % number of evolution steps

        % --- reproducibility ---
        seed  (1,1) double = 20240101

        % --- psi construction (matched to Python NEMTConfig) ---
        psi_window      (1,1) double = 128   % rolling z-score window, real part
        psi_n_fft       (1,1) double = 128   % FFT size, must be power of two
        momentum_window (1,1) double = 24    % rolling z-score window, imag part

        % --- safety valves (off by default; see exp1) ---
        useAmpClip (1,1) logical = false
        clipAmp    (1,1) double  = 10.0
    end

    methods
        function obj = NEMTParams(varargin)
            % NEMTParams('alpha',0.2,'steps',50,...)  name-value override
            if nargin == 0, return; end
            if mod(nargin,2) ~= 0
                error('NEMTParams: expects name-value pairs');
            end
            for i = 1:2:nargin
                obj.(varargin{i}) = varargin{i+1};
            end
        end

        function s = describe(obj)
            s = sprintf(['alpha=%.4g beta=%.4g eta=%.4g dt=%.4g dx=%.4g ' ...
                         'steps=%d psi_window=%d n_fft=%d seed=%d'], ...
                        obj.alpha, obj.beta, obj.eta, obj.dt, obj.dx, ...
                        obj.steps, obj.psi_window, obj.psi_n_fft, obj.seed);
        end
    end
end
