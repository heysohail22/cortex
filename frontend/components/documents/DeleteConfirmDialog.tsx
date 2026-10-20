"use client";
import { Trash2, Loader2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
export function DeleteConfirmDialog({
  open,
  filename,
  onOpenChange,
  onConfirm,
  isDeleting,
}: {
  open: boolean;
  filename: string;
  onOpenChange: (value: boolean) => void;
  onConfirm: () => void;
  isDeleting?: boolean;
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <span className="flex size-12 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
          <Trash2 className="size-5" />
        </span>
        <AlertDialogHeader>
          <AlertDialogTitle>Remove this source?</AlertDialogTitle>
          <AlertDialogDescription>
            <span className="break-all font-medium text-foreground">
              {filename}
            </span>{" "}
            will be removed from your library. Future answers will no longer use
            it. You’ll need the original file to upload it again.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>
            Keep document
          </AlertDialogCancel>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
            className="gap-2"
          >
            {isDeleting && <Loader2 className="size-3.5 animate-spin" />}
            {isDeleting ? "Removing…" : "Remove document"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
