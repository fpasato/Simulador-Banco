from functools import total_ordering
from utils.validators import get_db
import random
import sqlite3
from datetime import datetime, timedelta, timezone

# ----------------------------------------------------------------------
# Funções de consulta e manipulação de faturas
# ----------------------------------------------------------------------

def get_faturas(conta_id):
    """Retorna todas as faturas de uma conta (sem conversão de fuso)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faturas WHERE conta_id = ?", (conta_id,))
    faturas = cursor.fetchall()
    conn.close()
    return faturas


def pagar_fatura(fatura_id, conn=None):
    """Marca uma fatura como paga."""
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()
    cursor.execute("UPDATE faturas SET status = 'pago' WHERE id = ?", (fatura_id,))
    if not conn:
        local_conn.commit()
        local_conn.close()
    return True




def registrar_transacao(conta_id, valor, tipo, descricao, conn=None):
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()
    data_utc = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO transacoes_conta (conta_id, valor, tipo, descricao, data)
        VALUES (?, ?, ?, ?, ?)
    """, (conta_id, valor, tipo, descricao, data_utc))
    if not conn:
        local_conn.commit()
        local_conn.close()


def deletar_fatura(fatura_id, conn=None):
    """Remove uma fatura (utilizado apenas em contexto específico)."""
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()
    cursor.execute("DELETE FROM faturas WHERE id = ?", (fatura_id,))
    if not conn:
        local_conn.commit()
        local_conn.close()
    return True


def get_valor_fatura(fatura_id, conta_id):
    """Retorna o valor de uma fatura específica."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM faturas WHERE id = ? AND conta_id = ?", (fatura_id, conta_id))
    fatura = cursor.fetchone()
    conn.close()
    return fatura


# ----------------------------------------------------------------------
# Funções de controle de limite
# ----------------------------------------------------------------------

def limitar_faturas_pagas(conta_id, conn=None):
    """Mantém no máximo 100 faturas pagas, removendo as mais antigas."""
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM faturas WHERE conta_id = ? AND status = 'pago'", (conta_id,))
    count_pagas = cursor.fetchone()[0]

    if count_pagas > 100:
        excedente = count_pagas - 100
        cursor.execute("""
            DELETE FROM faturas 
            WHERE id IN (
                SELECT id FROM faturas 
                WHERE conta_id = ? AND status = 'pago'
                ORDER BY id ASC 
                LIMIT ?
            )
        """, (conta_id, excedente))

    if not conn:
        local_conn.commit()
        local_conn.close()


def limitar_faturas_pendentes(conta_id, conn=None):
    """Garante no máximo 50 faturas pendentes, removendo as mais antigas."""
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM faturas WHERE conta_id = ? AND status = 'pendente'", (conta_id,))
    count_pendentes = cursor.fetchone()[0]

    if count_pendentes > 50:
        excedente = count_pendentes - 50
        cursor.execute("""
            DELETE FROM faturas 
            WHERE id IN (
                SELECT id FROM faturas 
                WHERE conta_id = ? AND status = 'pendente'
                ORDER BY id ASC 
                LIMIT ?
            )
        """, (conta_id, excedente))

    if not conn:
        local_conn.commit()
        local_conn.close()


# ----------------------------------------------------------------------
# Funções auxiliares para geração de valores
# ----------------------------------------------------------------------

def gerar_valor(tipo):
    """Gera um valor aleatório dentro da faixa definida para o tipo."""
    ranges = {
        "luz": (80, 200),
        "agua": (50, 150),
        "internet": (100, 250),
        "aluguel": (400, 1200),
        "celular": (40, 100),
        "academia": (60, 120),
        "streaming": (20, 60),
        "uber": (10, 60),
        "ifood": (25, 120),
        "mercado": (100, 400),
        "gasolina": (200, 500),
        "multa": (100, 500),
    }
    minimo, maximo = ranges.get(tipo, (20, 300))
    return round(random.uniform(minimo, maximo), 2)


# ----------------------------------------------------------------------
# Geração de faturas (mensais obrigatórias e aleatórias)
# ----------------------------------------------------------------------

def gerar_faturas_mensais_obrigatorias(conta_id):
    """Gera as faturas mensais fixas (luz, água, etc.) com data de vencimento em UTC."""
    conn = get_db()
    cursor = conn.cursor()

    # Verifica limite de pendentes
    cursor.execute("SELECT COUNT(*) FROM faturas WHERE conta_id = ? AND status = 'pendente'", (conta_id,))
    pendentes = cursor.fetchone()[0]
    if pendentes >= 50:
        print(f"Usuário {conta_id} já possui 50 faturas pendentes. Não serão geradas novas.")
        conn.close()
        return

    nomes_tipos = [
        ("luz", "Conta de luz"),
        ("agua", "Conta de água"),
        ("internet", "Internet"),
        ("aluguel", "Aluguel"),
        ("celular", "Plano de celular"),
        ("academia", "Mensalidade academia"),
        ("streaming", "Assinatura streaming"),
    ]

    agora_utc = datetime.now(timezone.utc)
    faturas_mensais = []

    for nome, descricao in nomes_tipos:
        valor = gerar_valor(nome)
        faturas_mensais.append((
            nome,
            valor,
            "pendente",
            agora_utc + timedelta(hours=1),   # vence em 1 hora UTC
            descricao
        ))

    cursor.executemany("""
        INSERT INTO faturas (conta_id, tipo, valor, status, data_vencimento, descricao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (conta_id, t, v, s, d.isoformat(), desc)
        for t, v, s, d, desc in faturas_mensais
    ])

    limitar_faturas_pendentes(conta_id, conn=conn)   # aplica limite após inserção
    conn.commit()
    conn.close()
    print("Faturas mensais criadas")


