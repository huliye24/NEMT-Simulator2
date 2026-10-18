"use client";

import { useMemo, useState } from "react";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";
import styles from "./ExperimentsPage.module.css";

interface ExperimentRecord { id:string; code:string; title:string; kind:"MATLAB"|"GPU"; status:"已完成"|"分析中"|"设计中"; updated:string; }
const RECORDS:ExperimentRecord[]=[
  {id:"041",code:"EXP-041",title:"临界点动量参数扫描",kind:"GPU",status:"已完成",updated:"今天"},
  {id:"044",code:"EXP-044",title:"多尺度周期稳健性",kind:"MATLAB",status:"分析中",updated:"昨天"},
  {id:"047",code:"EXP-047",title:"UTC 时段过滤研究",kind:"GPU",status:"设计中",updated:"3 天前"},
  {id:"038",code:"EXP-038",title:"永续基差状态扫描",kind:"MATLAB",status:"已完成",updated:"1 周前"},
];

export default function ExperimentsPage({navigate}:StudioPageProps){
  const [selectedId,setSelectedId]=useState("041");
  const [filter,setFilter]=useState<"全部"|"MATLAB"|"GPU">("全部");
  const records=useMemo(()=>RECORDS.filter(record=>filter==="全部"||record.kind===filter),[filter]);
  const selected=RECORDS.find(record=>record.id===selectedId)??RECORDS[0];
  return <div className={styles.page}>
    <header className={styles.header}><div><p>WORKSPACE / EXPERIMENT ARCHIVE</p><h1>实验档案</h1><span>记录实验设计、云端环境、结果与可复现产物。</span></div><div className={styles.headerMeta}><span><i/> GPU CLOUD · ARCHIVE MODE</span><button type="button" className="ns-btn ns-btn-dark ns-btn-sm">+ 新建实验设计</button></div></header>
    <section className={styles.workspace}>
      <aside className={styles.index}><div className={styles.panelTitle}><span>01</span><div><strong>实验索引</strong><em>EXPERIMENT INDEX</em></div></div><label className={styles.search}><StudioIcon name="experiments" size={14}/><input placeholder="搜索实验设计或结果"/></label><div className={styles.filters}>{(["全部","MATLAB","GPU"] as const).map(item=><button key={item} type="button" className={filter===item?styles.activeFilter:""} onClick={()=>setFilter(item)}>{item}</button>)}</div><div className={styles.list}>{records.map(record=><button key={record.id} type="button" className={selected.id===record.id?styles.selected:""} onClick={()=>setSelectedId(record.id)}><span><b>{record.code}</b><em>{record.kind}</em></span><strong>{record.title}</strong><small>{record.status} · {record.updated}</small></button>)}</div><button type="button" className={styles.researchLink} onClick={()=>navigate("research")}>关联研究文档 <StudioIcon name="chevronRight" size={12}/></button></aside>
      <article className={styles.dossier}>
        <div className={styles.dossierHead}><div><span>{selected.code} / {selected.kind}</span><h2>{selected.title}</h2><p>关联研究 R-024 · 临界点后的动量延续</p></div><strong className={styles.status}>{selected.status}</strong></div>
        <section className={styles.abstract}><span>ABSTRACT</span><p>验证相位一致性、成交量扩张与动量延续之间的联合关系，并评估参数在不同时间尺度和市场状态下的稳健性。</p></section>
        <div className={styles.columns}>
          <div className={styles.protocol}><SectionHeading index="02" title="实验设计" caption="PROTOCOL"/><InfoBlock title="研究问题"><p>临界状态形成后，加入成交量过滤是否能显著提高未来 12 根 K 线的方向命中率？</p></InfoBlock><InfoBlock title="变量与对照"><dl><div><dt>自变量</dt><dd>相位一致性阈值、成交量分位数</dd></div><div><dt>因变量</dt><dd>12-bar 延续命中率与最大不利偏移</dd></div><div><dt>对照组</dt><dd>不使用成交量过滤的基础模型</dd></div></dl></InfoBlock><InfoBlock title="方法"><ol><li>冻结数据集版本与预处理配置。</li><li>在 GPU 云端完成 1,024 组参数扫描。</li><li>使用 walk-forward 分割，避免未来信息泄漏。</li><li>保存随机种子、环境清单与结果摘要。</li></ol></InfoBlock><div className={styles.environment}><span>COMPUTE ENVIRONMENT</span><div><b>GPU Cloud</b><small>NVIDIA A100 · MATLAB R2026a</small></div><div><b>Dataset</b><small>BTCUSDT-15M · ds_2026q3_v4</small></div><div><b>Reproducibility</b><small>seed 24041 · env locked</small></div></div></div>
          <div className={styles.results}><SectionHeading index="03" title="实验结果" caption="RESULTS & ARTIFACTS"/><div className={styles.resultLead}><span>PRIMARY OUTCOME</span><strong>+9.7<small> pp</small></strong><p>加入成交量过滤后的命中率提升</p></div><div className={styles.metrics}><Metric label="BASELINE" value="58.7%"/><Metric label="FILTERED" value="68.4%"/><Metric label="MAX DD" value="9.8%"/><Metric label="SAMPLES" value="1,284"/></div><InfoBlock title="结论"><p>主要假设得到支持，但提升集中在 UTC 08:00–20:00。低流动性时段仍出现明显衰减，下一轮应加入时段过滤并做跨周期复验。</p></InfoBlock><InfoBlock title="限制"><p>当前仅覆盖 BTC/USDT，且交易成本使用固定费率模型；结果不能直接外推至低流动性资产。</p></InfoBlock><div className={styles.artifacts}><header><strong>研究产物</strong><span>04 FILES</span></header><Artifact name="result_summary.md" type="报告"/><Artifact name="metrics.parquet" type="数据"/><Artifact name="critical_scan.m" type="脚本"/><Artifact name="environment.lock" type="环境"/></div></div>
        </div>
      </article>
    </section>
  </div>
}

function SectionHeading({index,title,caption}:{index:string;title:string;caption:string}){return <div className={styles.sectionHeading}><span>{index}</span><div><strong>{title}</strong><em>{caption}</em></div></div>}
function InfoBlock({title,children}:{title:string;children:React.ReactNode}){return <section className={styles.infoBlock}><h3>{title}</h3>{children}</section>}
function Metric({label,value}:{label:string;value:string}){return <div><span>{label}</span><strong>{value}</strong></div>}
function Artifact({name,type}:{name:string;type:string}){return <button type="button"><span>↗</span><strong>{name}</strong><em>{type}</em></button>}
