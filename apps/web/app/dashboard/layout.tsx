import "./workspace.css";
import WorkspaceShell from "../../components/workflow/WorkspaceShell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}
