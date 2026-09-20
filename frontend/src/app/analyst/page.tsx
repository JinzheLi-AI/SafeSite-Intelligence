"use client";
import { useI18n } from "@/lib/i18n";
import { useState } from "react";
import { Sparkles, ArrowUpRight, ChartNoAxesCombined, MapPin, CircleCheck, Repeat2, Send, Clock3 } from "lucide-react";
import { useResource } from "@/lib/use-resource";
import { post, errorMessage } from "@/lib/api";
import { PageHeading, Button } from "@/components/ui";
import { AnalystResult, type AnalyticsAnswer } from "@/components/analyst-result";
const suggestions = [
  { icon: Clock3, question: "Show critical incidents from the last 30 days." },
  { icon: ChartNoAxesCombined, question: "What is our most common hazard this month?" },
  { icon: MapPin, question: "Which site has the most critical incidents?" },
  { icon: CircleCheck, question: "What is our incident closure rate?" },
  { icon: Repeat2, question: "Which hazards are recurring?" },
  { icon: Clock3, question: "What is the average rectification time?" },
];
export default function AnalystPage() {
  const { t } = useI18n();
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AnalyticsAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const capabilities = useResource<{ provider: string; flexible_ready: boolean }>("/analyst/capabilities");
  async function ask(value: string) {
    if (busy || value.trim().length < 3) return;
    setQuestion(value); setBusy(true); setResult(null); setError("");
    try { setResult(await post<AnalyticsAnswer>("/analyst/query", { question: value.trim() })); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return <><PageHeading eyebrow={t("LEARN / SAFETY INTELLIGENCE")} title={t("AI Safety Analyst")} description={t("Ask questions about your construction safety data.")}><span className="mode-badge">{t("Read-only safety analytics")}</span></PageHeading>
    <div className="analyst-hero"><span className="analyst-orb"><Sparkles size={31} /></span><div className="eyebrow">{t("YOUR SAFETY DATA, IN CONTEXT")}</div><h2>{t("From questions to informed action.")}</h2><p>{t("Explore patterns, compare sites and review closure performance.")}<br />{t("Every answer starts with records in your SafeSite database.")}</p>
      <div className="suggestion-grid">{suggestions.map(({ icon: Icon, question: q }) => <button key={t(q)} disabled={busy} onClick={() => ask(t(q))}><Icon size={21} /><span>{t(q)}</span><ArrowUpRight size={17} /></button>)}</div>
      <form className="analyst-input" onSubmit={(e) => { e.preventDefault(); void ask(question); }}><Sparkles size={20} /><input aria-label={t("Ask about safety data")} placeholder={t("Ask about hazards, incidents, sites or closure performance")} value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={1000} disabled={busy} /><Button type="submit" disabled={busy || question.trim().length < 3} aria-label={t("Submit question")}><Send size={17} /></Button></form>
      <small className="micro">{["openai", "deepseek"].includes(capabilities.data?.provider ?? "") ? (capabilities.data?.flexible_ready ? t("Common questions use registered metrics. Flexible questions use an AI plan checked against those metrics.") : t("Common metrics are available. Flexible AI planning needs backend credentials.")) : t("Registered metrics query your actual database without an AI model.")} {" "}{t("Dates use Hong Kong time.")}</small>
      {busy && <div className="analyst-notice" role="status" aria-live="polite"><Sparkles size={21} /><div><strong>{t("Analyzing your safety data")}</strong><p>{t("Understanding question · Building safety query · Validating SQL · Analyzing results")}</p></div></div>}
      {error && <p role="alert" className="field-error">{t(error)}</p>}
    </div>{result && <AnalystResult result={result} />}</>;
}
