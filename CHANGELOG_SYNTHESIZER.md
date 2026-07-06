# CHANGELOG — Content Synthesizer (v5.4): notícias reais sem OPENAI_API_KEY

## Problema resolvido
Sem chave de IA, o portal só tinha os guias do bootstrap + Radar diário. Agora publica **notícias completas** automaticamente, com custo zero.

## Como funciona (respeitando direitos autorais)
- O **Discovery** agora captura também o `description`/`summary` que os próprios feeds RSS publicam (campo destinado a redistribuição), além de título, link e imagem.
- O **Content Synthesizer** (`agents/synthesizer.py`) agrupa manchetes correlatas (clustering por sobreposição de palavras-chave) e, a partir dos **resumos de múltiplas fontes**, redige uma notícia em estrutura editorial (lead + "O que se sabe" com blocos atribuídos + "Contexto" + "Fontes"), sempre com **atribuição explícita e links**.
- **Não é cópia**: combina 2-3 fontes, reestrutura, atribui e nunca reproduz texto na íntegra. **Não inventa**: exige que a fonte traga resumo; sem resumo, não sintetiza.
- O **Publisher** publica até 6 notícias sintetizadas por ciclo, cada uma com imagem garantida (oficial do feed ou arte editorial), categoria `noticias`, tags e `source_url`.

## Fontes RSS ampliadas
TechCrunch, VentureBeat, The Verge, Wired, arXiv, Hugging Face, NVIDIA, Anthropic, OpenAI, Google AI — priorizando feeds com `description` rico.

## Correção de bug (encontrado na validação E2E)
No ciclo completo, o Content Writer criava rascunhos com o mesmo slug das manchetes, bloqueando a síntese por colisão de slug. Corrigido: a síntese verifica duplicidade por **título publicado** e gera slug único, publicando independentemente de rascunhos.

## Com OPENAI_API_KEY (quando configurada)
O Content Writer assume a redação completa (800-1500 palavras) via briefing do Research; a síntese extrativa continua como camada de custo zero garantindo volume mesmo sem/no limite do orçamento.

## Testes: 59/59 (4 novos do synthesizer). E2E: notícia completa publicada no ciclo, sem IA.
