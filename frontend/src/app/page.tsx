"use client";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { ArrowRight, ScanLine, Activity, ClipboardList, ShieldAlert, CircleCheck, ShieldCheck } from "lucide-react";
import { useResource } from "@/lib/use-resource";
import type { Dashboard, Trend, HazardCount } from "@/lib/types";
import { PageHeading, Panel, Metric, ErrorState, LoadingState, DemoNote } from "@/components/ui";
import { IncidentTable } from "@/components/incident-table";
import { RiskTrend, HazardChart } from "@/components/charts";
import { JurisdictionContext } from "@/components/jurisdiction-context";
export default function DashboardPage() {
  const { t } = useI18n();
  const summary = useResource<Dashboard>("/dashboard/summary");
  const trend = useResource<Trend[]>("/analytics/risk-trend");
  const hazards = useResource<HazardCount[]>("/analytics/hazards");
  if (summary.loading) return <LoadingState />;
  if (summary.error || !summary.data) return <ErrorState message={summary.error} retry={summary.reload} />;
  const data = summary.data;
  return <><PageHeading eyebrow={t("SITE INTELLIGENCE / OVERVIEW")} title={t("Safety, in clear view.")} description={t("Your operations at a glance. Spot risk early. Act with confidence.")}><Link href="/inspections" className="button button-primary"><ScanLine size={17} />{t("New AI inspection")}</Link></PageHeading>
    <JurisdictionContext compact /><div className="overview-banner"><div className="banner-icon"><ShieldCheck size={25} /></div><div><strong>{t("A safer site starts with a clear next step.")}</strong><p>{data.critical_incidents ? data.critical_incidents + t(" critical incidents need attention.") : t("Review the prepared Tower A inspection to begin.")} {" "}{t("AI surfaces the findings. Your team makes the decisions.")}</p></div><Link href="/inspections">{t("Review inspections")}{" "}<ArrowRight size={17} /></Link></div>
    <div className="metrics-grid"><Metric label={t("Safety Risk Score")} value={data.safety_risk_score + " / 100"} note={t("Active incidents · higher = more risk")} tone="teal" icon={<Activity size={19} />} /><Metric label={t("Open Incidents")} value={data.open_incidents} note={t("Across all active workflow stages")} icon={<ClipboardList size={19} />} /><Metric label={t("Critical Incidents")} value={data.critical_incidents} note={t("Require priority human attention")} tone="red" icon={<ShieldAlert size={19} />} /><Metric label={t("Resolved Incidents")} value={data.resolved_incidents} note={data.closure_rate + t("% incident closure rate")} tone="green" icon={<CircleCheck size={19} />} /></div>
    <div className="dashboard-charts"><Panel title={t("Safety risk trend")} subtitle={t("Average active incident risk · daily snapshot")} action={<span className="chart-period">{t("Last 14 days")}</span>}>{trend.error ? <ErrorState message={trend.error} retry={trend.reload} /> : trend.data ? <RiskTrend data={trend.data} /> : <LoadingState />}</Panel><Panel title={t("Top hazard types")} subtitle={t("All recorded inspection observations")} action={<span className="chart-period">{t("All time")}</span>}>{hazards.error ? <ErrorState message={hazards.error} retry={hazards.reload} /> : hazards.data ? <HazardChart data={hazards.data} /> : <LoadingState />}</Panel></div>
    <Panel title={t("Recent incidents")} subtitle={t("Track findings from confirmation to closure")} action={<Link className="text-link" href="/incidents">{t("View all incidents")}{" "}<ArrowRight size={15} /></Link>}><IncidentTable incidents={data.recent_incidents} /></Panel>
    <div className="workflow-strip">{[t("Sense"), t("Reason"), t("Govern"), t("Act"), t("Verify"), t("Learn")].map((s, i) => <div key={t(s)}><span>0{i + 1}</span><strong>{t(s)}</strong>{i < 5 && <ArrowRight size={14} />}</div>)}</div><DemoNote>{t("Demo workspace · All metrics are computed from persisted demonstration records.")}{" "}{t(data.score_definition)}</DemoNote>
  </>;
}
