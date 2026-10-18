"use client";

import { useState } from "react";
import type { StudioPageProps } from "../types";
import styles from "./ExecutionPage.module.css";

type StrategyState="运行中"|"已暂停";
interface Position {symbol:string;market:string;side:string;size:string;entry:string;mark:string;pnl:string;returnValue:string;margin:string;strategy:string;code:string;timeframe:string;state:StrategyState;signal:string;risk:string;}
const INITIAL:Position[]=[
  {symbol:"BTC/USDT",market:"PERPETUAL",side:"LONG",size:"0.042 BTC",entry:"81,944.20",mark:"82,176.80",pnl:"+9.77 USDT",returnValue:"+0.28%",margin:"6.8%",strategy:"NEMT Momentum",code:"EMG-01 · v1.8",timeframe:"15m",state:"运行中",signal:"17:42 加仓",risk:"62%"},
  {symbol:"ETH/USDT",market:"PERPETUAL",side:"SHORT",size:"0.61 ETH",entry:"3,128.40",mark:"3,119.70",pnl:"+5.31 USDT",returnValue:"+0.27%",margin:"4.2%",strategy:"Mean Revert 21",code:"MR-21 · v2.3",timeframe:"1h",state:"已暂停",signal:"等待人工确认",risk:"18%"},
  {symbol:"BTC-PERP",market:"HEDGE",side:"NEUTRAL",size:"0.018 BTC",entry:"82,010.00",mark:"82,176.80",pnl:"-3.00 USDT",returnValue:"-0.20%",margin:"2.9%",strategy:"Basis Neutral",code:"ARB-04 · v1.2",timeframe:"1h",state:"运行中",signal:"17:38 再平衡",risk:"34%"},
];

export default function ExecutionPage({notify}:StudioPageProps){
  const [positions,setPositions]=useState(INITIAL);
  const [selected,setSelected]=useState("BTC/USDT");
  const [tab,setTab]=useState("活跃订单");
  function toggle(symbol:string){setPositions(current=>current.map(item=>item.symbol===symbol?{...item,state:item.state==="运行中"?"已暂停":"运行中"}:item));const item=positions.find(position=>position.symbol===symbol);notify("success",`${item?.strategy} 已${item?.state==="运行中"?"暂停":"启动"}`)}
  return <div className={styles.page}>
    <section className={styles.book}><div className={styles.bookHead}><div><strong>当前持仓</strong><span>03 POSITIONS · 03 STRATEGIES ATTACHED</span></div><div className={styles.legend}><i/> 策略运行中 <i className={styles.paused}/> 已暂停</div></div>
      <div className={styles.positionHeader}><span>合约 / 方向</span><span>持仓</span><span>入场 / 标记</span><span>未实现盈亏</span><span>保证金</span><span>绑定策略与操作</span></div>
      {positions.map(item=><article key={item.symbol} className={`${styles.position} ${selected===item.symbol?styles.selected:""}`} onClick={()=>setSelected(item.symbol)}>
        <div className={styles.instrument}><span>{item.market}</span><strong>{item.symbol}</strong><b className={item.side==="SHORT"?styles.short:""}>{item.side}</b></div>
        <Value label="POSITION" value={item.size}/><Value label="PRICES" value={item.entry} note={item.mark}/><Value label="P&L" value={item.pnl} note={item.returnValue} tone={item.pnl.startsWith("+")?"good":"bad"}/><Value label="MARGIN" value={item.margin}/>
        <div className={styles.strategy}><div className={styles.strategyIdentity}><span className={item.state==="运行中"?styles.live:styles.hold}><i/>{item.state}</span><strong>{item.strategy}</strong><small>{item.code} · {item.timeframe} · Risk {item.risk}</small><em>{item.signal}</em></div><div className={styles.strategyActions}><button onClick={event=>{event.stopPropagation();notify("info",`打开 ${item.strategy} 编辑器`)}}>编辑</button><button className={item.state==="运行中"?styles.pause:styles.start} onClick={event=>{event.stopPropagation();toggle(item.symbol)}}>{item.state==="运行中"?"暂停":"启动"}</button><button onClick={event=>event.stopPropagation()}>日志</button></div></div>
      </article>)}
    </section>
    <div className={styles.lower}><section className={styles.details}><div className={styles.tabs}>{["活跃订单","成交记录","策略事件","参数调整","风控事件"].map(item=><button key={item} className={tab===item?styles.active:""} onClick={()=>setTab(item)}>{item}</button>)}</div><table><thead><tr><th>TIME</th><th>SYMBOL</th><th>STRATEGY</th><th>TYPE</th><th>SIZE</th><th>PRICE</th><th>STATUS</th></tr></thead><tbody><tr><td>17:42:08</td><td>BTC/USDT</td><td>EMG-01</td><td>LIMIT BUY</td><td>0.011 BTC</td><td>81,988.20</td><td><b className={styles.goodText}>FILLED</b></td></tr><tr><td>17:38:41</td><td>BTC-PERP</td><td>ARB-04</td><td>REBALANCE</td><td>0.006 BTC</td><td>82,104.10</td><td><b className={styles.waitText}>PARTIAL</b></td></tr></tbody></table></section></div>
  </div>
}
function Value({label,value,note,tone}:{label:string;value:string;note?:string;tone?:"good"|"bad"}){return <div className={styles.value}><span>{label}</span><strong className={tone?styles[`${tone}Text`]:""}>{value}</strong>{note?<small>{note}</small>:null}</div>}
