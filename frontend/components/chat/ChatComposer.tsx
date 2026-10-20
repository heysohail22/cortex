"use client";

import { useEffect, useId, useRef } from "react";
import {
  ArrowUp,
  Plus,
  BookOpen,
  Square,
  Sparkles,
  Globe2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: (text?: string) => void;
  isLoading: boolean;
  onStop?: () => void;
  onOpenDocuments?: () => void;
  hasDocuments?: boolean;
  source?: "rag" | "llm" | "web_search" | "hybrid" | "guardrail";
  disabled?: boolean;
}

const MAX_LENGTH = 4000;

export function ChatComposer({
  value,
  onChange,
  onSend,
  isLoading,
  onStop,
  onOpenDocuments,
  hasDocuments,
  source,
  disabled,
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const hintId = useId();
  const multiline = value.includes("\n") || value.length > 80;
  const tooLong = value.length > MAX_LENGTH;
  const canSend = Boolean(value.trim()) && !tooLong && !disabled && !isLoading;
  const documentSource =
    !isLoading && (source === "rag" || source === "hybrid");
  const webSource =
    !isLoading && (source === "web_search" || source === "hybrid");
  const assistantSource = !isLoading && (!source || source === "llm");
  const sourceBorder = documentSource
    ? "border-emerald-300/25 focus-within:border-emerald-300/55"
    : webSource
      ? "border-amber-300/25 focus-within:border-amber-300/55"
      : assistantSource
        ? "border-violet-300/25 focus-within:border-violet-300/55"
        : "border-white/12 focus-within:border-primary/45";
  const sendColor = documentSource
    ? "bg-emerald-300 text-emerald-950 hover:bg-emerald-200"
    : webSource
      ? "bg-amber-300 text-amber-950 hover:bg-amber-200"
      : "bg-violet-300 text-violet-950 hover:bg-violet-200";
  useEffect(() => {
    const textarea = ref.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [value]);
  const send = () => {
    if (canSend) onSend(value.trim());
  };

  return (
    <div className="mx-auto w-full max-w-[872px] shrink-0 px-4 pb-[max(16px,env(safe-area-inset-bottom))] pt-4 sm:px-7">
      <form
        aria-label="Message composer"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
        className={cn(
          "relative overflow-hidden rounded-[28px] border bg-[#1c1d21] p-2 shadow-[0_8px_40px_-16px_rgba(0,0,0,0.6)] transition-[border-color,box-shadow] duration-200 focus-within:shadow-[0_0_0_3px_rgba(196,177,240,0.04)]",
          tooLong
            ? "border-destructive/60 focus-within:border-destructive/60"
            : sourceBorder,
        )}
      >
        <div className="mx-2 mb-2 mt-1 flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2">
          <div
            role="group"
            aria-label="Automatic answer source"
            className="flex flex-wrap items-center gap-1.5"
          >
            {[
              {
                label: "Assistant",
                key: "llm",
                icon: Sparkles,
                active: assistantSource,
                activeColor:
                  "border-violet-300/30 bg-violet-300/12 text-violet-200",
                idleColor: "text-violet-300/50",
              },
              {
                label: "Documents",
                key: "rag",
                icon: BookOpen,
                active: documentSource,
                activeColor:
                  "border-emerald-300/30 bg-emerald-300/12 text-emerald-200",
                idleColor: "text-emerald-300/50",
              },
              {
                label: "Web search",
                key: "web_search",
                icon: Globe2,
                active: webSource,
                activeColor:
                  "border-amber-300/30 bg-amber-300/12 text-amber-200",
                idleColor: "text-amber-300/50",
              },
            ].map(
              ({ label, key, icon: Icon, active, activeColor, idleColor }) => (
                <span
                  key={key}
                  data-source={key}
                  data-active={active}
                  title={`${label}${active ? " · Current answer source" : ""}. Selected automatically by Cortex.`}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-medium transition-colors sm:px-2.5",
                    active ? activeColor : `border-transparent ${idleColor}`,
                  )}
                >
                  <Icon className="size-3" />
                  {label}
                  {active && (
                    <span className="sr-only"> (current answer source)</span>
                  )}
                </span>
              ),
            )}
          </div>
          <span
            className="hidden text-[9px] text-muted-foreground/60 sm:block"
            title={
              hasDocuments
                ? "Your library is available. Cortex selects sources automatically."
                : "Cortex selects the best source for each answer."
            }
          >
            {isLoading ? "Choosing source…" : "Auto source"}
          </span>
        </div>
        <div className="flex items-end gap-1.5 sm:gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            disabled={disabled}
            onClick={onOpenDocuments}
            aria-label="Add or manage documents"
            title="Add documents"
            className="mb-0.5 size-10 shrink-0 rounded-full text-muted-foreground hover:bg-white/5 hover:text-foreground"
          >
            <Plus className="size-5" />
          </Button>
          <Textarea
            ref={ref}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            rows={1}
            disabled={disabled}
            aria-label="Message Cortex"
            aria-describedby={hintId}
            aria-invalid={tooLong || undefined}
            placeholder={
              isLoading ? "Draft your next question…" : "Ask Cortex anything…"
            }
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing &&
                event.nativeEvent.keyCode !== 229
              ) {
                event.preventDefault();
                send();
              }
            }}
            className="max-h-[200px] min-h-11 flex-1 resize-none self-center rounded-none border-0 bg-transparent px-0.5 py-2.5 text-[15px] leading-6 shadow-none placeholder:text-muted-foreground/70 focus-visible:border-transparent focus-visible:outline-none focus-visible:ring-0"
          />
          {isLoading && onStop ? (
            <Button
              type="button"
              size="icon"
              onClick={onStop}
              aria-label="Stop response"
              title="Stop response"
              className="mb-0.5 size-10 shrink-0 rounded-full bg-foreground text-background hover:bg-foreground/90"
            >
              <Square className="size-3.5 fill-current" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              disabled={!canSend}
              aria-label="Send message"
              title="Send message"
              className={cn(
                "mb-0.5 size-10 shrink-0 rounded-full disabled:bg-white/8 disabled:text-muted-foreground/50 disabled:opacity-100",
                sendColor,
              )}
            >
              <ArrowUp className="size-5" />
            </Button>
          )}
        </div>
        {multiline && (
          <div className="mx-3 mb-1 mt-2 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-muted-foreground/60">
            <span className="flex items-center gap-1.5">
              <Sparkles className="size-3" />
              Make room for a bigger idea
            </span>
            <span className="hidden sm:block">
              Shift + Enter for a new line
            </span>
          </div>
        )}
      </form>
      <div
        id={hintId}
        aria-live="polite"
        className="mt-3 flex min-h-4 flex-wrap items-center justify-center gap-x-3 gap-y-1 text-center text-[10px] text-muted-foreground/60"
      >
        {tooLong ? (
          <span className="text-destructive">
            {value.length.toLocaleString()} / {MAX_LENGTH.toLocaleString()}{" "}
            characters. Shorten your message to send it.
          </span>
        ) : (
          <>
            <span>Cortex can make mistakes. Check important information.</span>
            <span className="hidden text-muted-foreground/35 sm:inline">·</span>
            <span className="hidden sm:inline">Enter to send</span>
            {value.length > MAX_LENGTH - 500 && (
              <span>
                {value.length.toLocaleString()} / {MAX_LENGTH.toLocaleString()}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
