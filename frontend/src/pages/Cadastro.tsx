import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, login } from "../lib/api";
import { Nav } from "./Landing";
import { usePageMetadata } from "../lib/seo";
import { trackEvent } from "../lib/telemetry";

export default function Cadastro() {
  usePageMetadata({ title: "Create account", description: "Create an AION account.", path: "/signup", robots: "noindex,nofollow" });
  const nav = useNavigate();
  const [nome, setName] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setPassword] = useState("");
  const [setupToken, setSetupToken] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setLoading] = useState(false);

  async function criar(e: React.FormEvent) {
    e.preventDefault();
    setErro(""); setLoading(true);
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ name: nome, email, password: senha, setup_token: setupToken || undefined }),
      });
      await login(email, senha);
      trackEvent("sign_up", { method: "password", owner_setup: Boolean(setupToken) });
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
        <p className="tag mb-2">new account</p>
        <h1 className="font-display text-3xl font-bold">Create account</h1>
        <form onSubmit={criar} className="mt-8 space-y-4">
          <label className="block text-sm font-medium">
            Name
            <input className="field mt-1.5" required minLength={2} value={nome}
              onChange={(e) => setName(e.target.value)} autoComplete="name" />
          </label>
          <label className="block text-sm font-medium">
            Email
            <input className="field mt-1.5" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input className="field mt-1.5" type="password" required minLength={8} value={senha}
              onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" />
            <span className="mt-1 block text-xs font-normal text-slateui">At least 8 characters.</span>
          </label>
          <label className="block text-sm font-medium">
            Owner setup token <span className="font-normal text-slateui">(first account only)</span>
            <input className="field mt-1.5" type="password" value={setupToken}
              onChange={(e) => setSetupToken(e.target.value)} autoComplete="off" />
          </label>
          {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">{erro}</p>}
          <button className="btn-primary w-full" disabled={carregando}>
            {carregando ? "Creating…" : "Create account"}
          </button>
        </form>
        <p className="mt-6 text-sm text-slateui">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-ultra hover:underline">Sign in</Link>
        </p>
      </main>
    </div>
  );
}
