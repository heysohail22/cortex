"use client";

import { verificationLabel, type VerificationStatus } from "@/lib/verification";

import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
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

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="relative my-3 rounded-xl bg-[#080b11] border border-white/8 overflow-hidden font-mono text-xs text-[#a5b4fc]">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#121824] border-b border-white/6 text-zinc-400">
        <span className="text-[10px]">Code</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 text-[10px] text-zinc-400 hover:text-white"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <pre className="p-3 overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="bg-[#121824] px-1.5 py-0.5 rounded text-[13px] text-[#9d93ff] font-mono border border-white/6"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

function formatMarkdown(text: string): React.ReactNode {
  const cleanedText = text.trim();

  const lines = cleanedText.split("\n");
  const elements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeLines: string[] = [];

  const flushCode = (key: string) => {
    elements.push(<CodeBlock key={key} code={codeLines.join("\n")} />);
    codeLines = [];
  };

  lines.forEach((line, i) => {
    if (line.startsWith("```")) {
      if (inCodeBlock) {
        flushCode(`code-${i}`);
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      return;
    }

    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={i} className="text-sm font-semibold text-white mt-3 mb-1">
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith("## ")) {
      elements.push(
        <h2 key={i} className="text-base font-bold text-white mt-3.5 mb-1.5">
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith("# ")) {
      elements.push(
        <h1 key={i} className="text-lg font-bold text-white mt-4 mb-2">
          {line.slice(2)}
        </h1>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const match = line.match(/^(\d+\.)\s(.*)/);
      if (match) {
        elements.push(
          <div key={i} className="flex items-start gap-2 ml-1 my-1 leading-relaxed">
            <span className="font-semibold text-[#9d93ff] shrink-0 font-mono text-xs mt-0.5">
              {match[1]}
            </span>
            <div className="text-zinc-200">{renderInline(match[2])}</div>
          </div>
        );
      }
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <li key={i} className="ml-5 my-0.5 leading-relaxed text-zinc-200 list-disc">
          {renderInline(line.slice(2))}
        </li>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(
        <p key={i} className="leading-[1.7] text-zinc-200 mb-1">
          {renderInline(line)}
        </p>
      );
    }
  });

  if (inCodeBlock && codeLines.length > 0) flushCode("code-final");

  return <>{elements}</>;
}

export function AssistantMessage({
  message,
  onWebSearchFallback,
}: AssistantMessageProps) {
  return (
    <div className="flex items-start gap-3.5 mb-6 animate-fade-in group">
      {/* Brand Logo Avatar */}
      <CoretextLogo size="sm" className="mt-0.5" />

      {/* Main Message Content */}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-zinc-200 leading-relaxed max-w-[760px]">
          {message.isLoading ? (
            <div className="flex items-center gap-2.5 py-2 text-zinc-400">
              <div className="spinner" />
              <span className="text-xs">
                Searching knowledge base & synthesizing response...
              </span>
            </div>
          ) : (
            <>
              {formatMarkdown(message.content)}

              <p className="mt-2 text-[11px] text-zinc-400" title="Source support does not guarantee that a source is correct or current.">
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
    </div>
  );
}
