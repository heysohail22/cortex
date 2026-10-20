"use client";

import { verificationLabel, type VerificationStatus } from "@/lib/verification";

import React from "react";
import { Loader2, ShieldCheck, CircleHelp } from "lucide-react";
import { MarkdownContent } from "./MarkdownContent";
import { Sources } from "./Sources";
import { MessageActions } from "./MessageActions";
import { CoretextLogo } from "@/components/ui/CoretextLogo";

export interface ChunkData {
  source: string;
  text: string;
  similarity?: number;
}

export interface WebResultData {
  title: string;
  url: string;
  content: string;
}

export interface MessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: "rag" | "llm" | "web_search" | "hybrid" | "guardrail";
  citations?: string[];
  isLoading?: boolean;
  suggest_web_search?: boolean;
  question?: string;
  timestamp?: string;
  chunksCount?: number;
  chunks?: ChunkData[];
  webResults?: WebResultData[];
  evaluationResult?: string;
  evaluationReason?: string;
  isGrounded?: boolean | null;
  verificationStatus?: VerificationStatus;
  groundednessReason?: string;
  route?: string;
  transformedQuery?: string;
}

interface AssistantMessageProps {
  message: MessageData;
  onWebSearchFallback?: (question: string) => void;
}

export function AssistantMessage({
  message,
  onWebSearchFallback,
}: AssistantMessageProps) {
  return (
    <article
      aria-label="Cortex answer"
      className="mb-10 flex items-start gap-3 animate-fade-in sm:gap-4"
    >
      {/* Brand Logo Avatar */}
      <CoretextLogo size="sm" className="mt-1 hidden sm:flex" />

      {/* Main Message Content */}
      <div className="flex-1 min-w-0">
        <div className="mb-4 flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground">Cortex</span>
          <span className="rounded-md border border-border bg-muted/50 px-1.5 py-0.5 text-[9px] text-muted-foreground">
            {message.source === "rag"
              ? "DOCUMENTS"
              : message.source === "web_search"
                ? "WEB"
                : message.source === "hybrid"
                  ? "DOCS + WEB"
                  : message.source === "guardrail"
                    ? "NOTICE"
                    : "ASSISTANT"}
          </span>
          {message.timestamp && (
            <span className="ml-auto text-[10px] text-muted-foreground/70">
              {message.timestamp}
            </span>
          )}
        </div>
        <div className="text-sm text-zinc-200 leading-relaxed max-w-[760px]">
          {message.isLoading ? (
            <div
              role="status"
              className="flex items-center gap-3 rounded-xl border border-border bg-card p-5 text-muted-foreground"
            >
              <Loader2 className="size-4 animate-spin text-primary" />
              <span className="text-xs">Finding a little clarity…</span>
            </div>
          ) : (
            <>
              <MarkdownContent content={message.content} />

              <p
                className="mt-5 flex items-center gap-1.5 text-[10px] text-muted-foreground"
                title="Source support does not guarantee that a source is correct or current."
              >
                {message.verificationStatus === "SUPPORTED" ? (
                  <ShieldCheck className="size-3 text-emerald-300" />
                ) : (
                  <CircleHelp className="size-3" />
                )}
                {verificationLabel(message.verificationStatus)}
              </p>

              {/* Sources */}
              {message.citations && message.citations.length > 0 && (
                <Sources
                  citations={message.citations}
                  sourceType={message.source}
                />
              )}

              {/* Actions & Transparency Footer */}
              <MessageActions
                content={message.content}
                timestamp={message.timestamp}
                source={message.source}
                chunksCount={message.chunks?.length || message.chunksCount || 0}
                chunks={message.chunks}
                webResults={message.webResults}
                evaluationResult={message.evaluationResult}
                evaluationReason={message.evaluationReason}
                isGrounded={message.isGrounded}
                verificationStatus={message.verificationStatus}
                groundednessReason={message.groundednessReason}
                route={message.route}
                transformedQuery={message.transformedQuery}
                question={message.question}
                suggestWebSearch={message.suggest_web_search}
                onWebSearchFallback={onWebSearchFallback}
              />
            </>
          )}
        </div>
      </div>
    </article>
  );
}
