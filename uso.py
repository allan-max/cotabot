"""Monitora o uso do plano Claude pelo robô e estima quantas cotações ainda cabem.

Como a estimativa é calculada
-----------------------------
O Claude Code informa duas coisas em cada rodada:
  1. o consumo EXATO da rodada, em dólar equivalente (total_cost_usd) — vem com centavos;
  2. a porcentagem usada de cada janela do plano (5 horas e semanal) — mas só em passos de 1%.

Medir "quantos % cada item gasta" direto pela porcentagem erra muito (um item de 2,4% aparece como 2% ou 3%).
Então o programa calibra uma taxa: quantos % da janela cada US$ 1 consome.
  - Itens cotados em sequência formam uma "corrente": a variação de % do começo do primeiro ao fim do último,
    dividida pelo custo somado da corrente. Na corrente, o erro de arredondamento de 1% vale uma vez só, e não
    um por item — por isso a taxa fica mais precisa a cada item.
  - % por item = custo médio por item × taxa.
  - Itens que cabem = (teto − uso atual) ÷ % por item.
A faixa (mínimo–máximo) mostra a margem de erro do arredondamento de 1% e encolhe conforme o robô cota mais.

Limite: a porcentagem é da conta inteira. Se você usar o Claude enquanto o robô cota, a taxa sobe um pouco.
"""
import json
import math
import threading
from datetime import datetime, timedelta
from pathlib import Path

ARQ = Path(__file__).parent / "uso.jsonl"
ULTIMOS = 30            # itens usados no custo médio por item
FOLGA_CORRENTE_S = 180  # intervalo máximo entre um item e o próximo para continuarem na mesma corrente
ERRO_LEITURA = 0.01     # a porcentagem vem em passos de 1%: ±0,5% em cada ponta da corrente
# Até onde o robô pode ir em cada janela (fração). A estimativa "cabem N itens" conta até esse teto.
TETO = {"five_hour": 0.70, "seven_day": 1.00}
_trava = threading.Lock()

# Última leitura do uso real da conta (vem de qualquer rodada do Claude Code: cotação ou consulta rápida).
atual = {"janelas": None, "lido_em": None}


def definir_atual(janelas):
    if janelas:
        atual["janelas"] = janelas
        atual["lido_em"] = datetime.now()


def idade_leitura_s():
    return (datetime.now() - atual["lido_em"]).total_seconds() if atual["lido_em"] else None


def registrar(reg):
    reg = {"data": datetime.now().isoformat(timespec="seconds"), **reg}
    with _trava, ARQ.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


def _ler():
    if not ARQ.exists():
        return []
    linhas = []
    for l in ARQ.read_text(encoding="utf-8").splitlines():
        try:
            linhas.append(json.loads(l))
        except ValueError:
            continue
    return linhas


def _valido(r):
    """Item que pesquisou de verdade (rodada sem navegador não serve de medida)."""
    return (r.get("status") == "pronto" and (r.get("custo_usd") or 0) > 0
            and ((r.get("sites_visitados") or 0) > 0 or (r.get("anuncios") or 0) > 0))


def _inicio_fim(r):
    fim = datetime.fromisoformat(r["data"])
    ini = datetime.fromisoformat(r["inicio"]) if r.get("inicio") else fim - timedelta(seconds=r.get("duracao_s") or 0)
    return ini, fim


