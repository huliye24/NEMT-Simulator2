$ErrorActionPreference = 'Stop'

$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$chapters = Join-Path $project 'manuscript\chapters'
$macroRoot = 'E:\文川院\01 学科母体\10 宏观趋势调度学'
$legacyRoot = 'E:\荣景文川知识库_旧软件开发归档_20261012\01-项目\NEMT Quant OS\04-理论'

function Find-Source([string]$name) {
    $hit = Get-ChildItem -LiteralPath $macroRoot -Recurse -File -Filter $name | Select-Object -First 1
    if (-not $hit) { throw "Missing source: $name" }
    return $hit.FullName
}

function Read-Utf8([string]$path) {
    return [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
}

function Write-Utf8([string]$name, [string]$text) {
    $path = Join-Path $chapters $name
    [System.IO.File]::WriteAllText($path, ($text.Trim() + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
}

function Convert-TablesToText([string]$text) {
    $lines = $text -split "`r?`n"
    $result = New-Object System.Collections.Generic.List[string]
    $i = 0
    $inFence = $false
    while ($i -lt $lines.Count) {
        if ($lines[$i] -match '^```') {
            $inFence = -not $inFence
            $result.Add($lines[$i]); $i++; continue
        }
        if (-not $inFence -and $lines[$i] -match '^\s*\|.*\|\s*$') {
            $start = $i
            $block = New-Object System.Collections.Generic.List[string]
            while ($i -lt $lines.Count -and $lines[$i] -match '^\s*\|.*\|\s*$') {
                $block.Add($lines[$i]); $i++
            }
            $isTable = $block | Where-Object { $_ -match '^\s*\|\s*:?-{3,}' }
            if ($isTable) {
                $result.Add('```text')
                foreach ($line in $block) {
                    if ($line -notmatch '^\s*\|\s*:?-{3,}') { $result.Add($line) }
                }
                $result.Add('```')
            } else {
                foreach ($line in $block) { $result.Add($line) }
            }
            continue
        }
        $result.Add($lines[$i]); $i++
    }
    return ($result -join "`r`n")
}

function Condense-StructuredMarkdown([string]$text, [int]$limit) {
    if ($text.Length -le $limit) { return $text }
    $sections = [regex]::Split($text, '(?m)(?=^## )') | Where-Object { $_.Trim() }
    if ($sections.Count -eq 0) { return $text.Substring(0, [Math]::Min($limit, $text.Length)) }
    $quota = [Math]::Max(130, [Math]::Floor($limit / $sections.Count))
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($section in $sections) {
        $blocks = [regex]::Split($section.Trim(), '\r?\n\s*\r?\n') | Where-Object { $_.Trim() }
        if ($blocks.Count -eq 0) { continue }
        $out.Add($blocks[0].Trim())
        $used = $blocks[0].Length
        $chosen = New-Object System.Collections.Generic.HashSet[int]
        for ($i = 1; $i -lt $blocks.Count; $i++) {
            if ($blocks[$i] -match '公式|定义|原则|规则|阈值|伪代码|=|→|```|状态|输出|风险') {
                if (($used + $blocks[$i].Length) -le ($quota + 180)) {
                    $out.Add($blocks[$i].Trim()); [void]$chosen.Add($i); $used += $blocks[$i].Length
                }
            }
        }
        for ($i = 1; $i -lt $blocks.Count -and $used -lt $quota; $i++) {
            if (-not $chosen.Contains($i) -and ($used + $blocks[$i].Length) -le ($quota + 100)) {
                $out.Add($blocks[$i].Trim()); $used += $blocks[$i].Length
            }
        }
    }
    return ($out -join "`r`n`r`n")
}

function Adapt-Chapter([string]$title, [string]$sourceName, [string]$lead, [int]$limit = 3200) {
    $text = Read-Utf8 (Find-Source $sourceName)
    $text = [regex]::Replace($text, '(?m)^# .+\r?\n', '')
    $text = [regex]::Replace($text, '(?ms)^## 副标题\s*.*?(?=^## )', '')
    $text = [regex]::Replace($text, '(?ms)^## 摘要\s*.*?(?=^## )', '')
    $text = [regex]::Replace($text, '(?ms)^## 关键词.*?(?=^## )', '')
    $text = [regex]::Replace($text, '(?ms)^## 参考资料.*$', '')
    $text = [regex]::Replace($text, '(?ms)^## 免责声明.*$', '')
    return "# $title`r`n`r`n$lead`r`n`r`n$text"
}

# Remove the old short-edition chapter set. The output directory is regenerated from this source set.
Get-ChildItem -LiteralPath $chapters -File -Filter '*.md' | Remove-Item -Force

$contents = @'
# NEMT 非平衡市场与宏观趋势调度理论

<p class="book-author">朱泫榛　著</p>

<p class="book-edition">理论整合版 1.0</p>

本书建立一套面向个人量化投资的可证伪框架：以宏观趋势决定战略方向，以市场状态决定资金姿态，以非平衡结构指标识别局部形态，以仓位调度和风险预算约束行动，并以回测、反证和复盘形成闭环。

## 全书结构

- 第一编　非平衡市场的理论基础
- 第二编　宏观趋势与市场状态
- 第三编　从市场判断到资本调度
- 第四编　NEMT 算法与系统工程
- 第五编　回测、反证与理论进化

> 本书讨论的是研究框架与系统工程，不构成投资建议。任何模型输出均不能替代风险评估、样本外验证和个人责任。
'@
Write-Utf8 '00-title.md' $contents

Write-Utf8 '01-part-one.md' "# 第一编　非平衡市场的理论基础`r`n`r`n从市场不可约的不确定性出发，建立趋势、状态、波动与噪声的概念边界，并说明 NLS、DCI、涡旋与随机共振在整个 NEMT 中应处的位置。"
Write-Utf8 '02-ch01.md' (Adapt-Chapter '第一章　从预测涨跌到调度不确定性' '宏观趋势调度学总论：从比特币市场到资金配置系统.md' 'NEMT 的研究对象不是下一根 K 线，而是在开放、非平衡和强反馈市场中，如何把不完整信息转换为受约束的资金动作。')
Write-Utf8 '03-ch02.md' (Adapt-Chapter '第二章　趋势、波动与噪声' 'R-003 趋势、波动与噪音的区别.md' '趋势提供方向，波动描述路径，噪声构成不可行动的信息。三者混淆，是量化系统频繁失效的首要原因。')

$nls = Read-Utf8 (Join-Path $legacyRoot 'NEMT理论.md')
$nls = [regex]::Replace($nls, '(?m)^# .+\r?\n', '')
$nls += "`r`n`r`n## 建模边界`r`n`r`nNLS 是市场结构的生成性假说，而不是宣称市场服从量子力学。ψ、α、β 与 η 必须对应可观测量；参数必须通过滚动估计与样本外检验识别；数值稳定性必须先于经济解释。MATLAB 理论实验负责求解器、边界条件、参数区域和灵敏度，交易系统只消费经过验证的结构特征。"
Write-Utf8 '04-ch03.md' ("# 第三章　非线性薛定谔市场模型`r`n`r`n" + $nls)

$signals = Read-Utf8 (Join-Path $legacyRoot '信号指标.md')
$signals = [regex]::Replace($signals, '(?m)^# .+\r?\n', '')
Write-Utf8 '05-ch04.md' ("# 第四章　DCI、涡旋与随机共振`r`n`r`n这些量不是独立的买卖按钮，而是描述局部有序度、能量聚集与噪声协同的结构观测量。`r`n`r`n" + $signals)

$phases = Read-Utf8 (Join-Path $legacyRoot '四相位.md')
$phases = [regex]::Replace($phases, '(?m)^# .+\r?\n', '')
Write-Utf8 '06-ch05.md' ("# 第五章　四相位状态机与尺度问题`r`n`r`n" + $phases + "`r`n`r`n## 与宏观 Regime 的关系`r`n`r`n四相位描述较短尺度上的结构演化，宏观 Regime 描述中长期资本环境。前者不能推翻后者，只能改变执行节奏和局部置信度。")

Write-Utf8 '07-part-two.md' "# 第二编　宏观趋势与市场状态`r`n`r`n将流动性、利率、美元、风险偏好、价格结构、资金流、链上供需、杠杆与情绪压缩为可解释的状态对象。"
Write-Utf8 '08-ch06.md' (Adapt-Chapter '第六章　宏观趋势引擎' 'Macro_Trend_Engine的设计_耶鲁格式中文.md' '宏观趋势引擎不是预测器，而是战略层状态压缩器。它把异质变量转化为趋势支持分与风险约束分。')
Write-Utf8 '09-ch07.md' (Adapt-Chapter '第七章　市场状态分类器' 'Market_Regime_Classifier的建模方法_耶鲁格式中文.md' '市场状态分类器位于判断与行动之间：先识别阶段，再解释信号，最后决定资金姿态。')
Write-Utf8 '10-ch08.md' (Adapt-Chapter '第八章　流动性、美元与利率周期' '全球流动性扩张与加密资产牛市的关系_耶鲁格式中文.md' '流动性并不机械决定价格，但它规定风险资产扩张或收缩的上层环境。')
Write-Utf8 '11-ch09.md' (Adapt-Chapter '第九章　风险偏好与高波动资产定价' '风险偏好周期与高波动资产定价_耶鲁格式中文.md' '比特币的方向不能脱离全球风险预算、波动率与信用条件单独理解。')
Write-Utf8 '12-ch10.md' (Adapt-Chapter '第十章　牛熊阶段、反转与假信号' '趋势反转中的假信号问题_耶鲁格式中文.md' '反转不是一个点，而是旧状态衰减、新状态竞争和确认逐步累积的过程。')

Write-Utf8 '13-part-three.md' "# 第三编　从市场判断到资本调度`r`n`r`n市场判断只有进入资产权重、风险预算和再平衡规则，才构成量化投资闭环。"
Write-Utf8 '14-ch11.md' (Adapt-Chapter '第十一章　从交易信号到资金调度' 'R-005 从交易信号到资金调度：投资系统的层级跃迁.md' 'NEMT 的核心产物不是 BUY 或 SELL，而是市场状态、目标权重、风险边界和行动理由。')
Write-Utf8 '15-ch12.md' (Adapt-Chapter '第十二章　资产配置引擎' '资产配置引擎如何服务于比特币趋势交易_耶鲁格式中文.md' '资产配置引擎把状态概率翻译成 BTC、ETH、稳定币、现金和高 Beta 风险敞口。')
Write-Utf8 '16-ch13.md' (Adapt-Chapter '第十三章　BTC、ETH 与稳定币组合模型' 'BTC_ETH与稳定币的组合配置模型_耶鲁格式中文.md' '分散化不能只看资产名称，而要检验压力期相关性、流动性和稳定币尾部风险。')
Write-Utf8 '17-ch14.md' (Adapt-Chapter '第十四章　进攻、防守与现金状态' '进攻仓位_防守仓位与现金仓位的动态切换_耶鲁格式中文.md' '仓位不是预测信心的线性放大，而是风险预算在不同市场状态下的离散表达。')
Write-Utf8 '18-ch15.md' (Adapt-Chapter '第十五章　趋势增强、衰减与分步调仓' '趋势增强时加仓_趋势衰减时减仓的系统模型_耶鲁格式中文.md' '调仓采用阈值、滞回、最大单步调整和冷却期，避免状态噪声被放大为交易成本。')
Write-Utf8 '19-ch16.md' (Adapt-Chapter '第十六章　自动调仓、执行与风险边界' '从宏观判断到自动调仓_NEMT的策略路径_耶鲁格式中文.md' '自动调仓不是无人监管的自动交易，而是受风险约束、可暂停、可追溯的组合再平衡。')

Write-Utf8 '20-part-four.md' "# 第四编　NEMT 算法与系统工程`r`n`r`n把理论对象落实为稳定接口、公式、数据契约、服务边界与可复现实验。"
Write-Utf8 '21-ch17.md' (Adapt-Chapter '第十七章　NEMT 系统总公式' 'WCAE-MTS-FORM-001_NEMT系统总公式.md' '本章集中给出状态变量、评分函数、分类规则、目标权重、风险约束、绩效函数和参数更新公式。' 12000)
Write-Utf8 '22-ch18.md' (Adapt-Chapter '第十八章　理论到软件模块的映射' 'WCAE-MTS-XMAP-001_宏观趋势调度学到NEMT系统映射.md' '每一个理论名词都必须落入数据字段、函数接口、测试断言和日志事件，否则仍停留在叙事层。' 6000)

$architecture = @'
# 第十九章　双实验室架构与计算分工

## 19.1 理论云与实测云

NEMT 采用双缓冲实验架构。MATLAB 云服务器承担理论侧实验：NLS 数值求解、参数扫描、稳定域、谱分析、敏感性与可辨识性。A10 GPU 服务器承担实测侧实验：大规模特征计算、模型训练、多资产多周期回测、滚动验证和消融实验。

```text
MATLAB 理论实验室
  方程 → 参数域 → 稳定性 → 候选结构特征
                       ↓ 版本化实验包
A10 实测实验室
  数据 → 特征 → 状态分类 → 策略 → 回测 → 样本外验证
                       ↓ 证据与失败案例
研究反馈回路
  保留 / 修正 / 降权 / 否证
```

## 19.2 实验契约

两个环境不能依靠人工复制结果。每个实验包至少包含：理论版本、代码提交、数据快照标识、参数、随机种子、时间区间、输出字段、评价指标和失败条件。MATLAB 输出的是候选特征和统计性质，不直接输出订单；A10 输出的是经验验证结果，不反向篡改理论定义。

## 19.3 状态对象

统一的 `MarketState` 至少包含宏观趋势、Regime、流动性、风险偏好、波动、动量、回撤风险、结构相位、置信度和时间尺度。所有下游模块只读取版本化状态，不直接跨层抓取原始数据。

## 19.4 决策日志

每次决策记录输入快照、状态概率、目标权重、风控修正、实际成交、成本、后续结果和模型版本。日志不是附属品，而是可证伪性和持续进化的基础设施。
'@
Write-Utf8 '23-ch19.md' $architecture

Write-Utf8 '24-part-five.md' "# 第五编　回测、反证与理论进化`r`n`r`n不以漂亮收益曲线证明理论，而以时间一致性、成本约束、样本外表现和失败记录判断其是否仍值得保留。"
Write-Utf8 '25-ch20.md' (Adapt-Chapter '第二十章　完整回测框架' '比特币宏观趋势调度系统的回测框架_耶鲁格式中文.md' '回测必须模拟当时可得信息、下一周期执行、手续费、滑点、调仓延迟和状态切换成本。' 6000)
Write-Utf8 '26-ch21.md' (Adapt-Chapter '第二十一章　反证、压力测试与失效条件' 'WCAE-MTS-VALIDATE-001_回测与反证验证任务清单.md' '理论不能只列支持性证据。每个核心命题必须预先声明失败条件、替代解释和停止使用的门槛。' 5000)
Write-Utf8 '27-ch22.md' (Adapt-Chapter '第二十二章　复盘、参数更新与理论边界' 'WCAE-MTS-AUDIT-001_ADV-0001产出物理论审计报告.md' 'NEMT 的终点不是自动交易，而是形成一个能记录错误、区分漂移与失效、逐步更新却不追逐噪声的研究系统。' 5000)

$afterword = @'
# 结语　从市场物理实验到个人资本操作系统

NEMT 的完整闭环由七步组成：观察数据，构造状态，识别阶段，生成目标配置，施加风险约束，模拟或执行再平衡，最后用结果反证先前判断。宏观层决定战略方向，Regime 层决定资金姿态，NLS 与结构指标提供局部信息，风险控制保留生存能力，回测与复盘阻止理论退化为信念。

这套理论仍有明确边界。宏观数据存在修订和滞后；加密市场制度持续变化；NLS 映射尚需可辨识性验证；少数完整周期不足以支撑无限复杂模型；稳定币和交易所风险无法只靠历史价格估计。因此，任何自动化都必须从研究模式进入纸面交易，再进入小资金半自动执行，最后才讨论有限权限的自动调仓。

衡量 NEMT 是否成功，不是看它能否解释所有行情，而是看它是否能持续回答四个问题：当前是什么状态；我们凭什么这样判断；在判断错误时最多损失什么；什么证据会迫使我们改变模型。
'@
Write-Utf8 '28-afterword.md' $afterword

# EPUB 3.4 rejects the legacy align attributes emitted for Markdown tables by
# the current Vivliostyle chain. Preserve table information as reflow-safe text.
Get-ChildItem -LiteralPath $chapters -File -Filter '*.md' | ForEach-Object {
    $clean = Convert-TablesToText (Read-Utf8 $_.FullName)
    [System.IO.File]::WriteAllText($_.FullName, ($clean.Trim() + "`r`n"), (New-Object System.Text.UTF8Encoding($false)))
}

$manifest = @'
title: NEMT 非平衡市场与宏观趋势调度理论
author: 朱泫榛
language: zh-Hans
size: A5
render:
  dpi: 200
  band_overlap: 0.08
transcribe:
  engine: manual
build:
  theme: nemt-theory
  format: epub
  output: NEMT_非平衡市场与宏观趋势调度理论_1.0.epub
collate: {}
'@
[System.IO.File]::WriteAllText((Join-Path $project 'book.yaml'), $manifest, (New-Object System.Text.UTF8Encoding($false)))

Write-Output "Generated $((Get-ChildItem -LiteralPath $chapters -File -Filter '*.md').Count) manuscript files."
