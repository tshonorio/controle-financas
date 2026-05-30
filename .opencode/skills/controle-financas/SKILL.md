---
name: controle-financas
description: Use when you need to understand, modify, or extend the Controle de Finanças Flet app. Trigger keywords: projeto, app, controle, finanças, financas, flet, entender, resumo, documentação, documentacao, contexto.
---

# App Controle de Finanças — Documentação do Projeto

## Visão Geral

App desktop/mobile em **Python Flet** com **SQLite** para controle de gastos, compras parceladas, custos fixos, rendas. Tema escuro com paleta Instagram (rosa/purple) e gradientes.

---

## Estrutura de Arquivos

```
controle/
├── main.py                # Ponto de entrada, navegação (4 abas), tema global
├── db.py                  # Camada SQLite — todas as queries CRUD
├── state.py               # Estado global: mês/ano selecionado, filtros
├── styles.py              # Cores (paleta rosa/purple), categorias, formatação, botões
├── pdf_export.py          # Exportação de extrato mensal em PDF
├── components/
│   ├── __init__.py
│   ├── common.py           # Componentes reutilizáveis (MoneyField, PeriodSelector, SummaryCard, etc.)
│   ├── dashboard.py        # Aba Dashboard — painel mensal interativo com navegação história + gráficos
│   ├── lanctos.py          # Aba Lançamentos — lista de parcelas pendentes
│   ├── registro_custo.py   # Aba Registro de Custo — formulário unificado (Fixo / Variável)
│   └── renda.py            # Aba Rendas — renda fixa + variável
└── controle.db             # Banco SQLite (gerado automaticamente)
```

---

## Navegação (4 Abas)

| Índice | Aba | Componente | Descrição |
|---|---|---|---|
| 0 | Lançamentos | `LanctosView` | Lista de parcelas **pendentes** com drag-and-drop, toggle de pagamento, editar, excluir, notificações |
| 1 | Registro de Custo | `RegistroCustoView` | Formulário unificado (seletor **Fixo** / **Variável**) — cadastra compras avulsas ou contas fixas mensais |
| 2 | Rendas | `RendaView` | Cadastro de renda fixa + rendas variáveis |
| 3 | Dashboard | `DashboardView` | Painel mensal interativo com navegação histórica, cards de resumo (Total / Fixos / Variáveis) e gráfico de pizza por categoria |

---

## Banco de Dados (SQLite)

### Tabela `compras`
| Coluna | Tipo | Descrição |
|---|---|---|
| id | INTEGER PK | |
| descricao | TEXT | Nome da compra |
| valor_total | REAL | |
| categoria | TEXT | Alimentação, Transporte, etc. |
| metodo_pagamento | TEXT | Pix, Débito, Crédito |
| num_parcelas | INTEGER | Total de parcelas (1 = à vista) |
| valores_parcelas | TEXT | JSON com valores futuros de cada parcela |
| local | TEXT | Local da compra |
| tipo_custo | TEXT | `'fixo'` ou `'variavel'` — discrimina a origem |

### Tabela `parcelas`
| Coluna | Tipo | Descrição |
|---|---|---|
| id | INTEGER PK | |
| compra_id | INTEGER FK | -> compras.id |
| num_parcela | INTEGER | Nº da parcela |
| valor_parcela | REAL | |
| data_vencimento | TEXT | YYYY-MM-DD |
| paga | INTEGER | 0 = pendente, 1 = paga |
| prioridade | INTEGER | Para reordenação manual |
| notificar_dias | INTEGER | Dias antes para notificar |
| custo_fixo_id | INTEGER FK | -> custos_fixos.id (se for custo fixo) |

### Tabela `custos_fixos`
| Coluna | Tipo |
|---|---|
| id, descricao, valor, dia_vencimento, categoria, metodo_pagamento | |

### Tabela `rendas`
| Coluna | Tipo |
|---|---|
| id, descricao, valor, data, categoria, tipo (fixa/variavel) | |

---

## Paleta de Cores (Instagram Theme)

```
Primary:     PINK/PINK_600     → Botões, ACCENT
Secondary:   PURPLE/DEEP_PURPLE → Gradientes, destaques
Success:     GREEN_400/GREEN_700 → Valores pagos, progresso
Warning:     AMBER              → Pendente
Error:       RED                → Saldo negativo, urgente
Surface:     SURFACE / SURFACE_VARIANT (dark)
```

### Gradientes usados
- `GRADIENT_BRAND`: PINK → PURPLE → DEEP_PURPLE (saldo positivo)
- `GRADIENT_GOLD`: AMBER → ORANGE (saldo negativo)
- `GRADIENT_GREEN`: GREEN → TEAL (receitas)
- Cards do dashboard: PINK→PURPLE (variáveis), PURPLE→DEEP_PURPLE (fixos), DEEP_PURPLE→INDIGO (total)

### Botões reutilizáveis (styles.py)
- `BTN_PRIMARY`: PINK_600 com bordas arredondadas
- `BTN_SUCCESS`: GREEN_700

---

## Fluxos Principais

### Registrar Custo (Fixo ou Variável)
1. Aba **Registro de Custo** — seletor visual no topo: **Fixo** | **Variável**
2. **Modo Variável**: preencher descrição, local, valor (máscara automática), data, categoria, método
   - Se "Crédito": definir nº parcelas e 1º vencimento → preview do valor da parcela
   - Salva em `compras` + 1ª parcela em `parcelas` com `tipo_custo = 'variavel'`
