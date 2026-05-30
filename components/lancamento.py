"""
View de Lançamento — formulário para cadastrar novas compras.
"""

from __future__ import annotations

import calendar as cal
from datetime import date
from typing import Callable

import flet as ft

from components.common import MoneyField, apply_money_mask
from db import db_execute
from state import AppState
from styles import BTN_PRIMARY, Colors, CATEGORIAS, format_real, parse_br_money


# ---------------------------------------------------------------------------
# Helper de data
# ---------------------------------------------------------------------------
def _add_months(source: date, months: int) -> date:
    """Adiciona N meses a uma data, ajustando o dia se necessário."""
    month = source.month - 1 + months
    year = source.year + month // 12
    month = month % 12 + 1
    day = min(source.day, cal.monthrange(year, month)[1])
    return date(year, month, day)


class LancamentoView(ft.Column):
    """Formulário de cadastro de nova compra com suporte a parcelamento."""

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
        self._selected_compra_date: list[date] = [date.today()]
        self._selected_venc_date: list[date] = [date.today()]
        self._build()

    # ------------------------------------------------------------------
    # Construção da view
    # ------------------------------------------------------------------
    def _build(self) -> None:
        # --- Descrição ---
        self._descricao = ft.TextField(
            label="Descrição da Compra",
            hint_text="Ex: Supermercado",
            border_radius=10,
        )

        # --- Local ---
        self._local = ft.TextField(
            label="Local da Compra",
            hint_text="Ex: Loja de compra",
            border_radius=10,
        )

        # --- Valor (com máscara monetária) ---
        self._valor_display = ft.TextField(
            label="Valor Total (R$)",
            hint_text="0,00",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_money_change,
            border_radius=10,
        )

        # --- Data da compra ---
        self._date_text = ft.Text(
            self._selected_compra_date[0].strftime("%d/%m/%Y"),
            size=15,
            weight=ft.FontWeight.BOLD,
        )
        self._date_picker = ft.DatePicker(
            on_change=self._on_date_change,
            first_date=date(date.today().year - 2, 1, 1),
            last_date=date(date.today().year + 5, 12, 31),
            help_text="dd/mm/aaaa",
            field_label_text="Data",
            cancel_text="Cancelar",
            confirm_text="OK",
        )

        date_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=Colors.ACCENT_300),
                    self._date_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=lambda _: self._date_picker.pick_date(),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=12,
            border_radius=10,
        )

        # --- Categoria ---
        self._categoria = ft.Dropdown(
            label="Categoria",
            hint_text="Selecione...",
            options=[ft.dropdown.Option(c["nome"]) for c in CATEGORIAS],
            border_radius=10,
        )

        # --- Método de pagamento ---
        self._metodo = ft.Dropdown(
            label="Método de Pagamento",
            hint_text="Selecione...",
            options=[
                ft.dropdown.Option("Pix"),
                ft.dropdown.Option("Débito"),
                ft.dropdown.Option("Crédito"),
            ],
            value="Pix",
            on_change=lambda _: self._toggle_credit(),
            border_radius=10,
        )

        # --- Parcelamento (Crédito) ---
        self._num_parcelas = ft.TextField(
            label="Número de Parcelas",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            on_change=lambda _: self._update_preview(),
        )

        # --- Primeiro vencimento ---
        self._venc_text = ft.Text(
            self._selected_venc_date[0].strftime("%d/%m/%Y"),
            size=15,
            weight=ft.FontWeight.BOLD,
        )
        self._venc_picker = ft.DatePicker(
            on_change=self._on_venc_change,
            first_date=date(date.today().year - 2, 1, 1),
            last_date=date(date.today().year + 5, 12, 31),
            help_text="dd/mm/aaaa",
            field_label_text="Vencimento",
            cancel_text="Cancelar",
            confirm_text="OK",
        )
        venc_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=Colors.ACCENT_300),
                    self._venc_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=lambda _: self._venc_picker.pick_date(),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=12,
            border_radius=10,
        )

        self._preview_text = ft.Text(
            "Valor de cada parcela: R$ 0,00",
            size=13,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.INDIGO_200,
        )
        self._preview_container = ft.Container(
            content=self._preview_text,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.INDIGO),
            border=ft.Border.all(
                1, ft.Colors.with_opacity(0.3, ft.Colors.INDIGO)
            ),
            border_radius=10,
            padding=12,
            alignment=ft.Alignment.CENTER,
            visible=False,
        )

        self._parcelamento_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    "Nº Parcelas",
                                    size=12,
                                    color=ft.Colors.GREY_400,
                                ),
                                self._num_parcelas,
                            ],
                            expand=1,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    "1º Vencimento",
                                    size=12,
                                    color=ft.Colors.GREY_400,
                                ),
                                venc_btn,
                            ],
                            expand=2,
                        ),
                    ],
                    spacing=10,
                ),
                self._preview_container,
            ],
            spacing=10,
            visible=False,
        )

        # --- Observação ---
        self._observacao = ft.TextField(
            label="Observações",
            hint_text="Opcional",
            multiline=True,
            min_lines=2,
            border_radius=10,
        )

        # --- Botão salvar ---
        save_btn = ft.ElevatedButton(
            text="Salvar Lançamento",
            icon=ft.Icons.SAVE,
            style=BTN_PRIMARY,
            height=48,
            on_click=self._salvar,
        )

        # --- Layout final ---
        self.controls = [
            ft.Text("Custo Variável", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            self._descricao,
            self._local,
            self._valor_display,
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Data da Compra",
                                size=12,
                                color=ft.Colors.GREY_400,
                            ),
                            date_btn,
                        ],
                        expand=1,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Pagamento",
                                size=12,
                                color=ft.Colors.GREY_400,
                            ),
                            self._metodo,
                        ],
                        expand=1,
                    ),
                ],
                spacing=10,
            ),
            self._categoria,
            self._parcelamento_section,
            self._observacao,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            save_btn,
        ]
        self.spacing = 14
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

        # Adiciona date pickers ao overlay da página (será feito pelo main)
        self._overlays: list[ft.Control] = [self._date_picker, self._venc_picker]

    @property
    def overlays(self) -> list[ft.Control]:
        """Date pickers que devem ser adicionados ao page.overlay."""
        return self._overlays

    # ------------------------------------------------------------------
    # Handlers de entrada
    # ------------------------------------------------------------------
    def _on_money_change(self, e: ft.ControlEvent) -> None:
        """Máscara monetária dinâmica no campo de valor."""
        apply_money_mask(e)
        self._update_preview()

    def _on_date_change(self, e: ft.ControlEvent) -> None:
        """Atualiza a data da compra e ajusta vencimento se não for crédito."""
        self._selected_compra_date[0] = e.control.value.date()
        self._date_text.value = self._selected_compra_date[0].strftime("%d/%m/%Y")
        self._date_text.update()

        if self._metodo.value != "Crédito":
            self._selected_venc_date[0] = self._selected_compra_date[0]
            self._venc_text.value = self._selected_venc_date[0].strftime("%d/%m/%Y")
            self._venc_text.update()

    def _on_venc_change(self, e: ft.ControlEvent) -> None:
        """Atualiza a data do primeiro vencimento."""
        self._selected_venc_date[0] = e.control.value.date()
        self._venc_text.value = self._selected_venc_date[0].strftime("%d/%m/%Y")
        self._venc_text.update()

    # ------------------------------------------------------------------
    # Lógica de parcelamento
    # ------------------------------------------------------------------
    def _toggle_credit(self) -> None:
        """Mostra/esconde campos de parcelamento conforme método de pagamento."""
        is_credit = self._metodo.value == "Crédito"
        self._parcelamento_section.visible = is_credit

        if not is_credit:
            self._num_parcelas.value = "1"
            self._selected_venc_date[0] = self._selected_compra_date[0]
            self._venc_text.value = self._selected_venc_date[0].strftime("%d/%m/%Y")
        else:
            proximo = _add_months(self._selected_compra_date[0], 1)
            self._selected_venc_date[0] = proximo
            self._venc_text.value = proximo.strftime("%d/%m/%Y")

        self._update_preview()
        self._parcelamento_section.update()
        self._venc_text.update()

    def _update_preview(self) -> None:
        """Atualiza o texto de prévia do valor da parcela."""
        if not self._valor_display.value:
            self._preview_container.visible = False
            self._preview_container.update()
            return

        try:
            valor_total = parse_br_money(self._valor_display.value)
            parcelas = int(self._num_parcelas.value) if self._num_parcelas.value else 1

            if parcelas > 1:
                v_parcela = valor_total / parcelas
                self._preview_text.value = (
                    f"Valor da parcela: {parcelas}x de {format_real(v_parcela)}"
                )
                self._preview_container.visible = True
            else:
                self._preview_container.visible = False
        except (ValueError, TypeError):
            self._preview_container.visible = False

        self._preview_container.update()

    # ------------------------------------------------------------------
    # Salvar compra
    # ------------------------------------------------------------------
    def _salvar(self, _: ft.ControlEvent) -> None:
        """Valida campos, insere compra + parcelas no banco."""
        if not self._descricao.value:
            self._show_toast("Por favor, informe a descrição.", is_error=True)
            return
        if not self._valor_display.value:
            self._show_toast("Por favor, informe o valor.", is_error=True)
            return
        if not self._categoria.value:
            self._show_toast("Por favor, selecione uma categoria.", is_error=True)
            return

        try:
            valor_total = parse_br_money(self._valor_display.value)
            desc = self._descricao.value
            local = self._local.value or None
            cat = self._categoria.value
            metodo = self._metodo.value
            num_p = int(self._num_parcelas.value) if self._num_parcelas.value else 1

            # Inserir compra
            compra_id = db_execute(
                """
                INSERT INTO compras
                    (descricao, valor_total, categoria,
                     metodo_pagamento, num_parcelas,
                     valores_parcelas, local)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (desc, valor_total, cat, metodo, num_p, None, local),
            )

            # Gerar parcelas (uma por vez para crédito)
            first_venc = self._selected_venc_date[0]
            if num_p <= 1:
                paga = 0
                db_execute(
                    """
                    INSERT INTO parcelas
                        (compra_id, num_parcela, valor_parcela,
                         data_vencimento, paga)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (compra_id, 1, valor_total, first_venc.strftime("%Y-%m-%d"), paga),
                )
            else:
                valor_base = round(valor_total / num_p, 2)
                diferenca = round(valor_total - (valor_base * num_p), 2)

                # Gera a lista de valores de todas as parcelas
                valores_futuros: list[float] = []
                for i in range(num_p):
                    vp = valor_base
                    if i == num_p - 1:
                        vp = round(valor_base + diferenca, 2)
                    valores_futuros.append(vp)

                # Armazena os valores futuros como JSON
                import json
                db_execute(
                    "UPDATE compras SET valores_parcelas = ? WHERE id = ?",
                    (json.dumps(valores_futuros), compra_id),
                )

                # Cria apenas a primeira parcela
                venc = first_venc.strftime("%Y-%m-%d")
                db_execute(
                    """
                    INSERT INTO parcelas
                        (compra_id, num_parcela, valor_parcela,
                         data_vencimento, paga)
                    VALUES (?, ?, ?, ?, 0)
                    """,
                    (compra_id, 1, valores_futuros[0], venc),
                )

            self._show_toast("Lançamento adicionado com sucesso!")
            self._on_navigate(0)

        except Exception as ex:
            self._show_toast(f"Erro ao salvar: {ex}", is_error=True)
