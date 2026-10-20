"use client";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
export function ConversationSearch({
  value,
  onChange,
  isCollapsed,
}: {
  value: string;
  onChange: (value: string) => void;
  isCollapsed?: boolean;
}) {
  if (isCollapsed) return null;
  return (
    <div className="relative mx-4 mb-5">
      <Search className="pointer-events-none absolute left-3 top-3 size-3.5 text-muted-foreground" />
      <Input
        aria-label="Search conversations"
        placeholder="Search conversations"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 border-border/70 bg-background/40 pl-9 text-xs"
      />
    </div>
  );
}
