"use client";
import { useI18n } from "@/lib/i18n";
import { useProject } from "@/lib/project-context";
import { useState } from "react";
import { ScanLine, MapPin, ShieldCheck } from "lucide-react";
import type { Project } from "@/lib/types";
import { Button, Panel } from "./ui";
import { ImageUpload } from "./image-upload";
export interface InspectionDraft { project_id: number; site_id: number; location_text: string; description: string; file: File | null }
export function InspectionForm({ projects, busy, onAnalyze, real = false, ready = true }: { projects: Project[]; busy: boolean; real?: boolean; ready?: boolean; onAnalyze: (draft: InspectionDraft) => void }) {
  const { t } = useI18n();
  const { projectId: selectedProject, selectProject: setProjectId } = useProject();
  const projectId = selectedProject || projects[0]?.id || 0;
  const project = projects.find((p) => p.id === projectId);
  const [selectedSiteId, setSiteId] = useState(project?.sites[0]?.id ?? 0);
  const siteId = project?.sites.some(s => s.id === selectedSiteId) ? selectedSiteId : project?.sites[0]?.id ?? 0;
  const [location, setLocation] = useState("Level 16 · East Facade");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  return <Panel title={t("New site inspection")} subtitle={t("Capture the context. Let AI prepare the review.")} className="inspection-form-panel"><form onSubmit={(e) => { e.preventDefault(); onAnalyze({ project_id: projectId, site_id: siteId, location_text: location, description, file }); }}>
    <fieldset disabled={busy}><div className="field-row"><label>{t("Project")}<select value={projectId} onChange={(e) => { const id = Number(e.target.value); setProjectId(id); setSiteId(projects.find((p) => p.id === id)?.sites[0]?.id ?? 0); }}>{projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label>{t("Site")}<select value={siteId} onChange={(e) => setSiteId(Number(e.target.value))}>{project?.sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label></div>
    <label>{t("Location")}<div className="input-with-icon"><MapPin size={16} /><input required maxLength={300} value={location} onChange={(e) => setLocation(e.target.value)} placeholder={t("Level, zone or work area")} /></div></label>
    <ImageUpload file={file} onChange={setFile} disabled={busy} required={real} />
    <label>{t("Additional context")}{" "}<span className="optional">{t("Optional")}</span><textarea rows={3} maxLength={4000} placeholder={t("Describe the activity or areas that need attention…")} value={description} onChange={(e) => setDescription(e.target.value)} /></label>
    <div className="mock-context"><ShieldCheck size={16} /><span>{real ? t("The uploaded image will be sent to the configured multimodal model. Human review remains required.") : file ? t("Image will be stored as evidence. Analysis uses the fixed Tower A demo scenario.") : t("No image? Run the prepared Tower A demonstration scenario.")}</span></div>
    <Button type="submit" busy={busy} disabled={!ready || (real && !file) || !projectId || !siteId || !location.trim()}><ScanLine size={17} />{t("Analyze Site")}</Button></fieldset></form></Panel>;
}
