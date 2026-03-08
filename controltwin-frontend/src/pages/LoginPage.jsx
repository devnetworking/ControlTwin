import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Eye, EyeOff } from "lucide-react";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [form, setForm] = useState({ username: "", password: "" });
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (!form.username || !form.password) {
      setError("Username and password are required.");
      return;
    }

    try {
      setLoading(true);
      await login(form);
      navigate("/dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || "Invalid credentials or account locked.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ot-bg p-4">
      <div className="w-full max-w-md rounded-xl border border-ot-border bg-ot-card p-8 shadow-xl">
        <div className="mb-6 text-center">
          <div className="mb-3 inline-flex items-center gap-2 text-2xl font-bold">
            <Shield className="h-7 w-7 text-ot-blue" />
            <span className="text-white">
              Control<span className="text-ot-blue">Twin</span>
            </span>
          </div>
          <p className="text-sm text-gray-300">Industrial Control System Digital Twin</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <Input
            placeholder="Username"
            value={form.username}
            onChange={(e) => setForm((s) => ({ ...s, username: e.target.value }))}
            required
          />
          <div className="relative">
            <Input
              type={showPwd ? "text" : "password"}
              placeholder="Password"
              value={form.password}
              onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))}
              required
            />
            <button
              type="button"
              className="absolute right-3 top-2.5 text-gray-300"
              onClick={() => setShowPwd((v) => !v)}
            >
              {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {error ? <div className="text-sm text-ot-red">{error}</div> : null}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Login"}
          </Button>
        </form>
      </div>
    </div>
  );
}
