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
const Privacidade = React.lazy(() => import("./pages/Institucional").then(m => ({ default: m.Privacy })));
const Termos = React.lazy(() => import("./pages/Institucional").then(m => ({ default: m.Terms })));
const Contato = React.lazy(() => import("./pages/Institucional").then(m => ({ default: m.Contact })));
const Categorias = React.lazy(() => import("./pages/Institucional").then(m => ({ default: (p: any) => m.Taxonomia({ tipo: "categories" }) })));
const TagsPage = React.lazy(() => import("./pages/Institucional").then(m => ({ default: (p: any) => m.Taxonomia({ tipo: "tags" }) })));

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <React.Suspense fallback={<div className="p-10 font-mono text-sm text-slateui">Loading…</div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<Sobre />} />
        <Route path="/articles" element={<Blog />} />
        <Route path="/article/:slug" element={<ArtigoLazy />} />
        <Route path="/categories" element={<Categorias />} />
        <Route path="/tags" element={<TagsPage />} />
        <Route path="/privacy" element={<Privacidade />} />
        <Route path="/terms" element={<Termos />} />
        <Route path="/contact" element={<Contato />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Cadastro />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/editor/:id" element={<Editor />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      </React.Suspense>
    </BrowserRouter>
  </React.StrictMode>
);
