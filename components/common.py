"""
Helpers de UI — componentes reutilizáveis e máscara monetária.
"""

from __future__ import annotations

import flet as ft

from styles import Colors, format_real


# ---------------------------------------------------------------------------
# Máscara monetária
# ---------------------------------------------------------------------------
def apply_money_mask(e: ft.ControlEvent) -> None:
    """Aplica máscara monetária brasileira em tempo real num TextField.

    Uso: passar como `on_change` de um ft.TextField.
    """
    val = e.control.value or ""
    clean = "".join(c for c in val if c.isdigit())
    if not clean:
        e.control.value = ""
    else:
        e.control.value = format_real(float(clean) / 100)
    e.control.update()


class MoneyField(ft.TextField):
    """TextField com máscara monetária brasileira embutida."""

    def __init__(
        self,
        label: str = "Valor (R$)",
        hint_text: str = "0,00",
        value: str = "",
    ) -> None:
        super().__init__(
            label=label,
            hint_text=hint_text,
            value=value,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=apply_money_mask,
            border_radius=10,
        )