def _correntes(registros, janela):
    """Agrupa itens seguidos (mesma janela, sem pausa longa). Devolve [(variação, custo, nº itens)]."""
    correntes, atual_c, fim_ant, reset_ant = [], None, None, None
    for r in registros:
        a, d = (r.get("antes") or {}).get(janela), (r.get("depois") or {}).get(janela)
        if not (_valido(r) and a and d and a.get("resetsAt") == d.get("resetsAt")):
            atual_c, fim_ant = None, None  # quebra a corrente
            continue
        ini, fim = _inicio_fim(r)
        continua = (atual_c is not None and reset_ant == a.get("resetsAt")
                    and (ini - fim_ant).total_seconds() <= FOLGA_CORRENTE_S)
        if continua:
            atual_c["fim"] = d["utilization"]
            atual_c["custo"] += r["custo_usd"]
            atual_c["n"] += 1
        else:
            atual_c = {"ini": a["utilization"], "fim": d["utilization"], "custo": r["custo_usd"], "n": 1}
            correntes.append(atual_c)
        fim_ant, reset_ant = fim, a.get("resetsAt")
    return [(max(0.0, c["fim"] - c["ini"]), c["custo"], c["n"]) for c in correntes]


def _taxa(registros, janela):
    """% da janela por US$ 1: (taxa, taxa_min, taxa_max, variação total medida, nº itens)."""
    cs = _correntes(registros, janela)
    custo = sum(c for _, c, _ in cs)
    if not cs or custo <= 0:
        return None
    var = sum(v for v, _, _ in cs)
    erro = ERRO_LEITURA * len(cs)
    return (var / custo, max(0.0, var - erro) / custo, (var + erro) / custo, var, sum(n for _, _, n in cs))


def _hora(ts):
    return datetime.fromtimestamp(ts).strftime("%d/%m %H:%M") if ts else None


def _cabem(livre, por_item):
    if por_item is None or por_item <= 0:
        return None
    return max(0, math.floor(livre / por_item))


def resumo():
    todos = _ler()
    validos = [r for r in todos if _valido(r)]
    recentes = validos[-ULTIMOS:]
    custo_item = sum(r["custo_usd"] for r in recentes) / len(recentes) if recentes else None
    janelas_atuais = atual["janelas"] or next((r["depois"] for r in reversed(todos) if r.get("depois")), {})
    out = {
        "lido_em": atual["lido_em"].strftime("%H:%M:%S") if atual["lido_em"] else None,
        "itens_medidos": len(validos),
        "itens_total": len(todos),
        "media_duracao_min": round(sum(r.get("duracao_s") or 0 for r in recentes) / len(recentes) / 60, 1) if recentes else None,
        "media_custo_usd": round(custo_item, 3) if custo_item else None,
        "media_passos": round(sum(r.get("passos") or 0 for r in recentes) / len(recentes)) if recentes else None,
        "janelas": {},
    }
    for janela, nome in (("five_hour", "Limite de 5 horas"), ("seven_day", "Limite semanal")):
        a = janelas_atuais.get(janela) or {}
        usado = a.get("utilization")
        teto = TETO[janela]
        info = {"nome": nome, "teto_pct": round(teto * 100),
                "usado_pct": round(usado * 100) if usado is not None else None,
                "renova": _hora(a.get("resetsAt")),
                "media_por_item_pct": None, "faixa_por_item_pct": None,
                "cabem_itens": None, "cabem_min": None, "cabem_max": None,
                "confianca": None, "medido_pct": None, "itens_calibracao": 0}
        t = _taxa(validos, janela)
        if t and custo_item and usado is not None:
            taxa, taxa_min, taxa_max, var, n = t
            livre = max(0.0, teto - usado)
            por_item, por_min, por_max = taxa * custo_item, taxa_min * custo_item, taxa_max * custo_item
            info.update(
                media_por_item_pct=round(por_item * 100, 2) if por_item > 0 else None,
                faixa_por_item_pct=[round(por_min * 100, 2), round(por_max * 100, 2)],
                cabem_itens=_cabem(livre, por_item),
                cabem_min=_cabem(livre, por_max),
                cabem_max=_cabem(livre, por_min),  # None = sem limite superior medido ainda
                medido_pct=round(var * 100),
                itens_calibracao=n,
                # quanto mais % medido de verdade, menor o peso do erro de 1% na leitura
                confianca="alta" if var >= 0.10 else "média" if var >= 0.04 else "baixa",
            )
        out["janelas"][janela] = info
    return out
