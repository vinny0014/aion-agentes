"""Seed de demonstração — popula o banco com conteúdo inicial.
Uso: python scripts_seed.py (na pasta backend, com o app parado ou rodando)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.database import init_db, execute, query_one
from app.agents.registry import seed_agents

init_db(); seed_agents()
ARTIGOS = [
    ("O que são agentes de IA e por que eles importam", "o-que-sao-agentes-de-ia",
     "Agentes de IA são sistemas que percebem, decidem e agem para cumprir objetivos.",
     "## Introdução\n\nAgentes de inteligência artificial são sistemas capazes de perceber um ambiente, tomar decisões e executar ações em direção a um objetivo — com graus variados de autonomia.\n\n## Como funcionam\n\nUm agente combina um modelo de linguagem ou de decisão com ferramentas: acesso a APIs, bancos de dados, navegadores e outros sistemas. O ciclo típico é observar, planejar, agir e avaliar o resultado.\n\n## Aplicações\n\nDo atendimento ao cliente à produção de conteúdo, passando por automação de operações e engenharia de software, agentes já executam fluxos completos sob supervisão humana.\n\n## Conclusão\n\nA tendência é clara: equipes híbridas, em que humanos definem direção e qualidade e agentes executam o volume."),
    ("Pipeline de conteúdo automatizado: da pauta à publicação", "pipeline-de-conteudo-automatizado",
     "Como estruturar fila, templates e agendador para publicar todos os dias.",
     "## A pauta vira fila\n\nTodo conteúdo começa como um tópico em uma fila priorizada. Isso separa a decisão editorial (o que publicar) da execução (como produzir).\n\n## Templates dão consistência\n\nModelos de artigo, notícia e guia garantem estrutura previsível e facilitam revisão.\n\n## O agendador fecha o ciclo\n\nUm scheduler processa a fila em intervalos regulares, gera rascunhos e registra pendências quando algo depende de intervenção humana.\n\n## Conclusão\n\nAutomatizar o pipeline não elimina o editor — libera o editor para o que importa: qualidade e direção."),
]
for title, slug, excerpt, body in ARTIGOS:
    if not query_one("SELECT id FROM contents WHERE slug = ?", (slug,)):
        execute("""INSERT INTO contents (title, slug, body, excerpt, status, seo_title, seo_description, published_at)
                   VALUES (?,?,?,?,'published',?,?,datetime('now'))""",
                (title, slug, body, excerpt, title, excerpt[:160]))
        print(f"publicado: {slug}")
print("seed concluído")
