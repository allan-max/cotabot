"""Gera um Word por item a partir de resultados/*.json, salvando em words/."""
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BASE = Path(__file__).parent
RESULTADOS = BASE / "resultados"
WORDS = BASE / "words"

ICONE = {"ok": "OK", "falha": "FALHA", "nao_informado": "NÃO INFORMADO"}
SECOES = [
    ("atende", "Atendem", RGBColor(0x1B, 0x7F, 0x3B)),
    ("verificar", "Verificar manualmente (falta informação no anúncio)", RGBColor(0xB2, 0x6A, 0x00)),
    ("nao_atende", "Não atendem", RGBColor(0xB0, 0x1E, 0x1E)),
]


def preco_num(p):
    """'R$ 4.654,05' -> 4654.05; sem preço vai para o fim."""
    try:
        return float(str(p).replace("R$", "").replace(".", "").replace(",", ".").strip())
    except ValueError:
        return float("inf")


def add_link(paragraph, url, texto):
    r_id = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    estilo = OxmlElement("w:rStyle")
    estilo.set(qn("w:val"), "Hyperlink")
    rpr.append(estilo)
    cor = OxmlElement("w:color")
    cor.set(qn("w:val"), "0563C1")
    rpr.append(cor)
    sub = OxmlElement("w:u")
    sub.set(qn("w:val"), "single")
    rpr.append(sub)
    run.append(rpr)
    t = OxmlElement("w:t")
    t.text = texto
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


def gerar(dados, destino):
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10.5)

    doc.add_heading(f"Cotação – item {dados.get('codigo', '')}", level=0)
    info = doc.add_paragraph()
    info.add_run("Site: ").bold = True
    info.add_run(f"{dados.get('site', '')}    ")
    info.add_run("Data: ").bold = True
    info.add_run(str(dados.get("data", "")))
    if dados.get("referencia"):
        info.add_run("    Referência do cliente: ").bold = True
        info.add_run(dados["referencia"])

    doc.add_heading("Descrição do cliente", level=2)
    doc.add_paragraph(dados.get("descricao", ""))

    if dados.get("bloqueado"):
        p = doc.add_paragraph()
        r = p.add_run("ATENÇÃO: o site bloqueou o acesso durante a cotação. O resultado pode estar incompleto.")
        r.bold = True
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW

    reqs = dados.get("requisitos", [])
    if reqs:
        doc.add_heading("Requisitos", level=2)
        tab = doc.add_table(rows=1, cols=2)
        tab.style = "Light Grid Accent 1"
        tab.rows[0].cells[0].text = "Campo"
        tab.rows[0].cells[1].text = "Valor"
        for r in reqs:
            c = tab.add_row().cells
            c[0].text = str(r.get("campo", ""))
            c[1].text = str(r.get("valor", ""))

    if dados.get("buscas"):
        doc.add_paragraph().add_run("Buscas feitas: ").bold = True
        doc.paragraphs[-1].add_run(" · ".join(dados["buscas"]))

    anuncios = dados.get("anuncios", [])
    for chave, titulo, cor in SECOES:
        grupo = sorted((a for a in anuncios if a.get("status") == chave), key=lambda a: preco_num(a.get("preco")))
        h = doc.add_heading(f"{titulo} ({len(grupo)})", level=1)
        for run in h.runs:
            run.font.color.rgb = cor
        if not grupo:
            doc.add_paragraph().add_run("Nenhum anúncio.").italic = True
            continue
        for a in grupo:
            p = doc.add_paragraph(style="List Number")
            r = p.add_run(a.get("titulo", "(sem título)"))
            r.bold = True
            if a.get("referencia_exata"):
                tag = p.add_run("  [MODELO DE REFERÊNCIA]")
                tag.bold = True
                tag.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN
            p.add_run(f"\nPreço: {a.get('preco') or 'não encontrado'}\n")
            add_link(p, a.get("url", ""), a.get("url", ""))
            if a.get("motivo"):
                m = doc.add_paragraph()
                m.paragraph_format.left_indent = Pt(18)
                m.add_run("Motivo: ").bold = True
                m.add_run(a["motivo"])
            pend = [x for x in a.get("requisitos", []) if x.get("resultado") != "ok"]
            for x in pend:
                d = doc.add_paragraph(style="List Bullet 2")
                d.add_run(f"{x.get('campo')}: {ICONE.get(x.get('resultado'), x.get('resultado'))}")
                if x.get("encontrado"):
                    d.add_run(f" (anúncio: {x['encontrado']})")

    doc.save(destino)


def main():
    WORDS.mkdir(exist_ok=True)
    arquivos = sorted(RESULTADOS.glob("*.json"))
    if not arquivos:
        print("Nenhum resultado em resultados\\*.json")
        return 1
    for arq in arquivos:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        destino = WORDS / f"{arq.stem}.docx"
        try:
            gerar(dados, destino)
        except PermissionError:
            print(f"ERRO: feche o arquivo {destino.name} no Word e rode de novo.")
            continue
        print(f"Gerado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
