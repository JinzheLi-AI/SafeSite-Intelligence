"use client";
import { useI18n } from "@/lib/i18n";
import { ErrorState } from "@/components/ui";
export default function ErrorPage({ reset }: { reset: () => void }) {
  useI18n(); return <ErrorState message="This page could not load. Try again or check the backend connection." retry={reset} />; }
