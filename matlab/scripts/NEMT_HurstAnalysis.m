%% NEMT_HurstAnalysis - Hurst指数分析
% 输入: 工作区中的 timestamp, close 或 raw
% 输出: H (Hurst指数)
%
% 使用方法:
%   1. 导入 .mat 文件
%   2. 运行: H = NEMT_HurstAnalysis

function H = NEMT_HurstAnalysis()
%% 获取数据
vars = evalin('base', 'who');

if any(strcmp(vars, 'raw'))
    raw = evalin('base', 'raw');
    close = raw.close(:);  % 转列向量
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

%% R/S分析
fprintf('\n计算 Hurst 指数...\n');

n = length(returns);
maxK = floor(n / 4);
nVals = floor(linspace(4, maxK, 20));
nVals = unique(nVals);  % 去重

RS_vals = zeros(length(nVals), 1);
for i = 1:length(nVals)
    RS_vals(i) = calcRS(returns, floor(nVals(i)));
end

log_n = log(nVals);
log_RS = log(RS_vals);
p = polyfit(log_n, log_RS, 1);
H = p(1);

fprintf('Hurst 指数 H = %.4f\n', H);

%% 图1: R/S分析
fig1 = figure('Position', [100, 100, 1400, 800], 'Color', [0.05 0.05 0.1]);
movegui('center');

subplot(2,2,1);
plot(timestamp, close, 'b-', 'LineWidth', 1);
title('价格走势', 'FontSize', 14, 'FontWeight', 'bold');
ylabel('价格');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

subplot(2,2,2);
semilogx(nVals, RS_vals, 'bo-', 'MarkerSize', 6, 'MarkerFaceColor', 'b');
hold on;
x_fit = linspace(min(nVals), max(nVals), 100);
plot(x_fit, x_fit.^H, 'r--', 'LineWidth', 2);
title(sprintf('R/S 分析: H = %.4f', H), 'FontSize', 14, 'FontWeight', 'bold');
xlabel('n');
ylabel('R/S');
legend('实测', sprintf('n^{%.2f}', H), 'Location', 'best');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

%% 图2: 多尺度波动率
subplot(2,2,3);
scales = [1, 6, 24, 72, 168];
colors = lines(length(scales));
hold on;
n = length(returns);
for i = 1:length(scales)
    s = scales(i);
    if s < n
        vol = movstd(returns, s) * sqrt(24);
        t_idx = s+1:min(length(vol), n);
        if length(t_idx) > 1
            t = timestamp(t_idx);
            vol = vol(t_idx);
            plot(t, vol, 'Color', colors(i,:), 'LineWidth', 1.2);
        end
    end
end
legend(arrayfun(@(x) sprintf('%dH', x), scales, 'UniformOutput', false));
title('多尺度波动率', 'FontSize', 14, 'FontWeight', 'bold');
ylabel('年化波动率');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

%% 图3: 功率谱
subplot(2,2,4);
y = returns - mean(returns);
n = length(y);
Y = fft(y);
P = abs(Y(2:floor(n/2)+1)).^2 / n;
f = (0:length(P)-1) / n;
loglog(f(2:end), P(2:end), 'b-', 'LineWidth', 1.5);
title('功率谱密度', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('频率');
ylabel('功率');
grid on; grid minor;
set(gca, 'Color', [0.1 0.1 0.15], 'XColor', [0.5 0.5 0.5], 'YColor', [0.5 0.5 0.5]);

%% 解读
fprintf('\n┌─────────────────────────────────────┐\n');
if H > 0.5
    fprintf('│ H > 0.5: 趋势持续性 (动量效应)     │\n');
elseif H < 0.5
    fprintf('│ H < 0.5: 趋势反转性               │\n');
else
    fprintf('│ H ≈ 0.5: 接近随机游走             │\n');
end
fprintf('│ 分形维数 D_f = %.4f               │\n', 2-H);
fprintf('└─────────────────────────────────────┘\n');
end

function RS = calcRS(data, n)
N = floor(length(data) / n);
if N < 2, RS = nan; return; end

RS_vals = zeros(N, 1);
for i = 1:N
    subseries = data((i-1)*n + 1 : i*n);
    subseries = subseries - mean(subseries);
    cumsumY = cumsum(subseries);
    R = max(cumsumY) - min(cumsumY);
    S = std(subseries);
    if S > 0, RS_vals(i) = R / S; end
end
RS = mean(RS_vals(~isnan(RS_vals)));
end
