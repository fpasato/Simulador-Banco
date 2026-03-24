from functools import total_ordering
from utils.validators import get_db
import random
import sqlite3
from datetime import datetime, timedelta

def get_faturas(conta_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faturas WHERE conta_id = ?", (conta_id,))
    faturas = cursor.fetchall()
    conn.close()
    return faturas

def pagar_fatura(fatura_id, conn=None):
    # Se não recebeu conexão, abre uma nova
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()
    
    cursor.execute("UPDATE faturas SET status = 'pago' WHERE id = ?", (fatura_id,))
    
    # Só commita e fecha se a conexão for local (criada aqui dentro)
    if not conn:
        local_conn.commit()
        local_conn.close()
    return True

def registrar_transacao(conta_id, valor, conn=None):
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()
    
    cursor.execute("""
        INSERT INTO transacoes_conta (conta_id, valor, tipo, descricao)
        VALUES (?, ?, 'debito', 'Pagamento de fatura')
    """, (conta_id, valor))
    
    if not conn:
        local_conn.commit()
        local_conn.close()
    return True

def deletar_fatura(fatura_id, conn=None):
    local_conn = conn if conn else get_db()
    cursor = local_conn.cursor()
    
    cursor.execute("DELETE FROM faturas WHERE id = ?", (fatura_id,))
    
    if not conn:
        local_conn.commit()
        local_conn.close()
    return True

def get_valor_fatura(fatura_id, conta_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM faturas WHERE id = ? AND conta_id = ?", (fatura_id, conta_id))
    fatura = cursor.fetchone()
    conn.close()
    return fatura

def gerar_valor(tipo):
    ranges = {
        "luz": (80, 200),
        "agua": (50, 150),
        "internet": (70, 150),
        "aluguel": (400, 1200),
        "celular": (40, 100),
        "academia": (60, 120),
        "streaming": (20, 60),

        # extras (caso use depois)
        "uber": (10, 60),
        "ifood": (25, 120),
        "mercado": (100, 400),
        "gasolina": (120, 300),
        "multa": (100, 500),
    }

    minimo, maximo = ranges.get(tipo, (20, 300))
    return round(random.uniform(minimo, maximo), 2)

def gerar_faturas_mensais_obrigatorias(conta_id):
    conn = get_db()
    cursor = conn.cursor()

    nomes_tipos = [
        ("luz", "Conta de luz"),
        ("agua", "Conta de água"),
        ("internet", "Internet"),
        ("aluguel", "Aluguel"),
        ("celular", "Plano de celular"),
        ("academia", "Mensalidade academia"),
        ("streaming", "Assinatura streaming"),
    ]
    
    faturas_mensais = []

    for nome, descricao in nomes_tipos:
        valor = gerar_valor(nome)

        faturas_mensais.append((
            nome,
            valor,
            "pendente",
            datetime.now() + timedelta(hours=1),
            descricao
        ))

    # Inserir no banco
    cursor.executemany("""
        INSERT INTO faturas (conta_id, tipo, valor, status, data_vencimento, descricao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (conta_id, t, v, s, d.isoformat(), desc)
        for t, v, s, d, desc in faturas_mensais
    ])

    conn.commit()
    conn.close()
    print("Faturas mensais criadas")
    


def gerar_faturas_aleatorias(conta_id):
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

    faturas_aleatorias = []

    for tipo, descricao in tipos_aleatorios:
        valor = gerar_valor(tipo)
        
        faturas_aleatorias.append((
            tipo,
            valor,
            "pendente",
            datetime.now() + timedelta(hours=1),
            descricao
        ))
    
    #  sorteia quantidade
    quantidade = random.randint(1, 5)
    
    # pega só algumas
    faturas_escolhidas = random.sample(faturas_aleatorias, quantidade)
    
    # Inserir no banco (AGORA CORRETO)
    cursor.executemany("""
        INSERT INTO faturas (conta_id, tipo, valor, status, data_vencimento, descricao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (conta_id, t, v, s, d.isoformat(), desc)
        for t, v, s, d, desc in faturas_escolhidas
    ])
    
    conn.commit()
    conn.close()

    print(f"{quantidade} faturas aleatórias criadas 🚀")


def gerar_faturas_mensais_todos_usuarios():
    """Função wrapper para o scheduler - gera faturas para todos os usuários"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM contas")
    contas = cursor.fetchall()
    conn.close()
    
    for conta in contas:
        gerar_faturas_mensais_obrigatorias(conta['id'])


def gerar_faturas_aleatorias_todos_usuarios():
    """Função wrapper para o scheduler - gera faturas aleatórias para todos os usuários"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM contas")
    contas = cursor.fetchall()
    conn.close()
    
    for conta in contas:
        gerar_faturas_aleatorias(conta['id'])
        


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

    agora = datetime.now()

    for fatura in faturas:
        try:
            data_vencimento = datetime.fromisoformat(fatura['data_vencimento'])
            if agora <= data_vencimento:
                continue  # ainda não venceu

            # Horas de atraso (pode ser fracionado)
            atraso_segundos = (agora - data_vencimento).total_seconds()
            atraso_horas = atraso_segundos / 3600

            # Extrai valores atuais
            valor_atual = float(fatura['valor'] or 0)
            juros_acumulado = float(fatura['juros'] or 0)

            # Valor base = valor original (sem nenhum juro)
            valor_base = valor_atual - juros_acumulado

            # Total de juros devido até agora (juros simples sobre o valor base)
            juros_total = valor_base * 0.02 * atraso_horas
            novo_valor = valor_base + juros_total

            # Atualiza a fatura com os valores totais
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
    print("Juros aplicados nas faturas atrasadas 🚀")