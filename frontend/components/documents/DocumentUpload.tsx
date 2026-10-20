"use client";
import { useRef, useState } from "react";
import {
  AlertCircle,
  FileUp,
  FileText,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface Props {
  sessionId: string;
  onUploaded: (filename: string, chunks: number, sizeMb: string) => void;
  isUploading: boolean;
  setIsUploading: (value: boolean) => void;
}
export function DocumentUpload({
  sessionId,
  onUploaded,
  isUploading,
  setIsUploading,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const busy = useRef(false);
  const [dragging, setDragging] = useState(false);
  const [filename, setFilename] = useState("");
  const [error, setError] = useState<string | null>(null);
  const upload = async (file?: File) => {
    if (!file || busy.current || isUploading) return;
    if (!/\.(pdf|docx|txt|md)$/i.test(file.name)) {
      setError("Choose a PDF, DOCX, TXT, or Markdown file.");
      return;
    }
    busy.current = true;
    setError(null);
    setFilename(file.name);
    setIsUploading(true);
    const form = new FormData();
    form.append("file", file);
    form.append("session_id", sessionId);
    try {
      const response = await fetch(`${API_URL}/api/documents/upload`, {
        method: "POST",
        body: form,
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "We couldn’t process this document. Please try another file.",
        );
      onUploaded(
        data.filename,
        data.chunks,
        `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      );
      toast.success(`${data.filename} added to your library`);
    } catch (cause) {
      const message =
        cause instanceof Error
          ? cause.message
          : "Upload failed. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      busy.current = false;
      setIsUploading(false);
      setFilename("");
      if (inputRef.current) inputRef.current.value = "";
    }
  };
  return (
    <div className="space-y-5">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!isUploading) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          void upload(event.dataTransfer.files[0]);
        }}
        className={`flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed p-7 text-center transition-colors ${dragging ? "border-primary bg-primary/10" : "border-border bg-muted/30"}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          aria-label="Choose a document to upload"
          className="sr-only"
          disabled={isUploading}
          onChange={(event) => void upload(event.target.files?.[0])}
          tabIndex={-1}
        />
        <span className="mb-5 flex size-14 items-center justify-center rounded-2xl border border-primary/15 bg-primary/10 text-primary">
          {isUploading ? (
            <Loader2 className="size-6 animate-spin" />
          ) : (
            <FileUp className="size-6" />
          )}
        </span>
        <p className="max-w-full break-all text-sm font-medium">
          {isUploading ? filename : "Drop your knowledge here"}
        </p>
        <p className="mb-5 mt-2 text-xs leading-6 text-muted-foreground">
          {isUploading
            ? "Uploading and preparing your document. This may take a moment."
            : "Drag a document here, or choose a file from your device."}
        </p>
        <Button
          variant="outline"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
          className="gap-2"
        >
          <FileUp className="size-3.5" />
          {isUploading ? "Processing document…" : "Choose a file"}
        </Button>
        <p className="mt-4 text-[10px] tracking-wider text-muted-foreground">
          PDF · DOCX · TXT · MARKDOWN
        </p>
      </div>
      {error && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-destructive/20 bg-destructive/5 p-3 text-xs leading-6 text-destructive"
        >
          <AlertCircle className="mt-1 size-4 shrink-0" />
          {error}
        </div>
      )}
      <div className="space-y-4">
        <div className="flex gap-3">
          <FileText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div>
            <p className="text-xs font-medium">From files to useful answers</p>
            <p className="mt-1 text-xs leading-6 text-muted-foreground">
              Reports, notes, guides, or research. Add a source and ask
              questions in your own words.
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div>
            <p className="text-xs font-medium">Keep the context close</p>
            <p className="mt-1 text-xs leading-6 text-muted-foreground">
              Uploaded documents become available to your conversations in this
              workspace.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
