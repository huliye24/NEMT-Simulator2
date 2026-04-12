%% NEMT_ExportReport - 导出分析报告
% 自动生成 Markdown 格式报告并保存
%
% 使用方法:
%   1. 先运行: report = NEMT_IntelligenceReport()
%   2. 然后:  NEMT_ExportReport(report)
%   3. 或直接: NEMT_ExportReport()  % 自动生成

function NEMT_ExportReport(report)
%% 生成报告
if nargin < 1
    report = NEMT_IntelligenceReport();
end

%% 获取数据用于绘图
vars = evalin('base', 'who');

if any(strcmp(vars, 'raw'))
    raw = evalin('base', 'raw');
    close = raw.close(:);
    timestamp = raw.timestamp(:);
elseif any(strcmp(vars, 'close'))
    close = evalin('base', 'close');
    if any(strcmp(vars, 'timestamp')), timestamp = evalin('base', 'timestamp'); end
end

if ~exist('timestamp', 'var'), timestamp = (1:length(close))'; end
returns = diff(log(close)) * 100;
absReturns = abs(returns);
cumRet = cumsum(returns);

%% 处理时间
if timestamp(1) > 700000
    ts_str = datestr(datetime(timestamp(1), 'ConvertFrom', 'posixtime'), 'yyyy-mm-dd');
    te_str = datestr(datetime(timestamp(end), 'ConvertFrom', 'posixtime'), 'yyyy-mm-dd');
elseif timestamp(1) > 70000
    ts_str = datestr(datetime(timestamp(1), 'ConvertFrom', 'excel'), 'yyyy-mm-dd');
    te_str = datestr(datetime(timestamp(end), 'ConvertFrom', 'excel'), 'yyyy-mm-dd');
else
    ts_str = '未知';
    te_str = '未知';
end

%% 目录设置
baseDir = fileparts(fileparts(mfilename('fullpath')));
reportDir = fullfile(baseDir, 'results', 'reports');
if ~exist(reportDir, 'dir'), mkdir(reportDir); end

dateStr = datestr(now, 'yyyy-mm-dd');
dateNum = datestr(now, 'yyyymmdd_HHMMSS');
reportFile = fullfile(reportDir, [dateNum '_analysis_report.md']);

%% 生成 Markdown 内容
md = sprintf(['# NEMT 市场分析报告\n\n', ...
    '> 生成时间: %s\n', ...
    '> 数据区间: %s 至 %s\n\n', ...
    '---\n\n'], ...
    datestr(now, 'yyyy-mm-dd HH:MM:SS'), ts_str, te_str);

%% 一、执行摘要
md = [md, sprintf(['## 一、执行摘要\n\n', ...
    '| 指标 | 数值 | 状态 |\n', ...
    '|:---|:---|:---|\n', ...
    '| 市场状态 | %s | %s |\n', ...
    '| Hurst指数 | %.4f | %s |\n', ...
    '| ARCH效应 | %.4f | %s |\n', ...
    '| 年化波动率 | %.2f%% | %s |\n', ...
    '| 风险等级 | %s | %s |\n', ...
    '| 日VaR(95%%) | %.2f%% | ⚠️ |\n\n'], ...
    report.regime, getStatusEmoji(report.regime), ...
    report.hurst, getHurstStatus(report.hurst), ...
    report.arch_effect, getARCHStatus(report.arch_effect), ...
    report.current_vol, getVolStatus(report.current_vol), ...
    report.risk_level, getRiskEmoji(report.risk_level), ...
    report.var_95)];

