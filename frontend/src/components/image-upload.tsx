"use client";
import { useI18n } from "@/lib/i18n";
import { useId, useRef, useState } from "react";
import { UploadCloud, ImageIcon, X } from "lucide-react";
export function ImageUpload({ file, onChange, disabled = false, required = false, label = "Construction image" }: { file: File | null; onChange: (file: File | null) => void; disabled?: boolean; required?: boolean; label?: string }) {
  const { t } = useI18n();
  const input = useRef<HTMLInputElement>(null); const id = useId(); const [drag, setDrag] = useState(false); const [error, setError] = useState("");
  function accept(next: File | undefined) {
    if (!next || disabled) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(next.type)) { setError("Choose a JPG, PNG or WebP image."); return; }
    if (next.size > 10 * 1024 * 1024) { setError("Choose an image smaller than 10 MB."); return; }
    setError(""); onChange(next);
  }
  return <div><label className="field-label" htmlFor={id}>{t(label)}<span>{required ? t("Required for real AI") : t("Optional in demo mode")}</span></label><input ref={input} id={id} type="file" className="sr-only" accept="image/jpeg,image/png,image/webp" disabled={disabled} onChange={(e) => accept(e.target.files?.[0])} /><button type="button" disabled={disabled} className={"upload-zone " + (drag ? "drag-active" : "")} onClick={() => input.current?.click()} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={(e) => { e.preventDefault(); setDrag(false); accept(e.dataTransfer.files[0]); }}>
    <span className="upload-icon">{file ? <ImageIcon size={26} /> : <UploadCloud size={26} />}</span><strong>{file ? file.name : t("Drop your site image here")}</strong><span>{file ? (file.size / 1024 / 1024).toFixed(1) + t(" MB · ready to upload") : <>{t("or")}{" "}<b>{t("browse files")}</b> {" "}{t("to upload")}</>}</span><small>{t("JPG, PNG or WebP · Up to 10 MB")}</small></button>{file && <button type="button" className="remove-file" onClick={() => { onChange(null); if (input.current) input.current.value = ""; }} disabled={disabled}><X size={13} />{t("Remove image")}</button>}{error && <p className="field-error" role="alert">{t(error)}</p>}</div>;
}
