"use client";

import { useState } from "react";
import { MessageSquare, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export interface ConversationData {
  id: string;
  title: string;
  createdAt: number;
  timestampStr?: string;
}
interface ConversationItemProps {
  chat: ConversationData;
  isActive: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onRename?: (id: string, title: string) => void;
  isCollapsed?: boolean;
}

export function ConversationItem({
  chat,
  isActive,
  onSelect,
  onDelete,
  onRename,
  isCollapsed,
}: ConversationItemProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(chat.title);
  if (isCollapsed) return null;
  return (
    <>
      <div
        className={cn(
          "group flex min-w-0 items-center gap-1 rounded-lg p-1 transition-colors",
          isActive
            ? "bg-accent text-foreground"
            : "text-muted-foreground hover:bg-accent/50",
        )}
      >
        <button
          onClick={() => onSelect(chat.id)}
          aria-current={isActive ? "page" : undefined}
          className="flex min-w-0 flex-1 items-center gap-2.5 rounded-md px-2 py-2 text-left text-xs"
        >
          <MessageSquare
            className={cn("size-3.5 shrink-0", isActive && "text-primary")}
          />
          <span className="truncate">{chat.title}</span>
        </button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={`Actions for ${chat.title}`}
              className="shrink-0 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100 data-[state=open]:opacity-100"
            >
              <MoreHorizontal className="size-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-44">
            {onRename && (
              <DropdownMenuItem
                onClick={() => {
                  setTitle(chat.title);
                  setEditing(true);
                }}
              >
                <Pencil className="mr-2 size-3.5" />
                Rename
              </DropdownMenuItem>
            )}
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={() => onDelete(chat.id)}
            >
              <Trash2 className="mr-2 size-3.5" />
              Delete conversation
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <Dialog open={editing} onOpenChange={setEditing}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename conversation</DialogTitle>
            <DialogDescription>
              Give this conversation a name that’s easy to find.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (title.trim()) {
                onRename?.(chat.id, title.trim());
                setEditing(false);
              }
            }}
            className="space-y-5"
          >
            <div className="space-y-2">
              <label
                htmlFor={`title-${chat.id}`}
                className="text-xs text-muted-foreground"
              >
                Conversation name
              </label>
              <Input
                id={`title-${chat.id}`}
                autoFocus
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                maxLength={120}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditing(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!title.trim()}>
                Save name
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
