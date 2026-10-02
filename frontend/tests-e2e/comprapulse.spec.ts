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
