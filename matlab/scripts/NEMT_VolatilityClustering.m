%% NEMT_VolatilityClustering - 波动率聚类分析
% 输入: 工作区中的 timestamp, close 或 raw
% 输出: 图表
%
% 使用方法:
%   1. 导入 .mat 文件
%   2. 运行: NEMT_VolatilityClustering

function varargout = NEMT_VolatilityClustering()
%% 获取数据
vars = evalin('base', 'who');

if any(strcmp(vars, 'raw'))
    raw = evalin('base', 'raw');
    close = raw.close(:);
    if isfield(raw, 'timestamp'), timestamp = raw.timestamp(:); end
elseif any(strcmp(vars, 'close'))
    close = evalin('base', 'close');
    close = close(:);
    if any(strcmp(vars, 'timestamp'))
        timestamp = evalin('base', 'timestamp');
        timestamp = timestamp(:);
    end
else
    error('工作区中未找到数据');
end

if ~exist('timestamp', 'var'), timestamp = (1:length(close))'; end

%% 处理时间戳格式
n = length(timestamp);
if timestamp(1) > 700000
    timestamp = datetime(timestamp, 'ConvertFrom', 'posixtime');
elseif timestamp(1) > 70000
    timestamp = datetime(timestamp, 'ConvertFrom', 'excel');
elseif timestamp(1) > 1000
    try
        timestamp = datetime(timestamp, 'ConvertFrom', 'datenum');
    catch
        timestamp = (1:n)';
    end
end

returns = diff(log(close)) * 100;
absReturns = abs(returns);
squaredReturns = returns.^2;

%% 图1: 波动率聚类全景
fig1 = figure('Position', [50, 50, 1500, 900], 'Color', [0.03 0.03 0.08]);
movegui('center');

subplot(4,1,1);
plot(timestamp, close, 'b-', 'LineWidth', 1);
title('价格走势', 'FontSize', 14, 'FontWeight', 'bold');
ylabel('价格');
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

subplot(4,1,2);
volBand = 2 * movstd(returns, 24);
plot(timestamp(2:end), returns, 'g-', 'LineWidth', 0.5);
hold on;
plot(timestamp(2:end), volBand, 'r-', 'LineWidth', 1.5);
plot(timestamp(2:end), -volBand, 'r-', 'LineWidth', 1.5);
title('收益率 ±2σ 波动带', 'FontSize', 14, 'FontWeight', 'bold');
ylabel('收益率 (%)');
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

subplot(4,1,3);
imagesc(timestamp(2:end), 1, absReturns');
set(gca, 'YDir', 'normal', 'CLim', [0, prctile(absReturns, 95)]);
colormap hot;
colorbar;
title('波动率热力图', 'FontSize', 14, 'FontWeight', 'bold');

subplot(4,1,4);
scatter(absReturns(1:end-1), absReturns(2:end), 15, 'filled', 'MarkerFaceAlpha', 0.4);
title('波动率聚类 AR(1)', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('|r_t|');
ylabel('|r_{t+1}|');
grid on; grid minor;

%% 图2: ARCH效应检验
fig2 = figure('Position', [100, 100, 1400, 700], 'Color', [0.03 0.03 0.08]);
movegui('center');

maxLag = min(48, floor(length(returns)/4)-1);

subplot(2,3,1);
acfAbs = zeros(maxLag, 1);
for lag = 1:maxLag
    c = corrcoef(absReturns(1:end-lag), absReturns(lag+1:end));
    acfAbs(lag) = c(1,2);
end
stem(1:maxLag, acfAbs, 'MarkerSize', 3, 'BaseValue', 0);
title('|r_t| 自相关', 'FontSize', 12, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2,3,2);
acfSq = zeros(maxLag, 1);
for lag = 1:maxLag
    c = corrcoef(squaredReturns(1:end-lag), squaredReturns(lag+1:end));
    acfSq(lag) = c(1,2);
end
stem(1:maxLag, acfSq, 'MarkerSize', 3, 'BaseValue', 0);
title('|r_t|² 自相关', 'FontSize', 12, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2,3,3);
acfR2 = zeros(maxLag, 1);
for lag = 1:maxLag
    c = corrcoef(returns(1:end-lag), returns(lag+1:end));
    acfR2(lag) = c(1,2);
end
stem(1:maxLag, acfR2, 'MarkerSize', 3, 'BaseValue', 0);
title('r_t² 自相关', 'FontSize', 12, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2,3,4);
plot(timestamp(2:end), squaredReturns, 'm-', 'LineWidth', 0.5);
hold on;
plot(timestamp(2:end), movmean(squaredReturns, 24), 'r-', 'LineWidth', 2);
title('平方收益率', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('时间');
ylabel('r²');
grid on; grid minor;

subplot(2,3,5);
histogram(absReturns, 50, 'Normalization', 'pdf', 'FaceColor', [0.5 0.8 1], 'EdgeColor', 'none');
hold on;
x = linspace(0, max(absReturns), 100);
try
    params = fitdist(absReturns, 'tLocationScale');
    plot(x, pdf(params, x), 'r-', 'LineWidth', 2);
end
try
    plot(x, pdf(fitdist(absReturns, 'Normal'), x), 'g--', 'LineWidth', 2);
end
title('|r| 分布拟合', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('|r|');
ylabel('密度');
legend('实际', 't分布', '正态');
grid on; grid minor;

subplot(2,3,6);
predVol = sqrt(movvar(returns, 24));
actualVol = movstd(returns, 24);
minLen = min(length(predVol), length(actualVol));
predVol = predVol(1:minLen);
actualVol = actualVol(1:minLen);
scatter(predVol, actualVol, 5, 'filled', 'MarkerFaceAlpha', 0.3);
hold on;
maxVal = max(max(predVol), max(actualVol));
plot([0 maxVal], [0 maxVal], 'r--', 'LineWidth', 2);
title('波动率预测 vs 实际', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('预测');
ylabel('实际');
grid on; grid minor;

%% 统计输出
fprintf('\n┌─────────────────────────────────────────┐\n');
fprintf('│ 波动率聚类分析                            │\n');
fprintf('├─────────────────────────────────────────┤\n');
fprintf('│ 收益率标准差:   %8.4f%%               │\n', std(returns));
fprintf('│ |r|>2σ 比例:    %8.2f%%               │\n', mean(absReturns > 2*std(returns)) * 100);
fprintf('│ AR(1) 系数:    %+8.4f                 │\n', corr(absReturns(1:end-1), absReturns(2:end)));
fprintf('│ 偏度:          %8.4f                 │\n', skewness(returns));
fprintf('│ 峰度:          %8.4f                 │\n', kurtosis(returns));
fprintf('└─────────────────────────────────────────┘\n');

if nargout > 0, varargout{1} = {fig1, fig2}; end
end
