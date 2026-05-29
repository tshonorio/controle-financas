"""
View de Custos Fixos — formulário para cadastrar contas fixas mensais.
As parcelas geradas aparecem na aba Lançamentos para controle de pagamento.
"""

from __future__ import annotations

import calendar as cal
from datetime import date
from typing import Callable

import flet as ft

from components.common import apply_money_mask
from db import db_execute, inserir_custo_fixo
from state import AppState
from styles import BTN_PRIMARY, CATEGORIAS, Colors


def _add_months(source: date, months: int) -> date:
    month = source.month - 1 + months
    year = source.year + month // 12
    month = month % 12 + 1
    day = min(source.day, cal.monthrange(year, month)[1])
    return date(year, month, day)


class CustosFixosView(ft.Column):
    """Formulário para cadastrar custos fixos mensais."""

    def __init__(
        self,
        state: AppState,
        show_toast: Callable[[str], None],
        on_navigate: Callable[[int], None],
    ) -> None:
        super().__init__()
        self._state = state
        self._show_toast = show_toast
        self._on_navigate = on_navigate
        self._build()

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------
    def _build(self) -> None:
        self._descricao = ft.TextField(
            label="Descrição",
            hint_text="Ex: Aluguel",
            border_radius=10,
        )

        self._valor_display = ft.TextField(
            label="Valor (R$)",
            hint_text="0,00",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_money_change,
            border_radius=10,
        )

        self._dia = ft.TextField(
            label="Dia de vencimento",
            hint_text="05",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
        )

        self._categoria = ft.Dropdown(
            label="Categoria",
            hint_text="Selecione...",
            options=[ft.dropdown.Option(c["nome"]) for c in CATEGORIAS],
            border_radius=10,
        )

        self._metodo = ft.Dropdown(
            label="Método de Pagamento",
            hint_text="Selecione...",
            options=[
                ft.dropdown.Option("Pix"),
                ft.dropdown.Option("Débito"),
                ft.dropdown.Option("Crédito"),
            ],
            value="Pix",
            border_radius=10,
        )

        save_btn = ft.ElevatedButton(
            text="Adicionar Custo Fixo",
            icon=ft.icons.ADD_CIRCLE_OUTLINE,
            style=BTN_PRIMARY,
            height=48,
            on_click=self._salvar,
        )

        info = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.INFO_OUTLINE, size=16, color=Colors.ACCENT_300),
                            ft.Text("As parcelas geradas aparecem em Lançamentos.", size=12, color=Colors.GREY_400),
                        ],
                        spacing=6,
                    ),
                    ft.Text("O controle de pagamento é feito por lá.", size=12, color=Colors.GREY_400),
                ],
                spacing=2,
            ),
            padding=12,
            border_radius=10,
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[ft.colors.with_opacity(0.12, ft.colors.PINK_500), ft.colors.with_opacity(0.12, ft.colors.PURPLE_500)],
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.PINK_500)),
        )

        self.controls = [
            ft.Text("Custos Fixos", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Cadastre contas que se repetem mensalmente.", size=13, color=Colors.GREY_400),
            ft.Divider(height=8, color=ft.colors.TRANSPARENT),
            self._descricao,
            self._valor_display,
            self._dia,
            self._categoria,
            self._metodo,
            ft.Divider(height=6, color=ft.colors.TRANSPARENT),
            save_btn,
            ft.Divider(height=8, color=ft.colors.TRANSPARENT),
            info,
        ]
        self.spacing = 14
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_money_change(self, e: ft.ControlEvent) -> None:
        apply_money_mask(e)

    def _salvar(self, _: ft.ControlEvent) -> None:
        if not self._descricao.value:
            self._show_toast("Informe a descrição.", is_error=True)
            return
        if not self._valor_display.value:
            self._show_toast("Informe o valor.", is_error=True)
            return
        if not self._dia.value or not self._dia.value.isdigit():
            self._show_toast("Informe um dia válido (1-31).", is_error=True)
            return
        if not self._categoria.value:
            self._show_toast("Selecione uma categoria.", is_error=True)
            return

        try:
            valor = parse_br_money(self._valor_display.value)
            dia = int(self._dia.value)
            if dia < 1 or dia > 31:
                self._show_toast("Dia deve estar entre 1 e 31.", is_error=True)
                return

            desc = self._descricao.value.strip()
            cat = self._categoria.value
            metodo = self._metodo.value

            # Insere na tabela de definição de custos fixos
            cf_id = inserir_custo_fixo(desc, valor, dia, cat, metodo)

            # Cria uma compra para representar este custo fixo
            compra_id = db_execute(
                """
                INSERT INTO compras
                    (descricao, valor_total, categoria,
                     metodo_pagamento, num_parcelas)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"{desc} (fixo)", valor, cat, metodo, 1),
            )

            # Vencimento: próximo mês se o dia já passou este mês
            from calendar import monthrange
            primeiro_venc = date(hoje.year, hoje.month, min(dia, monthrange(hoje.year, hoje.month)[1]))
            if primeiro_venc <= hoje:
                primeiro_venc = _add_months(primeiro_venc, 1)
            venc_str = primeiro_venc.strftime("%Y-%m-%d")

            db_execute(
                """
                INSERT INTO parcelas
                    (compra_id, num_parcela, valor_parcela,
                     data_vencimento, paga, custo_fixo_id)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (compra_id, 1, valor, venc_str, cf_id),
            )

            self._show_toast(f"Custo fixo '{desc}' adicionado!")

            # Limpa os campos
            self._descricao.value = ""
            self._valor_display.value = ""
            self._dia.value = ""
            self._categoria.value = None
            self._metodo.value = "Pix"
            self.update()

            # Vai para Lançamentos
            self._on_navigate(0)

        except Exception as ex:
            self._show_toast(f"Erro ao salvar: {ex}", is_error=True)
