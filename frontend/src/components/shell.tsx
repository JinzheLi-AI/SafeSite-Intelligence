"use client";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ScanLine, ClipboardList, Sparkles, BookOpen, ShieldCheck, ChevronDown, ArrowUpRight, HardHat, Radio, Menu, X } from "lucide-react";
import { LanguageSwitcher } from "@/lib/i18n";
import { useState } from "react";
const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/inspections", label: "AI Inspection", icon: ScanLine },
  { href: "/incidents", label: "Incidents", icon: ClipboardList },
  { href: "/analyst", label: "AI Safety Analyst", icon: Sparkles },
  { href: "/knowledge", label: "Knowledge Base", icon: BookOpen },
];
export function Shell({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const pathname = usePathname(); const [menu, setMenu] = useState(false);
  const current = links.find((l) => l.href === "/" ? pathname === "/" : pathname.startsWith(l.href));
  return <div className="app-shell"><a href="#main-content" className="skip-link">{t("Skip to main content")}</a>
    {menu && <button className="sidebar-scrim" aria-label={t("Close navigation")} onClick={() => setMenu(false)} />}
    <aside className={"sidebar " + (menu ? "sidebar-open" : "")}>
      <Link href="/" className="brand"><span className="brand-mark"><ShieldCheck size={25} /></span><span>SafeSite<span className="brand-sub">INTELLIGENCE</span></span></Link>
      <div className="workspace-chip"><span className="workspace-icon"><HardHat size={18} /></span><span>{t("Safety workspace")}<small>{t("Enterprise command center")}</small></span></div>
      <div className="nav-label">{t("WORKSPACE")}</div>
      <nav aria-label={t("Main navigation")}>{links.map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={() => setMenu(false)} className={"nav-link " + ((href === "/" ? pathname === "/" : pathname.startsWith(href)) ? "active" : "")}><Icon size={19} /><span>{t(label)}</span>{label === "AI Inspection" && <span className="nav-ai">{t("AI")}</span>}</Link>)}</nav>
      <div className="sidebar-bottom"><div className="governance-card"><div><ShieldCheck size={18} /><strong>{t("Human-led. AI-assisted.")}</strong></div><p>{t("Every finding reviewed.")}<br />{t("Every decision traceable.")}</p><Link href="/analyst">{t("AI governance")}{" "}<ArrowUpRight size={14} /></Link></div><div className="sidebar-version"><Radio size={12} /> {" "}{t("Competition demo")}{" "}<span>{t("v0.1")}</span></div></div>
    </aside>
    <div className="workspace-main"><header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" aria-label={menu ? t("Close navigation") : t("Open navigation")} onClick={() => setMenu(!menu)}>{menu ? <X size={20} /> : <Menu size={20} />}</button><span>{t("Workspace")}</span><span className="slash">/</span><strong>{t(current?.label ?? "Incident detail")}</strong></div><div className="header-right"><LanguageSwitcher /><span className="environment"><span />{t("Demo environment")}</span><div className="header-divider" /><div className="avatar">SO</div><div className="role">{t("Safety Officer")}<small>{t("Demo role")}</small></div><ChevronDown size={14} className="muted" /></div></header>
    <main id="main-content">{children}</main><footer className="footer"><span>SafeSite Intelligence</span><span>{t("AI-Powered Construction Safety Command Center")}</span><span>{t("Human decisions. Auditable outcomes.")}</span></footer></div>
  </div>;
}
