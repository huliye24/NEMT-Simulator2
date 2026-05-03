%% NEMT_SaveFigure - 自动保存图表到分类文件夹
% 输入: category (分类), name (文件名)
% 用法: 
%   NEMT_SaveFigure('01_price', 'candlestick')
%   NEMT_SaveFigure('03_volatility', 'rolling_vol')
%   NEMT_SaveFigure('06_hurst', 'rs_analysis')

function NEMT_SaveFigure(category, name)
%% 配置
baseDir = fileparts(fileparts(mfilename('fullpath')));  % 上两级目录
saveDir = fullfile(baseDir, 'results', 'plots', category);
filename = sprintf('%s_%s_%s.png', ...
    datestr(now,'yyyymmdd'), ...
    name, ...
    category);

%% 创建目录
if ~exist(saveDir, 'dir')
    mkdir(saveDir);
    fprintf('创建目录: %s\n', saveDir);
end

%% 保存
savePath = fullfile(saveDir, filename);
saveas(gcf, savePath);
fprintf('✓ 已保存: %s\n', savePath);

%% 复制到figures/dashboard
if contains(category, 'dashboard')
    figDir = fullfile(baseDir, 'results', 'figures', 'dashboard');
    if ~exist(figDir, 'dir'), mkdir(figDir); end
    copyfile(savePath, fullfile(figDir, filename));
end
end
