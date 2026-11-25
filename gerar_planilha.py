"""Preenche a Planilha Base com o resultado do robô de cotação.

ORÇAMENTO
  linhas 2..25  -> A PRODUTO | B QUANTIDADE | C CUSTO (preço do anúncio escolhido, se houver)
  bloco ITEM n  -> linha 39 + 5*(n-1): "LOCAIS ORÇADOS" (fornecedores) e "VALORES" (preços), da coluna B em diante
COTAÇÃO
  por item: anúncio escolhido (fornecedor, link, preço), motivo da escolha, print e as outras opções
"""
from pathlib import Path

import openpyxl
from openpyxl.drawing.image import Image as XlImage
from openpyxl.styles import Alignment, Font, PatternFill
from PIL import Image

BASE = Path(__file__).parent
MODELO = BASE / "modelos" / "planilha_base_cotacao.xlsx"
SAIDA = BASE / "planilhas"
MAX_ITENS = 24
MAX_LOCAIS = 12  # colunas B..M de cada bloco ITEM
LARGURA_PRINT = 720  # px

AZUL = Font(color="0563C1", underline="single")
NEGRITO = Font(bold=True)
TITULO = Font(bold=True, size=13, color="FFFFFF")
FUNDO_TITULO = PatternFill("solid", fgColor="1F4E79")
FUNDO_ESCOLHIDO = PatternFill("solid", fgColor="E2EFDA")
QUEBRA = Alignment(wrap_text=True, vertical="top")


