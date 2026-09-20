"use client";
import { useI18n } from "@/lib/i18n";
import type { AnalysisProvenance } from "@/lib/types";
export function AnalysisSource({ source }: { source?: AnalysisProvenance }) {
  const { t } = useI18n();
  const label = source?.kind === "REAL_AI" ? "REAL AI" : source?.kind === "DEMO_AI" ? "DEMO AI" : "SOURCE UNKNOWN";
  return <div className="info-callout"><strong>{t("Analysis source:")}{" "}{t(label)}</strong>{source?.model_name && <p className="micro">{source.provider} / {source.model_name} / {source.prompt_version}</p>}<p>{source?.kind === "DEMO_AI" ? t("Simulated findings from the prepared demonstration scenario.") : t("This AI-assisted assessment does not replace a formal safety inspection.")}</p></div>;
}
