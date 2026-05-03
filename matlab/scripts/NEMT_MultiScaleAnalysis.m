%% NEMT_MultiScaleAnalysis - 多尺度相关性分析
% 输入: 工作区中的 timestamp, close 或 raw
% 输出: 图表
%
% 使用方法:
%   1. 导入 .mat 文件
%   2. 运行: NEMT_MultiScaleAnalysis

function varargout = NEMT_MultiScaleAnalysis()
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

scales = [1, 4, 24, 72, 168];
scaleNames = {'1H', '4H', '1D', '3D', '7D'};

%% 图1: 多尺度收益率
fig1 = figure('Position', [50, 50, 1500, 800], 'Color', [0.03 0.03 0.08]);
movegui('center');

subplot(3,1,1);
plot(timestamp, close, 'w-', 'LineWidth', 1);
title('价格走势', 'FontSize', 14, 'FontWeight', 'bold');
ylabel('价格');
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

subplot(3,1,2);
colors = lines(length(scales));
hold on;
for i = 1:length(scales)
    s = scales(i);
    if s < length(close)
        idx = 1:s:length(close);
        scaleRet = diff(log(close(idx))) * 100;
        t_idx = idx(1:length(scaleRet));
        plot(timestamp(t_idx), scaleRet, 'Color', colors(i,:), 'LineWidth', 1, 'DisplayName', scaleNames{i});
    end
end
title('不同时间尺度收益率', 'FontSize', 14, 'FontWeight', 'bold');
ylabel('收益率 (%)');
legend('Location', 'best');
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

subplot(3,1,3);
volScales = [1, 2, 4, 6, 12, 24, 48, 72, 120, 168];
volValues = zeros(length(volScales), 1);
for i = 1:length(volScales)
    s = volScales(i);
    if s < length(returns)
        volValues(i) = std(returns(1:s:end)) * sqrt(24);
    end
