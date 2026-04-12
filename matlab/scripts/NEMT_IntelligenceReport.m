%% NEMT_IntelligenceReport - 智能分析报告生成器
% 自动分析数据，输出结构化结论
%
% 使用方法:
%   1. 导入 .mat 文件
%   2. 运行: report = NEMT_IntelligenceReport()

function report = NEMT_IntelligenceReport()
fprintf('\n');
fprintf('╔═══════════════════════════════════════════════════════════════╗\n');
fprintf('║          NEMT 智能分析报告 - 市场结构诊断                      ║\n');
fprintf('╚═══════════════════════════════════════════════════════════════╝\n');

%% 获取数据
vars = evalin('base', 'who');

if any(strcmp(vars, 'raw'))
    raw = evalin('base', 'raw');
    close = raw.close(:);
    timestamp = raw.timestamp(:);
    if isfield(raw, 'volume'), volume = raw.volume(:); else volume = ones(size(close)); end
elseif any(strcmp(vars, 'close'))
    close = evalin('base', 'close');
    close = close(:);
    if any(strcmp(vars, 'timestamp')), timestamp = evalin('base', 'timestamp'); end
    if any(strcmp(vars, 'volume')), volume = evalin('base', 'volume'); else volume = ones(size(close)); end
else
    error('请先导入数据');
end

if ~exist('timestamp', 'var'), timestamp = (1:length(close))'; end

%% 计算所有指标
returns = diff(log(close)) * 100;
absReturns = abs(returns);
cumRet = cumsum(returns);
n = length(returns);