def gerar_faturas_aleatorias(conta_id):
    """Gera faturas aleatórias com data de vencimento em UTC."""
    conn = get_db()
    cursor = conn.cursor()

    tipos_aleatorios = [
        ("uber", "Corrida de aplicativo"),
        ("ifood", "Pedido delivery"),
        ("farmacia", "Compra na farmácia"),
        ("mercado", "Supermercado"),
        ("gasolina", "Abastecimento"),
        ("manutencao", "Conserto emergencial"),
        ("multa", "Multa de trânsito"),
        ("consulta", "Consulta médica"),
    ]

    agora_utc = datetime.now(timezone.utc)
    faturas_aleatorias = []

    for tipo, descricao in tipos_aleatorios:
        valor = gerar_valor(tipo)
        faturas_aleatorias.append((
            tipo,
            valor,
            "pendente",
            agora_utc + timedelta(hours=1),
            descricao
        ))

    quantidade = random.randint(1, 5)
    faturas_escolhidas = random.sample(faturas_aleatorias, quantidade)

    cursor.executemany("""
        INSERT INTO faturas (conta_id, tipo, valor, status, data_vencimento, descricao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (conta_id, t, v, s, d.isoformat(), desc)
        for t, v, s, d, desc in faturas_escolhidas
    ])

    limitar_faturas_pendentes(conta_id, conn=conn)   # aplica limite
    conn.commit()
    conn.close()
    print(f"{quantidade} faturas aleatórias criadas")


def gerar_faturas_mensais_todos_usuarios():
    """Wrapper para o scheduler – gera faturas mensais para todos os usuários."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM contas")
    contas = cursor.fetchall()
    conn.close()

    for conta in contas:
        gerar_faturas_mensais_obrigatorias(conta['id'])


def gerar_faturas_aleatorias_todos_usuarios():
    """Wrapper para o scheduler – gera faturas aleatórias para todos os usuários."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM contas")
    contas = cursor.fetchall()
    conn.close()

    for conta in contas:
        gerar_faturas_aleatorias(conta['id'])


# ----------------------------------------------------------------------
# Aplicação de juros (executada periodicamente)
# ----------------------------------------------------------------------

def checa_juros():
    """
    Aplica juros simples de 2% por hora sobre o valor original
    para faturas pendentes vencidas.
    """
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, valor, juros, data_vencimento
        FROM faturas
        WHERE status = 'pendente'
    """)
    faturas = cursor.fetchall()

    agora_utc = datetime.now(timezone.utc)

    for fatura in faturas:
        try:
            data_vencimento = datetime.fromisoformat(fatura['data_vencimento'])
            if agora_utc <= data_vencimento:
                continue

            atraso_segundos = (agora_utc - data_vencimento).total_seconds()
            atraso_horas = atraso_segundos / 3600

            valor_atual = float(fatura['valor'] or 0)
            juros_acumulado = float(fatura['juros'] or 0)

            valor_base = valor_atual - juros_acumulado
            juros_total = valor_base * 0.02 * atraso_horas
            novo_valor = valor_base + juros_total

            cursor.execute("""
                UPDATE faturas
                SET valor = ?, juros = ?
                WHERE id = ?
            """, (
                round(novo_valor, 2),
                round(juros_total, 2),
                fatura['id']
            ))

        except Exception as e:
            print(f"Erro ao calcular juros para fatura {fatura['id']}: {e}")

    conn.commit()
    conn.close()