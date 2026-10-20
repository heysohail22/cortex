"use client";
import {
  FileText,
  MoreHorizontal,
  Eye,
  MessageSquarePlus,
  Download,
  Trash2,
  ArrowUpRight,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { DocumentInfo } from "./DocumentPreview";
import { toast } from "sonner";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface Props {
  doc: DocumentInfo;
  sessionId?: string;
  onPreview: (doc: DocumentInfo) => void;
  onDelete: (filename: string) => void;
  onUseInChat?: (filename: string) => void;
}
export function DocumentCard({
  doc,
  sessionId,
  onPreview,
  onDelete,
  onUseInChat,
}: Props) {
  const extension = doc.filename.split(".").pop()?.toUpperCase() || "FILE";
  const download = async () => {
    try {
      const res = await fetch(
        `${API_URL}/api/documents/${encodeURIComponent(doc.filename)}/url?session_id=${encodeURIComponent(sessionId || "")}`,
      );
      const data = await res.json();
      if (!res.ok || !data.url) throw new Error();
      window.open(data.url, "_blank", "noopener,noreferrer");
    } catch {
      toast.error("The original file is unavailable right now");
    }
  };
  return (
    <Card className="group flex min-w-0 flex-col bg-card p-5 shadow-none transition-colors hover:border-primary/35">
      <div className="mb-5 flex items-start justify-between">
        <span
          className={`flex size-11 items-center justify-center rounded-xl ${extension === "PDF" ? "bg-rose-400/10 text-rose-300" : extension === "DOCX" ? "bg-sky-400/10 text-sky-300" : "bg-primary/10 text-primary"}`}
        >
          <FileText className="size-5" />
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={`Actions for ${doc.filename}`}
            >
              <MoreHorizontal className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onPreview(doc)}>
              <Eye className="mr-2 size-4" />
              Document details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={download}>
              <Download className="mr-2 size-4" />
              Download original
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => onDelete(doc.filename)}
            >
              <Trash2 className="mr-2 size-4" />
              Remove document
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <button onClick={() => onPreview(doc)} className="text-left">
        <span
          className="block truncate text-sm font-medium text-foreground"
          title={doc.filename}
        >
          {doc.filename}
        </span>
        <span className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
          <span>{extension}</span>
          <span>·</span>
          <span>{doc.sizeMb || "Size unavailable"}</span>
        </span>
      </button>
      <div className="mt-5 flex items-center justify-between gap-2 border-t border-border pt-4">
        <span className="text-[10px] text-muted-foreground">
          {doc.chunks != null ? `${doc.chunks} passages` : "Added to library"}
        </span>
        {onUseInChat ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onUseInChat(doc.filename)}
            className="h-7 gap-1 px-1 text-[11px] text-primary"
          >
            <MessageSquarePlus className="size-3" />
            Ask a question
            <ArrowUpRight className="size-3" />
          </Button>
        ) : (
          <Button variant="ghost" size="sm" onClick={() => onPreview(doc)}>
            View details
          </Button>
        )}
      </div>
    </Card>
  );
}
