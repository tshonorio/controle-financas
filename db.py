"""
Módulo de acesso ao banco de dados SQLite.

Encapsula todas as operações de CRUD referentes a Compras e Parcelas,
separando a lógica de persistência da lógica de interface.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime
import sqlite3

DB_NAME = "controle.db"


# ---------------------------------------------------------------------------
# Funções de conexão e inicialização
# ---------------------------------------------------------------------------
def _connect() -> sqlite3.Connection:
    """Cria uma conexão com o banco habilitando foreign keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Cria as tabelas compras e parcelas se não existirem."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor_total REAL NOT NULL,
                categoria TEXT NOT NULL,
                metodo_pagamento TEXT NOT NULL,
                num_parcelas INTEGER NOT NULL DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                num_parcela INTEGER NOT NULL,
                valor_parcela REAL NOT NULL,
                data_vencimento TEXT NOT NULL,
                paga INTEGER NOT NULL DEFAULT 0,
                prioridade INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(compra_id) REFERENCES compras(id) ON DELETE CASCADE
            )
        """)
        # Migração: colunas de bancos antigos
        for col in ("prioridade", "notificar_dias", "custo_fixo_id"):
            try:
                cursor.execute(f"ALTER TABLE parcelas ADD COLUMN {col} INTEGER")
            except sqlite3.OperationalError:
                pass

        for col in ("valores_parcelas", "local", "tipo_custo"):
            try:
                cursor.execute(f"ALTER TABLE compras ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custos_fixos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                dia_vencimento INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                metodo_pagamento TEXT NOT NULL,
                observacao TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT,
                categoria TEXT,
                tipo TEXT NOT NULL DEFAULT 'variavel'
            )
        """)


# ---------------------------------------------------------------------------
# Operações genéricas
# ---------------------------------------------------------------------------
def db_execute(query: str, params: tuple = ()) -> int:
    """Executa INSERT/UPDATE/DELETE e retorna o lastrowid."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid


def db_query(query: str, params: tuple = ()) -> list[tuple]:
    """Executa SELECT e retorna as linhas como lista de tuplas."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


# ---------------------------------------------------------------------------
# Queries de parcelas
# ---------------------------------------------------------------------------

def buscar_resumo_mes(ano: int, mes: int) -> dict:
    """Retorna agregados mensais para o Dashboard.

    Adapte a cláusula WHERE se seu banco usar colunas diferentes
    para filtrar por mês (ex: ``data_vencimento``).
    """
    inicio = f"{ano:04d}-{mes:02d}-01"
    ultimo_dia = monthrange(ano, mes)[1]
    fim = f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"

    rows = db_query(
        """
        SELECT c.tipo_custo, c.categoria, p.valor_parcela, p.paga
        FROM parcelas p
        JOIN compras c ON p.compra_id = c.id
        WHERE p.data_vencimento BETWEEN ? AND ?
        """,
        (inicio, fim),
    )

    total_geral = 0.0
    total_fixo = 0.0
    total_var = 0.0
    total_pago = 0.0
    total_pend = 0.0
    por_categoria: dict[str, float] = {}

    for tipo_custo, cat, valor, paga in rows:
        total_geral += valor
        if tipo_custo == "fixo":
            total_fixo += valor
        else:
            total_var += valor
        if paga == 1:
            total_pago += valor
        else:
            total_pend += valor
        por_categoria[cat] = por_categoria.get(cat, 0.0) + valor

    return {
        "total_geral": total_geral,
        "total_fixo": total_fixo,
        "total_variavel": total_var,
        "total_pago": total_pago,
        "total_pendente": total_pend,
        "por_categoria": por_categoria,
        "tem_dados": total_geral > 0,
    }


def buscar_parcelas_futuras(data_fim: str) -> list[tuple]:
    """Retorna parcelas não pagas posteriores a data_fim."""
    return db_query(
        "SELECT valor_parcela FROM parcelas WHERE data_vencimento > ? AND paga = 0",
        (data_fim,),
    )


def buscar_parcelas_extrato(
    ano: int,
    mes: int,
    status: str = "todos",
    categoria: str = "todas",
) -> list[tuple]:
    """Retorna parcelas filtradas para a view de extrato."""
    inicio = f"{ano:04d}-{mes:02d}-01"
    ultimo_dia = monthrange(ano, mes)[1]
    fim = f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"

    query = """
        SELECT p.id, c.descricao, p.num_parcela, c.num_parcelas,
               p.valor_parcela, p.data_vencimento, p.paga,
               c.categoria, c.metodo_pagamento, c.id,
               p.notificar_dias
        FROM parcelas p
        JOIN compras c ON p.compra_id = c.id
        WHERE p.data_vencimento BETWEEN ? AND ?
    """
    params: list[str | int] = [inicio, fim]

    if status == "pagos":
        query += " AND p.paga = 1"
    elif status == "pendentes":
        query += " AND p.paga = 0"

    if categoria != "todas":
        query += " AND c.categoria = ?"
        params.append(categoria)

    query += " ORDER BY p.data_vencimento ASC"
    return db_query(query, tuple(params))


