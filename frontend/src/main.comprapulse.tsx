import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";

const CompraPulse = React.lazy(() => import("./pages/CompraPulse"));
const CompraPulseAdmin = React.lazy(() =>
  import("./pages/CompraPulse").then((module) => ({ default: module.CompraPulseAdmin })),
);
const Login = React.lazy(() =>
  import("./pages/CompraPulseAccess").then((module) => ({ default: module.CompraPulseLogin })),
);
const NotFound = React.lazy(() =>
  import("./pages/CompraPulseAccess").then((module) => ({ default: module.CompraPulseNotFound })),
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <React.Suspense fallback={<div className="p-10 font-mono text-sm text-slateui">Carregando…</div>}>
        <Routes>
          <Route path="/" element={<CompraPulse />} />
          <Route path="/produto/:id" element={<CompraPulse />} />
          <Route path="/admin" element={<CompraPulseAdmin />} />
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </React.Suspense>
    </BrowserRouter>
  </React.StrictMode>,
);
