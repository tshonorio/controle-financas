"""
View de Registro de Custo — formulário unificado para custos fixos e variáveis.
"""

from __future__ import annotations

import calendar as cal
from datetime import date
from typing import Callable

import flet as ft

from components.common import apply_money_mask
from db import db_execute, inserir_custo_fixo
from state import AppState
from styles import BTN_PRIMARY, Colors, CATEGORIAS, format_real, parse_br_money


# ---------------------------------------------------------------------------
# Helper de data
# ---------------------------------------------------------------------------
def _add_months(source: date, months: int) -> date:
    month = source.month - 1 + months
    year = source.year + month // 12
    month = month % 12 + 1
    day = min(source.day, cal.monthrange(year, month)[1])
    return date(year, month, day)


class RegistroCustoView(ft.Column):
    """Formulário único para cadastrar custos fixos ou variáveis."""

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
        self._tipo: str = "variavel"
        self._selected_compra_date: list[date] = [date.today()]
        self._selected_venc_date: list[date] = [date.today()]
        self._build()
        self._apply_initial_state()

    # ------------------------------------------------------------------
    # Construção do formulário
    # ------------------------------------------------------------------
    def _build(self) -> None:
        # --- Seletor de tipo (Fixo / Variável) ---
        self._btn_fixo = ft.Container(
            content=ft.Text("Fixo", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            padding=ft.padding.symmetric(vertical=10),
            border_radius=ft.border_radius.only(top_left=10, bottom_left=10),
            bgcolor=Colors.with_opacity(0.1, Colors.WHITE),
            expand=True,
            on_click=lambda _: self._set_tipo("fixo"),
        )
        self._btn_variavel = ft.Container(
            content=ft.Text("Variável", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            padding=ft.padding.symmetric(vertical=10),
            border_radius=ft.border_radius.only(top_right=10, bottom_right=10),
            bgcolor=ft.Colors.PINK_600,
            expand=True,
            on_click=lambda _: self._set_tipo("variavel"),
        )

        # --- Descrição ---
        self._descricao = ft.TextField(
            label="Nome do Custo",
            hint_text="Ex: Aluguel / Supermercado",
            border_radius=10,
        )

        # --- Local (só variável) ---
        self._local = ft.TextField(
            label="Local",
            hint_text="Ex: Loja de compra",
            border_radius=10,
        )

        # --- Valor (com máscara) ---
        self._valor_display = ft.TextField(
            label="Valor (R$)",
            hint_text="0,00",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_money_change,
            border_radius=10,
        )

        # --- Dia de vencimento (só fixo) ---
        self._dia = ft.TextField(
            label="Dia do Vencimento",
            hint_text="Ex: 15",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
        )

        # --- Data da compra (só variável) ---
        self._date_text = ft.Text(
            self._selected_compra_date[0].strftime("%d/%m/%Y"),
            size=15, weight=ft.FontWeight.BOLD,
        )
        self._date_picker = ft.DatePicker(
            on_change=self._on_date_change,
            first_date=date(date.today().year - 2, 1, 1),
            last_date=date(date.today().year + 5, 12, 31),
        )
        self._date_btn = ft.Container(
            content=ft.Row(
                [ft.Icon(ft.icons.CALENDAR_MONTH, color=Colors.ACCENT_300), self._date_text],
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

        # --- Parcelamento (Crédito / só variável) ---
        self._num_parcelas = ft.TextField(
            label="Número de Parcelas", value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            on_change=lambda _: self._update_preview(),
        )
        self._venc_text = ft.Text(
            self._selected_venc_date[0].strftime("%d/%m/%Y"),
            size=15, weight=ft.FontWeight.BOLD,
        )
        self._venc_picker = ft.DatePicker(
            on_change=self._on_venc_change,
            first_date=date(date.today().year - 2, 1, 1),
            last_date=date(date.today().year + 5, 12, 31),
        )
        self._venc_btn = ft.Container(
            content=ft.Row(
                [ft.Icon(ft.icons.CALENDAR_MONTH, color=Colors.ACCENT_300), self._venc_text],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=lambda _: self._venc_picker.pick_date(),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=12,
            border_radius=10,
        )
        self._preview_text = ft.Text(
            "Valor de cada parcela: R$ 0,00",
            size=13, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_200,
        )
        self._preview_container = ft.Container(
            content=self._preview_text,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.INDIGO),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.INDIGO)),
            border_radius=10, padding=12, alignment=ft.alignment.center,
            visible=False,
        )
        self._parcelamento_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Column([ft.Text("Nº Parcelas", size=12, color=ft.Colors.GREY_400), self._num_parcelas], expand=1),
                        ft.Column([ft.Text("1º Vencimento", size=12, color=ft.Colors.GREY_400), self._venc_btn], expand=2),
                    ],
                    spacing=10,
                ),
                self._preview_container,
            ],
            spacing=10, visible=False,
        )

        # --- Botão salvar ---
        save_btn = ft.ElevatedButton(
            text="Salvar",
            icon=ft.icons.SAVE,
            style=BTN_PRIMARY,
            height=48,
            on_click=self._salvar,
        )

        # --- Layout final ---
        self.controls = [
            ft.Text("Registro de Custo", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.Container(
                content=ft.Row([self._btn_fixo, self._btn_variavel], spacing=0),
                border=ft.Border.all(1, Colors.WHITE_10),
                border_radius=10,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            self._descricao,
            self._local,
            self._valor_display,
            self._dia,
            ft.Column(
                [
                    ft.Text("Data da Compra", size=12, color=ft.Colors.GREY_400),
                    ft.Row(
                        [
                            self._date_btn,
                            self._metodo,
                        ],
                        spacing=10,
                    ),
                ],
                spacing=4,
            ),
            self._categoria,
            self._parcelamento_section,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            save_btn,
        ]
        self.spacing = 14
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

        self._overlays: list[ft.Control] = [self._date_picker, self._venc_picker]

    @property
    def overlays(self) -> list[ft.Control]:
        return self._overlays

    # ------------------------------------------------------------------
    # Controle de tipo
    # ------------------------------------------------------------------
    def _set_tipo(self, tipo: str) -> None:
        self._tipo = tipo
        if tipo == "fixo":
            self._btn_fixo.bgcolor = ft.Colors.PINK_600
            self._btn_variavel.bgcolor = Colors.with_opacity(0.1, Colors.WHITE)
        else:
            self._btn_fixo.bgcolor = Colors.with_opacity(0.1, Colors.WHITE)
            self._btn_variavel.bgcolor = ft.Colors.PINK_600
        self._update_fields()
        self.update()

    def _apply_initial_state(self) -> None:
        is_var = self._tipo == "variavel"
        self._local.visible = is_var
        self._dia.visible = not is_var
        self._parcelamento_section.visible = is_var and self._metodo.value == "Crédito"

    def _update_fields(self) -> None:
        is_var = self._tipo == "variavel"
        self._local.visible = is_var
        self._dia.visible = not is_var
        self._parcelamento_section.visible = is_var and self._metodo.value == "Crédito"
        self.update()

    # ------------------------------------------------------------------
    # Handlers de entrada
    # ------------------------------------------------------------------
    def _on_money_change(self, e: ft.ControlEvent) -> None:
        apply_money_mask(e)
        self._update_preview()

    def _on_date_change(self, e: ft.ControlEvent) -> None:
        self._selected_compra_date[0] = e.control.value.date()
        self._date_text.value = self._selected_compra_date[0].strftime("%d/%m/%Y")
        self._date_text.update()
        if self._metodo.value != "Crédito":
            self._selected_venc_date[0] = self._selected_compra_date[0]
            self._venc_text.value = self._selected_venc_date[0].strftime("%d/%m/%Y")
            self._venc_text.update()

    def _on_venc_change(self, e: ft.ControlEvent) -> None:
        self._selected_venc_date[0] = e.control.value.date()
        self._venc_text.value = self._selected_venc_date[0].strftime("%d/%m/%Y")
        self._venc_text.update()

    def _toggle_credit(self) -> None:
        if self._tipo != "variavel":
            return
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
        if not self._valor_display.value:
            self._preview_container.visible = False
            self._preview_container.update()
            return
        try:
            valor_total = parse_br_money(self._valor_display.value)
            parcelas = int(self._num_parcelas.value) if self._num_parcelas.value else 1
            if parcelas > 1:
                v_parcela = valor_total / parcelas
                self._preview_text.value = f"Valor da parcela: {parcelas}x de {format_real(v_parcela)}"
                self._preview_container.visible = True
            else:
                self._preview_container.visible = False
        except (ValueError, TypeError):
            self._preview_container.visible = False
        self._preview_container.update()

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------
    def _salvar(self, _: ft.ControlEvent) -> None:
        if not self._descricao.value:
            self._show_toast("Informe a descrição.", is_error=True)
            return
        if not self._valor_display.value:
            self._show_toast("Informe o valor.", is_error=True)
            return
        if not self._categoria.value:
            self._show_toast("Selecione uma categoria.", is_error=True)
            return
        if self._tipo == "fixo":
            if not self._dia.value or not self._dia.value.isdigit():
                self._show_toast("Informe um dia válido (1-31).", is_error=True)
                return
            self._salvar_fixo()
        else:
            self._salvar_variavel()

    def _salvar_fixo(self) -> None:
        try:
            valor = parse_br_money(self._valor_display.value)
            dia = int(self._dia.value)
            if dia < 1 or dia > 31:
                self._show_toast("Dia deve estar entre 1 e 31.", is_error=True)
                return
            desc = self._descricao.value.strip()
            cat = self._categoria.value
            metodo = self._metodo.value

            cf_id = inserir_custo_fixo(desc, valor, dia, cat, metodo)

            compra_id = db_execute(
                """
                INSERT INTO compras
                    (descricao, valor_total, categoria,
                     metodo_pagamento, num_parcelas, tipo_custo)
                VALUES (?, ?, ?, ?, ?, 'fixo')
                """,
                (f"{desc} (fixo)", valor, cat, metodo, 1),
            )

            hoje = date.today()
            primeiro_venc = date(hoje.year, hoje.month, min(dia, cal.monthrange(hoje.year, hoje.month)[1]))
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
            self._limpar()
            self._on_navigate(0)

        except Exception as ex:
            self._show_toast(f"Erro ao salvar: {ex}", is_error=True)

    def _salvar_variavel(self) -> None:
        try:
            valor_total = parse_br_money(self._valor_display.value)
            desc = self._descricao.value
            local = self._local.value or None
            cat = self._categoria.value
            metodo = self._metodo.value
            num_p = int(self._num_parcelas.value) if self._num_parcelas.value else 1

            compra_id = db_execute(
                """
                INSERT INTO compras
                    (descricao, valor_total, categoria,
                     metodo_pagamento, num_parcelas,
                     valores_parcelas, local, tipo_custo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'variavel')
                """,
                (desc, valor_total, cat, metodo, num_p, None, local),
            )

            first_venc = self._selected_venc_date[0]
            if num_p <= 1:
                db_execute(
                    """
                    INSERT INTO parcelas
                        (compra_id, num_parcela, valor_parcela,
                         data_vencimento, paga)
                    VALUES (?, ?, ?, ?, 0)
                    """,
                    (compra_id, 1, valor_total, first_venc.strftime("%Y-%m-%d")),
                )
            else:
                valor_base = round(valor_total / num_p, 2)
                diferenca = round(valor_total - (valor_base * num_p), 2)
                valores_futuros: list[float] = []
                for i in range(num_p):
                    vp = valor_base
                    if i == num_p - 1:
                        vp = round(valor_base + diferenca, 2)
                    valores_futuros.append(vp)

                import json
                db_execute(
                    "UPDATE compras SET valores_parcelas = ? WHERE id = ?",
                    (json.dumps(valores_futuros), compra_id),
                )
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

            self._show_toast("Custo variável adicionado com sucesso!")
            self._limpar()
            self._on_navigate(0)

        except Exception as ex:
            self._show_toast(f"Erro ao salvar: {ex}", is_error=True)

    def _limpar(self) -> None:
        self._descricao.value = ""
        self._local.value = ""
        self._valor_display.value = ""
        self._dia.value = ""
        self._num_parcelas.value = "1"
        self._categoria.value = None
        self._metodo.value = "Pix"
        self.update()
