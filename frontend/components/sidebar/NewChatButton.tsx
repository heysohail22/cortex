"use client";

import React from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface NewChatButtonProps {
  onClick: () => void;
  isCollapsed?: boolean;
}

export function NewChatButton({
  onClick,
  isCollapsed = false,
}: NewChatButtonProps) {
  if (isCollapsed) {
    return (
      <Button
        onClick={onClick}
        variant="accent"
        size="icon"
        className="w-9 h-9 rounded-xl mx-auto my-2 shrink-0"
        title="New Chat"
      >
        <Plus className="w-4 h-4" />
      </Button>
    );
  }

  return (
    <div className="px-3 pt-3 pb-2">
      <Button
        onClick={onClick}
        className="w-full h-10 rounded-lg bg-white/8 hover:bg-white/12 text-zinc-100 font-medium text-xs border border-white/10 flex items-center justify-start gap-2 px-3.5 transition-colors"
      >
        <Plus className="w-4 h-4" />
        <span>New Chat</span>
      </Button>
    </div>
  );
}
