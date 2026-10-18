// 由 rivertype assemble 生成 — NEMT 三项数值实验结论
// 用 ESM 导出（export default），在 CommonJS 与 "type": "module" 仓库内都能被 vivliostyle 加载
export default {
    title: "NEMT 三项数值实验结论",
    author: "NEMT Simulator Research",
    language: "zh-Hans",
    size: "A5",
    entry: [
        { path: "chapters/01-conclusions.md" },
    ],
    theme: "style.css",
    output: [
        {
            path: "../output/NEMT_MATLAB_Experiment_Conclusions_2026-10-17.epub",
            format: "epub"
        }
    ]
};
