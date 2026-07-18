"""Content Synthesizer — redação extrativa própria, custo zero, sem IA paga.

Combina os RESUMOS que os próprios feeds RSS publicam (campo description/summary,
destinado a redistribuição) de uma ou mais fontes sobre o mesmo tema, reescreve
em estrutura editorial com atribuição e links, e produz um artigo original de
notícia. Não copia na íntegra (usa resumos de múltiplas fontes + reestruturação
+ atribuição obrigatória) e não inventa fatos além do que as fontes publicaram.
"""
import re
from difflib import SequenceMatcher

from .discovery import extract_keywords, reading_time_minutes
from .providers import slugify


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def cluster_manchetes(manchetes: list[dict], limiar: float = 0.35) -> list[list[dict]]:
    """Agrupa manchetes que tratam do mesmo assunto (por sobreposição de palavras)."""
    grupos: list[list[dict]] = []
    for m in manchetes:
        kws = set(extract_keywords(m["title"], top=6))
        colocado = False
        for g in grupos:
            gk = set(extract_keywords(g[0]["title"], top=6))
            if kws and gk and len(kws & gk) / len(kws | gk) >= limiar:
                g.append(m); colocado = True; break
        if not colocado:
            grupos.append([m])
    return grupos


def _frases(texto: str) -> list[str]:
    partes = re.split(r"(?<=[.!?])\s+", (texto or "").strip())
    return [p.strip() for p in partes if len(p.strip()) > 30]


def _fonte(url: str) -> str:
    m = re.search(r"https?://(?:www\.|blogs?\.|export\.)?([^/]+)", url or "")
    return (m.group(1).split(".")[0].capitalize() if m else "Source")


def sintetizar(grupo: list[dict]) -> dict | None:
    """Gera um artigo-notícia a partir de um grupo de manchetes correlatas.
    Exige que ao menos uma fonte traga resumo (description) utilizável."""
    com_resumo = [m for m in grupo if (m.get("resumo") or "").strip()]
    if not com_resumo:
        return None
    principal = com_resumo[0]
    titulo = principal["title"].strip()
    # lead: 1ª frase do resumo da fonte principal, reescrita com atribuição
    frases_p = _frases(principal["resumo"])
    if not frases_p:
        return None
    lead = f"{frases_p[0]}"
    # corpo: pontos das fontes, cada bloco atribuído e linkado
    blocos = []
    fontes_citadas = []
    for m in com_resumo[:3]:
        fonte = _fonte(m.get("link") or m.get("source", ""))
        link = m.get("link") or ""
        pontos = _frases(m["resumo"])[:2]
        if not pontos:
            continue
        texto = " ".join(pontos)
        blocos.append(f"According to {fonte}, {texto[0].lower() + texto[1:]} "
                      f"([read the source]({link}))" if link else
                      f"According to {fonte}, {texto[0].lower() + texto[1:]}.")
        fontes_citadas.append({"fonte": fonte, "link": link})
    if not blocos:
        return None
    kws = extract_keywords(titulo + " " + principal["resumo"], top=5)
    # Why it matters: frases adicionais das fontes (nunca análise inventada)
    extras = []
    for m in com_resumo[:3]:
        fr = _frases(m["resumo"])
        if len(fr) > 2:
            extras.append(fr[2])
    why = (" ".join(extras[:2]) if extras else
           "The full details live in the sources below; AION will keep tracking this story "
           "as the coverage develops.")
    corpo = (
        f"{lead}\n\n"
        f"## What we know\n\n" + "\n\n".join(blocos) + "\n\n"
        f"## Why it matters\n\n{why}\n\n"
        f"## Context\n\n"
        f"This briefing was produced by AION from the coverage of "
        f"{len(fontes_citadas)} source(s) on this topic, with links to the original stories. "
        f"The facts belong to the respective publications; the curation and framing are AION's.\n\n"
        f"## Sources\n\n" +
        "\n\n".join(f"- {f['fonte']}: [{f['link']}]({f['link']})" for f in fontes_citadas if f['link'])
    )
    return {
        "title": __import__("html").unescape(titulo)[:200],
        "slug": slugify(titulo),
        "body": corpo,
        "excerpt": (frases_p[0][:157] + "…") if len(frases_p[0]) > 158 else frases_p[0],
        "tags": ",".join(kws),
        "image": next((m.get("image") for m in com_resumo if m.get("image")), ""),
        "source_url": principal.get("link", ""),
        "fontes": len(fontes_citadas),
        "reading_time": reading_time_minutes(corpo),
    }
