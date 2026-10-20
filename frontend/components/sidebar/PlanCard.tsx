"use client";

import React from "react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

interface PlanCardProps {
  usedMessages?: number;
  maxMessages?: number;
  onUpgrade?: () => void;
  isCollapsed?: boolean;
}

export function PlanCard({
  usedMessages = 2400,
  maxMessages = 10000,
  onUpgrade,
  isCollapsed = false,
}: PlanCardProps) {
  if (isCollapsed) return null;

  const percentage = Math.min(
    100,
    Math.round((usedMessages / maxMessages) * 100),
  );

  return (
    <div className="mx-3 my-2 p-3.5 rounded-xl bg-[#202124] border border-white/8 flex flex-col gap-2.5">
      <div className="flex items-start justify-between">
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-white">Free Plan</span>
          <span className="text-[11px] text-zinc-400">
            Upgrade for more limits
          </span>
        </div>
        <Button
          size="sm"
          onClick={onUpgrade}
          className="h-7 px-3 text-[11px] rounded-lg bg-[#b5a0ee] hover:bg-[#c7b5f5] text-white font-medium shadow-sm"
        >
          Upgrade
        </Button>
      </div>

      <div className="flex flex-col gap-1.5 pt-0.5">
        <Progress value={percentage} className="h-1.5 bg-black/40" />
        <div className="flex justify-between items-center text-[10px] text-zinc-400 font-mono">
          <span>
            {(usedMessages / 1000).toFixed(1)}k /{" "}
            {(maxMessages / 1000).toFixed(0)}k messages used
          </span>
          <span>{percentage}%</span>
        </div>
      </div>
    </div>
  );
}
