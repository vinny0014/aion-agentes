"""Conteúdo editorial inicial — publicado automaticamente no primeiro boot
com banco vazio, para o portal nunca estrear em branco."""
from .core import database as db
from .agents.imagegen import editorial_data_uri

ARTIGOS = [
    ("O que são agentes de IA e por que eles importam", "o-que-sao-agentes-de-ia",
     "guias", "agentes,ia",
     "Agentes de IA são sistemas que percebem, decidem e agem para cumprir objetivos.",
     "## Introdução\n\nAgentes de inteligência artificial são sistemas capazes de perceber um ambiente, tomar decisões e executar ações em direção a um objetivo — com graus variados de autonomia.\n\n## Como funcionam\n\nUm agente combina um modelo de linguagem ou de decisão com ferramentas: acesso a APIs, bancos de dados, navegadores e outros sistemas. O ciclo típico é observar, planejar, agir e avaliar o resultado.\n\n## Aplicações\n\nDo atendimento ao cliente à produção de conteúdo, passando por automação de operações e engenharia de software, agentes já executam fluxos completos sob supervisão humana.\n\n## Conclusão\n\nA tendência é clara: equipes híbridas, em que humanos definem direção e qualidade e agentes executam o volume."),
    ("Pipeline de conteúdo automatizado: da pauta à publicação", "pipeline-de-conteudo-automatizado",
     "guias", "pipeline,automacao,ia",
     "Como estruturar fila, templates e agendador para publicar todos os dias.",
     "## A pauta vira fila\n\nTodo conteúdo começa como um tópico em uma fila priorizada. Isso separa a decisão editorial (o que publicar) da execução (como produzir).\n\n## Templates dão consistência\n\nModelos de artigo, notícia e guia garantem estrutura previsível e facilitam revisão.\n\n## O agendador fecha o ciclo\n\nUm scheduler processa a fila em intervalos regulares, gera rascunhos e registra pendências quando algo depende de intervenção humana.\n\n## Conclusão\n\nAutomatizar o pipeline não elimina o editor — libera o editor para o que importa: qualidade e direção."),
    ("Como o AION funciona: uma redação operada por 20 agentes", "como-o-aion-funciona",
     "guias", "aion,agentes,automacao",
     "Conheça a arquitetura multiagente que pesquisa, escreve, verifica e publica.",
     "## Uma redação autônoma\n\nO AION é operado por uma equipe de agentes com papéis definidos: Discovery pesquisa fontes oficiais, Content escreve, Fact Check verifica, SEO otimiza e o Publisher publica — tudo coordenado pelo CEO Master sob um orçamento controlado pelo Cost Guard.\n\n## O Radar IA\n\nTodos os dias, o Discovery coleta as manchetes das principais fontes do setor e o Publisher monta o Radar IA: uma curadoria original com atribuição e link para cada matéria.\n\n## Supervisão humana\n\nConteúdos com problemas são bloqueados pelo Fact Check e aguardam revisão no painel. Autonomia com responsabilidade.\n\n## Conclusão\n\nO resultado é um portal que se mantém vivo 24 horas por dia — e melhora conforme novas credenciais e fontes são conectadas."),
]


def seed_initial_content() -> int:
    n = 0
    for title, slug, cat, tags, excerpt, body in ARTIGOS:
        if not db.query_one("SELECT id FROM contents WHERE slug = ?", (slug,)):
            db.execute(
                """INSERT INTO contents (title, slug, body, excerpt, status,
                   seo_title, seo_description, category, tags, image_url,
                   image_alt, image_credit, image_width, image_height, published_at)
                   VALUES (?,?,?,?,'published',?,?,?,?,?,?,?,'1200','630',datetime('now'))""",
                (title, slug, body, excerpt, title, excerpt[:160], cat, tags,
                 editorial_data_uri(title, cat), f"Arte editorial AION: {title[:90]}",
                 "Arte editorial AION"))
            n += 1
    db.execute("INSERT INTO logs (level, source, message) VALUES "
               "('info','bootstrap',?)", (f"Bootstrap publicou {n} artigo(s) inicial(is)",))
    return n
