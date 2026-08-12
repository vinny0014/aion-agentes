# Analytics do AION News

Cadastre `VITE_GA_MEASUREMENT_ID=G-DVT2E73K18` no ambiente de build da Hostinger. O valor pertence exclusivamente ao AION News. `VITE_GA_DEBUG=true` é opcional e deve ser usado apenas em validação temporária.

O frontend usa uma única Google tag direta (`gtag.js`), sem Google Tag Manager. A tag e os eventos permanecem bloqueados até o visitante aceitar Analytics no banner. A navegação SPA envia um `page_view` manual por URL porque a configuração usa `send_page_view: false`.

Eventos editoriais: `page_view`, `article_view`, `article_scroll_25`, `article_scroll_50`, `article_scroll_90`, `outbound_source_click`, `search_performed`, `newsletter_subscribe` e `category_view`. O texto pesquisado e dados de formulário não são enviados.

Para validar, limpe `aion_cookie_consent_v1` no armazenamento local, recuse e confirme que `gtag.js`/requisições do Google Analytics não carregam. Depois aceite, navegue entre rotas e confirme no GA4 Realtime um único `page_view` por URL e os eventos correspondentes.
