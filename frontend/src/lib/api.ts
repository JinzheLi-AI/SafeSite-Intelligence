import { getLocale, translate } from "./i18n";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(API_URL + path, { ...options, cache: "no-store", headers: { "X-SafeSite-Language": getLocale(), ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...options.headers } });
  } catch {
    throw new Error("Cannot reach the safety API. Check that the backend is running on port 8000.");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = payload.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((e: { msg: string }) => e.msg).join("; ") : "Request failed. Please try again.");
  }
  return response.json() as Promise<T>;
}
export function post<T>(path: string, data: object = {}): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(data) });
}
export async function upload(file: File): Promise<string> {
  const form = new FormData(); form.append("file", file);
  return (await api<{ image_path: string }>("/uploads", { method: "POST", body: form })).image_path;
}
export function imageUrl(path: string): string { return API_URL.replace(/\/api\/v1\/?$/, "") + path; }
export function errorMessage(error: unknown): string { return error instanceof Error ? error.message : "Something went wrong. Please retry."; }
export function humanize(value: string): string { return translate(value) !== value ? translate(value) : translate(value.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())); }
export function dateTime(value: string | null): string {
  return value ? new Intl.DateTimeFormat(getLocale() === "zh-CN" ? "zh-CN" : "en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value)) : translate("Not set");
}
