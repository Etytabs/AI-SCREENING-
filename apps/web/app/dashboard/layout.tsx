import "./workspace.css";
import "./skin.css";
import "./check-cards.css";
import "./sidebar-layout.css";
import WorkspaceShell from "../../components/workflow/WorkspaceShell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}
