"use client";
import {
  FileText,
  Download,
  MessageSquarePlus,
  CalendarDays,
  Layers,
  HardDrive,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export interface DocumentInfo {
  filename: string;
  chunks?: number;
  sizeMb?: string;
  uploadDate?: string;
}
interface Props {
  open: boolean;
  document: DocumentInfo | null;
  sessionId?: string;
  onOpenChange: (open: boolean) => void;
  onUseInChat?: (filename: string) => void;
}
export function DocumentPreview({
  open,
  document,
  sessionId,
  onOpenChange,
  onUseInChat,
}: Props) {
  if (!document) return null;
  const download = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/documents/${encodeURIComponent(document.filename)}/url?session_id=${encodeURIComponent(sessionId || "")}`,
      );
      const data = await response.json();
      if (!response.ok || !data.url) throw new Error();
      window.open(data.url, "_blank", "noopener,noreferrer");
    } catch {
      toast.error("Could not open the original document");
    }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg overflow-hidden p-0">
        <div className="border-b border-border bg-muted/30 px-6 pb-6 pt-7">
          <span className="mb-5 flex size-14 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary">
            <FileText className="size-6" />
          </span>
          <DialogHeader>
            <span className="section-label">DOCUMENT DETAILS</span>
            <DialogTitle className="break-all pr-3 text-xl leading-7">
              {document.filename}
            </DialogTitle>
            <DialogDescription>
              A source in your personal knowledge base.
            </DialogDescription>
          </DialogHeader>
        </div>
        <div className="px-6 py-2">
          <dl className="divide-y divide-border">
            {[
              {
                icon: Layers,
                label: "Indexed passages",
                value: document.chunks ?? "Unavailable",
              },
              {
                icon: HardDrive,
                label: "File size",
                value: document.sizeMb || "Unavailable",
              },
              {
                icon: CalendarDays,
                label: "Date added",
                value: document.uploadDate || "Unavailable",
              },
            ].map(({ icon: Icon, label, value }) => (
              <div
                key={label}
                className="flex items-center justify-between gap-4 py-4 text-xs"
              >
                <dt className="flex items-center gap-2 text-muted-foreground">
                  <Icon className="size-4" />
                  {label}
                </dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <p className="mb-5 mt-2 rounded-lg bg-muted/50 p-3 text-xs leading-6 text-muted-foreground">
            Ask Cortex to summarize this document, explain a section, or find a
            specific detail. Answers can include citations back to your source.
          </p>
        </div>
        <DialogFooter className="border-t border-border px-6 py-4">
          <Button variant="outline" onClick={download} className="gap-2">
            <Download className="size-3.5" />
            Download
          </Button>
          {onUseInChat && (
            <Button
              onClick={() => {
                onUseInChat(document.filename);
                onOpenChange(false);
              }}
              className="gap-2"
            >
              <MessageSquarePlus className="size-3.5" />
              Use in conversation
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
