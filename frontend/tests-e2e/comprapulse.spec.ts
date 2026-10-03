import { expect, test } from '@playwright/test';

// UI contract tests with intercepted API responses, not evidence of real Shopee attribution.
test('admin must preview before saving and edits invalidate approval', async ({ page }) => {
  let saves = 0;
  let previewed: unknown;
  let saved: unknown;
  await page.route('**/api/commerce/admin', route => route.fulfill({ json: {
    metrics: { events: {}, commission_feed_connected: false }, offers: [], jobs: [],
  } }));
  await page.route('**/api/commerce/admin/import/preview', async route => {
    previewed = route.request().postDataJSON().records[0];
    await route.fulfill({json: {accepted_count: 1, rejected_count: 0, rejected: [],
      preview_receipts: [{index: 0, receipt: 'test-preview-receipt'}]}});
  });
  await page.route('**/api/commerce/admin/import', async route => {
    saves++; saved = route.request().postDataJSON();
    await route.fulfill({status: 201, json: {offer_id: 1, created: true}});
  });
  await page.goto('/comprapulse/admin');
  const record = {title: 'Fixture de teste local', price_cents: 6000, category: 'Casa',
    image_url: '/og-cover.png', source_url: 'https://shopee.com.br/product/1/1',
    affiliate_url: 'https://shope.ee/test-only'};
  const input = page.getByLabel('Registro JSON normalizado');
  const save = page.getByRole('button', {name: 'Confirmar e salvar rascunho'});
  await input.fill(JSON.stringify(record));
  await expect(save).toHaveCount(0);
  await page.getByRole('button', {name: 'Conferir preview'}).click();
  await expect(save).toBeVisible();
  expect(saves).toBe(0);
  await input.fill(JSON.stringify({...record, title: 'Fixture alterada'}));
  await expect(save).toHaveCount(0);
  await page.getByRole('button', {name: 'Conferir preview'}).click();
  await save.click();
  await expect(page.getByText('Rascunho salvo.', {exact: false})).toBeVisible();
  expect(saves).toBe(1);
  expect(saved).toEqual({record: previewed, preview_receipt: 'test-preview-receipt'});
});

test('rejected preview cannot save a draft', async ({page}) => {
  await page.route('**/api/commerce/admin', route => route.fulfill({json: {
    metrics: {events: {}, commission_feed_connected: false}, offers: [], jobs: [],
  }}));
  await page.route('**/api/commerce/admin/import/preview', route => route.fulfill({json: {
    accepted_count: 0, rejected_count: 1, rejected: [{index: 0, error_code: 'invalid_offer_fields'}],
  }}));
  await page.goto('/comprapulse/admin');
  await page.getByLabel('Registro JSON normalizado').fill('{}');
  await page.getByRole('button', {name: 'Conferir preview'}).click();
  await expect(page.getByText('Registro rejeitado:', {exact: false})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Confirmar e salvar rascunho'})).toHaveCount(0);
});

test('admin selects one CSV pilot without receiving commercial URLs', async ({page}) => {
  let saved: unknown;
  await page.route('**/api/commerce/admin', route => route.fulfill({json: {
    metrics: {events: {}, commission_feed_connected: false}, offers: [], jobs: [],
    official_adapter_connected: true,
  }}));
  await page.route('**/api/commerce/admin/import/preview-csv', route => route.fulfill({json: {
    row_index: 7, candidate: {product_id: '1:2', title: 'Piloto oficial',
      category: 'Casa', price_cents: 1990, observed_at: 1800000000, expires_at: 1800003600},
    image_present: true, preview_receipt: 'csv-preview-receipt', persisted: false, published: false,
  }}));
  await page.route('**/api/commerce/admin/import/csv', async route => {
    saved = route.request().postDataJSON();
    await route.fulfill({status: 201, json: {offer_id: 1, created: true}});
  });
  await page.goto('/comprapulse/admin');
  await page.getByLabel('Linha do export').fill('7');
  await page.getByRole('button', {name: 'Conferir piloto'}).click();
  await expect(page.getByText('Piloto oficial')).toBeVisible();
  await expect(page.getByText(/R\$\s*19,90/)).toBeVisible();
  await page.getByRole('button', {name: 'Salvar piloto como rascunho'}).click();
  await expect(page.getByText('Piloto salvo como rascunho.', {exact: false})).toBeVisible();
  expect(saved).toEqual({row_index: 7, preview_receipt: 'csv-preview-receipt'});
});

test('technical evidence keeps tracking and publication blocked', async ({page}) => {
  await page.route('**/api/commerce/admin', route => route.fulfill({json: {
    metrics: {events: {}, commission_feed_connected: false}, jobs: [],
    official_adapter_connected: false, technical_verifier_enabled: true,
    offers: [{id: 12, title: 'Piloto oficial', status: 'draft',
      reason: 'verification_required', expires_at: 1800003600}],
  }}));
  await page.route('**/api/commerce/admin/offers/12/verify-technical', route => route.fulfill({json: {
    offer_id: 12, status: 'REVIEW_REQUIRED', destination_matches: true,
    image_valid: true, stock_valid: false, tracking_verified: false,
    publishable: false, reason: 'tracking_and_stock_unconfirmed',
  }}));
  await page.goto('/comprapulse/admin');
  await page.getByRole('button', {name: 'Verificar destino e imagem'}).click();
  await expect(page.getByText('Destino e imagem passaram.', {exact: false})).toBeVisible();
  await expect(page.getByText('tracking continuam pendentes', {exact: false})).toBeVisible();
});

test('premium storefront renders only validated catalog data', async ({page}) => {
  await page.route('**/api/commerce/catalog', route => route.fulfill({json: {items: [{
    offer_id: 21, product_id: '1:2', title: 'Produto oficial de teste', category: 'Casa',
    price_cents: 1990, image_url: '/og-cover.png',
    affiliate_url: 'https://shope.ee/test-only', observed_at: 1800000000,
    expires_at: 4102444800,
  }]}}));
  await page.goto('/comprapulse');
  await expect(page.getByRole('heading', {name: 'Comprar bem começa por uma oferta que foi conferida.'})).toBeVisible();
  await expect(page.getByText('1 oferta ativa')).toBeVisible();
  await expect(page.getByRole('button', {name: 'Casa'})).toBeVisible();
  await expect(page.getByText('Produto oficial de teste')).toBeVisible();
  await expect(page.getByText(/R\$\s*19,90/)).toBeVisible();
  await expect(page.getByRole('link', {name: 'Ver na Shopee'})).toHaveAttribute('href','https://shope.ee/test-only');
  await page.getByPlaceholder('O que você está procurando?').fill('não existe');
  await expect(page.getByText('Nenhuma oferta validada nesta seleção.')).toBeVisible();
});

for (const width of [360, 390, 430, 1440]) {
  test(`empty catalog fits viewport ${width}`, async ({page}) => {
    await page.setViewportSize({width, height: 900});
    await page.route('**/api/commerce/catalog', route => route.fulfill({json: {items: []}}));
    await page.goto('/comprapulse');
    await expect(page.getByText('Nenhuma oferta validada nesta seleção.')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await expect(page.getByRole('link', {name: 'Ver oferta na Shopee'})).toHaveCount(0);
  });
}
