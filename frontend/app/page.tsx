"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { MessageList } from "@/components/chat/MessageList";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { DocumentsDrawer } from "@/components/documents/DocumentsDrawer";
import { MessageData } from "@/components/chat/AssistantMessage";
import { ConversationData } from "@/components/sidebar/ConversationItem";
import { DocumentInfo } from "@/components/documents/DocumentPreview";
import { toast } from "sonner";

export interface ChatSession {
  id: string;
  title: string;
  messages: MessageData[];
  createdAt: number;
  timestampStr?: string;
}

interface DocMeta {
  chunks: number;
  sizeMb: string;
  uploadDate: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function generateSafeId(): string {
  if (typeof window !== "undefined" && window.crypto && typeof window.crypto.randomUUID === "function") {
    try {
      return window.crypto.randomUUID();
    } catch {
      // fallback
    }
  }
  return "id-" + Date.now().toString(36) + "-" + Math.random().toString(36).substring(2, 9);
}

function getOrCreateUserId(): string {
  if (typeof window === "undefined") return "ssr";
  const key = "coretext_user_id";
  try {
    let id = localStorage.getItem(key);
    if (!id) {
      id = generateSafeId();
      localStorage.setItem(key, id);
    }
    return id;
  } catch {
    return generateSafeId();
  }
}

function getDocMetaCache(userId: string): Record<string, DocMeta> {
  if (typeof window === "undefined" || !userId || userId === "ssr") return {};
  try {
    const raw = localStorage.getItem(`coretext_docs_${userId}`);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveDocMeta(userId: string, filename: string, meta: DocMeta) {
  if (typeof window === "undefined" || !userId || userId === "ssr") return;
  try {
    const cache = getDocMetaCache(userId);
    cache[filename] = meta;
    localStorage.setItem(`coretext_docs_${userId}`, JSON.stringify(cache));
  } catch {
    // ignore
  }
}

function removeDocMeta(userId: string, filename: string) {
  if (typeof window === "undefined" || !userId || userId === "ssr") return;
  try {
    const cache = getDocMetaCache(userId);
    delete cache[filename];
    localStorage.setItem(`coretext_docs_${userId}`, JSON.stringify(cache));
  } catch {
    // ignore
  }
}

function loadSavedSessions(): ChatSession[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem("coretext_sessions");
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        // Filter out any mock/demo sessions from earlier versions
        return parsed.filter(
          (s) =>
            s &&
            typeof s === "object" &&
            typeof s.id === "string" &&
            !s.id.startsWith("demo-rag-") &&
            s.id !== "demo-rag-1"
        );
      }
    }
    return [];
  } catch {
    return [];
  }
}

function saveSessionsToStorage(sessions: ChatSession[]) {
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem("coretext_sessions", JSON.stringify(sessions));
    } catch {
      // ignore
    }
  }
}

