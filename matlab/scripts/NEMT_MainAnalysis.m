%% NEMT_MainAnalysis - 主分析程序
% 输入: 工作区中的 timestamp, open, high, low, close, volume 或 raw
% 输出: 图表
%
% 使用方法:
%   1. 导入 .mat 文件
%   2. 运行: NEMT_MainAnalysis

function varargout = NEMT_MainAnalysis()
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
    error('工作区中未找到数据，请先导入 .mat 文件');
end

if ~exist('open', 'var'), open = close; end
if ~exist('high', 'var'), high = close; end
if ~exist('low', 'var'), low = close; end
if ~exist('volume', 'var'), volume = zeros(size(close)); end
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
cumRet = cumsum(returns);

%% 图1: K线图 + 成交量
fig1 = figure('Position', [100, 100, 1400, 800], 'Color', [0.05 0.05 0.1]);
movegui('center');

subplot(2,1,1);
plot(timestamp, close, 'b-', 'LineWidth', 1);
hold on;
plot(timestamp, high, 'r-', 'LineWidth', 0.5);
plot(timestamp, low, 'g-', 'LineWidth', 0.5);
title('价格走势', 'FontSize', 16, 'FontWeight', 'bold');
ylabel('价格');
legend('Close', 'High', 'Low');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

subplot(2,1,2);
colors = zeros(length(close), 3);
colors(:,1) = (close > open);
colors(:,2) = 0.4;
colors(:,3) = 1 - colors(:,1);
bar(timestamp, volume, 0.8, 'FaceColor', 'flat', 'CData', colors);
title('成交量', 'FontSize', 14);
xlabel('时间');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

%% 图2: 收益率分析
fig2 = figure('Position', [200, 200, 1400, 800], 'Color', [0.05 0.05 0.1]);
movegui('center');

subplot(2,2,1);
histogram(returns, 50, 'FaceColor', [0.3 0.8 1], 'EdgeColor', 'none');
hold on;
xline(0, 'r-', 'LineWidth', 2);
xline(mean(returns), 'g--', 'LineWidth', 2);
title('收益率分布', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('收益率 (%)');
ylabel('频次');
grid on; grid minor;

subplot(2,2,2);
qqplot(returns);
title('Q-Q图', 'FontSize', 14, 'FontWeight', 'bold');
grid on; grid minor;

subplot(2,2,3);
plot(timestamp(2:end), cumRet, 'b-', 'LineWidth', 1.5);
title('累计收益率', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('时间');
ylabel('累计 (%)');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

subplot(2,2,4);
rollingVol = movstd(returns, 24) * sqrt(24) * 100;
plot(timestamp(2:end), rollingVol, 'm-', 'LineWidth', 1.5);
title('24H滚动波动率', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('时间');
ylabel('年化 (%)');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

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

if nargout > 0, varargout{1} = {fig1, fig2}; end
end
