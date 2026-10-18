"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, tradeApi } from "@/lib/trade/api";
import type { Health, Session } from "@/lib/trade/types";
import { BrandMark, ModeBadge, Spinner, StatusDot } from "./ui";

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
    <div className="trade-shell flex min-h-dvh flex-col">
      <div className="flex flex-1 flex-col justify-center w-full max-w-[420px] mx-auto px-5 py-10 trade-safe-top">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <BrandMark size={42} />
            <div className="flex items-center gap-2">
              {health ? <ModeBadge mode={health.mode} /> : null}
              <StatusDot tone={health ? "ok" : healthError ? "bad" : "warn"} pulse={Boolean(health)} />
            </div>
          </div>
          <p className="mt-7 text-[11px] font-black uppercase tracking-[0.28em] text-[#c84538] -rotate-1">NEMT / BINANCE</p>
          <h1 className="mt-1 text-[48px] leading-[.88] font-black tracking-[-0.075em] text-[#161714]">
            TRADE<br />DIFFERENT.
          </h1>
          <div className="mt-4 h-[7px] w-28 bg-[#123f39] rotate-[-3deg]" />
        </div>

        <div className="trade-card trade-card-accent p-5">
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
              <p className="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Quick access</p>
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
            </div>
          ) : null}
        </div>
        <p className="mt-5 text-[10px] font-semibold tracking-wide text-slate-500">
          {healthError ? "CLOUD OFFLINE" : health ? "CLOUD READY · KEYS STAY SERVER-SIDE" : "CONNECTING…"}
        </p>
      </div>
    </div>
  );
}
