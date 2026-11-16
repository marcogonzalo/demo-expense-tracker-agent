import { useEffect, useState } from "react";
import { api } from "./api";

function formatEuro(value) {
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
  }).format(value ?? 0);
}

export default function App() {
  const [dark, setDark] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [movements, setMovements] = useState([]);
  const [report, setReport] = useState(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  async function refresh() {
    const [m, mov] = await Promise.all([api.metrics(), api.movements()]);
    setMetrics(m);
    setMovements(mov.movements || []);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function runPipeline() {
    setBusy(true);
    setError("");
    try {
      const result = await api.pipeline();
      setMetrics(result.metrics);
      setReport(result.analyze?.report || null);
      const mov = await api.movements();
      setMovements(mov.movements || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const categories = metrics?.category_breakdown || [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="animate-rise mb-10 flex flex-wrap items-end justify-between gap-4 border-b border-[var(--color-line)] pb-6">
        <div>
          <p className="font-mono text-xs tracking-[0.18em] text-[var(--color-muted)] uppercase">
            Demo Expense Tracker Agent
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Spending pulse
          </h1>
          <p className="mt-2 max-w-xl text-[var(--color-muted)]">
            Categorized movements, November spike vs monthly average, necessity
            labels from the agent pipeline.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setDark((v) => !v)}
            className="rounded-md border border-[var(--color-line)] px-3 py-2 text-sm"
          >
            {dark ? "Light mode" : "Dark mode"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={runPipeline}
            className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {busy ? "Running…" : "Run pipeline"}
          </button>
        </div>
      </header>

      {error ? (
        <p className="mb-6 rounded-md border border-[var(--color-danger)] px-3 py-2 text-sm text-[var(--color-danger)]">
          {error}
        </p>
      ) : null}

      <section className="animate-rise mb-8 grid gap-4 sm:grid-cols-3" style={{ animationDelay: "60ms" }}>
        <Stat
          label="Total expense"
          value={formatEuro(metrics?.total_expense)}
        />
        <Stat
          label="Avg monthly (Jun–Oct)"
          value={formatEuro(metrics?.average_monthly_expense_jun_oct)}
        />
        <Stat
          label="November vs average"
          value={formatEuro(metrics?.november_vs_average_delta)}
          tone={
            (metrics?.november_vs_average_delta || 0) > 0 ? "danger" : "accent"
          }
        />
      </section>

      <section className="mb-10 grid gap-8 lg:grid-cols-2">
        <div className="animate-rise" style={{ animationDelay: "120ms" }}>
          <h2 className="mb-4 text-lg font-semibold">Spend by category</h2>
          <ul className="space-y-3">
            {categories.length === 0 ? (
              <li className="text-sm text-[var(--color-muted)]">
                No data yet. Run the pipeline.
              </li>
            ) : (
              categories.map((row) => (
                <li key={row.category}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span>{row.category}</span>
                    <span className="font-mono text-[var(--color-muted)]">
                      {row.percentage}% · {formatEuro(row.amount)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded bg-[var(--color-line)]">
                    <div
                      className="h-full bg-[var(--color-accent)]"
                      style={{ width: `${Math.min(row.percentage, 100)}%` }}
                    />
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="animate-rise" style={{ animationDelay: "180ms" }}>
          <h2 className="mb-4 text-lg font-semibold">Analyst report</h2>
          {report ? (
            <div className="space-y-4 text-sm leading-relaxed text-[var(--color-muted)]">
              <Block title="Patterns" body={report.patterns} />
              <Block title="Excesses" body={report.excesses} />
              <div>
                <h3 className="mb-1 font-medium text-[var(--color-ink)]">Actions</h3>
                <ul className="list-disc space-y-1 pl-5">
                  {(report.actions || []).map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-sm text-[var(--color-muted)]">
              Run the pipeline to generate patterns, excesses, and actions.
            </p>
          )}
        </div>
      </section>

      <section className="animate-rise" style={{ animationDelay: "240ms" }}>
        <h2 className="mb-4 text-lg font-semibold">Transactions</h2>
        <div className="overflow-x-auto border border-[var(--color-line)]">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[var(--color-panel)] font-mono text-xs tracking-wide text-[var(--color-muted)] uppercase">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Concept</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Necessity</th>
                <th className="px-3 py-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((m) => (
                <tr key={m.id} className="border-t border-[var(--color-line)]">
                  <td className="px-3 py-2 font-mono text-xs">{m.date}</td>
                  <td className="px-3 py-2">{m.concept}</td>
                  <td className="px-3 py-2">{m.category}</td>
                  <td className="px-3 py-2">
                    {m.necessity_label ? (
                      <span
                        title={m.necessity_description}
                        style={{ color: m.necessity_color || "inherit" }}
                      >
                        {m.necessity_level}. {m.necessity_label}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {formatEuro(m.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, tone = "ink" }) {
  const color =
    tone === "danger"
      ? "var(--color-danger)"
      : tone === "accent"
        ? "var(--color-accent)"
        : "var(--color-ink)";
  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-panel)]/70 px-4 py-4">
      <p className="text-xs tracking-wide text-[var(--color-muted)] uppercase">
        {label}
      </p>
      <p className="mt-2 font-mono text-2xl" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

function Block({ title, body }) {
  return (
    <div>
      <h3 className="mb-1 font-medium text-[var(--color-ink)]">{title}</h3>
      <p>{body}</p>
    </div>
  );
}
