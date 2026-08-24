"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [apiEndpoint, setApiEndpoint] = useState("http://localhost:8000");
  const [theme, setTheme] = useState("dark");
  const [notifications, setNotifications] = useState(true);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-slate-400">Configure NEMT system</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Configuration */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">API Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-2">API Endpoint</label>
              <input
                type="text"
                value={apiEndpoint}
                onChange={(e) => setApiEndpoint(e.target.value)}
                placeholder="http://localhost:8000"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <span className="text-slate-500 text-xs mt-1 block">
                Future: Connect to FastAPI backend
              </span>
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-2">API Key</label>
              <input
                type="password"
                placeholder="Enter API key"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-emerald-400 text-sm">Mock Mode Active</span>
            </div>
          </div>
        </div>

        {/* Display Settings */}
        <div className="nemt-card p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Display</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-2">Theme</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setTheme("dark")}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    theme === "dark"
                      ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  Dark
                </button>
                <button
                  onClick={() => setTheme("light")}
                  disabled
                  className="px-4 py-2 rounded-lg font-medium bg-slate-800 text-slate-600 border border-slate-700 cursor-not-allowed"
                >
                  Light (Soon)
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
              <span className="text-white">Notifications</span>
              <button
                onClick={() => setNotifications(!notifications)}
                className={`w-12 h-6 rounded-full transition-all ${
                  notifications ? "bg-blue-500" : "bg-slate-600"
                }`}
              >
                <div className={`w-5 h-5 rounded-full bg-white transition-all ${
                  notifications ? "translate-x-6" : "translate-x-0.5"
                }`} />
              </button>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="nemt-card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-white mb-4">About NEMT</h2>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Version</span>
              <span className="text-white">Alpha 0.1.0</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Build</span>
              <span className="text-white">2025.08.25</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Status</span>
              <span className="text-emerald-400">Alpha Testing</span>
            </div>
          </div>
          <p className="text-slate-500 text-sm mt-4">
            NEMT is an AI Financial Intelligence system combining Human Judgment with AI Execution.
          </p>
        </div>
      </div>
    </div>
  );
}
