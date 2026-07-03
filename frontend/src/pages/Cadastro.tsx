import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, login } from "../lib/api";
import { Nav } from "./Landing";

export default function Cadastro() {
  const nav = useNavigate();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function criar(e: React.FormEvent) {
    e.preventDefault();
    setErro(""); setCarregando(true);
    try {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ name: nome, email, password: senha }),
      });
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
        <p className="tag mb-2">novo acesso</p>
        <h1 className="font-display text-3xl font-bold">Criar conta</h1>
        <form onSubmit={criar} className="mt-8 space-y-4">
          <label className="block text-sm font-medium">
            Nome
            <input className="field mt-1.5" required minLength={2} value={nome}
              onChange={(e) => setNome(e.target.value)} autoComplete="name" />
          </label>
          <label className="block text-sm font-medium">
            E-mail
            <input className="field mt-1.5" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">
            Senha
            <input className="field mt-1.5" type="password" required minLength={8} value={senha}
              onChange={(e) => setSenha(e.target.value)} autoComplete="new-password" />
            <span className="mt-1 block text-xs font-normal text-slateui">Mínimo de 8 caracteres.</span>
          </label>
          {erro && <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300">{erro}</p>}
          <button className="btn-primary w-full" disabled={carregando}>
            {carregando ? "Criando…" : "Criar conta"}
          </button>
        </form>
        <p className="mt-6 text-sm text-slateui">
          Já tem conta?{" "}
          <Link to="/login" className="font-medium text-ultra hover:underline">Entrar</Link>
        </p>
      </main>
    </div>
  );
}
