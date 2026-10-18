function varargout = io_tools(op, varargin)
% io_tools  Golden sample generation, CSV writing, tolerance checks.
%
%   io_tools('golden', outDir)          write the golden sample CSVs
%   io_tools('golden', outDir, p)       same, with explicit NEMTParams
%   io_tools('save',   path, header, M) write a numeric matrix as CSV
%   tf = io_tools('close', a, b, tol)   max abs difference below tol?
%
%   WHY THE GOLDEN SAMPLE EXISTS
%   The main repository already contains seven mutually incompatible
%   spectral-width implementations, two of which are outright fake (one is
%   std() of the power array, one returns a random number). Adding a
%   MATLAB branch creates an eighth unless the two sides are pinned to a
%   shared numeric fixture. The theory book asks for exactly this in
%   section 8.5: "MATLAB, CPU reference and GPU implementations should
%   share a fixed golden sample with stated absolute and relative tolerances".
%
%   The fixture is deterministic (eta = 0, fixed seed), so MATLAB and
%   Python must agree to ~1e-12. If they do not, STOP and reconcile before
%   running any experiment.

    switch lower(op)
        case 'golden'
            outDir = varargin{1};
            if numel(varargin) >= 2 && ~isempty(varargin{2})
                p = varargin{2};
            else
                p = NEMTParams();
            end
            writeGolden(outDir, p);

        case 'save'
            path   = varargin{1};
            header = varargin{2};
            M      = varargin{3};
            writeCsv(path, header, M);

        case 'close'
            a = varargin{1}; b = varargin{2}; tol = varargin{3};
            a = a(:); b = b(:);
            n = min(numel(a), numel(b));
            d = max(abs(a(1:n) - b(1:n)));
            varargout{1} = (d <= tol);
            if nargout >= 2, varargout{2} = d; end

        otherwise
            error('io_tools: unknown op "%s"', op);
    end
end

function writeGolden(outDir, p)
    if ~exist(outDir, 'dir'), mkdir(outDir); end

    nBars = 1024;
    [close, ~] = gen_synthetic_price(nBars, struct('seed', p.seed));
    io_tools('save', fullfile(outDir,'golden_close.csv'), ...
             {'bar','close'}, [(1:nBars)', close]);
    [psi_re, psi_im] = construct_psi(close, p, 'logprice_z');

    % A single psi profile at a fixed bar, padded to psi_n_fft.
    i0 = p.psi_window + 300;
    seg_re = psi_re(i0-p.psi_window+1:i0);
    seg_im = psi_im(i0-p.psi_window+1:i0);

    psi0 = nls_pad(seg_re, seg_im, p.psi_n_fft);

    io_tools('save', fullfile(outDir,'golden_psi0.csv'), ...
             {'index','psi0_re','psi0_im'}, ...
             [(1:numel(psi0))', real(psi0), imag(psi0)]);

    % Evolved state, one file per solver.
    solvers = {'ssfm','euler','rk4'};
    for k = 1:numel(solvers)
        ps = nls_evolve(seg_re, seg_im, p, solvers{k});
        io_tools('save', fullfile(outDir, ['golden_psi_' solvers{k} '.csv']), ...
                 {'index','psi_re','psi_im'}, ...
                 [(1:numel(ps))', real(ps), imag(ps)]);
        [W, mu, pw] = spectral_width(ps);
        io_tools('save', fullfile(outDir, ['golden_sw_' solvers{k} '.csv']), ...
                 {'spectral_width','mean_freq'}, [W, mu]);
        if strcmpi(solvers{k},'ssfm')
            io_tools('save', fullfile(outDir,'golden_power.csv'), ...
                     {'k','power'}, [(0:numel(pw)-1)', pw]);
        end
    end

    meta = [p.alpha, p.beta, p.eta, p.dt, p.dx, p.steps, ...
            p.psi_window, p.psi_n_fft, p.momentum_window, p.seed, i0, nBars];
    io_tools('save', fullfile(outDir,'golden_meta.csv'), ...
             {'alpha','beta','eta','dt','dx','steps','psi_window', ...
              'psi_n_fft','momentum_window','seed','bar_index','n_bars'}, meta);

    fprintf('golden sample written to %s\n', outDir);
end

function writeCsv(path, header, M)
    fid = fopen(path, 'w');
    if fid < 0, error('io_tools: cannot write %s', path); end
    fprintf(fid, '%s', header{1});
    for c = 2:numel(header), fprintf(fid, ',%s', header{c}); end
    fprintf(fid, '\n');
    for r = 1:size(M,1)
        fprintf(fid, '%.17g', M(r,1));
        for c = 2:size(M,2), fprintf(fid, ',%.17g', M(r,c)); end
        fprintf(fid, '\n');
    end
    fclose(fid);
end
