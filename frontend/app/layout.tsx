import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Cortex — Corrective RAG Assistant",
  description:
    "Ask questions about your knowledge base with transparent Corrective RAG, real-time web search, and AI reasoning.",
  keywords: [
    "RAG",
    "Corrective RAG",
    "Cortex",
    "AI",
    "Agentic RAG",
    "Knowledge Base",
  ],
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable}`}
      suppressHydrationWarning
    >
      <body
        className="bg-background text-foreground font-sans antialiased overflow-hidden min-h-screen"
        suppressHydrationWarning
      >
        {children}
        <Toaster position="bottom-right" richColors />
      </body>
    </html>
  );
}
