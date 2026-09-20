"use client";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { EmptyState } from "@/components/ui";
export default function NotFound() {
  const { t } = useI18n(); return <EmptyState title={t("Page not found")}><p>{t("This workspace page does not exist.")}</p><Link className="button button-primary" href="/">{t("Back to dashboard")}</Link></EmptyState>; }
