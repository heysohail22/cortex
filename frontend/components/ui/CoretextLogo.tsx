"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface CoretextLogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  glow?: boolean;
}

export function CoretextLogoMark({
  className = "w-4 h-4",
}: {
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Top-Left Orbital Arc */}
      <path
        d="M12 3C7.03 3 3 7.03 3 12C3 14.15 3.76 16.12 5.03 17.67L7.86 14.84C7.31 13.99 7 13.03 7 12C7 9.24 9.24 7 12 7C13.03 7 13.99 7.31 14.84 7.86L17.67 5.03C16.12 3.76 14.15 3 12 3Z"
        fill="currentColor"
        fillOpacity="0.95"
      />
      {/* Bottom-Right Orbital Arc */}
      <path
        d="M12 21C16.97 21 21 16.97 21 12C21 9.85 20.24 7.88 18.97 6.33L16.14 9.16C16.69 10.01 17 10.97 17 12C17 14.76 14.76 17 12 17C10.97 17 10.01 16.69 9.16 16.14L6.33 18.97C7.88 20.24 9.85 21 12 21Z"
        fill="currentColor"
        fillOpacity="0.8"
      />
      {/* Central Knowledge Nucleus */}
      <circle cx="12" cy="12" r="2.5" fill="currentColor" />
    </svg>
  );
}

export function CoretextLogo({
  size = "md",
  className,
  glow = false,
}: CoretextLogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8 rounded-xl",
    md: "w-8 h-8 rounded-xl",
    lg: "w-14 h-14 rounded-2xl",
  };

  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-4.5 h-4.5",
    lg: "w-7 h-7",
  };

  return (
    <div
      className={cn(
        "bg-primary/15 border border-primary/20 flex items-center justify-center text-primary shrink-0 transition-transform select-none",
        sizeClasses[size],
        glow && "shadow-md shadow-[#b5a0ee]/35 ring-1 ring-white/15",
        className,
      )}
    >
      <CoretextLogoMark className={iconSizes[size]} />
    </div>
  );
}