export default function Home() {
  const [userId, setUserId] = useState<string>("ssr");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const activeChatIdRef = useRef<string | null>(null);

  useEffect(() => {
    activeChatIdRef.current = activeChatId;
  }, [activeChatId]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [documentsDrawerOpen, setDocumentsDrawerOpen] = useState(false);

  // Initialize persistent state after hydration using microtask to avoid cascading renders
  useEffect(() => {
    const id = getOrCreateUserId();
    const loadedSessions = loadSavedSessions();
    saveSessionsToStorage(loadedSessions);

    queueMicrotask(() => {
      setUserId(id);
      setSessions(loadedSessions);
      if (loadedSessions.length > 0) {
        setActiveChatId(loadedSessions[0].id);
      } else {
        setActiveChatId(null);
      }
    });
  }, []);

  // Sync documents from backend
  useEffect(() => {
    if (userId === "ssr") return;
    fetch(`${API_URL}/api/documents?session_id=${encodeURIComponent(userId)}`)
      .then((r) => {
        if (!r.ok) return null;
        return r.json();
      })
      .then((data) => {
        if (data && Array.isArray(data.documents)) {
          const metaCache = getDocMetaCache(userId);
          const backendDocs: DocumentInfo[] = data.documents.map((name: string) => {
            const cached = metaCache[name];
            const itemFromBackend = data.items?.find(
              (it: { filename: string; chunks: number }) => it.filename === name
            );
            return {
              filename: name,
              chunks: itemFromBackend?.chunks || cached?.chunks || 0,
              sizeMb: cached?.sizeMb || "Uploaded",
              uploadDate: cached?.uploadDate || "Uploaded",
            };
          });
          setDocuments(backendDocs);
        } else {
          setDocuments([]);
        }
      })
      .catch(() => {
        // If backend fetch fails, do not invent mock documents
      });
  }, [userId]);

  // Sync saved chat sessions from Supabase
  useEffect(() => {
    fetch(`${API_URL}/api/sessions`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && Array.isArray(data.sessions) && data.sessions.length > 0) {
          setSessions((prev) => {
            const backendSessions: ChatSession[] = data.sessions.map(
              (bs: {
                id: string;
                title: string;
                messages: Array<{ id: string; role: string; content: string; timestamp?: string }>;
                created_at: string;
              }) => {
                const parsedTime = bs.created_at ? new Date(bs.created_at).getTime() : Date.now();
                return {
                  id: bs.id,
                  title: bs.title || "Chat",
                  messages: (bs.messages || []).map((m) => ({
                    id: m.id || generateSafeId(),
                    role: m.role as "user" | "assistant",
                    content: m.content || "",
                    timestamp: m.timestamp
                      ? new Date(m.timestamp).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
                      : undefined,
                  })),
                  createdAt: isNaN(parsedTime) ? Date.now() : parsedTime,
                };
              }
            );

            const merged = [...prev];
            for (const bs of backendSessions) {
              const idx = merged.findIndex((s) => s.id === bs.id);
              if (idx === -1) {
                merged.push(bs);
              } else if (merged[idx].messages.length === 0 && bs.messages.length > 0) {
                merged[idx] = {
                  ...merged[idx],
                  title: bs.title,
                  messages: bs.messages,
                };
              }
            }

            merged.sort((a, b) => b.createdAt - a.createdAt);
            saveSessionsToStorage(merged);

            if (!activeChatIdRef.current && merged.length > 0) {
              setActiveChatId(merged[0].id);
            }
            return merged;
          });
        }
      })
      .catch(() => {
        // Fallback to local storage if backend is unavailable
      });
  }, []);

  // Active session and messages
  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeChatId),
    [sessions, activeChatId]
  );
  const messages = useMemo(
    () => (activeSession ? activeSession.messages : []),
    [activeSession]
  );

  const createNewChat = useCallback(() => {
    const active = sessions.find((s) => s.id === activeChatIdRef.current);
    if (active && active.messages.length === 0) {
      return;
    }
    const emptyExisting = sessions.find((s) => s.messages.length === 0);
    if (emptyExisting) {
      setActiveChatId(emptyExisting.id);
      return;
    }
    const newId = generateSafeId();
    const newSession: ChatSession = {
      id: newId,
      title: "New Chat",
      messages: [],
      createdAt: Date.now(),
    };
    setSessions((prev) => {
      const updated = [newSession, ...prev];
      saveSessionsToStorage(updated);
      return updated;
    });
    setActiveChatId(newId);
  }, [sessions]);

  const deleteChat = useCallback(async (id: string) => {
    setSessions((prev) => {
      const updated = prev.filter((s) => s.id !== id);
      saveSessionsToStorage(updated);
      return updated;
    });
    if (activeChatIdRef.current === id) {
      setSessions((prev) => {
        const remaining = prev.filter((s) => s.id !== id);
        setActiveChatId(remaining.length > 0 ? remaining[0].id : null);
        return remaining;
      });
    }

    try {
      const res = await fetch(`${API_URL}/api/sessions/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      if (res.ok) {
        toast.success("Chat deleted");
      } else {
        toast.error("Failed to delete chat from database");
      }
    } catch {
      toast.error("Network error deleting chat from database");
    }
  }, []);

  const renameChat = useCallback((id: string, newTitle: string) => {
    setSessions((prev) => {
      const updated = prev.map((s) => (s.id === id ? { ...s, title: newTitle } : s));
      saveSessionsToStorage(updated);
      return updated;
    });
    toast.success("Chat renamed");
  }, []);

  const handleSend = useCallback(
    async (customInput?: string) => {
      const question = (typeof customInput === "string" ? customInput : input).trim();
      if (!question || isLoading) return;

      const currentTime = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

      const userMsg: MessageData = {
        id: generateSafeId(),
        role: "user",
        content: question,
        timestamp: currentTime,
      };

      const loadingMsg: MessageData = {
        id: generateSafeId(),
        role: "assistant",
        content: "",
        isLoading: true,
        timestamp: currentTime,
      };

      let targetSessionId = activeChatIdRef.current;
      const titleText = question.length > 32 ? question.slice(0, 32) + "..." : question;

      if (!targetSessionId) {
        targetSessionId = generateSafeId();
        const newSession: ChatSession = {
          id: targetSessionId,
          title: titleText,
          messages: [userMsg, loadingMsg],
          createdAt: Date.now(),
        };
        setActiveChatId(targetSessionId);
        activeChatIdRef.current = targetSessionId;
        setSessions((prev) => {
          const updated = [newSession, ...prev];
          saveSessionsToStorage(updated);
          return updated;
        });
      } else {
        setSessions((prev) => {
          const activeIdx = prev.findIndex((s) => s.id === targetSessionId);
          if (activeIdx === -1) {
            const newSession: ChatSession = {
              id: targetSessionId!,
              title: titleText,
              messages: [userMsg, loadingMsg],
              createdAt: Date.now(),
            };
            const updated = [newSession, ...prev];
            saveSessionsToStorage(updated);
            return updated;
          }

          const session = prev[activeIdx];
          const updatedMsgs = [...session.messages, userMsg, loadingMsg];
          const updatedSession: ChatSession = {
            ...session,
            messages: updatedMsgs,
            title: session.messages.length === 0 ? titleText : session.title,
          };
          const updated = [...prev];
          updated[activeIdx] = updatedSession;
          saveSessionsToStorage(updated);
          return updated;
        });
      }

      setInput("");
      setIsLoading(true);

      try {
        const res = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: question,
            session_id: targetSessionId,
            user_id: userId,
          }),
        });

        const data = await res.json();

        const assistantMsg: MessageData = {
          id: loadingMsg.id,
          role: "assistant",
          content: data.answer || "Sorry, no answer could be synthesized.",
          source: data.source || "llm",
          citations: data.citations || [],
          suggest_web_search: data.suggest_web_search || false,
          question: question,
          timestamp: currentTime,
          chunksCount: Array.isArray(data.chunks)
            ? data.chunks.length
            : data.source === "rag"
            ? 5
            : 0,
          chunks: data.chunks || [],
          webResults: data.web_results || [],
          evaluationResult: data.evaluation_result,
          evaluationReason: data.evaluation_reason,
          isGrounded: data.is_grounded,
          groundednessReason: data.groundedness_reason,
          route: data.route,
          transformedQuery: data.transformed_query,
        };

        setSessions((prev) => {
          const activeIdx = prev.findIndex((s) => s.id === targetSessionId);
          if (activeIdx === -1) return prev;
          const session = prev[activeIdx];
          const updatedMsgs = session.messages.map((m) =>
            m.id === loadingMsg.id ? assistantMsg : m
          );
          const updated = [...prev];
          updated[activeIdx] = { ...session, messages: updatedMsgs };
          saveSessionsToStorage(updated);
          return updated;
        });
      } catch {
        setSessions((prev) => {
          const activeIdx = prev.findIndex((s) => s.id === targetSessionId);
          if (activeIdx === -1) return prev;
          const session = prev[activeIdx];
          const updatedMsgs = session.messages.map((m) =>
            m.id === loadingMsg.id
              ? {
                  ...m,
                  isLoading: false,
                  content:
                    `⚠️ Failed to connect to the backend service at ${API_URL}. Please check that the FastAPI service is running.`,
                  source: "llm" as const,

                }
              : m
          );
          const updated = [...prev];
          updated[activeIdx] = { ...session, messages: updatedMsgs };
          saveSessionsToStorage(updated);
          return updated;
        });
      } finally {
        setIsLoading(false);
      }
    },
    [input, isLoading, userId]
  );

  const handleWebSearchFallback = useCallback(
    (question: string) => {
      handleSend(`Search the web for ${question}`);
    },
    [handleSend]
  );

  const handleDocumentUploaded = useCallback(
    (filename: string, chunks: number, sizeMb: string) => {
      const uploadDate = new Date().toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
      const newDoc: DocumentInfo = {
        filename,
        chunks: chunks || 0,
        sizeMb: sizeMb || "1.0 MB",
        uploadDate,
      };
      setDocuments((prev) => {
        const filtered = prev.filter((d) => d.filename !== filename);
        return [newDoc, ...filtered];
      });
      saveDocMeta(userId, filename, { chunks, sizeMb, uploadDate });
    },
    [userId]
  );

  const handleDocumentDeleted = useCallback(
    (filename: string) => {
      setDocuments((prev) => prev.filter((d) => d.filename !== filename));
      removeDocMeta(userId, filename);
    },
    [userId]
  );

  const handleUseInChat = useCallback(
    (filename: string) => {
      setInput(`Summarize and explain the key findings in ${filename}`);
    },
    []
  );

  // Map sessions to ConversationData
  const conversations: ConversationData[] = useMemo(
    () =>
      sessions.map((s) => ({
        id: s.id,
        title: s.title,
        createdAt: s.createdAt,
        timestampStr: s.timestampStr,
      })),
    [sessions]
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#080b11] text-zinc-100 antialiased">
      {/* ── Left Sidebar ──────────────────────────────────────────────────────── */}
      <Sidebar
        conversations={conversations}
        activeChatId={activeChatId}
        userId={userId}
        onSelectChat={setActiveChatId}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        isOpen={sidebarOpen}
      />

      {/* ── Main Chat Area ───────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <ChatHeader
          title={activeSession?.title || "New Chat"}
          docCount={documents.length}
          onOpenDocuments={() => setDocumentsDrawerOpen(true)}
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          sidebarOpen={sidebarOpen}
        />

        <MessageList
          messages={messages}
          onSelectPrompt={(prompt) => handleSend(prompt)}
          onOpenDocuments={() => setDocumentsDrawerOpen(true)}
          onWebSearchFallback={handleWebSearchFallback}
        />

        <ChatComposer
          value={input}
          onChange={setInput}
          onSend={handleSend}
          isLoading={isLoading}
          onOpenDocuments={() => setDocumentsDrawerOpen(true)}
          hasDocuments={documents.length > 0}
        />
      </main>

      {/* ── Right Documents Drawer (Sheet) ───────────────────────────────────── */}
      <DocumentsDrawer
        open={documentsDrawerOpen}
        onOpenChange={setDocumentsDrawerOpen}
        documents={documents}
        sessionId={userId}
        onDocumentUploaded={handleDocumentUploaded}
        onDocumentDeleted={handleDocumentDeleted}
        onUseInChat={handleUseInChat}
      />
    </div>
  );
}
