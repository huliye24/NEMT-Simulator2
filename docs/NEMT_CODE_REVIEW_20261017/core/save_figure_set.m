function save_figure_set(fig, outDir, baseName)
% save_figure_set  Export one figure as PNG, PDF, SVG and FIG.
%
%   save_figure_set(fig, outDir, baseName)
%
%   PNG is rendered at 200 dpi for quick inspection; PDF/SVG stay vector
%   where the renderer supports it. The editable .fig is kept so axes can
%   be revised without rerunning an experiment.

    if nargin < 3
        error('save_figure_set: needs fig, outDir, baseName');
    end
    if ~exist(outDir, 'dir')
        mkdir(outDir);
    end

    pngPath = fullfile(outDir, [baseName '.png']);
    pdfPath = fullfile(outDir, [baseName '.pdf']);
    svgPath = fullfile(outDir, [baseName '.svg']);
    figPath = fullfile(outDir, [baseName '.fig']);

    try
        exportgraphics(fig, pngPath, 'Resolution', 200, 'BackgroundColor', 'white');
    catch
        print(fig, '-dpng', '-r200', pngPath);
    end
    try
        exportgraphics(fig, pdfPath, 'ContentType', 'vector', 'BackgroundColor', 'white');
    catch
        print(fig, '-dpdf', pdfPath);
    end
    try
        exportgraphics(fig, svgPath, 'ContentType', 'vector', 'BackgroundColor', 'white');
    catch
        print(fig, '-dsvg', svgPath);
    end
    try
        savefig(fig, figPath);
    catch
        % The raster and vector files above are the primary deliverables.
    end
end
