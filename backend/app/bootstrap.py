"""Initial English editorial drafts for a fresh installation.

They intentionally remain drafts until a real HTTP image passes the publication
gate. Production must never launch placeholder or data-URI news images.
"""
from .core import database as db

ARTIGOS = [
    ("What AI agents are and why they matter", "what-ai-agents-are",
     "guides", "agents,ai",
     "AI agents are systems that perceive, decide and act to accomplish goals.",
     "## Introduction\n\nArtificial-intelligence agents are systems able to perceive an environment, make decisions and take actions toward a goal — with varying degrees of autonomy.\n\n## How they work\n\nAn agent combines a language or decision model with tools: APIs, databases, browsers and other systems. The typical loop is observe, plan, act and evaluate the result.\n\n## Applications\n\nFrom customer support to content production, operations automation and software engineering, agents already run full workflows under human supervision.\n\n## Conclusion\n\nThe trend is clear: hybrid teams, where humans set direction and quality while agents execute the volume."),
    ("The automated content pipeline: from idea to publication", "automated-content-pipeline",
     "guides", "pipeline,automation,ai",
     "How to structure a queue, templates and a scheduler to publish every day.",
     "## Ideas become a queue\n\nEvery piece of content starts as a topic in a prioritized queue. That separates the editorial decision (what to publish) from execution (how to produce it).\n\n## Templates bring consistency\n\nArticle, news and guide templates guarantee a predictable structure and make review easier.\n\n## The scheduler closes the loop\n\nA scheduler processes the queue at regular intervals, produces drafts and logs anything that requires human action.\n\n## Conclusion\n\nAutomating the pipeline does not remove the editor — it frees the editor for what matters: quality and direction."),
    ("Inside AION: a newsroom operated by 20+ agents", "inside-aion-newsroom",
     "guides", "aion,agents,automation",
     "Meet the multi-agent architecture that researches, writes, verifies and publishes.",
     "## An autonomous newsroom\n\nAION is operated by a team of agents with defined roles: Discovery researches official sources, the Writer drafts, Fact Check verifies, SEO optimizes and the Publisher ships — all coordinated by the CEO Master under a budget enforced by the Cost Guard.\n\n## The AI Radar\n\nEvery day, Discovery collects the top headlines from the industry's leading sources and the Publisher assembles the AI Radar: an original curation with attribution and a link to every story.\n\n## Human oversight\n\nContent with problems is blocked by Fact Check and waits for review in the panel. Autonomy with accountability.\n\n## Conclusion\n\nThe result is a portal that stays alive 24 hours a day — and improves as new credentials and sources are connected."),
]


def seed_initial_content() -> int:
    n = 0
    for title, slug, cat, tags, excerpt, body in ARTIGOS:
        if not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug,)):
            db.execute(
                """INSERT INTO contents (title, slug, body, excerpt, status,
                   seo_title, seo_description, category, tags, image_url,
                   image_alt, image_credit, author, published_at)
                   VALUES (?,?,?,?,'draft',?,?,?,?,?,'','','AION Editorial',NULL)""",
                (title, slug, body, excerpt, title, excerpt[:160], cat, tags, ""))
            n += 1
    db.execute("INSERT INTO logs (level, source, message) VALUES "
               "('info','bootstrap',?)", (f"Bootstrap created {n} image-gated draft(s)",))
    return n
