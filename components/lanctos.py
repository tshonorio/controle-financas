"""
View de Lançamentos — lista todas as parcelas com prioridade e toggle de pagamento.
"""

from __future__ import annotations

from datetime import date, datetime
from threading import Timer
from typing import Callable

import flet as ft

from components.common import apply_money_mask
from db import (
    atualizar_parcela,
    atualizar_prioridades_em_lote,
    buscar_todas_parcelas,
    criar_proxima_parcela_cf,
    criar_proxima_parcela_compra,
    definir_notificar_parcela,
    deletar_parcela,
    toggle_parcela,
)
from state import AppState
from styles import Colors, get_categoria_info, format_real, parse_br_money


class LanctosView(ft.Column):
    """Lista de parcelas com controle de pagamento e prioridade."""

    def __init__(
        self,
        state: AppState,
        show_toast: Callable[[str], None],
        on_navigate: Callable[[int], None],
        page: ft.Page | None = None,
    ) -> None:
        super().__init__()
        self._state = state
        self._show_toast = show_toast
        self._on_navigate = on_navigate
        self._page = page
        self._parcela_ids: list[int] = []
        self._dragging_id: int | None = None
        self._edit_timer: Timer | None = None
        self._edit_picker: ft.DatePicker | None = None
        self._build()

    def _build_item(
        self,
        p_id: int,
        c_id: int,
        desc: str,
        n_p: int,
        tot_p: int,
        valor: float,
        venc_str: str,
        paga: int,
        cat: str,
        metodo: str,
        notificar_dias: int | None,
        local: str | None = None,
        custo_fixo_id: int | None = None,
    ) -> ft.Control:
        """Monta um item individual com suporte a drag-and-drop."""
        is_paid = paga == 1
        venc_date = datetime.strptime(venc_str, "%Y-%m-%d").date()
        venc_fmt = venc_date.strftime("%d/%m/%Y")
        days_remaining = (venc_date - date.today()).days
        cat_info = get_categoria_info(cat)

        if is_paid:
            border_color = Colors.WHITE_10
            border_width = 1
        elif days_remaining <= 1:
            border_color = Colors.RED
            border_width = 5
        elif days_remaining <= 9:
            border_color = Colors.ORANGE
            border_width = 5
        else:
            border_color = Colors.LIGHT_BLUE
            border_width = 5

        def _make_body(opacity_override: float | None = None) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.CHECK_CIRCLE
                            if is_paid
                            else ft.icons.RADIO_BUTTON_UNCHECKED,
                            icon_color=Colors.GREEN if is_paid else Colors.GREY_500,
                            on_click=lambda _, pid=p_id, ps=paga, d=desc, rid=c_id, cf=custo_fixo_id: self._confirm_toggle(
                                pid, ps, d, rid, cf
                            ),
                        ),
                        ft.Container(
                            content=ft.Icon(
                                cat_info["icon"],
                                color=cat_info["cor"],
                                size=18,
                            ),
                            bgcolor=Colors.with_opacity(0.1, cat_info["cor"]),
                            border_radius=8,
                            padding=6,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    desc,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    style=ft.TextStyle(
                                        decoration=ft.TextDecoration.LINE_THROUGH
                                        if is_paid
                                        else None
                                    ),
                                    color=Colors.GREY_500 if is_paid else Colors.WHITE,
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"{n_p}ª de {tot_p}", size=11, color=Colors.GREY_400),
                                        ft.Text("•", size=11, color=Colors.GREY_600),
                                        ft.Text(venc_fmt, size=11, color=Colors.GREY_400),
                                        ft.Text("•", size=11, color=Colors.GREY_600),
                                        ft.Text(metodo, size=11, color=Colors.ACCENT_200),
                                        *([ft.Text("•", size=11, color=Colors.GREY_600), ft.Text(local, size=11, color=Colors.GREY_400)] if local else []),
                                    ],
                                    spacing=4,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Text(
                            format_real(valor),
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=Colors.GREEN_400 if is_paid else Colors.WHITE,
                        ),
                        ft.IconButton(
                            icon=ft.icons.NOTIFICATIONS_ACTIVE
                            if notificar_dias is not None
                            else ft.icons.NOTIFICATIONS_NONE,
                            icon_size=18,
                            icon_color=(
                                Colors.ACCENT_300
                                if notificar_dias is not None
                                else Colors.GREY_600
                            ),
                            tooltip=(
                                f"Lembrar {notificar_dias} dia{'s' if notificar_dias != 1 else ''} antes"
                                if notificar_dias is not None
                                else "Definir lembrete"
                            ),
                            on_click=lambda _, pid=p_id, d=desc, nd=notificar_dias: self._abrir_dialog_notificacao(
                                pid, d, nd
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            icon_size=18,
                            icon_color=Colors.RED_300,
                            tooltip="Excluir",
                            on_click=lambda _, pid=p_id: self._delete_item(pid),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                padding=8,
                border_radius=12,
                bgcolor=(
                    Colors.with_opacity(0.4, ft.colors.SURFACE_VARIANT)
                    if is_paid
                    else ft.colors.SURFACE_VARIANT
                ),
                border=ft.border.all(border_width, border_color),
                opacity=opacity_override if opacity_override is not None else (0.6 if is_paid else 1.0),
            )

        def on_tap_down(_):
            self._cancel_edit_timer()
            self._edit_timer = Timer(
                2.0, lambda: self._open_edit_dialog(p_id, c_id, desc, valor, venc_str)
            )
            self._edit_timer.daemon = True
            self._edit_timer.start()

        def on_tap_up(_):
            self._cancel_edit_timer()

        gesture = ft.GestureDetector(
            content=_make_body(),
            on_tap_down=on_tap_down,
            on_tap_up=on_tap_up,
        )

        draggable = ft.Draggable(
            content=gesture,
            content_when_dragging=_make_body(0.7),
            on_drag_start=lambda _: (
                setattr(self, '_dragging_id', p_id),
                self._cancel_edit_timer(),
            ),
        )

        drag_target = ft.DragTarget(
            content=draggable,
            on_accept=lambda e, tgt=p_id: self._handle_drop(tgt),
        )

        return drag_target

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------
    def _build(self) -> None:
        rows = buscar_todas_parcelas()

        unpaid_items: list[ft.Control] = []
        self._parcela_ids = []

        for r in rows:
            (
                p_id, desc, n_p, tot_p, valor,
                venc_str, paga, cat, metodo, c_id, prioridade,
                notificar_dias, custo_fixo_id, local,
            ) = r

            if paga == 1:
                continue

            item = self._build_item(
                p_id, c_id, desc, n_p, tot_p, valor, venc_str, paga,
                cat, metodo, notificar_dias, local, custo_fixo_id,
            )
            unpaid_items.append(item)
            self._parcela_ids.append(p_id)

        # --- Header ---
        pendentes = len(unpaid_items)

        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            "Meus Lançamentos",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"{pendentes} pendente{'s' if pendentes != 1 else ''}",
                            size=12,
                            color=Colors.GREY_400,
                        ),
                    ],
                    spacing=2,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Lista ---
        if not unpaid_items:
            list_container = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=48, color=Colors.GREEN_400),
                        ft.Text(
                            "Todas as contas estão pagas!",
                            color=Colors.GREY_500,
                            size=14,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=60,
            )
        else:
            list_container = ft.Column(
                controls=unpaid_items,
                spacing=8,
                expand=True,
            )

        # --- Dica ---
        hint = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.TOUCH_APP, size=14, color=Colors.GREY_500),
                    ft.Text(
                        "Segure e arraste para reordenar · pressione 2s para editar",
                        size=11,
                        color=Colors.GREY_500,
                    ),
                ],
                spacing=6,
            ),
            padding=8,
            border_radius=8,
            bgcolor=Colors.with_opacity(0.05, Colors.WHITE),
        )

        self.controls = [
            header,
            hint,
            ft.Divider(height=4, color=ft.colors.TRANSPARENT),
            list_container,
        ]
        self.spacing = 8
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    # ------------------------------------------------------------------
    # Drop handler
    # ------------------------------------------------------------------
    def _handle_drop(self, tgt_id: int) -> None:
        """Recebe o drop e troca a prioridade entre os dois itens."""
        src_id = self._dragging_id
        if src_id is None or src_id == tgt_id:
            return

        src_idx = self._parcela_ids.index(src_id)
        tgt_idx = self._parcela_ids.index(tgt_id)

        # Troca na lista
        self._parcela_ids[src_idx], self._parcela_ids[tgt_idx] = (
            self._parcela_ids[tgt_idx],
            self._parcela_ids[src_idx],
        )

        # Salva no banco
        total = len(self._parcela_ids)
        novas = [(pid, total - i) for i, pid in enumerate(self._parcela_ids)]
        atualizar_prioridades_em_lote(novas)

        self._on_navigate(0)

    # ------------------------------------------------------------------
    # Toggle pagamento
    # ------------------------------------------------------------------
    def _confirm_toggle(self, parcela_id: int, status_atual: bool | int, descricao: str,
                        compra_id: int | None = None, custo_fixo_id: int | None = None) -> None:
        """Mostra confirmação antes de alternar pagamento."""
        page = self._page
        if not page:
            self._toggle(parcela_id, status_atual, compra_id, custo_fixo_id)
            return

        is_paid = bool(int(status_atual))
        titulo = "Confirmar pagamento" if not is_paid else "Reverter pagamento"
        mensagem = f"Marcar \"{descricao}\" como pago?" if not is_paid else f"Reverter \"{descricao}\" para pendente?"
        cor = Colors.GREEN if not is_paid else Colors.AMBER

        def confirmar(_):
            dlg.open = False
            page.update()
            self._toggle(parcela_id, status_atual, compra_id, custo_fixo_id)

        def cancelar(_):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.CHECK_CIRCLE if not is_paid else ft.icons.UNDO, color=cor, size=20),
                    ft.Text(titulo, size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Text(mensagem, size=13),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.FilledButton("Confirmar", on_click=confirmar, style=ft.ButtonStyle(color=cor)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _toggle(self, parcela_id: int, status_atual: bool | int,
                compra_id: int | None = None, custo_fixo_id: int | None = None) -> None:
        """Alterna o status de pagamento e recarrega a view."""
        status_int = int(status_atual)
        is_marking_paid = status_int == 0

        toggle_parcela(parcela_id, status_int)

        if is_marking_paid:
            if custo_fixo_id is not None and compra_id is not None:
                # Custo fixo pago — perguntar se quer renovar
                self._perguntar_renovacao(compra_id, custo_fixo_id)
            elif compra_id is not None:
                # Parcela de compra parcelada — gerar próxima automaticamente
                criou = criar_proxima_parcela_compra(compra_id)
                if criou:
                    self._show_toast("Pago! Próxima parcela liberada.")
                else:
                    self._show_toast("Pago! Última parcela.")
                self._on_navigate(0)
            else:
                self._show_toast("Pago!")
                self._on_navigate(0)
        else:
            self._show_toast("Marcado como pendente")
            self._on_navigate(0)

    def _perguntar_renovacao(self, compra_id: int, custo_fixo_id: int) -> None:
        """Pergunta se o usuário quer renovar o custo fixo para o próximo mês."""
        page = self._page
        if not page:
            self._on_navigate(0)
            return

        def renovar(_):
            dlg.open = False
            page.update()
            criou = criar_proxima_parcela_cf(custo_fixo_id, compra_id)
            if criou:
                self._show_toast("Custo fixo renovado para o próximo mês!")
            else:
                self._show_toast("Próximo mês já possui parcela deste custo fixo.")
            self._on_navigate(0)

        def pular(_):
            dlg.open = False
            page.update()
            self._show_toast("Pago!")
            self._on_navigate(0)

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.REPEAT_ROUNDED, color=Colors.ACCENT_300, size=20),
                    ft.Text("Renovar custo fixo?", size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Text(
                "Deseja gerar uma nova parcela para o próximo mês?",
                size=13,
            ),
            actions=[
                ft.TextButton("Não", on_click=pular),
                ft.FilledButton("Sim, renovar", on_click=renovar,
                                style=ft.ButtonStyle(color=Colors.GREEN)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ------------------------------------------------------------------
    # Notificação por item
    # ------------------------------------------------------------------
    def _abrir_dialog_notificacao(
        self, parcela_id: int, descricao: str, dias_atual: int | None
    ) -> None:
        """Abre diálogo para definir lembrete individual."""
        page = self._page
        if not page:
            self._show_toast("Erro: página não disponível")
            return

        opcoes = [
            ("Não lembrar", ""),
            ("1 dia antes", "1"),
            ("2 dias antes", "2"),
            ("3 dias antes", "3"),
            ("5 dias antes", "5"),
            ("7 dias antes", "7"),
        ]

        radio_group = ft.RadioGroup(
            content=ft.Column(
                [ft.Radio(value=val, label=label) for label, val in opcoes],
                spacing=4,
            ),
            value=str(dias_atual) if dias_atual is not None else "",
        )

        def salvar(_):
            raw = radio_group.value
            dias = int(raw) if raw else None
            definir_notificar_parcela(parcela_id, dias)
            msg = (
                f"Lembrete definido para {descricao}"
                if dias is not None
                else f"Lembrete removido de {descricao}"
            )
            self._show_toast(msg)
            dlg.open = False
            page.update()
            self._on_navigate(0)

        def cancelar(_):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.NOTIFICATIONS_OUTLINED, color=Colors.ACCENT_300),
                    ft.Text("Lembrete", size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    ft.Text(
                        f"Quando avisar sobre \"{descricao}\"?",
                        size=13,
                        color=Colors.GREY_400,
                    ),
                    ft.Divider(height=8, color=ft.colors.TRANSPARENT),
                    radio_group,
                ],
                spacing=8,
                width=260,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.FilledButton("Salvar", on_click=salvar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ------------------------------------------------------------------
    # Timer helpers
    # ------------------------------------------------------------------
    def _cancel_edit_timer(self) -> None:
        """Cancela o timer de edição (se ativo)."""
        if self._edit_timer:
            self._edit_timer.cancel()
            self._edit_timer = None

    # ------------------------------------------------------------------
    # Excluir item
    # ------------------------------------------------------------------
    def _delete_item(self, parcela_id: int) -> None:
        """Confirma e exclui uma parcela (e a compra se for a última)."""
        page = self._page
        if not page:
            return

        def confirmar(_):
            dlg.open = False
            page.update()
            deletar_parcela(parcela_id)
            self._show_toast("Item excluído!")
            self._on_navigate(0)

        def cancelar(_):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Excluir item"),
            content=ft.Text("Tem certeza que deseja excluir este lançamento?", size=13),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Excluir", on_click=confirmar, style=ft.ButtonStyle(color=Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ------------------------------------------------------------------
    # Editar item (long-press)
    # ------------------------------------------------------------------
    def _open_edit_dialog(
        self,
        parcela_id: int,
        compra_id: int,
        descricao: str,
        valor_atual: float,
        venc_str: str,
    ) -> None:
        """Abre diálogo para editar valor e vencimento da parcela."""
        page = self._page
        if not page:
            return

        valor_field = ft.TextField(
            label="Valor",
            value=format_real(valor_atual),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._apply_mask(e),
            border_radius=10,
        )

        venc_date = datetime.strptime(venc_str, "%Y-%m-%d").date()
        venc_field = ft.Text(
            venc_date.strftime("%d/%m/%Y"),
            size=15,
            weight=ft.FontWeight.BOLD,
        )

        edit_picker = ft.DatePicker(
            on_change=lambda e: (
                setattr(venc_field, 'value', e.control.value.date().strftime("%d/%m/%Y")),
                venc_field.update(),
            ),
            first_date=date(date.today().year - 2, 1, 1),
            last_date=date(date.today().year + 5, 12, 31),
            help_text="dd/mm/aaaa",
            field_label_text="Nova data",
            cancel_text="Cancelar",
            confirm_text="OK",
        )
        page.overlay.append(edit_picker)
        self._edit_picker = edit_picker

        def pick_date(_):
            edit_picker.pick_date()

        def salvar(_):
            try:
                novo_valor = parse_br_money(valor_field.value)
            except ValueError:
                self._show_toast("Valor inválido!", is_error=True)
                return
            nova_data = datetime.strptime(venc_field.value, "%d/%m/%Y").date().strftime("%Y-%m-%d")
            atualizar_parcela(parcela_id, novo_valor, nova_data)
            dlg.open = False
            page.update()
            self._show_toast("Item atualizado!")
            self._on_navigate(0)

        def cancelar(_):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.EDIT_OUTLINED, color=Colors.ACCENT_300),
                    ft.Text("Editar", size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    ft.Text(descricao, size=13, color=Colors.GREY_400, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=6, color=ft.colors.TRANSPARENT),
                    valor_field,
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.CALENDAR_MONTH, color=Colors.ACCENT_300, size=18),
                                venc_field,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        on_click=pick_date,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        padding=12,
                        border_radius=10,
                    ),
                ],
                spacing=8,
                width=280,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.FilledButton("Salvar", on_click=salvar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    @staticmethod
    def _apply_mask(e: ft.ControlEvent) -> None:
        apply_money_mask(e)
