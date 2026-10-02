import React, { useState } from 'react';
import { api } from '../lib/api';

type Preview = { record: Record<string, any>; accepted: boolean; errors: string[]; receipt: string };
type CsvCandidate = { row_index: number; preview_receipt: string; candidate: {
  product_id: string; title: string; category: string; price_cents: number;
  observed_at: number; expires_at: number;
} };

const brl = (c: number) => new Intl.NumberFormat('pt-BR', {
  style: 'currency', currency: 'BRL',
}).format(c / 100);

export function CsvPilotPreview({ enabled, onSaved }: {
  enabled: boolean; onSaved: () => Promise<unknown>;
}) {
  const [rowIndex, setRowIndex] = useState('0');
  const [preview, setPreview] = useState<CsvCandidate | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function inspect() {
    setBusy(true); setMessage(''); setPreview(null);
    try {
      const result = await api('/api/commerce/admin/import/preview-csv', {
        method: 'POST', body: JSON.stringify({ row_index: Number(rowIndex) }),
      });
      setPreview(result);
    } catch {
      setMessage('A linha não existe, está inválida ou o export perdeu a validade.');
    } finally { setBusy(false); }
  }

  async function save() {
    if (!preview || busy) return;
    setBusy(true); setMessage('');
    try {
      await api('/api/commerce/admin/import/csv', { method: 'POST', body: JSON.stringify({
        row_index: preview.row_index, preview_receipt: preview.preview_receipt,
      }) });
      setPreview(null);
      setMessage('Piloto salvo como rascunho. Link, imagem e tracking ainda exigem validação.');
      await onSaved();
    } catch {
      setMessage('O export ou o recibo mudou/expirou. Faça um novo preview.');
    } finally { setBusy(false); }
  }

  return <section><h2>Selecionar piloto do CSV oficial</h2>
    {!enabled ? <p>Configure um export oficial fresco no servidor para habilitar esta etapa.</p> : <>
      <p>Escolha uma linha entre 0 e 499. A prévia não persiste nem publica a oferta.</p>
      <label>Linha do export<input type="number" min="0" max="499" value={rowIndex}
        onChange={e => { setRowIndex(e.target.value); setPreview(null); }} /></label>
      <button type="button" disabled={busy || rowIndex === ''} onClick={inspect}>Conferir piloto</button>
      {preview && <article className="cp-card cp-detail"><div className="cp-card-body">
        <small>{preview.candidate.category}</small><h2>{preview.candidate.title}</h2>
        <strong className="cp-price">{brl(preview.candidate.price_cents)}</strong>
        <p>ID oficial: {preview.candidate.product_id}</p>
        <p>A imagem e o link permanecem bloqueados até as validações técnicas.</p>
        <button type="button" disabled={busy} onClick={save}>Salvar piloto como rascunho</button>
      </div></article>}
    </>}
    {message && <p role="status">{message}</p>}
  </section>;
}

export function ImportPreview({ onSaved }: { onSaved: () => Promise<unknown> }) {
  const [input, setInput] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function inspect(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setPreview(null); setMessage('');
    try {
      const record = JSON.parse(input);
      const result = await api('/api/commerce/admin/import/preview', {
        method: 'POST', body: JSON.stringify({ records: [record] }),
      });
      const receipt = result.preview_receipts?.find((r: {index: number}) => r.index === 0)?.receipt ?? '';
      setPreview({ record,
        accepted: result.accepted_count === 1 && result.rejected_count === 0 && Boolean(receipt),
        errors: result.rejected.map((r: {error_code: string}) => r.error_code), receipt });
    } catch {
      setMessage('Não foi possível validar o registro. Confira o JSON e a origem oficial.');
    } finally { setBusy(false); }
  }

  async function save() {
    if (!preview?.accepted || busy) return;
    setBusy(true); setMessage('');
    try {
      await api('/api/commerce/admin/import', { method: 'POST', body: JSON.stringify({
        record: preview.record, preview_receipt: preview.receipt,
      }) });
      setPreview(null); setInput('');
      setMessage('Rascunho salvo. A oferta continua sem aprovação para publicação.');
      await onSaved();
    } catch {
      setPreview(null);
      setMessage('Não foi possível concluir a operação. Atualize o painel e faça um novo preview antes de tentar novamente.');
    } finally { setBusy(false); }
  }

  return <section>
    <h2>Importar registro oficial</h2>
    <p>Confira o preview antes de salvar. A validação de formato não comprova destino, imagem ou tracking.</p>
    <form onSubmit={inspect}>
      <label htmlFor="cp-import">Registro JSON normalizado</label>
      <textarea id="cp-import" value={input} disabled={busy} rows={9} required
        onChange={e => { setInput(e.target.value); setPreview(null); setMessage(''); }}/>
      <button disabled={busy}>{busy ? 'Processando…' : 'Conferir preview'}</button>
    </form>
    {message && <p role="status">{message}</p>}
    {preview && <div aria-label="Preview da importação">
      <p role="status">{preview.accepted ? 'Formato aceito — publicação bloqueada até verificação oficial.' : 'Registro rejeitado: ' + preview.errors.join(', ')}</p>
      {preview.accepted && <>
        <img src={preview.record.image_url} alt={preview.record.title} referrerPolicy="no-referrer" style={{maxWidth: '100%', width: 240}}/>
        <h3>{preview.record.title}</h3>
        <p>{new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'}).format(preview.record.price_cents / 100)}</p>
        <p>Categoria: {preview.record.category}</p>
        <p>Loja e desconto: não informados neste formato.</p>
        <p style={{overflowWrap: 'anywhere'}}>Produto: {preview.record.source_url}</p>
        <p style={{overflowWrap: 'anywhere'}}>Link afiliado: {preview.record.affiliate_url}</p>
        <p>Nenhum dado foi salvo pelo preview.</p>
        <button type="button" disabled={busy} onClick={save}>Confirmar e salvar rascunho</button>
      </>}
    </div>}
  </section>;
}
