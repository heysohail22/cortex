import type { MessageData } from "@/components/chat/AssistantMessage";

export interface ChatSession {
  id: string;
  title: string;
  messages: MessageData[];
  createdAt: number;
  timestampStr?: string;
}

export interface SavedSession {
  id: string;
  title?: string;
  created_at?: string;
  messages?: {
    id?: string;
    role: string;
    content?: string;
    timestamp?: string;
  }[];
}

export function conversationHref(id: string): string {
  return `/c/${encodeURIComponent(id)}`;
}

export function generateSafeId(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `id-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`
  );
}

export function loadSavedSessions(): ChatSession[] {
  try {
    const stored: unknown = JSON.parse(
      localStorage.getItem("coretext_sessions") || "[]",
    );
    if (!Array.isArray(stored)) return [];
    return stored
      .filter(
        (session): session is ChatSession =>
          session &&
          typeof session.id === "string" &&
          typeof session.title === "string" &&
          typeof session.createdAt === "number" &&
          Array.isArray(session.messages) &&
          !session.id.startsWith("demo-rag-"),
      )
      .map((session) => ({
        ...session,
        // A request cannot survive a full browser reload. Do not leave a permanent spinner.
        messages: session.messages
          .filter(
            (message) =>
              message &&
              typeof message.content === "string" &&
              (message.role === "user" || message.role === "assistant"),
          )
          .map((message) =>
            message.isLoading ? { ...message, isLoading: false } : message,
          ),
      }));
  } catch {
    return [];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  try {
    localStorage.setItem("coretext_sessions", JSON.stringify(sessions));
  } catch {
    /* Browser storage may be disabled or full. */
  }
}

export function mergeSavedSessions(
  local: ChatSession[],
  remote: SavedSession[],
  deletedIds: ReadonlySet<string> = new Set(),
): ChatSession[] {
  const merged = [...local];
  for (const saved of remote) {
    if (typeof saved.id !== "string" || deletedIds.has(saved.id)) continue;
    const date = saved.created_at ? new Date(saved.created_at).getTime() : NaN;
    const session: ChatSession = {
      id: saved.id,
      title: saved.title || "Conversation",
      createdAt: Number.isFinite(date) ? date : Date.now(),
      messages: (Array.isArray(saved.messages) ? saved.messages : [])
        .filter(
          (message) => message.role === "user" || message.role === "assistant",
        )
        .map((message) => ({
          id: message.id || generateSafeId(),
          role: message.role as "user" | "assistant",
          content: message.content || "",
          timestamp: message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })
            : undefined,
        })),
    };
    const index = merged.findIndex((item) => item.id === session.id);
    if (index === -1) merged.push(session);
    else {
      const existing = merged[index];
      const interrupted = existing.messages.some(
        (message) =>
          message.role === "assistant" &&
          !message.content &&
          !message.isLoading,
      );
      // Never overwrite a response currently being generated in this tab.
      if (
        !existing.messages.some((message) => message.isLoading) &&
        (existing.messages.length === 0 || interrupted) &&
        session.messages.length > 0
      ) {
        merged[index] = {
          ...session,
          title: existing.title === "New Chat" ? session.title : existing.title,
        };
      }
    }
  }
  return merged
    .filter((session) => !deletedIds.has(session.id))
    .sort((a, b) => b.createdAt - a.createdAt);
}
