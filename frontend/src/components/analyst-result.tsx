"use client";
import { useI18n } from "@/lib/i18n";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Panel } from "@/components/ui";
import { humanize } from "@/lib/api";
export type AnalyticsAnswer = {
  localized?: Record<string, Partial<AnalyticsAnswer>>;
  status: "success" | "no_data" | "unsupported" | "rejected" | "unavailable" | "error";
  question: string; answer: string; insight: string; interpretation: string; metric: string | null;
  metric_definition: string; time_range: string; timezone: string; assumptions: string[];
  key_metric: string | number | null; unit: string; sql: string | null; rows_returned: number;
  truncated: boolean; provider: string; model: string | null; validation: string; latency_ms: number;
  rows: Record<string, string | number | null>[];
  chart: { type: "metric" | "bar" | "line" | "table"; xKey: string | null; yKey: string | null; data: Record<string, string | number | null>[] } | null;
};
export function AnalystResult({ result: original }: { result: AnalyticsAnswer }) {
  const { t, locale } = useI18n();
  const result = { ...original, ...original.localized?.[locale] };
  const chart = result.chart ? { ...result.chart, data: result.chart.data.map(row => ({ ...row, ...(row.label ? { label: t(row.label) } : {}) })) } : null;
  const columns = result.rows.length ? Object.keys(result.rows[0]) : [];
  return <section aria-label={t("Safety analytics result")} className="analyst-result">
    <Panel title={result.status === "success" ? t("Your safety data, explained") : result.status === "no_data" ? t("No matching data") : result.status === "rejected" ? t("Request rejected") : result.status === "unsupported" ? t("Question not supported") : t("Analysis unavailable")}
      action={<span className="mode-badge">{result.provider === "deterministic" ? t("Database query · no LLM") : result.provider === "test" ? t("Injected test planner") : t("AI plan · verified SQL")}</span>}>
      <p className="micro">{t("Question:")}{" "}{result.question}</p>
      <p className="analyst-answer" role="status">{result.answer}</p>
      {result.status === "success" && result.key_metric !== null && <div className="analyst-kpi"><strong>{typeof result.key_metric === "number" ? result.key_metric.toLocaleString(undefined, { maximumFractionDigits: 2 }) : result.key_metric}</strong><span>{t(result.unit)}</span></div>}
      {chart && (chart.type === "bar" || chart.type === "line") && <div className="chart-frame analyst-chart" role="img" aria-label={chart.type === "bar" ? t("Safety metric by group from database results") : t("Incident volume over recorded days")}>
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          {chart.type === "bar" ? <BarChart data={chart.data} margin={{ top: 12, right: 16, bottom: 65, left: 0 }}>
            <CartesianGrid stroke="#edf0f1" vertical={false} /><XAxis dataKey={chart.xKey!} interval={0} angle={-25} textAnchor="end" tick={{ fontSize: 11 }} height={80} /><YAxis tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey={chart.yKey!} name={t(result.unit)} fill="#258c78" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          </BarChart> : <LineChart data={chart.data} margin={{ top: 12, right: 16, bottom: 12, left: 0 }}>
            <CartesianGrid stroke="#edf0f1" vertical={false} /><XAxis dataKey={chart.xKey!} tick={{ fontSize: 11 }} minTickGap={25} /><YAxis tick={{ fontSize: 11 }} allowDecimals={false} /><Tooltip /><Line dataKey={chart.yKey!} name={t(result.unit)} stroke="#258c78" strokeWidth={2.5} dot={false} isAnimationActive={false} />
          </LineChart>}
        </ResponsiveContainer>
      </div>}
      {result.insight && <div className="analyst-insight"><strong>{t("Management insight")}</strong><p>{result.insight}</p></div>}
      {result.rows.length > 0 && <div className="table-scroll" tabIndex={0} aria-label={t("Supporting database rows")}><table><thead><tr>{columns.map((c) => <th key={c}>{humanize(c)}</th>)}</tr></thead><tbody>{result.rows.map((row, i) => <tr key={i}>{columns.map((c) => <td key={c}>{typeof row[c] === "number" ? row[c].toLocaleString(undefined, { maximumFractionDigits: 2 }) : row[c] === null ? t("Not available") : t(String(row[c]))}</td>)}</tr>)}</tbody></table></div>}
      {result.interpretation && <div className="analyst-context"><strong>{t("Query interpretation")}</strong><p>{result.interpretation}</p><strong>{t("Metric definition")}</strong><p>{result.metric_definition}</p><strong>{t("Time range")}</strong><p>{result.time_range}</p><p>{result.timezone}</p>{result.assumptions.map((a) => <p className="micro" key={a}>{a}</p>)}</div>}
      <details className="analyst-technical"><summary>{t("Technical details")}</summary><p>{t("Metric:")}{" "}{result.metric ?? t("None")} {" "}{t("· Rows returned:")}{" "}{result.rows_returned} · {result.latency_ms} {" "}{t("ms")}</p><p>{t("Validation:")}{" "}{t(result.validation)}</p><p>{t("Provider:")}{" "}{result.provider}{result.model ? " / " + result.model : ""}</p>{result.sql && <pre>{result.sql}</pre>}</details>
    </Panel>
  </section>;
}
