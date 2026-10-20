"use client";

import Link from "next/link";
import { useEffect } from "react";
import {
  ArrowUpRight,
  Loader2,
  MessageSquareDashed,
  RotateCcw,
} from "lucide-react";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { MessageList } from "@/components/chat/MessageList";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { Button } from "@/components/ui/button";
import { useWorkspace } from "./Workspace";

export function ChatPage() {
  const {
    activeChatId,
    activeSession,
    hydrated,
    historyStatus,
    input,
    setInput,
    isLoading,
    documents,
    sidebarOpen,
    toggleSidebar,
    openDocuments,
    openDocumentUpload,
    sendMessage,
    stopResponse,
    retryHistory,
  } = useWorkspace();
  useEffect(() => {
    document.title = activeSession
      ? `${activeSession.title} — Cortex`
      : "New conversation — Cortex";
  }, [activeSession?.title, activeSession]);
  const unavailable = Boolean(activeChatId && !activeSession);
  const restoring = !hydrated || (unavailable && historyStatus === "loading");
  return (
    <>
      <ChatHeader
        title={
          activeSession?.title ||
          (activeChatId ? "Conversation" : "New conversation")
        }
        docCount={documents.length}
        onOpenDocuments={openDocuments}
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
      />
      {activeChatId && (restoring || unavailable) ? (
        <div className="flex min-h-0 flex-1 flex-col items-center justify-center px-6 text-center">
          {restoring ? (
            <>
              <Loader2 className="mb-5 size-7 animate-spin text-primary" />
              <p role="status" className="text-sm text-muted-foreground">
                Opening your conversation…
              </p>
            </>
          ) : (
            <>
              <span className="mb-5 flex size-14 items-center justify-center rounded-2xl border border-border bg-card">
                <MessageSquareDashed className="size-6 text-primary" />
              </span>
              <h1 className="text-xl font-medium tracking-tight">
                {historyStatus === "offline"
                  ? "This conversation couldn’t be loaded"
                  : "Conversation not found"}
              </h1>
              <p className="mt-3 max-w-sm text-sm leading-7 text-muted-foreground">
                {historyStatus === "offline"
                  ? "Your saved history is unavailable right now. Check your connection and try again."
                  : "This link doesn’t match a conversation in your saved history. It may have been deleted or created in another workspace."}
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <Button
                  variant="outline"
                  onClick={retryHistory}
                  className="gap-2"
                >
                  <RotateCcw className="size-3.5" />
                  Try again
                </Button>
                <Button asChild>
                  <Link href="/" className="gap-2">
                    Start a conversation
                    <ArrowUpRight className="size-3.5" />
                  </Link>
                </Button>
              </div>
            </>
          )}
        </div>
      ) : (
        <>
          <MessageList
            messages={activeSession?.messages || []}
            onSelectPrompt={(prompt) => void sendMessage(prompt)}
            onOpenDocuments={openDocumentUpload}
            onWebSearchFallback={(question) =>
              void sendMessage(`Search the web for ${question}`)
            }
          />
          <ChatComposer
            key={activeChatId || "new"}
            value={input}
            onChange={setInput}
            onSend={sendMessage}
            isLoading={isLoading}
            onStop={stopResponse}
            disabled={!hydrated}
            onOpenDocuments={openDocumentUpload}
          />
        </>
      )}
    </>
  );
}
