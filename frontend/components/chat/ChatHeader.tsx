"use client";

import { FileText, PanelLeft, ChevronRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatHeaderProps {
  title: string;
  docCount: number;
  onOpenDocuments: () => void;
  onToggleSidebar?: () => void;
  sidebarOpen?: boolean;
}

export function ChatHeader({
  title,
  docCount,
  onOpenDocuments,
  onToggleSidebar,
  sidebarOpen,
}: ChatHeaderProps) {
  return (
    <header className="z-20 flex h-16 shrink-0 items-center justify-between gap-3 border-b border-border px-4 sm:px-7">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          aria-expanded={sidebarOpen}
        >
          <PanelLeft className="size-4" />
        </Button>
        <span className="hidden text-xs text-muted-foreground/75 sm:block">
          Workspace
        </span>
        <ChevronRight className="hidden size-3 text-muted-foreground/50 sm:block" />
        <span className="truncate text-xs font-medium text-foreground">
          {title}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="hidden items-center gap-1.5 text-[11px] text-muted-foreground/75 md:flex">
          <Sparkles className="size-3 text-primary" />
          Cortex assistant
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={onOpenDocuments}
          className="gap-2"
        >
          <FileText className="size-3.5" />
          <span className="hidden sm:inline">Knowledge base</span>
          <span className="rounded bg-white/5 px-1.5 text-[10px] text-muted-foreground">
            {docCount}
          </span>
        </Button>
      </div>
    </header>
  );
}
