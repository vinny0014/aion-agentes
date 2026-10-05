import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../lib/api";

function Brand() {
  return (
    <header className="border-b border-white/10 bg-slate-950 px-6 py-5">
      <Link className="font-display text-xl font-bold text-white" to="/">
        Compra<span className="text-orange-400">Pulse</span>
      </Link>
    </header>
  );
}

export function CompraPulseLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setPassword] = useState("");
  const [erro, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, senha);
      navigate("/admin");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível entrar.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <Brand />
      <main className="mx-auto max-w-sm px-6 py-16">
        <p className="tag mb-2">acesso administrativo</p>
        <h1 className="font-display text-3xl font-bold">Entrar no CompraPulse</h1>
        <form onSubmit={submit} className="mt-8 space-y-4">
          <label className="block text-sm font-medium">
            E-mail
            <input className="field mt-1.5" type="email" required value={email}
              onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">
            Senha
            <input className="field mt-1.5" type="password" required value={senha}
              onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </label>
          {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">{erro}</p>}
          <button className="btn-primary w-full" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </main>
    </div>
  );
}

export function CompraPulseNotFound() {
  return (
    <div className="min-h-screen">
      <Brand />
      <main className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="tag mb-3">erro 404</p>
        <h1 className="font-display text-5xl font-bold">Página não encontrada</h1>
        <p className="mx-auto mt-5 max-w-md text-slateui">Este endereço não existe no CompraPulse.</p>
        <Link to="/" className="btn-primary mt-8 inline-flex">Voltar às ofertas</Link>
      </main>
    </div>
  );
}
