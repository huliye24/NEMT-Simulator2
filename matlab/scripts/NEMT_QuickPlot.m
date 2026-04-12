%% NEMT_QuickPlot - 快速K线图
% 输入: 工作区中的 timestamp, open, high, low, close, volume
%       或 raw 结构体
% 输出: 图表
%
% 使用方法:
%   1. 在MATLAB中导入 .mat 文件: load('E:\NEMT Simulator\matlab_data\BTC_1h.mat')
%   2. 运行: NEMT_QuickPlot

function fig = NEMT_QuickPlot()
%% 检查工作区数据
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
if timestamp(1) > 700000  % Unix timestamp (秒)
    timestamp = datetime(timestamp, 'ConvertFrom', 'posixtime');
elseif timestamp(1) > 70000  % Excel日期
    timestamp = datetime(timestamp, 'ConvertFrom', 'excel');
elseif timestamp(1) > 1000  % 可能是matplotlib日期数字
    try
        timestamp = datetime(timestamp, 'ConvertFrom', 'datenum');
    catch
        timestamp = (1:n)';
    end
end

%% 创建图表
fig = figure('Position', [100, 100, 1600, 900], 'Color', [0.03 0.03 0.08]);
movegui('center');

% 价格走势
subplot(2,1,1);
plot(timestamp, close, 'b-', 'LineWidth', 1);
hold on;
plot(timestamp, high, 'r-', 'LineWidth', 0.5);
plot(timestamp, low, 'g-', 'LineWidth', 0.5);
datetick('x', 'yyyy-mm', 'keeplimits');
title('K线图', 'FontSize', 16, 'FontWeight', 'bold', 'Color', 'white');
ylabel('价格 (USDT)', 'FontSize', 12);
legend('Close', 'High', 'Low', 'Location', 'best');
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

% 成交量
subplot(2,1,2);
colors = zeros(length(close), 3);
colors(:,1) = (close > open);
colors(:,2) = 0.4;
colors(:,3) = 1 - colors(:,1);
bar(timestamp, volume, 0.8, 'FaceColor', 'flat', 'CData', colors);
datetick('x', 'yyyy-mm', 'keeplimits');
title('成交量', 'FontSize', 14, 'FontWeight', 'bold', 'Color', 'white');
ylabel('Volume', 'FontSize', 12);
xlabel('时间', 'FontSize', 12);
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

fprintf('\n✓ K线图生成完成\n');
end
