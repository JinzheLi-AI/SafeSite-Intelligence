"use client";
import { useI18n } from "@/lib/i18n";
import { useEffect, useState } from "react";
import { ScanLine, Check, LoaderCircle } from "lucide-react";
const stages = ["Analyzing scene", "Detecting hazards", "Assessing risk", "Retrieving safety guidance", "Preparing recommendations"];
export function AnalysisProgress({ real = false }: { real?: boolean }) {
  const { t } = useI18n();
  const [step, setStep] = useState(0);
  useEffect(() => { const timer = setInterval(() => setStep((s) => Math.min(s + 1, 4)), 240); return () => clearInterval(timer); }, []);
  if (real) return <div className="analysis-progress" role="status" aria-live="polite"><div className="scan-orb"><ScanLine size={36} /></div><div className="eyebrow">{t("REAL AI ANALYSIS")}</div><h2>{t("Reviewing the uploaded image.")}</h2><p><LoaderCircle size={17} className="spin" /> {" "}{t("Waiting for validated visual observations.")}</p><small>{t("Risk is calculated by the backend after validation. This may take a moment.")}</small></div>;
  return <div className="analysis-progress" role="status" aria-live="polite"><div className="scan-orb"><ScanLine size={36} /></div><div className="eyebrow">{t("MOCK ANALYSIS PIPELINE")}</div><h2>{t("Turning observations into action.")}</h2><p>{t("Structured findings. Deterministic risk. Human oversight.")}</p><div className="analysis-stages">{stages.map((stage, i) => <div key={t(stage)} className={i <= step ? "stage-active" : ""}>{i < step ? <Check size={17} /> : i === step ? <LoaderCircle size={17} className="spin" /> : <span className="stage-dot" />}<span>{t(stage)}</span></div>)}</div><small>{t("Fixed demonstration scenario · no live image understanding")}</small></div>;
}
