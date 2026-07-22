import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../lib/api";
import { Nav } from "./Landing";
import { usePageMetadata } from "../lib/seo";
import { trackEvent } from "../lib/telemetry";

export default function Login() {
  usePageMetadata({ title: "Sign in", description: "Sign in to the AION editorial workspace.", path: "/login", robots: "noindex,nofollow" });
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setLoading] = useState(false);

  async function entrar(e: React.FormEvent) {
    e.preventDefault();
    setErro(""); setLoading(true);
    try {
      await login(email, senha);
      trackEvent("login", { method: "password" });
      nav("/dashboard");
    } catch (err: any) {
      setErro(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <Nav />
      <main id="main-content" className="mx-auto max-w-sm px-6 py-16">
        <p className="tag mb-2">account access</p>
        <h1 className="font-display text-3xl font-bold">Sign in</h1>
        <form onSubmit={entrar} className="mt-8 space-y-4">
          <label className="block text-sm font-medium">
            Email
            <input className="field mt-1.5" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input className="field mt-1.5" type="password" required value={senha}
              onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
          </label>
          {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">{erro}</p>}
          <button className="btn-primary w-full" disabled={carregando}>
            {carregando ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="mt-6 text-sm text-slateui">
          Don't have an account?{" "}
          <Link to="/signup" className="font-medium text-ultra hover:underline">Create account</Link>
        </p>
      </main>
    </div>
  );
}
