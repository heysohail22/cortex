"use client";
import { useEffect, useState } from "react";
import { Check, Fingerprint, Monitor, UserRound } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { readProfile, DEFAULT_PROFILE, PROFILE_EVENT } from "@/lib/profile";
import { toast } from "sonner";
export function SettingsDialog({
  open,
  onOpenChange,
  userId,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
}) {
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [tab, setTab] = useState("profile");
  useEffect(() => {
    if (open) queueMicrotask(() => setProfile(readProfile()));
  }, [open]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl p-0 overflow-hidden">
        <DialogHeader className="border-b border-border px-6 py-5">
          <span className="section-label">YOUR WORKSPACE</span>
          <DialogTitle>Make yourself at home</DialogTitle>
          <DialogDescription>
            Personal details and workspace preferences.
          </DialogDescription>
        </DialogHeader>
        <Tabs value={tab} onValueChange={setTab} className="px-6">
          <TabsList className="mb-5">
            <TabsTrigger value="profile" className="gap-2">
              <UserRound className="size-3.5" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="workspace" className="gap-2">
              <Monitor className="size-3.5" />
              Workspace
            </TabsTrigger>
          </TabsList>
          <TabsContent value="profile">
            <form
              id="profile-form"
              className="space-y-5 pb-6"
              onSubmit={(event) => {
                event.preventDefault();
                try {
                  localStorage.setItem(
                    "cortex_profile",
                    JSON.stringify({
                      name: profile.name.trim(),
                      email: profile.email.trim(),
                    }),
                  );
                  window.dispatchEvent(new Event(PROFILE_EVENT));
                  toast.success("Profile saved on this device");
                  onOpenChange(false);
                } catch {
                  toast.error("Your browser could not save these preferences");
                }
              }}
            >
              <div className="flex items-center gap-3 rounded-xl bg-muted/50 p-4">
                <div className="flex size-11 items-center justify-center rounded-xl bg-primary/15 text-lg text-primary">
                  {profile.name.charAt(0).toUpperCase() || "C"}
                </div>
                <div>
                  <p className="text-sm font-medium">Your personal space</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    This profile is saved in your browser.
                  </p>
                </div>
              </div>
              <div className="space-y-2">
                <label htmlFor="profile-name" className="text-xs font-medium">
                  Display name
                </label>
                <Input
                  id="profile-name"
                  value={profile.name}
                  onChange={(event) =>
                    setProfile({ ...profile, name: event.target.value })
                  }
                  required
                  maxLength={80}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="profile-email" className="text-xs font-medium">
                  Email{" "}
                  <span className="text-muted-foreground">(optional)</span>
                </label>
                <Input
                  id="profile-email"
                  type="email"
                  placeholder="you@example.com"
                  value={profile.email}
                  onChange={(event) =>
                    setProfile({ ...profile, email: event.target.value })
                  }
                />
              </div>
            </form>
          </TabsContent>
          <TabsContent value="workspace" className="space-y-4 pb-6">
            <div className="rounded-xl border border-border p-4">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <Monitor className="size-4 text-muted-foreground" />
                  Appearance
                </span>
                <span className="flex items-center gap-1.5 text-xs text-primary">
                  <Check className="size-3" />
                  Midnight
                </span>
              </div>
              <p className="mt-2 text-xs leading-6 text-muted-foreground">
                A quiet, dark workspace designed for focused reading.
              </p>
            </div>
            <div className="rounded-xl border border-border p-4">
              <p className="flex items-center gap-2 text-sm">
                <Fingerprint className="size-4 text-muted-foreground" />
                Workspace identity
              </p>
              <p className="mt-2 break-all font-mono text-xs text-muted-foreground">
                {userId}
              </p>
              <p className="mt-3 text-xs leading-6 text-muted-foreground">
                This browser identity connects your uploaded documents to your
                conversations.
              </p>
            </div>
          </TabsContent>
        </Tabs>
        <DialogFooter className="border-t border-border bg-muted/20 px-6 py-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {tab === "profile" && (
            <Button
              type="submit"
              form="profile-form"
              disabled={!profile.name.trim()}
            >
              Save profile
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
