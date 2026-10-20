"use client";
import { useEffect, useRef } from "react";
import { ArrowUp, Paperclip, Sparkles, Loader2, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: (text?: string) => void;
  isLoading: boolean;
  onOpenDocuments?: () => void;
  hasDocuments?: boolean;
}
export function ChatComposer({
  value,
  onChange,
  onSend,
  isLoading,
  onOpenDocuments,
  hasDocuments,
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 180)}px`;
    }
  }, [value]);
  const send = () => {
    if (value.trim() && !isLoading) onSend(value.trim());
  };
  return (
    <div className="mx-auto w-full max-w-[872px] shrink-0 px-4 pb-[max(16px,env(safe-area-inset-bottom))] pt-3 sm:px-7">
      <div className="rounded-2xl border border-input bg-card p-3 shadow-lg shadow-black/10 transition-colors focus-within:border-primary/50">
        <Textarea
          ref={ref}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (
              !event.nativeEvent.isComposing &&
              event.key === "Enter" &&
              !event.shiftKey
            ) {
              event.preventDefault();
              send();
            }
          }}
          rows={2}
          aria-label="Message Cortex"
          placeholder="Ask a question, or explore an idea…"
          disabled={isLoading}
          className="max-h-44 min-h-16 resize-none rounded-none border-0 bg-transparent px-2 py-1.5 text-sm leading-7 shadow-none focus-visible:border-transparent focus-visible:ring-0"
        />
        <div className="mt-2 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Attach or manage documents"
              onClick={onOpenDocuments}
            >
              <Paperclip className="size-4" />
            </Button>
            <span className="h-4 w-px bg-border" />
            <span className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
              {hasDocuments ? (
                <BookOpen className="size-3 text-primary" />
              ) : (
                <Sparkles className="size-3 text-primary" />
              )}
              {hasDocuments ? "Your knowledge connected" : "Auto routing"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-[10px] text-muted-foreground/60 sm:block">
              Shift + Enter for a new line
            </span>
            <Button
              size="icon"
              disabled={!value.trim() || isLoading}
              aria-label={isLoading ? "Generating answer" : "Send message"}
              onClick={send}
              className="size-9 rounded-xl"
            >
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <ArrowUp className="size-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
      <p className="mt-3 text-center text-[10px] text-muted-foreground/65">
        A little perspective, powered by AI. Verify important information.
      </p>
    </div>
  );
}
