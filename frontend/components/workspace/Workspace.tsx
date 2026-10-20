"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
} from "react";
import { useParams, usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { DocumentUploadDialog } from "@/components/documents/DocumentUploadDialog";
import { DocumentsDrawer } from "@/components/documents/DocumentsDrawer";
import type { DocumentInfo } from "@/components/documents/DocumentPreview";
import type { MessageData } from "@/components/chat/AssistantMessage";
import {
  conversationHref,
  generateSafeId,
  loadSavedSessions,
  mergeSavedSessions,
  saveSessions,
  type ChatSession,
} from "@/lib/chat-sessions";
import { toast } from "sonner";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface DocMeta {
  chunks: number;
  sizeMb: string;
  uploadDate: string;
}
interface WorkspaceValue {
  userId: string;
  activeChatId: string | null;
  activeSession: ChatSession | undefined;
  hydrated: boolean;
  historyStatus: "loading" | "ready" | "offline";
  input: string;
  setInput: (value: string) => void;
  isLoading: boolean;
  documents: DocumentInfo[];
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  openDocuments: () => void;
  openDocumentUpload: () => void;
  sendMessage: (text?: string) => Promise<void>;
  stopResponse: () => void;
  retryHistory: () => void;
  onDocumentUploaded: (
    filename: string,
    chunks: number,
    sizeMb: string,
  ) => void;
  onDocumentDeleted: (filename: string) => void;
  useDocumentInChat: (filename: string) => void;
}
const WorkspaceContext = createContext<WorkspaceValue | null>(null);
export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context)
    throw new Error("Workspace pages must be inside the workspace layout");
  return context;
}
function documentCache(userId: string): Record<string, DocMeta> {
  try {
    return JSON.parse(localStorage.getItem(`coretext_docs_${userId}`) || "{}");
  } catch {
    return {};
  }
}
function updateDocumentCache(userId: string, filename: string, meta?: DocMeta) {
  try {
    const cache = documentCache(userId);
    if (meta) cache[filename] = meta;
    else delete cache[filename];
    localStorage.setItem(`coretext_docs_${userId}`, JSON.stringify(cache));
  } catch {
    /* Browser storage is optional. */
  }
}

