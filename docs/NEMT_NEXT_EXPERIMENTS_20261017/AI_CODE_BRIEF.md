# 给代码 AI 的实现契约

## 任务

只实现本目录冻结的实验四、五、六，不修改科学判据。可修复实现错误，但必须保留日志、补回归测试并完整重跑受影响实验。

## 推荐结构

```text
next_experiments_20261017/
  core/                         # 复用上一组已验证函数；新增函数必须有测试
  exp4_fixed_step_stability/
  exp5_observable_robustness/
  exp6_btc_oos_h001/
  tests/
  output/
  run_next_experiments.m
```

## 必须先写的测试

1. 参数写入测试：不同 `(alpha,beta)` 必须实际改变求解器输入，防止 MI 缺陷重现。
2. 时间对齐测试：特征时间 `t` 只能使用 `≤t` 数据，标签必须严格来自 `t+1...t+H`。
3. 求解器黄金样本测试：上一组 C5 文件逐点一致。
4. 指标解析样本：正弦波、白噪声、chirp 的谱熵/质心/尾部质量方向正确。
5. 固定 seed 可重复测试：同配置两次运行的 CSV 哈希一致。
6. 快速模式只缩小网格，不改变公式、阈值和列名。

## 运行门

`run_next_experiments.m` 先跑测试，再跑实验四；C4.3/C4.5 失败则停止。实验五没有指标通过 C5.1–C5.4 时，实验六标记 BLOCKED。实验六测试段只允许一次确认性运行；调试应使用训练段的截断副本。

## 输出要求

- CSV 为 UTF-8，浮点数保留至少 15 位有效数字。
- `config.json` 写出参数、seed、Git commit、MATLAB 版本和输入文件哈希。
- `verdict.csv` 固定列：`criterion,observed,threshold,status,notes`。
- 图只从已保存 CSV 重建，禁止图与 CSV 各算一遍。
- 最终生成 `run_manifest.json` 和 `SHA256SUMS.txt`。

