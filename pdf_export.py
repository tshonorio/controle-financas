"""
Exportação de extrato financeiro em PDF usando fpdf2.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from db import buscar_parcelas_extrato, buscar_parcelas_futuras
from styles import NOMES_MESES, format_real


def gerar_extrato_pdf(ano: int, mes: int, destino: str | Path) -> str:
    """Gera um PDF com o extrato completo do mês e salva em destino.

    Args:
        ano: Ano do extrato.
        mes: Mês do extrato (1-12).
        destino: Caminho onde salvar o PDF.

    Returns:
        Caminho do arquivo gerado.
    """
    rows = buscar_parcelas_extrato(ano, mes)
    total_mes = sum(r[4] for r in rows)
    total_pago = sum(r[4] for r in rows if r[6] == 1)
    total_pendente = total_mes - total_pago

    ultimo = monthrange(ano, mes)[1]
    futuros = buscar_parcelas_futuras(f"{ano:04d}-{mes:02d}-{ultimo:02d}")
    total_futuro = sum(r[0] for r in futuros)

    nome_mes = NOMES_MESES[mes]
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cabeçalho
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Extrato Financeiro", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"{nome_mes} de {ano}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Resumo
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Resumo do Mes", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    resumo = [
        ("Total do Mes:", format_real(total_mes)),
        ("Pago:", format_real(total_pago)),
        ("Pendente:", format_real(total_pendente)),
    ]
    if total_futuro > 0:
        resumo.append(("Comprometido (futuro):", format_real(total_futuro)))

    for label, valor in resumo:
        pdf.cell(90, 7, f"  {label}", new_x="END")
        pdf.cell(0, 7, valor, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Tabela de lançamentos
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Lancamentos Detalhados", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    col_w = [8, 52, 16, 24, 36, 24, 24]
    headers = ["#", "Descricao", "Parc", "Vencimento", "Valor", "Status", "Categoria"]

    # Cabeçalho da tabela
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(200, 200, 200)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, align="C", fill=True)
    pdf.ln()

    # Linhas
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(220, 220, 220)
    fill = False
    for idx, r in enumerate(rows):
        _, desc, n_p, tot_p, valor, venc_str, paga, cat, *_ = r[:9]
        venc = datetime.strptime(venc_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        parcela = f"{n_p}/{tot_p}"
        status = "Pago" if paga == 1 else "Pendente"
        linha = [
            str(idx + 1),
            desc[:28],
            parcela,
            venc,
            format_real(valor),
            status,
            cat[:10],
        ]

        if fill:
            pdf.set_fill_color(25, 25, 25)
        else:
            pdf.set_fill_color(18, 18, 18)

        for i, val in enumerate(linha):
            pdf.cell(col_w[i], 6, val, border=1, align="C" if i != 1 else "L", fill=True)
        pdf.ln()
        fill = not fill

    # Rodapé
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(120, 120, 120)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 5, f"Gerado em {agora}", align="C")

    pdf.output(str(destino))
    return str(destino)
