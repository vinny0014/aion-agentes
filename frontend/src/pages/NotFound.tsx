import { Link } from "react-router-dom";
import { Nav } from "./Landing";

export default function NotFound() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="tag mb-3">erro 404</p>
        <h1 className="font-display text-6xl font-bold tracking-tight">
          Page not <span className="text-ultra">found</span>
        </h1>
        <p className="mx-auto mt-5 max-w-md text-slateui">
          Our Monitor agent checked: this address does not exist on AION.
          Ele pode ter sido movido ou nunca ter existido.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/" className="btn-primary">Back to home</Link>
          <Link to="/articles" className="btn-ghost">Browse articles</Link>
        </div>
      </main>
    </div>
  );
}
