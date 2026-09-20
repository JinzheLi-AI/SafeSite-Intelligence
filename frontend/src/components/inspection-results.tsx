"use client";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { useState } from "react";
import { ArrowRight, CheckCheck, ShieldCheck, CircleX } from "lucide-react";
import type { Inspection, Incident } from "@/lib/types";
import { post, errorMessage } from "@/lib/api";
import { Badge, Button, ErrorState, Panel } from "./ui";
import { AnalysisSource } from "./analysis-source";
import { HazardCard } from "./risk";
export function InspectionResults({ inspection, onUpdate }: { inspection: Inspection; onUpdate: (inspection: Inspection) => void }) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notes, setNotes] = useState("");
  const [modified, setModified] = useState(false); const [description, setDescription] = useState("");
  const [assigned, setAssigned] = useState("Safety Officer"); const [deadline, setDeadline] = useState("");
  async function review(action: "confirm" | "reject") {
    setError(""); setBusy(true);
    try {
      if (action === "reject") onUpdate(await post<Inspection>("/inspections/" + inspection.id + "/reject", { notes }));
      else {
        const incidents = await post<Incident[]>("/inspections/" + inspection.id + "/confirm", { notes, decision: modified ? "MODIFIED" : "CONFIRMED", modified_description: modified ? description : null, assigned_to: assigned, deadline: deadline ? new Date(deadline).toISOString() : null });
        onUpdate({ ...inspection, status: modified ? "MODIFIED" : "CONFIRMED", incident_ids: incidents.map((i) => i.id) });
      }
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  const reviewed = ["CONFIRMED", "MODIFIED", "REJECTED"].includes(inspection.status);
  return <div className="results-stack"><div className="results-summary"><div className="summary-icon"><ShieldCheck size={25} /></div><div><div className="eyebrow">{t("INSPECTION #")}{inspection.id} {" "}{t("/ ANALYSIS COMPLETE")}</div><h2>{inspection.hazards.length ? inspection.hazards.length + t(" hazards identified for review.") : t("No supported hazards confidently identified in this image.")}</h2><p>{inspection.location_text} · {Math.round((inspection.analysis_json?.overall_confidence ?? 0) * 100)}{t("% overall confidence")}</p></div><Badge value={reviewed ? inspection.status : "UNDER_REVIEW"} /></div>
    <AnalysisSource source={inspection.analysis_source} /><p className="body-copy">{t(inspection.analysis_json?.summary)}</p>{inspection.analysis_json?.requires_human_review && <div className="info-callout"><strong>{t("Human review required")}</strong><p>{t("Check the image and supporting observations before acting.")}</p></div>}{!!inspection.analysis_json?.reasoning_notes.length && <div className="info-callout"><strong>{t("Evidence and uncertainty")}</strong><ul>{inspection.analysis_json.reasoning_notes.map((note, i) => <li key={i}>{t(note)}</li>)}</ul></div>}
    {inspection.hazards.map((hazard, index) => <HazardCard key={hazard.id} hazard={hazard} index={index} source={inspection.analysis_source} />)}
    {error && <ErrorState message={error} />}
    {!reviewed && inspection.hazards.length > 0 && <Panel title={t("Human Review Required")} subtitle={t("Review the evidence and recommendations before creating incidents.")} className="review-panel"><div className="review-fields"><div className="field-row"><label>{t("Assign corrective actions to")}<input maxLength={100} value={assigned} onChange={(e) => setAssigned(e.target.value)} /></label><label>{t("Deadline")}{" "}<span className="optional">{t("Optional")}</span><input type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} /></label></div><label>{t("Review notes / rejection reason")}<textarea rows={2} maxLength={4000} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t("Record your decision context. A reason is required for rejection.")} /></label><label className="check-label"><input type="checkbox" checked={modified} onChange={(e) => setModified(e.target.checked)} />{t("Modify the accepted description before confirming")}</label>{modified && <label>{t("Accepted description for the incidents")}<textarea rows={3} maxLength={4000} value={description} onChange={(e) => setDescription(e.target.value)} placeholder={t("Your assessment is saved alongside the original AI findings.")} /></label>}</div><div className="review-actions"><span><ShieldCheck size={15} />{t("Your decision is recorded in the audit trail.")}</span><Button variant="secondary" disabled={busy || !notes.trim()} onClick={() => review("reject")}><CircleX size={16} />{t("Reject Findings")}</Button><Button busy={busy} disabled={!assigned.trim() || (modified && !description.trim())} onClick={() => review("confirm")}><CheckCheck size={17} />{modified ? t("Modify / Confirm Findings") : t("Confirm Findings")}</Button></div></Panel>}
    {inspection.incident_ids.length > 0 && <div className="success-panel"><CheckCheck size={24} /><div><h3>{t("Findings confirmed. Incidents created.")}</h3><p>{t("Each hazard has its own owner, corrective actions and audit trail.")}</p><div className="incident-links">{inspection.incident_ids.map((id, index) => <Link className="button button-primary" key={id} href={"/incidents/" + id}>{index === 0 ? t("Open primary incident") : t("Open related incident")}<ArrowRight size={16} /></Link>)}</div></div></div>}
    {inspection.status === "REJECTED" && <div className="info-callout">{t("Findings rejected by human review. No incidents were created.")}{" "}{inspection.review_notes}</div>}
  </div>;
}
