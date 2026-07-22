# AION — catálogo operacional dos 35 agentes

O banco preserva os 35 registros históricos. A classificação abaixo separa os nove agentes principais dos módulos internos e das integrações externas. O campo `status` (`idle`, `running`, `error`) representa somente o estado de execução; não prova capacidade. A prova operacional fica em `config_json`, `agent_runs`, `logs`, `memories` e nos efeitos persistidos.

| ID lógico | Nome | Classificação | Handler/execução | Limitação real |
|---|---|---|---|---|
| ceo-master | Commander / CEO Master | OPERATIONAL | `orchestrator.run_cycle` | Limite de 4 ciclos/h e lock com TTL |
| discovery | Discovery | OPERATIONAL | `team.discovery_agent` | Depende da disponibilidade dos RSS |
| content | Content | OPERATIONAL | `team.content_writer_agent` | Redação final requer provedor configurado |
| fact-check | Verification / Fact Check | OPERATIONAL | `team.fact_check_agent` | Checagem factual profunda pode exigir IA |
| image | Image | OPERATIONAL | `team.image_agent` | Usa template AION quando fontes externas falham |
| image-quality | Image Validator | OPERATIONAL | `team.image_quality_agent` | OCR não está incluído |
| seo | SEO Publisher gate | OPERATIONAL | `team.seo_agent` | Publicação final é executada pelo módulo Publisher |
| monitor | Monitor Recovery | OPERATIONAL | `team.monitor_agent` a cada 5 min | Integrações externas exigem rede e DNS válidos |
| cost-guard | Cost Guard | OPERATIONAL | `team.cost_guard_agent` | Custos dependem do uso reportado pelo provedor |
| developer | Developer | INTERNAL_MODULE | sem handler autônomo | Mudança de código passa por Git/PR |
| qa | QA | INTERNAL_MODULE | `team.qa_agent` | E2E completo roda no CI com Chromium |
| github | GitHub | BLOCKED_EXTERNAL | conector externo | Requer GitHub/PR e permissões válidas |
| deploy | Deploy | BLOCKED_EXTERNAL | Vercel/Render | Requer contas e configuração externa |
| image-repair | Image Repair | INTERNAL_MODULE | `team.image_repair_agent` | — |
| image-prompt | Image Prompt | INTERNAL_MODULE | `team.image_prompt_agent` | Prompt não é imagem publicada |
| image-optimization | Image Optimization | INTERNAL_MODULE | `team.image_optimization_agent` | — |
| translation | Public Language | INTERNAL_MODULE | `team.translation_agent` | O portal público permanece somente em inglês |
| research | Research | INTERNAL_MODULE | `team.research_agent` | Usa fatos e fontes coletados |
| breaking-news | Breaking News | INTERNAL_MODULE | `team.breaking_news_agent` | Detecção determinística por sinais |
| trend-hunter | Trend Hunter | INTERNAL_MODULE | `team.trend_hunter_agent` | Tendências externas dependem do Discovery |
| publisher | Publisher | INTERNAL_MODULE | `team.publisher_agent` | Nunca contorna os gates de fonte, imagem e idioma |
| rss | RSS | INTERNAL_MODULE | `team.rss_agent` | — |
| google-news | Google News | INTERNAL_MODULE | `team.google_news_agent` | Cadastro no Publisher Center é externo |
| scheduler | Scheduler | INTERNAL_MODULE | APScheduler | Executa dentro do serviço Render |
| discovery-growth | Discovery Growth | INTERNAL_MODULE | `team.discovery_growth_agent` | Métricas externas não são inventadas |
| dashboard | Dashboard | INTERNAL_MODULE | `team.dashboard_agent` | Exibe somente dados persistidos |
| performance | Performance | INTERNAL_MODULE | `team.performance_agent` | CWV real exige medição em produção |
| security | Security | INTERNAL_MODULE | `team.security_agent` | — |
| social-media | Social Media | PARTIAL | `team.social_media_agent` | Publicação exige credenciais das redes |
| newsletter | Newsletter | PARTIAL | `team.newsletter_agent` | Envio exige SMTP/provedor |
| analytics | Analytics | PARTIAL | `team.analytics_agent` | Tráfego externo exige GA4 conectado |
| google-discover | Google Discover | PARTIAL | `team.google_discover_agent` | Métricas reais existem no Search Console |
| search-console | Search Console | PARTIAL | `team.search_console_agent` | Propriedade e acesso são externos |
| adsense-opt | AdSense Optimization | PARTIAL | `team.adsense_agent` | Aprovação e receita são externas |
| revenue | Revenue | PARTIAL | `team.revenue_agent` | Receita permanece `null` até integração real |

Pipeline crítico: `Scheduler → Commander → Discovery → Research → Content → SEO → Image → Image Validator → Fact Check → Publisher → RSS/Sitemaps → Monitor Recovery`.

Orçamento: US$13/mês para APIs, além de US$7/mês do Render. O Cost Guard entra em modo econômico em US$10, restringe para conteúdo essencial em US$12 e bloqueia novas chamadas pagas em US$13. RSS, cache, monitoramento e templates continuam funcionando sem IA paga.
