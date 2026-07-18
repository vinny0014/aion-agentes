import { Link } from "react-router-dom";
import { Nav } from "./Landing";
import { usePageMetadata } from "../lib/seo";

export default function NotFound() {
  usePageMetadata({ title: "Page not found", description: "The requested AION page does not exist.", path: location.pathname, robots: "noindex,nofollow" });
  return (
    <div className="min-h-screen">
      <Nav />
      <main id="main-content" className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="tag mb-3">error 404</p>
        <h1 className="font-display text-6xl font-bold tracking-tight">
          Page not <span className="text-ultra">found</span>
        </h1>
        <p className="mx-auto mt-5 max-w-md text-slateui">
          Our Monitor agent checked: this address does not exist on AION.
          It may have moved or may never have existed.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/" className="btn-primary">Back to home</Link>
          <Link to="/articles" className="btn-ghost">Browse articles</Link>
        </div>
      </main>
    </div>
  );
}
