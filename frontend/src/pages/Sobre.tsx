import { Nav } from "./Landing";
import { usePageMetadata } from "../lib/seo";

export default function Sobre() {
  usePageMetadata({ title: "About", description: "Learn how AION AI NEWS OS combines autonomous newsroom agents with human editorial supervision.", path: "/about" });
  return (
    <div className="min-h-screen">
      <Nav />
      <main id="main-content" className="mx-auto max-w-3xl px-6 py-16">
        <p className="tag mb-2">about</p>
        <h1 className="font-display text-4xl font-bold">About <span className="grad-text">AION</span></h1>
        <div className="prose-body mt-8 space-y-4 text-slateui">
          <p>
            AION AI NEWS OS is an artificial-intelligence news portal built on a simple idea:
            a publication can be operated, from draft to publication, by a team of AI agents
            with well-defined responsibilities — under human supervision.
          </p>
          <p>
            The platform runs a daily production pipeline (queue, scheduler and templates)
            coordinated by an orchestrator of 25+ agents: Discovery, Research, Writer,
            Fact Check, SEO, Image, Publisher, QA, Security, Monitor and Cost Guard, among
            others. Each covers one stage of the operation, from sourcing to shipping.
          </p>
          <p>
            <strong>Editorial team.</strong> Content is published under three bylines:
            AION Editorial (agent-produced, human-supervised), Vinicio Alves (founder's
            research and analysis) and Guest Author (invited contributors). Every story
            carries its author, date, category and — whenever it draws on external
            reporting — explicit attribution and links to the original sources.
          </p>
          <p>
            <strong>Editorial policy.</strong> We never copy third-party articles, never
            invent facts, and always cite sources. Curation pieces such as the daily AI
            Radar clearly separate what the sources reported from AION's own framing.
          </p>
          <p>
            The project was built production-ready: JWT authentication, rate limiting,
            security headers, automated tests and a strict monthly AI budget enforced by
            the Cost Guard agent.
          </p>
        </div>
      </main>
    </div>
  );
}
