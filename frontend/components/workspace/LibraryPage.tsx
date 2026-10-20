"use client";
import { DocumentLibrary } from "@/components/documents/DocumentsDrawer";
import { useWorkspace } from "./Workspace";
export function LibraryPage() {
  const {
    documents,
    userId,
    onDocumentUploaded,
    onDocumentDeleted,
    useDocumentInChat,
    toggleSidebar,
  } = useWorkspace();
  return (
    <DocumentLibrary
      documents={documents}
      sessionId={userId}
      onDocumentUploaded={onDocumentUploaded}
      onDocumentDeleted={onDocumentDeleted}
      onUseInChat={useDocumentInChat}
      onToggleSidebar={toggleSidebar}
    />
  );
}