%% 二、收益率统计
md = [md, sprintf(['## 二、收益率统计特征\n\n', ...
    '```\n', ...
    '┌──────────────────────────────────────────┐\n', ...
    '│ 基础统计                                 │\n', ...
    '├──────────────────────────────────────────┤\n', ...
    '│ 样本数量:         %-10d                 │\n', ...
    '│ 累计收益率:      %+8.2f%%             │\n', ...
    '│ 日均收益率:      %+8.4f%%             │\n', ...
    '│ 标准差:          %8.4f%%               │\n', ...
    '│ 偏度:            %8.4f                 │\n', ...
    '│ 峰度:            %8.4f                 │\n', ...
    '└──────────────────────────────────────────┘\n', ...
    '```\n\n'], ...
    report.data_length, report.cum_return, report.mean_return, ...
    report.volatility, report.skewness, report.kurtosis)];

%% 三、市场状态解读
md = [md, sprintf(['## 三、市场状态解读\n\n', ...
    '### 3.1 时间序列特性\n\n', ...
    '- **Hurst指数 = %.4f**\n', ...
    '  - 含义: %s\n', ...
    '  - 市场特征: %s\n\n', ...
    '- **ARCH效应 = %.4f**\n', ...
    '  - 含义: %s\n', ...
    '  - 市场特征: 波动率存在明显聚类，高波动期后会持续一段时间\n\n'], ...
    report.hurst, interpretHurstText(report.hurst), report.memory_type, ...
    report.arch_effect, interpretARCHText(report.arch_effect))];

%% 四、风险评估
md = [md, sprintf(['## 四、风险评估\n\n', ...
    '| 风险指标 | 数值 | 解读 |\n', ...
    '|:---|:---|:---|\n', ...
    '| 日VaR(95%%) | %.2f%% | 95%%概率下单日损失不超过此值 |\n', ...
    '| 日VaR(99%%) | %.2f%% | 99%%概率下单日损失不超过此值 |\n', ...
    '| 最大回撤 | %.2f%% | 历史最大回撤幅度 |\n', ...
    '| 年化波动率 | %.2f%% | 市场波动程度 |\n\n'], ...
    report.var_95, prctile(returns, 1), report.max_drawdown, report.current_vol)];

%% 五、分布特征
skew_interp = interpretSkewText(report.skewness);
kurt_interp = interpretKurtText(report.kurtosis);
md = [md, sprintf(['## 五、收益率分布特征\n\n', ...
    '### 5.1 偏度分析\n', ...
    '- 偏度 = %.4f → %s\n', ...
    '- 交易含义: %s\n\n', ...
    '### 5.2 峰度分析\n', ...
    '- 峰度 = %.4f → %s\n', ...
    '- 交易含义: %s\n\n', ...
    '### 5.3 尾部风险\n', ...
    '- 极端收益事件(>3σ)占比: %.2f%%\n', ...
    '- 正常分布下预期: 0.27%%\n', ...
    '- 结论: 实际极端事件频率是理论值的 %.1f 倍\n\n'], ...
    report.skewness, skew_interp{1}, skew_interp{2}, ...
    report.kurtosis, kurt_interp{1}, kurt_interp{2}, ...
    mean(abs(returns) > 3*std(returns)) * 100, ...
    mean(abs(returns) > 3*std(returns)) * 100 / 0.27)];

%% 六、策略建议
md = [md, sprintf(['## 六、策略建议\n\n', ...
    '### 6.1 当前市场适合的策略类型\n\n'], report.regime)];

if report.hurst > 0.55
    md = [md, '**趋势跟踪策略** ✓ 推荐\n\n'];
    md = [md, '- 均线交叉策略(MA Cross)\n'];
    md = [md, '- 趋势线突破策略\n'];
    md = [md, '- 动量指标策略(MACD, RSI Momentum)\n\n'];
elseif report.hurst < 0.45
    md = [md, '**均值回归策略** ✓ 推荐\n\n'];
    md = [md, '- 布林带策略\n'];
    md = [md, '- RSI 超买超卖\n'];
    md = [md, '- 统计套利\n\n'];
else
    md = [md, '**区间震荡策略** ✓ 推荐\n\n'];
    md = [md, '- 支撑阻力位交易\n'];
    md = [md, '- 波段操作\n\n'];
end

