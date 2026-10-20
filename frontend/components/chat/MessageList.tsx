"use client";

import React, { useRef, useEffect } from "react";
import { UserMessage } from "./UserMessage";
import { AssistantMessage, MessageData } from "./AssistantMessage";
import { EmptyState } from "./EmptyState";

interface MessageListProps {
  messages: MessageData[];
  onSelectPrompt: (prompt: string) => void;
  onOpenDocuments: () => void;
  onWebSearchFallback?: (question: string) => void;
}

export function MessageList({
  messages,
  onSelectPrompt,
  onOpenDocuments,
  onWebSearchFallback,
}: MessageListProps) {
  const scrollEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 min-h-0 overflow-y-auto px-5 sm:px-8">
        <EmptyState
          onSelectPrompt={onSelectPrompt}
          onOpenDocuments={onOpenDocuments}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 overflow-y-auto px-5 sm:px-8 py-6">
      <div className="max-w-[816px] mx-auto flex flex-col justify-start">
        {messages.map((msg) => {
          if (msg.role === "user") {
            return (
              <UserMessage
                key={msg.id}
                content={msg.content}
                timestamp={msg.timestamp}
              />
            );
          }
          return (
            <AssistantMessage
              key={msg.id}
              message={msg}
              onWebSearchFallback={onWebSearchFallback}
            />
          );
        })}
        <div ref={scrollEndRef} className="h-4" />
      </div>
    </div>
  );
}
