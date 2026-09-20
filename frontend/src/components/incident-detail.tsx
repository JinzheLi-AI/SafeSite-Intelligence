"use client";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, ArrowRight, MapPin, UserRound, CalendarDays, ShieldCheck, FileImage, Check, ClipboardCheck, PencilLine } from "lucide-react";
import type { Incident, Audit } from "@/lib/types";
import { useResource } from "@/lib/use-resource";
import { api, post, upload, errorMessage, dateTime, imageUrl } from "@/lib/api";
import { PageHeading, Panel, Badge, Button, LoadingState, ErrorState } from "./ui";
import { AnalysisSource } from "./analysis-source";
import { RiskBreakdown, CitationCard } from "./risk";
import { AuditTimeline } from "./audit-timeline";
import { ReinspectionPanel } from "./reinspection-panel";
export function IncidentDetail({ id }: { id: string }) {
  const { t } = useI18n();
  const resource = useResource<Incident>("/incidents/" + id); const audit = useResource<Audit[]>("/incidents/" + id + "/audit");
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState(""); const [description, setDescription] = useState(""); const [assigned, setAssigned] = useState("");
  async function command(action: string, body: object = {}) {
    setBusy(true); setError("");
    try { resource.setData(await post<Incident>("/incidents/" + id + "/" + action, body)); await audit.reload(); setEditing(false); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  async function toggleAction(actionId: number, done: boolean) {
    setBusy(true); setError("");
    const previous = resource.data;
    if (previous) resource.setData({ ...previous, corrective_actions: previous.corrective_actions.map((a) => a.id === actionId ? { ...a, status: done ? "COMPLETED" : "PENDING" } : a) });
    try { resource.setData(await api<Incident>("/incidents/" + id + "/actions/" + actionId, { method: "PATCH", body: JSON.stringify({ status: done ? "COMPLETED" : "PENDING" }) })); await audit.reload(); }
    catch (e) { resource.setData(previous); setError(errorMessage(e)); } finally { setBusy(false); }
  }
  async function reinspect(file: File | null, useDemo: boolean, notes: string) {
    setBusy(true); setError("");
    try { const evidence_path = file ? await upload(file) : null; resource.setData(await post<Incident>("/incidents/" + id + "/reinspect", { evidence_path, use_demo_evidence: useDemo, notes })); await audit.reload(); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  if (resource.loading) return <LoadingState />;
  if (resource.error || !resource.data) return <ErrorState message={resource.error} retry={resource.reload} />;
  const incident = resource.data; const open = ["OPEN", "UNDER_REVIEW"].includes(incident.status);
  const stages = ["OPEN", "RECTIFICATION", "REINSPECTION", "CLOSED"];
  const activeStage = stages.indexOf(incident.status === "UNDER_REVIEW" ? "OPEN" : incident.status);
  return <><Link href="/incidents" className="back-link"><ArrowLeft size={15} />{t("Incident register")}</Link><PageHeading eyebrow={incident.incident_code + t(" / CASE WORKSPACE")} title={incident.title} description={incident.project_name + " · " + incident.site_name}><Badge value={incident.risk_level} /><Badge value={incident.status} /></PageHeading>
    {error && <ErrorState message={error} />}
    {incident.status === "CLOSED" && <div className="success-panel"><ShieldCheck size={27} /><div><h3>{t("Case closed by human decision.")}</h3><p>{t("Closed")}{" "}{dateTime(incident.closed_at)}{t(". The complete findings and audit trail remain available.")}</p></div></div>}
    {incident.status === "REJECTED" ? <div className="info-callout">{t("This incident was rejected by human review. The decision and original AI findings are retained for audit.")}</div> : <div className="case-stepper">{stages.map((stage, i) => <div className={i <= activeStage ? "step-complete" : ""} key={stage}><span>{i < activeStage ? <Check size={15} /> : i + 1}</span><strong>{[t("Confirmed"), t("Rectification"), t("Reinspection"), t("Closed")][i]}</strong>{i < 3 && <div className="step-line" />}</div>)}</div>}
    <div className="incident-facts"><div><MapPin size={18} /><span>{t("Location")}<strong>{incident.location_text}</strong></span></div><div><UserRound size={18} /><span>{t("Assigned person")}<strong>{incident.assigned_to}</strong></span></div><div><CalendarDays size={18} /><span>{t("Deadline")}<strong>{dateTime(incident.deadline)}</strong></span></div><div><ShieldCheck size={18} /><span>{t("Human decision")}<strong>{t(incident.human_decision)}</strong></span></div><div className="fact-score"><strong>{incident.risk_score}<small>/100</small></strong><span>{t("Initial risk score")}</span></div></div>
    {open && <div className="case-toolbar"><p><ShieldCheck size={17} />{t("Human-confirmed findings. Ready for corrective action.")}</p><Button variant="secondary" disabled={busy} onClick={() => { setEditing(!editing); setDescription(incident.description); setAssigned(incident.assigned_to); }}><PencilLine size={15} />{t("Review decision")}</Button><Button busy={busy} onClick={() => command("start-rectification")}><ClipboardCheck size={16} />{t("Start Rectification")}</Button></div>}
    {editing && <Panel title={t("Human review")} subtitle={t("Your accepted assessment is retained alongside the original AI finding.")}><div className="panel-body review-fields"><label>{t("Accepted description")}<textarea maxLength={4000} value={description} onChange={(e) => setDescription(e.target.value)} /></label><label>{t("Assigned person")}<input maxLength={100} value={assigned} onChange={(e) => setAssigned(e.target.value)} /></label><label>{t("Review notes / rejection reason")}<textarea maxLength={4000} value={notes} onChange={(e) => setNotes(e.target.value)} /></label><div className="button-row"><Button variant="danger" disabled={busy || !notes.trim()} onClick={() => command("reject", { notes })}>{t("Reject incident")}</Button><Button disabled={busy || !description.trim() || !assigned.trim()} onClick={() => command("confirm", { decision: "MODIFIED", modified_description: description, assigned_to: assigned, notes, deadline: incident.deadline })}>{t("Modify / confirm incident")}</Button></div></div></Panel>}
    <div className="detail-layout"><div className="detail-main"><Panel title={t("AI Findings")} subtitle={t("Original observation, preserved for traceability")}><div className="panel-body"><div className="finding-title"><h3>{t(incident.hazard.title)}</h3><span className="mode-badge">{Math.round(incident.hazard.confidence * 100)}{t("% confidence")}</span></div><p className="body-copy">{t(incident.hazard.description)}</p>{incident.description !== incident.hazard.description && <div className="human-amendment"><strong>{t("Human-accepted assessment")}</strong><p>{t(incident.description)}</p></div>}<AnalysisSource source={incident.analysis_source} />{incident.hazard.confidence < .85 && <p className="info-callout">{incident.hazard.confidence < .60 ? t("Insufficient / uncertain evidence. Human review required.") : t("Human review required.")}</p>}</div></Panel>
    <Panel title={t("Evidence")} subtitle={t("Observed details associated with this inspection")}><div className="panel-body"><ul className="evidence-list">{incident.hazard.evidence.map((e) => <li key={t(e)}><span />{t(e)}</li>)}</ul>{incident.image_path ? <a href={imageUrl(incident.image_path)} className="evidence-link" target="_blank" rel="noreferrer"><FileImage size={20} /><span>{t("View original site image")}<small>{t("Persisted inspection evidence")}</small></span><ArrowRight size={17} /></a> : <div className="evidence-link"><FileImage size={20} /><span>{t("Prepared demonstration scenario")}<small>{t("No original site photograph attached")}</small></span></div>}</div></Panel>
    <Panel title={t("Risk Breakdown")} subtitle={t("Deterministic assessment · AI confidence never discounts risk")}><div className="panel-body"><RiskBreakdown risk={incident.hazard.risk_breakdown} /></div></Panel>
    <Panel title={t("Applicable Safety Guidance")} subtitle={t("Evidence status is always visible")}><div className="panel-body">{incident.hazard.citations.length ? incident.hazard.citations.map((c) => <CitationCard key={c.id} citation={c} />) : <div className="info-callout">{t(incident.hazard.guidance_message ?? "No sufficiently relevant verified safety source was retrieved.")}</div>}</div></Panel>
    <Panel title={t("Corrective Actions")} subtitle={t("Mark actions complete only after human verification")} action={<span className="count-chip">{incident.corrective_actions.filter((a) => a.status === "COMPLETED").length}/{incident.corrective_actions.length}</span>}><div className="corrective-list">{incident.corrective_actions.map((a) => <label className={"corrective-item " + (a.status === "COMPLETED" ? "action-completed" : "")} key={a.id}><input type="checkbox" checked={a.status === "COMPLETED"} disabled={busy || incident.status !== "RECTIFICATION"} onChange={(e) => toggleAction(a.id, e.target.checked)} /><span><strong>{t(a.action_text)}</strong><small>{t(a.assigned_to)} · {a.status === "COMPLETED" ? t("Completed ") + dateTime(a.completed_at) : t("Awaiting completion")}</small></span><Badge value={a.priority} /></label>)}</div></Panel>
    <ReinspectionPanel incident={incident} busy={busy} onReinspect={reinspect} onClose={() => command("close", { notes: "Evidence reviewed and closure explicitly approved by the Safety Officer." })} onReturn={() => command("start-rectification", { notes: "Human review requests further corrective work." })} />
    </div><div className="detail-aside"><Panel title={t("Audit Trail")} subtitle={t("A clear record of who did what")}>{audit.error ? <ErrorState message={audit.error} retry={audit.reload} /> : audit.loading ? <LoadingState /> : <AuditTimeline entries={audit.data ?? []} />}</Panel><div className="governance-note"><ShieldCheck size={23} /><h3>{t("Accountability by design.")}</h3><p>{t("AI recommends. People decide. Every important transition is persisted with its actor and timestamp.")}</p><Link className="text-link" href="/analyst">{t("View AI execution metadata")}{" "}<ArrowRight size={14} /></Link></div></div></div>
  </>;
}
