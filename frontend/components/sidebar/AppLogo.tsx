"use client";

import React from "react";
import { CoretextLogo } from "@/components/ui/CoretextLogo";

interface AppLogoProps {
  isCollapsed?: boolean;
}

export function AppLogo({ isCollapsed = false }: AppLogoProps) {
  return (
    <div className="flex items-center px-4 py-3.5 h-20 shrink-0">
      <div className="flex items-center gap-3">
        <CoretextLogo size="md" />
        {!isCollapsed && (
          <div className="flex flex-col">
            <span className="text-[15px] font-semibold tracking-tight text-foreground">
              Cortex
            </span>
            <span className="text-[10px] font-medium text-muted-foreground">
              Your knowledge, connected
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
