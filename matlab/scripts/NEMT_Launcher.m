%% NEMT_Launcher - 分析启动器
% 运行此脚本可查看所有分析选项

clc; clear;
addpath(genpath(fileparts(mfilename('fullpath'))));

fprintf('\n');
fprintf('┌─────────────────────────────────────────────────────────────────────┐\n');
fprintf('│                   NEMT 数据分析平台                                 │\n');
fprintf('│                   Bitcoin/USDT 1H 数据分析                          │\n');
fprintf('└─────────────────────────────────────────────────────────────────────┘\n');
fprintf('\n');

% 检查数据文件
dataFiles = {
    'BTC_1h.mat', ...
    'BTC_1h.csv', ...
    '..\matlab_data\BTC_1h.mat', ...
    '..\matlab_data\BTC_1h.csv'
};
dataFound = false;
dataFile = '';

for i = 1:length(dataFiles)
    if exist(dataFiles{i}, 'file')
        dataFound = true;
        dataFile = dataFiles{i};
        break;
    end
end

if ~dataFound
    fprintf('  ⚠ 未找到数据文件!\n');
    fprintf('  请先在Python中运行以下命令获取数据:\n\n');
    fprintf('  cd E:\\NEMT Simulator\n');
    fprintf('  python -m binance_fetcher BTC -i 1h -d 30\n\n');
    return;
end

fprintf('  ✓ 发现数据文件: %s\n\n', dataFile);

% 显示菜单
fprintf('  请选择分析模块:\n\n');
fprintf('  ┌────┬──────────────────────────────────────────────┐\n');
fprintf('  │ 1  │ 综合仪表盘 (Dashboard)                       │\n');
fprintf('  │    │   - 一键生成所有核心图表                      │\n');
fprintf('  ├────┼──────────────────────────────────────────────┤\n');
fprintf('  │ 2  │ 主分析 (MainAnalysis)                        │\n');
fprintf('  │    │   - K线图、收益率分析、波动率聚类             │\n');
fprintf('  ├────┼──────────────────────────────────────────────┤\n');
fprintf('  │ 3  │ Hurst指数分析 (HurstAnalysis)                 │\n');
fprintf('  │    │   - 长记忆性、分形特性、R/S分析               │\n');
fprintf('  ├────┼──────────────────────────────────────────────┤\n');
fprintf('  │ 4  │ 波动率聚类 (VolatilityClustering)             │\n');
fprintf('  │    │   - ARCH效应、自相关、波动率预测              │\n');
fprintf('  ├────┼──────────────────────────────────────────────┤\n');
fprintf('  │ 5  │ 多尺度分析 (MultiScaleAnalysis)              │\n');
fprintf('  │    │   - 多时间尺度相关性、功率谱、Granger因果    │\n');
fprintf('  ├────┼──────────────────────────────────────────────┤\n');
fprintf('  │ 6  │ 全部运行 (Run All)                           │\n');
fprintf('  │    │   - 运行所有分析模块                          │\n');
fprintf('  ├────┼────────────────────────────────────��─────────┤\n');
fprintf('  │ 7  │ 数据信息 (DataInfo)                          │\n');
fprintf('  │    │   - 显示当前数据的基本统计信息                │\n');
fprintf('  └────┴──────────────────────────────────────────────┘\n');
fprintf('\n');

choice = input('请输入选择 (1-7): ');

switch choice
    case 1
        fprintf('\n启动综合仪表盘...\n');
        NEMT_Dashboard;
    case 2
        fprintf('\n启动主分析...\n');
        NEMT_MainAnalysis;
    case 3
        fprintf('\n启动Hurst指数分析...\n');
        NEMT_HurstAnalysis;
    case 4
        fprintf('\n启动波动率聚类分析...\n');
        NEMT_VolatilityClustering;
    case 5
        fprintf('\n启动多尺度分析...\n');
        NEMT_MultiScaleAnalysis;
    case 6
        fprintf('\n运行全部分析...\n\n');
        fprintf('>>> 运行综合仪表盘...\n');
        NEMT_Dashboard;
        fprintf('\n>>> 运行主分析...\n');
        NEMT_MainAnalysis;
        fprintf('\n>>> 运行Hurst指数分析...\n');
        NEMT_HurstAnalysis;
        fprintf('\n>>> 运行波动率聚类分析...\n');
        NEMT_VolatilityClustering;
        fprintf('\n>>> 运行多尺度分析...\n');
        NEMT_MultiScaleAnalysis;
        fprintf('\n✓ 全部分析完成！\n');
    case 7
        fprintf('\n显示数据信息...\n');
        if exist('BTC_1h.mat', 'file')
            raw = load('BTC_1h.mat');
        else
            T = readtable('BTC_1h.csv');
            raw.timestamp = datetime(T.timestamp);
            raw.close = T.close;
            raw.open = T.open;
            raw.high = T.high;
            raw.low = T.low;
            raw.volume = T.volume;
        end
        
        fprintf('\n  数据文件: %s\n', dataFile);
        fprintf('  时间范围: %s ~ %s\n', ...
            datestr(raw.timestamp(1)), datestr(raw.timestamp(end)));
        fprintf('  数据点数: %d\n', length(raw.close));
        fprintf('  价格范围: %.2f ~ %.2f\n', min(raw.low), max(raw.high));
        fprintf('  成交量范围: %.2f ~ %.2f\n', min(raw.volume), max(raw.volume));
        
        returns = diff(log(raw.close)) * 100;
        fprintf('\n  收益率统计:\n');
        fprintf('    均值: %.4f%%\n', mean(returns));
        fprintf('    标准差: %.4f%%\n', std(returns));
        fprintf('    偏度: %.4f\n', skewness(returns));
        fprintf('    峰度: %.4f\n', kurtosis(returns));
    otherwise
        fprintf('无效选择!\n');
end