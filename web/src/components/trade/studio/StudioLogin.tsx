"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import type { Health, Session } from "@/lib/trade/types";
import { ModePill, Spinner, StatusDot } from "./common";
import { StudioBrand, StudioIcon } from "./icons";

interface StudioLoginProps {
  onLoggedIn: (session: Session) => void;
  notice?: string | null;
}

export default function StudioLogin({ onLoggedIn, notice }: StudioLoginProps) {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState<"password" | "demo" | "admin" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    tradeApi
      .health()
      .then((next) => {
        if (!cancelled) {
          setHealth(next);
          setHealthError(null);
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setHealthError(reason instanceof Error ? reason.message : "无法连接 NEMT 服务端");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function finish(promise: Promise<Session>, kind: "password" | "demo" | "admin") {
    setPending(kind);
    setError(null);
    try {
      onLoggedIn(await promise);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "登录失败，请检查服务端状态后重试");
    } finally {
      setPending(null);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !password || pending) return;
    void finish(tradeApi.login(username.trim(), password), "password");
  }

  return (
    <div className="nemt-studio ns-login">
      <header className="ns-login-header">
        <StudioBrand />
        <div className="ns-login-header-meta">
          <span className="ns-login-header-product">Professional quant execution</span>
          <span className="ns-login-header-status">
            <StatusDot tone={health ? "ok" : healthError ? "bad" : "warn"} pulse={Boolean(health)} />
            {healthError ? "Cloud offline" : health ? "Cloud ready" : "Connecting"}
          </span>
          {health ? <ModePill mode={health.mode} /> : null}
        </div>
      </header>

      <main className="ns-login-main">
        <section className="ns-login-intro" aria-label="关于 NEMT Studio">
          <p className="ns-login-kicker">NEMT / CLOUD WORKBENCH</p>
          <h1>
            行情、风控与执行，
            <br />
            共用一条链路。
          </h1>
          <p className="ns-login-lead">
            面向数字资产量化的专业交易工作台。行情、账户、订单与服务端风控在同一个专业界面中协同。
          </p>

          <div className="ns-login-pillars">
            <div>
              <span className="ns-login-pillar-index">01</span>
              <div>
                <strong>Data first</strong>
                <p>实时行情、K 线与账户快照均来自同一云端服务。</p>
              </div>
            </div>
            <div>
              <span className="ns-login-pillar-index">02</span>
              <div>
                <strong>Precision execution</strong>
                <p>从行情校验、订单预览到二次确认，每一步清晰可追溯。</p>
              </div>
            </div>
            <div>
              <span className="ns-login-pillar-index">03</span>
              <div>
                <strong>Fail closed</strong>
                <p>预览、二次确认、幂等提交与服务端强制风控。</p>
              </div>
            </div>
          </div>

          <div className="ns-login-intro-foot">
            <StudioIcon name="lock" size={14} />
            交易所密钥仅存服务端 · 浏览器不接触凭据
          </div>
        </section>

        <section className="ns-login-form-wrap" aria-label="登录">
          <div className="ns-login-card">
            <div className="ns-login-card-head">
              <span className="ns-login-card-mark">
                <StudioIcon name="shield" size={19} />
              </span>
              <div>
                <h2>登录 NEMT Studio</h2>
                <p>使用账户密码，或进入 DEMO 模拟环境。</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="ns-login-form">
              <label className="ns-field">
                <span className="ns-field-label">账户</span>
                <span className="ns-input-wrap">
                  <input
                    className="ns-input"
                    autoComplete="username"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    placeholder="输入账户名"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    disabled={Boolean(pending)}
                  />
                </span>
              </label>

              <label className="ns-field">
                <span className="ns-field-label">密码</span>
                <span className="ns-input-wrap">
                  <input
                    className="ns-input ns-input-with-action"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="输入密码"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    disabled={Boolean(pending)}
                  />
                  <button
                    type="button"
                    className="ns-input-action"
                    onClick={() => setShowPassword((value) => !value)}
                    tabIndex={-1}
                  >
                    {showPassword ? "隐藏" : "显示"}
                  </button>
                </span>
              </label>

              {error ?? notice ? (
                <div role="alert" className="ns-inline-alert ns-inline-alert-danger">
                  <span className="ns-inline-alert-body">{error ?? notice}</span>
                </div>
              ) : null}

              <button
                type="submit"
                className="ns-btn ns-btn-dark ns-btn-lg ns-btn-block"
                disabled={Boolean(pending) || !username.trim() || !password}
              >
                {pending === "password" ? <Spinner size={16} /> : null}
                {pending === "password" ? "正在验证…" : "登录工作台"}
              </button>
            </form>

            {health?.mode === "DEMO" ? (
              <div className="ns-login-demo">
                <div className="ns-login-divider">
                  <span>DEMO ACCESS</span>
                </div>
                <div className="ns-login-demo-actions">
                  <button
                    type="button"
                    className="ns-btn ns-btn-outline"
                    onClick={() => void finish(tradeApi.demoLogin("demo"), "demo")}
                    disabled={Boolean(pending)}
                  >
                    {pending === "demo" ? <Spinner size={14} /> : <StudioIcon name="trade" size={15} />}
                    交易员 DEMO
                  </button>
                  <button
                    type="button"
                    className="ns-btn ns-btn-outline"
                    onClick={() => void finish(tradeApi.demoLogin("admin"), "admin")}
                    disabled={Boolean(pending)}
                  >
                    {pending === "admin" ? <Spinner size={14} /> : <StudioIcon name="shield" size={15} />}
                    管理员 DEMO
                  </button>
                </div>
                <p>DEMO 订单只写入本地模拟账本，不涉及真实资金。</p>
              </div>
            ) : null}

            <div className="ns-login-security">
              <span>
                <StatusDot tone={health ? "ok" : healthError ? "bad" : "warn"} />
                {healthError ?? (health ? `NEMT Cloud API v${health.version}` : "正在连接 NEMT Cloud API…")}
              </span>
              <span>HTTPS · HttpOnly Session</span>
            </div>
          </div>

          <p className="ns-login-footnote">
            NEMT Studio 目前仅提供 DEMO 与受控 TESTNET 能力。LIVE 实盘写入未开放。
          </p>
        </section>
      </main>
    </div>
  );
}
