import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../lib/api";
import { Nav } from "./Landing";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function entrar(e: React.FormEvent) {
    e.preventDefault();
    setErro(""); setCarregando(true);
    try {
      await login(email, senha);
      nav("/dashboard");
    } catch (err: any) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-sm px-6 py-16">
        <p className="tag mb-2">acesso</p>
        <h1 className="font-display text-3xl font-bold">Entrar</h1>
        <form onSubmit={entrar} className="mt-8 space-y-4">
          <label className="block text-sm font-medium">
            E-mail
            <input className="field mt-1.5" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">
            Senha
            <input className="field mt-1.5" type="password" required value={senha}
              onChange={(e) => setSenha(e.target.value)} autoComplete="current-password" />
          </label>
          {erro && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{erro}</p>}
          <button className="btn-primary w-full" disabled={carregando}>
            {carregando ? "Entrando…" : "Entrar"}
          </button>
        </form>
        <p className="mt-6 text-sm text-slateui">
          Ainda não tem conta?{" "}
          <Link to="/cadastro" className="font-medium text-ultra hover:underline">Criar conta</Link>
        </p>
      </main>
    </div>
  );
}
