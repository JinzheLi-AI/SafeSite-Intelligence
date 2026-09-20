"use client";
import { useI18n } from "@/lib/i18n";
import { useState } from "react";
import Link from "next/link";
import { Search, ScanLine, ClipboardList } from "lucide-react";
import { useResource } from "@/lib/use-resource";
import type { Incident } from "@/lib/types";
import { PageHeading, Panel, LoadingState, ErrorState } from "@/components/ui";
import { IncidentTable } from "@/components/incident-table";
export default function IncidentsPage() {
  const { t } = useI18n();
  const { data, error, loading, reload } = useResource<Incident[]>("/incidents?limit=200");
  const [search, setSearch] = useState(""); const [status, setStatus] = useState("ALL"); const [risk, setRisk] = useState("ALL");
  const rows = data?.filter((i) => (status === "ALL" || i.status === status) && (risk === "ALL" || i.risk_level === risk) && [i.title, i.incident_code, i.location_text, i.assigned_to].join(" ").toLowerCase().includes(search.toLowerCase())) ?? [];
  return <><PageHeading eyebrow={t("GOVERN → ACT → VERIFY")} title={t("Every finding, followed through.")} description={t("Manage corrective work and keep a clear record of every decision.")}><Link className="button button-primary" href="/inspections"><ScanLine size={16} />{t("New AI inspection")}</Link></PageHeading><Panel><div className="list-toolbar"><div className="list-title"><ClipboardList size={20} /><h2>{t("Incident register")}</h2><span className="count-chip">{data?.length ?? "—"}</span></div><div className="filters"><div className="input-with-icon"><Search size={16} /><input aria-label={t("Search incidents")} placeholder={t("Search incidents…")} value={search} onChange={(e) => setSearch(e.target.value)} /></div><select aria-label={t("Filter by status")} value={status} onChange={(e) => setStatus(e.target.value)}><option value="ALL">{t("All statuses")}</option>{["OPEN", "UNDER_REVIEW", "RECTIFICATION", "REINSPECTION", "CLOSED", "REJECTED"].map((s) => <option key={s} value={s}>{t(s)}</option>)}</select><select aria-label={t("Filter by risk")} value={risk} onChange={(e) => setRisk(e.target.value)}><option value="ALL">{t("All risks")}</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => <option key={s} value={s}>{t(s)}</option>)}</select></div></div>{loading ? <LoadingState /> : error ? <ErrorState message={error} retry={reload} /> : <IncidentTable incidents={rows} />}<div className="table-footer">{t("Showing")}{" "}{rows.length} {" "}{t("of")}{" "}{data?.length ?? 0} {" "}{t("loaded incidents · Most recent 200 records · Persistent workflow data")}</div></Panel></>;
}
