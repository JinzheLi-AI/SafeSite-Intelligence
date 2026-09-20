"use client";
import { useI18n } from "@/lib/i18n";
import { ArrowUpRight, LoaderCircle, AlertCircle, Inbox } from "lucide-react";
import type { ReactNode, ButtonHTMLAttributes } from "react";
import { humanize } from "@/lib/api";
export function Badge({ value }: { value: string }) {
  useI18n(); return <span className={"badge badge-" + value.toLowerCase()}><span className="badge-dot" />{humanize(value)}</span>; }
export function Button({ children, variant = "primary", busy, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger"; busy?: boolean }) {
  useI18n();
  return <button {...props} disabled={props.disabled || busy} className={"button button-" + variant + " " + (props.className ?? "")}>{busy && <LoaderCircle size={16} className="spin" />}{children}</button>;
}
export function PageHeading({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: ReactNode }) {
  const { t } = useI18n();
  return <div className="page-heading"><div><div className="eyebrow">{t(eyebrow)}</div><h1>{t(title)}</h1><p>{t(description)}</p></div><div className="heading-actions">{children}</div></div>;
}
export function Panel({ title, subtitle, children, action, className = "" }: { title?: string; subtitle?: string; children: ReactNode; action?: ReactNode; className?: string }) {
  const { t } = useI18n();
  return <section className={"panel " + className}>{title && <div className="panel-heading"><div><h2>{t(title)}</h2>{subtitle && <p>{t(subtitle)}</p>}</div>{action}</div>}{children}</section>;
}
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  const { t } = useI18n();
  return <div className="error-state" role="alert"><AlertCircle size={20} /><div><strong>{t("We couldn’t complete that request")}</strong><p>{t(message)}</p>{retry && <Button variant="secondary" onClick={retry}>{t("Try again")}</Button>}</div></div>;
}
export function LoadingState({ label = "Loading workspace…" }: { label?: string }) {
  const { t } = useI18n(); return <div className="loading-state" role="status"><LoaderCircle className="spin" size={24} /><span>{t(label)}</span></div>; }
export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  const { t } = useI18n(); return <div className="empty-state"><Inbox size={30} /><h3>{t(title)}</h3>{children}</div>; }
export function Metric({ label, value, note, tone = "neutral", icon }: { label: string; value: number | string; note: string; tone?: string; icon: ReactNode }) {
  const { t } = useI18n();
  return <div className={"metric metric-" + tone}><div className="metric-top"><span>{t(label)}</span><span className="metric-icon">{icon}</span></div><div className="metric-value">{value}</div><div className="metric-note"><ArrowUpRight size={14} />{t(note)}</div></div>;
}
export function DemoNote({ children }: { children?: ReactNode }) {
  const { t } = useI18n(); return <div className="demo-note"><span className="demo-pill">{t("DEMO")}</span><span>{children ?? t("Mock AI results and sample guidance. Human review is required; recommendations are not legally binding decisions.")}</span></div>; }
