"""
Constantes de estilo, temas e formatação compartilhadas entre componentes.
"""

from __future__ import annotations

import flet as ft


# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
class Colors:
    """Constantes de cores do aplicativo — paleta Instagram."""

    SURFACE: str = ft.Colors.SURFACE
    SURFACE_VARIANT: str = ft.Colors.SURFACE_VARIANT

    ACCENT: str = ft.Colors.PINK
    ACCENT_600: str = ft.Colors.PINK_600
    ACCENT_300: str = ft.Colors.PINK_300
    ACCENT_200: str = ft.Colors.PINK_200

    GRADIENT_BRAND = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.Colors.PINK_500, ft.Colors.PURPLE_500, ft.Colors.DEEP_PURPLE_500],
    )

    GRADIENT_GOLD = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.Colors.AMBER_400, ft.Colors.ORANGE_500],
    )

    GRADIENT_GREEN = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.Colors.GREEN_500, ft.Colors.TEAL_500],
    )

    GREEN: str = ft.Colors.GREEN
    GREEN_400: str = ft.Colors.GREEN_400
    GREEN_700: str = ft.Colors.GREEN_700

    AMBER: str = ft.Colors.AMBER
    CYAN: str = ft.Colors.CYAN
    LIGHT_BLUE: str = ft.Colors.LIGHT_BLUE
    ORANGE: str = ft.Colors.ORANGE

    RED: str = ft.Colors.RED
    RED_300: str = ft.Colors.RED_300
    RED_700: str = ft.Colors.RED_700

    GREY_400: str = ft.Colors.GREY_400
    GREY_500: str = ft.Colors.GREY_500
    GREY_600: str = ft.Colors.GREY_600
    GREY_700: str = ft.Colors.GREY_700

    WHITE: str = ft.Colors.WHITE
    WHITE_10: str = ft.Colors.WHITE10

    @staticmethod
    def with_opacity(opacity: float, color: str) -> str:
        return ft.Colors.with_opacity(opacity, color)


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
CATEGORIAS: list[dict[str, str]] = [
    {"nome": "Alimentação", "cor": ft.Colors.GREEN, "icon": ft.icons.RESTAURANT},
    {"nome": "Transporte", "cor": ft.Colors.BLUE, "icon": ft.icons.DIRECTIONS_CAR},
    {"nome": "Lazer", "cor": ft.Colors.PURPLE, "icon": ft.icons.GAMEPAD},
    {"nome": "Casa/Moradia", "cor": ft.Colors.AMBER, "icon": ft.icons.HOME},
    {"nome": "Saúde", "cor": ft.Colors.RED, "icon": ft.icons.FAVORITE},
    {"nome": "Educação", "cor": ft.Colors.CYAN, "icon": ft.icons.SCHOOL},
    {"nome": "Outros", "cor": ft.Colors.GREY, "icon": ft.icons.CREDIT_CARD},
]


def get_categoria_info(nome: str) -> dict[str, str]:
    """Retorna informações da categoria pelo nome (case-insensitive)."""
    for cat in CATEGORIAS:
        if cat["nome"].lower() == nome.lower():
            return cat
    return {"nome": nome, "cor": ft.Colors.GREY, "icon": ft.icons.CREDIT_CARD}


# ---------------------------------------------------------------------------
# Nomes dos meses
# ---------------------------------------------------------------------------
NOMES_MESES: dict[int, str] = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


# ---------------------------------------------------------------------------
# Helpers de formatação
# ---------------------------------------------------------------------------
def format_real(value: float | None) -> str:
    """Formata um float como moeda brasileira (R$ X.XXX,XX)."""
    if value is None:
        value = 0.0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_br_money(text: str) -> float:
    """Converte string brasileira (ex: 'R$ 1.234,56' ou '1234,56') em float."""
    cleaned = text.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    if not cleaned:
        return 0.0
    return float(cleaned)


# ---------------------------------------------------------------------------
# Botões reutilizáveis
# ---------------------------------------------------------------------------
BTN_PRIMARY = ft.ButtonStyle(
    color=ft.Colors.WHITE,
    bgcolor=ft.Colors.PINK_600,
    shape=ft.RoundedRectangleBorder(radius=10),
)

BTN_SUCCESS = ft.ButtonStyle(
    color=ft.Colors.WHITE,
    bgcolor=ft.Colors.GREEN_700,
    shape=ft.RoundedRectangleBorder(radius=10),
)
