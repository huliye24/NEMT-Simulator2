%% NEMT_FullAnalysis - 完整分析流程
% 运行全部分析并生成报告
%
% 使用方法:
%   1. 导入 .mat 文件
%   2. 运行: NEMT_FullAnalysis

function NEMT_FullAnalysis()
fprintf('\n');
fprintf('╔═══════════════════════════════════════════════════════════════╗\n');
fprintf('║                 NEMT 完整分析流程                            ║\n');
fprintf('╚═══════════════════════════════════════════════════════════════╝\n');

%% 1. 快速图表
fprintf('\n[1/5] 生成K线图...\n');
try
    NEMT_QuickPlot;
    NEMT_SaveAll;
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

%% 2. 主分析
fprintf('\n[2/5] 主分析程序...\n');
try
    NEMT_MainAnalysis;
    NEMT_SaveAll;
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

%% 3. 仪表盘
fprintf('\n[3/5] 生成仪表盘...\n');
try
    NEMT_Dashboard;
    NEMT_SaveAll;
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

%% 4. 波动率分析
fprintf('\n[4/5] 波动率聚类分析...\n');
try
    NEMT_VolatilityClustering;
    NEMT_SaveAll;
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

%% 5. 多尺度分析
fprintf('\n[5/5] 多尺度相关性分析...\n');
try
    NEMT_MultiScaleAnalysis;
    NEMT_SaveAll;
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

%% 6. Hurst分析
fprintf('\n[6/5] 分形Hurst分析...\n');
try
    NEMT_HurstAnalysis;
    NEMT_SaveAll;
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

%% 7. 智能报告
fprintf('\n[7/7] 生成智能分析报告...\n');
try
    report = NEMT_IntelligenceReport;
    NEMT_ExportReport(report);
    fprintf('    ✓ 完成\n');
catch ME
    fprintf('    ✗ 跳过: %s\n', ME.message);
end

fprintf('\n');
fprintf('╔═══════════════════════════════════════════════════════════════╗\n');
fprintf('║                    全部分析完成!                              ║\n');
fprintf('╚═══════════════════════════════════════════════════════════════╝\n');

fprintf('\n📁 输出目录:\n');
fprintf('   • results/plots/     - 各类图表\n');
fprintf('   • results/reports/    - Markdown报告\n');
fprintf('\n');
end
