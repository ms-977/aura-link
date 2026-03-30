"use client";

import { useEffect, useState } from "react";

const BACKEND = "http://localhost:8000";

interface ProviderStat {
  name: string;
  requests: number;
  total_tokens: number;
  avg_latency_ms: number;
}

interface Stats {
  total_requests: number;
  total_tokens: number;
  providers: ProviderStat[];
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

// Colour-code providers so the dot matches the brand
const PROVIDER_COLOURS: Record<string, string> = {
  gemini: "bg-blue-400",
  ollama: "bg-purple-400",
};

function dotColour(name: string): string {
  return PROVIDER_COLOURS[name.toLowerCase()] ?? "bg-gray-400";
}

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch(`${BACKEND}/v1/stats`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: Stats = await res.json();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch stats");
      }
    }

    fetchStats();
    // Refresh every 10 seconds so the dashboard stays live
    const interval = setInterval(fetchStats, 10_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Aura-Link</h1>
            <p className="text-gray-400 mt-1">Multi-LLM Gateway Dashboard</p>
          </div>
          {/* Live indicator */}
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            Live · refreshes every 10s
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-800 bg-red-950 px-5 py-4 text-sm text-red-300">
            ⚠ Could not reach backend: {error}. Is the FastAPI server running on port 8000?
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            label="Total Requests"
            value={stats ? String(stats.total_requests) : "—"}
            sub="across all providers"
            loading={!stats && !error}
          />
          <StatCard
            label="Tokens Used"
            value={stats ? formatTokens(stats.total_tokens) : "—"}
            sub="prompt + completion"
            loading={!stats && !error}
          />
          <StatCard
            label="Active Providers"
            value={stats ? String(stats.providers.length) : "—"}
            sub={stats?.providers.map(p => p.name).join(", ") ?? ""}
            loading={!stats && !error}
          />
        </div>

        {/* Provider Status */}
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h2 className="text-lg font-semibold mb-4">Provider Breakdown</h2>

          {!stats && !error && (
            <div className="space-y-3">
              {[1, 2].map(i => (
                <div key={i} className="h-6 rounded bg-gray-800 animate-pulse" />
              ))}
            </div>
          )}

          {stats && stats.providers.length === 0 && (
            <p className="text-gray-500 text-sm">
              No requests yet. Send a request to /v1/chat/completions to see data here.
            </p>
          )}

          {stats && stats.providers.length > 0 && (
            <div className="space-y-4">
              {stats.providers.map(p => (
                <div key={p.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${dotColour(p.name)}`} />
                    <span className="capitalize">{p.name}</span>
                  </div>
                  <span className="text-gray-400 text-sm">
                    {p.requests} req · {formatTokens(p.total_tokens)} tokens · {p.avg_latency_ms}ms avg
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </main>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface StatCardProps {
  label: string;
  value: string;
  sub: string;
  loading: boolean;
}

function StatCard({ label, value, sub, loading }: StatCardProps) {
  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <p className="text-gray-400 text-sm">{label}</p>
      {loading ? (
        <div className="h-10 mt-2 rounded bg-gray-800 animate-pulse" />
      ) : (
        <p className="text-4xl font-bold mt-2">{value}</p>
      )}
      <p className="text-gray-500 text-xs mt-1">{sub}</p>
    </div>
  );
}