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
