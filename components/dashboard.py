"""
View do Dashboard — painel mensal com navegação histórica e gráficos.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from db import buscar_resumo_mes
from state import AppState
from styles import Colors, NOMES_MESES, get_categoria_info, format_real


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def _build_pie_sections(
    por_categoria: dict[str, float], total: float
) -> list[ft.PieChartSection]:
    sections: list[ft.PieChartSection] = []
    for cat, valor in sorted(por_categoria.items(), key=lambda x: x[1], reverse=True):
        info = get_categoria_info(cat)
        pct = (valor / total) * 100
        sections.append(
            ft.PieChartSection(
                value=pct,
                color=info["cor"],
                radius=25,
            )
        )
    return sections


def _build_legend(por_categoria: dict[str, float]) -> ft.Column:
    items: list[ft.Control] = []
    for cat, valor in sorted(por_categoria.items(), key=lambda x: x[1], reverse=True):
        info = get_categoria_info(cat)
        items.append(
            ft.Row(
                [
                    ft.Container(width=10, height=10, border_radius=5, bgcolor=info["cor"]),
                    ft.Text(cat, size=12, expand=True),
                    ft.Text(format_real(valor), size=12, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            )
        )
    return ft.Column(items, spacing=6)


# ---------------------------------------------------------------------------
# Card de resumo inline (evita import circular com common.py)
# ---------------------------------------------------------------------------
class _SummaryCard(ft.Container):
    def __init__(self, icon: str, title: str, color: str) -> None:
        super().__init__()
        self._title = title
        self._color = color
        self._valor_text = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD)
        self._build(icon)

    def _build(self, icon: str) -> None:
        self.content = ft.Column(
            [
                ft.Row(
                    [ft.Icon(icon, color=self._color, size=24), ft.Text(self._title, size=11, color=Colors.GREY_400)],
                    spacing=6,
                ),
                self._valor_text,
            ],
            spacing=4,
        )
        self.bgcolor = Colors.with_opacity(0.1, self._color)
        self.border = ft.Border.all(1, Colors.with_opacity(0.2, self._color))
        self.border_radius = 14
        self.padding = 14
        self.expand = True

    def set_valor(self, valor: float) -> None:
        self._valor_text.value = format_real(valor)


# ===========================================================================
# Dashboard principal
# ===========================================================================
class DashboardView(ft.Column):
    """Painel interativo com navegação mensal, cards de resumo e gráfico."""

    def __init__(
        self,
        state: AppState,
        show_toast: Callable[[str], None],
    ) -> None:
        super().__init__()
        self._state = state
        self._show_toast = show_toast
        self.spacing = 14
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
        self._build()
        self._load_data()

    # ------------------------------------------------------------------
    # Construção da estrutura (executada uma vez)
    # ------------------------------------------------------------------
    def _build(self) -> None:
        st = self._state
        self._label = ft.Text(size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, expand=True)

        # --- Navegação mensal ---
        nav_row = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.icons.KEYBOARD_ARROW_LEFT_ROUNDED, on_click=lambda _: self._navegar(-1)),
                    self._label,
                    ft.IconButton(icon=ft.icons.KEYBOARD_ARROW_RIGHT_ROUNDED, on_click=lambda _: self._navegar(1)),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=10,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[ft.Colors.PINK_800, ft.Colors.PURPLE_800],
            ),
        )

        # --- Cards de resumo ---
        self._card_total = _SummaryCard(ft.icons.ATTACH_MONEY, "Custo Total", Colors.WHITE)
        self._card_fixo = _SummaryCard(ft.icons.REPEAT, "C. Fixos", ft.Colors.PINK_400)
        self._card_var = _SummaryCard(ft.icons.SHOPPING_CART, "C. Variáveis", ft.Colors.PURPLE_400)

        cards_row = ft.Row(
            [self._card_total, self._card_fixo, self._card_var],
            spacing=8,
        )

        # --- Container do gráfico (mutável) ---
        self._chart_container = ft.Container()

        # --- Estado vazio ---
        self._empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.INSERT_CHART_OUTLINED, size=56, color=Colors.GREY_600),
                    ft.Text("Nenhum dado encontrado para este mês", size=14, color=Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            padding=60,
            visible=False,
        )

        self.controls = [
            nav_row,
            cards_row,
            self._chart_container,
            self._empty_state,
        ]

    def _load_data(self) -> None:
        st = self._state
        nome = NOMES_MESES[st.mes_selecionado]
        self._label.value = f"{nome} de {st.ano_selecionado}"

        data = buscar_resumo_mes(st.ano_selecionado, st.mes_selecionado)

        if not data["tem_dados"]:
            self._chart_container.content = None
            self._empty_state.visible = True
            return

        self._empty_state.visible = False
        self._card_total.set_valor(data["total_geral"])
        self._card_fixo.set_valor(data["total_fixo"])
        self._card_var.set_valor(data["total_variavel"])

        por_cat = data["por_categoria"]
        total = data["total_geral"]
        sections = _build_pie_sections(por_cat, total)

        self._chart_container.content = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.PieChart(
                            sections=sections,
                            sections_space=2,
                            center_space_radius=30,
                            animate=True,
                        ),
                        width=100,
                        height=100,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(width=1, height=80, bgcolor=Colors.WHITE_10),
                    ft.Container(
                        content=_build_legend(por_cat),
                        expand=True,
                        padding=ft.padding.only(left=12),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=16,
            border=ft.Border.all(1, Colors.WHITE_10),
            border_radius=16,
            bgcolor=Colors.with_opacity(0.08, Colors.WHITE),
            height=160,
        )

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------
    def _navegar(self, delta: int) -> None:
        self._state.navegar_mes(delta)
        self._refresh()

    # ------------------------------------------------------------------
    # Refresh dos dados (com update — só quando já está na página)
    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        self._load_data()
        self.update()
