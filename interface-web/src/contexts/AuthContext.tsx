import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authSessionExpiredEvent } from "@/lib/api/client";
import { authService } from "@/lib/api/services";
import { storageKeys } from "@/lib/storage";
import type { SessionUser } from "@/types/app";

type AuthContextValue = {
  user: SessionUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type StoredSession = Partial<SessionUser> & {
  cod_usuario?: number;
  nome?: string;
  ativo?: boolean;
  perfil?: string;
};

const normalizeRole = (value?: string | null): SessionUser["role"] =>
  value === "ADMIN" || value === "Administrador" ? "Administrador" : "Usuário";

const normalizeSession = (session: StoredSession): SessionUser | null => {
  const id = session.id ?? session.cod_usuario;
  const name = session.name ?? session.nome;
  const role = normalizeRole(session.role ?? session.perfil);
  const active = session.active ?? session.ativo;

  if (
    !Number.isFinite(id) ||
    typeof name !== "string" ||
    typeof session.login !== "string" ||
    typeof session.email !== "string" ||
    typeof session.token !== "string" ||
    typeof active !== "boolean"
  ) {
    return null;
  }

  return {
    id,
    name,
    login: session.login,
    email: session.email,
    role,
    active,
    token: session.token,
  };
};

const readSession = (): SessionUser | null => {
  const raw = localStorage.getItem(storageKeys.session);
  if (!raw) {
    return null;
  }

  try {
    return normalizeSession(JSON.parse(raw) as StoredSession);
  } catch {
    localStorage.removeItem(storageKeys.session);
    return null;
  }
};

const clearSession = () => {
  localStorage.removeItem(storageKeys.session);
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const handleSessionExpired = () => {
      clearSession();
      if (isMounted) {
        setUser(null);
        setIsLoading(false);
      }
    };

    const restoreSession = async () => {
      const storedSession = readSession();
      if (!storedSession) {
        if (isMounted) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const validatedSession = await authService.me(storedSession.token);
        localStorage.setItem(storageKeys.session, JSON.stringify(validatedSession));
        if (isMounted) {
          setUser(validatedSession);
        }
      } catch {
        clearSession();
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    window.addEventListener(authSessionExpiredEvent, handleSessionExpired);
    void restoreSession();

    return () => {
      isMounted = false;
      window.removeEventListener(authSessionExpiredEvent, handleSessionExpired);
    };
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAuthenticated: !!user,
    isAdmin: user?.role === "Administrador",
    isLoading,
    async login(email: string, password: string) {
      const session = await authService.login(email, password);
      localStorage.setItem(storageKeys.session, JSON.stringify(session));
      setUser(session);
    },
    async logout() {
      const session = user ?? readSession();
      try {
        await authService.logout(session?.token);
      } finally {
        clearSession();
        setUser(null);
      }
    },
  }), [isLoading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
};
