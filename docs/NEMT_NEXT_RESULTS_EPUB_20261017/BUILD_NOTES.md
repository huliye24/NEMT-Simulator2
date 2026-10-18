# 构建与验证记录

- RiverType：0.1.0
- 语言：zh-Hans
- 版式：A5 流式 EPUB
- 主题：`nemt-results`
- 正文：1 章，4 张正式实验图
- 来源：云端正式运行 `20261017T073704Z`、`FINAL_REPORT.md`、verdict CSV、manifest 与正式图件
- 产物：`output/NEMT_Exp4_Gate_Result_2026-10-17.epub`

## 来源完整性

正式运行目录共 36 个文件（含 `SHA256SUMS.txt`）。本地按清单复算全部正式产物，结果一致。

## 检查结果

RiverType 内置检查完成：0 errors、1 warning。唯一警告是本机无 Java，未运行官方 EPUBCheck。内置检查已覆盖容器、OPF、manifest、spine、导航、内部链接、资源与图片替代文本。

使用 Calibre 7.21.0 独立转换为 14 页 A5 PDF，抽查第 1、2、4、7、10、13 页及四张图。标题、判定表、正文、图件、结论与末页均正常；未发现图片缺失、字符替换、裁切、重叠或标题孤行。

## 经验回流

本书沿用中文技术 EPUB 的既有主题经验：标题 keep-with-next、段落 widows/orphans、不使用 `text-justify: inter-ideograph`。暂未发现新的跨项目 RiverType 缺陷；若构建或检查出现新问题，再写入经验台账。