%% ========== 1. 基础统计 ==========
fprintf('\n【一、基础统计特征】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

mean_ret = mean(returns);
std_ret = std(returns);
skew = skewness(returns);
kurt = kurtosis(returns);
total_ret = cumRet(end);

fprintf('  📊 收益率统计:\n');
fprintf('     • 均值:     %+.4f%% (日)\n', mean_ret);
fprintf('     • 标准差:   %.4f%%\n', std_ret);
fprintf('     • 累计收益: %+.2f%%\n', total_ret);

fprintf('  📈 分布特征:\n');
fprintf('     • 偏度:     %.4f (%s)\n', skew, interpretSkew(skew));
fprintf('     • 峰度:     %.4f (%s)\n', kurt, interpretKurt(kurt));

%% ========== 2. 波动率分析 ==========
fprintf('\n【二、波动率特征】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

rolling_vol = movstd(returns, 24) * sqrt(24) * 100;
vol_current = rolling_vol(end);
vol_max = max(rolling_vol);
vol_min = min(rolling_vol);
vol_mean = mean(rolling_vol);

% 波动率聚类检验
arch_effect = corr(absReturns(1:end-1), absReturns(2:end));

% 波动率位置
vol_percentile = mean(rolling_vol <= vol_current) * 100;

fprintf('  📉 波动率水平:\n');
fprintf('     • 当前年化: %.2f%%\n', vol_current);
fprintf('     • 历史区间: [%.2f%%, %.2f%%]\n', vol_min, vol_max);
fprintf('     • 历史分位: %.1f%% (百分位)\n', vol_percentile);

fprintf('  🔥 波动率聚类:\n');
fprintf('     • ARCH效应: %.4f (%s)\n', arch_effect, interpretARCH(arch_effect));

vol_status = interpretVolRegime(vol_current, vol_mean, vol_max);
fprintf('  🎯 波动率状态: %s\n', vol_status);

%% ========== 3. 相关性/记忆性 ==========
fprintf('\n【三、时间序列特性】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

% 自相关
maxLag = min(24, floor(n/4)-1);
acf1 = zeros(maxLag, 1);
for lag = 1:maxLag
    c = corrcoef(returns(1:end-lag), returns(lag+1:end));
    acf1(lag) = c(1,2);
end
acf_sum = sum(acf1(1:5));

% 收益率自相关
ret_autocorr = acf1(1);

fprintf('  🔄 自相关分析:\n');
fprintf('     • lag-1自相关: %.4f (%s)\n', ret_autocorr, interpretACF(ret_autocorr));
fprintf('     • 前5阶和:    %.4f\n', acf_sum);

% Hurst指数
H = calcHurst(returns);
fprintf('  🎲 Hurst指数: %.4f\n', H);
fprintf('     • %s\n', interpretHurst(H));

memory_type = interpretMemory(H);
fprintf('  🧠 记忆类型: %s\n', memory_type);

%% ========== 4. 分布性质 ==========
fprintf('\n【四、分布性质检验】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

% 正态性检验
[jb_p, jb_stat] = jbTest(returns);
normal_score = min(1, abs(skew)/2 + (kurt-3)/10);

fprintf('  📐 正态性:\n');
fprintf('     • 偏度偏离: %.2f (0=对称)\n', abs(skew));
fprintf('     • 峰度偏离: %.2f (0=正态)\n', abs(kurt-3)/3);
fprintf('     • 非正态程度: %.0f%%\n', normal_score * 100);

if jb_p < 0.05
    fprintf('     • JB检验: 拒绝正态 (p=%.4f)\n', jb_p);
else
    fprintf('     • JB检验: 不能拒绝正态 (p=%.4f)\n', jb_p);
end

% 厚尾检验
tail_ratio = prctile(returns, 99) / prctile(returns, 1);
fprintf('  📊 尾部特征:\n');
fprintf('     • 上下尾比: %.2f (1=对称)\n', abs(tail_ratio));

%% ========== 5. 市场状态判断 ==========
fprintf('\n【五、市场状态诊断】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

% 综合判断
regime = diagnoseRegime(H, arch_effect, kurt, skew, vol_current, vol_mean);
fprintf('\n');
fprintf('  ┌─────────────────────────────────────────┐\n');
fprintf('  │  🎯 当前市场状态: %-22s│\n', regime.name);
fprintf('  └─────────────────────────────────────────┘\n');
fprintf('\n');
fprintf('  特征描述:\n');
for i = 1:length(regime.features)
    fprintf('    %d. %s\n', i, regime.features{i});
end

%% ========== 6. 风险评估 ==========
fprintf('\n【六、风险指标】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

% VaR
var_95 = prctile(returns, 5);
var_99 = prctile(returns, 1);
cvar_95 = mean(returns(returns <= var_95));

% 最大回撤
cum_max = cummax(close);
drawdown = (close - cum_max) ./ cum_max * 100;
max_dd = min(drawdown) * 100;

fprintf('  ⚠️ 风险度量:\n');
fprintf('     • VaR(95%%):    %.2f%% (单日最大损失)\n', var_95);
fprintf('     • VaR(99%%):    %.2f%%\n', var_99);
fprintf('     • CVaR(95%%):   %.2f%% (预期尾部损失)\n', cvar_95);
fprintf('     • 最大回撤:    %.2f%%\n', max_dd);
fprintf('     • 年化波动:    %.2f%%\n', vol_current);

risk_level = interpretRisk(var_95, max_dd, vol_current);
fprintf('\n  🛡️ 风险等级: %s\n', risk_level);

%% ========== 7. 结论与建议 ==========
fprintf('\n【七、综合结论】\n');
fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

conclusions = generateConclusions(regime, H, arch_effect, kurt, vol_current, var_95);
for i = 1:length(conclusions)
    fprintf('  %s\n', conclusions{i});
end

%% ========== 8. 输出结构体 ==========
report = struct();
report.timestamp = datestr(now);
report.data_length = n;
report.mean_return = mean_ret;
report.volatility = std_ret;
report.cum_return = total_ret;
report.skewness = skew;
report.kurtosis = kurt;
report.hurst = H;
report.arch_effect = arch_effect;
report.current_vol = vol_current;
report.var_95 = var_95;
report.max_drawdown = max_dd;
report.regime = regime.name;
report.risk_level = risk_level;
report.memory_type = memory_type;

fprintf('\n');
fprintf('╔═══════════════════════════════════════════════════════════════╗\n');
fprintf('║                    分析报告生成完毕                            ║\n');
fprintf('╚═══════════════════════════════════════════════════════════════╝\n');
end

%% ========== 辅助函数 ==========

function str = interpretSkew(s)
if abs(s) < 0.1
    str = '对称';
elseif s > 0.5
    str = '强烈右偏(正收益肥尾)';
elseif s > 0.1
    str = '轻度右偏';
elseif s < -0.5
    str = '强烈左偏(负收益肥尾)';
else
    str = '轻度左偏';
end
end

function str = interpretKurt(k)
if k < 3
    str = '薄尾';
elseif k < 5
    str = '正常';
elseif k < 7
    str = '厚尾';
else
    str = '极厚尾';
end
end

function str = interpretARCH(r)
if r < 0.1
    str = '弱(无聚类)';
elseif r < 0.3
    str = '中等';
elseif r < 0.5
    str = '较强';
else
    str = '强(明显聚类)';
end
end

function str = interpretACF(r)
if abs(r) < 0.05
    str = '无相关(随机)';
elseif r > 0.1
    str = '正相关(趋势)';
else
    str = '负相关(反转)';
end
end

function str = interpretHurst(H)
if H > 0.6
    str = 'H>0.5: 趋势持续性，存在长期记忆';
elseif H > 0.5
    str = 'H>0.5: 略偏趋势持续';
elseif H < 0.4
    str = 'H<0.5: 趋势反转性较强';
else
    str = 'H≈0.5: 接近随机游走';
end
end

function str = interpretVolRegime(vol, mean_vol, max_vol)
ratio = vol / max_vol;
if ratio > 0.8
    str = '🔴 高波动期(顶部)';
elseif ratio > 0.5
    str = '🟡 中高波动';
elseif ratio > 0.2
    str = '🟢 正常波动';
else
    str = '🔵 低波动期(底部)';
end
end

function str = interpretMemory(H)
if H > 0.55
    str = '📈 趋势市场(动量效应)';
elseif H < 0.45
    str = '📉 均值回归市场';
else
    str = '⚖️ 随机游走市场';
end
end

function str = interpretRisk(var_95, max_dd, vol)
risk_score = var_95 + max_dd/10 + vol/20;
if risk_score < -3
    str = '🟢 低风险';
elseif risk_score < -2
    str = '🟡 中低风险';
elseif risk_score < -1
    str = '🟠 中高风险';
else
    str = '🔴 高风险';
end
end

function str = interpretSkewTrading(skew)
if skew < -0.3
    str = '左偏(负收益风险大)';
elseif skew > 0.3
    str = '右偏(正收益潜力大)';
else
    str = '基本对称';
end
end

function regime = diagnoseRegime(H, arch, kurt, skew, vol, mean_vol)
regime = struct('name', '未知', 'features', {});

% 高波动聚类
if arch > 0.3
    regime.features{end+1} = '波动率聚类明显(ARCH效应强)';
end

% 厚尾
if kurt > 5
    regime.features{end+1} = sprintf('收益率分布厚尾(峰度=%.1f)', kurt);
end

% 偏度
if skew < -0.3
    regime.features{end+1} = '左偏分布(负收益极端事件更频繁)';
elseif skew > 0.3
    regime.features{end+1} = '右偏分布(正收益极端事件更频繁)';
end

% Hurst判断
if H > 0.55
    regime.features{end+1} = '长期记忆性强(趋势延续概率高)';
elseif H < 0.45
    regime.features{end+1} = '长期记忆性弱(均值回归特征明显)';
end

% 波动率位置
vol_ratio = vol / mean_vol;
if vol_ratio > 1.2
    regime.features{end+1} = '当前波动率高于历史均值';
elseif vol_ratio < 0.8
    regime.features{end+1} = '当前波动率低于历史均值';
end

% 综合命名
if H > 0.55 && arch > 0.3 && kurt > 5
    regime.name = '趋势+高波动混沌';
elseif H > 0.55 && arch < 0.2
    regime.name = '稳定趋势市场';
elseif H < 0.45 && arch > 0.3
    regime.name = '均值回归+高波动';
elseif H < 0.45 && arch < 0.2
    regime.name = '均值回归稳定';
elseif H > 0.55
    regime.name = '趋势动量市场';
elseif kurt > 5
    regime.name = '厚尾风险市场';
else
    regime.name = '随机游走市场';
end
end

function conclusions = generateConclusions(regime, H, arch, kurt, vol, var_95)
conclusions = {};

conclusions{end+1} = '【市场结构诊断】';
conclusions{end+1} = sprintf('  • 市场属于"%s"类型', regime.name);

if H > 0.55
    conclusions{end+1} = '  • 检测到明显的趋势持续性，适合趋势跟踪策略';
elseif H < 0.45
    conclusions{end+1} = '  • 表现出均值回归特征，反转策略可能有效';
else
    conclusions{end+1} = '  • 价格序列接近随机游走，短期预测困难';
end

if arch > 0.3
    conclusions{end+1} = '  • 波动率聚类强烈，高波动期后会持续，适合波动率交易';
else
    conclusions{end+1} = '  • 波动率聚类不明显，市场状态转换较快';
end

if kurt > 5
    conclusions{end+1} = sprintf('  • 极端收益事件频繁(峰度=%.1f)，风险警示加强', kurt);
end

conclusions{end+1} = '';
conclusions{end+1} = '【风险特征】';
conclusions{end+1} = sprintf('  • 日VaR(95%%)=%.2f%%，即95%%概率单日损失不超过%.2f%%', abs(var_95), abs(var_95));
conclusions{end+1} = sprintf('  • 年化波动率=%.2f%%，市场活跃度%s', vol, ...
    iif(vol > 50, '极高', iif(vol > 30, '较高', iif(vol > 15, '正常', '偏低'))));

conclusions{end+1} = '';
conclusions{end+1} = '【交易启示】';
if H > 0.55 && arch > 0.3
    conclusions{end+1} = '  → 趋势策略：均线交叉、趋势线突破';
    conclusions{end+1} = '  → 波动率策略：买入波动率(gamma交易)';
elseif H < 0.45 && arch > 0.3
    conclusions{end+1} = '  → 均值回归：布林带、RSI等技术指标有效';
    conclusions{end+1} = '  → 波动率策略：卖出波动率(volatility crush)';
elseif H < 0.45
    conclusions{end+1} = '  → 区间交易：支撑阻力位操作';
else
    conclusions{end+1} = '  → 建议观望或使用期权对冲';
end

conclusions{end+1} = '';
conclusions{end+1} = '【注意事项】';
conclusions{end+1} = '  ⚠️ 历史分析不代表未来表现';
conclusions{end+1} = '  ⚠️ 高峰度表明极端事件概率增加';
conclusions{end+1} = '  ⚠️ 建议结合基本面和市场情绪综合判断';
end

function result = iif(cond, true_val, false_val)
if cond, result = true_val; else result = false_val; end
end

function H = calcHurst(data)
n = length(data);
maxK = floor(n / 4);
nVals = floor(linspace(4, maxK, 15));
nVals = unique(nVals(nVals > 1));
RS_vals = zeros(length(nVals), 1);
for i = 1:length(nVals)
    RS_vals(i) = calcRS(data, floor(nVals(i)));
end
RS_vals = RS_vals(RS_vals > 0 & isfinite(RS_vals));
if length(RS_vals) > 1
    H = polyfit(log(nVals(1:length(RS_vals))), log(RS_vals), 1);
    H = H(1);
else
    H = 0.5;
end
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

function [pval, stat] = jbTest(x)
n = length(x);
m1 = mean(x);
m2 = std(x);
sk = skewness(x);
ku = kurtosis(x);
stat = n/6 * (sk^2 + 0.25*(ku-3)^2);
pval = 1 - chi2cdf(stat, 2);
end
