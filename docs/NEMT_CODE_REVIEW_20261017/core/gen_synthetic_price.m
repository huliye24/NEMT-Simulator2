function [close, info] = gen_synthetic_price(n, cfg)
% gen_synthetic_price  Reproducible synthetic close prices.
%
%   [close, info] = gen_synthetic_price(n)
%   [close, info] = gen_synthetic_price(n, cfg)
%
%   cfg fields (all optional):
%     seed      integer        default 20240101
%     mu        drift per bar  default 0.0
%     vol0      starting vol   default 0.01   (per bar)
%     garchA    ARCH term      default 0.05
%     garchB    GARCH term     default 0.90
%     regime    'none' | 'switch'   default 'none'
%     s0        starting price default 100
%
%   The generator deliberately includes volatility clustering (GARCH(1,1))
%   because exp2 and exp3 need a series whose volatility structure is known
%   by construction: if an NLS quantity fails to recover it, the failure
%   belongs to the NLS step, not to the data.
%
%   Deterministic: same seed always gives the same series.

    if nargin < 2, cfg = struct(); end
    if ~isfield(cfg,'seed'),   cfg.seed   = 20240101; end
    if ~isfield(cfg,'mu'),     cfg.mu     = 0.0;      end
    if ~isfield(cfg,'vol0'),   cfg.vol0   = 0.01;     end
    if ~isfield(cfg,'garchA'), cfg.garchA = 0.05;     end
    if ~isfield(cfg,'garchB'), cfg.garchB = 0.90;     end
    if ~isfield(cfg,'regime'), cfg.regime = 'none';   end
    if ~isfield(cfg,'s0'),     cfg.s0     = 100;      end

    rng(cfg.seed);

    omega = (cfg.vol0^2) * max(1 - cfg.garchA - cfg.garchB, 1e-8);

    close = zeros(n,1);
    vol   = zeros(n,1);
    close(1) = cfg.s0;
    vol(1)   = cfg.vol0;

    h = cfg.vol0^2;
    for t = 2:n
        z   = randn;
        sig = sqrt(h);

        if strcmpi(cfg.regime,'switch')
            mu_t = cfg.mu + 0.0004*sin(2*pi*t/2000);
        else
            mu_t = cfg.mu;
        end

        close(t) = close(t-1) * exp(mu_t - 0.5*sig^2 + sig*z);
        vol(t)   = sig;
        h        = omega + cfg.garchA*(sig*z)^2 + cfg.garchB*h;
    end

    info.vol  = vol;
    info.seed = cfg.seed;
    info.cfg  = cfg;
end
