"use client";

import {
  ArrowUpRight,
  FileText,
  Globe2,
  Sparkles,
  Upload,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
  onOpenDocuments: () => void;
}

const suggestions = [
  {
    icon: BookOpen,
    label: "Understand a topic",
    detail: "Make the complex feel simple",
    prompt:
      "Explain how retrieval-augmented generation works, with a simple example.",
  },
  {
    icon: Globe2,
    label: "Explore what’s new",
    detail: "Find a fresh perspective",
    prompt:
      "Search the web for the latest developments in artificial intelligence.",
  },
  {
    icon: Sparkles,
    label: "Connect the dots",
    detail: "Turn information into ideas",
    prompt: "Help me compare RAG and fine-tuning. When should I use each?",
  },
];

export function EmptyState({
  onSelectPrompt,
  onOpenDocuments,
}: EmptyStateProps) {
  return (
    <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col justify-center py-10 sm:py-16 animate-fade-in">
      <div className="mb-6 flex items-center gap-2 text-xs font-medium tracking-wide text-primary">
        <span className="flex size-7 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
          <Sparkles className="size-3.5" />
        </span>
        A little curiosity goes a long way
      </div>
      <h1 className="text-4xl font-medium leading-[1.15] tracking-[-0.045em] text-foreground sm:text-5xl">
        Big questions.
        <br />
        <span className="text-muted-foreground/75">Clearer answers.</span>
      </h1>
      <p className="mt-5 max-w-md text-sm leading-7 text-muted-foreground">
        Your documents, the web, and a fresh perspective.
        <br className="hidden sm:block" /> Bring it all together in one
        conversation.
      </p>
      <div className="mt-9 grid gap-3 sm:grid-cols-3">
        {suggestions.map(({ icon: Icon, label, detail, prompt }) => (
          <Button
            key={label}
            variant="ghost"
            onClick={() => onSelectPrompt(prompt)}
            className="group h-auto flex-col items-start gap-4 whitespace-normal rounded-xl border border-border bg-white/[0.015] p-4 text-left hover:border-primary/30 hover:bg-white/[0.04]"
          >
            <div className="flex w-full items-center justify-between">
              <Icon className="size-4 text-muted-foreground" />
              <ArrowUpRight className="size-3.5 text-muted-foreground/50 transition-colors group-hover:text-primary" />
            </div>
            <div>
              <span className="block text-xs font-medium text-foreground">
                {label}
              </span>
              <span className="mt-1.5 block text-[11px] font-normal text-muted-foreground/75">
                {detail}
              </span>
            </div>
          </Button>
        ))}
      </div>
      <Card className="mt-5 flex flex-col justify-between gap-4 border-dashed bg-transparent p-4 shadow-none sm:flex-row sm:items-center">
        <div className="flex items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/5">
            <FileText className="size-4 text-muted-foreground" />
          </div>
          <div>
            <p className="text-xs font-medium text-foreground">
              Make it your knowledge space
            </p>
            <p className="mt-1 text-[11px] text-muted-foreground/75">
              Add documents. Ask questions. Find what matters.
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onOpenDocuments}
          className="gap-2 text-xs"
        >
          <Upload className="size-3.5" />
          Add documents
        </Button>
      </Card>
      <p className="mt-7 text-[10px] tracking-wide text-muted-foreground/50">
        BUILT FOR YOUR NEXT “AHA” MOMENT
      </p>
    </div>
  );
}
