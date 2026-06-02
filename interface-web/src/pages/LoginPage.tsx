import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const redirectTo = (location.state as { from?: string } | null)?.from || "/busca";

  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, navigate, redirectTo]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast({
        title: "Sessão iniciada",
        description: "Frontend autenticado e pronto para consumir os módulos do sistema.",
      });
      navigate(redirectTo, { replace: true });
    } catch (error) {
      toast({
        title: "Falha no login",
        description: error instanceof Error ? error.message : "Não foi possível autenticar.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted">
      <div className="w-full max-w-md animate-fade-in">
        <div className="glass-card p-8">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <img
              src="/logo_ifesdoc.ico"
              alt="Logo do IFESDOC"
              className="h-14 w-14 rounded-xl object-contain mb-4"
            />
            <h1 className="text-2xl font-bold text-foreground">IFESDOC</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Sistema de Indexação e Busca de Documentos
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu.email@ifes.edu.br"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full h-11" disabled={loading}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Entrando...
                </span>
              ) : (
                "Entrar"
              )}
            </Button>
          </form>

          <p className="text-xs text-muted-foreground text-center mt-6">
            © 2026 IFESDOC — Todos os direitos reservados
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
