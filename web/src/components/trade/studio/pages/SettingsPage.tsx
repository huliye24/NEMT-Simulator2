"use client";

import { useState } from "react";
import { StudioIcon } from "../icons";
import type { StudioPageProps } from "../types";
import styles from "./SettingsPage.module.css";

interface SettingsPageProps extends StudioPageProps { onLogout:()=>Promise<void>; }

export default function SettingsPage({session,data,onLogout}:SettingsPageProps){
  const [logoutBusy,setLogoutBusy]=useState(false);
  const initials=session.user.username.slice(0,2).toUpperCase();
  async function handleLogout(){if(logoutBusy)return;setLogoutBusy(true);try{await onLogout()}finally{setLogoutBusy(false)}}
  return <div className={styles.page}>
    <section className={styles.account}>
      <div className={styles.avatar}>{initials}</div>
      <div className={styles.identity}><span>ACCOUNT PROFILE</span><h1>{session.user.username}</h1><p>{session.user.roles.join(" · ")}</p></div>
      <div className={styles.session}><span><i className={data.online?styles.online:styles.offline}/>{data.online?"已登录":"连接中"}</span><strong>{session.mode}</strong></div>
    </section>
    <section className={styles.loginCard}>
      <div className={styles.loginIcon}><StudioIcon name="shield" size={21}/></div>
      <div><span>LOGIN SESSION</span><h2>当前登录</h2><p>你正在以 <strong>{session.user.username}</strong> 的身份使用 emergentix。</p></div>
      <button type="button" onClick={()=>void handleLogout()} disabled={logoutBusy}><StudioIcon name="logout" size={15}/>{logoutBusy?"正在退出…":"退出登录"}</button>
    </section>
    <p className={styles.note}>退出后将返回登录界面。本页不保存交易环境、服务器或风控配置。</p>
  </div>
}
