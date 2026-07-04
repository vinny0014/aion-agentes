import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import Landing from "./pages/Landing";
const Sobre = React.lazy(() => import("./pages/Sobre"));
const Login = React.lazy(() => import("./pages/Login"));
const Cadastro = React.lazy(() => import("./pages/Cadastro"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const Admin = React.lazy(() => import("./pages/Admin"));
const Blog = React.lazy(() => import("./pages/Blog").then(m => ({ default: m.Conteudos })));
const ArtigoLazy = React.lazy(() => import("./pages/Blog").then(m => ({ default: m.Artigo })));
const Editor = React.lazy(() => import("./pages/Editor"));
const NotFound = React.lazy(() => import("./pages/NotFound"));
const Privacidade = React.lazy(() => import("./pages/Institucional").then(m => ({ default: m.Privacidade })));
const Termos = React.lazy(() => import("./pages/Institucional").then(m => ({ default: m.Termos })));
const Contato = React.lazy(() => import("./pages/Institucional").then(m => ({ default: m.Contato })));
const Categorias = React.lazy(() => import("./pages/Institucional").then(m => ({ default: (p: any) => m.Taxonomia({ tipo: "categorias" }) })));
const TagsPage = React.lazy(() => import("./pages/Institucional").then(m => ({ default: (p: any) => m.Taxonomia({ tipo: "tags" }) })));

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <React.Suspense fallback={<div className="p-10 font-mono text-sm text-slateui">carregando…</div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/sobre" element={<Sobre />} />
        <Route path="/conteudos" element={<Blog />} />
        <Route path="/conteudo/:slug" element={<ArtigoLazy />} />
        <Route path="/categorias" element={<Categorias />} />
        <Route path="/tags" element={<TagsPage />} />
        <Route path="/privacidade" element={<Privacidade />} />
        <Route path="/termos" element={<Termos />} />
        <Route path="/contato" element={<Contato />} />
        <Route path="/login" element={<Login />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/editor/:id" element={<Editor />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      </React.Suspense>
    </BrowserRouter>
  </React.StrictMode>
);
