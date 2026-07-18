"""Create the same safe English drafts used by the production bootstrap."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.database import init_db
from app.agents.registry import seed_agents
from app.bootstrap import seed_initial_content

init_db()
seed_agents()
created = seed_initial_content()
print(f"seed complete: {created} safe English draft(s) created")
