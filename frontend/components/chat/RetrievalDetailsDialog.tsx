"use client";

import { verificationLabel, type VerificationStatus } from "@/lib/verification";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database, CheckCircle2, ShieldCheck, Cpu } from "lucide-react";

interface ChunkItem {
  source: string;
  text: string;
  similarity?: number;
}

interface WebResultItem {
  title: string;
  url: string;
  content: string;
}

interface RetrievalDetailsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question?: string;
  source?: "rag" | "llm" | "web_search" | "hybrid" | "guardrail";
  chunksCount?: number;
  chunks?: ChunkItem[];
  webResults?: WebResultItem[];
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
  question = "What is RAG and how does it work?",
  source = "rag",
  chunksCount = 0,
  chunks = [],
  webResults = [],
  evaluationResult,
  verificationStatus,
  transformedQuery,
}: RetrievalDetailsDialogProps) {
  const isRag = source === "rag" || source === "hybrid";
  const isWeb = source === "web_search";
  const isLlm = source === "llm";
  const isGuard = source === "guardrail";

  const totalChunks = chunks.length > 0 ? chunks.length : chunksCount;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl max-h-[85vh] flex flex-col bg-[#0d111a] border-white/10 text-zinc-100 p-0 overflow-hidden">
        <DialogHeader className="px-5 pt-5 pb-3 border-b border-white/8 shrink-0">
          <DialogTitle className="text-base font-semibold flex items-center gap-2">
            <Database className="w-4 h-4 text-[#6d5dfc]" />
            Corrective RAG Pipeline Details
          </DialogTitle>
          <DialogDescription className="text-xs text-zinc-400">
            Transparency breakdown of query routing, retrieved context excerpts, and groundedness validation.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-4 text-xs">
          {/* Query */}
          <div className="p-3 rounded-xl bg-[#121824] border border-white/6 flex flex-col gap-1.5">
            <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">
              Original Query
            </span>
            <span className="text-zinc-200 italic font-medium leading-relaxed">
              &ldquo;{question}&rdquo;
            </span>
            {transformedQuery && transformedQuery !== question && (
              <div className="pt-1.5 mt-1 border-t border-white/6 flex flex-col gap-0.5">
                <span className="text-[10px] text-[#9d93ff] uppercase tracking-wider font-semibold">
                  Optimized Search Query
                </span>
                <span className="text-zinc-300 font-mono text-[11px]">
                  {transformedQuery}
                </span>
              </div>
            )}
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-xl bg-[#121824] border border-white/6 flex flex-col gap-1">
              <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">
                Retrieval Route
              </span>
              <Badge
                variant={
                  isRag
                    ? "rag"
                    : isWeb
                    ? "web"
                    : isGuard
                    ? "destructive"
                    : "llm"
                }
                className="w-fit mt-0.5"
              >
                {isRag
                  ? source === "hybrid"
                    ? "Hybrid (Docs + Web)"
                    : "Document RAG"
                  : isWeb
                  ? "Web Search"
                  : isGuard
                  ? "Safety Guardrail"
                  : "Direct Knowledge"}
              </Badge>
            </div>

            <div className="p-3 rounded-xl bg-[#121824] border border-white/6 flex flex-col gap-1">
              <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">
                Retrieved Context
              </span>
              <span className="font-semibold text-white mt-0.5">
                {isRag
                  ? `${totalChunks} Document Chunk${totalChunks === 1 ? "" : "s"}`
                  : isWeb
                  ? `${webResults.length || 5} Web Sources`
                  : isGuard
                  ? "Blocked Prompt"
                  : "Direct LLM (No Retrieval)"}
              </span>
            </div>
          </div>

          {/* Corrective checks / Pipeline Metadata */}
          <div className="p-3.5 rounded-xl bg-[#121824] border border-white/6 flex flex-col gap-2.5">
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
              {isRag
                ? "Document Verification & Grounding"
                : isWeb
                ? "Web Search Execution"
                : "Execution Mode"}
            </span>

            {isRag && (
              <>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    Retrieval Evaluator:
                  </span>
                  <span className="text-emerald-400 font-medium font-mono text-[11px]">
                    {evaluationResult || "Not assessed"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className={`w-3.5 h-3.5 ${verificationStatus === "SUPPORTED" ? "text-emerald-400" : "text-zinc-400"}`} />
                    Groundedness Judge:
                  </span>
                  <span className={`font-medium font-mono text-[11px] ${verificationStatus === "SUPPORTED" ? "text-emerald-400" : "text-zinc-400"}`}>
                    {verificationLabel(verificationStatus)}
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-[#6d5dfc]" />
                    Embeddings Model:
                  </span>
                  <span className="font-mono text-zinc-400 text-[11px]">
                    Gemini MRL (768d)
                  </span>
                </div>
              </>
            )}

            {isWeb && (
              <>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                    Search Provider:
                  </span>
                  <span className="text-amber-400 font-medium font-mono text-[11px]">
                    Tavily Live Web API
                  </span>
                </div>
                <div className="flex justify-between items-center text-zinc-300">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className={`w-3.5 h-3.5 ${verificationStatus === "SUPPORTED" ? "text-emerald-400" : "text-zinc-400"}`} />
                    Context Mode:
                  </span>
                  <span className="text-zinc-300 font-mono text-[11px]">
                    Real-time Web Grounding
                  </span>
                </div>
              </>
            )}

            {isLlm && (
              <div className="flex justify-between items-center text-zinc-300">
                <span className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-[#6d5dfc]" />
                  Generation Path:
                </span>
                <span className="text-[#9d93ff] font-medium font-mono text-[11px]">
                  Direct LLM Reasoning (Retriever Bypassed)
                </span>
              </div>
            )}
          </div>

          {/* ── Retrieved Document Chunks (Where the response was generated from) ── */}
          {chunks && chunks.length > 0 && (
            <div className="flex flex-col gap-2 pt-1">
              <span className="text-[11px] font-semibold text-[#9d93ff] uppercase tracking-wider flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#9d93ff]" />
                Retrieved Document Chunks ({chunks.length})
              </span>

              <div className="flex flex-col gap-2.5">
                {chunks.map((chunk, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-[#080b11] border border-white/8 flex flex-col gap-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white">
                        Chunk #{idx + 1} &bull; {chunk.source}
                      </span>
                      {chunk.similarity !== undefined && chunk.similarity !== null && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-mono">
                          Score: {(chunk.similarity * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <p className="text-zinc-300 text-[11px] leading-relaxed whitespace-pre-wrap font-mono bg-[#121824]/60 p-2.5 rounded-lg border border-white/4">
                      {chunk.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Web Search Snippets ── */}
          {webResults && webResults.length > 0 && (
            <div className="flex flex-col gap-2 pt-1">
              <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-amber-400" />
                Web Search Results ({webResults.length})
              </span>

              <div className="flex flex-col gap-2.5">
                {webResults.map((web, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-[#080b11] border border-white/8 flex flex-col gap-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white truncate max-w-[320px]">
                        {web.title || `Source #${idx + 1}`}
                      </span>
                      {web.url && (
                        <a
                          href={web.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] text-amber-400 hover:underline truncate max-w-[160px]"
                        >
                          {new URL(web.url).hostname.replace("www.", "")}
                        </a>
                      )}
                    </div>
                    <p className="text-zinc-300 text-[11px] leading-relaxed whitespace-pre-wrap font-sans bg-[#121824]/60 p-2.5 rounded-lg border border-white/4">
                      {web.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="px-5 py-3 border-t border-white/8 bg-[#080b11]/80 shrink-0">
          <Button
            variant="outline"
            type="button"
            onClick={() => onOpenChange(false)}
            className="text-xs h-8"
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
