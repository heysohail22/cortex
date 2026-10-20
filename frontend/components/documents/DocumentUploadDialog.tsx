"use client";

import { useState } from "react";
import { ArrowUpRight, BookOpen } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { DocumentUpload } from "./DocumentUpload";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionId: string;
  onUploaded: (filename: string, chunks: number, sizeMb: string) => void;
  documentCount?: number;
  onViewLibrary?: () => void;
}

export function DocumentUploadDialog({
  open,
  onOpenChange,
  sessionId,
  onUploaded,
  documentCount = 0,
  onViewLibrary,
}: Props) {
  const [uploading, setUploading] = useState(false);
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!uploading) onOpenChange(next);
      }}
    >
      <DialogContent className="max-w-lg overflow-y-auto border-emerald-300/15 p-0 [--primary:#6ee7b7] [--primary-foreground:#022c22]">
        <DialogHeader className="border-b border-border bg-emerald-300/[0.03] px-6 pb-5 pt-6 text-left">
          <span className="mb-3 flex size-10 items-center justify-center rounded-xl border border-emerald-300/20 bg-emerald-300/10 text-emerald-300">
            <BookOpen className="size-5" />
          </span>
          <span className="section-label text-emerald-300/80">
            KNOWLEDGE BASE
          </span>
          <DialogTitle className="text-xl">
            Bring your documents into the conversation
          </DialogTitle>
          <DialogDescription>
            Upload a file and ask Cortex to find answers in your own sources.
          </DialogDescription>
        </DialogHeader>
        <div className="px-6 pb-5">
          <DocumentUpload
            sessionId={sessionId}
            isUploading={uploading}
            setIsUploading={setUploading}
            onUploaded={(filename, chunks, sizeMb) => {
              onUploaded(filename, chunks, sizeMb);
              onOpenChange(false);
            }}
          />
        </div>
        <DialogFooter className="items-center border-t border-border bg-muted/20 px-6 py-4 sm:justify-between">
          <span className="text-[11px] text-muted-foreground">
            {documentCount} {documentCount === 1 ? "document" : "documents"} in
            your library
          </span>
          {onViewLibrary ? (
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-xs text-emerald-300"
              disabled={uploading}
              onClick={() => {
                onOpenChange(false);
                onViewLibrary();
              }}
            >
              View library
              <ArrowUpRight className="size-3.5" />
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              disabled={uploading}
              onClick={() => onOpenChange(false)}
            >
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