# ---------------------------------------------------------------------------
# Operações de escrita
# ---------------------------------------------------------------------------
def toggle_parcela(parcela_id: int, status_atual: int) -> int:
    """Alterna o status de pagamento de uma parcela. Retorna o novo status."""
    novo = 0 if status_atual == 1 else 1
    db_execute("UPDATE parcelas SET paga = ? WHERE id = ?", (novo, parcela_id))
    return novo


# ---------------------------------------------------------------------------
# Queries de prioridade (Lançamentos)
# ---------------------------------------------------------------------------
def buscar_todas_parcelas() -> list[tuple]:
    """Retorna todas as parcelas ordenadas por prioridade (desc) e vencimento."""
    return db_query(
        """
        SELECT p.id, c.descricao, p.num_parcela, c.num_parcelas,
               p.valor_parcela, p.data_vencimento, p.paga,
               c.categoria, c.metodo_pagamento, c.id, p.prioridade,
               p.notificar_dias, p.custo_fixo_id, c.local
        FROM parcelas p
        JOIN compras c ON p.compra_id = c.id
        ORDER BY p.paga ASC, p.prioridade DESC, p.data_vencimento ASC
        """
    )


def atualizar_prioridades_em_lote(parcelas: list[tuple[int, int]]) -> None:
    """Atualiza prioridades de múltiplas parcelas de uma vez.

    Args:
        parcelas: Lista de tuplas (parcela_id, nova_prioridade).
    """
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "UPDATE parcelas SET prioridade = ? WHERE id = ?",
            [(p, pid) for pid, p in parcelas],
        )


