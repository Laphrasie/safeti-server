import { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { LogOut, Wind, Bell, User } from "lucide-react";

interface Props {
  children: ReactNode;
  title?: string;
  actions?: ReactNode;
  unreadAlerts?: number;
}

const ROLE_LABELS: Record<string, string> = {
  wearer: "Porteur",
  doctor: "Médecin",
  supervisor: "Responsable",
};

export default function Layout({ children, title, actions, unreadAlerts }: Props) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Top navbar */}
      <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-1.5 rounded-lg">
              <Wind className="w-5 h-5 text-white" />
            </div>
            <span className="text-white font-semibold text-lg tracking-tight">
              Gas Monitor
            </span>
            {title && (
              <>
                <span className="text-gray-600 mx-1">/</span>
                <span className="text-gray-300 text-sm">{title}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-4">
            {actions}

            {/* Unread alerts badge */}
            {unreadAlerts != null && unreadAlerts > 0 && (
              <span className="relative">
                <Bell className="w-5 h-5 text-gray-400" />
                <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                  {unreadAlerts > 9 ? "9+" : unreadAlerts}
                </span>
              </span>
            )}

            {/* User info */}
            <div className="flex items-center gap-2 text-sm">
              <div className="bg-gray-800 rounded-full p-1.5">
                <User className="w-4 h-4 text-gray-300" />
              </div>
              <div className="hidden sm:block text-right">
                <p className="text-white text-sm font-medium leading-none">
                  {user?.full_name}
                </p>
                <p className="text-gray-500 text-xs mt-0.5">
                  {ROLE_LABELS[user?.role ?? ""] ?? user?.role}
                </p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-gray-400 hover:text-red-400 transition-colors text-sm"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>
    </div>
  );
}
