%% NEMT_Dashboard - 综合分析仪表盘
% 输入: 工作区中的 timestamp, open, high, low, close, volume 或 raw
% 输出: 综合图表
%
% 使用方法:
%   1. 导入 .mat 文件: load('E:\NEMT Simulator\matlab_data\BTC_1h.mat')
%   2. 运行: NEMT_Dashboard

function fig = NEMT_Dashboard()
%% 获取数据
vars = evalin('base', 'who');

if any(strcmp(vars, 'raw'))
    raw = evalin('base', 'raw');
    timestamp = raw.timestamp(:);
    open = raw.open(:);
    high = raw.high(:);
    low = raw.low(:);
    close = raw.close(:);
    volume = raw.volume(:);
elseif any(strcmp(vars, 'close'))
    if any(strcmp(vars, 'timestamp')), timestamp = evalin('base', 'timestamp'); end
    if any(strcmp(vars, 'open')), open = evalin('base', 'open'); end
    if any(strcmp(vars, 'high')), high = evalin('base', 'high'); end
    if any(strcmp(vars, 'low')), low = evalin('base', 'low'); end
    close = evalin('base', 'close');
    if any(strcmp(vars, 'volume')), volume = evalin('base', 'volume'); end
    
    timestamp = timestamp(:);
    open = open(:);
    high = high(:);
    low = low(:);
    close = close(:);
    volume = volume(:);
else
    error('工作区中未找到数据');
end

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
cumRet = cumsum(returns);
absReturns = abs(returns);

%% 仪表盘布局
fig = figure('Position', [50, 50, 1800, 1000], 'Color', [0.02 0.02 0.05]);
movegui('center');

annotation('textbox', [0.3, 0.93, 0.4, 0.05], 'String', 'BTC/USDT 综合分析仪表盘', ...
    'FontSize', 20, 'FontWeight', 'bold', 'Color', [0.3 0.9 1], ...
    'HorizontalAlignment', 'center', 'BackgroundColor', 'none', 'EdgeColor', 'none');

%% 1. 价格走势
subplot(3, 4, [1 5]);
plot(timestamp, close, 'b-', 'LineWidth', 1);
title('价格走势', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('价格 (USDT)');
grid on; grid minor;
set(gca, 'Color', [0.05 0.05 0.1], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

%% 2. 收益率分布
subplot(3, 4, [2 6]);
histogram(returns, 60, 'Normalization', 'pdf', 'FaceColor', [0.2 0.8 0.5], 'EdgeColor', 'none');
hold on;
x = linspace(min(returns), max(returns), 100);
plot(x, normpdf(x, mean(returns), std(returns)), 'r-', 'LineWidth', 2);
title('收益率分布', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('收益率 (%)');
ylabel('密度');
grid on; grid minor;

%% 3. 累计收益
subplot(3, 4, 3);
plot(timestamp(2:end), cumRet, 'g-', 'LineWidth', 1.5);
title('累计收益率', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('累计 (%)');
grid on; grid minor;
set(gca, 'Color', [0.05 0.05 0.1], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

%% 4. 波动率热力
subplot(3, 4, 4);
imagesc(timestamp(2:end), 1, absReturns');
set(gca, 'YDir', 'normal', 'CLim', [0, prctile(absReturns, 98)]);
colormap hot;
colorbar;
title('波动率热力', 'FontSize', 12, 'FontWeight', 'bold');
set(gca, 'XTickLabel', '');

%% 5. 自相关
subplot(3, 4, 8);
maxLag = min(48, floor(length(returns)/4)-1);
acfVals = zeros(maxLag, 1);
for lag = 1:maxLag
    c = corrcoef(returns(1:end-lag), returns(lag+1:end));
    acfVals(lag) = c(1,2);
end
stem(1:maxLag, acfVals, 'MarkerSize', 3, 'BaseValue', -0.3);
hold on;
plot([1 maxLag], 1.96/sqrt(length(returns))*[1 1], 'r--');
plot([1 maxLag], -1.96/sqrt(length(returns))*[1 1], 'r--');
title('ACF', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('滞后');
grid on; grid minor;

%% 6. Q-Q图
subplot(3, 4, 9);
qqplot(returns);
title('Q-Q图', 'FontSize', 12, 'FontWeight', 'bold');
grid on; grid minor;

%% 7. 滚动波动率
subplot(3, 4, 10);
rollingVol = movstd(returns, 24) * sqrt(24) * 100;
plot(timestamp(2:end), rollingVol, 'm-', 'LineWidth', 1);
title('24H滚动波动率', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('年化 (%)');
grid on; grid minor;
set(gca, 'Color', [0.05 0.05 0.1], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

%% 8. 波动率聚类
subplot(3, 4, 11);
scatter(absReturns(1:end-1), absReturns(2:end), 10, 'filled', 'MarkerFaceAlpha', 0.4);
title('波动率聚类', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('|r_t|');
ylabel('|r_{t+1}|');
grid on; grid minor;

%% 9. 功率谱
subplot(3, 4, 12);
nFFT = length(returns);
Y = fft(returns - mean(returns));
P = abs(Y(2:floor(nFFT/2)+1)).^2 / nFFT;
f = (1:length(P)) / nFFT;
loglog(f(2:end), P(2:end), 'b-', 'LineWidth', 1);
title('功率谱', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('频率');
ylabel('功率');
grid on; grid minor;

%% 统计输出
fprintf('\n┌─────────────────────────────────────────┐\n');
fprintf('│ 统计摘要                                 │\n');
fprintf('├─────────────────────────────────────────┤\n');
fprintf('│ 收益率均值:     %+8.4f%%             │\n', mean(returns));
fprintf('│ 收益率标准差:   %8.4f%%               │\n', std(returns));
fprintf('│ 偏度:           %8.4f                 │\n', skewness(returns));
fprintf('│ 峰度:           %8.4f                 │\n', kurtosis(returns));
fprintf('│ 累计收益率:    %+8.2f%%             │\n', cumRet(end));
fprintf('└─────────────────────────────────────────┘\n');
end
