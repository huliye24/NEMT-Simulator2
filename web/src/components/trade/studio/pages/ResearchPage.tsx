"use client";

import { useMemo, useState } from "react";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";
import styles from "./ResearchPage.module.css";

interface NoteItem { id:string; code:string; title:string; kind:"研究"|"报告"|"实验记录"; updated:string; }
const NOTES:NoteItem[]=[
  {id:"critical",code:"R-024",title:"临界点后的动量延续",kind:"研究",updated:"刚刚"},
  {id:"entropy",code:"R-019",title:"低熵区间的突破质量",kind:"研究",updated:"2h"},
  {id:"decay",code:"REP-12",title:"Q3 相位策略研究报告",kind:"报告",updated:"昨天"},
  {id:"volume",code:"EXP-41",title:"成交量过滤参数实验",kind:"实验记录",updated:"3d"},
  {id:"noise",code:"R-011",title:"噪声过滤阈值比较",kind:"研究",updated:"5d"},
  {id:"basis",code:"EXP-38",title:"永续基差状态扫描",kind:"实验记录",updated:"1w"},
];

const INITIAL_MARKDOWN=`# 临界点后的动量延续

> 状态：研究中  ·  市场：BTC/USDT  ·  周期：15m

## 研究问题

当市场从稳定态进入 \`critical_up\`，相位一致性与成交量扩张同时出现时，后续 12 根 K 线的趋势延续概率是否显著提升？

## 核心假设

临界点并不是单一价格信号。只有当以下条件共同出现时，动量延续才具有可交易性：

- 相位一致性高于 **0.80**
- 成交量超过过去 20 日的 **65% 分位数**
- 波函数斜率保持正向至少 3 个观察窗口

## 实验记录

### EXP-041 · MATLAB Cloud

- 数据范围：2026-04-01 → 2026-09-30
- 样本数量：1,284
- 参数文件：\`critical_momentum_v03.m\`
- 运行状态：已完成

初步结果显示，加入成交量过滤后命中率由 58.7% 提升至 68.4%，但低流动性时段仍然存在明显衰减。

## 下一步

1. 加入 UTC 时段过滤。
2. 比较 5m、15m 与 1h 三个尺度。
3. 将结果整理为正式研究报告。`;

export default function ResearchPage({ navigate: _navigate }:StudioPageProps){
  const [selectedId,setSelectedId]=useState("critical");
  const [query,setQuery]=useState("");
  const [markdown,setMarkdown]=useState(INITIAL_MARKDOWN);
  const [preview,setPreview]=useState(false);
  const filtered=useMemo(()=>NOTES.filter(n=>`${n.code}${n.title}${n.kind}`.toLowerCase().includes(query.toLowerCase())),[query]);
  const selected=NOTES.find(n=>n.id===selectedId)??NOTES[0];
  return <div className={styles.page}>
    <section className={styles.workspace}>
      <aside className={styles.library}><div className={styles.searchBar}><label className={styles.search}><StudioIcon name="research" size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} aria-label="搜索文档"/></label><button type="button" className={styles.newDoc} title="新建文档" aria-label="新建文档"><StudioIcon name="plus" size={16}/></button></div><div className={styles.noteList}>{filtered.map(note=><button key={note.id} type="button" className={selected.id===note.id?styles.selectedNote:""} onClick={()=>setSelectedId(note.id)}><strong>{note.title}</strong><small>更新于 {note.updated}</small></button>)}</div></aside>
      <main className={styles.editor}>
        <div className={styles.toolbar}><button title="标题">H</button><button title="粗体"><b>B</b></button><button title="引用">❞</button><button title="链接">↗</button><button title="代码">&lt;/&gt;</button><span/><div className={styles.editorModes}><button type="button" className={!preview?styles.activeMode:""} onClick={()=>setPreview(false)}>编辑</button><button type="button" className={preview?styles.activeMode:""} onClick={()=>setPreview(true)}>预览</button></div></div>
        {preview?<article className={styles.preview}><h1>临界点后的动量延续</h1><blockquote>状态：研究中 · 市场：BTC/USDT · 周期：15m</blockquote><h2>研究问题</h2><p>当市场从稳定态进入 <code>critical_up</code>，相位一致性与成交量扩张同时出现时，后续 12 根 K 线的趋势延续概率是否显著提升？</p><h2>核心假设</h2><p>临界点并不是单一价格信号。只有相位一致性、成交量扩张和波函数斜率共同出现时，动量延续才具有可交易性。</p><h2>实验记录</h2><h3>EXP-041 · MATLAB Cloud</h3><p>初步结果显示，加入成交量过滤后命中率由 58.7% 提升至 68.4%，但低流动性时段仍存在明显衰减。</p><h2>下一步</h2><ol><li>加入 UTC 时段过滤。</li><li>比较 5m、15m 与 1h 三个尺度。</li><li>整理为正式研究报告。</li></ol></article>:<textarea className={styles.markdown} value={markdown} onChange={e=>setMarkdown(e.target.value)} spellCheck={false} aria-label="Markdown 研究笔记"/>}
      </main>
    </section>
  </div>
}

