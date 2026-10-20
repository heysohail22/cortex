"use client";
import { useEffect, useState } from "react";
import { ChevronsUpDown, Settings2 } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { SettingsDialog } from "./SettingsDialog";
import { DEFAULT_PROFILE, readProfile, PROFILE_EVENT } from "@/lib/profile";
export function UserProfile({
  userId,
  isCollapsed,
}: {
  userId: string;
  isCollapsed?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  useEffect(() => {
    const update = () => setProfile(readProfile());
    queueMicrotask(update);
    window.addEventListener(PROFILE_EVENT, update);
    return () => window.removeEventListener(PROFILE_EVENT, update);
  }, []);
  if (isCollapsed) return null;
  return (
    <>
      <div className="shrink-0 border-t border-border p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-3 rounded-xl p-2 text-left transition-colors hover:bg-accent">
              <Avatar className="size-9 rounded-xl">
                <AvatarFallback className="rounded-xl bg-primary/15 text-xs font-semibold text-primary">
                  {profile.name.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-xs font-medium">
                  {profile.name}
                </span>
                <span className="mt-1 block truncate text-[10px] text-muted-foreground">
                  {profile.email || "Personal workspace"}
                </span>
              </span>
              <ChevronsUpDown className="size-3.5 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-60">
            <div className="px-3 py-2">
              <p className="text-xs font-medium">Your workspace</p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                Preferences are saved on this device.
              </p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setOpen(true)}>
              <Settings2 className="mr-2 size-4" />
              Settings & profile
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <SettingsDialog open={open} onOpenChange={setOpen} userId={userId} />
    </>
  );
}
