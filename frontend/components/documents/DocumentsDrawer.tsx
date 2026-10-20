"use client";
import { useState } from "react";
import {
  BookOpen,
  Search,
  Upload,
  History,
  Files,
  Layers,
  ArrowUpRight,
  PanelLeft,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DocumentCard } from "./DocumentCard";
import { DocumentUploadDialog } from "./DocumentUploadDialog";
import { DocumentPreview, DocumentInfo } from "./DocumentPreview";
import { DeleteConfirmDialog } from "./DeleteConfirmDialog";
import { ManageDeletedDialog, DeletedDocInfo } from "./ManageDeletedDialog";
import { toast } from "sonner";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface LibraryProps {
  documents: DocumentInfo[];
  sessionId: string;
  onDocumentUploaded: (
    filename: string,
    chunks: number,
    sizeMb: string,
  ) => void;
  onDocumentDeleted: (filename: string) => void;
  onUseInChat?: (filename: string) => void;
  compact?: boolean;
  onToggleSidebar?: () => void;
}
interface DocumentsDrawerProps extends LibraryProps {
  open: boolean;
  onOpenChange: (value: boolean) => void;
}
export function DocumentLibrary({
  documents,
  sessionId,
  onDocumentUploaded,
  onDocumentDeleted,
  onUseInChat,
  compact,
  onToggleSidebar,
}: LibraryProps) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("recent");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [preview, setPreview] = useState<DocumentInfo | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<DeletedDocInfo[]>([]);
  const filtered = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(query.toLowerCase()),
  );
  if (sort === "name")
    filtered.sort((a, b) => a.filename.localeCompare(b.filename));
  const remove = async () => {
    if (!deleting || busy) return;
    const filename = deleting;
    setBusy(true);
    try {
      const response = await fetch(
        `${API_URL}/api/documents/${encodeURIComponent(filename)}?session_id=${encodeURIComponent(sessionId)}`,
        { method: "DELETE" },
      );
      if (!response.ok) throw new Error();
      onDocumentDeleted(filename);
      setHistory((previous) => [
        {
          filename,
          deletedAt: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          sizeMb:
            documents.find((doc) => doc.filename === filename)?.sizeMb ||
            "Size unavailable",
        },
        ...previous,
      ]);
      setDeleting(null);
      toast.success("Document removed from your library");
    } catch {
      toast.error("Could not remove the document. Please try again.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-background">
      {!compact && (
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-border px-4 sm:px-7">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <PanelLeft className="size-4" />
          </Button>
          <span className="text-xs text-muted-foreground">Workspace</span>
          <span className="text-xs text-muted-foreground/50">/</span>
          <span className="text-xs font-medium">Knowledge base</span>
        </header>
      )}
      <div
        className={`min-h-0 flex-1 overflow-y-auto ${compact ? "p-5" : "p-5 sm:p-10"}`}
      >
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div>
              <span className="section-label">YOUR PERSONAL LIBRARY</span>
              <h1
                className={`mt-3 font-medium tracking-tight ${compact ? "text-2xl" : "text-3xl sm:text-4xl"}`}
              >
                Knowledge, all together.
              </h1>
              <p className="mt-3 max-w-lg text-xs leading-6 text-muted-foreground">
                A home for your documents. Add what matters, then turn it into a
                conversation.
              </p>
            </div>
            <Button onClick={() => setUploadOpen(true)} className="gap-2">
              <Upload className="size-3.5" />
              Add documents
            </Button>
          </div>
          <div className="my-7 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Files className="size-3.5" />
                Documents
              </div>
              <p className="mt-3 text-2xl font-medium tracking-tight">
                {documents.length}
                <span className="ml-2 text-[11px] font-normal tracking-normal text-muted-foreground">
                  in your library
                </span>
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Layers className="size-3.5" />
                Indexed passages
              </div>
              <p className="mt-3 text-2xl font-medium tracking-tight">
                {documents
                  .reduce((sum, doc) => sum + (doc.chunks || 0), 0)
                  .toLocaleString()}
                <span className="ml-2 text-[11px] font-normal tracking-normal text-muted-foreground">
                  searchable
                </span>
              </p>
            </div>
          </div>
          <div className="mb-5 flex flex-wrap items-center gap-3">
            <div className="relative min-w-40 flex-1">
              <Search className="pointer-events-none absolute left-3 top-3 size-3.5 text-muted-foreground" />
              <Input
                aria-label="Search documents"
                placeholder="Find a document…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="pl-9 text-xs"
              />
            </div>
            <select
              aria-label="Sort documents"
              value={sort}
              onChange={(event) => setSort(event.target.value)}
              className="h-9 rounded-lg border border-input bg-card px-3 text-xs text-muted-foreground"
            >
              <option value="recent">Library order</option>
              <option value="name">Name A–Z</option>
            </select>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setHistoryOpen(true)}
              aria-label="View recently removed documents"
            >
              <History className="size-4" />
            </Button>
          </div>
          {filtered.length > 0 ? (
            <div
              className={`grid gap-4 ${compact ? "grid-cols-1" : "sm:grid-cols-2 xl:grid-cols-3"}`}
            >
              {filtered.map((doc) => (
                <DocumentCard
                  key={doc.filename}
                  doc={doc}
                  sessionId={sessionId}
                  onPreview={setPreview}
                  onDelete={setDeleting}
                  onUseInChat={onUseInChat}
                />
              ))}
            </div>
          ) : (
            <div className="flex min-h-72 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card/40 px-5 py-10 text-center">
              <span className="mb-5 flex size-14 items-center justify-center rounded-2xl border border-border bg-muted/50">
                <BookOpen className="size-6 text-primary" />
              </span>
              <h2 className="text-base font-medium">
                {query
                  ? "No documents match your search"
                  : "Good answers start with good sources"}
              </h2>
              <p className="mt-3 max-w-sm text-xs leading-6 text-muted-foreground">
                {query
                  ? "Try another name, or clear your search to see your library."
                  : "Add your first document and give your conversations a little more context."}
              </p>
              <Button
                variant="outline"
                className="mt-5 gap-2"
                onClick={() => (query ? setQuery("") : setUploadOpen(true))}
              >
                {query ? "Clear search" : "Upload your first document"}
                <ArrowUpRight className="size-3.5" />
              </Button>
            </div>
          )}
          <p className="mt-6 text-[11px] text-muted-foreground/70">
            PDF, Word, text, and Markdown. Your library is shared across your
            conversations.
          </p>
        </div>
      </div>
      <DocumentUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        sessionId={sessionId}
        onUploaded={onDocumentUploaded}
        documentCount={documents.length}
      />
      <DocumentPreview
        open={Boolean(preview)}
        document={preview}
        sessionId={sessionId}
        onOpenChange={(value) => {
          if (!value) setPreview(null);
        }}
        onUseInChat={onUseInChat}
      />
      <DeleteConfirmDialog
        open={Boolean(deleting)}
        filename={deleting || ""}
        onOpenChange={(value) => {
          if (!value && !busy) setDeleting(null);
        }}
        onConfirm={remove}
        isDeleting={busy}
      />
      <ManageDeletedDialog
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        deletedDocs={history}
      />
    </div>
  );
}
export function DocumentsDrawer({
  open,
  onOpenChange,
  ...props
}: DocumentsDrawerProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full gap-0 p-0 sm:max-w-xl">
        <div className="shrink-0 border-b border-border px-5 py-5">
          <SheetTitle className="flex items-center gap-2 text-sm">
            <BookOpen className="size-4 text-primary" />
            Knowledge base
          </SheetTitle>
          <SheetDescription className="mt-1 text-xs text-muted-foreground">
            Your sources, close to the conversation.
          </SheetDescription>
        </div>
        <DocumentLibrary {...props} compact />
      </SheetContent>
    </Sheet>
  );
}