def _numero(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("R$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _tipo(a):
    """'distribuidor · google · contato: (27) 9999-9999'"""
    partes = [a.get("tipo_site"), a.get("origem")]
    if a.get("contato"):
        partes.append("contato: " + str(a["contato"]))
    return " · ".join(str(p) for p in partes if p)


def _link(cel, url, texto=None):
    if url and str(url).startswith(("http://", "https://")):
        cel.value = texto or url
        cel.hyperlink = url
        cel.font = AZUL
    else:
        cel.value = texto or url or ""


def _print(ws, caminho, ancora, pasta_tmp):
    """Coloca o print reduzido na aba. Devolve quantas linhas ele ocupa (aprox.)."""
    p = Path(caminho or "")
    if not caminho or not p.is_file():
        return 0
    try:
        with Image.open(p) as im:
            im = im.convert("RGB")
            if im.width > LARGURA_PRINT:
                im = im.resize((LARGURA_PRINT, int(im.height * LARGURA_PRINT / im.width)))
            pasta_tmp.mkdir(parents=True, exist_ok=True)
            destino = pasta_tmp / f"{p.stem}_{ancora}.png"
            im.save(destino)
            altura = im.height
    except Exception:  # noqa: BLE001 - print ruim não pode derrubar a planilha
        return 0
    ws.add_image(XlImage(str(destino)), ancora)
    return altura // 20 + 2  # ~20 px por linha


def gerar(tarefa):
    """tarefa = dict salvo pelo cotabot_local. Devolve o caminho do .xlsx gerado."""
    wb = openpyxl.load_workbook(MODELO)
    orc = wb["ORÇAMENTO"]
    cot = wb["COTAÇÃO"] if "COTAÇÃO" in wb.sheetnames else wb.create_sheet("COTAÇÃO")
    tmp = SAIDA / f"_prints_{tarefa['id']}"

    cot.column_dimensions["A"].width = 22
    cot.column_dimensions["B"].width = 60
    cot.column_dimensions["C"].width = 28
    cot.column_dimensions["D"].width = 50
    cot.column_dimensions["E"].width = 40
    cot["A1"] = f"COTAÇÃO DO EVENTO {tarefa.get('evento') or ''}".strip()
    cot["A1"].font = Font(bold=True, size=15)
    cot["A2"] = "Sites: " + (", ".join(tarefa.get("sites") or []) or "padrão (9 fornecedores da cote-para-mim + Google)")
    linha = 4

    for item in tarefa["itens"][:MAX_ITENS]:
        n = item["numero"]
        r = item.get("resultado") or {}
        anuncios = r.get("anuncios") or []
        idx = r.get("escolhido")
        escolhido = anuncios[idx] if isinstance(idx, int) and 0 <= idx < len(anuncios) else None

        # ---- ORÇAMENTO: linha do item ----
        lin = 1 + n
        orc[f"A{lin}"] = item["descricao"]
        orc[f"B{lin}"] = item.get("quantidade") or 1
        custo = _numero(escolhido.get("preco_numero")) if escolhido else None
        if custo is not None:
            orc[f"C{lin}"] = custo

        # ---- ORÇAMENTO: bloco ITEM n (locais e valores) ----
        topo = 39 + 5 * (n - 1)
        ordem = ([escolhido] if escolhido else []) + [a for a in anuncios if a is not escolhido]
        for col, a in enumerate(ordem[:MAX_LOCAIS], start=2):
            c_local = orc.cell(row=topo + 1, column=col)
            _link(c_local, a.get("link"), a.get("fornecedor"))
            valor = _numero(a.get("preco_numero"))
            orc.cell(row=topo + 2, column=col, value=valor if valor is not None else (a.get("preco") or ""))

        # ---- COTAÇÃO: seção do item ----
        cab = cot.cell(row=linha, column=1, value=f"ITEM {n}")
        cab.font, cab.fill = TITULO, FUNDO_TITULO
        desc = cot.cell(row=linha, column=2, value=item["descricao"])
        desc.font, desc.fill = Font(bold=True, color="FFFFFF"), FUNDO_TITULO
        desc.alignment = QUEBRA
        for col in (3, 4, 5):
            cot.cell(row=linha, column=col).fill = FUNDO_TITULO
        linha += 1

        if item.get("status") == "erro":
            cot.cell(row=linha, column=1, value="Erro").font = NEGRITO
            cot.cell(row=linha, column=2, value=item.get("erro", "")).alignment = QUEBRA
            linha += 2
            continue

        if escolhido:
            for rotulo, valor in (("Escolhido", f"{escolhido.get('fornecedor', '')} — {escolhido.get('titulo', '')}"),
                                  ("Tipo de site", _tipo(escolhido)),
                                  ("Preço", escolhido.get("preco", "")),
                                  ("Link", None),
                                  ("Motivo da escolha", r.get("motivo_escolha", ""))):
                cot.cell(row=linha, column=1, value=rotulo).font = NEGRITO
                c = cot.cell(row=linha, column=2)
                if rotulo == "Link":
                    _link(c, escolhido.get("link"))
                else:
                    c.value = valor
                    c.alignment = QUEBRA
                for col in (1, 2):
                    cot.cell(row=linha, column=col).fill = FUNDO_ESCOLHIDO
                linha += 1
            cot.cell(row=linha, column=1, value="Print").font = NEGRITO
            ocupadas = _print(cot, r.get("print"), f"B{linha}", tmp)
            if not ocupadas:
                cot.cell(row=linha, column=2, value="(sem print)")
            linha += max(ocupadas, 1) + 1
        else:
            cot.cell(row=linha, column=1, value="Escolhido").font = NEGRITO
            cot.cell(row=linha, column=2, value=r.get("motivo_escolha") or "Nenhum anúncio atendeu.").alignment = QUEBRA
            linha += 2

        outros = [a for a in anuncios if a is not escolhido]
        if outros:
            cot.cell(row=linha, column=1, value="Outras opções").font = NEGRITO
            for col, h in ((2, "Anúncio"), (3, "Preço"), (4, "Observação"), (5, "Tipo / origem / contato")):
                cot.cell(row=linha, column=col, value=h).font = NEGRITO
            linha += 1
            for a in outros:
                cot.cell(row=linha, column=1, value=a.get("fornecedor", ""))
                _link(cot.cell(row=linha, column=2), a.get("link"), a.get("titulo"))
                cot.cell(row=linha, column=3, value=a.get("preco", ""))
                cot.cell(row=linha, column=4, value=a.get("observacao", "")).alignment = QUEBRA
                cot.cell(row=linha, column=5, value=_tipo(a)).alignment = QUEBRA
                linha += 1
        for nf in r.get("nao_encontrado") or []:
            cot.cell(row=linha, column=1, value=nf.get("fornecedor", ""))
            cot.cell(row=linha, column=2, value="Não encontrado: " + str(nf.get("motivo", ""))).alignment = QUEBRA
            linha += 1
        linha += 2

    SAIDA.mkdir(exist_ok=True)
    nome = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(tarefa.get("evento") or tarefa["id"]))
    destino = SAIDA / f"planilha_base_cotacao_{nome}.xlsx"
    if destino.exists():
        destino = SAIDA / f"planilha_base_cotacao_{nome}_{tarefa['id'][:6]}.xlsx"
    wb.save(destino)
    return destino