3. **Modo Fixo**: preencher descrição, valor, dia do vencimento, categoria, método
   - Data do 1º vencimento calculada automaticamente
   - Salva em `custos_fixos` (definição) + `compras` + `parcela` com `tipo_custo = 'fixo'` e `custo_fixo_id`
4. Valores futuros (parcelamento) armazenados em JSON (`valores_parcelas`)
5. Navega para Lançamentos

### Pagar Parcela (Lançamentos)
1. Clicar no círculo da parcela pendente
2. Confirmar no diálogo
3. `toggle_parcela()` marca `paga = 1`
4. Se for `custo_fixo_id`: pergunta se quer renovar para próximo mês
5. Se for compra parcelada: cria próxima parcela automaticamente
6. Item some da lista

### Custos Fixos (Renovação)
1. Cadastra em Registro de Custo > **Fixo** → gera definição em `custos_fixos` + `compras` + `parcelas`
2. Parcela aparece em Lançamentos para pagamento
3. Ao pagar, pergunta se quer renovar → cria parcela do mês seguinte

### Dashboard Mensal
1. Aba **Dashboard** carrega automaticamente o mês corrente
2. Navegação com setas ⬅️ ➡️ para percorrer o histórico
3. Três cards de resumo: Custo Total, C. Fixos, C. Variáveis
4. Gráfico de pizza (`PieChart`) mostra distribuição por categoria
5. Ao navegar, apenas os dados do dashboard são atualizados (sem recarregar a tela)
6. Meses sem dados exibem "Nenhum dado encontrado para este mês"

---

## Máscara Monetária

Centralizada em `common.py`:
- `apply_money_mask(e)`: aplica em `on_change` de TextField
- `MoneyField`: TextField com máscara embutida

Usada em: `registro_custo.py`, `renda.py`, `lanctos.py`

---

## Decisões de UX/UI

- **Tema escuro** com `color_scheme_seed=ft.colors.PINK`
- **Tema claro** configurado separadamente em `page.dark_theme` / `page.theme`
- **Toggle tema**: botão no canto superior direito (lua/sol)
- **NavBar**: sem labels, só ícones, `label_behavior=ALWAYS_HIDE`, altura 64
- **Registro de Custo**: formulário unificado com seletor visual Fixo/Variável no topo
- **Lançamentos**: só pendentes
- **Máscara monetária**: `apply_money_mask()` centralizada em `common.py`

---

## Funcionalidades Extras

- **Drag-and-drop**: reordenar parcelas por prioridade (arrastar)
- **Editar**: pressionar 2s sobre item → editar valor/vencimento
- **Notificações**: definir lembretes (1, 2, 3, 5, 7 dias antes)
- **Exportar PDF**: extrato mensal via `pdf_export.py` (fpdf2)

---

## Problemas de Migração Flet 0.22 → 0.85

### APIs Depreciadas e Substituições

| Padrão antigo | Novo padrão | Arquivos afetados |
|---|---|---|
| `ft.colors.*` | `ft.Colors.*` | 8 |
| `ft.icons.*` | `ft.Icons.*` | 8 |
| `ft.alignment.*` | `ft.Alignment.TOP_LEFT` (UPPER_CASE) | 3 |
| `ft.border.all/only` | `ft.Border.all/only` | 2 |
| `ft.padding.symmetric/only` | `ft.Padding.symmetric/only` | 3 |
| `ft.border_radius.only` | `ft.BorderRadius.only` | 1 |
| `SURFACE_VARIANT` | `SURFACE_CONTAINER_HIGHEST` | 9 |
| `ft.app(target=main)` | `ft.run(main)` | main.py |
| `ft.NavigationDestination` | `ft.NavigationBarDestination` | main.py |
| `ElevatedButton(text="...")` | `ElevatedButton("...")` (posicional) | 5 |
| `Dropdown(on_change=...)` | `Dropdown(on_select=...)` | 2 |
| `ft.dropdown.Option` | `ft.DropdownOption` | 4 |

### 🚨 PROBLEMA ATUAL: APK Mostra Tela Preta (não resolvido)

**Sintoma**: APK compila e instala, mas abre com tela preta (sem crash visível).

**Contexto**: Bug conhecido do Flet — issues #6022, #6169, #6135. Mesmo apps "Hello World" apresentam o problema em versões > 0.80.x.

**O que já foi tentado (30/05/2026):**
1. ✅ Removido `ft.SafeArea` do root (causava tela preta)
2. ✅ Revertidas mudanças de responsividade (dashboard wrap/expand, metadata wrap)
3. ✅ Adicionado `pyproject.toml` com boot screen habilitado
4. ✅ Pin `flet==0.85.1` em vez de `>=0.85.0`
5. ❌ APK ainda mostra tela preta (run #21)

**Próximos passos a tentar:**
1. Conectar `adb logcat` e filtrar por `com.github.tshonorio.controle_financas` para ver erro real
2. Tentar `flet==0.80.5` (última versão antes dos relatos de tela branca)
3. Criar um "Hello World" mínimo e buildar APK para ver se o problema é no código ou no build do Flet
4. Verificar logs do build com `--verbose` (já está no workflow)
5. Testar no emulador Android em vez de físico
