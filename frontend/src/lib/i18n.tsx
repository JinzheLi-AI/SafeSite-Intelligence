"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import en from "../../../shared/locales/en.json";
import zh from "../../../shared/locales/zh-CN.json";
export type Locale = "en" | "zh-CN";
export const LOCALE_KEY = "safesite.locale";
let activeLocale: Locale = "en";
export function getLocale(): Locale { return activeLocale; }
export function translate(text: string | number | null | undefined, locale: Locale = activeLocale, values: Record<string, string | number> = {}): string {
  const source = String(text ?? "");
  const dictionary: Record<string, string> = locale === "zh-CN" ? zh : en;
  let output = dictionary[source] ?? source;
  if (output === source && locale === "zh-CN") {
    for (const [template, target] of Object.entries(dictionary).sort((a,b) => b[0].length-a[0].length)) {
      const names = [...template.matchAll(/\{(\w+)\}/g)].map(m => m[1]);
      if (!names.length) continue;
      let pattern = template.replace(/[.*+?^\$()|[\]\\]/g, "\\$&");
      for (const name of names) pattern = pattern.replace("{" + name + "}", "(.+?)");
      const match = new RegExp("^" + pattern + "$", "s").exec(source);
      if (match) { output = target; names.forEach((name, i) => { output = output.replaceAll("{" + name + "}", dictionary[match[i + 1]] ?? match[i + 1]); }); break; }
    }
  }
  for (const [key, value] of Object.entries(values)) output = output.replaceAll("{" + key + "}", String(value));
  return output;
}
type Translator = (text: string | number | null | undefined, values?: Record<string, string | number>) => string;
const LocaleContext = createContext<{ locale: Locale; setLocale: (locale: Locale) => void; t: Translator }>({ locale: "en", setLocale: () => {}, t: text => String(text ?? "") });
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, update] = useState<Locale>("en");
  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(LOCALE_KEY); } catch {}
    if (saved === "zh-CN") { activeLocale = saved; queueMicrotask(() => update("zh-CN")); document.documentElement.lang = saved; }
  }, []);
  function setLocale(next: Locale) {
    activeLocale = next; update(next); document.documentElement.lang = next;
    try { localStorage.setItem(LOCALE_KEY, next); } catch {}
  }
  return <LocaleContext.Provider value={{ locale, setLocale, t: (text, values = {}) => translate(text, locale, values) }}>{children}</LocaleContext.Provider>;
}
export function useI18n() { return useContext(LocaleContext); }
export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();
  return <div className="language-switcher" role="group" aria-label="Language / 语言"><button type="button" lang="en" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>EN</button><span aria-hidden="true">|</span><button type="button" lang="zh-CN" aria-pressed={locale === "zh-CN"} onClick={() => setLocale("zh-CN")}>中文</button></div>;
}
