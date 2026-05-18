import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Search,
  FileUp,
  Database,
  BarChart3,
  Clock,
  Users,
  Settings,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { appEnv } from "@/lib/env";

const navItems = [
  { title: "Busca", path: "/busca", icon: Search, adminOnly: false },
  { title: "Ingestão", path: "/ingestao", icon: FileUp, adminOnly: true },
  { title: "Indexação", path: "/indexacao", icon: Database, adminOnly: true },
  { title: "Métricas", path: "/metricas", icon: BarChart3, adminOnly: true },
  { title: "Histórico", path: "/historico", icon: Clock, adminOnly: false },
  { title: "Gestão de Usuários", path: "/usuarios", icon: Users, adminOnly: true },
  { title: "Configurações", path: "/configuracoes", icon: Settings, adminOnly: false },
];

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, isAdmin } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <aside className="w-64 min-h-screen bg-sidebar flex flex-col border-r border-sidebar-border shrink-0">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-sidebar-border">
        <img
          src="/logo_ifesdoc.ico"
          alt="Logo do IFESDOC"
          className="h-8 w-8 rounded-sm object-contain mr-3 shrink-0"
        />
        <span className="text-xl font-bold text-sidebar-accent-foreground tracking-tight">
          {appEnv.appName}
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.filter((item) => !item.adminOnly || isAdmin).map((item) => {
          const isActive = location.pathname.startsWith(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`sidebar-link ${isActive ? "sidebar-link-active" : "sidebar-link-inactive"}`}
            >
              <item.icon className="h-4.5 w-4.5 shrink-0" />
              <span>{item.title}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-3 border-t border-sidebar-border">
        <button
          type="button"
          onClick={handleLogout}
          className="sidebar-link sidebar-link-inactive"
        >
          <LogOut className="h-4.5 w-4.5 shrink-0" />
          <span>Sair</span>
        </button>
      </div>
    </aside>
  );
}
