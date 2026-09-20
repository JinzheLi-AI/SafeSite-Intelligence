"use client";
import { useI18n } from "@/lib/i18n";
import { useEffect, useState } from "react";
import { ScanLine, ArrowRight, ShieldCheck, ListChecks, Scale, RotateCcw } from "lucide-react";
import type { Project, Inspection, AIHealth } from "@/lib/types";
import { api, post, upload, errorMessage, dateTime } from "@/lib/api";
import { useResource } from "@/lib/use-resource";
import { PageHeading, ErrorState, LoadingState, Panel, Button, Badge } from "@/components/ui";
import { InspectionForm, type InspectionDraft } from "@/components/inspection-form";
import { InspectionResults } from "@/components/inspection-results";
import { AnalysisProgress } from "@/components/analysis-progress";
export default function InspectionPage() {
  const { t } = useI18n();
  const health = useResource<AIHealth>("/health"); const real = health.data?.ai_mode === "real";
  const projects = useResource<Project[]>("/projects"); const history = useResource<Inspection[]>("/inspections");
  const [current, setCurrent] = useState<Inspection | null>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  useEffect(() => { const id = new URLSearchParams(window.location.search).get("id"); if (id) api<Inspection>("/inspections/" + id).then(setCurrent).catch((e) => setError(errorMessage(e))); }, []);
  function select(inspection: Inspection | null) { setCurrent(inspection); window.history.replaceState(null, "", inspection ? "/inspections?id=" + inspection.id : "/inspections"); }
  async function analyze(draft: InspectionDraft) {
    setBusy(true); setError("");
    try {
      const path = draft.file ? await upload(draft.file) : null;
      const created = await post<Inspection>("/inspections", { project_id: draft.project_id, site_id: draft.site_id, location_text: draft.location_text, description: draft.description || null, source_type: path ? "IMAGE" : "DEMO", image_path: path });
      select(created);
      const [result] = await Promise.all([post<Inspection>("/inspections/" + created.id + "/analyze"), new Promise((resolve) => setTimeout(resolve, real ? 0 : 1200))]);
      select(result); void history.reload();
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  async function resume() {
    if (!current) return; setBusy(true); setError("");
    try { select(await post<Inspection>("/inspections/" + current.id + "/analyze")); void history.reload(); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  return <><PageHeading eyebrow={t("SENSE → REASON → GOVERN")} title={t("A second set of eyes. A safer site.")} description={t("Turn site observations into explainable, actionable safety findings.")}><span className="mode-badge"><ScanLine size={15} />{health.data ? real ? t("REAL AI provider") : t("DEMO AI provider") : t("Checking AI provider")}</span>{current && <Button variant="secondary" disabled={busy} onClick={() => select(null)}><RotateCcw size={15} />{t("New inspection")}</Button>}</PageHeading>
    {health.error && <ErrorState message={health.error} retry={health.reload} />}{health.data?.ai_error && <ErrorState message={health.data.ai_error} />}
    {error && <ErrorState message={error} />}
    {busy ? <AnalysisProgress real={real} /> : current?.analysis_json ? <InspectionResults key={current.id} inspection={current} onUpdate={(i) => { select(i); void history.reload(); }} /> : current ? <Panel title={t("Inspection saved")} subtitle={current.location_text}><div className="panel-body"><p>{current.status === "ANALYZING" ? t("Analysis may still be running. If interrupted, retry after five minutes (longer with extended provider timeouts). Your uploaded image and context are preserved.") : t("Your inspection is persisted and ready for analysis.")}</p><Button disabled={!health.data?.ai_ready || (real && !current.image_path)} onClick={resume}>{t("Run saved inspection analysis")}</Button></div></Panel> : <><p className="micro">{t("New AI results follow the selected language. Existing records keep their recorded language.")}</p><div className="inspection-layout"><div>{projects.loading ? <LoadingState /> : projects.error ? <ErrorState message={projects.error} retry={projects.reload} /> : projects.data?.length ? <InspectionForm projects={projects.data} busy={busy} real={real} ready={health.data?.ai_ready ?? false} onAnalyze={analyze} /> : <ErrorState message="No projects exist. Run the backend seed command." />}</div><div className="inspection-side"><div className="intelligence-card"><span className="intelligence-icon"><ScanLine size={28} /></span><div className="eyebrow">{t("FROM IMAGE TO INSIGHT")}</div><h2>{t("See the risk.")}<br />{t("Understand the why.")}</h2><p>{t("A structured safety review, built for the people who make the decisions.")}</p><div className="intelligence-feature"><ListChecks size={19} /><div><strong>{t("Evidence-led findings")}</strong><span>{t("Visible observations, clearly explained")}</span></div></div><div className="intelligence-feature"><Scale size={19} /><div><strong>{t("Consistent risk assessment")}</strong><span>{t("Transparent scores and safety policies")}</span></div></div><div className="intelligence-feature"><ShieldCheck size={19} /><div><strong>{t("You remain in control")}</strong><span>{t("No incident without human confirmation")}</span></div></div></div><div className="info-callout"><strong>{t("Evidence before decisions")}</strong><p>{t("Real mode analyzes uploaded images. Demo mode uses a fixed scenario. Real findings retrieve relevant official safety guidance for the active project jurisdiction when the index is available; human confirmation controls the incident workflow.")}</p></div></div></div></>}
    {!busy && <Panel title={t("Inspection history")} subtitle={t("Resume a saved analysis or continue the prepared Tower A scenario.")} className="history-panel">{history.error ? <ErrorState message={history.error} retry={history.reload} /> : history.loading ? <LoadingState /> : <div className="history-list">{history.data?.filter((i) => i.analysis_json || ["CREATED", "ANALYZING"].includes(i.status)).slice(0, 8).map((i) => <button key={i.id} className="history-item" onClick={() => { select(i); window.scrollTo({ top: 0, behavior: "smooth" }); }}><span className="history-icon"><ScanLine size={19} /></span><span><strong>{i.location_text}</strong><small>{t("Inspection #")}{i.id} · {dateTime(i.created_at)}</small></span><Badge value={i.status} /><ArrowRight size={17} /></button>)}</div>}</Panel>}
  </>;
}
