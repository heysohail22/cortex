"use client";
import { MessageSquare } from "lucide-react";
import { ConversationItem, ConversationData } from "./ConversationItem";
import { ScrollArea } from "@/components/ui/scroll-area";
interface Props {
  conversations: ConversationData[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onDeleteChat: (id: string) => void;
  onRenameChat?: (id: string, title: string) => void;
  isCollapsed?: boolean;
  searching?: boolean;
}
export function ConversationList({
  conversations,
  activeChatId,
  onSelectChat,
  onDeleteChat,
  onRenameChat,
  isCollapsed,
  searching,
}: Props) {
  if (isCollapsed) return null;
  const today = new Date().setHours(0, 0, 0, 0);
  const groups = [
    {
      label: "Today",
      chats: conversations.filter((chat) => chat.createdAt >= today),
    },
    {
      label: "Previous conversations",
      chats: conversations.filter((chat) => chat.createdAt < today),
    },
  ];
  return (
    <ScrollArea className="min-h-0 flex-1 px-3">
      <div className="pb-4">
        {conversations.length === 0 ? (
          <div className="mx-1 rounded-xl border border-dashed border-border p-5 text-center">
            <MessageSquare className="mx-auto mb-3 size-5 text-muted-foreground/60" />
            <p className="text-xs text-muted-foreground">
              {searching
                ? "No matching conversations"
                : "Your next idea starts here"}
            </p>
            <p className="mt-1.5 text-[11px] leading-5 text-muted-foreground/60">
              {searching
                ? "Try a different search."
                : "Start a chat and find it here later."}
            </p>
          </div>
        ) : (
          groups.map(
            ({ label, chats }) =>
              chats.length > 0 && (
                <div key={label} className="mb-5">
                  <h2 className="mb-2 px-3 text-[10px] font-medium uppercase tracking-widest text-muted-foreground/70">
                    {label}
                  </h2>
                  <div className="space-y-0.5">
                    {chats.map((chat) => (
                      <ConversationItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === activeChatId}
                        onSelect={onSelectChat}
                        onDelete={onDeleteChat}
                        onRename={onRenameChat}
                      />
                    ))}
                  </div>
                </div>
              ),
          )
        )}
      </div>
    </ScrollArea>
  );
}
