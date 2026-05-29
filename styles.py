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

    SURFACE: str = ft.colors.SURFACE
    SURFACE_VARIANT: str = ft.colors.SURFACE_VARIANT

    ACCENT: str = ft.colors.PINK
    ACCENT_600: str = ft.colors.PINK_600
    ACCENT_300: str = ft.colors.PINK_300
    ACCENT_200: str = ft.colors.PINK_200

    GRADIENT_BRAND = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.colors.PINK_500, ft.colors.PURPLE_500, ft.colors.DEEP_PURPLE_500],
    )

    GRADIENT_GOLD = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.colors.AMBER_400, ft.colors.ORANGE_500],
    )

    GRADIENT_GREEN = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.colors.GREEN_500, ft.colors.TEAL_500],
    )

    GREEN: str = ft.colors.GREEN
    GREEN_400: str = ft.colors.GREEN_400
    GREEN_700: str = ft.colors.GREEN_700

    AMBER: str = ft.colors.AMBER
    CYAN: str = ft.colors.CYAN
    LIGHT_BLUE: str = ft.colors.LIGHT_BLUE
    ORANGE: str = ft.colors.ORANGE

    RED: str = ft.colors.RED
    RED_300: str = ft.colors.RED_300
    RED_700: str = ft.colors.RED_700

    GREY_400: str = ft.colors.GREY_400
    GREY_500: str = ft.colors.GREY_500
    GREY_600: str = ft.colors.GREY_600
    GREY_700: str = ft.colors.GREY_700

    WHITE: str = ft.colors.WHITE
    WHITE_10: str = ft.colors.WHITE10

    @staticmethod
    def with_opacity(opacity: float, color: str) -> str:
        return ft.colors.with_opacity(opacity, color)


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
CATEGORIAS: list[dict[str, str]] = [
    {"nome": "Alimentação", "cor": ft.colors.GREEN, "icon": ft.icons.RESTAURANT},
    {"nome": "Transporte", "cor": ft.colors.BLUE, "icon": ft.icons.DIRECTIONS_CAR},
    {"nome": "Lazer", "cor": ft.colors.PURPLE, "icon": ft.icons.GAMEPAD},
    {"nome": "Casa/Moradia", "cor": ft.colors.AMBER, "icon": ft.icons.HOME},
    {"nome": "Saúde", "cor": ft.colors.RED, "icon": ft.icons.FAVORITE},
    {"nome": "Educação", "cor": ft.colors.CYAN, "icon": ft.icons.SCHOOL},
    {"nome": "Outros", "cor": ft.colors.GREY, "icon": ft.icons.CREDIT_CARD},
]


def get_categoria_info(nome: str) -> dict[str, str]:
    """Retorna informações da categoria pelo nome (case-insensitive)."""
    for cat in CATEGORIAS:
        if cat["nome"].lower() == nome.lower():
            return cat
    return {"nome": nome, "cor": ft.colors.GREY, "icon": ft.icons.CREDIT_CARD}


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
    color=ft.colors.WHITE,
    bgcolor=ft.colors.PINK_600,
    shape=ft.RoundedRectangleBorder(radius=10),
)

BTN_SUCCESS = ft.ButtonStyle(
    color=ft.colors.WHITE,
    bgcolor=ft.colors.GREEN_700,
    shape=ft.RoundedRectangleBorder(radius=10),
)