if report.arch_effect > 0.3
    md = [md, '### 6.2 波动率交易\n\n'];
    md = [md, '**波动率聚类强烈，适合:**\n'];
    md = [md, '- 买入期权策略(买gamma)\n'];
    md = [md, '- 波动率突破策略\n'];
    md = [md, '- 风险反转策略\n\n'];
else
    md = [md, '### 6.2 波动率交易\n\n'];
    md = [md, '**波动率聚类较弱:**\n'];
    md = [md, '- 波动率转化较快\n'];
    md = [md, '- 建议使用短周期期权或及时止损\n\n'];
end

if report.kurtosis > 5
    md = [md, '### 6.3 尾部风险\n\n'];
    md = [md, '⚠️ **高峰度警告**: 极端事件频繁发生\n'];
    md = [md, '- 建议使用期权对冲尾部风险\n'];
    md = [md, '- 适当降低仓位\n'];
    md = [md, '- 设置更严格的止损\n\n'];
end

%% 七、结论
md = [md, sprintf(['## 七、综合结论\n\n', ...
    '根据对 %s 至 %s 数据分析：\n\n', ...
    '**1. 市场状态**: %s\n\n', ...
    '**2. 波动特征**: 当前年化波动率 %.2f%%，%s\n\n', ...
    '**3. 记忆特性**: Hurst指数 %.4f，表明市场%s\n\n', ...
    '**4. 风险评估**: %s，建议%s\n\n', ...
    '**5. 操作建议**: %s\n\n'], ...
    ts_str, te_str, ...
    report.regime, ...
    report.current_vol, getVolDesc(report.current_vol), ...
    report.hurst, getHurstDesc(report.hurst), ...
    report.risk_level, getRiskAdvice(report.risk_level), ...
    getStrategyHint(report.hurst, report.arch_effect, report.kurtosis))];

%% 八、附录
md = [md, sprintf(['## 八、指标说明\n\n', ...
    '| 指标 | 说明 | 参考值 |\n', ...
    '|:---|:---|:---|\n', ...
    '| Hurst指数 | 衡量时间序列长期记忆性 | H>0.5趋势，H<0.5反转，H=0.5随机 |\n', ...
    '| ARCH效应 | 波动率聚类程度 | >0.3为强聚类，<0.1为弱 |\n', ...
    '| VaR | 在险价值，潜在最大损失 | 95%置信度下单日最大损失 |\n', ...
    '| 偏度 | 分布对称性 | >0右偏(正收益厚尾)，<0左偏(负收益厚尾) |\n', ...
    '| 峰度 | 尾部厚度 | >3厚尾，>5极厚尾，3为正态 |\n\n---\n\n', ...
    '*本报告由 NEMT 分析系统自动生成*\n', ...
    '*生成时间: %s*\n'], datestr(now, 'yyyy-mm-dd HH:MM:SS'))];

%% 保存文件
fid = fopen(reportFile, 'w', 'n', 'utf-8');
fwrite(fid, md);
fclose(fid);

fprintf('\n✓ 报告已保存: %s\n', reportFile);

%% 自动打开文件
if ispc
    winopen(reportFile);
end
end

%% ========== 辅助函数 ==========

function emoji = getStatusEmoji(regime)
switch regime
    case {'趋势动量市场', '稳定趋势市场'}
        emoji = '📈';
    case {'均值回归市场', '均值回归稳定'}
        emoji = '⚖️';
    case {'趋势+高波动混沌', '均值回归+高波动'}
        emoji = '🔥';
    otherwise
        emoji = '⚪';
end
end

function emoji = getRiskEmoji(risk)
if contains(risk, '高风险'), emoji = '🔴';
elseif contains(risk, '中高风险'), emoji = '🟠';
elseif contains(risk, '中低风险'), emoji = '🟡';
else, emoji = '🟢';
end
end

