import { Workspace } from "@/components/workspace/Workspace";
export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Workspace>{children}</Workspace>;
}
