"use client";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { Incident } from "@/lib/types";
import { dateTime } from "@/lib/api";
import { Badge, EmptyState } from "./ui";
export function IncidentTable({ incidents }: { incidents: Incident[] }) {
  const { t } = useI18n();
  if (!incidents.length) return <EmptyState title={t("No incidents to show")}><p>{t("Confirmed inspection findings will appear here.")}</p></EmptyState>;
  return <div className="table-scroll"><table><thead><tr><th>{t("Incident / location")}</th><th>{t("Risk level")}</th><th>{t("Status")}</th><th>{t("Assigned to")}</th><th>{t("Created")}</th><th><span className="sr-only">{t("Open")}</span></th></tr></thead><tbody>{incidents.map((i) => <tr key={i.id}><td><Link className="table-title" href={"/incidents/" + i.id}>{t(i.title)}</Link><small>{i.incident_code} · {i.site_name}</small></td><td><Badge value={i.risk_level} /></td><td><Badge value={i.status} /></td><td><span className="assignee"><span className="mini-avatar">{i.assigned_to.split(" ").map((s) => s[0]).slice(0,2).join("")}</span>{t(i.assigned_to)}</span></td><td className="nowrap muted">{dateTime(i.created_at)}</td><td><Link className="table-open" aria-label={t("Open ") + i.incident_code} href={"/incidents/" + i.id}><ArrowUpRight size={18} /></Link></td></tr>)}</tbody></table></div>;
}