# ---------------------------------------------------------------------------
# Notificações por item
# ---------------------------------------------------------------------------
def deletar_parcela(parcela_id: int) -> None:
    """Exclui uma parcela e remove a compra se for a última."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT compra_id FROM parcelas WHERE id = ?", (parcela_id,))
        row = cursor.fetchone()
        if not row:
            return
        compra_id = row[0]
        cursor.execute("DELETE FROM parcelas WHERE id = ?", (parcela_id,))
        cursor.execute("SELECT COUNT(*) FROM parcelas WHERE compra_id = ?", (compra_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("DELETE FROM compras WHERE id = ?", (compra_id,))


def atualizar_parcela(parcela_id: int, valor: float, data_vencimento: str) -> None:
    """Atualiza valor e data de vencimento de uma parcela."""
    db_execute(
        "UPDATE parcelas SET valor_parcela = ?, data_vencimento = ? WHERE id = ?",
        (valor, data_vencimento, parcela_id),
    )


def definir_notificar_parcela(parcela_id: int, dias_antes: int | None) -> None:
    """Define quantos dias antes notificar para uma parcela. None = desligar."""
    db_execute(
        "UPDATE parcelas SET notificar_dias = ? WHERE id = ?",
        (dias_antes, parcela_id),
    )


def inserir_custo_fixo(descricao: str, valor: float, dia: int, categoria: str, metodo: str) -> int:
    """Insere um novo custo fixo e retorna seu id."""
    return db_execute(
        "INSERT INTO custos_fixos (descricao, valor, dia_vencimento, categoria, metodo_pagamento) "
        "VALUES (?, ?, ?, ?, ?)",
        (descricao, valor, dia, categoria, metodo),
    )


def buscar_custo_fixo(cf_id: int) -> tuple | None:
    """Retorna os dados de um custo fixo pelo id."""
    rows = db_query(
        "SELECT id, descricao, valor, dia_vencimento, categoria, metodo_pagamento "
        "FROM custos_fixos WHERE id = ?",
        (cf_id,),
    )
    return rows[0] if rows else None


def criar_proxima_parcela_cf(cf_id: int, compra_id: int) -> bool:
    """Cria a próxima parcela (mês seguinte) de um custo fixo.
    
    Calcula o próximo vencimento com base na última parcela da compra,
    não na data atual.
    Retorna True se criou, False se já existe parcela para o próximo mês.
    """
    cf = buscar_custo_fixo(cf_id)
    if not cf:
        return False

    _cf_id, desc, valor, dia, cat, metodo = cf

    # Busca a última parcela desta compra
    ultima = db_query(
        "SELECT data_vencimento FROM parcelas WHERE compra_id = ? ORDER BY data_vencimento DESC LIMIT 1",
        (compra_id,),
    )
    if not ultima:
        return False

    ultima_data = datetime.strptime(ultima[0][0], "%Y-%m-%d").date()

    # Próximo mês a partir da última parcela
    if ultima_data.month == 12:
        prox_ano = ultima_data.year + 1
        prox_mes = 1
    else:
        prox_ano = ultima_data.year
        prox_mes = ultima_data.month + 1

    ultimo_dia = monthrange(prox_ano, prox_mes)[1]
    dia_ajustado = min(dia, ultimo_dia)
    prox_venc = f"{prox_ano:04d}-{prox_mes:02d}-{dia_ajustado:02d}"

    # Verifica se já existe parcela para essa competência
    existing = db_query(
        "SELECT id FROM parcelas WHERE compra_id = ? AND data_vencimento = ?",
        (compra_id, prox_venc),
    )
    if existing:
        return False

    # Número da próxima parcela
    max_num = db_query(
        "SELECT COALESCE(MAX(num_parcela), 0) FROM parcelas WHERE compra_id = ?",
        (compra_id,),
    )
    prox_num = max_num[0][0] + 1 if max_num else 1

    total_parcelas = db_query(
        "SELECT num_parcelas FROM compras WHERE id = ?",
        (compra_id,),
    )
    if total_parcelas:
        novo_total = total_parcelas[0][0] + 1
        db_execute("UPDATE compras SET num_parcelas = ?, valor_total = valor_total + ? WHERE id = ?",
                   (novo_total, valor, compra_id))

    db_execute(
        "INSERT INTO parcelas (compra_id, num_parcela, valor_parcela, data_vencimento, paga, custo_fixo_id) "
        "VALUES (?, ?, ?, ?, 0, ?)",
        (compra_id, prox_num, valor, prox_venc, cf_id),
    )
    return True


def criar_proxima_parcela_compra(compra_id: int) -> bool:
    """Cria a próxima parcela de uma compra parcelada (uma por vez).

    Lê os valores futuros de compras.valores_parcelas (JSON).
    Retorna True se criou, False se não há mais parcelas ou já existe.
    """
    import json

    compra = db_query(
        "SELECT num_parcelas, valores_parcelas FROM compras WHERE id = ?",
        (compra_id,),
    )
    if not compra or not compra[0][1]:
        return False

    num_parcelas = compra[0][0]
    valores_json = compra[0][1]
    try:
        valores: list[float] = json.loads(valores_json)
    except (json.JSONDecodeError, TypeError):
        return False

    criadas = db_query(
        "SELECT COUNT(*) FROM parcelas WHERE compra_id = ?",
        (compra_id,),
    )
    qtd = criadas[0][0] if criadas else 0

    if qtd >= len(valores):
        return False

    # Próximo índice a criar
    prox_idx = qtd  # 0-based
    prox_valor = valores[prox_idx]
    prox_num = prox_idx + 1

    # Vencimento: último vencimento + 1 mês
    ultima = db_query(
        "SELECT data_vencimento FROM parcelas WHERE compra_id = ? ORDER BY data_vencimento DESC LIMIT 1",
        (compra_id,),
    )
    if not ultima:
        return False

    ultima_data = datetime.strptime(ultima[0][0], "%Y-%m-%d").date()
    if ultima_data.month == 12:
        prox_ano = ultima_data.year + 1
        prox_mes = 1
    else:
        prox_ano = ultima_data.year
        prox_mes = ultima_data.month + 1

    ultimo_dia = monthrange(prox_ano, prox_mes)[1]
    dia_ajustado = min(ultima_data.day, ultimo_dia)
    prox_venc = f"{prox_ano:04d}-{prox_mes:02d}-{dia_ajustado:02d}"

    db_execute(
        "INSERT INTO parcelas (compra_id, num_parcela, valor_parcela, data_vencimento, paga) "
        "VALUES (?, ?, ?, ?, 0)",
        (compra_id, prox_num, prox_valor, prox_venc),
    )

    # Se esta era a última, limpa o JSON (opcional)
    if prox_idx + 1 >= len(valores):
        db_execute("UPDATE compras SET valores_parcelas = NULL WHERE id = ?", (compra_id,))

    return True


# ---------------------------------------------------------------------------
# Rendas
# ---------------------------------------------------------------------------
def buscar_renda_fixa() -> tuple | None:
    """Retorna a renda fixa cadastrada."""
    rows = db_query(
        "SELECT id, descricao, valor FROM rendas WHERE tipo = 'fixa' LIMIT 1"
    )
    return rows[0] if rows else None


def salvar_renda_fixa(descricao: str, valor: float) -> int:
    """Insere ou atualiza a renda fixa."""
    existente = buscar_renda_fixa()
    if existente:
        db_execute(
            "UPDATE rendas SET descricao = ?, valor = ? WHERE id = ?",
            (descricao, valor, existente[0]),
        )
        return existente[0]
    return db_execute(
        "INSERT INTO rendas (descricao, valor, tipo) VALUES (?, ?, 'fixa')",
        (descricao, valor),
    )


def buscar_rendas_variaveis() -> list[tuple]:
    """Retorna todas as rendas variáveis ordenadas por data."""
    return db_query(
        "SELECT id, descricao, valor, data, categoria FROM rendas WHERE tipo = 'variavel' ORDER BY data DESC"
    )


def inserir_renda_variavel(descricao: str, valor: float, data: str, categoria: str = "") -> int:
    """Insere uma nova renda variável."""
    return db_execute(
        "INSERT INTO rendas (descricao, valor, data, categoria, tipo) VALUES (?, ?, ?, ?, 'variavel')",
        (descricao, valor, data, categoria),
    )


def excluir_renda(renda_id: int) -> None:
    """Exclui uma renda (fixa ou variável)."""
    db_execute("DELETE FROM rendas WHERE id = ?", (renda_id,))


