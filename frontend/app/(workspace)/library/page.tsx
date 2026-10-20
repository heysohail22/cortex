import type { Metadata } from "next";
import { LibraryPage } from "@/components/workspace/LibraryPage";
export const metadata: Metadata = { title: "Knowledge base — Cortex" };
export default function KnowledgeBasePage() {
  return <LibraryPage />;
}
