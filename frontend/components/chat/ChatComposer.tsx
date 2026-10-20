"use client";

import { useEffect, useId, useRef } from "react";
import { ArrowUp, Plus, BookOpen, Square, Sparkles } from "lucide-react";
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
  disabled,
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const hintId = useId();
  const multiline = value.includes("\n") || value.length > 80;
  const tooLong = value.length > MAX_LENGTH;
  const canSend = Boolean(value.trim()) && !tooLong && !disabled && !isLoading;
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
          "relative overflow-hidden rounded-[28px] border bg-[#1c1d21] p-2 shadow-[0_8px_40px_-16px_rgba(0,0,0,0.6)] transition-[border-color,box-shadow] duration-200 focus-within:border-primary/45 focus-within:shadow-[0_0_0_3px_rgba(196,177,240,0.04)]",
          tooLong ? "border-destructive/60" : "border-white/12",
        )}
      >
        {hasDocuments && (
          <button
            type="button"
            disabled={disabled}
            onClick={onOpenDocuments}
            className="mb-1 ml-3 mt-1 flex items-center gap-1.5 rounded-full border border-primary/15 bg-primary/[0.06] px-2.5 py-1 text-[10px] text-primary transition-colors hover:bg-primary/10"
          >
            <BookOpen className="size-3" />
            Your knowledge base
          </button>
        )}
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
              className="mb-0.5 size-10 shrink-0 rounded-full bg-foreground text-background hover:bg-primary hover:text-primary-foreground disabled:bg-white/8 disabled:text-muted-foreground/50 disabled:opacity-100"
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
