"""Arquitetura de Agentes AION.

Cada agente tem responsabilidade única. Nesta fase, os agentes são registrados
no banco e o pipeline de conteúdo roda sem provedores externos (fila fica em
'blocked' com pendência humana registrada até que uma API key seja configurada).
Quando as chaves forem adicionadas ao .env, `providers.generate()` passa a
gerar conteúdo real sem mudanças de arquitetura.
"""
import json

from ..core import database as db
from ..core.config import settings

AGENT_DEFINITIONS = [
    ("ceo-master", "CEO MASTER", "orquestracao",
     "Coordena todos os agentes, define prioridades e aprova entregas."),
    ("developer", "Developer", "engenharia",
     "Implementa funcionalidades, corrige bugs e mantém a base de código."),
    ("qa", "QA", "qualidade",
     "Executa testes, valida fluxos críticos e bloqueia regressões."),
    ("content", "Content", "conteudo",
     "Produz e revisa o conteúdo diário do portal a partir da fila."),
    ("seo", "SEO", "seo",
     "Otimiza títulos, meta descriptions, slugs, schema e sitemap."),
    ("github", "GitHub", "versionamento",
     "Organiza commits, branches, PRs e documentação do repositório."),
    ("deploy", "Deploy", "devops",
     "Prepara e executa deploys no Vercel (frontend) e Render (backend)."),
    ("monitor", "Monitor", "observabilidade",
     "Acompanha health check, logs e alertas de erro."),
    ("cost-guard", "Cost Guard", "custos",
     "Monitora consumo de APIs de IA e impede estouro de orçamento."),
]


def seed_agents() -> None:
    """Registra os agentes padrão (idempotente)."""
    for slug, name, role, desc in AGENT_DEFINITIONS:
        if not db.query_one("SELECT id FROM agents WHERE slug = ?", (slug,)):
            db.execute(
                "INSERT INTO agents (slug, name, role, description) VALUES (?,?,?,?)",
                (slug, name, role, desc),
            )


# ---------------- Provedores de IA (plugáveis) ----------------
class ProviderNotConfigured(Exception):
    pass


def resolve_provider(requested: str) -> str:
    """Escolhe o provedor disponível; lança erro se nenhum estiver configurado."""
    keys = {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "openrouter": settings.OPENROUTER_API_KEY,
        "gemini": settings.GEMINI_API_KEY,
    }
    if requested != "pending" and keys.get(requested):
        return requested
    for name, key in keys.items():
        if key:
            return name
    raise ProviderNotConfigured(
        "Nenhuma API de IA configurada. Adicione OPENAI_API_KEY, ANTHROPIC_API_KEY, "
        "OPENROUTER_API_KEY ou GEMINI_API_KEY ao arquivo .env do backend."
    )


TEMPLATES = {
    "artigo_padrao": (
        "Escreva um artigo em português para o portal AION AGENTES sobre: {topic}. "
        "Estrutura: título, introdução, 3 seções com subtítulos, conclusão. "
        "Tom informativo e acessível."
    ),
    "noticia_curta": (
        "Escreva uma notícia curta (até 300 palavras) sobre: {topic}. "
        "Lead direto, contexto e fecho."
    ),
    "guia_pratico": (
        "Escreva um guia prático passo a passo sobre: {topic}, com pré-requisitos e dicas."
    ),
}


def process_queue_once() -> dict:
    """Processa a fila de conteúdo. Sem provedor configurado, marca itens como
    'blocked' e registra a pendência humana — o resto do sistema segue operando."""
    items = db.query("SELECT * FROM content_queue WHERE status = 'queued' ORDER BY id LIMIT 10")
    processed, blocked = 0, 0
    for item in items:
        try:
            provider = resolve_provider(item["provider"])
            # Ponto de integração: chamada real ao provedor entra aqui.
            # prompt = TEMPLATES[item["template"]].format(topic=item["topic"])
            db.execute(
                "UPDATE content_queue SET status = 'processing', provider = ? WHERE id = ?",
                (provider, item["id"]),
            )
            processed += 1
        except ProviderNotConfigured as exc:
            db.execute(
                "UPDATE content_queue SET status = 'blocked', error = ? WHERE id = ?",
                (str(exc), item["id"]),
            )
            db.execute(
                "INSERT INTO logs (level, source, message, meta_json) VALUES ('warn','content-pipeline',?,?)",
                ("Item da fila bloqueado: falta configurar API de IA (PENDÊNCIA HUMANA)",
                 json.dumps({"queue_id": item["id"], "topic": item["topic"]})),
            )
            blocked += 1
    return {"processed": processed, "blocked": blocked, "scanned": len(items)}