export function Workspace({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams<{ chatId?: string }>();
  // The route is the source of truth, including when navigating back or forward.
  const activeChatId = params.chatId || null;
  const [userId, setUserId] = useState("ssr");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [historyStatus, setHistoryStatus] =
    useState<WorkspaceValue["historyStatus"]>("loading");
  const [historyAttempt, setHistoryAttempt] = useState(0);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [documentsOpen, setDocumentsOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [pendingIds, setPendingIds] = useState<string[]>([]);
  const requests = useRef(new Map<string, AbortController>());
  const deletedIds = useRef(new Set<string>());
  const draftSessionId = useRef<string | null>(null);
  const activeSession = sessions.find((session) => session.id === activeChatId);
  const input = drafts[activeChatId || "new"] || "";

  useEffect(() => {
    let user: string;
    try {
      user = localStorage.getItem("coretext_user_id") || generateSafeId();
      localStorage.setItem("coretext_user_id", user);
    } catch {
      user = generateSafeId();
    }
    const saved = loadSavedSessions();
    queueMicrotask(() => {
      setUserId(user);
      setSessions(saved);
      setHydrated(true);
      setSidebarOpen(window.matchMedia("(min-width: 768px)").matches);
    });
  }, []);

  useEffect(() => {
    if (hydrated) saveSessions(sessions);
  }, [sessions, hydrated]);
  useEffect(() => {
    draftSessionId.current = null;
  }, [pathname]);

  useEffect(() => {
    if (!hydrated) return;
    const controller = new AbortController();
    queueMicrotask(() => setHistoryStatus("loading"));
    fetch(`${API_URL}/api/sessions`, {
      signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]),
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("History unavailable");
        return response.json();
      })
      .then((data) => {
        if (!Array.isArray(data.sessions)) throw new Error("Invalid history");
        setSessions((previous) =>
          mergeSavedSessions(previous, data.sessions, deletedIds.current),
        );
        setHistoryStatus("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setHistoryStatus("offline");
      });
    return () => controller.abort();
  }, [hydrated, historyAttempt]);

  useEffect(() => {
    if (userId === "ssr") return;
    const controller = new AbortController();
    fetch(`${API_URL}/api/documents?session_id=${encodeURIComponent(userId)}`, {
      signal: controller.signal,
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!data || !Array.isArray(data.documents)) return;
        const cache = documentCache(userId);
        setDocuments(
          data.documents.map((filename: string) => ({
            filename,
            chunks:
              data.items?.find(
                (item: { filename: string; chunks: number }) =>
                  item.filename === filename,
              )?.chunks ??
              cache[filename]?.chunks ??
              0,
            sizeMb: cache[filename]?.sizeMb || "Size unavailable",
            uploadDate: cache[filename]?.uploadDate || "Date unavailable",
          })),
        );
      })
      .catch(() => {
        /* Keep the current library if the backend is unavailable. */
      });
    return () => controller.abort();
  }, [userId]);

  useEffect(() => {
    const pending = requests.current;
    return () => {
      for (const request of pending.values()) request.abort();
    };
  }, []);

  const createNewChat = useCallback(() => {
    draftSessionId.current = null;
    setDrafts((previous) => ({ ...previous, new: "" }));
    router.push("/");
  }, [router]);

  const deleteChat = useCallback(
    async (id: string) => {
      deletedIds.current.add(id);
      requests.current.get(id)?.abort();
      setSessions((previous) =>
        previous.filter((session) => session.id !== id),
      );
      setDrafts((previous) => {
        const updated = { ...previous };
        delete updated[id];
        return updated;
      });
      if (activeChatId === id) router.replace("/");
      try {
        const response = await fetch(
          `${API_URL}/api/sessions/${encodeURIComponent(id)}`,
          { method: "DELETE" },
        );
        if (!response.ok) throw new Error();
        toast.success("Conversation deleted");
      } catch {
        toast.error("Removed on this device. Could not sync the deletion.");
      }
    },
    [activeChatId, router],
  );

  const renameChat = useCallback((id: string, title: string) => {
    setSessions((previous) =>
      previous.map((session) =>
        session.id === id ? { ...session, title } : session,
      ),
    );
    toast.success("Conversation renamed");
  }, []);

  const sendMessage = useCallback(
    async (customInput?: string) => {
      const question = (
        typeof customInput === "string" ? customInput : input
      ).trim();
      if (
        !question ||
        question.length > 4000 ||
        !hydrated ||
        (activeChatId && !activeSession)
      )
        return;
      const targetId =
        activeChatId || draftSessionId.current || generateSafeId();
      if (requests.current.has(targetId)) return;
      const controller = new AbortController();
      requests.current.set(targetId, controller);
      setPendingIds((previous) => [...previous, targetId]);
      if (!activeChatId) draftSessionId.current = targetId;
      const timestamp = new Date().toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
      });
      const userMessage: MessageData = {
        id: generateSafeId(),
        role: "user",
        content: question,
        timestamp,
      };
      const loadingMessage: MessageData = {
        id: generateSafeId(),
        role: "assistant",
        content: "",
        isLoading: true,
        timestamp,
      };
      const title =
        question.length > 40 ? `${question.slice(0, 40)}…` : question;
      setSessions((previous) => {
        const existing = previous.find((session) => session.id === targetId);
        if (!existing)
          return [
            {
              id: targetId,
              title,
              createdAt: Date.now(),
              messages: [userMessage, loadingMessage],
            },
            ...previous,
          ];
        return previous.map((session) =>
          session.id === targetId
            ? {
                ...session,
                title: session.messages.length === 0 ? title : session.title,
                messages: [...session.messages, userMessage, loadingMessage],
              }
            : session,
        );
      });
      setDrafts((previous) => ({ ...previous, [activeChatId || "new"]: "" }));
      if (!activeChatId) router.push(conversationHref(targetId));
      const finish = (message: MessageData) =>
        setSessions((previous) =>
          previous.map((session) =>
            session.id === targetId
              ? {
                  ...session,
                  messages: session.messages.map((existing) =>
                    existing.id === loadingMessage.id ? message : existing,
                  ),
                }
              : session,
          ),
        );
      try {
        const response = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            message: question,
            session_id: targetId,
            user_id: userId,
          }),
        });
        if (!response.ok) throw new Error("Response unavailable");
        const data = await response.json();
        finish({
          id: loadingMessage.id,
          role: "assistant",
          content: data.answer || "No answer was returned. Please try again.",
          source: data.source || "llm",
          citations: data.citations || [],
          suggest_web_search: data.suggest_web_search || false,
          question,
          timestamp,
          chunksCount: Array.isArray(data.chunks) ? data.chunks.length : 0,
          chunks: data.chunks || [],
          webResults: data.web_results || [],
          evaluationResult: data.evaluation_result,
          evaluationReason: data.evaluation_reason,
          isGrounded: data.is_grounded,
          verificationStatus: data.verification_status,
          groundednessReason: data.groundedness_reason,
          route: data.route,
          transformedQuery: data.transformed_query,
        });
      } catch {
        finish({
          id: loadingMessage.id,
          role: "assistant",
          content: controller.signal.aborted
            ? "Response stopped."
            : "I couldn’t reach the assistant. Please try sending your question again in a moment.",
          source: "llm",
          verificationStatus: "SKIPPED",
          timestamp,
          question,
        });
      } finally {
        requests.current.delete(targetId);
        setPendingIds((previous) => previous.filter((id) => id !== targetId));
      }
    },
    [input, hydrated, activeChatId, activeSession, router, userId],
  );

  const onDocumentUploaded = useCallback(
    (filename: string, chunks: number, sizeMb: string) => {
      const uploadDate = new Date().toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
      setDocuments((previous) => [
        { filename, chunks, sizeMb, uploadDate },
        ...previous.filter((document) => document.filename !== filename),
      ]);
      updateDocumentCache(userId, filename, { chunks, sizeMb, uploadDate });
    },
    [userId],
  );
  const onDocumentDeleted = useCallback(
    (filename: string) => {
      setDocuments((previous) =>
        previous.filter((document) => document.filename !== filename),
      );
      updateDocumentCache(userId, filename);
    },
    [userId],
  );
  const useDocumentInChat = useCallback(
    (filename: string) => {
      setDrafts((previous) => ({
        ...previous,
        [activeChatId || "new"]:
          `Summarize and explain the key findings in ${filename}`,
      }));
      setDocumentsOpen(false);
      router.push(activeChatId ? conversationHref(activeChatId) : "/");
    },
    [activeChatId, router],
  );

  const value: WorkspaceValue = {
    userId,
    activeChatId,
    activeSession,
    hydrated,
    historyStatus,
    input,
    setInput: (text) =>
      setDrafts((previous) => ({ ...previous, [activeChatId || "new"]: text })),
    isLoading: Boolean(activeChatId && pendingIds.includes(activeChatId)),
    documents,
    sidebarOpen,
    toggleSidebar: () => setSidebarOpen((previous) => !previous),
    openDocuments: () => setDocumentsOpen(true),
    openDocumentUpload: () => setUploadOpen(true),
    sendMessage,
    stopResponse: () => {
      if (activeChatId) requests.current.get(activeChatId)?.abort();
    },
    retryHistory: () => setHistoryAttempt((previous) => previous + 1),
    onDocumentUploaded,
    onDocumentDeleted,
    useDocumentInChat,
  };
  return (
    <WorkspaceContext value={value}>
      <div className="flex h-dvh w-full overflow-hidden bg-background text-foreground antialiased">
        <Sidebar
          conversations={sessions}
          activeChatId={activeChatId}
          userId={userId}
          onSelectChat={(id) => router.push(conversationHref(id))}
          onNewChat={createNewChat}
          onDeleteChat={deleteChat}
          onRenameChat={renameChat}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onOpenLibrary={() => router.push("/library")}
          libraryOpen={pathname === "/library"}
          docCount={documents.length}
        />
        <main className="relative flex h-full min-w-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>
        <DocumentUploadDialog
          open={uploadOpen}
          onOpenChange={setUploadOpen}
          sessionId={userId}
          onUploaded={onDocumentUploaded}
          documentCount={documents.length}
          onViewLibrary={() => router.push("/library")}
        />
        <DocumentsDrawer
          open={documentsOpen}
          onOpenChange={setDocumentsOpen}
          documents={documents}
          sessionId={userId}
          onDocumentUploaded={onDocumentUploaded}
          onDocumentDeleted={onDocumentDeleted}
          onUseInChat={useDocumentInChat}
        />
      </div>
    </WorkspaceContext>
  );
}
