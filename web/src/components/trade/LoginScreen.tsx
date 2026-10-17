"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import type { Health, Session } from "@/lib/trade/types";
import { ModeBadge, Spinner, StatusDot } from "./ui";

export default function LoginScreen({
  onLoggedIn,
  notice,
}: {
  onLoggedIn: (session: Session) => void;
  notice?: string | null;
}) {
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
          setHealthError(
            reason instanceof Error ? reason.message : "无法连接 NEMT 服务端"
          );
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
      const session = await promise;
      onLoggedIn(session);
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "登录失败，请检查服务端状态后重试"
      );
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
    <div className="trade-shell flex flex-col">
      <div className="flex-1 flex flex-col justify-center w-full max-w-[440px] mx-auto px-5 py-10 trade-safe-top">
        <div className="flex flex-col items-center text-center">
          <div className="relative">
            <div className="absolute inset-0 -m-6 rounded-full bg-cyan-400/12 blur-3xl" />
            <div className="relative w-[86px] h-[86px] rounded-[24px] overflow-hidden ring-1 ring-cyan-300/25 shadow-[0_18px_60px_rgba(0,165,217,0.18)]">
              <Image
                src="/icons/icon-512.png"
                alt="NEMT"
                width={172}
                height={172}
                className="w-full h-full object-cover"
                priority
              />
            </div>
          </div>
          <h1 className="mt-5 text-[25px] font-bold tracking-[0.06em] text-slate-100">
            NEMT <span className="trade-cyan">TRADE</span>
          </h1>
          <p className="mt-1.5 text-[12px] text-slate-500 tracking-wide">
            Binance Spot · Mobile Trading Terminal · V0.1
          </p>

          <div className="flex items-center gap-2 mt-4">
            {health ? (
              <>
                <ModeBadge mode={health.mode} />
                <span className="trade-chip">
                  <StatusDot tone="ok" />
                  SERVER ONLINE
                </span>
              </>
            ) : healthError ? (
              <span className="trade-chip trade-chip-danger">
                <StatusDot tone="bad" />
                SERVER UNREACHABLE
              </span>
            ) : (
              <span className="trade-chip">
                <Spinner size={10} />
                CONNECTING
              </span>
            )}
          </div>
        </div>

        <div className="trade-card trade-card-accent mt-7 p-5">
          {health?.mode === "DEMO" ? (
            <div className="mb-5 rounded-xl border border-amber-300/15 bg-amber-300/[0.05] px-3.5 py-3">
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-amber-200">
                <span className="trade-dot" />
                Demo Environment
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-amber-100/55">
                演示环境使用本地模拟账本，不连接真实资金，也不会向交易所发送订单。
              </p>
            </div>
          ) : health ? (
            <div className="mb-5 rounded-xl border border-cyan-300/15 bg-cyan-300/[0.05] px-3.5 py-3">
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-cyan-200">
                <span className="trade-dot" />
                {health.mode} Environment
              </div>
              <p className="mt-1 text-[11px] leading-relaxed text-cyan-100/55">
                凭据仅存在于服务端。V0.1 不提供 LIVE 下单路径。
              </p>
            </div>
          ) : null}

          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="block">
              <span className="block mb-1.5 text-[11px] font-medium text-slate-400">
                账户
              </span>
              <input
                className="trade-input"
                autoComplete="username"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                inputMode="text"
                placeholder="demo"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={Boolean(pending)}
              />
            </label>
            <label className="block">
              <span className="block mb-1.5 text-[11px] font-medium text-slate-400">
                密码
              </span>
              <div className="relative">
                <input
                  className="trade-input pr-16"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="输入密码"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  disabled={Boolean(pending)}
                />
                <button
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-2.5 py-1.5 text-[11px] font-semibold text-slate-500 hover:text-slate-300"
                  onClick={() => setShowPassword((value) => !value)}
                  tabIndex={-1}
                >
                  {showPassword ? "隐藏" : "显示"}
                </button>
              </div>
            </label>

            {error ?? notice ? (
              <div
                role="alert"
                className="rounded-xl border border-rose-400/25 bg-rose-400/[0.07] px-3 py-2.5 text-[12px] leading-relaxed text-rose-200"
              >
                {error ?? notice}
              </div>
            ) : null}

            <button
              type="submit"
              className="trade-btn trade-btn-primary w-full"
              disabled={Boolean(pending) || !username.trim() || !password}
            >
              {pending === "password" ? <Spinner size={16} /> : null}
              {pending === "password" ? "登录中…" : "登录"}
            </button>
          </form>

          {health?.mode === "DEMO" ? (
            <div className="mt-4">
              <div className="flex items-center gap-3">
                <div className="h-px flex-1 bg-white/[0.06]" />
                <span className="text-[10px] uppercase tracking-[0.16em] text-slate-600">
                  Demo quick access
                </span>
                <div className="h-px flex-1 bg-white/[0.06]" />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  className="trade-btn trade-btn-outline !min-h-[44px] text-[12px]"
                  onClick={() => void finish(tradeApi.demoLogin("demo"), "demo")}
                  disabled={Boolean(pending)}
                >
                  {pending === "demo" ? <Spinner size={14} /> : null}
                  交易员 DEMO
                </button>
                <button
                  type="button"
                  className="trade-btn trade-btn-outline !min-h-[44px] text-[12px]"
                  onClick={() => void finish(tradeApi.demoLogin("admin"), "admin")}
                  disabled={Boolean(pending)}
                >
                  {pending === "admin" ? <Spinner size={14} /> : null}
                  管理员 DEMO
                </button>
              </div>
              <p className="mt-2.5 text-center text-[10px] leading-relaxed text-slate-600">
                密码登录示例：demo / nemt-demo · admin / nemt-admin（仅本机演示）
              </p>
            </div>
          ) : null}
        </div>

        <div className="mt-5 space-y-2 px-1">
          <p className="flex items-start gap-2 text-[10px] leading-relaxed text-slate-600">
            <span className="text-cyan-400/60 mt-[1px]">◈</span>
            App 只调用 NEMT Cloud API。Binance Key / Secret 永不进入浏览器或本地存储。
          </p>
          <p className="flex items-start gap-2 text-[10px] leading-relaxed text-slate-600">
            <span className="text-cyan-400/60 mt-[1px]">◈</span>
            模拟盘通过不代表盈利能力。LIVE 实盘默认不可用，需独立审批。
          </p>
        </div>

        <div className="mt-7 flex items-center justify-center gap-4 text-[11px] text-slate-600">
          <Link href="/" className="hover:text-slate-300 transition-colors">
            研究终端 ↗
          </Link>
          <span className="w-px h-3 bg-white/10" />
          <a href="/offline.html" className="hover:text-slate-300 transition-colors">
            离线说明
          </a>
        </div>
      </div>
    </div>
  );
}
