import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import './comprapulse.css';

type Offer={offer_id:number;product_id:string;title:string;category:string;price_cents:number;image_url:string;affiliate_url:string;expires_at:number;observed_at:number};
const brl=(c:number)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(c/100);
const date=(s:number)=>new Date(s*1000).toLocaleString('pt-BR');
function send(event_type:string, offer_id?:number, placement='catalog'){
  if(localStorage.getItem('cp_analytics_consent')!=='yes')return;
  const data=JSON.stringify({event_id:crypto.randomUUID(),event_type,offer_id,placement,consent:true});
  // The official destination is already the href; telemetry never rewrites or delays it.
  navigator.sendBeacon('/api/commerce/events',new Blob([data],{type:'application/json'}));
}
function Shell({children}:{children:React.ReactNode}){
  const [consent,setConsent]=useState(()=>localStorage.getItem('cp_analytics_consent'));
  useEffect(()=>{ document.documentElement.lang='pt-BR'; document.title='CompraPulse — Ofertas Shopee';
    let meta=document.querySelector('meta[name="robots"]'); if(!meta){meta=document.createElement('meta');meta.setAttribute('name','robots');document.head.appendChild(meta)}
    meta.setAttribute('content','noindex,nofollow');
  },[]);
  return <div className="cp"><header className="cp-header"><Link className="cp-logo" to="/comprapulse">Compra<span>Pulse</span></Link><nav><Link to="/comprapulse">Explorar ofertas</Link><Link to="/comprapulse/admin">Painel</Link></nav></header>{children}<footer>Podemos receber comissão pelas compras feitas pelos nossos links. Preço, frete e disponibilidade devem ser confirmados na Shopee.</footer>{!consent&&<div className="cp-consent"><span>Permitir a contagem anônima de visitas e cliques para melhorar nossa seleção?</span><button onClick={()=>{localStorage.setItem('cp_analytics_consent','no');setConsent('no')}}>Recusar</button><button onClick={()=>{localStorage.setItem('cp_analytics_consent','yes');setConsent('yes')}}>Permitir</button></div>}</div>
}
function OfferCard({o,detail=false}:{o:Offer;detail?:boolean}){
  const [broken,setBroken]=useState(false); const [expired,setExpired]=useState(o.expires_at*1000<=Date.now());
  useEffect(()=>{const id=setTimeout(()=>setExpired(true),Math.max(0,o.expires_at*1000-Date.now()));return()=>clearTimeout(id)},[o.expires_at]);
  if(broken||expired)return null;
  return <article className={'cp-card '+(detail?'cp-detail':'')}><Link to={'/comprapulse/produto/'+o.offer_id}><img src={o.image_url} alt={o.title} loading="lazy" onError={()=>setBroken(true)} /></Link><div className="cp-card-body"><small>{o.category}</small><h2><Link to={'/comprapulse/produto/'+o.offer_id}>{o.title}</Link></h2><strong className="cp-price">{brl(o.price_cents)}</strong><p className="cp-time">Preço consultado em {date(o.observed_at)}</p><a className="cp-cta" href={o.affiliate_url} rel="sponsored noopener noreferrer" target="_blank" onClick={e=>{if(o.expires_at*1000<=Date.now()){e.preventDefault();setExpired(true);return}send('merchant_click',o.offer_id,detail?'product':'catalog')}}>Ver oferta na Shopee</a></div></article>
}
export default function CompraPulse(){
  const {id}=useParams(); const [items,setItems]=useState<Offer[]>([]); const [q,setQ]=useState('');const [category,setCategory]=useState('');const [status,setStatus]=useState('loading');
  useEffect(()=>{let live=true; const refresh=()=>api('/api/commerce/catalog').then(r=>{if(live){setItems(r.items);setStatus('ok')}}).catch(()=>{if(live){setItems([]);setStatus('error')}});refresh();const timer=setInterval(refresh,60000);return()=>{live=false;clearInterval(timer)}},[]);
  useEffect(()=>{send(id?'product_view':'landing_view',id?Number(id):undefined,id?'product':'catalog')},[id]);
  const filtered=items.filter(o=>(!id||String(o.offer_id)===id)&&(!category||o.category===category)&&o.title.toLocaleLowerCase().includes(q.toLocaleLowerCase()));
  return <Shell><main><div className="cp-heading"><span className="cp-eyebrow">SELEÇÃO SHOPEE</span><h1>{id?'Confira a oferta.':'O que está vendendo mais, pelo melhor preço.'}</h1><p>Produtos reais, links verificados e preços com data de consulta.</p></div>{!id&&<div className="cp-search"><label>O que você procura?<input placeholder="Buscar produto" value={q} onChange={e=>setQ(e.target.value)}/></label><label>Categoria<select value={category} onChange={e=>{setCategory(e.target.value);send('category_view',undefined,'category')}}><option value="">Todas</option>{[...new Set(items.map(o=>o.category))].map(c=><option key={c}>{c}</option>)}</select></label></div>}<div className="cp-section-head"><h2>{id?'Detalhes':'Ofertas verificadas'}</h2><span>{filtered.length} {filtered.length===1?'oferta':'ofertas'}</span></div>{status==='loading'?<p role="status">Consultando ofertas…</p>:status==='error'?<div className="cp-empty" role="status"><h2>Catálogo temporariamente indisponível</h2><p>Não foi possível confirmar as ofertas. Tente novamente mais tarde.</p></div>:filtered.length===0?<div className="cp-empty"><h2>{id?'Esta oferta não está disponível.':'Nenhuma oferta validada nesta seleção.'}</h2><p>Uma oferta só aparece depois da verificação de preço, imagem e link oficial.</p>{id&&<Link to="/comprapulse">Explorar ofertas disponíveis</Link>}</div>:<div className="cp-grid">{filtered.map(o=><OfferCard key={o.offer_id} o={o} detail={!!id}/>)}</div>}</main></Shell>
}
export function CompraPulseAdmin(){
  const [data,setData]=useState<any>(null);const [error,setError]=useState('');const [input,setInput]=useState('');const [busy,setBusy]=useState(false);
  const refresh=()=>api('/api/commerce/admin').then(setData).catch(()=>setError('Entre com uma conta administradora. O módulo CompraPulse também precisa estar habilitado.'));
  useEffect(()=>{refresh()},[]);
  return <Shell><main><div className="cp-heading"><span className="cp-eyebrow">OPERAÇÃO</span><h1>Painel CompraPulse</h1><p>Validações, fila de trabalho e resultados registrados.</p></div>{error&&<p role="alert">{error} <Link to="/login">Entrar</Link></p>}{data&&<><div className="cp-metrics">{[['Visitas',data.metrics.events.landing_view??0],['Cliques para Shopee',data.metrics.events.merchant_click??0],['Comissão aprovada',data.metrics.commission_feed_connected?brl(data.metrics.approved_commission_cents):'Não conectada'],['Lucro líquido',data.metrics.commission_feed_connected?brl(data.metrics.net_profit_cents):'Não disponível']].map(([k,v])=><div key={k}><span>{k}</span><strong>{v}</strong></div>)}</div><h2>Saúde das ofertas</h2><div className="cp-table"><table><thead><tr><th>Produto</th><th>Status</th><th>Motivo</th><th>Validade</th></tr></thead><tbody>{data.offers.map((o:any)=><tr key={o.id}><td>{o.title}</td><td>{o.status}</td><td>{o.reason}</td><td>{date(o.expires_at)}</td></tr>)}</tbody></table></div><h2>Fila de trabalho</h2><div className="cp-table"><table><thead><tr><th>Job</th><th>Status</th><th>Tentativas</th><th>Erro</th></tr></thead><tbody>{data.jobs.map((j:any)=><tr key={j.id}><td>{j.job_type}</td><td>{j.status}</td><td>{j.attempt}</td><td>{j.error_code??'—'}</td></tr>)}</tbody></table></div><h2>Importar registro oficial</h2><p>O registro entra em rascunho. A importação não aprova nem publica o produto.</p><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{await api('/api/commerce/admin/import',{method:'POST',body:JSON.stringify(JSON.parse(input))});setInput('');await refresh()}catch{setError('Registro inválido. Confira o formato e a origem oficial dos dados.')}finally{setBusy(false)}}}><label htmlFor="cp-import">Registro JSON normalizado</label><textarea id="cp-import" value={input} onChange={e=>setInput(e.target.value)} rows={9} required/><button disabled={busy}>{busy?'Importando…':'Salvar rascunho'}</button></form></>}</main></Shell>
}
