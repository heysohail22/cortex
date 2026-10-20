"use client";
import { FileText, History } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
export interface DeletedDocInfo {
  filename: string;
  deletedAt: string;
  sizeMb: string;
}
export function ManageDeletedDialog({
  open,
  onOpenChange,
  deletedDocs,
}: {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  deletedDocs: DeletedDocInfo[];
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <span className="mb-3 flex size-10 items-center justify-center rounded-xl bg-muted text-muted-foreground">
            <History className="size-5" />
          </span>
          <DialogTitle>Recently removed</DialogTitle>
          <DialogDescription>
            Document removals during this visit. To use a removed document
            again, upload the original file.
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-72 space-y-2 overflow-auto">
          {deletedDocs.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border py-10 text-center">
              <History className="mx-auto mb-3 size-6 text-muted-foreground/50" />
              <p className="text-sm">Nothing removed yet</p>
              <p className="mt-2 text-xs text-muted-foreground">
                Your removal history will appear here.
              </p>
            </div>
          ) : (
            deletedDocs.map((doc, index) => (
              <div
                key={`${doc.filename}-${index}`}
                className="flex items-center gap-3 rounded-xl border border-border p-3"
              >
                <FileText className="size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="truncate text-xs">{doc.filename}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {doc.deletedAt} · {doc.sizeMb}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