function status = getHurstStatus(H)
if H > 0.55, status = '📈 趋势';
elseif H < 0.45, status = '📉 反转';
else, status = '⚖️ 中性';
end
end

function status = getARCHStatus(arch)
if arch > 0.3, status = '🔥 强';
elseif arch > 0.1, status = '🟡 中';
else, status = '🟢 弱';
end
end

function status = getVolStatus(vol)
if vol > 80, status = '🔴 极高';
elseif vol > 50, status = '🟠 高';
elseif vol > 30, status = '🟡 中';
else, status = '🟢 低';
end
end

function text = interpretHurstText(H)
if H > 0.6
    text = 'H > 0.5: 存在长期记忆性，价格趋势一旦形成会持续较长时间';
elseif H > 0.5
    text = 'H > 0.5: 略偏趋势持续，但不是很强';
elseif H < 0.4
    text = 'H < 0.5: 存在均值回归特性，价格会向均值回归';
else
    text = 'H ≈ 0.5: 接近随机游走，趋势和反转概率相当';
end
end

function text = interpretARCHText(arch)
if arch > 0.4
    text = 'ARCH效应强: 波动率存在强烈聚类，高波动期后会持续一段时间';
elseif arch > 0.2
    text = 'ARCH效应中等: 波动率有一定聚类特征';
else
    text = 'ARCH效应弱: 波动率聚类不明显';
end
end

function text = interpretSkewText(skew)
if skew < -0.5
    text{1} = '强烈左偏 🔴';
    text{2} = '负收益极端事件更频繁，下跌时波动更大，风险较大';
elseif skew < -0.2
    text{1} = '轻度左偏 🟡';
    text{2} = '略偏负收益，风险略高于正收益';
elseif skew > 0.2
    text{1} = '轻度右偏 🟡';
    text{2} = '略偏正收益，收益潜力略大于风险';
else
    text{1} = '基本对称 🟢';
    text{2} = '正负收益分布较为对称';
end
end

function text = interpretKurtText(kurt)
if kurt > 7
    text{1} = '极厚尾 🔴🔴';
    text{2} = '极端事件发生频率远高于正态分布预测，风险很高';
elseif kurt > 5
    text{1} = '厚尾 🟠';
    text{2} = '极端事件发生频率高于正常水平，需要警惕';
elseif kurt > 3
    text{1} = '正常 🟡';
    text{2} = '分布接近正态，极端事件概率正常';
else
    text{1} = '薄尾 🟢';
    text{2} = '极端事件较少，分布比正态更集中';
end
end

function desc = getVolDesc(vol)
if vol > 80, desc = '波动率极高，市场极度不稳定';
elseif vol > 50, desc = '波动率高，市场活跃度高';
elseif vol > 30, desc = '波动率中等，波动正常';
else, desc = '波动率偏低，市场相对稳定';
end
end

function desc = getHurstDesc(H)
if H > 0.6, desc = '具有强趋势持续性，适合趋势跟踪';
elseif H > 0.5, desc = '略偏趋势，但强度一般';
elseif H < 0.4, desc = '具有均值回归特性，反转策略可能有效';
else, desc = '接近随机游走，短期预测困难';
end
end

function advice = getRiskAdvice(risk)
if contains(risk, '高风险'), advice = '降低仓位，谨慎操作';
elseif contains(risk, '中高风险'), advice = '适当控制仓位';
elseif contains(risk, '中低风险'), advice = '可正常操作';
else, advice = '风险较低，可适当加仓';
end
end

function hint = getStrategyHint(H, arch, kurt)
if H > 0.55 && arch > 0.3
    hint = '趋势+波��率交易策略';
elseif H > 0.55
    hint = '趋势跟踪策略';
elseif H < 0.45 && arch > 0.3
    hint = '均值回归 + 波动率交易';
elseif H < 0.45
    hint = '均值回归策略';
elseif kurt > 5
    hint = '尾部对冲 + 轻仓操作';
else
    hint = '区间震荡 + 短周期操作';
end
end