import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import "./globals.css";
import { LocaleProvider } from "@/lib/i18n";
import { ProjectProvider } from "@/lib/project-context";
export const metadata: Metadata = { title: { default: "SafeSite Intelligence", template: "%s · SafeSite Intelligence" }, description: "AI-Powered Construction Safety Command Center. Human-led construction safety workflows." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><LocaleProvider><ProjectProvider><Shell>{children}</Shell></ProjectProvider></LocaleProvider></body></html>;
}
