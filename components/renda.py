"""
View de Rendas — cadastro de renda fixa mensal e rendas variáveis.
"""

from __future__ import annotations

from datetime import date
from typing import Callable

import flet as ft

from db import (
    buscar_renda_fixa,
    buscar_rendas_variaveis,
    excluir_renda,
    inserir_renda_variavel,
    salvar_renda_fixa,
)
from components.common import apply_money_mask
from state import AppState
from styles import BTN_PRIMARY, BTN_SUCCESS, Colors, format_real, parse_br_money


class RendaView(ft.Column):
    """Formulário de renda fixa + listagem e cadastro de rendas variáveis."""

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

    def _build(self) -> None:
        renda_fixa = buscar_renda_fixa()

        # --- Renda Fixa ---
        self._fixa_desc = ft.TextField(
            label="Descrição",
            hint_text="Ex: Salário",
            value=renda_fixa[1] if renda_fixa else "Salário",
            border_radius=10,
        )

        self._fixa_valor = ft.TextField(
            label="Valor Mensal (R$)",
            hint_text="0,00",
            value=format_real(renda_fixa[2]) if renda_fixa else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_money_change_fixa,
            border_radius=10,
        )

        fixa_save = ft.ElevatedButton(
            text="Salvar Renda Fixa",
            icon=ft.icons.SAVE,
            style=BTN_SUCCESS,
            height=42,
            on_click=self._salvar_fixa,
        )

        fixa_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.ATTACH_MONEY, color=Colors.GREEN_400, size=22),
                            ft.Text("Renda Fixa Mensal", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    self._fixa_desc,
                    self._fixa_valor,
                    fixa_save,
                ],
                spacing=10,
            ),
            padding=16,
            border_radius=14,
            bgcolor=Colors.with_opacity(0.06, Colors.WHITE),
            border=ft.border.all(1, Colors.WHITE_10),
        )

        # --- Renda Variável ---
        self._var_desc = ft.TextField(
            label="Descrição",
            hint_text="Ex: Hora extra, PLR, freela",
            border_radius=10,
        )

        self._var_valor = ft.TextField(
            label="Valor (R$)",
            hint_text="0,00",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_money_change_var,
            border_radius=10,
        )

        self._var_data = ft.Text(
            date.today().strftime("%d/%m/%Y"),
            size=15,
            weight=ft.FontWeight.BOLD,
        )
        self._var_date_picker = ft.DatePicker(
            on_change=self._on_var_date_change,
            first_date=date(date.today().year - 2, 1, 1),
            last_date=date(date.today().year + 5, 12, 31),
        )

        var_data_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.CALENDAR_MONTH, color=Colors.ACCENT_300, size=18),
                    self._var_data,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            on_click=lambda _: self._var_date_picker.pick_date(),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=12,
            border_radius=10,
        )

        self._var_cat = ft.Dropdown(
            label="Categoria",
            options=[
                ft.dropdown.Option("Hora Extra"),
                ft.dropdown.Option("PLR"),
                ft.dropdown.Option("Freela"),
                ft.dropdown.Option("Comissão"),
                ft.dropdown.Option("Outros"),
            ],
            border_radius=10,
        )

        var_add = ft.ElevatedButton(
            text="Adicionar Renda Variável",
            icon=ft.icons.ADD_CIRCLE_OUTLINE,
            style=BTN_PRIMARY,
            height=42,
            on_click=self._adicionar_variavel,
        )

        var_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.TRENDING_UP, color=Colors.ACCENT_300, size=22),
                            ft.Text("Renda Variável", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    self._var_desc,
                    self._var_valor,
                    ft.Row(
                        [
                            ft.Column([ft.Text("Data", size=12, color=Colors.GREY_400), var_data_btn], expand=1),
                            ft.Column([ft.Text("Categoria", size=12, color=Colors.GREY_400), self._var_cat], expand=1),
                        ],
                        spacing=10,
                    ),
                    var_add,
                ],
                spacing=10,
            ),
            padding=16,
            border_radius=14,
            bgcolor=Colors.with_opacity(0.06, Colors.WHITE),
            border=ft.border.all(1, Colors.WHITE_10),
        )

        # --- Lista de rendas variáveis ---
        var_rows = buscar_rendas_variaveis()
        var_items: list[ft.Control] = []
        for r in var_rows:
            rid, rdesc, rvalor, rdata, rcat = r
            var_items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.icons.TRENDING_UP, size=16, color=Colors.GREEN_400),
                                bgcolor=Colors.with_opacity(0.15, Colors.GREEN),
                                border_radius=8,
                                padding=6,
                            ),
                            ft.Column(
                                [
                                    ft.Text(rdesc, size=14, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"{rdata} • {rcat}" if rcat else rdata, size=11, color=Colors.GREY_400),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Text(format_real(rvalor), size=14, weight=ft.FontWeight.BOLD, color=Colors.GREEN_400),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_size=18,
                                icon_color=Colors.RED_300,
                                on_click=lambda _, x=rid: self._excluir_variavel(x),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=10,
                    border_radius=10,
                    bgcolor=Colors.with_opacity(0.04, Colors.WHITE),
                    border=ft.border.all(1, Colors.WHITE_10),
                )
            )

        if not var_items:
            var_items.append(
                ft.Container(
                    content=ft.Text("Nenhuma renda variável cadastrada", color=Colors.GREY_500, size=13),
                    alignment=ft.alignment.center,
                    padding=20,
                )
            )

        # --- Totais ---
        total_fixa = renda_fixa[2] if renda_fixa else 0
        total_var = sum(r[2] for r in var_rows)
        total_geral = total_fixa + total_var

        resumo = ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Renda Fixa", size=11, color=Colors.GREY_400),
                            ft.Text(format_real(total_fixa), size=16, weight=ft.FontWeight.BOLD, color=Colors.GREEN_400),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    expand=True,
                    padding=12,
                    border_radius=10,
                    bgcolor=Colors.with_opacity(0.08, Colors.GREEN),
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Variável", size=11, color=Colors.GREY_400),
                            ft.Text(format_real(total_var), size=16, weight=ft.FontWeight.BOLD, color=Colors.ACCENT_300),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    expand=True,
                    padding=12,
                    border_radius=10,
                    bgcolor=Colors.with_opacity(0.08, Colors.ACCENT),
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Total", size=11, color=Colors.GREY_400),
                            ft.Text(format_real(total_geral), size=16, weight=ft.FontWeight.BOLD, color=Colors.WHITE),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    expand=True,
                    padding=12,
                    border_radius=10,
                    bgcolor=Colors.with_opacity(0.08, Colors.WHITE),
                ),
            ],
            spacing=8,
        )

        # --- Layout final ---
        self.controls = [
            ft.Text("Minhas Rendas", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=6, color=ft.colors.TRANSPARENT),
            resumo,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            fixa_card,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            var_card,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            ft.Text("Histórico de Rendas Variáveis", size=14, weight=ft.FontWeight.BOLD, color=Colors.GREY_400),
            ft.Column(var_items, spacing=6),
        ]
        self.spacing = 14
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

        self._overlays: list[ft.Control] = [self._var_date_picker]

    @property
    def overlays(self) -> list[ft.Control]:
        return self._overlays

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    @staticmethod
    def _on_money_change_fixa(e: ft.ControlEvent) -> None:
        apply_money_mask(e)

    @staticmethod
    def _on_money_change_var(e: ft.ControlEvent) -> None:
        apply_money_mask(e)

    def _on_var_date_change(self, e: ft.ControlEvent) -> None:
        self._var_data.value = e.control.value.date().strftime("%d/%m/%Y")
        self._var_data.update()

    def _salvar_fixa(self, _: ft.ControlEvent) -> None:
        if not self._fixa_desc.value:
            self._show_toast("Informe a descrição.", is_error=True)
            return
        if not self._fixa_valor.value:
            self._show_toast("Informe o valor.", is_error=True)
            return
        try:
            valor = parse_br_money(self._fixa_valor.value)
            salvar_renda_fixa(self._fixa_desc.value.strip(), valor)
            self._show_toast("Renda fixa salva!")
            self._on_navigate(3)
        except Exception as ex:
            self._show_toast(f"Erro: {ex}", is_error=True)

    def _adicionar_variavel(self, _: ft.ControlEvent) -> None:
        if not self._var_desc.value:
            self._show_toast("Informe a descrição.", is_error=True)
            return
        if not self._var_valor.value:
            self._show_toast("Informe o valor.", is_error=True)
            return
        try:
            valor = parse_br_money(self._var_valor.value)
            data = self._var_data.value  # dd/mm/yyyy
            from datetime import datetime
            data_db = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
            cat = self._var_cat.value or ""
            inserir_renda_variavel(self._var_desc.value.strip(), valor, data_db, cat)
            self._show_toast("Renda variável adicionada!")
            self._on_navigate(3)
        except Exception as ex:
            self._show_toast(f"Erro: {ex}", is_error=True)

    def _excluir_variavel(self, renda_id: int) -> None:
        excluir_renda(renda_id)
        self._show_toast("Renda excluída!")
        self._on_navigate(3)
