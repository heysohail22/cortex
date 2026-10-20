"use client";
import { useState } from "react";
import { ArrowUpRight, FileText, Globe2, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { safeWebUrl } from "@/lib/urls";
interface Props {
  citations?: string[];
  sourceType?: "rag" | "llm" | "web_search" | "hybrid" | "guardrail";
}
export function Sources({ citations = [] }: Props) {
  const [expanded, setExpanded] = useState(false);
  if (citations.length === 0) return null;
  return (
    <section aria-label="Answer sources" className="mt-6">
      <h3 className="section-label mb-3">SOURCES · {citations.length}</h3>
      <div className="grid gap-2 sm:grid-cols-2">
        {(expanded ? citations : citations.slice(0, 4)).map(
          (citation, index) => {
            const url = safeWebUrl(citation);
            return url ? (
              <a
                key={`${citation}-${index}`}
                href={url.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex min-w-0 items-center gap-3 rounded-xl border border-border bg-card p-3 transition-colors hover:border-primary/40"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-amber-400/10 text-amber-300">
                  <Globe2 className="size-3.5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs text-foreground">
                    {url.hostname.replace(/^www\./, "")}
                  </span>
                  <span className="mt-1 block text-[10px] text-muted-foreground">
                    Web source · {index + 1}
                  </span>
                </span>
                <ArrowUpRight className="size-3.5 shrink-0 text-muted-foreground group-hover:text-primary" />
              </a>
            ) : (
              <div
                key={`${citation}-${index}`}
                className="flex min-w-0 items-center gap-3 rounded-xl border border-border bg-card p-3"
                title={citation}
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <FileText className="size-3.5" />
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-xs">{citation}</span>
                  <span className="mt-1 block text-[10px] text-muted-foreground">
                    Document source · {index + 1}
                  </span>
                </span>
              </div>
            );
          },
        )}
      </div>
      {citations.length > 4 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="mt-2 gap-1.5 text-[11px]"
        >
          {expanded
            ? "Show fewer"
            : `Show ${citations.length - 4} more sources`}
          <ChevronDown
            className={`size-3 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        </Button>
      )}
    </section>
  );
}
