"""
Controle de Finanças — Ponto de entrada da aplicação Flet.

Responsabilidades:
  - Configurar a janela e o tema
  - Inicializar o banco de dados
  - Montar a barra de navegação
  - Orquestrar a troca de views (Lançamentos, Registro de Custo, Rendas)
"""

from __future__ import annotations

import flet as ft

from components.dashboard import DashboardView
from components.lanctos import LanctosView
from components.registro_custo import RegistroCustoView
from components.renda import RendaView
from db import init_db
from state import AppState
from styles import Colors


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------
def main(page: ft.Page) -> None:
    """Configura e executa a aplicação Flet."""

    # --- Configuração da janela ---
    page.title = "Controle de Finanças"
    page.theme_mode = ft.ThemeMode.DARK
    page.locale_configuration = ft.LocaleConfiguration(
        current_locale=ft.Locale(language_code="pt", country_code="BR"),
        supported_locales=[ft.Locale(language_code="pt", country_code="BR")],
    )
    page.window_resizable = True
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.PINK,
        card_theme=ft.CardTheme(
            color=ft.Colors.WHITE,
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=14),
            margin=0,
        ),
        navigation_bar_theme=ft.NavigationBarTheme(
            indicator_color=ft.Colors.PINK_200,
        ),
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.PINK,
        card_theme=ft.CardTheme(
            color=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=14),
            margin=0,
        ),
        navigation_bar_theme=ft.NavigationBarTheme(
            indicator_color=ft.Colors.PINK_400,
        ),
    )

    # --- Inicialização ---
    init_db()
    state = AppState()

    # --- Recipiente principal ---
    content_container = ft.Container(expand=True, padding=12)

    # --- Toggle de tema ---
    _is_dark = True

    def _toggle_theme(_: ft.ControlEvent) -> None:
        nonlocal _is_dark
        _is_dark = not _is_dark
        page.theme_mode = ft.ThemeMode.DARK if _is_dark else ft.ThemeMode.LIGHT
        theme_btn.icon = ft.Icons.DARK_MODE if _is_dark else ft.Icons.LIGHT_MODE
        theme_btn.update()
        page.update()

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        selected_icon=ft.Icons.LIGHT_MODE,
        icon_color=ft.Colors.PINK_300,
        on_click=_toggle_theme,
        tooltip="Alternar tema",
    )

    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("Controle de Finanças", size=18, weight=ft.FontWeight.BOLD),
                theme_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        border=ft.Border.only(bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))),
    )

    # --- Notificações ---
    def show_toast(text: str, is_error: bool = False) -> None:
        """Exibe um snackbar de notificação."""
        page.overlay.append(
            ft.SnackBar(
                content=ft.Text(text, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
                open=True,
            )
        )
        page.update()

    # --- Navegação ---
    def render_current_view() -> None:
        """Reconstroi a view ativa conforme o índice de navegação."""
        idx = page.navigation_bar.selected_index

        if idx == 0:
            content_container.content = LanctosView(
                state=state,
                show_toast=show_toast,
                on_navigate=lambda _: render_current_view(),
                page=page,
            )
        elif idx == 1:
            view = RegistroCustoView(
                state=state,
                show_toast=show_toast,
                on_navigate=_go_to_index,
            )
            for overlay in getattr(view, "overlays", []):
                page.overlay.append(overlay)
            content_container.content = view
        elif idx == 2:
            view = RendaView(
                state=state,
                show_toast=show_toast,
                on_navigate=_go_to_index,
            )
            for overlay in getattr(view, "overlays", []):
                page.overlay.append(overlay)
            content_container.content = view
        elif idx == 3:
            content_container.content = DashboardView(
                state=state,
                show_toast=show_toast,
            )
        page.update()

    def _go_to_index(idx: int) -> None:
        page.navigation_bar.selected_index = idx
        render_current_view()

    def on_navigation_change(e: ft.ControlEvent) -> None:
        page.navigation_bar.selected_index = e.control.selected_index
        render_current_view()

    # --- Barra de navegação inferior ---
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_navigation_change,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_HIDE,
        height=64,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                selected_icon=ft.Icons.RECEIPT_LONG_ROUNDED,
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADD_CARD_OUTLINED,
                selected_icon=ft.Icons.ADD_CARD_ROUNDED,
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                selected_icon=ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD_ROUNDED,
            ),
        ],
        bgcolor=ft.Colors.SURFACE,
        elevation=10,
        indicator_color=ft.Colors.PINK_200,
    )

    # --- Renderização inicial ---
    page.add(ft.Column([top_bar, content_container], spacing=0, expand=True))
    render_current_view()


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ft.run(main, port=8550, host="127.0.0.1")
