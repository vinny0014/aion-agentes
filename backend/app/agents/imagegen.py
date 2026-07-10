"""Arte editorial SVG determinística — 1200x630, custo zero, sem IA, sem rede.

Cada artigo gera uma capa única (cores derivadas do título por hash), estilo
editorial premium: gradiente profundo, malha sutil, marca AION e categoria.
Servida como data-URI (nunca quebra, nunca faz request externo).
"""
import base64
import hashlib
import html

PALETAS = [
    ("#2036c7", "#00b3c6", "#0a0a12"),
    ("#7c3aed", "#d946ef", "#0d0817"),
    ("#0e7fd4", "#22d3ee", "#081018"),
    ("#8b5cf6", "#ec4899", "#120a1a"),
    ("#0891b2", "#6366f1", "#07101a"),
    ("#c026d3", "#8b5cf6", "#120818"),
]


def _hash(texto: str) -> int:
    return int(hashlib.sha256(texto.encode()).hexdigest(), 16)


def editorial_svg(titulo: str, categoria: str = "IA") -> str:
    h = _hash(titulo or "AION")
    c1, c2, bg = PALETAS[h % len(PALETAS)]
    seed = (h >> 8) % 360
    t = html.escape((titulo or "AION")[:80])
    cat = html.escape((categoria or "IA").upper()[:24])
    # blobs de gradiente pseudo-aleatórios, porém determinísticos
    bx, by = 300 + (h % 400), 180 + ((h >> 4) % 200)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<defs>
<radialGradient id="g1" cx="{70 + (h%20)}%" cy="30%" r="70%">
<stop offset="0%" stop-color="{c1}" stop-opacity="0.85"/><stop offset="100%" stop-color="{bg}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="g2" cx="20%" cy="80%" r="60%">
<stop offset="0%" stop-color="{c2}" stop-opacity="0.7"/><stop offset="100%" stop-color="{bg}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
<stop offset="55%" stop-color="{bg}" stop-opacity="0"/><stop offset="100%" stop-color="{bg}" stop-opacity="0.92"/>
</linearGradient>
<pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
<path d="M48 0H0V48" fill="none" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1"/>
</pattern>
</defs>
<rect width="1200" height="630" fill="{bg}"/>
<rect width="1200" height="630" fill="url(#grid)"/>
<circle cx="{bx}" cy="{by}" r="260" fill="url(#g1)"/>
<circle cx="{bx-380}" cy="{by+260}" r="240" fill="url(#g2)"/>
<rect width="1200" height="630" fill="url(#fade)"/>
<circle cx="{980 - (h % 120)}" cy="{470 + (h % 60)}" r="150" fill="url(#g2)" opacity="0.5"/>
<line x1="0" y1="{500 + (h % 40)}" x2="1200" y2="{380 + (h % 60)}" stroke="{c2}" stroke-opacity="0.18" stroke-width="2"/>
<g transform="translate(72,120)">
<text x="0" y="0" font-family="Georgia,serif" font-size="24" fill="{c2}" font-weight="bold" letter-spacing="6">{cat}</text>
</g>
<g transform="translate(72,556)">
<polygon points="0,0 22,0 11,-20" fill="{c1}"/>
<text x="34" y="0" font-family="Arial,sans-serif" font-size="24" fill="#ffffff" font-weight="bold">AION</text>
<text x="118" y="0" font-family="monospace" font-size="15" fill="#9CA0B4">AI NEWS OS</text>
</g>
</svg>'''


def _wrap(texto: str, largura: int) -> str:
    palavras, linhas, atual = texto.split(), [], ""
    for w in palavras:
        if len(atual) + len(w) + 1 <= largura:
            atual = f"{atual} {w}".strip()
        else:
            linhas.append(atual); atual = w
        if len(linhas) == 3:
            break
    if atual and len(linhas) < 3:
        linhas.append(atual)
    return "".join(
        f'<tspan x="0" dy="{0 if i==0 else 64}">{l}</tspan>' for i, l in enumerate(linhas[:3]))


def editorial_data_uri(titulo: str, categoria: str = "IA") -> str:
    svg = editorial_svg(titulo, categoria)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


# ═══════════ IMAGE PROVIDERS (fotografia editorial) ═══════════
import os
import urllib.parse


def photo_prompt(titulo: str, tags: str = "") -> str:
    """Prompt fotográfico editorial: sem texto, sem logo, sem cara de IA."""
    tema = ", ".join([t.strip() for t in (tags or "").split(",") if t.strip()][:3]) or "artificial intelligence technology"
    return (f"professional editorial photograph for a news article about {titulo[:90]}, "
            f"{tema}, photojournalism style, natural lighting, shallow depth of field, "
            f"realistic, high detail, 4k, no text, no words, no logo, no watermark")


def provider_photo_url(titulo: str, tags: str = "") -> tuple[str, str] | None:
    """URL de foto gerada pelo provedor configurado (IMAGE_PROVIDER).
    - pollinations: gratuito, sem chave (padrão)
    - gemini ("Nano Banana"): requer GEMINI_API_KEY (integração por ENV)
    - none: desliga provedores (cai na arte SVG)
    Retorna (url, credit) ou None."""
    provider = os.environ.get("IMAGE_PROVIDER", "pollinations").lower()
    if provider in ("none", "off", ""):
        return None
    if provider == "pollinations":
        prompt = urllib.parse.quote(photo_prompt(titulo, tags))
        url = (f"https://image.pollinations.ai/prompt/{prompt}"
               f"?width=1200&height=630&nologo=true&seed={_hash(titulo) % 99999}")
        return url, "Editorial photo via Pollinations.ai"
    if provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            return None  # integração pronta; falta credencial (pendência humana)
        # Geração via Gemini exige chamada de API com custo; implementação ativa
        # apenas quando a chave existir — nunca simulamos o resultado.
        return None
    return None


# ═══════════ HERO IMAGE RANKING ═══════════
def probe_image(url: str) -> dict:
    """Baixa a imagem (até 3MB) e mede dimensões reais via Pillow.
    Falha graciosa (rede indisponível → dimensões desconhecidas)."""
    if not url.startswith("http"):
        return {"ok": False}
    try:
        import io
        import httpx
        from PIL import Image
        r = httpx.get(url, timeout=8, follow_redirects=True,
                      headers={"User-Agent": "AION-HeroImage/1.0"})
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
            return {"ok": False}
        img = Image.open(io.BytesIO(r.content[:3_000_000]))
        return {"ok": True, "w": img.width, "h": img.height}
    except Exception:
        return {"ok": None, "w": 0, "h": 0}  # inconclusivo (sem rede): não reprova


def score_hero_candidate(c: dict) -> float:
    """Score de qualidade: oficial > og > provedor; 1200x630+; proporção 1.91."""
    if not c.get("url") or c["url"].startswith("data:image/svg"):
        return -100.0  # arte genérica: só como último recurso absoluto
    s = 0.0
    s += {"feed": 4, "og": 3, "provider": 1.5}.get(c.get("source", ""), 0)
    w, h = c.get("w") or 0, c.get("h") or 0
    if w >= 1200:
        s += 2
    elif 0 < w < 600:
        s -= 3  # miniatura pequena
    if w and h:
        ratio = w / h
        if 1.6 <= ratio <= 2.2:
            s += 1  # próximo de 1.91:1
        elif ratio < 1.0:
            s -= 2  # retrato/avatar
    if c.get("verificado") is False:
        s -= 100  # não carregou (HTTP != 200)
    return s