end
semilogx(volScales, volValues, 'bo-', 'MarkerSize', 8, 'MarkerFaceColor', 'b', 'LineWidth', 2);
title('年化波动率 vs 时间尺度', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('时间尺度 (小时)');
ylabel('年化波动率 (%)');
grid on; grid minor;
set(gca, 'Color', [0.08 0.08 0.12], 'XColor', [0.4 0.4 0.4], 'YColor', [0.4 0.4 0.4]);

%% 图2: 相关性结构
fig2 = figure('Position', [100, 100, 1400, 700], 'Color', [0.03 0.03 0.08]);
movegui('center');

subplot(2,2,1);
maxLag = min(48, floor(length(returns)/4)-1);
acf = zeros(maxLag, 1);
for lag = 1:maxLag
    c = corrcoef(returns(1:end-lag), returns(lag+1:end));
    acf(lag) = c(1,2);
end
stem(1:maxLag, acf, 'MarkerSize', 3, 'BaseValue', -0.2);
hold on;
plot([1 maxLag], 1.96/sqrt(length(returns))*[1 1], 'r--');
plot([1 maxLag], -1.96/sqrt(length(returns))*[1 1], 'r--');
title('收益率自相关', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('滞后');
ylabel('ACF');
grid on; grid minor;

subplot(2,2,2);
% 多尺度相关性热力图
nScales = 5;
corrMatrix = zeros(nScales);
for i = 1:nScales
    for j = 1:nScales
        s1 = scales(i); s2 = scales(j);
        if s1 < length(close) && s2 < length(close)
            r1 = diff(log(close(1:s1:end)));
            r2 = diff(log(close(1:s2:end)));
            minLen = min(length(r1), length(r2));
            corrMatrix(i,j) = corr(r1(1:minLen), r2(1:minLen));
        end
    end
end
imagesc(corrMatrix, [-1 1]);
colormap redblue;
colorbar;
set(gca, 'XTick', 1:nScales, 'XTickLabel', scaleNames, ...
    'YTick', 1:nScales, 'YTickLabel', scaleNames);
title('多尺度收益率相关性', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('时间尺度');
ylabel('时间尺度');

subplot(2,2,3);
absReturns = abs(returns);
lags = -48:48;
crossCorr = zeros(length(lags), 1);
nData = length(returns);
for i = 1:length(lags)
    lag = lags(i);
    if lag < 0
        idx1 = 1:nData+lag;
        idx2 = 1-lag:nData;
        if length(idx1) == length(idx2) && length(idx1) > 1
            crossCorr(i) = corr(returns(idx1), absReturns(idx2));
        end
    else
        idx1 = 1+lag:nData;
        idx2 = 1:nData-lag;
        if length(idx1) == length(idx2) && length(idx1) > 1
            crossCorr(i) = corr(returns(idx1), absReturns(idx2));
        end
    end
end
stem(lags, crossCorr, 'MarkerSize', 3, 'BaseValue', 0);
hold on;
plot([-48 48], [0.1 0.1], 'r--');
plot([-48 48], [-0.1 -0.1], 'r--');
title('收益率-波动率交叉相关', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('滞后');
ylabel('CCF');
grid on; grid minor;

subplot(2,2,4);
window = 168;
if window < length(returns) - 1
    rollingCorr = zeros(length(returns) - window, 1);
    for i = 1:length(rollingCorr)
        windowData = returns(i:i+window-1);
        if length(windowData) > 2
            rollingCorr(i) = corr(windowData(1:end-1), abs(windowData(2:end)));
        end
    end
    t = timestamp(window+1:end);
    if length(t) > length(rollingCorr), t = t(1:length(rollingCorr)); end
    plot(t, rollingCorr, 'm-', 'LineWidth', 0.5);
    hold on;
    plot(t, movmean(rollingCorr, min(24, length(rollingCorr))), 'r-', 'LineWidth', 2);
end
yline(0, 'k--');
title('滚动相关性 (7天窗口)', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('时间');
ylabel('相关性');
grid on; grid minor;

%% 图3: 长记忆性
fig3 = figure('Position', [150, 150, 1400, 500], 'Color', [0.03 0.03 0.08]);
movegui('center');

subplot(1,3,1);
maxLag = min(72, floor(length(returns)/2)-1);
semivar = zeros(maxLag, 1);
for h = 1:maxLag
    pairs = 0; sumVal = 0;
    for i = 1:length(returns)-h
        sumVal = sumVal + (returns(i) - returns(i+h))^2;
        pairs = pairs + 1;
    end
    if pairs > 0, semivar(h) = sumVal / (2 * pairs); end
end
plot(1:maxLag, semivar, 'b-', 'LineWidth', 2);
title('半变异函数', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('滞后 h');
ylabel('γ(h)');
set(gca, 'XScale', 'log', 'YScale', 'log');
grid on; grid minor;

subplot(1,3,2);
scaleSpectrum = zeros(5, 1);
for i = 1:5
    s = scales(i);
    if s < length(close)
        r = diff(log(close(1:s:end)));
        scaleSpectrum(i) = var(r);
    end
end
bar(scaleNames(1:5), scaleSpectrum, 'FaceColor', [0.3 0.7 1]);
title('各尺度波动率谱', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('时间尺度');
ylabel('方差');
grid on; grid minor;

subplot(1,3,3);
% Hurst简化计算
n = length(returns);
maxK = floor(n / 4);
nVals = floor(linspace(4, maxK, 20));
nVals = unique(nVals);
RS_vals = zeros(length(nVals), 1);
for i = 1:length(nVals)
    RS_vals(i) = calcRS(returns, floor(nVals(i)));
end
H = polyfit(log(nVals), log(RS_vals), 1);
H = H(1);
interpretation = {'H > 0.5: 趋势持续', 'H < 0.5: 趋势反转', 'H ≈ 0.5: 随机游走'};
text(0.1, 0.7, 'Hurst指数解读:', 'FontSize', 14, 'FontWeight', 'bold');
for i = 1:length(interpretation), text(0.1, 0.5-i*0.15, interpretation{i}, 'FontSize', 12); end
text(0.1, 0.2, sprintf('H = %.4f', H), 'FontSize', 16, 'FontWeight', 'bold', 'Color', 'g');
axis off;

%% 统计输出
fprintf('\n┌─────────────────────────────────────────┐\n');
fprintf('│ 多尺度分析                               │\n');
fprintf('├─────────────────────────────────────────┤\n');
fprintf('│ Hurst指数 H ≈ %.4f                     │\n', H);
fprintf('└─────────────────────────────────────────┘\n');

if nargout > 0, varargout{1} = {fig1, fig2, fig3}; end
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
