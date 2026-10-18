# 构建与验证记录

- 构建日期：2026-10-17
- RiverType：0.1.0
- 语言：zh-Hans
- 版式：A5 流式 EPUB
- 主题：`nemt-lab`
- 正文：1 章，含 4 张代表性实验图
- 产物：`output/NEMT_MATLAB_Experiment_Conclusions_2026-10-17.epub`

## 自动检查

RiverType 内置检查结果：0 errors；1 warning。唯一警告是本机没有可执行的 Java，因此未运行官方 EPUBCheck 5.4.0。已定位 EPUBCheck JAR，但缺少 Java 运行时。

内置检查覆盖 ZIP、OPF、manifest、spine、导航、内部链接、资源与图片替代文本。首次检查发现章节中的四个图片路径缺少 `../`，已修复并通过复检。

## 独立阅读环境抽查

使用 Calibre 7.21.0 将 EPUB 独立转换为 17 页 A5 PDF，并抽查第 1、2、3、4、7、10、13、17 页。标题、表格、正文、列表、四张图和末页目录均正常；未观察到字符替换、图片缺失或标题孤行问题。

## 已接受限制

- 未运行官方 EPUBCheck，原因是本机缺少 Java；交付状态不得描述为“EPUBCheck 零错误零警告”。
- Calibre PDF 仅用于视觉抽查，不是正式交付物。
- EPUB 为实验结论整理，不替代完整 HTML 报告、CSV、代码和运行日志。

## 经验回流

本次未发现需要推广为 RiverType 核心规则的新经验。图片相对路径错误属于单书作者输入问题，现有检查器已准确拦截，修正后无需修改核心、插件或主题。
