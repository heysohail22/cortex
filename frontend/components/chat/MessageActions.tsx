"use client";
import { useState } from "react";
import {
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Globe2,
  ArrowUpRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { RetrievalDetailsDialog } from "./RetrievalDetailsDialog";
import { VerificationStatus } from "@/lib/verification";
import { toast } from "sonner";
interface MessageActionsProps {
  content: string;
  timestamp?: string;
  source?: "rag" | "llm" | "web_search" | "hybrid" | "guardrail";
  chunksCount?: number;
  chunks?: Array<{ source: string; text: string; similarity?: number }>;
  webResults?: Array<{ title: string; url: string; content: string }>;
  evaluationResult?: string;
  evaluationReason?: string;
  isGrounded?: boolean | null;
  verificationStatus?: VerificationStatus;
  groundednessReason?: string;
  route?: string;
  transformedQuery?: string;
  question?: string;
  suggestWebSearch?: boolean;
  onWebSearchFallback?: (question: string) => void;
  detailsOpen?: boolean;
  setDetailsOpen?: (open: boolean) => void;
}
export function MessageActions(props: MessageActionsProps) {
  const [copied, setCopied] = useState(false);
  const [vote, setVote] = useState<boolean | null>(null);
  const [open, setOpen] = useState(false);
  const setDetails = props.setDetailsOpen ?? setOpen;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(props.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error("Could not copy the answer");
    }
  };
  return (
    <>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-border/70 pt-3">
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={copied ? "Answer copied" : "Copy answer"}
            onClick={copy}
          >
            {copied ? (
              <Check className="size-3.5 text-emerald-300" />
            ) : (
              <Copy className="size-3.5" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Mark answer helpful"
            aria-pressed={vote === true}
            onClick={() => setVote(vote === true ? null : true)}
            className={vote === true ? "bg-primary/10 text-primary" : ""}
          >
            <ThumbsUp className="size-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Mark answer unhelpful"
            aria-pressed={vote === false}
            onClick={() => setVote(vote === false ? null : false)}
            className={vote === false ? "bg-primary/10 text-primary" : ""}
          >
            <ThumbsDown className="size-3.5" />
          </Button>
          {vote !== null && (
            <span className="ml-2 text-[10px] text-muted-foreground">
              Marked for this visit
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setDetails(true)}
          className="gap-1.5 text-[11px]"
        >
          Behind this answer
          <ArrowUpRight className="size-3" />
        </Button>
      </div>
      {props.suggestWebSearch &&
        props.question &&
        props.onWebSearchFallback && (
          <Button
            variant="outline"
            size="sm"
            className="mt-3 max-w-full gap-2"
            onClick={() => props.onWebSearchFallback?.(props.question!)}
          >
            <Globe2 className="size-3.5 shrink-0" />
            <span className="truncate">Explore this question on the web</span>
          </Button>
        )}
      <RetrievalDetailsDialog
        {...props}
        open={props.detailsOpen ?? open}
        onOpenChange={setDetails}
      />
    </>
  );
}
