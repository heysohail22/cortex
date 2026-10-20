"use client";
import { useState } from "react";
import { BookOpen, MessageSquarePlus, Sparkles } from "lucide-react";
import { AppLogo } from "./AppLogo";
import { ConversationList } from "./ConversationList";
import { ConversationSearch } from "./ConversationSearch";
import { UserProfile } from "./UserProfile";
import { ConversationData } from "./ConversationItem";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useMediaQuery } from "@/hooks/use-media-query";
import { cn } from "@/lib/utils";
interface SidebarProps {
  conversations: ConversationData[];
  activeChatId: string | null;
  userId: string;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  onRenameChat?: (id: string, title: string) => void;
  isOpen: boolean;
  onClose: () => void;
  onOpenLibrary: () => void;
  libraryOpen: boolean;
  docCount: number;
}
export function Sidebar({
  conversations,
  activeChatId,
  userId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
  isOpen,
  onClose,
  onOpenLibrary,
  libraryOpen,
  docCount,
}: SidebarProps) {
  const [search, setSearch] = useState("");
  const desktop = useMediaQuery("(min-width: 768px)");
  const navigate = (action: () => void) => {
    action();
    if (!desktop) onClose();
  };
  const content = (
    <>
      <AppLogo />
      <div className="space-y-1 px-4 pb-5">
        <Button
          onClick={() => navigate(onNewChat)}
          className="mb-2 h-10 w-full justify-start gap-2.5"
        >
          <MessageSquarePlus className="size-4" />
          New conversation
        </Button>
        <Button
          variant="ghost"
          aria-haspopup="dialog"
          onClick={() => navigate(onOpenLibrary)}
          className={cn(
            "w-full justify-start gap-2.5 text-xs",
            libraryOpen && "bg-accent text-foreground",
          )}
        >
          <BookOpen className="size-4" />
          Knowledge base
          <span className="ml-auto rounded-md bg-background/60 px-1.5 py-0.5 text-[10px] text-muted-foreground">
            {docCount}
          </span>
        </Button>
      </div>
      <ConversationSearch value={search} onChange={setSearch} />
      <ConversationList
        conversations={conversations.filter((chat) =>
          chat.title.toLowerCase().includes(search.toLowerCase()),
        )}
        activeChatId={libraryOpen ? null : activeChatId}
        onSelectChat={(id) => navigate(() => onSelectChat(id))}
        onDeleteChat={onDeleteChat}
        onRenameChat={onRenameChat}
        searching={Boolean(search)}
      />
      <div className="mx-4 mb-4 rounded-xl border border-primary/10 bg-primary/5 p-3.5">
        <p className="flex items-center gap-2 text-xs font-medium text-primary">
          <Sparkles className="size-3.5" />A space for your next idea
        </p>
        <p className="mt-2 text-[11px] leading-5 text-muted-foreground">
          Bring your knowledge. Find a new perspective.
        </p>
      </div>
      <UserProfile userId={userId} />
    </>
  );
  return desktop ? (
    <aside
      aria-label="Workspace navigation"
      inert={!isOpen}
      className={cn(
        "flex h-full shrink-0 flex-col overflow-hidden border-r border-border bg-sidebar transition-[width] duration-200",
        isOpen ? "w-[272px]" : "w-0 border-r-0",
      )}
    >
      <div className="flex h-full w-[272px] flex-col">{content}</div>
    </aside>
  ) : (
    <Sheet
      open={isOpen}
      onOpenChange={(value) => {
        if (!value) onClose();
      }}
    >
      <SheetContent
        side="left"
        className="w-[min(304px,88vw)] gap-0 bg-sidebar p-0"
      >
        <SheetTitle className="sr-only">Cortex workspace</SheetTitle>
        <SheetDescription className="sr-only">
          Navigate conversations, documents, and settings.
        </SheetDescription>
        {content}
      </SheetContent>
    </Sheet>
  );
}
