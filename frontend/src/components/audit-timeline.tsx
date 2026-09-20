"use client";
import { useI18n } from "@/lib/i18n";
import { ShieldCheck, Cpu, UserRound, Clock3 } from "lucide-react";
import type { Audit } from "@/lib/types";
import { dateTime, humanize } from "@/lib/api";
import { EmptyState } from "./ui";
export function AuditTimeline({ entries }: { entries: Audit[] }) {
  const { t } = useI18n();
  if (!entries.length) return <EmptyState title={t("No audit entries yet")} />;
  return <ol className="audit-timeline">{entries.map((entry) => <li key={entry.id}><span className={"audit-icon actor-" + entry.actor_type.toLowerCase()}>{entry.action === "CASE_CLOSED_BY_HUMAN" ? <ShieldCheck size={16} /> : entry.actor_type === "AI" ? <Cpu size={16} /> : entry.actor_type === "HUMAN" ? <UserRound size={16} /> : <Clock3 size={16} />}</span><div><strong>{humanize(entry.action)}</strong><p>{entry.actor_name} <span className="audit-actor">{t(entry.actor_type)}</span></p>{entry.previous_value?.status != null && entry.new_value?.status != null && <p className="audit-transition">{humanize(String(entry.previous_value.status))} → {humanize(String(entry.new_value.status))}</p>}{entry.metadata_json?.notes ? <blockquote>{String(entry.metadata_json.notes)}</blockquote> : null}<time dateTime={entry.created_at}>{dateTime(entry.created_at)}</time></div></li>)}</ol>;
}
