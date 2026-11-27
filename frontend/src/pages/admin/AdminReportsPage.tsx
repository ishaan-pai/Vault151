import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { adminApi } from "../../api/adminClient";
import type { Report } from "../../api/adminTypes";

const REPORT_KEYS = [
  "paid-not-shipped",
  "sales-by-set",
  "multi-card-orders",
  "graded-buyers",
  "follow-ups",
] as const;

function ReportTable({ report }: { report: Report }) {
  if (report.rowCount === 0) {
    return <p className="text-sm text-muted">No rows match right now.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-seam">
            {report.columns.map((column) => (
              <th key={column} className="px-2 py-1.5 font-medium text-muted">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {report.rows.map((row, index) => (
            <tr key={index} className="border-b border-seam/50 last:border-0">
              {report.columns.map((column) => (
                <td key={column} className="px-2 py-1.5 text-ink">
                  {row[column]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReportSection({ reportKey }: { reportKey: string }) {
  const [minCards, setMinCards] = useState(2);
  const [showSql, setShowSql] = useState(false);

  const takesParameter = reportKey === "multi-card-orders";
  const report = useQuery({
    queryKey: ["admin", "report", reportKey, takesParameter ? minCards : null],
    queryFn: () => adminApi.report(reportKey, takesParameter ? minCards : undefined),
    retry: false,
  });

  return (
    <section className="rounded-lg border border-seam bg-surface p-4">
      {report.isPending ? (
        <p className="text-sm text-muted">Running&hellip;</p>
      ) : report.isError ? (
        <p className="text-sm text-danger">{report.error.message}</p>
      ) : (
        <>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-medium text-ink">{report.data.title}</h2>
              <p className="mt-1 text-xs text-muted">{report.data.description}</p>
              <p className="mt-1 text-xs text-brass">{report.data.feature}</p>
            </div>

            <div className="flex items-center gap-3">
              {takesParameter ? (
                <label className="flex items-center gap-2 text-xs text-muted">
                  At least
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={minCards}
                    onChange={(event) =>
                      setMinCards(Math.max(1, Number(event.target.value) || 1))
                    }
                    className="w-16 rounded border border-seam bg-canvas px-2 py-1 text-sm text-ink"
                  />
                  cards
                </label>
              ) : null}

              <button
                type="button"
                onClick={() => setShowSql((current) => !current)}
                className="text-xs text-muted underline hover:text-brass"
              >
                {showSql ? "Hide query" : "Show query"}
              </button>
            </div>
          </div>

          {showSql ? (
            <pre className="mt-3 overflow-x-auto rounded border border-seam bg-canvas p-3 text-xs text-muted">
              <code>{report.data.sql}</code>
            </pre>
          ) : null}

          <p className="mt-3 text-xs text-muted">
            {report.data.rowCount} row{report.data.rowCount === 1 ? "" : "s"}
          </p>

          <div className="mt-2">
            <ReportTable report={report.data} />
          </div>
        </>
      )}
    </section>
  );
}

/**
 * The five Assignment 5 queries, run against live data.
 *
 * Each section names the SQL feature it demonstrates and can show the exact
 * statement behind it, so this page doubles as the demo script: scroll through it
 * and every graded query feature appears in the running product rather than in a
 * SQL*Plus session beside it.
 */
export function AdminReportsPage() {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted">
        Each report is one of the project&rsquo;s graded queries, run against live
        data. Use &ldquo;Show query&rdquo; to see the SQL behind it.
      </p>

      {REPORT_KEYS.map((key) => (
        <ReportSection key={key} reportKey={key} />
      ))}
    </div>
  );
}
