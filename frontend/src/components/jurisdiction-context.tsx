"use client";
import { useProject } from "@/lib/project-context";
import { useI18n } from "@/lib/i18n";
import { useResource } from "@/lib/use-resource";
type Context = { project_id: number | null; name: string; supported: boolean; authority: string | null; regulatory_jurisdiction: string | null; options: { code: string; name: string; supported: boolean }[] };
export function JurisdictionContext({ compact = false }: { compact?: boolean }) {
  const { projectId, projects, selectProject } = useProject();
  const { t } = useI18n();
  const context = useResource<Context>("/knowledge/context" + (projectId ? "?project_id=" + projectId : ""));
  if (!context.data) return <p className="micro">{t(context.error || "Loading project jurisdiction…")}</p>;
  const data = context.data;
  if (compact) return <p className="micro jurisdiction-summary">{t("Active project jurisdiction")}: {t(data.name)} · {t("Dashboard metrics cover all projects.")}</p>;
  return <div className="jurisdiction-context">
    <label>{t("Active project")}<select aria-label={t("Active project")} value={projectId} onChange={e => selectProject(Number(e.target.value))}>{projects.map(p => <option value={p.id} key={p.id}>{p.name}</option>)}</select></label>
    <label>{t("Regulatory Jurisdiction")}<select aria-label={t("Regulatory Jurisdiction")} value={data.regulatory_jurisdiction ?? ""} onChange={() => {}}>
      {!data.options.some(o => o.code === data.regulatory_jurisdiction) && <option value={data.regulatory_jurisdiction ?? ""}>{t(data.name)} — {t("Coming Soon")}</option>}
      {data.options.map(o => <option key={o.code} value={o.code} disabled={!o.supported}>{t(o.name)} — {t(o.supported ? "Active / Verified" : "Coming Soon")}</option>)}
    </select></label><div><strong>{t("Current pilot configuration")}: {t("Hong Kong SAR")}</strong><p>{t("Verified corpus")}: {data.supported ? t(data.authority) : t("No verified corpus for this jurisdiction")}</p></div>
  </div>;
}
