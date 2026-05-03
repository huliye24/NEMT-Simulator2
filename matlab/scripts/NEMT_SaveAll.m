%% NEMT_SaveAll - 一键保存所有分析图表
% 运行完所有分析后调用此脚本，自动保存所有打开的图表

function NEMT_SaveAll()
baseDir = fileparts(fileparts(mfilename('fullpath')));
figs = findobj(0, 'Type', 'figure');

for i = 1:length(figs)
    fig = figs(i);
    figName = get(fig, 'Name');
    
    if isempty(figName) || strcmp(figName, 'Figure 1')
        figName = sprintf('figure_%d', i);
    end
    
    % 按图表内容分类
    category = classifyFigure(fig);
    saveDir = fullfile(baseDir, 'results', 'plots', category);
    
    if ~exist(saveDir, 'dir')
        mkdir(saveDir);
    end
    
    filename = sprintf('%s_%s_%s.png', ...
        datestr(now,'yyyymmdd'), ...
        figName, ...
        category);
    
    savePath = fullfile(saveDir, filename);
    saveas(fig, savePath);
    fprintf('✓ [%d/%d] 已保存: %s\n', i, length(figs), filename);
end

fprintf('\n全部 %d 张图表已保存到 results/plots/\n', length(figs));
end

function category = classifyFigure(fig)
title = get(fig, 'Name');
if ~isempty(title)
    if contains(lower(title), 'price') || contains(lower(title), 'k线')
        category = '01_price';
    elseif contains(lower(title), 'volatility') || contains(lower(title), '波动')
        category = '03_volatility';
    elseif contains(lower(title), 'hurst')
        category = '06_hurst';
    elseif contains(lower(title), 'distribution') || contains(lower(title), 'q-q')
        category = '04_distribution';
    elseif contains(lower(title), 'correlation') || contains(lower(title), '相关')
        category = '05_correlation';
    else
        category = '00_misc';
    end
else
    category = '00_misc';
end
end
