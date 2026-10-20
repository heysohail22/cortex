"use client";
export function UserMessage({
  content,
  timestamp,
}: {
  content: string;
  timestamp?: string;
}) {
  return (
    <article
      aria-label="Your message"
      className="mb-8 ml-auto flex max-w-[92%] flex-col items-end gap-2 animate-fade-in sm:max-w-[80%]"
    >
      <div className="rounded-2xl rounded-br-md border border-primary/10 bg-primary/[0.08] px-5 py-3.5 text-sm leading-7 text-foreground whitespace-pre-wrap break-words">
        {content}
      </div>
      <span className="pr-1 text-[10px] text-muted-foreground">
        You{timestamp ? ` · ${timestamp}` : ""}
      </span>
    </article>
  );
}
