"""
Módulo de gerenciamento de estado global da aplicação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class AppState:
    """Estado reativo da aplicação Flet.

    Attributes:
        mes_selecionado: Mês corrente na navegação (1-12).
        ano_selecionado: Ano corrente na navegação.
        extrato_status: Filtro de status no extrato ('todos'|'pagos'|'pendentes').
        extrato_categoria: Filtro de categoria no extrato (nome ou 'todas').
    """

    mes_selecionado: int = field(default_factory=lambda: date.today().month)
    ano_selecionado: int = field(default_factory=lambda: date.today().year)
    extrato_status: str = "todos"
    extrato_categoria: str = "todas"

    def navegar_mes(self, delta: int) -> None:
        """Avança ou retrocede o mês selecionado."""
        m = self.mes_selecionado + delta
        if m > 12:
            self.mes_selecionado = 1
            self.ano_selecionado += 1
        elif m < 1:
            self.mes_selecionado = 12
            self.ano_selecionado -= 1
        else:
            self.mes_selecionado = m

    def resetar_filtros_extrato(self) -> None:
        """Restaura os filtros do extrato para os valores padrão."""
        self.extrato_status = "todos"
        self.extrato_categoria = "todas"
