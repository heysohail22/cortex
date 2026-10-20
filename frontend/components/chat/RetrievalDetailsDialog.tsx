"use client";
import {
  FileText,
  Globe2,
  Route,
  ShieldCheck,
  ArrowUpRight,
  Search,
  Sparkles,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { verificationLabel, VerificationStatus } from "@/lib/verification";
import { safeWebUrl } from "@/lib/urls";
interface Props {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  question?: string;
  source?: string;
  chunksCount?: number;
  chunks?: { source: string; text: string; similarity?: number }[];
  webResults?: { title: string; url: string; content: string }[];
  evaluationResult?: string;
  evaluationReason?: string;
  isGrounded?: boolean | null;
  verificationStatus?: VerificationStatus;
  groundednessReason?: string;
  route?: string;
  transformedQuery?: string;
}
export function RetrievalDetailsDialog({
  open,
  onOpenChange,
  question,
  source,
  chunks = [],
  webResults = [],
  verificationStatus,
  evaluationResult,
  evaluationReason,
  groundednessReason,
  route,
  transformedQuery,
}: Props) {
  const label =
    source === "rag"
      ? "Your documents"
      : source === "hybrid"
        ? "Documents + web"
        : source === "web_search"
          ? "Web search"
          : source === "guardrail"
            ? "Response policy"
            : "Model knowledge";
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[88dvh] max-w-2xl flex-col gap-0 overflow-hidden p-0">
        <DialogHeader className="shrink-0 border-b border-border px-6 py-5">
          <span className="section-label">A CLOSER LOOK</span>
          <DialogTitle className="flex items-center gap-2">
            <Search className="size-4 text-primary" />
            Behind this answer
          </DialogTitle>
          <DialogDescription>
            Explore the sources and checks used for this response.
          </DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="overview" className="flex min-h-0 flex-1 flex-col">
          <div className="shrink-0 px-6 pt-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="documents">
                Documents{" "}
                <span className="ml-1.5 text-[10px] opacity-60">
                  {chunks.length}
                </span>
              </TabsTrigger>
              <TabsTrigger value="web">
                Web{" "}
                <span className="ml-1.5 text-[10px] opacity-60">
                  {webResults.length}
                </span>
              </TabsTrigger>
            </TabsList>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-6">
            <TabsContent value="overview" className="m-0 space-y-5">
              <div className="rounded-xl border border-border bg-muted/30 p-4">
                <p className="section-label">YOUR QUESTION</p>
                <p className="mt-3 text-sm leading-7">
                  {question ||
                    "The original question was not saved with this answer."}
                </p>
                {transformedQuery && transformedQuery !== question && (
                  <div className="mt-4 border-t border-border pt-3">
                    <p className="section-label">SEARCHED AS</p>
                    <p className="mt-2 text-xs leading-6 text-muted-foreground">
                      {transformedQuery}
                    </p>
                  </div>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-border p-4">
                  <Route className="mb-3 size-4 text-primary" />
                  <p className="text-[11px] text-muted-foreground">
                    Answer based on
                  </p>
                  <p className="mt-2 text-sm">{label}</p>
                </div>
                <div className="rounded-xl border border-border p-4">
                  <ShieldCheck
                    className={`mb-3 size-4 ${verificationStatus === "SUPPORTED" ? "text-emerald-300" : "text-muted-foreground"}`}
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Source verification
                  </p>
                  <p className="mt-2 text-sm">
                    {verificationLabel(verificationStatus)}
                  </p>
                </div>
              </div>
              {(evaluationResult || evaluationReason || groundednessReason) && (
                <section className="space-y-3 rounded-xl border border-border p-4">
                  <h3 className="text-xs font-medium">What the checks found</h3>
                  {evaluationResult && (
                    <Badge variant="secondary">{evaluationResult}</Badge>
                  )}
                  {evaluationReason && (
                    <p className="text-xs leading-6 text-muted-foreground">
                      {evaluationReason}
                    </p>
                  )}
                  {groundednessReason && (
                    <p className="text-xs leading-6 text-muted-foreground">
                      {groundednessReason}
                    </p>
                  )}
                </section>
              )}
              {route && (
                <p className="break-all text-[11px] text-muted-foreground">
                  Response route: <span className="font-mono">{route}</span>
                </p>
              )}
              <p className="text-[11px] leading-6 text-muted-foreground">
                A source check measures support for an answer. It does not
                establish that a source is accurate or current.
              </p>
            </TabsContent>
            <TabsContent value="documents" className="m-0 space-y-3">
              {chunks.length ? (
                chunks.map((chunk, index) => (
                  <article
                    key={index}
                    className="overflow-hidden rounded-xl border border-border"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-muted/40 p-4">
                      <h3 className="flex min-w-0 items-center gap-2 text-xs">
                        <FileText className="size-3.5 shrink-0 text-primary" />
                        <span className="break-all">{chunk.source}</span>
                      </h3>
                      <span className="text-[10px] text-muted-foreground">
                        Passage {index + 1}
                        {typeof chunk.similarity === "number"
                          ? ` · ${Math.round(chunk.similarity * 100)}% match`
                          : ""}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap break-words p-4 text-xs leading-7 text-muted-foreground">
                      {chunk.text}
                    </p>
                  </article>
                ))
              ) : (
                <Empty
                  icon={FileText}
                  title="No document passages"
                  detail="This answer has no saved document excerpts."
                />
              )}
            </TabsContent>
            <TabsContent value="web" className="m-0 space-y-3">
              {webResults.length ? (
                webResults.map((result, index) => {
                  const url = safeWebUrl(result.url);
                  return (
                    <article
                      key={index}
                      className="rounded-xl border border-border p-4"
                    >
                      <h3 className="text-sm font-medium">
                        {result.title || `Source ${index + 1}`}
                      </h3>
                      {url && (
                        <a
                          href={url.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-2 inline-flex items-center gap-1 text-[11px] text-primary"
                        >
                          {url.hostname}
                          <ArrowUpRight className="size-3" />
                        </a>
                      )}
                      <p className="mt-3 whitespace-pre-wrap break-words text-xs leading-7 text-muted-foreground">
                        {result.content}
                      </p>
                    </article>
                  );
                })
              ) : (
                <Empty
                  icon={Globe2}
                  title="No web sources"
                  detail="This answer has no saved web search results."
                />
              )}
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
function Empty({
  icon: Icon = Sparkles,
  title,
  detail,
}: {
  icon?: typeof Sparkles;
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-border py-12 text-center">
      <Icon className="mx-auto mb-4 size-7 text-muted-foreground/50" />
      <p className="text-sm">{title}</p>
      <p className="mt-2 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}
